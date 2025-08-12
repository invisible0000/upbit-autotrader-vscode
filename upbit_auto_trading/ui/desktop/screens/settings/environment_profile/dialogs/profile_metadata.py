"""
Profile Metadata Data Class
===========================

프로파일 메타데이터를 관리하는 데이터 클래스
YAML 직렬화/역직렬화, 유효성 검증 등의 기능 제공

Author: AI Assistant
Created: 2025-08-11
Task: 4.2.1
"""

from typing import Optional
import yaml

class ProfileMetadata:
    """프로파일 메타데이터를 관리하는 데이터 클래스"""
    def __init__(self, name: str = "", description: str = "",
                 created_at: str = "", created_from: str = "",
                 tags: Optional[list] = None, profile_type: str = "custom"):
        self.name = name
        self.description = description
        self.created_at = created_at or self._get_current_timestamp()
        self.created_from = created_from
        self.tags = tags or []
        self.profile_type = profile_type

    def _get_current_timestamp(self) -> str:
        import datetime
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> dict:
        """딕셔너리로 변환 (YAML 저장용)"""
        return {
            'profile_info': {
                'name': self.name,
                'description': self.description,
                'created_at': self.created_at,
                'created_from': self.created_from,
                'tags': self.tags
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ProfileMetadata':
        """딕셔너리에서 ProfileMetadata 객체 생성"""
        # 'profile' 섹션에서 직접 메타데이터 추출 (YAML 구조와 일치)
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            created_at=data.get('created_at', ''),
            created_from=data.get('created_from', ''),
            tags=data.get('tags', []),
            profile_type=data.get('profile_type', 'custom')
        )

    @classmethod
    def from_yaml_content(cls, yaml_content: str) -> 'ProfileMetadata':
        """YAML 내용에서 메타데이터 추출"""
        try:
            data = yaml.safe_load(yaml_content) or {}

            # profile 섹션이 있으면 해당 섹션에서 메타데이터 추출
            if 'profile' in data and isinstance(data['profile'], dict):
                profile_data = data['profile']
                return cls.from_dict(profile_data)
            else:
                # profile 섹션이 없으면 전체 데이터에서 메타데이터 추출 시도
                return cls.from_dict(data)

        except yaml.YAMLError as e:
            # YAML 파싱 실패 시 빈 메타데이터 반환
            print(f"YAML 파싱 실패: {e}")
            return cls()
        except Exception as e:
            # 기타 오류 시 빈 메타데이터 반환
            print(f"메타데이터 추출 실패: {e}")
            return cls()

    def to_yaml_string(self) -> str:
        """YAML 문자열로 변환"""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)

    def generate_display_name(self, profile_name: str) -> str:
        """콤보박스용 표시명 생성"""
        if self.name:
            return f"{self.name} ({profile_name})"
        else:
            return profile_name

    def is_custom_profile(self) -> bool:
        """커스텀 프로파일 여부 확인"""
        return bool(self.created_from)  # created_from이 있으면 커스텀 프로파일

    def add_tag(self, tag: str):
        """태그 추가"""
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """태그 제거"""
        if tag in self.tags:
            self.tags.remove(tag)

    def validate(self) -> tuple[bool, str]:
        """메타데이터 유효성 검증"""
        if not self.name.strip():
            return False, "프로파일 이름은 필수입니다"

        if len(self.name) > 100:
            return False, "프로파일 이름은 100자를 초과할 수 없습니다"

        if len(self.description) > 500:
            return False, "설명은 500자를 초과할 수 없습니다"

        # 태그 유효성 검사
        for tag in self.tags:
            if not isinstance(tag, str) or not tag.strip():
                return False, "태그는 비어있을 수 없습니다"
            if len(tag) > 50:
                return False, "태그는 50자를 초과할 수 없습니다"

        return True, "유효한 메타데이터입니다"
