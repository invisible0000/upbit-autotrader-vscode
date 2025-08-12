"""
전략 관련 도메인 이벤트
Strategy Aggregate와 관련된 모든 비즈니스 이벤트 정의

추적 가능한 기본값 설계:
- TODO_REQUIRED_FIELD: 나중에 필수 필드로 변경할 예정
- TEMP_DEFAULT: dataclass 제약으로 인한 임시 기본값
- VALID_DEFAULT: 의미있는 기본값
- OPTIONAL_FIELD: 진짜 선택적 필드
- TODO_VALIDATION: 나중에 구조 개선 시 제거할 임시 검증 로직
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from .base_domain_event import DomainEvent

@dataclass(frozen=True)
class StrategyCreated(DomainEvent):
    """전략 생성 이벤트"""
    # TODO_REQUIRED_FIELD: 나중에 필수 필드로 변경 예정
    strategy_id: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    strategy_name: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None

    # VALID_DEFAULT: 의미있는 기본값
    strategy_type: str = "entry"  # 'entry', 'management', 'combined'

    # OPTIONAL_FIELD: 진짜 선택적 필드
    creator_id: Optional[str] = None
    strategy_config: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "strategy.created"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id or "INVALID_STRATEGY_ID"

    def __post_init__(self):
        """이벤트 생성 후 필수 필드 검증"""
        super().__post_init__()

        # TODO_VALIDATION: 나중에 구조 개선 시 제거할 임시 검증 로직
        if not self.strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다 (현재 임시 None 기본값)")
        if not self.strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다 (현재 임시 None 기본값)")

@dataclass(frozen=True)
class StrategyUpdated(DomainEvent):
    """전략 수정 이벤트"""
    # TODO_REQUIRED_FIELD: 나중에 필수 필드로 변경 예정
    strategy_id: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    strategy_name: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None

    # VALID_DEFAULT: 의미있는 기본값
    updated_fields: Dict[str, Any] = field(default_factory=dict)

    # OPTIONAL_FIELD: 진짜 선택적 필드
    previous_version: Optional[str] = None
    new_version: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "strategy.updated"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id or "INVALID_STRATEGY_ID"

    def __post_init__(self):
        """이벤트 생성 후 필수 필드 검증"""
        super().__post_init__()

        # TODO_VALIDATION: 나중에 구조 개선 시 제거할 임시 검증 로직
        if not self.strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다 (현재 임시 None 기본값)")
        if not self.strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다 (현재 임시 None 기본값)")

@dataclass(frozen=True)
class StrategyDeleted(DomainEvent):
    """전략 삭제 이벤트"""
    # TODO_REQUIRED_FIELD: 나중에 필수 필드로 변경 예정
    strategy_id: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    strategy_name: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None

    # OPTIONAL_FIELD: 진짜 선택적 필드
    deleted_by: Optional[str] = None
    deletion_reason: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "strategy.deleted"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id or "INVALID_STRATEGY_ID"

    def __post_init__(self):
        """이벤트 생성 후 필수 필드 검증"""
        super().__post_init__()

        # TODO_VALIDATION: 나중에 구조 개선 시 제거할 임시 검증 로직
        if not self.strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다 (현재 임시 None 기본값)")
        if not self.strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다 (현재 임시 None 기본값)")

@dataclass(frozen=True)
class StrategyActivated(DomainEvent):
    """전략 활성화 이벤트"""
    # TODO_REQUIRED_FIELD: 나중에 필수 필드로 변경 예정
    strategy_id: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    strategy_name: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None

    # OPTIONAL_FIELD: 진짜 선택적 필드
    activated_by: Optional[str] = None
    activation_reason: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "strategy.activated"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id or "INVALID_STRATEGY_ID"

    def __post_init__(self):
        """이벤트 생성 후 필수 필드 검증"""
        super().__post_init__()

        # TODO_VALIDATION: 나중에 구조 개선 시 제거할 임시 검증 로직
        if not self.strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다 (현재 임시 None 기본값)")
        if not self.strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다 (현재 임시 None 기본값)")

@dataclass(frozen=True)
class StrategyDeactivated(DomainEvent):
    """전략 비활성화 이벤트"""
    # TODO_REQUIRED_FIELD: 나중에 필수 필드로 변경 예정
    strategy_id: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    strategy_name: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None

    # OPTIONAL_FIELD: 진짜 선택적 필드
    deactivated_by: Optional[str] = None
    deactivation_reason: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "strategy.deactivated"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id or "INVALID_STRATEGY_ID"

    def __post_init__(self):
        """이벤트 생성 후 필수 필드 검증"""
        super().__post_init__()

        # TODO_VALIDATION: 나중에 구조 개선 시 제거할 임시 검증 로직
        if not self.strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다 (현재 임시 None 기본값)")
        if not self.strategy_name:
            raise ValueError("strategy_name은 필수 필드입니다 (현재 임시 None 기본값)")

@dataclass(frozen=True)
class StrategyBacktestCompleted(DomainEvent):
    """전략 백테스트 완료 이벤트"""
    # TODO_REQUIRED_FIELD: 나중에 필수 필드로 변경 예정
    strategy_id: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    backtest_id: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    symbol: Optional[str] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None

    # TODO_REQUIRED_FIELD: 성능 지표들도 필수이지만 임시 기본값
    total_return: Optional[float] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    max_drawdown: Optional[float] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None
    sharpe_ratio: Optional[float] = None  # TEMP_DEFAULT: 필수값이지만 dataclass 제약으로 임시 None

    # VALID_DEFAULT: 의미있는 기본값
    win_rate: float = 0.0
    total_trades: int = 0
    completed_at: Optional[datetime] = field(default_factory=datetime.now)

    # OPTIONAL_FIELD: 진짜 선택적 필드
    additional_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "strategy.backtest.completed"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id or "INVALID_STRATEGY_ID"

    def __post_init__(self):
        """이벤트 생성 후 필수 필드 검증"""
        super().__post_init__()

        # TODO_VALIDATION: 나중에 구조 개선 시 제거할 임시 검증 로직
        if not self.strategy_id:
            raise ValueError("strategy_id는 필수 필드입니다 (현재 임시 None 기본값)")
        if not self.backtest_id:
            raise ValueError("backtest_id는 필수 필드입니다 (현재 임시 None 기본값)")
        if not self.symbol:
            raise ValueError("symbol은 필수 필드입니다 (현재 임시 None 기본값)")
        if self.total_return is None:
            raise ValueError("total_return은 필수 필드입니다 (현재 임시 None 기본값)")
        if self.max_drawdown is None:
            raise ValueError("max_drawdown는 필수 필드입니다 (현재 임시 None 기본값)")
        if self.sharpe_ratio is None:
            raise ValueError("sharpe_ratio는 필수 필드입니다 (현재 임시 None 기본값)")
