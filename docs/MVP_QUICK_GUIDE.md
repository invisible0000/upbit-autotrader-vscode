# 🚀 MVP 패턴 실용 가이드 (Quick Guide)

## ⚡ 빠른 판단 체크리스트

### MVP 패턴 필요성 즉시 판단 (30초)

```text
[ ] UI 위젯이 5개 이상인가?
[ ] 비즈니스 로직(검증/변환/계산)이 있는가?
[ ] 비동기 작업(API/DB/파일)이 있는가?
[ ] 테스트가 필요한가?
[ ] 다른 곳에서 재사용할 가능성이 있는가?

✅ 3개 이상 체크: MVP 패턴 적용
❌ 2개 이하 체크: 단순 Widget으로 충분
```

### 초급자를 위한 간단 판단법

```python
# 이런 코드가 View에 있다면 MVP 필요!
def on_save_clicked(self):
    # ❌ 검증 로직
    if not self.validate_inputs():
        return

    # ❌ 데이터 변환
    data = self.transform_user_input()

    # ❌ 비즈니스 처리
    result = self.save_to_database(data)

    # ❌ 복잡한 UI 업데이트
    self.update_multiple_widgets(result)
```

## 🎯 3단계 적용 패턴 (15분 구현)

### Step 1: View 인터페이스 정의 (3분)

```python
# 1. interfaces/my_view_interface.py 생성
from typing import Protocol
from PyQt6.QtCore import pyqtSignal

class IMyView(Protocol):
    # View → Presenter 시그널
    save_requested: pyqtSignal = pyqtSignal()
    data_changed: pyqtSignal = pyqtSignal(dict)

    # Presenter → View 메서드
    def update_ui_state(self, data: dict) -> None: ...
    def show_loading(self, loading: bool) -> None: ...
    def show_message(self, message: str) -> None: ...
```

### Step 2: Presenter 구현 (5분)

```python
# 2. presenters/my_presenter.py 생성
from PyQt6.QtCore import QObject, pyqtSignal

class MyPresenter(QObject):
    # Presenter → View 시그널
    ui_update_requested = pyqtSignal(dict)
    loading_state_changed = pyqtSignal(bool)

    def __init__(self, view, service):
        super().__init__()
        self._view = view
        self._service = service
        self._connect_view_signals()

    def _connect_view_signals(self):
        """View 시그널 연결"""
        self._view.save_requested.connect(self.handle_save)
        self.ui_update_requested.connect(self._view.update_ui_state)
        self.loading_state_changed.connect(self._view.show_loading)

    @pyqtSlot()
    def handle_save(self):
        """저장 처리 (비즈니스 로직)"""
        try:
            self.loading_state_changed.emit(True)
            data = self._view.get_form_data()  # View에서 데이터만 수집
            self._service.save(data)  # Service에 위임
            self._view.show_message("저장 완료")
        finally:
            self.loading_state_changed.emit(False)
```

### Step 3: View 연결 (7분)

```python
# 3. 기존 View 클래스에 MVP 패턴 적용
class MyView(QWidget):
    # 시그널 선언
    save_requested = pyqtSignal()
    data_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.presenter = None
        self._setup_ui()
        self._connect_internal_signals()

    def set_presenter(self, presenter):
        """Presenter 주입"""
        self.presenter = presenter

    def _connect_internal_signals(self):
        """내부 위젯 시그널 연결"""
        self.save_button.clicked.connect(self.save_requested.emit)

    # === Presenter가 호출할 메서드들 ===
    def get_form_data(self) -> dict:
        """폼 데이터 수집 (순수 UI 로직)"""
        return {"name": self.name_edit.text()}

    def update_ui_state(self, data: dict):
        """UI 상태 업데이트"""
        self.name_edit.setText(data.get("name", ""))

    def show_loading(self, loading: bool):
        """로딩 상태 표시"""
        self.save_button.setEnabled(not loading)
```

## 🏗️ 계층별 적용 가이드

### Presentation Layer에서의 MVP 역할

