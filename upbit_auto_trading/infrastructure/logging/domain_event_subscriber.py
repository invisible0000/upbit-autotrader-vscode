"""
Infrastructure Layer - Domain Events Subscriber
Domain Events를 구독하여 Infrastructure Logger로 전달하는 간단한 구현
"""

from upbit_auto_trading.domain.events.logging_events import (
    DomainLogRequested, DomainErrorOccurred, DomainComponentInitialized,
    DomainOperationStarted, DomainOperationCompleted
)
from upbit_auto_trading.domain.events import (
    subscribe_to_domain_events, DomainEvent
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


class DomainLoggingSubscriber:
    """
    Domain Events를 구독하여 Infrastructure Logger로 전달

    Domain Layer에서 발행한 로깅 이벤트를 받아서
    기존 Infrastructure 로깅 시스템으로 전달하는 간단한 구현
    """

    def __init__(self):
        """Domain Events Subscriber 초기화"""
        self._logger = create_component_logger("DomainEventsSubscriber")
        self._setup_subscriptions()
        self._logger.info("🔗 Domain Events 로깅 구독자 초기화 완료")

    def _setup_subscriptions(self) -> None:
        """Domain Events 구독 설정"""
        # 주요 로깅 이벤트 구독
        subscribe_to_domain_events("DomainLogRequested", self._handle_domain_event)
        subscribe_to_domain_events("DomainErrorOccurred", self._handle_domain_event)
        subscribe_to_domain_events("DomainComponentInitialized", self._handle_domain_event)
        subscribe_to_domain_events("DomainOperationStarted", self._handle_domain_event)
        subscribe_to_domain_events("DomainOperationCompleted", self._handle_domain_event)

    def _handle_domain_event(self, event: DomainEvent) -> None:
        """모든 Domain Event를 처리하는 통합 핸들러"""
        try:
            if isinstance(event, DomainLogRequested):
                self._handle_log_request(event)
            elif isinstance(event, DomainErrorOccurred):
                self._handle_error_occurred(event)
            elif isinstance(event, DomainComponentInitialized):
                self._handle_component_init(event)
            elif isinstance(event, DomainOperationStarted):
                self._handle_operation_start(event)
            elif isinstance(event, DomainOperationCompleted):
                self._handle_operation_complete(event)
        except Exception:
            # 이벤트 처리 실패 시 조용히 무시 (무한 루프 방지)
            pass

    def _handle_log_request(self, event: DomainLogRequested) -> None:
        """DomainLogRequested 이벤트 처리"""
        try:
            # 컴포넌트별 로거 생성
            component_logger = create_component_logger(event.component_name)

            # 로그 레벨에 따라 적절한 메서드 호출
            level_method = getattr(component_logger, event.log_level.value.lower(), None)
            if level_method:
                if event.context_data:
                    # 컨텍스트 데이터가 있는 경우 메시지에 포함
                    message = f"{event.message} | Context: {event.context_data}"
                else:
                    message = event.message

                level_method(message)
            else:
                # 알 수 없는 로그 레벨인 경우 info로 처리
                component_logger.info(f"[{event.log_level.value}] {event.message}")

        except Exception:
            # 로깅 처리 실패 시 조용히 무시 (무한 루프 방지)
            pass

    def _handle_error_occurred(self, event: DomainErrorOccurred) -> None:
        """DomainErrorOccurred 이벤트 처리"""
        try:
            component_logger = create_component_logger(event.component_name)
            error_message = f"❌ {event.error_type}: {event.error_message}"

            if event.error_context:
                error_message += f" | Context: {event.error_context}"

            component_logger.error(error_message)

        except Exception:
            pass

    def _handle_component_init(self, event: DomainComponentInitialized) -> None:
        """DomainComponentInitialized 이벤트 처리"""
        try:
            component_logger = create_component_logger(event.component_name)
            init_message = f"🎯 {event.component_type} 초기화 완료"

            if event.initialization_context:
                init_message += f" | Context: {event.initialization_context}"

            component_logger.info(init_message)

        except Exception:
            pass

    def _handle_operation_start(self, event: DomainOperationStarted) -> None:
        """DomainOperationStarted 이벤트 처리"""
        try:
            component_logger = create_component_logger(event.component_name)
            start_message = f"🚀 작업 시작: {event.operation_name}"

            if event.operation_parameters:
                start_message += f" | Parameters: {event.operation_parameters}"

            component_logger.debug(start_message)

        except Exception:
            pass

    def _handle_operation_complete(self, event: DomainOperationCompleted) -> None:
        """DomainOperationCompleted 이벤트 처리"""
        try:
            component_logger = create_component_logger(event.component_name)
            complete_message = f"✅ 작업 완료: {event.operation_name}"

            if event.execution_time_ms:
                complete_message += f" | 실행시간: {event.execution_time_ms}ms"

            if event.result_summary:
                complete_message += f" | 결과: {event.result_summary}"

            component_logger.debug(complete_message)

        except Exception:
            pass


# 전역 구독자 인스턴스 (Singleton 패턴)
_domain_logging_subscriber = None


def get_domain_logging_subscriber() -> DomainLoggingSubscriber:
    """Domain Logging Subscriber 싱글톤 인스턴스 반환"""
    global _domain_logging_subscriber
    if _domain_logging_subscriber is None:
        _domain_logging_subscriber = DomainLoggingSubscriber()
    return _domain_logging_subscriber


def initialize_domain_logging_subscriber() -> DomainLoggingSubscriber:
    """Domain Events 로깅 구독자 초기화 (편의 함수)"""
    return get_domain_logging_subscriber()
