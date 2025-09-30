# 📋 TASK_20250930_01: Presenter 안전 단계별 이동 작업

## 🎯 태스크 목표

### 주요 목표

**MVP 아키텍처 완성을 위한 모든 Presenter의 안전한 단계별 이동**

- UI 계층에 흩어져 있는 모든 Presenter를 Presentation 계층으로 통합 이동
- DDD + Clean Architecture 준수: UI Layer는 순수 View만, Presentation Layer에 모든 Presenter 집중
- 중복 파일 정리 및 Import 경로 충돌 해결
- 각 이동 단계마다 검증하여 시스템 안정성 보장

### 완료 기준

- ✅ UI 계층(`ui/desktop/**/presenters/`)에서 모든 Presenter 제거
- ✅ Presentation 계층(`presentation/presenters/`)에 체계적으로 조직화
- ✅ 모든 Factory와 View의 Import 경로 업데이트
- ✅ `python run_desktop_ui.py` 실행 시 모든 기능 정상 동작
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

### 🔄 이동 대상 Presenters (14개 파일)

#### Phase 1: 중복 파일 정리 (2개)

```
🚨 중복 위험 파일들
├── ui/desktop/screens/settings/presenters/database_settings_presenter.py  (Legacy - 삭제)
└── ui/desktop/screens/strategy_management/tabs/trigger_builder/presenters/trigger_builder_presenter.py  (중복 확인 필요)
```

#### Phase 2: Settings Presenters (4개) - TASK_04 연계

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

#### Phase 4: Strategy Management Presenters (1개)

```
ui/desktop/screens/strategy_management/shared/presenters/ → presentation/presenters/strategy/
└── condition_builder_presenter.py
```

#### Phase 5: Chart View Presenters (2개)

```
ui/desktop/screens/chart_view/presenters/ → presentation/presenters/chart/
├── window_lifecycle_presenter.py
└── orderbook_presenter.py
```

### 🎯 목표 구조

```
presentation/presenters/
├── main_window_presenter.py
├── settings_presenter.py
├── strategy_management_presenter.py (예정)
├── settings/
│   ├── api_settings_presenter.py
│   ├── database_settings_presenter.py
│   ├── logging_management_presenter.py
│   ├── logging_config_presenter.py
│   ├── notification_settings_presenter.py
│   ├── ui_settings_presenter.py
│   └── environment_profile_presenter.py
├── strategy_management/
│   ├── condition_builder_presenter.py
│   ├── trigger_builder_presenter.py
│   └── strategy_maker_presenter.py
└── chart_view/
    ├── window_lifecycle_presenter.py
    └── orderbook_presenter.py
```

---

## 🔄 체계적 작업 절차 (8단계)

### Phase 1: 중복 파일 안전 정리

#### 1.1 Legacy Database Settings Presenter 제거

```powershell
# 현재 사용중인 Import 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "ui\.desktop\.screens\.settings\.presenters\.database_settings_presenter"

# 안전하게 백업 후 제거
Move-Item "upbit_auto_trading\ui\desktop\screens\settings\presenters\database_settings_presenter.py" "legacy\mvp_restructure_20250930\database_settings_presenter_ui_legacy.py"
```

#### 1.2 Trigger Builder Presenter 중복 해결

```powershell
# 두 파일 내용 비교
Compare-Object (Get-Content "presentation\presenters\trigger_builder_presenter.py") (Get-Content "ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters\trigger_builder_presenter.py")

# 더 최신/완전한 버전 확인 후 구버전 제거
```

### Phase 2: Settings Presenters 일괄 이동 (TASK_04 연계)

#### 2.1 Settings 하위 폴더 확인

```powershell
# 이동 대상 확인
Get-ChildItem "ui\desktop\screens\settings" -Recurse -Include "*presenter*.py" | Select-Object Name, Directory
```

#### 2.2 순차적 이동