```python
# DDD + MVP 통합 구조
┌─────────────────┐
│   UI Event      │ ← 사용자 입력
└─────────────────┘
         │
┌─────────────────┐
│   View          │ ← Passive View (UI만)
│   (PyQt6)       │
└─────────────────┘
         │ 시그널
┌─────────────────┐
│   Presenter     │ ← UI 로직 + 오케스트레이션
│   (Presentation)│
└─────────────────┘
         │
┌─────────────────┐
│ Application     │ ← 비즈니스 로직
│ Service         │
└─────────────────┘
```

### 각 계층의 책임

| 계층 | 책임 | 금지사항 |
|------|------|----------|
| **View** | UI 렌더링, 입력 수집, 시그널 발생 | 비즈니스 로직, 직접 DB/API 호출 |
| **Presenter** | UI 로직, 데이터 변환, 오케스트레이션 | 직접 UI 조작, 도메인 규칙 구현 |
| **Application Service** | 비즈니스 로직, 트랜잭션 관리 | UI 상태 관리, 사용자 입력 처리 |

## 📋 즉시 적용 템플릿

### 완전한 MVP 컴포넌트 템플릿

```python
# === 1. View 인터페이스 ===
class ISettingsView(Protocol):
    settings_changed: pyqtSignal = pyqtSignal(dict)
    save_requested: pyqtSignal = pyqtSignal()

    def update_settings_display(self, settings: dict) -> None: ...
    def set_save_button_state(self, enabled: bool) -> None: ...

# === 2. Presenter 구현 ===
class SettingsPresenter(QObject):
    settings_loaded = pyqtSignal(dict)

    def __init__(self, view: ISettingsView, service):
        super().__init__()
        self._view = view
        self._service = service

        # 시그널 연결
        view.save_requested.connect(self.handle_save)
        self.settings_loaded.connect(view.update_settings_display)

    def handle_save(self):
        try:
            self._view.set_save_button_state(False)
            settings = self._view.get_current_settings()
            self._service.save_settings(settings)
        finally:
            self._view.set_save_button_state(True)

# === 3. View 구현 ===
class SettingsView(QWidget):
    settings_changed = pyqtSignal(dict)
    save_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.presenter = None
        self._setup_ui()

    def set_presenter(self, presenter):
        self.presenter = presenter

    # Presenter 인터페이스 구현
    def get_current_settings(self) -> dict: ...
    def update_settings_display(self, settings: dict): ...
    def set_save_button_state(self, enabled: bool): ...

# === 4. MVP 컨테이너에서 조립 ===
def create_settings_mvp():
    service = container.get_settings_service()
    view = SettingsView()
    presenter = SettingsPresenter(view, service)
    view.set_presenter(presenter)
    return view, presenter
```

### 시그널 연결 표준 패턴

```python
class StandardMVPView(QWidget):
    def _connect_presenter_signals(self):
        """표준 Presenter 시그널 연결 패턴"""
        if not self.presenter:
            return

        # View → Presenter (액션 시그널)
        self.action_requested.connect(self.presenter.handle_action)
        self.data_changed.connect(self.presenter.handle_data_change)

        # Presenter → View (상태 업데이트)
        self.presenter.ui_update_needed.connect(self.update_ui_state)
        self.presenter.loading_changed.connect(self.show_loading_state)
        self.presenter.error_occurred.connect(self.show_error_message)
```

## 🔧 문제 해결 가이드

### 흔한 문제 1: 초기화 순서 오류

```python
# ❌ 문제: View에서 바로 Presenter 메서드 호출
class BadView(QWidget):
    def __init__(self):
        super().__init__()
        self.presenter = SomePresenter(self)
        self.presenter.load_data()  # ❌ 시그널 연결 전 호출

# ✅ 해결: 초기화 완료 후 호출
class GoodView(QWidget):
    def __init__(self):
        super().__init__()
        self.presenter = None

    def set_presenter(self, presenter):
        self.presenter = presenter
        # 모든 연결 완료 후 초기 로드
        QTimer.singleShot(0, presenter.load_initial_data)
```

### 흔한 문제 2: 순환 참조

