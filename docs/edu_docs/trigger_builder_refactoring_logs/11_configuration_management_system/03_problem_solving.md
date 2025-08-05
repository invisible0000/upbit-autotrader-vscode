# 🔧 Configuration Management System 문제해결 가이드

> **대상**: Configuration Management System 구현 중 발생하는 문제 해결
> **목적**: 실제 겪은 문제들과 해결 방법을 체계적으로 정리
> **활용**: 유사한 문제 발생 시 빠른 해결책 제공

## 📋 문제 분류

### 1. 환경 및 설정 문제 🌍
### 2. 코딩 및 구현 문제 💻
### 3. 테스트 및 검증 문제 🧪
### 4. 아키텍처 및 설계 문제 🏗️

---

## 🌍 환경 및 설정 문제

### Problem 1: Windows PowerShell Unicode 인코딩 오류

**증상:**
```
UnicodeEncodeError: 'cp949' codec can't encode character '\u2713' in position 47: illegal multibyte sequence
```

**발생 상황:**
- pytest 실행 시 한글이나 특수문자 출력
- Windows 환경에서 기본 인코딩이 cp949
- 테스트 결과 출력에 ✅, ❌ 같은 유니코드 문자 포함

**해결 방법:**
```powershell
# 1. 환경변수 설정 (세션별)
$env:PYTHONIOENCODING = 'utf-8'
pytest tests/infrastructure/config/ -v

# 2. 시스템 전역 설정 (영구적)
[System.Environment]::SetEnvironmentVariable("PYTHONIOENCODING", "utf-8", "User")

# 3. 테스트 실행 스크립트 생성
# run_tests.ps1
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONLEGACYWINDOWSSTDIO = 'utf-8'
pytest tests/infrastructure/config/ -v --tb=short
```

**예방 방법:**
- 프로젝트에 run_tests.ps1 스크립트 포함
- README에 Windows 환경 설정 가이드 작성
- CI/CD 파이프라인에서 인코딩 설정 표준화

**교훈:**
Windows 환경에서는 UTF-8 인코딩을 명시적으로 설정해야 함

---

### Problem 2: 설정 파일과 데이터클래스 필드 불일치

**증상:**
```python
KeyError: 'websocket_url'
TypeError: __init__() got an unexpected keyword argument 'websocket_url'
```

**발생 상황:**
- 기존 config.yaml에는 있지만 새로운 dataclass에는 없는 필드
- 또는 그 반대 상황
- 설정 로딩 시 dataclass 생성 실패

**문제 분석:**
```python
# 기존 config.yaml
upbit_api:
  base_url: "https://api.upbit.com"
  websocket_url: "wss://api.upbit.com/websocket/v1"  # 이 필드가 없음

# 새로운 UpbitApiConfig
@dataclass
class UpbitApiConfig:
    base_url: str = "https://api.upbit.com"
    # websocket_url 필드가 누락됨
```

**해결 방법:**
```python
# 1. 누락된 필드 추가 (권장)
@dataclass
class UpbitApiConfig:
    base_url: str = "https://api.upbit.com"
    websocket_url: str = "wss://api.upbit.com/websocket/v1"  # 추가
    timeout_seconds: int = 10

# 2. 기본값으로 호환성 확보
@dataclass
class TradingConfig:
    max_position_size_krw: int = 1000000
    default_fee: float = 0.0005  # 기존 config에 없어도 기본값으로 처리
    default_slippage: float = 0.001

# 3. 필드 매핑 함수 활용
def create_config_from_dict(cls, config_dict: Dict[str, Any]):
    """딕셔너리에서 dataclass 생성 (필드 매핑 포함)"""
    valid_fields = {f.name for f in fields(cls)}
    filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
    return cls(**filtered_dict)
```

**예방 방법:**
- 기존 설정 파일 분석 후 dataclass 설계
- 마이그레이션 계획 수립
- 필드 매핑 유틸리티 함수 작성

**교훈:**
기존 시스템과의 호환성을 우선적으로 고려해야 함

---

## 💻 코딩 및 구현 문제

### Problem 3: DI 컨테이너 순환 의존성 문제

**증상:**
```python
RecursionError: maximum recursion depth exceeded
DependencyResolutionError: 순환 의존성 감지: ServiceA -> ServiceB -> ServiceA
```

**발생 상황:**
```python
class ServiceA:
    def __init__(self, service_b: ServiceB):
        self.service_b = service_b

class ServiceB:
    def __init__(self, service_a: ServiceA):  # 순환 참조!
        self.service_a = service_a
```

