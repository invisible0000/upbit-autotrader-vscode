# 📋 TASK_20250928_01: 깔끔한 DI 아키텍처 전면 재구축

## 🎯 태스크 목표

- **주요 목표**: 하위호환성 없이 DDD 구조에 완벽히 부합하는 의존성 주입 시스템 구축
- **완료 기준**: `python run_desktop_ui.py` 실행 시 모든 핵심 서비스가 DI Container를 통해 해결되며, 7규칙 전략 정상 동작

## 📊 현재 상황 분석

### 🔴 주요 문제점

1. **혼재된 DI 패턴**: 자체 구현 DIContainer + 수동 resolve() 방식 혼재
2. **Service Locator 패턴 잔존**: `get_path_service()` 등 전역 함수들 다수 존재
3. **Placeholder 상태 핵심 서비스**: API, Repository, Application Service 등록 미완성
4. **아키텍처 불일치**: ApplicationContext vs DIContainer 역할 모호

### 💎 전문가 권고사항

- **dependency-injector 라이브러리 전면 도입**: `@inject` 데코레이터 + Provider 패턴
- **생성자 주입 패턴 표준화**: 모든 서비스에 일관된 DI 적용
- **Configuration Provider 활용**: 설정 파일 기반 환경별 구성 관리

### 🎯 설계 원칙

- **Clean Architecture DDD 준수**: Domain → Application → Infrastructure → Presentation
- **의존성 역전 원칙**: 인터페이스 기반 느슨한 결합
- **단일 책임 원칙**: 각 컴포넌트는 명확한 단일 책임

## 🔄 체계적 작업 절차

### Phase 1: Foundation Setup (2-3시간)

- [ ] **dependency-injector 라이브러리 도입 및 기존 DIContainer 대체**
- [ ] **Container 구조 재설계**: DeclarativeContainer 기반 Provider 패턴 적용
- [ ] **ApplicationContext 역할 명확화**: Container 관리자 역할로 단순화

### Phase 2: Core Infrastructure DI (3-4시간)

- [ ] **Database 서비스 DI 등록**: DatabaseManager, Repository 팩토리
- [ ] **Configuration 서비스 DI 등록**: PathService, ConfigService 통합
- [ ] **Logging 서비스 DI 등록**: 통합 로깅 시스템

### Phase 3: Domain & Application Layer DI (2-3시간)

- [ ] **Repository 인터페이스 DI 등록**: IStrategyRepository, ITriggerRepository 등
- [ ] **Domain 서비스 DI 등록**: StrategyCompatibilityService 등
- [ ] **Application 서비스 DI 등록**: TriggerApplicationService 등

### Phase 4: Presentation Layer Integration (2-3시간)

- [ ] **UI 서비스 DI 등록**: ThemeService, StyleManager, NavigationBar 등
- [ ] **MainWindow DI 통합**: @inject 데코레이터 적용
- [ ] **Screen 컴포넌트 DI 적용**: 모든 UI 컴포넌트에 생성자 주입

### Phase 5: Testing & Validation (1-2시간)

- [ ] **DI Container 테스트**: 모든 서비스 해결 검증
- [ ] **통합 테스트**: API 키 설정 UI 정상 동작 확인
- [ ] **7규칙 전략 검증**: 트리거 빌더에서 전략 구성 가능 확인

## 🛠️ 상세 구현 계획

### 1. dependency-injector 도입 및 Container 재구축

#### 1.1 라이브러리 설치 및 Import 정리

```bash
pip install dependency-injector
```

#### 1.2 새로운 Container 구조 설계

