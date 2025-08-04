"""
충돌 해결 방식 값 객체 (ConflictResolution)

여러 관리 전략이 동시에 신호를 발생시킬 때의 충돌 해결 방식을 정의합니다.
기존 ConflictResolutionTypeEnum을 도메인 값 객체로 이동시킨 것입니다.
"""

from enum import Enum


class ConflictResolution(Enum):
    """
    전략 충돌 해결 방식

    여러 관리 전략이 동시에 다른 신호를 보낼 때 어떻게 해결할지 정의:
    - CONSERVATIVE: 가장 보수적인 신호 채택 (HOLD > CLOSE > ADD)
    - PRIORITY: 우선순위가 높은 전략의 신호 채택
    - MERGE: 신호들을 병합하여 종합적 판단
    """

    CONSERVATIVE = "conservative"
    PRIORITY = "priority"
    MERGE = "merge"

    def __str__(self) -> str:
        """문자열 표현"""
        return self.value

    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"ConflictResolution.{self.name}"

    def get_display_name(self) -> str:
        """사용자 친화적 표시명"""
        display_names = {
            self.CONSERVATIVE: "보수적 해결",
            self.PRIORITY: "우선순위 기반",
            self.MERGE: "신호 병합"
        }
        return display_names.get(self, str(self.value))

    def get_description(self) -> str:
        """상세 설명"""
        descriptions = {
            self.CONSERVATIVE: "가장 안전한 신호를 선택합니다 (HOLD > CLOSE > ADD)",
            self.PRIORITY: "우선순위가 높은 전략의 신호를 따릅니다",
            self.MERGE: "여러 신호를 종합하여 최적의 결정을 내립니다"
        }
        return descriptions.get(self, "정의되지 않은 해결 방식")

    def resolve_signals(self, signals: list) -> str:
        """
        충돌 해결 로직 적용

        Args:
            signals: 충돌하는 신호들의 리스트

        Returns:
            해결된 최종 신호
        """
        if not signals:
            return "HOLD"

        if len(signals) == 1:
            return signals[0]

        if self == ConflictResolution.CONSERVATIVE:
            return self._resolve_conservative(signals)
        elif self == ConflictResolution.PRIORITY:
            return self._resolve_priority(signals)
        elif self == ConflictResolution.MERGE:
            return self._resolve_merge(signals)
        else:
            return "HOLD"

    def _resolve_conservative(self, signals: list) -> str:
        """보수적 해결: 안전한 순서로 우선순위 적용"""
        priority_order = ["HOLD", "CLOSE_POSITION", "UPDATE_STOP", "ADD_SELL", "ADD_BUY"]

        for priority_signal in priority_order:
            if priority_signal in signals:
                return priority_signal

        return signals[0]  # 기본값

    def _resolve_priority(self, signals: list) -> str:
        """우선순위 해결: 첫 번째 신호 채택 (호출 순서 기반)"""
        return signals[0]

    def _resolve_merge(self, signals: list) -> str:
        """병합 해결: 신호들의 특성을 종합 판단"""
        # 간단한 병합 로직 (실제로는 더 복잡한 알고리즘 필요)
        buy_signals = [s for s in signals if "BUY" in s]
        sell_signals = [s for s in signals if "SELL" in s or "CLOSE" in s]

        if len(sell_signals) > len(buy_signals):
            return "CLOSE_POSITION"
        elif len(buy_signals) > len(sell_signals):
            return "ADD_BUY"
        else:
            return "HOLD"

    @classmethod
    def from_string(cls, value: str) -> "ConflictResolution":
        """문자열에서 객체 생성"""
        for resolution in cls:
            if resolution.value == value:
                return resolution
        raise ValueError(f"지원하지 않는 충돌 해결 방식: {value}")

    @classmethod
    def get_all_display_names(cls) -> dict[str, str]:
        """모든 해결 방식의 표시명 딕셔너리 반환"""
        return {res.value: res.get_display_name() for res in cls}

    def is_safe_resolution(self) -> bool:
        """안전한 해결 방식인지 확인"""
        return self in [ConflictResolution.CONSERVATIVE, ConflictResolution.PRIORITY]
