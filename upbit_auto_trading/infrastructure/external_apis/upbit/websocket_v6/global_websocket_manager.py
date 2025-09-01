"""
GlobalWebSocketManager v6.0 (최종 안정화 버전)
================================================

WebSocket v6의 핵심 중앙 관리자 (싱글톤)
v5 호환성 완전 제거, 순수 v6 아키텍처
"""

import asyncio
import weakref
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger

# Rate Limiter 연동 (선택적)
try:
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
        get_global_rate_limiter,
        UpbitRateLimitGroup
    )
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False

from .types import (
    DataType, WebSocketType, GlobalManagerState, ConnectionState,
    BaseWebSocketEvent, TradeEvent, MyOrderEvent, MyAssetEvent,
    SubscriptionSpec, ComponentSubscription,
    PerformanceMetrics, HealthStatus,
    create_ticker_event, create_orderbook_event,
    get_data_type_from_message
)
from .exceptions import SubscriptionError, RecoveryError
from .config import get_config
from .subscription_state_manager import SubscriptionStateManager
from .data_routing_engine import DataRoutingEngine
from .native_websocket_client import NativeWebSocketClient, create_public_client, create_private_client


@dataclass
class ConnectionMetrics:
    """연결별 메트릭스"""
    connection_type: WebSocketType
    is_connected: bool = False
    connect_time: Optional[float] = None
    last_message_time: Optional[float] = None
    message_count: int = 0
    error_count: int = 0
    reconnect_count: int = 0
    bytes_received: int = 0
    current_subscriptions: int = 0

    @property
    def uptime_seconds(self) -> float:
        """연결 지속 시간"""
        if not self.is_connected or not self.connect_time:
            return 0.0
        return time.time() - self.connect_time

    @property
    def messages_per_second(self) -> float:
        """초당 메시지 수"""
        if not self.is_connected or self.uptime_seconds <= 0:
            return 0.0
        return self.message_count / self.uptime_seconds

    @property
    def error_rate(self) -> float:
        """에러율 (0.0 ~ 1.0)"""
        if self.message_count == 0:
            return 0.0
        return self.error_count / (self.message_count + self.error_count)

    @property
    def health_score(self) -> float:
        """연결 건강도 점수 (0.0 ~ 1.0)"""
        if not self.is_connected:
            return 0.0

        # 기본 점수
        score = 0.5

        # 연결 유지 시간 보너스 (최대 30분)
        uptime_bonus = min(self.uptime_seconds / 1800, 0.3)
        score += uptime_bonus

        # 에러율 패널티
        error_penalty = self.error_rate * 0.4
        score -= error_penalty

        # 메시지 활동 보너스
        if self.message_count > 0:
            score += 0.2

        return max(0.0, min(1.0, score))

class EpochManager:
    """재연결 시 데이터 순서 보장을 위한 Epoch 관리"""

    def __init__(self):
        self._current_epochs: Dict[WebSocketType, int] = {
            WebSocketType.PUBLIC: 0,
            WebSocketType.PRIVATE: 0
        }
        self._lock = asyncio.Lock()

    async def increment_epoch(self, connection_type: WebSocketType) -> int:
        """재연결 시 Epoch 증가"""
        async with self._lock:
            self._current_epochs[connection_type] += 1
            return self._current_epochs[connection_type]

    def get_current_epoch(self, connection_type: WebSocketType) -> int:
        """현재 Epoch 반환"""
        return self._current_epochs[connection_type]

    def is_current_epoch(self, connection_type: WebSocketType, epoch: int) -> bool:
        """주어진 Epoch가 현재 Epoch인지 확인 (백워드 호환성)"""
        return epoch == self._current_epochs[connection_type]

    def reset_epoch(self, connection_type: WebSocketType) -> None:
        """Epoch 리셋 (테스트용)"""
        self._current_epochs[connection_type] = 0