**해결 방법:**
```python
# 1. 순환 의존성 감지 로직 구현
class DIContainer:
    def __init__(self):
        self._resolving_stack: Set[Type] = set()

    def resolve(self, service_type: Type) -> Any:
        if service_type in self._resolving_stack:
            cycle = " -> ".join([t.__name__ for t in self._resolving_stack])
            raise DependencyResolutionError(f"순환 의존성 감지: {cycle} -> {service_type.__name__}")

        self._resolving_stack.add(service_type)
        try:
            return self._create_instance(service_type)
        finally:
            self._resolving_stack.remove(service_type)

# 2. 설계 개선으로 순환 의존성 제거
class ServiceA:
    def __init__(self, event_bus: IEventBus):  # 중간 계층 활용
        self.event_bus = event_bus

class ServiceB:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus

# 3. Factory 패턴 활용
class ServiceFactory:
    def create_service_a(self, service_b: ServiceB) -> ServiceA:
        return ServiceA(service_b)
```

**예방 방법:**
- 의존성 그래프 설계 시 순환 검증
- 인터페이스를 통한 의존성 역전
- Event Bus나 Mediator 패턴 활용

**교훈:**
DI 컨테이너는 반드시 순환 의존성 감지 기능이 필요함

---

### Problem 4: threading.Lock vs threading.RLock 선택 문제

**증상:**
```python
RuntimeError: cannot release un-acquired lock
DeadlockError: 같은 스레드에서 락 재진입 시도
```

**발생 상황:**
```python
class DIContainer:
    def __init__(self):
        self._lock = threading.Lock()  # 문제가 되는 부분

    def resolve(self, service_type: Type):
        with self._lock:
            # ... 의존성 해결 중 ...
            dependency = self.resolve(other_type)  # 재진입 시도!
```

**해결 방법:**
```python
# 1. RLock 사용 (권장)
class DIContainer:
    def __init__(self):
        self._lock = threading.RLock()  # 재진입 가능한 락

    def resolve(self, service_type: Type):
        with self._lock:
            # 같은 스레드에서 재진입 가능
            dependency = self.resolve(other_type)  # OK!

# 2. 락 범위 최소화
class DIContainer:
    def resolve(self, service_type: Type):
        registration = self._get_registration(service_type)  # 락 범위 분리
        return self._create_instance(registration)

    def _get_registration(self, service_type: Type):
        with self._lock:
            return self._services.get(service_type)
```

**비교표:**
| 구분 | Lock | RLock |
|------|------|-------|
| 재진입 | 불가능 | 가능 |
| 성능 | 빠름 | 약간 느림 |
| 사용 상황 | 단순한 동기화 | 복잡한 호출 체인 |

**예방 방법:**
- 복잡한 호출 체인이 예상되면 RLock 사용
- 락 범위를 최소한으로 유지
- 락 사용 패턴을 문서화

**교훈:**
DI 컨테이너처럼 재귀적 호출이 발생하는 곳은 RLock 필수

---

## 🧪 테스트 및 검증 문제

### Problem 5: pytest fixture 스코프 문제

**증상:**
```python
ScopeMismatchError: fixture 'temp_config_dir' has scope 'function'
but depends on fixture 'session_config' with scope 'session'
```

**발생 상황:**
```python
@pytest.fixture(scope="session")
def session_config():
    return {"global": "value"}

@pytest.fixture(scope="function")
def temp_config_dir(session_config):  # 스코프 불일치!
    # ...
```

**해결 방법:**
```python
# 1. 스코프 통일
@pytest.fixture(scope="function")
def session_config():  # function 스코프로 변경
    return {"global": "value"}

@pytest.fixture(scope="function")
def temp_config_dir(session_config):
    # ...

# 2. 의존성 제거
@pytest.fixture(scope="function")
def temp_config_dir():
    # session_config 의존성 제거하고 독립적으로 구성
    config = {"global": "value"}  # 직접 정의
    # ...

# 3. 파라미터화 활용
@pytest.mark.parametrize("config_type", ["development", "testing", "production"])
def test_environment_configs(config_type, temp_config_dir):
    # 파라미터화로 여러 환경 테스트
```

**pytest fixture 스코프 가이드:**
- `function`: 각 테스트 함수마다 새로 생성
- `class`: 테스트 클래스마다 새로 생성
- `module`: 모듈마다 새로 생성
- `session`: 전체 테스트 세션에서 한 번만 생성

**예방 방법:**
- fixture 의존성 그래프 설계 시 스코프 고려
- 독립적인 fixture 설계 우선
- 복잡한 의존성보다는 파라미터화 활용

**교훈:**
fixture 스코프는 생명주기와 직결되므로 신중하게 설계해야 함

---

### Problem 6: 테스트 격리 문제

**증상:**
```python
AssertionError: Expected 1 but got 2
# 이전 테스트의 상태가 다음 테스트에 영향
```

