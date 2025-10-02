# 📋 TASK_20250930_02: 전략 관리 Presenter 전용 이동 작업

## 🎯 태스크 목표

### 주요 목표

**복잡한 전략 관리 화면의 안전하고 체계적인 Presenter 이동**

- 전략 관리(Strategy Management) 화면의 모든 Presenter를 안전하게 이동
- 복잡한 탭 구조 및 공유 컴포넌트 관계 정리
- 중복된 trigger_builder_presenter.py 파일 해결
- MVP 패턴 및 Factory 연결 완전 검증
- 트리거 빌더, 전략 메이커 등 핵심 기능의 안정성 보장

### 완료 기준

- ✅ 전략 관리 관련 모든 Presenter를 `presentation/presenters/strategy_management/`로 이동
- ✅ 중복된 trigger_builder_presenter.py 파일 정리
- ✅ 모든 전략 관리 Factory의 Import 경로 업데이트
- ✅ 트리거 빌더, 조건 빌더, 전략 메이커 정상 동작 검증
- ✅ `python run_desktop_ui.py` → Strategy Management 완전 정상 동작

---

## 📊 현재 상황 분석

### 🔍 전략 관리 화면 복잡도 분석

#### UI 구조 현황

```
ui/desktop/screens/strategy_management/
├── tabs/
│   ├── trigger_builder/
│   │   └── presenters/
│   │       └── trigger_builder_presenter.py    🚨 중복 위험
│   ├── strategy_maker/
│   ├── backtesting/
│   └── monitoring/
└── shared/
    └── presenters/
        └── condition_builder_presenter.py      ⭐ 이동 대상
```

#### 기존 Presenter 위치 현황

```
presentation/presenters/
├── strategy_maker_presenter.py          ✅ 이미 존재 (최상위)
├── trigger_builder_presenter.py         ✅ 이미 존재 (최상위)
└── settings/
    └── ... (Settings 관련)

ui/desktop/screens/strategy_management/
├── tabs/trigger_builder/presenters/
│   └── trigger_builder_presenter.py     🚨 중복 파일
└── shared/presenters/
    └── condition_builder_presenter.py   ⭐ 이동 대상
```

### 🚨 중복 파일 문제

- **trigger_builder_presenter.py**: presentation/presenters/와 ui/desktop/screens/strategy_management/tabs/trigger_builder/presenters/ 양쪽 존재
- **전략 메이커**: 이미 presentation/presenters/strategy_maker_presenter.py 존재

### 🎯 목표 구조

```
presentation/presenters/
├── main_window_presenter.py
├── settings_presenter.py               ✅ 탭 관리용
├── strategy_management_presenter.py    ⭐ 신규 생성 (탭 관리용)
├── settings/
│   └── ... (Settings 관련)
└── strategy_management/                ⭐ UI 구조 기반
    ├── trigger_builder_presenter.py    ⭐ 중복 해결 후 이동
    ├── condition_builder_presenter.py  ⭐ shared에서 이동
    └── strategy_maker_presenter.py     ⭐ 최상위에서 이동
```

---

## 🔄 체계적 작업 절차 (7단계)

### Phase 1: 중복 파일 분석 및 해결

#### 1.1 Trigger Builder Presenter 중복 분석

```powershell
# 두 파일 상세 비교
$file1 = "presentation\presenters\trigger_builder_presenter.py"
$file2 = "ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters\trigger_builder_presenter.py"

# 파일 크기 및 최종 수정 시간 비교
Get-Item $file1, $file2 | Select-Object Name, Length, LastWriteTime

# 내용 상세 비교
Compare-Object (Get-Content $file1) (Get-Content $file2) | Measure-Object
```

#### 1.2 최신/완전한 버전 결정

```powershell
# 내용 차이가 있는 경우 수동 검토
Compare-Object (Get-Content $file1) (Get-Content $file2) | Select-Object InputObject, SideIndicator

# 더 완전한 버전을 기준으로 Legacy 버전 백업 후 제거
```

#### 1.3 Factory Import 현황 확인

```powershell
# Trigger Builder를 Import하는 모든 Factory 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "trigger_builder_presenter" -Context 2
```