```python
# upbit_auto_trading/infrastructure/dependency_injection/container.py (완전 교체)
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

class ApplicationContainer(containers.DeclarativeContainer):
    """DDD 아키텍처 기반 애플리케이션 DI 컨테이너"""

    # Configuration Provider
    config = providers.Configuration()

    # Infrastructure Layer Providers
    logging_service = providers.Singleton(...)
    database_manager = providers.Singleton(...)
    path_service = providers.Singleton(...)

    # Repository Providers
    strategy_repository = providers.Singleton(...)
    trigger_repository = providers.Singleton(...)

    # Domain Service Providers
    strategy_compatibility_service = providers.Factory(...)

    # Application Service Providers
    trigger_application_service = providers.Factory(...)

    # UI Service Providers
    theme_service = providers.Singleton(...)
    style_manager = providers.Singleton(...)
```

#### 1.3 ApplicationContext 역할 단순화

```python
# upbit_auto_trading/infrastructure/dependency_injection/app_context.py (대폭 수정)
class ApplicationContext:
    """애플리케이션 컨텍스트 - Container 관리 전담"""

    def __init__(self):
        self._container = ApplicationContainer()

    def initialize(self) -> None:
        # Configuration 로딩
        self._container.config.from_yaml('config/config.yaml')

        # Wiring 설정
        self._container.wire(modules=[
            'upbit_auto_trading.ui.desktop.main_window',
            'upbit_auto_trading.ui.desktop.screens',
        ])

    def container(self) -> ApplicationContainer:
        return self._container
```

### 2. Infrastructure Layer DI 등록

#### 2.1 Database 서비스 Provider 등록

```python
# Container 내 Database Provider
database_manager = providers.Singleton(
    DatabaseConnectionProvider.get_manager,
)

# Repository Factory Pattern
strategy_repository = providers.Factory(
    SqliteStrategyRepository,
    database_manager=database_manager,
)
```

#### 2.2 Configuration 서비스 통합

```python
# 기존 get_path_service() 제거하고 Provider로 등록
path_service = providers.Singleton(
    PathConfigurationService,
    config=config.paths,
)

# Repository에 PathService 주입
strategy_repository = providers.Factory(
    SqliteStrategyRepository,
    database_manager=database_manager,
    path_service=path_service,
)
```

#### 2.3 Logging 서비스 Provider

```python
logging_service = providers.Singleton(
    LoggingServiceImpl,
    config=config.logging,
)
```

### 3. API 서비스 DI 등록 (긴급 복구)

#### 3.1 ApiKeyService Provider 등록

```python
# Repository 생성
secure_keys_repository = providers.Factory(
    SqliteSecureKeysRepository,
    database_manager=database_manager,
)

# ApiKeyService 등록
api_key_service = providers.Factory(
    ApiKeyService,
    repository=secure_keys_repository,
)
```

### 4. UI Layer @inject 적용

#### 4.1 MainWindow 생성자 주입

```python
# upbit_auto_trading/ui/desktop/main_window.py
from dependency_injector.wiring import inject, Provide

class MainWindow(QMainWindow):
    @inject
    def __init__(
        self,
        theme_service: IThemeService = Provide[ApplicationContainer.theme_service],
        style_manager: StyleManager = Provide[ApplicationContainer.style_manager],
        parent=None
    ):
        super().__init__(parent)
        self._theme_service = theme_service
        self._style_manager = style_manager
        # ...
```

#### 4.2 Screen 컴포넌트 생성자 주입

```python
# upbit_auto_trading/ui/desktop/screens/settings/settings_screen.py
class SettingsScreen(QWidget):
    @inject
    def __init__(
        self,
        api_key_service: IApiKeyService = Provide[ApplicationContainer.api_key_service],
        parent=None
    ):
        super().__init__(parent)
        self._api_key_service = api_key_service
        # ...
```

### 5. 전역 함수 제거 및 DI 마이그레이션

#### 5.1 제거 대상 전역 함수들

```python
# 제거할 함수들 (Service Locator 패턴)
- get_path_service()
- get_domain_event_publisher()
- database_connection_service (전역 변수)
- PathServiceFactory.get_instance()
```

