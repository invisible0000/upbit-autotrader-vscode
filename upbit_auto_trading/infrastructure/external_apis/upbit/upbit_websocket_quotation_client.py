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
from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import RateLimitConfig, RateLimiter


class WebSocketDataType(Enum):
    """WebSocket 데이터 타입 (공개 API 전용)"""
    TICKER = "ticker"
    TRADE = "trade"
    ORDERBOOK = "orderbook"
    CANDLE = "candle"  # 모든 캔들 타입 통합


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

        # 🆕 통합 Rate Limiter 적용
        self.rate_limiter = RateLimiter(RateLimitConfig.upbit_websocket_connect())

        # 재연결 설정
        self.auto_reconnect = True
        self.reconnect_delay = 5.0
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0

        # 메시지 처리 설정
        self.ping_interval = 30.0  # 30초마다 PING
        self.message_timeout = 10.0  # 메시지 타임아웃 10초

        # 🔧 메시지 수신 루프 제어 (단일 수신 아키텍처)
        self.message_loop_task: Optional[asyncio.Task] = None
        self.auto_start_message_loop = True  # 구독 시 자동으로 메시지 수신 시작
        self._message_loop_running = False  # 중복 실행 방지

        # 🆕 외부 제너레이터 요청 지원 (큐 기반)
        self._external_listeners: List[asyncio.Queue] = []  # 외부에서 listen() 호출 시 사용할 큐들
        self._enable_external_listen = False  # listen() 제너레이터 활성화 여부

        # 🔧 백그라운드 태스크 추적
        self._background_tasks: set = set()  # 백그라운드 태스크 추적

    async def connect(self) -> bool:
        """WebSocket 연결 (API 키 불필요)"""
        try:
            # 🆕 Rate Limit 검사
            await self.rate_limiter.acquire()

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
            keep_alive_task = asyncio.create_task(self._keep_alive())
            self._background_tasks.add(keep_alive_task)
            keep_alive_task.add_done_callback(self._background_tasks.discard)

            return True

        except Exception as e:
            self.logger.error(f"❌ WebSocket 연결 실패: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """WebSocket 연결 해제 (모든 태스크 정리)"""
        try:
            self.auto_reconnect = False

            # 🔧 메시지 수신 루프 중지
            if self.message_loop_task and not self.message_loop_task.done():
                self.message_loop_task.cancel()
                try:
                    await self.message_loop_task
                except asyncio.CancelledError:
                    pass
                self.message_loop_task = None

            # 🔧 모든 백그라운드 태스크 정리
            if self._background_tasks:
                self.logger.debug(f"백그라운드 태스크 {len(self._background_tasks)}개 정리 중...")
                for task in list(self._background_tasks):
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                self._background_tasks.clear()
                self.logger.debug("백그라운드 태스크 정리 완료")

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
            self._message_loop_running = False

    async def subscribe_ticker(self, markets: List[str]) -> bool:
        """현재가 정보 구독 (스크리너 핵심)"""
        return await self._subscribe(WebSocketDataType.TICKER, markets)

    async def subscribe_trade(self, markets: List[str]) -> bool:
        """체결 정보 구독"""
        return await self._subscribe(WebSocketDataType.TRADE, markets)

    async def subscribe_orderbook(self, markets: List[str]) -> bool:
        """호가 정보 구독"""
        return await self._subscribe(WebSocketDataType.ORDERBOOK, markets)

    async def subscribe_candle(self, markets: List[str], unit: int = 1) -> bool:
        """캔들 정보 구독 (단위는 smart_routing에서 처리)"""
        return await self._subscribe(WebSocketDataType.CANDLE, markets, unit)

    async def _subscribe(self, data_type: WebSocketDataType, markets: List[str], candle_unit: Optional[int] = None) -> bool:
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

            # 캔들 타입인 경우 단위 지정
            if data_type == WebSocketDataType.CANDLE and candle_unit:
                # 캔들 단위별 타입 지정 (업비트 공식 API 형식)
                candle_type_map = {
                    # 초봉
                    0: "candle.1s",      # 1초봉 (특별값 0으로 구분)
                    # 분봉 (분 단위 그대로 사용)
                    1: "candle.1m",      # 1분봉
                    3: "candle.3m",      # 3분봉
                    5: "candle.5m",      # 5분봉
                    10: "candle.10m",    # 10분봉
                    15: "candle.15m",    # 15분봉
                    30: "candle.30m",    # 30분봉
                    60: "candle.60m",    # 60분봉 (1시간)
                    240: "candle.240m"   # 240분봉 (4시간)
                }
                actual_type = candle_type_map.get(candle_unit, "candle.5m")
                subscribe_msg[1]["type"] = actual_type

            await self.websocket.send(json.dumps(subscribe_msg))

            # 🆕 Rate Limit 검사 (메시지 전송 시)
            await self.rate_limiter.acquire()

            # 구독 정보 저장 (중복 방지)
            if data_type.value not in self.subscriptions:
                self.subscriptions[data_type.value] = []

            # 중복 제거하면서 추가
            for market in markets:
                if market not in self.subscriptions[data_type.value]:
                    self.subscriptions[data_type.value].append(market)

            # 🔧 첫 구독 시 자동으로 메시지 수신 루프 시작
            if self.auto_start_message_loop and not self.message_loop_task and not self._message_loop_running:
                self.message_loop_task = asyncio.create_task(self._message_receiver_loop())
                self.logger.debug("🚀 메시지 수신 루프 자동 시작")

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
        """실시간 메시지 수신 제너레이터 (큐 기반으로 단일 수신 루프와 연동)"""
        if not self.is_connected or not self.websocket:
            raise RuntimeError("WebSocket이 연결되지 않음")

        # 외부 listen 모드 활성화
        self._enable_external_listen = True

        # 이 제너레이터 전용 큐 생성
        message_queue = asyncio.Queue()
        self._external_listeners.append(message_queue)

        # 메시지 루프가 없으면 시작
        if not self.message_loop_task and not self._message_loop_running:
            self.message_loop_task = asyncio.create_task(self._message_receiver_loop())
            self.logger.debug("🚀 메시지 수신 루프 시작 (listen() 요청)")

        try:
            while self.is_connected:
                try:
                    # 큐에서 메시지 대기 (타임아웃 적용)
                    message = await asyncio.wait_for(message_queue.get(), timeout=self.message_timeout)
                    yield message
                except asyncio.TimeoutError:
                    # 타임아웃은 정상적인 상황 (메시지가 없을 때)
                    continue
                except Exception as e:
                    self.logger.error(f"메시지 큐 처리 오류: {e}")
                    break
        finally:
            # 정리: 큐 제거
            if message_queue in self._external_listeners:
                self._external_listeners.remove(message_queue)

            if self.auto_reconnect:
                await self._attempt_reconnect()

    def _infer_message_type(self, data: Dict[str, Any]) -> Optional[WebSocketDataType]:
        """메시지 타입 추론 (단순화된 로직)"""
        # 에러 메시지 체크
        if 'error' in data:
            self.logger.warning(f"WebSocket 에러 수신: {data.get('error')}")
            return None

        # 상태 메시지 체크 (UP 메시지 등)
        if 'status' in data:
            self.logger.debug(f"상태 메시지: {data.get('status')}")
            return None

        # 업비트 공식 type 필드 직접 사용
        if 'type' in data:
            msg_type = data['type']

            # 캔들 타입들을 통합 처리
            if msg_type.startswith('candle.'):
                return WebSocketDataType.CANDLE

            # 기본 타입 매핑
            type_mapping = {
                'ticker': WebSocketDataType.TICKER,
                'trade': WebSocketDataType.TRADE,
                'orderbook': WebSocketDataType.ORDERBOOK
            }

            return type_mapping.get(msg_type)

        # 필드 기반 추론 (fallback)
        if 'trade_price' in data and 'change_rate' in data and 'signed_change_rate' in data:
            return WebSocketDataType.TICKER
        elif 'trade_price' in data and 'trade_volume' in data and 'ask_bid' in data:
            return WebSocketDataType.TRADE
        elif 'orderbook_units' in data:
            return WebSocketDataType.ORDERBOOK
        elif 'opening_price' in data and 'trade_price' in data and 'candle_date_time_utc' in data:
            return WebSocketDataType.CANDLE
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

    async def _message_receiver_loop(self) -> None:
        """🔧 단일 메시지 수신 루프 - 모든 WebSocket recv를 여기서 처리"""
        if self._message_loop_running:
            self.logger.debug("메시지 수신 루프 이미 실행 중")
            return

        if not self.is_connected or not self.websocket:
            self.logger.error("WebSocket이 연결되지 않음")
            return

        self._message_loop_running = True
        self.logger.debug("메시지 수신 루프 시작")

        try:
            # 🆕 단일 recv 루프로 모든 메시지 처리
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

                    # 1. 등록된 핸들러 실행
                    await self._handle_message(message)

                    # 2. 외부 listen() 제너레이터들에게 메시지 전달
                    if self._enable_external_listen and self._external_listeners:
                        for queue in self._external_listeners.copy():  # copy()로 안전한 순회
                            try:
                                queue.put_nowait(message)
                            except asyncio.QueueFull:
                                self.logger.warning("외부 listen 큐가 가득참")
                            except Exception as e:
                                self.logger.error(f"외부 listen 큐 오류: {e}")

                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패: {e}")
                except Exception as e:
                    self.logger.error(f"메시지 처리 오류: {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("WebSocket 연결이 닫혔습니다")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"메시지 수신 루프 오류: {e}")
        finally:
            self._message_loop_running = False
            self.message_loop_task = None
            self.logger.debug("메시지 수신 루프 종료")

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
