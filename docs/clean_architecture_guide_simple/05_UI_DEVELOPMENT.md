# 🎨 UI 개발 가이드 (MVP 패턴)

> **목적**: MVP 패턴 기반 Clean Architecture UI 개발  
> **대상**: LLM 에이전트, UI 개발자  
> **갱신**: 2025-08-03

## 🏗️ MVP 패턴 구조

```
👤 사용자 ↔ 🎨 View ↔ 🎭 Presenter ↔ ⚙️ Service (Application)
              ↑         ↑            ↑
            UI만       조율만        비즈니스
           담당        담당           로직
```

**핵심 원칙**: View는 바보(Passive)여야 하고, Presenter가 모든 로직을 처리

## 🎯 계층별 역할 분리

### 🎨 View (PyQt6 UI)
**✅ 담당**: 표시, 입력 수집, UI 상태 변경  
**❌ 금지**: 비즈니스 로직, 데이터 처리, 외부 호출

### 🎭 Presenter  
**✅ 담당**: View-Service 중재, 입력 변환, UI 로직  
**❌ 금지**: 직접 UI 조작, 복잡한 비즈니스 계산

### ⚙️ Service (Application)
**✅ 담당**: Use Case 실행, 비즈니스 흐름  
**❌ 금지**: UI 참조, View 상태 관리

## 💡 실제 구현: 트리거 생성 UI

### 1단계: 🎨 View 구현
```python
# presentation/views/trigger_builder_view.py
class TriggerBuilderView(QWidget):
    """트리거 생성 UI - Passive View"""
    
    def __init__(self):
        super().__init__()
        self.presenter = None  # Presenter 주입
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성만 담당"""
        layout = QVBoxLayout()
        
        # ✅ UI 요소 생성
        self.variable_combo = QComboBox()
        self.operator_combo = QComboBox()
        self.target_value_input = QLineEdit()
        self.create_button = QPushButton("트리거 생성")
        
        # ✅ 이벤트 연결
        self.create_button.clicked.connect(self.on_create_clicked)
        self.variable_combo.currentTextChanged.connect(self.on_variable_changed)
        
        layout.addWidget(QLabel("변수:"))
        layout.addWidget(self.variable_combo)
        layout.addWidget(QLabel("연산자:"))
        layout.addWidget(self.operator_combo)
        layout.addWidget(QLabel("목표값:"))
        layout.addWidget(self.target_value_input)
        layout.addWidget(self.create_button)
        
        self.setLayout(layout)
    
    # ✅ View의 책임: 이벤트를 Presenter에 전달
    def on_create_clicked(self):
        """생성 버튼 클릭 → Presenter 호출"""
        if self.presenter:
            self.presenter.handle_create_trigger()
            
    def on_variable_changed(self, variable):
        """변수 변경 → Presenter 호출"""
        if self.presenter:
            self.presenter.handle_variable_changed(variable)
    
    # ✅ View의 책임: 데이터 표시
    def update_variable_list(self, variables):
        """변수 목록 업데이트"""
        self.variable_combo.clear()
        for var in variables:
            self.variable_combo.addItem(var.display_name, var.id)
            
    def update_operator_list(self, operators):
        """연산자 목록 업데이트"""
        self.operator_combo.clear()
        self.operator_combo.addItems(operators)
        
    def show_success_message(self, message):
        """성공 메시지 표시"""
        QMessageBox.information(self, "성공", message)
        
    def show_error_message(self, message):
        """에러 메시지 표시"""
        QMessageBox.warning(self, "오류", message)
        
    def clear_form(self):
        """폼 초기화"""
        self.target_value_input.clear()
        
    def get_form_data(self):
        """폼 데이터 수집"""
        return {
            'variable_id': self.variable_combo.currentData(),
            'operator': self.operator_combo.currentText(),
            'target_value': self.target_value_input.text()
        }
```

