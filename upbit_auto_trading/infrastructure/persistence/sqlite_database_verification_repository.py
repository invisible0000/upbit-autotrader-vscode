"""
SQLite Database Verification Repository Implementation
SQLite 데이터베이스 검증을 위한 Infrastructure 구현체
"""

import sqlite3
from pathlib import Path
from typing import Optional, Tuple

from upbit_auto_trading.domain.database_configuration.repositories.database_verification_repository import (
    IDatabaseVerificationRepository
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


class SqliteDatabaseVerificationRepository(IDatabaseVerificationRepository):
    """SQLite 데이터베이스 검증 Repository 구현체"""

    def __init__(self):
        self.logger = create_component_logger("SqliteDatabaseVerificationRepository")

    def verify_sqlite_integrity(self, file_path: Path) -> bool:
        """SQLite 파일의 무결성을 검증합니다."""
        try:
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check(1)")
                result = cursor.fetchone()

                if result and result[0] == 'ok':
                    self.logger.debug(f"SQLite 구조 검증 성공: {file_path}")
                    return True
                else:
                    self.logger.warning(f"SQLite 무결성 검사 실패: {result}")
                    return False

        except Exception as e:
            self.logger.warning(f"SQLite 구조 검증 실패: {e}")
            return False

    def check_database_accessibility(self, file_path: Path) -> bool:
        """데이터베이스 파일에 접근 가능한지 확인합니다."""
        try:
            if not file_path.exists():
                return False

            # 읽기 접근 테스트
            with sqlite3.connect(file_path, timeout=5.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()

            self.logger.debug(f"데이터베이스 접근 성공: {file_path}")
            return True

        except Exception as e:
            self.logger.warning(f"데이터베이스 접근 실패: {file_path}, {e}")
            return False

    def get_database_info(self, file_path: Path) -> Optional[dict]:
        """데이터베이스 기본 정보를 조회합니다."""
        try:
            if not file_path.exists():
                return None

            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()

                # 파일 크기
                file_size = file_path.stat().st_size

                # SQLite 버전
                cursor.execute("SELECT sqlite_version()")
                sqlite_version = cursor.fetchone()[0]

                # 테이블 수
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

                info = {
                    'file_size': file_size,
                    'sqlite_version': sqlite_version,
                    'table_count': table_count,
                    'file_path': str(file_path)
                }

                self.logger.debug(f"데이터베이스 정보 조회 성공: {info}")
                return info

        except Exception as e:
            self.logger.error(f"데이터베이스 정보 조회 실패: {file_path}, {e}")
            return None

    def test_connection(self, file_path: Path) -> Tuple[bool, str]:
        """데이터베이스 연결을 테스트합니다."""
        try:
            if not file_path.exists():
                return False, f"파일이 존재하지 않습니다: {file_path}"

            with sqlite3.connect(file_path, timeout=10.0) as conn:
                cursor = conn.cursor()

                # 기본 연결 테스트
                cursor.execute("SELECT 1")
                cursor.fetchone()

                # 무결성 체크
                cursor.execute("PRAGMA integrity_check(1)")
                integrity_result = cursor.fetchone()

                if integrity_result and integrity_result[0] == 'ok':
                    message = f"연결 테스트 성공: {file_path}"
                    self.logger.info(message)
                    return True, message
                else:
                    message = f"무결성 검사 실패: {integrity_result}"
                    self.logger.warning(message)
                    return False, message

        except sqlite3.OperationalError as e:
            message = f"SQLite 연결 오류: {e}"
            self.logger.error(message)
            return False, message

        except Exception as e:
            message = f"연결 테스트 실패: {e}"
            self.logger.error(message)
            return False, message
