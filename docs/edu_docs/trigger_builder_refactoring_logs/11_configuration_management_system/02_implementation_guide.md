# 🛠️ Configuration Management System 구현 가이드

> **대상**: Infrastructure Layer 설정 관리 시스템 구현을 담당하는 개발자
> **목적**: 단계별 구현 방법과 핵심 패턴 제공
> **참조**: Clean Architecture, DDD, 의존성 주입 패턴

## 📋 시스템 개요

### 구현 목표
- 환경별 설정 분리 (development/testing/production)
- 타입 안전한 설정 관리 (dataclass 기반)
- 통합 의존성 주입 시스템 (생명주기 관리)
- Clean Architecture Infrastructure Layer 완성

### 핵심 컴포넌트
```
upbit_auto_trading/infrastructure/
├── config/                          # 설정 관리 시스템
│   ├── models/config_models.py      # dataclass 설정 모델
│   └── loaders/config_loader.py     # YAML 로더
└── dependency_injection/            # DI 시스템
    ├── container.py                 # DI 컨테이너
    └── app_context.py              # 애플리케이션 컨텍스트
```

## 🔧 Step 1: 설정 모델 구현

### 1.1 Environment Enum 정의
```python
from enum import Enum

class Environment(Enum):
    """애플리케이션 실행 환경"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

    @classmethod
    def from_string(cls, value: str) -> 'Environment':
        """문자열에서 Environment 변환"""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.DEVELOPMENT  # 기본값
```

**💡 구현 포인트:**
- 기본값을 DEVELOPMENT로 설정하여 안전성 확보
- from_string() 메서드로 환경변수 처리 간소화

### 1.2 Configuration Dataclass 구현 패턴
```python
from dataclasses import dataclass, field
from typing import Optional
import os

@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    settings_db_path: str = "data/settings.sqlite3"
    strategies_db_path: str = "data/strategies.sqlite3"
    market_data_db_path: str = "data/market_data.sqlite3"
    connection_timeout: int = 30
    enable_backup: bool = True
    backup_interval_hours: int = 24

    def __post_init__(self):
        """환경변수 오버라이드 처리"""
        # 환경변수가 있으면 해당 값으로 오버라이드
        if db_path := os.environ.get('UPBIT_SETTINGS_DB_PATH'):
            self.settings_db_path = db_path
        if timeout := os.environ.get('UPBIT_DB_TIMEOUT'):
            self.connection_timeout = int(timeout)
```

**💡 구현 포인트:**
- `__post_init__()`에서 환경변수 처리
- walrus operator(`:=`)로 간결한 조건문 작성
- 타입 변환 시 예외 처리 고려

### 1.3 환경별 기본값 시스템
```python
# 환경별 기본 설정값 정의
DEFAULT_CONFIGS = {
    Environment.DEVELOPMENT: {
        'logging': {'level': 'DEBUG', 'console_enabled': True},
        'trading': {'paper_trading': True, 'max_position_size_krw': 100000},
        'ui': {'headless': False}
    },
    Environment.TESTING: {
        'logging': {'level': 'WARNING', 'console_enabled': False},
        'trading': {'paper_trading': True, 'max_position_size_krw': 10000},
        'ui': {'headless': True}
    },
    Environment.PRODUCTION: {
        'logging': {'level': 'INFO', 'console_enabled': False},
        'trading': {'paper_trading': False, 'max_position_size_krw': 5000000},
        'database': {'enable_backup': True}
    }
}
```

**💡 구현 포인트:**
- 환경별로 명확한 차별화 전략
- development: 디버깅 친화적
- testing: 격리된 테스트 환경
- production: 실운영 최적화

## 🔧 Step 2: 설정 로더 구현

### 2.1 ConfigLoader 핵심 구조
```python
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """YAML 기반 계층적 설정 로더"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)

    def load_config(self, environment: Environment) -> ApplicationConfig:
        """환경별 설정 로드"""
        # 1. 기본 설정 로드
        base_config = self._load_base_config()

        # 2. 환경별 설정 로드
        env_config = self._load_environment_config(environment)

        # 3. 환경별 기본값 적용
        defaults = DEFAULT_CONFIGS.get(environment, {})

        # 4. 설정 병합 (우선순위: 환경설정 > 기본설정 > 기본값)
        merged_config = self._merge_configs(defaults, base_config, env_config)

        # 5. ApplicationConfig 객체 생성
        return self._create_application_config(merged_config, environment)
```

