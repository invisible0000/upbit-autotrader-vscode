"""
Strategy DTO - 전략 관련 데이터 전송 객체들

Application Layer와 다른 계층 간의 데이터 전송을 위한 DTO들을 정의합니다.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass(frozen=True)
class CreateStrategyDto:
    """전략 생성 요청 DTO"""
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: str = "system"

@dataclass(frozen=True)
class StrategyDto:
    """전략 응답 DTO"""
    strategy_id: str
    name: str
    description: Optional[str]
    tags: List[str]
    status: str
    entry_triggers_count: int
    exit_triggers_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, strategy) -> 'StrategyDto':
        """도메인 엔티티에서 DTO 생성

        Args:
            strategy: Strategy 도메인 엔티티

        Returns:
            StrategyDto: 엔티티 데이터로 생성된 DTO
        """
        return cls(
            strategy_id=strategy.strategy_id.value,
            name=strategy.name,
            description=strategy.description,
            tags=strategy.tags or [],
            status=strategy.status.value if hasattr(strategy.status, 'value') else str(strategy.status),
            entry_triggers_count=len(getattr(strategy, 'entry_triggers', [])),
            exit_triggers_count=len(getattr(strategy, 'exit_triggers', [])),
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )

@dataclass(frozen=True)
class UpdateStrategyDto:
    """전략 수정 요청 DTO"""
    strategy_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    updated_by: str = "system"
