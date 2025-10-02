# 📋 초기화 시퀀스 리팩터링 계획서

> **작성일**: 2025년 10월 2일
> **목적**: 기술 부채 관리 및 아키텍처 일관성 확보
> **범위**: `run_desktop_ui.py`부터 시작하는 전체 애플리케이션 초기화 흐름 정리

---

## 🎯 리팩터링 배경 및 목적

### 현재 상황

- 프로젝트 기틀이 잡힌 구현 초기 단계
- DDD 4계층 아키텍처 + QAsync + MVP 패턴 적용 중
- 의존성 주입(DI) 시스템이 도입되었으나 일관성 부족
- 초기화 순서와 책임 분리가 명확하지 않음

### 리팩터링 목적

1. **기술 부채 조기 관리**: 구조가 복잡해지기 전 정리
2. **초기화 시퀀스 명확화**: 서비스 시작 순서의 논리적 정당성 확보
3. **DI 패턴 일관성**: Singleton Provider를 통한 계층별 서비스 제공
4. **테스트 용이성**: Mock 주입이 가능한 구조로 개선
5. **유지보수성**: 신규 개발자도 이해 가능한 명확한 구조

---

## 🔍 핵심 아키텍처 원칙 재확인

### 1. 서비스 시작 우선순위 (대화 내용 핵심)

#### ✅ 논리적 의존성 체인

```
1. 경로 서비스 (PathService)
   ↓ "설정 파일이 어디 있는지 알려줌"

2. 설정 읽기 서비스 (ConfigLoader)
   ↓ "설정값을 메모리로 로드"

3. 로깅 서비스 (LoggingService)
   ↓ "경로와 설정을 바탕으로 로그 시스템 초기화"

4. DB 서비스 (DatabaseConnection)
   ↓ "경로 서비스가 알려준 위치에 DB 파일 생성/연결"

5. Infrastructure Layer 서비스들
   ↓ "외부 API, Repository 등 초기화"

6. Application Layer 서비스들
   ↓ "비즈니스 로직 서비스 초기화"

7. Presentation Layer (GUI)
   ↓ "모든 준비 완료 후 UI 표시"
```

#### 🔑 핵심 질문과 답변 정리

**Q1: 프로그램 시작 시 첫 번째 서비스는?**
> **A: 경로 서비스** (PathService)
>
> - 이유: 모든 파일(설정, DB, 로그)의 위치를 결정해야 다른 서비스가 동작 가능
> - 역할: "어디에(Where)?" 담당

**Q2: DB 파일 생성은 파일시스템 서비스 vs DB 서비스?**
> **A: DB 서비스의 책임**
>
> - 경로 서비스: "어디에?" (디렉터리 생성 포함)
> - DB 서비스: "무엇을? 어떻게?" (파일 생성, 스키마 초기화, 연결 관리)
> - 협력 구조: 경로 서비스 → DB 경로 제공 → DB 서비스 → 파일 생성/연결

**Q3: DDD 구조에서 qasync 사용 시 싱글톤 필요?**
> **A: 전통적 싱글톤 ❌, DI 컨테이너의 Singleton Provider ✅**
>
> - 전통적 싱글톤 문제점:
>   - 강한 결합 (Tight Coupling)
>   - 테스트 불가 (Mock 주입 어려움)
>   - 숨겨진 의존성 (명시적이지 않음)
> - DI Singleton Provider 장점:
>   - 명시적 의존성 (생성자 주입)
>   - 느슨한 결합 (인터페이스 의존)
>   - 테스트 용이 (Mock 쉽게 주입)
>   - 중앙 관리 (Container에서 생명주기 제어)

### 2. 각 레이어별 DI 전략

#### Infrastructure Layer