```powershell
# 하나씩 안전하게 이동
Move-Item "ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter.py" "presentation\presenters\settings\"
Move-Item "ui\desktop\screens\settings\logging_management\presenters\logging_config_presenter.py" "presentation\presenters\settings\"
Move-Item "ui\desktop\screens\settings\notification_settings\presenters\notification_settings_presenter.py" "presentation\presenters\settings\"
Move-Item "ui\desktop\screens\settings\ui_settings\presenters\ui_settings_presenter.py" "presentation\presenters\settings\"
Move-Item "ui\desktop\screens\settings\environment_profile\presenters\environment_profile_presenter.py" "presentation\presenters\settings\"
```

#### 2.3 각 이동 후 즉시 테스트

```powershell
# 각 파일 이동 후 바로 테스트
python run_desktop_ui.py
# Settings 화면 접근 및 해당 탭 동작 확인
```

### Phase 3: Main Window Presenter 이동 (최고 위험도)

#### 3.1 Main Window 의존성 분석

```powershell
# Main Window Presenter를 참조하는 모든 파일 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "ui\.desktop\.presenters\.main_window_presenter"
```

#### 3.2 Factory 파일 Import 경로 준비

```python
# 예상 수정 대상
# Before: from upbit_auto_trading.ui.desktop.presenters.main_window_presenter import MainWindowPresenter
# After:  from upbit_auto_trading.presentation.presenters.main_window_presenter import MainWindowPresenter
```

#### 3.3 안전한 이동 및 즉시 수정

```powershell
# 1. Main Window Presenter 이동
Move-Item "ui\desktop\presenters\main_window_presenter.py" "presentation\presenters\"

# 2. 즉시 Import 경로 수정 (동시에 진행)
# 3. 바로 테스트 실행
python run_desktop_ui.py
```

### Phase 4: Strategy Management Presenters 이동

#### 4.1 Strategy 폴더 생성 및 이동

```powershell
# Strategy 폴더 생성
New-Item -ItemType Directory -Path "presentation\presenters\strategy" -Force

# Condition Builder Presenter 이동
Move-Item "ui\desktop\screens\strategy_management\shared\presenters\condition_builder_presenter.py" "presentation\presenters\strategy\"
```

### Phase 5: Chart View Presenters 이동

#### 5.1 Chart 폴더 생성 및 이동

```powershell
# Chart 폴더 생성
New-Item -ItemType Directory -Path "presentation\presenters\chart" -Force

# Chart 관련 Presenters 이동
Move-Item "ui\desktop\screens\chart_view\presenters\window_lifecycle_presenter.py" "presentation\presenters\chart\"
Move-Item "ui\desktop\screens\chart_view\presenters\orderbook_presenter.py" "presentation\presenters\chart\"
```

### Phase 6: Import 경로 일괄 수정

#### 6.1 모든 Factory 파일 수정

```powershell
# Factory 파일들에서 Import 경로 검색
Get-ChildItem upbit_auto_trading -Recurse -Include "*factory*.py" | Select-String "ui\.desktop.*presenters"
```

#### 6.2 View 파일들 Import 경로 수정

```powershell
# View 파일들에서 Presenter Import 검색
Get-ChildItem upbit_auto_trading -Recurse -Include "*.py" | Select-String "from.*ui\.desktop.*presenters"
```

### Phase 7: 빈 Presenters 폴더 정리

#### 7.1 빈 폴더 탐지 및 제거

```powershell
# 빈 presenters 폴더들 찾기
Get-ChildItem upbit_auto_trading -Recurse -Directory -Name "presenters" | ForEach-Object {
    $path = "upbit_auto_trading\$_"
    if ((Get-ChildItem $path -File).Count -eq 0) {
        Write-Host "빈 폴더 발견: $path"
        Remove-Item $path -Recurse -Force
    }
}
```

### Phase 8: 최종 통합 검증

#### 8.1 전체 시스템 테스트

