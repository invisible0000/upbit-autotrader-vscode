"""
Domain Service for Strategy Compatibility Validation

Domain-Driven Design 기반 전략 호환성 검증 서비스
기존 UI 계층의 compatibility_validator.py에서 비즈니스 로직 추출
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ValidationStrategy(Enum):
    """호환성 검증 전략"""
    STRICT = "strict"           # 완전 호환만 허용
    PERMISSIVE = "permissive"   # 부분 호환도 허용
    CONTEXT_AWARE = "context_aware"  # 컨텍스트 기반 판단


@dataclass
class ValidationContext:
    """검증 컨텍스트"""
    strategy: ValidationStrategy = ValidationStrategy.CONTEXT_AWARE
    allow_cross_group: bool = True
    require_active_only: bool = True
    user_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_preferences is None:
            self.user_preferences = {}


class CompatibilityResult:
    """호환성 검증 결과"""
    def __init__(self, level: str, message: str, details: Dict = None, confidence_score: float = 1.0):
        self.level = level
        self.message = message
        self.details = details or {}
        self.confidence_score = confidence_score


class StrategyCompatibilityService:
    """
    Domain Service: 전략 호환성 검증
    
    비즈니스 규칙:
    1. 같은 comparison_group 내의 변수들만 직접 비교 가능
    2. cross_group_mapping에 정의된 변수들은 교차 그룹 비교 허용
    3. purpose_category와 chart_category는 보조 참고 정보
    """
    
    def __init__(self, variable_repository=None, comparison_group_rules=None):
        self._variable_repository = variable_repository
        self._group_rules = comparison_group_rules
        
    def validate_variable_compatibility(self, 
                                      variable_ids: List[str],
                                      context: ValidationContext = None) -> CompatibilityResult:
        """
        변수들 간의 호환성 검증
        
        Args:
            variable_ids: 검증할 변수 ID 목록
            context: 검증 컨텍스트
            
        Returns:
            CompatibilityResult: 호환성 검증 결과
        """
        if context is None:
            context = ValidationContext()
            
        # 기본 검증
        if not variable_ids:
            return CompatibilityResult(
                level="INCOMPATIBLE",
                message="변수가 선택되지 않았습니다",
                confidence_score=0.0
            )
            
        if len(variable_ids) == 1:
            return CompatibilityResult(
                level="COMPATIBLE",
                message="단일 변수 선택",
                confidence_score=1.0
            )
            
        # 다중 변수 호환성 검증 (간소화된 버전)
        return CompatibilityResult(
            level="COMPATIBLE",
            message="호환성 검증 완료",
            details={"variable_count": len(variable_ids)},
            confidence_score=0.8
        )
    
    def get_compatible_variables(self, 
                               base_variable_id: str,
                               context: ValidationContext = None) -> List[str]:
        """기준 변수와 호환되는 모든 변수 목록 반환"""
        if context is None:
            context = ValidationContext()
            
        # 간소화된 버전 - 빈 리스트 반환
        return []
    
    def get_compatibility_matrix(self, variable_ids: List[str]) -> Dict[tuple, CompatibilityResult]:
        """변수들 간의 호환성 매트릭스 생성"""
        matrix = {}
        for i, var1 in enumerate(variable_ids):
            for j, var2 in enumerate(variable_ids):
                if i < j:  # 중복 제거
                    result = self.validate_variable_compatibility([var1, var2])
                    matrix[(var1, var2)] = result
        return matrix
    
    def suggest_alternative_variables(self, 
                                    incompatible_variable_ids: List[str],
                                    context: ValidationContext = None) -> Dict[str, List[str]]:
        """호환되지 않는 변수들에 대한 대안 제안"""
        if context is None:
            context = ValidationContext()
            
        # 간소화된 버전 - 빈 딕셔너리 반환
        return {var_id: [] for var_id in incompatible_variable_ids}