**발생 상황:**
```python
# 전역 변수 사용으로 인한 격리 실패
_global_context = None

def test_context_creation():
    context = ApplicationContext()
    set_application_context(context)
    assert get_application_context() is not None

def test_context_reset():
    # 이전 테스트의 context가 남아있음!
    assert get_application_context() is None  # 실패!
```

**해결 방법:**
```python
# 1. teardown 메서드 활용
class TestApplicationContext:
    def teardown_method(self):
        """각 테스트 후 정리"""
        reset_application_context()

# 2. pytest fixture로 자동 정리
@pytest.fixture(autouse=True)
def reset_global_state():
    """모든 테스트에 자동 적용되는 정리 fixture"""
    yield  # 테스트 실행
    reset_application_context()  # 테스트 후 정리

# 3. 컨텍스트 매니저 활용
def test_context_with_manager():
    with ApplicationContext("testing") as context:
        # with 블록 내에서만 유효
        assert context.config is not None
    # 블록 종료 시 자동 정리

# 4. Mock 활용으로 전역 상태 회피
@patch('module.get_application_context')
def test_with_mock(mock_get_context):
    mock_get_context.return_value = mock_context
    # 전역 상태 변경 없이 테스트
```

**테스트 격리 체크리스트:**
- [ ] 전역 변수나 싱글톤 상태 초기화
- [ ] 임시 파일이나 디렉토리 정리
- [ ] 데이터베이스 트랜잭션 롤백
- [ ] 환경변수 복원
- [ ] Mock 객체 reset

**예방 방법:**
- autouse fixture로 자동 정리
- 컨텍스트 매니저 패턴 활용
- Mock을 통한 의존성 격리
- 전역 상태 최소화

**교훈:**
테스트 격리는 자동화하고, 수동 정리에 의존하지 말 것

---

## 🏗️ 아키텍처 및 설계 문제

### Problem 7: 설정 병합 우선순위 혼란

**증상:**
```python
# 예상: development 환경에서는 DEBUG 로그
# 실제: INFO 로그 출력됨
AssertionError: Expected 'DEBUG' but got 'INFO'
```

**발생 상황:**
```python
# 잘못된 병합 순서
def load_config(self, environment):
    base_config = self._load_base_config()
    env_config = self._load_environment_config(environment)
    defaults = DEFAULT_CONFIGS.get(environment, {})

    # 잘못된 순서: 기본값이 환경설정을 덮어씀
    merged = self._merge_configs(env_config, base_config, defaults)
```

**해결 방법:**
```python
# 1. 명확한 우선순위 정의
PRIORITY_ORDER = [
    "환경별 설정 파일",    # 최고 우선순위
    "기본 설정 파일",      # 중간 우선순위
    "환경별 기본값",       # 최저 우선순위
]

def load_config(self, environment):
    # 올바른 순서: 낮은 우선순위부터 높은 우선순위 순으로 병합
    defaults = DEFAULT_CONFIGS.get(environment, {})      # 1. 기본값
    base_config = self._load_base_config()               # 2. 기본 설정
    env_config = self._load_environment_config(environment) # 3. 환경 설정

    merged = self._merge_configs(defaults, base_config, env_config)

# 2. 병합 로직 개선
def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
    """낮은 우선순위부터 높은 우선순위 순으로 병합"""
    result = {}
    for config in configs:  # 순서대로 덮어쓰기
        result = self._deep_merge(result, config)
    return result

# 3. 병합 과정 로깅으로 디버깅 지원
def _merge_configs_with_logging(self, *configs):
    result = {}
    for i, config in enumerate(configs):
        logger.debug(f"병합 단계 {i+1}: {config}")
        result = self._deep_merge(result, config)
        logger.debug(f"병합 결과: {result}")
    return result
```

**우선순위 설계 원칙:**
1. **구체적 > 일반적**: 환경별 설정 > 기본 설정
2. **사용자 정의 > 시스템 기본값**: 설정 파일 > DEFAULT_CONFIGS
3. **런타임 > 정적**: 환경변수 > 설정 파일

**예방 방법:**
- 우선순위를 명시적으로 문서화
- 테스트 케이스로 우선순위 검증
- 병합 과정을 로깅으로 추적 가능하게 구현

**교훈:**
설정 병합 순서는 시스템의 동작을 결정하는 핵심 요소

---

### Problem 8: 타입 힌트와 런타임 타입 불일치

**증상:**
```python
TypeError: expected str, got int
# 타입 힌트는 str인데 실제로는 int가 전달됨
```

**발생 상황:**
```python
@dataclass
class DatabaseConfig:
    connection_timeout: int = 30  # 타입 힌트는 int

# YAML에서 로드 시 문자열로 읽힘
config_dict = yaml.load("connection_timeout: '30'")  # str '30'
config = DatabaseConfig(**config_dict)  # 타입 불일치!
```

