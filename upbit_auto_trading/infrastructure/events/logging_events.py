"""
로깅 시스템을 위한 도메인 이벤트들
Event-Driven Architecture에서 로그 메시지를 이벤트로 처리
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent


class LogLevel(Enum):
    """로그 레벨 열거형"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogMessageEvent(DomainEvent):
    """로그 메시지 이벤트"""

    # 로그 메시지 관련 필드
    message: str
    level: LogLevel
    logger_name: str
    module_name: Optional[str] = None
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    thread_name: Optional[str] = None
    process_id: Optional[int] = None

    # 추가 컨텍스트
    tags: Dict[str, Any] = None
    extra_data: Dict[str, Any] = None

    def __post_init__(self):
        super().__init__()
        if self.tags is None:
            self.tags = {}
        if self.extra_data is None:
            self.extra_data = {}

        # 메타데이터에 로깅 정보 추가
        self.add_metadata("log_level", self.level.value)
        self.add_metadata("logger_name", self.logger_name)
        if self.module_name:
            self.add_metadata("module", self.module_name)
        if self.function_name:
            self.add_metadata("function", self.function_name)

    @property
    def event_type(self) -> str:
        return "logging.message"

    @property
    def aggregate_id(self) -> str:
        """로거명을 Aggregate ID로 사용"""
        return f"logger.{self.logger_name}"

    def _get_event_data(self) -> Dict[str, Any]:
        """이벤트별 고유 데이터"""
        return {
            "message": self.message,
            "level": self.level.value,
            "logger_name": self.logger_name,
            "module_name": self.module_name,
            "function_name": self.function_name,
            "line_number": self.line_number,
            "thread_name": self.thread_name,
            "process_id": self.process_id,
            "tags": self.tags,
            "extra_data": self.extra_data
        }


@dataclass
class LogConfigurationChangedEvent(DomainEvent):
    """로깅 구성 변경 이벤트"""

    configuration_section: str
    old_value: Any
    new_value: Any
    config_path: str

    def __post_init__(self):
        super().__init__()
        self.add_metadata("config_section", self.configuration_section)
        self.add_metadata("config_path", self.config_path)

    @property
    def event_type(self) -> str:
        return "logging.configuration_changed"

    @property
    def aggregate_id(self) -> str:
        return f"logging_config.{self.configuration_section}"

    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "configuration_section": self.configuration_section,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "config_path": self.config_path
        }


@dataclass
class EnvironmentVariableChangedEvent(DomainEvent):
    """환경 변수 변경 이벤트"""

    variable_name: str
    old_value: Optional[str]
    new_value: Optional[str]

    def __post_init__(self):
        super().__init__()
        self.add_metadata("variable_name", self.variable_name)
        self.add_metadata("change_type", self._get_change_type())

    @property
    def event_type(self) -> str:
        return "environment.variable_changed"

    @property
    def aggregate_id(self) -> str:
        return f"env_var.{self.variable_name}"

    def _get_change_type(self) -> str:
        """변경 타입 결정"""
        if self.old_value is None and self.new_value is not None:
            return "created"
        elif self.old_value is not None and self.new_value is None:
            return "deleted"
        else:
            return "updated"

    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "variable_name": self.variable_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_type": self._get_change_type()
        }


@dataclass
class LogViewerStateChangedEvent(DomainEvent):
    """로그 뷰어 상태 변경 이벤트"""

    viewer_id: str
    state_change: str
    previous_state: Optional[str] = None
    new_state: Optional[str] = None

    def __post_init__(self):
        super().__init__()
        self.add_metadata("viewer_id", self.viewer_id)
        self.add_metadata("state_change", self.state_change)

    @property
    def event_type(self) -> str:
        return "ui.log_viewer_state_changed"

    @property
    def aggregate_id(self) -> str:
        return f"log_viewer.{self.viewer_id}"

    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "viewer_id": self.viewer_id,
            "state_change": self.state_change,
            "previous_state": self.previous_state,
            "new_state": self.new_state
        }


@dataclass
class LogFilterChangedEvent(DomainEvent):
    """로그 필터 변경 이벤트"""

    filter_type: str  # level, logger, search_text, etc.
    filter_value: Any
    is_active: bool

    def __post_init__(self):
        super().__init__()
        self.add_metadata("filter_type", self.filter_type)
        self.add_metadata("is_active", self.is_active)

    @property
    def event_type(self) -> str:
        return "ui.log_filter_changed"

    @property
    def aggregate_id(self) -> str:
        return f"log_filter.{self.filter_type}"

    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "filter_type": self.filter_type,
            "filter_value": self.filter_value,
            "is_active": self.is_active
        }