```python
# ❌ 문제: View ↔ Presenter 강한 결합
class BadPresenter:
    def __init__(self, view):
        self._view = view
        view.presenter = self  # 순환 참조

# ✅ 해결: 약한 참조 또는 의존성 주입
class GoodPresenter:
    def __init__(self, view_interface):
        self._view = view_interface  # 인터페이스만 참조

# MVPContainer에서 연결
def create_mvp():
    view = MyView()
    presenter = MyPresenter(view)  # View 주입
    view.set_presenter(presenter)   # 역방향 연결
```

### 흔한 문제 3: View에서 직접 Service 호출

```python
# ❌ 문제: View에서 직접 비즈니스 로직
class BadView(QWidget):
    def on_save(self):
        data = self.get_form_data()
        # ❌ View에서 직접 Service 호출
        self.service.save(data)

# ✅ 해결: Presenter를 통한 위임
class GoodView(QWidget):
    def on_save(self):
        # ✅ 단순히 시그널만 발생
        self.save_requested.emit()
```

## ⚠️ 안티패턴 회피

### 절대 하지 말아야 할 것들

```python
# ❌ 1. View에서 직접 Presenter 생성
class BadView(QWidget):
    def __init__(self):
        self.presenter = MyPresenter(self)  # DI 패턴 위반

# ❌ 2. Presenter에서 UI 직접 조작
class BadPresenter:
    def handle_save(self):
        self._view.save_button.setText("저장 중...")  # View 캡슐화 위반

# ❌ 3. View에 비즈니스 로직
class BadView(QWidget):
    def on_save(self):
        if self.validate_business_rules():  # 비즈니스 로직 포함
            self.save_to_database()

# ❌ 4. Presenter에서 QWidget 직접 상속
class BadPresenter(QWidget):  # UI 컴포넌트와 결합
    pass

# ❌ 5. 시그널 없이 직접 메서드 호출
class BadView(QWidget):
    def on_button_click(self):
        self.presenter.handle_save()  # 강한 결합
```

### MVP 패턴 위반 자동 탐지

```powershell
# PowerShell로 안티패턴 탐지
# 1. View에서 Service 직접 호출
Get-ChildItem ui\desktop -Recurse -Include *view.py | Select-String "service\."

# 2. Presenter에서 UI 직접 조작
Get-ChildItem presentation\presenters -Recurse | Select-String "\.setText\(|\.setEnabled\("

# 3. View에서 직접 Presenter 생성
Get-ChildItem ui\desktop -Recurse -Include *view.py | Select-String "Presenter\("
```

## ✅ 성공 기준

### MVP 구현 완료 체크리스트

```text
[ ] View 인터페이스가 명확히 정의되었는가?
[ ] View에 비즈니스 로직이 없는가?
[ ] Presenter에서 UI를 직접 조작하지 않는가?
[ ] 시그널/슬롯으로만 통신하는가?
[ ] MVP 컨테이너에서 생성되는가?
[ ] View 없이 Presenter 테스트가 가능한가?
[ ] 순환 참조가 없는가?
```

### 올바른 MVP 검증 테스트

```python
def test_presenter_without_view():
    """View 없이 Presenter 테스트"""
    # Mock View 생성
    mock_view = Mock()
    mock_service = Mock()

    # Presenter 테스트
    presenter = MyPresenter(mock_view, mock_service)
    presenter.handle_save()

    # 검증: Service 호출 여부만 확인
    mock_service.save.assert_called_once()
    # UI 조작은 시그널로만 확인
    mock_view.show_loading.assert_called()

def test_view_signal_emission():
    """View 시그널 발생 테스트"""
    view = MyView()

    with qtbot.waitSignal(view.save_requested):
        view.save_button.click()  # 시그널 발생 확인만
```

### 성공적인 MVP 패턴의 징후

1. **View 코드가 매우 단순함**: UI 구성과 시그널 연결만
2. **Presenter 테스트가 쉬움**: Mock View로 완벽한 테스트
3. **변경 영향이 최소화됨**: UI 변경이 로직에 영향 없음
4. **재사용성이 높음**: 같은 Presenter를 다른 View에 적용 가능

---

**🎯 핵심 원칙**: MVP = "View는 바보, Presenter는 똑똑이"

**⚡ 즉시 적용**: View에 `if`문이 있다면 Presenter로 이동하라!
