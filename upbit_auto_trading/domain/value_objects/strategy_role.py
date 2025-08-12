"""
전략 역할 값 객체 (StrategyRole)

전략의 역할을 정의하는 값 객체입니다.
기존 role_based_strategy.py의 StrategyRole enum을 도메인으로 이동시킨 것입니다.
"""

from enum import Enum

class StrategyRole(Enum):
    """
    전략 역할 분류
    
    전략 시스템에서 각 전략이 담당하는 역할:
    - ENTRY: 진입 전략 (포지션이 없을 때 최초 진입 신호)
    - MANAGEMENT: 관리 전략 (포지션이 있을 때 리스크 관리 및 수익 최적화)
    """
    
    ENTRY = "entry"
    MANAGEMENT = "management"
    
    def __str__(self) -> str:
        """문자열 표현"""
        return self.value
    
    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"StrategyRole.{self.name}"
    
    def get_display_name(self) -> str:
        """사용자 친화적 표시명"""
        display_names = {
            self.ENTRY: "진입 전략",
            self.MANAGEMENT: "관리 전략"
        }
        return display_names.get(self, str(self.value))
    
    def get_description(self) -> str:
        """상세 설명"""
        descriptions = {
            self.ENTRY: "포지션이 없을 때 최초 진입 신호를 생성합니다",
            self.MANAGEMENT: "포지션이 있을 때 리스크 관리 및 수익 최적화를 담당합니다"
        }
        return descriptions.get(self, "정의되지 않은 전략 역할")
    
    def get_allowed_signals(self) -> list[str]:
        """허용되는 신호 타입들"""
        if self == StrategyRole.ENTRY:
            return ["BUY", "SELL", "HOLD"]
        elif self == StrategyRole.MANAGEMENT:
            return ["ADD_BUY", "ADD_SELL", "CLOSE_POSITION", "UPDATE_STOP", "HOLD"]
        else:
            return ["HOLD"]
    
    def is_valid_signal(self, signal: str) -> bool:
        """해당 역할에서 유효한 신호인지 확인"""
        return signal in self.get_allowed_signals()
    
    def requires_position(self) -> bool:
        """포지션이 필요한 역할인지 확인"""
        return self == StrategyRole.MANAGEMENT
    
    def can_activate_without_position(self) -> bool:
        """포지션 없이 활성화 가능한지 확인"""
        return self == StrategyRole.ENTRY
    
    @classmethod
    def from_string(cls, value: str) -> "StrategyRole":
        """문자열에서 객체 생성"""
        for role in cls:
            if role.value == value:
                return role
        raise ValueError(f"지원하지 않는 전략 역할: {value}")
    
    @classmethod
    def get_all_display_names(cls) -> dict[str, str]:
        """모든 역할의 표시명 딕셔너리 반환"""
        return {role.value: role.get_display_name() for role in cls}
