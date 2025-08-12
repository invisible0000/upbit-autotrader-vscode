"""
Profile Metadata Entity
=======================

프로파일 메타데이터를 관리하는 Domain Entity입니다.
프로파일의 설명, 생성정보, 태그 등을 관리합니다.

DDD Entity 특징:
- 프로파일명을 식별자로 사용
- 프로파일 정보와 메타데이터를 캡슐화
- 표시명과 파일경로 관리 기능
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ProfileMetadata")

@dataclass
class ProfileMetadata:
    """
    프로파일 메타데이터 엔티티

    Attributes:
        name: 프로파일명 (Entity 식별자)
        description: 프로파일 설명
        created_at: 생성 시각
        created_from: 기반이 된 프로파일명 (복사 시)
        tags: 프로파일 태그 리스트
        file_path: 프로파일 파일 경로
        profile_type: 프로파일 유형 ('built-in', 'custom')
    """

    # Entity 식별자
    name: str

    # 메타데이터 정보
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    created_from: str = ""
    tags: List[str] = field(default_factory=list)

    # 파일 시스템 정보
    file_path: str = ""
    profile_type: str = "custom"  # 'built-in', 'custom'

    def __post_init__(self):
        """엔티티 초기화 후 검증"""
        self._validate_metadata()
        logger.debug(f"ProfileMetadata 생성됨: {self.name}")

    def _validate_metadata(self) -> None:
        """메타데이터 불변 조건 검증"""
        if not self.name.strip():
            raise ValueError("프로파일명은 필수입니다")

        if not self._is_valid_profile_name(self.name):
            raise ValueError("프로파일명은 영문, 숫자, 언더스코어, 하이픈만 허용됩니다")

        if self.profile_type not in ['built-in', 'custom']:
            raise ValueError("프로파일 타입은 'built-in' 또는 'custom'이어야 합니다")

        # 태그 정규화
        self.tags = [tag.strip().lower() for tag in self.tags if tag.strip()]

    def _is_valid_profile_name(self, name: str) -> bool:
        """프로파일명 유효성 검사"""
        return name.replace('_', '').replace('-', '').isalnum()

    def get_display_name(self) -> str:
        """UI 표시용 이름 생성"""
        if self.description:
            return f"{self.description} ({self.name})"
        else:
            return self.name

    def get_display_info(self) -> str:
        """UI 표시용 상세 정보"""
        info_parts = []

        if self.description:
            info_parts.append(f"설명: {self.description}")

        if self.created_from:
            info_parts.append(f"기반: {self.created_from}")

        if self.tags:
            info_parts.append(f"태그: {', '.join(self.tags)}")

        info_parts.append(f"타입: {self.profile_type}")
        info_parts.append(f"생성: {self.created_at.strftime('%Y-%m-%d %H:%M')}")

        return " | ".join(info_parts)

    def add_tag(self, tag: str) -> None:
        """태그 추가"""
        normalized_tag = tag.strip().lower()
        if normalized_tag and normalized_tag not in self.tags:
            self.tags.append(normalized_tag)
            logger.debug(f"프로파일 {self.name}에 태그 추가: {normalized_tag}")

    def remove_tag(self, tag: str) -> bool:
        """태그 제거"""
        normalized_tag = tag.strip().lower()
        if normalized_tag in self.tags:
            self.tags.remove(normalized_tag)
            logger.debug(f"프로파일 {self.name}에서 태그 제거: {normalized_tag}")
            return True
        return False

    def has_tag(self, tag: str) -> bool:
        """태그 보유 여부 확인"""
        return tag.strip().lower() in self.tags

    def update_description(self, new_description: str) -> None:
        """설명 업데이트"""
        old_description = self.description
        self.description = new_description.strip()
        logger.debug(f"프로파일 {self.name} 설명 업데이트: '{old_description}' → '{self.description}'")

    def set_file_path(self, file_path: str) -> None:
        """파일 경로 설정"""
        self.file_path = str(Path(file_path).resolve())
        logger.debug(f"프로파일 {self.name} 파일 경로 설정: {self.file_path}")

    def is_built_in(self) -> bool:
        """빌트인 프로파일 여부"""
        return self.profile_type == "built-in"

    def is_custom(self) -> bool:
        """커스텀 프로파일 여부"""
        return self.profile_type == "custom"

    def get_file_name(self) -> str:
        """파일명만 추출"""
        if self.file_path:
            return Path(self.file_path).name
        return f"{self.name}.yaml"

    def matches_search(self, search_term: str) -> bool:
        """검색어와 매칭 여부 확인"""
        search_lower = search_term.lower().strip()
        if not search_lower:
            return True

        # 이름, 설명, 태그에서 검색
        searchable_text = " ".join([
            self.name.lower(),
            self.description.lower(),
            " ".join(self.tags)
        ])

        return search_lower in searchable_text

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (직렬화용)"""
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'created_from': self.created_from,
            'tags': self.tags.copy(),
            'file_path': self.file_path,
            'profile_type': self.profile_type
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ProfileMetadata':
        """딕셔너리에서 생성 (역직렬화용)"""
        data = data.copy()
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])

        return cls(**data)

    def __str__(self) -> str:
        """메타데이터 문자열 표현"""
        return f"ProfileMetadata({self.name}, {self.profile_type})"

    def __repr__(self) -> str:
        """메타데이터 디버깅 표현"""
        return (f"ProfileMetadata(name='{self.name}', "
                f"description='{self.description[:20]}...', "
                f"profile_type='{self.profile_type}', "
                f"tags={self.tags})")
