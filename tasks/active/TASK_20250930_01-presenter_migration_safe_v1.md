# 📋 TASK_20250930_01: Presenter 안전 단계별 이동 작업 (전략관리 제외)

## 🎯 태스크 목표

### 주요 목표

**MVP 아키텍처 완성을 위한 Presenter의 안전한 단계별 이동 (전략 관리 화면 제외)**

- UI 계층에 흩어져 있는 Presenter를 Presentation 계층으로 UI 폴더 구조와 동일하게 통합 이동
- DDD + Clean Architecture 준수: UI Layer는 순수 View만, Presentation Layer에 모든 Presenter 집중
- 중복 파일 정리 및 Import 경로 충돌 해결
- 각 이동 단계마다 검증하여 시스템 안정성 보장
- **전략 관리(strategy_management) 화면은 별도 태스크로 분리하여 진행**

### 완료 기준

- ✅ UI 계층(`ui/desktop/**/presenters/`)에서 Presenter 제거 (전략 관리 제외)
- ✅ Presentation 계층(`presentation/presenters/`)에 UI 구조와 동일하게 조직화
- ✅ 모든 Factory와 View의 Import 경로 업데이트
- ✅ `python run_desktop_ui.py` 실행 시 모든 기능 정상 동작 (전략 관리 제외)
- ✅ 중복 파일 완전 제거 및 정리

---

## 📊 현재 상황 분석

### ✅ 이미 이동 완료된 Presenters

```
presentation/presenters/
├── settings_presenter.py
├── strategy_maker_presenter.py
├── trigger_builder_presenter.py
└── settings/
    ├── api_settings_presenter.py         ✅ TASK_02 완료
    └── database_settings_presenter.py    ✅ TASK_03 완료
```

### 🔄 이동 대상 Presenters (전략 관리 제외)

#### Phase 1: 중복 파일 정리 (1개)

```
🚨 중복 위험 파일들
└── ui/desktop/screens/settings/presenters/database_settings_presenter.py  (Legacy - 삭제)
```

#### Phase 2: Settings Presenters (5개) - TASK_04 연계

```
ui/desktop/screens/settings/*/presenters/ → presentation/presenters/settings/
├── logging_management/presenters/logging_management_presenter.py
├── logging_management/presenters/logging_config_presenter.py
├── notification_settings/presenters/notification_settings_presenter.py
├── ui_settings/presenters/ui_settings_presenter.py
└── environment_profile/presenters/environment_profile_presenter.py
```

#### Phase 3: Main Window Presenter (1개) - 최고 우선순위

```
ui/desktop/presenters/ → presentation/presenters/
└── main_window_presenter.py  (핵심 컴포넌트)
```

#### Phase 4: Chart View Presenters (2개)

```
ui/desktop/screens/chart_view/presenters/ → presentation/presenters/chart_view/
├── window_lifecycle_presenter.py
└── orderbook_presenter.py
```

### 🎯 목표 구조 (UI 폴더 구조 기반)

```
presentation/presenters/
├── main_window_presenter.py              ⭐ 이동 대상
├── settings_presenter.py                 ✅ 기존 (탭 관리용)
├── settings/                             ⭐ UI와 동일한 구조
│   ├── api_settings_presenter.py         ✅ TASK_02 완료
│   ├── database_settings_presenter.py    ✅ TASK_03 완료
│   ├── logging_management_presenter.py   ⭐ 이동 대상
│   ├── logging_config_presenter.py       ⭐ 이동 대상
│   ├── notification_settings_presenter.py ⭐ 이동 대상
│   ├── ui_settings_presenter.py          ⭐ 이동 대상
│   └── environment_profile_presenter.py  ⭐ 이동 대상
└── chart_view/                           ⭐ UI와 동일한 구조
    ├── window_lifecycle_presenter.py     ⭐ 이동 대상
    └── orderbook_presenter.py            ⭐ 이동 대상
```

### 📋 UI 화면별 분류 (Navigation Bar 기준)

```
UI 폴더 구조 → Presenter 조직화 계획

ui/desktop/screens/
├── asset_screener/        → 🔮 향후 확장 (현재 Presenter 없음)
├── backtesting/          → 🔮 향후 확장 (현재 Presenter 없음)
├── chart_view/           → ✅ Phase 4: presentation/presenters/chart_view/
├── dashboard/            → 🔮 향후 확장 (현재 Presenter 없음)
├── live_trading/         → 🔮 향후 확장 (현재 Presenter 없음)
├── monitoring_alerts/    → 🔮 향후 확장 (현재 Presenter 없음)
├── notification_center/  → 🔮 향후 확장 (현재 Presenter 없음)
├── portfolio_configuration/ → 🔮 향후 확장 (현재 Presenter 없음)
├── settings/             → ✅ Phase 2: presentation/presenters/settings/
└── strategy_management/  → 🚫 별도 태스크 (TASK_20250930_02)
```

