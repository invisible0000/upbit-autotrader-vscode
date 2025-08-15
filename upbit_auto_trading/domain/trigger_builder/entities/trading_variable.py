"""
TradingVariable Entity
- 트레이딩 변수/지표를 나타내는 도메인 엔티티
- 파라미터 관리 및 호환성 검증 로직 포함
- 통합 파라미터 지원 (동적 관리 전략용)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Union

from upbit_auto_trading.domain.trigger_builder.enums import (
    VariableCategory, ChartCategory, ComparisonGroup
)
from upbit_auto_trading.domain.trigger_builder.value_objects.variable_parameter import VariableParameter
from upbit_auto_trading.domain.trigger_builder.value_objects.unified_parameter import UnifiedParameter
from upbit_auto_trading.domain.trigger_builder.value_objects.change_detection_parameter import ChangeDetectionParameter
from upbit_auto_trading.domain.exceptions.validation_exceptions import ValidationError


@dataclass
class TradingVariable:
    """트레이딩 변수 엔티티"""
    variable_id: str
    display_name_ko: str
    display_name_en: str
    description: str
    purpose_category: VariableCategory
    chart_category: ChartCategory
    comparison_group: ComparisonGroup
    parameter_required: bool
    is_active: bool
    source: str = "built-in"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    parameters: List[VariableParameter] = field(default_factory=list)
    unified_parameters: List[UnifiedParameter] = field(default_factory=list)
    change_detection_parameters: List[ChangeDetectionParameter] = field(default_factory=list)

    def __post_init__(self):
        """생성 후 검증"""
        self._validate()

    def _validate(self):
        """엔티티 유효성 검증"""
        if not self.variable_id or not self.variable_id.strip():
            raise ValidationError("variable_id는 비어있을 수 없습니다")

        if not self.display_name_ko or not self.display_name_ko.strip():
            raise ValidationError("display_name_ko는 비어있을 수 없습니다")

        if not self.display_name_en or not self.display_name_en.strip():
            raise ValidationError("display_name_en은 비어있을 수 없습니다")

        if not self.description or not self.description.strip():
            raise ValidationError("description은 비어있을 수 없습니다")

    def add_parameter(self, parameter: VariableParameter) -> None:
        """파라미터 추가"""
        # 중복 파라미터 체크
        if any(p.parameter_name == parameter.parameter_name for p in self.parameters):
            raise ValidationError(f"파라미터 '{parameter.parameter_name}'는 이미 존재합니다")

        self.parameters.append(parameter)
        self.updated_at = datetime.now()

    def add_unified_parameter(self, parameter: UnifiedParameter) -> None:
        """통합 파라미터 추가 (동적 관리 전략용)"""
        # 중복 파라미터 체크
        if any(p.name == parameter.name for p in self.unified_parameters):
            raise ValidationError(f"통합 파라미터 '{parameter.name}'는 이미 존재합니다")

        self.unified_parameters.append(parameter)
        self.updated_at = datetime.now()

    def remove_parameter(self, parameter_name: str) -> None:
        """파라미터 제거"""
        self.parameters = [p for p in self.parameters if p.parameter_name != parameter_name]
        self.updated_at = datetime.now()

    def remove_unified_parameter(self, parameter_name: str) -> None:
        """통합 파라미터 제거"""
        self.unified_parameters = [p for p in self.unified_parameters if p.name != parameter_name]
        self.updated_at = datetime.now()

    def add_change_detection_parameter(self, parameter: ChangeDetectionParameter) -> None:
        """변화 감지 파라미터 추가 (메타 변수용)"""
        # 중복 파라미터 체크
        if any(p.name == parameter.name for p in self.change_detection_parameters):
            raise ValidationError(f"변화 감지 파라미터 '{parameter.name}'는 이미 존재합니다")

        self.change_detection_parameters.append(parameter)
        self.updated_at = datetime.now()

    def remove_change_detection_parameter(self, parameter_name: str) -> None:
        """변화 감지 파라미터 제거"""
        self.change_detection_parameters = [p for p in self.change_detection_parameters if p.name != parameter_name]
        self.updated_at = datetime.now()

    def get_change_detection_parameter(self, parameter_name: str) -> Optional[ChangeDetectionParameter]:
        """변화 감지 파라미터 조회"""
        for parameter in self.change_detection_parameters:
            if parameter.name == parameter_name:
                return parameter
        return None

    def get_parameter(self, parameter_name: str) -> Optional[VariableParameter]:
        """파라미터 조회"""
        for parameter in self.parameters:
            if parameter.parameter_name == parameter_name:
                return parameter
        return None

    def get_unified_parameter(self, parameter_name: str) -> Optional[UnifiedParameter]:
        """통합 파라미터 조회"""
        for parameter in self.unified_parameters:
            if parameter.name == parameter_name:
                return parameter
        return None

    def validate_required_parameters(self) -> None:
        """필수 파라미터 검증 (확장)"""
        if self.parameter_required:
            has_parameters = (
                len(self.parameters) > 0
                or len(self.unified_parameters) > 0
                or len(self.change_detection_parameters) > 0
            )
            if not has_parameters:
                raise ValidationError(f"변수 '{self.variable_id}'는 파라미터가 필요합니다")

    def is_meta_variable(self) -> bool:
        """메타 변수인지 확인 (META_ 접두사)"""
        return self.variable_id.startswith("META_")

    def is_dynamic_management_variable(self) -> bool:
        """동적 관리 변수인지 확인"""
        return self.purpose_category == VariableCategory.DYNAMIC_MANAGEMENT

    def is_change_detection_variable(self) -> bool:
        """변화 감지 변수인지 확인"""
        return len(self.change_detection_parameters) > 0 or self.is_meta_variable()

    def can_compare_with(self, other: 'TradingVariable') -> bool:
        """다른 변수와 비교 가능한지 확인"""
        return self.comparison_group == other.comparison_group

    def is_compatible_with(self, other: 'TradingVariable') -> bool:
        """다른 변수와 호환 가능한지 확인 (더 넓은 개념)"""
        # 동일한 comparison_group이면 호환 가능
        if self.comparison_group == other.comparison_group:
            return True

        # 특별 호환성 규칙 (예: 가격과 백분율은 특정 조건에서 호환)
        # 필요에 따라 확장 가능
        return False

    def get_display_name(self, language: str = "ko") -> str:
        """언어별 표시명 반환"""
        if language == "en":
            return self.display_name_en
        return self.display_name_ko

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (직렬화용)"""
        return {
            "variable_id": self.variable_id,
            "display_name_ko": self.display_name_ko,
            "display_name_en": self.display_name_en,
            "description": self.description,
            "purpose_category": self.purpose_category.value,
            "chart_category": self.chart_category.value,
            "comparison_group": self.comparison_group.value,
            "parameter_required": self.parameter_required,
            "is_active": self.is_active,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "parameters": [
                {
                    "parameter_name": p.parameter_name,
                    "display_name_ko": p.display_name_ko,
                    "display_name_en": p.display_name_en,
                    "parameter_type": p.parameter_type,
                    "default_value": p.default_value,
                    "min_value": p.min_value,
                    "max_value": p.max_value,
                    "description": p.description
                }
                for p in self.parameters
            ]
        }
