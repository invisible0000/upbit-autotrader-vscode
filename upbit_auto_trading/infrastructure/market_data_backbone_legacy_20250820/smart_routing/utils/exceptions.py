"""
Smart Routing 시스템 예외 클래스 정의

이 모듈은 Smart Router에서 발생할 수 있는 모든 예외를 정의합니다.
"""

from typing import Optional


class SmartRoutingException(Exception):
    """Smart Routing 시스템 기본 예외"""
    pass


class DataRouterException(SmartRoutingException):
    """데이터 라우터 관련 예외"""
    pass


class DataProviderException(SmartRoutingException):
    """데이터 제공자 관련 예외"""
    pass


class InvalidSymbolException(SmartRoutingException):
    """유효하지 않은 심볼 예외"""
    pass


class InvalidTimeframeException(SmartRoutingException):
    """유효하지 않은 타임프레임 예외"""
    pass


class InvalidRequestException(SmartRoutingException):
    """유효하지 않은 요청 예외"""
    pass


class ProviderUnavailableException(DataProviderException):
    """제공자 사용 불가 예외"""
    pass


class RateLimitExceededException(DataProviderException):
    """레이트 제한 초과 예외"""

    def __init__(self, message: str, retry_after_seconds: Optional[int] = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ConnectionException(DataProviderException):
    """연결 관련 예외"""
    pass


class AuthenticationException(DataProviderException):
    """인증 관련 예외"""
    pass


class DataNotFoundException(DataProviderException):
    """데이터를 찾을 수 없음 예외"""
    pass


class InvalidResponseException(DataProviderException):
    """유효하지 않은 응답 예외"""
    pass


class SubscriptionException(SmartRoutingException):
    """실시간 구독 관련 예외"""
    pass


class ChannelSelectionException(SmartRoutingException):
    """채널 선택 관련 예외"""
    pass
