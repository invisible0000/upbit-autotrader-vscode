# 📋 TASK_20251001_04: 완전한 Container 아키텍처 재구축 - 3-Container 통합 시스템

## 🎯 태스크 목표

### 주요 목표

**TASK_20251001_03 완전 분석 결과를 바탕으로 기존 장점과 신규 장점을 융합한 완벽한 3-Container 아키텍처 구축**

- **백업본의 통합 장점 보존**: 모든 UI 기능 완전 작동, 검증된 안정성
- **신규본의 구조 장점 활용**: 명확한 네이밍, Container 책임 분리, 개선된 아키텍처
- **3-Container 시스템 완성**: External(Infrastructure) + Application(Business) + Presentation(UI) Layer 완전 지원
- **유기적 연결 체계**: 모든 Container가 DILifecycleManager를 통해 통합 관리되는 완벽한 DI 시스템

### 완료 기준

- ✅ **ExternalDependencyContainer**: Infrastructure Layer 전담, 기존 기능 보존
- ✅ **ApplicationServiceContainer**: Business Logic Layer 전담, 기존 기능 보존
- ✅ **PresentationContainer**: UI Layer 전담, 백업본 UI Providers 완전 복원
- ✅ **DILifecycleManager**: 3-Container 통합 관리 및 유기적 연결 체계 완성
- ✅ **MVP Container**: Import 경로 수정 및 3-Container 연동 지원
- ✅ **MainWindow**: 완전한 기능 복구 (화면 전환, 메뉴, 네비게이션, 상태 관리)
- ✅ **7규칙 전략**: 트리거 빌더에서 전략 구성 기능 무결성 유지

---

## 📊 현재 상황 분석 (TASK_20251001_03 완전 분석 결과)

### 🎯 **핵심 문제점 (완전 규명됨)**

#### 1. **UI Layer 담당 Container 부재** (치명적)

```
백업본: ApplicationContainer (Infrastructure + Application + UI 통합 관리) ✅
신규본: ExternalDependencyContainer (Infrastructure만) + ApplicationServiceContainer (Business만) ❌
결과: UI Layer Providers 완전 누락 → MainWindow 모든 기능 실패
```

#### 2. **Provider 매트릭스 분석 결과**

| Provider명 | 백업본 | 신규본 | 영향도 | 필요 작업 |
|------------|--------|--------|--------|-----------|
| **main_window_presenter** | ✅ Factory + services Dict | ❌ 완전 누락 | 🔥 치명적 | PresentationContainer에 완전 복원 |
| **screen_manager_service** | ✅ Factory + app_container | ❌ 완전 누락 | 🔥 치명적 | 3-Container 연동 구조 |
| **window_state_service** | ✅ Factory | ❌ 완전 누락 | 🔴 높음 | Provider 정의 |
| **menu_service** | ✅ Factory | ❌ 완전 누락 | 🔴 높음 | Provider 정의 |
| **navigation_service** | ✅ Factory | ❌ 완전 누락 | 🟡 중간 | Widget Factory |
| **status_bar_service** | ✅ Factory + DB Health | ❌ 완전 누락 | 🟡 중간 | Provider + 의존성 체인 |

#### 3. **Import 체인 단절**

```
현재 실패 체인:
mvp_container.py → from application.container import (존재하지 않음!) → ImportError
→ MVP 시스템 전체 초기화 불가 → 모든 Presenter 생성 실패

올바른 체인:
mvp_container.py → from application_service_container import → ApplicationServiceContainer
→ MVP 시스템 정상 초기화 → Presenter 생성 가능
```

#### 4. **DI 실행 흐름 단절**

```
백업본 성공 흐름:
run_desktop_ui.py → ApplicationContext → ApplicationContainer → main_window_presenter Provider
→ services Dict 주입 → 모든 UI Services 정상 작동

신규본 실패 흐름:
run_desktop_ui.py → DILifecycleManager → ExternalDependencyContainer → main_window_presenter 없음!
→ MainWindow() 직접 생성 → @inject 실패 → 모든 UI Services None
```

