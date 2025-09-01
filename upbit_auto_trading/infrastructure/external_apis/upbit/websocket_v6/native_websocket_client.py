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
from dataclasses import dataclass

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None

from upbit_auto_trading.infrastructure.logging import create_component_logger

# v6 타입 import
from .types import WebSocketType, ConnectionState
from .exceptions import ConnectionError
from .simple_format_converter import (
    convert_simple_to_default,
    convert_default_to_simple
)


@dataclass
class ConnectionConfig:
    """WebSocket 연결 설정"""
    url: str
    enable_compression: bool = True
    enable_simple_format: bool = True
    connect_timeout: float = 10.0
    heartbeat_interval: float = 30.0
    max_message_size: int = 1024 * 1024  # 1MB


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
        self._websocket: Optional[WebSocketClientProtocol] = None
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

    async def connect(self) -> bool:
        """WebSocket 연결"""
        try:
            if not WEBSOCKETS_AVAILABLE:
                raise ConnectionError("websockets 라이브러리가 설치되지 않음")

            self.logger.info(f"{self.connection_type.value} WebSocket 연결 시작")
            self._connection_state = ConnectionState.CONNECTING

            # 연결 옵션 설정
            extra_headers = {}

            # Private 연결의 경우 JWT 토큰 추가
            if self.connection_type == WebSocketType.PRIVATE:
                if not self._jwt_token:
                    await self._refresh_jwt_token()
                if self._jwt_token:
                    extra_headers["Authorization"] = f"Bearer {self._jwt_token}"

            # WebSocket 연결
            self._websocket = await websockets.connect(
                self.config.url,
                extra_headers=extra_headers,
                compression="deflate" if self.config.enable_compression else None,
                max_size=self.config.max_message_size,
                timeout=self.config.connect_timeout,
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
                        except:
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
                if (self._last_message_time and
                    time.time() - self._last_message_time > 120):  # 2분간 메시지 없음
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
                if (self._token_expires_at and
                    time.time() > self._token_expires_at * 0.8):
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
    """Public WebSocket 클라이언트 생성"""
    config = ConnectionConfig(
        url="wss://api.upbit.com/websocket/v1",
        enable_compression=enable_compression,
        enable_simple_format=enable_simple_format
    )

    return NativeWebSocketClient(
        connection_type=WebSocketType.PUBLIC,
        config=config,
        message_handler=message_handler
    )


def create_private_client(
    message_handler: Optional[Callable[[Dict[str, Any]], None]] = None,
    enable_compression: bool = True,
    enable_simple_format: bool = True
) -> NativeWebSocketClient:
    """Private WebSocket 클라이언트 생성"""
    config = ConnectionConfig(
        url="wss://api.upbit.com/websocket/v1",
        enable_compression=enable_compression,
        enable_simple_format=enable_simple_format
    )

    return NativeWebSocketClient(
        connection_type=WebSocketType.PRIVATE,
        config=config,
        message_handler=message_handler
    )
