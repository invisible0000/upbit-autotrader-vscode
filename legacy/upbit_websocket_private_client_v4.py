"""
업비트 WebSocket v5.0 - Private 클라이언트 (v4.0 통합 버전)

🎯 특징:
- SubscriptionManager v4.0 완전 통합
- 레거시 호환성 제거, 순수 v4.0 API
- JWT 인증 자동 처리 및 토큰 갱신
- Private 데이터 전용 (myOrder, myAsset)
- 보안 강화 및 자동 생명주기 관리
"""
import asyncio
import json
import jwt
import time
import uuid
import websockets
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import (
    validate_mixed_message, create_websocket_message,
    create_connection_status
)
from .config import load_config
from .state import WebSocketState, WebSocketStateMachine
from .subscription_manager import SubscriptionManager
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


class UpbitWebSocketPrivateV5:
    """업비트 WebSocket v5.0 Private 클라이언트 - v4.0 구독 매니저 통합"""

    def __init__(self,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 config_path: Optional[str] = None,
                 event_broker: Optional[Any] = None,
                 cleanup_interval: Optional[int] = None):
        """
        Args:
            access_key: 업비트 API Access Key (None이면 UpbitAuthenticator에서 자동 로드)
            secret_key: 업비트 API Secret Key (None이면 UpbitAuthenticator에서 자동 로드)
            config_path: 설정 파일 경로
            event_broker: 외부 이벤트 브로커
            cleanup_interval: 구독 자동 정리 간격 (초, None이면 30초)
        """
        # UpbitAuthenticator를 통한 API 키 로드
        self.auth = UpbitAuthenticator(access_key, secret_key)

        # API 키 검증
        if not self.auth._access_key or not self.auth._secret_key:
            raise InvalidAPIKeysError("Private WebSocket 클라이언트는 API 키가 필수입니다")

        # 설정 로드
        self.config = load_config(config_path)

        # 상태 관리
        self.state_machine = WebSocketStateMachine()

        # 연결 관리
        self.websocket: Optional[Any] = None
        self.connection_id = str(uuid.uuid4())

        # 🚀 v4.0 구독 관리자 통합 (Private 전용)
        self.subscription_manager = SubscriptionManager(
            cleanup_interval=cleanup_interval or 30
        )

        # JWT 토큰 관리
        self._jwt_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._token_refresh_task: Optional[asyncio.Task] = None

        # 이벤트 시스템
        self.event_broker = event_broker

        # 통계
        self.stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'errors': 0,
            'reconnect_count': 0,
            'start_time': datetime.now(),
            'last_message_time': None,
            'auth_token_refreshes': 0,
            'auth_failures': 0
        }

        # 백그라운드 태스크
        self._tasks: Set[asyncio.Task] = set()

        logger.info(f"Private WebSocket 클라이언트 v4.0 초기화 완료 - ID: {self.connection_id}")

    def _default_callback(self, symbol: str, data_type: str, data: dict):
        """기본 콜백 함수"""
        logger.debug(f"Private 기본 콜백: {symbol} {data_type} 데이터 수신")

    def _generate_jwt_token(self) -> str:
        """JWT 토큰 생성 및 갱신"""
        if not self.auth._secret_key:
            raise InvalidAPIKeysError("Secret Key가 없습니다")

        # 토큰 만료 시간: 현재 시간 + 9분 (10분 만료 전 여유)
        expire_time = datetime.now() + timedelta(minutes=9)

        payload = {
            'iss': self.auth._access_key,
            'exp': int(expire_time.timestamp())
        }

        token = jwt.encode(payload, self.auth._secret_key, algorithm='HS256')

        # 토큰 정보 저장
        self._jwt_token = token
        self._token_expires_at = expire_time

        logger.debug("JWT 토큰 생성 완료")
        return token

    def _is_token_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if not self._token_expires_at:
            return True

        # 만료 1분 전에 갱신 필요로 판단
        return datetime.now() >= (self._token_expires_at - timedelta(minutes=1))

    async def _refresh_token_if_needed(self) -> None:
        """필요시 토큰 갱신"""
        if self._is_token_expired():
            logger.info("JWT 토큰 갱신 중...")
            try:
                self._generate_jwt_token()
                self.stats['auth_token_refreshes'] += 1
                logger.info("JWT 토큰 갱신 완료")
            except Exception as e:
                logger.error(f"JWT 토큰 갱신 실패: {e}")
                self.stats['auth_failures'] += 1

    async def _start_token_refresh_task(self) -> None:
        """토큰 자동 갱신 태스크 시작"""
        async def token_refresh_loop():
            while self.is_connected():
                try:
                    await asyncio.sleep(300)  # 5분마다 체크
                    await self._refresh_token_if_needed()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"토큰 갱신 루프 오류: {e}")

        self._token_refresh_task = asyncio.create_task(token_refresh_loop())
        self._tasks.add(self._token_refresh_task)
        self._token_refresh_task.add_done_callback(self._tasks.discard)

    async def connect(self) -> None:
        """WebSocket 연결 - JWT 인증 포함"""
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

            # 🚀 v4.0 구독 매니저에 WebSocket 연결 설정
            self.subscription_manager.set_websocket_connections(private_ws=self.websocket)

            # 백그라운드 태스크 시작
            self._start_background_tasks()

            # 백그라운드 서비스 시작
            await self.subscription_manager.start_background_services()

            # 토큰 자동 갱신 태스크 시작
            await self._start_token_refresh_task()

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

            # 백그라운드 서비스 중단
            self.subscription_manager.stop_background_services()

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
        """내 주문 구독 - v4.0 단순화"""
        return await self._subscribe(PrivateDataType.MY_ORDER, markets, callback)

    async def subscribe_my_assets(self, callback: Optional[Callable] = None) -> str:
        """내 자산 구독 - v4.0 단순화"""
        return await self._subscribe(PrivateDataType.MY_ASSET, None, callback)

    async def _subscribe(self, data_type: str, markets: Optional[List[str]] = None,
                         callback: Optional[Callable] = None) -> str:
        """Private 데이터 구독 - v4.0 단순화"""
        if not self.is_connected():
            raise SubscriptionError("Private WebSocket이 연결되지 않았습니다", data_type)

        try:
            self.state_machine.transition_to(WebSocketState.SUBSCRIBING)

            # v4.0 실시간 구독
            success = await self.subscription_manager.request_realtime_data(
                symbols=markets or [],  # Private에서는 심볼이 마켓
                data_type=data_type,
                callback=callback or self._default_callback,
                client_id=f"private_{data_type}",
                connection_type="private"
            )

            if success:
                subscription_id = f"private_{data_type}_{int(time.time())}"
                self.state_machine.transition_to(WebSocketState.ACTIVE)
                logger.info(f"Private 구독 완료: {data_type}")
                return subscription_id
            else:
                raise SubscriptionError(f"Private 구독 실패: {data_type}", data_type)

        except Exception as e:
            error = SubscriptionError(f"Private 구독 실패: {str(e)}", data_type)
            await self._handle_error(error)
            raise error

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 해제 - v4.0"""
        try:
            await self.subscription_manager.unsubscribe(subscription_id)
            logger.info(f"Private 구독 해제 완료: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"Private 구독 해제 실패: {e}")
            return False

    async def unsubscribe_all(self) -> bool:
        """모든 구독 해제 - v4.0"""
        try:
            return await self.subscription_manager.unsubscribe_all("private")
        except Exception as e:
            logger.error(f"Private 전체 구독 해제 실패: {e}")
            return False

    # JWT 토큰 관리 메서드들
    async def rotate_jwt_token(self, force: bool = False) -> bool:
        """JWT 토큰 강제 순환 갱신"""
        logger.info(f"🔄 JWT 토큰 {'강제 ' if force else ''}순환 갱신 시작")

        try:
            if force or self._is_token_expired():
                self._generate_jwt_token()
                self.stats['auth_token_refreshes'] += 1
                logger.info("JWT 토큰 순환 갱신 완료")
                return True
            else:
                logger.info("JWT 토큰이 아직 유효하여 갱신하지 않음")
                return True

        except Exception as e:
            logger.error(f"JWT 토큰 순환 갱신 실패: {e}")
            self.stats['auth_failures'] += 1
            return False

    async def get_auth_status(self) -> Dict[str, Any]:
        """Private 인증 상태 종합 정보"""
        current_time = time.time()

        # JWT 토큰 상태
        jwt_status = {
            "exists": bool(self._jwt_token),
            "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
            "time_to_expiry": (self._token_expires_at.timestamp() - current_time) if self._token_expires_at else None,
            "auto_refresh_active": self._token_refresh_task is not None and not self._token_refresh_task.done()
        }

        # 연결 상태
        connection_status = {
            "connected": self.is_connected(),
            "connection_state": self.state_machine.current_state.name
        }

        # 구독 상태
        subscription_state = self.subscription_manager.get_state()

        return {
            "jwt": jwt_status,
            "connection": connection_status,
            "subscriptions": {
                "realtime_intents": len(subscription_state.get('realtime_intents', {})),
                "private_connection": subscription_state.get('private_connection', {})
            },
            "security_level": "private_authenticated" if jwt_status["exists"] else "unauthenticated",
            "status_checked_at": current_time
        }

    # 상태 조회 메서드들
    async def get_status(self) -> Dict[str, Any]:
        """연결 상태 조회 - v4.0"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # v4.0 구독 정보
        subscription_state = self.subscription_manager.get_state()

        return {
            **create_connection_status(
                state=self.state_machine.current_state.name,
                connection_id=self.connection_id
            ),
            "uptime_seconds": round(uptime, 2),
            "messages_received": self.stats['messages_received'],
            "messages_processed": self.stats['messages_processed'],
            "error_count": self.stats['errors'],
            "auth_metrics": {
                "token_refreshes": self.stats['auth_token_refreshes'],
                "auth_failures": self.stats['auth_failures'],
                "token_expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
                "token_valid": not self._is_token_expired()
            },
            "subscription_state": subscription_state
        }

    async def health_check(self) -> Dict[str, Any]:
        """종합 건강 상태 체크 - v4.0"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()

        # 연결 상태 체크
        is_connected = self.is_connected()

        # 최근 메시지 수신 확인 (30초 이내)
        last_message_ago = None
        if self.stats['last_message_time']:
            last_message_ago = (current_time - self.stats['last_message_time']).total_seconds()

        # JWT 토큰 상태 확인
        token_valid = not self._is_token_expired()

        # 건강도 점수 계산
        health_score = 100

        if not is_connected:
            health_score -= 50

        if not token_valid:
            health_score -= 30

        if last_message_ago and last_message_ago > 60:
            health_score -= 15

        if self.stats['errors'] / max(self.stats['messages_received'], 1) > 0.02:
            health_score -= 10

        if self.stats['auth_failures'] > 0:
            health_score -= 5

        # 상태 등급
        if health_score >= 90:
            status = "🟢 EXCELLENT"
        elif health_score >= 75:
            status = "🟡 GOOD"
        elif health_score >= 50:
            status = "🟠 WARNING"
        else:
            status = "🔴 CRITICAL"

        # v4.0 구독 정보
        subscription_state = self.subscription_manager.get_state()
        active_intents = len(subscription_state.get('realtime_intents', {}))

        return {
            'overall_status': status,
            'health_score': max(0, health_score),
            'connection_status': '🟢 Connected' if is_connected else '🔴 Disconnected',
            'auth_status': '🟢 Valid Token' if token_valid else '🔴 Invalid Token',
            'uptime_minutes': round(uptime / 60, 1),
            'last_message_seconds_ago': round(last_message_ago, 1) if last_message_ago else None,
            'error_count': self.stats['errors'],
            'active_subscriptions': active_intents,
            'token_auto_refresh': self._token_refresh_task is not None and not self._token_refresh_task.done()
        }

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.state_machine.is_connected()

    def get_supported_data_types(self) -> List[str]:
        """Private 클라이언트가 지원하는 데이터 타입 목록"""
        return [PrivateDataType.MY_ORDER, PrivateDataType.MY_ASSET]

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
        """메시지 수신 루프 - v4.0 단순화"""
        logger.info("Private 메시지 수신 루프 시작")

        try:
            if self.websocket:
                async for message in self.websocket:
                    self.stats['messages_received'] += 1
                    self.stats['last_message_time'] = datetime.now()
                    await self._process_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.warning("Private WebSocket 연결이 종료되었습니다")
            await self._handle_disconnection()

        except Exception as e:
            logger.error(f"Private 메시지 루프 오류: {e}")
            self.stats['errors'] += 1
            await self._handle_error(WebSocketError(
                f"Private 메시지 루프 오류: {str(e)}",
                error_code=ErrorCode.CONNECTION_FAILED
            ))

    async def _process_message(self, raw_message: str) -> None:
        """메시지 처리 - v4.0 단순화"""
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
            self.stats['errors'] += 1
            error = MessageParsingError(raw_message, str(e))
            await self._handle_error(error)
        except Exception as e:
            self.stats['errors'] += 1
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
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("myOrder", "PRIVATE", validated_data)
            await self._emit_data(PrivateDataType.MY_ORDER, message)
        except Exception as e:
            logger.error(f"MyOrder 데이터 처리 오류: {e}")

    async def _handle_my_asset(self, data: Dict[str, Any]) -> None:
        """내 자산 데이터 처리"""
        try:
            validated_data = validate_mixed_message(data)
            message = create_websocket_message("myAsset", "PRIVATE", validated_data)
            await self._emit_data(PrivateDataType.MY_ASSET, message)
        except Exception as e:
            logger.error(f"MyAsset 데이터 처리 오류: {e}")

    async def _emit_data(self, data_type: str, data: Any) -> None:
        """데이터 발송 - v4.0 직접 처리"""
        # v4.0에서는 on_data_received로 직접 처리
        symbol = "PRIVATE"  # Private 데이터는 심볼이 없음
        self.subscription_manager.on_data_received(symbol, data_type, data)

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

        # 인증 관련 오류는 별도 처리
        if isinstance(error, InvalidAPIKeysError):
            self.stats['auth_failures'] += 1

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
        """재연결 시도 - JWT 토큰 갱신 포함"""
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

                # 토큰 갱신 후 재연결
                await self._refresh_token_if_needed()
                await self.connect()

                logger.info("Private 재연결 성공")
                return

            except Exception as e:
                logger.error(f"Private 재연결 실패 (시도 {attempt + 1}): {e}")

        logger.error("Private 최대 재연결 시도 횟수 초과")
        self.state_machine.transition_to(WebSocketState.ERROR)


# 편의 함수들
async def create_private_client(access_key: Optional[str] = None,
                                secret_key: Optional[str] = None,
                                config_path: Optional[str] = None,
                                event_broker: Optional[Any] = None,
                                cleanup_interval: int = 30) -> UpbitWebSocketPrivateV5:
    """Private 클라이언트 생성"""
    client = UpbitWebSocketPrivateV5(
        access_key=access_key,
        secret_key=secret_key,
        config_path=config_path,
        event_broker=event_broker,
        cleanup_interval=cleanup_interval
    )
    await client.connect()
    return client


async def quick_subscribe_my_orders(access_key: Optional[str] = None,
                                    secret_key: Optional[str] = None,
                                    markets: Optional[List[str]] = None,
                                    callback: Optional[Callable] = None) -> UpbitWebSocketPrivateV5:
    """빠른 내 주문 구독 (개발/테스트용)"""
    client = await create_private_client(access_key, secret_key)
    await client.subscribe_my_orders(markets, callback)
    return client


async def quick_subscribe_my_assets(access_key: Optional[str] = None,
                                    secret_key: Optional[str] = None,
                                    callback: Optional[Callable] = None) -> UpbitWebSocketPrivateV5:
    """빠른 내 자산 구독 (개발/테스트용)"""
    client = await create_private_client(access_key, secret_key)
    await client.subscribe_my_assets(callback)
    return client
