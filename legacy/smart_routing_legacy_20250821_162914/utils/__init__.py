"""
Smart Routing Utils

유틸리티 모듈들을 제공합니다.
"""

from .exceptions import (
    SmartRoutingException,
    DataRouterException,
    DataProviderException,
    InvalidRequestException,
    DataRangeExceedsLimitException,
    SymbolNotSupportedException,
    TimeframeNotSupportedException,
    ApiRateLimitException,
    WebSocketConnectionException,
    WebSocketDataException,
    RestApiException,
    DataValidationException,
    ChannelSelectionException,
    DataTransformationException,
    TimeoutException,
    ErrorConverter
)

__all__ = [
    # 기본 예외
    "SmartRoutingException",
    "DataRouterException",
    "DataProviderException",

    # 요청 관련 예외
    "InvalidRequestException",
    "DataRangeExceedsLimitException",
    "SymbolNotSupportedException",
    "TimeframeNotSupportedException",

    # API 관련 예외
    "ApiRateLimitException",
    "WebSocketConnectionException",
    "WebSocketDataException",
    "RestApiException",
    "TimeoutException",

    # 데이터 관련 예외
    "DataValidationException",
    "ChannelSelectionException",
    "DataTransformationException",

    # 유틸리티
    "ErrorConverter"
]
