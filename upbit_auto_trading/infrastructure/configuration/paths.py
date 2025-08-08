"""
[DEPRECATED] 레거시 경로 관리 시스템

⚠️ 이 모듈은 더 이상 사용되지 않습니다 (deprecated).
⚠️ 대신 DDD 기반 DatabasePathService를 사용하세요.

새로운 DDD 기반 경로 관리:
- upbit_auto_trading.domain.database_configuration.services.database_path_service.DatabasePathService
- upbit_auto_trading.infrastructure.persistence.database_configuration_repository_impl.FileSystemDatabaseConfigurationRepository

기존 코드:
    from upbit_auto_trading.infrastructure.configuration.paths import infrastructure_paths
    db_path = infrastructure_paths.SETTINGS_DB

새로운 코드:
    from upbit_auto_trading.domain.database_configuration.services.database_path_service import DatabasePathService
    from upbit_auto_trading.infrastructure.persistence.database_configuration_repository_impl import FileSystemDatabaseConfigurationRepository

    repository = FileSystemDatabaseConfigurationRepository()
    service = DatabasePathService(repository)
    paths = service.get_all_paths()
    db_path = paths.get('settings', 'default_path')

이 파일은 호환성을 위해서만 유지되며, 향후 버전에서 제거될 예정입니다.
"""

import warnings
from pathlib import Path

# 사용 시 경고 메시지 출력
warnings.warn(
    "paths.py는 deprecated 되었습니다. DDD 기반 DatabasePathService를 사용하세요.",
    DeprecationWarning,
    stacklevel=2
)


class PathsConfiguration:
    """DDD Infrastructure Layer용 경로 관리 클래스"""

    def __init__(self):
        # 프로젝트 루트 자동 감지 (현재 파일 기준 4단계 상위)
        self.APP_ROOT = Path(__file__).parents[3]

        # 루트 레벨 디렉토리 구조
        self.DATA_DIR = self.APP_ROOT / "data"
        self.CONFIG_DIR = self.APP_ROOT / "config"
        self.LOGS_DIR = self.APP_ROOT / "logs"
        self.BACKUPS_DIR = self.APP_ROOT / "backups"

        # 보안 디렉토리
        self.SECURE_DIR = self.CONFIG_DIR / "secure"

        # 데이터베이스 파일 경로 (기본값)
        self._default_settings_db = self.DATA_DIR / "settings.sqlite3"
        self._default_strategies_db = self.DATA_DIR / "strategies.sqlite3"
        self._default_market_data_db = self.DATA_DIR / "market_data.sqlite3"

        # 실제 사용 중인 경로 (기본값으로 초기화)
        self.SETTINGS_DB = self._default_settings_db
        self.STRATEGIES_DB = self._default_strategies_db
        self.MARKET_DATA_DB = self._default_market_data_db

        # API 자격증명 파일 경로
        self.API_CREDENTIALS_FILE = self.SECURE_DIR / "api_credentials.json"

        # 필요한 디렉토리 생성
        self._ensure_directories()

    def _ensure_directories(self):
        """필요한 디렉토리가 없으면 생성"""
        directories = [
            self.DATA_DIR, self.CONFIG_DIR, self.LOGS_DIR,
            self.BACKUPS_DIR, self.SECURE_DIR
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_db_path(self, db_name: str) -> Path:
        """데이터베이스 경로 반환"""
        db_mapping = {
            'settings': self.SETTINGS_DB,
            'strategies': self.STRATEGIES_DB,
            'market_data': self.MARKET_DATA_DB
        }
        return db_mapping.get(db_name, self.DATA_DIR / f"{db_name}.sqlite3")

    def get_app_info(self) -> dict:
        """앱 경로 정보 반환"""
        return {
            'app_root': str(self.APP_ROOT),
            'data_dir': str(self.DATA_DIR),
            'config_dir': str(self.CONFIG_DIR),
            'settings_db': str(self.SETTINGS_DB),
            'strategies_db': str(self.STRATEGIES_DB),
            'market_data_db': str(self.MARKET_DATA_DB),
        }

    def update_database_path(self, database_type: str, new_path: str) -> bool:
        """데이터베이스 경로 동적 업데이트"""
        try:
            from pathlib import Path
            new_path_obj = Path(new_path)

            if database_type == "settings":
                self.SETTINGS_DB = new_path_obj
            elif database_type == "strategies":
                self.STRATEGIES_DB = new_path_obj
            elif database_type == "market_data":
                self.MARKET_DATA_DB = new_path_obj
            else:
                return False

            return True
        except Exception:
            return False

    def reset_database_paths(self):
        """
        [DEPRECATED] 데이터베이스 경로를 기본값으로 재설정

        ⚠️ 이 메서드는 DDD 시스템과 충돌하므로 무력화되었습니다.
        ⚠️ DDD DatabasePathService에서 경로를 관리하므로 reset하지 않습니다.
        """
        import warnings
        warnings.warn(
            "reset_database_paths()는 더 이상 지원되지 않습니다. "
            "DDD DatabasePathService를 사용하여 경로를 관리하세요.",
            DeprecationWarning,
            stacklevel=2
        )

        # DDD 시스템이 활성화된 경우 reset 무시
        try:
            from upbit_auto_trading.domain.database_configuration.services.database_path_service import DatabasePathService
            from upbit_auto_trading.infrastructure.persistence.database_configuration_repository_impl import FileSystemDatabaseConfigurationRepository

            repository = FileSystemDatabaseConfigurationRepository()
            service = DatabasePathService(repository)
            current_paths = service.get_all_paths()

            if len(current_paths) >= 3:
                # DDD 시스템이 활성화된 경우 reset 무시하고 DDD 경로로 동기화
                self.update_database_path('settings', current_paths.get('settings', str(self._default_settings_db)))
                self.update_database_path('strategies', current_paths.get('strategies', str(self._default_strategies_db)))
                self.update_database_path('market_data', current_paths.get('market_data', str(self._default_market_data_db)))
                return

        except Exception:
            pass

        # DDD 시스템 실패 시에만 기본값 복원
        self.SETTINGS_DB = self._default_settings_db
        self.STRATEGIES_DB = self._default_strategies_db
        self.MARKET_DATA_DB = self._default_market_data_db


# Infrastructure Layer 전용 인스턴스
infrastructure_paths = PathsConfiguration()
