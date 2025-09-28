# 📋 의존성 주입 아키텍처 가이드

## 🎯 개요

본 문서는 업비트 자동매매 시스템에서 구축한 의존성 주입(Dependency Injection, DI) 아키텍처에 대한 종합적인 가이드입니다. Clean Architecture와 DDD 원칙을 준수하며, dependency-injector 라이브러리를 활용한 체계적인 의존성 관리 방법을 제시합니다.

---

## 1. 의존성 주입이란 무엇인가? 📚

### 1.1 비개발자를 위한 간단한 설명

의존성 주입을 **"스마트 부품 상자"** 로 생각해보세요.

**🔧 기존 방식 (문제점)**:

- 자동차를 만들 때, 핸들 제작자가 직접 바퀴 공장에 가서 바퀴를 만들어와야 함
- 네비게이션 제작자가 직접 지도 회사와 GPS 위성에 연결해야 함
- **문제**: 모든 부품이 다른 부품 만드는 방법까지 알아야 해서 복잡함

**✨ 의존성 주입 방식**:

- 스마트 부품 상자가 모든 부품을 만들고 관리하는 방법을 알고 있음
- 핸들 제작자는 "바퀴가 필요해!"라고 요청만 하면 됨
- 부품 상자가 알아서 최신형 바퀴를 가져다줌
- **장점**: 각 제작자는 자신의 전문 분야에만 집중 가능

### 1.2 기술적 개요

의존성 주입은 **객체가 필요로 하는 다른 객체(의존성)를 직접 생성하지 않고, 외부에서 전달받는 설계 패턴**입니다.

**핵심 원칙**:

- **제어의 역전 (IoC)**: 객체 생성과 관리를 외부 컨테이너에 위임
- **느슨한 결합 (Loose Coupling)**: 구체적인 구현 대신 인터페이스에 의존
- **단일 책임 원칙**: 각 클래스는 자신의 핵심 기능에만 집중

---

## 2. 의존성 주입 방법과 비교 🔄

### 2.1 생성자 주입 (Constructor Injection) ✅ **권장**

```python
class TradingService:
    def __init__(self, api_client: IUpbitClient, repository: IStrategyRepository):
        self._api_client = api_client
        self._repository = repository
```

**장점**:

- 필수 의존성 보장, 객체 불변성 유지
- 명시적 의존성 관계 표현

**단점**:

- 의존성이 많을 때 생성자가 길어질 수 있음

### 2.2 세터 주입 (Setter Injection) ⚠️ **지양**

```python
class TradingService:
    def set_api_client(self, client: IUpbitClient):
        self._api_client = client
```

**문제점**:

- 객체 불완전 상태 발생 가능
- 의존성 누락 위험성

### 2.3 서비스 로케이터 패턴 ❌ **비권장**

```python
# 안티패턴 예시
client = ServiceLocator.get_service(IUpbitClient)
```

**문제점**:

- 숨겨진 의존성으로 가독성 저하
- 테스트 어려움

### 2.4 DI 컨테이너 🏆 **채택**

```python
from dependency_injector.wiring import inject, Provide

class TradingService:
    @inject
    def __init__(
        self,
        api_client: IUpbitClient = Provide["upbit_client"],
        repository: IStrategyRepository = Provide["strategy_repository"]
    ):
        self._api_client = api_client
        self._repository = repository
```

**선택 이유**:

- 자동 의존성 해결
- 테스트용 Mock 교체 용이
- 설정 파일 기반 구성 관리

---

## 3. 우리의 DI 아키텍처 구축 개요 🏗️

### 3.1 핵심 구성 요소

#### ApplicationContainer

- 📁 `upbit_auto_trading/infrastructure/dependency_injection/container.py`
- dependency-injector 기반 DeclarativeContainer
- 모든 서비스 Provider 등록 및 관리

#### ApplicationContext

- 📁 `upbit_auto_trading/infrastructure/dependency_injection/app_context.py`
- Container 생명주기 관리
- Wiring 설정 및 초기화

#### 설정 파일

- 📁 `config/config.yaml`
- 환경별 설정 분리
- Configuration Provider를 통한 주입

### 3.2 아키텍처 계층별 적용

```
┌─────────────────┐    ┌──────────────────┐
│   Presentation  │◄───┤ @inject 데코레이터  │
│     Layer       │    └──────────────────┘
└─────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐
│   Application   │◄───┤   Use Case       │
│     Layer       │    │   Services       │
└─────────────────┘    └──────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐
│     Domain      │◄───┤ Repository       │
│     Layer       │    │ Interfaces       │
└─────────────────┘    └──────────────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐
│ Infrastructure  │◄───┤ Provider 등록    │
│     Layer       │    │ (Container.py)   │
└─────────────────┘    └──────────────────┘
```

