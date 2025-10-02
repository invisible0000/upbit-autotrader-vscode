# 🚀 초기화 리팩터링 퀵 스타트 가이드

> **대상**: 개발자 / AI Assistant
> **목적**: 첨부된 대화 내용의 핵심을 실행 가능한 액션으로 변환
> **관련 문서**: `INITIALIZATION_SEQUENCE_REFACTORING_PLAN.md`

---

## 💡 핵심 인사이트 3가지

### 1️⃣ 서비스 시작은 "경로 → 설정 → 로깅 → DB" 순서

**왜?**

- 설정 파일을 읽으려면 → 파일 위치를 알아야 함 (경로 필요)
- DB 파일을 생성하려면 → 저장 위치를 알아야 함 (경로 필요)
- 로그를 기록하려면 → 로그 디렉터리 위치를 알아야 함 (경로 필요)

**코드 적용**:

```python
# ✅ 올바른 순서
path_service = PathServiceFactory.get_service("production")  # 1순위
config = ConfigLoader(path_service.get_config_path())       # 2순위
logging_service = LoggingService(path_service.get_log_path()) # 3순위
db_connection = DatabaseConnection(path_service.get_db_path()) # 4순위
```

```python
# ❌ 잘못된 순서
config = ConfigLoader("./config.yaml")  # 경로 하드코딩!
path_service = PathServiceFactory.get_service()  # 너무 늦음
```

---

### 2️⃣ 전통적 싱글톤 ❌, DI Singleton Provider ✅

**전통적 싱글톤의 문제**:

```python
# ❌ 피해야 할 패턴
class OrderService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

# 클라이언트 코드
order_service = OrderService.get_instance()  # 강한 결합!
```

**DI Singleton Provider 사용**:

```python
# ✅ 권장 패턴
# containers.py
class UnifiedDIContainer(containers.DeclarativeContainer):
    order_service = providers.Singleton(
        OrderApplicationService,
        repository=Provide[order_repository]
    )

# 클라이언트 코드 (명시적 주입)
@inject
def __init__(
    self,
    order_service: OrderApplicationService = Provide[UnifiedDIContainer.order_service]
):
    self._order_service = order_service  # 느슨한 결합!
```

**장점**:

- ✅ 테스트 시 Mock 쉽게 주입 가능
- ✅ 의존성이 생성자에 명시됨
- ✅ 인터페이스로 추상화 가능

---

### 3️⃣ DB 파일 생성은 DB 서비스의 책임

**역할 분리**:

| 서비스 | 책임 | 예시 |
|--------|------|------|
| **PathService** | "어디에?" (Where) | `C:\Users\...\data\trading.db` 경로 제공 |
| **DatabaseService** | "무엇을? 어떻게?" (What/How) | DB 파일 생성, 스키마 초기화, 연결 관리 |

**코드 예시**:

```python
# 1. PathService가 경로 제공
path_service = PathServiceFactory.get_service()
db_path = path_service.get_database_path()  # "어디에?"

# 2. PathService가 디렉터리 존재 확인/생성
path_service.initialize_directories()  # data/ 폴더 생성

# 3. DatabaseService가 DB 파일 생성/연결
db_service = DatabaseService(db_path)  # "무엇을? 어떻게?"
db_service.connect()  # sqlite3.connect() 호출 → 파일 생성
db_service.initialize_schema()  # CREATE TABLE ...
```

---

## 🎯 즉시 실행 가능한 액션

### Action 1: `run_desktop_ui.py` 초기화 순서 검증

**목표**: 현재 코드에서 경로 서비스가 최우선으로 초기화되는지 확인

**실행 단계**:

```powershell
# 1. 현재 초기화 로그 확인
$env:UPBIT_LOG_SCOPE = "verbose"
$env:UPBIT_COMPONENT_FOCUS = "MainApp,PathServiceFactory"
python run_desktop_ui.py

# 2. 로그에서 순서 확인
# 예상 출력:
# [PathServiceFactory] 🏭 새로운 PathService 인스턴스 생성
# [ConfigLoader] ⚙️ 설정 파일 로드: <경로>
# [LoggingService] 📝 로깅 시스템 초기화
```

**검증 포인트**:

- [ ] PathServiceFactory 로그가 가장 먼저 출력되는가?
- [ ] ConfigLoader가 PathService 이후에 실행되는가?
- [ ] 만약 순서가 뒤바뀌었다면 → 즉시 수정 필요

---

### Action 2: DI 컨테이너 현재 상태 파악

**목표**: 현재 사용 중인 DI 시스템이 무엇인지 명확히 파악

**실행 단계**:

```powershell
# 1. DI 컨테이너 관련 파일 검색
Get-ChildItem upbit_auto_trading/infrastructure/dependency_injection -Recurse -Include *.py

# 2. 현재 run_desktop_ui.py에서 사용 중인 것 확인
Select-String -Path run_desktop_ui.py -Pattern "DILifecycleManager|ExternalDependencyContainer"
```

**분석 질문**:

