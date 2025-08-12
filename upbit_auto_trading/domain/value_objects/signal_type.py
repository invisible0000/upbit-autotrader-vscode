"""
신호 타입 값 객체 (SignalType)

매매 신호의 종류를 정의하는 값 객체입니다.
기존 role_based_strategy.py의 SignalType enum을 도메인으로 이동시킨 것입니다.
"""

from enum import Enum

class SignalType(Enum):
    """
    신호 타입 분류
    
    매매 시스템에서 생성되는 모든 신호의 종류:
    
    진입 신호:
    - BUY: 매수 진입
    - SELL: 매도 진입 (공매도)
    - HOLD: 관망
    
    관리 신호:
    - ADD_BUY: 추가 매수 (물타기/불타기)
    - ADD_SELL: 부분 매도
    - CLOSE_POSITION: 전체 청산
    - UPDATE_STOP: 스탑 가격 업데이트
    """
    
    # 진입 신호
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    
    # 관리 신호
    ADD_BUY = "ADD_BUY"
    ADD_SELL = "ADD_SELL"
    CLOSE_POSITION = "CLOSE_POSITION"
    UPDATE_STOP = "UPDATE_STOP"
    
    def __str__(self) -> str:
        """문자열 표현"""
        return self.value
    
    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"SignalType.{self.name}"
    
    def get_display_name(self) -> str:
        """사용자 친화적 표시명"""
        display_names = {
            self.BUY: "매수",
            self.SELL: "매도",
            self.HOLD: "관망",
            self.ADD_BUY: "추가 매수",
            self.ADD_SELL: "부분 매도",
            self.CLOSE_POSITION: "전체 청산",
            self.UPDATE_STOP: "손절선 조정"
        }
        return display_names.get(self, str(self.value))
    
    def get_description(self) -> str:
        """상세 설명"""
        descriptions = {
            self.BUY: "새로운 매수 포지션을 진입합니다",
            self.SELL: "새로운 매도 포지션을 진입합니다 (공매도)",
            self.HOLD: "현재 상태를 유지합니다",
            self.ADD_BUY: "기존 포지션에 추가로 매수합니다 (물타기/불타기)",
            self.ADD_SELL: "기존 포지션의 일부를 매도합니다",
            self.CLOSE_POSITION: "모든 포지션을 청산합니다",
            self.UPDATE_STOP: "손절선 가격을 업데이트합니다"
        }
        return descriptions.get(self, "정의되지 않은 신호")
    
    def get_signal_category(self) -> str:
        """신호 카테고리 반환"""
        entry_signals = [self.BUY, self.SELL, self.HOLD]
        management_signals = [self.ADD_BUY, self.ADD_SELL, self.CLOSE_POSITION, self.UPDATE_STOP]
        
        if self in entry_signals:
            return "ENTRY"
        elif self in management_signals:
            return "MANAGEMENT"
        else:
            return "UNKNOWN"
    
    def is_entry_signal(self) -> bool:
        """진입 신호인지 확인"""
        return self.get_signal_category() == "ENTRY"
    
    def is_management_signal(self) -> bool:
        """관리 신호인지 확인"""
        return self.get_signal_category() == "MANAGEMENT"
    
    def is_action_signal(self) -> bool:
        """실제 거래 행동이 필요한 신호인지 확인"""
        return self != SignalType.HOLD
    
    def is_buy_signal(self) -> bool:
        """매수 관련 신호인지 확인"""
        return self in [SignalType.BUY, SignalType.ADD_BUY]
    
    def is_sell_signal(self) -> bool:
        """매도 관련 신호인지 확인"""
        return self in [SignalType.SELL, SignalType.ADD_SELL, SignalType.CLOSE_POSITION]
    
    def requires_quantity(self) -> bool:
        """수량 정보가 필요한 신호인지 확인"""
        return self in [SignalType.BUY, SignalType.SELL, SignalType.ADD_BUY, SignalType.ADD_SELL]
    
    def requires_price(self) -> bool:
        """가격 정보가 필요한 신호인지 확인"""
        return self != SignalType.HOLD
    
    def get_priority_score(self) -> int:
        """신호 우선순위 점수 (높을수록 우선순위 높음)"""
        priority_scores = {
            self.CLOSE_POSITION: 100,  # 최우선
            self.UPDATE_STOP: 80,
            self.ADD_SELL: 60,
            self.ADD_BUY: 40,
            self.SELL: 30,
            self.BUY: 20,
            self.HOLD: 0  # 최하위
        }
        return priority_scores.get(self, 0)
    
    @classmethod
    def from_string(cls, value: str) -> "SignalType":
        """문자열에서 객체 생성"""
        for signal in cls:
            if signal.value == value:
                return signal
        raise ValueError(f"지원하지 않는 신호 타입: {value}")
    
    @classmethod
    def get_entry_signals(cls) -> list["SignalType"]:
        """진입 신호들만 반환"""
        return [signal for signal in cls if signal.is_entry_signal()]
    
    @classmethod
    def get_management_signals(cls) -> list["SignalType"]:
        """관리 신호들만 반환"""
        return [signal for signal in cls if signal.is_management_signal()]
    
    @classmethod
    def get_all_display_names(cls) -> dict[str, str]:
        """모든 신호의 표시명 딕셔너리 반환"""
        return {signal.value: signal.get_display_name() for signal in cls}
