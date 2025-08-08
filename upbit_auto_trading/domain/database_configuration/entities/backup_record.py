"""
데이터베이스 설정 도메인 - 백업 기록 엔터티

백업 작업의 생명주기와 메타데이터를 관리하는 도메인 엔터티입니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("BackupRecord")


class BackupStatus(Enum):
    """백업 상태 열거형"""
    PENDING = "pending"      # 대기 중
    RUNNING = "running"      # 진행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"        # 실패
    CORRUPTED = "corrupted"  # 손상됨


class BackupType(Enum):
    """백업 타입 열거형"""
    MANUAL = "manual"        # 수동 백업
    AUTOMATIC = "automatic"  # 자동 백업
    SCHEDULED = "scheduled"  # 예약 백업


@dataclass(frozen=True)
class BackupRecord:
    """
    백업 기록 엔터티

    데이터베이스 백업 작업의 메타데이터와 생명주기를 관리합니다.
    """

    backup_id: str
    source_profile_id: str
    source_database_type: str
    backup_file_path: Path
    backup_type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """엔터티 생성 후 유효성 검증"""
        self._validate_business_rules()
        logger.debug(f"BackupRecord 생성됨: {self.backup_id} ({self.status.value})")

    def _validate_business_rules(self) -> None:
        """도메인 비즈니스 규칙 검증"""
        if not self.backup_id or len(self.backup_id.strip()) == 0:
            raise ValueError("백업 ID는 필수입니다")

        if not self.source_profile_id or len(self.source_profile_id.strip()) == 0:
            raise ValueError("소스 프로필 ID는 필수입니다")

        if self.source_database_type not in ['settings', 'strategies', 'market_data']:
            raise ValueError(f"지원하지 않는 데이터베이스 타입: {self.source_database_type}")

        if not self.backup_file_path:
            raise ValueError("백업 파일 경로는 필수입니다")

        # 파일 확장자 검증
        if not str(self.backup_file_path).endswith('.sqlite3'):
            raise ValueError("백업 파일은 .sqlite3 확장자여야 합니다")

        # 상태 일관성 검증
        if self.status == BackupStatus.COMPLETED and not self.completed_at:
            raise ValueError("완료된 백업은 완료 시간이 필요합니다")

        if self.status == BackupStatus.FAILED and not self.error_message:
            raise ValueError("실패한 백업은 에러 메시지가 필요합니다")

        # 시간 일관성 검증
        if self.completed_at and self.completed_at < self.created_at:
            raise ValueError("완료 시간은 생성 시간보다 이전일 수 없습니다")

    def is_backup_file_exists(self) -> bool:
        """백업 파일 존재 여부 확인"""
        exists = self.backup_file_path.exists()
        logger.debug(f"백업 파일 존재 여부 확인 - {self.backup_file_path}: {exists}")
        return exists

    def get_backup_file_size(self) -> int:
        """백업 파일 크기 조회 (바이트)"""
        if not self.is_backup_file_exists():
            logger.warning(f"백업 파일이 존재하지 않음: {self.backup_file_path}")
            return 0

        size = self.backup_file_path.stat().st_size
        logger.debug(f"백업 파일 크기 조회 - {self.backup_file_path}: {size} bytes")
        return size

    def calculate_duration(self) -> Optional[float]:
        """백업 소요 시간 계산 (초)"""
        if not self.completed_at:
            return None

        duration = (self.completed_at - self.created_at).total_seconds()
        logger.debug(f"백업 소요 시간 계산: {self.backup_id} - {duration}초")
        return duration

    def mark_as_running(self) -> 'BackupRecord':
        """
        백업을 실행 중 상태로 변경

        Returns:
            실행 중 상태의 새로운 BackupRecord 인스턴스
        """
        from dataclasses import replace

        if self.status != BackupStatus.PENDING:
            raise ValueError(f"대기 중 상태에서만 실행 중으로 변경 가능합니다: {self.status}")

        running_backup = replace(self, status=BackupStatus.RUNNING)
        logger.info(f"백업 실행 시작: {self.backup_id}")
        return running_backup

    def mark_as_completed(self, file_size: int, checksum: Optional[str] = None) -> 'BackupRecord':
        """
        백업을 완료 상태로 변경

        Args:
            file_size: 백업 파일 크기
            checksum: 파일 체크섬 (선택적)

        Returns:
            완료 상태의 새로운 BackupRecord 인스턴스
        """
        from dataclasses import replace

        if self.status not in [BackupStatus.PENDING, BackupStatus.RUNNING]:
            raise ValueError(f"대기 중 또는 실행 중 상태에서만 완료로 변경 가능합니다: {self.status}")

        if not self.is_backup_file_exists():
            raise ValueError(f"백업 파일이 존재하지 않습니다: {self.backup_file_path}")

        completed_backup = replace(
            self,
            status=BackupStatus.COMPLETED,
            completed_at=datetime.now(),
            file_size_bytes=file_size,
            checksum=checksum,
            error_message=None
        )

        logger.info(f"백업 완료: {self.backup_id} - {file_size} bytes")
        return completed_backup

    def mark_as_failed(self, error_message: str) -> 'BackupRecord':
        """
        백업을 실패 상태로 변경

        Args:
            error_message: 실패 원인

        Returns:
            실패 상태의 새로운 BackupRecord 인스턴스
        """
        from dataclasses import replace

        if self.status in [BackupStatus.COMPLETED, BackupStatus.CORRUPTED]:
            raise ValueError(f"완료 또는 손상 상태에서는 실패로 변경할 수 없습니다: {self.status}")

        failed_backup = replace(
            self,
            status=BackupStatus.FAILED,
            completed_at=datetime.now(),
            error_message=error_message
        )

        logger.error(f"백업 실패: {self.backup_id} - {error_message}")
        return failed_backup

    def mark_as_corrupted(self, reason: str) -> 'BackupRecord':
        """
        백업을 손상된 상태로 변경

        Args:
            reason: 손상 원인

        Returns:
            손상된 상태의 새로운 BackupRecord 인스턴스
        """
        from dataclasses import replace

        corrupted_backup = replace(
            self,
            status=BackupStatus.CORRUPTED,
            error_message=reason
        )

        logger.warning(f"백업 손상됨: {self.backup_id} - {reason}")
        return corrupted_backup

    def verify_integrity(self, expected_checksum: Optional[str] = None) -> bool:
        """
        백업 파일 무결성 검증

        Args:
            expected_checksum: 예상 체크섬 (선택적)

        Returns:
            무결성 검증 결과
        """
        if not self.is_backup_file_exists():
            logger.warning(f"백업 파일이 존재하지 않아 무결성 검증 불가: {self.backup_file_path}")
            return False

        if self.status != BackupStatus.COMPLETED:
            logger.warning(f"완료되지 않은 백업의 무결성 검증: {self.backup_id}")
            return False

        # 파일 크기 검증
        actual_size = self.get_backup_file_size()
        if self.file_size_bytes and actual_size != self.file_size_bytes:
            logger.error(f"백업 파일 크기 불일치: 예상={self.file_size_bytes}, 실제={actual_size}")
            return False

        # 체크섬 검증 (있는 경우)
        if expected_checksum and self.checksum and expected_checksum != self.checksum:
            logger.error(f"백업 파일 체크섬 불일치: 예상={expected_checksum}, 실제={self.checksum}")
            return False

        logger.debug(f"백업 파일 무결성 검증 성공: {self.backup_id}")
        return True

    def get_display_info(self) -> Dict[str, Any]:
        """UI 표시용 정보 반환"""
        return {
            'backup_id': self.backup_id,
            'source_type': self.source_database_type,
            'backup_type': self.backup_type.value,
            'status': self.status.value,
            'file_path': str(self.backup_file_path),
            'file_size': self.file_size_bytes,
            'created_at': self.created_at,
            'completed_at': self.completed_at,
            'duration': self.calculate_duration(),
            'exists': self.is_backup_file_exists(),
            'error_message': self.error_message
        }

    def __str__(self) -> str:
        return f"BackupRecord(id='{self.backup_id}', status='{self.status.value}', type='{self.backup_type.value}')"

    def __repr__(self) -> str:
        return (f"BackupRecord(backup_id='{self.backup_id}', source_profile_id='{self.source_profile_id}', "
                f"status='{self.status.value}', backup_type='{self.backup_type.value}', "
                f"created_at='{self.created_at}')")
