"""
데이터베이스 설정 도메인 - 데이터베이스 경로 값 객체

데이터베이스 파일 경로의 유효성과 비즈니스 규칙을 관리하는 값 객체입니다.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DatabasePath")


@dataclass(frozen=True)
class DatabasePath:
    """
    데이터베이스 경로 값 객체

    데이터베이스 파일 경로의 유효성 검증과 비즈니스 규칙을 캡슐화합니다.
    """

    path: Path

    def __post_init__(self):
        """값 객체 생성 후 유효성 검증"""
        self._validate_path()
        logger.debug(f"DatabasePath 생성됨: {self.path}")

    def _validate_path(self) -> None:
        """경로 유효성 검증"""
        if not self.path:
            raise ValueError("데이터베이스 경로는 필수입니다")

        # 절대 경로 검증
        if not self.path.is_absolute():
            raise ValueError("데이터베이스 경로는 절대 경로여야 합니다")

        # 파일 확장자 검증
        if self.path.suffix != '.sqlite3':
            raise ValueError("데이터베이스 파일은 .sqlite3 확장자여야 합니다")

        # 파일명 검증
        if not self.path.name or self.path.name.startswith('.'):
            raise ValueError("유효하지 않은 데이터베이스 파일명입니다")

        # 예약된 이름 검증
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

        filename_without_ext = self.path.stem.upper()
        if filename_without_ext in reserved_names:
            raise ValueError(f"예약된 파일명은 사용할 수 없습니다: {filename_without_ext}")

        # 부모 디렉토리 검증
        if not self.path.parent:
            raise ValueError("유효하지 않은 부모 디렉토리입니다")

    def exists(self) -> bool:
        """파일 존재 여부 확인"""
        exists = self.path.exists()
        logger.debug(f"파일 존재 여부 - {self.path}: {exists}")
        return exists

    def is_readable(self) -> bool:
        """파일 읽기 가능 여부 확인"""
        if not self.exists():
            return False

        try:
            readable = os.access(self.path, os.R_OK)
            logger.debug(f"파일 읽기 가능 - {self.path}: {readable}")
            return readable
        except Exception as e:
            logger.warning(f"파일 읽기 권한 확인 실패: {e}")
            return False

    def is_valid(self) -> bool:
        """경로 유효성 전체 검사"""
        try:
            # 기본 경로 유효성 (이미 __post_init__에서 검증됨)
            # 추가 비즈니스 규칙 검증
            return (self.path is not None and
                    self.path.suffix == '.sqlite3' and
                    self.validate_database_name_convention())
        except Exception as e:
            logger.warning(f"경로 유효성 검사 실패: {e}")
            return False

    def is_writable(self) -> bool:
        """파일 쓰기 가능 여부 확인"""
        if self.exists():
            try:
                writable = os.access(self.path, os.W_OK)
                logger.debug(f"파일 쓰기 가능 - {self.path}: {writable}")
                return writable
            except Exception as e:
                logger.warning(f"파일 쓰기 권한 확인 실패: {e}")
                return False
        else:
            # 파일이 없으면 부모 디렉토리의 쓰기 권한 확인
            try:
                parent_writable = os.access(self.path.parent, os.W_OK)
                logger.debug(f"부모 디렉토리 쓰기 가능 - {self.path.parent}: {parent_writable}")
                return parent_writable
            except Exception as e:
                logger.warning(f"부모 디렉토리 쓰기 권한 확인 실패: {e}")
                return False

    def ensure_parent_directory(self) -> bool:
        """부모 디렉토리 생성 (없는 경우)"""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"부모 디렉토리 생성/확인됨: {self.path.parent}")
            return True
        except Exception as e:
            logger.error(f"부모 디렉토리 생성 실패: {e}")
            return False

    def get_file_size(self) -> Optional[int]:
        """파일 크기 조회 (바이트)"""
        if not self.exists():
            return None

        try:
            size = self.path.stat().st_size
            logger.debug(f"파일 크기 - {self.path}: {size} bytes")
            return size
        except Exception as e:
            logger.warning(f"파일 크기 조회 실패: {e}")
            return None

    def get_relative_to(self, base_path: Path) -> Optional[Path]:
        """기준 경로로부터의 상대 경로 반환"""
        try:
            relative = self.path.relative_to(base_path)
            logger.debug(f"상대 경로 계산 - 기준: {base_path}, 결과: {relative}")
            return relative
        except ValueError:
            logger.debug(f"상대 경로 계산 불가 - {self.path}는 {base_path}의 하위 경로가 아님")
            return None

    def is_same_directory(self, other_path: 'DatabasePath') -> bool:
        """다른 경로와 같은 디렉토리에 있는지 확인"""
        same_dir = self.path.parent == other_path.path.parent
        logger.debug(f"같은 디렉토리 확인 - {self.path.parent} == {other_path.path.parent}: {same_dir}")
        return same_dir

    def create_backup_path(self, suffix: str = "") -> 'DatabasePath':
        """백업 경로 생성"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.path.stem}_backup_{timestamp}{suffix}.sqlite3"
        backup_path = self.path.parent / backup_name

        backup_db_path = DatabasePath(backup_path)
        logger.debug(f"백업 경로 생성: {self.path} -> {backup_path}")
        return backup_db_path

    def create_temp_path(self) -> 'DatabasePath':
        """임시 파일 경로 생성"""
        import uuid

        temp_name = f"{self.path.stem}_temp_{uuid.uuid4().hex[:8]}.sqlite3"
        temp_path = self.path.parent / temp_name

        temp_db_path = DatabasePath(temp_path)
        logger.debug(f"임시 경로 생성: {self.path} -> {temp_path}")
        return temp_db_path

    def validate_database_name_convention(self) -> bool:
        """데이터베이스 이름 규칙 검증"""
        filename = self.path.stem

        # 표준 데이터베이스 이름 패턴
        standard_names = ['settings', 'strategies', 'market_data']

        # 백업 파일 패턴 (예: settings_backup_20250101_120000)
        import re
        backup_pattern = r'^(settings|strategies|market_data)_backup_\d{8}_\d{6}$'

        # 임시 파일 패턴 (예: settings_temp_a1b2c3d4)
        temp_pattern = r'^(settings|strategies|market_data)_temp_[a-f0-9]{8}$'

        is_standard = filename in standard_names
        is_backup = bool(re.match(backup_pattern, filename))
        is_temp = bool(re.match(temp_pattern, filename))

        is_valid = is_standard or is_backup or is_temp

        logger.debug(f"데이터베이스 이름 규칙 검증 - {filename}: {is_valid} "
                    f"(표준: {is_standard}, 백업: {is_backup}, 임시: {is_temp})")
        return is_valid

    def to_string(self) -> str:
        """문자열 표현 반환"""
        return str(self.path)

    def __str__(self) -> str:
        return str(self.path)

    def __repr__(self) -> str:
        return f"DatabasePath('{self.path}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, DatabasePath):
            return False
        return self.path == other.path

    def __hash__(self) -> int:
        return hash(self.path)
