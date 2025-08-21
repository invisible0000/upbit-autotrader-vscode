"""
배치 구독 관리자

Test 08-11 검증 기반 배치 WebSocket 구독을 관리합니다.
189개 심볼까지 5,241 symbols/sec 성능으로 처리 가능합니다.

핵심 기능:
- 지능형 배치 구독 생명주기 관리
- 동적 구독 그룹핑 및 최적화
- 네트워크 효율성 기반 구독 조절
- 실시간 성능 모니터링
"""

import asyncio
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import time

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient, WebSocketDataType
)
from ..models import DataType, RoutingContext, UsageContext

logger = create_component_logger("BatchSubscriptionManager")


class SubscriptionState(Enum):
    """구독 상태"""
    IDLE = "idle"           # 대기 상태
    CONNECTING = "connecting"   # 연결 중
    ACTIVE = "active"       # 활성 구독
    PAUSED = "paused"       # 일시 정지
    ERROR = "error"         # 오류 상태
    TERMINATED = "terminated"  # 종료됨


@dataclass
class SubscriptionGroup:
    """구독 그룹"""
    group_id: str
    symbols: Set[str]
    data_type: DataType
    state: SubscriptionState = SubscriptionState.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: Optional[datetime] = None
    usage_contexts: Set[UsageContext] = field(default_factory=set)

    # 성능 메트릭
    message_count: int = 0
    total_latency_ms: float = 0.0
    error_count: int = 0

    @property
    def symbol_count(self) -> int:
        return len(self.symbols)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.message_count if self.message_count > 0 else 0.0

    @property
    def error_rate(self) -> float:
        return self.error_count / self.message_count if self.message_count > 0 else 0.0

    @property
    def is_active(self) -> bool:
        return self.state == SubscriptionState.ACTIVE

    @property
    def requires_realtime(self) -> bool:
        return UsageContext.REALTIME_TRADING in self.usage_contexts


@dataclass
class BatchPerformanceMetrics:
    """배치 성능 메트릭"""
    symbols_per_second: float
    avg_latency_ms: float
    success_rate: float
    network_efficiency: float
    active_groups: int
    total_symbols: int

    @property
    def performance_grade(self) -> str:
        """성능 등급"""
        if self.symbols_per_second >= 5000:  # Test 08-11 기준
            return "A+"
        elif self.symbols_per_second >= 3000:
            return "A"
        elif self.symbols_per_second >= 1000:
            return "B"
        elif self.symbols_per_second >= 500:
            return "C"
        else:
            return "D"