**💡 구현 포인트:**
- 명확한 우선순위: 환경설정 > 기본설정 > 기본값
- 각 단계를 별도 메서드로 분리하여 테스트 용이성 확보

### 2.2 설정 병합 로직
```python
def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
    """여러 설정을 깊은 병합"""
    result = {}

    for config in configs:
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 중첩된 딕셔너리는 재귀적으로 병합
                result[key] = self._merge_configs(result[key], value)
            else:
                # 단순 값은 덮어쓰기
                result[key] = value

    return result
```

**💡 구현 포인트:**
- 깊은 병합으로 중첩 구조 지원
- 재귀적 병합으로 모든 레벨 처리

### 2.3 설정 검증 통합
```python
def _create_application_config(self, config_dict: Dict[str, Any],
                             environment: Environment) -> ApplicationConfig:
    """설정 딕셔너리에서 ApplicationConfig 생성"""
    try:
        app_config = ApplicationConfig(
            environment=environment,
            database=DatabaseConfig(**config_dict.get('database', {})),
            upbit_api=UpbitApiConfig(**config_dict.get('upbit_api', {})),
            # ... 다른 설정들
        )

        # 비즈니스 규칙 검증
        app_config.validate()
        return app_config

    except Exception as e:
        raise ConfigurationError(f"설정 생성 실패: {e}") from e
```

**💡 구현 포인트:**
- dataclass 언패킹으로 간결한 객체 생성
- validate() 메서드로 비즈니스 규칙 검증
- 명확한 예외 메시지 제공

## 🔧 Step 3: 의존성 주입 컨테이너 구현

### 3.1 생명주기 관리 시스템
```python
from enum import Enum
from dataclasses import dataclass
from typing import Type, Any, Callable, Optional
import threading

class LifetimeScope(Enum):
    """서비스 생명주기 유형"""
    SINGLETON = "singleton"    # 전역 단일 인스턴스
    TRANSIENT = "transient"    # 요청 시마다 새 인스턴스
    SCOPED = "scoped"         # 스코프별 단일 인스턴스

@dataclass
class ServiceRegistration:
    """서비스 등록 정보"""
    service_type: Type
    implementation_type: Type
    lifetime: LifetimeScope
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
```

**💡 구현 포인트:**
- Enum으로 생명주기 타입 안전성 확보
- dataclass로 등록 정보 구조화

### 3.2 DIContainer 핵심 로직
```python
class DIContainer:
    """스레드 안전 의존성 주입 컨테이너"""

    def __init__(self):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()  # 재진입 가능한 락

    def register_singleton(self, service_type: Type, implementation_type: Type):
        """싱글톤 서비스 등록"""
        with self._lock:
            self._services[service_type] = ServiceRegistration(
                service_type=service_type,
                implementation_type=implementation_type,
                lifetime=LifetimeScope.SINGLETON
            )

    def resolve(self, service_type: Type) -> Any:
        """서비스 해결 (인스턴스 반환)"""
        with self._lock:
            registration = self._services.get(service_type)
            if not registration:
                raise ServiceNotRegisteredError(f"서비스 {service_type} 미등록")

            return self._create_instance(registration)
```

**💡 구현 포인트:**
- threading.RLock으로 데드락 방지
- 명확한 예외 처리로 디버깅 지원

### 3.3 자동 의존성 주입
```python
import inspect

def _create_instance(self, registration: ServiceRegistration) -> Any:
    """등록 정보에 따라 인스턴스 생성"""
    if registration.lifetime == LifetimeScope.SINGLETON:
        # 싱글톤: 기존 인스턴스가 있으면 반환
        if registration.service_type in self._instances:
            return self._instances[registration.service_type]

    # 새 인스턴스 생성
    instance = self._instantiate_with_dependencies(registration.implementation_type)

    if registration.lifetime == LifetimeScope.SINGLETON:
        # 싱글톤은 인스턴스 캐시
        self._instances[registration.service_type] = instance

    return instance

def _instantiate_with_dependencies(self, cls: Type) -> Any:
    """생성자 의존성 자동 주입"""
    signature = inspect.signature(cls.__init__)
    args = {}

    for param_name, param in signature.parameters.items():
        if param_name == 'self':
            continue

        # 타입 힌트에서 의존성 해결
        param_type = param.annotation
        if param_type in self._services:
            args[param_name] = self.resolve(param_type)
        elif param.default is not param.empty:
            # 기본값 사용
            args[param_name] = param.default
        else:
            raise DependencyResolutionError(f"의존성 해결 실패: {param_type}")

    return cls(**args)
```

