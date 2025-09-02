"""
데이터 풀 관리자
==============

WebSocket 데이터를 중앙집중식으로 관리하는 데이터 풀 시스템
복잡한 콜백 시스템 대신 간단한 데이터 요청/응답 모델 사용

핵심 원칙:
- 전역 관리자가 모든 WebSocket 데이터 수신
- 클라이언트는 필요할 때 최신 데이터 요청
- 심볼별 최신 데이터를 메모리에 캐시
- 구독 상태는 단순히 "어떤 심볼을 관리할지" 결정
"""

import asyncio
import time
from typing import Dict, Set, Optional, Any, List
from dataclasses import dataclass, field
from collections import defaultdict, deque

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .types import (
    DataType, TickerEvent, OrderbookEvent, TradeEvent, CandleEvent,
    MyOrderEvent, MyAssetEvent, BaseWebSocketEvent
)


@dataclass
class DataPoolEntry:
    """데이터 풀 엔트리"""
    symbol: str
    data_type: DataType
    data: BaseWebSocketEvent
    timestamp: float = field(default_factory=time.time)
    update_count: int = 0


@dataclass
class ClientInterest:
    """클라이언트 관심사 등록"""
    client_id: str
    data_types: Set[DataType]
    symbols: Set[str]
    last_access: float = field(default_factory=time.time)


