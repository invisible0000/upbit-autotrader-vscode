"""
글로벌 웹소켓 매니저 v6.0
=========================

WebSocket v6의 핵심 중앙 관리자 (싱글톤)
업비트 구독 덮어쓰기 문제를 완전히 해결하는 전역 관리 시스템

핵심 역할:
- 단일 Public/Private 연결 관리
- 전역 구독 상태 통합 및 최적화
- 데이터 라우팅 및 분배
- 장애 복구 및 자동 재연결
- 전역 Rate Limiter 연동
- WeakRef 기반 자동 리소스 정리

설계 원칙:
- Single Source of Truth (단일 진실 공급원)
- Zero Configuration (제로 설정)
- Graceful Degradation (우아한 성능 저하)
- Fail-Safe Design (안전 장치 설계)
"""

import asyncio
import weakref
import time
from typing import Dict, List, Optional, Set, Any, Callable, Union
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger

# Rate Limiter 연동
try:
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
        get_global_rate_limiter,
        UpbitRateLimitGroup
    )
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False

from .types import (
    DataType, WebSocketType, GlobalManagerState,
    BaseWebSocketEvent, TickerEvent, OrderbookEvent, TradeEvent,
    MyOrderEvent, MyAssetEvent, SubscriptionSpec, ComponentSubscription,
    PerformanceMetrics, HealthStatus
)
from .exceptions import (
    ConnectionError, SubscriptionError, RecoveryError
)
from .config import get_config
from .subscription_state_manager import SubscriptionStateManager
from .data_routing_engine import DataRoutingEngine


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
        """주어진 Epoch가 현재 Epoch인지 확인"""
        return epoch == self._current_epochs[connection_type]


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
        if self.uptime_seconds <= 0:
            return 0.0
        return self.message_count / self.uptime_seconds


