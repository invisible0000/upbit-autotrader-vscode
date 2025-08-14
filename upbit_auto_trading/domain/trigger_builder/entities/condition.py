"""
Condition Entity
- 거래 조건을 나타내는 도메인 엔티티
- 변수, 연산자, 비교값의 조합
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable
from upbit_auto_trading.domain.trigger_builder.value_objects.condition_value import ConditionValue
from upbit_auto_trading.domain.trigger_builder.enums import ConditionOperator, ConditionStatus
from upbit_auto_trading.domain.exceptions.validation_exceptions import ValidationError


@dataclass
class Condition:
    """거래 조건 엔티티"""
    condition_id: str
    variable: TradingVariable
    operator: ConditionOperator
    value: ConditionValue
    description: str
    status: ConditionStatus = ConditionStatus.VALID
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """생성 후 검증"""
        self._validate()

    def _validate(self):
        """엔티티 유효성 검증"""
        if not self.condition_id or not self.condition_id.strip():
            raise ValidationError("condition_id는 비어있을 수 없습니다")

        if not self.description or not self.description.strip():
            raise ValidationError("description은 비어있을 수 없습니다")

        # 변수의 필수 파라미터 검증
        self.variable.validate_required_parameters()

        # 변수 비교 시 호환성 검증
        if self.value.is_variable_comparison():
            comparison_variable = self.value.get_comparison_variable()
            if not self.variable.can_compare_with(comparison_variable):
                raise ValidationError("호환되지 않는 변수 비교입니다")

    def is_crossover_condition(self) -> bool:
        """크로스오버 조건인지 확인"""
        return self.operator in (ConditionOperator.CROSSOVER, ConditionOperator.CROSSUNDER)

    def is_simple_comparison(self) -> bool:
        """단순 비교 조건인지 확인"""
        return self.operator in (
            ConditionOperator.GREATER_THAN,
            ConditionOperator.LESS_THAN,
            ConditionOperator.GREATER_THAN_OR_EQUAL,
            ConditionOperator.LESS_THAN_OR_EQUAL,
            ConditionOperator.EQUAL,
            ConditionOperator.NOT_EQUAL
        )

    def evaluate(self, market_data: Dict[str, Any]) -> bool:
        """
        조건 평가 (현재는 모의 구현)
        실제로는 변수 계산 엔진과 연동되어야 함
        """
        try:
            # 변수값 가져오기
            variable_value = market_data.get(self.variable.variable_id)
            if variable_value is None:
                return False

            # 비교값 가져오기
            if self.value.is_constant():
                comparison_value = self.value.get_constant_value()
            else:
                # 변수 비교의 경우 - 실제로는 변수 계산 필요
                comparison_variable_id = self.value.get_comparison_variable_id()
                comparison_value = market_data.get(comparison_variable_id)
                if comparison_value is None:
                    return False

            # 연산자에 따른 비교
            if self.operator == ConditionOperator.GREATER_THAN:
                return variable_value > comparison_value
            elif self.operator == ConditionOperator.LESS_THAN:
                return variable_value < comparison_value
            elif self.operator == ConditionOperator.GREATER_THAN_OR_EQUAL:
                return variable_value >= comparison_value
            elif self.operator == ConditionOperator.LESS_THAN_OR_EQUAL:
                return variable_value <= comparison_value
            elif self.operator == ConditionOperator.EQUAL:
                return variable_value == comparison_value
            elif self.operator == ConditionOperator.NOT_EQUAL:
                return variable_value != comparison_value
            elif self.operator == ConditionOperator.CROSSOVER:
                # 크로스오버 로직 - 실제로는 이전 값과 비교 필요
                return variable_value > comparison_value
            elif self.operator == ConditionOperator.CROSSUNDER:
                # 크로스언더 로직 - 실제로는 이전 값과 비교 필요
                return variable_value < comparison_value

            return False

        except Exception:
            self.status = ConditionStatus.ERROR
            return False

    def get_description_text(self) -> str:
        """조건 설명 텍스트 생성"""
        variable_name = self.variable.get_display_name()
        operator_text = self._get_operator_text()
        value_text = self.value.get_display_text()

        return f"{variable_name} {operator_text} {value_text}"

    def _get_operator_text(self) -> str:
        """연산자 텍스트 반환"""
        operator_map = {
            ConditionOperator.GREATER_THAN: "보다 클 때",
            ConditionOperator.LESS_THAN: "보다 작을 때",
            ConditionOperator.GREATER_THAN_OR_EQUAL: "보다 크거나 같을 때",
            ConditionOperator.LESS_THAN_OR_EQUAL: "보다 작거나 같을 때",
            ConditionOperator.EQUAL: "와 같을 때",
            ConditionOperator.NOT_EQUAL: "와 다를 때",
            ConditionOperator.CROSSOVER: "을 상향 돌파할 때",
            ConditionOperator.CROSSUNDER: "을 하향 돌파할 때"
        }
        return operator_map.get(self.operator, self.operator.value)

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (직렬화용)"""
        return {
            "condition_id": self.condition_id,
            "variable": self.variable.to_dict(),
            "operator": self.operator.value,
            "value": self.value.to_dict(),
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