**💡 구현 포인트:**
- inspect 모듈로 생성자 시그니처 분석
- 타입 힌트 기반 자동 의존성 해결
- 기본값 지원으로 유연성 확보

## 🔧 Step 4: 애플리케이션 컨텍스트 구현

### 4.1 통합 초기화 프로세스
```python
class ApplicationContext:
    """애플리케이션 전체 컨텍스트 관리"""

    def __init__(self, environment: str = "development"):
        self.environment = Environment.from_string(environment)
        self.config: Optional[ApplicationConfig] = None
        self.container: Optional[DIContainer] = None

    def initialize(self) -> None:
        """4단계 초기화 프로세스"""
        try:
            # 1. 설정 로드
            self._load_configuration()

            # 2. 로깅 시스템 초기화
            self._setup_logging()

            # 3. DI 컨테이너 초기화
            self._setup_container()

            # 4. 핵심 서비스 등록
            self._register_core_services()

        except Exception as e:
            raise ApplicationContextError(f"컨텍스트 초기화 실패: {e}") from e
```

**💡 구현 포인트:**
- 명확한 4단계 초기화 프로세스
- 각 단계별 실패 시 명확한 에러 메시지

### 4.2 컨텍스트 매니저 패턴
```python
def __enter__(self) -> 'ApplicationContext':
    """컨텍스트 진입"""
    if not self.config or not self.container:
        self.initialize()
    return self

def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    """컨텍스트 종료 - 리소스 정리"""
    if self.container:
        self.container.dispose()
    self.config = None
    self.container = None
```

**💡 구현 포인트:**
- with 구문으로 안전한 리소스 관리
- 명시적 dispose()로 메모리 누수 방지

### 4.3 전역 컨텍스트 관리
```python
# 전역 컨텍스트 관리
_global_context: Optional[ApplicationContext] = None
_context_lock = threading.Lock()

def get_application_context() -> Optional[ApplicationContext]:
    """전역 애플리케이션 컨텍스트 조회"""
    with _context_lock:
        return _global_context

def set_application_context(context: ApplicationContext) -> None:
    """전역 애플리케이션 컨텍스트 설정"""
    global _global_context
    with _context_lock:
        _global_context = context
```

**💡 구현 포인트:**
- 스레드 안전한 전역 컨텍스트 관리
- 명시적 설정/해제로 생명주기 제어

## 🔧 Step 5: 환경별 설정 파일 구성

### 5.1 기본 설정 파일 구조 (config.yaml)
```yaml
# 애플리케이션 메타정보
app_name: "Upbit Auto Trading"
app_version: "1.0.0"
config_version: "1.0"

# 데이터베이스 설정 (3-DB 아키텍처)
database:
  settings_db_path: "data/settings.sqlite3"
  strategies_db_path: "data/strategies.sqlite3"
  market_data_db_path: "data/market_data.sqlite3"
  connection_timeout: 30
  enable_backup: false  # 환경별로 오버라이드

# 업비트 API 설정
upbit_api:
  base_url: "https://api.upbit.com"
  websocket_url: "wss://api.upbit.com/websocket/v1"
  requests_per_second: 5
  timeout_seconds: 10
  max_retries: 3

# 기타 공통 설정들...
```

**💡 구현 포인트:**
- 모든 환경에서 공통으로 사용할 기본값
- 환경별 오버라이드가 필요한 부분은 적절한 기본값 설정

### 5.2 환경별 오버라이드 (config.development.yaml)
```yaml
# 개발 환경 전용 설정
development:
  debug_mode: true

logging:
  level: "DEBUG"
  console_enabled: true

trading:
  paper_trading: true  # 모의거래
  max_position_size_krw: 100000  # 소액

database:
  enable_backup: false  # 개발에서는 백업 비활성화
```