### 🎯 **신규 구조의 장점 (보존해야 할 가치)**

1. **명확한 네이밍**: ExternalDependencyContainer, DILifecycleManager 등 역할이 명확
2. **Container 책임 분리**: Infrastructure와 Application Logic의 명확한 구분
3. **확장 가능한 구조**: 각 Layer별로 독립적 확장 가능
4. **아키텍처 일관성**: DDD 원칙에 부합하는 계층별 분리

### 🎯 **백업본의 장점 (복원해야 할 기능)**

1. **완전한 UI 지원**: 모든 UI Providers가 통합 관리됨
2. **검증된 안정성**: 실제 동작하는 완전한 DI 체계
3. **유기적 연결**: 모든 서비스가 하나의 Container에서 조화롭게 동작
4. **MVP 패턴 완성**: Presenter와 View의 완벽한 의존성 주입

---

## 🔄 체계적 작업 절차 (필수 준수)

### 8단계 작업 절차

1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **🔄 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커

- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

---

## 📋 작업 계획 - 3-Container 아키텍처 완성

### Phase 1: PresentationContainer 생성 및 UI Layer Providers 복원 (예상 시간: 2시간)

#### 1.1 PresentationContainer 새로 생성

- [x] **안전 백업 생성**
  - ✅ ExternalDependencyContainer 백업: external_dependency_container_backup_task04.py
  - ✅ ApplicationServiceContainer 백업: application_service_container_backup_task04.py
  - ✅ MVP Container 백업: mvp_container_backup_task04.py
  - ✅ DILifecycleManager 백업: di_lifecycle_manager_backup_task04.py
  - ✅ 모든 핵심 Container 파일 안전하게 백업 완료

- [x] **PresentationContainer 클래스 생성**
  - ✅ `upbit_auto_trading/presentation/presentation_container.py` 새 파일 생성 완료
  - ✅ DDD Architecture 기반 Presentation Layer 전담 Container 설계
  - ✅ dependency-injector 패턴으로 UI Providers 전용 Container 구현
  - ✅ External/Application Container 의존성 주입 체계 구축
  - ✅ 백업본 UI Layer Providers 패턴 완벽 복원

#### 1.2 UI Layer Providers 완전 복원

- [x] **Navigation & Status Bar Providers**
  - ✅ NavigationBar Service Provider 정의 완료 (Widget Factory 패턴)
  - ✅ StatusBar Service Provider 정의 + DatabaseHealthService 의존성 주입 완료
  - ✅ UI Infrastructure 기반 서비스 완전 복원 (백업본과 동일)

- [x] **Application Services Providers (UI 연동용)**
  - ✅ ScreenManagerService Provider 정의 완료 (ApplicationServiceContainer 의존성 - 백업본과 동일)
  - ✅ WindowStateService Provider 정의 완료 (순수 UI 상태 관리)
  - ✅ MenuService Provider 정의 완료 (UI 메뉴 관리)

- [x] **MainWindowPresenter Provider 완전 복원**
  - ✅ services Dict 패턴으로 모든 필요 서비스 주입 구조 구현 완료
  - ✅ ThemeService(External), DatabaseHealthService, NavigationBar, ApiKeyService(External) 연결 완료
  - ✅ ScreenManager, WindowState, Menu 서비스 완전 주입 완료
  - ✅ 백업본과 동일한 서비스 주입 체계 구현 (순서 및 패턴 일치)
  - ⚠️ MainWindowPresenter Import 문제는 Phase 3에서 해결 예정

### Phase 2: DILifecycleManager 3-Container 통합 관리 구현 (예상 시간: 1.5시간)

#### 2.1 3-Container 초기화 체계 구축

- [x] **DILifecycleManager 확장**
  - ✅ ExternalDependencyContainer (Infrastructure Layer) 기존 유지
  - ✅ ApplicationServiceContainer (Business Logic Layer) 기존 유지
  - ✅ PresentationContainer (UI Layer) 새로 추가 초기화 및 관리 완료
  - ✅ 3-Container 통합 초기화 프로세스 구현 완료
  - ✅ get_presentation_container(), get_main_window_presenter() 메서드 추가

