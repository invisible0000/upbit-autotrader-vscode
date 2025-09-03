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
from typing import Dict, List, Set, Optional, Callable, Any
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


@dataclass
class SubscriptionComplexity:
    """구독 복잡성 정보 (이전: SubscriptionConflict)"""
    symbol: str
    data_types: Set[DataType]  # 이전: conflicting_types
    components: Set[str]
    complexity_score: float = 0.0  # 복잡성 점수
    optimization_suggestion: str = "merge"  # merge, prioritize, separate


class SubscriptionManager:
    """간소화된 구독 상태 관리자 (v6.1 Enhanced)"""

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

        # ===== 새로운 v6.1 기능들 =====

        # 구독 복잡성 관리 (이전: 충돌 관리)
        self._detected_complexities: List[SubscriptionComplexity] = []
        self._complexity_analysis_enabled: bool = True

        # 성능 모니터링
        self._performance_metrics: Dict[str, Any] = {
            'total_batches_processed': 0,
            'total_conflicts_resolved': 0,
            'avg_batch_size': 0.0,
            'last_batch_processed_at': None,
            'subscription_efficiency_score': 0.0
        }

        # 구독 상태 스냅샷 (재연결 복원용)
        self._last_state_snapshot: Optional[Dict] = None
        self._auto_snapshot_enabled: bool = True

        self.logger.info("구독 관리자 v6.1 초기화 완료 (Enhanced Features)")

    # ================================================================
    # v6.1 새로운 핵심 기능들
    # ================================================================

    def analyze_subscription_complexity(self) -> List[SubscriptionComplexity]:
        """구독 복잡성 분석 (이전: detect_subscription_conflicts)"""
        complexities = []
        symbol_to_types = {}

        # 모든 활성 구독에서 심볼별 타입 수집
        for subscriptions in [self._public_subscriptions, self._private_subscriptions]:
            for data_type, active_sub in subscriptions.items():
                for symbol in active_sub.symbols:
                    if symbol not in symbol_to_types:
                        symbol_to_types[symbol] = {'types': set(), 'components': set()}
                    symbol_to_types[symbol]['types'].add(data_type)
                    symbol_to_types[symbol]['components'].update(active_sub.components)

        # 복잡성 분석 (같은 심볼에 여러 타입 = 높은 복잡성)
        for symbol, info in symbol_to_types.items():
            if len(info['types']) > 1:
                # 복잡성 점수 계산 (타입 수에 따라)
                complexity_score = min(1.0, len(info['types']) / 5.0)  # 최대 5개 타입 기준

                complexities.append(SubscriptionComplexity(
                    symbol=symbol,
                    data_types=info['types'],
                    components=info['components'],
                    complexity_score=complexity_score,
                    optimization_suggestion="merge"  # 기본값
                ))

        self._detected_complexities = complexities
        return complexities

    def calculate_subscription_efficiency(self) -> float:
        """구독 효율성 점수 계산 (0.0 ~ 1.0)"""
        total_subscriptions = len(self._public_subscriptions) + len(self._private_subscriptions)
        if total_subscriptions == 0:
            return 1.0

        # 중복도 계산 (복잡성 기반)
        complexities = self.analyze_subscription_complexity()
        complexity_penalty = len(complexities) * 0.1

        # 전체 효율성 점수 (복잡성 기반)
        efficiency = max(0.0, 1.0 - complexity_penalty)
        self._performance_metrics['subscription_efficiency_score'] = efficiency

        return efficiency

    def create_state_snapshot(self) -> Dict:
        """현재 구독 상태의 스냅샷 생성"""
        snapshot = {
            'timestamp': time.time(),
            'public_subscriptions': {
                dt.value: {
                    'symbols': list(sub.symbols),
                    'components': list(sub.components),
                    'message_count': sub.message_count
                }
                for dt, sub in self._public_subscriptions.items()
            },
            'private_subscriptions': {
                dt.value: {
                    'symbols': list(sub.symbols),
                    'components': list(sub.components),
                    'message_count': sub.message_count
                }
                for dt, sub in self._private_subscriptions.items()
            },
            'component_count': len(self._component_subscriptions),
            'performance_metrics': self._performance_metrics.copy()
        }

        if self._auto_snapshot_enabled:
            self._last_state_snapshot = snapshot

        return snapshot

    # ================================================================
    # 컴포넌트 관리 (v6.1 Enhanced)
    # ================================================================

    async def register_component(
        self,
        component_id: str,
        subscription_specs: List[SubscriptionSpec],
        callback: Optional[Callable] = None,
        cleanup_ref: Optional[object] = None,
        priority: int = 0
    ) -> Dict[DataType, SubscriptionChange]:
        """컴포넌트 구독 등록 (v6.1 배치 처리 적용)"""
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

            # 변경사항이 있으면 즉시 알림 전송
            if changes and not all(change.is_empty for change in changes.values()):
                await self._notify_changes(changes)

            return changes

    async def unregister_component(
        self,
        component_id: str,
        priority: int = 10  # 해제는 높은 우선순위
    ) -> Dict[DataType, SubscriptionChange]:
        """컴포넌트 구독 해제 (v6.1 배치 처리 적용)"""
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

            # 변경사항이 있으면 즉시 알림 전송
            if changes and not all(change.is_empty for change in changes.values()):
                await self._notify_changes(changes)

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
    # 조회 메서드 (v6.1 Enhanced)
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

    def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계 (v6.1 Enhanced)"""
        public_symbols = sum(len(sub.symbols) for sub in self._public_subscriptions.values())
        private_symbols = sum(len(sub.symbols) for sub in self._private_subscriptions.values())

        return {
            'components': len(self._component_subscriptions),
            'public_types': len(self._public_subscriptions),
            'private_types': len(self._private_subscriptions),
            'public_symbols': public_symbols,
            'private_symbols': private_symbols,
            'total_symbols': public_symbols + private_symbols,

            # v6.1 새로운 통계
            'detected_complexities': len(self._detected_complexities),
            'efficiency_score': self.calculate_subscription_efficiency(),
            'performance_metrics': self._performance_metrics.copy()
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭스 조회"""
        metrics = self._performance_metrics.copy()
        metrics.update({
            'current_efficiency': self.calculate_subscription_efficiency(),
            'active_complexities': len(self._detected_complexities),
            'total_active_subscriptions': len(self._public_subscriptions) + len(self._private_subscriptions)
        })
        return metrics

    def get_complexity_report(self) -> Dict[str, Any]:
        """구독 복잡성 보고서 (이전: get_conflict_report)"""
        complexities = self.analyze_subscription_complexity()

        return {
            'total_complexities': len(complexities),
            'complexities': [
                {
                    'symbol': complexity.symbol,
                    'data_types': [dt.value for dt in complexity.data_types],
                    'affected_components': list(complexity.components),
                    'complexity_score': complexity.complexity_score,
                    'optimization_suggestion': complexity.optimization_suggestion
                }
                for complexity in complexities
            ],
            'efficiency_impact': max(0, 1.0 - len(complexities) * 0.1)
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
    'SubscriptionChange',
    'SubscriptionComplexity'
]
