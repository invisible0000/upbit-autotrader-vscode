"""
Smart Routing 도메인 모델 패키지

거래소 독립적인 도메인 모델들을 제공합니다:
- TradingSymbol: 거래 심볼 추상화
- Timeframe: 타임프레임 표준화
- Request Models: 요청 모델들
- Response Models: 응답 모델들
"""

from .symbols import (
    TradingSymbol,
    SymbolValidator,
    create_krw_symbol,
    create_usdt_symbol,
    parse_symbol,
    POPULAR_KRW_SYMBOLS
)

from .timeframes import (
    Timeframe,
    TimeframeValidator,
    MINUTE_TIMEFRAMES,
    HOUR_TIMEFRAMES,
    DAY_TIMEFRAMES,
    UPBIT_SUPPORTED_TIMEFRAMES,
    parse_timeframe
)

from .requests import (
    RealtimeDataType,
    DataRequestPriority,
    CandleDataRequest,
    TickerDataRequest,
    OrderbookDataRequest,
    TradeHistoryRequest,
    RealtimeSubscriptionRequest,
    MarketListRequest,
    create_candle_request,
    create_realtime_request,
    create_ticker_request
)

from .responses import (
    CandleData,
    CandleDataResponse,
    TickerData,
    TickerDataResponse,
    OrderbookEntry,
    OrderbookData,
    OrderbookDataResponse,
    TradeData,
    TradeHistoryResponse,
    MarketListResponse,
    RealtimeSubscriptionResponse,
    ErrorResponse,
    create_candle_response
)

__all__ = [
    # Symbols
    "TradingSymbol",
    "SymbolValidator",
    "create_krw_symbol",
    "create_usdt_symbol",
    "parse_symbol",
    "POPULAR_KRW_SYMBOLS",

    # Timeframes
    "Timeframe",
    "TimeframeValidator",
    "MINUTE_TIMEFRAMES",
    "HOUR_TIMEFRAMES",
    "DAY_TIMEFRAMES",
    "UPBIT_SUPPORTED_TIMEFRAMES",
    "parse_timeframe",

    # Request Models
    "RealtimeDataType",
    "DataRequestPriority",
    "CandleDataRequest",
    "TickerDataRequest",
    "OrderbookDataRequest",
    "TradeHistoryRequest",
    "RealtimeSubscriptionRequest",
    "MarketListRequest",
    "create_candle_request",
    "create_realtime_request",
    "create_ticker_request",

    # Response Models
    "CandleData",
    "CandleDataResponse",
    "TickerData",
    "TickerDataResponse",
    "OrderbookEntry",
    "OrderbookData",
    "OrderbookDataResponse",
    "TradeData",
    "TradeHistoryResponse",
    "MarketListResponse",
    "RealtimeSubscriptionResponse",
    "ErrorResponse",
    "create_candle_response",
]
