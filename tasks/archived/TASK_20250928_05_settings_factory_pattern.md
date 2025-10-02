# 📋 TASK_20250928_05: SettingsViewFactory 패턴 도입 및 컴포넌트 생성 책임 분리

## 🎯 태스크 목표

- **주요 목표**: Settings Screen의 Factory 패턴 부재 위반 해결 및 컴포넌트 생성 책임 완전 분리
- **완료 기준**: SettingsViewFactory 도입으로 View에서 하위 컴포넌트 생성 로직 완전 제거
- **우선순위**: High (P1) - 자동 분석 도구 검증에서 새로 발견된 설계 패턴 위반

## 🚨 해결 대상 위반사항

### 위반 내용

- **위반 ID**: V20250928_052
- **위반 건수**: 1건 (High) - 하지만 광범위한 영향
- **발견 과정**: 자동 분석 도구 검증 중 수동 발견 (구조적 설계 문제)
- **위반 영역**: `settings_screen.py`의 모든 lazy initialization 메서드들
  - `_initialize_api_settings()`
  - `_initialize_database_settings()`
  - `_initialize_ui_settings()`
  - `_initialize_logging_management()`
  - `_initialize_notification_settings()`
  - `_initialize_environment_profile()`

### 근본 원인

1. **책임 분산**: View가 UI 표시 + 하위 컴포넌트 생성까지 담당
2. **확장성 부족**: 새 컴포넌트 추가 시 View 수정 필요
3. **재사용성 저하**: 동일한 생성 로직이 여러 곳에 중복
4. **테스트 어려움**: 컴포넌트 생성 로직을 독립적으로 테스트할 수 없음

## ✅ 해결 체크리스트

### Phase 1: Factory 패턴 설계 및 인터페이스 정의 (2시간)

- [ ] **SettingsComponentFactory 인터페이스 설계**
  - [ ] `ISettingsComponentFactory` 프로토콜 정의
  - [ ] 각 설정 컴포넌트별 생성 메서드 시그니처 정의
  - [ ] 설정 타입별 팩토리 분류 (API, Database, UI, Logging, Notification, Environment)

- [ ] **컴포넌트 생성 전략 수립**
  - [ ] Eager Loading vs Lazy Loading 전략 재정의
  - [ ] 컴포넌트 간 의존성 관리 방안
  - [ ] 생성 실패 시 폴백 전략

- [ ] **Factory 레지스트리 설계**
  - [ ] 컴포넌트 타입별 Factory 등록 메커니즘
  - [ ] 런타임 Factory 교체 가능성 (테스트용 Mock Factory)
  - [ ] Factory 생명주기 관리

### Phase 2: SettingsViewFactory 구현 (3시간)

- [ ] **메인 SettingsViewFactory 클래스 구현**
  - [ ] DI 컨테이너와 연동하여 완전히 구성된 컴포넌트 생성
  - [ ] 각 설정 타입별 전용 생성 메서드 구현
  - [ ] 컴포넌트 간 의존성 자동 해결

- [ ] **하위 컴포넌트 Factory들 구현**
  - [ ] `ApiSettingsComponentFactory`
  - [ ] `DatabaseSettingsComponentFactory`
  - [ ] `UiSettingsComponentFactory`
  - [ ] `LoggingSettingsComponentFactory`
  - [ ] `NotificationSettingsComponentFactory`
  - [ ] `EnvironmentProfileComponentFactory`

- [ ] **Factory 조합 및 통합**
  - [ ] 여러 Factory를 조합하여 완전한 Settings View 생성
  - [ ] 컴포넌트 초기화 순서 관리
  - [ ] 부분 실패 시 복구 메커니즘

### Phase 3: SettingsScreen 리팩터링 (2.5시간)

- [ ] **하위 컴포넌트 생성 로직 완전 제거**
  - [ ] `_initialize_api_settings()` 메서드 제거 또는 단순화
  - [ ] `_initialize_database_settings()` 메서드 제거 또는 단순화
  - [ ] `_initialize_ui_settings()` 메서드 제거 또는 단순화
  - [ ] 기타 모든 `_initialize_*()` 메서드들 처리

- [ ] **Factory 기반 컴포넌트 주입**
  - [ ] 생성자에 `SettingsViewFactory` 주입
  - [ ] Factory를 통한 하위 컴포넌트 요청 및 설정
  - [ ] View는 순수하게 UI 구성 및 이벤트 처리만 담당

- [ ] **탭 전환 로직 개선**
  - [ ] `_on_tab_changed()` 메서드에서 Factory 활용
  - [ ] 필요 시에만 컴포넌트 생성 (진정한 Lazy Loading)
  - [ ] 탭별 로딩 상태 관리

### Phase 4: 의존성 주입 설정 업데이트 (1시간)

