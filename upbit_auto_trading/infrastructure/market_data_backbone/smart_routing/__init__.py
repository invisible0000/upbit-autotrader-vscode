"""
Smart Routing - Layer 1: API 추상화

완전히 추상화된 마켓 데이터 라우팅 시스템입니다.
업비트 API 구조를 완전히 은닉하고 도메인 모델만 노출합니다.

주요 특징:
1. 자율적 채널 선택 (REST ↔ WebSocket 자동 전환)
2. API 제한 준수 (200개 초과 시 명시적 에러)
3. 완전한 도메인 모델 기반
4. 내부 빈도 분석으로 최적화
"""

# 도메인 모델
from .models import (
    TradingSymbol,
    Timeframe,
    CandleData,
    TickerData,
    OrderbookData,
    TradeData,
    CandleDataRequest,
    TickerDataRequest,
    OrderbookDataRequest,
    TradeDataRequest,
    CandleDataResponse,
    TickerDataResponse,
    OrderbookDataResponse,
    TradeDataResponse,
    RoutingStatsResponse,
    HealthCheckResponse
)

# 인터페이스
from .interfaces import (
    IDataRouter,
    IDataProvider
)

# 구현체
from .implementations import (
    UpbitRestProvider,
    SmartDataRouter,
    BasicChannelSelector,
    BasicFrequencyAnalyzer
)

# 예외
from .utils import (
    SmartRoutingException,
    DataRouterException,
    DataProviderException,
    InvalidRequestException,
    DataRangeExceedsLimitException,
    SymbolNotSupportedException,
    TimeframeNotSupportedException,
    ApiRateLimitException,
    WebSocketConnectionException,
    RestApiException,
    ErrorConverter
)

__all__ = [
    # 도메인 모델
    "TradingSymbol",
    "Timeframe",
    "CandleData",
    "TickerData",
    "OrderbookData",
    "TradeData",

    # 요청/응답 모델
    "CandleDataRequest",
    "TickerDataRequest",
    "OrderbookDataRequest",
    "TradeDataRequest",
    "CandleDataResponse",
    "TickerDataResponse",
    "OrderbookDataResponse",
    "TradeDataResponse",
    "RoutingStatsResponse",
    "HealthCheckResponse",

    # 인터페이스
    "IDataRouter",
    "IDataProvider",

    # 구현체
    "UpbitRestProvider",
    "SmartDataRouter",
    "BasicChannelSelector",
    "BasicFrequencyAnalyzer",

    # 예외
    "SmartRoutingException",
    "DataRouterException",
    "DataProviderException",
    "InvalidRequestException",
    "DataRangeExceedsLimitException",
    "SymbolNotSupportedException",
    "TimeframeNotSupportedException",
    "ApiRateLimitException",
    "WebSocketConnectionException",
    "RestApiException",
    "ErrorConverter"
]

# 버전 정보
__version__ = "1.0.0"
__author__ = "Smart Routing Team"
__description__ = "완전 추상화된 마켓 데이터 라우팅 시스템"
