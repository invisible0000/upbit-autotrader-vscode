# TASK-20250803-13

## Title
Presentation Layer - View 리팩토링 및 Passive View 구현

## Objective (목표)
기존 UI 컴포넌트들을 Passive View 패턴으로 리팩토링하여 모든 비즈니스 로직을 제거하고, UI는 순수한 표시와 사용자 입력 전달 기능만 담당하도록 합니다. MVP 패턴의 View 계층을 완성합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 4: Presentation Layer 리팩토링 (3주)" > "4.2 View 리팩토링 (1주)"

## Pre-requisites (선행 조건)
- `TASK-20250803-12`: MVP 패턴 Presenter 구현 완료
- Application Layer Service들과 연동 준비 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 기존 View 비즈니스 로직 식별
- [ ] `ui/desktop/screens/strategy_management/` 내 모든 UI 클래스 분석
- [ ] 각 View에서 제거할 비즈니스 로직 목록 작성
- [ ] View 인터페이스 정의 필요 항목 식별

### 2. **[인터페이스 정의]** View 계약 정의
- [ ] `upbit_auto_trading/presentation/interfaces/view_contracts.py` 생성:
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IBaseView(ABC):
    """모든 View의 기본 인터페이스"""
    @abstractmethod
    def show_loading(self, message: str) -> None: pass
    @abstractmethod
    def hide_loading(self) -> None: pass
    @abstractmethod
    def show_error(self, message: str) -> None: pass
    @abstractmethod
    def show_success(self, message: str) -> None: pass

class IStrategyListView(IBaseView):
    """전략 목록 View 인터페이스"""
    @abstractmethod
    def display_strategies(self, strategies: List[Dict]) -> None: pass
    @abstractmethod
    def clear_selection(self) -> None: pass
    @abstractmethod
    def get_selected_strategy_id(self) -> Optional[str]: pass

class ITriggerBuilderView(IBaseView):
    """트리거 빌더 View 인터페이스"""
    @abstractmethod
    def display_variables(self, variables: List[Dict]) -> None: pass
    @abstractmethod
    def update_condition_preview(self, preview: str) -> None: pass
    @abstractmethod
    def show_compatibility_warning(self, message: str) -> None: pass
    @abstractmethod
    def add_condition_card(self, condition: Dict) -> None: pass
```

### 3. **[리팩토링]** Strategy Management Views
- [ ] `strategy_maker_view.py` 리팩토링:
```python
class StrategyMakerView(QWidget, IStrategyMakerView):
    def __init__(self):
        super().__init__()
        self._presenter: Optional[StrategyMakerPresenter] = None
        self.setup_ui()
    
    def set_presenter(self, presenter: StrategyMakerPresenter) -> None:
        """Presenter 연결 (의존성 주입)"""
        self._presenter = presenter
        self.connect_signals()
    
    def setup_ui(self) -> None:
        """UI 구성만 담당"""
        self.name_input = QLineEdit()
        self.save_button = QPushButton("저장")
        # ... UI 구성 로직만
    
    def _on_save_clicked(self) -> None:
        """사용자 입력을 Presenter로 전달"""
        if not self._presenter:
            return
        strategy_data = self.collect_form_data()
        self._presenter.handle_save_strategy(strategy_data)
    
    def display_validation_errors(self, errors: List[str]) -> None:
        """검증 오류 표시"""
        QMessageBox.warning(self, "입력 오류", "\n".join(errors))
```

### 4. **[리팩토링]** Trigger Builder View
- [ ] `trigger_builder_view.py` 완전 리팩토링:
```python
class TriggerBuilderView(QWidget, ITriggerBuilderView):
    def __init__(self):
        super().__init__()
        self._presenter: Optional[TriggerBuilderPresenter] = None
        self.variable_combo = QComboBox()
        self.operator_combo = QComboBox()
        self.setup_ui()
    
    def _on_variable_changed(self) -> None:
        """변수 선택 변경을 Presenter에 알림"""
        if self._presenter:
            variable = self.variable_combo.currentText()
            self._presenter.handle_variable_selection(variable)
    
    def display_variables(self, variables: List[Dict]) -> None:
        """변수 목록 표시"""
        self.variable_combo.clear()
        for var in variables:
            self.variable_combo.addItem(var['display_name'], var['id'])
    
    def update_compatibility_status(self, is_compatible: bool) -> None:
        """호환성 상태 UI 업데이트"""
        if is_compatible:
            self.status_label.setText("✅ 호환")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("❌ 비호환")
            self.status_label.setStyleSheet("color: red;")
```

### 5. **[리팩토링]** Chart Components
- [ ] 차트 컴포넌트들의 데이터 로직 제거
- [ ] 순수 표시 기능만 유지

### 6. **[통합]** View Factory 및 DI 연동
- [ ] `presentation/view_factory.py` 생성:
```python
class ViewFactory:
    def __init__(self, container: DIContainer):
        self._container = container
    
    def create_strategy_maker_view(self) -> StrategyMakerView:
        """전략 메이커 View 생성 및 Presenter 연결"""
        view = StrategyMakerView()
        presenter = self._container.resolve(StrategyMakerPresenter)
        presenter.set_view(view)
        view.set_presenter(presenter)
        return view
```

### 7. **[테스트]** View 단위 테스트
- [ ] `tests/presentation/views/` 폴더 생성
- [ ] View별 단위 테스트 작성:
```python
def test_strategy_maker_view_user_input():
    # Given
    view = StrategyMakerView()
    mock_presenter = Mock()
    view.set_presenter(mock_presenter)
    
    # When
    view.name_input.setText("테스트 전략")
    QTest.mouseClick(view.save_button, Qt.LeftButton)
    
    # Then
    mock_presenter.handle_save_strategy.assert_called_once()
```

## Verification Criteria (완료 검증 조건)

### **[Passive View 확인]**
- [ ] 모든 View 클래스에서 비즈니스 로직 완전 제거
- [ ] View가 Presenter만 호출하고 다른 서비스 직접 접근 안함
- [ ] UI 이벤트가 모두 Presenter로 위임됨

### **[View 인터페이스 준수]**
- [ ] 모든 View가 해당 인터페이스 구현
- [ ] Presenter가 View 인터페이스만 참조

### **[기능 동작 확인]**
- [ ] 기존 UI 기능이 모두 정상 동작
- [ ] 사용자 상호작용이 올바르게 처리됨

## Notes (주의사항)
- View는 표시와 입력 전달만 담당
- 모든 상태 관리는 Presenter에서 처리
- PyQt6 시그널/슬롯은 View 내부에서만 사용