- [x] **Container 간 의존성 주입 체계**
  - ✅ PresentationContainer가 External + Application Container 참조 완료
  - ✅ 순환 참조 방지를 위한 Dependency Injection 패턴 적용 완료
  - ✅ create_presentation_container Factory 패턴으로 동적 연결 완료
  - ✅ Container 간 의존성 주입 검증 체계 구현

#### 2.2 통합 Wiring 시스템 구현

- [x] **3-Container Wiring 설정**
  - ✅ 각 Container별 담당 모듈 명확히 분리하여 Wiring 완료
  - ✅ Infrastructure, Application, Presentation Layer별 @inject 활성화 완료
  - ✅ _wire_presentation_modules() 메서드로 UI Layer Wiring 구현
  - ⚠️ MVP Container import 문제로 전체 시스템 통합 검증은 Phase 3에서 해결

### Phase 3: MVP Container 및 연결 체계 수정 (예상 시간: 1시간)

#### 3.1 MVP Container Import 경로 수정

- [x] **Import 경로 완전 수정**
  - ✅ `from upbit_auto_trading.application.container` → `from upbit_auto_trading.application.application_service_container` 완료
  - ✅ ApplicationServiceContainer 클래스 참조 정상화 완료
  - ✅ MVP 시스템 초기화 완전 성공 - Import 오류 완전 해결

#### 3.2 MVP와 3-Container 연동

- [x] **MVP Container 3-Container 지원**
  - ✅ ApplicationServiceContainer (Business Logic) 접근 완료
  - ✅ PresentationContainer (UI Services) 접근 완료
  - ✅ get_application_container, get_presentation_container, set_presentation_container 메서드 구현
  - ✅ MVP 패턴에서 필요한 모든 서비스 접근 경로 완전 구축

### Phase 4: MainWindow 및 실행 흐름 통합 검증 (예상 시간: 1시간)

#### 4.1 MainWindow Provider 연동 검증

- [x] **run_desktop_ui.py 실행 흐름 수정**
  - ✅ DILifecycleManager → 3-Container → PresentationContainer.main_window_presenter 구조 완성
  - ✅ MainWindow @inject 패턴 적용: 외부 서비스 자동 주입, Presenter 직접 가져오기 제거
  - ✅ MVP 패턴 올바른 구조: Presenter ↔ View 상호 연결, DI 서비스 자동 주입
  - ✅ 에러 숨김 제거: 폴백 로직 제거, 구조적 문제 시 애플리케이션 종료로 명확한 오류 드러내기
  - ✅ 지연 초기화 패턴 적용: MainWindow.complete_initialization() 메서드로 Presenter 설정 후 완전 초기화
  - ✅ @inject Wiring 문제 해결: ExternalDependencyContainer에 MainWindow 모듈 추가하여 DI 정상 작동
  - ✅ **근본적 구조 문제 해결 완료**:
    - 🔧 Dependency Injection 패턴 수정: .provided → .provider 패턴으로 실제 인스턴스 주입
    - 🔧 Async/Sync 패턴 정리: MainWindowPresenter에서 동기 메서드만 사용하도록 수정
    - 🔧 Wiring 모듈 정리: 존재하지 않는 'upbit_auto_trading.ui.desktop.views' 모듈 제거
    - 🔧 Defensive Programming: API 서비스 호출 시 Factory Provider 객체 문제 방지
  - ⚠️ 최종 검증 필요: 모든 근본적 문제 해결 후 시스템 안정성 확인

#### 4.2 전체 UI 기능 검증

- [ ] **MainWindow 완전 기능 테스트**
  - 화면 전환 (chart_view, settings_view 등) 정상 동작 확인
  - 메뉴 기능 및 네비게이션 완전 작동 확인
  - 창 상태 저장/복원, 상태바 표시 정상 동작 확인
  - 모든 경고 메시지 해결 확인

### Phase 5: 7규칙 전략 무결성 및 최종 시스템 검증 (예상 시간: 30분)

