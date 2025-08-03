# TASK-20250803-11

## Title
Infrastructure Layer - 설정 관리 시스템 구현 (Configuration Management & Dependency Injection)

## Objective (목표)
Clean Architecture의 Infrastructure Layer에서 애플리케이션 설정 관리와 의존성 주입 시스템을 구현합니다. 환경별 설정 분리, 타입 안전한 설정 로딩, 의존성 컨테이너를 통한 객체 생성 및 생명주기 관리를 제공하여 유지보수성과 테스트 가능성을 향상시킵니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 3: Infrastructure Layer 구현 (2주)" > "3.3 설정 관리 및 의존성 주입 (3일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-08`: Repository 구현 완료
- `TASK-20250803-09`: External API 클라이언트 구현 완료
- `TASK-20250803-10`: Event Bus 구현 완료
- 기존 `config/` 폴더 구조 분석 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 기존 설정 시스템 분석 및 요구사항 정의
- [ ] `config/config.yaml`, `config/database_config.yaml` 구조 분석
- [ ] 환경별 설정 분리 요구사항 (development, testing, production)
- [ ] 설정 검증 및 타입 안전성 요구사항
- [ ] 의존성 주입 대상 컴포넌트 식별

### 2. **[폴더 구조 생성]** Configuration 시스템 구조
- [ ] `upbit_auto_trading/infrastructure/config/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/config/models/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/config/loaders/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/dependency_injection/` 폴더 생성

### 3. **[새 코드 작성]** 설정 모델 정의
- [ ] `upbit_auto_trading/infrastructure/config/models/config_models.py` 생성:
```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
from enum import Enum

class Environment(Enum):
    """실행 환경"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    settings_db_path: str
    strategies_db_path: str
    market_data_db_path: str
    connection_timeout: int = 30
    max_connections: int = 10
    wal_mode: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    
    def __post_init__(self):
        """경로 검증 및 절대경로 변환"""
        self.settings_db_path = str(Path(self.settings_db_path).resolve())
        self.strategies_db_path = str(Path(self.strategies_db_path).resolve())
        self.market_data_db_path = str(Path(self.market_data_db_path).resolve())

@dataclass
class UpbitApiConfig:
    """Upbit API 설정"""
    base_url: str = "https://api.upbit.com/v1"
    requests_per_second: int = 10
    requests_per_minute: int = 600
    timeout_seconds: int = 30
    max_retries: int = 3
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    
    def __post_init__(self):
        """환경변수에서 API 키 로드"""
        if not self.access_key:
            self.access_key = os.getenv('UPBIT_ACCESS_KEY')
        if not self.secret_key:
            self.secret_key = os.getenv('UPBIT_SECRET_KEY')

@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "logs/upbit_auto_trading.log"
    file_max_size_mb: int = 100
    file_backup_count: int = 5
    console_enabled: bool = True
    context: str = "development"  # development, testing, production, debugging
    scope: str = "normal"         # silent, minimal, normal, verbose, debug_all
    component_focus: Optional[str] = None
    
    def __post_init__(self):
        """환경변수에서 로깅 설정 오버라이드"""
        self.context = os.getenv('UPBIT_LOG_CONTEXT', self.context)
        self.scope = os.getenv('UPBIT_LOG_SCOPE', self.scope)
        self.component_focus = os.getenv('UPBIT_COMPONENT_FOCUS', self.component_focus)
        if os.getenv('UPBIT_CONSOLE_OUTPUT', '').lower() == 'true':
            self.console_enabled = True

@dataclass
class EventBusConfig:
    """Event Bus 설정"""
    implementation: str = "in_memory"  # in_memory, sqlite, redis
    worker_count: int = 4
    batch_size: int = 10
    batch_timeout_seconds: float = 1.0
    max_queue_size: int = 10000
    retry_max_attempts: int = 3
    retry_delay_seconds: float = 1.0
    retry_exponential_base: float = 2.0
    storage_enabled: bool = True
    storage_cleanup_days: int = 7

@dataclass
class TradingConfig:
    """매매 설정"""
    max_position_size_krw: int = 1000000  # 최대 포지션 크기 (원)
    min_order_amount_krw: int = 5000      # 최소 주문 금액 (원)
    max_orders_per_minute: int = 10       # 분당 최대 주문 수
    stop_loss_enabled: bool = True
    take_profit_enabled: bool = True
    paper_trading: bool = True            # 모의 거래 모드
    allowed_markets: List[str] = field(default_factory=lambda: ["KRW-BTC", "KRW-ETH"])

@dataclass
class UIConfig:
    """UI 설정"""
    theme: str = "light"  # light, dark
    window_width: int = 1600
    window_height: int = 1000
    auto_refresh_interval_seconds: int = 5
    chart_update_interval_seconds: int = 1
    max_chart_candles: int = 200

@dataclass
class ApplicationConfig:
    """전체 애플리케이션 설정"""
    environment: Environment
    database: DatabaseConfig
    upbit_api: UpbitApiConfig
    logging: LoggingConfig
    event_bus: EventBusConfig
    trading: TradingConfig
    ui: UIConfig
    
    # 메타 정보
    app_name: str = "Upbit Auto Trading"
    app_version: str = "1.0.0"
    config_version: str = "1.0"
    
    def is_development(self) -> bool:
        """개발 환경인지 확인"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """테스트 환경인지 확인"""
        return self.environment == Environment.TESTING
    
    def is_production(self) -> bool:
        """프로덕션 환경인지 확인"""
        return self.environment == Environment.PRODUCTION
    
    def validate(self) -> List[str]:
        """설정 유효성 검사"""
        errors = []
        
        # 데이터베이스 경로 검증
        for db_path in [self.database.settings_db_path, 
                       self.database.strategies_db_path, 
                       self.database.market_data_db_path]:
            db_dir = Path(db_path).parent
            if not db_dir.exists():
                errors.append(f"데이터베이스 디렉토리가 존재하지 않습니다: {db_dir}")
        
        # 로그 디렉토리 검증
        log_dir = Path(self.logging.file_path).parent
        if not log_dir.exists():
            errors.append(f"로그 디렉토리가 존재하지 않습니다: {log_dir}")
        
        # API 키 검증 (프로덕션에서)
        if self.is_production() and not self.trading.paper_trading:
            if not self.upbit_api.access_key or not self.upbit_api.secret_key:
                errors.append("프로덕션 환경에서는 Upbit API 키가 필요합니다")
        
        # 매매 설정 검증
        if self.trading.max_position_size_krw < self.trading.min_order_amount_krw:
            errors.append("최대 포지션 크기가 최소 주문 금액보다 작습니다")
        
        return errors

# 환경별 기본 설정
DEFAULT_CONFIGS = {
    Environment.DEVELOPMENT: {
        "database": {
            "backup_enabled": False,
            "connection_timeout": 10
        },
        "logging": {
            "level": "DEBUG",
            "console_enabled": True
        },
        "trading": {
            "paper_trading": True,
            "max_position_size_krw": 100000
        },
        "event_bus": {
            "worker_count": 2,
            "storage_cleanup_days": 1
        }
    },
    Environment.TESTING: {
        "database": {
            "settings_db_path": ":memory:",
            "strategies_db_path": ":memory:",
            "market_data_db_path": ":memory:",
            "backup_enabled": False
        },
        "logging": {
            "level": "WARNING",
            "file_enabled": False,
            "console_enabled": False
        },
        "trading": {
            "paper_trading": True,
            "max_position_size_krw": 10000
        },
        "upbit_api": {
            "timeout_seconds": 5,
            "max_retries": 1
        }
    },
    Environment.PRODUCTION: {
        "database": {
            "backup_enabled": True,
            "backup_interval_hours": 6
        },
        "logging": {
            "level": "INFO",
            "console_enabled": False
        },
        "trading": {
            "paper_trading": False,  # 주의: 실제 거래
            "max_orders_per_minute": 5
        },
        "event_bus": {
            "worker_count": 8,
            "storage_cleanup_days": 30
        }
    }
}
```

### 4. **[새 코드 작성]** 설정 로더 구현
- [ ] `upbit_auto_trading/infrastructure/config/loaders/config_loader.py` 생성:
```python
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
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
            return ApplicationConfig(
                environment=environment,
                database=DatabaseConfig(**config_dict.get('database', {})),
                upbit_api=UpbitApiConfig(**config_dict.get('upbit_api', {})),
                logging=LoggingConfig(**config_dict.get('logging', {})),
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
            database=DatabaseConfig(
                settings_db_path="data/settings.sqlite3",
                strategies_db_path="data/strategies.sqlite3",
                market_data_db_path="data/market_data.sqlite3"
            ),
            upbit_api=UpbitApiConfig(),
            logging=LoggingConfig(),
            event_bus=EventBusConfig(),
            trading=TradingConfig(),
            ui=UIConfig()
        )
        
        # dataclass를 딕셔너리로 변환
        config_dict = asdict(default_config)
        
        # 환경은 문자열로 변환
        config_dict['environment'] = config_dict['environment'].value
        
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
```

### 5. **[새 코드 작성]** 의존성 주입 컨테이너
- [ ] `upbit_auto_trading/infrastructure/dependency_injection/container.py` 생성:
```python
from typing import Dict, Any, TypeVar, Type, Callable, Optional, List
from abc import ABC, abstractmethod
import inspect
from enum import Enum
import threading
import logging

T = TypeVar('T')

class LifetimeScope(Enum):
    """객체 생명주기 범위"""
    TRANSIENT = "transient"    # 매번 새 인스턴스
    SINGLETON = "singleton"    # 앱 전체에서 하나
    SCOPED = "scoped"         # 스코프 내에서 하나

class ServiceRegistration:
    """서비스 등록 정보"""
    
    def __init__(self, service_type: Type[T], implementation: Any,
                 lifetime: LifetimeScope = LifetimeScope.TRANSIENT,
                 factory: Optional[Callable] = None):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance: Optional[T] = None

class DIContainer:
    """의존성 주입 컨테이너"""
    
    def __init__(self, parent: Optional['DIContainer'] = None):
        """
        Args:
            parent: 부모 컨테이너 (계층적 컨테이너 지원)
        """
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._parent = parent
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._disposing = False
    
    def register_singleton(self, service_type: Type[T], 
                          implementation: Any = None) -> 'DIContainer':
        """싱글톤으로 서비스 등록"""
        return self._register(service_type, implementation, LifetimeScope.SINGLETON)
    
    def register_transient(self, service_type: Type[T], 
                          implementation: Any = None) -> 'DIContainer':
        """일시적(매번 새 인스턴스)으로 서비스 등록"""
        return self._register(service_type, implementation, LifetimeScope.TRANSIENT)
    
    def register_scoped(self, service_type: Type[T], 
                       implementation: Any = None) -> 'DIContainer':
        """스코프 내 싱글톤으로 서비스 등록"""
        return self._register(service_type, implementation, LifetimeScope.SCOPED)
    
    def register_factory(self, service_type: Type[T], 
                        factory: Callable[[], T],
                        lifetime: LifetimeScope = LifetimeScope.TRANSIENT) -> 'DIContainer':
        """팩토리 함수로 서비스 등록"""
        registration = ServiceRegistration(
            service_type=service_type,
            implementation=None,
            lifetime=lifetime,
            factory=factory
        )
        
        with self._lock:
            self._services[service_type] = registration
        
        return self
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'DIContainer':
        """기존 인스턴스로 서비스 등록 (싱글톤)"""
        registration = ServiceRegistration(
            service_type=service_type,
            implementation=instance,
            lifetime=LifetimeScope.SINGLETON
        )
        registration.instance = instance
        
        with self._lock:
            self._services[service_type] = registration
            self._instances[service_type] = instance
        
        return self
    
    def _register(self, service_type: Type[T], implementation: Any,
                 lifetime: LifetimeScope) -> 'DIContainer':
        """내부 등록 메서드"""
        if implementation is None:
            implementation = service_type
        
        registration = ServiceRegistration(
            service_type=service_type,
            implementation=implementation,
            lifetime=lifetime
        )
        
        with self._lock:
            self._services[service_type] = registration
        
        return self
    
    def resolve(self, service_type: Type[T]) -> T:
        """서비스 해결"""
        if self._disposing:
            raise RuntimeError("컨테이너가 해제된 상태입니다")
        
        with self._lock:
            # 현재 컨테이너에서 찾기
            if service_type in self._services:
                return self._create_instance(service_type)
            
            # 부모 컨테이너에서 찾기
            if self._parent:
                try:
                    return self._parent.resolve(service_type)
                except ServiceNotRegisteredError:
                    pass
            
            raise ServiceNotRegisteredError(f"서비스가 등록되지 않았습니다: {service_type}")
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """서비스 해결 시도 (실패 시 None 반환)"""
        try:
            return self.resolve(service_type)
        except ServiceNotRegisteredError:
            return None
    
    def _create_instance(self, service_type: Type[T]) -> T:
        """인스턴스 생성"""
        registration = self._services[service_type]
        
        # 싱글톤 인스턴스 확인
        if registration.lifetime == LifetimeScope.SINGLETON:
            if registration.instance is not None:
                return registration.instance
            
            if service_type in self._instances:
                return self._instances[service_type]
        
        # 스코프 인스턴스 확인
        elif registration.lifetime == LifetimeScope.SCOPED:
            if service_type in self._instances:
                return self._instances[service_type]
        
        # 새 인스턴스 생성
        if registration.factory:
            instance = registration.factory()
        else:
            instance = self._create_instance_with_injection(registration.implementation)
        
        # 인스턴스 캐싱
        if registration.lifetime == LifetimeScope.SINGLETON:
            registration.instance = instance
            self._instances[service_type] = instance
        elif registration.lifetime == LifetimeScope.SCOPED:
            self._instances[service_type] = instance
        
        return instance
    
    def _create_instance_with_injection(self, implementation_type: Type[T]) -> T:
        """의존성 주입을 통한 인스턴스 생성"""
        try:
            # 생성자 시그니처 분석
            init_signature = inspect.signature(implementation_type.__init__)
            
            # 생성자 매개변수 해결
            kwargs = {}
            for param_name, param in init_signature.parameters.items():
                if param_name == 'self':
                    continue
                
                # 타입 힌트가 있는 경우
                if param.annotation != inspect.Parameter.empty:
                    try:
                        kwargs[param_name] = self.resolve(param.annotation)
                    except ServiceNotRegisteredError:
                        # 기본값이 있으면 사용
                        if param.default != inspect.Parameter.empty:
                            kwargs[param_name] = param.default
                        else:
                            raise DependencyResolutionError(
                                f"{implementation_type} 생성자의 매개변수 '{param_name}' "
                                f"(타입: {param.annotation})을 해결할 수 없습니다"
                            )
                
                # 기본값 사용
                elif param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
            
            return implementation_type(**kwargs)
            
        except Exception as e:
            self._logger.error(f"인스턴스 생성 실패 {implementation_type}: {e}")
            raise DependencyResolutionError(f"인스턴스 생성 실패: {e}") from e
    
    def is_registered(self, service_type: Type[T]) -> bool:
        """서비스 등록 여부 확인"""
        return service_type in self._services or (
            self._parent and self._parent.is_registered(service_type)
        )
    
    def create_scope(self) -> 'DIContainer':
        """새 스코프 생성"""
        return DIContainer(parent=self)
    
    def get_registrations(self) -> List[ServiceRegistration]:
        """등록된 서비스 목록 조회"""
        with self._lock:
            return list(self._services.values())
    
    def dispose(self) -> None:
        """컨테이너 해제"""
        with self._lock:
            self._disposing = True
            
            # IDisposable 인터페이스를 구현한 인스턴스들 해제
            for instance in self._instances.values():
                if hasattr(instance, 'dispose'):
                    try:
                        instance.dispose()
                    except Exception as e:
                        self._logger.warning(f"인스턴스 해제 실패: {e}")
            
            self._instances.clear()
            self._services.clear()
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.dispose()

class ServiceNotRegisteredError(Exception):
    """서비스가 등록되지 않은 경우 발생하는 예외"""
    pass

class DependencyResolutionError(Exception):
    """의존성 해결 실패 시 발생하는 예외"""
    pass

# 전역 컨테이너 (선택적 사용)
_global_container: Optional[DIContainer] = None

def get_global_container() -> DIContainer:
    """전역 컨테이너 조회"""
    global _global_container
    if _global_container is None:
        _global_container = DIContainer()
    return _global_container

def set_global_container(container: DIContainer) -> None:
    """전역 컨테이너 설정"""
    global _global_container
    _global_container = container

def reset_global_container() -> None:
    """전역 컨테이너 재설정"""
    global _global_container
    if _global_container:
        _global_container.dispose()
    _global_container = None
```

### 6. **[새 코드 작성]** 애플리케이션 컨텍스트
- [ ] `upbit_auto_trading/infrastructure/dependency_injection/app_context.py` 생성:
```python
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from upbit_auto_trading.infrastructure.config.models.config_models import ApplicationConfig
from upbit_auto_trading.infrastructure.config.loaders.config_loader import ConfigLoader
from upbit_auto_trading.infrastructure.dependency_injection.container import DIContainer
from upbit_auto_trading.infrastructure.external_apis import ApiClientFactory, UpbitClient

class ApplicationContext:
    """애플리케이션 컨텍스트 - 설정과 의존성 주입을 통합 관리"""
    
    def __init__(self, config_dir: str = "config", environment: Optional[str] = None):
        """
        Args:
            config_dir: 설정 파일 디렉토리
            environment: 실행 환경 (None이면 자동 감지)
        """
        self._config_dir = config_dir
        self._environment = environment
        self._config: Optional[ApplicationConfig] = None
        self._container: Optional[DIContainer] = None
        self._logger = logging.getLogger(__name__)
        self._initialized = False
    
    def initialize(self) -> None:
        """애플리케이션 컨텍스트 초기화"""
        if self._initialized:
            return
        
        try:
            # 1. 설정 로드
            self._load_configuration()
            
            # 2. 로깅 설정
            self._setup_logging()
            
            # 3. 의존성 컨테이너 설정
            self._setup_dependency_injection()
            
            # 4. 핵심 서비스 등록
            self._register_core_services()
            
            self._initialized = True
            self._logger.info(f"✅ 애플리케이션 컨텍스트 초기화 완료 (환경: {self.config.environment.value})")
            
        except Exception as e:
            self._logger.error(f"❌ 애플리케이션 컨텍스트 초기화 실패: {e}")
            raise
    
    def _load_configuration(self) -> None:
        """설정 로드"""
        config_loader = ConfigLoader(self._config_dir)
        self._config = config_loader.load_config(self._environment)
        
        self._logger.debug(f"설정 로드 완료: {self._config.environment.value}")
    
    def _setup_logging(self) -> None:
        """로깅 설정"""
        log_config = self._config.logging
        
        # 로그 레벨 설정
        logging.getLogger().setLevel(getattr(logging, log_config.level.upper()))
        
        # 로그 디렉토리 생성
        if log_config.file_enabled:
            log_path = Path(log_config.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._logger.debug("로깅 설정 완료")
    
    def _setup_dependency_injection(self) -> None:
        """의존성 주입 컨테이너 설정"""
        self._container = DIContainer()
        
        # 설정 객체 등록
        self._container.register_instance(ApplicationConfig, self._config)
        
        self._logger.debug("의존성 주입 컨테이너 설정 완료")
    
    def _register_core_services(self) -> None:
        """핵심 서비스 등록"""
        # API 클라이언트 팩토리
        self._container.register_factory(
            UpbitClient,
            lambda: ApiClientFactory.create_upbit_client(
                self._config.upbit_api.access_key,
                self._config.upbit_api.secret_key
            ),
            lifetime=DIContainer.LifetimeScope.SINGLETON
        )
        
        # Repository 등록 (다른 태스크에서 구현된 것들)
        self._register_repositories()
        
        # Event Bus 등록
        self._register_event_system()
        
        self._logger.debug("핵심 서비스 등록 완료")
    
    def _register_repositories(self) -> None:
        """Repository 등록"""
        # 이전 태스크에서 구현된 Repository들을 등록
        # (실제 구현에서는 import 후 등록)
        pass
    
    def _register_event_system(self) -> None:
        """Event System 등록"""
        # 이전 태스크에서 구현된 Event Bus를 등록
        # (실제 구현에서는 import 후 등록)
        pass
    
    @property
    def config(self) -> ApplicationConfig:
        """애플리케이션 설정"""
        if not self._initialized:
            raise RuntimeError("애플리케이션 컨텍스트가 초기화되지 않았습니다")
        return self._config
    
    @property
    def container(self) -> DIContainer:
        """의존성 주입 컨테이너"""
        if not self._initialized:
            raise RuntimeError("애플리케이션 컨텍스트가 초기화되지 않았습니다")
        return self._container
    
    def resolve(self, service_type):
        """서비스 해결"""
        return self.container.resolve(service_type)
    
    def create_scope(self):
        """새 의존성 스코프 생성"""
        return self.container.create_scope()
    
    def reload_configuration(self) -> None:
        """설정 다시 로드"""
        if not self._initialized:
            return
        
        self._logger.info("설정 다시 로드 중...")
        
        # 새 설정 로드
        config_loader = ConfigLoader(self._config_dir)
        new_config = config_loader.load_config(self._environment)
        
        # 설정 업데이트
        old_env = self._config.environment
        self._config = new_config
        
        # 컨테이너의 설정 인스턴스 업데이트
        self._container.register_instance(ApplicationConfig, self._config)
        
        self._logger.info(f"설정 다시 로드 완료: {old_env.value} -> {new_config.environment.value}")
    
    def dispose(self) -> None:
        """애플리케이션 컨텍스트 해제"""
        if self._container:
            self._container.dispose()
            self._container = None
        
        self._initialized = False
        self._logger.info("애플리케이션 컨텍스트 해제 완료")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.dispose()

# 애플리케이션 전역 컨텍스트 (선택적 사용)
_app_context: Optional[ApplicationContext] = None

def get_application_context() -> ApplicationContext:
    """전역 애플리케이션 컨텍스트 조회"""
    global _app_context
    if _app_context is None:
        _app_context = ApplicationContext()
        _app_context.initialize()
    return _app_context

def set_application_context(context: ApplicationContext) -> None:
    """전역 애플리케이션 컨텍스트 설정"""
    global _app_context
    if _app_context:
        _app_context.dispose()
    _app_context = context

def reset_application_context() -> None:
    """전역 애플리케이션 컨텍스트 재설정"""
    global _app_context
    if _app_context:
        _app_context.dispose()
    _app_context = None
```

### 7. **[업데이트]** 기존 설정 파일 개선
- [ ] `config/config.yaml` 업데이트:
```yaml
# Upbit Auto Trading System - Base Configuration

# 데이터베이스 설정
database:
  settings_db_path: "data/settings.sqlite3"
  strategies_db_path: "data/strategies.sqlite3"
  market_data_db_path: "data/market_data.sqlite3"
  connection_timeout: 30
  max_connections: 10
  wal_mode: true
  backup_enabled: true
  backup_interval_hours: 24

# Upbit API 설정
upbit_api:
  base_url: "https://api.upbit.com/v1"
  requests_per_second: 10
  requests_per_minute: 600
  timeout_seconds: 30
  max_retries: 3
  # API 키는 환경변수에서 로드: UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY

# 로깅 설정
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_enabled: true
  file_path: "logs/upbit_auto_trading.log"
  file_max_size_mb: 100
  file_backup_count: 5
  console_enabled: true
  context: "development"
  scope: "normal"

# Event Bus 설정
event_bus:
  implementation: "in_memory"
  worker_count: 4
  batch_size: 10
  batch_timeout_seconds: 1.0
  max_queue_size: 10000
  retry_max_attempts: 3
  retry_delay_seconds: 1.0
  retry_exponential_base: 2.0
  storage_enabled: true
  storage_cleanup_days: 7

# 매매 설정
trading:
  max_position_size_krw: 1000000
  min_order_amount_krw: 5000
  max_orders_per_minute: 10
  stop_loss_enabled: true
  take_profit_enabled: true
  paper_trading: true
  allowed_markets:
    - "KRW-BTC"
    - "KRW-ETH"
    - "KRW-XRP"

# UI 설정
ui:
  theme: "light"
  window_width: 1600
  window_height: 1000
  auto_refresh_interval_seconds: 5
  chart_update_interval_seconds: 1
  max_chart_candles: 200

# 애플리케이션 메타정보
app_name: "Upbit Auto Trading"
app_version: "1.0.0"
config_version: "1.0"
```

### 8. **[새 파일 생성]** 환경별 설정 파일들
- [ ] `config/config.development.yaml` 생성:
```yaml
# Development Environment Overrides

database:
  backup_enabled: false
  connection_timeout: 10

logging:
  level: "DEBUG"
  console_enabled: true

trading:
  paper_trading: true
  max_position_size_krw: 100000

event_bus:
  worker_count: 2
  storage_cleanup_days: 1
```

- [ ] `config/config.testing.yaml` 생성:
```yaml
# Testing Environment Overrides

database:
  settings_db_path: ":memory:"
  strategies_db_path: ":memory:"
  market_data_db_path: ":memory:"
  backup_enabled: false

logging:
  level: "WARNING"
  file_enabled: false
  console_enabled: false

trading:
  paper_trading: true
  max_position_size_krw: 10000

upbit_api:
  timeout_seconds: 5
  max_retries: 1
```

- [ ] `config/config.production.yaml` 생성:
```yaml
# Production Environment Overrides

database:
  backup_enabled: true
  backup_interval_hours: 6

logging:
  level: "INFO"
  console_enabled: false

trading:
  paper_trading: false  # 주의: 실제 거래
  max_orders_per_minute: 5

event_bus:
  worker_count: 8
  storage_cleanup_days: 30
```

### 9. **[테스트 코드 작성]** Configuration 시스템 테스트
- [ ] `tests/infrastructure/config/` 폴더 생성
- [ ] `tests/infrastructure/config/test_config_loader.py` 생성:
```python
import pytest
import tempfile
import yaml
from pathlib import Path

from upbit_auto_trading.infrastructure.config.loaders.config_loader import (
    ConfigLoader, EnvironmentConfigManager, ConfigurationError
)
from upbit_auto_trading.infrastructure.config.models.config_models import (
    Environment, ApplicationConfig
)

class TestConfigLoader:
    @pytest.fixture
    def temp_config_dir(self):
        """임시 설정 디렉토리"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            
            # 기본 설정 파일 생성
            base_config = {
                'database': {
                    'settings_db_path': 'data/settings.sqlite3',
                    'strategies_db_path': 'data/strategies.sqlite3',
                    'market_data_db_path': 'data/market_data.sqlite3'
                },
                'logging': {
                    'level': 'INFO'
                }
            }
            
            with open(config_dir / 'config.yaml', 'w') as f:
                yaml.dump(base_config, f)
            
            # 개발 환경 설정 파일 생성
            dev_config = {
                'logging': {
                    'level': 'DEBUG'
                },
                'trading': {
                    'paper_trading': True
                }
            }
            
            with open(config_dir / 'config.development.yaml', 'w') as f:
                yaml.dump(dev_config, f)
            
            yield config_dir
    
    def test_load_base_config(self, temp_config_dir):
        # Given
        loader = ConfigLoader(temp_config_dir)
        
        # When
        config = loader.load_config('development')
        
        # Then
        assert isinstance(config, ApplicationConfig)
        assert config.environment == Environment.DEVELOPMENT
        assert config.logging.level == 'DEBUG'  # 환경별 오버라이드
        assert config.trading.paper_trading == True
    
    def test_environment_override(self, temp_config_dir):
        # Given
        loader = ConfigLoader(temp_config_dir)
        
        # When
        config = loader.load_config('testing')
        
        # Then
        assert config.environment == Environment.TESTING
        # 기본 설정값 사용
        assert config.database.settings_db_path == ':memory:'  # 테스트 기본값
    
    def test_config_validation_error(self, temp_config_dir):
        # Given
        invalid_config = {
            'trading': {
                'max_position_size_krw': 1000,  # 너무 작음
                'min_order_amount_krw': 5000   # 더 큼
            }
        }
        
        with open(temp_config_dir / 'config.invalid.yaml', 'w') as f:
            yaml.dump(invalid_config, f)
        
        loader = ConfigLoader(temp_config_dir)
        
        # When & Then
        with pytest.raises(ConfigurationError):
            loader.load_config('invalid')

class TestDependencyInjection:
    def test_container_registration_and_resolution(self):
        # Given
        from upbit_auto_trading.infrastructure.dependency_injection.container import DIContainer
        
        container = DIContainer()
        
        # When
        container.register_singleton(str, "test_string")
        result = container.resolve(str)
        
        # Then
        assert result == "test_string"
    
    def test_automatic_dependency_injection(self):
        # Given
        from upbit_auto_trading.infrastructure.dependency_injection.container import DIContainer
        
        class ServiceA:
            def __init__(self):
                self.value = "A"
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a
                self.value = "B"
        
        container = DIContainer()
        container.register_singleton(ServiceA)
        container.register_transient(ServiceB)
        
        # When
        service_b = container.resolve(ServiceB)
        
        # Then
        assert isinstance(service_b, ServiceB)
        assert isinstance(service_b.service_a, ServiceA)
        assert service_b.service_a.value == "A"
```

### 10. **[통합]** Configuration 시스템 초기화
- [ ] `upbit_auto_trading/infrastructure/config/__init__.py` 생성:
```python
from .models.config_models import ApplicationConfig, Environment
from .loaders.config_loader import ConfigLoader, EnvironmentConfigManager

__all__ = ['ApplicationConfig', 'Environment', 'ConfigLoader', 'EnvironmentConfigManager']
```

- [ ] `upbit_auto_trading/infrastructure/dependency_injection/__init__.py` 생성:
```python
from .container import DIContainer, LifetimeScope
from .app_context import ApplicationContext, get_application_context

__all__ = ['DIContainer', 'LifetimeScope', 'ApplicationContext', 'get_application_context']
```

## Verification Criteria (완료 검증 조건)

### **[설정 시스템 검증]** 모든 환경별 설정 정상 로드 확인
- [ ] `pytest tests/infrastructure/config/ -v` 실행하여 모든 테스트 통과
- [ ] Python REPL에서 설정 로드 테스트:
```python
from upbit_auto_trading.infrastructure.config import ConfigLoader

# 모든 환경 설정 검증
loader = ConfigLoader()
for env in ['development', 'testing', 'production']:
    config = loader.load_config(env)
    print(f"✅ {env} 설정 로드 성공")
    print(f"   - 환경: {config.environment.value}")
    print(f"   - 로그 레벨: {config.logging.level}")
    print(f"   - 모의 거래: {config.trading.paper_trading}")
```

### **[의존성 주입 검증]** DIContainer 정상 동작 확인
- [ ] 서비스 등록 및 해결 테스트
- [ ] 생명주기 관리 (Singleton, Transient, Scoped) 확인
- [ ] 자동 의존성 주입 동작 확인

### **[애플리케이션 컨텍스트 검증]** 통합 시스템 동작 확인
- [ ] ApplicationContext 초기화 및 설정 로드 확인
- [ ] 핵심 서비스들의 DI 등록 확인
- [ ] 컨텍스트 생명주기 관리 확인

### **[설정 파일 검증]** 모든 환경별 설정 파일 유효성 확인
- [ ] 기본 `config.yaml` 파일 구문 검증
- [ ] 환경별 설정 파일 오버라이드 동작 확인
- [ ] 설정 검증 로직 정상 동작 확인

## Notes (주의사항)
- 환경변수를 통한 설정 오버라이드 지원
- 프로덕션 환경에서는 API 키 필수 검증
- 설정 변경 시 애플리케이션 재시작 고려
- 의존성 순환 참조 방지
- 컨테이너 생명주기 적절한 관리
- 설정 파일 보안 고려 (API 키 등)
