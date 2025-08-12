"""
비교 연산자 값 객체 (ComparisonOperator)

트리거 조건에서 사용하는 비교 연산자를 정의하는 열거형 값 객체입니다.
기존 트리거 빌더 시스템과 호환되는 연산자 세트를 제공합니다.
"""

from enum import Enum

class ComparisonOperator(Enum):
    """
    비교 연산자 열거형
    
    기존 시스템에서 사용하는 연산자들과 호환:
    - > (초과/돌파)
    - < (미만/이탈)
    - >= (이상/도달)
    - <= (이하/하락)
    - == (동일)
    - != (다름)
    - ~= (근사/유사)
    """
    
    # 기본 비교 연산자
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    
    # 특수 연산자
    APPROXIMATELY_EQUAL = "~="  # 근사 비교 (±5% 오차 허용)
    
    def __str__(self) -> str:
        """문자열 표현"""
        return self.value
    
    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"ComparisonOperator.{self.name}"
    
    def get_display_name(self) -> str:
        """사용자 친화적 표시명"""
        display_names = {
            self.GREATER_THAN: "초과 (>)",
            self.LESS_THAN: "미만 (<)",
            self.GREATER_EQUAL: "이상 (>=)",
            self.LESS_EQUAL: "이하 (<=)",
            self.EQUAL: "같음 (==)",
            self.NOT_EQUAL: "다름 (!=)",
            self.APPROXIMATELY_EQUAL: "근사 (~=)"
        }
        return display_names.get(self, str(self.value))
    
    def get_description(self) -> str:
        """상세 설명"""
        descriptions = {
            self.GREATER_THAN: "기준값보다 클 때 (돌파)",
            self.LESS_THAN: "기준값보다 작을 때 (이탈)",
            self.GREATER_EQUAL: "기준값 이상일 때 (도달)",
            self.LESS_EQUAL: "기준값 이하일 때 (하락)",
            self.EQUAL: "기준값과 정확히 같을 때",
            self.NOT_EQUAL: "기준값과 다를 때",
            self.APPROXIMATELY_EQUAL: "기준값과 근사할 때 (±5% 오차)"
        }
        return descriptions.get(self, "정의되지 않은 연산자")
    
    def evaluate(self, left_value: float, right_value: float, tolerance: float = 0.05) -> bool:
        """
        두 값을 비교하여 결과 반환
        
        Args:
            left_value: 좌변값 (변수값)
            right_value: 우변값 (기준값)
            tolerance: 근사 비교 시 허용 오차 (기본 5%)
            
        Returns:
            비교 결과 (True/False)
        """
        if self == ComparisonOperator.GREATER_THAN:
            return left_value > right_value
        elif self == ComparisonOperator.LESS_THAN:
            return left_value < right_value
        elif self == ComparisonOperator.GREATER_EQUAL:
            return left_value >= right_value
        elif self == ComparisonOperator.LESS_EQUAL:
            return left_value <= right_value
        elif self == ComparisonOperator.EQUAL:
            return left_value == right_value
        elif self == ComparisonOperator.NOT_EQUAL:
            return left_value != right_value
        elif self == ComparisonOperator.APPROXIMATELY_EQUAL:
            # 근사 비교: 상대 오차가 tolerance 이내
            if right_value == 0:
                return abs(left_value) <= tolerance
            relative_error = abs(left_value - right_value) / abs(right_value)
            return relative_error <= tolerance
        else:
            raise ValueError(f"지원하지 않는 연산자: {self}")
    
    def get_python_operator(self) -> str:
        """Python 연산자 문자열 반환"""
        return self.value if self != ComparisonOperator.APPROXIMATELY_EQUAL else "~="
    
    def is_inequality(self) -> bool:
        """부등식 연산자인지 확인"""
        return self in [
            ComparisonOperator.GREATER_THAN,
            ComparisonOperator.LESS_THAN,
            ComparisonOperator.GREATER_EQUAL,
            ComparisonOperator.LESS_EQUAL
        ]
    
    def is_equality(self) -> bool:
        """등식 연산자인지 확인"""
        return self in [
            ComparisonOperator.EQUAL,
            ComparisonOperator.NOT_EQUAL,
            ComparisonOperator.APPROXIMATELY_EQUAL
        ]
    
    def is_directional(self) -> bool:
        """방향성이 있는 연산자인지 확인 (>, <, >=, <=)"""
        return self in [
            ComparisonOperator.GREATER_THAN,
            ComparisonOperator.LESS_THAN,
            ComparisonOperator.GREATER_EQUAL,
            ComparisonOperator.LESS_EQUAL
        ]
    
    @classmethod
    def from_string(cls, operator_str: str) -> "ComparisonOperator":
        """문자열에서 연산자 객체 생성"""
        for operator in cls:
            if operator.value == operator_str:
                return operator
        raise ValueError(f"지원하지 않는 연산자 문자열: {operator_str}")
    
    @classmethod
    def get_all_display_names(cls) -> dict[str, str]:
        """모든 연산자의 표시명 딕셔너리 반환"""
        return {op.value: op.get_display_name() for op in cls}
    
    @classmethod
    def get_directional_operators(cls) -> list["ComparisonOperator"]:
        """방향성 있는 연산자들만 반환"""
        return [op for op in cls if op.is_directional()]
    
    @classmethod
    def get_equality_operators(cls) -> list["ComparisonOperator"]:
        """등식 연산자들만 반환"""
        return [op for op in cls if op.is_equality()]
