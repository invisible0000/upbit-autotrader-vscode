"""
WebSocket v6.2 구독 관리자 (리얼타임 스트림 중심)
===============================================

핵심 개념:
- 주 책임: WebSocket 구독 관리 (Subscription Management)
- 내부 구현: 리얼타임 스트림 중심 처리
- 관리되어야 하는 현 구독상태는 상항 리얼타임 스트림 목록
- 스냅샷 요청이 있을때 관리해서 통합하여 메세지를 보내야 함
- SIMPLE 형식은 일방향 변환만 (SIMPLE→DEFAULT)
"""

import asyncio
import weakref
from datetime import datetime
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.external_apis.upbit.websocket.core.websocket_types import (
    DataType, ComponentSubscription, SubscriptionSpec, WebSocketType
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class SubscriptionChange:
    """구독 변경 정보"""
    data_type: DataType
    old_symbols: Set[str]
    new_symbols: Set[str]
    change_type: str  # "added", "removed", "modified"


@dataclass
class SubscriptionComplexity:
    """구독 복잡성 정보"""
    symbol: str
    data_types: Set[DataType]
    components: Set[str]
    complexity_score: float
    optimization_suggestion: str


@dataclass
class RealtimeStreamState:
    """리얼타임 스트림 상태"""
    ws_type: WebSocketType
    data_type: DataType
    symbols: Set[str]
    components: Set[str]  # 이 스트림을 구독한 컴포넌트들
    created_at: datetime
    last_updated: datetime


class SubscriptionManager:
    """v6.2 리얼타임 스트림 중심 구독 관리자"""

    def __init__(self):
        self.logger = create_component_logger("SubscriptionManager")

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

        # 🔍 변경 감지를 위한 이전 상태 저장 (하드웨어 여유 활용)
        self._previous_stream_state: Dict[WebSocketType, Dict[DataType, Set[str]]] = {
            WebSocketType.PUBLIC: {},
            WebSocketType.PRIVATE: {}
        }

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
        """리얼타임 스트림 추가/확장 (Public API - 락 획득)"""
        self.logger.debug(f"🎯 add_realtime_stream() 호출: {ws_type.value}/{data_type.value} {symbols} by {component_id}")

        async with self._lock:
            self.logger.debug(f"🔒 락 획득 완료: {ws_type.value}/{data_type.value}")
            await self._add_realtime_stream_unlocked(ws_type, data_type, symbols, component_id)

    async def _add_realtime_stream_unlocked(self, ws_type: WebSocketType, data_type: DataType,
                                            symbols: Set[str], component_id: str) -> None:
        """리얼타임 스트림 추가/확장 (Internal API - 락 없이)"""
        self.logger.debug(f"🎯 _add_realtime_stream_unlocked() 시작: {ws_type.value}/{data_type.value}")
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
        self.logger.debug(f"📊 메트릭 업데이트 완료: {ws_type.value}/{data_type.value}")

        # 🔄 실제 변경사항만 감지하여 알림 (하드웨어 여유 활용)
        self.logger.debug(f"🔔 변경 감지 호출 시작: {ws_type.value}/{data_type.value}")
        self._detect_and_notify_changes(ws_type, data_type, symbols)
        self.logger.debug(f"✅ 변경 감지 호출 완료: {ws_type.value}/{data_type.value}")

    async def remove_realtime_stream(self, ws_type: WebSocketType, data_type: DataType,
                                     symbols: Set[str], component_id: str) -> None:
        """리얼타임 스트림 제거/축소"""
        async with self._lock:
            await self._remove_realtime_stream_unlocked(ws_type, data_type, symbols, component_id)

    async def _remove_realtime_stream_unlocked(self, ws_type: WebSocketType, data_type: DataType,
                                               symbols: Set[str], component_id: str) -> None:
        """리얼타임 스트림 제거/축소 (Lock 없는 내부 메서드)"""
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
            return self._consume_snapshot_requests_unlocked(ws_type, data_type)

    def _consume_snapshot_requests_unlocked(self, ws_type: WebSocketType, data_type: DataType) -> Set[str]:
        """스냅샷 요청 소비 (락 없이 - 내부용)"""
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

            # 스냅샷 요청 심볼 (일회성 소비) - 락 없이 호출
            snapshot_symbols = self._consume_snapshot_requests_unlocked(ws_type, data_type)

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
        self.logger.info(f"📝 SubscriptionManager.register_component() 시작: {component_id}")

        async with self._lock:
            self._component_subscriptions[component_id] = subscription
            self.logger.debug(f"📊 컴포넌트 구독 저장 완료: {component_id}")

            # WeakRef로 자동 정리 (안전한 콜백)
            def cleanup(ref):
                try:
                    # 이벤트 루프가 실행 중인지 확인
                    loop = asyncio.get_running_loop()
                    if loop and not loop.is_closed():
                        asyncio.create_task(self._cleanup_component(component_id))
                    else:
                        self.logger.debug(f"컴포넌트 자동 정리 스킵 (이벤트 루프 없음): {component_id}")
                except RuntimeError:
                    # 이벤트 루프가 없거나 종료됨, 무시
                    self.logger.debug(f"컴포넌트 자동 정리 스킵 (이벤트 루프 없음): {component_id}")
                except Exception as e:
                    self.logger.error(f"컴포넌트 자동 정리 오류: {e}")

            self._component_refs[component_id] = weakref.ref(component_ref, cleanup)
            self.logger.debug(f"🔗 WeakRef 설정 완료: {component_id}")

            # 구독 스펙에 따라 리얼타임 스트림 추가
            for i, spec in enumerate(subscription.subscriptions):
                self.logger.debug(
                    f"🎯 구독 스펙 {i + 1}/{len(subscription.subscriptions)} 처리: "
                    f"{spec.data_type.value} {spec.symbols}"
                )

                # 데이터 타입에 따라 WebSocket 타입 결정
                ws_type = (WebSocketType.PRIVATE if spec.data_type in [DataType.MYORDER, DataType.MYASSET]
                           else WebSocketType.PUBLIC)
                self.logger.debug(f"📡 WebSocket 타입 결정: {ws_type.value}")

                await self._add_realtime_stream_unlocked(
                    ws_type, spec.data_type, set(spec.symbols), component_id
                )
                self.logger.debug(f"✅ 리얼타임 스트림 추가 완료: {spec.data_type.value}")

            self.logger.info(f"✅ SubscriptionManager 컴포넌트 등록 완료: {component_id} ({len(subscription.subscriptions)}개 스펙)")

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
            for spec in subscription.subscriptions:
                # 데이터 타입에 따라 WebSocket 타입 결정
                ws_type = (WebSocketType.PRIVATE if spec.data_type in [DataType.MYORDER, DataType.MYASSET]
                           else WebSocketType.PUBLIC)

                # 🔧 Lock 없는 내부 메서드 사용으로 재귀 Lock 문제 해결
                await self._remove_realtime_stream_unlocked(
                    ws_type, spec.data_type, set(spec.symbols), component_id
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

    def _notify_changes(self, changes: Dict[DataType, SubscriptionChange]) -> None:
        """변경사항 알림"""
        self.logger.info(f"📢 변경 알림 전송 시작: {len(self._change_callbacks)}개 콜백")

        for i, callback in enumerate(self._change_callbacks):
            try:
                self.logger.debug(f"📞 콜백 {i + 1}/{len(self._change_callbacks)} 호출 중...")
                callback(changes)
                self.logger.debug(f"✅ 콜백 {i + 1} 호출 완료")
            except Exception as e:
                self.logger.error(f"변경 알림 콜백 오류: {e}")

        if self._change_callbacks:
            self.logger.info(f"✅ 변경 알림 전송 완료: {len(self._change_callbacks)}개 콜백")
        else:
            self.logger.warning("⚠️ 등록된 변경 알림 콜백이 없음!")

    def _detect_and_notify_changes(self, ws_type: WebSocketType, data_type: DataType,
                                   new_symbols: Set[str]) -> None:
        """실제 변경사항 감지 및 알림 (하드웨어 여유 활용)"""
        self.logger.debug(f"🔍 _detect_and_notify_changes() 시작: {ws_type.value}/{data_type.value}")
        try:
            # 현재 상태 가져오기
            self.logger.debug(f"📊 현재 상태 조회: {ws_type.value}/{data_type.value}")
            current_symbols = set()
            if data_type in self._realtime_streams[ws_type]:
                current_symbols = self._realtime_streams[ws_type][data_type].symbols.copy()
            self.logger.debug(f"📊 현재 심볼: {current_symbols}")

            # 이전 상태와 비교
            self.logger.debug(f"📊 이전 상태 조회: {ws_type.value}/{data_type.value}")
            previous_symbols = self._previous_stream_state[ws_type].get(data_type, set())
            self.logger.debug(f"📊 이전 심볼: {previous_symbols}")

            # 실제 변경 여부 확인
            if current_symbols == previous_symbols:
                self.logger.debug(f"변경 없음: {ws_type.value}/{data_type.value} - 알림 스킵")
                return

            self.logger.debug(f"🔄 변경 감지됨: {ws_type.value}/{data_type.value}")

            # 변경 유형 분석
            added_symbols = current_symbols - previous_symbols
            removed_symbols = previous_symbols - current_symbols

            if added_symbols or removed_symbols:
                change_type = "modified"
                if not previous_symbols:
                    change_type = "added"
                elif not current_symbols:
                    change_type = "removed"

                self.logger.info(f"🔔 변경 감지: {ws_type.value}/{data_type.value} - "
                                 f"추가: {len(added_symbols)}, 제거: {len(removed_symbols)}")

                # 변경사항 알림
                self.logger.debug("📢 SubscriptionChange 객체 생성 중...")
                changes = {data_type: SubscriptionChange(
                    data_type=data_type,
                    old_symbols=previous_symbols,
                    new_symbols=current_symbols,
                    change_type=change_type
                )}
                self.logger.debug("📢 변경 알림 전송 중...")
                self._notify_changes(changes)
                self.logger.debug("📢 변경 알림 전송 완료")

                # 🎯 상태 업데이트는 메시지 전송 완료 후 commit_subscription_state_update()에서 수행

        except Exception as e:
            self.logger.error(f"변경 감지 중 오류: {e}")
            # 🎯 에러 시에도 상태 업데이트는 WebSocketManager에서 처리

    def get_subscription_classification(self, ws_type: WebSocketType) -> Dict[DataType, Dict[str, List[str]]]:
        """
        현재 구독을 신규/기존으로 분류하여 반환 (상태 업데이트 없음)

        Args:
            ws_type: WebSocket 타입

        Returns:
            {DataType: {'existing': [symbols], 'new': [symbols]}} 형태
        """
        classification = {}

        try:
            # 동기적으로 처리 (읽기 전용 작업)
            for data_type, stream_info in self._realtime_streams[ws_type].items():
                current_symbols = stream_info.symbols.copy()
                previous_symbols = self._previous_stream_state[ws_type].get(data_type, set())

                # Private 타입 (myAsset, myOrder)은 심볼이 없으므로 스트림 존재 여부로 판단
                if data_type.is_private():
                    # Private 타입: 이전 상태 존재 여부로 신규/기존 구분
                    if data_type in self._previous_stream_state[ws_type]:
                        # 이전에 구독한 적이 있음 -> 기존 구독
                        classification[data_type] = {
                            'existing': [],  # Private 타입은 심볼 없음
                            'new': []
                        }
                        self.logger.debug(f"📊 Private 구독 분류 ({data_type.value}): 기존 구독")
                    else:
                        # 처음 구독 -> 신규 구독
                        classification[data_type] = {
                            'existing': [],
                            'new': []  # Private 타입은 심볼 없지만 신규로 분류
                        }
                        self.logger.debug(f"📊 Private 구독 분류 ({data_type.value}): 신규 구독")
                else:
                    # Public 타입: 기존 로직 (심볼 기반 분류)
                    existing_symbols = list(current_symbols & previous_symbols)  # 교집합: 기존 구독
                    new_symbols = list(current_symbols - previous_symbols)       # 차집합: 신규 구독

                    if existing_symbols or new_symbols:
                        classification[data_type] = {
                            'existing': existing_symbols,
                            'new': new_symbols
                        }

                        self.logger.debug(f"📊 Public 구독 분류 ({data_type.value}): "
                                          f"기존 {len(existing_symbols)}개, 신규 {len(new_symbols)}개")

        except Exception as e:
            self.logger.error(f"구독 분류 중 오류: {e}")

        return classification

    def commit_subscription_state_update(self, ws_type: WebSocketType) -> None:
        """
        메시지 전송 완료 후 _previous_stream_state 업데이트

        Args:
            ws_type: WebSocket 타입
        """
        try:
            current_streams = self._realtime_streams[ws_type]

            for data_type, stream_info in current_streams.items():
                current_symbols = stream_info.symbols.copy()
                self._previous_stream_state[ws_type][data_type] = current_symbols

                self.logger.debug(f"📊 상태 업데이트 완료 ({data_type.value}): "
                                  f"{len(current_symbols)}개 심볼을 이전 상태로 저장")

        except Exception as e:
            self.logger.error(f"구독 상태 업데이트 중 오류 ({ws_type}): {e}")
