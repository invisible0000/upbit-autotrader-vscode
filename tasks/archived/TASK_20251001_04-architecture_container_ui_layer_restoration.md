# 📋 TASK_20251001_04: ExternalDependencyContainer UI Layer Providers 복원 및 Import 경로 수정

## 🎯 태스크 목표

### 주요 목표

**TASK_20251001_03 분석 결과를 바탕으로 ExternalDependencyContainer에 누락된 UI Layer Providers 복원**

- ExternalDependencyContainer에 UI Layer Providers 섹션 완전 복원 (MainWindowPresenter, Application Services 등)
- MVP Container의 Import 경로 오류 수정 (`application.container` → `application_service_container`)
- MainWindow의 모든 기능 완전 복구 (화면 전환, 메뉴, 네비게이션, 상태 관리)
- DDD 아키텍처 원칙을 준수하면서 명확한 네이밍과 개선된 구조 유지

### 완료 기준

- ✅ ExternalDependencyContainer에 UI Layer Providers 섹션 완전 추가
- ✅ MainWindowPresenter Provider 정상 정의 및 서비스 주입 체계 구축
- ✅ ScreenManagerService, WindowStateService, MenuService Provider 정의
- ✅ NavigationService, StatusBarService Provider 정의
- ✅ MVP Container Import 경로 문제 해결
- ✅ `python run_desktop_ui.py` 실행 시 모든 UI 기능 정상 동작
- ✅ MainWindow 기능 완전 복구: 화면 전환, 메뉴, 네비게이션, 창 상태 관리
- ✅ 7규칙 전략 구성 기능 무결성 유지

---

## 📊 현재 상황 분석

### 🔴 발생한 핵심 문제 (TASK_20251001_03 분석 결과)

1. **UI Layer Providers 완전 누락**

   ```python
   # 백업본에 존재했던 UI Layer Providers 섹션이 신규본에서 완전 삭제됨
   # ExternalDependencyContainer에는 Infrastructure 중심 Provider만 존재

   # 누락된 Provider들:
   # - main_window_presenter
   # - screen_manager_service
   # - window_state_service
   # - menu_service
   # - navigation_service
   # - status_bar_service
   ```

2. **MVP Container Import 경로 오류**

   ```python
   # 현재 잘못된 Import (존재하지 않는 모듈)
   from upbit_auto_trading.application.container import ApplicationServiceContainer

   # 올바른 Import
   from upbit_auto_trading.application.application_service_container import ApplicationServiceContainer
   ```

3. **MainWindow 기능 실패 증상**

   ```
   WARNING | MainWindowPresenter | ⚠️ ScreenManagerService를 사용할 수 없음
   WARNING | MainWindowPresenter | ⚠️ WindowStateService를 사용할 수 없음
   WARNING | MainWindowPresenter | ⚠️ MenuService를 사용할 수 없음
   WARNING | MainWindow | ⚠️ 화면 전환 실패: chart_view
   WARNING | MainWindow | ⚠️ 창 상태 저장 실패
   ```

### 사용 가능한 리소스

- **백업 파일들**: `container_backup_20251001.py`에서 정상 작동하는 UI Layer Providers 패턴 확보
- **TASK_20251001_03 분석**: 정확한 근본 원인과 해결 방향 파악 완료
- **DDD 구조**: 기존 아키텍처 원칙과 MVP 패턴 구조 유지 가능
- **검증 환경**: `python run_desktop_ui.py`로 즉시 기능 테스트 가능

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

## 📋 작업 계획

### Phase 1: 백업본 UI Layer Providers 분석 및 추출 (예상 시간: 30분)

- [ ] **백업본 UI Layer Providers 섹션 완전 분석**
  - `container_backup_20251001.py`에서 UI Layer Providers 섹션 추출
  - 각 Provider의 정의 방식과 의존성 주입 패턴 분석
  - MainWindowPresenter의 services 딕셔너리 구조 파악

- [ ] **Provider 의존성 체계 매핑**
  - 각 UI Service Provider 간의 의존성 관계 파악
  - Infrastructure Container와의 연결 지점 확인
  - 순환 참조 방지를 위한 Self 참조 패턴 확인

### Phase 2: ExternalDependencyContainer UI Layer Providers 추가 (예상 시간: 1시간)

- [ ] **안전 백업 생성**
  - `external_dependency_container.py` 백업 파일 생성
  - 현재 작동하는 Infrastructure Provider들 보존 확인

- [ ] **UI Infrastructure Providers 섹션 추가**
  - Navigation Bar Service, Status Bar Service Provider 정의
  - Database Health Service 의존성 주입 구조 구성

- [ ] **Application Services Providers 섹션 추가**
  - ScreenManagerService Provider 정의 (ApplicationServiceContainer 의존성)
  - WindowStateService Provider 정의
  - MenuService Provider 정의

