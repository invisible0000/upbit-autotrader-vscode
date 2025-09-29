# 📋 TASK_20250928_04: View→Presenter 직접 생성 DI 패턴 위반 해결

## 🎯 태스크 목표

- **주요 목표**: Settings Screen에서 View가 Presenter를 직접 생성하는 Critical DI 패턴 위반 4건 해결
- **완료 기준**: MVPContainer를 통한 완전한 의존성 주입 적용으로 모든 Presenter 생성을 DI 컨테이너에서 관리
- **우선순위**: Critical (P0) - 자동 분석 도구 검증에서 새로 발견된 심각한 아키텍처 위반

## 🚨 해결 대상 위반사항

### 위반 내용

- **위반 ID**: V20250928_051
- **위반 건수**: 4건 (Critical)
- **발견 과정**: 자동 분석 도구 검증 중 수동 발견 (도구가 놓친 심각한 위반)
- **위반 위치**:
  1. `settings_screen.py:98` - `self.main_presenter = SettingsPresenter(...)`
  2. `settings_screen.py:185` - `self.api_settings_presenter = ApiSettingsPresenter(...)`
  3. `settings_screen.py:210` - `self.database_settings_presenter = DatabaseSettingsPresenter(...)`
  4. `settings_screen.py:248` - `self.logging_management_presenter = LoggingManagementPresenter(...)`

### 근본 원인

1. **DI 컨테이너 우회**: MVPContainer가 존재함에도 불구하고 View에서 수동으로 Presenter 생성
2. **테스트 불가능 코드**: Mock 주입이 불가능하여 단위 테스트 작성 어려움
3. **결합도 증가**: View가 Presenter의 구체적 생성자에 직접 의존
4. **일관성 부족**: 일부는 DI, 일부는 수동 생성으로 혼재

## ✅ 해결 체크리스트

### Phase 1: MVPContainer 확장 및 설정 (2시간)

- [ ] **SettingsScreen 전용 MVP 생성 메서드 확장**
  - [ ] `create_settings_screen_mvp()` 메서드 개선
  - [ ] 모든 하위 Presenter들을 사전에 구성된 상태로 주입
  - [ ] Lazy loading 전략 재설계 (완전한 즉시 초기화 vs 완전한 lazy loading)

- [ ] **하위 Presenter들의 DI 설정 추가**
  - [ ] API Settings Presenter DI 바인딩
  - [ ] Database Settings Presenter DI 바인딩
  - [ ] Logging Management Presenter DI 바인딩
  - [ ] UI Settings Presenter DI 바인딩

- [ ] **생명주기 관리 정책 수립**
  - [ ] Singleton vs Transient 정책 결정
  - [ ] 순환 참조 방지 패턴 적용
  - [ ] 초기화 순서 의존성 관리

### Phase 2: SettingsScreen 리팩터링 (3시간)

- [ ] **직접 Presenter 생성 코드 제거**
  - [ ] `line 98`: `self.main_presenter = SettingsPresenter(...)` 제거
  - [ ] `line 185`: `self.api_settings_presenter = ApiSettingsPresenter(...)` 제거
  - [ ] `line 210`: `self.database_settings_presenter = DatabaseSettingsPresenter(...)` 제거
  - [ ] `line 248`: `self.logging_management_presenter = LoggingManagementPresenter(...)` 제거

- [ ] **생성자 의존성 주입 적용**
  - [ ] `@inject` 데코레이터 적용
  - [ ] 모든 필요한 Presenter들을 생성자 매개변수로 주입받도록 수정
  - [ ] `Provide[...]` 구문을 통한 DI 컨테이너 연결

- [ ] **초기화 로직 재구성**
  - [ ] `_init_sub_widgets()` 메서드에서 Presenter 생성 로직 제거
  - [ ] 주입받은 Presenter들과 View 연결 로직으로 대체
  - [ ] 초기화 순서 문제 해결 (API 키 관리자 워닝 제거)

### Phase 3: 생명주기 관리 개선 (2시간)

- [ ] **컴포넌트 초기화 전략 통일**
  - [ ] Lazy loading vs 즉시 초기화 정책 일관성 확보
  - [ ] `_initialize_api_settings()` 등 lazy 메서드들 재검토
  - [ ] 탭 전환 시 초기화 로직 개선

