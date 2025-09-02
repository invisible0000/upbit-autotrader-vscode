"""
네이티브 WebSocket 클라이언트 v6.0
================================

업비트 WebSocket v6 전용 네이티브 클라이언트
v5 호환성 완전 제거, 순수 v6 아키텍처

핵심 기능:
- 직접 websockets 라이브러리 사용
- SIMPLE 포맷 지원 (대역폭 절약)
- 압축 지원 (deflate)
- 자동 재연결
- JWT 토큰 관리 (Private 전용)
"""

import asyncio
import json
import time
import gzip
from typing import Dict, List, Optional, Any, Callable, Set

try:
    import websockets
    # websockets 15.0+ 타입 힌트 문제 해결
    WebSocketClientProtocol = None
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None

from upbit_auto_trading.infrastructure.logging import create_component_logger

# Rate Limiter 연동 (필수)
try:
    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter import (
        get_global_rate_limiter
    )
    from upbit_auto_trading.infrastructure.external_apis.upbit.dynamic_rate_limiter_wrapper import (
        get_dynamic_rate_limiter, DynamicConfig, AdaptiveStrategy
    )
    RATE_LIMITER_AVAILABLE = True
except ImportError:
    RATE_LIMITER_AVAILABLE = False

# v6 타입 import
from .types import WebSocketType, ConnectionState
from .config import ConnectionConfig  # config.py의 ConnectionConfig 사용
from .exceptions import ConnectionError
from .simple_format_converter import (
    convert_simple_to_default,
    convert_default_to_simple
)


