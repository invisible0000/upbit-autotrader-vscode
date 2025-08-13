"""
Path Configuration Repository Interface
DDD Domain Layer - Infrastructure 계층에 대한 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from pathlib import Path


class IPathConfigurationRepository(ABC):
    """경로 설정 Repository 인터페이스 (Domain Layer)"""

    @abstractmethod
    def get_base_directory(self, dir_type: str) -> Path:
        """기본 디렉토리 경로 조회"""
        pass

    @abstractmethod
    def get_database_path(self, db_name: str) -> Path:
        """데이터베이스 파일 경로 조회"""
        pass

    @abstractmethod
    def get_security_path(self, resource: str) -> Path:
        """보안 관련 파일 경로 조회"""
        pass

    @abstractmethod
    def get_logging_config(self) -> Dict[str, any]:
        """로깅 설정 조회"""
        pass

    @abstractmethod
    def get_backup_config(self) -> Dict[str, any]:
        """백업 설정 조회"""
        pass

    @abstractmethod
    def update_database_path(self, db_name: str, new_path: Path) -> bool:
        """데이터베이스 경로 업데이트 (DDD 도메인 서비스용)"""
        pass

    @abstractmethod
    def get_required_files(self) -> List[str]:
        """필수 파일 목록 조회"""
        pass

    @abstractmethod
    def validate_structure(self) -> bool:
        """프로젝트 구조 유효성 검증"""
        pass

    @abstractmethod
    def ensure_directories(self) -> bool:
        """필수 디렉토리 생성"""
        pass


class IPathConfigurationService(ABC):
    """경로 설정 Domain Service 인터페이스"""

    @abstractmethod
    def get_project_root(self) -> Path:
        """프로젝트 루트 디렉토리 조회"""
        pass

    @abstractmethod
    def resolve_path(self, relative_path: str, environment: Optional[str] = None) -> Path:
        """상대 경로를 절대 경로로 변환"""
        pass

    @abstractmethod
    def change_database_location(self, db_name: str, new_path: Path) -> bool:
        """데이터베이스 위치 변경 (도메인 로직)"""
        pass

    @abstractmethod
    def initialize_environment(self, environment: str) -> bool:
        """환경별 경로 초기화"""
        pass
