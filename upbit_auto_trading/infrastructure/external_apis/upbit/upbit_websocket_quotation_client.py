"""
업비트 WebSocket Quotation 클라이언트
- API 키 불필요한 시세 데이터 실시간 수신
- 스크리너/백테스팅 최적화 설계
"""

import asyncio
import websockets
import json
import uuid
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


class WebSocketDataType(Enum):
    """WebSocket 데이터 타입"""
    TICKER = "ticker"
    TRADE = "trade"
    ORDERBOOK = "orderbook"
    CANDLE_1M = "candle.1"
    CANDLE_5M = "candle.5"
    CANDLE_15M = "candle.15"


@dataclass
class WebSocketMessage:
    """WebSocket 메시지 구조"""
    type: WebSocketDataType
    market: str
    data: Dict[str, Any]
    timestamp: datetime
    raw_data: str


class UpbitWebSocketQuotationClient:
    """
    업비트 WebSocket Quotation 클라이언트 (API 키 불필요)
    스크리너/백테스팅용 실시간 시세 데이터 수신
    """

    def __init__(self):
        self.url = "wss://api.upbit.com/websocket/v1"  # API 키 불필요
        self.websocket: Optional[Any] = None
        self.is_connected = False
        self.subscriptions: Dict[str, List[str]] = {}  # type -> markets
        self.message_handlers: Dict[WebSocketDataType, List[Callable]] = {}
        self.logger = create_component_logger("UpbitWebSocketQuotation")

        # 재연결 설정
        self.auto_reconnect = True
        self.reconnect_delay = 5.0
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0

        # 메시지 처리 설정
        self.ping_interval = 30.0  # 30초마다 PING
        self.message_timeout = 10.0  # 메시지 타임아웃 10초

    async def connect(self) -> bool:
        """WebSocket 연결 (API 키 불필요)"""
        try:
            self.logger.info(f"WebSocket 연결 시도: {self.url}")

            # 연결 설정 (인증 불필요)
            self.websocket = await websockets.connect(
                self.url,
                ping_interval=self.ping_interval,
                ping_timeout=self.message_timeout,
                compression=None  # 압축 비활성화로 성능 최적화
            )

            self.is_connected = True
            self.reconnect_attempts = 0
            self.logger.info("✅ WebSocket 연결 성공 (API 키 불필요)")

            # PING 메시지로 연결 유지
            asyncio.create_task(self._keep_alive())

            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 실패: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        try:
            self.auto_reconnect = False
            if self.websocket:
                try:
                    # WebSocket 상태 확인 후 닫기
                    if hasattr(self.websocket, 'close') and not getattr(self.websocket, 'closed', True):
                        await self.websocket.close()
                    self.logger.info("WebSocket 연결 해제 완료")
                except Exception as close_error:
                    self.logger.debug(f"WebSocket 닫기 중 오류 (무시됨): {close_error}")
        except Exception as e:
            self.logger.warning(f"WebSocket 연결 해제 중 오류: {e}")
        finally:
            self.is_connected = False
            self.websocket = None

    async def subscribe_ticker(self, markets: List[str]) -> bool:
        """현재가 정보 구독 (스크리너 핵심)"""
        return await self._subscribe(WebSocketDataType.TICKER, markets)

    async def subscribe_trade(self, markets: List[str]) -> bool:
        """체결 정보 구독"""
        return await self._subscribe(WebSocketDataType.TRADE, markets)

    async def subscribe_orderbook(self, markets: List[str]) -> bool:
        """호가 정보 구독"""
        return await self._subscribe(WebSocketDataType.ORDERBOOK, markets)

    async def subscribe_candle(self, markets: List[str], unit: int = 5) -> bool:
        """캔들 정보 구독 (백테스팅 핵심)"""
        candle_type_map = {
            1: WebSocketDataType.CANDLE_1M,
            5: WebSocketDataType.CANDLE_5M,
            15: WebSocketDataType.CANDLE_15M
        }

        if unit not in candle_type_map:
            self.logger.error(f"지원하지 않는 캔들 단위: {unit}분")
            return False

        return await self._subscribe(candle_type_map[unit], markets)

    async def _subscribe(self, data_type: WebSocketDataType, markets: List[str]) -> bool:
        """내부 구독 메서드"""
        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket이 연결되지 않음")
            return False

        try:
            # 고유 티켓 생성
            ticket = f"upbit-auto-trader-{uuid.uuid4().hex[:8]}"

            # 구독 메시지 구성
            subscribe_msg = [
                {"ticket": ticket},
                {"type": data_type.value, "codes": markets},
                {"format": "DEFAULT"}  # 압축하지 않은 기본 형식
            ]

            await self.websocket.send(json.dumps(subscribe_msg))

            # 구독 정보 저장
            if data_type.value not in self.subscriptions:
                self.subscriptions[data_type.value] = []
            self.subscriptions[data_type.value].extend(markets)

            self.logger.info(f"✅ {data_type.value} 구독 완료: {markets}")
            return True

        except Exception as e:
            self.logger.error(f"❌ {data_type.value} 구독 실패: {e}")
            return False

    def add_message_handler(self, data_type: WebSocketDataType, handler: Callable[[WebSocketMessage], None]) -> None:
        """메시지 핸들러 등록"""
        if data_type not in self.message_handlers:
            self.message_handlers[data_type] = []
        self.message_handlers[data_type].append(handler)
        self.logger.debug(f"메시지 핸들러 등록: {data_type.value}")

    async def listen(self) -> AsyncGenerator[WebSocketMessage, None]:
        """실시간 메시지 수신 제너레이터"""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("WebSocket이 연결되지 않음")

        try:
            async for raw_message in self.websocket:
                try:
                    # JSON 파싱
                    data = json.loads(raw_message)

                    # 메시지 타입 추론
                    message_type = self._infer_message_type(data)
                    if not message_type:
                        continue

                    # Market 정보 추출 (여러 필드에서 확인)
                    market = data.get('market') or data.get('code') or data.get('symbol', 'UNKNOWN')

                    # WebSocketMessage 객체 생성
                    message = WebSocketMessage(
                        type=message_type,
                        market=market,
                        data=data,
                        timestamp=datetime.now(),
                        raw_data=raw_message
                    )

                    # 등록된 핸들러 실행
                    await self._handle_message(message)

                    yield message

                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패: {e}")
                except Exception as e:
                    self.logger.error(f"메시지 처리 오류: {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket 연결이 닫혔습니다")
            self.is_connected = False

            if self.auto_reconnect:
                await self._attempt_reconnect()

    def _infer_message_type(self, data: Dict[str, Any]) -> Optional[WebSocketDataType]:
        """메시지 타입 추론 (개선된 로직)"""
        # 에러 메시지 체크
        if 'error' in data:
            self.logger.warning(f"WebSocket 에러 수신: {data.get('error')}")
            return None

        # 상태 메시지 체크 (UP 메시지 등)
        if 'status' in data:
            self.logger.debug(f"상태 메시지: {data.get('status')}")
            return None

        # 데이터 타입별 구분 (더 정확한 조건)
        if 'trade_price' in data and 'change_rate' in data and 'signed_change_rate' in data:
            return WebSocketDataType.TICKER
        elif 'trade_price' in data and 'trade_volume' in data and 'ask_bid' in data:
            return WebSocketDataType.TRADE
        elif 'orderbook_units' in data:
            return WebSocketDataType.ORDERBOOK
        elif 'opening_price' in data and 'closing_price' in data and 'high_price' in data:
            # 캔들 데이터 - 정확한 타입은 추가 로직 필요
            return WebSocketDataType.CANDLE_5M  # 기본값
        else:
            # 디버그를 위해 알 수 없는 타입의 필드들 로깅
            field_list = list(data.keys())[:10]  # 처음 10개 필드만
            self.logger.debug(f"알 수 없는 메시지 타입: {field_list}")
            return None

    async def _handle_message(self, message: WebSocketMessage) -> None:
        """메시지 핸들러 실행"""
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
        self.logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}")

        await asyncio.sleep(self.reconnect_delay)

        if await self.connect():
            # 기존 구독 복원
            for data_type, markets in self.subscriptions.items():
                await self._subscribe(WebSocketDataType(data_type), markets)
            return True

        return False

    async def __aenter__(self):
        """async with 컨텍스트 매니저 진입"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 컨텍스트 매니저 종료"""
        await self.disconnect()