### 2단계: 🎭 Presenter 구현
```python
# presentation/presenters/trigger_builder_presenter.py
class TriggerBuilderPresenter:
    """트리거 생성 Presenter - MVP 중재자"""
    
    def __init__(self, view, trigger_service, variable_service):
        self.view = view
        self.trigger_service = trigger_service      # Application Layer
        self.variable_service = variable_service    # Application Layer
        
        # ✅ View에 자신을 주입
        self.view.presenter = self
        
        # ✅ 초기화
        self._load_initial_data()
    
    def _load_initial_data(self):
        """초기 데이터 로드"""
        try:
            # ✅ Service 호출
            variables = self.variable_service.get_all_variables()
            
            # ✅ View 업데이트
            self.view.update_variable_list(variables)
            
        except Exception as e:
            self.view.show_error_message(f"초기 데이터 로드 실패: {e}")
    
    def handle_variable_changed(self, variable_id):
        """변수 변경 처리"""
        try:
            # ✅ Service 호출로 호환 연산자 조회
            operators = self.variable_service.get_compatible_operators(variable_id)
            
            # ✅ View 업데이트
            self.view.update_operator_list(operators)
            
        except Exception as e:
            self.view.show_error_message(f"연산자 로드 실패: {e}")
    
    def handle_create_trigger(self):
        """트리거 생성 처리"""
        try:
            # ✅ View에서 데이터 수집
            form_data = self.view.get_form_data()
            
            # ✅ 기본 검증
            if not self._validate_form_data(form_data):
                return
            
            # ✅ Command 객체 생성
            command = CreateTriggerCommand(
                variable_id=form_data['variable_id'],
                operator=form_data['operator'],
                target_value=form_data['target_value']
            )
            
            # ✅ Service 호출
            result = self.trigger_service.create_trigger(command)
            
            if result.success:
                # ✅ 성공 처리
                self.view.show_success_message("트리거가 생성되었습니다")
                self.view.clear_form()
                self._refresh_trigger_list()
            else:
                # ✅ 실패 처리
                self.view.show_error_message(result.error)
                
        except ValidationError as e:
            self.view.show_error_message(f"입력 오류: {e.message}")
        except Exception as e:
            self.view.show_error_message(f"시스템 오류: {e}")
    
    def _validate_form_data(self, form_data):
        """기본 폼 검증"""
        if not form_data['variable_id']:
            self.view.show_error_message("변수를 선택하세요")
            return False
            
        if not form_data['target_value']:
            self.view.show_error_message("목표값을 입력하세요")
            return False
            
        return True
        
    def _refresh_trigger_list(self):
        """트리거 목록 새로고침"""
        # ✅ 다른 View 갱신 (이벤트 기반으로 처리 가능)
        pass
```

### 3단계: ⚙️ Service 연동
```python
# application/services/trigger_service.py (이미 구현됨)
class TriggerService:
    def create_trigger(self, command: CreateTriggerCommand):
        # Application Layer 로직
        pass
```

## 🔧 MVP 패턴 고급 기법

### 1. 이벤트 기반 View 갱신
```python
class TriggerBuilderPresenter:
    def __init__(self, view, services, event_bus):
        self.view = view
        self.services = services
        self.event_bus = event_bus
        
        # ✅ 이벤트 구독
        self.event_bus.subscribe(TriggerCreated, self._on_trigger_created)
        self.event_bus.subscribe(VariableUpdated, self._on_variable_updated)
    
    def _on_trigger_created(self, event: TriggerCreated):
        """트리거 생성 이벤트 처리"""
        # ✅ View 업데이트
        self.view.add_trigger_to_list(event.trigger_dto)
        
    def _on_variable_updated(self, event: VariableUpdated):
        """변수 업데이트 이벤트 처리"""
        # ✅ 변수 목록 새로고침
        variables = self.variable_service.get_all_variables()
        self.view.update_variable_list(variables)
```

### 2. View State Management
```python
class ViewState:
    """View 상태 관리 객체"""
    def __init__(self):
        self.is_loading = False
        self.selected_variable = None
        self.form_data = {}
        
class TriggerBuilderPresenter:
    def __init__(self, view, services):
        self.view = view
        self.services = services
        self.state = ViewState()
    
    def _set_loading(self, loading: bool):
        """로딩 상태 관리"""
        self.state.is_loading = loading
        self.view.set_loading_state(loading)
        
    def handle_create_trigger(self):
        self._set_loading(True)
        try:
            # 트리거 생성 로직
            pass
        finally:
            self._set_loading(False)
```

### 3. 복잡한 UI 상태 처리
```python
class FormValidator:
    """폼 검증 헬퍼"""
    
    @staticmethod
    def validate_trigger_form(form_data):
        errors = []
        
        if not form_data['variable_id']:
            errors.append("변수를 선택하세요")
            
        if not form_data['target_value']:
            errors.append("목표값을 입력하세요")
        elif not FormValidator._is_numeric(form_data['target_value']):
            errors.append("목표값은 숫자여야 합니다")
            
        return errors
    
    @staticmethod
    def _is_numeric(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

class TriggerBuilderPresenter:
    def _validate_form_data(self, form_data):
        """향상된 폼 검증"""
        errors = FormValidator.validate_trigger_form(form_data)
        
        if errors:
            self.view.show_validation_errors(errors)
            return False
            
        return True
```

## 🎯 UI 개발 모범 사례

### ✅ 권장사항
1. **View는 순수 UI만**: 계산, 검증, 변환 로직 금지
2. **Presenter에서 모든 로직**: View-Service 중재 역할
3. **명확한 책임 분리**: 각 계층이 자신의 역할만 수행
4. **이벤트 기반 통신**: 느슨한 결합으로 확장성 확보

### ❌ 피해야 할 것들
1. **View에서 Service 직접 호출**: Presenter를 거쳐야 함
2. **Service에서 View 참조**: 의존성 방향 위반
3. **복잡한 UI 로직을 View에**: Presenter로 이동
4. **하드코딩된 UI 상태**: State 객체 활용

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처 구조
- [계층별 책임](02_LAYER_RESPONSIBILITIES.md): Presentation 계층 상세
- [기능 개발](04_FEATURE_DEVELOPMENT.md): UI 개발 워크플로

---
**💡 핵심**: "View는 바보여야 하고, Presenter가 똑똑해야 합니다!"
