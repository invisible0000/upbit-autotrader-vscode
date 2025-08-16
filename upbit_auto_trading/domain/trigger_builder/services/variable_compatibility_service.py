"""
Variable Compatibility Service
- 변수 간 호환성 검증 도메인 서비스
- 순수 도메인 로직, 외부 의존성 없음
"""
from typing import List, Set

from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable
from upbit_auto_trading.domain.trigger_builder.enums import ComparisonGroup, VariableCategory


class VariableCompatibilityService:
    """변수 호환성 검증 도메인 서비스"""

    def can_compare_variables(self, var1: TradingVariable, var2: TradingVariable) -> bool:
        """두 변수가 비교 가능한지 확인"""
        # 메타변수(dynamic_management)는 모든 변수와 호환됩니다
        if (var1.purpose_category.value == "dynamic_management" or
                var2.purpose_category.value == "dynamic_management"):
            return True

        return var1.can_compare_with(var2)

    def get_compatible_comparison_groups(self, group: ComparisonGroup) -> Set[ComparisonGroup]:
        """호환 가능한 비교 그룹들 반환"""
        compatibility_matrix = {
            ComparisonGroup.PRICE_COMPARABLE: {ComparisonGroup.PRICE_COMPARABLE},
            ComparisonGroup.PERCENTAGE_COMPARABLE: {ComparisonGroup.PERCENTAGE_COMPARABLE, ComparisonGroup.ZERO_CENTERED},
            ComparisonGroup.ZERO_CENTERED: {ComparisonGroup.ZERO_CENTERED, ComparisonGroup.PERCENTAGE_COMPARABLE},
            ComparisonGroup.VOLUME_COMPARABLE: {ComparisonGroup.VOLUME_COMPARABLE},
            ComparisonGroup.VOLATILITY_COMPARABLE: {ComparisonGroup.VOLATILITY_COMPARABLE},
            ComparisonGroup.CAPITAL_COMPARABLE: {ComparisonGroup.CAPITAL_COMPARABLE},
            ComparisonGroup.QUANTITY_COMPARABLE: {ComparisonGroup.QUANTITY_COMPARABLE},
            ComparisonGroup.SIGNAL_CONDITIONAL: {ComparisonGroup.SIGNAL_CONDITIONAL}
        }
        return compatibility_matrix.get(group, {group})

    def filter_compatible_variables(self, target_variable: TradingVariable,
                                    candidate_variables: List[TradingVariable]) -> List[TradingVariable]:
        """대상 변수와 호환 가능한 변수들만 필터링"""
        # 메타변수는 모든 변수와 호환됩니다
        if target_variable.purpose_category.value == "dynamic_management":
            return [
                var for var in candidate_variables
                if var.variable_id != target_variable.variable_id
            ]

        compatible_groups = self.get_compatible_comparison_groups(target_variable.comparison_group)

        return [
            var for var in candidate_variables
            if ((var.comparison_group in compatible_groups or
                 var.purpose_category.value == "dynamic_management") and
                var.variable_id != target_variable.variable_id)
        ]

    def get_recommended_variables_for_category(self, category: VariableCategory,
                                               variables: List[TradingVariable]) -> List[TradingVariable]:
        """카테고리별 추천 변수들 반환"""
        category_variables = [var for var in variables if var.purpose_category == category]

        # 카테고리별 우선순위 로직
        priority_map = {
            VariableCategory.TREND: ["SMA", "EMA", "BOLLINGER_BAND"],
            VariableCategory.MOMENTUM: ["RSI", "STOCHASTIC", "MACD"],
            VariableCategory.VOLATILITY: ["ATR", "BOLLINGER_BAND"],
            VariableCategory.VOLUME: ["VOLUME", "VOLUME_SMA"],
            VariableCategory.PRICE: ["CURRENT_PRICE", "HIGH_PRICE", "LOW_PRICE"],
            VariableCategory.CAPITAL: ["CASH_BALANCE", "TOTAL_BALANCE"],
            VariableCategory.STATE: ["PROFIT_PERCENT", "POSITION_SIZE"]
        }

        priority_ids = priority_map.get(category, [])

        # 우선순위에 따라 정렬
        sorted_variables = []
        for priority_id in priority_ids:
            for var in category_variables:
                if var.variable_id == priority_id:
                    sorted_variables.append(var)

        # 우선순위에 없는 변수들 추가
        remaining_variables = [var for var in category_variables if var not in sorted_variables]
        sorted_variables.extend(remaining_variables)

        return sorted_variables

    def validate_variable_combination(self, variables: List[TradingVariable]) -> bool:
        """변수 조합의 전체적인 유효성 검증"""
        if len(variables) < 2:
            return True  # 단일 변수는 항상 유효

        # 모든 변수가 활성화되어 있는지 확인
        if not all(var.is_active for var in variables):
            return False

        # 첫 번째 변수와 나머지 변수들의 호환성 확인
        base_variable = variables[0]
        for other_variable in variables[1:]:
            if not self.can_compare_variables(base_variable, other_variable):
                return False

        return True

    def get_incompatibility_reason(self, var1: TradingVariable, var2: TradingVariable) -> str:
        """호환되지 않는 이유를 문자열로 반환"""
        if var1.comparison_group != var2.comparison_group:
            compatible_groups = self.get_compatible_comparison_groups(var1.comparison_group)
            if var2.comparison_group not in compatible_groups:
                return f"비교 그룹이 호환되지 않습니다: {var1.comparison_group.value} vs {var2.comparison_group.value}"

        if not var1.is_active or not var2.is_active:
            return "비활성화된 변수가 포함되어 있습니다"

        return "알 수 없는 호환성 문제"