### Phase 2: 전략 관리 탭 Presenter 생성

#### 2.1 Strategy Management Presenter 생성

```python
# presentation/presenters/strategy_management_presenter.py
"""
전략 관리 탭 통합 Presenter

전략 관리 화면의 탭 전환 및 상태 관리를 담당합니다.
- Trigger Builder 탭
- Strategy Maker 탭
- Backtesting 탭
- Monitoring 탭
"""

class StrategyManagementPresenter:
    """전략 관리 화면 탭 관리 Presenter"""

    def __init__(self, view):
        self.view = view
        self._current_tab = None

    def initialize(self):
        """초기화 및 기본 탭 설정"""
        self._setup_tab_navigation()
        self.switch_to_trigger_builder()

    def switch_to_trigger_builder(self):
        """트리거 빌더 탭으로 전환"""
        pass

    def switch_to_strategy_maker(self):
        """전략 메이커 탭으로 전환"""
        pass

    def switch_to_backtesting(self):
        """백테스팅 탭으로 전환"""
        pass

    def switch_to_monitoring(self):
        """모니터링 탭으로 전환"""
        pass
```

### Phase 3: Strategy Management 폴더 구조 생성

#### 3.1 폴더 생성 및 초기화

```powershell
# UI 구조와 동일한 폴더 생성
New-Item -ItemType Directory -Path "presentation\presenters\strategy_management" -Force

# __init__.py 생성
New-Item -ItemType File -Path "presentation\presenters\strategy_management\__init__.py" -Force
```

#### 3.2 **init**.py 초기화

```python
# presentation/presenters/strategy_management/__init__.py
"""
Strategy Management Presenters

전략 관리 화면 관련 모든 Presenter들을 포함합니다.
"""

from .trigger_builder_presenter import TriggerBuilderPresenter
from .condition_builder_presenter import ConditionBuilderPresenter
from .strategy_maker_presenter import StrategyMakerPresenter

__all__ = [
    'TriggerBuilderPresenter',
    'ConditionBuilderPresenter',
    'StrategyMakerPresenter'
]
```

### Phase 4: 순차적 Presenter 이동

#### 4.1 Condition Builder Presenter 이동 (가장 안전)

```powershell
# 1. 백업
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "ui\desktop\screens\strategy_management\shared\presenters\condition_builder_presenter.py" "legacy\mvp_restructure_20250930\condition_builder_presenter_backup_$timestamp.py"

# 2. 이동
Move-Item "ui\desktop\screens\strategy_management\shared\presenters\condition_builder_presenter.py" "presentation\presenters\strategy_management\"

# 3. 즉시 테스트
python run_desktop_ui.py
# Strategy Management → Trigger Builder 접근하여 조건 빌더 동작 확인
```

#### 4.2 Trigger Builder Presenter 중복 해결 후 이동

```powershell
# 1. 중복 해결 (더 완전한 버전을 기준으로)
# 예: presentation 쪽이 더 최신인 경우
Move-Item "ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters\trigger_builder_presenter.py" "legacy\mvp_restructure_20250930\trigger_builder_presenter_ui_legacy.py"

# 2. presentation 쪽 파일을 strategy_management 폴더로 이동
Move-Item "presentation\presenters\trigger_builder_presenter.py" "presentation\presenters\strategy_management\"

# 3. 즉시 테스트
python run_desktop_ui.py
# Strategy Management → Trigger Builder 탭 정상 동작 확인
```

#### 4.3 Strategy Maker Presenter 이동

```powershell
# 1. 백업
Copy-Item "presentation\presenters\strategy_maker_presenter.py" "legacy\mvp_restructure_20250930\strategy_maker_presenter_backup_$timestamp.py"

# 2. 이동
Move-Item "presentation\presenters\strategy_maker_presenter.py" "presentation\presenters\strategy_management\"

# 3. 즉시 테스트
python run_desktop_ui.py
# Strategy Management → Strategy Maker 탭 정상 동작 확인
```

### Phase 5: Factory Import 경로 수정

#### 5.1 전략 관리 관련 Factory 파일 확인

