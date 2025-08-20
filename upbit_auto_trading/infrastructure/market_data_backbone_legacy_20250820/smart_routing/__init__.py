"""
Smart Routing 시스템 - 완전 추상화된 데이터 라우터

이 패키지는 거래소 독립적인 데이터 라우팅 시스템을 제공합니다.
내부 시스템은 업비트 API 구조를 알 필요 없이 도메인 모델만으로
모든 데이터 요청을 처리할 수 있습니다.

주요 구성요소:
- models: 도메인 모델 (TradingSymbol, Timeframe, Request/Response)
- interfaces: 추상 인터페이스 (IDataRouter, IDataProvider)
- implementations: 구현체 (SmartDataRouter, UpbitDataProvider)
- strategies: 라우팅 전략 (ChannelSelector, Optimization)
- utils: 유틸리티 (FieldMapper, RateLimiter, SubscriptionManager)
"""

from .models import (
    TradingSymbol,
    Timeframe,
    CandleDataRequest,
    TickerDataRequest,
    OrderbookDataRequest,
    TradeHistoryRequest,
    RealtimeSubscriptionRequest,
    RealtimeDataType,
    DataRequestPriority,
    create_candle_request,
    create_ticker_request,
    create_realtime_request
)

from .interfaces import (
    IDataRouter,
    IDataProvider
)

# 구현체는 implementations 패키지에서 import
# from .implementations import SmartDataRouter, UpbitDataProvider

__version__ = "2.0.0"

__all__ = [
    # Domain Models
    "TradingSymbol",
    "Timeframe",

    # Request Models
    "CandleDataRequest",
    "TickerDataRequest",
    "OrderbookDataRequest",
    "TradeHistoryRequest",
    "RealtimeSubscriptionRequest",

    # Enums
    "RealtimeDataType",
    "DataRequestPriority",

    # Convenience Functions
    "create_candle_request",
    "create_ticker_request",
    "create_realtime_request",

    # Core Interfaces
    "IDataRouter",
    "IDataProvider",

    # Main Implementation (추후 추가)
    # "SmartDataRouter",
    # "create_smart_data_router",
]


def get_version() -> str:
    """패키지 버전 반환"""
    return __version__


def get_supported_exchanges() -> list[str]:
    """지원하는 거래소 목록"""
    return ["upbit"]  # 추후 확장: ["upbit", "binance", "coinbase"]


def create_symbol(symbol_str: str, exchange: str = "upbit") -> TradingSymbol:
    """편의 함수: 문자열로부터 심볼 생성"""
    if exchange == "upbit":
        return TradingSymbol.from_upbit_format(symbol_str)
    else:
        raise ValueError(f"지원되지 않는 거래소: {exchange}")


def create_timeframe(timeframe_str: str) -> Timeframe:
    """편의 함수: 문자열로부터 타임프레임 생성"""
    from .models import parse_timeframe
    return parse_timeframe(timeframe_str)
