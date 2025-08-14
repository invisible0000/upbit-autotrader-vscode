"""
변화 감지 서비스
- 메타 변수들의 변화 감지 로직 처리
- 외부 변수 추적 및 변화 감지 알고리즘
"""
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from upbit_auto_trading.domain.trigger_builder.entities.trading_variable import TradingVariable
from upbit_auto_trading.domain.trigger_builder.value_objects.change_detection_parameter import ChangeDetectionParameter
from upbit_auto_trading.domain.trigger_builder.enums import DetectionType, BreakoutType, ResetTrigger


@dataclass
class ChangeDetectionResult:
    """변화 감지 결과"""
    variable_id: str
    detected: bool
    previous_value: Optional[Decimal]
    current_value: Optional[Decimal]
    change_amount: Optional[Decimal]
    change_percentage: Optional[Decimal]
    detection_reason: str


class ChangeDetectionService:
    """변화 감지 도메인 서비스"""

    def detect_variable_change(
        self,
        variable: TradingVariable,
        current_value: Decimal,
        previous_value: Optional[Decimal] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ChangeDetectionResult:
        """
        변수의 변화 감지

        Args:
            variable: 대상 변수
            current_value: 현재 값
            previous_value: 이전 값
            context: 추가 컨텍스트 (기준값 등)

        Returns:
            변화 감지 결과
        """
        if not variable.is_change_detection_variable():
            return ChangeDetectionResult(
                variable_id=variable.variable_id,
                detected=False,
                previous_value=previous_value,
                current_value=current_value,
                change_amount=None,
                change_percentage=None,
                detection_reason="변화 감지 변수가 아님"
            )

        # 변화 감지 파라미터가 있는 경우
        for param in variable.change_detection_parameters:
            result = self._detect_with_parameter(param, current_value, previous_value, context)
            if result.detected:
                return result

        # 기본 변화 감지 (파라미터 없는 경우)
        return self._detect_basic_change(variable.variable_id, current_value, previous_value)

    def _detect_with_parameter(
        self,
        param: ChangeDetectionParameter,
        current_value: Decimal,
        previous_value: Optional[Decimal],
        context: Optional[Dict[str, Any]]
    ) -> ChangeDetectionResult:
        """파라미터 기반 변화 감지"""

        # RSI 변화 감지
        if param.is_rsi_change_detector():
            return self._detect_rsi_change(param, current_value, previous_value)

        # 가격 돌파 감지
        elif param.is_price_breakout_detector():
            return self._detect_price_breakout(param, current_value, context)

        # 거래량 급증 감지
        elif param.is_volume_spike_detector():
            return self._detect_volume_spike(param, current_value, context)

        else:
            return self._detect_basic_change(param.name, current_value, previous_value)

    def _detect_rsi_change(
        self,
        param: ChangeDetectionParameter,
        current_value: Decimal,
        previous_value: Optional[Decimal]
    ) -> ChangeDetectionResult:
        """RSI 변화 감지"""
        if previous_value is None:
            return ChangeDetectionResult(
                variable_id=param.name,
                detected=False,
                previous_value=None,
                current_value=current_value,
                change_amount=None,
                change_percentage=None,
                detection_reason="이전 값 없음"
            )

        detected = param.should_detect_change(current_value, previous_value)
        change_amount = current_value - previous_value
        change_percentage = None

        if previous_value != 0:
            change_percentage = (change_amount / previous_value) * 100

        return ChangeDetectionResult(
            variable_id=param.name,
            detected=detected,
            previous_value=previous_value,
            current_value=current_value,
            change_amount=change_amount,
            change_percentage=change_percentage,
            detection_reason=f"{param.detection_type.value if param.detection_type else '변화'} 감지" if detected else "임계값 미달"
        )

    def _detect_price_breakout(
        self,
        param: ChangeDetectionParameter,
        current_value: Decimal,
        context: Optional[Dict[str, Any]]
    ) -> ChangeDetectionResult:
        """가격 돌파 감지"""
        if not context or not param.reference_value:
            return ChangeDetectionResult(
                variable_id=param.name,
                detected=False,
                previous_value=None,
                current_value=current_value,
                change_amount=None,
                change_percentage=None,
                detection_reason="기준값 없음"
            )

        reference_price = context.get(param.reference_value)
        if reference_price is None:
            return ChangeDetectionResult(
                variable_id=param.name,
                detected=False,
                previous_value=None,
                current_value=current_value,
                change_amount=None,
                change_percentage=None,
                detection_reason=f"기준값 '{param.reference_value}' 없음"
            )

        reference_price = Decimal(str(reference_price))

        # 돌파 감지 로직
        detected = False
        if param.breakout_type == BreakoutType.UPWARD_BREAK:
            detected = current_value > reference_price
        elif param.breakout_type == BreakoutType.DOWNWARD_BREAK:
            detected = current_value < reference_price

        # 확인 임계값 적용
        if detected and param.confirmation_threshold:
            threshold_amount = reference_price * (param.confirmation_threshold / 100)
            if param.breakout_type == BreakoutType.UPWARD_BREAK:
                detected = current_value > (reference_price + threshold_amount)
            elif param.breakout_type == BreakoutType.DOWNWARD_BREAK:
                detected = current_value < (reference_price - threshold_amount)

        change_amount = current_value - reference_price
        change_percentage = (change_amount / reference_price) * 100 if reference_price != 0 else None

        return ChangeDetectionResult(
            variable_id=param.name,
            detected=detected,
            previous_value=reference_price,
            current_value=current_value,
            change_amount=change_amount,
            change_percentage=change_percentage,
            detection_reason=f"{param.breakout_type.value if param.breakout_type else '돌파'} 감지" if detected else "돌파 미발생"
        )

    def _detect_volume_spike(
        self,
        param: ChangeDetectionParameter,
        current_value: Decimal,
        context: Optional[Dict[str, Any]]
    ) -> ChangeDetectionResult:
        """거래량 급증 감지"""
        if not context or not param.baseline_period:
            return ChangeDetectionResult(
                variable_id=param.name,
                detected=False,
                previous_value=None,
                current_value=current_value,
                change_amount=None,
                change_percentage=None,
                detection_reason="기준 기간 정보 없음"
            )

        baseline_volume = context.get("baseline_volume")
        if baseline_volume is None:
            return ChangeDetectionResult(
                variable_id=param.name,
                detected=False,
                previous_value=None,
                current_value=current_value,
                change_amount=None,
                change_percentage=None,
                detection_reason="기준 거래량 없음"
            )

        baseline_volume = Decimal(str(baseline_volume))

        # 급증 감지
        spike_threshold = baseline_volume * (param.spike_multiplier or Decimal("2.0"))
        detected = current_value > spike_threshold

        change_amount = current_value - baseline_volume
        change_percentage = (change_amount / baseline_volume) * 100 if baseline_volume != 0 else None

        return ChangeDetectionResult(
            variable_id=param.name,
            detected=detected,
            previous_value=baseline_volume,
            current_value=current_value,
            change_amount=change_amount,
            change_percentage=change_percentage,
            detection_reason=f"{param.spike_multiplier}배 급증 감지" if detected else "급증 미감지"
        )

    def _detect_basic_change(
        self,
        variable_id: str,
        current_value: Decimal,
        previous_value: Optional[Decimal]
    ) -> ChangeDetectionResult:
        """기본 변화 감지"""
        if previous_value is None:
            return ChangeDetectionResult(
                variable_id=variable_id,
                detected=False,
                previous_value=None,
                current_value=current_value,
                change_amount=None,
                change_percentage=None,
                detection_reason="이전 값 없음"
            )

        detected = current_value != previous_value
        change_amount = current_value - previous_value
        change_percentage = None

        if previous_value != 0:
            change_percentage = (change_amount / previous_value) * 100

        return ChangeDetectionResult(
            variable_id=variable_id,
            detected=detected,
            previous_value=previous_value,
            current_value=current_value,
            change_amount=change_amount,
            change_percentage=change_percentage,
            detection_reason="값 변화 감지" if detected else "값 변화 없음"
        )

    def should_reset_tracking(self, variable: TradingVariable, event: ResetTrigger) -> bool:
        """추적 값 초기화 여부 확인"""
        for param in variable.unified_parameters:
            if param.should_reset(event):
                return True
        return False

    def get_trackable_variables(self, variables: List[TradingVariable]) -> List[TradingVariable]:
        """추적 가능한 변수들 필터링"""
        return [
            var for var in variables
            if not var.is_meta_variable()  # 메타 변수는 추적 대상에서 제외
            and var.is_active
        ]
