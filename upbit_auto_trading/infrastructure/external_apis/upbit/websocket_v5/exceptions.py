"""
업비트 WebSocket v5.0 - 사용자 정의 예외 시스템

🎯 특징:
- 구체적인 예외 타입
- 자동 복구 힌트
- 상황별 에러 코드
- 구조화된 에러 정보
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class ErrorCode(Enum):
    """오류 코드"""
    # 연결 관련 오류
    CONNECTION_FAILED = "CONNECTION_FAILED"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    CONNECTION_CLOSED = "CONNECTION_CLOSED"

    # 인증 관련 오류
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INVALID_API_KEYS = "INVALID_API_KEYS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # 구독 관련 오류
    SUBSCRIPTION_FAILED = "SUBSCRIPTION_FAILED"
    INVALID_SUBSCRIPTION_PARAMS = "INVALID_SUBSCRIPTION_PARAMS"
    TOO_MANY_SUBSCRIPTIONS = "TOO_MANY_SUBSCRIPTIONS"
    UNSUPPORTED_DATA_TYPE = "UNSUPPORTED_DATA_TYPE"

    # 메시지 관련 오류
    MESSAGE_PARSING_FAILED = "MESSAGE_PARSING_FAILED"
    INVALID_MESSAGE_FORMAT = "INVALID_MESSAGE_FORMAT"
    MESSAGE_TIMEOUT = "MESSAGE_TIMEOUT"

    # 설정 관련 오류
    INVALID_CONFIG = "INVALID_CONFIG"
    CONFIG_FILE_NOT_FOUND = "CONFIG_FILE_NOT_FOUND"

    # 시스템 관련 오류
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    STATE_TRANSITION_ERROR = "STATE_TRANSITION_ERROR"


class RecoveryAction(Enum):
    """복구 액션"""
    RETRY = "RETRY"
    RECONNECT = "RECONNECT"
    RECONFIGURE = "RECONFIGURE"
    ABORT = "ABORT"
    WAIT = "WAIT"


class WebSocketError(Exception):
    """WebSocket 기본 예외"""

    def __init__(self,
                 message: str,
                 error_code: ErrorCode,
                 recovery_action: RecoveryAction = RecoveryAction.ABORT,
                 details: Optional[Dict[str, Any]] = None,
                 original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.error_code = error_code
        self.recovery_action = recovery_action
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now()

    def get_error_info(self) -> Dict[str, Any]:
        """구조화된 오류 정보 반환"""
        return {
            "message": str(self),
            "error_code": self.error_code.value,
            "recovery_action": self.recovery_action.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }

    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        return self.recovery_action in {RecoveryAction.RETRY, RecoveryAction.RECONNECT}

    def should_reconnect(self) -> bool:
        """재연결 필요 여부"""
        return self.recovery_action == RecoveryAction.RECONNECT


class WebSocketConnectionError(WebSocketError):
    """WebSocket 연결 관련 예외"""

    def __init__(self, message: str,
                 url: Optional[str] = None,
                 original_exception: Optional[Exception] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONNECTION_FAILED,
            recovery_action=RecoveryAction.RECONNECT,
            details={"url": url},
            original_exception=original_exception
        )


class WebSocketConnectionTimeoutError(WebSocketConnectionError):
    """WebSocket 연결 타임아웃 예외"""

    def __init__(self, timeout_seconds: float, url: Optional[str] = None):
        super().__init__(
            message=f"WebSocket 연결 타임아웃 ({timeout_seconds}초)",
            url=url
        )
        self.error_code = ErrorCode.CONNECTION_TIMEOUT
        self.details["timeout_seconds"] = timeout_seconds


class WebSocketAuthenticationError(WebSocketError):
    """WebSocket 인증 관련 예외"""

    def __init__(self, message: str, auth_type: str = "unknown"):
        super().__init__(
            message=message,
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            recovery_action=RecoveryAction.RECONFIGURE,
            details={"auth_type": auth_type}
        )


class InvalidAPIKeysError(WebSocketAuthenticationError):
    """잘못된 API 키 예외"""

    def __init__(self, message: str = "유효하지 않은 API 키입니다"):
        super().__init__(message, auth_type="api_key")
        self.error_code = ErrorCode.INVALID_API_KEYS


class SubscriptionError(WebSocketError):
    """구독 관련 예외"""

    def __init__(self, message: str,
                 data_type: Optional[str] = None,
                 symbols: Optional[list] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SUBSCRIPTION_FAILED,
            recovery_action=RecoveryAction.RETRY,
            details={
                "data_type": data_type,
                "symbols": symbols
            }
        )


class InvalidParameterError(SubscriptionError):
    """잘못된 파라미터 예외"""

    def __init__(self, parameter_name: str, parameter_value: Any, reason: str):
        message = f"잘못된 파라미터 '{parameter_name}': {reason}"
        super().__init__(
            message=message,
            data_type=None,
            symbols=None
        )
        self.error_code = ErrorCode.INVALID_SUBSCRIPTION_PARAMS
        self.recovery_action = RecoveryAction.RECONFIGURE
        self.details.update({
            "parameter_name": parameter_name,
            "parameter_value": str(parameter_value),
            "reason": reason
        })


class TooManySubscriptionsError(SubscriptionError):
    """구독 수 초과 예외"""

    def __init__(self, current_count: int, max_allowed: int):
        message = f"구독 수 초과: {current_count}/{max_allowed}"
        super().__init__(message)
        self.error_code = ErrorCode.TOO_MANY_SUBSCRIPTIONS
        self.recovery_action = RecoveryAction.RECONFIGURE
        self.details.update({
            "current_count": current_count,
            "max_allowed": max_allowed
        })


class UnsupportedDataTypeError(SubscriptionError):
    """지원하지 않는 데이터 타입 예외"""

    def __init__(self, data_type: str, supported_types: list):
        message = f"지원하지 않는 데이터 타입: {data_type}"
        super().__init__(message, data_type=data_type)
        self.error_code = ErrorCode.UNSUPPORTED_DATA_TYPE
        self.recovery_action = RecoveryAction.RECONFIGURE
        self.details["supported_types"] = supported_types


class MessageError(WebSocketError):
    """메시지 관련 예외"""

    def __init__(self, message: str, raw_message: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.MESSAGE_PARSING_FAILED,
            recovery_action=RecoveryAction.RETRY,
            details={"raw_message": raw_message}
        )


class MessageParsingError(MessageError):
    """메시지 파싱 실패 예외"""

    def __init__(self, raw_message: str, parsing_error: str):
        message = f"메시지 파싱 실패: {parsing_error}"
        super().__init__(message, raw_message)


class MessageTimeoutError(MessageError):
    """메시지 타임아웃 예외"""

    def __init__(self, timeout_seconds: float):
        message = f"메시지 수신 타임아웃 ({timeout_seconds}초)"
        super().__init__(message)
        self.error_code = ErrorCode.MESSAGE_TIMEOUT
        self.details["timeout_seconds"] = timeout_seconds


class ConfigurationError(WebSocketError):
    """설정 관련 예외"""

    def __init__(self, message: str, config_section: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_CONFIG,
            recovery_action=RecoveryAction.RECONFIGURE,
            details={"config_section": config_section}
        )


class ConfigFileNotFoundError(ConfigurationError):
    """설정 파일 없음 예외"""

    def __init__(self, config_path: str):
        message = f"설정 파일을 찾을 수 없습니다: {config_path}"
        super().__init__(message)
        self.error_code = ErrorCode.CONFIG_FILE_NOT_FOUND
        self.details["config_path"] = config_path


class RateLimitExceededError(WebSocketError):
    """Rate Limit 초과 예외"""

    def __init__(self, current_rate: float, max_rate: float, wait_time: float):
        message = f"Rate Limit 초과: {current_rate:.1f}/{max_rate:.1f} req/s"
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            recovery_action=RecoveryAction.WAIT,
            details={
                "current_rate": current_rate,
                "max_rate": max_rate,
                "wait_time": wait_time
            }
        )


class MemoryLimitExceededError(WebSocketError):
    """메모리 한계 초과 예외"""

    def __init__(self, current_usage_mb: float, limit_mb: float):
        message = f"메모리 사용량 초과: {current_usage_mb:.1f}/{limit_mb:.1f} MB"
        super().__init__(
            message=message,
            error_code=ErrorCode.MEMORY_LIMIT_EXCEEDED,
            recovery_action=RecoveryAction.ABORT,
            details={
                "current_usage_mb": current_usage_mb,
                "limit_mb": limit_mb
            }
        )


class StateTransitionError(WebSocketError):
    """상태 전이 오류 예외"""

    def __init__(self, current_state: str, target_state: str):
        message = f"잘못된 상태 전이: {current_state} -> {target_state}"
        super().__init__(
            message=message,
            error_code=ErrorCode.STATE_TRANSITION_ERROR,
            recovery_action=RecoveryAction.ABORT,
            details={
                "current_state": current_state,
                "target_state": target_state
            }
        )


# 예외 복구 도우미 함수들
def get_recovery_delay(error: WebSocketError, attempt: int) -> float:
    """예외 타입에 따른 복구 지연 시간 계산"""
    base_delays = {
        ErrorCode.CONNECTION_FAILED: 2.0,
        ErrorCode.CONNECTION_TIMEOUT: 5.0,
        ErrorCode.AUTHENTICATION_FAILED: 10.0,
        ErrorCode.RATE_LIMIT_EXCEEDED: error.details.get('wait_time', 1.0),
        ErrorCode.SUBSCRIPTION_FAILED: 1.0,
        ErrorCode.MESSAGE_PARSING_FAILED: 0.1,
    }

    base_delay = base_delays.get(error.error_code, 1.0)

    # 지수 백오프 적용 (최대 60초)
    delay = min(base_delay * (2 ** attempt), 60.0)
    return delay


def should_retry_error(error: WebSocketError, attempt: int, max_attempts: int) -> bool:
    """예외 타입과 시도 횟수에 따른 재시도 여부 판단"""
    if attempt >= max_attempts:
        return False

    # 재시도 불가능한 오류들
    no_retry_codes = {
        ErrorCode.INVALID_API_KEYS,
        ErrorCode.INVALID_CONFIG,
        ErrorCode.CONFIG_FILE_NOT_FOUND,
        ErrorCode.STATE_TRANSITION_ERROR,
        ErrorCode.MEMORY_LIMIT_EXCEEDED
    }

    return error.error_code not in no_retry_codes and error.can_retry()