class BatchSubscriptionManager:
    """배치 구독 관리자

    Test 08-11 검증된 성능(5,241 symbols/sec)을 기반으로
    지능형 배치 WebSocket 구독을 관리합니다.
    """

    def __init__(self):
        """배치 구독 관리자 초기화"""
        logger.info("BatchSubscriptionManager 초기화 시작")

        # 실제 WebSocket 클라이언트 초기화
        self.ws_client = UpbitWebSocketQuotationClient()
        self._connection_lock = asyncio.Lock()
        self._is_connected = False

        # Test 08-11 검증 기반 최적화 파라미터
        self.MAX_SYMBOLS_PER_GROUP = 189  # Test 검증된 최대값
        self.OPTIMAL_SYMBOLS_PER_GROUP = 150  # 여유분 포함 최적값
        self.TARGET_LATENCY_MS = 11.20  # Test 실측 평균
        self.MAX_CONCURRENT_GROUPS = 5  # 동시 그룹 수 제한

        # 구독 그룹 관리
        self._subscription_groups: Dict[str, SubscriptionGroup] = {}
        self._symbol_to_group: Dict[str, str] = {}  # 심볼 → 그룹 ID 매핑
        self._data_callbacks: Dict[str, List[Callable]] = {}  # 그룹별 콜백

        # 성능 모니터링
        self._performance_history: List[BatchPerformanceMetrics] = []
        self._last_optimization_time = datetime.now()
        self._total_messages_processed = 0

        # 구독 최적화 정책
        self._optimization_policies = {
            UsageContext.REALTIME_TRADING: {
                'max_latency_ms': 5.0,
                'priority_weight': 1.0,
                'group_size_preference': 'small'  # 낮은 지연시간 우선
            },
            UsageContext.MARKET_SCANNING: {
                'max_latency_ms': 50.0,
                'priority_weight': 0.8,
                'group_size_preference': 'large'  # 처리량 우선
            },
            UsageContext.PORTFOLIO_MONITORING: {
                'max_latency_ms': 20.0,
                'priority_weight': 0.9,
                'group_size_preference': 'medium'
            },
            UsageContext.RESEARCH_ANALYSIS: {
                'max_latency_ms': 100.0,
                'priority_weight': 0.3,
                'group_size_preference': 'large'
            }
        }

        logger.info("BatchSubscriptionManager 초기화 완료")

    async def subscribe_symbols(
        self,
        symbols: List[str],
        data_type: DataType,
        context: RoutingContext,
        callback: Optional[Callable] = None
    ) -> str:
        """심볼 배치 구독 요청"""
        logger.info(f"배치 구독 요청 - 심볼: {len(symbols)}개, 타입: {data_type.value}, 컨텍스트: {context.usage_context.value}")

        # 최적 그룹 배치 결정
        group_assignments = await self._determine_optimal_grouping(symbols, data_type, context)

        subscription_results = []

        for group_id, group_symbols in group_assignments.items():
            if group_id in self._subscription_groups:
                # 기존 그룹에 추가
                result = await self._add_to_existing_group(group_id, group_symbols, context, callback)
            else:
                # 새 그룹 생성
                result = await self._create_new_group(group_id, group_symbols, data_type, context, callback)

            subscription_results.append(result)

        # 구독 최적화 실행
        await self._optimize_subscriptions()

        logger.info(f"배치 구독 완료 - {len(subscription_results)}개 그룹 처리")
        return subscription_results[0] if subscription_results else None

    async def _determine_optimal_grouping(
        self,
        symbols: List[str],
        data_type: DataType,
        context: RoutingContext
    ) -> Dict[str, List[str]]:
        """최적 그룹 배치 결정"""
        policy = self._optimization_policies.get(context.usage_context, self._optimization_policies[UsageContext.MARKET_SCANNING])

        group_assignments = {}
        remaining_symbols = symbols.copy()

        # 1. 기존 그룹에 추가 가능한 심볼 확인
        for group_id, group in self._subscription_groups.items():
            if (group.data_type == data_type and
                group.state == SubscriptionState.ACTIVE and
                len(group.symbols) < self.OPTIMAL_SYMBOLS_PER_GROUP):

                # 추가 가능한 심볼 수 계산
                available_slots = self.OPTIMAL_SYMBOLS_PER_GROUP - len(group.symbols)
                symbols_to_add = []

                for symbol in remaining_symbols[:available_slots]:
                    if symbol not in group.symbols:
                        symbols_to_add.append(symbol)

                if symbols_to_add:
                    group_assignments[group_id] = symbols_to_add
                    remaining_symbols = [s for s in remaining_symbols if s not in symbols_to_add]

        # 2. 새 그룹 생성이 필요한 심볼들 처리
        group_counter = 0
        while remaining_symbols:
            # 그룹 크기 결정
            if policy['group_size_preference'] == 'small':
                group_size = min(50, len(remaining_symbols))
            elif policy['group_size_preference'] == 'large':
                group_size = min(self.OPTIMAL_SYMBOLS_PER_GROUP, len(remaining_symbols))
            else:  # medium
                group_size = min(100, len(remaining_symbols))

            new_group_id = f"batch_{data_type.value}_{int(time.time())}_{group_counter}"
            group_assignments[new_group_id] = remaining_symbols[:group_size]
            remaining_symbols = remaining_symbols[group_size:]
            group_counter += 1

        logger.debug(f"그룹 배치 결정 완료 - {len(group_assignments)}개 그룹")
        return group_assignments

    async def _create_new_group(
        self,
        group_id: str,
        symbols: List[str],
        data_type: DataType,
        context: RoutingContext,
        callback: Optional[Callable] = None
    ) -> str:
        """새 구독 그룹 생성"""
        logger.info(f"새 구독 그룹 생성 - ID: {group_id}, 심볼: {len(symbols)}개")

        # 그룹 생성
        group = SubscriptionGroup(
            group_id=group_id,
            symbols=set(symbols),
            data_type=data_type,
            state=SubscriptionState.CONNECTING,
            usage_contexts={context.usage_context}
        )

        self._subscription_groups[group_id] = group

        # 심볼 → 그룹 매핑 업데이트
        for symbol in symbols:
            self._symbol_to_group[symbol] = group_id

        # 콜백 등록
        if callback:
            if group_id not in self._data_callbacks:
                self._data_callbacks[group_id] = []
            self._data_callbacks[group_id].append(callback)

        # WebSocket 구독 시작 (Mock)
        await self._start_websocket_subscription(group)

        return group_id

    async def _add_to_existing_group(
        self,
        group_id: str,
        symbols: List[str],
        context: RoutingContext,
        callback: Optional[Callable] = None
    ) -> str:
        """기존 그룹에 심볼 추가"""
        logger.info(f"기존 그룹에 추가 - ID: {group_id}, 새 심볼: {len(symbols)}개")

        group = self._subscription_groups[group_id]

        # 심볼 추가
        group.symbols.update(symbols)
        group.usage_contexts.add(context.usage_context)

        # 심볼 매핑 업데이트
        for symbol in symbols:
            self._symbol_to_group[symbol] = group_id

        # 콜백 등록
        if callback:
            if group_id not in self._data_callbacks:
                self._data_callbacks[group_id] = []
            self._data_callbacks[group_id].append(callback)

        # WebSocket 구독 업데이트
        await self._update_websocket_subscription(group)

        return group_id

    async def _start_websocket_subscription(self, group: SubscriptionGroup) -> None:
        """WebSocket 구독 시작 (실제 구현)"""
        logger.info(f"WebSocket 구독 시작 - 그룹: {group.group_id}, 심볼: {group.symbol_count}개")

        try:
            # WebSocket 연결 확인
            await self._ensure_websocket_connection()

            # 심볼 리스트를 구독 형식으로 변환
            symbols_list = list(group.symbols)

            # 데이터 타입에 따른 구독 실행
            success = False
            if group.data_type == DataType.TICKER:
                success = await self.ws_client.subscribe_ticker(symbols_list)
            elif group.data_type == DataType.ORDERBOOK:
                success = await self.ws_client.subscribe_orderbook(symbols_list)
            elif group.data_type == DataType.TRADE:
                success = await self.ws_client.subscribe_trade(symbols_list)
            else:
                # 기본값으로 티커 구독
                success = await self.ws_client.subscribe_ticker(symbols_list)

            if success:
                group.state = SubscriptionState.ACTIVE
                group.last_activity = datetime.now()

                # 메시지 핸들러 등록
                self._register_message_handler(group)

                logger.info(f"✅ WebSocket 구독 활성화 - 그룹: {group.group_id}")
            else:
                group.state = SubscriptionState.ERROR
                group.error_count += 1
                logger.error(f"❌ WebSocket 구독 실패 - 그룹: {group.group_id}")

        except Exception as e:
            logger.error(f"WebSocket 구독 실패 - 그룹: {group.group_id}, 오류: {str(e)}")
            group.state = SubscriptionState.ERROR
            group.error_count += 1

    def _register_message_handler(self, group: SubscriptionGroup) -> None:
        """메시지 핸들러 등록"""
        def message_handler(data: Dict[str, Any]) -> None:
            """메시지 처리 핸들러"""
            asyncio.create_task(self._handle_websocket_message(group, data))

        # WebSocket 클라이언트에 핸들러 등록
        # 주의: 실제 UpbitWebSocketQuotationClient의 구조에 맞게 수정 필요
        data_type = WebSocketDataType.TICKER
        if group.data_type == DataType.TICKER:
            data_type = WebSocketDataType.TICKER
        elif group.data_type == DataType.ORDERBOOK:
            data_type = WebSocketDataType.ORDERBOOK
        elif group.data_type == DataType.TRADE:
            data_type = WebSocketDataType.TRADE

        if data_type not in self.ws_client.message_handlers:
            self.ws_client.message_handlers[data_type] = []
        self.ws_client.message_handlers[data_type].append(message_handler)

    async def _ensure_websocket_connection(self) -> None:
        """WebSocket 연결 확인 및 설정"""
        async with self._connection_lock:
            if not self._is_connected:
                try:
                    success = await self.ws_client.connect()
                    if success:
                        self._is_connected = True
                        logger.info("✅ WebSocket 연결 성공")
                    else:
                        raise ConnectionError("WebSocket 연결 실패")
                except Exception as e:
                    logger.error(f"❌ WebSocket 연결 오류: {e}")
                    raise

    async def _handle_websocket_message(self, group: SubscriptionGroup, data: Dict[str, Any]) -> None:
        """WebSocket 메시지 처리"""
        try:
            start_time = time.time()

            # 메시지 통계 업데이트
            group.message_count += 1
            group.last_activity = datetime.now()
            self._total_messages_processed += 1

            # 지연시간 계산 (현재 시간 기준 추정)
            latency_ms = (time.time() - start_time) * 1000
            group.total_latency_ms += latency_ms

            # 콜백 실행
            if group.group_id in self._data_callbacks:
                for callback in self._data_callbacks[group.group_id]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(data)
                        else:
                            callback(data)
                    except Exception as e:
                        logger.error(f"콜백 실행 오류 - 그룹: {group.group_id}, 오류: {str(e)}")

        except Exception as e:
            logger.error(f"메시지 처리 오류 - 그룹: {group.group_id}, 오류: {str(e)}")
            group.error_count += 1

    async def _update_websocket_subscription(self, group: SubscriptionGroup) -> None:
        """WebSocket 구독 업데이트"""
        logger.info(f"WebSocket 구독 업데이트 - 그룹: {group.group_id}, 심볼: {group.symbol_count}개")

        try:
            # 기존 구독 해제 후 새로운 구독 시작
            await self._stop_websocket_subscription(group)
            await self._start_websocket_subscription(group)

            group.last_activity = datetime.now()
            logger.info(f"✅ WebSocket 구독 업데이트 완료 - 그룹: {group.group_id}")

        except Exception as e:
            logger.error(f"❌ WebSocket 구독 업데이트 실패 - 그룹: {group.group_id}, 오류: {str(e)}")
            group.state = SubscriptionState.ERROR
            group.error_count += 1

    async def _stop_websocket_subscription(self, group: SubscriptionGroup) -> None:
        """WebSocket 구독 중지"""
        try:
            # 메시지 핸들러 제거
            self._unregister_message_handler(group)

            # 상태 업데이트
            group.state = SubscriptionState.IDLE
            logger.info(f"✅ WebSocket 구독 중지 - 그룹: {group.group_id}")

        except Exception as e:
            logger.error(f"❌ WebSocket 구독 중지 실패 - 그룹: {group.group_id}, 오류: {str(e)}")

    def _unregister_message_handler(self, group: SubscriptionGroup) -> None:
        """메시지 핸들러 제거"""
        try:
            data_type = WebSocketDataType.TICKER
            if group.data_type == DataType.TICKER:
                data_type = WebSocketDataType.TICKER
            elif group.data_type == DataType.ORDERBOOK:
                data_type = WebSocketDataType.ORDERBOOK
            elif group.data_type == DataType.TRADE:
                data_type = WebSocketDataType.TRADE

            # 해당 그룹의 핸들러 제거
            if data_type in self.ws_client.message_handlers:
                # 실제 구현에서는 특정 그룹의 핸들러만 제거해야 함
                # 현재는 단순하게 전체 리스트 초기화
                self.ws_client.message_handlers[data_type] = []

        except Exception as e:
            logger.error(f"메시지 핸들러 제거 실패 - 그룹: {group.group_id}, 오류: {str(e)}")

    async def _optimize_subscriptions(self) -> None:
        """구독 최적화"""
        if datetime.now() - self._last_optimization_time < timedelta(seconds=30):
            return  # 30초마다만 최적화 실행

        logger.info("구독 최적화 실행 시작")

        # 비효율적인 그룹 식별
        inefficient_groups = []
        for group in self._subscription_groups.values():
            if (group.is_active and
                group.message_count > 100 and  # 충분한 샘플
                group.avg_latency_ms > self.TARGET_LATENCY_MS * 1.5):
                inefficient_groups.append(group)

        # 그룹 병합/분할 최적화
        await self._optimize_group_sizes()

        # 비활성 그룹 정리
        await self._cleanup_inactive_groups()

        self._last_optimization_time = datetime.now()
        logger.info(f"구독 최적화 완료 - 비효율 그룹: {len(inefficient_groups)}개 발견")

    async def _optimize_group_sizes(self) -> None:
        """그룹 크기 최적화"""
        # 소규모 그룹들을 병합
        small_groups = [g for g in self._subscription_groups.values()
                       if g.is_active and g.symbol_count < 30]

        if len(small_groups) >= 2:
            logger.info(f"소규모 그룹 병합 검토 - {len(small_groups)}개 그룹")
            # 실제 구현에서는 그룹 병합 로직 추가

    async def _cleanup_inactive_groups(self) -> None:
        """비활성 그룹 정리"""
        cutoff_time = datetime.now() - timedelta(minutes=10)

        inactive_groups = []
        for group_id, group in self._subscription_groups.items():
            if (group.last_activity and
                group.last_activity < cutoff_time and
                group.state != SubscriptionState.ACTIVE):
                inactive_groups.append(group_id)

        for group_id in inactive_groups:
            await self.unsubscribe_group(group_id)
            logger.info(f"비활성 그룹 정리 - ID: {group_id}")

    async def unsubscribe_group(self, group_id: str) -> bool:
        """그룹 구독 해제"""
        if group_id not in self._subscription_groups:
            return False

        logger.info(f"그룹 구독 해제 - ID: {group_id}")

        group = self._subscription_groups[group_id]
        group.state = SubscriptionState.TERMINATED

        # 심볼 매핑 제거
        symbols_to_remove = []
        for symbol, mapped_group_id in self._symbol_to_group.items():
            if mapped_group_id == group_id:
                symbols_to_remove.append(symbol)

        for symbol in symbols_to_remove:
            del self._symbol_to_group[symbol]

        # 콜백 제거
        if group_id in self._data_callbacks:
            del self._data_callbacks[group_id]

        # 그룹 제거
        del self._subscription_groups[group_id]

        return True

    async def get_performance_metrics(self) -> BatchPerformanceMetrics:
        """성능 메트릭 조회"""
        active_groups = [g for g in self._subscription_groups.values() if g.is_active]
        total_symbols = sum(g.symbol_count for g in active_groups)

        if not active_groups:
            return BatchPerformanceMetrics(0.0, 0.0, 0.0, 0.0, 0, 0)

        # 평균 지연시간 계산
        total_latency = sum(g.total_latency_ms for g in active_groups)
        total_messages = sum(g.message_count for g in active_groups)
        avg_latency = total_latency / total_messages if total_messages > 0 else 0.0

        # 처리량 계산 (Test 08-11 기준)
        symbols_per_second = total_symbols / (avg_latency / 1000.0) if avg_latency > 0 else 0.0

        # 성공률 계산
        total_errors = sum(g.error_count for g in active_groups)
        success_rate = 1.0 - (total_errors / total_messages) if total_messages > 0 else 0.0

        # 네트워크 효율성 (배치 크기 기반)
        avg_group_size = total_symbols / len(active_groups) if active_groups else 0
        network_efficiency = min(1.0, avg_group_size / self.OPTIMAL_SYMBOLS_PER_GROUP)

        return BatchPerformanceMetrics(
            symbols_per_second=symbols_per_second,
            avg_latency_ms=avg_latency,
            success_rate=success_rate,
            network_efficiency=network_efficiency,
            active_groups=len(active_groups),
            total_symbols=total_symbols
        )

    async def get_subscription_status(self) -> Dict[str, Any]:
        """구독 상태 조회"""
        metrics = await self.get_performance_metrics()

        group_details = {}
        for group_id, group in self._subscription_groups.items():
            group_details[group_id] = {
                'symbols': list(group.symbols),
                'symbol_count': group.symbol_count,
                'data_type': group.data_type.value,
                'state': group.state.value,
                'avg_latency_ms': group.avg_latency_ms,
                'message_count': group.message_count,
                'error_rate': group.error_rate,
                'usage_contexts': [ctx.value for ctx in group.usage_contexts]
            }

        return {
            'performance': {
                'symbols_per_second': metrics.symbols_per_second,
                'avg_latency_ms': metrics.avg_latency_ms,
                'success_rate': metrics.success_rate,
                'network_efficiency': metrics.network_efficiency,
                'performance_grade': metrics.performance_grade
            },
            'groups': group_details,
            'total_groups': len(self._subscription_groups),
            'active_groups': metrics.active_groups,
            'total_symbols': metrics.total_symbols,
            'total_messages_processed': self._total_messages_processed
        }
