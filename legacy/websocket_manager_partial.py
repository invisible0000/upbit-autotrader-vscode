"""
WebSocket v6.0 통합 매니저
========================

중앙 집중식 WebSocket 관리자 (네이티브 연결 로직 포함)
- 싱글톤 패턴으로 전역 관리
- 내부에 네이티브 WebSocket 연결 로직 통합
- 사용자는 websocket_client.py만 사용
"""

import asyncio
import weakref
import time
import json
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass

try:
    import websockets
    import websockets.exceptions
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WEBSOCKETS_AVAILABLE = False

from upbit_auto_trading.infrastructure.logging import create_component_logger

# Rate Limiter 연동 (선택적)
try:
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
        get_global_rate_limiter
    )
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    get_global_rate_limiter = None
    RATE_LIMITER_AVAILABLE = False

from .websocket_types import (
    WebSocketType, GlobalManagerState, ConnectionState, DataType,
    BaseWebSocketEvent, SubscriptionSpec, ComponentSubscription,
    PerformanceMetrics, HealthStatus, ConnectionMetrics,
    TickerEvent, OrderbookEvent, TradeEvent, CandleEvent,
    convert_dict_to_event
)
from .data_processor import DataProcessor, create_data_processor
from ..support.websocket_config import (
    WebSocketConfig, get_config
)
from ..support.subscription_manager import SubscriptionManager


@dataclass
class EpochManager:
    """재연결 시 데이터 순서 보장을 위한 Epoch 관리"""
    current_epoch: int = 0
    last_reconnect: float = 0.0

    def next_epoch(self) -> int:
        """다음 Epoch 번호 생성"""
        self.current_epoch += 1
        self.last_reconnect = time.time()
        return self.current_epoch


