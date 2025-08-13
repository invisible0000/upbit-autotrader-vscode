"""
Infrastructure Configuration 모듈
Factory + Caching 패턴 기반 경로 관리 시스템

새로운 아키텍처:
- PathServiceFactory: 인스턴스 생성 및 캐싱 관리
- Thread-safe 구현
- 테스트용 캐시 정리 지원
- Config 파일 기반: config/paths_config.yaml
"""

from pathlib import Path
from typing import Optional

# Factory + Caching 패턴 Import
from upbit_auto_trading.infrastructure.configuration.path_service_factory import (
    PathServiceFactory,
    get_path_service,
    get_test_path_service,
    clear_path_service_cache,
    # Legacy 호환성 (단계적 제거 예정)
    create_path_service,
    get_shared_path_service,
)


class LegacyInfrastructurePaths:
    """
    ⚠️ DEPRECATED: Factory 패턴으로 완전 교체됨

    Migration Guide:
    - infrastructure_paths.SETTINGS_DB → get_path_service().get_database_path('settings')
    - infrastructure_paths.DATA_DIR → get_path_service().get_directory_path('data')
    """

    def __init__(self, custom_root: Optional[Path] = None):
        # Factory에서 관리되는 서비스 사용
        self._path_service = get_path_service()
        self._update_legacy_attributes()

    def _update_legacy_attributes(self):
        """Legacy 속성들을 Factory 기반 서비스에서 가져오기"""
        try:
            # 프로젝트 루트
            self.APP_ROOT = self._path_service.get_project_root()

            # 기본 디렉토리들
            self.DATA_DIR = self._path_service.get_directory_path('data')
            self.CONFIG_DIR = self._path_service.get_directory_path('config')
            self.LOGS_DIR = self._path_service.get_directory_path('logs')
            self.BACKUPS_DIR = self._path_service.get_directory_path('backups')

            # 데이터베이스 파일들
            self.SETTINGS_DB = self._path_service.get_database_path('settings')
            self.STRATEGIES_DB = self._path_service.get_database_path('strategies')
            self.MARKET_DATA_DB = self._path_service.get_database_path('market_data')

        except Exception as e:
            # 폴백: 하드코딩된 기본값
            self._fallback_to_hardcoded_paths()
            print(f"⚠️ Factory 서비스 로드 실패, 하드코딩 폴백: {e}")

    def _fallback_to_hardcoded_paths(self):
        """폴백: 하드코딩된 경로들"""
        self.APP_ROOT = Path(__file__).parents[3]
        self.DATA_DIR = self.APP_ROOT / "data"
        self.CONFIG_DIR = self.APP_ROOT / "config"
        self.LOGS_DIR = self.APP_ROOT / "logs"
        self.BACKUPS_DIR = self.APP_ROOT / "backups"
        self.SETTINGS_DB = self.DATA_DIR / "settings.sqlite3"
        self.STRATEGIES_DB = self.DATA_DIR / "strategies.sqlite3"
        self.MARKET_DATA_DB = self.DATA_DIR / "market_data.sqlite3"

    def get_db_path(self, db_name: str) -> Path:
        """데이터베이스 경로 반환 (Factory 서비스로 위임)"""
        return self._path_service.get_database_path(db_name)

    def change_database_path(self, db_name: str, new_path: Path) -> bool:
        """데이터베이스 경로 변경 (Factory 서비스로 위임)"""
        success = self._path_service.change_database_location(db_name, new_path)
        if success:
            self._update_legacy_attributes()
        return success


# Legacy 호환성 인스턴스 (단계적 제거 예정)
infrastructure_paths = LegacyInfrastructurePaths()
paths = infrastructure_paths  # Legacy 별칭

# 새로운 Factory 기반 시스템 (권장 사용)
path_service = get_path_service()

__all__ = [
    # Factory 패턴 (권장)
    'PathServiceFactory',
    'get_path_service',
    'get_test_path_service',
    'clear_path_service_cache',
    'path_service',

    # Legacy 호환성 (제거 예정)
    'infrastructure_paths',
    'paths',
    'create_path_service',
    'get_shared_path_service',
]