```powershell
# 전체 앱 기능 테스트
python run_desktop_ui.py
# 1. Main Window 정상 로드
# 2. Settings → 6개 탭 모두 접근
# 3. Strategy Management 정상 동작
# 4. Chart View 정상 표시
```

#### 8.2 Import 경로 정리 확인

```powershell
# UI 계층에서 Presenter Import 잔재 확인 (있으면 안됨)
Get-ChildItem upbit_auto_trading\ui -Recurse -Include *.py | Select-String "from.*presenters" | Where-Object { $_ -notmatch "presentation\.presenters" }
```

---

## 🛠️ 구체적 구현 계획

### Main Window Presenter 이동 (최고 위험)

#### 현재 Import 패턴 분석

```python
# 예상 Factory 위치: upbit_auto_trading/application/factories/main_window_factory.py
from upbit_auto_trading.ui.desktop.presenters.main_window_presenter import MainWindowPresenter

# 변경될 패턴
from upbit_auto_trading.presentation.presenters.main_window_presenter import MainWindowPresenter
```

#### 안전한 변경 절차

1. **백업**: Main Window 관련 모든 파일 백업
2. **이동**: Presenter 파일 이동
3. **수정**: Factory Import 경로 즉시 수정
4. **테스트**: 즉시 앱 실행 테스트
5. **롤백**: 문제시 즉시 복원

### Settings Presenters 이동 (TASK_04 연계)

#### Settings Factory 수정 패턴

```python
# settings_view_factory.py에서 수정될 Import들
# Before:
from upbit_auto_trading.ui.desktop.screens.settings.logging_management.presenters.logging_management_presenter import LoggingManagementPresenter
from upbit_auto_trading.ui.desktop.screens.settings.notification_settings.presenters.notification_settings_presenter import NotificationSettingsPresenter

# After:
from upbit_auto_trading.presentation.presenters.settings.logging_management_presenter import LoggingManagementPresenter
from upbit_auto_trading.presentation.presenters.settings.notification_settings_presenter import NotificationSettingsPresenter
```

#### 각 Settings Factory별 수정

```python
class LoggingSettingsComponentFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # Import 경로 변경으로 Factory 패턴 동일하게 유지
        from presentation.presenters.settings.logging_management_presenter import LoggingManagementPresenter
        # 나머지 구현은 TASK_04 패턴 적용
```

### Strategy & Chart Presenters 이동

#### 새 폴더 구조 생성

```python
# presentation/presenters/strategy/__init__.py
"""Strategy Management Presenters"""

# presentation/presenters/chart/__init__.py
"""Chart View Presenters"""
```

#### Factory Import 경로 업데이트

```python
# 전략 관련 Factory들
from presentation.presenters.strategy.condition_builder_presenter import ConditionBuilderPresenter

# 차트 관련 Factory들
from presentation.presenters.chart.window_lifecycle_presenter import WindowLifecyclePresenter
from presentation.presenters.chart.orderbook_presenter import OrderbookPresenter
```

---

## 🎯 성공 기준

### 기술적 검증

#### 아키텍처 순수성

- ✅ **UI Layer 순수성**: `ui/` 폴더에서 모든 Presenter 제거 완료
- ✅ **Presentation Layer 통합**: 모든 Presenter가 `presentation/presenters/`에 체계적 조직화
- ✅ **DDD 준수**: UI → Presentation → Application → Infrastructure 계층 준수
- ✅ **Import 경로 일관성**: 모든 Factory와 View가 `presentation.presenters` 경로 사용

#### 파일 구조 정리

- ✅ **중복 제거**: Legacy 파일들 완전 제거
- ✅ **폴더 정리**: 빈 presenters 폴더 모두 제거
- ✅ **백업 보관**: Legacy 파일들 안전하게 백업 폴더에 보관

### 동작 검증

#### 엔드투엔드 테스트

