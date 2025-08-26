"""
Realtime Data Manager - 실시간 데이터 관리

Layer 2: WebSocket 구독 관리 & 실시간 캔들 중복 제거
- WebSocket 구독 자동 관리
- 실시간 캔들 중복 제거 (분봉 교체)
- 백그라운드 구독 상태 추적
- 스마트 구독 해제 (3분 미사용)
- 메모리 사용량 최적화
"""
import time
import asyncio
import threading
from typing import Dict, Set, List, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .market_data_models import (
    DataResponse, Priority, CollectionStatusRecord
)

logger = create_component_logger("RealtimeDataManager")


class SubscriptionState(Enum):
    """구독 상태"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class SubscriptionRecord:
    """구독 기록"""
    symbols: Set[str]
    state: SubscriptionState
    created_at: datetime
    last_activity: datetime
    callback: Optional[Callable] = None
    error_count: int = 0
    auto_unsubscribe_minutes: int = 3

    def is_expired(self) -> bool:
        """자동 해제 시간 확인"""
        if self.auto_unsubscribe_minutes <= 0:
            return False

        timeout = timedelta(minutes=self.auto_unsubscribe_minutes)
        return datetime.now() - self.last_activity > timeout

    def update_activity(self) -> None:
        """활동 시간 업데이트"""
        self.last_activity = datetime.now()


@dataclass
class CandleUpdateRecord:
    """캔들 업데이트 기록"""
    symbol: str
    candle_type: str  # "1m", "5m", "1h", "1d"
    timestamp: datetime
    last_candle_data: Dict[str, Any]
    update_count: int = 0

    def should_replace_candle(self, new_candle: Dict[str, Any]) -> bool:
        """기존 캔들 교체 여부 판단"""
        if not self.last_candle_data:
            return True

        # 같은 분봉 시간인지 확인
        old_time = self.last_candle_data.get('candle_date_time_kst')
        new_time = new_candle.get('candle_date_time_kst')

        return old_time == new_time


class WebSocketSubscriptionManager:
    """WebSocket 구독 관리자"""

    def __init__(self):
        self._subscriptions: Dict[str, SubscriptionRecord] = {}
        self._symbol_to_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self._active_websockets: Dict[str, Any] = {}
        self._subscription_callbacks: Dict[str, Callable] = {}
        self._lock = threading.RLock()

        # 자동 정리 설정
        self._cleanup_interval = 60  # 60초마다 정리
        self._last_cleanup = time.time()

        logger.info("WebSocket 구독 관리자 초기화")

    def create_subscription(
        self,
        subscription_id: str,
        symbols: List[str],
        callback: Optional[Callable] = None,
        auto_unsubscribe_minutes: int = 3
    ) -> bool:
        """새 구독 생성"""
        with self._lock:
            if subscription_id in self._subscriptions:
                logger.warning(f"구독 ID 중복: {subscription_id}")
                return False

            symbol_set = set(symbols)

            # 구독 기록 생성
            subscription = SubscriptionRecord(
                symbols=symbol_set,
                state=SubscriptionState.PENDING,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                callback=callback,
                auto_unsubscribe_minutes=auto_unsubscribe_minutes
            )

            self._subscriptions[subscription_id] = subscription

            # 심볼별 구독 매핑
            for symbol in symbol_set:
                self._symbol_to_subscriptions[symbol].add(subscription_id)

            if callback:
                self._subscription_callbacks[subscription_id] = callback

            logger.info(f"구독 생성: {subscription_id}, 심볼 {len(symbols)}개, 자동해제 {auto_unsubscribe_minutes}분")
            return True

    def activate_subscription(self, subscription_id: str, websocket_connection: Any) -> bool:
        """구독 활성화"""
        with self._lock:
            if subscription_id not in self._subscriptions:
                logger.error(f"구독 ID 없음: {subscription_id}")
                return False

            subscription = self._subscriptions[subscription_id]
            subscription.state = SubscriptionState.ACTIVE
            subscription.update_activity()

            self._active_websockets[subscription_id] = websocket_connection

            logger.info(f"구독 활성화: {subscription_id}")
            return True

    def update_subscription_activity(self, subscription_id: str) -> None:
        """구독 활동 업데이트"""
        with self._lock:
            if subscription_id in self._subscriptions:
                self._subscriptions[subscription_id].update_activity()

    def get_subscriptions_for_symbol(self, symbol: str) -> List[str]:
        """심볼에 대한 활성 구독 목록"""
        with self._lock:
            active_subscriptions = []

            for sub_id in self._symbol_to_subscriptions.get(symbol, set()):
                if sub_id in self._subscriptions:
                    subscription = self._subscriptions[sub_id]
                    if subscription.state == SubscriptionState.ACTIVE:
                        active_subscriptions.append(sub_id)

            return active_subscriptions

    def close_subscription(self, subscription_id: str, reason: str = "manual") -> bool:
        """구독 종료"""
        with self._lock:
            if subscription_id not in self._subscriptions:
                logger.warning(f"종료할 구독 없음: {subscription_id}")
                return False

            subscription = self._subscriptions[subscription_id]
            subscription.state = SubscriptionState.CLOSED

            # WebSocket 연결 종료
            if subscription_id in self._active_websockets:
                try:
                    websocket = self._active_websockets[subscription_id]
                    if hasattr(websocket, 'close'):
                        websocket.close()
                except Exception as e:
                    logger.error(f"WebSocket 종료 오류: {e}")

                del self._active_websockets[subscription_id]

            # 콜백 제거
            if subscription_id in self._subscription_callbacks:
                del self._subscription_callbacks[subscription_id]

            # 심볼 매핑 제거
            for symbol in subscription.symbols:
                self._symbol_to_subscriptions[symbol].discard(subscription_id)

            # 구독 기록 제거
            del self._subscriptions[subscription_id]

            logger.info(f"구독 종료: {subscription_id}, 사유: {reason}")
            return True

    def cleanup_expired_subscriptions(self) -> int:
        """만료된 구독 정리"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return 0

        expired_count = 0

        with self._lock:
            expired_subscriptions = []

            for sub_id, subscription in self._subscriptions.items():
                if subscription.is_expired():
                    expired_subscriptions.append(sub_id)

            for sub_id in expired_subscriptions:
                if self.close_subscription(sub_id, "auto_expire"):
                    expired_count += 1

        self._last_cleanup = current_time

        if expired_count > 0:
            logger.info(f"만료된 구독 {expired_count}개 정리")

        return expired_count

    def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계"""
        with self._lock:
            total_subscriptions = len(self._subscriptions)
            active_subscriptions = sum(
                1 for s in self._subscriptions.values()
                if s.state == SubscriptionState.ACTIVE
            )
            total_symbols = len(self._symbol_to_subscriptions)

            return {
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'total_symbols': total_symbols,
                'active_websockets': len(self._active_websockets),
                'state_distribution': {
                    state.value: sum(
                        1 for s in self._subscriptions.values()
                        if s.state == state
                    )
                    for state in SubscriptionState
                }
            }


class RealtimeCandleDeduplicator:
    """실시간 캔들 중복 제거"""

    def __init__(self, max_history_per_symbol: int = 50):
        self.max_history_per_symbol = max_history_per_symbol
        self._candle_history: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=max_history_per_symbol))
        )
        self._latest_candles: Dict[str, CandleUpdateRecord] = {}
        self._lock = threading.RLock()

        logger.info(f"실시간 캔들 중복 제거기 초기화: 심볼당 최대 {max_history_per_symbol}개 이력")

    def process_realtime_candle(
        self,
        symbol: str,
        candle_type: str,
        candle_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """실시간 캔들 처리 및 중복 제거"""
        with self._lock:
            key = f"{symbol}_{candle_type}"

            # 기존 기록 확인
            if key in self._latest_candles:
                update_record = self._latest_candles[key]

                # 같은 분봉 시간인지 확인하여 교체 여부 결정
                if update_record.should_replace_candle(candle_data):
                    # 기존 캔들 교체
                    update_record.last_candle_data = candle_data
                    update_record.update_count += 1
                    update_record.timestamp = datetime.now()

                    logger.debug(f"캔들 교체: {symbol} {candle_type}, 업데이트 #{update_record.update_count}")

                    return {
                        'symbol': symbol,
                        'candle_type': candle_type,
                        'data': candle_data,
                        'action': 'replace',
                        'update_count': update_record.update_count
                    }
                else:
                    # 새로운 캔들
                    self._add_new_candle(symbol, candle_type, candle_data)

                    return {
                        'symbol': symbol,
                        'candle_type': candle_type,
                        'data': candle_data,
                        'action': 'new',
                        'update_count': 1
                    }
            else:
                # 첫 번째 캔들
                self._add_new_candle(symbol, candle_type, candle_data)

                return {
                    'symbol': symbol,
                    'candle_type': candle_type,
                    'data': candle_data,
                    'action': 'first',
                    'update_count': 1
                }

    def _add_new_candle(self, symbol: str, candle_type: str, candle_data: Dict[str, Any]) -> None:
        """새 캔들 추가"""
        key = f"{symbol}_{candle_type}"

        # 이력에 추가
        self._candle_history[symbol][candle_type].append(candle_data)

        # 최신 기록 업데이트
        self._latest_candles[key] = CandleUpdateRecord(
            symbol=symbol,
            candle_type=candle_type,
            timestamp=datetime.now(),
            last_candle_data=candle_data,
            update_count=1
        )

    def get_candle_history(self, symbol: str, candle_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """캔들 이력 조회"""
        with self._lock:
            history = self._candle_history[symbol][candle_type]
            return list(history)[-limit:] if history else []

    def get_latest_candle(self, symbol: str, candle_type: str) -> Optional[Dict[str, Any]]:
        """최신 캔들 조회"""
        with self._lock:
            key = f"{symbol}_{candle_type}"
            if key in self._latest_candles:
                return self._latest_candles[key].last_candle_data
            return None

    def cleanup_old_data(self, max_age_hours: int = 24) -> int:
        """오래된 데이터 정리"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_count = 0

            expired_keys = []
            for key, record in self._latest_candles.items():
                if record.timestamp < cutoff_time:
                    expired_keys.append(key)

            for key in expired_keys:
                symbol, candle_type = key.split('_', 1)

                # 이력 정리
                if symbol in self._candle_history and candle_type in self._candle_history[symbol]:
                    del self._candle_history[symbol][candle_type]

                # 최신 기록 정리
                del self._latest_candles[key]
                cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"오래된 캔들 데이터 {cleaned_count}개 정리")

            return cleaned_count

    def get_deduplication_stats(self) -> Dict[str, Any]:
        """중복 제거 통계"""
        with self._lock:
            total_symbols = len(set(
                record.symbol for record in self._latest_candles.values()
            ))

            total_candle_types = len(set(
                record.candle_type for record in self._latest_candles.values()
            ))

            total_updates = sum(
                record.update_count for record in self._latest_candles.values()
            )

            return {
                'tracked_symbols': total_symbols,
                'tracked_candle_types': total_candle_types,
                'total_candle_streams': len(self._latest_candles),
                'total_updates_processed': total_updates,
                'memory_usage': {
                    'latest_records': len(self._latest_candles),
                    'history_entries': sum(
                        len(candle_types) for candle_types in self._candle_history.values()
                    )
                }
            }


