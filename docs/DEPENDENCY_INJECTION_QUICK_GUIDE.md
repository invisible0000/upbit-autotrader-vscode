# 🚀 의존성 주입 실용 가이드

## 📋 빠른 판단 체크리스트

### ✅ DI 필요 (즉시 적용)

- [ ] 외부 리소스 사용 (DB, API, 파일)
- [ ] 다른 서비스/리포지토리 호출
- [ ] 설정값 의존성 (API 키, DB 경로)
- [ ] 테스트시 Mock 교체 필요

### ❌ DI 불필요 (직접 생성)

- [ ] DTO/Entity 클래스
- [ ] 유틸리티 정적 메서드
- [ ] 상수/열거형
- [ ] 단순 계산 로직

---

## 🔧 3단계 DI 적용 패턴

### 1단계: @inject 패턴 적용

```python
from dependency_injector.wiring import inject, Provide

class MyService:
    @inject
    def __init__(
        self,
        dependency: IDependency = Provide["dependency_provider"]
    ):
        self._dependency = dependency
```

### 2단계: Container 등록

```python
# container.py
dependency_provider = providers.Factory(
    ConcreteDependency,
    config_param=config.some.param
)
```

### 3단계: Wiring 활성화

```python
# container.py의 wire_container_modules()
wiring_modules = [
    "your.module.path",  # 추가
]
```

---

## 📊 계층별 적용 가이드

### Application Layer ✅ **필수**

```python
class TradingService:
    @inject
    def __init__(
        self,
        repository: IRepository = Provide["repository"],
        event_bus: IEventBus = Provide["event_bus"]
    ):
```

**패턴**: Factory Provider + 의존성 체인

### Infrastructure Layer ✅ **필수**

```python
class ApiClient:
    @inject
    def __init__(
        self,
        config: ApiConfig = Provide["api_config"],
        logger: Logger = Provide["logger"]
    ):
```

**패턴**: Singleton Provider + Configuration

### Domain Layer ⚠️ **선택적**

```python
# Repository 인터페이스만 의존
class DomainService:
    def __init__(self, repository: IRepository):
        # 순수 생성자 주입
```

**패턴**: 인터페이스 의존, 구현체 외부 주입

### Presentation Layer ✅ **권장**

```python
class MainWindow:
    @inject
    def __init__(
        self,
        service: IService = Provide["service"],
        theme: ITheme = Provide["theme"]
    ):
```

**패턴**: UI별 Factory Provider

---

## 🎯 Provider 선택 기준

| 조건 | Provider | 예시 |
|------|----------|------|
| **설정/리소스** | `Singleton` | DatabaseManager, Logger |
| **비즈니스 로직** | `Factory` | Services, Handlers |
| **UI 컴포넌트** | `Factory` | Windows, Dialogs |
| **설정값** | `Configuration` | API Keys, Paths |

---

## ⚡ 즉시 적용 템플릿

### Service 템플릿

```python
from dependency_injector.wiring import inject, Provide

class {{ServiceName}}:
    @inject
    def __init__(
        self,
        repository: I{{Entity}}Repository = Provide["{{entity}}_repository"],
        logger: Logger = Provide["logger"]
    ):
        self._repository = repository
        self._logger = logger

    def execute(self, command: Command) -> Result:
        try:
            # 비즈니스 로직
            entity = self._repository.find_by_id(command.id)
            entity.process(command.data)
            self._repository.save(entity)

            return Result(success=True)
        except Exception as e:
            self._logger.error(f"Execute failed: {e}")
            raise
```

### Repository 템플릿

```python
class Sqlite{{Entity}}Repository:
    @inject
    def __init__(
        self,
        db_manager: DatabaseManager = Provide["database_manager"]
    ):
        self._db = db_manager

    def find_by_id(self, entity_id: str) -> {{Entity}}:
        # SQLite 구현
        pass

    def save(self, entity: {{Entity}}) -> None:
        # SQLite 구현
        pass
```

### Container 등록 템플릿

```python
# ApplicationContainer 내부
{{entity}}_repository = providers.Factory(
    Sqlite{{Entity}}Repository,
    db_manager=database_manager
)

{{service_name}} = providers.Factory(
    {{ServiceName}},
    repository={{entity}}_repository,
    logger=logging_service
)
```

---

## 🔍 문제 해결 가이드

### "Provider not found" 오류

1. Container에 Provider 등록 확인
2. Wiring 모듈에 클래스 포함 확인
3. @inject 데코레이터 적용 확인

### "Circular dependency" 오류

1. 의존성 방향 검토 (Domain ← Infrastructure 금지)
2. Event 기반 느슨한 결합 적용
3. Lazy Provider 사용 고려

### 테스트 실패

```python
# Mock 주입 패턴
def test_service():
    container = ApplicationContainer()
    mock_repo = Mock(spec=IRepository)

    container.repository.override(mock_repo)
    service = container.service()

    # 테스트 실행
    result = service.execute(command)

    container.reset_override()  # 정리 필수
```

---

## ⚠️ 피해야 할 안티패턴

### ❌ Service Locator

```python
# 나쁨
def method(self):
    client = ServiceLocator.get("api_client")
```

### ❌ 직접 생성

```python
# 나쁨
def __init__(self):
    self.client = UpbitClient()  # 하드코딩
```

### ❌ 순환 의존성

```python
# 나쁨
class A:
    def __init__(self, b: B): pass

class B:
    def __init__(self, a: A): pass  # 순환!
```

---

## 🎯 성공 기준

### 코드 품질 지표

- [ ] **외부 의존성 제거**: new 키워드 최소화
- [ ] **테스트 커버리지**: Mock 주입으로 단위테스트
- [ ] **설정 외부화**: 하드코딩 값 config.yaml 분리
- [ ] **인터페이스 기반**: 구체적 구현 대신 추상화 의존

### 실행 검증

```python
# 정상 작동 확인
python run_desktop_ui.py
# → ERROR 없이 실행
# → "DI Container wiring 완료: N개 모듈" 로그 확인
```

---

## 📚 참고 링크

- **상세 가이드**: `docs/DEPENDENCY_INJECTION_ARCHITECTURE.md`
- **Container 구현**: `upbit_auto_trading/infrastructure/dependency_injection/`
- **태스크 기록**: `tasks/active/TASK_20250928_01-clean_di_architecture_rebuild.md`

---

**🏆 핵심 원칙**: "필요한 것은 요청하고, 제공할 것은 등록하라"