class GlobalWebSocketManager:
    """
    WebSocket v6.0 전역 관리자 (싱글톤)
    """

    _instance: Optional['GlobalWebSocketManager'] = None
    _init_lock = asyncio.Lock()

    def __new__(cls) -> 'GlobalWebSocketManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 중복 초기화 방지
        if hasattr(self, '_initialized'):
            return

        self.logger = create_component_logger("GlobalWebSocketManager")
        self.config = get_config()

        # 상태 관리
        self._state = GlobalManagerState.INITIALIZING
        self._startup_time = time.time()
        self._shutdown_requested = False

        # 핵심 컴포넌트
        self.subscription_manager = SubscriptionStateManager()
        self.data_router = DataRoutingEngine(self.config.backpressure)
        self.epoch_manager = EpochManager()

        # 네이티브 WebSocket 클라이언트
        self._public_client: Optional[NativeWebSocketClient] = None
        self._private_client: Optional[NativeWebSocketClient] = None

        # 연결 상태 추적
        self._connection_metrics: Dict[WebSocketType, ConnectionMetrics] = {
            WebSocketType.PUBLIC: ConnectionMetrics(WebSocketType.PUBLIC),
            WebSocketType.PRIVATE: ConnectionMetrics(WebSocketType.PRIVATE)
        }

        # 컴포넌트 생명주기 관리 (WeakRef)
        self._component_refs: Dict[str, weakref.ReferenceType] = {}

        # Rate Limiter (선택적)
        self._rate_limiter = None
        if RATE_LIMITER_AVAILABLE:
            try:
                self._rate_limiter = get_global_rate_limiter()
            except Exception as e:
                self.logger.warning(f"Rate Limiter 초기화 실패: {e}")

        self._initialized = True
        self.logger.info("GlobalWebSocketManager v6.0 초기화 완료")

    @classmethod
    async def get_instance(cls) -> 'GlobalWebSocketManager':
        """스레드 안전한 싱글톤 인스턴스 획득"""
        async with cls._init_lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance._async_initialize()
            return cls._instance

    async def _async_initialize(self):
        """비동기 초기화 작업"""
        try:
            self.logger.info("비동기 초기화 시작")

            # 구독 상태 관리자에 변경 콜백 등록
            self.subscription_manager.add_change_callback(
                self._on_subscription_changes_sync
            )

            # 데이터 라우터 시작
            await self.data_router.start()

            self._state = GlobalManagerState.IDLE
            self.logger.info("GlobalWebSocketManager 비동기 초기화 완료")

        except Exception as e:
            self.logger.error(f"비동기 초기화 실패: {e}")
            self._state = GlobalManagerState.ERROR
            raise RecoveryError(f"매니저 초기화 실패: {e}")

    def _on_subscription_changes_sync(self, changes):
        """구독 변경 이벤트 핸들러 (동기 래퍼)"""
        asyncio.create_task(self._on_subscription_changes(changes))

    async def _on_subscription_changes(self, changes):
        """구독 변경 이벤트 핸들러"""
        try:
            await self._apply_subscription_changes(changes)
        except Exception as e:
            self.logger.error(f"구독 변경 적용 실패: {e}")

    # =============================================================================
    # WebSocket 연결 관리
    # =============================================================================

    async def initialize_public_connection(self) -> bool:
        """Public WebSocket 연결 초기화"""
        try:
            self.logger.info("Public WebSocket 연결 초기화")

            # 메시지 핸들러 정의 (동기 래퍼)
            def public_message_handler(message_data: Dict[str, Any]) -> None:
                asyncio.create_task(
                    self._handle_received_message(message_data, WebSocketType.PUBLIC)
                )

            # 클라이언트 생성
            self._public_client = create_public_client(
                message_handler=public_message_handler,
                enable_compression=True,
                enable_simple_format=True
            )

            # 연결 시도
            success = await self._public_client.connect()
            if success:
                # 메트릭스 업데이트
                metrics = self._connection_metrics[WebSocketType.PUBLIC]
                metrics.is_connected = True
                metrics.connect_time = time.time()
                metrics.reconnect_count += 1

                # Epoch 증가
                await self.epoch_manager.increment_epoch(WebSocketType.PUBLIC)

                self.logger.info("Public WebSocket 연결 완료")
                return True
            else:
                self.logger.error("Public WebSocket 연결 실패")
                return False

        except Exception as e:
            self.logger.error(f"Public WebSocket 연결 실패: {e}")
            return False

    async def initialize_private_connection(self) -> bool:
        """Private WebSocket 연결 초기화"""
        try:
            self.logger.info("Private WebSocket 연결 초기화")

            # 메시지 핸들러 정의 (동기 래퍼)
            def private_message_handler(message_data: Dict[str, Any]) -> None:
                asyncio.create_task(
                    self._handle_received_message(message_data, WebSocketType.PRIVATE)
                )

            # 클라이언트 생성
            self._private_client = create_private_client(
                message_handler=private_message_handler,
                enable_compression=True,
                enable_simple_format=True
            )

            # 연결 시도
            success = await self._private_client.connect()
            if success:
                # 메트릭스 업데이트
                metrics = self._connection_metrics[WebSocketType.PRIVATE]
                metrics.is_connected = True
                metrics.connect_time = time.time()
                metrics.reconnect_count += 1

                # Epoch 증가
                await self.epoch_manager.increment_epoch(WebSocketType.PRIVATE)

                self.logger.info("Private WebSocket 연결 완료")
                return True
            else:
                self.logger.error("Private WebSocket 연결 실패")
                return False

        except Exception as e:
            self.logger.error(f"Private WebSocket 연결 실패: {e}")
            return False

    async def _handle_received_message(
        self,
        message_data: Dict[str, Any],
        connection_type: WebSocketType
    ) -> None:
        """수신된 메시지 처리"""
        try:
            # 현재 Epoch 가져오기
            current_epoch = self.epoch_manager.get_current_epoch(connection_type)

            # v6 이벤트로 변환
            v6_event = self._convert_to_v6_event(message_data, current_epoch, connection_type)

            if v6_event:
                # 데이터 타입 추론
                data_type = get_data_type_from_message(message_data)
                if data_type:
                    # v6 데이터 라우터로 분배
                    await self.data_router.route_event(v6_event, data_type)

                # 메트릭스 업데이트
                metrics = self._connection_metrics[connection_type]
                metrics.message_count += 1
                metrics.last_message_time = time.time()

        except Exception as e:
            self.logger.error(f"메시지 처리 실패: {e}")
            metrics = self._connection_metrics[connection_type]
            metrics.error_count += 1

    def _convert_to_v6_event(
        self,
        message_data: Dict[str, Any],
        epoch: int,
        connection_type: WebSocketType
    ) -> Optional[BaseWebSocketEvent]:
        """업비트 메시지를 v6 이벤트로 변환"""
        try:
            # 메시지 타입 확인
            msg_type = message_data.get('type', '').lower()

            if msg_type == 'ticker':
                return create_ticker_event(message_data, epoch, connection_type)
            elif msg_type == 'orderbook':
                return create_orderbook_event(message_data, epoch, connection_type)
            elif msg_type == 'trade':
                return TradeEvent(
                    epoch=epoch,
                    timestamp=time.time(),
                    connection_type=connection_type,
                    symbol=message_data.get('code'),
                    trade_price=Decimal(str(message_data.get('trade_price', 0))),
                    trade_volume=Decimal(str(message_data.get('trade_volume', 0))),
                    ask_bid=message_data.get('ask_bid', ''),
                    trade_timestamp=message_data.get('trade_timestamp', 0),
                    sequential_id=message_data.get('sequential_id', 0),
                    prev_closing_price=Decimal(str(
                        message_data.get('prev_closing_price', 0)
                    ))
                )
            elif msg_type in ['myorder', 'my_order']:
                # 긴 Decimal 변환을 헬퍼 함수로 처리
                def safe_decimal(value, default=0):
                    return (Decimal(str(value)) if value is not None
                           else Decimal(str(default)))

                return MyOrderEvent(
                    epoch=epoch,
                    timestamp=time.time(),
                    connection_type=connection_type,
                    symbol=message_data.get('market', ''),
                    uuid=message_data.get('uuid', ''),
                    order_type=message_data.get('order_type', ''),
                    ord_type=message_data.get('ord_type', ''),
                    price=safe_decimal(message_data.get('price')) if message_data.get('price') else None,
                    avg_price=safe_decimal(message_data.get('avg_price')) if message_data.get('avg_price') else None,
                    state=message_data.get('state', ''),
                    market=message_data.get('market', ''),
                    created_at=message_data.get('created_at', ''),
                    volume=safe_decimal(message_data.get('volume')) if message_data.get('volume') else None,
                    remaining_volume=safe_decimal(message_data.get('remaining_volume')) if message_data.get('remaining_volume') else None,
                    reserved_fee=safe_decimal(message_data.get('reserved_fee')) if message_data.get('reserved_fee') else None,
                    remaining_fee=safe_decimal(message_data.get('remaining_fee')) if message_data.get('remaining_fee') else None,
                    paid_fee=safe_decimal(message_data.get('paid_fee')) if message_data.get('paid_fee') else None,
                    locked=safe_decimal(message_data.get('locked')) if message_data.get('locked') else None,
                    executed_volume=safe_decimal(message_data.get('executed_volume')) if message_data.get('executed_volume') else None,
                    trades_count=message_data.get('trades_count')
                )
            elif msg_type in ['myasset', 'my_asset']:
                return MyAssetEvent(
                    epoch=epoch,
                    timestamp=time.time(),
                    connection_type=connection_type,
                    symbol=message_data.get('currency', ''),
                    currency=message_data.get('currency', ''),
                    balance=Decimal(str(message_data.get('balance', 0))),
                    locked=Decimal(str(message_data.get('locked', 0))),
                    avg_buy_price=Decimal(str(message_data.get('avg_buy_price', 0))) if message_data.get('avg_buy_price') else None,
                    avg_buy_price_modified=message_data.get('avg_buy_price_modified'),
                    unit_currency=message_data.get('unit_currency')
                )

            return None

        except Exception as e:
            self.logger.error(f"이벤트 변환 실패: {e}")
            return None

    # =============================================================================
    # 컴포넌트 생명주기 관리
    # =============================================================================

    async def register_component(
        self,
        component_id: str,
        component_instance: Any,
        subscriptions: List[SubscriptionSpec],
        callback: Callable[[BaseWebSocketEvent], None]
    ) -> ComponentSubscription:
        """컴포넌트 등록 및 구독 설정"""
        try:
            self.logger.info(f"컴포넌트 등록 시작: {component_id}")

            # WeakRef 생성 및 정리 콜백 설정
            def cleanup_callback(ref):
                asyncio.create_task(self._cleanup_component(component_id))

            weak_ref = weakref.ref(component_instance, cleanup_callback)
            self._component_refs[component_id] = weak_ref

            # 컴포넌트 구독 생성
            component_subscription = ComponentSubscription(
                component_id=component_id,
                subscription_specs=subscriptions,
                callback=callback,
                created_at=time.time(),
                is_active=True
            )

            # 구독 상태 관리자에 등록
            await self.subscription_manager.register_component(
                component_id, subscriptions, weak_ref
            )

            # 데이터 라우터에 콜백 등록
            for spec in subscriptions:
                consumer_id = f"{component_id}_{spec.data_type.value}"
                self.data_router.register_data_consumer(
                    consumer_id,
                    callback,
                    component_id,
                    spec.data_type
                )

            self.logger.info(f"컴포넌트 등록 완료: {component_id}, 구독 {len(subscriptions)}개")
            return component_subscription

        except Exception as e:
            self.logger.error(f"컴포넌트 등록 실패 {component_id}: {e}")
            raise SubscriptionError(f"컴포넌트 등록 오류: {e}")

    async def unregister_component(self, component_id: str) -> None:
        """컴포넌트 등록 해제"""
        try:
            self.logger.info(f"컴포넌트 등록 해제: {component_id}")

            # 구독 상태 관리자에서 제거
            await self.subscription_manager.unregister_component(component_id)

            # 데이터 라우터에서 콜백 제거
            for data_type in DataType:
                consumer_id = f"{component_id}_{data_type.value}"
                try:
                    self.data_router.unregister_data_consumer(consumer_id)
                except Exception:
                    pass  # 존재하지 않는 경우 무시

            # WeakRef 정리
            if component_id in self._component_refs:
                del self._component_refs[component_id]

            self.logger.info(f"컴포넌트 등록 해제 완료: {component_id}")

        except Exception as e:
            self.logger.error(f"컴포넌트 등록 해제 실패 {component_id}: {e}")
            raise SubscriptionError(f"컴포넌트 해제 오류: {e}")

    async def _cleanup_component(self, component_id: str) -> None:
        """컴포넌트 자동 정리 (WeakRef 콜백)"""
        try:
            self.logger.info(f"컴포넌트 자동 정리: {component_id}")
            await self.unregister_component(component_id)
        except Exception as e:
            self.logger.error(f"컴포넌트 자동 정리 실패 {component_id}: {e}")

    # =============================================================================
    # 구독 관리
    # =============================================================================

    async def _apply_subscription_changes(self, changes) -> None:
        """구독 변경사항을 물리적 연결에 적용"""
        try:
            self.logger.info("구독 변경사항 적용 시작")

            # Rate Limiter 체크 (가용 시에만)
            if self._rate_limiter and RATE_LIMITER_AVAILABLE:
                total_changes = sum(
                    len(change.added_symbols) + len(change.removed_symbols)
                    for change in changes.values()
                )

                if total_changes > 0:
                    try:
                        rate_limiter = await self._rate_limiter
                        # Rate Limiter 호환성 처리
                        await rate_limiter.acquire("websocket", min(total_changes, 10))
                    except Exception as e:
                        self.logger.warning(f"Rate limiting 실패: {e}")            # Public 구독 적용
            public_changes = {
                data_type: change for data_type, change in changes.items()
                if data_type in [DataType.TICKER, DataType.ORDERBOOK, DataType.TRADE]
            }
            if public_changes and self._public_client:
                await self._apply_public_subscriptions()

            # Private 구독 적용
            private_changes = {
                data_type: change for data_type, change in changes.items()
                if data_type in [DataType.MY_ORDER, DataType.MY_ASSET]
            }
            if private_changes and self._private_client:
                await self._apply_private_subscriptions()

            self.logger.info("구독 변경사항 적용 완료")

        except Exception as e:
            self.logger.error(f"구독 변경사항 적용 실패: {e}")
            raise SubscriptionError(f"구독 적용 오류: {e}")

    async def _apply_public_subscriptions(self) -> None:
        """Public WebSocket 구독 적용"""
        try:
            if not self._public_client or not self._public_client.is_connected:
                return

            # 현재 활성 Public 구독 목록 생성
            active_subscriptions = self.subscription_manager.get_active_subscriptions(
                WebSocketType.PUBLIC
            )

            subscription_messages = []

            for data_type, subscription in active_subscriptions.items():
                if subscription.symbols:
                    message = {
                        "ticket": f"v6_{data_type.value}_{int(time.time())}",
                        "type": data_type.value,
                        "codes": list(subscription.symbols),
                        "isOnlySnapshot": False,
                        "isOnlyRealtime": True
                    }
                    subscription_messages.append(message)

            # 구독 메시지 전송
            if subscription_messages:
                success = await self._public_client.send_subscription(subscription_messages)
                if success:
                    self.logger.info(f"Public 구독 적용 완료: {len(subscription_messages)}개")
                else:
                    self.logger.error("Public 구독 전송 실패")

        except Exception as e:
            self.logger.error(f"Public 구독 적용 실패: {e}")

    async def _apply_private_subscriptions(self) -> None:
        """Private WebSocket 구독 적용"""
        try:
            if not self._private_client or not self._private_client.is_connected:
                return

            active_subscriptions = self.subscription_manager.get_active_subscriptions(
                WebSocketType.PRIVATE
            )

            subscription_messages = []

            for data_type, subscription in active_subscriptions.items():
                if data_type == DataType.MY_ORDER:
                    message = {
                        "ticket": f"v6_myorder_{int(time.time())}",
                        "type": "myOrder",
                        "isOnlySnapshot": False,
                        "isOnlyRealtime": True
                    }
                    subscription_messages.append(message)

                elif data_type == DataType.MY_ASSET:
                    message = {
                        "ticket": f"v6_myasset_{int(time.time())}",
                        "type": "myAsset",
                        "isOnlySnapshot": False,
                        "isOnlyRealtime": True
                    }
                    subscription_messages.append(message)

            # 구독 메시지 전송
            if subscription_messages:
                success = await self._private_client.send_subscription(subscription_messages)
                if success:
                    self.logger.info(f"Private 구독 적용 완료: {len(subscription_messages)}개")
                else:
                    self.logger.error("Private 구독 전송 실패")

        except Exception as e:
            self.logger.error(f"Private 구독 적용 실패: {e}")

    # =============================================================================
    # 상태 조회 및 모니터링
    # =============================================================================

    async def get_health_status(self) -> HealthStatus:
        """전체 시스템 헬스 상태 반환"""
        try:
            # 연결 상태 요약
            public_metrics = self._connection_metrics[WebSocketType.PUBLIC]
            private_metrics = self._connection_metrics[WebSocketType.PRIVATE]

            # 성능 메트릭스
            performance = PerformanceMetrics(
                connection_count=sum(1 for m in self._connection_metrics.values() if m.is_connected),
                uptime_seconds=time.time() - self._startup_time,
                messages_received_total=sum(m.message_count for m in self._connection_metrics.values()),
                active_components=len([ref for ref in self._component_refs.values() if ref() is not None])
            )

            # 건강도 계산
            is_healthy = (
                self._state in [GlobalManagerState.IDLE, GlobalManagerState.ACTIVE]
                and not self._shutdown_requested
            )

            status = "healthy" if is_healthy else "degraded"
            if self._state == GlobalManagerState.ERROR:
                status = "critical"

            return HealthStatus(
                status=status,
                public_connection=(
                    ConnectionState.CONNECTED
                    if public_metrics.is_connected
                    else ConnectionState.DISCONNECTED
                ),
                private_connection=(
                    ConnectionState.CONNECTED
                    if private_metrics.is_connected
                    else ConnectionState.DISCONNECTED
                ),
                active_subscriptions={},  # TODO: 구독 요약 추가
                performance=performance,
                timestamp=time.time()
            )

        except Exception as e:
            self.logger.error(f"헬스 상태 조회 실패: {e}")
            return HealthStatus(
                status="critical",
                public_connection=ConnectionState.ERROR,
                private_connection=ConnectionState.ERROR,
                active_subscriptions={},
                performance=PerformanceMetrics(),
                timestamp=time.time()
            )

    async def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭스 반환"""
        try:
            total_messages = sum(m.message_count for m in self._connection_metrics.values())
            uptime = time.time() - self._startup_time

            return PerformanceMetrics(
                connection_count=sum(1 for m in self._connection_metrics.values() if m.is_connected),
                uptime_seconds=uptime,
                messages_received_total=total_messages,
                messages_per_second=total_messages / max(uptime, 1),
                active_components=len([ref for ref in self._component_refs.values() if ref() is not None])
            )
        except Exception as e:
            self.logger.error(f"성능 메트릭스 조회 실패: {e}")
            return PerformanceMetrics()

    def get_connection_metrics(self) -> Dict[WebSocketType, ConnectionMetrics]:
        """연결별 메트릭스 반환"""
        return self._connection_metrics.copy()

    # =============================================================================
    # 종료 및 정리
    # =============================================================================

    async def shutdown(self, timeout: float = 30.0) -> None:
        """우아한 종료"""
        try:
            self.logger.info("GlobalWebSocketManager 종료 시작")
            self._shutdown_requested = True
            self._state = GlobalManagerState.SHUTTING_DOWN

            # 컴포넌트 정리
            for component_id in list(self._component_refs.keys()):
                try:
                    await self.unregister_component(component_id)
                except Exception as e:
                    self.logger.error(f"컴포넌트 정리 실패 {component_id}: {e}")

            # 하위 시스템 종료
            try:
                if hasattr(self.subscription_manager, 'cleanup'):
                    await self.subscription_manager.cleanup()
            except Exception as e:
                self.logger.warning(f"구독 관리자 정리 실패: {e}")

            await self.data_router.stop()

            # WebSocket 연결 정리
            if self._public_client:
                await self._public_client.disconnect()
            if self._private_client:
                await self._private_client.disconnect()

            self._state = GlobalManagerState.STOPPED
            self.logger.info("GlobalWebSocketManager 종료 완료")

        except Exception as e:
            self.logger.error(f"종료 중 오류: {e}")
            self._state = GlobalManagerState.ERROR

    # =============================================================================
    # 상태 프로퍼티
    # =============================================================================

    @property
    def state(self) -> GlobalManagerState:
        """현재 관리자 상태"""
        return self._state

    @property
    def is_healthy(self) -> bool:
        """시스템 건강 상태"""
        return (
            self._state in [GlobalManagerState.IDLE, GlobalManagerState.ACTIVE]
            and not self._shutdown_requested
        )

    @property
    def active_component_count(self) -> int:
        """활성 컴포넌트 수"""
        return len([ref for ref in self._component_refs.values() if ref() is not None])


# =============================================================================
# 전역 접근 헬퍼 함수
# =============================================================================

async def get_global_websocket_manager() -> GlobalWebSocketManager:
    """전역 웹소켓 매니저 인스턴스 획득"""
    return await GlobalWebSocketManager.get_instance()


def get_global_websocket_manager_sync() -> GlobalWebSocketManager:
    """전역 웹소켓 매니저 인스턴스 획득 (동기 버전)"""
    if GlobalWebSocketManager._instance is None:
        # 임시로 매니저 인스턴스 생성 (초기화 없이)
        manager = GlobalWebSocketManager.__new__(GlobalWebSocketManager)
        manager._initialized = False
        GlobalWebSocketManager._instance = manager
    return GlobalWebSocketManager._instance


def is_manager_available() -> bool:
    """매니저 사용 가능 여부 확인"""
    return (
        GlobalWebSocketManager._instance is not None
        and hasattr(GlobalWebSocketManager._instance, '_initialized')
        and GlobalWebSocketManager._instance._initialized
    )