- [ ] **시그널 연결 시점 최적화**
  - [ ] `connect_view_signals()` 호출 시점 조정
  - [ ] 모든 컴포넌트가 완전히 초기화된 후 시그널 연결
  - [ ] 동적 시그널 연결/해제 메커니즘 도입

- [ ] **에러 처리 및 폴백 메커니즘**
  - [ ] Presenter 주입 실패 시 처리 로직
  - [ ] 부분적 초기화 실패에 대한 복구 메커니즘
  - [ ] 사용자에게 명확한 오류 메시지 제공

### Phase 4: 스크린 매니저 서비스 연동 (1시간)

- [ ] **ScreenManagerService 업데이트**
  - [ ] `_load_settings_screen()` 메서드 수정
  - [ ] MVPContainer를 통한 완전한 Settings Screen 생성
  - [ ] 기존 폴백 로직 제거 또는 개선

- [ ] **ApplicationContainer 설정**
  - [ ] Settings 관련 모든 서비스들이 DI 컨테이너에 등록되었는지 확인
  - [ ] 의존성 그래프 검증 및 순환 참조 방지
  - [ ] 필요한 경우 새로운 서비스 바인딩 추가

### Phase 5: 테스트 및 검증 (2시간)

- [ ] **자동 분석 도구 재실행**

  ```powershell
  python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings --violations-only
  ```

- [ ] **기능 무결성 테스트**
  - [ ] `python run_desktop_ui.py` 실행하여 설정 화면 정상 동작 확인
  - [ ] 모든 설정 탭 정상 로드 및 기능 테스트
  - [ ] API 키 관리자 초기화 워닝 완전 제거 확인

- [ ] **DI 패턴 준수 검증**
  - [ ] View에서 Presenter 직접 생성하는 코드 0건 확인
  - [ ] MVPContainer를 통한 모든 의존성 주입 확인
  - [ ] 단위 테스트 작성 가능성 검증 (Mock 주입 테스트)

## 🛠️ 구체적 수정 방법론

### 1. MVPContainer 확장 패턴

```python
# mvp_container.py 확장
class MVPContainer:
    def create_fully_configured_settings_screen(self, parent=None):
        """완전히 구성된 Settings Screen 생성"""

        # 1. 모든 하위 Presenter들을 미리 생성
        api_settings_presenter = self.create_api_settings_presenter()
        database_settings_presenter = self.create_database_settings_presenter()
        logging_presenter = self.create_logging_management_presenter()
        ui_settings_presenter = self.create_ui_settings_presenter()

        # 2. 메인 Settings Presenter 생성
        main_settings_presenter = self.create_settings_presenter()

        # 3. 완전히 구성된 SettingsScreen 생성
        settings_screen = SettingsScreen(
            parent=parent,
            main_presenter=main_settings_presenter,
            api_presenter=api_settings_presenter,
            database_presenter=database_settings_presenter,
            logging_presenter=logging_presenter,
            ui_presenter=ui_settings_presenter
        )

        return settings_screen
```

### 2. SettingsScreen 리팩터링 패턴

```python
# settings_screen.py 수정
class SettingsScreen(QWidget):
    @inject
    def __init__(self,
                 parent=None,
                 main_presenter=Provide["main_settings_presenter"],
                 api_presenter=Provide["api_settings_presenter"],
                 database_presenter=Provide["database_settings_presenter"],
                 logging_presenter=Provide["logging_presenter"],
                 ui_presenter=Provide["ui_settings_presenter"]):
        super().__init__(parent)

        # ✅ 모든 Presenter들이 완전히 구성된 상태로 주입됨
        self.main_presenter = main_presenter
        self.api_settings_presenter = api_presenter
        self.database_settings_presenter = database_presenter
        self.logging_management_presenter = logging_presenter
        self.ui_settings_presenter = ui_presenter

        self._setup_ui()
        self._connect_presenters()  # 주입된 Presenter들과 연결

    def _connect_presenters(self):
        """주입된 Presenter들과 View 연결"""
        # View ↔ Presenter 시그널 연결
        # 초기화 완료 후 안전하게 시그널 연결
```

### 3. 초기화 순서 개선

