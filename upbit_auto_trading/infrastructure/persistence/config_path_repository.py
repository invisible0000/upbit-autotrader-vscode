"""
Config-based Path Configuration Repository Implementation
Infrastructure Layer - YAML 설정 파일 기반 경로 관리
"""

import yaml
import os
from typing import Dict, Optional, List, Any
from pathlib import Path
from datetime import datetime

from upbit_auto_trading.domain.configuration.repositories.path_configuration_repository import IPathConfigurationRepository
from upbit_auto_trading.infrastructure.logging import create_component_logger


class ConfigPathRepository(IPathConfigurationRepository):
    """설정 파일 기반 경로 Repository 구현"""

    def __init__(self, config_file: Optional[Path] = None):
        self.logger = create_component_logger("ConfigPathRepository")

        # 프로젝트 루트 탐지 (최소한의 하드코딩)
        self._project_root = self._detect_project_root()

        # 설정 파일 경로
        self._config_file = config_file or (self._project_root / "config" / "paths_config.yaml")

        # 설정 캐시
        self._config_cache: Optional[Dict] = None
        self._cache_timestamp: Optional[datetime] = None

        self.logger.info(f"📁 ConfigPathRepository 초기화: {self._config_file}")

    def _detect_project_root(self) -> Path:
        """프로젝트 루트 탐지 (마지막 하드코딩)"""
        # 현재 파일 위치에서 프로젝트 루트 찾기
        current = Path(__file__)
        for parent in current.parents:
            if (parent / "pyproject.toml").exists() and (parent / "run_desktop_ui.py").exists():
                return parent

        # 폴백: 상대 경로 사용
        return Path(__file__).parents[4]

    def _load_config(self, force_reload: bool = False) -> Dict:
        """설정 파일 로드 (캐싱 지원)"""
        try:
            # 캐시 유효성 검사
            if not force_reload and self._config_cache and self._cache_timestamp:
                file_mtime = datetime.fromtimestamp(self._config_file.stat().st_mtime)
                if file_mtime <= self._cache_timestamp:
                    return self._config_cache

            # 설정 파일 로드
            with open(self._config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 환경변수 오버라이드 적용 (단순화)
            if config.get('env_override_enabled', False):
                self._apply_env_overrides(config)

            # 캐시 업데이트
            self._config_cache = config
            self._cache_timestamp = datetime.now()

            self.logger.debug("✅ 설정 파일 로드 완료")
            return config

        except Exception as e:
            self.logger.error(f"❌ 설정 파일 로드 실패: {e}")
            # 기본 설정 반환
            return self._get_default_config()

    def _apply_env_overrides(self, config: Dict) -> None:
        """환경변수 오버라이드 적용"""
        # UPBIT_DATA_DIR -> directories.data 매핑
        env_mappings = {
            'UPBIT_DATA_DIR': ['directories', 'data'],
            'UPBIT_LOGS_DIR': ['directories', 'logs'],
            'UPBIT_CONFIG_DIR': ['directories', 'config'],
            'UPBIT_BACKUPS_DIR': ['directories', 'backups'],
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value:
                target = config
                for key in config_path[:-1]:
                    target = target.setdefault(key, {})
                target[config_path[-1]] = env_value

    def _get_default_config(self) -> Dict:
        """기본 설정 반환 (폴백)"""
        return {
            'directories': {
                'data': 'data',
                'config': 'config',
                'logs': 'logs',
                'backups': 'backups'
            },
            'databases': {
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3',
                'market_data': 'data/market_data.sqlite3'
            },
            'security': {
                'secure_dir': 'config/secure',
                'api_credentials': 'config/secure/api_credentials.json'
            },
            'validation': {
                'required_files': ['pyproject.toml', 'run_desktop_ui.py'],
                'auto_create_dirs': True
            }
        }

    def _resolve_path(self, relative_path: str) -> Path:
        """상대 경로를 절대 경로로 변환"""
        if Path(relative_path).is_absolute():
            return Path(relative_path)
        return self._project_root / relative_path

    # IPathConfigurationRepository 구현

    def get_base_directory(self, dir_type: str) -> Path:
        """기본 디렉토리 경로 조회"""
        config = self._load_config()
        relative_path = config.get('directories', {}).get(dir_type, dir_type)
        return self._resolve_path(relative_path)

    def get_database_path(self, db_name: str) -> Path:
        """데이터베이스 파일 경로 조회"""
        config = self._load_config()
        relative_path = config.get('databases', {}).get(db_name, f"data/{db_name}.sqlite3")
        return self._resolve_path(relative_path)

    def get_security_path(self, resource: str) -> Path:
        """보안 관련 파일 경로 조회"""
        config = self._load_config()
        relative_path = config.get('security', {}).get(resource, f"config/secure/{resource}")
        return self._resolve_path(relative_path)

    def get_logging_config(self) -> Dict[str, Any]:
        """로깅 설정 조회"""
        config = self._load_config()
        return config.get('logging', {})

    def get_backup_config(self) -> Dict[str, Any]:
        """백업 설정 조회"""
        config = self._load_config()
        return config.get('backup', {})

    def update_database_path(self, db_name: str, new_path: Path) -> bool:
        """데이터베이스 경로 업데이트"""
        try:
            config = self._load_config(force_reload=True)

            # 상대 경로로 변환하여 저장
            relative_path = os.path.relpath(new_path, self._project_root)
            config.setdefault('databases', {})[db_name] = relative_path.replace('\\', '/')

            # 설정 파일 업데이트
            with open(self._config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

            # 캐시 무효화
            self._config_cache = None

            self.logger.info(f"✅ 데이터베이스 경로 업데이트: {db_name} -> {relative_path}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 경로 업데이트 실패: {e}")
            return False

    def get_required_files(self) -> List[str]:
        """필수 파일 목록 조회"""
        config = self._load_config()
        return config.get('validation', {}).get('required_files', [])

    def validate_structure(self) -> bool:
        """프로젝트 구조 유효성 검증"""
        try:
            required_files = self.get_required_files()
            for file_path in required_files:
                if not (self._project_root / file_path).exists():
                    self.logger.warning(f"⚠️ 필수 파일 누락: {file_path}")
                    return False

            self.logger.debug("✅ 프로젝트 구조 검증 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ 구조 검증 실패: {e}")
            return False

    def ensure_directories(self) -> bool:
        """필수 디렉토리 생성"""
        try:
            config = self._load_config()
            if not config.get('validation', {}).get('auto_create_dirs', True):
                return True

            # 기본 디렉토리 생성
            for dir_type in config.get('directories', {}).values():
                dir_path = self._resolve_path(dir_type)
                dir_path.mkdir(parents=True, exist_ok=True)

            # 보안 디렉토리 생성
            security_dir = config.get('security', {}).get('secure_dir', 'config/secure')
            self._resolve_path(security_dir).mkdir(parents=True, exist_ok=True)

            self.logger.debug("✅ 필수 디렉토리 생성 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ 디렉토리 생성 실패: {e}")
            return False