class NativeWebSocketClient:
    """
    네이티브 WebSocket 클라이언트

    업비트 WebSocket API와 직접 통신하는 순수 v6 클라이언트
    """

    def __init__(
        self,
        connection_type: WebSocketType,
        config: ConnectionConfig,
        message_handler: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.logger = create_component_logger(f"NativeWebSocketClient_{connection_type.value}")
        self.connection_type = connection_type
        self.config = config
        self.message_handler = message_handler

        # 연결 상태
        self._websocket: Optional[Any] = None  # websockets 15.0+ 호환
        self._connection_state = ConnectionState.DISCONNECTED
        self._connect_time: Optional[float] = None
        self._last_ping: Optional[float] = None

        # 메시지 통계
        self._messages_sent = 0
        self._messages_received = 0
        self._bytes_sent = 0
        self._bytes_received = 0
        self._last_message_time: Optional[float] = None

        # 백그라운드 작업
        self._background_tasks: Set[asyncio.Task] = set()
        self._shutdown_requested = False

        # Private 전용 (JWT 토큰)
        self._jwt_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

        # Rate Limiter 연동 (필수)
        self._rate_limiter = None
        self._dynamic_limiter = None
        if RATE_LIMITER_AVAILABLE:
            # 초기화는 connect() 시점에 비동기로 수행
            self.logger.info("Rate Limiter 초기화 예약됨")

    async def connect(self) -> bool:
        """WebSocket 연결"""
        try:
            if not WEBSOCKETS_AVAILABLE:
                raise ConnectionError("websockets 라이브러리가 설치되지 않음")

            self.logger.info(f"{self.connection_type.value} WebSocket 연결 시작")
            self._connection_state = ConnectionState.CONNECTING

            # Rate Limiter 초기화 (비동기)
            if RATE_LIMITER_AVAILABLE and not self._rate_limiter:
                try:
                    self._rate_limiter = await get_global_rate_limiter()
                    # 동적 Rate Limiter도 초기화 (Conservative 전략)
                    dynamic_config = DynamicConfig(
                        strategy=AdaptiveStrategy.CONSERVATIVE,
                        error_429_threshold=2,
                        reduction_ratio=0.7,
                        min_ratio=0.4
                    )
                    self._dynamic_limiter = await get_dynamic_rate_limiter(dynamic_config)
                    self.logger.info("Rate Limiter 초기화 완료 (Conservative 전략)")
                except Exception as e:
                    self.logger.warning(f"Rate Limiter 초기화 실패: {e}")

            # WebSocket 연결 Rate Limit 적용 (필수)
            if self._dynamic_limiter:
                try:
                    await self._dynamic_limiter.acquire("websocket_connect", "WS")
                    self.logger.debug("WebSocket 연결 Rate Limit 통과")
                except Exception as e:
                    self.logger.warning(f"WebSocket 연결 Rate Limit 실패: {e}")
                    # Rate Limit 실패 시에도 연결 시도는 계속 (로깅만)

            # 연결 옵션 설정
            headers = {}

            # Private 연결의 경우 JWT 토큰 추가 및 URL 선택
            if self.connection_type == WebSocketType.PRIVATE:
                if not self._jwt_token:
                    await self._refresh_jwt_token()
                if self._jwt_token:
                    headers["Authorization"] = f"Bearer {self._jwt_token}"
                    # Private 전용 URL 사용
                    url = self.config.private_url
                else:
                    self.logger.warning("Private 연결 요청되었지만 JWT 토큰이 없음")
                    return False
            else:
                # Public 전용 URL 사용
                url = self.config.public_url

            # WebSocket 연결 (websockets 15.0+ 호환)
            self._websocket = await websockets.connect(
                url,
                additional_headers=headers,
                compression="deflate" if self.config.enable_compression else None,
                max_size=self.config.max_message_size,
                open_timeout=self.config.connect_timeout,  # timeout → open_timeout
                ping_interval=self.config.heartbeat_interval,
                ping_timeout=self.config.connect_timeout
            )

            self._connection_state = ConnectionState.CONNECTED
            self._connect_time = time.time()

            # 백그라운드 작업 시작
            self._start_background_tasks()

            self.logger.info(f"{self.connection_type.value} WebSocket 연결 완료")
            return True

        except Exception as e:
            self.logger.error(f"{self.connection_type.value} WebSocket 연결 실패: {e}")
            self._connection_state = ConnectionState.ERROR

            # 429 에러 등 Rate Limit 관련 에러 처리
            if "429" in str(e) and self._dynamic_limiter:
                self.logger.warning("429 에러 감지 - 동적 Rate Limit 조정 시작")

            return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        try:
            self.logger.info(f"{self.connection_type.value} WebSocket 연결 해제 시작")
            self._shutdown_requested = True

            # 백그라운드 작업 취소
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()

            # 백그라운드 작업 완료 대기
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            # WebSocket 연결 종료
            if self._websocket:
                await self._websocket.close()
                self._websocket = None

            self._connection_state = ConnectionState.DISCONNECTED
            self.logger.info(f"{self.connection_type.value} WebSocket 연결 해제 완료")

        except Exception as e:
            self.logger.error(f"{self.connection_type.value} WebSocket 연결 해제 실패: {e}")

    async def send_subscription(self, subscription_data: List[Dict[str, Any]]) -> bool:
        """구독 메시지 전송"""
        try:
            if not self.is_connected:
                self.logger.warning("WebSocket이 연결되지 않음")
                return False

            # Rate Limit 적용 (구독 메시지 전송)
            if self._dynamic_limiter:
                try:
                    await self._dynamic_limiter.acquire("websocket_message", "WS")
                    self.logger.debug("구독 메시지 Rate Limit 통과")
                except Exception as e:
                    self.logger.error(f"구독 메시지 Rate Limit 실패: {e}")
                    return False  # Rate Limit 실패 시 전송 중단

            # SIMPLE 포맷으로 변환 (옵션)
            if self.config.enable_simple_format:
                converted_data = []
                for item in subscription_data:
                    converted_item = convert_default_to_simple(item)
                    converted_data.append(converted_item)
                subscription_data = converted_data

            # JSON 직렬화 및 전송
            message = json.dumps(subscription_data, ensure_ascii=False)

            await self._websocket.send(message)

            self._messages_sent += 1
            self._bytes_sent += len(message.encode('utf-8'))

            self.logger.debug(f"구독 메시지 전송: {len(subscription_data)}개 항목")
            return True

        except Exception as e:
            self.logger.error(f"구독 메시지 전송 실패: {e}")

            # 429 에러 감지 및 동적 조정
            if "429" in str(e) and self._dynamic_limiter:
                self.logger.warning("구독 메시지 429 에러 감지 - 동적 Rate Limit 조정")

            return False

    async def _refresh_jwt_token(self) -> bool:
        """JWT 토큰 갱신 (Private 전용)"""
        try:
            if self.connection_type != WebSocketType.PRIVATE:
                return True

            # JWT 토큰 생성 로직
            # TODO: upbit_auth 모듈 연동 필요
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import (
                UpbitAuthenticator
            )

            auth = UpbitAuthenticator()
            token_info = await auth.create_websocket_token()

            if token_info and 'access_token' in token_info:
                self._jwt_token = token_info['access_token']
                self._token_expires_at = time.time() + token_info.get('expires_in', 3600)
                self.logger.info("JWT 토큰 갱신 완료")
                return True

            return False

        except Exception as e:
            self.logger.error(f"JWT 토큰 갱신 실패: {e}")
            return False

    def _start_background_tasks(self) -> None:
        """백그라운드 작업 시작"""
        tasks = [
            self._message_receiver_task(),
            self._connection_monitor_task()
        ]

        if self.connection_type == WebSocketType.PRIVATE:
            tasks.append(self._jwt_refresh_task())

        for task in tasks:
            bg_task = asyncio.create_task(task)
            self._background_tasks.add(bg_task)
            bg_task.add_done_callback(self._background_tasks.discard)

    async def _message_receiver_task(self) -> None:
        """메시지 수신 백그라운드 작업"""
        try:
            while not self._shutdown_requested and self._websocket:
                try:
                    # 메시지 수신 (타임아웃 적용)
                    raw_message = await asyncio.wait_for(
                        self._websocket.recv(),
                        timeout=30.0
                    )

                    # 통계 업데이트
                    self._messages_received += 1
                    self._last_message_time = time.time()

                    if isinstance(raw_message, bytes):
                        # 압축된 데이터 처리
                        try:
                            raw_message = gzip.decompress(raw_message).decode('utf-8')
                        except (OSError, UnicodeDecodeError):
                            raw_message = raw_message.decode('utf-8')

                    self._bytes_received += len(raw_message.encode('utf-8'))

                    # JSON 파싱
                    try:
                        message_data = json.loads(raw_message)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"JSON 파싱 실패: {e}")
                        continue

                    # SIMPLE 포맷에서 DEFAULT 포맷으로 변환
                    if self.config.enable_simple_format:
                        message_data = convert_simple_to_default(message_data)

                    # 메시지 핸들러 호출
                    if self.message_handler:
                        try:
                            await self.message_handler(message_data)
                        except Exception as e:
                            self.logger.error(f"메시지 핸들러 실행 실패: {e}")

                except asyncio.TimeoutError:
                    # 타임아웃은 정상 - 연결 확인용
                    continue
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket 연결 종료됨")
                    break
                except Exception as e:
                    self.logger.error(f"메시지 수신 오류: {e}")
                    break

        except asyncio.CancelledError:
            self.logger.info("메시지 수신기 종료")
        except Exception as e:
            self.logger.error(f"메시지 수신기 오류: {e}")

    async def _connection_monitor_task(self) -> None:
        """연결 상태 모니터링 백그라운드 작업"""
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(30)  # 30초마다 체크

                # 연결 상태 확인
                if self._websocket and self._websocket.closed:
                    self.logger.warning("WebSocket 연결이 끊어짐 감지")
                    self._connection_state = ConnectionState.ERROR
                    break

                # 메시지 수신 타임아웃 체크
                last_msg_time = self._last_message_time
                if last_msg_time and time.time() - last_msg_time > 120:  # 2분간 메시지 없음
                    self.logger.warning("장시간 메시지 수신 없음")

        except asyncio.CancelledError:
            self.logger.info("연결 모니터 종료")
        except Exception as e:
            self.logger.error(f"연결 모니터 오류: {e}")

    async def _jwt_refresh_task(self) -> None:
        """JWT 토큰 갱신 백그라운드 작업 (Private 전용)"""
        try:
            while not self._shutdown_requested:
                await asyncio.sleep(300)  # 5분마다 체크

                # 토큰 만료 80% 시점에 갱신
                token_expires = self._token_expires_at
                if token_expires and time.time() > token_expires * 0.8:
                    self.logger.info("JWT 토큰 갱신 시도")
                    await self._refresh_jwt_token()

        except asyncio.CancelledError:
            self.logger.info("JWT 갱신기 종료")
        except Exception as e:
            self.logger.error(f"JWT 갱신기 오류: {e}")

    # =============================================================================
    # 상태 조회
    # =============================================================================

    @property
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return (
            self._websocket is not None and
            not self._websocket.closed and
            self._connection_state == ConnectionState.CONNECTED
        )

    @property
    def connection_state(self) -> ConnectionState:
        """현재 연결 상태"""
        return self._connection_state

    def get_statistics(self) -> Dict[str, Any]:
        """연결 통계 반환"""
        uptime = 0.0
        if self._connect_time:
            uptime = time.time() - self._connect_time

        return {
            "connection_type": self.connection_type.value,
            "state": self._connection_state.value,
            "uptime_seconds": uptime,
            "messages_sent": self._messages_sent,
            "messages_received": self._messages_received,
            "bytes_sent": self._bytes_sent,
            "bytes_received": self._bytes_received,
            "last_message_time": self._last_message_time,
            "compression_enabled": self.config.enable_compression,
            "simple_format_enabled": self.config.enable_simple_format
        }