1. **앱 시작**: `python run_desktop_ui.py` 완전 오류 없는 실행
2. **Main Window**: 메인 화면 정상 로드 및 모든 메뉴 접근
3. **Settings**: 6개 설정 탭 모두 정상 접근 및 기능 동작
4. **Strategy Management**: 전략 관리 화면 정상 동작
5. **Chart View**: 차트 화면 정상 표시 및 상호작용
6. **기능 통합**: 모든 MVP 패턴 구성 요소 정상 연결

#### 개별 Presenter 검증

##### Main Window Presenter

- ✅ 메인 메뉴 네비게이션 정상 동작
- ✅ 하위 화면 전환 및 Factory 호출 정상
- ✅ 앱 생명주기 관리 정상

##### Settings Presenters (TASK_04 연계)

- ✅ 모든 Settings Factory에서 새 Import 경로로 Presenter 정상 로드
- ✅ MVP 패턴 연결 정상 (View ↔ Presenter ↔ Service)
- ✅ 각 설정 탭 개별 기능 정상 동작

##### Strategy & Chart Presenters

- ✅ 전략 빌드 및 조건 설정 기능 정상
- ✅ 차트 데이터 표시 및 실시간 업데이트 정상
- ✅ 사용자 상호작용 및 이벤트 처리 정상

### 성능 및 안정성

#### 성능 지표

- ✅ **초기화 시간**: 각 Presenter 로딩 시간 기존 대비 동일 수준
- ✅ **메모리 사용**: Import 경로 변경으로 인한 메모리 사용 최적화
- ✅ **반응성**: UI 상호작용 반응 속도 기존 대비 동일 수준

#### 안정성 지표

- ✅ **오류 방지**: Import 경로 오류 및 ModuleNotFoundError 완전 해결
- ✅ **복구 가능성**: 문제 발생시 Legacy 백업으로 즉시 롤백 가능
- ✅ **확장성**: 새 Presenter 추가시 명확한 위치 및 패턴 제공

---

## 💡 작업 시 주의사항

### 단계별 안전 적용

#### 순차 진행 원칙

1. **하나씩 이동**: 절대 여러 Presenter 동시 이동 금지
2. **즉시 테스트**: 각 이동 후 바로 `python run_desktop_ui.py` 실행
3. **문제 발생시**: 즉시 이전 상태 롤백 후 원인 분석
4. **성공 확인**: 정상 동작 확인 후 다음 Presenter 진행

#### 백업 및 롤백 전략

```powershell
# 각 Presenter 이동 전 백업
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "ui\desktop\presenters\main_window_presenter.py" "legacy\mvp_restructure_20250930\main_window_presenter_backup_$timestamp.py"

# 문제 발생시 롤백
Move-Item "legacy\mvp_restructure_20250930\main_window_presenter_backup_$timestamp.py" "ui\desktop\presenters\main_window_presenter.py"
```

### Import 경로 관리

#### Factory 파일 우선 수정

```python
# Factory에서 Presenter Import 하는 모든 위치 사전 파악
Get-ChildItem upbit_auto_trading\application\factories -Include *.py | Select-String "from.*presenters"
```

#### View 파일 Import 확인

- 대부분의 View는 Factory를 통해 Presenter를 주입받으므로 직접 Import 없을 것으로 예상
- 혹시 직접 Import 하는 View가 있다면 함께 수정

### 중복 파일 처리

#### 안전한 중복 해결

```powershell
# 파일 내용 비교로 동일성 확인
$file1 = Get-Content "presentation\presenters\trigger_builder_presenter.py"
$file2 = Get-Content "ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters\trigger_builder_presenter.py"
Compare-Object $file1 $file2 | Measure-Object | Select-Object Count
```

#### Legacy 파일 보관 규칙

- 삭제 대신 `legacy/mvp_restructure_20250930/` 폴더로 이동
- 파일명에 원래 경로 정보 포함
- 30일 후 정리 예정

---

## 🚀 즉시 시작할 작업 순서

### 1단계: 중복 파일 정리 (위험도 낮음)

