"""
MarketDataBackbone V2 - API 예외 클래스들

통합 API에서 사용하는 모든 예외 클래스를 정의합니다.
"""

from typing import Any, Optional
from datetime import datetime
import re


class UnifiedDataException(Exception):
    """통합 API 기본 예외 클래스"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", original_error: Optional[Exception] = None):
        super().__init__(message)
        self.error_code = error_code
        self.original_error = original_error
        self.timestamp = datetime.now()


class ChannelUnavailableException(UnifiedDataException):
    """채널 사용 불가 예외"""
    def __init__(self, channel: str, reason: str):
        super().__init__(f"{channel} 채널 사용 불가: {reason}", "CHANNEL_UNAVAILABLE")
        self.channel = channel


class DataValidationException(UnifiedDataException):
    """데이터 검증 실패 예외"""
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(f"데이터 검증 실패 [{field}]: {reason}", "DATA_VALIDATION_ERROR")
        self.field = field
        self.value = value


class RateLimitException(UnifiedDataException):
    """요청 제한 초과 예외"""
    def __init__(self, retry_after: Optional[int] = None):
        message = "API 요청 제한 초과"
        if retry_after:
            message += f" (재시도 가능: {retry_after}초 후)"
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class NetworkException(UnifiedDataException):
    """네트워크 연결 문제 예외"""
    def __init__(self, operation: str, details: str):
        super().__init__(f"네트워크 오류 [{operation}]: {details}", "NETWORK_ERROR")
        self.operation = operation


class ErrorUnifier:
    """
    통합 에러 처리기 (전문가 권고: 통합 에러 처리)

    다양한 채널의 예외를 일관된 형태로 변환
    """

    @staticmethod
    def unify_error(error: Exception, channel: str, operation: str) -> UnifiedDataException:
        """다양한 예외를 통합 예외로 변환"""

        # HTTP 429 Too Many Requests
        if "429" in str(error) or "too many requests" in str(error).lower():
            # Remaining-Req 헤더에서 재시도 시간 추출 시도
            retry_after = ErrorUnifier._extract_retry_after(str(error))
            return RateLimitException(retry_after)

        # WebSocket 인증 에러
        if "INVALID_AUTH" in str(error) or "authentication" in str(error).lower():
            return UnifiedDataException(
                "인증 정보가 올바르지 않습니다",
                "AUTHENTICATION_ERROR",
                error
            )

        # 네트워크 연결 에러
        if any(keyword in str(error).lower() for keyword in
               ["connection", "timeout", "network", "socket"]):
            return NetworkException(operation, str(error))

        # 데이터 검증 에러
        if "validation" in str(error).lower() or "invalid data" in str(error).lower():
            return DataValidationException("unknown", None, str(error))

        # 채널 사용 불가
        if "unavailable" in str(error).lower() or "not available" in str(error).lower():
            return ChannelUnavailableException(channel, str(error))

        # 기본 통합 예외
        return UnifiedDataException(
            f"[{channel}] {operation} 실패: {str(error)}",
            "GENERAL_ERROR",
            error
        )

    @staticmethod
    def _extract_retry_after(error_text: str) -> Optional[int]:
        """에러 텍스트에서 재시도 시간 추출"""
        # 간단한 구현: 실제로는 HTTP 헤더 파싱 필요
        match = re.search(r'retry.{0,10}(\d+)', error_text.lower())
        if match:
            return int(match.group(1))
        return None