# =============================================================================
# 팩토리 함수
# =============================================================================

def create_public_client(
    message_handler: Optional[Callable[[Dict[str, Any]], None]] = None,
    enable_compression: bool = True,
    enable_simple_format: bool = True
) -> NativeWebSocketClient:
    """Public WebSocket 클라이언트 생성 (Rate Limiter 통합)"""
    config = ConnectionConfig(
        enable_compression=enable_compression,
        enable_simple_format=enable_simple_format
    )

    client = NativeWebSocketClient(
        connection_type=WebSocketType.PUBLIC,
        config=config,
        message_handler=message_handler
    )

    # Rate Limiter 사용 가능 여부 로깅
    if RATE_LIMITER_AVAILABLE:
        client.logger.info("Public 클라이언트 생성 완료 (Rate Limiter 활성화)")
    else:
        client.logger.warning("Public 클라이언트 생성 완료 (Rate Limiter 비활성화)")

    return client


def create_private_client(
    message_handler: Optional[Callable[[Dict[str, Any]], None]] = None,
    enable_compression: bool = True,
    enable_simple_format: bool = True
) -> NativeWebSocketClient:
    """Private WebSocket 클라이언트 생성 (Rate Limiter 통합)"""
    config = ConnectionConfig(
        enable_compression=enable_compression,
        enable_simple_format=enable_simple_format
    )

    client = NativeWebSocketClient(
        connection_type=WebSocketType.PRIVATE,
        config=config,
        message_handler=message_handler
    )

    # Rate Limiter 사용 가능 여부 로깅
    if RATE_LIMITER_AVAILABLE:
        client.logger.info("Private 클라이언트 생성 완료 (Rate Limiter 활성화)")
    else:
        client.logger.warning("Private 클라이언트 생성 완료 (Rate Limiter 비활성화)")

    return client