- [ ] `ExternalDependencyContainer`와 `DILifecycleManager`의 역할 차이는?
- [ ] 둘 다 필요한가? 하나로 통합 가능한가?
- [ ] 현재 Provider 전략(Singleton/Factory)이 명확한가?

**문서화**:

```markdown
## 현재 DI 시스템 현황

### ExternalDependencyContainer
- 역할: [조사 후 기록]
- 관리 서비스: [리스트 작성]
- Provider 전략: [Singleton/Factory 확인]

### DILifecycleManager
- 역할: [조사 후 기록]
- 생명주기 관리 범위: [확인]
- ExternalDependencyContainer와 관계: [명확화]
```

---

### Action 3: MVP 패턴 수동 연결 로직 제거 프로토타입

**목표**: MainWindow와 Presenter 자동 연결 구현

**Before (현재 - 수동 연결)**:

```python
# run_desktop_ui.py
presenter = self.di_manager.get_main_window_presenter()
self.main_window = MainWindow()
self.main_window.presenter = presenter  # 수동 연결
if hasattr(presenter, 'set_view'):
    presenter.set_view(self.main_window)  # 수동 연결
self.main_window.complete_initialization()
```

**After (목표 - 자동 연결)**:

```python
# run_desktop_ui.py (간소화)
self.main_window = MainWindow()  # DI가 자동으로 Presenter 주입
self.main_window.show()

# ui/desktop/main_window.py
from dependency_injector.wiring import inject, Provide

@inject
def __init__(
    self,
    presenter: MainWindowPresenter = Provide[UnifiedDIContainer.main_window_presenter]
):
    super().__init__()
    self.presenter = presenter  # 자동 주입됨
    self.presenter.set_view(self)  # 양방향 연결
    self._init_ui()
```

**실행 단계**:

1. [ ] `ui/desktop/main_window.py`에 `@inject` 데코레이터 추가
2. [ ] DI 컨테이너에 `main_window_presenter` Factory 등록
3. [ ] `run_desktop_ui.py`에서 수동 연결 코드 제거
4. [ ] 테스트: `python run_desktop_ui.py`로 정상 작동 확인

---

## 📋 Phase별 체크리스트

### Phase 1: 기반 정리 (1-2일)

- [ ] **Task 1.1**: PathService 최우선 보장
  - [ ] 현재 초기화 로그 분석
  - [ ] `ApplicationBootstrapper` 클래스 생성
  - [ ] Phase 1 초기화 메서드 구현

- [ ] **Task 1.2**: ConfigLoader 통합
  - [ ] PathService → ConfigLoader 의존성 명확화
  - [ ] Phase 2 초기화 메서드 구현

- [ ] **Task 1.3**: LoggingService 통합
  - [ ] Phase 3 초기화 메서드 구현
  - [ ] 초기화 순서 검증 테스트 작성

**완료 기준**:

```python
# 이 코드가 정상 작동해야 함
bootstrapper = ApplicationBootstrapper(qapp)
await bootstrapper.bootstrap_phase_1_to_3()
assert bootstrapper.services['path'] is not None
assert bootstrapper.services['config'] is not None
assert bootstrapper.services['logging'] is not None
```

---

### Phase 2: DI 컨테이너 통합 (2-3일)

- [ ] **Task 2.1**: 현재 DI 시스템 분석
  - [ ] `ExternalDependencyContainer` 역할 문서화
  - [ ] `DILifecycleManager` 역할 문서화
  - [ ] 통합 가능성 검토

- [ ] **Task 2.2**: `UnifiedDIContainer` 설계
  - [ ] 계층별 Provider 전략 정의
  - [ ] 프로토타입 구현
  - [ ] 기존 컨테이너와 비교 테스트

- [ ] **Task 2.3**: 점진적 마이그레이션
  - [ ] Infrastructure Layer 서비스 이전
  - [ ] Application Layer 서비스 이전
  - [ ] 기존 코드와 병렬 실행 검증

**완료 기준**:

```python
# DI 컨테이너로 모든 서비스 주입 가능해야 함
container = UnifiedDIContainer()
container.path_service.override(path_service_instance)
container.wire(modules=['upbit_auto_trading.infrastructure'])

# 서비스 획득 테스트
db_connection = container.db_connection()
assert db_connection is not None
```

---

### Phase 3: MVP 자동화 (1-2일)

- [ ] **Task 3.1**: MainWindow `@inject` 적용
  - [ ] Presenter 자동 주입 구현
  - [ ] 수동 연결 코드 제거
  - [ ] 정상 작동 검증

- [ ] **Task 3.2**: 다른 View들도 동일 패턴 적용
  - [ ] StrategyView
  - [ ] TriggerBuilderView
  - [ ] BacktestView

**완료 기준**:

```python
# run_desktop_ui.py가 이렇게 간단해져야 함
self.main_window = MainWindow()  # Presenter 자동 주입
self.main_window.show()
```

---

## 🧪 테스트 전략

### 단위 테스트

