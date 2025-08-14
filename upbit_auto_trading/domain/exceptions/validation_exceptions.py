"""
도메인 검증 예외 클래스들
"""
from upbit_auto_trading.domain.exceptions.domain_exceptions import DomainException


class ValidationError(DomainException):
    """도메인 검증 실패 예외"""
    def __init__(self, message: str = "도메인 검증에 실패했습니다"):
        super().__init__(message, "VALIDATION_ERROR")