**💡 구현 포인트:**
- 최소 오버라이드 원칙: 필요한 부분만 변경
- 개발 친화적 설정: DEBUG 로그, 모의거래, 콘솔 출력

### 5.3 테스트 환경 설정 (config.testing.yaml)
```yaml
# 테스트 환경 전용 설정
testing:
  fast_mode: true

logging:
  level: "WARNING"  # 테스트 노이즈 최소화
  console_enabled: false

database:
  # 테스트는 인메모리 또는 별도 DB 사용
  settings_db_path: ":memory:"
  connection_timeout: 5  # 빠른 실패

trading:
  max_position_size_krw: 10000  # 극소액

ui:
  headless: true  # 헤드리스 모드
```

**💡 구현 포인트:**
- 테스트 격리: 인메모리 DB, 헤드리스 모드
- 빠른 실행: 짧은 타임아웃, 최소 로그

## 🧪 Step 6: 테스트 전략

### 6.1 테스트 구조
```python
# tests/infrastructure/config/test_config_loader.py
import pytest
from pathlib import Path
import tempfile
import yaml

class TestConfigLoader:
    """ConfigLoader 테스트"""

    @pytest.fixture
    def temp_config_dir(self):
        """임시 설정 디렉토리 생성"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)

            # 기본 설정 파일 생성
            base_config = {
                'app_name': 'Test App',
                'database': {'connection_timeout': 30}
            }
            with open(config_dir / 'config.yaml', 'w') as f:
                yaml.dump(base_config, f)

            # 환경별 설정 파일 생성
            dev_config = {
                'logging': {'level': 'DEBUG'},
                'database': {'connection_timeout': 10}  # 오버라이드
            }
            with open(config_dir / 'config.development.yaml', 'w') as f:
                yaml.dump(dev_config, f)

            yield config_dir
```

**💡 구현 포인트:**
- pytest fixture로 격리된 테스트 환경
- 실제와 유사한 설정 파일 구조 생성

### 6.2 핵심 테스트 케이스
```python
def test_environment_override(self, temp_config_dir):
    """환경별 설정 오버라이드 테스트"""
    loader = ConfigLoader(str(temp_config_dir))
    config = loader.load_config(Environment.DEVELOPMENT)

    # 기본값 유지 확인
    assert config.app_name == 'Test App'

    # 환경별 오버라이드 확인
    assert config.logging.level == 'DEBUG'
    assert config.database.connection_timeout == 10  # 개발 환경 값

def test_dependency_injection_lifecycle(self):
    """DI 컨테이너 생명주기 테스트"""
    container = DIContainer()

    # 싱글톤 등록
    container.register_singleton(ITestService, TestService)

    # 동일 인스턴스 반환 확인
    service1 = container.resolve(ITestService)
    service2 = container.resolve(ITestService)
    assert service1 is service2  # 싱글톤 검증
```

**💡 구현 포인트:**
- 실제 사용 시나리오 기반 테스트
- 예상 동작과 실제 동작 비교 검증

## 📚 참고 패턴 및 Best Practices

### 설정 관리 패턴
1. **계층적 설정**: base + environment override
2. **타입 안전성**: dataclass + 런타임 검증
3. **환경변수 지원**: `__post_init__()` 활용
4. **기본값 전략**: 안전한 기본값 설정

### DI 컨테이너 패턴
1. **생명주기 관리**: Singleton/Transient/Scoped 명확한 구분
2. **자동 주입**: inspect 모듈 활용한 생성자 분석
3. **스레드 안전성**: RLock 사용한 동시성 보장
4. **에러 처리**: 명확한 예외 메시지

### 테스트 전략
1. **격리된 환경**: pytest fixture 활용
2. **실제 시나리오**: end-to-end 테스트 포함
3. **에러 케이스**: 예외 상황 모든 케이스 테스트
4. **수동 검증**: 단위 테스트 + 실제 동작 확인

---

**💡 핵심 원칙**: "복잡한 시스템도 작은 컴포넌트들의 조합으로 체계적으로 구현할 수 있다!"
