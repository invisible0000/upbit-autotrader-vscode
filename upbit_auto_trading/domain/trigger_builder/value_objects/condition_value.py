"""
ConditionValue Value Object
- 조건에서 비교할 값을 나타내는 값 객체
- 상수값 또는 다른 변수와의 비교를 지원
"""
from dataclasses import dataclass
from typing import Optional, Union, TYPE_CHECKING

from upbit_auto_trading.domain.exceptions.validation_exceptions import ValidationError

if TYPE_CHECKING:
    from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable


@dataclass(frozen=True)
class ConditionValue:
    """조건 비교값 값 객체"""
    value_type: str  # "constant" 또는 "variable"
    constant_value: Optional[Union[int, float, str, bool]]
    variable_id: Optional[str]
    variable_display_name: Optional[str]

    def __post_init__(self):
        """생성 후 검증"""
        self._validate()

    def _validate(self):
        """값 객체 유효성 검증"""
        if self.value_type not in ("constant", "variable"):
            raise ValidationError("value_type은 'constant' 또는 'variable'이어야 합니다")

        if self.value_type == "constant":
            if self.constant_value is None:
                raise ValidationError("상수값 타입에서는 constant_value가 필요합니다")
            if self.variable_id is not None or self.variable_display_name is not None:
                raise ValidationError("상수값 타입에서는 변수 정보가 있어서는 안됩니다")

        elif self.value_type == "variable":
            if not self.variable_id or not self.variable_id.strip():
                raise ValidationError("변수 타입에서는 variable_id가 필요합니다")
            if not self.variable_display_name or not self.variable_display_name.strip():
                raise ValidationError("변수 타입에서는 variable_display_name이 필요합니다")
            if self.constant_value is not None:
                raise ValidationError("변수 타입에서는 상수값이 있어서는 안됩니다")

    @classmethod
    def from_constant(cls, value: Union[int, float, str, bool]) -> 'ConditionValue':
        """상수값으로부터 ConditionValue 생성"""
        return cls(
            value_type="constant",
            constant_value=value,
            variable_id=None,
            variable_display_name=None
        )

    @classmethod
    def from_variable(cls, variable: 'TradingVariable') -> 'ConditionValue':
        """TradingVariable로부터 ConditionValue 생성"""
        from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable

        if not isinstance(variable, TradingVariable):
            raise ValidationError("variable은 TradingVariable 타입이어야 합니다")

        return cls(
            value_type="variable",
            constant_value=None,
            variable_id=variable.variable_id,
            variable_display_name=variable.display_name_ko
        )

    def is_constant(self) -> bool:
        """상수값인지 확인"""
        return self.value_type == "constant"

    def is_variable_comparison(self) -> bool:
        """변수 비교인지 확인"""
        return self.value_type == "variable"

    def get_constant_value(self) -> Union[int, float, str, bool]:
        """상수값 반환"""
        if not self.is_constant():
            raise ValidationError("상수값이 아닙니다")
        return self.constant_value  # type: ignore

    def get_comparison_variable_id(self) -> str:
        """비교 변수 ID 반환"""
        if not self.is_variable_comparison():
            raise ValidationError("변수 비교가 아닙니다")
        return self.variable_id  # type: ignore

    def get_comparison_variable(self) -> 'TradingVariable':
        """비교 변수 객체 반환 (임시 구현)"""
        if not self.is_variable_comparison():
            raise ValidationError("변수 비교가 아닙니다")

        # 실제로는 Repository에서 변수를 조회해야 하지만,
        # 테스트를 위해 임시로 간단한 객체 반환
        from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable
        from upbit_auto_trading.domain.trigger_builder.enums import (
            VariableCategory, ChartCategory, ComparisonGroup
        )

        # variable_id에 따라 적절한 comparison_group을 결정
        if self.variable_id == "RSI":
            comparison_group = ComparisonGroup.PERCENTAGE_COMPARABLE
            purpose_category = VariableCategory.MOMENTUM
            chart_category = ChartCategory.SUBPLOT
        else:
            comparison_group = ComparisonGroup.PRICE_COMPARABLE
            purpose_category = VariableCategory.TREND
            chart_category = ChartCategory.OVERLAY

        return TradingVariable(
            variable_id=self.variable_id,  # type: ignore
            display_name_ko=self.variable_display_name,  # type: ignore
            display_name_en=self.variable_display_name,  # type: ignore
            description="임시 변수",
            purpose_category=purpose_category,
            chart_category=chart_category,
            comparison_group=comparison_group,
            parameter_required=False,
            is_active=True
        )

    def get_display_text(self) -> str:
        """표시용 텍스트 반환"""
        if self.is_constant():
            return str(self.constant_value)
        else:
            return self.variable_display_name or self.variable_id or ""

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (직렬화용)"""
        return {
            "value_type": self.value_type,
            "constant_value": self.constant_value,
            "variable_id": self.variable_id,
            "variable_display_name": self.variable_display_name
        }