### 3.3 주요 Provider 등록 현황

- **Infrastructure**: DatabaseManager, PathService, LoggingService
- **Domain**: StrategyRepository, TriggerRepository, DomainEventPublisher
- **Application**: TriggerApplicationService, ChartDataService
- **Presentation**: ThemeService, StyleManager, NavigationBar

---

## 4. 의존성 주입이 필요한 상황과 구분 가이드 🎯

### 4.1 DI 적용 필수 대상 ✅

#### 서비스 계층 (Services)

```python
# 📁 upbit_auto_trading/application/services/
class StrategyApplicationService:
    @inject
    def __init__(
        self,
        strategy_repo: IStrategyRepository = Provide["strategy_repository"],
        trigger_repo: ITriggerRepository = Provide["trigger_repository"]
    ):
```

**이유**: 여러 의존성 조합하여 비즈니스 로직 수행

#### 리포지토리 (Repositories)

```python
# 📁 upbit_auto_trading/infrastructure/repositories/
class SqliteStrategyRepository:
    @inject
    def __init__(
        self,
        db_manager: DatabaseManager = Provide["database_manager"]
    ):
```

**이유**: 데이터 영속성, 외부 리소스 의존

#### 외부 API 클라이언트

```python
# 📁 upbit_auto_trading/infrastructure/external_apis/
class UpbitPrivateClient:
    @inject
    def __init__(
        self,
        api_key_service: IApiKeyService = Provide["api_key_service"],
        rate_limiter: IRateLimiter = Provide["rate_limiter"]
    ):
```

**이유**: API 키, 제한기 등 설정 의존성

### 4.2 DI 적용 불필요 대상 ❌

#### 데이터 전송 객체 (DTOs)

```python
# 📁 upbit_auto_trading/application/dto/
@dataclass
class StrategyCreateDto:
    name: str
    rules: List[TriggerRule]
```

**이유**: 단순 데이터 구조체, 의존성 없음

#### 도메인 엔티티 및 값 객체

```python
# 📁 upbit_auto_trading/domain/entities/
class Strategy:
    def __init__(self, name: str, rules: List[TriggerRule]):
        self._name = name
        self._rules = rules
```

**이유**: 도메인 핵심 개념, 서비스에 의해 생성됨

#### 유틸리티 클래스

```python
# 📁 upbit_auto_trading/infrastructure/utilities/
class TimeUtils:
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
```

**이유**: 상태 없는 정적 메서드

### 4.3 판별 기준

| 기준 | DI 필요 | DI 불필요 |
|------|---------|-----------|
| **외부 리소스 사용** | DB, API, 파일 시스템 | 메모리 내 연산만 |
| **다른 계층 객체 호출** | Service → Repository | 동일 계층 내 호출 |
| **테스트 격리 필요성** | Mock/Stub 교체 필요 | 직접 테스트 가능 |
| **구현 교체 가능성** | SQLite ↔ PostgreSQL | 고정된 알고리즘 |
| **설정 의존성** | API 키, DB 경로 등 | 하드코딩된 상수 |

---

## 5. DI 작업 체크포인트와 체크리스트 ✅

### 5.1 설계 단계 체크포인트

#### Phase 1: 의존성 식별

- [ ] **외부 리소스 의존성 파악**: DB, API, 파일 시스템
- [ ] **서비스 간 의존성 매핑**: 호출 관계 다이어그램 작성
- [ ] **인터페이스 정의**: 추상화 계층 설계
- [ ] **생명주기 결정**: Singleton vs Factory 패턴 선택

#### Phase 2: Container 설계

- [ ] **Provider 등록 순서**: Infrastructure → Domain → Application → Presentation
- [ ] **순환 의존성 검증**: 의존성 그래프 무방향성 확인
- [ ] **Configuration 분리**: 환경별 설정 외부화
- [ ] **Wiring 모듈 정의**: @inject 적용 대상 명시

### 5.2 구현 단계 체크리스트

#### 생성자 주입 패턴 적용

```python
# ✅ 올바른 패턴
class MyService:
    @inject
    def __init__(
        self,
        dependency: IDependency = Provide["dependency_provider"]
    ):
        self._dependency = dependency

# ❌ 잘못된 패턴
class MyService:
    def __init__(self):
        self._dependency = ConcreteDependency()  # 직접 생성
```

- [ ] **@inject 데코레이터 추가**
- [ ] **Provide 문법 정확성**: `Provide["provider_name"]`
- [ ] **타입 힌트 명시**: 인터페이스 기반 의존성
- [ ] **생성자 파라미터 순서**: 의존성 → 일반 파라미터