```python
# Singleton Provider 사용 (상태 공유, 생성 비용 높음)
providers.Singleton(
    DatabaseConnection,
    path_service=Provide[PathService]
)
providers.Singleton(
    UpbitApiClient,
    config=Provide[ConfigLoader]
)
providers.Singleton(
    OrderRepositoryImpl,
    db_connection=Provide[DatabaseConnection]
)
```

#### Application Layer

```python
# Singleton Provider 사용 (비즈니스 서비스 중앙 진입점)
providers.Singleton(
    OrderApplicationService,
    order_repository=Provide[OrderRepositoryImpl],
    exchange_api=Provide[UpbitApiClient]
)
providers.Singleton(
    StrategyService,
    strategy_repository=Provide[StrategyRepositoryImpl]
)
```

#### Presentation Layer

```python
# Factory Provider 사용 (View 생명주기에 따라 새 인스턴스)
providers.Factory(
    MainWindowPresenter,
    strategy_service=Provide[StrategyService],
    order_service=Provide[OrderApplicationService]
)
```

---

## 📐 현재 구조 분석

### 1. `run_desktop_ui.py` 현재 흐름

```python
main()
  ↓
QApplication 생성 (최우선 - DPI 설정)
  ↓
QAsyncApplication.initialize()
  ↓
  1. AppKernel.bootstrap()
  2. DILifecycleManager 초기화 (선택적)
  3. MainWindow 생성 (MVP 패턴)
  ↓
QAsyncApplication.run()
  ↓
종료 대기 (shutdown_event)
  ↓
QAsyncApplication.shutdown()
```

### 2. 문제점 식별

#### ❌ 문제 1: 초기화 순서 불명확

```python
# run_desktop_ui.py 현재 코드
self.kernel = AppKernel.bootstrap(self.qapp, kernel_config)
self.di_manager = get_di_lifecycle_manager()  # 순서 모호
```

- **문제**: AppKernel과 DILifecycleManager의 역할 중첩
- **영향**: 서비스 초기화 책임이 분산됨

#### ❌ 문제 2: 경로 서비스 최우선 보장 없음

```python
# 현재 PathServiceFactory는 지연 초기화 (lazy)
def get_service(cls, environment: str = "default"):
    if environment not in cls._instances:
        # 최초 호출 시 생성
```

- **문제**: 명시적인 "최우선 초기화" 보장 없음
- **영향**: 다른 서비스가 먼저 초기화되면 경로 불확실

#### ❌ 문제 3: DILifecycleManager와 Container 관계 불명확

```python
# infrastructure/dependency_injection/__init__.py
from .external_dependency_container import ExternalDependencyContainer
from .di_lifecycle_manager import DILifecycleManager
```

- **문제**: 두 컴포넌트의 책임 경계 모호
- **영향**: 개발자가 어느 것을 사용해야 할지 혼란

#### ❌ 문제 4: MVP 패턴 연결 로직 복잡

```python
# run_desktop_ui.py 라인 147-174
try:
    presenter = self.di_manager.get_main_window_presenter()
    self.main_window = MainWindow()
    self.main_window.presenter = presenter
    if hasattr(presenter, 'set_view'):
        presenter.set_view(self.main_window)
    self.main_window.complete_initialization()
except Exception as mvp_error:
    # 구조적 문제 발생 시 종료
```

- **문제**: 수동 연결 로직이 많고 에러 처리 복잡
- **영향**: 유지보수 어려움, 테스트 복잡

---

## 🎯 리팩터링 목표 아키텍처

### 1. 이상적인 초기화 시퀀스

