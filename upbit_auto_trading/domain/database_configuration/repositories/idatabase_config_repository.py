"""
데이터베이스 설정 도메인 - 저장소 인터페이스

데이터베이스 설정 영속성을 위한 저장소 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.database_profile import DatabaseProfile
from ..entities.backup_record import BackupRecord
from ..aggregates.database_configuration import DatabaseConfiguration

class IDatabaseConfigRepository(ABC):
    """
    데이터베이스 설정 저장소 인터페이스

    데이터베이스 설정의 영속성 계층을 추상화하는 인터페이스입니다.
    Domain Layer는 이 인터페이스에만 의존하며, 구체적인 구현은
    Infrastructure Layer에서 담당합니다.
    """

    @abstractmethod
    async def save_configuration(self, configuration: DatabaseConfiguration) -> None:
        """
        데이터베이스 설정 저장

        Args:
            configuration: 저장할 데이터베이스 설정 집합체
        """
        pass

    @abstractmethod
    async def load_configuration(self, configuration_id: str) -> Optional[DatabaseConfiguration]:
        """
        데이터베이스 설정 로드

        Args:
            configuration_id: 설정 ID

        Returns:
            데이터베이스 설정 집합체 (없으면 None)
        """
        pass

    @abstractmethod
    async def get_default_configuration(self) -> DatabaseConfiguration:
        """
        기본 데이터베이스 설정 반환

        Returns:
            기본 데이터베이스 설정 집합체
        """
        pass

    @abstractmethod
    async def save_profile(self, profile: DatabaseProfile) -> None:
        """
        데이터베이스 프로필 저장

        Args:
            profile: 저장할 프로필
        """
        pass

    @abstractmethod
    async def load_profile(self, profile_id: str) -> Optional[DatabaseProfile]:
        """
        데이터베이스 프로필 로드

        Args:
            profile_id: 프로필 ID

        Returns:
            데이터베이스 프로필 (없으면 None)
        """
        pass

    @abstractmethod
    async def load_profiles_by_type(self, database_type: str) -> List[DatabaseProfile]:
        """
        타입별 데이터베이스 프로필 목록 로드

        Args:
            database_type: 데이터베이스 타입

        Returns:
            해당 타입의 프로필 목록
        """
        pass

    @abstractmethod
    async def delete_profile(self, profile_id: str) -> bool:
        """
        데이터베이스 프로필 삭제

        Args:
            profile_id: 삭제할 프로필 ID

        Returns:
            삭제 성공 여부
        """
        pass

    @abstractmethod
    async def save_backup_record(self, backup_record: BackupRecord) -> None:
        """
        백업 기록 저장

        Args:
            backup_record: 저장할 백업 기록
        """
        pass

    @abstractmethod
    async def load_backup_record(self, backup_id: str) -> Optional[BackupRecord]:
        """
        백업 기록 로드

        Args:
            backup_id: 백업 ID

        Returns:
            백업 기록 (없으면 None)
        """
        pass

    @abstractmethod
    async def load_backup_records_by_profile(self, profile_id: str) -> List[BackupRecord]:
        """
        프로필별 백업 기록 목록 로드

        Args:
            profile_id: 프로필 ID

        Returns:
            해당 프로필의 백업 기록 목록
        """
        pass

    @abstractmethod
    async def delete_backup_record(self, backup_id: str) -> bool:
        """
        백업 기록 삭제

        Args:
            backup_id: 삭제할 백업 ID

        Returns:
            삭제 성공 여부
        """
        pass

    @abstractmethod
    async def cleanup_old_backup_records(self, cutoff_date: datetime) -> int:
        """
        오래된 백업 기록 정리

        Args:
            cutoff_date: 기준 날짜 (이전 기록 삭제)

        Returns:
            삭제된 기록 수
        """
        pass

    @abstractmethod
    async def get_active_profiles(self) -> Dict[str, DatabaseProfile]:
        """
        모든 활성 프로필 조회

        Returns:
            타입별 활성 프로필 (type -> profile)
        """
        pass

    @abstractmethod
    async def update_profile_access_time(self, profile_id: str, access_time: datetime) -> None:
        """
        프로필 마지막 접근 시간 업데이트

        Args:
            profile_id: 프로필 ID
            access_time: 접근 시간
        """
        pass

    @abstractmethod
    async def get_repository_statistics(self) -> Dict[str, Any]:
        """
        저장소 통계 정보 조회

        Returns:
            통계 정보
        """
        pass

    @abstractmethod
    async def verify_repository_integrity(self) -> bool:
        """
        저장소 무결성 검증

        Returns:
            무결성 검증 결과
        """
        pass

class IDatabaseValidationRepository(ABC):
    """
    데이터베이스 검증 저장소 인터페이스

    데이터베이스 파일의 검증과 관련된 저장소 인터페이스입니다.
    """

    @abstractmethod
    async def validate_database_schema(self, database_path: str, database_type: str) -> bool:
        """
        데이터베이스 스키마 검증

        Args:
            database_path: 데이터베이스 파일 경로
            database_type: 데이터베이스 타입

        Returns:
            스키마 검증 결과
        """
        pass

    @abstractmethod
    async def get_database_tables(self, database_path: str) -> List[str]:
        """
        데이터베이스 테이블 목록 조회

        Args:
            database_path: 데이터베이스 파일 경로

        Returns:
            테이블 이름 목록
        """
        pass

    @abstractmethod
    async def get_database_size(self, database_path: str) -> int:
        """
        데이터베이스 파일 크기 조회

        Args:
            database_path: 데이터베이스 파일 경로

        Returns:
            파일 크기 (바이트)
        """
        pass

    @abstractmethod
    async def check_database_corruption(self, database_path: str) -> bool:
        """
        데이터베이스 손상 여부 확인

        Args:
            database_path: 데이터베이스 파일 경로

        Returns:
            손상 여부 (True: 정상, False: 손상)
        """
        pass

    @abstractmethod
    async def get_database_metadata(self, database_path: str) -> Dict[str, Any]:
        """
        데이터베이스 메타데이터 조회

        Args:
            database_path: 데이터베이스 파일 경로

        Returns:
            메타데이터 정보
        """
        pass
