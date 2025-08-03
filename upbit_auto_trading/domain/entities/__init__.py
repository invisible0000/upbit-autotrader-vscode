"""
도메인 엔티티 (Domain Entities)

비즈니스의 핵심 개념들을 모델링한 엔티티들입니다.
각 엔티티는 고유한 식별자를 가지며, 생명주기 동안 상태 변경이 가능합니다.

주요 엔티티:
- Strategy: 매매 전략
- Trigger: 조건/트리거
- ManagementRule: 관리 규칙
"""

from .strategy import Strategy, InvalidStrategyConfigurationError, IncompatibleStrategyError
from .trigger import (
    Trigger,
    TriggerType,
    TradingVariable,
    TriggerEvaluationResult,
    create_rsi_entry_trigger,
    create_sma_crossover_trigger
)
from .management_rule import (
    ManagementRule,
    ManagementType,
    PositionState,
    ManagementExecutionResult,
    InvalidManagementRuleError,
    IncompatiblePositionStateError,
    create_pyramid_buying_rule,
    create_scale_in_buying_rule,
    create_trailing_stop_rule,
    create_fixed_stop_take_rule
)

__all__ = [
    "Strategy",
    "InvalidStrategyConfigurationError",
    "IncompatibleStrategyError",
    
    # Trigger 도메인 엔티티 및 관련 클래스
    "Trigger",
    "TriggerType",
    "TradingVariable",
    "TriggerEvaluationResult",
    
    # Trigger 팩토리 함수들
    "create_rsi_entry_trigger",
    "create_sma_crossover_trigger",
    
    # ManagementRule 도메인 엔티티 및 관련 클래스
    "ManagementRule",
    "ManagementType",
    "PositionState",
    "ManagementExecutionResult",
    "InvalidManagementRuleError",
    "IncompatiblePositionStateError",
    
    # ManagementRule 팩토리 함수들
    "create_pyramid_buying_rule",
    "create_scale_in_buying_rule",
    "create_trailing_stop_rule",
    "create_fixed_stop_take_rule"
]