- [ ] **MainWindowPresenter Provider 완전 복원**
  - services 딕셔너리를 통한 모든 필요 서비스 주입
  - ThemeService, DatabaseHealthService, NavigationBar, ApiKeyService 등 연결
  - ScreenManager, WindowState, Menu 서비스 완전 주입

### Phase 3: MVP Container Import 경로 수정 (예상 시간: 30분)

- [ ] **MVP Container Import 경로 수정**
  - `mvp_container.py`의 잘못된 Import 경로 수정
  - `from upbit_auto_trading.application.container` → `from upbit_auto_trading.application.application_service_container`

- [ ] **관련 파일들 Import 경로 점검**
  - 다른 파일들에서 유사한 Import 경로 오류 존재 여부 확인
  - Factory 패턴에서 Container 접근 경로 검증

### Phase 4: DI 연결 체계 통합 검증 (예상 시간: 45분)

- [ ] **Container 초기화 체계 검증**
  - DILifecycleManager → ExternalDependencyContainer → UI Providers 체인 확인
  - ApplicationServiceContainer 연동 정상 동작 확인

- [ ] **Provider 등록 상태 검증**
  - 모든 UI Layer Provider가 정상 등록되었는지 확인
  - 의존성 주입 체계 무결성 검증

### Phase 5: 통합 기능 테스트 및 검증 (예상 시간: 30분)

- [ ] **MainWindow 기능 완전 테스트**
  - `python run_desktop_ui.py` 실행하여 UI 정상 로딩 확인
  - 화면 전환 기능 테스트 (chart_view, settings_view 등)
  - 메뉴 기능 및 네비게이션 정상 동작 확인
  - 창 상태 저장/복원 기능 테스트

- [ ] **7규칙 전략 구성 기능 검증**
  - 트리거 빌더 화면 정상 접근 확인
  - 전략 관리 화면 기능 무결성 검증
  - 설정 화면 API 키 관리 기능 테스트

---

## 🛠️ 구체적 구현 방안

### 🔧 UI Layer Providers 섹션 구현 패턴

```python
# =============================================================================
# UI Layer Providers - Presentation Layer 서비스 (ExternalDependencyContainer에 추가)
# =============================================================================

# Navigation Bar Service - 네비게이션 관리
navigation_service = providers.Factory(
    "upbit_auto_trading.ui.desktop.common.widgets.navigation_bar.NavigationBar"
)

# Status Bar Service - 상태 바 관리
status_bar_service = providers.Factory(
    "upbit_auto_trading.ui.desktop.common.widgets.status_bar.StatusBar",
    database_health_service=providers.Factory(
        "upbit_auto_trading.application.services.database_health_service.DatabaseHealthService"
    )
)

# Application Services - MVP 패턴으로 Presenter에 위임
screen_manager_service = providers.Factory(
    "upbit_auto_trading.application.services.screen_manager_service.ScreenManagerService",
    application_container=providers.Factory(
        "upbit_auto_trading.application.application_service_container.ApplicationServiceContainer",
        repository_container=repository_container
    )
)

window_state_service = providers.Factory(
    "upbit_auto_trading.application.services.window_state_service.WindowStateService"
)

menu_service = providers.Factory(
    "upbit_auto_trading.application.services.menu_service.MenuService"
)

# MainWindowPresenter - MVP 패턴 적용 (모든 필요한 서비스 주입)
main_window_presenter = providers.Factory(
    "upbit_auto_trading.presentation.presenters.main_window_presenter.MainWindowPresenter",
    services=providers.Dict(
        theme_service=theme_service,
        database_health_service=providers.Factory(
            "upbit_auto_trading.application.services.database_health_service.DatabaseHealthService"
        ),
        navigation_bar=navigation_service,
        api_key_service=api_key_service,
        screen_manager_service=screen_manager_service,
        window_state_service=window_state_service,
        menu_service=menu_service
    )
)
```

### 🔧 MVP Container Import 수정 패턴

```python
# 수정 전 (오류)
from upbit_auto_trading.application.container import ApplicationServiceContainer

# 수정 후 (정상)
from upbit_auto_trading.application.application_service_container import ApplicationServiceContainer
```

---

## 🎯 성공 기준

### ✅ 기능적 성공 기준

1. **MainWindow 완전 기능 복구**: 모든 경고 메시지 사라지고 정상 동작
2. **화면 전환 정상 동작**: chart_view, settings_view 등 모든 화면 접근 가능
3. **UI 서비스 정상 작동**: 메뉴, 네비게이션, 상태바, 창 관리 완전 동작
4. **7규칙 전략 구성**: 트리거 빌더에서 전략 구성 기능 무결성 유지

### ✅ 기술적 성공 기준

1. **Provider 등록 완료**: 모든 UI Layer Provider가 ExternalDependencyContainer에 정상 등록
2. **Import 경로 해결**: MVP Container와 관련 파일들의 Import 오류 완전 해결
3. **DI 체인 무결성**: DILifecycleManager → ExternalDependencyContainer → UI Services 체인 완성
4. **아키텍처 준수**: DDD 원칙과 MVP 패턴을 유지하면서 구조 개선

