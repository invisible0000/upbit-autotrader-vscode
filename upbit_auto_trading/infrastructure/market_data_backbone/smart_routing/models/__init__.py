"""
Smart Routing 도메인 모델

완전히 추상화된 도메인 모델들을 제공합니다.
업비트 API 구조와 완전히 독립적인 비즈니스 개념들입니다.
"""

from .symbols import TradingSymbol
from .timeframes import Timeframe
from .market_data_types import (
    CandleData,
    TickerData,
    OrderbookData,
    OrderbookLevel,
    TradeData
)
from .requests import (
    CandleDataRequest,
    TickerDataRequest,
    OrderbookDataRequest,
    TradeDataRequest,
    RequestFactory
)
from .responses import (
    CandleDataResponse,
    TickerDataResponse,
    OrderbookDataResponse,
    TradeDataResponse,
    RoutingStatsResponse,
    HealthCheckResponse,
    ResponseFactory
)

__all__ = [
    # 도메인 객체
    "TradingSymbol",
    "Timeframe",

    # 데이터 타입
    "CandleData",
    "TickerData",
    "OrderbookData",
    "OrderbookLevel",
    "TradeData",

    # 요청 모델
    "CandleDataRequest",
    "TickerDataRequest",
    "OrderbookDataRequest",
    "TradeDataRequest",
    "RequestFactory",

    # 응답 모델
    "CandleDataResponse",
    "TickerDataResponse",
    "OrderbookDataResponse",
    "TradeDataResponse",
    "RoutingStatsResponse",
    "HealthCheckResponse",
    "ResponseFactory"
]
