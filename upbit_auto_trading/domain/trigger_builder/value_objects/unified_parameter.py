"""
통합 파라미터 Value Object
- 동적 관리 전략(불타기, 물타기, 트레일링 스탑)을 위한 통합 파라미터 구조
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Any
from ..enums import CalculationMethod, BaseVariable, TrailDirection, ResetTrigger


@dataclass(frozen=True)
class UnifiedParameter:
    """
    통합 파라미터 - 외부 제어형 상태 변수용 (확장형)

    동적 관리 전략에서 사용되는 파라미터의 통합 구조:
    - 불타기: 목표가 계산을 위한 base_variable + calculation_method
    - 물타기: 추가 매수 기준을 위한 base_variable + calculation_method
    - 트레일링 스탑: 추적 방향과 계산 방식 조합 + 초기화 트리거
    """
    name: str                                    # 파라미터 이름
    calculation_method: CalculationMethod        # 계산 방식 (확장됨)
    base_variable: BaseVariable                  # 기준값 타입
    value: Decimal                              # 계산에 사용될 값 (퍼센트, 원화 등)
    trail_direction: Optional[TrailDirection] = None      # 트레일링 방향 (양방향 지원)
    reset_trigger: Optional[ResetTrigger] = None          # 초기화 트리거 (신규)
    tracking_variable: Optional[str] = None               # 추적 변수명 (메타 변수용)

    def __post_init__(self):
        """초기화 후 검증 (확장)"""
        if self.calculation_method == CalculationMethod.PERCENTAGE_OF_TRACKED and self.trail_direction is None:
            raise ValueError("PERCENTAGE_OF_TRACKED 계산 방식에는 trail_direction이 필요합니다")

        if self.value == 0:
            raise ValueError("value는 0이 될 수 없습니다")

        # 메타 변수 검증
        if self.calculation_method in [
            CalculationMethod.PERCENTAGE_OF_EXTREME,
            CalculationMethod.PERCENTAGE_OF_TRACKED
        ] and self.tracking_variable is None:
            raise ValueError(f"{self.calculation_method.value} 계산 방식에는 tracking_variable이 필요합니다")

    def should_reset(self, trigger_event: ResetTrigger) -> bool:
        """해당 이벤트에서 초기화해야 하는지 확인"""
        return self.reset_trigger == trigger_event

    def calculate_target_value(self, context: dict[str, Any]) -> Decimal:
        """
        컨텍스트를 기반으로 목표값 계산

        Args:
            context: 계산에 필요한 컨텍스트 정보
                - entry_price: 진입가
                - average_price: 평단가
                - current_price: 현재가
                - high_price: 고가 (트레일링용)
                - low_price: 저가 (트레일링용)
                - tracked_value: 추적 중인 값 (트레일링용)

        Returns:
            계산된 목표값
        """
        base_price = self._get_base_price(context)

        if self.calculation_method == CalculationMethod.STATIC_VALUE:
            return base_price + self.value

        elif self.calculation_method == CalculationMethod.STATIC_VALUE_OFFSET:
            return base_price + self.value

        elif self.calculation_method == CalculationMethod.PERCENTAGE_OF_EXTREME:
            # 극값 기준 비율 계산 (최고/최저가 기준)
            if self.trail_direction == TrailDirection.UP:
                extreme_value = Decimal(str(context.get("high_price", context["current_price"])))
            elif self.trail_direction == TrailDirection.DOWN:
                extreme_value = Decimal(str(context.get("low_price", context["current_price"])))
            else:
                extreme_value = base_price

            return extreme_value * (Decimal("1") + self.value / Decimal("100"))

        elif self.calculation_method == CalculationMethod.PERCENTAGE_OF_TRACKED:
            if "tracked_value" not in context:
                raise ValueError("PERCENTAGE_OF_TRACKED 계산에는 tracked_value가 필요합니다")
            tracked_value = Decimal(str(context["tracked_value"]))
            return tracked_value * (Decimal("1") + self.value / Decimal("100"))

        elif self.calculation_method == CalculationMethod.ENTRY_PRICE_PERCENT:
            entry_price = Decimal(str(context["entry_price"]))
            return entry_price * (Decimal("1") + self.value / Decimal("100"))

        elif self.calculation_method == CalculationMethod.AVERAGE_PRICE_PERCENT:
            average_price = Decimal(str(context["average_price"]))
            return average_price * (Decimal("1") + self.value / Decimal("100"))

        else:
            raise ValueError(f"지원하지 않는 계산 방식: {self.calculation_method}")

    def _get_base_price(self, context: dict[str, Any]) -> Decimal:
        """기준가 추출"""
        if self.base_variable == BaseVariable.ENTRY_PRICE:
            return Decimal(str(context["entry_price"]))
        elif self.base_variable == BaseVariable.AVERAGE_PRICE:
            return Decimal(str(context["average_price"]))
        elif self.base_variable == BaseVariable.CURRENT_PRICE:
            return Decimal(str(context["current_price"]))
        elif self.base_variable == BaseVariable.HIGH_PRICE:
            return Decimal(str(context["high_price"]))
        elif self.base_variable == BaseVariable.LOW_PRICE:
            return Decimal(str(context["low_price"]))
        else:
            raise ValueError(f"지원하지 않는 기준값 타입: {self.base_variable}")

    def get_description(self) -> str:
        """파라미터 설명 텍스트 생성"""
        base_desc = {
            BaseVariable.ENTRY_PRICE: "진입가",
            BaseVariable.AVERAGE_PRICE: "평단가",
            BaseVariable.CURRENT_PRICE: "현재가",
            BaseVariable.HIGH_PRICE: "고가",
            BaseVariable.LOW_PRICE: "저가"
        }[self.base_variable]

        method_desc = {
            CalculationMethod.STATIC_VALUE: f"{base_desc} + {self.value}원",
            CalculationMethod.STATIC_VALUE_OFFSET: f"{base_desc} + {self.value}원",
            CalculationMethod.PERCENTAGE_OF_EXTREME: f"극값의 {self.value}%",
            CalculationMethod.PERCENTAGE_OF_TRACKED: f"추적값의 {self.value}%",
            CalculationMethod.ENTRY_PRICE_PERCENT: f"진입가의 {self.value}%",
            CalculationMethod.AVERAGE_PRICE_PERCENT: f"평단가의 {self.value}%"
        }[self.calculation_method]

        if self.trail_direction:
            direction_desc = {
                TrailDirection.UP: "상승",
                TrailDirection.DOWN: "하락",
                TrailDirection.BIDIRECTIONAL: "양방향"
            }[self.trail_direction]
            return f"{method_desc} ({direction_desc} 추적)"

        if self.reset_trigger and self.reset_trigger != ResetTrigger.NEVER:
            reset_desc = {
                ResetTrigger.POSITION_ENTRY: "진입시 초기화",
                ResetTrigger.POSITION_EXIT: "청산시 초기화",
                ResetTrigger.MANUAL_RESET: "수동 초기화",
                ResetTrigger.CONDITION_MET: "조건달성시 초기화",
                ResetTrigger.DAILY_RESET: "일일 초기화",
                ResetTrigger.STRATEGY_RESTART: "재시작시 초기화"
            }.get(self.reset_trigger, "")
            return f"{method_desc} [{reset_desc}]"

        return method_desc
