"""
트리거 및 신호 관련 도메인 이벤트
Trigger, Signal, Condition과 관련된 모든 비즈니스 이벤트 정의
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from . import DomainEvent


@dataclass(frozen=True)
class TriggerCreated(DomainEvent):
    """트리거 생성 이벤트"""
    # 필수 필드들 - 임시 기본값 (dataclass 제약으로 인한)
    trigger_id: str = ""  # 필수 필드
    trigger_name: str = ""  # 필수 필드
    strategy_id: str = ""  # 필수 필드
    trigger_conditions: List[Dict[str, Any]] = field(default_factory=list)  # 필수 필드
    logic_operator: str = "AND"  # 기본값
    created_by: Optional[str] = None  # 선택 필드

    def __post_init__(self):
        """필수 필드 검증"""
        if not self.trigger_id:
            raise ValueError("trigger_id는 필수 필드입니다")
        if not self.trigger_name:
            raise ValueError("trigger_name은 필수 필드입니다")
        if not self.strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다")

    @property
    def event_type(self) -> str:
        return "trigger.created"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id


@dataclass(frozen=True)
class TriggerUpdated(DomainEvent):
    """트리거 수정 이벤트"""
    trigger_id: str
    trigger_name: str
    updated_conditions: List[Dict[str, Any]]
    previous_conditions: List[Dict[str, Any]]
    logic_operator: str

    @property
    def event_type(self) -> str:
        return "trigger.updated"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id


@dataclass(frozen=True)
class TriggerDeleted(DomainEvent):
    """트리거 삭제 이벤트"""
    trigger_id: str
    trigger_name: str
    strategy_id: str
    deleted_by: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "trigger.deleted"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id


@dataclass(frozen=True)
class TriggerEvaluationStarted(DomainEvent):
    """트리거 평가 시작 이벤트"""
    trigger_id: str
    strategy_id: str
    symbol: str
    evaluation_timestamp: datetime
    market_data: Dict[str, Any]

    @property
    def event_type(self) -> str:
        return "trigger.evaluation.started"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id


@dataclass(frozen=True)
class TriggerEvaluationCompleted(DomainEvent):
    """트리거 평가 완료 이벤트"""
    trigger_id: str
    strategy_id: str
    symbol: str
    evaluation_result: bool
    triggered_conditions: List[str]
    failed_conditions: List[str]
    evaluation_duration_ms: float
    market_data_snapshot: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "trigger.evaluation.completed"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id


@dataclass(frozen=True)
class TriggerConditionMet(DomainEvent):
    """트리거 조건 만족 이벤트"""
    trigger_id: str
    condition_id: str
    condition_name: str
    symbol: str
    condition_value: Any
    threshold_value: Any
    operator: str  # '>', '<', '>=', '<=', '==', '!='

    @property
    def event_type(self) -> str:
        return "trigger.condition.met"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id


@dataclass(frozen=True)
class TradingSignalGenerated(DomainEvent):
    """매매 신호 생성 이벤트"""
    signal_id: str
    strategy_id: str
    trigger_id: Optional[str]
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD', 'ADD_BUY', 'CLOSE_POSITION'
    signal_strength: float  # 0.0 ~ 1.0
    price: float
    reason: str = ""
    quantity: Optional[float] = None
    confidence: float = 1.0
    technical_indicators: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "signal.generated"

    @property
    def aggregate_id(self) -> str:
        return self.signal_id


@dataclass(frozen=True)
class TradingSignalExecuted(DomainEvent):
    """매매 신호 실행 이벤트"""
    signal_id: str
    strategy_id: str
    symbol: str
    signal_type: str
    execution_price: float
    execution_quantity: float
    execution_timestamp: datetime
    execution_fee: float = 0.0
    order_id: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "signal.executed"

    @property
    def aggregate_id(self) -> str:
        return self.signal_id


@dataclass(frozen=True)
class TradingSignalRejected(DomainEvent):
    """매매 신호 거부 이벤트"""
    signal_id: str
    strategy_id: str
    symbol: str
    signal_type: str
    rejection_reason: str
    risk_check_results: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "signal.rejected"

    @property
    def aggregate_id(self) -> str:
        return self.signal_id


@dataclass(frozen=True)
class ConditionValidationCompleted(DomainEvent):
    """조건 검증 완료 이벤트"""
    condition_id: str
    variable_id: str
    validation_result: bool
    compatibility_checks: List[Dict[str, Any]]
    validation_errors: List[str] = field(default_factory=list)

    @property
    def event_type(self) -> str:
        return "condition.validation.completed"

    @property
    def aggregate_id(self) -> str:
        return self.condition_id


class TriggerEvaluatedEvent(DomainEvent):
    """트리거 평가 완료 이벤트"""

    def __init__(self, trigger_id: str, strategy_id: str, symbol: str,
                 evaluation_result: bool, evaluation_timestamp: datetime,
                 market_data: Optional[Dict[str, Any]] = None):
        super().__init__()  # DomainEvent 초기화
        self.trigger_id = trigger_id
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.evaluation_result = evaluation_result
        self.evaluation_timestamp = evaluation_timestamp
        self.market_data = market_data or {}

    @property
    def event_type(self) -> str:
        return "trigger.evaluated"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id


class TriggerActivatedEvent(DomainEvent):
    """트리거 활성화 이벤트"""

    def __init__(self, trigger_id: str, strategy_id: str, symbol: str,
                 activation_timestamp: datetime,
                 activation_conditions: Optional[List[str]] = None):
        super().__init__()  # DomainEvent 초기화
        self.trigger_id = trigger_id
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.activation_timestamp = activation_timestamp
        self.activation_conditions = activation_conditions or []

    @property
    def event_type(self) -> str:
        return "trigger.activated"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id


class TriggerEvaluationFailedEvent(DomainEvent):
    """트리거 평가 실패 이벤트"""

    def __init__(self, trigger_id: str, strategy_id: str, symbol: str,
                 error_message: str, evaluation_timestamp: datetime,
                 error_details: Optional[Dict[str, Any]] = None):
        super().__init__()  # DomainEvent 초기화
        self.trigger_id = trigger_id
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.error_message = error_message
        self.evaluation_timestamp = evaluation_timestamp
        self.error_details = error_details or {}

    @property
    def event_type(self) -> str:
        return "trigger.evaluation.failed"

    @property
    def aggregate_id(self) -> str:
        return self.trigger_id
