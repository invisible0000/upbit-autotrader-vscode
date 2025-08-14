"""
Condition Preview Service
- 조건 미리보기 생성 도메인 서비스
"""
from typing import Dict, Any, List

from upbit_auto_trading.domain.trigger_builder.entities.condition import Condition
from upbit_auto_trading.domain.trigger_builder.enums import ConditionOperator


class ConditionPreviewService:
    """조건 미리보기 생성 도메인 서비스"""

    def generate_condition_preview(self, condition: Condition) -> Dict[str, Any]:
        """조건의 미리보기 정보 생성"""
        return {
            "condition_id": condition.condition_id,
            "description": condition.get_description_text(),
            "human_readable": self._generate_human_readable_text(condition),
            "technical_details": self._generate_technical_details(condition),
            "evaluation_example": self._generate_evaluation_example(condition),
            "status": condition.status.value
        }

    def _generate_human_readable_text(self, condition: Condition) -> str:
        """사람이 읽기 쉬운 조건 설명 생성"""
        variable_name = condition.variable.get_display_name("ko")
        operator_text = self._get_korean_operator_text(condition.operator)
        value_text = self._format_value_text(condition)

        return f"{variable_name}이(가) {value_text} {operator_text} 경우"

    def _generate_technical_details(self, condition: Condition) -> Dict[str, Any]:
        """기술적 세부사항 생성"""
        return {
            "variable_id": condition.variable.variable_id,
            "variable_category": condition.variable.purpose_category.value,
            "chart_category": condition.variable.chart_category.value,
            "comparison_group": condition.variable.comparison_group.value,
            "operator": condition.operator.value,
            "value_type": condition.value.value_type,
            "parameter_required": condition.variable.parameter_required,
            "parameters": [
                {
                    "name": p.parameter_name,
                    "type": p.parameter_type,
                    "default": p.default_value
                }
                for p in condition.variable.parameters
            ]
        }

    def _generate_evaluation_example(self, condition: Condition) -> Dict[str, Any]:
        """평가 예제 생성"""
        variable_id = condition.variable.variable_id

        # 변수별 예제 값 제공
        example_values = {
            "RSI": [25.0, 45.0, 75.0],
            "SMA": [50000, 52000, 48000],
            "EMA": [50500, 51500, 49500],
            "CURRENT_PRICE": [51000, 52000, 49000],
            "PROFIT_PERCENT": [-5.0, 0.0, 10.0],
            "VOLUME": [1000000, 2000000, 500000]
        }

        test_values = example_values.get(variable_id, [100, 200, 300])

        examples = []
        for value in test_values:
            mock_data = {variable_id: value}
            result = condition.evaluate(mock_data)
            examples.append({
                "input_value": value,
                "result": result,
                "explanation": f"{variable_id}={value} -> {result}"
            })

        return {
            "test_cases": examples,
            "comparison_value": condition.value.get_display_text()
        }

    def _get_korean_operator_text(self, operator: ConditionOperator) -> str:
        """연산자의 한국어 표현 반환"""
        korean_operators = {
            ConditionOperator.GREATER_THAN: "보다 클",
            ConditionOperator.LESS_THAN: "보다 작을",
            ConditionOperator.GREATER_THAN_OR_EQUAL: "보다 크거나 같을",
            ConditionOperator.LESS_THAN_OR_EQUAL: "보다 작거나 같을",
            ConditionOperator.EQUAL: "와 같을",
            ConditionOperator.NOT_EQUAL: "와 다를",
            ConditionOperator.CROSSOVER: "을 상향 돌파할",
            ConditionOperator.CROSSUNDER: "을 하향 돌파할"
        }
        return korean_operators.get(operator, operator.value)

    def _format_value_text(self, condition: Condition) -> str:
        """비교값의 포맷팅된 텍스트 반환"""
        if condition.value.is_constant():
            value = condition.value.get_constant_value()
            variable = condition.variable

            # 변수별 단위 추가
            if variable.variable_id in ["RSI", "STOCHASTIC"]:
                return f"{value}%"
            elif variable.variable_id in ["PROFIT_PERCENT"]:
                return f"{value}%"
            elif variable.comparison_group.value == "price_comparable":
                return f"{value:,}원"
            else:
                return str(value)
        else:
            return condition.value.get_display_text()

    def generate_multiple_conditions_preview(self, conditions: List[Condition]) -> Dict[str, Any]:
        """여러 조건들의 통합 미리보기 생성"""
        if not conditions:
            return {"conditions": [], "summary": "조건이 없습니다"}

        condition_previews = [
            self.generate_condition_preview(condition)
            for condition in conditions
        ]

        # 조건들의 요약 정보
        categories = set(c.variable.purpose_category.value for c in conditions)
        variable_ids = [c.variable.variable_id for c in conditions]

        return {
            "conditions": condition_previews,
            "summary": {
                "total_count": len(conditions),
                "categories": list(categories),
                "variables": variable_ids,
                "combined_description": self._generate_combined_description(conditions)
            }
        }

    def _generate_combined_description(self, conditions: List[Condition]) -> str:
        """여러 조건들의 통합 설명 생성"""
        if len(conditions) == 1:
            return conditions[0].get_description_text()

        descriptions = [condition.get_description_text() for condition in conditions]
        return " 그리고 ".join(descriptions)
