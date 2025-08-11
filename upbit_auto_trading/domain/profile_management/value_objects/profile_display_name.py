"""
Profile Display Name Value Object
=================================

프로파일 표시명을 관리하는 Value Object입니다.
불변성과 유효성 검증을 제공합니다.

DDD Value Object 특징:
- 불변 객체 (immutable)
- 값으로만 식별됨 (동등성 비교)
- 자체 유효성 검증 포함
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProfileDisplayName:
    """
    프로파일 표시명 Value Object

    UI에서 사용자에게 표시되는 프로파일 이름을 관리합니다.
    원본 프로파일명과 설명을 조합하여 의미있는 표시명을 생성합니다.

    Attributes:
        profile_name: 원본 프로파일명
        description: 프로파일 설명 (선택적)
    """

    profile_name: str
    description: Optional[str] = None

    def __post_init__(self):
        """Value Object 초기화 후 검증"""
        self._validate()

    def _validate(self) -> None:
        """표시명 유효성 검증"""
        if not self.profile_name or not self.profile_name.strip():
            raise ValueError("프로파일명은 필수입니다")

        if len(self.profile_name) > 50:
            raise ValueError("프로파일명은 50자를 초과할 수 없습니다")

        if self.description is not None and len(self.description) > 100:
            raise ValueError("프로파일 설명은 100자를 초과할 수 없습니다")

    def get_display_text(self) -> str:
        """UI 표시용 텍스트 생성"""
        if self.description and self.description.strip():
            return f"{self.description.strip()} ({self.profile_name})"
        return self.profile_name

    def get_short_display(self) -> str:
        """짧은 표시명 (설명 우선)"""
        if self.description and self.description.strip():
            return self.description.strip()
        return self.profile_name

    def get_combo_display(self) -> str:
        """콤보박스용 표시명"""
        display_text = self.get_display_text()
        if len(display_text) > 40:
            # 긴 경우 말줄임표 적용
            return display_text[:37] + "..."
        return display_text

    def has_description(self) -> bool:
        """설명 보유 여부"""
        return self.description is not None and bool(self.description.strip())

    def matches_search(self, search_term: str) -> bool:
        """검색어 매칭 여부"""
        if not search_term.strip():
            return True

        search_lower = search_term.lower().strip()
        searchable_text = self.profile_name.lower()

        if self.description:
            searchable_text += " " + self.description.lower()

        return search_lower in searchable_text

    def __str__(self) -> str:
        """문자열 표현"""
        return self.get_display_text()

    def __repr__(self) -> str:
        """디버깅 표현"""
        return f"ProfileDisplayName('{self.profile_name}', '{self.description}')"
