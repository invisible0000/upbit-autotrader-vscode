"""
거래소 API 공통 예외 클래스들

API 클라이언트에서 사용하는 표준화된 예외들
"""
from typing import Optional, Dict, Any


class ApiClientError(Exception):
    """API 클라이언트 기본 예외"""

    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(ApiClientError):
    """인증 관련 예외"""
    pass


class RateLimitError(ApiClientError):
    """Rate Limit 관련 예외"""
    pass


class NetworkError(ApiClientError):
    """네트워크 관련 예외"""
    pass


class ValidationError(ApiClientError):
    """데이터 검증 관련 예외"""
    pass