```python
# 수정된 초기화 플로우
def __init__(self, ...):
    # 1. UI 기본 구조 생성
    self._setup_basic_ui()

    # 2. 주입된 Presenter들과 연결
    self._connect_presenters()

    # 3. 모든 컴포넌트 초기화 완료 후 시그널 연결
    self._connect_view_signals()  # 이제 안전하게 연결 가능

    # 4. 초기 데이터 로드
    self._load_initial_data()
```

## 🎯 완료 기준

### 필수 완료 사항

- [ ] **View→Presenter 직접 생성 완전 제거**: 4건 모든 Critical 위반 해결
- [ ] **MVPContainer 기반 완전한 DI**: 모든 Presenter가 DI 컨테이너에서 주입
- [ ] **API 키 관리자 워닝 완전 제거**: 초기화 순서 문제 근본 해결
- [ ] **기능 무결성 보장**: 기존 모든 설정 기능이 정상 동작

### 성공 지표

- [ ] 자동 분석 도구에서 V20250928_051 위반 0건 달성
- [ ] `grep -r "= .*Presenter(" settings_screen.py` 결과 0건
- [ ] Settings Screen 단위 테스트 작성 가능 (Mock Presenter 주입)
- [ ] 애플리케이션 시작 시 DI 관련 오류 0건

## 📊 예상 소요시간 및 리소스

- **총 예상시간**: 10시간
- **필요 기술**: DI 패턴, MVPContainer 시스템, 생명주기 관리
- **전제 조건**: 자동 분석 도구 검증 결과 이해

## 📋 위험 요소 및 대응

### 주요 위험

1. **순환 참조 발생**: 복잡한 Presenter 간 의존성으로 인한 순환 참조
   - **대응**: 의존성 그래프 사전 분석 및 인터페이스 기반 분리
   - **검증**: DI 컨테이너 초기화 시점에 순환 참조 탐지

2. **성능 영향**: 모든 Presenter 즉시 초기화로 인한 메모리 및 시간 오버헤드
   - **대응**: 적절한 Lazy loading 전략과 Singleton 패턴 활용
   - **모니터링**: 설정 화면 로드 시간 측정

3. **기존 기능 중단**: 대규모 리팩터링으로 인한 기능 오작동
   - **대응**: 단계별 수정 및 즉시 검증
   - **롤백 계획**: Git 브랜치 기반 변경사항 격리

## 🚀 시작 방법

```powershell
# 1. 현재 위반 상황 확인
Get-ChildItem upbit_auto_trading\ui\desktop\screens\settings -Include settings_screen.py | Select-String -Pattern "= .*Presenter\("

# 2. Git 브랜치 생성
git checkout -b fix/view-presenter-direct-creation-violations

# 3. Phase 1부터 순차 진행
# - MVPContainer 확장
# - SettingsScreen 리팩터링
# - 생명주기 관리 개선

# 4. 각 Phase별 검증
python run_desktop_ui.py  # 기능 테스트
python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings
```

## 📋 관련 문서

- **발견 과정**: `docs/architecture_review/mvp_pattern_review/settings_screen/2025-09-28_automated_tool_validation_report.md`
- **위반 등록**: `docs/architecture_review/violation_registry/active_violations.md` (V20250928_051)
- **MVPContainer 가이드**: `docs/MVP_ARCHITECTURE.md`
- **DI 패턴 가이드**: `docs/DEPENDENCY_INJECTION_ARCHITECTURE.md`
- **기본 태스크**: `tasks/active/TASK_20250928_01-settings_screen_mvp_review.md` (검증 완료)

## 🎯 태스크 1과의 연관성

이 태스크는 **태스크 1의 자동 분석 도구 유용성 검증** 과정에서 발견된 추가 Critical 위반사항을 해결합니다:

- **검증 결과**: 자동 도구가 89.3% 정확도를 보였지만 **DI 패턴 위반을 완전히 놓침**
- **수동 발견**: View→Presenter 직접 생성이라는 **아키텍처 핵심 위반** 4건 추가 탐지
- **완전성 달성**: 이 태스크 완료로 Settings Screen의 **완전한 MVP + DDD 아키텍처** 구현

---

**시작일**: 2025-09-28
**목표 완료일**: 2025-10-07
**우선순위**: Critical (P0)
**담당자**: TBD
**선행 태스크**: TASK_20250928_01 (완료), TASK_20250928_02 (병렬 진행 가능)
