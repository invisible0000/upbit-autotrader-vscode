"""
WebSocket v6.0 간소화된 구독 관리자
=================================

구독 상태 통합 관리 (subscription_state_manager.py 간소화)
- 컴포넌트별 구독 요청 통합
- WeakRef 기반 자동 정리
- Public/Private 구독 분리
- 원자적 상태 업데이트
"""

import asyncio
import time
import weakref
from typing import Dict, List, Set, Optional, Callable
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..core.websocket_types import (
    DataType, SubscriptionSpec, ComponentSubscription, WebSocketType
)


@dataclass
class ActiveSubscription:
    """활성 구독 정보"""
    data_type: DataType
    symbols: Set[str]
    components: Set[str]
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    message_count: int = 0


@dataclass
class SubscriptionChange:
    """구독 변경 정보"""
    added_symbols: Set[str] = field(default_factory=set)
    removed_symbols: Set[str] = field(default_factory=set)
    is_empty: bool = True

    def __post_init__(self):
        self.is_empty = not (self.added_symbols or self.removed_symbols)


class SubscriptionManager:
    """간소화된 구독 상태 관리자"""

    def __init__(self):
        self.logger = create_component_logger("SubscriptionManager")

        # 동시성 제어
        self._lock = asyncio.Lock()

        # 컴포넌트별 구독
        self._component_subscriptions: Dict[str, ComponentSubscription] = {}
        self._component_refs: Dict[str, weakref.ref] = {}

        # 통합된 활성 구독 (Public/Private 분리)
        self._public_subscriptions: Dict[DataType, ActiveSubscription] = {}
        self._private_subscriptions: Dict[DataType, ActiveSubscription] = {}

        # 변경 알림 콜백
        self._change_callbacks: List[Callable[[Dict[DataType, SubscriptionChange]], None]] = []

        self.logger.info("구독 관리자 초기화 완료")

    # ================================================================
    # 컴포넌트 관리
    # ================================================================

    async def register_component(
        self,
        component_id: str,
        subscription_specs: List[SubscriptionSpec],
        callback: Optional[Callable] = None,
        cleanup_ref: Optional[object] = None
    ) -> Dict[DataType, SubscriptionChange]:
        """컴포넌트 구독 등록"""
        async with self._lock:
            # 기존 구독 백업
            old_public = dict(self._public_subscriptions)
            old_private = dict(self._private_subscriptions)

            # 컴포넌트 구독 정보 저장
            component_subscription = ComponentSubscription(
                component_id=component_id,
                subscriptions=subscription_specs,
                callback=callback
            )
            self._component_subscriptions[component_id] = component_subscription

            # WeakRef 등록 (자동 정리용)
            if cleanup_ref:
                try:
                    def cleanup_callback(ref):
                        asyncio.create_task(self._cleanup_component(component_id))

                    weak_ref = weakref.ref(cleanup_ref, cleanup_callback)
                    self._component_refs[component_id] = weak_ref
                except TypeError:
                    self.logger.warning(f"WeakRef 생성 실패: {component_id}")

            # 통합 구독 상태 재계산
            self._recalculate_subscriptions()

            # 변경사항 계산
            changes = self._calculate_changes(
                old_public, old_private,
                self._public_subscriptions, self._private_subscriptions
            )

            # 변경 알림
            if changes and not all(change.is_empty for change in changes.values()):
                await self._notify_changes(changes)

            self.logger.debug(f"컴포넌트 등록: {component_id}, {len(subscription_specs)}개 구독")
            return changes

    async def unregister_component(self, component_id: str) -> Dict[DataType, SubscriptionChange]:
        """컴포넌트 구독 해제"""
        async with self._lock:
            if component_id not in self._component_subscriptions:
                return {}

            # 기존 구독 백업
            old_public = dict(self._public_subscriptions)
            old_private = dict(self._private_subscriptions)

            # 컴포넌트 제거
            del self._component_subscriptions[component_id]
            self._component_refs.pop(component_id, None)

            # 통합 구독 상태 재계산
            self._recalculate_subscriptions()

            # 변경사항 계산
            changes = self._calculate_changes(
                old_public, old_private,
                self._public_subscriptions, self._private_subscriptions
            )

            # 변경 알림
            if changes and not all(change.is_empty for change in changes.values()):
                await self._notify_changes(changes)

            self.logger.debug(f"컴포넌트 해제: {component_id}")
            return changes

    async def _cleanup_component(self, component_id: str) -> None:
        """컴포넌트 자동 정리 (WeakRef 콜백)"""
        self.logger.debug(f"컴포넌트 자동 정리: {component_id}")
        await self.unregister_component(component_id)

    # ================================================================
    # 구독 상태 관리
    # ================================================================

    def _recalculate_subscriptions(self) -> None:
        """통합 구독 상태 재계산"""
        # 기존 구독 초기화
        self._public_subscriptions.clear()
        self._private_subscriptions.clear()

        # 모든 컴포넌트 구독 통합
        for component_subscription in self._component_subscriptions.values():
            for spec in component_subscription.subscriptions:
                # Public/Private 분류
                target_subscriptions = (
                    self._private_subscriptions if spec.data_type.is_private()
                    else self._public_subscriptions
                )

                # 기존 구독에 추가 또는 새 구독 생성
                if spec.data_type in target_subscriptions:
                    active_sub = target_subscriptions[spec.data_type]
                    active_sub.symbols.update(spec.symbols)
                    active_sub.components.add(component_subscription.component_id)
                    active_sub.last_updated = time.time()
                else:
                    target_subscriptions[spec.data_type] = ActiveSubscription(
                        data_type=spec.data_type,
                        symbols=set(spec.symbols),
                        components={component_subscription.component_id}
                    )

    def _calculate_changes(
        self,
        old_public: Dict[DataType, ActiveSubscription],
        old_private: Dict[DataType, ActiveSubscription],
        new_public: Dict[DataType, ActiveSubscription],
        new_private: Dict[DataType, ActiveSubscription]
    ) -> Dict[DataType, SubscriptionChange]:
        """구독 변경사항 계산"""
        changes = {}

        # 모든 데이터 타입 수집
        all_data_types = set()
        all_data_types.update(old_public.keys())
        all_data_types.update(old_private.keys())
        all_data_types.update(new_public.keys())
        all_data_types.update(new_private.keys())

        for data_type in all_data_types:
            # 기존 심볼
            old_symbols = set()
            if data_type in old_public:
                old_symbols.update(old_public[data_type].symbols)
            if data_type in old_private:
                old_symbols.update(old_private[data_type].symbols)

            # 새 심볼
            new_symbols = set()
            if data_type in new_public:
                new_symbols.update(new_public[data_type].symbols)
            if data_type in new_private:
                new_symbols.update(new_private[data_type].symbols)

            # 변경사항 계산
            added = new_symbols - old_symbols
            removed = old_symbols - new_symbols

            if added or removed:
                changes[data_type] = SubscriptionChange(
                    added_symbols=added,
                    removed_symbols=removed,
                    is_empty=False
                )

        return changes

    # ================================================================
    # 조회 메서드
    # ================================================================

    def get_public_subscriptions(self) -> Dict[DataType, Set[str]]:
        """Public 구독 목록 조회"""
        return {
            data_type: active_sub.symbols.copy()
            for data_type, active_sub in self._public_subscriptions.items()
        }

    def get_private_subscriptions(self) -> Dict[DataType, Set[str]]:
        """Private 구독 목록 조회"""
        return {
            data_type: active_sub.symbols.copy()
            for data_type, active_sub in self._private_subscriptions.items()
        }

    def get_all_subscriptions(self) -> Dict[WebSocketType, Dict[DataType, Set[str]]]:
        """모든 구독 목록 조회"""
        return {
            WebSocketType.PUBLIC: self.get_public_subscriptions(),
            WebSocketType.PRIVATE: self.get_private_subscriptions()
        }

    def get_component_count(self) -> int:
        """등록된 컴포넌트 수"""
        return len(self._component_subscriptions)

    def get_subscription_stats(self) -> Dict[str, int]:
        """구독 통계"""
        public_symbols = sum(len(sub.symbols) for sub in self._public_subscriptions.values())
        private_symbols = sum(len(sub.symbols) for sub in self._private_subscriptions.values())

        return {
            'components': len(self._component_subscriptions),
            'public_types': len(self._public_subscriptions),
            'private_types': len(self._private_subscriptions),
            'public_symbols': public_symbols,
            'private_symbols': private_symbols,
            'total_symbols': public_symbols + private_symbols
        }

    def is_subscribed(self, data_type: DataType, symbol: str) -> bool:
        """특정 심볼/타입 구독 여부 확인"""
        if data_type.is_private():
            active_sub = self._private_subscriptions.get(data_type)
        else:
            active_sub = self._public_subscriptions.get(data_type)

        return active_sub is not None and symbol in active_sub.symbols

    # ================================================================
    # 변경 알림
    # ================================================================

    def add_change_callback(self, callback: Callable[[Dict[DataType, SubscriptionChange]], None]) -> None:
        """구독 변경 알림 콜백 등록"""
        self._change_callbacks.append(callback)

    def remove_change_callback(self, callback: Callable) -> None:
        """구독 변경 알림 콜백 해제"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)

    async def _notify_changes(self, changes: Dict[DataType, SubscriptionChange]) -> None:
        """구독 변경 알림"""
        for callback in self._change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(changes)
                else:
                    callback(changes)
            except Exception as e:
                self.logger.error(f"구독 변경 알림 오류: {e}")

    # ================================================================
    # 유지보수
    # ================================================================

    async def cleanup_stale_components(self) -> int:
        """오래된 컴포넌트 정리"""
        cleanup_count = 0
        current_time = time.time()

        for component_id in list(self._component_subscriptions.keys()):
            component_sub = self._component_subscriptions[component_id]

            # 10분 이상 비활성화된 컴포넌트 정리
            if current_time - component_sub.last_activity > 600:
                await self.unregister_component(component_id)
                cleanup_count += 1

        if cleanup_count > 0:
            self.logger.info(f"오래된 컴포넌트 정리: {cleanup_count}개")

        return cleanup_count

    def update_message_count(self, data_type: DataType) -> None:
        """메시지 카운트 업데이트"""
        if data_type.is_private():
            if data_type in self._private_subscriptions:
                self._private_subscriptions[data_type].message_count += 1
        else:
            if data_type in self._public_subscriptions:
                self._public_subscriptions[data_type].message_count += 1


__all__ = [
    'SubscriptionManager',
    'ActiveSubscription',
    'SubscriptionChange'
]
