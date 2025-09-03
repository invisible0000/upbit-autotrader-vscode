"""
WebSocket v6.2 리얼타임 스트림 중심 구독 관리자
=============================================

핵심 개념:
- 관리되어야 하는 현 구독상태는 상항 리얼타임 스트림 목록
- 스냅샷 요청이 있을때 관리해서 통합하여 메세지를 보내야 함
- SIMPLE 형식은 일방향 변환만 (SIMPLE→DEFAULT)
"""

import asyncio
import weakref
from datetime import datetime
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass

from upbit_auto_trading.domain.entities.trading.trading_data import DataType
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.support.websocket_types import (
    ComponentSubscription,
    SubscriptionSpec,
    SubscriptionChange,
    SubscriptionComplexity,
    WebSocketType
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class RealtimeStreamState:
    """리얼타임 스트림 상태"""
    ws_type: WebSocketType
    data_type: DataType
    symbols: Set[str]
    components: Set[str]  # 이 스트림을 구독한 컴포넌트들
    created_at: datetime
    last_updated: datetime


class RealtimeStreamManager:
    """v6.2 리얼타임 스트림 중심 구독 관리자"""

    def __init__(self):
        self.logger = create_component_logger("RealtimeStreamManager")

        # 동시성 제어
        self._lock = asyncio.Lock()

        # 🎯 핵심: 리얼타임 스트림 상태 (기본 관리 대상)
        self._realtime_streams: Dict[WebSocketType, Dict[DataType, RealtimeStreamState]] = {
            WebSocketType.PUBLIC: {},
            WebSocketType.PRIVATE: {}
        }

        # 📸 임시: 스냅샷 요청 큐 (일시적)
        self._snapshot_requests: Dict[WebSocketType, Dict[DataType, Set[str]]] = {
            WebSocketType.PUBLIC: {},
            WebSocketType.PRIVATE: {}
        }

        # 컴포넌트별 구독 추적 (WeakRef)
        self._component_subscriptions: Dict[str, ComponentSubscription] = {}
        self._component_refs: Dict[str, weakref.ref] = {}

        # 변경 알림 콜백
        self._change_callbacks: List[Callable[[Dict[DataType, SubscriptionChange]], None]] = []

        # 성능 메트릭
        self._metrics = {
            'total_realtime_streams': 0,
            'total_snapshot_requests': 0,
            'stream_updates': 0,
            'last_snapshot_batch_at': None,
            'efficiency_score': 1.0
        }

        self.logger.info("리얼타임 스트림 관리자 v6.2 초기화 완료")

    # ================================================================
    # 리얼타임 스트림 관리 (핵심 기능)
    # ================================================================

    async def add_realtime_stream(self, ws_type: WebSocketType, data_type: DataType,
                                  symbols: Set[str], component_id: str) -> None:
        """리얼타임 스트림 추가/확장"""
        async with self._lock:
            now = datetime.now()

            if data_type not in self._realtime_streams[ws_type]:
                # 새 스트림 생성
                self._realtime_streams[ws_type][data_type] = RealtimeStreamState(
                    ws_type=ws_type,
                    data_type=data_type,
                    symbols=symbols.copy(),
                    components={component_id},
                    created_at=now,
                    last_updated=now
                )
                self.logger.info(f"새 리얼타임 스트림 생성: {ws_type.value}/{data_type.value} ({len(symbols)}개 심볼)")
            else:
                # 기존 스트림 확장
                stream = self._realtime_streams[ws_type][data_type]
                new_symbols = symbols - stream.symbols
                stream.symbols.update(symbols)
                stream.components.add(component_id)
                stream.last_updated = now

                if new_symbols:
                    self.logger.info(f"리얼타임 스트림 확장: {ws_type.value}/{data_type.value} (+{len(new_symbols)}개)")

            self._update_metrics()

    async def remove_realtime_stream(self, ws_type: WebSocketType, data_type: DataType,
                                     symbols: Set[str], component_id: str) -> None:
        """리얼타임 스트림 제거/축소"""
        async with self._lock:
            if data_type not in self._realtime_streams[ws_type]:
                return

            stream = self._realtime_streams[ws_type][data_type]
            stream.components.discard(component_id)

            # 컴포넌트가 없으면 해당 심볼들 제거
            if not stream.components:
                stream.symbols -= symbols

                # 스트림이 완전히 비었으면 삭제
                if not stream.symbols:
                    del self._realtime_streams[ws_type][data_type]
                    self.logger.info(f"리얼타임 스트림 삭제: {ws_type.value}/{data_type.value}")
                else:
                    stream.last_updated = datetime.now()
                    self.logger.info(f"리얼타임 스트림 축소: {ws_type.value}/{data_type.value} (-{len(symbols)}개)")

            self._update_metrics()

    def get_realtime_streams(self, ws_type: WebSocketType) -> Dict[DataType, Set[str]]:
        """현재 리얼타임 스트림 목록 반환"""
        return {
            data_type: stream.symbols.copy()
            for data_type, stream in self._realtime_streams[ws_type].items()
        }

    def get_all_realtime_symbols(self, ws_type: WebSocketType, data_type: DataType) -> Set[str]:
        """특정 타입의 모든 리얼타임 스트림 심볼"""
        if data_type in self._realtime_streams[ws_type]:
            return self._realtime_streams[ws_type][data_type].symbols.copy()
        return set()

    # ================================================================
    # 스냅샷 요청 관리 (임시 상태)
    # ================================================================

    async def add_snapshot_request(self, ws_type: WebSocketType, data_type: DataType,
                                   symbols: Set[str]) -> None:
        """임시 스냅샷 요청 추가"""
        async with self._lock:
            if data_type not in self._snapshot_requests[ws_type]:
                self._snapshot_requests[ws_type][data_type] = set()

            self._snapshot_requests[ws_type][data_type].update(symbols)
            self._metrics['total_snapshot_requests'] = self._count_snapshot_requests()
            self._metrics['last_snapshot_batch_at'] = datetime.now().isoformat()

            self.logger.debug(f"스냅샷 요청 추가: {ws_type.value}/{data_type.value} ({len(symbols)}개)")

    async def consume_snapshot_requests(self, ws_type: WebSocketType, data_type: DataType) -> Set[str]:
        """스냅샷 요청 소비 및 클리어"""
        async with self._lock:
            symbols = self._snapshot_requests[ws_type].get(data_type, set()).copy()
            if data_type in self._snapshot_requests[ws_type]:
                del self._snapshot_requests[ws_type][data_type]

            self._metrics['total_snapshot_requests'] = self._count_snapshot_requests()

            if symbols:
                self.logger.debug(f"스냅샷 요청 처리: {ws_type.value}/{data_type.value} ({len(symbols)}개)")

            return symbols

    def get_pending_snapshots(self, ws_type: WebSocketType) -> Dict[DataType, Set[str]]:
        """대기 중인 스냅샷 요청 목록"""
        return {
            data_type: symbols.copy()
            for data_type, symbols in self._snapshot_requests[ws_type].items()
        }

    # ================================================================
    # 통합 메시지 생성 (리얼타임 + 스냅샷)
    # ================================================================

    async def create_unified_subscription_message(self, ws_type: WebSocketType, data_type: DataType) -> Dict[str, Set[str]]:
        """리얼타임 스트림과 스냅샷 요청을 통합한 구독 메시지 생성"""
        async with self._lock:
            # 리얼타임 스트림 심볼
            realtime_symbols = self.get_all_realtime_symbols(ws_type, data_type)

            # 스냅샷 요청 심볼 (일회성 소비)
            snapshot_symbols = await self.consume_snapshot_requests(ws_type, data_type)

            # 통합 (리얼타임 + 스냅샷)
            all_symbols = realtime_symbols | snapshot_symbols

            if not all_symbols:
                return {}

            result = {
                'realtime': realtime_symbols,
                'snapshot': snapshot_symbols,
                'combined': all_symbols
            }

            self.logger.debug(
                f"통합 구독 메시지 생성: {ws_type.value}/{data_type.value} "
                f"(리얼타임: {len(realtime_symbols)}, 스냅샷: {len(snapshot_symbols)})"
            )

            return result

    # ================================================================
    # 컴포넌트 관리 (기존 v6.1 호환성)
    # ================================================================

    async def register_component(self, component_id: str, subscription: ComponentSubscription,
                                 component_ref: Any) -> None:
        """컴포넌트 등록"""
        async with self._lock:
            self._component_subscriptions[component_id] = subscription

            # WeakRef로 자동 정리
            def cleanup():
                asyncio.create_task(self._cleanup_component(component_id))

            self._component_refs[component_id] = weakref.ref(component_ref, cleanup)

            # 구독 스펙에 따라 리얼타임 스트림 추가
            for spec in subscription.subscription_specs:
                await self.add_realtime_stream(
                    spec.ws_type, spec.data_type, spec.symbols, component_id
                )

            self.logger.info(f"컴포넌트 등록: {component_id} ({len(subscription.subscription_specs)}개 스펙)")

    async def unregister_component(self, component_id: str) -> None:
        """컴포넌트 등록 해제"""
        await self._cleanup_component(component_id)

    async def _cleanup_component(self, component_id: str) -> None:
        """컴포넌트 정리"""
        async with self._lock:
            if component_id not in self._component_subscriptions:
                return

            subscription = self._component_subscriptions[component_id]

            # 관련 리얼타임 스트림 제거
            for spec in subscription.subscription_specs:
                await self.remove_realtime_stream(
                    spec.ws_type, spec.data_type, spec.symbols, component_id
                )

            # 정리
            del self._component_subscriptions[component_id]
            if component_id in self._component_refs:
                del self._component_refs[component_id]

            self.logger.info(f"컴포넌트 정리 완료: {component_id}")

    # ================================================================
    # 상태 조회 및 분석
    # ================================================================

    def get_stream_summary(self) -> Dict[str, Any]:
        """스트림 상태 요약"""
        public_streams = len(self._realtime_streams[WebSocketType.PUBLIC])
        private_streams = len(self._realtime_streams[WebSocketType.PRIVATE])

        total_symbols = sum(
            len(stream.symbols)
            for streams in self._realtime_streams.values()
            for stream in streams.values()
        )

        return {
            'public_streams': public_streams,
            'private_streams': private_streams,
            'total_symbols': total_symbols,
            'active_components': len(self._component_subscriptions),
            'pending_snapshots': self._count_snapshot_requests(),
            'metrics': self._metrics.copy()
        }

    def analyze_stream_complexity(self) -> List[SubscriptionComplexity]:
        """스트림 복잡성 분석"""
        complexities = []
        symbol_analysis = {}

        # 심볼별 데이터 타입 수집
        for ws_type, streams in self._realtime_streams.items():
            for data_type, stream in streams.items():
                for symbol in stream.symbols:
                    if symbol not in symbol_analysis:
                        symbol_analysis[symbol] = {'types': set(), 'components': set()}
                    symbol_analysis[symbol]['types'].add(data_type)
                    symbol_analysis[symbol]['components'].update(stream.components)

        # 복잡성 계산
        for symbol, info in symbol_analysis.items():
            if len(info['types']) > 1:
                complexity_score = min(1.0, len(info['types']) / 5.0)

                complexities.append(SubscriptionComplexity(
                    symbol=symbol,
                    data_types=info['types'],
                    components=info['components'],
                    complexity_score=complexity_score,
                    optimization_suggestion="optimize_stream_consolidation"
                ))

        return complexities

    # ================================================================
    # 유틸리티 메서드
    # ================================================================

    def _update_metrics(self) -> None:
        """메트릭 업데이트"""
        self._metrics['total_realtime_streams'] = sum(
            len(streams) for streams in self._realtime_streams.values()
        )
        self._metrics['stream_updates'] += 1

        # 효율성 점수 계산
        complexities = self.analyze_stream_complexity()
        complexity_penalty = len(complexities) * 0.1
        self._metrics['efficiency_score'] = max(0.0, 1.0 - complexity_penalty)

    def _count_snapshot_requests(self) -> int:
        """스냅샷 요청 수 계산"""
        return sum(
            len(symbols) for requests in self._snapshot_requests.values()
            for symbols in requests.values()
        )

    async def clear_all_streams(self) -> None:
        """모든 스트림 클리어 (테스트/재시작용)"""
        async with self._lock:
            self._realtime_streams[WebSocketType.PUBLIC].clear()
            self._realtime_streams[WebSocketType.PRIVATE].clear()
            self._snapshot_requests[WebSocketType.PUBLIC].clear()
            self._snapshot_requests[WebSocketType.PRIVATE].clear()
            self._component_subscriptions.clear()
            self._component_refs.clear()
            self._update_metrics()

            self.logger.info("모든 스트림 상태 클리어 완료")

    # ================================================================
    # 변경 알림 시스템
    # ================================================================

    def add_change_callback(self, callback: Callable[[Dict[DataType, SubscriptionChange]], None]) -> None:
        """변경 알림 콜백 등록"""
        self._change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable[[Dict[DataType, SubscriptionChange]], None]) -> None:
        """변경 알림 콜백 제거"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    async def _notify_changes(self, changes: Dict[DataType, SubscriptionChange]) -> None:
        """변경사항 알림"""
        for callback in self._change_callbacks:
            try:
                callback(changes)
            except Exception as e:
                self.logger.error(f"변경 알림 콜백 오류: {e}")