#### Container 등록 검증

```python
# ApplicationContainer 내부
dependency_provider = providers.Factory(
    ConcreteDependency,
    config_param=config.dependency.param
)
```

- [ ] **Provider 타입 선택**: Factory vs Singleton
- [ ] **의존성 체인 구성**: 하위 의존성 주입
- [ ] **Configuration 연결**: config.yaml 매핑
- [ ] **Wiring 모듈 등록**: container.wire(modules=[...])

### 5.3 테스트 단계 검증

#### 단위 테스트 작성

```python
def test_my_service():
    # Arrange
    mock_dependency = Mock(spec=IDependency)
    container = ApplicationContainer()
    container.dependency_provider.override(mock_dependency)

    # Act
    service = container.my_service()
    result = service.execute()

    # Assert
    mock_dependency.some_method.assert_called_once()
    container.reset_override()
```

- [ ] **Mock 객체 주입**: Provider overriding 활용
- [ ] **격리된 테스트**: 외부 의존성 제거
- [ ] **Override 정리**: 테스트 종료 후 reset
- [ ] **Integration 테스트**: 실제 Container 동작 검증

### 5.4 배포 단계 체크리스트

- [ ] **설정 파일 분리**: dev/staging/production
- [ ] **환경 변수 매핑**: API 키, DB 연결 정보
- [ ] **Container 초기화 검증**: 모든 Provider 해결 가능
- [ ] **성능 영향 측정**: DI 오버헤드 최소화
- [ ] **로깅 및 모니터링**: Container 상태 추적

---

## 6. 의존성 주입 패턴 가이드 📋

### 6.1 표준 패턴 템플릿

#### Service Layer 패턴

```python
from dependency_injector.wiring import inject, Provide
from typing import Protocol

class IRepository(Protocol):
    def save(self, entity: Entity) -> None: ...
    def find_by_id(self, id: str) -> Entity: ...

class ApplicationService:
    @inject
    def __init__(
        self,
        repository: IRepository = Provide["repository"],
        event_publisher: IEventPublisher = Provide["event_publisher"]
    ):
        self._repository = repository
        self._event_publisher = event_publisher

    def execute_use_case(self, command: Command) -> Result:
        # 1. 도메인 로직 수행
        entity = self._repository.find_by_id(command.entity_id)
        entity.execute_business_logic(command.data)

        # 2. 변경사항 저장
        self._repository.save(entity)

        # 3. 이벤트 발행
        event = DomainEvent(entity.id, entity.get_changes())
        self._event_publisher.publish(event)

        return Result(success=True)
```

#### Repository Layer 패턴

```python
class SqliteRepository:
    @inject
    def __init__(
        self,
        db_manager: DatabaseManager = Provide["database_manager"],
        logger: Logger = Provide["logger"]
    ):
        self._db = db_manager
        self._logger = logger

    def save(self, entity: Entity) -> None:
        try:
            with self._db.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO entities (id, data) VALUES (?, ?)",
                    (entity.id, entity.serialize())
                )
            self._logger.info(f"Entity {entity.id} saved successfully")
        except Exception as e:
            self._logger.error(f"Failed to save entity: {e}")
            raise
```

#### UI Layer 패턴

```python
class MainWindow(QMainWindow):
    @inject
    def __init__(
        self,
        trading_service: ITradingService = Provide["trading_service"],
        theme_service: IThemeService = Provide["theme_service"],
        parent=None
    ):
        super().__init__(parent)
        self._trading_service = trading_service
        self._theme_service = theme_service
        self._setup_ui()

    def _on_trade_button_clicked(self):
        try:
            result = self._trading_service.execute_trade(self._get_trade_params())
            self._show_result(result)
        except Exception as e:
            self._show_error(str(e))
```

### 6.2 Container 구성 패턴

#### 계층별 Provider 구성

```python
class ApplicationContainer(containers.DeclarativeContainer):
    # Configuration
    config = providers.Configuration()

    # Infrastructure Layer
    logger = providers.Singleton(
        create_component_logger,
        name="App"
    )

    database_manager = providers.Singleton(
        DatabaseConnectionService
    )

    # Domain Layer
    strategy_repository = providers.Factory(
        SqliteStrategyRepository,
        db_manager=database_manager,
        logger=logger
    )

    event_publisher = providers.Singleton(
        DomainEventPublisher,
        logger=logger
    )

    # Application Layer
    trading_service = providers.Factory(
        TradingApplicationService,
        strategy_repository=strategy_repository,
        event_publisher=event_publisher
    )

    # Presentation Layer
    main_window = providers.Factory(
        MainWindow,
        trading_service=trading_service
    )
```