#### 5.2 DI Provider로 마이그레이션

```python
# 모든 전역 함수를 Container Provider로 교체
domain_event_publisher = providers.Singleton(
    DomainEventPublisher,
)

path_configuration_service = providers.Singleton(
    PathConfigurationService,
    config=config.paths,
)
```

## 🎯 성공 기준

### ✅ 기능적 검증 기준

- [ ] **API 키 설정 UI 완전 복구**: 사용자가 API 키 입력 및 저장 가능
- [ ] **모든 Screen 컴포넌트 정상 로딩**: 설정, 차트, 트리거 빌더 등 모든 화면 정상 표시
- [ ] **7규칙 전략 구성 가능**: 트리거 빌더에서 RSI, 불타기 등 7규칙 모두 구성 가능
- [ ] **실시간 데이터 연동**: WebSocket을 통한 코인리스트, 호가창 정상 동작

### ✅ 아키텍처 검증 기준

- [ ] **DI Container 해결률 100%**: 등록된 모든 서비스 정상 해결
- [ ] **Service Locator 패턴 완전 제거**: 전역 함수 0개, Provider 패턴만 사용
- [ ] **생성자 주입 패턴 표준화**: 모든 서비스에 @inject 데코레이터 적용
- [ ] **Configuration Provider 활용**: 모든 설정이 config.yaml 파일 기반

### ✅ 품질 검증 기준

- [ ] **ERROR 메시지 제로**: `python run_desktop_ui.py` 실행 시 ERROR 없음
- [ ] **WARNING 메시지 최소화**: 기존 대비 80% 감소
- [ ] **초기화 시간 유지**: 애플리케이션 시작 시간 5초 이내
- [ ] **메모리 사용량 최적화**: DI Container 오버헤드 최소화

## 💡 작업 시 주의사항

### 🛡️ 안전성 원칙

- **백업 우선**: 기존 DI 관련 파일들 모두 `_legacy` 백업
- **단계별 검증**: 각 Phase 완료 후 즉시 동작 확인
- **롤백 준비**: 문제 발생시 즉시 복구 가능한 상태 유지

### 🏗️ DDD 아키텍처 준수

- **계층 분리 엄수**: Domain은 Infrastructure 의존 금지
- **의존성 역전 원칙**: 인터페이스 기반 등록 우선
- **단일 책임 원칙**: 각 Provider는 하나의 책임만

### ⚡ 성능 고려사항

- **지연 로딩**: 필요한 시점에만 서비스 인스턴스 생성
- **싱글톤 패턴**: 상태를 갖지 않는 서비스는 Singleton으로
- **Factory 패턴**: 상태를 갖는 서비스는 Factory로

## 🧪 테스트 전략

### 1. 단위 테스트 (각 Phase별)

```python
def test_container_registration():
    """모든 서비스가 정상 등록되었는지 테스트"""
    container = ApplicationContainer()
    container.config.from_dict({...})

    # 핵심 서비스들 해결 테스트
    api_service = container.api_key_service()
    assert api_service is not None

    theme_service = container.theme_service()
    assert theme_service is not None
```

### 2. 통합 테스트

```bash
# UI 통합 테스트
python run_desktop_ui.py
# → 모든 화면 정상 로딩
# → API 키 설정 탭 정상 동작
# → 트리거 빌더에서 7규칙 구성 가능

# QAsync 마이그레이션 결과 유지 확인
# → WebSocket 연결 (Public + Private) 정상
# → 이벤트 루프 충돌 없음
```

### 3. 성능 테스트

```python
# 초기화 시간 측정
import time
start = time.time()
app_context = ApplicationContext()
app_context.initialize()
duration = time.time() - start
assert duration < 5.0  # 5초 이내
```

## 🔧 개발할 도구

### `di_migration_tool.py`: DI 마이그레이션 도구

