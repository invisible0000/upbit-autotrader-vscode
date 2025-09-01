"""
WebSocket v6.0 예외 정의
======================

WebSocket v6 시스템의 예외 계층 구조 정의
명확한 에러 분류와 복구 가능성 판단 지원

예외 계층:
- WebSocketException (기본)
  ├── ConnectionError
  ├── SubscriptionError
  ├── BackpressureError
  ├── AuthenticationError
  └── RecoveryError
"""

from typing import Optional, Any, Dict
from enum import Enum


class ErrorSeverity(Enum):
    """에러 심각도"""
    LOW = "low"           # 일시적, 자동 복구 가능
    MEDIUM = "medium"     # 재시도 필요
    HIGH = "high"         # 즉시 처리 필요
    CRITICAL = "critical"  # 시스템 중단 위험


class RecoverabilityType(Enum):
    """복구 가능성 타입"""
    AUTO_RECOVERABLE = "auto_recoverable"      # 자동 복구 가능
    MANUAL_RECOVERABLE = "manual_recoverable"  # 수동 개입 필요
    NON_RECOVERABLE = "non_recoverable"        # 복구 불가능


class WebSocketException(Exception):
    """WebSocket 기본 예외 클래스"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recoverable: RecoverabilityType = RecoverabilityType.AUTO_RECOVERABLE,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.recoverable = recoverable
        self.context = context or {}
        self.cause = cause

    def __str__(self) -> str:
        error_info = f"[{self.error_code}] " if self.error_code else ""
        severity_info = f"({self.severity.value.upper()}) " if self.severity else ""
        return f"{error_info}{severity_info}{self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """예외 정보를 딕셔너리로 변환 (로깅/모니터링용)"""
        return {
            'exception_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'severity': self.severity.value if self.severity else None,
            'recoverable': self.recoverable.value if self.recoverable else None,
            'context': self.context,
            'cause': str(self.cause) if self.cause else None
        }


class ConnectionError(WebSocketException):
    """WebSocket 연결 관련 오류"""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        connection_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if url:
            context['url'] = url
        if connection_type:
            context['connection_type'] = connection_type

        kwargs['context'] = context
        kwargs.setdefault('error_code', 'CONN_ERROR')
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('recoverable', RecoverabilityType.AUTO_RECOVERABLE)

        super().__init__(message, **kwargs)


class ConnectionTimeoutError(ConnectionError):
    """연결 타임아웃 오류"""

    def __init__(self, timeout_seconds: float, url: str, **kwargs):
        message = f"WebSocket 연결 타임아웃 ({timeout_seconds}초)"
        context = kwargs.get('context', {})
        context.update({
            'timeout_seconds': timeout_seconds,
            'url': url
        })

        kwargs['context'] = context
        kwargs['error_code'] = 'CONN_TIMEOUT'

        super().__init__(message, url=url, **kwargs)


class ConnectionLostError(ConnectionError):
    """연결 끊김 오류"""

    def __init__(self, reason: Optional[str] = None, **kwargs):
        message = "WebSocket 연결 끊김"
        if reason:
            message += f": {reason}"

        context = kwargs.get('context', {})
        if reason:
            context['disconnect_reason'] = reason

        kwargs['context'] = context
        kwargs['error_code'] = 'CONN_LOST'
        kwargs['severity'] = ErrorSeverity.MEDIUM  # 자동 재연결 가능

        super().__init__(message, **kwargs)


class SubscriptionError(WebSocketException):
    """구독 관련 오류"""

    def __init__(
        self,
        message: str,
        data_type: Optional[str] = None,
        symbols: Optional[list] = None,
        component_id: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if data_type:
            context['data_type'] = data_type
        if symbols:
            context['symbols'] = symbols
        if component_id:
            context['component_id'] = component_id

        kwargs['context'] = context
        kwargs.setdefault('error_code', 'SUB_ERROR')
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        kwargs.setdefault('recoverable', RecoverabilityType.AUTO_RECOVERABLE)

        super().__init__(message, **kwargs)


class SubscriptionConflictError(SubscriptionError):
    """구독 충돌 오류 (업비트 덮어쓰기 정책)"""

    def __init__(self, existing_symbols: list, new_symbols: list, **kwargs):
        message = f"구독 충돌 감지: 기존 {existing_symbols}, 신규 {new_symbols}"

        context = kwargs.get('context', {})
        context.update({
            'existing_symbols': existing_symbols,
            'new_symbols': new_symbols,
            'conflict_type': 'overwrite_policy'
        })

        kwargs['context'] = context
        kwargs['error_code'] = 'SUB_CONFLICT'
        kwargs['severity'] = ErrorSeverity.HIGH  # v6에서는 이런 상황이 발생하면 안됨

        super().__init__(message, **kwargs)


class SubscriptionLimitError(SubscriptionError):
    """구독 한도 초과 오류"""

    def __init__(self, current_count: int, max_limit: int, **kwargs):
        message = f"구독 한도 초과: {current_count}/{max_limit}"

        context = kwargs.get('context', {})
        context.update({
            'current_count': current_count,
            'max_limit': max_limit
        })

        kwargs['context'] = context
        kwargs['error_code'] = 'SUB_LIMIT'
        kwargs['severity'] = ErrorSeverity.MEDIUM
        kwargs['recoverable'] = RecoverabilityType.MANUAL_RECOVERABLE

        super().__init__(message, **kwargs)


class BackpressureError(WebSocketException):
    """백프레셔 관련 오류"""

    def __init__(
        self,
        message: str,
        queue_size: Optional[int] = None,
        max_size: Optional[int] = None,
        strategy: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if queue_size is not None:
            context['queue_size'] = queue_size
        if max_size is not None:
            context['max_size'] = max_size
        if strategy:
            context['strategy'] = strategy

        kwargs['context'] = context
        kwargs.setdefault('error_code', 'BACKPRESSURE')
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        kwargs.setdefault('recoverable', RecoverabilityType.AUTO_RECOVERABLE)

        super().__init__(message, **kwargs)


class QueueOverflowError(BackpressureError):
    """큐 오버플로우 오류"""

    def __init__(self, queue_size: int, max_size: int, dropped_count: int = 0, **kwargs):
        message = f"큐 오버플로우: {queue_size}/{max_size}"
        if dropped_count > 0:
            message += f", {dropped_count}개 메시지 폐기"

        context = kwargs.get('context', {})
        context.update({
            'queue_size': queue_size,
            'max_size': max_size,
            'dropped_count': dropped_count
        })

        kwargs['context'] = context
        kwargs['error_code'] = 'QUEUE_OVERFLOW'

        super().__init__(message, queue_size=queue_size, max_size=max_size, **kwargs)


class AuthenticationError(WebSocketException):
    """인증 관련 오류 (Private WebSocket 전용)"""

    def __init__(
        self,
        message: str,
        auth_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if auth_type:
            context['auth_type'] = auth_type

        kwargs['context'] = context
        kwargs.setdefault('error_code', 'AUTH_ERROR')
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('recoverable', RecoverabilityType.AUTO_RECOVERABLE)

        super().__init__(message, **kwargs)


class JWTTokenError(AuthenticationError):
    """JWT 토큰 관련 오류"""

    def __init__(self, token_issue: str, **kwargs):
        message = f"JWT 토큰 오류: {token_issue}"

        context = kwargs.get('context', {})
        context['token_issue'] = token_issue

        kwargs['context'] = context
        kwargs['error_code'] = 'JWT_ERROR'
        kwargs['auth_type'] = 'jwt'

        super().__init__(message, **kwargs)


class JWTTokenExpiredError(JWTTokenError):
    """JWT 토큰 만료 오류"""

    def __init__(self, expires_at: Optional[str] = None, **kwargs):
        message = "JWT 토큰 만료"
        if expires_at:
            message += f" (만료 시간: {expires_at})"

        context = kwargs.get('context', {})
        if expires_at:
            context['expires_at'] = expires_at

        kwargs['context'] = context
        kwargs['error_code'] = 'JWT_EXPIRED'
        kwargs['severity'] = ErrorSeverity.MEDIUM  # 자동 갱신 가능

        super().__init__("토큰 만료", **kwargs)


class RecoveryError(WebSocketException):
    """복구 프로세스 관련 오류"""

    def __init__(
        self,
        message: str,
        recovery_type: Optional[str] = None,
        attempt_count: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if recovery_type:
            context['recovery_type'] = recovery_type
        if attempt_count is not None:
            context['attempt_count'] = attempt_count

        kwargs['context'] = context
        kwargs.setdefault('error_code', 'RECOVERY_ERROR')
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('recoverable', RecoverabilityType.MANUAL_RECOVERABLE)

        super().__init__(message, **kwargs)


class ReconnectFailedError(RecoveryError):
    """재연결 실패 오류"""

    def __init__(self, attempt_count: int, max_attempts: int, last_error: Optional[str] = None, **kwargs):
        message = f"재연결 실패: {attempt_count}/{max_attempts} 시도"
        if last_error:
            message += f", 마지막 오류: {last_error}"

        context = kwargs.get('context', {})
        context.update({
            'attempt_count': attempt_count,
            'max_attempts': max_attempts,
            'last_error': last_error
        })

        kwargs['context'] = context
        kwargs['error_code'] = 'RECONNECT_FAILED'
        kwargs['recovery_type'] = 'reconnection'
        kwargs['recoverable'] = RecoverabilityType.NON_RECOVERABLE  # 최대 시도 후에는 수동 개입 필요

        super().__init__(message, **kwargs)


class SubscriptionRecoveryError(RecoveryError):
    """구독 복구 실패 오류"""

    def __init__(self, failed_subscriptions: list, **kwargs):
        message = f"구독 복구 실패: {len(failed_subscriptions)}개 구독"

        context = kwargs.get('context', {})
        context['failed_subscriptions'] = failed_subscriptions

        kwargs['context'] = context
        kwargs['error_code'] = 'SUB_RECOVERY_FAILED'
        kwargs['recovery_type'] = 'subscription_recovery'

        super().__init__(message, **kwargs)


class RateLimitError(WebSocketException):
    """Rate Limit 관련 오류"""

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        limit_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if retry_after is not None:
            context['retry_after'] = retry_after
        if limit_type:
            context['limit_type'] = limit_type

        kwargs['context'] = context
        kwargs.setdefault('error_code', 'RATE_LIMIT')
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        kwargs.setdefault('recoverable', RecoverabilityType.AUTO_RECOVERABLE)

        super().__init__(message, **kwargs)


class ValidationError(WebSocketException):
    """데이터 검증 오류"""

    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        **kwargs
    ):
        context = kwargs.get('context', {})
        if field_name:
            context['field_name'] = field_name
        if field_value is not None:
            context['field_value'] = field_value

        kwargs['context'] = context
        kwargs.setdefault('error_code', 'VALIDATION_ERROR')
        kwargs.setdefault('severity', ErrorSeverity.LOW)
        kwargs.setdefault('recoverable', RecoverabilityType.MANUAL_RECOVERABLE)

        super().__init__(message, **kwargs)


# =============================================================================
# 예외 유틸리티 함수
# =============================================================================

def is_recoverable_error(exception: Exception) -> bool:
    """예외가 복구 가능한지 판단"""
    if isinstance(exception, WebSocketException):
        return exception.recoverable in [
            RecoverabilityType.AUTO_RECOVERABLE,
            RecoverabilityType.MANUAL_RECOVERABLE
        ]

    # 표준 예외 처리
    if isinstance(exception, (ConnectionRefusedError, TimeoutError)):
        return True

    return False


def should_auto_retry(exception: Exception) -> bool:
    """자동 재시도가 필요한지 판단"""
    if isinstance(exception, WebSocketException):
        return exception.recoverable == RecoverabilityType.AUTO_RECOVERABLE

    # 표준 예외 처리
    if isinstance(exception, (ConnectionRefusedError, TimeoutError)):
        return True

    return False


def get_error_severity(exception: Exception) -> ErrorSeverity:
    """예외의 심각도 반환"""
    if isinstance(exception, WebSocketException):
        return exception.severity

    # 표준 예외의 기본 심각도
    if isinstance(exception, ConnectionRefusedError):
        return ErrorSeverity.HIGH
    elif isinstance(exception, TimeoutError):
        return ErrorSeverity.MEDIUM
    else:
        return ErrorSeverity.LOW


def create_error_context(
    component_id: Optional[str] = None,
    connection_type: Optional[str] = None,
    data_type: Optional[str] = None,
    symbols: Optional[list] = None,
    **additional_context
) -> Dict[str, Any]:
    """에러 컨텍스트 생성 유틸리티"""
    context = {}

    if component_id:
        context['component_id'] = component_id
    if connection_type:
        context['connection_type'] = connection_type
    if data_type:
        context['data_type'] = data_type
    if symbols:
        context['symbols'] = symbols

    context.update(additional_context)
    return context
