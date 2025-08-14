"""
Database Verification Repository Interface
데이터베이스 검증을 위한 Repository 인터페이스
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple


class IDatabaseVerificationRepository(ABC):
    """데이터베이스 검증을 위한 Repository 인터페이스"""

    @abstractmethod
    def verify_sqlite_integrity(self, file_path: Path) -> bool:
        """
        SQLite 파일의 무결성을 검증합니다.

        Args:
            file_path: 검증할 SQLite 파일 경로

        Returns:
            bool: 무결성 검증 성공 여부
        """
        pass

    @abstractmethod
    def check_database_accessibility(self, file_path: Path) -> bool:
        """
        데이터베이스 파일에 접근 가능한지 확인합니다.

        Args:
            file_path: 확인할 데이터베이스 파일 경로

        Returns:
            bool: 접근 가능 여부
        """
        pass

    @abstractmethod
    def get_database_info(self, file_path: Path) -> Optional[dict]:
        """
        데이터베이스 기본 정보를 조회합니다.

        Args:
            file_path: 조회할 데이터베이스 파일 경로

        Returns:
            Optional[dict]: 데이터베이스 정보 (크기, 버전 등)
        """
        pass

    @abstractmethod
    def test_connection(self, file_path: Path) -> Tuple[bool, str]:
        """
        데이터베이스 연결을 테스트합니다.

        Args:
            file_path: 테스트할 데이터베이스 파일 경로

        Returns:
            Tuple[bool, str]: (성공 여부, 메시지)
        """
        pass