```powershell
# Legacy Database Settings Presenter 백업 후 제거
Move-Item "upbit_auto_trading\ui\desktop\screens\settings\presenters\database_settings_presenter.py" "legacy\mvp_restructure_20250930\database_settings_presenter_ui_legacy.py"

# Trigger Builder 중복 확인 후 정리
Compare-Object (Get-Content "presentation\presenters\trigger_builder_presenter.py") (Get-Content "ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters\trigger_builder_presenter.py") -IncludeEqual | Measure-Object
```

### 2단계: Settings Presenters 이동 (TASK_04 연계)

```powershell
# 하나씩 안전하게 이동 (각각 후 테스트)
Move-Item "ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py  # 즉시 테스트

Move-Item "ui\desktop\screens\settings\notification_settings\presenters\notification_settings_presenter.py" "presentation\presenters\settings\"
python run_desktop_ui.py  # 즉시 테스트

# 나머지도 동일하게 진행...
```

### 3단계: Main Window Presenter 이동 (최고 위험도)

```powershell
# 1. 백업
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "ui\desktop\presenters\main_window_presenter.py" "legacy\mvp_restructure_20250930\main_window_presenter_backup_$timestamp.py"

# 2. 의존성 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "ui\.desktop\.presenters\.main_window_presenter"

# 3. 이동 + 즉시 Import 수정 + 테스트 (한번에 진행)
```

### 4단계: 나머지 Presenters 순차 이동

```powershell
# Strategy 폴더 생성 후 이동
New-Item -ItemType Directory -Path "presentation\presenters\strategy" -Force
Move-Item "ui\desktop\screens\strategy_management\shared\presenters\condition_builder_presenter.py" "presentation\presenters\strategy\"

# Chart 폴더 생성 후 이동
New-Item -ItemType Directory -Path "presentation\presenters\chart" -Force
Move-Item "ui\desktop\screens\chart_view\presenters\window_lifecycle_presenter.py" "presentation\presenters\chart\"
Move-Item "ui\desktop\screens\chart_view\presenters\orderbook_presenter.py" "presentation\presenters\chart\"
```

### 5단계: Import 경로 일괄 수정

```powershell
# Factory 파일들 Import 경로 수정
Get-ChildItem upbit_auto_trading\application\factories -Include *.py | Select-String "ui\.desktop.*presenters" -List

# 각 파일별로 수정 적용
```

### 6단계: 최종 정리 및 검증

```powershell
# 빈 presenters 폴더 제거
Get-ChildItem upbit_auto_trading\ui -Recurse -Directory -Name "presenters" | ForEach-Object {
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

- **TASK_E**: 통합 테스트 및 성능 검증 (이 태스크 완료 후)

### 종속성

- **TASK_04 연계**: Settings Presenters 이동이 TASK_04의 Factory 수정과 연결
- **Import 경로**: 모든 Factory 파일들이 새로운 Import 경로로 업데이트 필요

### 전파 효과

#### MVP 아키텍처 완성

- **계층 분리 완성**: UI Layer 순수성 확보 + Presentation Layer 통합 완성
- **DDD 준수**: 모든 Presenter가 올바른 계층에 위치
- **확장성**: 새 Presenter 추가시 명확한 위치 및 패턴

#### 개발 효율성

- **코드 탐색**: 모든 Presenter가 한 곳에 체계적으로 조직화
- **유지보수**: 일관된 Import 경로로 인한 관리 용이성
- **팀 협업**: 명확한 파일 구조로 인한 개발자 이해도 증진

---

## 📚 참고 자료

### MVP 아키텍처 문서

- **`MVP_QUICK_GUIDE.md`**: MVP 패턴 구현 가이드
- **`CURRENT_ARCHITECTURE_ADVANTAGES.md`**: 현재 구조의 올바른 사용법
- **`.github/copilot-instructions.md`**: DDD + MVP 아키텍처 가이드라인

### 기존 성공 사례

- **TASK_02 결과물**: API Settings Factory의 올바른 Import 패턴
- **TASK_03 결과물**: Database Settings Factory의 MVP 구조
- **presentation/presenters/settings/**: 이미 이동된 Presenter들의 구조

### Factory 패턴 참조

- **`upbit_auto_trading/application/factories/`**: 모든 Factory 파일들
- **Import 경로 수정**: Factory에서 Presenter 로딩하는 패턴들

---

## 🎉 예상 결과

### 완성된 MVP 아키텍처

#### 계층별 순수성 달성

```text
✅ 완성된 MVP 계층 구조

