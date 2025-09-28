# 📋 TASK_20250928_02: Settings Screen Infrastructure 계층 직접 접근 위반 해결

## 🎯 태스크 목표

- **주요 목표**: Settings 컴포넌트에서 Infrastructure 계층 직접 접근 위반 47건 + View→Presenter 직접 생성 4건 해결
- **완료 기준**: DDD 계층 순서 준수 + MVP 의존성 주입 패턴 완전 적용
- **우선순위**: Critical (P0) - 즉시 해결 필요 (자동 분석 도구 검증으로 추가 위반 발견)

## 🚨 해결 대상 위반사항

### 주요 위반 내용

#### V20250928_001 - Infrastructure 계층 직접 접근

- **위반 건수**: 47건 (Critical)
- **주요 패턴**: `from upbit_auto_trading.infrastructure.logging import create_component_logger`
- **영향 범위**: Settings Screen 전체 컴포넌트 (View, Presenter, Widget)

#### V20250928_051 - View→Presenter 직접 생성 (새 발견)

- **위반 건수**: 4건 (Critical)
- **주요 패턴**: `self.api_settings_presenter = ApiSettingsPresenter(...)` 등
- **영향 범위**: `settings_screen.py` 메인 View 클래스
- **발견 과정**: 자동 분석 도구 검증 중 수동 발견

### 근본 원인

1. **계층 경계 무시**: View와 Presenter에서 Infrastructure 직접 import
2. **의존성 주입 부재**: 필요한 서비스를 DI 컨테이너를 통해 주입받지 않음
3. **아키텍처 가이드라인 미준수**: DDD 계층 순서 원칙 위반
4. **MVP 패턴 위반**: View에서 Presenter를 직접 생성하여 DI 컨테이너 우회 (자동 분석 도구가 놓친 심각한 위반)

## ✅ 해결 체크리스트

### Phase 1: 로깅 서비스 의존성 주입 구조 구축 (2시간)

- [ ] **Application Service Layer에 로깅 서비스 추가**
  - [ ] `ApplicationLoggingService` 인터페이스 정의
  - [ ] Infrastructure 로깅을 감싸는 Application Service 구현
  - [ ] DI 컨테이너에 서비스 등록

- [ ] **Presentation Layer 로깅 인터페이스 정의**
  - [ ] `IPresentationLogger` 인터페이스 생성
  - [ ] View와 Presenter가 사용할 로깅 규약 정의
  - [ ] Component별 로깅 컨텍스트 관리

### Phase 2: Settings Screen View 계층 수정 (3시간)

- [ ] **메인 설정 화면 수정** (`settings_screen.py`)
  - [ ] `from upbit_auto_trading.infrastructure.logging import` 제거
  - [ ] 생성자에 로깅 서비스 주입 매개변수 추가
  - [ ] `@inject` 데코레이터를 통한 의존성 주입 적용

- [ ] **API Settings Views 수정** (8개 파일)
  - [ ] `api_settings_view.py`, `api_*_widget.py` 파일들 수정
  - [ ] Infrastructure 직접 import 제거
  - [ ] 생성자 매개변수를 통한 서비스 주입

- [ ] **Database Settings Views 수정** (5개 파일)
  - [ ] `database_settings_view.py`, `database_*_widget.py` 파일들 수정
  - [ ] Infrastructure 직접 import 제거
  - [ ] 의존성 주입 패턴 적용

- [ ] **기타 Settings Views 수정** (나머지 View 파일들)
  - [ ] Logging Management, UI Settings, Notification Settings Views
  - [ ] Environment Profile Views와 관련 Widget들
  - [ ] 일관된 의존성 주입 패턴 적용

### Phase 3: Settings Screen Presenter 계층 수정 (2시간)

- [ ] **Presenter 인터페이스 기반 로깅 적용**
  - [ ] `database_settings_presenter.py` 수정
  - [ ] `api_settings_presenter.py` 수정
  - [ ] `ui_settings_presenter.py` 수정
  - [ ] Infrastructure 직접 접근 제거

- [ ] **의존성 주입 컨테이너 활용**
  - [ ] Presenter 생성을 MVPContainer에서 담당
  - [ ] 필요한 Application Service들 자동 주입
  - [ ] `get_path_service` 등 Infrastructure 직접 호출 제거

### Phase 4: 의존성 주입 설정 업데이트 (1시간)

- [ ] **ApplicationContainer 설정 추가**
  - [ ] 로깅 관련 서비스 바인딩 추가
  - [ ] Settings 관련 서비스들 DI 설정
  - [ ] 생명주기 관리 (Singleton/Transient) 설정

- [ ] **MVPContainer 설정 업데이트**
  - [ ] Settings MVP 생성 로직에 새 의존성 추가
  - [ ] View와 Presenter 생성 시 서비스 주입
  - [ ] 순환 참조 방지 패턴 적용

### Phase 5: View→Presenter 직접 생성 위반 해결 (2시간)

- [ ] **SettingsScreen 메인 클래스 리팩터링**
  - [ ] `line 98`: `self.main_presenter = SettingsPresenter(...)` 제거
  - [ ] `line 185`: `self.api_settings_presenter = ApiSettingsPresenter(...)` 제거
  - [ ] `line 210`: `self.database_settings_presenter = ...` 제거
  - [ ] `line 248`: `self.logging_management_presenter = ...` 제거

- [ ] **MVPContainer를 통한 Presenter 주입**
  - [ ] 생성자에 MVPContainer 주입 매개변수 추가
  - [ ] 모든 Presenter를 DI 컨테이너에서 완전히 구성된 상태로 주입받도록 변경
  - [ ] Lazy loading 전략 재설계 (전체 즈시 초기화 vs 완전한 lazy loading)