```python
# run_desktop_ui.py (리팩터링 후)

class ApplicationBootstrapper:
    """애플리케이션 부트스트랩 전담 클래스"""

    def __init__(self, qapp: QApplication):
        self.qapp = qapp
        self.services = {}

    async def bootstrap(self) -> bool:
        """
        단계별 초기화 (명확한 순서 보장)
        """
        try:
            # Phase 1: 경로 서비스 (최우선)
            self.services['path'] = await self._init_path_service()

            # Phase 2: 설정 서비스
            self.services['config'] = await self._init_config_service()

            # Phase 3: 로깅 서비스
            self.services['logging'] = await self._init_logging_service()

            # Phase 4: DI 컨테이너 (모든 기반 준비 완료 후)
            self.services['container'] = await self._init_di_container()

            # Phase 5: Infrastructure 서비스들
            await self._init_infrastructure_services()

            # Phase 6: Application 서비스들
            await self._init_application_services()

            # Phase 7: Presentation Layer
            await self._init_presentation_layer()

            return True

        except Exception as e:
            logger.error(f"부트스트랩 실패: {e}")
            return False

    async def _init_path_service(self):
        """Phase 1: 경로 서비스 초기화"""
        logger.info("📂 Phase 1: 경로 서비스 초기화")

        # PathServiceFactory 사용 (싱글톤 보장)
        path_service = PathServiceFactory.get_service("production")

        # 필수 디렉터리 생성 확인
        path_service.initialize_directories()

        logger.info("✅ 경로 서비스 초기화 완료")
        return path_service

    async def _init_config_service(self):
        """Phase 2: 설정 서비스 초기화"""
        logger.info("⚙️ Phase 2: 설정 서비스 초기화")

        path_service = self.services['path']
        config_path = path_service.get_config_file_path()

        config_loader = ConfigLoader(config_path)
        config = config_loader.load()

        logger.info("✅ 설정 서비스 초기화 완료")
        return config

    async def _init_logging_service(self):
        """Phase 3: 로깅 서비스 초기화"""
        logger.info("📝 Phase 3: 로깅 서비스 초기화")

        path_service = self.services['path']
        config = self.services['config']

        log_path = path_service.get_log_directory()

        logging_service = LoggingService(
            log_directory=log_path,
            config=config.logging
        )
        logging_service.initialize()

        logger.info("✅ 로깅 서비스 초기화 완료")
        return logging_service

    async def _init_di_container(self):
        """Phase 4: DI 컨테이너 초기화"""
        logger.info("🔧 Phase 4: DI 컨테이너 초기화")

        # 기반 서비스들을 컨테이너에 주입
        container = UnifiedDIContainer()

        # 이미 초기화된 서비스들을 컨테이너에 등록
        container.path_service.override(self.services['path'])
        container.config_service.override(self.services['config'])
        container.logging_service.override(self.services['logging'])

        # 컨테이너 와이어링
        container.wire(modules=[
            'upbit_auto_trading.infrastructure',
            'upbit_auto_trading.application',
            'upbit_auto_trading.ui.desktop'
        ])

        logger.info("✅ DI 컨테이너 초기화 완료")
        return container
```

### 2. 통합 DI 컨테이너 설계

```python
# infrastructure/dependency_injection/unified_container.py

from dependency_injector import containers, providers

class UnifiedDIContainer(containers.DeclarativeContainer):
    """
    통합 DI 컨테이너 - 모든 레이어의 서비스 관리

    특징:
    - 명확한 의존성 체인
    - 계층별 Provider 전략
    - 테스트 용이성
    """

    # ============================================
    # Phase 1-3: 기반 서비스 (외부에서 주입받음)
    # ============================================
    path_service = providers.Dependency()  # 외부 주입
    config_service = providers.Dependency()  # 외부 주입
    logging_service = providers.Dependency()  # 외부 주입

    # ============================================
    # Phase 5: Infrastructure Layer (Singleton)
    # ============================================

    # DB 연결 (Singleton: 앱 전체 공유)
    db_connection = providers.Singleton(
        DatabaseConnection,
        db_path=path_service.provided.get_database_path
    )

    # API 클라이언트 (Singleton: 연결 상태 유지)
    upbit_api_client = providers.Singleton(
        UpbitApiClient,
        api_key=config_service.provided.api_key,
        secret_key=config_service.provided.secret_key
    )

    # Repository 구현체 (Singleton)
    strategy_repository = providers.Singleton(
        SqliteStrategyRepository,
        db_connection=db_connection
    )

    order_repository = providers.Singleton(
        SqliteOrderRepository,
        db_connection=db_connection
    )

    # ============================================
    # Phase 6: Application Layer (Singleton)
    # ============================================

    # 전략 서비스 (Singleton: 비즈니스 로직 중심)
    strategy_service = providers.Singleton(
        StrategyApplicationService,
        strategy_repository=strategy_repository
    )

    # 주문 서비스 (Singleton)
    order_service = providers.Singleton(
        OrderApplicationService,
        order_repository=order_repository,
        exchange_api=upbit_api_client
    )

    # ============================================
    # Phase 7: Presentation Layer (Factory)
    # ============================================

    # MainWindow Presenter (Factory: View당 새 인스턴스)
    main_window_presenter = providers.Factory(
        MainWindowPresenter,
        strategy_service=strategy_service,
        order_service=order_service
    )

    # Strategy Presenter (Factory)
    strategy_presenter = providers.Factory(
        StrategyPresenter,
        strategy_service=strategy_service
    )
```

