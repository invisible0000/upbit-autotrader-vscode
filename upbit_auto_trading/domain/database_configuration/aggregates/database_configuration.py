"""
데이터베이스 설정 도메인 - 데이터베이스 설정 집합체

데이터베이스 설정 관련 엔터티들을 통합 관리하는 집합체 루트입니다.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..entities.database_profile import DatabaseProfile
from ..entities.backup_record import BackupRecord, BackupType, BackupStatus
from ..value_objects.database_path import DatabasePath

logger = create_component_logger("DatabaseConfiguration")

@dataclass
class DatabaseConfiguration:
    """
    데이터베이스 설정 집합체 루트

    데이터베이스 프로필들과 백업 기록들을 통합 관리하며,
    데이터베이스 설정 관련 비즈니스 규칙을 강제합니다.
    """

    configuration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    profiles: Dict[str, DatabaseProfile] = field(default_factory=dict)
    backup_records: Dict[str, BackupRecord] = field(default_factory=dict)
    active_profile_ids: Dict[str, str] = field(default_factory=dict)  # type -> profile_id
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """집합체 생성 후 초기화"""
        logger.info(f"DatabaseConfiguration 집합체 생성됨: {self.configuration_id}")
        self._validate_consistency()

    def _validate_consistency(self) -> None:
        """집합체 일관성 검증"""
        # 활성 프로필 검증
        for db_type, profile_id in self.active_profile_ids.items():
            if profile_id not in self.profiles:
                raise ValueError(f"활성 프로필 {profile_id}가 존재하지 않습니다")

            profile = self.profiles[profile_id]
            if profile.database_type != db_type:
                raise ValueError(f"활성 프로필 타입 불일치: {db_type} != {profile.database_type}")

            if not profile.is_active:
                raise ValueError(f"비활성 프로필이 활성으로 설정됨: {profile_id}")

        # 중복 활성 프로필 검증
        for db_type in ['settings', 'strategies', 'market_data']:
            active_profiles = [p for p in self.profiles.values()
                             if p.database_type == db_type and p.is_active]
            if len(active_profiles) > 1:
                raise ValueError(f"{db_type} 타입에 여러 활성 프로필이 존재합니다")

        logger.debug("집합체 일관성 검증 완료")

    def add_database_profile(self, profile: DatabaseProfile) -> None:
        """
        데이터베이스 프로필 추가

        Args:
            profile: 추가할 데이터베이스 프로필
        """
        if profile.profile_id in self.profiles:
            raise ValueError(f"이미 존재하는 프로필 ID: {profile.profile_id}")

        # 동일한 경로의 프로필 존재 확인
        for existing_profile in self.profiles.values():
            if existing_profile.file_path == profile.file_path:
                raise ValueError(f"동일한 경로의 프로필이 이미 존재합니다: {profile.file_path}")

        # 활성 프로필인 경우 기존 활성 프로필 비활성화
        if profile.is_active:
            self._deactivate_profiles_of_type(profile.database_type)
            self.active_profile_ids[profile.database_type] = profile.profile_id

        self.profiles[profile.profile_id] = profile
        self._update_modified_time()

        logger.info(f"데이터베이스 프로필 추가됨: {profile.name} ({profile.database_type})")

    def remove_database_profile(self, profile_id: str) -> None:
        """
        데이터베이스 프로필 제거

        Args:
            profile_id: 제거할 프로필 ID
        """
        if profile_id not in self.profiles:
            raise ValueError(f"존재하지 않는 프로필 ID: {profile_id}")

        profile = self.profiles[profile_id]

        # 활성 프로필인 경우 활성 상태 해제
        if profile.is_active:
            if self.active_profile_ids.get(profile.database_type) == profile_id:
                del self.active_profile_ids[profile.database_type]

        # 관련 백업 기록들도 제거
        backup_ids_to_remove = [
            backup_id for backup_id, backup in self.backup_records.items()
            if backup.source_profile_id == profile_id
        ]

        for backup_id in backup_ids_to_remove:
            del self.backup_records[backup_id]
            logger.debug(f"관련 백업 기록 제거됨: {backup_id}")

        del self.profiles[profile_id]
        self._update_modified_time()

        logger.info(f"데이터베이스 프로필 제거됨: {profile.name} (백업 기록 {len(backup_ids_to_remove)}개도 함께 제거)")

    def activate_database_profile(self, profile_id: str) -> None:
        """
        데이터베이스 프로필 활성화

        Args:
            profile_id: 활성화할 프로필 ID
        """
        if profile_id not in self.profiles:
            raise ValueError(f"존재하지 않는 프로필 ID: {profile_id}")

        profile = self.profiles[profile_id]

        # 파일 존재 여부 확인
        if not profile.is_file_exists():
            raise ValueError(f"데이터베이스 파일이 존재하지 않습니다: {profile.file_path}")

        # 기존 활성 프로필 비활성화
        self._deactivate_profiles_of_type(profile.database_type)

        # 프로필 활성화
        activated_profile = profile.activate()
        self.profiles[profile_id] = activated_profile
        self.active_profile_ids[profile.database_type] = profile_id

        self._update_modified_time()
        logger.info(f"데이터베이스 프로필 활성화됨: {profile.name}")

    def deactivate_database_profile(self, profile_id: str) -> None:
        """
        데이터베이스 프로필 비활성화

        Args:
            profile_id: 비활성화할 프로필 ID
        """
        if profile_id not in self.profiles:
            raise ValueError(f"존재하지 않는 프로필 ID: {profile_id}")

        profile = self.profiles[profile_id]

        if not profile.is_active:
            logger.warning(f"이미 비활성 상태인 프로필: {profile.name}")
            return

        # 프로필 비활성화
        deactivated_profile = profile.deactivate()
        self.profiles[profile_id] = deactivated_profile

        # 활성 프로필 목록에서 제거
        if self.active_profile_ids.get(profile.database_type) == profile_id:
            del self.active_profile_ids[profile.database_type]

        self._update_modified_time()
        logger.info(f"데이터베이스 프로필 비활성화됨: {profile.name}")

    def _deactivate_profiles_of_type(self, database_type: str) -> None:
        """특정 타입의 모든 프로필 비활성화"""
        for profile_id, profile in self.profiles.items():
            if profile.database_type == database_type and profile.is_active:
                deactivated_profile = profile.deactivate()
                self.profiles[profile_id] = deactivated_profile
                logger.debug(f"기존 프로필 비활성화됨: {profile.name}")

        # 활성 프로필 목록에서 제거
        if database_type in self.active_profile_ids:
            del self.active_profile_ids[database_type]

    def get_active_profile(self, database_type: str) -> Optional[DatabaseProfile]:
        """
        특정 타입의 활성 프로필 조회

        Args:
            database_type: 데이터베이스 타입

        Returns:
            활성 프로필 (없으면 None)
        """
        active_profile_id = self.active_profile_ids.get(database_type)
        if not active_profile_id:
            return None

        active_profile = self.profiles.get(active_profile_id)
        logger.debug(f"활성 프로필 조회 - {database_type}: {active_profile.name if active_profile else 'None'}")
        return active_profile

    def get_profiles_by_type(self, database_type: str) -> List[DatabaseProfile]:
        """
        특정 타입의 모든 프로필 조회

        Args:
            database_type: 데이터베이스 타입

        Returns:
            해당 타입의 프로필 목록
        """
        profiles = [p for p in self.profiles.values() if p.database_type == database_type]
        logger.debug(f"타입별 프로필 조회 - {database_type}: {len(profiles)}개")
        return profiles

    def create_backup(self, profile_id: str, backup_type: BackupType = BackupType.MANUAL) -> str:
        """
        데이터베이스 백업 생성

        Args:
            profile_id: 백업할 프로필 ID
            backup_type: 백업 타입

        Returns:
            생성된 백업 기록 ID
        """
        if profile_id not in self.profiles:
            raise ValueError(f"존재하지 않는 프로필 ID: {profile_id}")

        profile = self.profiles[profile_id]

        if not profile.is_file_exists():
            raise ValueError(f"백업할 파일이 존재하지 않습니다: {profile.file_path}")

        # 백업 파일 경로 생성
        db_path = DatabasePath(profile.file_path)
        backup_path = db_path.create_backup_path()

        # 백업 기록 생성
        backup_id = str(uuid.uuid4())
        backup_record = BackupRecord(
            backup_id=backup_id,
            source_profile_id=profile_id,
            source_database_type=profile.database_type,
            backup_file_path=backup_path.path,
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            created_at=datetime.now()
        )

        self.backup_records[backup_id] = backup_record
        self._update_modified_time()

        logger.info(f"백업 기록 생성됨: {backup_id} for {profile.name}")
        return backup_id

    def get_backup_records_for_profile(self, profile_id: str) -> List[BackupRecord]:
        """
        특정 프로필의 백업 기록 조회

        Args:
            profile_id: 프로필 ID

        Returns:
            백업 기록 목록
        """
        records = [r for r in self.backup_records.values() if r.source_profile_id == profile_id]
        logger.debug(f"프로필 백업 기록 조회 - {profile_id}: {len(records)}개")
        return records

    def update_backup_status(self, backup_id: str, status: BackupStatus, **kwargs) -> None:
        """
        백업 상태 업데이트

        Args:
            backup_id: 백업 ID
            status: 새로운 상태
            **kwargs: 상태별 추가 정보
        """
        if backup_id not in self.backup_records:
            raise ValueError(f"존재하지 않는 백업 ID: {backup_id}")

        backup_record = self.backup_records[backup_id]

        if status == BackupStatus.RUNNING:
            updated_backup = backup_record.mark_as_running()
        elif status == BackupStatus.COMPLETED:
            file_size = kwargs.get('file_size', 0)
            checksum = kwargs.get('checksum')
            updated_backup = backup_record.mark_as_completed(file_size, checksum)
        elif status == BackupStatus.FAILED:
            error_message = kwargs.get('error_message', '알 수 없는 오류')
            updated_backup = backup_record.mark_as_failed(error_message)
        elif status == BackupStatus.CORRUPTED:
            reason = kwargs.get('reason', '알 수 없는 손상')
            updated_backup = backup_record.mark_as_corrupted(reason)
        else:
            raise ValueError(f"지원하지 않는 백업 상태: {status}")

        self.backup_records[backup_id] = updated_backup
        self._update_modified_time()

        logger.info(f"백업 상태 업데이트됨: {backup_id} -> {status.value}")

    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """
        오래된 백업 정리

        Args:
            retention_days: 보존 기간 (일)

        Returns:
            정리된 백업 수
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        backup_ids_to_remove = []
        for backup_id, backup in self.backup_records.items():
            if backup.created_at < cutoff_date:
                # 백업 파일도 삭제
                if backup.is_backup_file_exists():
                    try:
                        backup.backup_file_path.unlink()
                        logger.debug(f"백업 파일 삭제됨: {backup.backup_file_path}")
                    except Exception as e:
                        logger.warning(f"백업 파일 삭제 실패: {e}")

                backup_ids_to_remove.append(backup_id)

        # 백업 기록 제거
        for backup_id in backup_ids_to_remove:
            del self.backup_records[backup_id]

        if backup_ids_to_remove:
            self._update_modified_time()

        logger.info(f"오래된 백업 정리 완료: {len(backup_ids_to_remove)}개 제거")
        return len(backup_ids_to_remove)

    def get_configuration_summary(self) -> Dict[str, Any]:
        """설정 요약 정보 반환"""
        summary = {
            'configuration_id': self.configuration_id,
            'total_profiles': len(self.profiles),
            'active_profiles': len(self.active_profile_ids),
            'total_backups': len(self.backup_records),
            'created_at': self.created_at,
            'last_modified': self.last_modified,
            'profiles_by_type': {},
            'backup_status_summary': {}
        }

        # 타입별 프로필 수
        for db_type in ['settings', 'strategies', 'market_data']:
            profiles = self.get_profiles_by_type(db_type)
            active_profile = self.get_active_profile(db_type)
            summary['profiles_by_type'][db_type] = {
                'total': len(profiles),
                'active': active_profile.name if active_profile else None
            }

        # 백업 상태별 수
        for status in BackupStatus:
            count = len([b for b in self.backup_records.values() if b.status == status])
            summary['backup_status_summary'][status.value] = count

        logger.debug(f"설정 요약 정보 생성됨: {summary}")
        return summary

    def _update_modified_time(self) -> None:
        """마지막 수정 시간 업데이트"""
        self.last_modified = datetime.now()

    def __str__(self) -> str:
        return f"DatabaseConfiguration(id='{self.configuration_id}', profiles={len(self.profiles)}, backups={len(self.backup_records)})"

    def __repr__(self) -> str:
        return (f"DatabaseConfiguration(configuration_id='{self.configuration_id}', "
                f"profiles={len(self.profiles)}, backup_records={len(self.backup_records)}, "
                f"active_profiles={len(self.active_profile_ids)})")