#### Configuration 매핑 패턴

```python
# config/config.yaml
database:
  strategy_db_path: "data/strategies.sqlite3"
  market_data_db_path: "data/market_data.sqlite3"

api:
  upbit:
    base_url: "https://api.upbit.com"
    timeout: 30

logging:
  level: "INFO"
  console_enabled: true

# Container에서 사용
database_manager = providers.Singleton(
    DatabaseManager,
    strategy_db_path=config.database.strategy_db_path,
    market_data_db_path=config.database.market_data_db_path
)

upbit_client = providers.Factory(
    UpbitApiClient,
    base_url=config.api.upbit.base_url,
    timeout=config.api.upbit.timeout
)
```

### 6.3 테스트 패턴

#### Provider Override 패턴

```python
class TestTradingService:
    def setup_method(self):
        self.container = ApplicationContainer()
        self.mock_repository = Mock(spec=IStrategyRepository)
        self.mock_event_publisher = Mock(spec=IEventPublisher)

        # Mock 주입
        self.container.strategy_repository.override(self.mock_repository)
        self.container.event_publisher.override(self.mock_event_publisher)

    def teardown_method(self):
        self.container.reset_override()

    def test_execute_trade_success(self):
        # Given
        self.mock_repository.find_by_id.return_value = Strategy("test")
        service = self.container.trading_service()

        # When
        result = service.execute_trade(TradeCommand("buy", 100))

        # Then
        assert result.success is True
        self.mock_repository.save.assert_called_once()
        self.mock_event_publisher.publish.assert_called_once()
```

---

## 7. 전문가 마무리 조언 🎓

### 7.1 성공적인 DI 도입을 위한 핵심 원칙

#### "점진적 적용" 전략

- 새로운 기능부터 DI 패턴 적용 시작
- 기존 코드는 리팩토링 기회에 점진적 전환
- 한 번에 모든 것을 바꾸려 하지 말 것

#### "인터페이스 우선" 사고

- 구체적 구현보다 추상화에 의존
- Protocol이나 ABC를 활용한 계약 정의
- 테스트 가능성을 항상 고려

#### "설정 외부화" 습관

- 하드코딩된 값을 config.yaml로 분리
- 환경별 설정 파일 관리
- 민감한 정보는 환경 변수 활용

### 7.2 주요 안티패턴 회피

#### Service Locator 남용 금지

```python
# ❌ 안티패턴
def some_method(self):
    client = ServiceLocator.get("upbit_client")  # 의존성 숨김

# ✅ 올바른 패턴
@inject
def __init__(self, client: IUpbitClient = Provide["upbit_client"]):
    self._client = client
```

#### 순환 의존성 예방

- 계층 간 명확한 의존성 방향 유지
- Domain → Infrastructure 의존 금지
- 필요시 이벤트 기반 느슨한 결합 활용

#### 과도한 추상화 지양

- 실제 필요에 의한 인터페이스 도출
- YAGNI(You Aren't Gonna Need It) 원칙 준수

### 7.3 장기적 유지보수 관점

#### 의존성 그래프 관리

- 주기적 의존성 다이어그램 리뷰
- 복잡성 지표 모니터링
- 리팩토링 우선순위 결정

#### 팀 내 컨벤션 확립

- DI 패턴 코드 리뷰 체크리스트
- 신규 개발자 온보딩 가이드
- 지속적인 아키텍처 개선 문화

#### 성능 최적화

- Container 초기화 시간 모니터링
- 지연 로딩 vs 즉시 로딩 전략
- 메모리 사용량 프로파일링

---

## 🎯 결론

의존성 주입은 단순한 기술적 패턴이 아닌, **지속 가능한 소프트웨어 아키텍처의 핵심**입니다.

**업비트 자동매매 시스템**에서 구축한 DI 아키텍처는:

- ✅ Clean Architecture 원칙 준수
- ✅ 테스트 가능성 극대화
- ✅ 유연한 구성 관리
- ✅ 개발 생산성 향상

지속적인 학습과 개선을 통해 더욱 견고한 시스템으로 발전시켜 나가길 바랍니다.

---

**📚 참고 자료**:

- [dependency-injector 공식 문서](https://python-dependency-injector.ets-labs.org/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design 패턴](https://martinfowler.com/tags/domain%20driven%20design.html)

**📁 관련 파일**:

- `upbit_auto_trading/infrastructure/dependency_injection/container.py`
- `upbit_auto_trading/infrastructure/dependency_injection/app_context.py`
- `config/config.yaml`
- `tasks/active/TASK_20250928_01-clean_di_architecture_rebuild.md`
