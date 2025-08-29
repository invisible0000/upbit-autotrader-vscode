"""
업비트 WebSocket v5.0 - Private 클라이언트 (새 버전)

🎯 특징:
- Private 데이터 전용 (myOrder, myAsset)
- 최대 2개 티켓 제한
- JWT 인증 자동 처리
- 효율적인 티켓 재사용
- 명시적 상태 관리
- 타입 안전성 (Pydantic)
- Infrastructure 로깅 시스템
"""

import asyncio
import json
import jwt
import time
import uuid
import websockets
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import (
    infer_message_type, validate_mixed_message, create_websocket_message,
    create_connection_status, update_connection_status
)
from .config import load_config
from .state import WebSocketState, WebSocketStateMachine
from .exceptions import (
    WebSocketError, WebSocketConnectionError, WebSocketConnectionTimeoutError,
    SubscriptionError, MessageParsingError, InvalidAPIKeysError,
    ErrorCode
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator

logger = create_component_logger("UpbitWebSocketPrivateV5")


class PrivateDataType:
    """Private 데이터 타입"""
    MY_ORDER = "myOrder"
    MY_ASSET = "myAsset"


class PrivateTicketManager:
    """Private 전용 티켓 관리자 - 최대 2개 티켓"""

    def __init__(self, max_tickets: int = 2):
        self.max_tickets = max_tickets
        self.tickets: Dict[str, Dict[str, Any]] = {}
        self.data_type_mapping: Dict[str, str] = {}

        logger.info(f"Private 티켓 매니저 초기화 - 최대 {max_tickets}개 티켓")

    def get_or_create_ticket(self, data_type: str, markets: Optional[List[str]] = None) -> str:
        """Private 데이터 타입에 대한 티켓 획득"""
        # 기존 티켓이 있으면 재사용
        if data_type in self.data_type_mapping:
            ticket_id = self.data_type_mapping[data_type]
            logger.debug(f"기존 Private 티켓 재사용: {ticket_id} for {data_type}")
            return ticket_id

        # 새 티켓 생성
        if len(self.tickets) >= self.max_tickets:
            raise SubscriptionError(
                f"Private 티켓 한계 초과: {len(self.tickets)}/{self.max_tickets}",
                data_type
            )

        # 새 티켓 생성
        ticket_id = f"private-{uuid.uuid4().hex[:8]}"
        self.tickets[ticket_id] = {
            'data_types': {data_type},
            'markets': set(markets) if markets else set(),
            'created_at': datetime.now()
        }
        self.data_type_mapping[data_type] = ticket_id

        logger.info(f"새 Private 티켓 생성: {ticket_id} for {data_type}")
        return ticket_id

    def get_ticket_message(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Private 티켓의 구독 메시지 생성"""
        if ticket_id not in self.tickets:
            raise ValueError(f"Private 티켓을 찾을 수 없습니다: {ticket_id}")

        ticket_info = self.tickets[ticket_id]
        message = [{"ticket": ticket_id}]

        for data_type in ticket_info['data_types']:
            if data_type == PrivateDataType.MY_ORDER:
                sub_message = {"type": "myOrder"}
                if ticket_info['markets']:
                    sub_message["codes"] = list(ticket_info['markets'])
                message.append(sub_message)
            elif data_type == PrivateDataType.MY_ASSET:
                message.append({"type": "myAsset"})

        message.append({"format": "DEFAULT"})
        return message

    def get_stats(self) -> Dict[str, Any]:
        """Private 티켓 사용 통계"""
        return {
            "total_tickets": len(self.tickets),
            "max_tickets": self.max_tickets,
            "ticket_efficiency": (self.max_tickets - len(self.tickets)) / self.max_tickets * 100,
            "tickets": {
                tid: {
                    "data_types": list(info['data_types']),
                    "markets": list(info['markets']),
                    "created_at": info['created_at'].isoformat()
                }
                for tid, info in self.tickets.items()
            }
        }


class UpbitWebSocketPrivateV5:
    """업비트 WebSocket v5.0 Private 클라이언트"""

    def __init__(self,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 config_path: Optional[str] = None,
                 event_broker: Optional[Any] = None,
                 max_tickets: Optional[int] = None):
        """
        Args:
            access_key: 업비트 API Access Key (None이면 UpbitAuthenticator에서 자동 로드)
            secret_key: 업비트 API Secret Key (None이면 UpbitAuthenticator에서 자동 로드)
            config_path: 설정 파일 경로
            event_broker: 외부 이벤트 브로커
            max_tickets: 최대 티켓 수 (None이면 config의 private_pool_size 사용)
        """
        # UpbitAuthenticator를 통한 API 키 로드
        self.auth = UpbitAuthenticator(access_key, secret_key)

        # API 키 검증
        if not self.auth._access_key or not self.auth._secret_key:
            raise InvalidAPIKeysError("API 키가 설정되지 않았습니다")

        # 설정 로드
        self.config = load_config(config_path)

        # max_tickets 결정 (매개변수 우선, 없으면 config의 private_pool_size 사용)
        effective_max_tickets = (max_tickets
                                 if max_tickets is not None
                                 else self.config.subscription.private_pool_size)

        # 상태 관리
        self.state_machine = WebSocketStateMachine()

        # 연결 관리
        self.websocket: Optional[Any] = None
        self.connection_id = str(uuid.uuid4())

        # 티켓 관리
        self.ticket_manager = PrivateTicketManager(effective_max_tickets)

        # 구독 관리
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.callbacks: Dict[str, Callable] = {}

        # 이벤트 시스템
        self.event_broker = event_broker

        # 통계
        self.stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors': 0,
            'reconnect_count': 0,
            'start_time': datetime.now()
        }

        # 백그라운드 태스크
        self._tasks: Set[asyncio.Task] = set()

        logger.info(f"Private WebSocket 클라이언트 초기화 완료 - ID: {self.connection_id}")

    def _generate_jwt_token(self) -> str:
        """JWT 토큰 생성"""
        if not self.auth._secret_key:
            raise InvalidAPIKeysError("Secret Key가 없습니다")

        payload = {
            'iss': self.auth._access_key,
            'exp': int(time.time()) + 600  # 10분 후 만료
        }

        token = jwt.encode(payload, self.auth._secret_key, algorithm='HS256')
        logger.debug("JWT 토큰 생성 완료")
        return token

    async def connect(self) -> None:
        """WebSocket 연결"""
        if self.state_machine.current_state != WebSocketState.DISCONNECTED:
            logger.warning(f"이미 연결된 상태입니다: {self.state_machine.current_state}")
            return

        try:
            self.state_machine.transition_to(WebSocketState.CONNECTING)
            logger.info(f"Private WebSocket 연결 시도: {self.config.connection.url}")

            # JWT 토큰 생성
            jwt_token = self._generate_jwt_token()

            # WebSocket 연결 (Authorization 헤더 포함)
            headers = {
                'Authorization': f'Bearer {jwt_token}'
            }

            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    self.config.connection.url,
                    extra_headers=headers,
                    ping_interval=self.config.connection.ping_interval,
                    ping_timeout=self.config.connection.ping_timeout,
                    close_timeout=self.config.connection.close_timeout
                ),
                timeout=self.config.connection.connect_timeout
            )

            self.state_machine.transition_to(WebSocketState.CONNECTED)
            logger.info("Private WebSocket 연결 완료")

            # 백그라운드 태스크 시작
            self._start_background_tasks()

            # 이벤트 발송
            await self._emit_event("websocket.private.connected", {
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat()
            })

        except asyncio.TimeoutError:
            error = WebSocketConnectionTimeoutError(
                self.config.connection.connect_timeout,
                self.config.connection.url
            )
            await self._handle_error(error)
            raise error

        except Exception as e:
            error = WebSocketConnectionError(
                f"Private WebSocket 연결 실패: {str(e)}",
                self.config.connection.url,
                e
            )
            await self._handle_error(error)
            raise error

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        if self.state_machine.current_state == WebSocketState.DISCONNECTED:
            logger.info("이미 연결 해제된 상태입니다")
            return

        try:
            self.state_machine.transition_to(WebSocketState.DISCONNECTING)
            logger.info("Private WebSocket 연결 해제 시작")

            # 백그라운드 태스크 정리
            await self._cleanup_tasks()

            # WebSocket 연결 종료
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            self.state_machine.transition_to(WebSocketState.DISCONNECTED)
            logger.info("Private WebSocket 연결 해제 완료")

            # 이벤트 발송
            await self._emit_event("websocket.private.disconnected", {
                "connection_id": self.connection_id,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Private 연결 해제 중 오류: {e}")
            self.state_machine.transition_to(WebSocketState.ERROR)

    async def subscribe_my_orders(self, markets: Optional[List[str]] = None,
                                  callback: Optional[Callable] = None) -> str:
        """내 주문 구독"""
        return await self._subscribe(PrivateDataType.MY_ORDER, markets, callback)

    async def subscribe_my_assets(self, callback: Optional[Callable] = None) -> str:
        """내 자산 구독"""
        return await self._subscribe(PrivateDataType.MY_ASSET, None, callback)

    async def _subscribe(self, data_type: str, markets: Optional[List[str]] = None,
                         callback: Optional[Callable] = None) -> str:
        """Private 데이터 구독"""
        if not self.is_connected():
            raise SubscriptionError("WebSocket이 연결되지 않았습니다", data_type)

        try:
            self.state_machine.transition_to(WebSocketState.SUBSCRIBING)

            # 티켓 생성/획득
            ticket_id = self.ticket_manager.get_or_create_ticket(data_type, markets)

            # 구독 메시지 생성
            subscribe_message = self.ticket_manager.get_ticket_message(ticket_id)

            # 구독 요청 전송
            if self.websocket:
                await self.websocket.send(json.dumps(subscribe_message))

            # 구독 정보 저장
            subscription_id = f"{data_type}-{uuid.uuid4().hex[:8]}"
            self.subscriptions[subscription_id] = {
                'data_type': data_type,
                'markets': markets,
                'ticket_id': ticket_id,
                'created_at': datetime.now(),
                'message_count': 0
            }

            # 콜백 등록
            if callback:
                self.callbacks[subscription_id] = callback

            logger.info(f"Private 구독 완료: {data_type}")

            self.state_machine.transition_to(WebSocketState.ACTIVE)

            # 이벤트 발송
            await self._emit_event("websocket.private.subscribed", {
                "subscription_id": subscription_id,
                "data_type": data_type,
                "markets": markets,
                "ticket_id": ticket_id
            })

            return subscription_id

        except Exception as e:
            error = SubscriptionError(f"Private 구독 실패: {str(e)}", data_type)
            await self._handle_error(error)
            raise error

    async def unsubscribe(self, subscription_id: str) -> None:
        """구독 해제"""
        if subscription_id not in self.subscriptions:
            logger.warning(f"Private 구독을 찾을 수 없습니다: {subscription_id}")
            return

        try:
            subscription = self.subscriptions[subscription_id]
            data_type = subscription['data_type']

            # 구독 정보 제거
            del self.subscriptions[subscription_id]
            if subscription_id in self.callbacks:
                del self.callbacks[subscription_id]

            logger.info(f"Private 구독 해제 완료: {subscription_id}")

            # 이벤트 발송
            await self._emit_event("websocket.private.unsubscribed", {
                "subscription_id": subscription_id,
                "data_type": data_type
            })

        except Exception as e:
            logger.error(f"Private 구독 해제 중 오류: {e}")

    async def get_status(self) -> Dict[str, Any]:
        """연결 상태 조회"""
        uptime = (datetime.now() - self.stats['start_time']).total_seconds()

        return create_connection_status(
            state=self.state_machine.current_state.name,
            connection_id=self.connection_id
        )

    def get_ticket_stats(self) -> Dict[str, Any]:
        """티켓 사용 통계"""
        return self.ticket_manager.get_stats()

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.state_machine.is_connected()

    # 내부 메서드들
    def _start_background_tasks(self) -> None:
        """백그라운드 태스크 시작"""
        # 메시지 수신 루프
        task = asyncio.create_task(self._message_loop())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _cleanup_tasks(self) -> None:
        """백그라운드 태스크 정리"""
        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks.clear()

    async def _message_loop(self) -> None:
        """메시지 수신 루프"""
        logger.info("Private 메시지 수신 루프 시작")

        try:
            if self.websocket:
                async for message in self.websocket:
                    self.stats['messages_received'] += 1
                    await self._process_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Private WebSocket 연결이 종료되었습니다")
            await self._handle_disconnection()

        except Exception as e:
            logger.error(f"Private 메시지 루프 오류: {e}")
            await self._handle_error(WebSocketError(
                f"Private 메시지 루프 오류: {str(e)}",
                error_code=ErrorCode.CONNECTION_FAILED
            ))

    async def _process_message(self, raw_message: str) -> None:
        """메시지 처리"""
        try:
            data = json.loads(raw_message)

            # 메시지 타입 식별
            message_type = self._identify_data_type(data)
            if not message_type:
                logger.debug(f"알 수 없는 Private 메시지: {data}")
                return

            # 메시지별 처리
            if message_type == PrivateDataType.MY_ORDER:
                await self._handle_my_order(data)
            elif message_type == PrivateDataType.MY_ASSET:
                await self._handle_my_asset(data)

            self.stats['messages_processed'] += 1

        except json.JSONDecodeError as e:
            error = MessageParsingError(raw_message, str(e))
            await self._handle_error(error)
        except Exception as e:
            logger.error(f"Private 메시지 처리 중 오류: {e}")

    def _identify_data_type(self, data: Dict[str, Any]) -> Optional[str]:
        """Private 메시지 타입 식별"""
        if "type" in data:
            return data["type"]

        # 데이터 구조로 타입 추정
        if "order_type" in data or "side" in data:
            return PrivateDataType.MY_ORDER
        elif "currency" in data and "balance" in data:
            return PrivateDataType.MY_ASSET

        return None

    async def _handle_my_order(self, data: Dict[str, Any]) -> None:
        """내 주문 데이터 처리"""
        try:
            # 메시지 검증 및 정리
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("myOrder", "PRIVATE", validated_data)
            await self._emit_data(PrivateDataType.MY_ORDER, message)
        except Exception as e:
            logger.error(f"MyOrder 데이터 처리 오류: {e}")

    async def _handle_my_asset(self, data: Dict[str, Any]) -> None:
        """내 자산 데이터 처리"""
        try:
            # 메시지 검증 및 정리
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("myAsset", "PRIVATE", validated_data)
            await self._emit_data(PrivateDataType.MY_ASSET, message)
        except Exception as e:
            logger.error(f"MyAsset 데이터 처리 오류: {e}")

    async def _emit_data(self, data_type: str, data: Any) -> None:
        """데이터 발송"""
        # 콜백 실행
        for subscription_id, callback in self.callbacks.items():
            if self.subscriptions[subscription_id]['data_type'] == data_type:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Private 콜백 실행 오류: {e}")

        # 이벤트 브로커로 발송
        if self.event_broker:
            await self._emit_event(f"websocket.private.{data_type}", data)

    async def _emit_event(self, event_type: str, data: Any) -> None:
        """이벤트 발송"""
        if self.event_broker:
            try:
                await self.event_broker.emit(event_type, data)
            except Exception as e:
                logger.error(f"Private 이벤트 발송 오류: {e}")

    async def _handle_error(self, error: WebSocketError) -> None:
        """오류 처리"""
        self.stats['errors'] += 1
        logger.error(f"Private WebSocket 오류: {error}")

        self.state_machine.transition_to(WebSocketState.ERROR)

        # 이벤트 발송
        await self._emit_event("websocket.private.error", {
            "error_code": error.error_code.value,
            "message": str(error),
            "recovery_action": error.recovery_action.value
        })

    async def _handle_disconnection(self) -> None:
        """연결 해제 처리"""
        logger.warning("Private WebSocket 연결이 끊어졌습니다")

        if self.config.reconnection.auto_reconnect:
            await self._attempt_reconnect()
        else:
            self.state_machine.transition_to(WebSocketState.DISCONNECTED)

    async def _attempt_reconnect(self) -> None:
        """재연결 시도"""
        max_attempts = self.config.reconnection.max_attempts

        for attempt in range(max_attempts):
            try:
                self.stats['reconnect_count'] += 1
                logger.info(f"Private 재연결 시도 {attempt + 1}/{max_attempts}")

                # 지연 시간 계산
                delay = min(
                    self.config.reconnection.initial_delay * (self.config.reconnection.backoff_multiplier ** attempt),
                    self.config.reconnection.max_delay
                )

                await asyncio.sleep(delay)

                # 재연결
                await self.connect()

                # 구독 복원
                await self._restore_subscriptions()

                logger.info("Private 재연결 성공")
                return

            except Exception as e:
                logger.error(f"Private 재연결 실패 (시도 {attempt + 1}): {e}")

        logger.error("Private 최대 재연결 시도 횟수 초과")
        self.state_machine.transition_to(WebSocketState.ERROR)

    async def _restore_subscriptions(self) -> None:
        """구독 복원"""
        logger.info("Private 구독 복원 시작")

        for subscription_id, subscription in self.subscriptions.copy().items():
            try:
                await self._subscribe(
                    subscription['data_type'],
                    subscription['markets'],
                    self.callbacks.get(subscription_id)
                )
                logger.debug(f"Private 구독 복원 완료: {subscription_id}")
            except Exception as e:
                logger.error(f"Private 구독 복원 실패: {subscription_id}, {e}")


# 편의 함수
async def create_private_client(access_key: Optional[str] = None,
                                secret_key: Optional[str] = None,
                                config_path: Optional[str] = None,
                                event_broker: Optional[Any] = None,
                                max_tickets: int = 2) -> UpbitWebSocketPrivateV5:
    """Private 클라이언트 생성"""
    client = UpbitWebSocketPrivateV5(access_key, secret_key, config_path, event_broker, max_tickets)
    await client.connect()
    return client