---

## ✅ 현재 상황 분석 결과

### 📊 발견된 파일 현황

- **이미 완료**: `presentation/presenters/settings/` 에 api_settings_presenter.py, database_settings_presenter.py 존재
- **중복 위험**: `ui/desktop/screens/settings/presenters/database_settings_presenter.py` (Legacy 제거 필요)
- **이동 대상 Settings**: logging_management_presenter.py, logging_config_presenter.py, notification_settings_presenter.py, ui_settings_presenter.py, environment_profile_presenter.py
- **이동 대상 Main**: `ui/desktop/presenters/main_window_presenter.py`
- **이동 대상 Chart**: window_lifecycle_presenter.py, orderbook_presenter.py
- **제외**: strategy_management 관련 모든 Presenter들 (별도 태스크)

### 🎯 위험도 평가

- **낮음**: 중복 Legacy 파일 제거
- **중간**: Settings Presenters 이동 (Factory에서 import 경로 수정 필요)
- **높음**: Main Window Presenter (Container에서 참조, 핵심 컴포넌트)
- **중간**: Chart View Presenters (독립성 높음)

---

## 📋 단계별 체크리스트

### Phase 1: 중복 파일 안전 정리

- [x] 1.1 Legacy database_settings_presenter.py 중복 확인
  - ✅ UI 폴더 파일: 54,559 bytes (9/29 12:11) - Legacy
  - ✅ Presentation 폴더 파일: 45,236 bytes (9/29 18:49) - 현재 사용중
  - ✅ Factory에서 presentation 폴더 파일 사용 확인
- [x] 1.2 Legacy 파일 백업 후 안전 제거
  - ✅ 백업 위치: legacy/mvp_restructure_20250930/database_settings_presenter_ui_legacy_20250930_181123.py
  - ✅ UI 폴더에서 중복 파일 완전 제거 완료
- [x] 1.3 UI 실행 테스트 (python run_desktop_ui.py)
  - ✅ 사용자 스킵으로 진행 (중복 파일 제거만으로 충분)

### Phase 2: Settings Presenters 하나씩 안전 이동 (TASK_04 연계)

- [x] 2.1 logging_management_presenter.py 이동 + 테스트
  - ✅ 파일 이동: ui/desktop/screens/settings/logging_management/presenters/ → presentation/presenters/settings/
  - ✅ Factory Import 경로 수정: presentation.presenters.settings.logging_management_presenter
  - ✅ UI 테스트 통과: 이상 없음 확인
- [x] 2.2 logging_config_presenter.py 이동 + 테스트
  - ✅ 파일 이동: ui/desktop/screens/settings/logging_management/presenters/ → presentation/presenters/settings/
  - ✅ 예제 파일 Import 경로 수정 완료
  - ✅ UI 테스트 통과: 정상 동작 확인
  - ⚠️ 추가 조사 필요: Factory에서 직접 참조 없음 (기능 연결 상태 미확인)
- [x] 2.3 notification_settings_presenter.py 이동 + 테스트
  - ✅ 파일 이동: ui/desktop/screens/settings/notification_settings/presenters/ → presentation/presenters/settings/
  - ✅ Factory Import 경로 수정: presentation.presenters.settings.notification_settings_presenter
  - ✅ UI 테스트 통과: 정상 동작 확인
- [x] 2.4 ui_settings_presenter.py 이동 + 테스트
  - ✅ 파일 이동: ui/desktop/screens/settings/ui_settings/presenters/ → presentation/presenters/settings/
  - ✅ Factory Import 경로 수정: presentation.presenters.settings.ui_settings_presenter
  - ✅ UI 폴더 **init**.py 정리 (UISettingsPresenter Import 제거)
  - ✅ 교차 참조 해결: notification_settings **init**.py에서 구 경로 Presenter Import 제거
  - ✅ Settings 스크린 일관성 확보: Factory 패턴으로 통일 (직접 UISettingsView 인스턴스화 → Factory 패턴)
  - ✅ UI 테스트 통과: 정상 동작 확인 (에러 없이 실행)
  - 📚 **학습된 패턴**: Import 체인 의존성 문제 - **init**.py 간접 참조가 구 경로 Import 유발
  - 🔍 **API 키 탭 안전성 원리**: Lazy Loading + Dynamic Tab Replacement가 Import 체인 문제로부터 보호
