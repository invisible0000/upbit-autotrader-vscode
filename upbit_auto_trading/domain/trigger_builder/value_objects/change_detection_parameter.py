"""
변화 감지 파라미터 Value Object
- 메타 변수들의 변화 감지 로직을 위한 파라미터 구조
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from ..enums import DetectionType, BreakoutType, DetectionSensitivity


@dataclass(frozen=True)
class ChangeDetectionParameter:
    """
    변화 감지 파라미터 - 메타 변수의 변화 감지를 위한 설정

    사용처:
    - META_RSI_CHANGE: RSI 값 변화 감지
    - META_PRICE_BREAKOUT: 가격 돌파 감지
    - META_VOLUME_SPIKE: 거래량 급증 감지
    """
    name: str                                        # 파라미터 이름
    source_variable: str                             # 원본 변수 (RSI, 종가, 거래량 등)
    detection_type: Optional[DetectionType] = None   # 감지 방식 (RSI_CHANGE용)
    threshold_value: Optional[Decimal] = None        # 감지 임계값
    comparison_window: Optional[int] = None          # 비교 윈도우 (몇 틱 전과 비교)

    # 가격 돌파용 파라미터들
    breakout_type: Optional[BreakoutType] = None     # 돌파 유형
    reference_value: Optional[str] = None            # 기준값 (이동평균_20 등)
    confirmation_threshold: Optional[Decimal] = None  # 확인 임계값

    # 거래량 급증용 파라미터들
    spike_multiplier: Optional[Decimal] = None       # 급증 배수
    baseline_period: Optional[int] = None            # 기준 기간
    detection_sensitivity: Optional[DetectionSensitivity] = None  # 감지 민감도

    def __post_init__(self):
        """초기화 후 검증"""
        if not self.source_variable:
            raise ValueError("source_variable은 필수입니다")

        # RSI 변화 감지 검증
        if self.detection_type and not self.threshold_value:
            raise ValueError("detection_type 설정 시 threshold_value가 필요합니다")

        # 가격 돌파 감지 검증
        if self.breakout_type and not self.reference_value:
            raise ValueError("breakout_type 설정 시 reference_value가 필요합니다")

        # 거래량 급증 감지 검증
        if self.spike_multiplier and not self.baseline_period:
            raise ValueError("spike_multiplier 설정 시 baseline_period가 필요합니다")

    def is_rsi_change_detector(self) -> bool:
        """RSI 변화 감지 파라미터인지 확인"""
        return self.detection_type is not None

    def is_price_breakout_detector(self) -> bool:
        """가격 돌파 감지 파라미터인지 확인"""
        return self.breakout_type is not None

    def is_volume_spike_detector(self) -> bool:
        """거래량 급증 감지 파라미터인지 확인"""
        return self.spike_multiplier is not None

    def get_description(self) -> str:
        """파라미터 설명 텍스트 생성"""
        if self.is_rsi_change_detector():
            detection_value = self.detection_type.value if self.detection_type else "변화"
            return f"{self.source_variable} {detection_value} {self.threshold_value} 감지"

        elif self.is_price_breakout_detector():
            breakout_value = self.breakout_type.value if self.breakout_type else "돌파"
            return f"{self.source_variable}이 {self.reference_value} {breakout_value}"

        elif self.is_volume_spike_detector():
            return f"{self.source_variable} {self.spike_multiplier}배 급증 감지"

        else:
            return f"{self.source_variable} 변화 감지"

    def should_detect_change(self, current_value: Decimal, previous_value: Decimal) -> bool:
        """변화 감지 조건 확인"""
        if not self.threshold_value:
            return False

        if self.detection_type == DetectionType.ABSOLUTE_CHANGE:
            return abs(current_value - previous_value) >= self.threshold_value

        elif self.detection_type == DetectionType.PERCENT_CHANGE:
            if previous_value == 0:
                return False
            percent_change = abs((current_value - previous_value) / previous_value * 100)
            return percent_change >= self.threshold_value

        elif self.detection_type == DetectionType.DIRECTION_CHANGE:
            # 방향 변화 감지 (상승 -> 하락 또는 하락 -> 상승)
            return (current_value > previous_value) != (previous_value > current_value)

        return False
