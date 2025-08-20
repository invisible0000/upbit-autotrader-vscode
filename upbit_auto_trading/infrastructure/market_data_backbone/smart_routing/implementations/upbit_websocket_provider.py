"""
업비트 WebSocket 데이터 제공자 (새 구현)

업비트 WebSocket API를 통해 실시간 데이터를 제공합니다.
Smart Router의 IDataProvider 인터페이스를 구현합니다.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..interfaces.data_provider import IDataProvider
from ..models import (
    TradingSymbol,
    CandleDataRequest,
    TickerDataRequest,
    OrderbookDataRequest,
    TradeDataRequest,
    CandleDataResponse,
    TickerDataResponse,
    OrderbookDataResponse,
    TradeDataResponse,
    TickerData,
    OrderbookData,
    OrderbookLevel,
    TradeData,
    ResponseFactory
)
from ..utils.exceptions import (
    WebSocketConnectionException,
    WebSocketDataException,
    SymbolNotSupportedException
)
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_websocket_quotation_client import (
    UpbitWebSocketQuotationClient,
    WebSocketDataType,
    WebSocketMessage
)


class UpbitWebSocketProvider(IDataProvider):
    """업비트 WebSocket 데이터 제공자

    실시간 데이터 조회에 특화된 WebSocket 기반 프로바이더
    """

    def __init__(self):
        self.client: Optional[UpbitWebSocketQuotationClient] = None
        self.logger = logging.getLogger(self.__class__.__name__)

        # 최신 데이터 캐시
        self.latest_data: Dict[str, Dict[str, Any]] = {}

        # 연결 상태
        self.is_connected = False

        # 구독 관리
        self.active_subscriptions: Dict[str, set] = {
            "ticker": set(),
            "orderbook": set(),
            "trade": set()
        }

    async def connect(self):
        """WebSocket 연결 수립"""
        if self.client is None:
            self.client = UpbitWebSocketQuotationClient()

            # 메시지 핸들러 등록
            self.client.add_message_handler(WebSocketDataType.TICKER, self._handle_ticker_message)
            self.client.add_message_handler(WebSocketDataType.ORDERBOOK, self._handle_orderbook_message)
            self.client.add_message_handler(WebSocketDataType.TRADE, self._handle_trade_message)

        try:
            await self.client.connect()
            self.is_connected = True
            self.logger.info("WebSocket 연결 성공")

            # 메시지 리스너 시작 (백그라운드 태스크)
            asyncio.create_task(self._message_listener())

        except Exception as e:
            self.is_connected = False
            raise WebSocketConnectionException(f"WebSocket 연결 실패: {e}")

    async def _message_listener(self):
        """WebSocket 메시지 수신 리스너"""
        try:
            async for message in self.client.listen():
                # 메시지는 이미 핸들러에서 처리되므로 여기서는 별도 작업 불필요
                pass
        except Exception as e:
            self.logger.error(f"WebSocket 메시지 리스너 오류: {e}")
            self.is_connected = False

    async def disconnect(self):
        """WebSocket 연결 해제"""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            self.logger.info("WebSocket 연결 해제")

    def _handle_websocket_data(self, data: Dict[str, Any]):
        """WebSocket 데이터 수신 핸들러"""
        try:
            # 심볼 추출
            symbol_code = data.get('code', data.get('cd'))
            if symbol_code:
                self.latest_data[symbol_code] = data
                self.logger.debug(f"WebSocket 데이터 수신: {symbol_code}")
        except Exception as e:
            self.logger.error(f"WebSocket 데이터 처리 오류: {e}")

    def _handle_ticker_message(self, message: WebSocketMessage):
        """Ticker 메시지 핸들러"""
        try:
            # 업비트 형식으로 캐시 저장 (KRW-BTC)
            self.latest_data[message.market] = message.data
            self.logger.debug(f"Ticker 데이터 수신: {message.market}")
        except Exception as e:
            self.logger.error(f"Ticker 메시지 처리 오류: {e}")

    def _handle_orderbook_message(self, message: WebSocketMessage):
        """Orderbook 메시지 핸들러"""
        try:
            # 업비트 형식으로 캐시 저장 (KRW-BTC)
            self.latest_data[message.market] = message.data
            self.logger.debug(f"Orderbook 데이터 수신: {message.market}")
        except Exception as e:
            self.logger.error(f"Orderbook 메시지 처리 오류: {e}")

    def _handle_trade_message(self, message: WebSocketMessage):
        """Trade 메시지 핸들러"""
        try:
            # 업비트 형식으로 캐시 저장 (KRW-BTC)
            self.latest_data[message.market] = message.data
            self.logger.debug(f"Trade 데이터 수신: {message.market}")
        except Exception as e:
            self.logger.error(f"Trade 메시지 처리 오류: {e}")

    def get_provider_info(self) -> Dict[str, str]:
        """Provider 정보 반환"""
        return {
            "name": "upbit_websocket",
            "description": "업비트 WebSocket 실시간 데이터 제공자",
            "version": "1.0.0",
            "data_source": "websocket"
        }

    def get_supported_capabilities(self) -> List[str]:
        """지원되는 기능 목록 반환"""
        return ["ticker", "orderbook", "trade"]

    async def _ensure_connected(self):
        """연결 상태 확인 및 연결"""
        if not self.is_connected or not self.client:
            await self.connect()

    async def _subscribe_to_symbol(self, symbol: TradingSymbol, data_type: WebSocketDataType):
        """필요시 구독 설정"""
        await self._ensure_connected()

        symbol_code = symbol.to_upbit_symbol()

        # 이미 구독된 데이터가 있는지 확인
        if symbol_code in self.latest_data:
            return

        # 데이터 타입별 구독 설정
        try:
            if data_type == WebSocketDataType.TICKER:
                success = await self.client.subscribe_ticker([symbol_code])
            elif data_type == WebSocketDataType.TRADE:
                success = await self.client.subscribe_trade([symbol_code])
            elif data_type == WebSocketDataType.ORDERBOOK:
                success = await self.client.subscribe_orderbook([symbol_code])
            else:
                raise WebSocketDataException(f"지원하지 않는 데이터 타입: {data_type}")

            if not success:
                raise WebSocketConnectionException(f"구독 실패: {symbol_code}")

            self.logger.info(f"WebSocket 구독 시작: {symbol_code} ({data_type.value})")

        except Exception as e:
            raise WebSocketConnectionException(f"구독 설정 실패: {e}")

    async def _wait_for_data(self, symbol: TradingSymbol, timeout: float = 5.0) -> Dict[str, Any]:
        """데이터 수신 대기"""
        symbol_code = symbol.to_upbit_symbol()

        # 이미 캐시된 데이터가 있으면 반환
        if symbol_code in self.latest_data:
            return self.latest_data[symbol_code]

        # 데이터 수신 대기
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            if symbol_code in self.latest_data:
                return self.latest_data[symbol_code]
            await asyncio.sleep(0.1)

        raise WebSocketDataException(f"WebSocket 데이터 수신 타임아웃: {symbol_code}")

    # IDataProvider 인터페이스 구현

    async def get_candle_data(self, request: CandleDataRequest) -> CandleDataResponse:
        """캔들 데이터 조회 (WebSocket으로는 제한적)"""
        # WebSocket은 실시간 데이터에 특화되어 있어 과거 캔들 데이터는 제한적
        raise NotImplementedError("WebSocket 프로바이더는 캔들 데이터를 지원하지 않습니다. REST API를 사용하세요.")

    async def get_ticker_data(self, request: TickerDataRequest) -> TickerDataResponse:
        """티커 데이터 조회"""
        try:
            # 티커 데이터 구독
            await self._subscribe_to_symbol(request.symbol, WebSocketDataType.TICKER)

            # 데이터 수신 대기
            raw_data = await self._wait_for_data(request.symbol)

            # 도메인 모델로 변환 (Decimal 형변환 포함)
            from decimal import Decimal

            ticker_data = TickerData(
                timestamp=datetime.now(),
                current_price=Decimal(str(raw_data.get('trade_price', 0))),
                change_rate=Decimal(str(raw_data.get('signed_change_rate', 0.0))),
                change_amount=Decimal(str(raw_data.get('signed_change_price', 0))),
                volume_24h=Decimal(str(raw_data.get('acc_trade_volume_24h', 0.0))),
                high_24h=Decimal(str(raw_data.get('high_price', 0))),
                low_24h=Decimal(str(raw_data.get('low_price', 0))),
                opening_price=Decimal(str(raw_data.get('opening_price', 0)))
            )

            return TickerDataResponse(
                symbol=request.symbol,
                data=ticker_data,
                metadata=ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="websocket"
                )
            )

        except Exception as e:
            self.logger.error(f"WebSocket 티커 데이터 조회 실패: {e}")
            raise WebSocketDataException(f"티커 데이터 조회 실패: {e}")

    async def get_orderbook_data(self, request: OrderbookDataRequest) -> OrderbookDataResponse:
        """호가창 데이터 조회"""
        try:
            # 호가창 데이터 구독
            await self._subscribe_to_symbol(request.symbol, WebSocketDataType.ORDERBOOK)

            # 데이터 수신 대기
            raw_data = await self._wait_for_data(request.symbol)

            # 간단한 호가창 데이터 변환 (업비트 WebSocket 구조에 맞게 조정)
            from decimal import Decimal

            # 실제 구현에서는 raw_data의 orderbook_units 필드를 파싱해야 함
            orderbook_data = OrderbookData(
                timestamp=datetime.now(),
                bids=[],  # 실제: raw_data.get('orderbook_units', [])에서 bid 추출 필요
                asks=[]   # 실제: raw_data.get('orderbook_units', [])에서 ask 추출 필요
            )

            return OrderbookDataResponse(
                symbol=request.symbol,
                data=orderbook_data,
                metadata=ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="websocket"
                )
            )

        except Exception as e:
            self.logger.error(f"WebSocket 호가창 데이터 조회 실패: {e}")
            raise WebSocketDataException(f"호가창 데이터 조회 실패: {e}")

    async def get_trade_data(self, request: TradeDataRequest) -> TradeDataResponse:
        """체결 데이터 조회"""
        try:
            # 체결 데이터 구독
            await self._subscribe_to_symbol(request.symbol, WebSocketDataType.TRADE)

            # 데이터 수신 대기
            raw_data = await self._wait_for_data(request.symbol)

            # 체결 데이터 변환
            from decimal import Decimal

            trade_data = TradeData(
                timestamp=datetime.now(),
                price=Decimal(str(raw_data.get('trade_price', 0))),
                size=Decimal(str(raw_data.get('trade_volume', 0.0))),
                side=raw_data.get('ask_bid', 'BID').lower()
            )

            return TradeDataResponse(
                symbol=request.symbol,
                data=[trade_data],  # 리스트로 래핑
                metadata=ResponseFactory.create_metadata(
                    request_time=datetime.now(),
                    data_source="websocket"
                )
            )

        except Exception as e:
            self.logger.error(f"WebSocket 체결 데이터 조회 실패: {e}")
            raise WebSocketDataException(f"체결 데이터 조회 실패: {e}")

    async def get_market_list(self) -> List[TradingSymbol]:
        """마켓 목록 조회 (WebSocket으로는 불가능)"""
        raise NotImplementedError("WebSocket 프로바이더는 마켓 목록 조회를 지원하지 않습니다. REST API를 사용하세요.")

    async def health_check(self) -> Dict[str, Any]:
        """상태 확인"""
        return {
            "status": "healthy" if self.is_connected else "disconnected",
            "provider_type": "websocket",
            "connected": self.is_connected,
            "cached_symbols": len(self.latest_data),
            "last_check": datetime.now().isoformat()
        }