### 3. MainWindow MVP 자동 연결

```python
# ui/desktop/main_window.py (리팩터링 후)

from dependency_injector.wiring import inject, Provide
from upbit_auto_trading.infrastructure.dependency_injection import UnifiedDIContainer

class MainWindow(QMainWindow):
    """
    메인 윈도우 - MVP 패턴 View

    @inject 데코레이터로 자동 의존성 주입
    """

    @inject
    def __init__(
        self,
        presenter: MainWindowPresenter = Provide[UnifiedDIContainer.main_window_presenter]
    ):
        super().__init__()

        # Presenter 자동 주입 (DI 컨테이너가 관리)
        self.presenter = presenter

        # Presenter에 View 참조 설정 (양방향)
        self.presenter.set_view(self)

        # UI 초기화
        self._init_ui()

        # Presenter 초기화 완료 통보
        self.presenter.on_view_ready()

    def _init_ui(self):
        """UI 초기 구성"""
        # ... UI 코드
```

---

## 📋 실행 계획 (Step-by-Step)

### Phase 1: 기반 정리 (우선순위 1)

#### Task 1.1: PathService 최우선 초기화 보장

- [ ] `PathServiceFactory`에 명시적 초기화 메서드 추가
- [ ] `ApplicationBootstrapper` 클래스 생성
- [ ] Phase 1 초기화 로직 구현

#### Task 1.2: ConfigLoader 통합

- [ ] PathService → ConfigLoader 의존성 명확화
- [ ] Phase 2 초기화 로직 구현

#### Task 1.3: LoggingService 통합

- [ ] PathService + ConfigLoader → LoggingService 체인 구현
- [ ] Phase 3 초기화 로직 구현

### Phase 2: DI 컨테이너 통합 (우선순위 2)

#### Task 2.1: UnifiedDIContainer 설계

- [ ] 현재 `ExternalDependencyContainer` 분석
- [ ] 통합 컨테이너 설계 문서 작성
- [ ] `unified_container.py` 구현

#### Task 2.2: DILifecycleManager 역할 재정의

- [ ] Container와 Manager 책임 분리
- [ ] Manager → 생명주기만 담당하도록 단순화

#### Task 2.3: 레이어별 Provider 전략 적용

- [ ] Infrastructure: Singleton
- [ ] Application: Singleton
- [ ] Presentation: Factory

### Phase 3: MVP 패턴 자동화 (우선순위 3)

#### Task 3.1: @inject 데코레이터 적용

- [ ] MainWindow `__init__` 리팩터링
- [ ] 수동 연결 로직 제거

#### Task 3.2: Presenter 자동 와이어링

- [ ] Container에 Presenter 등록
- [ ] View ↔ Presenter 양방향 자동 연결

