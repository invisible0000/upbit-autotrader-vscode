"""
데이터베이스 설정 도메인 - 데이터베이스 프로필 엔터티

DDD Domain Layer의 핵심 엔터티로, 데이터베이스 프로필의 생명주기와
비즈니스 규칙을 관리합니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DatabaseProfile")

@dataclass(frozen=True)
class DatabaseProfile:
    """
    데이터베이스 프로필 엔터티

    단일 데이터베이스 인스턴스의 메타데이터와 설정 정보를 관리하는
    도메인 엔터티입니다.
    """

    profile_id: str
    name: str
    database_type: str  # 'settings', 'strategies', 'market_data'
    file_path: Path
    created_at: datetime
    last_accessed: Optional[datetime] = None
    is_active: bool = False
    size_bytes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """엔터티 생성 후 유효성 검증"""
        self._validate_business_rules()
        logger.debug(f"DatabaseProfile 생성됨: {self.name} ({self.database_type})")

    def _validate_business_rules(self) -> None:
        """도메인 비즈니스 규칙 검증"""
        if not self.profile_id or len(self.profile_id.strip()) == 0:
            raise ValueError("프로필 ID는 필수입니다")

        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("프로필 이름은 필수입니다")

        if self.database_type not in ['settings', 'strategies', 'market_data']:
            raise ValueError(f"지원하지 않는 데이터베이스 타입: {self.database_type}")

        if not self.file_path:
            raise ValueError("데이터베이스 파일 경로는 필수입니다")

        # 파일 확장자 검증
        if not str(self.file_path).endswith('.sqlite3'):
            raise ValueError("데이터베이스 파일은 .sqlite3 확장자여야 합니다")

        # 생성 시간 검증
        if self.created_at > datetime.now():
            raise ValueError("생성 시간은 미래일 수 없습니다")

        # 마지막 접근 시간 검증
        if self.last_accessed and self.last_accessed < self.created_at:
            raise ValueError("마지막 접근 시간은 생성 시간보다 이전일 수 없습니다")

    def is_file_exists(self) -> bool:
        """데이터베이스 파일 존재 여부 확인"""
        exists = self.file_path.exists()
        logger.debug(f"파일 존재 여부 확인 - {self.file_path}: {exists}")
        return exists

    def get_file_size(self) -> int:
        """데이터베이스 파일 크기 조회 (바이트)"""
        if not self.is_file_exists():
            logger.warning(f"파일이 존재하지 않음: {self.file_path}")
            return 0

        size = self.file_path.stat().st_size
        logger.debug(f"파일 크기 조회 - {self.file_path}: {size} bytes")
        return size

    def get_last_modified(self) -> Optional[datetime]:
        """데이터베이스 파일 마지막 수정 시간"""
        if not self.is_file_exists():
            return None

        modified = datetime.fromtimestamp(self.file_path.stat().st_mtime)
        logger.debug(f"마지막 수정 시간 - {self.file_path}: {modified}")
        return modified

    def mark_as_accessed(self) -> 'DatabaseProfile':
        """
        데이터베이스 접근 시간 업데이트

        Returns:
            새로운 DatabaseProfile 인스턴스 (불변 객체)
        """
        from dataclasses import replace

        now = datetime.now()
        updated_profile = replace(self, last_accessed=now)

        logger.debug(f"데이터베이스 접근 시간 업데이트: {self.name} -> {now}")
        return updated_profile

    def activate(self) -> 'DatabaseProfile':
        """
        데이터베이스 프로필 활성화

        Returns:
            활성화된 새로운 DatabaseProfile 인스턴스
        """
        from dataclasses import replace

        if not self.is_file_exists():
            raise ValueError(f"존재하지 않는 파일은 활성화할 수 없습니다: {self.file_path}")

        activated_profile = replace(self, is_active=True, last_accessed=datetime.now())
        logger.info(f"데이터베이스 프로필 활성화: {self.name}")
        return activated_profile

    def deactivate(self) -> 'DatabaseProfile':
        """
        데이터베이스 프로필 비활성화

        Returns:
            비활성화된 새로운 DatabaseProfile 인스턴스
        """
        from dataclasses import replace

        deactivated_profile = replace(self, is_active=False)
        logger.info(f"데이터베이스 프로필 비활성화: {self.name}")
        return deactivated_profile

    def update_metadata(self, metadata: Dict[str, Any]) -> 'DatabaseProfile':
        """
        프로필 메타데이터 업데이트

        Args:
            metadata: 새로운 메타데이터

        Returns:
            메타데이터가 업데이트된 새로운 DatabaseProfile 인스턴스
        """
        from dataclasses import replace

        current_metadata = self.metadata or {}
        updated_metadata = {**current_metadata, **metadata}

        updated_profile = replace(self, metadata=updated_metadata)
        logger.debug(f"메타데이터 업데이트: {self.name} - {list(metadata.keys())}")
        return updated_profile

    def get_display_info(self) -> Dict[str, Any]:
        """UI 표시용 정보 반환"""
        return {
            'name': self.name,
            'type': self.database_type,
            'path': str(self.file_path),
            'size': self.get_file_size(),
            'exists': self.is_file_exists(),
            'active': self.is_active,
            'last_accessed': self.last_accessed,
            'last_modified': self.get_last_modified()
        }

    def __str__(self) -> str:
        return f"DatabaseProfile(name='{self.name}', type='{self.database_type}', active={self.is_active})"

    def __repr__(self) -> str:
        return (f"DatabaseProfile(profile_id='{self.profile_id}', name='{self.name}', "
                f"database_type='{self.database_type}', file_path='{self.file_path}', "
                f"is_active={self.is_active})")