```python
"""
기능:
1. 기존 전역 함수 사용처 자동 탐지
2. @inject 데코레이터 자동 적용
3. Provider 등록 코드 자동 생성
4. 마이그레이션 전후 비교 리포트
"""
```

### `di_validator.py`: DI 검증 도구

```python
"""
기능:
1. Container 등록 상태 검증
2. 순환 의존성 탐지
3. 누락된 서비스 자동 탐지
4. 성능 벤치마크 측정
"""
```

## 📋 작업 상태 추적

### Phase 1: Foundation Setup

- [ ] dependency-injector 설치 및 기존 container.py 백업
- [ ] ApplicationContainer 클래스 생성 (DeclarativeContainer 기반)
- [ ] ApplicationContext 역할 단순화 및 wiring 설정
- [ ] 기본 Configuration Provider 등록

### Phase 2: Infrastructure Layer DI

- [ ] DatabaseManager Provider 등록
- [ ] PathService Provider 등록 (get_path_service() 대체)
- [ ] LoggingService Provider 등록
- [ ] ApiKeyService Provider 등록 (긴급 복구)

### Phase 3: Domain & Application Layer DI

- [ ] Repository 인터페이스 정의 및 Provider 등록
- [ ] Domain Service Provider 등록
- [ ] Application Service Provider 등록
- [ ] Event System Provider 등록

### Phase 4: UI Layer Integration

- [ ] ThemeService, StyleManager Provider 등록
- [ ] MainWindow @inject 적용
- [ ] SettingsScreen @inject 적용
- [ ] 기타 Screen 컴포넌트 @inject 적용

### Phase 5: Testing & Validation

- [ ] DI Container 단위 테스트
- [ ] UI 통합 테스트
- [ ] API 키 설정 UI 검증
- [ ] 7규칙 전략 구성 검증
- [ ] 성능 및 메모리 사용량 검증

## 🚀 즉시 시작할 작업

### 1. 환경 준비

```bash
# dependency-injector 설치
pip install dependency-injector

# 기존 파일 백업
Copy-Item "upbit_auto_trading/infrastructure/dependency_injection/container.py" "upbit_auto_trading/infrastructure/dependency_injection/container_legacy.py"
Copy-Item "upbit_auto_trading/infrastructure/dependency_injection/app_context.py" "upbit_auto_trading/infrastructure/dependency_injection/app_context_legacy.py"
```

### 2. 새로운 Container 뼈대 생성

```python
# upbit_auto_trading/infrastructure/dependency_injection/container.py
from dependency_injector import containers, providers

class ApplicationContainer(containers.DeclarativeContainer):
    """DDD 아키텍처 기반 애플리케이션 DI 컨테이너"""

    # Configuration
    config = providers.Configuration()

    # 기본 Provider들부터 차례대로 등록
```

### 3. 첫 번째 검증

```bash
# 기본 구조 동작 확인
python -c "
from upbit_auto_trading.infrastructure.dependency_injection.container import ApplicationContainer
container = ApplicationContainer()
print('✅ Container 생성 성공')
"
```

## 📊 예상 소요 시간

- **Phase 1**: 2-3시간 (Foundation Setup)
- **Phase 2**: 3-4시간 (Infrastructure DI)
- **Phase 3**: 2-3시간 (Domain/Application DI)
- **Phase 4**: 2-3시간 (UI Integration)
- **Phase 5**: 1-2시간 (Testing)

**총 예상 시간**: 10-15시간 (2-3일 분할 작업 권장)

---

**다음 에이전트 시작점**:

1. `pip install dependency-injector` 실행
2. Phase 1의 첫 번째 체크박스부터 순차 진행
3. 각 Phase 완료 후 반드시 `python run_desktop_ui.py`로 동작 확인

**🎯 성공의 핵심**: 하위호환성을 포기하고 깔끔한 아키텍처 구축에 집중. 각 단계마다 철저한 검증으로 안전한 마이그레이션 보장.