class RealtimeDataManager:
    """실시간 데이터 관리자 - Layer 2 메인 클래스"""

    def __init__(self):
        self.subscription_manager = WebSocketSubscriptionManager()
        self.candle_deduplicator = RealtimeCandleDeduplicator()

        # 통합 콜백 관리
        self._data_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()

        # 자동 정리 스케줄러
        self._cleanup_interval = 300  # 5분마다 정리
        self._last_cleanup = time.time()

        logger.info("RealtimeDataManager 통합 시스템 초기화")

    def subscribe_to_symbols(
        self,
        subscription_id: str,
        symbols: List[str],
        data_types: Optional[List[str]] = None,
        callback: Optional[Callable] = None
    ) -> bool:
        """심볼 구독"""
        data_types = data_types or ["ticker"]

        # WebSocket 구독 생성
        success = self.subscription_manager.create_subscription(
            subscription_id, symbols, callback
        )

        if success and callback:
            # 데이터 타입별 콜백 등록
            for data_type in data_types:
                self._data_callbacks[data_type].append(callback)

        return success

    def handle_realtime_data(self, data_type: str, symbol: str, data: Dict[str, Any]) -> None:
        """실시간 데이터 처리"""
        # 구독 활동 업데이트
        subscriptions = self.subscription_manager.get_subscriptions_for_symbol(symbol)
        for sub_id in subscriptions:
            self.subscription_manager.update_subscription_activity(sub_id)

        # 캔들 데이터 중복 제거 처리
        if data_type in ["1m", "5m", "15m", "1h", "4h", "1d"]:
            processed_candle = self.candle_deduplicator.process_realtime_candle(
                symbol, data_type, data
            )

            # 콜백 실행
            self._execute_callbacks("candle", {
                'symbol': symbol,
                'candle_type': data_type,
                'processed_data': processed_candle
            })
        else:
            # 일반 데이터 콜백 실행
            self._execute_callbacks(data_type, {
                'symbol': symbol,
                'data': data
            })

    def _execute_callbacks(self, data_type: str, payload: Dict[str, Any]) -> None:
        """콜백 실행"""
        with self._lock:
            callbacks = self._data_callbacks.get(data_type, [])

            for callback in callbacks:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"콜백 실행 오류 ({data_type}): {e}")

    def unsubscribe_symbols(self, subscription_id: str) -> bool:
        """구독 해제"""
        return self.subscription_manager.close_subscription(subscription_id, "manual")

    def cleanup_if_needed(self) -> None:
        """필요시 자동 정리"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup()
            self._last_cleanup = current_time

    def _cleanup(self) -> None:
        """정리 작업 실행"""
        # 만료된 구독 정리
        expired_subs = self.subscription_manager.cleanup_expired_subscriptions()

        # 오래된 캔들 데이터 정리
        cleaned_candles = self.candle_deduplicator.cleanup_old_data()

        if expired_subs > 0 or cleaned_candles > 0:
            logger.info(f"실시간 데이터 정리: 구독 {expired_subs}개, 캔들 {cleaned_candles}개")

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 실시간 통계"""
        self.cleanup_if_needed()

        subscription_stats = self.subscription_manager.get_subscription_stats()
        deduplication_stats = self.candle_deduplicator.get_deduplication_stats()

        return {
            'subscriptions': subscription_stats,
            'candle_deduplication': deduplication_stats,
            'active_callbacks': {
                data_type: len(callbacks)
                for data_type, callbacks in self._data_callbacks.items()
            },
            'last_cleanup': datetime.fromtimestamp(self._last_cleanup).isoformat()
        }
