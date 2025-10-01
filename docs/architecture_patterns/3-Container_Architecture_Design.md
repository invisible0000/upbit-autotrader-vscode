# 📋 3-Container 아키텍처 종합 설계 문서

## 🎯 전체 Container 구조 개요

### 🏗️ **완전한 3-Container + MVP 시스템 아키텍처**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    🎮 DILifecycleManager                             │
│                   (전체 Container 통합 관리)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ ExternalDependency│  │ApplicationService│  │  Presentation    │  │
│  │   Container      │  │   Container      │  │   Container      │  │
│  │ (Infrastructure) │  │ (Business Logic) │  │  (UI Services)   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│           │                      │                      │           │
│           └──────────────────────┼──────────────────────┘           │
│                                  │                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    MVP Container                            │   │
│  │              (Presenter-View 조합 관리)                     │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │   │
│  │   │  Settings   │    │  Strategy   │    │  Trigger    │    │   │
│  │   │ Presenter   │    │ Presenter   │    │ Presenter   │    │   │
│  │   └─────────────┘    └─────────────┘    └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 주요 Container별 역할 및 차이점

### 1. **PresentationContainer** (새로 생성) - UI Layer 전담

#### 📍 **파일 위치**

```
upbit_auto_trading/presentation/presentation_container.py
```

#### 🎯 **핵심 역할**

- **UI Infrastructure Services**: Navigation Bar, Status Bar, Theme Manager
- **UI Application Services**: Screen Manager, Window State, Menu Service
- **MainWindow Presenter Provider**: 모든 UI 서비스가 주입된 통합 Presenter
- **UI Layer DI 관리**: Presentation Layer의 모든 의존성 주입 담당

#### 🛠️ **제공하는 주요 Providers**

```python
class PresentationContainer:
    # UI Infrastructure
    navigation_service = providers.Factory(NavigationBar)
    status_bar_service = providers.Factory(StatusBar, database_health_service=...)

    # UI Application Services
    screen_manager_service = providers.Factory(ScreenManagerService, application_container=...)
    window_state_service = providers.Factory(WindowStateService)
    menu_service = providers.Factory(MenuService)

    # 핵심: MainWindow Presenter (모든 서비스 통합)
    main_window_presenter = providers.Factory(
        MainWindowPresenter,
        services=providers.Dict(
            theme_service=external_container.provided.theme_service,
            api_key_service=external_container.provided.api_key_service,
            screen_manager_service=screen_manager_service,
            window_state_service=window_state_service,
            menu_service=menu_service,
            navigation_bar=navigation_service
        )
    )
```

---

### 2. **MVP Container** (기존 유지) - Presenter-View 조합 관리

#### 📍 **파일 위치**

```
upbit_auto_trading/presentation/mvp_container.py (기존)
```

#### 🎯 **핵심 역할**

- **Feature별 Presenter 생성**: Settings, Strategy, Trigger, Backtest 등 각 화면별 Presenter
- **Presenter-View 조합**: MVP 패턴의 Presenter와 View를 연결하는 Factory 역할
- **Application Service 연동**: ApplicationServiceContainer에서 필요한 비즈니스 서비스 주입
- **화면별 MVP 완성**: 각 기능별로 독립적인 MVP 단위 제공

#### 🛠️ **제공하는 주요 기능**

```python
class MVPContainer:
    def create_settings_mvp(self):
        """Settings 화면의 Presenter + View 조합 생성"""

    def create_strategy_maker_mvp(self):
        """Strategy 화면의 Presenter + View 조합 생성"""

    def create_trigger_builder_mvp(self):
        """Trigger Builder 화면의 Presenter + View 조합 생성"""

    # PresentationContainer에서 제공하는 서비스들을 활용
    # ApplicationServiceContainer에서 비즈니스 로직 서비스 주입
```

---

## 🔄 Container 간 협력 관계

### 📊 **역할 분담 매트릭스**

| 구분 | ExternalDependency | ApplicationService | Presentation | MVP Container |
|------|-------------------|--------------------|--------------|---------------|
| **Infrastructure** | ✅ DB, API, 설정 | ❌ | ❌ | ❌ |
| **Business Logic** | ❌ | ✅ Use Cases, Domain | ❌ | ❌ |
| **UI Infrastructure** | ❌ | ❌ | ✅ Navigation, StatusBar | ❌ |
| **UI Services** | ❌ | ❌ | ✅ Screen, Window, Menu | ❌ |
| **MainWindow** | ❌ | ❌ | ✅ Presenter Provider | ❌ |
| **Feature MVP** | ❌ | ❌ | ❌ | ✅ Presenter-View 조합 |

### 🔗 **의존성 흐름**

#### **PresentationContainer 의존성**

```python
PresentationContainer:
├── ExternalDependencyContainer (Infrastructure 서비스)
│   ├── theme_service
│   ├── api_key_service
│   └── database_manager
├── ApplicationServiceContainer (Business 서비스)
│   ├── strategy_service
│   ├── trigger_service
│   └── settings_service
└── 자체 UI Services
    ├── navigation_service
    ├── status_bar_service
    ├── screen_manager_service
    ├── window_state_service
    └── menu_service
```

#### **MVP Container 의존성**

```python
MVPContainer:
├── ApplicationServiceContainer (비즈니스 로직)
│   ├── strategy_service → StrategyMakerPresenter
│   ├── trigger_service → TriggerBuilderPresenter
│   ├── settings_service → SettingsPresenter
│   └── backtest_service → BacktestPresenter
└── PresentationContainer (UI 서비스) - 필요시 접근
    └── theme_service, navigation_service 등
```

