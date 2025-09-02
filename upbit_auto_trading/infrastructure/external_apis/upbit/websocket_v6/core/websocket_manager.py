"""
WebSocket v6.0 간소화된 매니저
============================

핵심 기능만 포함한 단순한 WebSocket 관리자
- 싱글톤 패턴
- 기본적인 연결 관리
- 컴포넌트 등록/해제
- 구독 관리 위임
"""

import asyncio
import weakref
import time
import json
from typing import Dict, List, Optional, Any

try:
    import websockets
    import websockets.exceptions
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WEBSOCKETS_AVAILABLE = False

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .websocket_types import (
    WebSocketType, GlobalManagerState, ConnectionState, DataType,
    BaseWebSocketEvent, SubscriptionSpec, HealthStatus
)
from .data_processor import DataProcessor
from ..support.subscription_manager import SubscriptionManager
from ..support.jwt_manager import JWTManager


class WebSocketManager:
    """간소화된 WebSocket 매니저"""

    _instance: Optional['WebSocketManager'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        if WebSocketManager._instance is not None:
            raise RuntimeError("WebSocketManager는 싱글톤입니다. get_instance()를 사용하세요.")

        # 로깅
        self.logger = create_component_logger("WebSocketManager")

        # 상태
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

        # 하위 시스템
        self._data_processor: Optional[DataProcessor] = None
        self._subscription_manager: Optional[SubscriptionManager] = None
        self._jwt_manager: Optional[JWTManager] = None

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
            self._data_processor = DataProcessor()
            self._subscription_manager = SubscriptionManager()
            self._jwt_manager = JWTManager()

            # 구독 변경 감지
            self._subscription_manager.add_change_callback(self._on_subscription_change)

            self.logger.info("WebSocketManager 하위 시스템 초기화 완료")

        except Exception as e:
            self.logger.error(f"초기화 실패: {e}")
            raise

    def _on_subscription_change(self, changes: Dict) -> None:
        """구독 변경 콜백 (동기)"""
        # 비동기 처리를 백그라운드에서 실행
        asyncio.create_task(self._handle_subscription_changes(changes))

    async def _handle_subscription_changes(self, changes: Dict) -> None:
        """구독 변경 처리 (비동기)"""
        try:
            # 간단한 구현: 활성 구독이 있으면 연결, 없으면 해제
            if self._subscription_manager:
                public_subs = self._subscription_manager.get_public_subscriptions()
                private_subs = self._subscription_manager.get_private_subscriptions()

                # Public 연결 관리
                if public_subs:
                    await self._ensure_connection(WebSocketType.PUBLIC)
                else:
                    await self._disconnect_if_connected(WebSocketType.PUBLIC)

                # Private 연결 관리
                if private_subs:
                    await self._ensure_connection(WebSocketType.PRIVATE)
                else:
                    await self._disconnect_if_connected(WebSocketType.PRIVATE)

        except Exception as e:
            self.logger.error(f"구독 변경 처리 실패: {e}")

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

    # ================================================================
    # 컴포넌트 관리
    # ================================================================

    async def register_component(
        self,
        component_id: str,
        component_ref: Any,
        subscriptions: Optional[List[SubscriptionSpec]] = None
    ) -> None:
        """컴포넌트 등록"""
        try:
            # WeakRef로 컴포넌트 저장
            self._components[component_id] = weakref.ref(
                component_ref,
                lambda ref: asyncio.create_task(self._cleanup_component(component_id))
            )

            # 구독 등록
            if subscriptions and self._subscription_manager:
                await self._subscription_manager.register_component(
                    component_id,
                    subscriptions
                )

            self.logger.debug(f"컴포넌트 등록: {component_id}")

        except Exception as e:
            self.logger.error(f"컴포넌트 등록 실패 ({component_id}): {e}")
            raise

    async def unregister_component(self, component_id: str) -> None:
        """컴포넌트 해제"""
        try:
            # 구독 해제
            if self._subscription_manager:
                await self._subscription_manager.unregister_component(component_id)

            # 컴포넌트 제거
            self._components.pop(component_id, None)

            self.logger.debug(f"컴포넌트 해제: {component_id}")

        except Exception as e:
            self.logger.error(f"컴포넌트 해제 실패 ({component_id}): {e}")

    async def _cleanup_component(self, component_id: str) -> None:
        """컴포넌트 자동 정리 (WeakRef 콜백)"""
        try:
            self.logger.debug(f"컴포넌트 자동 정리: {component_id}")
            await self.unregister_component(component_id)
        except Exception as e:
            self.logger.error(f"컴포넌트 정리 오류 ({component_id}): {e}")

    # ================================================================
    # 연결 관리
    # ================================================================

    async def _ensure_connection(self, connection_type: WebSocketType) -> None:
        """연결 보장"""
        if self._connection_states[connection_type] != ConnectionState.CONNECTED:
            await self._connect_websocket(connection_type)

    async def _disconnect_if_connected(self, connection_type: WebSocketType) -> None:
        """연결되어 있다면 해제"""
        if self._connection_states[connection_type] == ConnectionState.CONNECTED:
            await self._disconnect_websocket(connection_type)

    async def _connect_websocket(self, connection_type: WebSocketType) -> None:
        """WebSocket 연결"""
        try:
            if not WEBSOCKETS_AVAILABLE:
                raise RuntimeError("websockets 라이브러리가 설치되지 않았습니다")

            self._connection_states[connection_type] = ConnectionState.CONNECTING

            # URL 설정
            url = "wss://api.upbit.com/websocket/v1"

            # 헤더 설정 (Private 연결 시 JWT 포함)
            headers = {}
            if connection_type == WebSocketType.PRIVATE and self._jwt_manager:
                token = await self._jwt_manager.get_valid_token()
                if token:
                    headers["Authorization"] = f"Bearer {token}"

            # 연결 생성
            if not WEBSOCKETS_AVAILABLE or websockets is None:
                raise RuntimeError("websockets 라이브러리가 설치되지 않았습니다")

            connection = await websockets.connect(url, extra_headers=headers)
            self._connections[connection_type] = connection
            self._connection_states[connection_type] = ConnectionState.CONNECTED

            # 메시지 수신 태스크 시작
            task = asyncio.create_task(self._handle_messages(connection_type, connection))
            self._message_tasks[connection_type] = task

            # 현재 구독 전송
            await self._send_current_subscriptions(connection_type)

            self.logger.info(f"WebSocket 연결 성공: {connection_type}")

        except Exception as e:
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED
            self.logger.error(f"WebSocket 연결 실패 ({connection_type}): {e}")
            raise

    async def _disconnect_websocket(self, connection_type: WebSocketType) -> None:
        """WebSocket 연결 해제"""
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

            self.logger.info(f"WebSocket 연결 해제: {connection_type}")

        except Exception as e:
            self.logger.error(f"연결 해제 실패 ({connection_type}): {e}")

    async def _disconnect_all(self) -> None:
        """모든 연결 해제"""
        for connection_type in WebSocketType:
            await self._disconnect_websocket(connection_type)

    async def _send_current_subscriptions(self, connection_type: WebSocketType) -> None:
        """현재 구독 정보 전송"""
        try:
            if connection_type == WebSocketType.PUBLIC and self._subscription_manager:
                subscriptions = self._subscription_manager.get_public_subscriptions()
            elif connection_type == WebSocketType.PRIVATE and self._subscription_manager:
                subscriptions = self._subscription_manager.get_private_subscriptions()
            else:
                subscriptions = {}

            for data_type, symbols in subscriptions.items():
                if symbols:
                    message = self._create_subscription_message(data_type, list(symbols))
                    await self._send_message(connection_type, message)

        except Exception as e:
            self.logger.error(f"구독 전송 실패 ({connection_type}): {e}")

    def _create_subscription_message(self, data_type: DataType, symbols: List[str]) -> str:
        """구독 메시지 생성"""
        message = [
            {"ticket": f"upbit_websocket_v6_{int(time.time())}"},
            {
                "type": data_type.value,
                "codes": symbols,
                "isOnlySnapshot": False,
                "isOnlyRealtime": False
            },
            {"format": "DEFAULT"}
        ]
        return json.dumps(message)

    async def _send_message(self, connection_type: WebSocketType, message: str) -> None:
        """메시지 전송"""
        connection = self._connections[connection_type]
        if connection and self._connection_states[connection_type] == ConnectionState.CONNECTED:
            try:
                await connection.send(message)
                self.logger.debug(f"메시지 전송 완료 ({connection_type})")
            except Exception as e:
                self.logger.error(f"메시지 전송 실패 ({connection_type}): {e}")

    async def _handle_messages(self, connection_type: WebSocketType, connection) -> None:
        """메시지 수신 처리"""
        try:
            async for message in connection:
                try:
                    # JSON 파싱
                    data = json.loads(message)

                    # 이벤트 생성
                    event = self._create_event(connection_type, data)
                    if event and self._data_processor:
                        # 데이터 프로세서로 전달
                        await self._data_processor.route_event(event)

                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패 ({connection_type}): {e}")
                except Exception as e:
                    self.logger.error(f"메시지 처리 실패 ({connection_type}): {e}")

        except Exception as e:
            if WEBSOCKETS_AVAILABLE and websockets and hasattr(websockets, 'exceptions'):
                if isinstance(e, websockets.exceptions.ConnectionClosed):
                    self.logger.info(f"WebSocket 연결 종료: {connection_type}")
                else:
                    self.logger.error(f"메시지 수신 오류 ({connection_type}): {e}")
            else:
                self.logger.error(f"메시지 수신 오류 ({connection_type}): {e}")
        finally:
            self._connection_states[connection_type] = ConnectionState.DISCONNECTED

    def _create_event(self, connection_type: WebSocketType, data: Dict) -> Optional[BaseWebSocketEvent]:
        """이벤트 생성"""
        try:
            # 데이터 타입 감지
            data_type = self._detect_data_type(data)
            if not data_type:
                return None

            # 기본 이벤트 생성
            return BaseWebSocketEvent(
                epoch=int(time.time() * 1000),
                timestamp=time.time(),
                connection_type=connection_type
            )

        except Exception as e:
            self.logger.error(f"이벤트 생성 실패: {e}")
            return None

    def _detect_data_type(self, data: Dict) -> Optional[DataType]:
        """데이터 타입 감지"""
        if 'ty' in data:
            type_value = data['ty']

            # 정확한 매칭
            for data_type in DataType:
                if data_type.value == type_value:
                    return data_type

        return None

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
            is_healthy = (
                self._state == GlobalManagerState.ACTIVE
                and self._data_processor is not None
                and self._subscription_manager is not None
            )

            return HealthStatus(
                status="healthy" if is_healthy else "unhealthy",
                uptime_seconds=0.0,  # 단순화
                total_messages_processed=0,
                connection_errors=0,
                last_error=None if is_healthy else "시스템 오류"
            )
        except Exception as e:
            return HealthStatus(
                status="error",
                uptime_seconds=0.0,
                total_messages_processed=0,
                connection_errors=1,
                last_error=str(e),
                last_error_time=time.time()
            )


# ================================================================
# 전역 접근
# ================================================================

_global_manager: Optional[WebSocketManager] = None


async def get_global_websocket_manager() -> WebSocketManager:
    """글로벌 WebSocket 매니저 반환"""
    global _global_manager
    if _global_manager is None:
        _global_manager = await WebSocketManager.get_instance()
    return _global_manager


async def get_websocket_manager() -> WebSocketManager:
    """WebSocketClient가 사용하는 매니저 반환"""
    return await get_global_websocket_manager()
