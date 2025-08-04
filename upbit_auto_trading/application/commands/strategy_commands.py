"""
Strategy Commands - 전략 관련 명령 객체들

Command 패턴을 구현하여 입력 데이터 검증과 비즈니스 규칙을 캡슐화합니다.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CreateStrategyCommand:
    """전략 생성 명령"""
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: str = "system"

    def validate(self) -> List[str]:
        """명령 유효성 검증

        Returns:
            List[str]: 검증 오류 메시지들 (빈 리스트면 검증 통과)
        """
        errors = []
        if not self.name or len(self.name.strip()) == 0:
            errors.append("전략 이름은 필수입니다")
        if len(self.name) > 100:
            errors.append("전략 이름은 100자를 초과할 수 없습니다")
        return errors


@dataclass(frozen=True)
class UpdateStrategyCommand:
    """전략 수정 명령"""
    strategy_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    updated_by: str = "system"

    def validate(self) -> List[str]:
        """명령 유효성 검증

        Returns:
            List[str]: 검증 오류 메시지들
        """
        errors = []
        if not self.strategy_id:
            errors.append("전략 ID는 필수입니다")
        if self.name is not None and len(self.name) > 100:
            errors.append("전략 이름은 100자를 초과할 수 없습니다")
        return errors


@dataclass(frozen=True)
class DeleteStrategyCommand:
    """전략 삭제 명령"""
    strategy_id: str
    soft_delete: bool = True
    deleted_by: str = "system"

    def validate(self) -> List[str]:
        """명령 유효성 검증

        Returns:
            List[str]: 검증 오류 메시지들
        """
        errors = []
        if not self.strategy_id:
            errors.append("전략 ID는 필수입니다")
        return errors
