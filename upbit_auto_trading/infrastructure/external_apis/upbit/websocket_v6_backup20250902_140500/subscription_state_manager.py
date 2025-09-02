"""
구독 상태 관리자
===============

WebSocket v6의 핵심 구독 상태 통합 관리
여러 컴포넌트의 구독 요청을 취합하여 최적화된 단일 구독 상태 생성

핵심 기능:
- 구독 요청 통합 (Union of all component requests)
- 원자적 상태 업데이트 (Race condition 방지)
- WeakRef 기반 자동 정리
- 구독 충돌 감지 및 해결
"""

import asyncio
import time
import weakref
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .types import (
    DataType, SubscriptionSpec, ComponentSubscription, WebSocketType,
    BaseWebSocketEvent, PerformanceMetrics
)


@dataclass
class ActiveSubscription:
    """활성 구독 정보"""
    data_type: DataType
    symbols: Set[str]                 # 통합된 심볼 목록
    components: Set[str]              # 구독 중인 컴포넌트들
    callbacks: List[Callable]        # 모든 콜백 목록
    created_at: float = field(default_factory=time.monotonic)
    last_updated: float = field(default_factory=time.monotonic)
    message_count: int = 0
    error_count: int = 0


@dataclass
class SubscriptionChange:
    """구독 변경 정보"""
    added_symbols: Set[str] = field(default_factory=set)
    removed_symbols: Set[str] = field(default_factory=set)
    added_components: Set[str] = field(default_factory=set)
    removed_components: Set[str] = field(default_factory=set)
    is_empty: bool = True

    def __post_init__(self):
        self.is_empty = not (
            self.added_symbols
            or self.removed_symbols
            or self.added_components
            or self.removed_components
        )