class WebSocketManager:
    """
    WebSocket v6.0 통합 관리자 (싱글톤)

    네이티브 WebSocket 연결 로직을 내부에 포함하여
    사용자는 websocket_client.py만 사용하면 됨
    """

    _instance: Optional['WebSocketManager'] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> 'WebSocketManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 중복 초기화 방지
        if hasattr(self, '_initialized'):
            return

        self.logger = create_component_logger("WebSocketManager")
        self._initialized = True

        # 상태 관리
        self._state = GlobalManagerState.INITIALIZING
        self._startup_time = time.time()
        self._shutdown_requested = False

        # 연결 관리
        self._connections: Dict[WebSocketType, Optional[Any]] = {
            WebSocketType.PUBLIC: None,
            WebSocketType.PRIVATE: None
        }
        self._connection_states: Dict[WebSocketType, ConnectionState] = {
            WebSocketType.PUBLIC: ConnectionState.DISCONNECTED,
            WebSocketType.PRIVATE: ConnectionState.DISCONNECTED
        }
        self._connection_metrics: Dict[WebSocketType, ConnectionMetrics] = {
            WebSocketType.PUBLIC: ConnectionMetrics(WebSocketType.PUBLIC),
            WebSocketType.PRIVATE: ConnectionMetrics(WebSocketType.PRIVATE)
        }

        # 구독 관리
        self._subscription_manager = SubscriptionManager()
        self._subscriptions: Dict[str, ComponentSubscription] = {}
        self._component_refs: Dict[str, weakref.ReferenceType] = {}

        # 데이터 처리
        self._data_processor = create_data_processor()

        self._active_subscriptions: Dict[WebSocketType, Set[str]] = {
            WebSocketType.PUBLIC: set(),
            WebSocketType.PRIVATE: set()
        }

        # 백그라운드 작업
        self._background_tasks: Set[asyncio.Task] = set()
        self._epoch_manager = EpochManager()

        # 성능 메트릭
        self._performance_metrics = PerformanceMetrics(
            messages_per_second=0.0,
            active_connections=0,
            total_components=0,
            last_updated=self._startup_time
        )

        # Rate Limiter (선택적)
        self._rate_limiter = None

        # 설정 로딩
        try:
            self._config = get_config()
            self.logger.info(f"설정 로딩 완료: {self._config.environment}")
        except Exception as e:
            self.logger.error(f"설정 로딩 실패: {e}")
            self._config = WebSocketConfig()  # 기본 설정 사용

        self._state = GlobalManagerState.IDLE
        self.logger.info("WebSocket 매니저 초기화 완료")

    # ================================================================
    # 연결 관리 (내부 네이티브 로직)
    # ================================================================

    # ================================================================
    # WebSocket 연결 관리 (통합 구현)
    # ================================================================
            self._connection_states[connection_type] = ConnectionState.CONNECTED

            # 메트릭 업데이트
            metrics = self._connection_metrics[connection_type]
            metrics.state = ConnectionState.CONNECTED
            metrics.connected_at = time.time()

            # 메시지 수신 태스크 시작
            task = asyncio.create_task(
                self._message_receiver_loop(connection_type)
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            self.logger.info(f"{connection_type.value} WebSocket 연결 완료")
            return True

        except Exception as e:
            self.logger.error(f"{connection_type.value} WebSocket 연결 실패: {e}")
            self._connection_states[connection_type] = ConnectionState.ERROR
            return False

    async def _disconnect_websocket(self, connection_type: WebSocketType) -> None:
        """내부 WebSocket 연결 해제"""
        try:
            websocket = self._connections.get(connection_type)
            if websocket:
                await websocket.close()
                self._connections[connection_type] = None
                self._connection_states[connection_type] = ConnectionState.DISCONNECTED

                # 메트릭 업데이트
                metrics = self._connection_metrics[connection_type]
                metrics.state = ConnectionState.DISCONNECTED
                metrics.connected_at = None

                self.logger.info(f"{connection_type.value} WebSocket 연결 해제 완료")

        except Exception as e:
            self.logger.error(f"{connection_type.value} WebSocket 연결 해제 실패: {e}")

    async def _message_receiver_loop(self, connection_type: WebSocketType) -> None:
        """메시지 수신 루프"""
        websocket = self._connections.get(connection_type)
        if not websocket:
            return

        try:
            while not self._shutdown_requested:
                try:
                    # 메시지 수신 (타임아웃 포함)
                    message = await asyncio.wait_for(
                        websocket.recv(),
                        timeout=30.0  # 30초 타임아웃
                    )

                    # 메트릭 업데이트
                    metrics = self._connection_metrics[connection_type]
                    metrics.total_messages += 1
                    metrics.last_message_at = time.time()

                    # 메시지 처리
                    await self._process_message(message, connection_type)

                except asyncio.TimeoutError:
                    # 타임아웃은 정상 (keep-alive)
                    continue

                except Exception as e:
                    # WebSocket 연결 종료 감지
                    if WEBSOCKETS_AVAILABLE and websockets and isinstance(e, websockets.exceptions.ConnectionClosed):
                        self.logger.warning(f"{connection_type.value} WebSocket 연결 종료됨")
                        break
                    elif "ConnectionClosed" in str(type(e)):
                        self.logger.warning(f"{connection_type.value} WebSocket 연결 종료됨")
                        break
                    self.logger.error(f"{connection_type.value} 메시지 수신 오류: {e}")
                    metrics = self._connection_metrics[connection_type]
                    metrics.error_count += 1

        except Exception as e:
            self.logger.error(f"{connection_type.value} 메시지 수신 루프 오류: {e}")
        finally:
            # 연결 상태 업데이트
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED
            self._connections[connection_type] = None

    async def _process_message(self, raw_message: str, connection_type: WebSocketType) -> None:
        """수신된 메시지 처리"""
        try:
            # JSON 파싱
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode('utf-8')

            message = json.loads(raw_message)

            # 이벤트 변환
            event = convert_dict_to_event(
                message,
                epoch=self._epoch_manager.current_epoch,
                connection_type=connection_type
            )

            if event:
                # 구독자들에게 이벤트 전달
                await self._distribute_event(event)

        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")

    async def _distribute_event(self, event: BaseWebSocketEvent) -> None:
        """이벤트를 구독자들에게 분배"""
        for component_id, subscription in self._subscriptions.items():
            try:
                # WeakRef 확인
                component_ref = self._component_refs.get(component_id)
                if component_ref and component_ref() is None:
                    # 죽은 참조 제거
                    await self._cleanup_component(component_id)
                    continue

                # 콜백 호출
                if subscription.callback:
                    # 비동기 콜백 처리
                    if asyncio.iscoroutinefunction(subscription.callback):
                        await subscription.callback(event)
                    else:
                        subscription.callback(event)

            except Exception as e:
                self.logger.error(f"이벤트 분배 오류 ({component_id}): {e}")

    # ================================================================
    # 구독 관리 (외부 인터페이스)
    # ================================================================

    async def register_component(
        self,
        component_id: str,
        component_instance: Any,
        subscriptions: List[SubscriptionSpec],
        callback: Callable[[BaseWebSocketEvent], None]
    ) -> ComponentSubscription:
        """컴포넌트 등록 및 구독 설정"""
        try:
            # 구독 관리자에 등록
            changes = await self._subscription_manager.register_component(
                component_id=component_id,
                subscription_specs=subscriptions,
                callback=callback,
                cleanup_ref=component_instance
            )

            # 데이터 프로세서에 콜백 등록
            for spec in subscriptions:
                callback_id = f"{component_id}_{spec.data_type.value}"
                self._data_processor.register_callback(
                    callback_id=callback_id,
                    component_id=component_id,
                    data_type=spec.data_type,
                    callback=callback
                )

            # WeakRef 생성 (추가 보안)
            def cleanup_callback(ref):
                asyncio.create_task(self._cleanup_component(component_id))

            try:
                weak_ref = weakref.ref(component_instance, cleanup_callback)
                self._component_refs[component_id] = weak_ref
            except TypeError:
                self.logger.warning(f"WeakRef 생성 실패: {component_id}")

            # 구독 정보 저장
            subscription = ComponentSubscription(
                component_id=component_id,
                subscriptions=subscriptions,
                callback=callback,
                created_at=time.time(),
                last_activity=time.time()
            )
            self._subscriptions[component_id] = subscription

            # WebSocket 연결 및 구독 처리
            await self._handle_subscription_changes(changes)

            self.logger.info(f"컴포넌트 등록 완료: {component_id}")
            return subscription

        except Exception as e:
            self.logger.error(f"컴포넌트 등록 실패 ({component_id}): {e}")
            raise

    async def unregister_component(self, component_id: str) -> None:
        """컴포넌트 등록 해제"""
        await self._cleanup_component(component_id)

    async def _cleanup_component(self, component_id: str) -> None:
        """컴포넌트 정리"""
        try:
            if component_id in self._subscriptions:
                del self._subscriptions[component_id]

            if component_id in self._component_refs:
                del self._component_refs[component_id]

            self.logger.debug(f"컴포넌트 정리 완료: {component_id}")

        except Exception as e:
            self.logger.error(f"컴포넌트 정리 오류 ({component_id}): {e}")

    # ================================================================
    # 구독 변경 처리 (DataProcessor 및 SubscriptionManager 통합)
    # ================================================================

    async def _handle_subscription_changes(self, changes: Dict) -> None:
        """구독 변경사항 처리"""
        try:
            # Public 구독 변경
            public_subs = self._subscription_manager.get_public_subscriptions()
            if public_subs:
                await self._ensure_connection(WebSocketType.PUBLIC)
                await self._update_websocket_subscriptions(WebSocketType.PUBLIC, public_subs)

            # Private 구독 변경
            private_subs = self._subscription_manager.get_private_subscriptions()
            if private_subs:
                await self._ensure_connection(WebSocketType.PRIVATE)
                await self._update_websocket_subscriptions(WebSocketType.PRIVATE, private_subs)

        except Exception as e:
            self.logger.error(f"구독 변경 처리 실패: {e}")

    async def _ensure_connection(self, connection_type: WebSocketType) -> None:
        """연결 보장"""
        if self._connection_states[connection_type] != ConnectionState.CONNECTED:
            await self._connect_websocket(connection_type)

    async def _update_websocket_subscriptions(
        self,
        connection_type: WebSocketType,
        subscriptions: Dict
    ) -> None:
        """WebSocket 구독 업데이트"""
        try:
            # 구독 메시지 생성 및 전송
            for data_type, symbols in subscriptions.items():
                if symbols:  # 빈 집합이 아닌 경우만
                    message = self._create_subscription_message(data_type, list(symbols))
                    await self._send_message(connection_type, message)

        except Exception as e:
            self.logger.error(f"구독 업데이트 실패 ({connection_type}): {e}")

    def _create_subscription_message(self, data_type, symbols: List[str]) -> List[Dict]:
        """구독 메시지 생성 (업비트 형식)"""
        ticket = {"ticket": f"upbit_websocket_v6_{int(time.time())}"}
        type_msg = {
            "type": data_type.value,
            "codes": symbols,
            "isOnlySnapshot": False,
            "isOnlyRealtime": False
        }
        format_msg = {"format": "DEFAULT"}

        return [ticket, type_msg, format_msg]

    async def _send_message(self, connection_type: WebSocketType, message: List[Dict]) -> None:
        """메시지 전송"""
        connection = self._connections[connection_type]
        if connection and self._connection_states[connection_type] == ConnectionState.CONNECTED:
            try:
                await connection.send(json.dumps(message))
                self.logger.debug(f"메시지 전송 완료 ({connection_type}): {message[1].get('type', 'unknown')}")
            except Exception as e:
                self.logger.error(f"메시지 전송 실패 ({connection_type}): {e}")

    # ================================================================
    # WebSocket 연결 관리
    # ================================================================

    async def _connect_websocket(self, connection_type: WebSocketType) -> None:
        """WebSocket 연결 생성"""
        try:
            self._connection_states[connection_type] = ConnectionState.CONNECTING

            # URL 설정
            url = self._get_websocket_url(connection_type)

            # 헤더 설정 (Private 연결 시 JWT 포함)
            headers = {}
            if connection_type == WebSocketType.PRIVATE:
                token = self._jwt_manager.generate_token()
                headers["Authorization"] = f"Bearer {token}"

            # 연결 생성
            connection = await websockets.connect(url, extra_headers=headers)
            self._connections[connection_type] = connection
            self._connection_states[connection_type] = ConnectionState.CONNECTED

            # 메시지 수신 태스크 시작
            task = asyncio.create_task(self._handle_messages(connection_type, connection))
            self._message_tasks[connection_type] = task

            self.logger.info(f"WebSocket 연결 성공: {connection_type}")

        except Exception as e:
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED
            self.logger.error(f"WebSocket 연결 실패 ({connection_type}): {e}")
            raise

    def _get_websocket_url(self, connection_type: WebSocketType) -> str:
        """WebSocket URL 반환"""
        if connection_type == WebSocketType.PUBLIC:
            return "wss://api.upbit.com/websocket/v1"
        else:  # PRIVATE
            return "wss://api.upbit.com/websocket/v1"

    async def _handle_messages(self, connection_type: WebSocketType, connection) -> None:
        """메시지 수신 처리"""
        try:
            async for message in connection:
                try:
                    # JSON 데이터 파싱
                    data = json.loads(message)

                    # 이벤트 생성 및 처리
                    event = self._create_websocket_event(connection_type, data)
                    if event:
                        await self._data_processor.process_data(event)

                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패 ({connection_type}): {e}")
                except Exception as e:
                    self.logger.error(f"메시지 처리 실패 ({connection_type}): {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"WebSocket 연결 종료: {connection_type}")
        except Exception as e:
            self.logger.error(f"메시지 수신 오류 ({connection_type}): {e}")
        finally:
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED

    def _create_websocket_event(self, connection_type: WebSocketType, data: Dict) -> Optional[BaseWebSocketEvent]:
        """WebSocket 이벤트 생성"""
        try:
            # 데이터 타입 감지
            data_type = self._detect_data_type(data)
            if not data_type:
                return None

            # 공통 필드
            event_data = {
                'timestamp': int(time.time() * 1000),
                'source': connection_type,
                'data_type': data_type,
                'raw_data': data
            }

            # 타입별 이벤트 생성
            if data_type == DataType.TICKER:
                return TickerWebSocketEvent(**event_data)
            elif data_type == DataType.ORDERBOOK:
                return OrderbookWebSocketEvent(**event_data)
            elif data_type == DataType.TRADE:
                return TradeWebSocketEvent(**event_data)
            elif data_type == DataType.CANDLE:
                return CandleWebSocketEvent(**event_data)
            else:
                return BaseWebSocketEvent(**event_data)

        except Exception as e:
            self.logger.error(f"이벤트 생성 실패: {e}")
            return None

    def _detect_data_type(self, data: Dict) -> Optional[DataType]:
        """데이터 타입 감지"""
        if 'ty' in data:
            type_map = {
                'ticker': DataType.TICKER,
                'orderbook': DataType.ORDERBOOK,
                'trade': DataType.TRADE,
                'candle': DataType.CANDLE
            }
            return type_map.get(data['ty'])
        return None

    async def _ensure_connections(self, subscriptions: List[SubscriptionSpec]) -> None:
        """필요한 연결 확인 및 생성"""
        required_connections = set()

        for spec in subscriptions:
            if spec.data_type.is_public():
                required_connections.add(WebSocketType.PUBLIC)
            elif spec.data_type.is_private():
                required_connections.add(WebSocketType.PRIVATE)

        for conn_type in required_connections:
            if self._connection_states[conn_type] != ConnectionState.CONNECTED:
                await self._connect_websocket(conn_type)

    async def _send_subscription_messages(self, subscriptions: List[SubscriptionSpec]) -> None:
        """WebSocket 구독 메시지 전송"""
        # Public 구독
        public_specs = [spec for spec in subscriptions if spec.data_type.is_public()]
        if public_specs:
            await self._send_public_subscription(public_specs)

        # Private 구독
        private_specs = [spec for spec in subscriptions if spec.data_type.is_private()]
        if private_specs:
            await self._send_private_subscription(private_specs)

    async def _send_public_subscription(self, subscriptions: List[SubscriptionSpec]) -> None:
        """Public 구독 메시지 전송"""
        websocket = self._connections.get(WebSocketType.PUBLIC)
        if not websocket:
            return

        try:
            # 업비트 WebSocket 구독 메시지 형식
            ticket = {"ticket": f"upbit_v6_{int(time.time())}"}

            types = []
            for spec in subscriptions:
                type_msg = {
                    "type": spec.data_type.value,
                    "codes": spec.symbols
                }
                if spec.unit:  # 캔들의 경우
                    type_msg["unit"] = spec.unit
                types.append(type_msg)

            format_msg = {"format": "DEFAULT"}  # 또는 "SIMPLE"

            message = [ticket] + types + [format_msg]
            await websocket.send(json.dumps(message))

            self.logger.info(f"Public 구독 메시지 전송: {len(types)}개 타입")

        except Exception as e:
            self.logger.error(f"Public 구독 메시지 전송 실패: {e}")

    async def _send_private_subscription(self, subscriptions: List[SubscriptionSpec]) -> None:
        """Private 구독 메시지 전송"""
        websocket = self._connections.get(WebSocketType.PRIVATE)
        if not websocket:
            return

        try:
            # Private 구독 로직 (JWT 토큰 필요)
            ticket = {"ticket": f"upbit_private_v6_{int(time.time())}"}

            types = []
            for spec in subscriptions:
                types.append({"type": spec.data_type.value})

            format_msg = {"format": "DEFAULT"}

            message = [ticket] + types + [format_msg]
            await websocket.send(json.dumps(message))

            self.logger.info(f"Private 구독 메시지 전송: {len(types)}개 타입")

        except Exception as e:
            self.logger.error(f"Private 구독 메시지 전송 실패: {e}")

    # ================================================================
    # 상태 조회
    # ================================================================

    async def get_health_status(self) -> HealthStatus:
        """헬스 상태 조회"""
        uptime = time.time() - self._startup_time

        # 연결 상태 확인
        connected_count = sum(
            1 for state in self._connection_states.values()
            if state == ConnectionState.CONNECTED
        )

        # 전체 메시지 수 계산
        total_messages = sum(
            metrics.total_messages
            for metrics in self._connection_metrics.values()
        )

        return HealthStatus(
            status="healthy" if connected_count > 0 else "disconnected",
            uptime_seconds=uptime,
            total_messages_processed=total_messages,
            connection_errors=sum(
                metrics.error_count
                for metrics in self._connection_metrics.values()
            ),
            last_error=None,
            last_error_time=None
        )

    async def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭 조회"""
        active_connections = sum(
            1 for state in self._connection_states.values()
            if state == ConnectionState.CONNECTED
        )

        # 메시지 처리율 계산
        total_messages = sum(
            metrics.total_messages
            for metrics in self._connection_metrics.values()
        )
        uptime = time.time() - self._startup_time
        messages_per_second = total_messages / max(uptime, 1.0)

        return PerformanceMetrics(
            messages_per_second=messages_per_second,
            active_connections=active_connections,
            total_components=len(self._subscriptions),
            last_updated=time.time()
        )

    # ================================================================
    # 생명주기 관리
    # ================================================================

    async def start(self) -> None:
        """매니저 시작"""
        if self._state == GlobalManagerState.ACTIVE:
            return

        self.logger.info("WebSocket 매니저 시작")
        self._state = GlobalManagerState.ACTIVE

    async def shutdown(self) -> None:
        """매니저 종료"""
        try:
            self.logger.info("WebSocket 매니저 종료 시작")
            self._state = GlobalManagerState.SHUTTING_DOWN
            self._shutdown_requested = True

            # 모든 연결 해제
            for connection_type in WebSocketType:
                await self._disconnect_websocket(connection_type)

            # 백그라운드 작업 취소
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()

            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            # 상태 초기화
            self._subscriptions.clear()
            self._component_refs.clear()

            self.logger.info("WebSocket 매니저 종료 완료")

        except Exception as e:
            self.logger.error(f"매니저 종료 오류: {e}")

    @property
    def uptime_seconds(self) -> float:
        """매니저 가동 시간"""
        return time.time() - self._startup_time


# ================================================================
# 전역 인스턴스 관리
# ================================================================

_global_manager: Optional[WebSocketManager] = None


async def get_websocket_manager() -> WebSocketManager:
    """전역 WebSocket 매니저 인스턴스 반환"""
    global _global_manager

    if _global_manager is None:
        async with WebSocketManager._lock:
            if _global_manager is None:
                _global_manager = WebSocketManager()
                await _global_manager.start()

    return _global_manager


def is_manager_available() -> bool:
    """매니저 가용성 확인"""
    return _global_manager is not None and _global_manager._state == GlobalManagerState.ACTIVE


async def shutdown_websocket_manager() -> None:
    """전역 매니저 종료"""
    global _global_manager

    if _global_manager:
        await _global_manager.shutdown()
        _global_manager = None
