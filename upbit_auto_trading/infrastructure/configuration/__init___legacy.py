"""
LEGACY BACKUP - 기존 Infrastructure Configuration 모듈
2025-08-14 Factory + Caching 패턴으로 교체되어 백업됨

사용하지 마세요!
새로운 시스템: path_service_factory.py + __init__.py
"""

from pathlib import Path
from typing import Optional

# 새로운 Config 기반 시스템 import
from upbit_auto_trading.infrastructure.persistence.config_path_repository import ConfigPathRepository
from upbit_auto_trading.domain.configuration.services.path_configuration_service import PathConfigurationService


class LegacyInfrastructurePaths:
    """
    Legacy 호환성을 위한 Infrastructure 경로 관리

    ⚠️ Deprecated: config/paths_config.yaml 기반 시스템 사용 권장

    Migration Path:
    1. infrastructure_paths.SETTINGS_DB → path_service.get_database_path('settings')
    2. infrastructure_paths.DATA_DIR → path_service.get_directory_path('data')
    """

    def __init__(self, custom_root: Optional[Path] = None):
        # 공유 인스턴스 사용 (중복 생성 방지)
        self._path_service = get_shared_path_service()

        # Legacy 속성들 (deprecated)
        self._update_legacy_attributes()

    def _update_legacy_attributes(self):
        """Legacy 속성들을 새로운 시스템에서 가져오기"""
        try:
            # 프로젝트 루트
            self.APP_ROOT = self._path_service.get_project_root()

            # 기본 디렉토리들
            self.DATA_DIR = self._path_service.get_directory_path('data')
            self.CONFIG_DIR = self._path_service.get_directory_path('config')
            self.LOGS_DIR = self._path_service.get_directory_path('logs')
            self.BACKUPS_DIR = self._path_service.get_directory_path('backups')
            self.SECURE_DIR = self._config_repository.get_security_path('secure_dir')

            # 데이터베이스 파일들
            self.SETTINGS_DB = self._path_service.get_database_path('settings')
            self.STRATEGIES_DB = self._path_service.get_database_path('strategies')
            self.MARKET_DATA_DB = self._path_service.get_database_path('market_data')

            # API 자격증명 파일
            self.API_CREDENTIALS_FILE = self._config_repository.get_security_path('api_credentials')

        except Exception as e:
            # 폴백: 하드코딩된 기본값
            self._fallback_to_hardcoded_paths()
            print(f"⚠️ Config 시스템 로드 실패, 하드코딩 폴백: {e}")

    def _fallback_to_hardcoded_paths(self):
        """폴백: 하드코딩된 경로들"""
        self.APP_ROOT = Path(__file__).parents[3]
        self.DATA_DIR = self.APP_ROOT / "data"
        self.CONFIG_DIR = self.APP_ROOT / "config"
        self.LOGS_DIR = self.APP_ROOT / "logs"
        self.BACKUPS_DIR = self.APP_ROOT / "backups"
        self.SECURE_DIR = self.CONFIG_DIR / "secure"
        self.SETTINGS_DB = self.DATA_DIR / "settings.sqlite3"
        self.STRATEGIES_DB = self.DATA_DIR / "strategies.sqlite3"
        self.MARKET_DATA_DB = self.DATA_DIR / "market_data.sqlite3"
        self.API_CREDENTIALS_FILE = self.SECURE_DIR / "api_credentials.json"

    def validate_structure(self) -> bool:
        """프로젝트 구조 유효성 검증 (새로운 시스템으로 위임)"""
        return self._config_repository.validate_structure()

    def get_db_path(self, db_name: str) -> Path:
        """데이터베이스 경로 반환 (새로운 시스템으로 위임)"""
        return self._path_service.get_database_path(db_name)

    def change_database_path(self, db_name: str, new_path: Path) -> bool:
        """
        데이터베이스 경로 변경 (DDD 원칙 준수)

        Domain Service를 통한 올바른 의존성 방향
        """
        success = self._path_service.change_database_location(db_name, new_path)
        if success:
            # Legacy 속성 업데이트
            self._update_legacy_attributes()
        return success


# 새로운 Config 기반 시스템 (권장)
def create_path_service() -> PathConfigurationService:
    """Config 기반 경로 관리 서비스 생성"""
    config_repository = ConfigPathRepository()
    path_service = PathConfigurationService(config_repository)
    path_service.initialize_directories()  # 단순화된 초기화
    return path_service


# 공유 인스턴스 (중복 생성 방지)
_shared_path_service: Optional[PathConfigurationService] = None

def get_shared_path_service() -> PathConfigurationService:
    """공유 Path Service 인스턴스 반환 (Singleton 패턴)"""
    global _shared_path_service
    if _shared_path_service is None:
        _shared_path_service = create_path_service()
    return _shared_path_service


# Legacy 호환성 인스턴스 (단계적 제거 예정)
infrastructure_paths = LegacyInfrastructurePaths()

# Legacy 별칭
paths = infrastructure_paths

# 새로운 시스템 (권장 사용) - 공유 인스턴스 사용
path_service = get_shared_path_service()

__all__ = [
    'infrastructure_paths',  # Legacy
    'paths',  # Legacy 별칭
    'path_service',  # 새로운 시스템 (권장)
    'create_path_service',  # 팩토리 함수
]