```powershell
# 전략 관리 관련 Factory 파일들 찾기
Get-ChildItem upbit_auto_trading\application\factories -Include *.py | Select-String "strategy.*factory\|trigger.*factory" -List
```

#### 5.2 Import 경로 일괄 수정

```python
# 예상 수정 패턴들

# Trigger Builder Factory
# Before:
from upbit_auto_trading.presentation.presenters.trigger_builder_presenter import TriggerBuilderPresenter
# After:
from upbit_auto_trading.presentation.presenters.strategy_management.trigger_builder_presenter import TriggerBuilderPresenter

# Strategy Maker Factory
# Before:
from upbit_auto_trading.presentation.presenters.strategy_maker_presenter import StrategyMakerPresenter
# After:
from upbit_auto_trading.presentation.presenters.strategy_management.strategy_maker_presenter import StrategyMakerPresenter

# Condition Builder Factory
# Before:
from upbit_auto_trading.ui.desktop.screens.strategy_management.shared.presenters.condition_builder_presenter import ConditionBuilderPresenter
# After:
from upbit_auto_trading.presentation.presenters.strategy_management.condition_builder_presenter import ConditionBuilderPresenter
```

### Phase 6: 전략 관리 Presenter 생성 및 연결

#### 6.1 Strategy Management Presenter 완성

```python
# presentation/presenters/strategy_management_presenter.py 완전 구현
class StrategyManagementPresenter:
    def __init__(self, view, trigger_builder_factory, strategy_maker_factory, condition_builder_factory):
        self.view = view
        self.trigger_builder_factory = trigger_builder_factory
        self.strategy_maker_factory = strategy_maker_factory
        self.condition_builder_factory = condition_builder_factory

    def initialize(self):
        """전략 관리 화면 초기화"""
        self._setup_tabs()
        self.load_trigger_builder_tab()

    def _setup_tabs(self):
        """탭 구조 설정"""
        self.view.setup_tab_widget()

    def load_trigger_builder_tab(self):
        """트리거 빌더 탭 로드"""
        trigger_builder_widget = self.trigger_builder_factory.create_component_instance(self.view)
        self.view.add_tab(trigger_builder_widget, "Trigger Builder")

    def load_strategy_maker_tab(self):
        """전략 메이커 탭 로드"""
        strategy_maker_widget = self.strategy_maker_factory.create_component_instance(self.view)
        self.view.add_tab(strategy_maker_widget, "Strategy Maker")
```

#### 6.2 Strategy Management Factory 생성/수정

```python
# application/factories/strategy_management_factory.py
class StrategyManagementFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        from upbit_auto_trading.presentation.presenters.strategy_management_presenter import StrategyManagementPresenter

        # 하위 Factory들 주입
        trigger_builder_factory = self._get_trigger_builder_factory()
        strategy_maker_factory = self._get_strategy_maker_factory()
        condition_builder_factory = self._get_condition_builder_factory()

        view = StrategyManagementView(parent)
        presenter = StrategyManagementPresenter(
            view=view,
            trigger_builder_factory=trigger_builder_factory,
            strategy_maker_factory=strategy_maker_factory,
            condition_builder_factory=condition_builder_factory
        )

        view.set_presenter(presenter)
        presenter.initialize()

        return view
```

### Phase 7: 빈 Presenters 폴더 정리 및 최종 검증

#### 7.1 전략 관리 관련 빈 폴더 제거

```powershell
# 전략 관리 관련 빈 presenters 폴더 제거
$strategyFolders = @(
    "upbit_auto_trading\ui\desktop\screens\strategy_management\shared\presenters",
    "upbit_auto_trading\ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters"
)

foreach ($folder in $strategyFolders) {
    if (Test-Path $folder) {
        $files = Get-ChildItem $folder -File -ErrorAction SilentlyContinue
        if ($files.Count -eq 0) {
            Remove-Item $folder -Recurse -Force
            Write-Host "✅ 빈 폴더 제거: $folder"
        }
    }
}
```

#### 7.2 전략 관리 기능 완전 검증

