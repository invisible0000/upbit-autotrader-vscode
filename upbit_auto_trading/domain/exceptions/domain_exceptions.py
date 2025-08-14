"""
도메인 예외 클래스들

도메인 계층에서 발생하는 비즈니스 규칙 위반이나 오류 상황을 나타내는 예외들입니다.
모든 도메인 예외는 DomainException을 상속받아 구현됩니다.
"""

from typing import Optional

class DomainException(Exception):
    """도메인 계층 기본 예외"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()

    def __str__(self):
        return f"[{self.error_code}] {self.message}"

class ValidationError(DomainException):
    """도메인 검증 실패 예외"""
    def __init__(self, message: str = "도메인 검증에 실패했습니다"):
        super().__init__(message, "VALIDATION_ERROR")


class InvalidStrategyIdError(DomainException):
    """잘못된 전략 ID 예외"""
    def __init__(self, message: str = "잘못된 전략 ID입니다"):
        super().__init__(message, "INVALID_STRATEGY_ID")

class InvalidTriggerIdError(DomainException):
    """잘못된 트리거 ID 예외"""
    def __init__(self, message: str = "잘못된 트리거 ID입니다"):
        super().__init__(message, "INVALID_TRIGGER_ID")

class IncompatibleTriggerError(DomainException):
    """호환되지 않는 트리거 예외"""
    def __init__(self, message: str = "호환되지 않는 트리거입니다"):
        super().__init__(message, "INCOMPATIBLE_TRIGGER")

class InvalidParameterError(DomainException):
    """잘못된 파라미터 예외"""
    def __init__(self, parameter_name: str, message: Optional[str] = None):
        msg = message or f"잘못된 파라미터: {parameter_name}"
        super().__init__(msg, "INVALID_PARAMETER")
        self.parameter_name = parameter_name

class StrategyValidationError(DomainException):
    """전략 검증 실패 예외"""
    def __init__(self, message: str = "전략 검증에 실패했습니다"):
        super().__init__(message, "STRATEGY_VALIDATION_ERROR")

class TriggerEvaluationError(DomainException):
    """트리거 평가 실패 예외"""
    def __init__(self, trigger_id: str, message: Optional[str] = None):
        msg = message or f"트리거 평가 실패: {trigger_id}"
        super().__init__(msg, "TRIGGER_EVALUATION_ERROR")
        self.trigger_id = trigger_id