class GlobalWebSocketManager:
    """
    WebSocket v6.0 전역 관리자 (싱글톤)

    전체 애플리케이션에서 단 하나의 인스턴스만 존재하며,
    모든 WebSocket 연결과 구독 상태를 중앙 관리합니다.

    주요 기능:
    - 업비트 Public/Private WebSocket 연결 관리
    - 여러 컴포넌트의 구독 요청 통합
    - 실시간 데이터 라우팅 및 분배
    - 자동 재연결 및 장애 복구
    - 메모리 누수 방지 (WeakRef 기반)
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

        # 물리적 WebSocket 연결 (v5 재사용)
        self._public_client: Optional[UpbitWebSocketPublicClient] = None
        self._private_client: Optional[UpbitWebSocketPrivateClient] = None

        # 연결 상태 추적
        self._connection_metrics: Dict[WebSocketType, ConnectionMetrics] = {
            WebSocketType.PUBLIC: ConnectionMetrics(WebSocketType.PUBLIC),
            WebSocketType.PRIVATE: ConnectionMetrics(WebSocketType.PRIVATE)
        }

        # 컴포넌트 생명주기 관리 (WeakRef)
        self._component_refs: Dict[str, weakref.ReferenceType] = {}
        self._component_cleanup_callbacks: Dict[str, Callable] = {}

        # 백그라운드 작업 관리
        self._background_tasks: Set[asyncio.Task] = set()

        # Rate Limiter 연동
        self._rate_limiter = None
        if RATE_LIMITER_AVAILABLE:
            self._rate_limiter = get_global_rate_limiter()

        # 성능 모니터링
        self._performance_metrics = PerformanceMetrics()
        self._last_metrics_update = time.time()

        self._initialized = True
        self.logger.info("GlobalWebSocketManager 초기화 완료")

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
                self._on_subscription_changes
            )

            # 데이터 라우터 시작
            await self.data_router.start()

            # 백그라운드 모니터링 작업 시작
            self._start_background_tasks()

            self._state = GlobalManagerState.IDLE
            self.logger.info("GlobalWebSocketManager 비동기 초기화 완료")

        except Exception as e:
            self.logger.error(f"비동기 초기화 실패: {e}")
            self._state = GlobalManagerState.ERROR
            raise RecoveryError(f"매니저 초기화 실패: {e}")

    def _start_background_tasks(self):
        """백그라운드 작업 시작"""
        tasks = [
            self._health_monitor_task(),
            self._metrics_collector_task(),
            self._connection_supervisor_task(),
            self._cleanup_monitor_task()
        ]

        for task in tasks:
            bg_task = asyncio.create_task(task)
            self._background_tasks.add(bg_task)
            # 작업 완료 시 자동 정리
            bg_task.add_done_callback(self._background_tasks.discard)

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
        """
        컴포넌트 등록 및 구독 설정

        Args:
            component_id: 고유 컴포넌트 식별자
            component_instance: 컴포넌트 인스턴스 (WeakRef 생성용)
            subscriptions: 구독 명세 목록
            callback: 데이터 수신 콜백

        Returns:
            ComponentSubscription: 생성된 컴포넌트 구독 정보
        """
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
                subscriptions=subscriptions,
                callback=callback,
                created_at=time.time(),
                is_active=True
            )

            # 구독 상태 관리자에 등록
            changes = await self.subscription_manager.register_component(
                component_id, subscriptions, weak_ref
            )

            # 데이터 라우터에 콜백 등록
            for spec in subscriptions:
                self.data_router.register_data_consumer(
                    f"{component_id}_{spec.data_type.value}_{spec.symbol}",
                    callback,
                    component_id,
                    spec.data_type
                )

            # 구독 변경 적용
            if changes:
                await self._apply_subscription_changes(changes)

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
            changes = await self.subscription_manager.unregister_component(component_id)

            # 데이터 라우터에서 콜백 제거
            # (consumer_id 패턴으로 모든 관련 콜백 제거)
            for consumer_id in list(self.data_router._fanout_hub._callbacks.keys()):
                if consumer_id.startswith(f"{component_id}_"):
                    self.data_router.unregister_data_consumer(consumer_id)

            # WeakRef 정리
            if component_id in self._component_refs:
                del self._component_refs[component_id]

            # 구독 변경 적용
            if changes:
                await self._apply_subscription_changes(changes)

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
    # 구독 관리 및 최적화
    # =============================================================================

    async def _on_subscription_changes(self, changes):
        """구독 변경 이벤트 핸들러"""
        try:
            await self._apply_subscription_changes(changes)
        except Exception as e:
            self.logger.error(f"구독 변경 적용 실패: {e}")

    async def _apply_subscription_changes(self, changes) -> None:
        """구독 변경사항을 물리적 연결에 적용"""
        try:
            self.logger.info("구독 변경사항 적용 시작")

            # Rate Limiter 체크
            if self._rate_limiter and RATE_LIMITER_AVAILABLE:
                # WebSocket 구독 요청에 대한 Rate Limit 체크
                total_changes = sum(
                    len(change.added_symbols) + len(change.removed_symbols)
                    for change in changes.values()
                )

                if total_changes > 0:
                    # Rate Limit 적용 (WebSocket 전용 그룹)
                    await self._rate_limiter.acquire(
                        group=UpbitRateLimitGroup.WEBSOCKET,
                        weight=min(total_changes, 10)  # 최대 10으로 제한
                    )

            # Public 구독 변경 적용
            public_changes = {
                data_type: change for data_type, change in changes.items()
                if data_type in [DataType.TICKER, DataType.ORDERBOOK, DataType.TRADE, DataType.CANDLE]
            }
            if public_changes:
                await self._apply_public_subscriptions(public_changes)

            # Private 구독 변경 적용
            private_changes = {
                data_type: change for data_type, change in changes.items()
                if data_type in [DataType.MY_ORDER, DataType.MY_ASSET]
            }
            if private_changes:
                await self._apply_private_subscriptions(private_changes)

            self.logger.info("구독 변경사항 적용 완료")

        except Exception as e:
            self.logger.error(f"구독 변경사항 적용 실패: {e}")
            raise SubscriptionError(f"구독 적용 오류: {e}")

    async def _apply_public_subscriptions(self, changes) -> None:
        """Public WebSocket 구독 적용"""
        try:
            if not self._public_client:
                self.logger.warning("Public 클라이언트가 연결되지 않음")
                return

            # 현재 활성 Public 구독 목록 생성
            active_subscriptions = self.subscription_manager.get_active_subscriptions(
                WebSocketType.PUBLIC
            )

            # v5 클라이언트 형식으로 변환
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

            # v5 클라이언트에 구독 요청
            if subscription_messages:
                await self._send_subscription_to_v5_client(
                    self._public_client, subscription_messages, WebSocketType.PUBLIC
                )

            # 메트릭스 업데이트
            self._connection_metrics[WebSocketType.PUBLIC].current_subscriptions = len(
                subscription_messages
            )

        except Exception as e:
            self.logger.error(f"Public 구독 적용 실패: {e}")
            raise

    async def _apply_private_subscriptions(self, changes) -> None:
        """Private WebSocket 구독 적용"""
        try:
            if not self._private_client:
                self.logger.warning("Private 클라이언트가 연결되지 않음")
                return

            # Private 구독은 심볼이 아닌 계정별 데이터
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

            # v5 클라이언트에 구독 요청
            if subscription_messages:
                await self._send_subscription_to_v5_client(
                    self._private_client, subscription_messages, WebSocketType.PRIVATE
                )

            # 메트릭스 업데이트
            self._connection_metrics[WebSocketType.PRIVATE].current_subscriptions = len(
                subscription_messages
            )

        except Exception as e:
            self.logger.error(f"Private 구독 적용 실패: {e}")
            raise

    async def _send_subscription_to_v5_client(
        self,
        client: Union[UpbitWebSocketPublicClient, UpbitWebSocketPrivateClient],
        messages: List[Dict[str, Any]],
        connection_type: WebSocketType
    ) -> None:
        """v5 클라이언트에 구독 메시지 전송"""
        try:
            # v5 클라이언트 API에 따른 구독 방법
            # (실제 v5 클라이언트 API 확인 후 수정 필요)

            if hasattr(client, 'send_subscription'):
                # 한 번에 여러 구독 전송
                await client.send_subscription(messages)
            elif hasattr(client, 'subscribe'):
                # 개별 구독 전송
                for message in messages:
                    await client.subscribe(message)
            else:
                self.logger.error(f"{connection_type} 클라이언트에 구독 메서드 없음")
                return

            self.logger.info(f"{connection_type} 구독 전송 완료: {len(messages)}개")

        except Exception as e:
            self.logger.error(f"{connection_type} 구독 전송 실패: {e}")
            raise ConnectionError(f"구독 전송 오류: {e}")

    # =============================================================================
    # WebSocket 연결 관리
    # =============================================================================

    async def initialize_public_connection(
        self,
        client: Optional[UpbitWebSocketPublicClient] = None
    ) -> bool:
        """Public WebSocket 연결 초기화"""
        try:
            self.logger.info("Public WebSocket 연결 초기화")

            if client is None and UpbitWebSocketPublicClient:
                # 새 클라이언트 생성
                client = UpbitWebSocketPublicClient()

            if client is None:
                self.logger.warning("Public WebSocket 클라이언트를 생성할 수 없음")
                return False

            self._public_client = client

            # v5 클라이언트의 메시지 핸들러를 v6 라우터로 연결
            await self._setup_v5_message_handler(client, WebSocketType.PUBLIC)

            # 연결 시도
            if hasattr(client, 'connect'):
                await client.connect()

            # 메트릭스 업데이트
            metrics = self._connection_metrics[WebSocketType.PUBLIC]
            metrics.is_connected = True
            metrics.connect_time = time.time()
            metrics.reconnect_count += 1

            # Epoch 증가 (재연결 구분)
            await self.epoch_manager.increment_epoch(WebSocketType.PUBLIC)

            self.logger.info("Public WebSocket 연결 완료")
            return True

        except Exception as e:
            self.logger.error(f"Public WebSocket 연결 실패: {e}")
            metrics = self._connection_metrics[WebSocketType.PUBLIC]
            metrics.is_connected = False
            metrics.error_count += 1
            return False

    async def initialize_private_connection(
        self,
        client: Optional[UpbitWebSocketPrivateClient] = None
    ) -> bool:
        """Private WebSocket 연결 초기화"""
        try:
            self.logger.info("Private WebSocket 연결 초기화")

            if client is None and UpbitWebSocketPrivateClient:
                # 새 클라이언트 생성 (JWT 토큰 필요)
                client = UpbitWebSocketPrivateClient()

            if client is None:
                self.logger.warning("Private WebSocket 클라이언트를 생성할 수 없음")
                return False

            self._private_client = client

            # v5 클라이언트의 메시지 핸들러를 v6 라우터로 연결
            await self._setup_v5_message_handler(client, WebSocketType.PRIVATE)

            # 연결 시도
            if hasattr(client, 'connect'):
                await client.connect()

            # 메트릭스 업데이트
            metrics = self._connection_metrics[WebSocketType.PRIVATE]
            metrics.is_connected = True
            metrics.connect_time = time.time()
            metrics.reconnect_count += 1

            # Epoch 증가
            await self.epoch_manager.increment_epoch(WebSocketType.PRIVATE)

            self.logger.info("Private WebSocket 연결 완료")
            return True

        except Exception as e:
            self.logger.error(f"Private WebSocket 연결 실패: {e}")
            metrics = self._connection_metrics[WebSocketType.PRIVATE]
            metrics.is_connected = False
            metrics.error_count += 1
            return False

    async def _setup_v5_message_handler(
        self,
        client: Union[UpbitWebSocketPublicClient, UpbitWebSocketPrivateClient],
        connection_type: WebSocketType
    ) -> None:
        """v5 클라이언트 메시지 핸들러를 v6 라우터에 연결"""
        try:
            # 기존 v5 핸들러 백업
            original_handler = getattr(client, '_on_message', None)

            async def v6_message_handler(raw_message: Any) -> None:
                try:
                    # v5 메시지를 v6 이벤트로 변환
                    v6_event = await self._convert_v5_to_v6_event(
                        raw_message, connection_type
                    )

                    if v6_event:
                        # v6 데이터 라우터로 분배
                        await self.data_router.route_event(
                            v6_event, v6_event.data_type
                        )

                        # 메트릭스 업데이트
                        metrics = self._connection_metrics[connection_type]
                        metrics.message_count += 1
                        metrics.last_message_time = time.time()

                        if hasattr(raw_message, '__len__'):
                            metrics.bytes_received += len(str(raw_message))

                    # 원본 v5 핸들러도 호출 (호환성 유지)
                    if original_handler:
                        await original_handler(raw_message)

                except Exception as e:
                    self.logger.error(f"v5→v6 메시지 처리 실패: {e}")
                    metrics = self._connection_metrics[connection_type]
                    metrics.error_count += 1

            # v5 클라이언트에 핸들러 설정
            if hasattr(client, 'set_message_handler'):
                client.set_message_handler(v6_message_handler)
            else:
                client._on_message = v6_message_handler

            self.logger.info(f"{connection_type} 메시지 핸들러 설정 완료")

        except Exception as e:
            self.logger.error(f"{connection_type} 핸들러 설정 실패: {e}")
            raise ConnectionError(f"핸들러 설정 오류: {e}")

    async def _convert_v5_to_v6_event(
        self,
        v5_message: Any,
        connection_type: WebSocketType
    ) -> Optional[BaseWebSocketEvent]:
        """v5 메시지를 v6 타입 안전 이벤트로 변환"""
        try:
            if not isinstance(v5_message, dict):
                return None

            # 현재 Epoch 가져오기
            current_epoch = self.epoch_manager.get_current_epoch(connection_type)

            # 메시지 타입 확인
            msg_type = v5_message.get('type', '').lower()
            symbol = v5_message.get('code', v5_message.get('cd', 'UNKNOWN'))
            timestamp = time.time() * 1000  # 밀리초

            # 타입별 이벤트 생성
            if msg_type == 'ticker':
                return TickerEvent(
                    symbol=symbol,
                    epoch=current_epoch,
                    connection_type=connection_type,
                    timestamp=timestamp,
                    trade_price=float(v5_message.get('tp', 0)),
                    signed_change_price=float(v5_message.get('scp', 0)),
                    signed_change_rate=float(v5_message.get('scr', 0)),
                    trade_volume=float(v5_message.get('tv', 0)),
                    acc_trade_volume_24h=float(v5_message.get('atv24h', 0)),
                    acc_trade_price_24h=float(v5_message.get('atp24h', 0)),
                    highest_52_week_price=float(v5_message.get('h52wp', 0)),
                    lowest_52_week_price=float(v5_message.get('l52wp', 0)),
                    raw_data=v5_message
                )

            elif msg_type == 'orderbook':
                return OrderbookEvent(
                    symbol=symbol,
                    epoch=current_epoch,
                    connection_type=connection_type,
                    timestamp=timestamp,
                    total_ask_size=float(v5_message.get('tas', 0)),
                    total_bid_size=float(v5_message.get('tbs', 0)),
                    orderbook_units=[],  # 실제로는 v5_message에서 파싱
                    raw_data=v5_message
                )

            elif msg_type == 'trade':
                return TradeEvent(
                    symbol=symbol,
                    epoch=current_epoch,
                    connection_type=connection_type,
                    timestamp=timestamp,
                    trade_price=float(v5_message.get('tp', 0)),
                    trade_volume=float(v5_message.get('tv', 0)),
                    ask_bid=v5_message.get('ab', 'ASK'),
                    sequential_id=v5_message.get('sid', 0),
                    raw_data=v5_message
                )

            elif msg_type in ['myorder', 'my_order']:
                return MyOrderEvent(
                    symbol=symbol,
                    epoch=current_epoch,
                    connection_type=connection_type,
                    timestamp=timestamp,
                    order_uuid=v5_message.get('uuid', ''),
                    order_type=v5_message.get('ot', 'limit'),
                    order_side=v5_message.get('os', 'bid'),
                    order_state=v5_message.get('ostate', 'wait'),
                    price=float(v5_message.get('price', 0)),
                    volume=float(v5_message.get('volume', 0)),
                    remaining_volume=float(v5_message.get('rv', 0)),
                    raw_data=v5_message
                )

            elif msg_type in ['myasset', 'my_asset']:
                return MyAssetEvent(
                    symbol=symbol,
                    epoch=current_epoch,
                    connection_type=connection_type,
                    timestamp=timestamp,
                    currency=v5_message.get('currency', symbol),
                    balance=float(v5_message.get('balance', 0)),
                    locked=float(v5_message.get('locked', 0)),
                    avg_buy_price=float(v5_message.get('avg_buy_price', 0)),
                    raw_data=v5_message
                )

            else:
                # 알 수 없는 타입은 기본 이벤트로
                return BaseWebSocketEvent(
                    symbol=symbol,
                    epoch=current_epoch,
                    connection_type=connection_type,
                    timestamp=timestamp,
                    data_type=DataType.TICKER,  # 기본값
                    raw_data=v5_message
                )

        except Exception as e:
            self.logger.error(f"v5→v6 이벤트 변환 실패: {e}")
            return None

    # =============================================================================
    # 백그라운드 모니터링 작업
    # =============================================================================

    async def _health_monitor_task(self) -> None:
        """헬스 모니터링 백그라운드 작업"""
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(self.config.monitoring.health_check_interval)

                # 연결 상태 체크
                for connection_type, metrics in self._connection_metrics.items():
                    if metrics.is_connected:
                        # 마지막 메시지 시간 체크
                        if (metrics.last_message_time and
                            time.time() - metrics.last_message_time > 60):
                            self.logger.warning(
                                f"{connection_type} 연결: 60초간 메시지 없음"
                            )

                # 컴포넌트 WeakRef 정리
                dead_refs = [
                    comp_id for comp_id, ref in self._component_refs.items()
                    if ref() is None
                ]
                for comp_id in dead_refs:
                    await self._cleanup_component(comp_id)

        except asyncio.CancelledError:
            self.logger.info("헬스 모니터 종료")
        except Exception as e:
            self.logger.error(f"헬스 모니터 오류: {e}")

    async def _metrics_collector_task(self) -> None:
        """성능 메트릭스 수집 백그라운드 작업"""
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(self.config.monitoring.metrics_collection_interval)

                # 성능 메트릭스 업데이트
                current_time = time.time()

                # 전체 메시지 처리량 계산
                total_messages = sum(
                    metrics.message_count
                    for metrics in self._connection_metrics.values()
                )

                time_diff = current_time - self._last_metrics_update
                if time_diff > 0:
                    self._performance_metrics.messages_per_second = (
                        total_messages / time_diff
                    )

                self._performance_metrics.active_connections = sum(
                    1 for metrics in self._connection_metrics.values()
                    if metrics.is_connected
                )

                self._performance_metrics.total_components = len(
                    self._component_refs
                )

                self._performance_metrics.last_updated = current_time
                self._last_metrics_update = current_time

                # 로그 출력 (주기적)
                if int(current_time) % 60 == 0:  # 1분마다
                    self.logger.info(
                        f"메트릭스 - 연결: {self._performance_metrics.active_connections}, "
                        f"컴포넌트: {self._performance_metrics.total_components}, "
                        f"MPS: {self._performance_metrics.messages_per_second:.1f}"
                    )

        except asyncio.CancelledError:
            self.logger.info("메트릭스 수집기 종료")
        except Exception as e:
            self.logger.error(f"메트릭스 수집 오류: {e}")

    async def _connection_supervisor_task(self) -> None:
        """연결 감시 및 자동 복구 백그라운드 작업"""
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(30)  # 30초마다 체크

                # Public 연결 체크
                if (self._public_client and
                    not self._connection_metrics[WebSocketType.PUBLIC].is_connected):
                    self.logger.info("Public 연결 복구 시도")
                    await self.initialize_public_connection(self._public_client)

                # Private 연결 체크
                if (self._private_client and
                    not self._connection_metrics[WebSocketType.PRIVATE].is_connected):
                    self.logger.info("Private 연결 복구 시도")
                    await self.initialize_private_connection(self._private_client)

        except asyncio.CancelledError:
            self.logger.info("연결 감시자 종료")
        except Exception as e:
            self.logger.error(f"연결 감시 오류: {e}")

    async def _cleanup_monitor_task(self) -> None:
        """리소스 정리 모니터링 백그라운드 작업"""
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(300)  # 5분마다 정리

                # 비활성 컴포넌트 정리
                cleaned = await self.subscription_manager.cleanup_inactive_components()
                if cleaned > 0:
                    self.logger.info(f"비활성 컴포넌트 {cleaned}개 정리")

                # 메모리 사용량 체크 (선택적)
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                if memory_mb > 500:  # 500MB 초과 시 경고
                    self.logger.warning(f"메모리 사용량 높음: {memory_mb:.1f}MB")

        except asyncio.CancelledError:
            self.logger.info("정리 모니터 종료")
        except Exception as e:
            self.logger.error(f"정리 모니터 오류: {e}")

    # =============================================================================
    # 상태 조회 및 모니터링
    # =============================================================================

    async def get_health_status(self) -> HealthStatus:
        """전체 시스템 헬스 상태 반환"""
        try:
            current_time = time.time()

            # 연결 상태 요약
            connections_ok = all(
                metrics.is_connected or connection_type == WebSocketType.PRIVATE
                for connection_type, metrics in self._connection_metrics.items()
            )

            # 에러율 계산
            total_messages = sum(m.message_count for m in self._connection_metrics.values())
            total_errors = sum(m.error_count for m in self._connection_metrics.values())
            error_rate = total_errors / max(total_messages, 1)

            # 전체 건강도 계산
            is_healthy = (
                self._state in [GlobalManagerState.IDLE, GlobalManagerState.ACTIVE] and
                connections_ok and
                error_rate < 0.05 and  # 5% 미만 에러율
                not self._shutdown_requested
            )

            return HealthStatus(
                is_healthy=is_healthy,
                state=self._state,
                connected_clients=sum(
                    1 for m in self._connection_metrics.values() if m.is_connected
                ),
                active_subscriptions=sum(
                    m.current_subscriptions for m in self._connection_metrics.values()
                ),
                error_count=total_errors,
                uptime_seconds=current_time - self._startup_time,
                last_check=current_time
            )

        except Exception as e:
            self.logger.error(f"헬스 상태 조회 실패: {e}")
            return HealthStatus(
                is_healthy=False,
                state=GlobalManagerState.ERROR,
                connected_clients=0,
                active_subscriptions=0,
                error_count=0,
                uptime_seconds=0,
                last_check=time.time()
            )

    async def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭스 반환"""
        return self._performance_metrics

    def get_connection_metrics(self) -> Dict[WebSocketType, ConnectionMetrics]:
        """연결별 메트릭스 반환"""
        return self._connection_metrics.copy()

    async def get_subscription_summary(self) -> Dict[str, Any]:
        """구독 상태 요약 반환"""
        try:
            return {
                "total_components": len(self._component_refs),
                "active_components": len([
                    ref for ref in self._component_refs.values() if ref() is not None
                ]),
                "subscriptions_by_type": self.subscription_manager.get_subscription_summary(),
                "routing_stats": self.data_router.get_routing_stats()
            }
        except Exception as e:
            self.logger.error(f"구독 요약 조회 실패: {e}")
            return {}

    # =============================================================================
    # 종료 및 정리
    # =============================================================================

    async def shutdown(self, timeout: float = 30.0) -> None:
        """우아한 종료"""
        try:
            self.logger.info("GlobalWebSocketManager 종료 시작")
            self._shutdown_requested = True
            self._state = GlobalManagerState.SHUTTING_DOWN

            # 백그라운드 작업 취소
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()

            # 백그라운드 작업 완료 대기 (타임아웃 적용)
            if self._background_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._background_tasks, return_exceptions=True),
                        timeout=timeout / 2
                    )
                except asyncio.TimeoutError:
                    self.logger.warning("백그라운드 작업 종료 타임아웃")

            # 컴포넌트 정리
            for component_id in list(self._component_refs.keys()):
                try:
                    await self.unregister_component(component_id)
                except Exception as e:
                    self.logger.error(f"컴포넌트 정리 실패 {component_id}: {e}")

            # 하위 시스템 종료
            await self.subscription_manager.cleanup()
            await self.data_router.stop()

            # WebSocket 연결 정리
            if self._public_client and hasattr(self._public_client, 'disconnect'):
                await self._public_client.disconnect()
            if self._private_client and hasattr(self._private_client, 'disconnect'):
                await self._private_client.disconnect()

            self._state = GlobalManagerState.STOPPED
            self.logger.info("GlobalWebSocketManager 종료 완료")

        except Exception as e:
            self.logger.error(f"종료 중 오류: {e}")
            self._state = GlobalManagerState.ERROR
            raise

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
            self._state in [GlobalManagerState.IDLE, GlobalManagerState.ACTIVE] and
            not self._shutdown_requested
        )

    @property
    def active_component_count(self) -> int:
        """활성 컴포넌트 수"""
        return len([ref for ref in self._component_refs.values() if ref() is not None])

    @property
    def uptime_seconds(self) -> float:
        """가동 시간 (초)"""
        return time.time() - self._startup_time


# =============================================================================
# 전역 접근 헬퍼 함수
# =============================================================================

async def get_global_websocket_manager() -> GlobalWebSocketManager:
    """
    전역 웹소켓 매니저 인스턴스 획득

    Returns:
        GlobalWebSocketManager: 싱글톤 인스턴스
    """
    return await GlobalWebSocketManager.get_instance()


def is_manager_available() -> bool:
    """
    매니저 사용 가능 여부 확인

    Returns:
        bool: 매니저가 초기화되어 사용 가능한지 여부
    """
    return (
        GlobalWebSocketManager._instance is not None and
        hasattr(GlobalWebSocketManager._instance, '_initialized') and
        GlobalWebSocketManager._instance._initialized
    )