```python
# tests/test_initialization_sequence.py

import pytest
from upbit_auto_trading.infrastructure.configuration import PathServiceFactory

def test_path_service_is_first():
    """경로 서비스가 다른 모든 서비스보다 먼저 초기화됨을 검증"""
    # PathService 인스턴스 생성 (캐시 초기화)
    PathServiceFactory.clear_cache()

    path_service = PathServiceFactory.get_service("test")

    # 경로가 유효한지 확인
    assert path_service.get_config_path().exists()
    assert path_service.get_log_directory().exists()
    assert path_service.get_database_path().parent.exists()

def test_config_loader_depends_on_path():
    """ConfigLoader가 PathService에 의존함을 검증"""
    path_service = PathServiceFactory.get_service("test")

    # PathService로부터 경로를 받아 ConfigLoader 생성
    config_loader = ConfigLoader(path_service.get_config_path())

    config = config_loader.load()
    assert config is not None

def test_di_container_singleton_scope():
    """DI 컨테이너의 Singleton Provider가 동일 인스턴스 반환함을 검증"""
    container = UnifiedDIContainer()

    service1 = container.order_service()
    service2 = container.order_service()

    assert service1 is service2  # 동일 인스턴스
```

### 통합 테스트

```python
# tests/integration/test_full_bootstrap.py

import pytest
import qasync
from PyQt6.QtWidgets import QApplication

@pytest.mark.asyncio
async def test_full_application_bootstrap():
    """전체 애플리케이션 부트스트랩 프로세스 검증"""
    app = qasync.QApplication([])

    bootstrapper = ApplicationBootstrapper(app)

    # Phase 1-7 전체 초기화
    success = await bootstrapper.bootstrap()

    assert success is True
    assert 'path' in bootstrapper.services
    assert 'config' in bootstrapper.services
    assert 'container' in bootstrapper.services

    # 정리
    await bootstrapper.shutdown()
```

---

## 🔧 트러블슈팅

### 문제 1: "PathService가 초기화되지 않았습니다" 에러

**증상**:

```
RuntimeError: PathService가 초기화되지 않았습니다
```

**원인**: ConfigLoader가 PathService보다 먼저 실행됨

**해결**:

```python
# ❌ 잘못된 순서
config = ConfigLoader("config.yaml")
path_service = PathServiceFactory.get_service()

# ✅ 올바른 순서
path_service = PathServiceFactory.get_service()
config = ConfigLoader(path_service.get_config_path())
```

---

### 문제 2: DI 컨테이너에서 서비스를 찾을 수 없음

**증상**:

```
DependencyNotFound: Cannot find dependency 'order_service'
```

**원인**: 컨테이너 와이어링이 안 됨

**해결**:

```python
# 컨테이너 와이어링 필수
container = UnifiedDIContainer()
container.wire(modules=['upbit_auto_trading.infrastructure'])
```

---

### 문제 3: MainWindow에서 Presenter가 None

**증상**:

```python
self.presenter.some_method()  # AttributeError: NoneType
```

**원인**: `@inject` 데코레이터 누락 또는 와이어링 안 됨

**해결**:

```python
# 1. @inject 데코레이터 확인
from dependency_injector.wiring import inject, Provide

@inject
def __init__(self, presenter: MainWindowPresenter = Provide[...]):
    # ...

# 2. 모듈 와이어링 확인
container.wire(modules=['upbit_auto_trading.ui.desktop.main_window'])
```

---

## 📊 진행 상황 추적

### Week 1 (Phase 1)

- [ ] 월: PathService 최우선 검증 + ApplicationBootstrapper 스켈레톤
- [ ] 화: Phase 1-3 구현
- [ ] 수: 단위 테스트 작성
- [ ] 목: 통합 테스트 + 리뷰
- [ ] 금: 버그 수정 + 문서화

### Week 2 (Phase 2)

- [ ] 월-화: 현재 DI 시스템 분석
- [ ] 수-목: UnifiedDIContainer 구현
- [ ] 금: 마이그레이션 시작

### Week 3 (Phase 3-4)

- [ ] 월-화: MVP 자동화
- [ ] 수-목: run_desktop_ui.py 재작성
- [ ] 금: 전체 통합 테스트

---

## 🎓 학습 자료

### 추천 읽기 순서

1. 본 문서 (`INITIALIZATION_REFACTORING_QUICK_START.md`)
2. 상세 계획서 (`INITIALIZATION_SEQUENCE_REFACTORING_PLAN.md`)
3. DDD 아키텍처 가이드 (`docs/ARCHITECTURE_GUIDE.md`)
4. DI 아키텍처 가이드 (`docs/DEPENDENCY_INJECTION_ARCHITECTURE.md`)

### 외부 참고

- [dependency-injector 공식 문서](https://python-dependency-injector.ets-labs.org/)
- [DDD 계층형 아키텍처 패턴](https://martinfowler.com/bliki/PresentationDomainDataLayering.html)

---

**마지막 업데이트**: 2025년 10월 2일
**다음 리뷰**: Phase 1 완료 시