class SubscriptionStateManager:
    """구독 상태 통합 관리자"""

    def __init__(self):
        self.logger = create_component_logger("SubscriptionStateManager")

        # 구독 상태 (Thread-safe)
        self._lock = asyncio.Lock()

        # 컴포넌트별 구독 (WeakRef로 자동 정리)
        self._component_subscriptions: Dict[str, ComponentSubscription] = {}
        self._component_refs: Dict[str, weakref.ref] = {}

        # 통합된 활성 구독
        self._active_subscriptions: Dict[DataType, ActiveSubscription] = {}

        # Public/Private 분리
        self._public_subscriptions: Dict[DataType, ActiveSubscription] = {}
        self._private_subscriptions: Dict[DataType, ActiveSubscription] = {}

        # 성능 메트릭
        self._performance_metrics = PerformanceMetrics()

        # 변경 이벤트 콜백
        self._change_callbacks: List[Callable[[Dict[DataType, SubscriptionChange]], None]] = []

        self.logger.info("구독 상태 관리자 초기화 완료")

    async def register_component(
        self,
        component_id: str,
        subscription_specs: List[SubscriptionSpec],
        cleanup_ref: Any = None
    ) -> Dict[DataType, SubscriptionChange]:
        """
        컴포넌트 구독 등록

        Args:
            component_id: 컴포넌트 식별자
            subscription_specs: 구독 규격 목록
            cleanup_ref: 자동 정리를 위한 참조 객체

        Returns:
            Dict[DataType, SubscriptionChange]: 데이터 타입별 변경사항
        """
        async with self._lock:
            self.logger.debug(f"컴포넌트 구독 등록: {component_id}, 스펙 {len(subscription_specs)}개")

            # 기존 구독 제거 (재등록 시)
            if component_id in self._component_subscriptions:
                await self._unregister_component_internal(component_id)

            # 컴포넌트 구독 생성 (디버깅용 로깅 추가)
            self.logger.debug(f"ComponentSubscription 생성 - component_id: {component_id}")
            self.logger.debug(f"subscription_specs: {subscription_specs}")

            try:
                component_subscription = ComponentSubscription(
                    component_id=component_id,
                    subscription_specs=subscription_specs
                )
            except Exception as e:
                self.logger.error(f"ComponentSubscription 생성 실패: {e}")
                self.logger.error(f"전달된 매개변수 - component_id: {component_id}, subscription_specs: {subscription_specs}")
                raise

            self._component_subscriptions[component_id] = component_subscription

            # WeakRef 등록 (자동 정리)
            if cleanup_ref is not None:
                # cleanup_ref가 이미 WeakRef인지 확인
                if isinstance(cleanup_ref, weakref.ReferenceType):
                    # 이미 WeakRef인 경우 그대로 저장
                    self._component_refs[component_id] = cleanup_ref
                    self.logger.debug(f"기존 WeakRef 저장: {cleanup_ref}")
                else:
                    # 일반 객체인 경우 WeakRef 생성
                    def cleanup_callback(ref):
                        asyncio.create_task(self._cleanup_component(component_id))

                    self._component_refs[component_id] = weakref.ref(cleanup_ref, cleanup_callback)
                    self.logger.debug(f"새 WeakRef 생성: {self._component_refs[component_id]}")

            # 구독 상태 재계산
            changes = await self._recalculate_subscriptions()

            # 성능 메트릭 업데이트
            self._performance_metrics.active_components = len(self._component_subscriptions)
            self._performance_metrics.active_subscriptions = len(self._active_subscriptions)

            self.logger.info(f"컴포넌트 {component_id} 구독 등록 완료")
            return changes

    async def unregister_component(self, component_id: str) -> Dict[DataType, SubscriptionChange]:
        """
        컴포넌트 구독 해제

        Args:
            component_id: 컴포넌트 식별자

        Returns:
            Dict[DataType, SubscriptionChange]: 데이터 타입별 변경사항
        """
        async with self._lock:
            return await self._unregister_component_internal(component_id)

    async def _unregister_component_internal(self, component_id: str) -> Dict[DataType, SubscriptionChange]:
        """내부 구독 해제 로직 (락 없이)"""
        if component_id not in self._component_subscriptions:
            return {}

        self.logger.debug(f"컴포넌트 구독 해제: {component_id}")

        # 컴포넌트 제거
        del self._component_subscriptions[component_id]

        # WeakRef 정리
        if component_id in self._component_refs:
            del self._component_refs[component_id]

        # 구독 상태 재계산
        changes = await self._recalculate_subscriptions()

        # 성능 메트릭 업데이트
        self._performance_metrics.active_components = len(self._component_subscriptions)
        self._performance_metrics.active_subscriptions = len(self._active_subscriptions)

        self.logger.info(f"컴포넌트 {component_id} 구독 해제 완료")
        return changes

    async def _cleanup_component(self, component_id: str) -> None:
        """WeakRef 콜백을 통한 자동 정리"""
        self.logger.debug(f"컴포넌트 자동 정리: {component_id}")
        try:
            await self.unregister_component(component_id)
        except Exception as e:
            self.logger.error(f"컴포넌트 자동 정리 실패: {component_id}, 오류: {e}")

    async def _recalculate_subscriptions(self) -> Dict[DataType, SubscriptionChange]:
        """구독 상태 재계산 (원자적 연산)"""
        self.logger.debug("구독 상태 재계산 시작")

        # 이전 상태 백업
        previous_subscriptions = dict(self._active_subscriptions)

        # 새로운 통합 상태 계산
        new_subscriptions: Dict[DataType, ActiveSubscription] = {}

        # 컴포넌트별 구독을 데이터 타입별로 통합
        grouped_specs: Dict[DataType, List[tuple]] = defaultdict(list)

        for component_id, component_sub in self._component_subscriptions.items():
            for spec in component_sub.subscription_specs:
                grouped_specs[spec.data_type].append((component_id, spec))

        # 데이터 타입별로 통합 구독 생성
        for data_type, component_specs in grouped_specs.items():
            symbols = set()
            components = set()
            callbacks = []

            for component_id, spec in component_specs:
                # 심볼 통합
                if spec.symbols:
                    symbols.update(spec.symbols)
                if spec.markets:  # Private 전용
                    symbols.update(spec.markets)

                components.add(component_id)
                callbacks.append(spec.callback)

            # 활성 구독 생성
            # Private 데이터는 심볼 없이도 유효 (myOrder, myAsset)
            if callbacks and (symbols or data_type.is_private()):
                active_sub = ActiveSubscription(
                    data_type=data_type,
                    symbols=symbols,
                    components=components,
                    callbacks=callbacks
                )
                new_subscriptions[data_type] = active_sub

        # 변경사항 계산
        changes = self._calculate_changes(previous_subscriptions, new_subscriptions)

        # 상태 업데이트
        self._active_subscriptions = new_subscriptions

        # Public/Private 분리
        self._separate_public_private_subscriptions()

        self.logger.debug(f"구독 상태 재계산 완료: {len(new_subscriptions)}개 활성 구독")

        # 변경 이벤트 발생
        if changes:
            await self._notify_subscription_changes(changes)

        return changes

    def _calculate_changes(
        self,
        previous: Dict[DataType, ActiveSubscription],
        current: Dict[DataType, ActiveSubscription]
    ) -> Dict[DataType, SubscriptionChange]:
        """구독 변경사항 계산"""
        changes: Dict[DataType, SubscriptionChange] = {}

        # 모든 데이터 타입 검사
        all_types = set(previous.keys()) | set(current.keys())

        for data_type in all_types:
            prev_sub = previous.get(data_type)
            curr_sub = current.get(data_type)

            change = SubscriptionChange()

            if prev_sub is None and curr_sub is not None:
                # 새로운 구독
                change.added_symbols = curr_sub.symbols.copy()
                change.added_components = curr_sub.components.copy()

            elif prev_sub is not None and curr_sub is None:
                # 구독 제거
                change.removed_symbols = prev_sub.symbols.copy()
                change.removed_components = prev_sub.components.copy()

            elif prev_sub is not None and curr_sub is not None:
                # 구독 변경
                change.added_symbols = curr_sub.symbols - prev_sub.symbols
                change.removed_symbols = prev_sub.symbols - curr_sub.symbols
                change.added_components = curr_sub.components - prev_sub.components
                change.removed_components = prev_sub.components - curr_sub.components

            # 변경사항이 있는 경우만 저장
            if not change.is_empty:
                change.is_empty = False
                changes[data_type] = change

        return changes

    def _separate_public_private_subscriptions(self) -> None:
        """Public/Private 구독 분리"""
        self._public_subscriptions.clear()
        self._private_subscriptions.clear()

        for data_type, subscription in self._active_subscriptions.items():
            if data_type in [DataType.MYORDER, DataType.MYASSET]:
                self._private_subscriptions[data_type] = subscription
            else:
                self._public_subscriptions[data_type] = subscription

    async def _notify_subscription_changes(self, changes: Dict[DataType, SubscriptionChange]) -> None:
        """구독 변경 이벤트 알림"""
        for callback in self._change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(changes)
                else:
                    callback(changes)
            except Exception as e:
                self.logger.error(f"구독 변경 콜백 오류: {e}")

    # =============================================================================
    # 조회 메서드
    # =============================================================================

    def get_active_subscriptions(self, connection_type: Optional[WebSocketType] = None) -> Dict[DataType, ActiveSubscription]:
        """활성 구독 목록 조회"""
        if connection_type == WebSocketType.PUBLIC:
            return dict(self._public_subscriptions)
        elif connection_type == WebSocketType.PRIVATE:
            return dict(self._private_subscriptions)
        else:
            return dict(self._active_subscriptions)

    def get_component_subscriptions(self) -> Dict[str, ComponentSubscription]:
        """컴포넌트별 구독 목록 조회"""
        return dict(self._component_subscriptions)

    def get_symbols_for_data_type(self, data_type: DataType) -> Set[str]:
        """특정 데이터 타입의 심볼 목록 조회"""
        if subscription := self._active_subscriptions.get(data_type):
            return subscription.symbols.copy()
        return set()

    def get_callbacks_for_data_type(self, data_type: DataType) -> List[Callable]:
        """특정 데이터 타입의 콜백 목록 조회"""
        if subscription := self._active_subscriptions.get(data_type):
            return subscription.callbacks.copy()
        return []

    def is_symbol_subscribed(self, symbol: str, data_type: Optional[DataType] = None) -> bool:
        """심볼이 구독 중인지 확인"""
        if data_type:
            subscription = self._active_subscriptions.get(data_type)
            return subscription is not None and symbol in subscription.symbols

        # 모든 데이터 타입에서 검색
        for subscription in self._active_subscriptions.values():
            if symbol in subscription.symbols:
                return True
        return False

    def get_subscription_summary(self) -> Dict[str, Any]:
        """구독 상태 요약"""
        return {
            'total_components': len(self._component_subscriptions),
            'total_subscriptions': len(self._active_subscriptions),
            'public_subscriptions': len(self._public_subscriptions),
            'private_subscriptions': len(self._private_subscriptions),
            'data_type_breakdown': {
                data_type.value: {
                    'symbols_count': len(subscription.symbols),
                    'components_count': len(subscription.components),
                    'callbacks_count': len(subscription.callbacks)
                }
                for data_type, subscription in self._active_subscriptions.items()
            },
            'performance': {
                'active_components': self._performance_metrics.active_components,
                'active_subscriptions': self._performance_metrics.active_subscriptions,
                'subscription_conflicts': self._performance_metrics.subscription_conflicts
            }
        }

    # =============================================================================
    # 이벤트 분배 지원
    # =============================================================================

    async def distribute_event(self, event: BaseWebSocketEvent) -> None:
        """이벤트를 해당 구독자들에게 분배"""
        data_type = self._infer_data_type_from_event(event)
        if not data_type:
            self.logger.warning(f"이벤트 데이터 타입 추론 실패: {type(event)}")
            return

        subscription = self._active_subscriptions.get(data_type)
        if not subscription:
            return

        # 심볼 필터링 (해당 심볼을 구독하는 경우만)
        if event.symbol and event.symbol not in subscription.symbols:
            return

        # 콜백 호출
        for callback in subscription.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)

                subscription.message_count += 1

            except Exception as e:
                subscription.error_count += 1
                self._performance_metrics.callback_errors += 1
                self.logger.error(f"콜백 오류: {e}, 이벤트: {type(event)}")

    def _infer_data_type_from_event(self, event: BaseWebSocketEvent) -> Optional[DataType]:
        """이벤트에서 데이터 타입 추론"""
        from .types import TickerEvent, OrderbookEvent, TradeEvent, CandleEvent, MyOrderEvent, MyAssetEvent

        if isinstance(event, TickerEvent):
            return DataType.TICKER
        elif isinstance(event, OrderbookEvent):
            return DataType.ORDERBOOK
        elif isinstance(event, TradeEvent):
            return DataType.TRADE
        elif isinstance(event, CandleEvent):
            # 캔들 이벤트는 unit 필드로 타입 결정
            unit = getattr(event, 'unit', 1)

            # 1초봉의 경우 unit 값 확인 필요 (업비트 문서상 candle.1s 지원)
            # 실제 응답에서 unit 값이 0 또는 다른 특별한 값일 가능성 고려
            if unit == 0:
                return DataType.CANDLE_1S   # 1초봉
            elif unit == 1:
                return DataType.CANDLE_1M   # 1분봉
            elif unit == 3:
                return DataType.CANDLE_3M
            elif unit == 5:
                return DataType.CANDLE_5M
            elif unit == 15:
                return DataType.CANDLE_15M
            elif unit == 30:
                return DataType.CANDLE_30M
            elif unit == 60:
                return DataType.CANDLE_60M
            elif unit == 240:
                return DataType.CANDLE_240M
            else:
                # 알 수 없는 unit 값인 경우 로깅하고 기본값 반환
                self.logger.warning(f"알 수 없는 캔들 unit 값: {unit}")
                return DataType.CANDLE_1M  # 기본값
        elif isinstance(event, MyOrderEvent):
            return DataType.MYORDER
        elif isinstance(event, MyAssetEvent):
            return DataType.MYASSET

        return None

    # =============================================================================
    # 변경 이벤트 관리
    # =============================================================================

    def add_change_callback(self, callback: Callable[[Dict[DataType, SubscriptionChange]], None]) -> None:
        """구독 변경 이벤트 콜백 추가"""
        self._change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable[[Dict[DataType, SubscriptionChange]], None]) -> None:
        """구독 변경 이벤트 콜백 제거"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    # =============================================================================
    # 정리 및 유지보수
    # =============================================================================

    async def cleanup_inactive_components(self) -> int:
        """비활성 컴포넌트 정리"""
        async with self._lock:
            inactive_components = []

            for component_id, component_ref in self._component_refs.items():
                if component_ref() is None:  # WeakRef가 None이면 객체 소멸됨
                    inactive_components.append(component_id)

            for component_id in inactive_components:
                await self._unregister_component_internal(component_id)

            if inactive_components:
                self.logger.info(f"비활성 컴포넌트 {len(inactive_components)}개 정리 완료")

            return len(inactive_components)

    async def validate_subscriptions(self) -> List[str]:
        """구독 상태 검증"""
        issues = []

        # 심볼 형식 검증
        for data_type, subscription in self._active_subscriptions.items():
            for symbol in subscription.symbols:
                if not symbol or '-' not in symbol:
                    issues.append(f"잘못된 심볼 형식: {symbol} in {data_type.value}")

        # 컴포넌트 참조 검증
        for component_id in self._component_subscriptions:
            if component_id in self._component_refs:
                if self._component_refs[component_id]() is None:
                    issues.append(f"컴포넌트 참조 누수: {component_id}")

        return issues

    def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭 조회"""
        return self._performance_metrics
