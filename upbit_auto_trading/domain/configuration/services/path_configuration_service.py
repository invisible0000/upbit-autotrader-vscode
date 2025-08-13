"""
Path Configuration Domain Service
DDD Domain Layer - 경로 관리 비즈니스 로직
"""

import os
from typing import Optional
from pathlib import Path

from upbit_auto_trading.domain.configuration.repositories.path_configuration_repository import (
    IPathConfigurationRepository,
    IPathConfigurationService
)
from upbit_auto_trading.infrastructure.logging import create_component_logger


class PathConfigurationService(IPathConfigurationService):
    """경로 설정 Domain Service"""

    def __init__(self, path_repository: IPathConfigurationRepository):
        self.logger = create_component_logger("PathConfigurationService")
        self._path_repository = path_repository

        self.logger.info("🔧 PathConfigurationService 초기화 완료 (DDD Domain Layer)")

    def get_project_root(self) -> Path:
        """프로젝트 루트 디렉토리 조회"""
        # Repository를 통해 기본 디렉토리 조회 후 부모 계산
        data_dir = self._path_repository.get_base_directory('data')
        return data_dir.parent

    def resolve_path(self, relative_path: str, environment: Optional[str] = None) -> Path:
        """상대 경로를 절대 경로로 변환"""
        project_root = self.get_project_root()

        if Path(relative_path).is_absolute():
            return Path(relative_path)

        return project_root / relative_path

    def change_database_location(self, db_name: str, new_path: Path) -> bool:
        """
        데이터베이스 위치 변경 (도메인 로직)

        DDD 원칙: Domain이 Infrastructure에 명령하는 올바른 방향
        """
        try:
            self.logger.info(f"📁 데이터베이스 위치 변경 요청: {db_name} -> {new_path}")

            # 1. 비즈니스 규칙 검증
            if not self._validate_database_path_change(db_name, new_path):
                return False

            # 2. Repository를 통한 Infrastructure 업데이트
            success = self._path_repository.update_database_path(db_name, new_path)

            if success:
                self.logger.info(f"✅ 데이터베이스 위치 변경 완료: {db_name}")
            else:
                self.logger.error(f"❌ 데이터베이스 위치 변경 실패: {db_name}")

            return success

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 위치 변경 중 오류: {e}")
            return False

    def initialize_directories(self) -> bool:
        """필수 디렉토리 초기화"""
        try:
            self.logger.info("🌍 경로 시스템 초기화")

            # 1. 프로젝트 구조 검증
            if not self._path_repository.validate_structure():
                self.logger.warning("⚠️ 프로젝트 구조 검증 실패")
                return False

            # 2. 필수 디렉토리 생성
            if not self._path_repository.ensure_directories():
                self.logger.error("❌ 디렉토리 생성 실패")
                return False

            self.logger.info("✅ 경로 시스템 초기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ 환경 초기화 실패: {e}")
            return False

    def initialize_environment(self, environment: str) -> bool:
        """환경별 경로 초기화 (Legacy 호환성)"""
        # 환경 프로파일 제거로 인해 단순히 디렉토리 초기화만 수행
        return self.initialize_directories()

    def get_database_path(self, db_name: str) -> Path:
        """데이터베이스 경로 조회 (도메인 메서드)"""
        return self._path_repository.get_database_path(db_name)

    def get_directory_path(self, dir_type: str) -> Path:
        """디렉토리 경로 조회 (도메인 메서드)"""
        return self._path_repository.get_base_directory(dir_type)

    def _validate_database_path_change(self, db_name: str, new_path: Path) -> bool:
        """데이터베이스 경로 변경 비즈니스 규칙 검증"""
        try:
            # 1. 유효한 데이터베이스 이름 검증
            valid_db_names = ['settings', 'strategies', 'market_data']
            if db_name not in valid_db_names:
                self.logger.error(f"❌ 유효하지 않은 데이터베이스 이름: {db_name}")
                return False

            # 2. 경로 유효성 검증
            if not new_path.suffix == '.sqlite3':
                self.logger.error(f"❌ SQLite 파일이 아님: {new_path}")
                return False

            # 3. 디렉토리 존재 여부 확인
            parent_dir = new_path.parent
            if not parent_dir.exists():
                self.logger.warning(f"⚠️ 디렉토리 없음, 생성 시도: {parent_dir}")
                parent_dir.mkdir(parents=True, exist_ok=True)

            # 4. 쓰기 권한 확인
            if not os.access(parent_dir, os.W_OK):
                self.logger.error(f"❌ 쓰기 권한 없음: {parent_dir}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"❌ 경로 변경 검증 실패: {e}")
            return False
