"""
Condition Validation Service
- 조건 유효성 검증 도메인 서비스
"""
from typing import List, Dict, Any

from upbit_auto_trading.domain.trigger_builder.entities.condition import Condition
from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable
from upbit_auto_trading.domain.trigger_builder.enums import ConditionOperator, VariableCategory, ComparisonGroup
from upbit_auto_trading.domain.trigger_builder.services.variable_compatibility_service import VariableCompatibilityService
from upbit_auto_trading.domain.exceptions.validation_exceptions import ValidationError


class ConditionValidationService:
    """조건 유효성 검증 도메인 서비스"""

    def __init__(self):
        self.compatibility_service = VariableCompatibilityService()

    def validate_condition(self, condition: Condition) -> bool:
        """조건 전체 유효성 검증"""
        try:
            # 기본 엔티티 검증 (이미 __post_init__에서 수행됨)
            # 추가 비즈니스 로직 검증
            self._validate_operator_compatibility(condition)
            self._validate_value_range(condition)
            self._validate_business_rules(condition)
            return True
        except ValidationError:
            return False

    def _validate_operator_compatibility(self, condition: Condition) -> None:
        """연산자와 변수 타입 호환성 검증"""
        variable = condition.variable
        operator = condition.operator

        # 크로스오버/크로스언더는 변수 비교에서만 사용 가능
        if operator in (ConditionOperator.CROSSOVER, ConditionOperator.CROSSUNDER):
            if condition.value.is_constant():
                raise ValidationError("크로스오버/크로스언더는 변수 비교에서만 사용할 수 있습니다")

        # 백분율 변수에 대한 상수값 범위 검증
        if (variable.comparison_group == ComparisonGroup.PERCENTAGE_COMPARABLE and
                condition.value.is_constant()):
            constant_value = condition.value.get_constant_value()
            if isinstance(constant_value, (int, float)) and not (0 <= constant_value <= 100):
                raise ValidationError("백분율 변수의 비교값은 0-100 범위여야 합니다")

    def _validate_value_range(self, condition: Condition) -> None:
        """값 범위 검증"""
        if not condition.value.is_constant():
            return

        constant_value = condition.value.get_constant_value()
        variable = condition.variable

        # 변수별 특별 범위 검증
        range_rules = {
            "RSI": (0, 100),
            "STOCHASTIC": (0, 100),
            "PROFIT_PERCENT": (-100, 1000)  # -100% ~ 1000% 수익률
        }

        if variable.variable_id in range_rules:
            min_val, max_val = range_rules[variable.variable_id]
            if isinstance(constant_value, (int, float)):
                if not (min_val <= constant_value <= max_val):
                    raise ValidationError(
                        f"{variable.variable_id}의 값은 {min_val}~{max_val} 범위여야 합니다"
                    )

    def _validate_business_rules(self, condition: Condition) -> None:
        """비즈니스 규칙 검증"""
        variable = condition.variable

        # RSI 과매도/과매수 일반적 범위 경고
        if variable.variable_id == "RSI" and condition.value.is_constant():
            rsi_value = condition.value.get_constant_value()
            if isinstance(rsi_value, (int, float)):
                if condition.operator == ConditionOperator.LESS_THAN and rsi_value > 50:
                    # 경고 수준이므로 예외를 발생시키지 않고 로그만 기록
                    pass
                elif condition.operator == ConditionOperator.GREATER_THAN and rsi_value < 50:
                    pass

    def get_suggested_operators(self, variable: TradingVariable) -> List[ConditionOperator]:
        """변수에 적합한 연산자 제안"""
        # 변수 카테고리별 추천 연산자
        category_operators = {
            VariableCategory.MOMENTUM: [
                ConditionOperator.LESS_THAN,
                ConditionOperator.GREATER_THAN,
                ConditionOperator.LESS_THAN_OR_EQUAL,
                ConditionOperator.GREATER_THAN_OR_EQUAL
            ],
            VariableCategory.TREND: [
                ConditionOperator.GREATER_THAN,
                ConditionOperator.LESS_THAN,
                ConditionOperator.CROSSOVER,
                ConditionOperator.CROSSUNDER
            ],
            VariableCategory.PRICE: [
                ConditionOperator.GREATER_THAN,
                ConditionOperator.LESS_THAN,
                ConditionOperator.GREATER_THAN_OR_EQUAL,
                ConditionOperator.LESS_THAN_OR_EQUAL
            ]
        }

        return category_operators.get(variable.purpose_category, list(ConditionOperator))

    def get_suggested_values(self, variable: TradingVariable) -> Dict[str, Any]:
        """변수에 적합한 비교값 제안"""
        suggestions = {
            "RSI": {
                "oversold": 30,
                "overbought": 70,
                "common_values": [20, 25, 30, 70, 75, 80]
            },
            "STOCHASTIC": {
                "oversold": 20,
                "overbought": 80,
                "common_values": [15, 20, 25, 75, 80, 85]
            },
            "PROFIT_PERCENT": {
                "take_profit": [5, 10, 15, 20],
                "stop_loss": [-3, -5, -10, -15],
                "rebalance": [2, 3, 5]
            }
        }

        return suggestions.get(variable.variable_id, {})

    def validate_condition_combination(self, conditions: List[Condition]) -> bool:
        """여러 조건의 조합 유효성 검증"""
        if len(conditions) <= 1:
            return True

        # 중복 변수 검사
        variable_ids = [c.variable.variable_id for c in conditions]
        if len(variable_ids) != len(set(variable_ids)):
            return False  # 중복 변수 있음

        # 상충하는 조건 검사 (같은 변수에 대한 모순된 조건)
        return self._check_contradictory_conditions(conditions)

    def _check_contradictory_conditions(self, conditions: List[Condition]) -> bool:
        """상충하는 조건이 있는지 검사"""
        # 간단한 예시: RSI > 70 AND RSI < 30 같은 모순 검사
        # 실제로는 더 복잡한 로직이 필요

        for i, condition1 in enumerate(conditions):
            for condition2 in conditions[i + 1:]:
                if (condition1.variable.variable_id == condition2.variable.variable_id and
                        condition1.value.is_constant() and condition2.value.is_constant()):

                    val1 = condition1.value.get_constant_value()
                    val2 = condition2.value.get_constant_value()
                    op1 = condition1.operator
                    op2 = condition2.operator

                    # 명백한 모순 검사
                    if (op1 == ConditionOperator.GREATER_THAN and
                            op2 == ConditionOperator.LESS_THAN and
                            isinstance(val1, (int, float)) and isinstance(val2, (int, float)) and
                            val1 >= val2):
                        return False

        return True