### ✅ 품질 기준

1. **코드 안정성**: 모든 변경 사항이 기존 기능에 영향 없이 적용됨
2. **테스트 통과**: UI 실행 테스트와 기능 검증 모두 성공
3. **구조 일관성**: 명확한 네이밍과 개선된 Container 구조 유지
4. **문서화**: 모든 변경 사항이 명확히 기록되고 추적 가능함

---

## 💡 작업 시 주의사항

### 안전성 원칙

- **백업 필수**: ExternalDependencyContainer 수정 전 반드시 백업 생성
- **단계별 검증**: 각 Phase 완료 후 UI 테스트로 기능 확인
- **점진적 적용**: 한 번에 모든 Provider를 추가하지 말고 단계적 적용
- **롤백 준비**: 문제 발생 시 즉시 백업본으로 복원 가능하도록 준비

### 아키텍처 원칙

- **DDD 준수**: Domain Layer의 순수성을 해치지 않는 범위에서 UI Provider 정의
- **MVP 패턴 유지**: Presenter와 View의 의존성 주입 체계 보존
- **순환 참조 방지**: Self 참조 패턴과 Factory 패턴으로 의존성 순환 방지
- **책임 분리**: Infrastructure, Application, UI Layer의 명확한 역할 구분 유지

---

## 🚀 즉시 시작할 작업

### 1단계: 백업 및 현재 상태 확인 (10분)

```powershell
# 현재 ExternalDependencyContainer 백업 생성
Copy-Item "upbit_auto_trading\infrastructure\dependency_injection\external_dependency_container.py" "upbit_auto_trading\infrastructure\dependency_injection\external_dependency_container_backup_20251001_task04.py"

# 백업본에서 UI Layer Providers 섹션 확인
Get-Content "upbit_auto_trading\infrastructure\dependency_injection\container_backup_20251001.py" -Encoding UTF8 | Select-String -Pattern "UI Layer Providers" -Context 20
```

### 2단계: UI Layer Providers 섹션 추출 및 분석 (15분)

```powershell
# MainWindowPresenter 정의 패턴 확인
Get-Content "upbit_auto_trading\infrastructure\dependency_injection\container_backup_20251001.py" -Encoding UTF8 | Select-String -Pattern "main_window_presenter.*=.*providers" -Context 10

# Application Services 정의 패턴 확인
Get-Content "upbit_auto_trading\infrastructure\dependency_injection\container_backup_20251001.py" -Encoding UTF8 | Select-String -Pattern "screen_manager_service|window_state_service|menu_service" -Context 5
```

### 3단계: 즉시 UI 테스트로 현재 문제 확인 (5분)

```powershell
# 현재 UI 실행하여 경고 메시지 확인
python run_desktop_ui.py
```

---

## 🔗 연관 태스크

### 선행 태스크

- **TASK_20251001_02**: 컨테이너 파일명 직접 변경 (문제 발생 원인)
- **TASK_20251001_03**: 컨테이너 구조 변경 전후 비교 진단 및 문제점 분석 (근본 원인 파악)

### 후속 태스크 계획

- **TASK_20251001_05**: 7규칙 전략 완전 검증 및 최종 시스템 안정성 확인
- **Container 구조 최적화**: UI Layer와 Infrastructure Layer의 명확한 분리 구조 정립

---

## 📚 참고 문서

### 기술 참고 자료

- **백업 파일**: `container_backup_20251001.py` - 정상 작동하는 UI Layer Providers 패턴
- **분석 결과**: `TASK_20251001_03-container_structure_diagnosis.md` - 근본 원인 분석
- **.github/copilot-instructions.md**: DDD 아키텍처 및 MVP 패턴 가이드라인

### 검증 가이드

- **UI 테스트**: `python run_desktop_ui.py` - 전체 기능 검증
- **7규칙 검증**: 트리거 빌더 → 전략 관리 → 7규칙 구성 테스트
- **아키텍처 검증**: PowerShell 명령어로 계층 위반 탐지

---

**문서 유형**: Container 구조 복원 및 Import 수정 태스크
**우선순위**: 🔥 최고 (MainWindow 기능 완전 중단 상태)
**예상 소요 시간**: 2-3시간
**접근 방식**: 백업본 패턴 복원 → Import 수정 → 통합 검증

---

> **💡 핵심 메시지**: "백업본의 성공 패턴을 신규 구조에 적용하여 안정성과 발전성을 동시에 확보!"
>
> **🎯 성공 전략**: 단계별 복원 → 점진적 검증 → 완전한 기능 회복!

---

**다음 에이전트 시작점**: Phase 1.1 백업 파일 생성 및 UI Layer Providers 섹션 분석부터 시작
