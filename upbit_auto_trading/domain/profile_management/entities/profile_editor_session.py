"""
Profile Editor Session Entity
=============================

프로파일 편집 세션을 관리하는 Domain Entity입니다.
Temp 파일 기반 안전한 편집 워크플로우를 지원합니다.

DDD Entity 특징:
- 고유한 식별자(session_id)를 가짐
- 상태 변경이 가능한 가변 객체
- 비즈니스 규칙과 불변 조건을 캡슐화
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("ProfileEditorSession")

@dataclass
class ProfileEditorSession:
    """
    프로파일 편집 세션 엔티티

    Attributes:
        session_id: 세션 고유 식별자
        profile_name: 편집 중인 프로파일명
        is_new_profile: 신규 프로파일 생성 여부
        temp_file_path: 임시 파일 경로 (편집 중)
        original_content: 원본 YAML 내용
        current_content: 현재 편집 중인 내용
        created_at: 세션 생성 시각
        last_modified: 마지막 수정 시각
    """

    # Entity 식별자
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 프로파일 정보
    profile_name: str = ""
    is_new_profile: bool = False

    # 파일 경로 및 내용
    temp_file_path: Optional[str] = None
    original_content: str = ""
    current_content: str = ""

    # 시간 정보
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """엔티티 초기화 후 검증"""
        self._validate_session_state()
        logger.debug(f"ProfileEditorSession 생성됨: {self.session_id[:8]}...")

    def _validate_session_state(self) -> None:
        """세션 상태 불변 조건 검증"""
        if not self.profile_name.strip():
            raise ValueError("프로파일명은 필수입니다")

        if self.is_new_profile and self.original_content:
            raise ValueError("신규 프로파일은 원본 내용이 없어야 합니다")

        if not self.is_new_profile and not self.original_content:
            raise ValueError("기존 프로파일은 원본 내용이 있어야 합니다")

    def update_content(self, new_content: str) -> None:
        """편집 내용 업데이트"""
        if new_content != self.current_content:
            self.current_content = new_content
            self.last_modified = datetime.now()
            logger.debug(f"세션 {self.session_id[:8]} 내용 업데이트됨")

    def set_temp_file_path(self, temp_path: str) -> None:
        """임시 파일 경로 설정"""
        self.temp_file_path = temp_path
        self.last_modified = datetime.now()
        logger.debug(f"세션 {self.session_id[:8]} 임시 파일 설정: {temp_path}")

    def is_content_modified(self) -> bool:
        """내용이 수정되었는지 확인"""
        return self.current_content != self.original_content

    def has_temp_file(self) -> bool:
        """임시 파일이 있는지 확인"""
        return self.temp_file_path is not None

    def get_session_duration(self) -> float:
        """세션 지속 시간 (초 단위)"""
        return (datetime.now() - self.created_at).total_seconds()

    def reset_to_original(self) -> None:
        """원본 내용으로 되돌리기"""
        self.current_content = self.original_content
        self.last_modified = datetime.now()
        logger.info(f"세션 {self.session_id[:8]} 원본으로 되돌림")

    def finalize_session(self) -> None:
        """세션 완료 처리"""
        logger.info(f"세션 {self.session_id[:8]} 완료 - 지속시간: {self.get_session_duration():.1f}초")

    def __str__(self) -> str:
        """세션 정보 문자열 표현"""
        status = "신규" if self.is_new_profile else "편집"
        modified = "수정됨" if self.is_content_modified() else "미수정"
        return f"ProfileEditorSession({self.profile_name}, {status}, {modified})"

    def __repr__(self) -> str:
        """세션 디버깅 표현"""
        return (f"ProfileEditorSession(session_id='{self.session_id[:8]}...', "
                f"profile_name='{self.profile_name}', "
                f"is_new_profile={self.is_new_profile}, "
                f"is_modified={self.is_content_modified()})")