class DataPoolManager:
    """
    데이터 풀 관리자

    WebSocket 데이터를 중앙에서 수집하고 클라이언트 요청 시 제공하는 단순한 모델
    """

    def __init__(self, max_history: int = 1000):
        self.logger = create_component_logger("DataPoolManager")

        # 데이터 풀 (심볼별 최신 데이터)
        self._data_pool: Dict[str, Dict[DataType, DataPoolEntry]] = defaultdict(dict)

        # 클라이언트 관심사 등록
        self._client_interests: Dict[str, ClientInterest] = {}

        # 필요한 구독 심볼 계산 (모든 클라이언트 관심사 통합)
        self._required_subscriptions: Dict[DataType, Set[str]] = defaultdict(set)

        # 데이터 히스토리 (선택사항, 차트용)
        self._data_history: Dict[str, Dict[DataType, deque]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=max_history)))

        # 성능 메트릭
        self._total_updates = 0
        self._client_requests = 0

        self.logger.info("데이터 풀 관리자 초기화 완료")

    # =============================================================================
    # 클라이언트 관심사 관리
    # =============================================================================

    def register_client_interest(
        self,
        client_id: str,
        data_types: Set[DataType],
        symbols: Set[str]
    ) -> Dict[DataType, Set[str]]:
        """
        클라이언트 관심사 등록

        Args:
            client_id: 클라이언트 식별자
            data_types: 관심 데이터 타입들
            symbols: 관심 심볼들

        Returns:
            Dict[DataType, Set[str]]: 새로 구독이 필요한 데이터
        """
        self.logger.debug(f"클라이언트 관심사 등록: {client_id}, {len(symbols)}개 심볼")

        # 기존 관심사 백업
        old_interests = dict(self._client_interests)

        # 새 관심사 등록
        self._client_interests[client_id] = ClientInterest(
            client_id=client_id,
            data_types=data_types.copy(),
            symbols=symbols.copy()
        )

        # 필요한 구독 재계산
        old_subscriptions = dict(self._required_subscriptions)
        self._recalculate_required_subscriptions()

        # 변경사항 계산
        changes = self._calculate_subscription_changes(old_subscriptions, self._required_subscriptions)

        self.logger.info(f"클라이언트 {client_id} 관심사 등록 완료")
        return changes

    def unregister_client_interest(self, client_id: str) -> Dict[DataType, Set[str]]:
        """
        클라이언트 관심사 해제

        Args:
            client_id: 클라이언트 식별자

        Returns:
            Dict[DataType, Set[str]]: 구독 해제 가능한 데이터
        """
        if client_id not in self._client_interests:
            return {}

        self.logger.debug(f"클라이언트 관심사 해제: {client_id}")

        # 기존 구독 백업
        old_subscriptions = dict(self._required_subscriptions)

        # 클라이언트 제거
        del self._client_interests[client_id]

        # 필요한 구독 재계산
        self._recalculate_required_subscriptions()

        # 변경사항 계산
        changes = self._calculate_subscription_changes(old_subscriptions, self._required_subscriptions)

        self.logger.info(f"클라이언트 {client_id} 관심사 해제 완료")
        return changes

    def _recalculate_required_subscriptions(self) -> None:
        """필요한 구독 재계산 (모든 클라이언트 관심사 통합)"""
        # 초기화
        self._required_subscriptions.clear()

        # 모든 클라이언트 관심사 통합
        for client_interest in self._client_interests.values():
            for data_type in client_interest.data_types:
                self._required_subscriptions[data_type].update(client_interest.symbols)

        self.logger.debug(f"구독 재계산 완료: {len(self._required_subscriptions)}개 타입")

    def _calculate_subscription_changes(
        self,
        old_subs: Dict[DataType, Set[str]],
        new_subs: Dict[DataType, Set[str]]
    ) -> Dict[DataType, Set[str]]:
        """구독 변경사항 계산"""
        changes = {}

        # 모든 데이터 타입 검사
        all_types = set(old_subs.keys()) | set(new_subs.keys())

        for data_type in all_types:
            old_symbols = old_subs.get(data_type, set())
            new_symbols = new_subs.get(data_type, set())

            if old_symbols != new_symbols:
                changes[data_type] = new_symbols

        return changes

    # =============================================================================
    # 데이터 수신 및 저장
    # =============================================================================

    def store_websocket_data(self, event: BaseWebSocketEvent) -> None:
        """
        WebSocket 데이터 저장

        Args:
            event: WebSocket 이벤트
        """
        if not hasattr(event, 'symbol') or not event.symbol:
            return

        # 데이터 타입 추론
        data_type = self._infer_data_type(event)
        if not data_type:
            return

        symbol = event.symbol

        # 데이터 풀에 저장
        entry = DataPoolEntry(
            symbol=symbol,
            data_type=data_type,
            data=event,
            timestamp=time.time()
        )

        if symbol in self._data_pool and data_type in self._data_pool[symbol]:
            entry.update_count = self._data_pool[symbol][data_type].update_count + 1

        self._data_pool[symbol][data_type] = entry

        # 히스토리에 추가 (선택사항)
        self._data_history[symbol][data_type].append(event)

        self._total_updates += 1

        # 로깅 (주기적으로만)
        if self._total_updates % 100 == 0:
            self.logger.debug(f"데이터 업데이트: {symbol} {data_type.value} (총 {self._total_updates}건)")

    def _infer_data_type(self, event: BaseWebSocketEvent) -> Optional[DataType]:
        """이벤트에서 데이터 타입 추론"""
        if isinstance(event, TickerEvent):
            return DataType.TICKER
        elif isinstance(event, OrderbookEvent):
            return DataType.ORDERBOOK
        elif isinstance(event, TradeEvent):
            return DataType.TRADE
        elif isinstance(event, CandleEvent):
            # 캔들 타입 세분화 필요시 unit 필드 확인
            return DataType.CANDLE_1M  # 기본값
        elif isinstance(event, MyOrderEvent):
            return DataType.MYORDER
        elif isinstance(event, MyAssetEvent):
            return DataType.MYASSET
        return None

    # =============================================================================
    # 데이터 조회 API
    # =============================================================================

    def get_latest_data(
        self,
        client_id: str,
        data_type: DataType,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, BaseWebSocketEvent]:
        """
        최신 데이터 조회

        Args:
            client_id: 요청 클라이언트
            data_type: 데이터 타입
            symbols: 조회할 심볼들 (None이면 클라이언트 관심사 전체)

        Returns:
            Dict[str, BaseWebSocketEvent]: 심볼별 최신 데이터
        """
        self._client_requests += 1

        # 클라이언트 관심사 확인
        if client_id not in self._client_interests:
            self.logger.warning(f"미등록 클라이언트 요청: {client_id}")
            return {}

        client_interest = self._client_interests[client_id]
        client_interest.last_access = time.time()

        # 조회 대상 심볼 결정
        if symbols is None:
            target_symbols = client_interest.symbols
        else:
            # 클라이언트 관심사와 교집합만
            target_symbols = client_interest.symbols & set(symbols)

        # 데이터 수집
        result = {}
        for symbol in target_symbols:
            if symbol in self._data_pool and data_type in self._data_pool[symbol]:
                entry = self._data_pool[symbol][data_type]
                result[symbol] = entry.data

        self.logger.debug(f"데이터 조회: {client_id} {data_type.value} {len(result)}개")
        return result

    def get_data_history(
        self,
        client_id: str,
        data_type: DataType,
        symbol: str,
        limit: int = 100
    ) -> List[BaseWebSocketEvent]:
        """
        데이터 히스토리 조회

        Args:
            client_id: 요청 클라이언트
            data_type: 데이터 타입
            symbol: 심볼
            limit: 최대 조회 개수

        Returns:
            List[BaseWebSocketEvent]: 히스토리 데이터
        """
        if client_id not in self._client_interests:
            return []

        if symbol not in self._data_history or data_type not in self._data_history[symbol]:
            return []

        history = list(self._data_history[symbol][data_type])
        return history[-limit:] if limit > 0 else history

    # =============================================================================
    # 상태 조회
    # =============================================================================

    def get_required_subscriptions(self) -> Dict[DataType, Set[str]]:
        """현재 필요한 구독 목록 조회"""
        return {dt: symbols.copy() for dt, symbols in self._required_subscriptions.items()}

    def get_data_summary(self) -> Dict[str, Any]:
        """데이터 풀 상태 요약"""
        symbol_count = len(self._data_pool)
        data_type_counts = defaultdict(int)

        for symbol_data in self._data_pool.values():
            for data_type in symbol_data.keys():
                data_type_counts[data_type.value] += 1

        return {
            'total_symbols': symbol_count,
            'data_type_breakdown': dict(data_type_counts),
            'total_updates': self._total_updates,
            'client_requests': self._client_requests,
            'active_clients': len(self._client_interests)
        }

    def get_client_interests(self) -> Dict[str, Dict[str, Any]]:
        """클라이언트 관심사 현황"""
        return {
            client_id: {
                'data_types': [dt.value for dt in interest.data_types],
                'symbols': list(interest.symbols),
                'last_access': interest.last_access
            }
            for client_id, interest in self._client_interests.items()
        }

    # =============================================================================
    # 유지보수
    # =============================================================================

    async def cleanup_old_data(self, max_age_seconds: int = 3600) -> int:
        """오래된 데이터 정리"""
        current_time = time.time()
        cleaned_count = 0

        for symbol in list(self._data_pool.keys()):
            for data_type in list(self._data_pool[symbol].keys()):
                entry = self._data_pool[symbol][data_type]
                if current_time - entry.timestamp > max_age_seconds:
                    del self._data_pool[symbol][data_type]
                    cleaned_count += 1

            # 심볼에 데이터가 없으면 삭제
            if not self._data_pool[symbol]:
                del self._data_pool[symbol]

        if cleaned_count > 0:
            self.logger.info(f"오래된 데이터 {cleaned_count}개 정리 완료")

        return cleaned_count

    async def cleanup_inactive_clients(self, max_idle_seconds: int = 1800) -> List[str]:
        """비활성 클라이언트 정리"""
        current_time = time.time()
        inactive_clients = []

        for client_id, interest in list(self._client_interests.items()):
            if current_time - interest.last_access > max_idle_seconds:
                inactive_clients.append(client_id)
                del self._client_interests[client_id]

        if inactive_clients:
            # 구독 재계산
            self._recalculate_required_subscriptions()
            self.logger.info(f"비활성 클라이언트 {len(inactive_clients)}개 정리 완료")

        return inactive_clients
