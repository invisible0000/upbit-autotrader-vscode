"""
트리거 식별자 값 객체 (TriggerId)

트리거 조건을 고유하게 식별하는 불변 값 객체입니다.
트리거 빌더 시스템과의 연동을 위한 식별자 규칙을 적용합니다.
"""

import re
from dataclasses import dataclass
from typing import ClassVar

from ..exceptions.domain_exceptions import InvalidTriggerIdError

@dataclass(frozen=True)
class TriggerId:
    """
    트리거 식별자 값 객체
    
    비즈니스 규칙:
    - 최소 3자 이상, 최대 100자 이하
    - 영문자, 숫자, 언더스코어, 하이픈, 점(.) 허용
    - 영문자로 시작해야 함
    - 트리거 타입 접두사 권장 (ENTRY_, MANAGEMENT_, EXIT_)
    """
    
    value: str
    
    # 클래스 상수
    MIN_LENGTH: ClassVar[int] = 3
    MAX_LENGTH: ClassVar[int] = 100
    VALID_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z][a-zA-Z0-9_.-]*$')
    
    # 트리거 타입 접두사
    ENTRY_PREFIX: ClassVar[str] = "ENTRY_"
    MANAGEMENT_PREFIX: ClassVar[str] = "MANAGEMENT_"
    EXIT_PREFIX: ClassVar[str] = "EXIT_"
    
    def __post_init__(self):
        """생성 후 유효성 검증"""
        if not self.value:
            raise InvalidTriggerIdError("트리거 ID는 필수입니다")
        
        if len(self.value) < self.MIN_LENGTH:
            raise InvalidTriggerIdError(
                f"트리거 ID는 최소 {self.MIN_LENGTH}자 이상이어야 합니다. 입력값: '{self.value}'"
            )
        
        if len(self.value) > self.MAX_LENGTH:
            raise InvalidTriggerIdError(
                f"트리거 ID는 최대 {self.MAX_LENGTH}자 이하여야 합니다. 입력값: '{self.value}'"
            )
        
        if not self.VALID_PATTERN.match(self.value):
            raise InvalidTriggerIdError(
                f"트리거 ID는 영문자로 시작하고 영문자, 숫자, 언더스코어, 하이픈, 점만 포함할 수 있습니다. 입력값: '{self.value}'"
            )
    
    def __str__(self) -> str:
        """문자열 표현"""
        return self.value
    
    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"TriggerId('{self.value}')"
    
    @classmethod
    def generate_entry_trigger(cls, base_name: str) -> "TriggerId":
        """진입 트리거 ID 생성"""
        import uuid
        short_uuid = str(uuid.uuid4())[:8].upper()
        return cls(f"{cls.ENTRY_PREFIX}{base_name}_{short_uuid}")
    
    @classmethod
    def generate_management_trigger(cls, base_name: str) -> "TriggerId":
        """관리 트리거 ID 생성"""
        import uuid
        short_uuid = str(uuid.uuid4())[:8].upper()
        return cls(f"{cls.MANAGEMENT_PREFIX}{base_name}_{short_uuid}")
    
    @classmethod
    def generate_exit_trigger(cls, base_name: str) -> "TriggerId":
        """청산 트리거 ID 생성"""
        import uuid
        short_uuid = str(uuid.uuid4())[:8].upper()
        return cls(f"{cls.EXIT_PREFIX}{base_name}_{short_uuid}")
    
    def get_trigger_type(self) -> str:
        """트리거 타입 추출"""
        if self.value.startswith(self.ENTRY_PREFIX):
            return "ENTRY"
        elif self.value.startswith(self.MANAGEMENT_PREFIX):
            return "MANAGEMENT"
        elif self.value.startswith(self.EXIT_PREFIX):
            return "EXIT"
        else:
            return "UNKNOWN"
    
    def is_entry_trigger(self) -> bool:
        """진입 트리거인지 확인"""
        return self.value.startswith(self.ENTRY_PREFIX)
    
    def is_management_trigger(self) -> bool:
        """관리 트리거인지 확인"""
        return self.value.startswith(self.MANAGEMENT_PREFIX)
    
    def is_exit_trigger(self) -> bool:
        """청산 트리거인지 확인"""
        return self.value.startswith(self.EXIT_PREFIX)
    
    def get_base_name(self) -> str:
        """기본 이름 추출 (접두사 제거)"""
        for prefix in [self.ENTRY_PREFIX, self.MANAGEMENT_PREFIX, self.EXIT_PREFIX]:
            if self.value.startswith(prefix):
                remaining = self.value[len(prefix):]
                # UUID 부분 제거 (마지막 언더스코어 이후)
                if '_' in remaining:
                    return remaining.rsplit('_', 1)[0]
                return remaining
        return self.value
    
    def get_display_name(self) -> str:
        """사용자 친화적 표시명 생성"""
        base_name = self.get_base_name()
        trigger_type = self.get_trigger_type()
        
        # 타입별 한글 표시
        type_names = {
            "ENTRY": "진입",
            "MANAGEMENT": "관리", 
            "EXIT": "청산"
        }
        
        type_display = type_names.get(trigger_type, trigger_type)
        return f"[{type_display}] {base_name.replace('_', ' ').title()}"
