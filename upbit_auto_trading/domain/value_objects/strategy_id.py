"""
전략 식별자 값 객체 (StrategyId)

전략을 고유하게 식별하는 불변 값 객체입니다.
비즈니스 규칙에 따라 ID 유효성을 검증하고, 동일성을 보장합니다.
"""

import re
from dataclasses import dataclass
from typing import ClassVar

from ..exceptions.domain_exceptions import InvalidStrategyIdError

@dataclass(frozen=True)
class StrategyId:
    """
    전략 식별자 값 객체

    비즈니스 규칙:
    - 최소 3자 이상, 최대 50자 이하
    - 영문자, 숫자, 언더스코어, 하이픈만 허용
    - 영문자로 시작해야 함
    - 대소문자 구분
    """

    value: str

    # 클래스 상수
    MIN_LENGTH: ClassVar[int] = 3
    MAX_LENGTH: ClassVar[int] = 50
    VALID_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]*$')

    def __post_init__(self):
        """생성 후 유효성 검증"""
        if not self.value:
            raise InvalidStrategyIdError("전략 ID는 필수입니다")

        if len(self.value) < self.MIN_LENGTH:
            raise InvalidStrategyIdError(
                f"전략 ID는 최소 {self.MIN_LENGTH}자 이상이어야 합니다. 입력값: '{self.value}'"
            )

        if len(self.value) > self.MAX_LENGTH:
            raise InvalidStrategyIdError(
                f"전략 ID는 최대 {self.MAX_LENGTH}자 이하여야 합니다. 입력값: '{self.value}'"
            )

        if not self.VALID_PATTERN.match(self.value):
            raise InvalidStrategyIdError(
                f"전략 ID는 영문자로 시작하고 영문자, 숫자, 언더스코어, 하이픈만 포함할 수 있습니다. 입력값: '{self.value}'"
            )

    def __str__(self) -> str:
        """문자열 표현"""
        return self.value

    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"StrategyId('{self.value}')"

    @classmethod
    def generate_default(cls, base_name: str = "STRATEGY") -> "StrategyId":
        """기본 전략 ID 생성"""
        import uuid
        short_uuid = str(uuid.uuid4())[:8].upper()
        return cls(f"{base_name}_{short_uuid}")

    @classmethod
    def from_combination_id(cls, combination_id: str) -> "StrategyId":
        """기존 combination_id를 StrategyId로 변환"""
        # 기존 시스템과의 호환성을 위해 combination_id를 그대로 사용
        return cls(combination_id)

    def is_basic_7_rule_strategy(self) -> bool:
        """기본 7규칙 전략인지 확인"""
        return self.value.startswith("BASIC_7_RULE")

    def get_display_name(self) -> str:
        """사용자 친화적 표시명 생성"""
        # 언더스코어를 공백으로 변환하고 단어별 첫글자 대문자화
        return self.value.replace("_", " ").title()