ui/ (UI Layer - Pure Views)
├── 📁 desktop/
│   ├── 📁 screens/          ✅ View Components만 존재
│   └── 📁 common/           ✅ UI 공통 리소스만

presentation/ (Presentation Layer - All Presenters)
├── 📁 presenters/
│   ├── 📄 main_window_presenter.py       ⭐ 이동 완료
│   ├── 📄 settings_presenter.py          ✅ 기존
│   ├── 📄 strategy_maker_presenter.py    ✅ 기존
│   ├── 📄 trigger_builder_presenter.py   ✅ 기존
│   ├── 📁 settings/                      ⭐ 확장 완료
│   │   ├── 📄 api_settings_presenter.py            ✅ TASK_02
│   │   ├── 📄 database_settings_presenter.py       ✅ TASK_03
│   │   ├── 📄 logging_management_presenter.py      ⭐ 이동 완료
│   │   ├── 📄 notification_settings_presenter.py   ⭐ 이동 완료
│   │   ├── 📄 ui_settings_presenter.py             ⭐ 이동 완료
│   │   └── 📄 environment_profile_presenter.py     ⭐ 이동 완료
│   ├── 📁 strategy/                      ⭐ 신규 생성
│   │   └── 📄 condition_builder_presenter.py       ⭐ 이동 완료
│   └── 📁 chart/                         ⭐ 신규 생성
│       ├── 📄 window_lifecycle_presenter.py        ⭐ 이동 완료
│       └── 📄 orderbook_presenter.py               ⭐ 이동 완료

application/ (Application Layer - Business Logic)
└── 📁 factories/            ✅ Import 경로 모두 업데이트 완료
```

#### 개발자 경험 향상

- ✅ **직관적 구조**: 모든 Presenter가 `presentation/presenters/`에 체계적 배치
- ✅ **일관된 Import**: `from presentation.presenters.*` 패턴 전체 통일
- ✅ **확장 용이성**: 새 기능 추가시 명확한 파일 위치
- ✅ **유지보수성**: 계층별 역할 분리로 인한 코드 이해 및 수정 용이성

#### 시스템 안정성 확보

- ✅ **아키텍처 준수**: DDD + Clean Architecture + MVP 패턴 완전 구현
- ✅ **의존성 관리**: 계층간 올바른 의존성 방향 확보
- ✅ **테스트 용이성**: 각 Presenter의 독립적 테스트 및 Mock 가능
- ✅ **배포 안정성**: Import 오류 및 경로 문제 완전 해결

---

**다음 에이전트 시작점**:

1. 중복 파일 정리 (database_settings_presenter.py Legacy 제거)
2. Settings Presenters 하나씩 안전 이동 (TASK_04와 연계)
3. Main Window Presenter 신중한 이동 (최고 위험도)
4. Strategy & Chart Presenters 순차 이동
5. 모든 Factory Import 경로 일괄 수정
6. 빈 presenters 폴더 정리
7. 최종 통합 테스트 및 검증
8. TASK_04 (Settings Factory 수정)과 통합 진행

---

**문서 유형**: 아키텍처 정리 태스크
**우선순위**: 🏗️ 아키텍처 필수 (MVP 구조 완성을 위한 필수 작업)
**예상 소요 시간**: 3-4시간 (안전한 단계별 진행)
**성공 기준**: UI Layer 순수성 + Presentation Layer 통합 + 모든 Import 경로 정리 + 정상 동작 보장
