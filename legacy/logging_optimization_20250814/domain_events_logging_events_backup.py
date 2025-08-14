"""
Domain Events - 로깅 이벤트 정의
DDD 원칙에 따른 Domain Layer 로깅을 위한 이벤트들
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent


class LogLevel(Enum):
    """로그 레벨 - Domain Layer 표준"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class DomainLogRequested(DomainEvent):
    """
    Domain 로그 요청 이벤트

    Domain Layer에서 로깅이 필요할 때 발행되는 이벤트
    Infrastructure Layer에서 이 이벤트를 구독하여 실제 로깅을 수행
    """

    component_name: str
    """로그를 요청하는 컴포넌트명"""

    log_level: LogLevel
    """로그 레벨"""

    message: str
    """로그 메시지"""

    context_data: Optional[Dict[str, Any]] = None
    """추가 컨텍스트 데이터"""

    exception_info: Optional[str] = None
    """예외 정보 (에러 로그인 경우)"""

    @property
    def event_type(self) -> str:
        return "DomainLogRequested"

    @property
    def aggregate_id(self) -> str:
        return f"logging:{self.component_name}"

    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class DomainComponentInitialized(DomainEvent):
    """
    Domain 컴포넌트 초기화 완료 이벤트

    Domain Service나 Entity가 초기화될 때 발행
    """

    component_name: str
    """초기화된 컴포넌트명"""

    component_type: str
    """컴포넌트 타입 (Service, Entity, ValueObject 등)"""

    initialization_context: Optional[Dict[str, Any]] = None
    """초기화 컨텍스트"""

    @property
    def event_type(self) -> str:
        return "DomainComponentInitialized"

    @property
    def aggregate_id(self) -> str:
        return f"component:{self.component_name}"

    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class DomainOperationStarted(DomainEvent):
    """
    Domain 작업 시작 이벤트

    중요한 Domain 작업이 시작될 때 발행
    """

    component_name: str
    """작업을 수행하는 컴포넌트명"""

    operation_name: str
    """작업명"""

    operation_parameters: Optional[Dict[str, Any]] = None
    """작업 파라미터"""

    @property
    def event_type(self) -> str:
        return "DomainOperationStarted"

    @property
    def aggregate_id(self) -> str:
        return f"operation:{self.component_name}:{self.operation_name}"

    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class DomainOperationCompleted(DomainEvent):
    """
    Domain 작업 완료 이벤트

    중요한 Domain 작업이 완료될 때 발행
    """

    component_name: str
    """작업을 수행한 컴포넌트명"""

    operation_name: str
    """작업명"""

    execution_time_ms: Optional[float] = None
    """실행 시간 (밀리초)"""

    result_summary: Optional[str] = None
    """결과 요약"""

    @property
    def event_type(self) -> str:
        return "DomainOperationCompleted"

    @property
    def aggregate_id(self) -> str:
        return f"operation:{self.component_name}:{self.operation_name}"

    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class DomainErrorOccurred(DomainEvent):
    """
    Domain 오류 발생 이벤트

    Domain Layer에서 오류가 발생했을 때 발행
    """

    component_name: str
    """오류가 발생한 컴포넌트명"""

    error_type: str
    """오류 타입"""

    error_message: str
    """오류 메시지"""

    error_context: Optional[Dict[str, Any]] = None
    """오류 발생 컨텍스트"""

    stack_trace: Optional[str] = None
    """스택 트레이스"""

    @property
    def event_type(self) -> str:
        return "DomainErrorOccurred"

    @property
    def aggregate_id(self) -> str:
        return f"error:{self.component_name}"

    def __post_init__(self):
        super().__post_init__()