```powershell
# 전체 전략 관리 기능 테스트
python run_desktop_ui.py

# 검증 체크리스트:
# 1. Strategy Management 메뉴 접근
# 2. Trigger Builder 탭 정상 로드 및 기능 동작
# 3. Strategy Maker 탭 정상 로드 및 기능 동작
# 4. 조건 빌더 (Condition Builder) 정상 동작
# 5. 탭 간 전환 정상 동작
# 6. 7규칙 전략 생성 및 저장 테스트
```

---

## 🛠️ 구체적 구현 계획

### 중복 해결 전략

```powershell
# Trigger Builder Presenter 중복 해결 단계별 가이드

# 1단계: 파일 비교 분석
$presentationFile = "presentation\presenters\trigger_builder_presenter.py"
$uiFile = "ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters\trigger_builder_presenter.py"

# 파일 정보 비교
Get-Item $presentationFile, $uiFile | Format-Table Name, Length, LastWriteTime

# 2단계: 내용 차이 확인
$diff = Compare-Object (Get-Content $presentationFile) (Get-Content $uiFile)
if ($diff) {
    Write-Host "⚠️ 파일 내용 차이 발견 - 수동 검토 필요"
    $diff | Select-Object InputObject, SideIndicator
} else {
    Write-Host "✅ 파일 내용 동일 - 안전하게 중복 제거 가능"
}

# 3단계: Factory Import 현황 확인
Get-ChildItem upbit_auto_trading -Recurse -Include *.py | Select-String "trigger_builder_presenter" | Select-Object Filename, Line
```

### Factory 수정 패턴

```python
# 전략 관리 관련 Factory들의 Import 경로 수정

# 1. Trigger Builder Factory
class TriggerBuilderFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # 새로운 경로
        from upbit_auto_trading.presentation.presenters.strategy_management.trigger_builder_presenter import TriggerBuilderPresenter

        # 기존 로직 유지
        app_container = self._get_application_container()
        # ... 서비스 주입

        view = TriggerBuilderView(parent)
        presenter = TriggerBuilderPresenter(view=view, **services)

        return view

# 2. Strategy Management Factory (상위)
class StrategyManagementFactory(BaseComponentFactory):
    def create_component_instance(self, parent, **kwargs):
        # 탭 관리용 Presenter
        from upbit_auto_trading.presentation.presenters.strategy_management_presenter import StrategyManagementPresenter

        # 하위 탭 Factory들
        trigger_factory = self._container.get_factory("trigger_builder")
        strategy_factory = self._container.get_factory("strategy_maker")

        view = StrategyManagementView(parent)
        presenter = StrategyManagementPresenter(
            view=view,
            trigger_factory=trigger_factory,
            strategy_factory=strategy_factory
        )

        return view
```

---

## 🎯 성공 기준

### 기술적 검증

#### 전략 관리 아키텍처 완성

- ✅ **중복 해결**: trigger_builder_presenter.py 중복 완전 해결
- ✅ **폴더 구조**: UI 구조와 동일한 strategy_management 폴더 완성
- ✅ **탭 관리**: strategy_management_presenter.py로 탭 전환 관리
- ✅ **Import 일관성**: 모든 전략 관리 Presenter가 동일한 경로 사용

#### MVP 패턴 완성

- ✅ **Factory 연결**: 모든 전략 관리 Factory의 새로운 Import 경로
- ✅ **Presenter 분리**: 각 기능별 Presenter 명확한 역할 분담
- ✅ **View 연결**: Factory를 통한 올바른 MVP 조립

### 기능 검증

#### 핵심 전략 관리 기능

1. **Trigger Builder**: 트리거 조건 설정 및 7규칙 구성
2. **Strategy Maker**: 전략 생성, 편집, 저장
3. **Condition Builder**: 공통 조건 설정 컴포넌트
4. **탭 전환**: 각 탭 간 원활한 전환 및 상태 유지

#### 엔드투엔드 테스트

1. **앱 시작**: `python run_desktop_ui.py` 정상 실행
2. **전략 관리 접근**: Strategy Management 메뉴 정상 로드
3. **7규칙 전략 생성**: 트리거 빌더에서 7규칙 전략 완전 구성 가능
4. **전략 저장/로드**: 전략 저장 후 재로드 정상 동작
5. **탭 기능**: 모든 탭의 개별 기능 정상 동작

