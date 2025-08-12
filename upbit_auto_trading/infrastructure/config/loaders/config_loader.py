import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import os
from dataclasses import asdict

from upbit_auto_trading.infrastructure.config.models.config_models import (
    ApplicationConfig, Environment, DatabaseConfig, UpbitApiConfig,
    LoggingConfig, EventBusConfig, TradingConfig, UIConfig, DEFAULT_CONFIGS
)

class ConfigurationError(Exception):
    """설정 관련 오류"""
    pass

class ConfigLoader:
    """설정 로더"""

    def __init__(self, config_dir: Union[str, Path] = "config"):
        """
        Args:
            config_dir: 설정 파일 디렉토리 경로
        """
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise ConfigurationError(f"설정 디렉토리가 존재하지 않습니다: {self.config_dir}")

    def load_config(self, environment: Optional[str] = None) -> ApplicationConfig:
        """설정 로드"""
        # 환경 결정
        env = self._determine_environment(environment)

        # 기본 설정 로드
        base_config = self._load_base_config()

        # 환경별 설정 로드
        env_config = self._load_environment_config(env)

        # 설정 병합
        merged_config = self._merge_configs(base_config, env_config, env)

        # ApplicationConfig 객체 생성
        app_config = self._create_application_config(merged_config, env)

        # 설정 검증
        validation_errors = app_config.validate()
        if validation_errors:
            error_msg = "설정 검증 실패:\n" + "\n".join(f"- {error}" for error in validation_errors)
            raise ConfigurationError(error_msg)

        return app_config

    def _determine_environment(self, environment: Optional[str]) -> Environment:
        """실행 환경 결정"""
        # 명시적 환경 설정
        if environment:
            try:
                return Environment(environment)
            except ValueError:
                raise ConfigurationError(f"유효하지 않은 환경: {environment}")

        # 환경변수에서 로드
        env_var = os.getenv('UPBIT_ENVIRONMENT')
        if env_var:
            try:
                return Environment(env_var)
            except ValueError:
                raise ConfigurationError(f"환경변수 UPBIT_ENVIRONMENT 값이 유효하지 않습니다: {env_var}")

        # 기본값: development
        return Environment.DEVELOPMENT

    def _load_base_config(self) -> Dict[str, Any]:
        """기본 설정 로드"""
        base_config_path = self.config_dir / "config.yaml"

        if not base_config_path.exists():
            # 기본 설정 파일이 없으면 빈 딕셔너리 반환
            return {}

        return self._load_yaml_file(base_config_path)

    def _load_environment_config(self, environment: Environment) -> Dict[str, Any]:
        """환경별 설정 로드"""
        env_config_path = self.config_dir / f"config.{environment.value}.yaml"

        if env_config_path.exists():
            return self._load_yaml_file(env_config_path)

        # 환경별 설정 파일이 없으면 기본값 사용
        return DEFAULT_CONFIGS.get(environment, {})

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """YAML 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                return content if content is not None else {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"YAML 파일 파싱 오류 {file_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"설정 파일 로드 오류 {file_path}: {e}")

    def _merge_configs(self, base_config: Dict[str, Any],
                       env_config: Dict[str, Any],
                       environment: Environment) -> Dict[str, Any]:
        """설정 병합 (환경별 설정이 기본 설정을 오버라이드)"""
        merged = {}

        # 환경 설정
        merged['environment'] = environment.value

        # 각 섹션별 병합
        sections = ['database', 'upbit_api', 'logging', 'event_bus', 'trading', 'ui']

        for section in sections:
            section_config = {}

            # 기본 설정
            if section in base_config:
                section_config.update(base_config[section])

            # 환경별 설정으로 오버라이드
            if section in env_config:
                section_config.update(env_config[section])

            merged[section] = section_config

        return merged

    def _create_application_config(self, config_dict: Dict[str, Any],
                                   environment: Environment) -> ApplicationConfig:
        """딕셔너리에서 ApplicationConfig 객체 생성"""
        try:
            # LoggingConfig 필드 필터링 (유효한 필드만 전달)
            logging_data = config_dict.get('logging', {})
            valid_logging_fields = {
                'level', 'format', 'file_enabled', 'main_log_path', 'session_log_enabled',
                'session_log_path', 'llm_log_enabled', 'llm_main_log_path', 'llm_session_log_path',
                'console_enabled', 'console_level', 'context', 'scope', 'max_log_file_size',
                'backup_count', 'encoding', 'component_focus', 'feature_development',
                'llm_briefing_enabled', 'performance_monitoring', 'briefing_update_interval'
            }
            filtered_logging_data = {k: v for k, v in logging_data.items() if k in valid_logging_fields}

            return ApplicationConfig(
                environment=environment,
                database=DatabaseConfig(**config_dict.get('database', {})),
                upbit_api=UpbitApiConfig(**config_dict.get('upbit_api', {})),
                logging=LoggingConfig(**filtered_logging_data),
                event_bus=EventBusConfig(**config_dict.get('event_bus', {})),
                trading=TradingConfig(**config_dict.get('trading', {})),
                ui=UIConfig(**config_dict.get('ui', {}))
            )
        except TypeError as e:
            raise ConfigurationError(f"설정 객체 생성 오류: {e}")

    def save_config_template(self, output_path: Optional[Path] = None) -> Path:
        """설정 템플릿 파일 생성"""
        if output_path is None:
            output_path = self.config_dir / "config.template.yaml"

        # 기본 설정으로 템플릿 생성
        default_config = ApplicationConfig(
            environment=Environment.DEVELOPMENT,
            database=DatabaseConfig(),
            upbit_api=UpbitApiConfig(),
            logging=LoggingConfig(),
            event_bus=EventBusConfig(),
            trading=TradingConfig(),
            ui=UIConfig()
        )

        # dataclass를 딕셔너리로 변환
        config_dict = asdict(default_config)

        # 환경은 문자열로 변환
        config_dict['environment'] = config_dict['environment']

        # YAML로 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False,
                      allow_unicode=True, sort_keys=False)

        return output_path

class EnvironmentConfigManager:
    """환경별 설정 관리자"""

    def __init__(self, config_dir: Union[str, Path] = "config"):
        self.config_loader = ConfigLoader(config_dir)
        self._cached_configs: Dict[Environment, ApplicationConfig] = {}

    def get_config(self, environment: Optional[Environment] = None) -> ApplicationConfig:
        """설정 조회 (캐싱 지원)"""
        if environment is None:
            environment = Environment.DEVELOPMENT

        if environment not in self._cached_configs:
            self._cached_configs[environment] = self.config_loader.load_config(
                environment.value
            )

        return self._cached_configs[environment]

    def reload_config(self, environment: Environment) -> ApplicationConfig:
        """설정 다시 로드"""
        if environment in self._cached_configs:
            del self._cached_configs[environment]

        return self.get_config(environment)

    def clear_cache(self) -> None:
        """설정 캐시 지우기"""
        self._cached_configs.clear()

    def list_available_environments(self) -> List[Environment]:
        """사용 가능한 환경 목록"""
        return list(Environment)

    def validate_all_environments(self) -> Dict[Environment, List[str]]:
        """모든 환경의 설정 검증"""
        validation_results = {}

        for env in Environment:
            try:
                config = self.get_config(env)
                validation_results[env] = config.validate()
            except Exception as e:
                validation_results[env] = [f"설정 로드 실패: {str(e)}"]

        return validation_results