#### 5.1 7규칙 전략 구성 기능 검증

- [ ] **트리거 빌더 완전 검증**
  - 전략 관리 화면 정상 접근 확인
  - 7규칙 전략 구성 기능 무결성 확인 (RSI 과매도, 수익시 불타기, 익절, 트레일링 스탑, 물타기, 급락/급등 감지)
  - 설정 화면 API 키 관리 기능 정상 동작 확인

#### 5.2 전체 시스템 안정성 검증

- [ ] **3-Container 아키텍처 무결성 확인**
  - 각 Container의 책임 분리 원칙 준수 확인
  - DDD 계층 위반 없음 검증 (PowerShell 스크립트)
  - 전체 DI 시스템 메모리 누수 및 성능 확인

---

## 🛠️ 구체적 구현 방안

### 🔧 PresentationContainer 구현 패턴

```python
"""
Presentation Container - UI Layer 전담 DI 컨테이너
Clean Architecture Presentation Layer의 모든 UI 서비스를 중앙 관리
"""

from dependency_injector import containers, providers
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("PresentationContainer")

class PresentationContainer(containers.DeclarativeContainer):
    """
    Presentation Layer 전담 DI 컨테이너

    UI Services Management:
    - MainWindow Presenter (MVP 패턴 핵심)
    - Application UI Services (Screen, Window, Menu)
    - UI Infrastructure (Navigation, StatusBar)
    - Theme & Style Management (UI 일관성)

    External Dependencies:
    - ExternalDependencyContainer (Infrastructure 서비스)
    - ApplicationServiceContainer (Business 서비스)
    """

    # Configuration
    config = providers.Configuration()

    # External Container Dependencies (주입받을 예정)
    external_container = providers.Dependency()
    application_container = providers.Dependency()

    # =============================================================================
    # UI Infrastructure Providers
    # =============================================================================

    # Navigation Bar Service
    navigation_service = providers.Factory(
        "upbit_auto_trading.ui.desktop.common.widgets.navigation_bar.NavigationBar"
    )

    # Status Bar Service (DatabaseHealthService 의존성)
    status_bar_service = providers.Factory(
        "upbit_auto_trading.ui.desktop.common.widgets.status_bar.StatusBar",
        database_health_service=providers.Factory(
            "upbit_auto_trading.application.services.database_health_service.DatabaseHealthService"
        )
    )

    # =============================================================================
    # Application UI Services Providers
    # =============================================================================

    # Screen Manager Service (ApplicationServiceContainer 연동)
    screen_manager_service = providers.Factory(
        "upbit_auto_trading.application.services.screen_manager_service.ScreenManagerService",
        application_container=application_container
    )

    # Window State Service
    window_state_service = providers.Factory(
        "upbit_auto_trading.application.services.window_state_service.WindowStateService"
    )

    # Menu Service
    menu_service = providers.Factory(
        "upbit_auto_trading.application.services.menu_service.MenuService"
    )

    # =============================================================================
    # MainWindow Presenter - MVP 패턴 완전 구현
    # =============================================================================

    # MainWindowPresenter (백업본과 동일한 services Dict 패턴)
    main_window_presenter = providers.Factory(
        "upbit_auto_trading.presentation.presenters.main_window_presenter.MainWindowPresenter",
        services=providers.Dict(
            # Infrastructure Services (ExternalDependencyContainer에서)
            theme_service=external_container.provided.theme_service,
            api_key_service=external_container.provided.api_key_service,

            # Application Services (현재 Container에서)
            screen_manager_service=screen_manager_service,
            window_state_service=window_state_service,
            menu_service=menu_service,

            # UI Infrastructure (현재 Container에서)
            navigation_bar=navigation_service,
            database_health_service=providers.Factory(
                "upbit_auto_trading.application.services.database_health_service.DatabaseHealthService"
            )
        )
    )
```

### 🔧 DILifecycleManager 3-Container 통합 패턴

