"""
데이터베이스 설정 리포지토리 구현체

Domain Layer의 IDatabaseConfigRepository 인터페이스를 SQLite로 구현합니다.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.configuration.paths import infrastructure_paths
from upbit_auto_trading.domain.database_configuration.repositories.idatabase_config_repository import IDatabaseConfigRepository
from upbit_auto_trading.domain.database_configuration.entities.database_profile import DatabaseProfile
from upbit_auto_trading.domain.database_configuration.entities.backup_record import BackupRecord, BackupType, BackupStatus
from upbit_auto_trading.domain.database_configuration.aggregates.database_configuration import DatabaseConfiguration

logger = create_component_logger("DatabaseConfigRepository")


class DatabaseConfigRepository(IDatabaseConfigRepository):
    """
    SQLite 기반 데이터베이스 설정 리포지토리 구현체

    settings.sqlite3에 데이터베이스 설정 정보를 저장하고 관리합니다.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        리포지토리 초기화

        Args:
            db_path: 데이터베이스 파일 경로 (None이면 기본 settings.sqlite3 사용)
        """
        self.db_path = db_path or infrastructure_paths.SETTINGS_DB
        self._ensure_database_exists()
        self._create_tables()
        logger.info(f"DatabaseConfigRepository 초기화됨: {self.db_path}")

    def _ensure_database_exists(self) -> None:
        """데이터베이스 파일이 없으면 생성"""
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"데이터베이스 파일 생성됨: {self.db_path}")

    def _create_tables(self) -> None:
        """필요한 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- 데이터베이스 프로필 테이블
                CREATE TABLE IF NOT EXISTS database_profiles (
                    profile_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    database_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT,
                    metadata TEXT,

                    UNIQUE(file_path),
                    UNIQUE(database_type, is_active)
                        WHERE is_active = 1  -- 활성 프로필은 타입당 하나만
                );

                -- 백업 기록 테이블
                CREATE TABLE IF NOT EXISTS backup_records (
                    backup_id TEXT PRIMARY KEY,
                    source_profile_id TEXT NOT NULL,
                    source_database_type TEXT NOT NULL,
                    backup_file_path TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    file_size_bytes INTEGER,
                    checksum TEXT,
                    error_message TEXT,

                    FOREIGN KEY (source_profile_id) REFERENCES database_profiles(profile_id)
                );

                -- 인덱스 생성
                CREATE INDEX IF NOT EXISTS idx_profiles_type_active
                    ON database_profiles(database_type, is_active);
                CREATE INDEX IF NOT EXISTS idx_backups_profile
                    ON backup_records(source_profile_id);
                CREATE INDEX IF NOT EXISTS idx_backups_created
                    ON backup_records(created_at);
            """)

        logger.debug("데이터베이스 테이블 생성/확인 완료")

    async def save_configuration(self, configuration: DatabaseConfiguration) -> None:
        """
        데이터베이스 설정 저장

        Args:
            config: 저장할 데이터베이스 설정
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN TRANSACTION")

            try:
                # 기존 데이터 삭제 (완전 교체)
                conn.execute("DELETE FROM backup_records")
                conn.execute("DELETE FROM database_profiles")

                # 프로필 저장
                for profile in config.profiles.values():
                    self._save_profile(conn, profile)

                # 백업 기록 저장
                for backup in config.backup_records.values():
                    self._save_backup_record(conn, backup)

                conn.execute("COMMIT")
                logger.info(f"데이터베이스 설정 저장 완료: {len(config.profiles)}개 프로필, {len(config.backup_records)}개 백업")

            except Exception as e:
                conn.execute("ROLLBACK")
                logger.error(f"❌ 데이터베이스 설정 저장 실패: {e}")
                raise

    def load_configuration(self) -> Optional[DatabaseConfiguration]:
        """
        데이터베이스 설정 로드

        Returns:
            로드된 데이터베이스 설정 (없으면 None)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # 프로필 로드
                profiles = {}
                cursor = conn.execute("SELECT * FROM database_profiles")
                for row in cursor.fetchall():
                    profile = self._row_to_profile(row)
                    profiles[profile.profile_id] = profile

                # 백업 기록 로드
                backup_records = {}
                cursor = conn.execute("SELECT * FROM backup_records")
                for row in cursor.fetchall():
                    backup = self._row_to_backup_record(row)
                    backup_records[backup.backup_id] = backup

                # 활성 프로필 매핑 구성
                active_profile_ids = {}
                for profile in profiles.values():
                    if profile.is_active:
                        active_profile_ids[profile.database_type] = profile.profile_id

                # 설정 객체 생성
                config = DatabaseConfiguration(
                    profiles=profiles,
                    backup_records=backup_records,
                    active_profile_ids=active_profile_ids
                )

                logger.info(f"데이터베이스 설정 로드 완료: {len(profiles)}개 프로필, {len(backup_records)}개 백업")
                return config

        except Exception as e:
            logger.error(f"❌ 데이터베이스 설정 로드 실패: {e}")
            return None

    def save_profile(self, profile: DatabaseProfile) -> None:
        """
        개별 프로필 저장

        Args:
            profile: 저장할 프로필
        """
        with sqlite3.connect(self.db_path) as conn:
            self._save_profile(conn, profile)
            logger.debug(f"프로필 저장됨: {profile.name}")

    def load_profile(self, profile_id: str) -> Optional[DatabaseProfile]:
        """
        개별 프로필 로드

        Args:
            profile_id: 프로필 ID

        Returns:
            로드된 프로필 (없으면 None)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM database_profiles WHERE profile_id = ?",
                (profile_id,)
            )
            row = cursor.fetchone()

            if row:
                profile = self._row_to_profile(row)
                logger.debug(f"프로필 로드됨: {profile.name}")
                return profile

            return None

    def delete_profile(self, profile_id: str) -> None:
        """
        프로필 삭제

        Args:
            profile_id: 삭제할 프로필 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN TRANSACTION")

            try:
                # 관련 백업 기록 삭제
                conn.execute(
                    "DELETE FROM backup_records WHERE source_profile_id = ?",
                    (profile_id,)
                )

                # 프로필 삭제
                cursor = conn.execute(
                    "DELETE FROM database_profiles WHERE profile_id = ?",
                    (profile_id,)
                )

                if cursor.rowcount > 0:
                    conn.execute("COMMIT")
                    logger.info(f"프로필 삭제됨: {profile_id}")
                else:
                    conn.execute("ROLLBACK")
                    logger.warning(f"삭제할 프로필이 없음: {profile_id}")

            except Exception as e:
                conn.execute("ROLLBACK")
                logger.error(f"❌ 프로필 삭제 실패 {profile_id}: {e}")
                raise

    def find_profiles_by_type(self, database_type: str) -> List[DatabaseProfile]:
        """
        타입별 프로필 조회

        Args:
            database_type: 데이터베이스 타입

        Returns:
            해당 타입의 프로필 목록
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM database_profiles WHERE database_type = ? ORDER BY created_at DESC",
                (database_type,)
            )

            profiles = []
            for row in cursor.fetchall():
                profile = self._row_to_profile(row)
                profiles.append(profile)

            logger.debug(f"타입별 프로필 조회 - {database_type}: {len(profiles)}개")
            return profiles

    def find_active_profile(self, database_type: str) -> Optional[DatabaseProfile]:
        """
        활성 프로필 조회

        Args:
            database_type: 데이터베이스 타입

        Returns:
            활성 프로필 (없으면 None)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM database_profiles WHERE database_type = ? AND is_active = 1",
                (database_type,)
            )
            row = cursor.fetchone()

            if row:
                profile = self._row_to_profile(row)
                logger.debug(f"활성 프로필 조회 - {database_type}: {profile.name}")
                return profile

            return None

    def save_backup_record(self, backup: BackupRecord) -> None:
        """
        백업 기록 저장

        Args:
            backup: 저장할 백업 기록
        """
        with sqlite3.connect(self.db_path) as conn:
            self._save_backup_record(conn, backup)
            logger.debug(f"백업 기록 저장됨: {backup.backup_id}")

    def load_backup_record(self, backup_id: str) -> Optional[BackupRecord]:
        """
        백업 기록 로드

        Args:
            backup_id: 백업 ID

        Returns:
            로드된 백업 기록 (없으면 None)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM backup_records WHERE backup_id = ?",
                (backup_id,)
            )
            row = cursor.fetchone()

            if row:
                backup = self._row_to_backup_record(row)
                logger.debug(f"백업 기록 로드됨: {backup.backup_id}")
                return backup

            return None

    def find_backup_records_by_profile(self, profile_id: str) -> List[BackupRecord]:
        """
        프로필별 백업 기록 조회

        Args:
            profile_id: 프로필 ID

        Returns:
            해당 프로필의 백업 기록 목록
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM backup_records WHERE source_profile_id = ? ORDER BY created_at DESC",
                (profile_id,)
            )

            backups = []
            for row in cursor.fetchall():
                backup = self._row_to_backup_record(row)
                backups.append(backup)

            logger.debug(f"프로필별 백업 기록 조회 - {profile_id}: {len(backups)}개")
            return backups

    def delete_backup_record(self, backup_id: str) -> None:
        """
        백업 기록 삭제

        Args:
            backup_id: 삭제할 백업 ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM backup_records WHERE backup_id = ?",
                (backup_id,)
            )

            if cursor.rowcount > 0:
                logger.info(f"백업 기록 삭제됨: {backup_id}")
            else:
                logger.warning(f"삭제할 백업 기록이 없음: {backup_id}")

    def _save_profile(self, conn: sqlite3.Connection, profile: DatabaseProfile) -> None:
        """프로필을 데이터베이스에 저장"""
        conn.execute("""
            INSERT OR REPLACE INTO database_profiles (
                profile_id, name, database_type, file_path, is_active,
                created_at, last_accessed, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.profile_id,
            profile.name,
            profile.database_type,
            str(profile.file_path),
            profile.is_active,
            profile.created_at.isoformat(),
            profile.last_accessed.isoformat() if profile.last_accessed else None,
            json.dumps(profile.metadata) if profile.metadata else None
        ))

    def _save_backup_record(self, conn: sqlite3.Connection, backup: BackupRecord) -> None:
        """백업 기록을 데이터베이스에 저장"""
        conn.execute("""
            INSERT OR REPLACE INTO backup_records (
                backup_id, source_profile_id, source_database_type, backup_file_path,
                backup_type, status, created_at, started_at, completed_at,
                file_size_bytes, checksum, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            backup.backup_id,
            backup.source_profile_id,
            backup.source_database_type,
            str(backup.backup_file_path),
            backup.backup_type.value,
            backup.status.value,
            backup.created_at.isoformat(),
            backup.started_at.isoformat() if backup.started_at else None,
            backup.completed_at.isoformat() if backup.completed_at else None,
            backup.file_size_bytes,
            backup.checksum,
            backup.error_message
        ))

    def _row_to_profile(self, row: sqlite3.Row) -> DatabaseProfile:
        """데이터베이스 행을 DatabaseProfile 객체로 변환"""
        return DatabaseProfile(
            profile_id=row['profile_id'],
            name=row['name'],
            database_type=row['database_type'],
            file_path=Path(row['file_path']),
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']),
            last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )

    def _row_to_backup_record(self, row: sqlite3.Row) -> BackupRecord:
        """데이터베이스 행을 BackupRecord 객체로 변환"""
        return BackupRecord(
            backup_id=row['backup_id'],
            source_profile_id=row['source_profile_id'],
            source_database_type=row['source_database_type'],
            backup_file_path=Path(row['backup_file_path']),
            backup_type=BackupType(row['backup_type']),
            status=BackupStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            file_size_bytes=row['file_size_bytes'],
            checksum=row['checksum'],
            error_message=row['error_message']
        )

    def get_repository_stats(self) -> Dict[str, Any]:
        """리포지토리 통계 정보 반환"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM database_profiles")
            total_profiles = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM database_profiles WHERE is_active = 1")
            active_profiles = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM backup_records")
            total_backups = cursor.fetchone()[0]

            stats = {
                'total_profiles': total_profiles,
                'active_profiles': active_profiles,
                'total_backups': total_backups,
                'db_path': str(self.db_path),
                'db_size_bytes': self.db_path.stat().st_size if self.db_path.exists() else 0
            }

            logger.debug(f"리포지토리 통계: {stats}")
            return stats

    def __str__(self) -> str:
        return f"DatabaseConfigRepository(db_path='{self.db_path}')"

    def __repr__(self) -> str:
        stats = self.get_repository_stats()
        return (f"DatabaseConfigRepository(db_path='{self.db_path}', "
                f"profiles={stats['total_profiles']}, backups={stats['total_backups']})")