---

## 💡 작업 시 주의사항

### 전략 관리 특수성

- **핵심 기능**: 7규칙 전략 생성이 최종 목표이므로 기능 손실 절대 금지
- **복잡한 구조**: 탭, 공유 컴포넌트, Factory 관계가 복잡하므로 단계별 검증 필수
- **중복 해결**: trigger_builder_presenter.py 중복은 신중하게 처리

### 안전한 이동 전략

#### 단계별 검증

1. **파일 이동 후 즉시 테스트**: 각 Presenter 이동 후 바로 기능 확인
2. **중복 해결 우선**: 중복 파일 문제 먼저 해결 후 이동 진행
3. **Factory 수정 동기화**: Presenter 이동과 Factory Import 수정 동시 진행
4. **롤백 준비**: 문제 발생시 즉시 이전 상태로 복원 가능하도록 백업

### 7규칙 전략 무결성

- **RSI 과매도 진입**: 트리거 조건 설정 정상 동작
- **수익시 불타기**: 추가 매수 로직 정상 동작
- **계획된 익절**: 목표가 도달시 매도 로직
- **트레일링 스탑**: 동적 손절가 조정
- **하락시 물타기**: 추가 매수 조건
- **급락 감지**: 급락 상황 대응
- **급등 감지**: 급등 상황 대응

---

## 🚀 즉시 시작할 작업 순서

### 1단계: 중복 파일 상세 분석

```powershell
# Trigger Builder 중복 파일 분석
$file1 = "presentation\presenters\trigger_builder_presenter.py"
$file2 = "ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters\trigger_builder_presenter.py"

Write-Host "=== 파일 정보 비교 ==="
Get-Item $file1, $file2 | Format-Table Name, Length, LastWriteTime

Write-Host "=== 내용 차이 분석 ==="
$diff = Compare-Object (Get-Content $file1) (Get-Content $file2)
if ($diff) {
    Write-Host "⚠️ 차이 발견: $($diff.Count) 줄"
} else {
    Write-Host "✅ 파일 내용 동일"
}
```

### 2단계: Strategy Management 폴더 구조 생성

```powershell
# 폴더 및 초기 파일 생성
New-Item -ItemType Directory -Path "presentation\presenters\strategy_management" -Force
New-Item -ItemType File -Path "presentation\presenters\strategy_management\__init__.py" -Force

Write-Host "✅ Strategy Management 폴더 구조 생성 완료"
```

### 3단계: 가장 안전한 Condition Builder부터 이동

```powershell
# 1. 백업
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "ui\desktop\screens\strategy_management\shared\presenters\condition_builder_presenter.py" "legacy\mvp_restructure_20250930\condition_builder_presenter_backup_$timestamp.py"

# 2. 이동
Move-Item "ui\desktop\screens\strategy_management\shared\presenters\condition_builder_presenter.py" "presentation\presenters\strategy_management\"

# 3. 즉시 테스트
python run_desktop_ui.py
Write-Host "Condition Builder 이동 완료 - Strategy Management 화면에서 조건 빌더 동작 확인 필요"
```

### 4단계: Trigger Builder 중복 해결 및 이동

```powershell
# 중복 해결 후 이동 (더 완전한 버전 확인 후)
# 예: presentation 쪽이 더 최신인 경우
Move-Item "ui\desktop\screens\strategy_management\tabs\trigger_builder\presenters\trigger_builder_presenter.py" "legacy\mvp_restructure_20250930\trigger_builder_ui_legacy.py"

Move-Item "presentation\presenters\trigger_builder_presenter.py" "presentation\presenters\strategy_management\"

python run_desktop_ui.py
Write-Host "Trigger Builder 이동 완료 - 7규칙 전략 구성 기능 확인 필요"
```

### 5단계: Strategy Maker 이동

```powershell
# Strategy Maker 이동
Copy-Item "presentation\presenters\strategy_maker_presenter.py" "legacy\mvp_restructure_20250930\strategy_maker_backup_$timestamp.py"
Move-Item "presentation\presenters\strategy_maker_presenter.py" "presentation\presenters\strategy_management\"

python run_desktop_ui.py
Write-Host "Strategy Maker 이동 완료 - 전략 생성 및 편집 기능 확인 필요"
```

