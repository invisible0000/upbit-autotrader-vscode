"""
Condition Validation Repository Interface
- 조건 호환성 및 검증 데이터를 위한 Repository 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from upbit_auto_trading.domain.trigger_builder.enums import ComparisonGroup, VariableCategory


class IConditionValidationRepository(ABC):
    """조건 검증 Repository 인터페이스"""

    @abstractmethod
    async def get_compatibility_rules(self) -> Dict[str, Any]:
        """호환성 규칙 조회"""
        pass

    @abstractmethod
    async def get_comparison_group_rules(self, group: ComparisonGroup) -> Dict[str, Any]:
        """비교 그룹별 규칙 조회"""
        pass

    @abstractmethod
    async def get_variable_category_rules(self, category: VariableCategory) -> Dict[str, Any]:
        """변수 카테고리별 규칙 조회"""
        pass

    @abstractmethod
    async def get_operator_compatibility(self, variable_id: str) -> List[str]:
        """변수별 사용 가능한 연산자 조회"""
        pass

    @abstractmethod
    async def validate_variable_combination(self, variable1_id: str, variable2_id: str) -> bool:
        """변수 조합 검증"""
        pass

    @abstractmethod
    async def get_parameter_constraints(self, variable_id: str) -> Dict[str, Any]:
        """변수별 파라미터 제약조건 조회"""
        pass

    @abstractmethod
    async def log_validation_result(self, validation_data: Dict[str, Any]) -> bool:
        """검증 결과 로깅"""
        pass
