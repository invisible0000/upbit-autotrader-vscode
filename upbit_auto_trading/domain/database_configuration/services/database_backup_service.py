"""
데이터베이스 설정 도메인 - 데이터베이스 백업 서비스

데이터베이스 백업과 관련된 도메인 비즈니스 로직을 처리하는 서비스입니다.
"""

import shutil
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..entities.database_profile import DatabaseProfile
from ..entities.backup_record import BackupRecord, BackupType, BackupStatus
from ..value_objects.database_path import DatabasePath
from ..value_objects.database_type import DatabaseType

logger = create_component_logger("DatabaseBackupService")

class DatabaseBackupService:
    """
    데이터베이스 백업 도메인 서비스

    데이터베이스 백업 생성, 복원, 검증 등의 도메인 로직을 담당합니다.
    """

    def __init__(self):
        logger.debug("DatabaseBackupService 초기화됨")

    def create_backup(self, profile: DatabaseProfile, backup_type: BackupType = BackupType.MANUAL) -> BackupRecord:
        """
        데이터베이스 백업 생성

        Args:
            profile: 백업할 데이터베이스 프로필
            backup_type: 백업 타입

        Returns:
            백업 기록
        """
        logger.info(f"백업 생성 시작: {profile.name}")

        # 소스 파일 검증
        if not profile.is_file_exists():
            raise ValueError(f"백업할 파일이 존재하지 않습니다: {profile.file_path}")

        # 백업 경로 생성
        source_path = DatabasePath(profile.file_path)
        backup_path = source_path.create_backup_path()

        # 백업 디렉토리 생성
        if not backup_path.ensure_parent_directory():
            raise RuntimeError(f"백업 디렉토리 생성 실패: {backup_path.path.parent}")

        try:
            # 파일 복사
            shutil.copy2(profile.file_path, backup_path.path)
            logger.debug(f"파일 복사 완료: {profile.file_path} -> {backup_path.path}")

            # 백업 파일 검증
            if not backup_path.exists():
                raise RuntimeError("백업 파일 생성 실패")

            # 체크섬 계산
            checksum = self._calculate_file_checksum(backup_path.path)
            file_size = backup_path.get_file_size() or 0

            # 백업 기록 생성
            import uuid
            backup_record = BackupRecord(
                backup_id=str(uuid.uuid4()),
                source_profile_id=profile.profile_id,
                source_database_type=profile.database_type,
                backup_file_path=backup_path.path,
                backup_type=backup_type,
                status=BackupStatus.COMPLETED,
                created_at=datetime.now(),
                completed_at=datetime.now(),
                file_size_bytes=file_size,
                checksum=checksum
            )

            logger.info(f"백업 생성 완료: {backup_record.backup_id} ({file_size} bytes)")
            return backup_record

        except Exception as e:
            logger.error(f"백업 생성 실패: {e}")

            # 실패한 백업 파일 정리
            if backup_path.exists():
                try:
                    backup_path.path.unlink()
                    logger.debug("실패한 백업 파일 정리됨")
                except Exception as cleanup_error:
                    logger.warning(f"백업 파일 정리 실패: {cleanup_error}")

            raise RuntimeError(f"백업 생성 실패: {e}") from e

    def restore_backup(self, backup_record: BackupRecord, target_profile: DatabaseProfile) -> bool:
        """
        백업 복원

        Args:
            backup_record: 복원할 백업 기록
            target_profile: 복원 대상 프로필

        Returns:
            복원 성공 여부
        """
        logger.info(f"백업 복원 시작: {backup_record.backup_id} -> {target_profile.name}")

        # 백업 파일 검증
        if not backup_record.is_backup_file_exists():
            raise ValueError(f"백업 파일이 존재하지 않습니다: {backup_record.backup_file_path}")

        if backup_record.status != BackupStatus.COMPLETED:
            raise ValueError(f"완료되지 않은 백업은 복원할 수 없습니다: {backup_record.status}")

        # 타입 호환성 검증
        if backup_record.source_database_type != target_profile.database_type:
            raise ValueError(f"데이터베이스 타입 불일치: {backup_record.source_database_type} != {target_profile.database_type}")

        # 백업 무결성 검증
        if not self.verify_backup_integrity(backup_record):
            raise ValueError("백업 파일 무결성 검증 실패")

        try:
            # 기존 파일 백업 (있는 경우)
            target_path = DatabasePath(target_profile.file_path)
            temp_backup_path = None

            if target_path.exists():
                temp_backup_path = target_path.create_temp_path()
                shutil.copy2(target_profile.file_path, temp_backup_path.path)
                logger.debug(f"기존 파일 임시 백업: {temp_backup_path.path}")

            # 백업 파일 복원
            target_path.ensure_parent_directory()
            shutil.copy2(backup_record.backup_file_path, target_profile.file_path)
            logger.debug(f"백업 복원 완료: {backup_record.backup_file_path} -> {target_profile.file_path}")

            # 복원된 파일 검증
            restored_checksum = self._calculate_file_checksum(target_profile.file_path)
            if backup_record.checksum and restored_checksum != backup_record.checksum:
                # 복원 실패 - 원본 복구
                if temp_backup_path and temp_backup_path.exists():
                    shutil.copy2(temp_backup_path.path, target_profile.file_path)
                    logger.warning("복원 실패로 인한 원본 복구 완료")

                raise RuntimeError("복원된 파일의 체크섬이 일치하지 않습니다")

            # 임시 백업 파일 정리
            if temp_backup_path and temp_backup_path.exists():
                temp_backup_path.path.unlink()
                logger.debug("임시 백업 파일 정리됨")

            logger.info(f"백업 복원 성공: {backup_record.backup_id}")
            return True

        except Exception as e:
            logger.error(f"백업 복원 실패: {e}")
            raise RuntimeError(f"백업 복원 실패: {e}") from e

    def verify_backup_integrity(self, backup_record: BackupRecord) -> bool:
        """
        백업 파일 무결성 검증

        Args:
            backup_record: 검증할 백업 기록

        Returns:
            무결성 검증 결과
        """
        logger.debug(f"백업 무결성 검증 시작: {backup_record.backup_id}")

        if backup_record.status != BackupStatus.COMPLETED:
            logger.warning(f"완료되지 않은 백업: {backup_record.status}")
            return False

        if not backup_record.is_backup_file_exists():
            logger.warning(f"백업 파일이 존재하지 않음: {backup_record.backup_file_path}")
            return False

        # 파일 크기 검증
        actual_size = backup_record.get_backup_file_size()
        if backup_record.file_size_bytes and actual_size != backup_record.file_size_bytes:
            logger.error(f"파일 크기 불일치: 예상={backup_record.file_size_bytes}, 실제={actual_size}")
            return False

        # 체크섬 검증 (있는 경우)
        if backup_record.checksum:
            actual_checksum = self._calculate_file_checksum(backup_record.backup_file_path)
            if actual_checksum != backup_record.checksum:
                logger.error(f"체크섬 불일치: 예상={backup_record.checksum}, 실제={actual_checksum}")
                return False

        # SQLite 파일 구조 검증
        if not self._verify_sqlite_structure(backup_record.backup_file_path):
            logger.error("SQLite 파일 구조 검증 실패")
            return False

        logger.debug(f"백업 무결성 검증 성공: {backup_record.backup_id}")
        return True

    def cleanup_corrupted_backups(self, backup_records: List[BackupRecord]) -> List[str]:
        """
        손상된 백업 파일 정리

        Args:
            backup_records: 검사할 백업 기록 목록

        Returns:
            정리된 백업 ID 목록
        """
        logger.info(f"손상된 백업 검사 시작: {len(backup_records)}개")

        corrupted_backup_ids = []

        for backup_record in backup_records:
            try:
                if not self.verify_backup_integrity(backup_record):
                    # 손상된 백업 파일 삭제
                    if backup_record.is_backup_file_exists():
                        backup_record.backup_file_path.unlink()
                        logger.debug(f"손상된 백업 파일 삭제됨: {backup_record.backup_file_path}")

                    corrupted_backup_ids.append(backup_record.backup_id)

            except Exception as e:
                logger.warning(f"백업 검증 중 오류: {backup_record.backup_id} - {e}")
                corrupted_backup_ids.append(backup_record.backup_id)

        logger.info(f"손상된 백업 정리 완료: {len(corrupted_backup_ids)}개")
        return corrupted_backup_ids

    def get_backup_statistics(self, backup_records: List[BackupRecord]) -> Dict[str, Any]:
        """
        백업 통계 정보 계산

        Args:
            backup_records: 백업 기록 목록

        Returns:
            백업 통계 정보
        """
        stats = {
            'total_backups': len(backup_records),
            'completed_backups': 0,
            'failed_backups': 0,
            'corrupted_backups': 0,
            'total_size_bytes': 0,
            'average_size_bytes': 0,
            'by_type': {},
            'by_status': {},
            'oldest_backup': None,
            'newest_backup': None
        }

        if not backup_records:
            return stats

        total_size = 0
        completed_count = 0

        # 상태별 분류
        for backup in backup_records:
            status_count = stats['by_status'].get(backup.status.value, 0)
            stats['by_status'][backup.status.value] = status_count + 1

            if backup.status == BackupStatus.COMPLETED:
                completed_count += 1
                if backup.file_size_bytes:
                    total_size += backup.file_size_bytes
            elif backup.status == BackupStatus.FAILED:
                stats['failed_backups'] += 1
            elif backup.status == BackupStatus.CORRUPTED:
                stats['corrupted_backups'] += 1

            # 타입별 분류
            type_count = stats['by_type'].get(backup.source_database_type, 0)
            stats['by_type'][backup.source_database_type] = type_count + 1

        stats['completed_backups'] = completed_count
        stats['total_size_bytes'] = total_size
        stats['average_size_bytes'] = total_size // completed_count if completed_count > 0 else 0

        # 가장 오래된/최신 백업
        sorted_backups = sorted(backup_records, key=lambda b: b.created_at)
        stats['oldest_backup'] = sorted_backups[0].created_at
        stats['newest_backup'] = sorted_backups[-1].created_at

        logger.debug(f"백업 통계 계산 완료: {stats}")
        return stats

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """파일 SHA-256 체크섬 계산"""
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)

            checksum = sha256_hash.hexdigest()
            logger.debug(f"체크섬 계산 완료: {file_path} -> {checksum[:8]}...")
            return checksum

        except Exception as e:
            logger.error(f"체크섬 계산 실패: {e}")
            return ""

    def _verify_sqlite_structure(self, file_path: Path) -> bool:
        """SQLite 파일 구조 기본 검증"""
        try:
            import sqlite3

            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()

                # SQLite 헤더 검증
                cursor.execute("PRAGMA integrity_check(1)")
                result = cursor.fetchone()

                if result and result[0] == 'ok':
                    logger.debug(f"SQLite 구조 검증 성공: {file_path}")
                    return True
                else:
                    logger.warning(f"SQLite 무결성 검사 실패: {result}")
                    return False

        except Exception as e:
            logger.warning(f"SQLite 구조 검증 실패: {e}")
            return False
