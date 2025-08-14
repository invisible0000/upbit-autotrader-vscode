"""
Domain Layer Logging
도메인 계층용 임시 로깅 시스템

Phase 1에서 Domain Events 기반 로깅으로 대체될 예정입니다.
현재는 DDD 순수성을 유지하면서 기본적인 로깅 기능을 제공합니다.
"""

from typing import Any, Optional, Dict

# Domain Events 로깅 시스템
from upbit_auto_trading.domain.events.logging_events import (
    DomainLogRequested, LogLevel, DomainComponentInitialized,
    DomainOperationStarted, DomainOperationCompleted, DomainErrorOccurred
)


class DomainEventsLogger:
    """
    Domain Events 기반 로거

    Infrastructure 의존성 없이 Domain Events를 통해 로깅을 수행하는 DDD 순수 구현
    """

    def __init__(self, component_name: str):
        self._component_name = component_name

        # 컴포넌트 초기화 이벤트 발행
        self._publish_event(DomainComponentInitialized(
            component_name=component_name,
            component_type="Logger"
        ))

    def debug(self, message: str, context_data: Optional[Dict[str, Any]] = None) -> None:
        """Debug 레벨 로그"""
        self._log(LogLevel.DEBUG, message, context_data)

    def info(self, message: str, context_data: Optional[Dict[str, Any]] = None) -> None:
        """Info 레벨 로그"""
        self._log(LogLevel.INFO, message, context_data)

    def warning(self, message: str, context_data: Optional[Dict[str, Any]] = None) -> None:
        """Warning 레벨 로그"""
        self._log(LogLevel.WARNING, message, context_data)

    def error(self, message: str, context_data: Optional[Dict[str, Any]] = None,
              exception_info: Optional[str] = None) -> None:
        """Error 레벨 로그"""
        self._log(LogLevel.ERROR, message, context_data, exception_info)

    def critical(self, message: str, context_data: Optional[Dict[str, Any]] = None,
                 exception_info: Optional[str] = None) -> None:
        """Critical 레벨 로그"""
        self._log(LogLevel.CRITICAL, message, context_data, exception_info)

    def operation_started(self, operation_name: str,
                          parameters: Optional[Dict[str, Any]] = None) -> None:
        """Domain 작업 시작 로깅"""
        self._publish_event(DomainOperationStarted(
            component_name=self._component_name,
            operation_name=operation_name,
            operation_parameters=parameters
        ))

    def operation_completed(self, operation_name: str,
                            execution_time_ms: Optional[float] = None,
                            result_summary: Optional[str] = None) -> None:
        """Domain 작업 완료 로깅"""
        self._publish_event(DomainOperationCompleted(
            component_name=self._component_name,
            operation_name=operation_name,
            execution_time_ms=execution_time_ms,
            result_summary=result_summary
        ))

    def error_occurred(self, error_type: str, error_message: str,
                       error_context: Optional[Dict[str, Any]] = None,
                       stack_trace: Optional[str] = None) -> None:
        """Domain 오류 발생 로깅"""
        self._publish_event(DomainErrorOccurred(
            component_name=self._component_name,
            error_type=error_type,
            error_message=error_message,
            error_context=error_context,
            stack_trace=stack_trace
        ))

    def _log(self, level: LogLevel, message: str,
             context_data: Optional[Dict[str, Any]] = None,
             exception_info: Optional[str] = None) -> None:
        """내부 로깅 메서드 - Domain Event 발행"""
        self._publish_event(DomainLogRequested(
            component_name=self._component_name,
            log_level=level,
            message=message,
            context_data=context_data,
            exception_info=exception_info
        ))

    def _publish_event(self, event) -> None:
        """Domain Event 발행 - 안전한 구현"""
        try:
            # Domain Events Publisher를 안전하게 import
            from upbit_auto_trading.domain.events import publish_domain_event
            publish_domain_event(event)
        except Exception:
            # 이벤트 발행 실패 시 조용히 무시 (DDD 순수성 유지)
            pass


def create_domain_logger(component_name: str) -> DomainEventsLogger:
    """
    Domain Events 기반 로거 생성

    Args:
        component_name: 컴포넌트 이름

    Returns:
        DomainEventsLogger: Domain Events 기반 로거

    Note:
        Infrastructure 의존성 없는 순수한 Domain Logger입니다.
        실제 로깅은 Infrastructure Layer에서 Domain Events를 구독하여 처리합니다.
    """
    return DomainEventsLogger(component_name)