### Phase 4: run_desktop_ui.py 재작성 (우선순위 4)

#### Task 4.1: ApplicationBootstrapper 적용

- [ ] 기존 `QAsyncApplication` 대체
- [ ] 단계별 초기화 로직 구현

#### Task 4.2: 에러 핸들링 개선

- [ ] 단계별 실패 시 명확한 에러 메시지
- [ ] 롤백 로직 구현

#### Task 4.3: 종료 시퀀스 정리

- [ ] 역순 종료 보장
- [ ] 리소스 정리 검증

### Phase 5: 테스트 및 검증 (우선순위 5)

#### Task 5.1: 단위 테스트 작성

- [ ] ApplicationBootstrapper 테스트
- [ ] UnifiedDIContainer 테스트

#### Task 5.2: 통합 테스트

- [ ] 전체 초기화 시퀀스 테스트
- [ ] MVP 패턴 연결 테스트

#### Task 5.3: 실제 실행 검증

- [ ] `python run_desktop_ui.py` 정상 작동
- [ ] 7규칙 전략 구성 가능 확인

---

## 🎯 성공 기준

### 정량적 지표

- [ ] 초기화 단계가 명확히 7단계로 분리됨
- [ ] DI Container Provider가 계층별로 적절히 설정됨
- [ ] 수동 연결 코드가 80% 이상 제거됨
- [ ] 단위 테스트 커버리지 70% 이상

### 정성적 지표

- [ ] 신규 개발자가 초기화 흐름을 30분 내 이해 가능
- [ ] 새로운 서비스 추가 시 명확히 어느 단계에 넣을지 알 수 있음
- [ ] Mock 주입을 통한 테스트가 용이함
- [ ] 에러 발생 시 어느 단계에서 실패했는지 즉시 파악 가능

---

## 📚 참고 자료

### 현재 프로젝트 문서

- `docs/ARCHITECTURE_GUIDE.md` - DDD 4계층 구조
- `docs/MVP_ARCHITECTURE.md` - MVP 패턴 가이드
- `docs/DEPENDENCY_INJECTION_ARCHITECTURE.md` - DI 아키텍처
- `.github/copilot-instructions.md` - 개발 가이드라인

### 핵심 대화 내용

1. **경로 서비스 우선**: 설정 읽기보다 경로 확정이 선행
2. **DB 파일 생성 책임**: 경로 서비스(Where) + DB 서비스(What/How)
3. **DI Singleton Provider**: 전통적 싱글톤 패턴 대체

### 외부 참고

- `dependency-injector` 공식 문서
- DDD 계층형 아키텍처 베스트 프랙티스
- PyQt6 + qasync 비동기 패턴

---

## ⚠️ 리스크 및 대응

### Risk 1: 기존 코드와의 호환성

- **리스크**: 점진적 리팩터링 중 기존 코드 동작 중단
- **대응**: Legacy 호환 함수 유지, 단계적 마이그레이션

### Risk 2: DI 컨테이너 복잡도 증가

- **리스크**: 통합 컨테이너가 너무 비대해짐
- **대응**: 레이어별 하위 컨테이너로 분리 (Modular Design)

### Risk 3: 초기화 시간 증가

- **리스크**: 7단계 순차 초기화로 인한 시작 시간 지연
- **대응**:
  - 병렬화 가능한 단계 식별 (Phase 5-6)
  - 지연 초기화 적용 (사용 시점 초기화)

---

## 📌 다음 액션

1. **즉시 실행**: Task 1.1 시작 (PathService 최우선 초기화)
2. **문서 리뷰**: 이 계획서를 팀/AI와 리뷰
3. **프로토타입**: ApplicationBootstrapper 최소 구현
4. **검증**: 기존 `run_desktop_ui.py`와 병렬 실행 테스트

---

**작성자**: GitHub Copilot
**검토 필요**: 프로젝트 리드
**갱신 주기**: 각 Phase 완료 시
