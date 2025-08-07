"""
DDD Infrastructure Layer - 경로 관리 시스템
기존 config/simple_paths.py의 DDD 버전
"""

from pathlib import Path


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

        # 데이터베이스 파일 경로
        self.SETTINGS_DB = self.DATA_DIR / "settings.sqlite3"
        self.STRATEGIES_DB = self.DATA_DIR / "strategies.sqlite3"
        self.MARKET_DATA_DB = self.DATA_DIR / "market_data.sqlite3"

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


# Infrastructure Layer 전용 인스턴스
infrastructure_paths = PathsConfiguration()
