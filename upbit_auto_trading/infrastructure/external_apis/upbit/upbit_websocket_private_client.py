"""
업비트 WebSocket Private 클라이언트
- API 키 필요한 개인 거래/계좌 정보 실시간 수신
- 실시간 매매 전략 최적화 설계
"""

import asyncio
import websockets
import json
import uuid
from typing import Dict, List, Optional, Callable, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator


class PrivateWebSocketDataType(Enum):
    """Private WebSocket 데이터 타입"""
    MY_ORDER = "myOrder"     # 내 주문/체결 정보
    MY_ASSET = "myAsset"     # 내 자산(잔고) 정보


@dataclass
class PrivateWebSocketMessage:
    """Private WebSocket 메시지 구조"""
    type: PrivateWebSocketDataType
    data: Dict[str, Any]
    timestamp: datetime
    raw_data: str


class UpbitWebSocketPrivateClient:
    """
    업비트 WebSocket Private 클라이언트 (API 키 필요)
    실시간 매매/자산 정보 수신
    """

    def __init__(self, access_key: str, secret_key: str):
        self.url = "wss://api.upbit.com/websocket/v1/private"
        self.auth = UpbitAuthenticator(access_key, secret_key)
        self.websocket: Optional[Any] = None
        self.is_connected = False
        self.subscriptions: Dict[str, List[str]] = {}  # type -> markets
        self.message_handlers: Dict[PrivateWebSocketDataType, List[Callable]] = {}
        self.logger = create_component_logger("UpbitWebSocketPrivate")

        # 연결 관리
        self.ping_interval = 30.0  # 30초마다 PING
        self.message_timeout = 60.0  # 60초 메시지 타임아웃
        self.auto_reconnect = True
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0

    async def connect(self) -> bool:
        """WebSocket 연결 (API 키 인증 필요)"""
        try:
            self.logger.info(f"Private WebSocket 연결 시도: {self.url}")

            # JWT 토큰 생성
            jwt_token = self.auth.create_jwt_token()
            headers = {
                "Authorization": jwt_token  # 'Bearer ' 접두사는 create_jwt_token에서 이미 추가됨
            }

            self.websocket = await websockets.connect(
                self.url,
                additional_headers=headers,
                ping_interval=self.ping_interval,
                ping_timeout=self.message_timeout,
                close_timeout=10.0
            )

            self.is_connected = True
            self.reconnect_attempts = 0

            # PING 메시지로 연결 유지
            asyncio.create_task(self._keep_alive())

            self.logger.info("✅ Private WebSocket 연결 성공 (API 키 인증 완료)")
            return True

        except Exception as e:
            self.logger.error(f"❌ Private WebSocket 연결 실패: {e}")
            return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        self.is_connected = False
        self.auto_reconnect = False  # 자동 재연결 비활성화

        try:
            if self.websocket:
                try:
                    # WebSocket 상태 확인 후 정상적으로 닫기
                    if not self.websocket.closed:
                        await asyncio.wait_for(self.websocket.close(), timeout=3.0)
                except asyncio.TimeoutError:
                    self.logger.warning("WebSocket 닫기 타임아웃 - 강제 종료")
                except Exception as close_error:
                    self.logger.debug(f"WebSocket 닫기 중 오류: {close_error}")

                self.logger.info("Private WebSocket 연결 해제 완료")

        except Exception as e:
            self.logger.warning(f"연결 해제 중 오류: {e}")
        finally:
            self.websocket = None

            # 추가적인 정리 - 모든 백그라운드 태스크 정리
            try:
                # 현재 태스크를 제외한 모든 태스크 취소
                current_task = asyncio.current_task()
                all_tasks = [task for task in asyncio.all_tasks() if task != current_task and not task.done()]

                if all_tasks:
                    self.logger.debug(f"WebSocket 정리: {len(all_tasks)}개 태스크 취소 중...")
                    for task in all_tasks:
                        if not task.cancelled():
                            task.cancel()

                    # 짧은 시간 대기
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*all_tasks, return_exceptions=True),
                            timeout=1.0
                        )
                    except (asyncio.TimeoutError, Exception):
                        pass  # 타임아웃 무시

            except Exception as cleanup_error:
                self.logger.debug(f"추가 정리 중 오류 (무시됨): {cleanup_error}")

    async def subscribe_my_orders(self, markets: Optional[List[str]] = None) -> bool:
        """내 주문/체결 정보 구독"""
        return await self._subscribe("myOrder", markets)

    async def subscribe_my_assets(self) -> bool:
        """내 자산(잔고) 정보 구독"""
        return await self._subscribe("myAsset", None)

    async def _subscribe(self, data_type: str, markets: Optional[List[str]]) -> bool:
        """데이터 구독"""
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket이 연결되지 않음")
            return False

        try:
            # 구독 요청 메시지 구성
            ticket = str(uuid.uuid4())
            request_data: List[Dict[str, Any]] = [
                {"ticket": ticket}
            ]

            # 데이터 타입별 요청 구성
            if data_type == "myOrder":
                if markets:
                    request_data.append({"type": "myOrder", "codes": markets})
                else:
                    request_data.append({"type": "myOrder"})
            elif data_type == "myAsset":
                request_data.append({"type": "myAsset"})

            # 포맷 지정 (기본 포맷)
            request_data.append({"format": "DEFAULT"})

            # 구독 요청 전송
            message = json.dumps(request_data)
            await self.websocket.send(message)

            # 구독 목록 업데이트
            if data_type not in self.subscriptions:
                self.subscriptions[data_type] = []
            if markets:
                self.subscriptions[data_type].extend(markets)

            self.logger.info(f"✅ {data_type} 구독 완료: {markets}")
            return True

        except Exception as e:
            self.logger.error(f"❌ {data_type} 구독 실패: {e}")
            return False

    async def listen(self) -> AsyncGenerator[PrivateWebSocketMessage, None]:
        """메시지 스트림 수신"""
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket이 연결되지 않음")
            return

        try:
            async for raw_message in self.websocket:
                try:
                    # JSON 파싱
                    if isinstance(raw_message, bytes):
                        raw_message = raw_message.decode('utf-8')

                    data = json.loads(raw_message)

                    # 에러 응답 처리
                    if 'error' in data:
                        self.logger.error(f"WebSocket 에러: {data['error']}")
                        continue

                    # 메시지 타입 식별
                    message_type = self._identify_message_type(data)
                    if not message_type:
                        continue

                    # 메시지 객체 생성
                    message = PrivateWebSocketMessage(
                        type=message_type,
                        data=data,
                        timestamp=datetime.now(),
                        raw_data=raw_message
                    )

                    # 메시지 핸들러 호출
                    await self._call_handlers(message)

                    yield message

                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패: {e}")
                except Exception as e:
                    self.logger.error(f"메시지 처리 오류: {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket 연결이 종료됨")
            self.is_connected = False
            if self.auto_reconnect:
                await self._attempt_reconnect()
        except Exception as e:
            self.logger.error(f"메시지 수신 오류: {e}")
            self.is_connected = False

    def _identify_message_type(self, data: Dict[str, Any]) -> Optional[PrivateWebSocketDataType]:
        """메시지 타입 식별"""
        try:
            # 메시지 타입별 고유 필드로 식별
            if 'order_id' in data or 'trade_id' in data:
                return PrivateWebSocketDataType.MY_ORDER
            elif 'balance' in data or 'locked' in data:
                return PrivateWebSocketDataType.MY_ASSET

            self.logger.debug(f"알 수 없는 메시지 타입: {data}")
            return None

        except Exception as e:
            self.logger.error(f"메시지 타입 식별 실패: {e}")
            return None

    def add_handler(self, data_type: PrivateWebSocketDataType, handler: Callable) -> None:
        """메시지 핸들러 추가"""
        if data_type not in self.message_handlers:
            self.message_handlers[data_type] = []
        self.message_handlers[data_type].append(handler)

    async def _call_handlers(self, message: PrivateWebSocketMessage) -> None:
        """메시지 핸들러 호출"""
        handlers = self.message_handlers.get(message.type, [])
        for handler in handlers:
            try:
                await handler(message) if asyncio.iscoroutinefunction(handler) else handler(message)
            except Exception as e:
                self.logger.error(f"메시지 핸들러 실행 오류: {e}")

    async def _keep_alive(self) -> None:
        """연결 유지 (PING 메시지)"""
        while self.is_connected and self.websocket:
            try:
                await asyncio.sleep(self.ping_interval)
                if self.is_connected and self.websocket:
                    await self.websocket.ping()
            except Exception as e:
                self.logger.warning(f"PING 전송 실패: {e}")
                break

    async def _attempt_reconnect(self) -> bool:
        """자동 재연결 시도"""
        if not self.auto_reconnect or self.reconnect_attempts >= self.max_reconnect_attempts:
            return False

        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 30)  # 지수 백오프

        self.logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts} (대기: {wait_time}초)")

        await asyncio.sleep(wait_time)
        return await self.connect()

    async def __aenter__(self):
        """async context manager 진입"""
        if await self.connect():
            return self
        else:
            raise ConnectionError("Private WebSocket 연결 실패")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async context manager 종료"""
        await self.disconnect()