```python
class DILifecycleManager:
    """3-Container 통합 관리자"""

    def __init__(self):
        self._external_container = None
        self._application_container = None
        self._presentation_container = None
        self._is_initialized = False

    def initialize(self):
        """3-Container 순차 초기화 및 연동"""

        # 1. ExternalDependencyContainer (Infrastructure)
        self._external_container = create_external_dependency_container()

        # 2. ApplicationServiceContainer (Business Logic)
        repository_container = self._external_container.repository_container()
        self._application_container = ApplicationServiceContainer(repository_container)

        # 3. PresentationContainer (UI Layer)
        self._presentation_container = PresentationContainer()

        # Container 간 의존성 주입
        self._presentation_container.external_container.override(self._external_container)
        self._presentation_container.application_container.override(self._application_container)

        # 통합 Wiring
        self._wire_all_containers()

        self._is_initialized = True

    def get_main_window_presenter(self):
        """MainWindow Presenter 조회 (run_desktop_ui.py에서 사용)"""
        if not self._is_initialized:
            raise RuntimeError("DILifecycleManager 초기화 필요")

        return self._presentation_container.main_window_presenter()
```

### 🔧 run_desktop_ui.py 수정 패턴

```python
# 기존: MainWindow() 직접 생성 (실패)
self.main_window = MainWindow()

# 수정: PresentationContainer Provider 사용 (성공)
if self.di_manager:
    presenter = self.di_manager.get_main_window_presenter()
    # MainWindow는 Presenter가 생성하거나, Presenter와 연결된 View 패턴 사용
    self.main_window = presenter.get_view()  # 또는 적절한 View 생성 패턴
```

---

## 🎯 성공 기준

### ✅ 아키텍처 성공 기준

1. **3-Container 완전 분리**: 각 Container가 명확한 책임만 담당
   - ExternalDependencyContainer: Infrastructure Layer 전담
   - ApplicationServiceContainer: Business Logic Layer 전담
   - PresentationContainer: UI Layer 전담

2. **유기적 연결 완성**: DILifecycleManager를 통한 3-Container 통합 관리
   - Container 간 의존성 주입 체계 완성
   - 순환 참조 없는 안전한 연결 구조
   - 전체 시스템 일관성 유지

### ✅ 기능적 성공 기준

1. **MainWindow 완전 복구**: 모든 UI 기능이 백업본 수준으로 복원
   - 화면 전환 (chart_view, settings_view 등) 정상 동작
   - 메뉴, 네비게이션, 상태바 완전 기능
   - 창 상태 관리 (저장/복원) 정상 동작
   - 모든 경고 메시지 완전 해결

2. **7규칙 전략 무결성**: 트리거 빌더에서 전략 구성 완전 작동
   - RSI 과매도 진입, 수익시 불타기, 계획된 익절
   - 트레일링 스탑, 하락시 물타기, 급락/급등 감지
   - 모든 규칙의 조합 및 실행 가능 확인

### ✅ 기술적 성공 기준

1. **DI 시스템 무결성**: @inject 데코레이터와 Provider 체계 완전 작동
2. **MVP 패턴 완성**: Presenter-View 의존성 주입 정상 동작
3. **Import 체계 완성**: 모든 모듈이 올바른 경로로 참조됨
4. **메모리 안정성**: Container 순환 참조 없음, 정상적인 생명주기 관리

---

## 💡 작업 시 주의사항

### 아키텍처 원칙

- **DDD 계층 준수**: Domain Layer 순수성 절대 보장
- **Container 책임 분리**: 각 Container의 명확한 역할 유지
- **의존성 방향 준수**: Presentation → Application → Infrastructure 방향
- **순환 참조 금지**: Self 참조와 Dependency Injection으로 해결

### 안전성 원칙

- **점진적 구현**: 각 Phase별로 기능 확인 후 다음 단계 진행
- **백업 필수**: 모든 수정 전 백업 파일 생성
- **롤백 준비**: 문제 발생 시 즉시 복구 가능한 상태 유지
- **검증 철저**: 각 Container별로 독립적 검증 후 통합 검증

---

## 🚀 즉시 시작할 작업

### 1단계: 현재 상태 백업 및 PresentationContainer 기본 구조 (30분)