- [x] 2.5 environment_profile_presenter.py 이동 + 테스트
  - ✅ 파일 이동: ui/desktop/screens/settings/environment_profile/presenters/environment_profile_presenter.py → presentation/presenters/settings/
  - ✅ UI 테스트 통과: 정상 동작 확인
  - ✅ Factory Import 경로 확인 및 문제 없음
  - ✅ Import 체인 문제 없음 확인

- [x] 2.6 Settings Factory Import 경로 일괄 수정 및 UI 폴더 presenters 폴더 정리
  - [x] 2.6.1 Settings Factory Import 경로 일괄 수정 ✅ (이미 올바른 경로 사용중 확인)
  - [x] 2.6.2 UI 폴더 내 설정 관련 presenters 폴더 제거 (전략 관리 제외) ✅ 완료

### Phase 3: Main Window Presenter 신중 이동 (최고 위험도)

- [x] 3.1 Main Window Presenter 의존성 분석
  - ✅ Container.py에서 Factory Provider로 관리 (L242 수정 필요)
  - ✅ main_window.py에서 Container 주입으로 사용 (경로 수정 불필요)
  - ✅ presenters/**init**.py에서 export (L8 이동 후 삭제)
  - ✅ Legacy 파일에서만 직접 Import (영향 없음)
- [x] 3.2 Main Window Presenter 백업 생성
  - ✅ 백업 완료: main_window_presenter_backup_20250930_193056.py
  - ✅ 파일 크기: 12,432 bytes
  - ✅ 위치: legacy/mvp_restructure_20250930/
- [x] 3.3 Main Window Presenter 이동
  - ✅ 파일 이동 완료: presentation/presenters/main_window_presenter.py
  - ✅ 파일 크기 유지: 12,432 bytes
  - ✅ 기존 위치에서 제거 확인됨
- [x] 3.4 Container Import 경로 즉시 수정
  - ✅ Container.py L242 경로 수정: presentation.presenters.main_window_presenter
  - ✅ UI presenters/**init**.py Import 주석 처리
  - ✅ **all** 목록 주석 처리 (이동됨 표시)
- [x] 3.5 Main Window UI 테스트 (즉시)
  - ✅ python run_desktop_ui.py 정상 실행 확인
  - ✅ Main Window 로드 성공
  - ✅ 모든 기능 정상 작동 확인

### Phase 4: Chart View Presenters 이동

- [x] 4.1 Chart View 폴더 구조 생성 (presentation/presenters/chart_view/)
  - ✅ 폴더 생성 완료: presentation/presenters/chart_view/
  - ✅ 이동 대상 확인: window_lifecycle_presenter.py (12,052 bytes)
  - ✅ 이동 대상 확인: orderbook_presenter.py (7,542 bytes)
- [x] 4.2 window_lifecycle_presenter.py 이동 + 테스트
  - ✅ 파일 이동: presentation/presenters/chart_view/window_lifecycle_presenter.py
  - ✅ Import 경로 수정: chart_view_screen.py에서 새 경로로 업데이트
  - ✅ UI 테스트 통과: Chart View 정상 작동 확인
- [x] 4.3 orderbook_presenter.py 이동 + 테스트
  - ✅ 파일 이동: presentation/presenters/chart_view/orderbook_presenter.py
  - ✅ Import 경로 수정: orderbook_widget.py에서 새 경로로 업데이트
  - ✅ UI 테스트 통과: Chart View 정상 작동 확인
  - ✅ 기존 presenters 폴더 제거 완료
- [x] 4.4 Chart View Factory Import 경로 수정 (스킵)
  - ✅ Factory 패턴 미적용 확인: Chart View 전용 Factory 없음
  - ✅ 단계 스킵: Import 경로 수정 불필요

### Phase 5: Import 경로 일괄 수정 및 정리

- [x] 5.1 모든 Factory 파일의 Import 경로 검증
  - ✅ 모든 Factory가 이미 올바른 presentation.presenters 경로 사용 중 확인
  - ✅ Settings Factory, Main Window Factory 모두 정상 경로 적용됨
- [x] 5.2 누락된 Import 경로 수정
  - ✅ 누락된 Import 경로 없음 확인 (Phase 1-4에서 완전 처리됨)
- [x] 5.3 빈 presenters 폴더 정리
  - ✅ 모든 빈 presenters 폴더가 이미 정리됨 확인

### Phase 6: 최종 검증 및 정리

- [x] 6.1 전체 UI 시스템 테스트
  - ✅ python run_desktop_ui.py 정상 실행 확인
  - ✅ Main Window 완전 로드 성공
  - ✅ 모든 메뉴 및 화면 정상 접근 확인
- [x] 6.2 Settings 7개 탭 모두 접근 테스트
  - ✅ API 키, 데이터베이스, 로깅 관리, 로깅 설정, 알림 설정, UI 설정, 환경 프로필 모든 탭 정상 접근
  - ✅ 각 설정 탭별 기능 정상 동작 확인
  - ✅ MVP 패턴 및 Factory 패턴 정상 작동 검증
- [x] 6.3 Chart View 정상 동작 확인
  - ✅ 차트 화면 정상 표시 및 상호작용 확인
  - ✅ window_lifecycle_presenter, orderbook_presenter 정상 동작
  - ✅ 새로운 Import 경로 정상 작동 검증
- [x] 6.4 Strategy Management 기존 구조 정상 동작 확인
  - ✅ 전략 관리 화면 기존 구조 그대로 정상 동작 확인
  - ✅ 별도 태스크(TASK_20250930_02)로 진행 예정
- [x] 6.5 아키텍처 계층 위반 검사
  - ✅ DDD 계층 위반 없음 확인
  - ✅ UI Layer 순수성 확보 (Presenter 제거 완료)
  - ✅ Presentation Layer 체계적 조직화 완료

---

## 🔄 체계적 작업 절차 (6단계)

### Phase 1: 중복 파일 안전 정리

#### 1.1 Legacy Database Settings Presenter 제거

```powershell
# 현재 사용중인 Import 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "ui\.desktop\.screens\.settings\.presenters\.database_settings_presenter"

# 안전하게 백업 후 제거
Move-Item "upbit_auto_trading\ui\desktop\screens\settings\presenters\database_settings_presenter.py" "legacy\mvp_restructure_20250930\database_settings_presenter_ui_legacy.py"
```

### Phase 2: Settings Presenters 일괄 이동 (TASK_04 연계)

#### 2.1 Settings 하위 폴더 확인

```powershell
# 이동 대상 확인
Get-ChildItem "ui\desktop\screens\settings" -Recurse -Include "*presenter*.py" | Select-Object Name, Directory
```

#### 2.2 순차적 이동 (하나씩 안전하게)

```powershell
# 각 Presenter 하나씩 이동 후 즉시 테스트
Move-Item "ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py  # 즉시 테스트

Move-Item "ui\desktop\screens\settings\logging_management\presenters\logging_config_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py  # 즉시 테스트

Move-Item "ui\desktop\screens\settings\notification_settings\presenters\notification_settings_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py  # 즉시 테스트

Move-Item "ui\desktop\screens\settings\ui_settings\presenters\ui_settings_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py  # 즉시 테스트

Move-Item "ui\desktop\screens\settings\environment_profile\presenters\environment_profile_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py  # 즉시 테스트
```

### Phase 3: Main Window Presenter 이동 (최고 위험도)

#### 3.1 Main Window 의존성 분석

```powershell
# Main Window Presenter를 참조하는 모든 파일 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "ui\.desktop\.presenters\.main_window_presenter"
```

#### 3.2 안전한 이동 및 즉시 수정

```powershell
# 1. 백업
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "ui\desktop\presenters\main_window_presenter.py" "legacy\mvp_restructure_20250930\main_window_presenter_backup_$timestamp.py"

# 2. 이동
Move-Item "ui\desktop\presenters\main_window_presenter.py" "presentation\presenters\"

# 3. 즉시 Import 경로 수정 (Factory 파일들)
# 4. 바로 테스트 실행
python run_desktop_ui.py
```

### Phase 4: Chart View Presenters 이동

#### 4.1 Chart View 폴더 생성 및 이동

```powershell
# Chart View 폴더 생성 (UI 구조와 동일)
New-Item -ItemType Directory -Path "presentation\presenters\chart_view" -Force

# Chart 관련 Presenters 순차 이동
Move-Item "ui\desktop\screens\chart_view\presenters\window_lifecycle_presenter.py" "presentation\presenters\chart_view\"
python run_desktop_ui.py  # 즉시 테스트

Move-Item "ui\desktop\screens\chart_view\presenters\orderbook_presenter.py" "presentation\presenters\chart_view\"
python run_desktop_ui.py  # 즉시 테스트
```

### Phase 5: Import 경로 일괄 수정

#### 5.1 모든 Factory 파일 수정

```powershell
# Factory 파일들에서 Import 경로 검색 (전략 관리 제외)
Get-ChildItem upbit_auto_trading -Recurse -Include "*factory*.py" | Select-String "ui\.desktop.*presenters" | Where-Object { $_ -notmatch "strategy_management" }
```

#### 5.2 Import 경로 수정 패턴

```python
# Settings Factory 수정 패턴
# Before:
from upbit_auto_trading.ui.desktop.screens.settings.logging_management.presenters.logging_management_presenter import LoggingManagementPresenter
# After:
from upbit_auto_trading.presentation.presenters.settings.logging_management_presenter import LoggingManagementPresenter

# Main Window Factory 수정 패턴
# Before:
from upbit_auto_trading.ui.desktop.presenters.main_window_presenter import MainWindowPresenter
# After:
from upbit_auto_trading.presentation.presenters.main_window_presenter import MainWindowPresenter

# Chart View Factory 수정 패턴
# Before:
from upbit_auto_trading.ui.desktop.screens.chart_view.presenters.window_lifecycle_presenter import WindowLifecyclePresenter
# After:
from upbit_auto_trading.presentation.presenters.chart_view.window_lifecycle_presenter import WindowLifecyclePresenter
```

### Phase 6: 빈 Presenters 폴더 정리 및 최종 검증

#### 6.1 빈 폴더 탐지 및 제거

```powershell
# 빈 presenters 폴더들 찾기 (전략 관리 제외)
Get-ChildItem upbit_auto_trading\ui -Recurse -Directory -Name "presenters" | Where-Object { $_ -notmatch "strategy_management" } | ForEach-Object {
    $path = "upbit_auto_trading\ui\$_"
    if ((Get-ChildItem $path -File -ErrorAction SilentlyContinue).Count -eq 0) {
        Write-Host "빈 폴더 발견: $path"
        Remove-Item $path -Recurse -Force
    }
}
```

#### 6.2 전체 시스템 테스트 (전략 관리 제외)

```powershell
# 전체 앱 기능 테스트
python run_desktop_ui.py
# 1. Main Window 정상 로드
# 2. Settings → 7개 탭 모두 접근
# 3. Chart View 정상 표시
# 4. 전략 관리는 기존 구조 그대로 정상 동작 확인
```

---

## 🛠️ 구체적 구현 계획

### Settings Factory Import 경로 수정 (TASK_04 연계)

```python
class LoggingSettingsComponentFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # 새로운 Import 경로 적용
        from upbit_auto_trading.presentation.presenters.settings.logging_management_presenter import LoggingManagementPresenter

        # 나머지 Factory 패턴은 TASK_04와 동일하게 적용
        app_container = self._get_application_container()
        logging_service = app_container.get_logging_service()

        view = LoggingSettingsComponent(parent)
        presenter = LoggingManagementPresenter(view=view, logging_service=logging_service)

        view.set_presenter(presenter)
        presenter.initialize()

        return view
```

### Main Window Factory Import 경로 수정

```python
# main_window_factory.py 수정
class MainWindowFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # 새로운 Import 경로
        from upbit_auto_trading.presentation.presenters.main_window_presenter import MainWindowPresenter

        # 기존 Factory 로직 유지
        app_container = self._get_application_container()
        # ... 기존 서비스 주입 로직

        view = MainWindow(parent)
        presenter = MainWindowPresenter(view=view, **services)

        return view
```

### Chart View Factory Import 경로 수정

```python
# chart_view_factory.py 수정 (존재하는 경우)
class ChartViewFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # UI 폴더 구조와 동일한 경로
        from upbit_auto_trading.presentation.presenters.chart_view.window_lifecycle_presenter import WindowLifecyclePresenter
        from upbit_auto_trading.presentation.presenters.chart_view.orderbook_presenter import OrderbookPresenter

        # Factory 로직...
```

---

## 🎯 성공 기준

### 기술적 검증

#### 아키텍처 순수성

- ✅ **UI Layer 순수성**: `ui/` 폴더에서 Presenter 제거 완료 (전략 관리 제외)
- ✅ **Presentation Layer 통합**: UI 구조와 동일한 폴더명으로 체계적 조직화
- ✅ **DDD 준수**: UI → Presentation → Application → Infrastructure 계층 준수
- ✅ **Import 경로 일관성**: `presentation.presenters` 경로 사용

#### 파일 구조 정리

- ✅ **UI 구조 반영**: UI 폴더명과 동일한 Presenter 폴더 구조
- ✅ **중복 제거**: Legacy 파일들 완전 제거
- ✅ **백업 보관**: Legacy 파일들 안전하게 백업

### 동작 검증

#### 엔드투엔드 테스트

1. **앱 시작**: `python run_desktop_ui.py` 완전 오류 없는 실행
2. **Main Window**: 메인 화면 정상 로드 및 모든 메뉴 접근
3. **Settings**: 7개 설정 탭 모두 정상 접근 및 기능 동작
4. **Chart View**: 차트 화면 정상 표시 및 상호작용
5. **Strategy Management**: 기존 구조로 정상 동작 (이동하지 않음)

---

## 🎓 중요 학습: Import 체인 의존성 패턴 (Phase 2.4에서 발견)

### 🚨 **문제 패턴**: 간접 Import 체인이 구 경로 참조 유발

**상황**: UI 설정 화면만 폴백되고 API 키 설정은 정상 동작

**원인 분석**:

1. **Factory Import**: 둘 다 직접 Import 사용 (문제 없음)

   ```python
   # API & UI 설정 모두 동일한 패턴
   from upbit_auto_trading.ui.desktop.screens.settings.api_settings.views.api_settings_view import ApiSettingsView
   from upbit_auto_trading.ui.desktop.screens.settings.ui_settings.views.ui_settings_view import UISettingsView
   ```

2. **간접 Import 체인 문제** (UI 설정만 해당):

   ```
   UISettingsView 로드 시도
   → settings/__init__.py 로드 (NotificationSettingsView Import 포함)
   → notification_settings/__init__.py 로드
   → 구 경로 notification_settings_presenter Import 시도 ❌
   ```

3. **API 설정이 안전한 이유**:
   - `api_settings/__init__.py`에서 Presenter Import 없음 (View만)
   - 간접 Import 체인에 구 경로 참조 없음

### 🛡️ **핵심 발견**: Lazy Loading + Dynamic Tab Replacement의 보호 효과

**API 키 탭이 유일하게 정상 동작한 진짜 이유**:

#### 🏗️ **탭 초기화 패턴 비교**

| 탭 | 초기화 시점 | Import 시점 | 동적 교체 | 안전성 |
|-----|------------|------------|----------|--------|
| **UI 설정** | 앱 시작시 즉시 | 앱 시작시 | ✅ 첫 번째 탭 교체 | ❌ Import 체인 노출 |
| **API 키** | 탭 클릭시 | 탭 클릭시 | ✅ removeTab + insertTab | ✅ 완전 격리 |
| **데이터베이스** | 탭 클릭시 | 탭 클릭시 | ✅ removeTab + insertTab | ✅ 완전 격리 |
| **기타 탭들** | 탭 클릭시 | 탭 클릭시 | ✅ removeTab + insertTab | ❌ Import 체인 문제 |

#### 🔍 **Dynamic Tab Replacement 메커니즘**

**초기 상태**: 모든 탭이 `QWidget()` placeholder

```python
self.tab_widget.addTab(QWidget(), "API 키")  # 빈 위젯
```

**탭 활성화시**: 실제 컴포넌트로 교체

```python
elif index == 1:  # API 키 탭
    self._initialize_api_settings()  # Factory로 생성
    if self.api_key_manager:
        self.tab_widget.removeTab(1)           # placeholder 제거
        self.tab_widget.insertTab(1, self.api_key_manager, "API 키")  # 실제 컴포넌트 삽입
```

#### ✅ **보호 효과**

- **Import 격리**: 사용자가 탭을 클릭하기 전까지 컴포넌트 Import 안됨
- **에러 격리**: notification_settings Import 체인 문제가 API 키 탭에 영향 없음
- **독립성**: 각 탭이 완전히 독립적으로 로드됨

**핵심**: API 키 설정은 **"진정한 Lazy Loading"** 으로 Import 체인 문제로부터 완전히 보호받음!

> 📚 **상세 문서**: [Lazy Loading + Dynamic Tab Replacement 패턴](../../docs/architecture_patterns/import_safety/LAZY_LOADING_IMPORT_CHAIN_SAFETY.md)

### ✅ **해결 방법**: **init**.py 정리 전략

**핵심 원칙**: Presenter 이동 시 **모든 **init**.py에서 Presenter Import 제거**

```python
# ❌ 위험한 패턴 (구 경로 참조 유발)
from .presenters.some_presenter import SomePresenter

# ✅ 안전한 패턴 (View만 노출)
from .views.some_view import SomeView
# Presenter는 presentation/presenters/로 이동됨 (주석 추가)
```

### 🔧 **Settings 스크린 일관성 확보**

**발견된 불일치**: UI 설정만 직접 인스턴스화, 다른 탭들은 Factory 패턴

**수정 전 (불일치)**:

```python
def _initialize_ui_settings(self):
    from upbit_auto_trading.ui.desktop.screens.settings.ui_settings import UISettingsView
    self.ui_settings = UISettingsView(self, logging_service=self._logging_service)  # 직접 생성
```

**수정 후 (일관성)**:

```python
def _initialize_ui_settings(self):
    self.ui_settings = self._settings_factory.create_ui_settings_component(parent=self)  # Factory 패턴
```

### 📝 **Presenter 이동 시 체크리스트** (향후 적용)

1. **파일 이동**: `ui/.../presenters/` → `presentation/presenters/`
2. **Factory Import 수정**: 새 경로로 업데이트
3. **UI 폴더 **init**.py 정리**: Presenter Import 모두 제거 ⭐
4. **상위 폴더 **init**.py 확인**: 간접 참조 체인 점검 ⭐
5. **Settings 스크린 패턴 통일**: Factory 패턴으로 일관성 확보 ⭐
6. **UI 테스트**: 각 탭별 정상 동작 확인

**⭐ 표시 항목들이 Phase 2.4에서 새롭게 발견된 핵심 포인트**

---

## 💡 작업 시 주의사항

### 전략 관리 화면 제외 원칙

- **완전 제외**: strategy_management 관련 모든 Presenter는 이동하지 않음
- **기존 동작 보장**: 전략 관리 화면은 현재 구조 그대로 정상 동작해야 함
- **별도 태스크**: TASK_20250930_02에서 전략 관리 화면 전용 이동 작업 진행

### 단계별 안전 적용

#### 순차 진행 원칙

1. **하나씩 이동**: 절대 여러 Presenter 동시 이동 금지
2. **즉시 테스트**: 각 이동 후 바로 `python run_desktop_ui.py` 실행
3. **문제 발생시**: 즉시 이전 상태 롤백 후 원인 분석
4. **성공 확인**: 정상 동작 확인 후 다음 Presenter 진행

### UI 구조 일관성 유지

- **폴더명 통일**: UI 폴더명과 Presenter 폴더명 완전 일치
- **확장성**: 향후 UI 화면 추가시 동일한 구조로 Presenter 추가 가능
- **네비게이션 바 대응**: 각 메뉴별로 명확한 Presenter 위치

---

## 🚀 즉시 시작할 작업 순서

### 1단계: 중복 파일 정리 (위험도 낮음)

```powershell
# Legacy Database Settings Presenter 백업 후 제거
Move-Item "upbit_auto_trading\ui\desktop\screens\settings\presenters\database_settings_presenter.py" "legacy\mvp_restructure_20250930\database_settings_presenter_ui_legacy.py"
```

### 2단계: Settings Presenters 순차 이동 (TASK_04 연계)

```powershell
# 각 Presenter 하나씩 이동 → 테스트 → 다음 진행
Move-Item "ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py

Move-Item "ui\desktop\screens\settings\notification_settings\presenters\notification_settings_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py

# 나머지도 동일하게...
```

### 3단계: Main Window Presenter 신중 이동 (최고 위험도)

```powershell
# 백업 → 이동 → Import 수정 → 테스트 (한 번에 진행)
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "ui\desktop\presenters\main_window_presenter.py" "legacy\mvp_restructure_20250930\main_window_presenter_backup_$timestamp.py"

Move-Item "ui\desktop\presenters\main_window_presenter.py" "presentation\presenters\"
# 즉시 Factory Import 수정
python run_desktop_ui.py
```

### 4단계: Chart View Presenters 이동

```powershell
# UI 구조와 동일한 폴더 생성
New-Item -ItemType Directory -Path "presentation\presenters\chart_view" -Force

# 순차 이동
Move-Item "ui\desktop\screens\chart_view\presenters\window_lifecycle_presenter.py" "presentation\presenters\chart_view\"
python run_desktop_ui.py

Move-Item "ui\desktop\screens\chart_view\presenters\orderbook_presenter.py" "presentation\presenters\chart_view\"
python run_desktop_ui.py
```

### 5단계: Import 경로 일괄 수정

```powershell
# Factory 파일들 Import 경로 수정 (전략 관리 제외)
Get-ChildItem upbit_auto_trading\application\factories -Include *.py | Select-String "ui\.desktop.*presenters" -List | Where-Object { $_ -notmatch "strategy" }
```

### 6단계: 최종 정리 및 검증

```powershell
# 빈 presenters 폴더 제거 (전략 관리 제외)
Get-ChildItem upbit_auto_trading\ui -Recurse -Directory -Name "presenters" | Where-Object { $_ -notmatch "strategy_management" } | ForEach-Object {
    $path = "upbit_auto_trading\ui\$_"
    if ((Get-ChildItem $path -File -ErrorAction SilentlyContinue).Count -eq 0) {
        Remove-Item $path -Recurse -Force
        Write-Host "✅ 빈 폴더 제거: $path"
    }
}

# 최종 통합 테스트
python run_desktop_ui.py
```

---

## 🔗 연관 태스크

### 선행 태스크

- **TASK_01**: Container 사용법 확립 (완료)
- **TASK_02**: API Settings Factory 완성 (완료)
- **TASK_03**: Database Settings Factory 완성 (완료)

### 병행 태스크

- **TASK_04**: 나머지 Settings Factory 수정 (병행 진행)

### 후속 태스크

- **TASK_20250930_02**: 전략 관리 Presenter 이동 (별도 태스크)
- **TASK_E**: 통합 테스트 및 성능 검증

### 종속성

- **TASK_04 연계**: Settings Presenters 이동이 TASK_04의 Factory 수정과 연결
- **Import 경로**: Factory 파일들이 새로운 Import 경로로 업데이트 필요
- **전략 관리 제외**: strategy_management 관련 모든 작업 제외

---

## 🎉 예상 결과

### 완성된 MVP 아키텍처 (전략 관리 제외)

```text
✅ UI 구조 기반 Presenter 조직화

presentation/presenters/
├── 📄 main_window_presenter.py           ⭐ 이동 완료
├── 📄 settings_presenter.py              ✅ 기존 (탭 관리용)
├── 📁 settings/                          ⭐ UI 구조와 동일
│   ├── 📄 api_settings_presenter.py            ✅ TASK_02
│   ├── 📄 database_settings_presenter.py       ✅ TASK_03
│   ├── 📄 logging_management_presenter.py      ⭐ 이동 완료
│   ├── 📄 logging_config_presenter.py          ⭐ 이동 완료
│   ├── 📄 notification_settings_presenter.py   ⭐ 이동 완료
│   ├── 📄 ui_settings_presenter.py             ⭐ 이동 완료
│   └── 📄 environment_profile_presenter.py     ⭐ 이동 완료
└── 📁 chart_view/                        ⭐ UI 구조와 동일
    ├── 📄 window_lifecycle_presenter.py        ⭐ 이동 완료
    └── 📄 orderbook_presenter.py               ⭐ 이동 완료

ui/desktop/screens/strategy_management/   🚫 기존 구조 유지 (별도 태스크)
```

#### 개발자 경험 향상

- ✅ **직관적 구조**: UI 폴더와 동일한 Presenter 폴더 구조
- ✅ **일관된 Import**: `from presentation.presenters.*` 패턴
- ✅ **확장 용이성**: 새 UI 화면 추가시 명확한 Presenter 위치
- ✅ **네비게이션 대응**: 메뉴별 명확한 구조

---

**다음 에이전트 시작점**:

1. 중복 파일 정리 (database_settings_presenter.py Legacy 제거)
2. Settings Presenters 하나씩 안전 이동 (TASK_04와 연계)
3. Main Window Presenter 신중한 이동 (최고 위험도)
4. Chart View Presenters 순차 이동 (UI 구조와 동일)
5. Import 경로 일괄 수정 (전략 관리 제외)
6. 빈 presenters 폴더 정리
7. 최종 통합 테스트 및 검증
8. TASK_20250930_02 (전략 관리 Presenter 이동) 준비

---

**문서 유형**: 아키텍처 정리 태스크 (전략 관리 제외)
**우선순위**: 🏗️ 아키텍처 필수 (MVP 구조 완성을 위한 필수 작업)
**예상 소요 시간**: 2-3시간 (전략 관리 제외로 단축)
**성공 기준**: UI Layer 순수성 + UI 구조 기반 Presenter 조직화 + 정상 동작 보장
