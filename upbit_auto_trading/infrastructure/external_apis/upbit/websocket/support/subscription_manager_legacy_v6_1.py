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
from datetime import datetime
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
    """간소화된 구독 상태 관리자 (v6.2 리얼타임 스트림 중심)"""

    def __init__(self):
        self.logger = create_component_logger("SubscriptionManager")

        # 동시성 제어
        self._lock = asyncio.Lock()

        # 컴포넌트별 구독
        self._component_subscriptions: Dict[str, ComponentSubscription] = {}
        self._component_refs: Dict[str, weakref.ref] = {}

        # 🎯 핵심 상태: 리얼타임 스트림 목록 (기본 관리 대상)
        self._realtime_streams: Dict[WebSocketType, Dict[DataType, Set[str]]] = {
            WebSocketType.PUBLIC: {},
            WebSocketType.PRIVATE: {}
        }

        # 📸 임시 상태: 스냅샷 요청 목록 (일시적)
        self._pending_snapshot_requests: Dict[WebSocketType, Dict[DataType, Set[str]]] = {
            WebSocketType.PUBLIC: {},
            WebSocketType.PRIVATE: {}
        }

        # 변경 알림 콜백
        self._change_callbacks: List[Callable[[Dict[DataType, SubscriptionChange]], None]] = []

        # ===== v6.2 리얼타임 스트림 관리 기능 =====

        # 구독 복잡성 관리
        self._detected_complexities: List[SubscriptionComplexity] = []
        self._complexity_analysis_enabled: bool = True

        # 성능 모니터링
        self._performance_metrics: Dict[str, Any] = {
            'total_realtime_streams': 0,
            'total_snapshot_requests': 0,
            'stream_protection_events': 0,
            'last_snapshot_batch_at': None,
            'stream_efficiency_score': 0.0
        }

        # 스트림 상태 스냅샷 (재연결 복원용)
        self._last_stream_snapshot: Optional[Dict] = None
        self._auto_snapshot_enabled: bool = True

        self.logger.info("구독 관리자 v6.2 초기화 완료 (리얼타임 스트림 중심)")

    # ================================================================
    # v6.2 리얼타임 스트림 관리 기능들
    # ================================================================

    def analyze_subscription_complexity(self) -> List[SubscriptionComplexity]:
        """구독 복잡성 분석 (v6.2 리얼타임 스트림 기반)"""
        complexities = []
        symbol_to_types = {}

        # 리얼타임 스트림에서 심볼별 타입 수집
        for ws_type, type_symbols in self._realtime_streams.items():
            for data_type, symbols in type_symbols.items():
                for symbol in symbols:
                    if symbol not in symbol_to_types:
                        symbol_to_types[symbol] = {'types': set(), 'ws_types': set()}
                    symbol_to_types[symbol]['types'].add(data_type)
                    symbol_to_types[symbol]['ws_types'].add(ws_type)

        # 복잡성 분석 (같은 심볼에 여러 타입 = 높은 복잡성)
        for symbol, info in symbol_to_types.items():
            if len(info['types']) > 1:
                # 복잡성 점수 계산 (타입 수에 따라)
                complexity_score = min(1.0, len(info['types']) / 5.0)  # 최대 5개 타입 기준

                complexities.append(SubscriptionComplexity(
                    symbol=symbol,
                    data_types=info['types'],
                    components=set(),  # 리얼타임 스트림에서는 컴포넌트 추적이 다름
                    complexity_score=complexity_score,
                    optimization_suggestion="merge_realtime_streams"
                ))

        self._detected_complexities = complexities
        return complexities

    def calculate_subscription_efficiency(self) -> float:
        """구독 효율성 점수 계산 (v6.2: 리얼타임 스트림 기준)"""
        total_realtime_streams = sum(
            len(symbols) for type_symbols in self._realtime_streams.values()
            for symbols in type_symbols.values()
        )

        if total_realtime_streams == 0:
            return 1.0

        # 중복도 계산 (복잡성 기반)
        complexities = self.analyze_subscription_complexity()
        complexity_penalty = len(complexities) * 0.1

        # 스트림 효율성 점수
        efficiency = max(0.0, 1.0 - complexity_penalty)
        self._performance_metrics['stream_efficiency_score'] = efficiency

        return efficiency

    # ================================================================
    # v6.2 리얼타임 스트림 핵심 메서드들
    # ================================================================

    async def add_realtime_stream(self, ws_type: WebSocketType, data_type: DataType, symbol: str) -> None:
        """리얼타임 스트림 추가"""
        async with self._lock:
            if data_type not in self._realtime_streams[ws_type]:
                self._realtime_streams[ws_type][data_type] = set()

            self._realtime_streams[ws_type][data_type].add(symbol)
            self._performance_metrics['total_realtime_streams'] = self._count_total_realtime_streams()

            self.logger.debug(f"리얼타임 스트림 추가: {ws_type.value}/{data_type.value}/{symbol}")

    async def remove_realtime_stream(self, ws_type: WebSocketType, data_type: DataType, symbol: str) -> None:
        """리얼타임 스트림 제거"""
        async with self._lock:
            if (data_type in self._realtime_streams[ws_type] and
                    symbol in self._realtime_streams[ws_type][data_type]):
                
                self._realtime_streams[ws_type][data_type].remove(symbol)
                
                # 빈 타입 정리
                if not self._realtime_streams[ws_type][data_type]:
                    del self._realtime_streams[ws_type][data_type]
                
                self._performance_metrics['total_realtime_streams'] = self._count_total_realtime_streams()
                
                self.logger.debug(f"리얼타임 스트림 제거: {ws_type.value}/{data_type.value}/{symbol}")    async def add_snapshot_request(self, ws_type: WebSocketType, data_type: DataType, symbol: str) -> None:
        """임시 스냅샷 요청 추가"""
        async with self._lock:
            if data_type not in self._pending_snapshot_requests[ws_type]:
                self._pending_snapshot_requests[ws_type][data_type] = set()

            self._pending_snapshot_requests[ws_type][data_type].add(symbol)
            self._performance_metrics['total_snapshot_requests'] = self._count_total_snapshot_requests()
            self._performance_metrics['last_snapshot_batch_at'] = datetime.now().isoformat()

            self.logger.debug(f"스냅샷 요청 추가: {ws_type.value}/{data_type.value}/{symbol}")

    async def clear_snapshot_requests(self, ws_type: WebSocketType, data_type: DataType) -> Set[str]:
        """스냅샷 요청 일괄 처리 및 클리어"""
        async with self._lock:
            symbols = set()
            if data_type in self._pending_snapshot_requests[ws_type]:
                symbols = self._pending_snapshot_requests[ws_type][data_type].copy()
                del self._pending_snapshot_requests[ws_type][data_type]

            self._performance_metrics['total_snapshot_requests'] = self._count_total_snapshot_requests()

            if symbols:
                self.logger.debug(f"스냅샷 요청 처리 완료: {ws_type.value}/{data_type.value} ({len(symbols)}개)")

            return symbols

    def get_realtime_streams(self, ws_type: WebSocketType) -> Dict[DataType, Set[str]]:
        """현재 리얼타임 스트림 목록 조회"""
        return self._realtime_streams[ws_type].copy()

    def get_pending_snapshots(self, ws_type: WebSocketType) -> Dict[DataType, Set[str]]:
        """대기 중인 스냅샷 요청 목록 조회"""
        return self._pending_snapshot_requests[ws_type].copy()

    def _count_total_realtime_streams(self) -> int:
        """전체 리얼타임 스트림 수 계산"""
        return sum(
            len(symbols) for type_symbols in self._realtime_streams.values()
            for symbols in type_symbols.values()
        )

    def _count_total_snapshot_requests(self) -> int:
        """전체 스냅샷 요청 수 계산"""
        return sum(
            len(symbols) for type_symbols in self._pending_snapshot_requests.values()
            for symbols in type_symbols.values()
        )
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
        priority: int = 0,
        stream_filter: Optional[str] = None  # v6.1: "SNAPSHOT", "REALTIME", None
    ) -> Dict[DataType, SubscriptionChange]:
        """컴포넌트 구독 등록 (v6.1 스트림 필터링 지원)"""
        async with self._lock:
            # 기존 구독 백업
            old_public = dict(self._public_subscriptions)
            old_private = dict(self._private_subscriptions)

            # 컴포넌트 구독 정보 저장 (v6.1 스트림 필터링 포함)
            component_subscription = ComponentSubscription(
                component_id=component_id,
                subscriptions=subscription_specs,
                callback=callback,
                stream_filter=stream_filter  # v6.1 새로운 필드
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
    # v6.1 스트림 필터링 기능
    # ================================================================

    def should_deliver_message(self, component_id: str, stream_type: str) -> bool:
        """
        컴포넌트에 메시지를 전달할지 결정 (스트림 필터링)

        Args:
            component_id: 컴포넌트 ID
            stream_type: 메시지의 스트림 타입 ("SNAPSHOT" 또는 "REALTIME")

        Returns:
            메시지 전달 여부
        """
        component_sub = self._component_subscriptions.get(component_id)
        if not component_sub:
            return False

        stream_filter = component_sub.stream_filter

        # 필터가 없으면 모든 메시지 전달
        if not stream_filter:
            return True

        # 필터에 따른 선택적 전달
        if stream_filter == "SNAPSHOT" and stream_type == "SNAPSHOT":
            return True
        elif stream_filter == "REALTIME" and stream_type == "REALTIME":
            return True
        else:
            return False

    def get_filtered_components(self, data_type: DataType, stream_type: str) -> List[str]:
        """
        특정 데이터 타입과 스트림 타입에 관심 있는 컴포넌트 목록 반환

        Args:
            data_type: 데이터 타입
            stream_type: 스트림 타입

        Returns:
            관심 있는 컴포넌트 ID 목록
        """
        interested_components = []

        for component_id, component_sub in self._component_subscriptions.items():
            # 해당 데이터 타입을 구독하는지 확인
            subscribes_to_type = any(
                spec.data_type == data_type
                for spec in component_sub.subscriptions
            )

            if subscribes_to_type and self.should_deliver_message(component_id, stream_type):
                interested_components.append(component_id)

        return interested_components

    def get_stream_preferences_summary(self) -> Dict[str, Any]:
        """
        전체 컴포넌트의 스트림 필터링 현황 요약

        Returns:
            스트림 필터링 현황 딕셔너리
        """
        filter_counts = {"SNAPSHOT": 0, "REALTIME": 0, "ALL": 0}
        filter_details = []

        for component_id, component_sub in self._component_subscriptions.items():
            stream_filter = component_sub.stream_filter

            if stream_filter == "SNAPSHOT":
                filter_counts["SNAPSHOT"] += 1
            elif stream_filter == "REALTIME":
                filter_counts["REALTIME"] += 1
            else:
                filter_counts["ALL"] += 1

            filter_details.append({
                "component_id": component_id,
                "stream_filter": stream_filter or "ALL",
                "subscription_count": len(component_sub.subscriptions)
            })

        return {
            "summary": filter_counts,
            "details": filter_details,
            "total_components": len(self._component_subscriptions)
        }

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
