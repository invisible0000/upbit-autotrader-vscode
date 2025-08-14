"""
Domain Layer 로깅 전략 - Domain Events 기반 대안

Domain 계층에서 Infrastructure에 직접 의존하지 않고 로깅을 수행하는 방법을 설계합니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent


class LogLevel(Enum):
    """로그 레벨"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class DomainLogEvent(DomainEvent):
    """Domain 계층에서 발생하는 로그 이벤트"""
    component_name: str
    log_level: LogLevel
    message: str
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.event_type:
            self.event_type = "DomainLogEvent"


class DomainLogger:
    """
    Domain 계층 전용 로거

    Infrastructure 의존성 없이 Domain Events를 통해 로깅합니다.
    """

    def __init__(self, component_name: str):
        self.component_name = component_name

    def debug(self, message: str, **context):
        """디버그 로그"""
        self._log(LogLevel.DEBUG, message, context)

    def info(self, message: str, **context):
        """정보 로그"""
        self._log(LogLevel.INFO, message, context)

    def warning(self, message: str, **context):
        """경고 로그"""
        self._log(LogLevel.WARNING, message, context)

    def error(self, message: str, **context):
        """오류 로그"""
        self._log(LogLevel.ERROR, message, context)

    def critical(self, message: str, **context):
        """치명적 오류 로그"""
        self._log(LogLevel.CRITICAL, message, context)

    def _log(self, level: LogLevel, message: str, context: Dict[str, Any]):
        """Domain Event를 통한 로그 발행"""
        try:
            # Domain Event Publisher를 통해 로그 이벤트 발행
            from upbit_auto_trading.domain.events import publish_domain_event

            event = DomainLogEvent(
                component_name=self.component_name,
                log_level=level,
                message=message,
                context=context or {}
            )

            publish_domain_event(event)

        except Exception:
            # Domain Events 시스템이 실패해도 Domain 로직은 계속 진행
            # 로깅 실패가 비즈니스 로직을 중단시키면 안 됨
            pass


def create_domain_logger(component_name: str) -> DomainLogger:
    """Domain 계층 전용 로거 생성"""
    return DomainLogger(component_name)


# Infrastructure 계층에서 DomainLogEvent를 처리하는 핸들러 등록
def setup_domain_log_handler():
    """
    Infrastructure 계층에서 호출하여 Domain 로그 이벤트를 실제 로깅 시스템으로 전달
    """
    from upbit_auto_trading.domain.events import get_domain_event_publisher
    from upbit_auto_trading.infrastructure.logging import get_logging_service

    def handle_domain_log_event(event: DomainLogEvent):
        """Domain 로그 이벤트를 Infrastructure 로깅 시스템으로 전달"""
        try:
            logging_service = get_logging_service()
            logger = logging_service.get_logger(event.component_name)

            # LogLevel enum을 logging 레벨로 변환
            level_mapping = {
                LogLevel.DEBUG: 10,    # logging.DEBUG
                LogLevel.INFO: 20,     # logging.INFO
                LogLevel.WARNING: 30,  # logging.WARNING
                LogLevel.ERROR: 40,    # logging.ERROR
                LogLevel.CRITICAL: 50  # logging.CRITICAL
            }

            logger.log(level_mapping[event.log_level], event.message)

        except Exception as e:
            # 로깅 시스템 오류가 발생해도 Domain 이벤트 처리는 계속 진행
            print(f"Domain log handler error: {e}")

    # 이벤트 핸들러 등록
    publisher = get_domain_event_publisher()
    publisher.register_handler(DomainLogEvent, handle_domain_log_event)