```powershell
# 전체 Container 파일 백업 생성
Copy-Item "upbit_auto_trading\infrastructure\dependency_injection\external_dependency_container.py" "upbit_auto_trading\infrastructure\dependency_injection\external_dependency_container_backup_task04.py"
Copy-Item "upbit_auto_trading\application\application_service_container.py" "upbit_auto_trading\application\application_service_container_backup_task04.py"
Copy-Item "upbit_auto_trading\presentation\mvp_container.py" "upbit_auto_trading\presentation\mvp_container_backup_task04.py"

# PresentationContainer 파일 생성 준비
New-Item -Path "upbit_auto_trading\presentation" -Name "presentation_container.py" -ItemType "File"
```

### 2단계: 백업본에서 UI Layer Providers 패턴 추출 (15분)

```powershell
# UI Layer Providers 섹션 전체 추출
Get-Content "upbit_auto_trading\infrastructure\dependency_injection\container_backup_20251001.py" -Encoding UTF8 | Select-String -Pattern "UI Layer Providers" -Context 50

# MainWindowPresenter services Dict 패턴 상세 추출
Get-Content "upbit_auto_trading\infrastructure\dependency_injection\container_backup_20251001.py" -Encoding UTF8 | Select-String -Pattern "main_window_presenter.*=.*providers\.Factory" -Context 15
```

### 3단계: 즉시 검증 환경 확인 (5분)

```powershell
# 현재 UI 실행하여 문제 상태 확인
python run_desktop_ui.py
# 예상 결과: MainWindow 기능 실패 메시지들 확인

# DI 시스템 상태 확인
python -c "
from upbit_auto_trading.infrastructure.dependency_injection import get_di_lifecycle_manager
manager = get_di_lifecycle_manager()
print(f'DI Manager 초기화: {manager.is_initialized}')
print(f'External Container: {manager.get_external_container() is not None}')
print(f'Application Container: {manager.get_application_container() is not None}')
"
```

---

## 🔗 연관 태스크

### 선행 태스크

- **TASK_20251001_02**: 컨테이너 파일명 직접 변경 (문제 발생 원인)
- **TASK_20251001_03**: 컨테이너 구조 변경 전후 비교 진단 및 문제점 분석 (✅ **완전 완료** - 모든 원인 규명)

### 후속 태스크 계획

- **TASK_20251001_05**: 3-Container 아키텍처 성능 최적화 및 확장성 검증
- **TASK_20251001_06**: Container 기반 테스트 자동화 시스템 구축

---

## 📚 참고 문서

### 기술 참고 자료

- **TASK_20251001_03 완전 분석**: Provider 매트릭스, Import 체인 다이어그램, DI 실행 흐름 완전 분석 결과
- **백업 파일들**: 검증된 UI Layer Providers 패턴과 성공적인 DI 체계
- **.github/copilot-instructions.md**: DDD 아키텍처 및 3-Container 시스템 가이드라인

### 아키텍처 설계 원칙

- **Clean Architecture**: Presentation → Application → Domain ← Infrastructure
- **DDD 패턴**: 계층별 책임 분리 및 의존성 역전 원칙
- **MVP 패턴**: Presenter-View 분리 및 의존성 주입 체계
- **Container 패턴**: 각 Layer별 DI Container 전담 관리

---

**문서 유형**: 완전한 Container 아키텍처 재구축 태스크
**우선순위**: 🔥 최고 (시스템 안정성 + 아키텍처 완성도)
**예상 소요 시간**: 6-7시간 (안전하고 완전한 구현)
**접근 방식**: 기존 장점 + 신규 장점 융합 → 3-Container 완전 시스템

---

> **💡 핵심 메시지**: "백업본의 통합 장점과 신규본의 구조 장점을 융합한 완벽한 3-Container 아키텍처!"
>
> **🎯 성공 전략**: 점진적 구현 → 각 Container별 검증 → 통합 시스템 완성!

---

**다음 에이전트 시작점**: Phase 1.1 안전 백업 생성 및 PresentationContainer 기본 구조 생성부터 시작
