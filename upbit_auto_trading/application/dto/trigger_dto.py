"""
Trigger DTO - 트리거 관련 데이터 전송 객체들
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass(frozen=True)
class CreateTriggerDto:
    """트리거 생성 요청 DTO"""
    strategy_id: str
    variable_id: str
    variable_params: Dict[str, Any]
    operator: str
    target_value: Any
    trigger_type: str  # ENTRY, EXIT
    trigger_name: Optional[str] = None


@dataclass(frozen=True)
class TriggerDto:
    """트리거 응답 DTO"""
    trigger_id: str
    strategy_id: str
    trigger_name: str
    variable_id: str
    variable_params: Dict[str, Any]
    operator: str
    target_value: Any
    trigger_type: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_entity(cls, trigger) -> 'TriggerDto':
        """도메인 엔티티에서 DTO 생성

        Args:
            trigger: Trigger 도메인 엔티티

        Returns:
            TriggerDto: 엔티티 데이터로 생성된 DTO
        """
        return cls(
            trigger_id=trigger.trigger_id.value,
            strategy_id=trigger.strategy_id.value if trigger.strategy_id else "",
            trigger_name=trigger.trigger_name or "",
            variable_id=trigger.variable.variable_id,
            variable_params=trigger.variable.parameters,
            operator=trigger.operator.value if hasattr(trigger.operator, 'value') else str(trigger.operator),
            target_value=trigger.target_value,
            trigger_type=trigger.trigger_type.value if hasattr(trigger.trigger_type, 'value') else str(trigger.trigger_type),
            is_active=trigger.is_active,
            created_at=trigger.created_at
        )