### 6단계: Factory Import 경로 일괄 수정

```powershell
# 전략 관리 관련 Factory 파일들 Import 수정
Get-ChildItem upbit_auto_trading\application\factories -Include *.py | Select-String "trigger_builder_presenter\|strategy_maker_presenter\|condition_builder_presenter" -List

Write-Host "Factory Import 경로 수정 필요 - 각 Factory 파일 개별 수정 진행"
```

### 7단계: 최종 검증

```powershell
# 전략 관리 완전 검증
python run_desktop_ui.py

Write-Host "=== 최종 검증 체크리스트 ==="
Write-Host "1. Strategy Management 메뉴 접근"
Write-Host "2. Trigger Builder 탭 - 7규칙 전략 구성"
Write-Host "3. Strategy Maker 탭 - 전략 생성/편집"
Write-Host "4. 조건 빌더 컴포넌트 정상 동작"
Write-Host "5. 탭 간 전환 및 상태 유지"
```

---

## 🔗 연관 태스크

### 선행 태스크

- **TASK_20250930_01**: 다른 Presenter 이동 (병행 가능)

### 후속 태스크

- **TASK_E**: 통합 테스트 및 성능 검증

### 종속성

- **독립적 수행 가능**: 다른 Presenter 이동과 독립적으로 수행
- **Factory 수정**: 전략 관리 관련 Factory들의 Import 경로 수정 필요
- **7규칙 검증**: 최종적으로 7규칙 전략 생성 기능 완전 검증

---

## 🎉 예상 결과

### 완성된 전략 관리 아키텍처

```text
✅ 전략 관리 Presenter 완전 조직화

presentation/presenters/
├── 📄 strategy_management_presenter.py   ⭐ 탭 관리용 (신규)
└── 📁 strategy_management/              ⭐ UI 구조와 동일
    ├── 📄 trigger_builder_presenter.py        ⭐ 중복 해결 후 이동
    ├── 📄 condition_builder_presenter.py      ⭐ shared에서 이동
    └── 📄 strategy_maker_presenter.py         ⭐ 최상위에서 이동

ui/desktop/screens/strategy_management/   ✅ Pure View만 남음
├── 📁 tabs/                             ✅ View Components
└── 📁 shared/                           ✅ View Components
```

#### 전략 관리 기능 완성

- ✅ **7규칙 전략**: RSI 과매도, 불타기, 익절, 트레일링 스탑, 물타기, 급락/급등 감지
- ✅ **트리거 빌더**: 복잡한 조건 조합 및 트리거 설정
- ✅ **전략 메이커**: 전략 생성, 편집, 저장, 로드
- ✅ **조건 빌더**: 공통 조건 설정 컴포넌트
- ✅ **탭 관리**: 원활한 탭 전환 및 상태 유지

#### 시스템 안정성

- ✅ **중복 해결**: trigger_builder_presenter.py 중복 완전 해결
- ✅ **Factory 연결**: 모든 전략 관리 Factory 정상 동작
- ✅ **MVP 패턴**: 완전한 View-Presenter-Model 분리
- ✅ **확장성**: 새로운 전략 기능 추가시 명확한 구조

---

**다음 에이전트 시작점**:

1. Trigger Builder 중복 파일 상세 분석 및 해결
2. Strategy Management 폴더 구조 생성
3. Condition Builder 안전한 이동 (가장 위험도 낮음)
4. Trigger Builder 중복 해결 후 이동
5. Strategy Maker 이동
6. 전략 관리 Factory Import 경로 수정
7. Strategy Management Presenter 생성 및 탭 관리 구현
8. 7규칙 전략 생성 기능 완전 검증

---

**문서 유형**: 전략 관리 전용 이동 태스크
**우선순위**: 🎯 핵심 기능 (7규칙 전략 생성 핵심 기능)
**예상 소요 시간**: 3-4시간 (복잡한 구조로 인한 신중한 진행)
**성공 기준**: 전략 관리 완전 이동 + 7규칙 전략 무결성 + 중복 파일 해결 완료