- [ ] **ApplicationContainer에 Factory 등록**
  - [ ] `SettingsViewFactory` 및 모든 하위 Factory들 바인딩
  - [ ] Factory들이 필요한 서비스 의존성 주입 설정
  - [ ] Singleton vs Factory 생명주기 정책 수립

- [ ] **MVPContainer와 Factory 연동**
  - [ ] MVPContainer에서 Factory를 활용한 View 생성
  - [ ] Factory 기반 MVP 조합 로직
  - [ ] 기존 `create_settings_mvp()` 메서드 Factory 활용으로 개선

### Phase 5: 테스트 및 검증 (1.5시간)

- [ ] **Factory 패턴 동작 검증**
  - [ ] 각 Factory가 올바른 컴포넌트를 생성하는지 확인
  - [ ] Factory 간 의존성이 올바르게 해결되는지 검증
  - [ ] Mock Factory를 통한 테스트 가능성 확인

- [ ] **기능 무결성 테스트**
  - [ ] `python run_desktop_ui.py` 실행하여 모든 설정 탭 정상 동작 확인
  - [ ] 탭 전환 시 컴포넌트 생성이 올바르게 동작하는지 검증
  - [ ] 메모리 사용량 및 성능 영향 측정

- [ ] **아키텍처 준수성 검증**
  - [ ] View에서 컴포넌트 직접 생성하는 코드 완전 제거 확인
  - [ ] Factory 패턴이 올바르게 적용되었는지 검증
  - [ ] SRP(Single Responsibility Principle) 준수 확인

## 🛠️ 구체적 구현 방법론

### 1. Factory 인터페이스 설계

```python
# interfaces/settings_factory_interface.py
from typing import Protocol, Optional
from PyQt6.QtWidgets import QWidget

class ISettingsComponentFactory(Protocol):
    """Settings 컴포넌트 생성을 담당하는 Factory 인터페이스"""

    def create_api_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """API 설정 컴포넌트 생성"""
        ...

    def create_database_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """데이터베이스 설정 컴포넌트 생성"""
        ...

    def create_ui_settings_component(self, parent: Optional[QWidget] = None) -> QWidget:
        """UI 설정 컴포넌트 생성"""
        ...

    # ... 기타 컴포넌트들
```

### 2. 메인 Factory 구현

```python
# factories/settings_view_factory.py
class SettingsViewFactory:
    """Settings View와 관련된 모든 컴포넌트를 생성하는 메인 Factory"""

    @inject
    def __init__(self,
                 mvp_container=Provide["mvp_container"],
                 api_settings_factory=Provide["api_settings_factory"],
                 database_factory=Provide["database_settings_factory"],
                 # ... 기타 Factory들
                 ):
        self._mvp_container = mvp_container
        self._api_factory = api_settings_factory
        self._database_factory = database_factory
        # ...

    def create_fully_configured_settings_screen(self, parent=None) -> SettingsScreen:
        """완전히 구성된 Settings Screen 생성"""

        # 1. View 먼저 생성 (컴포넌트 생성 로직 없이)
        settings_screen = SettingsScreen(parent=parent, factory=self)

        # 2. 필요한 경우에만 하위 컴포넌트 생성 및 설정
        # (Lazy loading 또는 즉시 초기화 정책에 따라)

        return settings_screen

    def create_api_settings_component(self, parent=None):
        """API 설정 컴포넌트를 완전히 구성된 상태로 생성"""
        return self._api_factory.create_component(parent)

    # ... 기타 컴포넌트 생성 메서드들
```

### 3. SettingsScreen 리팩터링

```python
# settings_screen.py 수정
class SettingsScreen(QWidget):
    @inject
    def __init__(self,
                 parent=None,
                 factory=Provide["settings_view_factory"]):
        super().__init__(parent)
        self._factory = factory

        # ✅ 컴포넌트 생성 로직 없음, 순수하게 UI 구성만
        self._setup_ui()
        self._setup_tabs()

        # 초기화된 컴포넌트들을 저장할 딕셔너리
        self._components = {}

    def _on_tab_changed(self, index: int):
        """탭 변경 시 필요한 컴포넌트만 Factory에서 생성"""
        tab_name = self.tabs.tabText(index)

        if tab_name not in self._components:
            # ✅ Factory를 통해 컴포넌트 생성
            component = self._factory.create_component_by_name(tab_name, parent=self)
            self._components[tab_name] = component

            # 탭에 컴포넌트 추가
            self.tabs.widget(index).layout().addWidget(component)

    # ❌ 제거된 메서드들
    # def _initialize_api_settings(self): 제거
    # def _initialize_database_settings(self): 제거
    # ... 기타 _initialize_* 메서드들 제거
```

### 4. 타입별 하위 Factory 예시

