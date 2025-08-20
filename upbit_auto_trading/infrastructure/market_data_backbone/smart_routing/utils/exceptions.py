"""
Smart Routing 예외 처리 체계

완전 추상화된 Smart Routing에서 발생하는 예외들을 정의합니다.
업비트 API 에러를 도메인 레벨 에러로 변환합니다.
"""

from typing import Optional, Dict, Any


class SmartRoutingException(Exception):
    """Smart Routing 기본 예외 클래스"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DataRouterException(SmartRoutingException):
    """데이터 라우터 예외"""
    pass


class DataProviderException(SmartRoutingException):
    """데이터 제공자 예외"""
    pass


class InvalidRequestException(SmartRoutingException):
    """잘못된 요청 예외"""

    def __init__(self, message: str, request_params: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_REQUEST",
            details={"request_params": request_params}
        )


class DataRangeExceedsLimitException(SmartRoutingException):
    """데이터 범위 제한 초과 예외

    업비트 API 제한(200개)을 초과하는 요청 시 발생
    Coordinator에서 분할 처리해야 함을 알림
    """

    def __init__(
        self,
        message: str,
        requested_count: Optional[int] = None,
        max_limit: int = 200
    ):
        super().__init__(
            message=message,
            error_code="DATA_RANGE_EXCEEDS_LIMIT",
            details={
                "requested_count": requested_count,
                "max_limit": max_limit,
                "suggestion": "Coordinator에서 분할 요청을 사용하세요"
            }
        )


class SymbolNotSupportedException(SmartRoutingException):
    """지원하지 않는 심볼 예외"""

    def __init__(self, symbol: str):
        super().__init__(
            message=f"지원하지 않는 심볼: {symbol}",
            error_code="SYMBOL_NOT_SUPPORTED",
            details={"symbol": symbol}
        )


class TimeframeNotSupportedException(SmartRoutingException):
    """지원하지 않는 타임프레임 예외"""

    def __init__(self, timeframe: str):
        super().__init__(
            message=f"지원하지 않는 타임프레임: {timeframe}",
            error_code="TIMEFRAME_NOT_SUPPORTED",
            details={"timeframe": timeframe}
        )


class ApiRateLimitException(SmartRoutingException):
    """API 요청 제한 예외"""

    def __init__(
        self,
        message: str = "API 요청 제한에 도달했습니다",
        retry_after_seconds: Optional[int] = None
    ):
        super().__init__(
            message=message,
            error_code="API_RATE_LIMIT",
            details={"retry_after_seconds": retry_after_seconds}
        )


class WebSocketConnectionException(SmartRoutingException):
    """WebSocket 연결 예외"""

    def __init__(self, message: str = "WebSocket 연결에 실패했습니다"):
        super().__init__(
            message=message,
            error_code="WEBSOCKET_CONNECTION_FAILED"
        )


class WebSocketDataException(SmartRoutingException):
    """WebSocket 데이터 수신 예외"""

    def __init__(self, message: str = "WebSocket 데이터 수신에 실패했습니다"):
        super().__init__(
            message=message,
            error_code="WEBSOCKET_DATA_ERROR"
        )


class RestApiException(SmartRoutingException):
    """REST API 예외"""

    def __init__(
        self,
        message: str,
        http_status: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="REST_API_ERROR",
            details={
                "http_status": http_status,
                "response_data": response_data
            }
        )


class DataValidationException(SmartRoutingException):
    """데이터 검증 예외"""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            error_code="DATA_VALIDATION_ERROR",
            details={
                "field_name": field_name,
                "field_value": field_value
            }
        )


class ChannelSelectionException(SmartRoutingException):
    """채널 선택 예외"""

    def __init__(self, message: str = "적절한 데이터 채널을 선택할 수 없습니다"):
        super().__init__(
            message=message,
            error_code="CHANNEL_SELECTION_FAILED"
        )


class DataTransformationException(SmartRoutingException):
    """데이터 변환 예외"""

    def __init__(
        self,
        message: str,
        source_format: Optional[str] = None,
        target_format: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="DATA_TRANSFORMATION_ERROR",
            details={
                "source_format": source_format,
                "target_format": target_format
            }
        )


class TimeoutException(SmartRoutingException):
    """요청 타임아웃 예외"""

    def __init__(
        self,
        message: str = "요청 시간이 초과되었습니다",
        timeout_seconds: Optional[float] = None
    ):
        super().__init__(
            message=message,
            error_code="REQUEST_TIMEOUT",
            details={"timeout_seconds": timeout_seconds}
        )


# 업비트 API 에러를 Smart Routing 에러로 변환하는 헬퍼 함수들
class ErrorConverter:
    """업비트 API 에러를 도메인 에러로 변환"""

    @staticmethod
    def from_upbit_error(
        upbit_error_code: str,
        upbit_message: str,
        http_status: Optional[int] = None
    ) -> SmartRoutingException:
        """업비트 에러를 Smart Routing 에러로 변환"""

        # 업비트 에러 코드별 매핑
        error_mapping = {
            "INVALID_PARAMETER": InvalidRequestException,
            "INVALID_MARKET": SymbolNotSupportedException,
            "TOO_MANY_REQUESTS": ApiRateLimitException,
            "INTERNAL_SERVER_ERROR": RestApiException,
        }

        exception_class = error_mapping.get(upbit_error_code, SmartRoutingException)

        if exception_class == InvalidRequestException:
            return exception_class(upbit_message)
        elif exception_class == SymbolNotSupportedException:
            return exception_class(upbit_message)
        elif exception_class == ApiRateLimitException:
            return exception_class(upbit_message)
        else:
            return exception_class(
                message=upbit_message,
                error_code=upbit_error_code,
                details={"http_status": http_status}
            )

    @staticmethod
    def from_http_error(
        http_status: int,
        response_text: str
    ) -> SmartRoutingException:
        """HTTP 에러를 Smart Routing 에러로 변환"""

        if http_status == 400:
            return InvalidRequestException(
                f"잘못된 요청: {response_text}",
                {"http_status": http_status}
            )
        elif http_status == 429:
            return ApiRateLimitException(
                f"요청 제한 초과: {response_text}"
            )
        elif http_status >= 500:
            return RestApiException(
                f"서버 에러: {response_text}",
                http_status=http_status
            )
        else:
            return RestApiException(
                f"HTTP 에러 ({http_status}): {response_text}",
                http_status=http_status
            )
