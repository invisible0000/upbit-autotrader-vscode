"""
통합 설정 서비스

DDD 원칙에 따라 모든 설정을 통합 관리하며
YAML 파일 충돌을 해결하는 도메인 서비스입니다.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.database_configuration.services.database_path_service import DatabasePathService

class UnifiedConfigService:
    """통합 설정 관리 도메인 서비스"""

    def __init__(self, db_path_service: DatabasePathService, config_root: str = "config"):
        self.logger = create_component_logger("UnifiedConfigService")
        self.db_path_service = db_path_service
        self.config_root = Path(config_root)

        # 설정 파일 경로들
        self.main_config_path = self.config_root / "config.yaml"
        self.env_config_path = self.config_root / "config.development.yaml"

        self.logger.info("🔧 통합 설정 서비스 초기화 완료")

    def get_database_paths(self) -> Dict[str, str]:
        """
        데이터베이스 경로 조회 - DDD 서비스 우선 사용

        Returns:
            Dict[str, str]: 데이터베이스 타입별 경로
        """
        try:
            # 1차: DDD 서비스에서 동적 경로 조회
            paths = self.db_path_service.get_all_paths()
            self.logger.debug(f"✅ DDD 동적 경로 조회 성공: {len(paths)}개")
            return paths

        except Exception as e:
            self.logger.warning(f"⚠️ DDD 동적 경로 조회 실패, 설정 파일 폴백: {e}")

            # 2차: config.yaml 폴백 경로 사용
            return self._get_fallback_database_paths()

    def _get_fallback_database_paths(self) -> Dict[str, str]:
        """설정 파일에서 폴백 데이터베이스 경로 조회"""
        try:
            config = self._load_merged_config()
            db_config = config.get('database', {})

            return {
                'settings': db_config.get('fallback_settings_db', 'data/settings.sqlite3'),
                'strategies': db_config.get('fallback_strategies_db', 'data/strategies.sqlite3'),
                'market_data': db_config.get('fallback_market_data_db', 'data/market_data.sqlite3')
            }

        except Exception as e:
            self.logger.error(f"❌ 폴백 경로 조회 실패: {e}")
            # 최종 하드코딩 폴백
            return {
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3',
                'market_data': 'data/market_data.sqlite3'
            }

    def get_config(self, section: str = None) -> Dict[str, Any]:
        """
        통합 설정 조회

        Args:
            section: 특정 섹션만 조회할 경우 섹션명

        Returns:
            Dict[str, Any]: 병합된 설정
        """
        try:
            config = self._load_merged_config()

            # 데이터베이스 경로를 DDD 서비스로 업데이트
            if 'database' in config:
                dynamic_paths = self.get_database_paths()
                config['database']['current_paths'] = dynamic_paths

                # 동적 경로 사용 여부 확인
                if config['database'].get('use_dynamic_paths', True):
                    self.logger.debug("🔄 DDD 동적 경로를 설정에 적용")
                else:
                    self.logger.debug("📋 정적 폴백 경로 사용")

            if section:
                return config.get(section, {})

            return config

        except Exception as e:
            self.logger.error(f"❌ 설정 조회 실패: {e}")
            return {}

    def _load_merged_config(self) -> Dict[str, Any]:
        """메인 설정과 환경별 설정을 병합"""
        # 1. 메인 설정 로드
        main_config = self._load_yaml(self.main_config_path)

        # 2. 환경별 설정 로드 (development)
        env_config = self._load_yaml(self.env_config_path)

        # 3. 깊은 병합 수행
        merged = self._deep_merge(main_config, env_config)

        self.logger.debug(f"✅ 설정 병합 완료: main + env")
        return merged

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """YAML 파일 로드"""
        try:
            if not path.exists():
                self.logger.warning(f"⚠️ 설정 파일 없음: {path}")
                return {}

            with open(path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f) or {}
                self.logger.debug(f"📋 YAML 로드 성공: {path.name}")
                return content

        except Exception as e:
            self.logger.error(f"❌ YAML 로드 실패 {path}: {e}")
            return {}

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """딕셔너리 깊은 병합"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def validate_config(self) -> bool:
        """설정 유효성 검사"""
        try:
            config = self.get_config()

            # 필수 섹션 확인
            required_sections = ['database', 'logging', 'trading']
            for section in required_sections:
                if section not in config:
                    self.logger.error(f"❌ 필수 설정 섹션 누락: {section}")
                    return False

            # 데이터베이스 경로 유효성 확인
            db_paths = self.get_database_paths()
            if len(db_paths) != 3:
                self.logger.error(f"❌ 데이터베이스 경로 불완전: {len(db_paths)}/3")
                return False

            self.logger.info("✅ 설정 유효성 검사 통과")
            return True

        except Exception as e:
            self.logger.error(f"❌ 설정 유효성 검사 실패: {e}")
            return False

    def sync_with_ddd_system(self) -> bool:
        """DDD 시스템과 설정 동기화"""
        try:
            # DDD 서비스에서 현재 경로 조회
            current_paths = self.db_path_service.get_all_paths()

            # 메인 config.yaml 업데이트 (동적 참조 정보만)
            config = self._load_yaml(self.main_config_path)
            if 'database' not in config:
                config['database'] = {}

            config['database']['last_sync_at'] = datetime.now().isoformat()
            config['database']['ddd_service_active'] = True
            config['database']['dynamic_path_count'] = len(current_paths)

            # 파일 저장
            with open(self.main_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

            self.logger.info("✅ DDD 시스템과 설정 동기화 완료")
            return True

        except Exception as e:
            self.logger.error(f"❌ DDD 동기화 실패: {e}")
            return False
