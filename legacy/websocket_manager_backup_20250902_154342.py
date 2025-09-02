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
from typing import Dict, List, Optional, Any, Callable

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
    BaseWebSocketEvent, SubscriptionSpec, ConnectionMetrics, HealthStatus,
    TickerEvent, OrderbookEvent, TradeEvent, CandleEvent
)
from .data_processor import DataProcessor, create_data_processor
from ..support.websocket_config import (
    WebSocketConfig, get_config
)
from ..support.subscription_manager import SubscriptionManager
from ..support.jwt_manager import JWTManager


class WebSocketManager:
    """
    WebSocket v6.0 글로벌 매니저

    네이티브 WebSocket 연결 로직을 내장한 중앙 집중식 관리자.
    외부에서는 WebSocketClient만 사용하도록 설계됨.
    """

    _instance: Optional['WebSocketManager'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        if WebSocketManager._instance is not None:
            raise RuntimeError("WebSocketManager는 싱글톤입니다. get_instance()를 사용하세요.")

        # 로깅
        self.logger = create_component_logger("WebSocketManager")

        # 설정
        self._config: WebSocketConfig = get_config()

        # 상태 관리
        self._state = GlobalManagerState.IDLE
        self._connections: Dict[WebSocketType, Optional[Any]] = {
            WebSocketType.PUBLIC: None,
            WebSocketType.PRIVATE: None
        }
        self._connection_states: Dict[WebSocketType, ConnectionState] = {
            WebSocketType.PUBLIC: ConnectionState.DISCONNECTED,
            WebSocketType.PRIVATE: ConnectionState.DISCONNECTED
        }

        # 메시지 수신 태스크
        self._message_tasks: Dict[WebSocketType, Optional[asyncio.Task]] = {
            WebSocketType.PUBLIC: None,
            WebSocketType.PRIVATE: None
        }

        # 컴포넌트 관리
        self._components: Dict[str, weakref.ReferenceType] = {}
        self._component_callbacks: Dict[str, List[Callable]] = {}

        # 하위 시스템
        self._data_processor: Optional[DataProcessor] = None
        self._subscription_manager: Optional[SubscriptionManager] = None
        self._jwt_manager: Optional[JWTManager] = None

        # 메트릭스
        self._connection_metrics: Dict[WebSocketType, ConnectionMetrics] = {
            WebSocketType.PUBLIC: ConnectionMetrics(),
            WebSocketType.PRIVATE: ConnectionMetrics()
        }

        self.logger.info("WebSocketManager 초기화 완료")

    @classmethod
    async def get_instance(cls) -> 'WebSocketManager':
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance._initialize()
        return cls._instance

    async def _initialize(self) -> None:
        """내부 초기화"""
        try:
            # 하위 시스템 초기화
            self._data_processor = create_data_processor()
            self._subscription_manager = SubscriptionManager()
            self._jwt_manager = JWTManager()

            # 구독 변경 감지
            self._subscription_manager.add_change_callback(self._handle_subscription_changes)

            self.logger.info("WebSocketManager 하위 시스템 초기화 완료")

        except Exception as e:
            self.logger.error(f"초기화 실패: {e}")
            raise

    # ================================================================
    # 상태 관리
    # ================================================================

    async def start(self) -> None:
        """WebSocket 매니저 시작"""
        if self._state == GlobalManagerState.ACTIVE:
            self.logger.warning("이미 실행 중입니다")
            return

        try:
            self._state = GlobalManagerState.INITIALIZING
            self.logger.info("WebSocket 매니저 시작")

            # 활성 구독이 있으면 연결 시작
            await self._check_and_connect()

            self._state = GlobalManagerState.ACTIVE
            self.logger.info("WebSocket 매니저 시작 완료")

        except Exception as e:
            self._state = GlobalManagerState.ERROR
            self.logger.error(f"시작 실패: {e}")
            raise

    async def stop(self) -> None:
        """WebSocket 매니저 정지"""
        if self._state == GlobalManagerState.IDLE:
            return

        try:
            self._state = GlobalManagerState.SHUTTING_DOWN
            self.logger.info("WebSocket 매니저 정지")

            # 모든 연결 종료
            await self._disconnect_all()

            self._state = GlobalManagerState.IDLE
            self.logger.info("WebSocket 매니저 정지 완료")

        except Exception as e:
            self._state = GlobalManagerState.ERROR
            self.logger.error(f"정지 실패: {e}")

    async def _check_and_connect(self) -> None:
        """필요한 연결 확인 및 생성"""
        # Public 구독 확인
        public_subs = self._subscription_manager.get_public_subscriptions()
        if public_subs:
            await self._ensure_connection(WebSocketType.PUBLIC)

        # Private 구독 확인
        private_subs = self._subscription_manager.get_private_subscriptions()
        if private_subs:
            await self._ensure_connection(WebSocketType.PRIVATE)

    # ================================================================
    # 컴포넌트 등록/해제
    # ================================================================

    def register_component(
        self,
        component_id: str,
        component_ref: Any,
        subscriptions: Optional[List[SubscriptionSpec]] = None,
        callbacks: Optional[List[Callable]] = None
    ) -> None:
        """컴포넌트 등록"""
        try:
            # WeakRef로 컴포넌트 저장
            self._components[component_id] = weakref.ref(
                component_ref,
                lambda ref: self._cleanup_component(component_id)
            )

            # 콜백 저장
            if callbacks:
                self._component_callbacks[component_id] = callbacks

            # 구독 등록 (비동기 작업을 백그라운드에서 실행)
            if subscriptions:
                asyncio.create_task(
                    self._subscription_manager.register_component(
                        component_id,
                        subscriptions,
                        callback=callbacks[0] if callbacks else None,
                        cleanup_ref=component_ref
                    )
                )

            self.logger.debug(f"컴포넌트 등록: {component_id}")

        except Exception as e:
            self.logger.error(f"컴포넌트 등록 실패 ({component_id}): {e}")
            raise

    def unregister_component(self, component_id: str) -> None:
        """컴포넌트 해제"""
        try:
            # 구독 해제
            self._subscription_manager.remove_component_subscriptions(component_id)

            # 컴포넌트 제거
            self._components.pop(component_id, None)
            self._component_callbacks.pop(component_id, None)

            self.logger.debug(f"컴포넌트 해제: {component_id}")

        except Exception as e:
            self.logger.error(f"컴포넌트 해제 실패 ({component_id}): {e}")

    def _cleanup_component(self, component_id: str) -> None:
        """컴포넌트 자동 정리 (WeakRef 콜백)"""
        try:
            self.logger.debug(f"컴포넌트 자동 정리: {component_id}")

            # 구독 해제
            self._subscription_manager.remove_component_subscriptions(component_id)

            # 콜백 제거
            self._component_callbacks.pop(component_id, None)

            self.logger.debug(f"컴포넌트 정리 완료: {component_id}")

        except Exception as e:
            self.logger.error(f"컴포넌트 정리 오류 ({component_id}): {e}")

    # ================================================================
    # 구독 변경 처리 (DataProcessor 및 SubscriptionManager 통합)
    # ================================================================

    def _handle_subscription_changes(self, changes: Dict) -> None:
        """구독 변경사항 처리 (동기 버전)"""
        asyncio.create_task(self._handle_subscription_changes_async(changes))

    async def _handle_subscription_changes_async(self, changes: Dict) -> None:
        """구독 변경사항 처리 (비동기 버전)"""
        try:
            # Public 구독 변경
            if self._subscription_manager.has_public_subscriptions():
                await self._ensure_connection(WebSocketType.PUBLIC)
                await self._update_websocket_subscriptions(WebSocketType.PUBLIC)

            # Private 구독 변경
            if self._subscription_manager.has_private_subscriptions():
                await self._ensure_connection(WebSocketType.PRIVATE)
                await self._update_websocket_subscriptions(WebSocketType.PRIVATE)

        except Exception as e:
            self.logger.error(f"구독 변경 처리 실패: {e}")

    async def _ensure_connection(self, connection_type: WebSocketType) -> None:
        """연결 보장"""
        if self._connection_states[connection_type] != ConnectionState.CONNECTED:
            await self._connect_websocket(connection_type)

    async def _update_websocket_subscriptions(self, connection_type: WebSocketType) -> None:
        """WebSocket 구독 업데이트"""
        try:
            # 구독 정보 가져오기
            if connection_type == WebSocketType.PUBLIC:
                subscriptions = self._subscription_manager.get_public_subscriptions()
            else:
                subscriptions = self._subscription_manager.get_private_subscriptions()

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
                if WEBSOCKETS_AVAILABLE and websockets:
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
            if not WEBSOCKETS_AVAILABLE:
                raise RuntimeError("websockets 라이브러리가 설치되지 않았습니다")

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
                        await self._data_processor.process_event(event)

                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패 ({connection_type}): {e}")
                except Exception as e:
                    self.logger.error(f"메시지 처리 실패 ({connection_type}): {e}")

        except Exception as e:
            if WEBSOCKETS_AVAILABLE and hasattr(websockets, 'exceptions'):
                if isinstance(e, websockets.exceptions.ConnectionClosed):
                    self.logger.info(f"WebSocket 연결 종료: {connection_type}")
                else:
                    self.logger.error(f"메시지 수신 오류 ({connection_type}): {e}")
            else:
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
                return TickerEvent(**event_data)
            elif data_type == DataType.ORDERBOOK:
                return OrderbookEvent(**event_data)
            elif data_type == DataType.TRADE:
                return TradeEvent(**event_data)
            elif data_type.value.startswith('candle.'):
                return CandleEvent(**event_data)
            else:
                return BaseWebSocketEvent(**event_data)

        except Exception as e:
            self.logger.error(f"이벤트 생성 실패: {e}")
            return None

    def _detect_data_type(self, data: Dict) -> Optional[DataType]:
        """데이터 타입 감지"""
        if 'ty' in data:
            type_value = data['ty']

            # 정확한 매칭 시도
            for data_type in DataType:
                if data_type.value == type_value:
                    return data_type

            # 부분 매칭 (candle 등)
            if type_value.startswith('candle.'):
                return DataType.CANDLE_1M  # 기본값

        return None

    async def _disconnect_all(self) -> None:
        """모든 연결 종료"""
        for connection_type in WebSocketType:
            await self._disconnect_websocket(connection_type)

    async def _disconnect_websocket(self, connection_type: WebSocketType) -> None:
        """특정 WebSocket 연결 종료"""
        try:
            # 메시지 태스크 취소
            task = self._message_tasks.get(connection_type)
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # 연결 종료
            connection = self._connections.get(connection_type)
            if connection:
                await connection.close()

            # 상태 초기화
            self._connections[connection_type] = None
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED
            self._message_tasks[connection_type] = None

            self.logger.info(f"WebSocket 연결 종료: {connection_type}")

        except Exception as e:
            self.logger.error(f"연결 종료 실패 ({connection_type}): {e}")

    # ================================================================
    # 상태 조회
    # ================================================================

    def get_state(self) -> GlobalManagerState:
        """매니저 상태 반환"""
        return self._state

    def get_connection_state(self, connection_type: WebSocketType) -> ConnectionState:
        """연결 상태 반환"""
        return self._connection_states[connection_type]

    def get_health_status(self) -> HealthStatus:
        """헬스 상태 반환"""
        try:
            # 간단한 헬스 체크
            is_healthy = (
                self._state == GlobalManagerState.RUNNING and
                self._data_processor is not None and
                self._subscription_manager is not None
            )

            return HealthStatus(
                is_healthy=is_healthy,
                manager_state=self._state,
                connection_states=dict(self._connection_states),
                active_components=len(self._components),
                error_message=None if is_healthy else "시스템 오류"
            )
        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                manager_state=self._state,
                connection_states={},
                active_components=0,
                error_message=str(e)
            )


# ================================================================
# 전역 인스턴스 접근
# ================================================================

_global_manager: Optional[WebSocketManager] = None

async def get_global_websocket_manager() -> WebSocketManager:
    """글로벌 WebSocket 매니저 인스턴스 반환"""
    global _global_manager
    if _global_manager is None:
        _global_manager = await WebSocketManager.get_instance()
    return _global_manager