- [ ] **생명주기 관리 개선**
  - [ ] 초기화 순서 문제 해결 (API 키 관리자 워닝 제거)
  - [ ] 시그널 연결 시점 정비 (Component 초기화 완료 후 연결)

### Phase 6: 테스트 및 검증 (1.5시간)

- [ ] **자동 분석 도구 재실행**

  ```powershell
  python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings --violations-only
  ```

- [ ] **기능 테스트 실행**
  - [ ] `python run_desktop_ui.py` 실행하여 설정 화면 정상 동작 확인
  - [ ] 각 설정 탭별 기본 기능 동작 테스트
  - [ ] 로깅 출력이 정상적으로 동작하는지 확인

- [ ] **아키텍처 규칙 준수 검증**

  ```powershell
  # Infrastructure 직접 import 존재하지 않는지 확인
  Get-ChildItem upbit_auto_trading\ui\desktop\screens\settings -Recurse -Include *.py | Select-String -Pattern "from upbit_auto_trading\.infrastructure"
  ```

## 🛠️ 구체적 수정 방법론

### 1. 로깅 서비스 구조

```python
# 신규: application/services/logging_application_service.py
class ApplicationLoggingService:
    def __init__(self, infrastructure_logger_factory):
        self._logger_factory = infrastructure_logger_factory

    def get_component_logger(self, component_name: str):
        return self._logger_factory.create_component_logger(component_name)

# 기존 View 수정 패턴
class SettingsView(QWidget):
    @inject
    def __init__(self,
                 logging_service=Provide["logging_service"],
                 parent=None):
        super().__init__(parent)
        self.logger = logging_service.get_component_logger("SettingsView")
        # Infrastructure import 없이 로깅 사용 가능
```

### 2. 단계적 수정 전략

**우선순위 1**: Core 설정 화면 (`settings_screen.py`)
**우선순위 2**: API 설정 관련 파일들 (사용 빈도 높음)
**우선순위 3**: 데이터베이스 설정 관련 파일들
**우선순위 4**: 기타 설정 관련 파일들

### 3. 검증 기준

- [ ] `grep -r "from upbit_auto_trading.infrastructure" upbit_auto_trading/ui/desktop/screens/settings/` 결과가 0건
- [ ] 자동 분석 도구에서 Critical 위반 0건
- [ ] 모든 설정 화면이 정상 동작
- [ ] 로깅 출력이 정상 작동

## 🎯 완료 기준

### 필수 완료 사항

- [ ] **Infrastructure 직접 접근 완전 제거**: 47건 모든 위반 해결
- [ ] **의존성 주입 패턴 완전 적용**: Settings Screen 전체에 DI 적용
- [ ] **기능 무결성 보장**: 기존 기능이 모두 정상 동작
- [ ] **아키텍처 규칙 준수**: DDD 계층 순서 완전 준수

### 성공 지표

- [ ] 자동 분석 도구에서 Critical 위반 0건 달성
- [ ] Settings Screen 관련 모든 기능 정상 동작
- [ ] 코드 품질 향상 (계층 분리, 테스트 용이성)
- [ ] 향후 유사 위반 방지 가이드라인 수립

## 📊 예상 소요시간 및 리소스

- **총 예상시간**: 11.5시간 (기존 9.5시간 + View→Presenter DI 위반 해결 2시간)
- **필요 기술**: DDD 아키텍처, 의존성 주입, MVP 패턴, PyQt6
- **전제 조건**: ApplicationContainer와 MVPContainer 시스템 이해 + 자동 분석 도구 검증 결과 반영

## 📋 위험 요소 및 대응

### 주요 위험

1. **기존 기능 동작 중단**: DI 적용 중 기존 기능 오작동 가능성
   - **대응**: 단계별 수정 후 즉시 기능 테스트
   - **롤백 계획**: Git 브랜치를 통한 변경사항 격리

2. **순환 의존성 발생**: 잘못된 DI 설정으로 인한 순환 참조
   - **대응**: 각 서비스별 의존성 그래프 사전 검토
   - **검증**: 애플리케이션 시작 시 DI 컨테이너 초기화 테스트

3. **성능 영향**: 의존성 주입으로 인한 초기화 시간 증가
   - **대응**: Lazy loading 및 Singleton 패턴 적절 활용
   - **모니터링**: 설정 화면 로드 시간 측정

## 🚀 시작 방법

```powershell
# 1. 현재 위반 상황 재확인
python docs\architecture_review\tools\mvp_quick_analyzer.py --component settings --violations-only

# 2. Git 브랜치 생성
git checkout -b fix/settings-infrastructure-violations

# 3. Phase 1부터 순차적 진행
# - ApplicationLoggingService 구현
# - DI 컨테이너 설정
# - 개별 파일 수정

# 4. 각 Phase별 검증
python run_desktop_ui.py  # 기능 테스트
```

## 📋 관련 문서

- **근본 분석**: `docs/architecture_review/mvp_pattern_review/settings_screen/2025-09-28_mvp_violation_report.md`
- **자동 분석**: `docs/architecture_review/mvp_pattern_review/settings_screen/2025-09-28_automated_analysis_report.md`
- **도구 검증 보고서**: `docs/architecture_review/mvp_pattern_review/settings_screen/2025-09-28_automated_tool_validation_report.md` (새 위반 발견)
- **위반사항 등록**: `docs/architecture_review/violation_registry/active_violations.md` (V20250928_051, 052 추가)
- **DDD 가이드**: `docs/DDD_아키텍처_패턴_가이드.md`
- **DI 가이드**: `docs/DEPENDENCY_INJECTION_ARCHITECTURE.md`

---

**시작일**: 2025-09-28
**목표 완료일**: 2025-10-05
**우선순위**: Critical (P0)
**담당자**: TBD