```python
# factories/api_settings_component_factory.py
class ApiSettingsComponentFactory:
    """API 설정 관련 컴포넌트들을 생성하는 전용 Factory"""

    @inject
    def __init__(self,
                 mvp_container=Provide["mvp_container"],
                 api_service=Provide["api_service"]):
        self._mvp_container = mvp_container
        self._api_service = api_service

    def create_component(self, parent=None):
        """완전히 구성된 API 설정 컴포넌트 생성"""

        # 1. View 생성
        api_view = ApiSettingsView(parent)

        # 2. Presenter 생성 및 연결
        api_presenter = self._mvp_container.create_api_settings_presenter()
        api_view.set_presenter(api_presenter)

        # 3. 필요한 서비스 연결
        api_presenter.set_api_service(self._api_service)

        return api_view
```

## 🎯 완료 기준

### 필수 완료 사항

- [ ] **Factory 패턴 완전 적용**: Settings Screen의 모든 컴포넌트 생성이 Factory를 통해 수행
- [ ] **View 책임 순수화**: SettingsScreen이 순수하게 UI 표시만 담당
- [ ] **확장성 확보**: 새 설정 컴포넌트 추가 시 Factory만 확장하면 됨
- [ ] **테스트 용이성**: Mock Factory를 통한 단위 테스트 가능

### 성공 지표

- [ ] `grep -r "_initialize_.*settings" settings_screen.py` 결과 0건 또는 Factory 호출만 존재
- [ ] Factory를 통하지 않은 컴포넌트 직접 생성 코드 0건
- [ ] Settings Screen 단위 테스트에서 Mock Factory 활용 가능
- [ ] 새 설정 탭 추가 시 SettingsScreen 코드 수정 불필요

## 📊 예상 소요시간 및 리소스

- **총 예상시간**: 10시간
- **필요 기술**: Factory 패턴, 의존성 주입, 컴포넌트 설계
- **전제 조건**: MVP 패턴과 DI 시스템 이해

## 📋 위험 요소 및 대응

### 주요 위험

1. **과도한 추상화**: Factory 패턴 남용으로 인한 코드 복잡성 증가
   - **대응**: 필요한 곳에만 적절한 수준의 추상화 적용
   - **검증**: 코드 가독성 및 유지보수성 정기 리뷰

2. **성능 오버헤드**: Factory를 통한 컴포넌트 생성으로 인한 성능 저하
   - **대응**: 적절한 캐싱 및 Lazy Loading 전략
   - **모니터링**: 컴포넌트 생성 시간 측정

3. **의존성 복잡성**: Factory 간 복잡한 의존성으로 인한 관리 어려움
   - **대응**: 명확한 의존성 그래프 및 문서화
   - **검증**: DI 컨테이너 초기화 테스트

## 🚀 시작 방법

```powershell
# 1. 현재 컴포넌트 생성 패턴 분석
Get-ChildItem upbit_auto_trading\ui\desktop\screens\settings -Include settings_screen.py | Select-String -Pattern "_initialize_.*settings"

# 2. Git 브랜치 생성
git checkout -b feature/settings-view-factory-pattern

# 3. Phase 1부터 순차 진행
# - Factory 인터페이스 설계
# - 메인 Factory 구현
# - SettingsScreen 리팩터링

# 4. 검증
python run_desktop_ui.py
# 모든 설정 탭 정상 동작 확인
```

## 📋 관련 문서

- **발견 과정**: `docs/architecture_review/mvp_pattern_review/settings_screen/2025-09-28_automated_tool_validation_report.md`
- **위반 등록**: `docs/architecture_review/violation_registry/active_violations.md` (V20250928_052)
- **Factory 패턴 가이드**: `docs/DESIGN_PATTERNS.md` (작성 필요)
- **MVP 가이드**: `docs/MVP_ARCHITECTURE.md`
- **기본 태스크**: `tasks/active/TASK_20250928_01-settings_screen_mvp_review.md` (검증 완료)

## 🎯 태스크 1과의 연관성

이 태스크는 **태스크 1의 자동 분석 도구 유용성 검증** 과정에서 발견된 구조적 설계 문제를 해결합니다:

- **검증 결과**: 자동 도구가 Factory 패턴 부재를 탐지하지 못함
- **수동 발견**: View의 **과도한 책임**과 **확장성 부족** 문제 식별
- **설계 개선**: Factory 패턴 도입으로 **관심사 분리** 및 **확장성** 확보
- **완전성 달성**: 이 태스크 완료로 Settings Screen의 **완전한 객체지향 설계** 구현

## 🔗 다른 태스크와의 관계

- **TASK_04와 병렬 진행**: DI 패턴과 Factory 패턴이 상호 보완적 관계
- **TASK_02, 03 선행**: Infrastructure 접근과 UI 조작 위반 해결 후 진행 권장
- **시너지 효과**: 모든 태스크 완료 시 **완전한 MVP + DDD + Factory 패턴** 달성

---

**시작일**: 2025-09-28
**목표 완료일**: 2025-10-10
**우선순위**: High (P1)
**담당자**: TBD
**선행 태스크**: TASK_20250928_01 (완료), TASK_20250928_02/03 (권장)