**해결 방법:**
```python
# 1. 타입 변환 로직 추가
@dataclass
class DatabaseConfig:
    connection_timeout: int = 30

    def __post_init__(self):
        # 타입 변환 처리
        if isinstance(self.connection_timeout, str):
            self.connection_timeout = int(self.connection_timeout)

# 2. 팩토리 메서드 활용
@dataclass
class DatabaseConfig:
    connection_timeout: int = 30

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseConfig':
        """딕셔너리에서 타입 안전하게 생성"""
        # 타입 변환 로직
        if 'connection_timeout' in data:
            data['connection_timeout'] = int(data['connection_timeout'])
        return cls(**data)

# 3. Pydantic 활용 (외부 라이브러리)
from pydantic import BaseModel

class DatabaseConfig(BaseModel):
    connection_timeout: int = 30
    # Pydantic이 자동으로 타입 변환 및 검증

# 4. 타입 검증 데코레이터
def type_checked(cls):
    """타입 검증 데코레이터"""
    original_init = cls.__init__

    def new_init(self, *args, **kwargs):
        # 타입 검증 로직
        for field_name, field_type in cls.__annotations__.items():
            if field_name in kwargs:
                value = kwargs[field_name]
                if not isinstance(value, field_type):
                    kwargs[field_name] = field_type(value)  # 타입 변환
        original_init(self, *args, **kwargs)

    cls.__init__ = new_init
    return cls
```

**타입 안전성 체크리스트:**
- [ ] YAML 로딩 시 타입 변환
- [ ] 환경변수 처리 시 타입 변환
- [ ] dataclass 생성 시 타입 검증
- [ ] 런타임 타입 체크 추가

**예방 방법:**
- 팩토리 메서드로 안전한 객체 생성
- 타입 변환 로직을 중앙집중화
- Pydantic 같은 검증 라이브러리 고려
- 단위 테스트에서 타입 불일치 케이스 포함

**교훈:**
외부 데이터 소스에서 오는 데이터는 항상 타입 검증/변환이 필요

---

## 🛠️ 문제해결 체크리스트

### 환경 문제 발생 시
1. [ ] 환경변수 설정 확인 (PYTHONIOENCODING 등)
2. [ ] 설정 파일 경로 및 권한 확인
3. [ ] Python 버전 및 의존성 버전 확인
4. [ ] 운영체제별 차이점 고려

### 코딩 문제 발생 시
1. [ ] 타입 힌트와 실제 타입 일치 확인
2. [ ] 순환 의존성 검사
3. [ ] 스레드 안전성 검토
4. [ ] 에러 메시지 명확성 확인

### 테스트 문제 발생 시
1. [ ] 테스트 격리 상태 점검
2. [ ] fixture 스코프 및 의존성 확인
3. [ ] Mock 객체 설정 검토
4. [ ] 테스트 데이터 일관성 검증

### 아키텍처 문제 발생 시
1. [ ] 설정 병합 우선순위 검토
2. [ ] 의존성 방향 확인 (Clean Architecture)
3. [ ] 인터페이스 분리 원칙 준수 확인
4. [ ] 생명주기 관리 로직 점검

## 🚨 일반적인 디버깅 전략

### 1. 로깅 활용
```python
import logging
logger = logging.getLogger(__name__)

def debug_config_loading():
    logger.debug("설정 로딩 시작")
    logger.debug(f"환경: {environment}")
    logger.debug(f"설정 파일 경로: {config_path}")
    logger.debug(f"로드된 설정: {config_dict}")
```

### 2. 단계별 검증
```python
def step_by_step_verification():
    # 1단계: 파일 존재 확인
    assert config_file.exists(), f"설정 파일 없음: {config_file}"

    # 2단계: YAML 파싱 확인
    with open(config_file) as f:
        config_dict = yaml.safe_load(f)
    assert config_dict is not None

    # 3단계: 객체 생성 확인
    config = ApplicationConfig.from_dict(config_dict)
    assert config is not None
```

### 3. 최소 재현 케이스 작성
```python
def minimal_reproduction():
    """문제의 최소 재현 케이스"""
    # 복잡한 시스템에서 문제가 발생하면
    # 최소한의 코드로 동일한 문제 재현
    container = DIContainer()
    container.register_singleton(IService, ServiceImpl)
    service = container.resolve(IService)  # 여기서 문제 발생?
```

---

**💡 핵심 원칙**: "문제가 발생하면 당황하지 말고 체계적으로 분석하라. 모든 문제는 반드시 원인이 있다!"

**🎯 빠른 해결을 위한 팁:**
1. **에러 메시지 정독** - 대부분의 힌트가 여기에 있음
2. **최소 재현** - 복잡한 문제를 단순하게 분해
3. **로그 활용** - 시스템 상태를 가시화
4. **테스트 작성** - 문제 해결 후 재발 방지
