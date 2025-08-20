"""
데이터 응답 모델 정의

이 모듈은 Smart Router에서 반환하는 응답 모델들을 정의합니다.
모든 응답은 표준화된 형태로 반환되어 거래소별 차이를 추상화합니다.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from .symbols import TradingSymbol
from .timeframes import Timeframe


@dataclass(frozen=True)
class CandleData:
    """개별 캔들 데이터"""

    timestamp: datetime                  # 캔들 시작 시간
    open: Decimal                       # 시가
    high: Decimal                       # 고가
    low: Decimal                        # 저가
    close: Decimal                      # 종가
    volume: Decimal                     # 거래량
    quote_volume: Optional[Decimal] = None  # 견적 통화 거래량

    @property
    def ohlc(self) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """OHLC 튜플 반환"""
        return (self.open, self.high, self.low, self.close)

    @property
    def price_change(self) -> Decimal:
        """가격 변화 (종가 - 시가)"""
        return self.close - self.open

    @property
    def price_change_rate(self) -> Decimal:
        """가격 변화율"""
        if self.open == 0:
            return Decimal('0')
        return (self.close - self.open) / self.open


@dataclass(frozen=True)
class CandleDataResponse:
    """캔들 데이터 응답"""

    symbol: TradingSymbol
    timeframe: Timeframe
    data: List[CandleData]
    request_timestamp: datetime
    response_timestamp: datetime
    source: str = "rest"                # 데이터 소스 ("rest" or "websocket")

    @property
    def count(self) -> int:
        """응답 캔들 개수"""
        return len(self.data)

    @property
    def response_time_ms(self) -> int:
        """응답 시간 (밀리초)"""
        delta = self.response_timestamp - self.request_timestamp
        return int(delta.total_seconds() * 1000)

    @property
    def latest_candle(self) -> Optional[CandleData]:
        """최신 캔들"""
        return self.data[0] if self.data else None

    @property
    def oldest_candle(self) -> Optional[CandleData]:
        """가장 오래된 캔들"""
        return self.data[-1] if self.data else None


@dataclass(frozen=True)
class TickerData:
    """티커 데이터"""

    symbol: TradingSymbol
    price: Decimal                      # 현재가
    change: Decimal                     # 전일 대비 변화량
    change_rate: Decimal                # 전일 대비 변화율
    volume_24h: Decimal                 # 24시간 거래량
    quote_volume_24h: Optional[Decimal] = None  # 24시간 견적 통화 거래량
    high_24h: Optional[Decimal] = None  # 24시간 고가
    low_24h: Optional[Decimal] = None   # 24시간 저가
    timestamp: Optional[datetime] = None

    @property
    def is_positive_change(self) -> bool:
        """상승인지 확인"""
        return self.change > 0

    @property
    def is_negative_change(self) -> bool:
        """하락인지 확인"""
        return self.change < 0


@dataclass(frozen=True)
class TickerDataResponse:
    """티커 데이터 응답"""

    data: TickerData
    request_timestamp: datetime
    response_timestamp: datetime
    source: str = "rest"

    @property
    def response_time_ms(self) -> int:
        """응답 시간 (밀리초)"""
        delta = self.response_timestamp - self.request_timestamp
        return int(delta.total_seconds() * 1000)


@dataclass(frozen=True)
class OrderbookEntry:
    """호가 엔트리"""

    price: Decimal                      # 가격
    size: Decimal                       # 수량

    @property
    def total_value(self) -> Decimal:
        """총 가치 (가격 × 수량)"""
        return self.price * self.size


@dataclass(frozen=True)
class OrderbookData:
    """호가 데이터"""

    symbol: TradingSymbol
    bids: List[OrderbookEntry]          # 매수 호가 (높은 가격순)
    asks: List[OrderbookEntry]          # 매도 호가 (낮은 가격순)
    timestamp: datetime

    @property
    def best_bid(self) -> Optional[OrderbookEntry]:
        """최고 매수 호가"""
        return self.bids[0] if self.bids else None

    @property
    def best_ask(self) -> Optional[OrderbookEntry]:
        """최저 매도 호가"""
        return self.asks[0] if self.asks else None

    @property
    def spread(self) -> Optional[Decimal]:
        """스프레드 (매도가 - 매수가)"""
        if self.best_bid and self.best_ask:
            return self.best_ask.price - self.best_bid.price
        return None

    @property
    def spread_rate(self) -> Optional[Decimal]:
        """스프레드 비율"""
        if self.best_bid and self.spread:
            return self.spread / self.best_bid.price
        return None

    @property
    def total_bid_volume(self) -> Decimal:
        """총 매수 물량"""
        return sum((entry.size for entry in self.bids), Decimal('0'))

    @property
    def total_ask_volume(self) -> Decimal:
        """총 매도 물량"""
        return sum((entry.size for entry in self.asks), Decimal('0'))


@dataclass(frozen=True)
class OrderbookDataResponse:
    """호가 데이터 응답"""

    data: OrderbookData
    request_timestamp: datetime
    response_timestamp: datetime
    source: str = "rest"

    @property
    def response_time_ms(self) -> int:
        """응답 시간 (밀리초)"""
        delta = self.response_timestamp - self.request_timestamp
        return int(delta.total_seconds() * 1000)


@dataclass(frozen=True)
class TradeData:
    """거래 데이터"""

    timestamp: datetime
    price: Decimal                      # 체결 가격
    size: Decimal                       # 체결 수량
    side: str                          # 체결 방향 ("buy" or "sell")
    trade_id: Optional[str] = None     # 거래 ID

    @property
    def total_value(self) -> Decimal:
        """체결 금액"""
        return self.price * self.size

    @property
    def is_buy_side(self) -> bool:
        """매수 체결인지 확인"""
        return self.side.lower() == "buy"

    @property
    def is_sell_side(self) -> bool:
        """매도 체결인지 확인"""
        return self.side.lower() == "sell"


@dataclass(frozen=True)
class TradeHistoryResponse:
    """거래 내역 응답"""

    symbol: TradingSymbol
    trades: List[TradeData]
    request_timestamp: datetime
    response_timestamp: datetime
    next_cursor: Optional[str] = None   # 다음 페이지 커서
    source: str = "rest"

    @property
    def count(self) -> int:
        """거래 개수"""
        return len(self.trades)

    @property
    def response_time_ms(self) -> int:
        """응답 시간 (밀리초)"""
        delta = self.response_timestamp - self.request_timestamp
        return int(delta.total_seconds() * 1000)

    @property
    def total_volume(self) -> Decimal:
        """총 거래량"""
        return sum((trade.size for trade in self.trades), Decimal('0'))

    @property
    def total_value(self) -> Decimal:
        """총 거래금액"""
        return sum((trade.total_value for trade in self.trades), Decimal('0'))


@dataclass(frozen=True)
class MarketListResponse:
    """마켓 목록 응답"""

    markets: List[TradingSymbol]
    request_timestamp: datetime
    response_timestamp: datetime
    total_count: int

    @property
    def response_time_ms(self) -> int:
        """응답 시간 (밀리초)"""
        delta = self.response_timestamp - self.request_timestamp
        return int(delta.total_seconds() * 1000)

    def filter_by_quote_currency(self, quote_currency: str) -> List[TradingSymbol]:
        """견적 통화별 필터링"""
        return [
            market for market in self.markets
            if market.quote_currency.upper() == quote_currency.upper()
        ]


@dataclass(frozen=True)
class MarketStatusResponse:
    """마켓 상태 응답"""

    market_open: bool                   # 시장 개장 여부
    trading_enabled: bool               # 거래 가능 여부
    maintenance_mode: bool              # 점검 모드 여부
    server_time: datetime               # 서버 시간
    message: Optional[str] = None       # 상태 메시지
    next_maintenance: Optional[datetime] = None  # 다음 점검 시간

    @property
    def is_trading_available(self) -> bool:
        """거래 가능 여부"""
        return self.market_open and self.trading_enabled and not self.maintenance_mode


@dataclass(frozen=True)
class RealtimeDataResponse:
    """실시간 데이터 응답"""

    symbol: TradingSymbol
    data_type: str                      # "ticker", "orderbook", "trade"
    data: Dict[str, Any]               # 실시간 데이터
    timestamp: datetime

    @property
    def is_ticker_data(self) -> bool:
        """티커 데이터인지 확인"""
        return self.data_type == "ticker"

    @property
    def is_orderbook_data(self) -> bool:
        """호가 데이터인지 확인"""
        return self.data_type == "orderbook"

    @property
    def is_trade_data(self) -> bool:
        """거래 데이터인지 확인"""
        return self.data_type == "trade"


# 기존 인터페이스 호환용 타입 별칭
TickerResponse = TickerDataResponse
OrderbookResponse = OrderbookDataResponse


@dataclass(frozen=True)
class RealtimeSubscriptionResponse:
    """실시간 구독 응답"""

    subscription_id: str
    symbol: TradingSymbol
    data_types: List[str]
    status: str                         # "active", "inactive", "error"
    message: Optional[str] = None       # 상태 메시지

    @property
    def is_active(self) -> bool:
        """구독이 활성화되어 있는지 확인"""
        return self.status == "active"


@dataclass(frozen=True)
class ErrorResponse:
    """오류 응답"""

    error_code: str
    error_message: str
    timestamp: datetime
    request_info: Optional[Dict[str, Any]] = None

    @property
    def is_rate_limit_error(self) -> bool:
        """레이트 제한 오류인지 확인"""
        return "rate" in self.error_code.lower() or "limit" in self.error_code.lower()

    @property
    def is_network_error(self) -> bool:
        """네트워크 오류인지 확인"""
        return "network" in self.error_code.lower() or "timeout" in self.error_code.lower()


# 편의 함수들
def create_candle_response(
    symbol: TradingSymbol,
    timeframe: Timeframe,
    raw_data: List[Dict[str, Any]],
    source: str = "rest"
) -> CandleDataResponse:
    """원시 데이터로부터 캔들 응답 생성"""
    candles = []
    for item in raw_data:
        candle = CandleData(
            timestamp=datetime.fromisoformat(item['timestamp']),
            open=Decimal(str(item['open'])),
            high=Decimal(str(item['high'])),
            low=Decimal(str(item['low'])),
            close=Decimal(str(item['close'])),
            volume=Decimal(str(item['volume'])),
            quote_volume=Decimal(str(item.get('quote_volume', 0)))
        )
        candles.append(candle)

    now = datetime.now()
    return CandleDataResponse(
        symbol=symbol,
        timeframe=timeframe,
        data=candles,
        request_timestamp=now,
        response_timestamp=now,
        source=source
    )