---

## 🎯 실제 동작 시나리오

### 🚀 **MainWindow 생성 과정**

```python
# 1. DILifecycleManager에서 통합 초기화
di_manager = get_di_lifecycle_manager()
di_manager.initialize()  # 3-Container 모두 초기화

# 2. PresentationContainer에서 MainWindowPresenter 생성
main_presenter = di_manager.get_presentation_container().main_window_presenter()
# → 모든 UI 서비스가 주입된 완전한 Presenter

# 3. MainWindow와 Presenter 연결
main_window = MainWindow()
main_window.set_presenter(main_presenter)  # MVP 패턴 완성
```

### 🔄 **Settings 화면 전환 과정**

```python
# 1. MainWindow에서 Settings 화면 전환 요청
main_window_presenter.switch_to_settings()

# 2. ScreenManagerService에서 MVP Container 활용
screen_manager = di_manager.get_presentation_container().screen_manager_service()
settings_view, settings_presenter = mvp_container.create_settings_mvp()

# 3. Settings MVP가 ApplicationServiceContainer의 비즈니스 서비스 활용
settings_presenter.load_data()  # → ApplicationServiceContainer.settings_service() 호출
```

---

## 🏗️ 아키텍처 장점

### 1. **명확한 책임 분리**

#### **PresentationContainer**

- ✅ **UI Layer 전담**: MainWindow와 관련된 모든 UI 서비스 통합 관리
- ✅ **Infrastructure 연동**: ExternalDependencyContainer의 Infrastructure 서비스 활용
- ✅ **Business 연동**: ApplicationServiceContainer의 비즈니스 서비스 연동

#### **MVP Container**

- ✅ **Feature별 관리**: 각 화면별 독립적인 MVP 단위 제공
- ✅ **조합 전담**: Presenter와 View의 생성 및 연결 전담
- ✅ **확장성**: 새로운 화면 추가 시 MVP Container에만 추가하면 됨

### 2. **유연한 확장성**

```python
# 새로운 화면 추가 시
class MVPContainer:
    def create_new_feature_mvp(self):
        """새 기능 화면의 MVP 조합"""
        # PresentationContainer의 UI 서비스 활용
        # ApplicationServiceContainer의 비즈니스 서비스 활용
        # 독립적인 MVP 단위 생성
```

### 3. **테스트 용이성**

```python
# 각 Container별 독립적 테스트 가능
def test_presentation_container():
    """PresentationContainer만 테스트"""

def test_mvp_container():
    """MVP Container만 테스트"""

def test_integration():
    """전체 Container 통합 테스트"""
```

---

## 🔧 구현 순서 및 마이그레이션

### Phase 1: PresentationContainer 생성

1. **새 파일 생성**: `presentation/presentation_container.py`
2. **UI Providers 이전**: 백업본의 UI Layer Providers를 PresentationContainer로 이전
3. **의존성 설정**: External + Application Container 참조 설정

### Phase 2: MVP Container 수정

1. **Import 경로 수정**: `application.container` → `application_service_container`
2. **PresentationContainer 연동**: 필요시 UI 서비스 접근 경로 추가
3. **기능 검증**: 기존 MVP 생성 기능 정상 동작 확인

### Phase 3: DILifecycleManager 확장

1. **PresentationContainer 추가**: 3-Container 관리로 확장
2. **의존성 주입**: Container 간 참조 설정
3. **통합 Wiring**: 전체 시스템 @inject 활성화

---

## 📋 최종 파일 구조

```
upbit_auto_trading/
├── infrastructure/
│   └── dependency_injection/
│       ├── external_dependency_container.py     # Infrastructure Layer
│       └── di_lifecycle_manager.py              # 전체 Container 관리
├── application/
│   └── application_service_container.py         # Business Logic Layer
└── presentation/
    ├── presentation_container.py                # UI Layer (새로 생성)
    └── mvp_container.py                         # MVP 조합 관리 (기존 수정)
```

---

## 🎯 핵심 차이점 요약

### **PresentationContainer vs MVP Container**

| 구분 | PresentationContainer | MVP Container |
|------|----------------------|---------------|
| **목적** | UI Layer DI 관리 | MVP 패턴 조합 |
| **범위** | MainWindow + UI Services | Feature별 Presenter-View |
| **생성물** | Provider (DI 서비스) | MVP 조합 (Presenter + View) |
| **의존성** | 3-Container 모두 참조 | 주로 Application Container |
| **생명주기** | DILifecycleManager 관리 | 필요시 생성 |
| **확장성** | UI 서비스 추가 | 새 화면 MVP 추가 |

### **핵심 협력 패턴**

1. **PresentationContainer**: "UI에 필요한 모든 서비스를 제공한다"
2. **MVP Container**: "각 화면의 MVP 조합을 만든다"
3. **함께 작동**: MVP Container가 PresentationContainer의 서비스를 활용하여 완전한 MVP 생성

---

> **💡 핵심 메시지**:
>
> **PresentationContainer**는 "UI Layer의 DI 컨테이너"로서 모든 UI 관련 서비스와 MainWindow Presenter를 제공하고,
>
> **MVP Container**는 "각 화면별 MVP 조합 Factory"로서 Presenter와 View를 생성하여 연결하는 역할을 합니다.
>
> 둘은 **상호 보완적**으로 작동하여 완전한 UI 아키텍처를 구성합니다!

---

**문서 유형**: Container 아키텍처 설계 문서
**작성일**: 2025년 10월 1일
**연관 태스크**: TASK_20251001_04
