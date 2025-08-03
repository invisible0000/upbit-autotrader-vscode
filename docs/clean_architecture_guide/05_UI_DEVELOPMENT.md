# 🎨 UI 개발 가이드 (MVP 패턴)

> **목적**: MVP 패턴 기반 UI 개발 및 Clean Architecture 통합  
> **대상**: UI 개발자, Presenter 구현자  
> **예상 읽기 시간**: 16분

## 🏗️ MVP 패턴 구조

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    View     │◄──►│  Presenter  │───►│    Model    │
│  (PyQt6)    │    │(비즈니스    │    │(Application │
│             │    │ 로직 조율)   │    │   Layer)    │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 🎯 역할 분리 원칙

#### View (UI 계층)
- **Only**: 사용자 입력 수집, 데이터 표시, UI 상태 관리
- **Never**: 비즈니스 로직, 데이터 처리, 외부 서비스 호출

#### Presenter (Presentation 계층)
- **Only**: View-Model 중재, 사용자 입력 변환, UI 로직
- **Never**: UI 직접 조작, 복잡한 비즈니스 로직

#### Model (Application 계층)
- **Only**: 비즈니스 유스케이스, 데이터 조회/변경
- **Never**: UI 관련 로직, View 참조

## 📝 실제 구현 예시: 조건 생성 UI

### 1. View 구현 (PyQt6)
```python
# presentation/views/condition_builder_view.py
class ConditionBuilderView(QWidget):
    """조건 생성 UI - View (Passive View 패턴)"""
    
    def __init__(self):
        super().__init__()
        self.presenter = None  # Presenter가 주입됨
        self.setup_ui()
        self.setup_events()
    
    def setup_ui(self):
        """UI 구성 - View의 핵심 책임"""
        layout = QVBoxLayout(self)
        
        # 변수 선택 섹션
        variable_group = QGroupBox("1. 변수 선택")
        variable_layout = QVBoxLayout(variable_group)
        
        self.variable_combo = QComboBox()
        self.variable_combo.setPlaceholderText("변수를 선택하세요")
        variable_layout.addWidget(QLabel("매매 변수:"))
        variable_layout.addWidget(self.variable_combo)
        
        # 파라미터 설정 섹션
        self.parameter_group = QGroupBox("2. 파라미터 설정")
        self.parameter_layout = QFormLayout(self.parameter_group)
        self.parameter_widgets = {}  # 동적 위젯 저장
        
        # 조건 설정 섹션
        condition_group = QGroupBox("3. 조건 설정")
        condition_layout = QFormLayout(condition_group)
        
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(['>', '>=', '<', '<=', '==', '!=', '~='])
        
        self.target_value_input = QLineEdit()
        self.target_value_input.setPlaceholderText("비교할 값을 입력하세요")
        
        condition_layout.addRow("연산자:", self.operator_combo)
        condition_layout.addRow("목표값:", self.target_value_input)
        
        # 미리보기 섹션
        preview_group = QGroupBox("4. 미리보기")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("조건을 설정하면 미리보기가 표시됩니다")
        self.preview_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        preview_layout.addWidget(self.preview_label)
        
        # 버튼 섹션
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("조건 생성")
        self.reset_button = QPushButton("초기화")
        self.create_button.setEnabled(False)  # 초기에는 비활성화
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.create_button)
        
        # 전체 레이아웃 구성
        layout.addWidget(variable_group)
        layout.addWidget(self.parameter_group)
        layout.addWidget(condition_group)
        layout.addWidget(preview_group)
        layout.addLayout(button_layout)
    
    def setup_events(self):
        """이벤트 연결 - View의 책임"""
        self.variable_combo.currentTextChanged.connect(self.on_variable_changed)
        self.operator_combo.currentTextChanged.connect(self.on_condition_changed)
        self.target_value_input.textChanged.connect(self.on_condition_changed)
        self.create_button.clicked.connect(self.on_create_clicked)
        self.reset_button.clicked.connect(self.on_reset_clicked)
    
    # ======== Presenter로부터 호출되는 메서드들 ========
    
    def set_available_variables(self, variables: List[VariableDto]):
        """사용 가능한 변수 목록 설정"""
        self.variable_combo.clear()
        for variable in variables:
            self.variable_combo.addItem(variable.display_name, variable.id)
    
    def show_parameter_widgets(self, parameter_configs: List[ParameterConfig]):
        """파라미터 입력 위젯 동적 생성"""
        # 기존 위젯 제거
        self.clear_parameter_widgets()
        
        for config in parameter_configs:
            widget = self._create_parameter_widget(config)
            self.parameter_layout.addRow(f"{config.display_name}:", widget)
            self.parameter_widgets[config.name] = widget
    
    def update_preview(self, preview_text: str, is_valid: bool):
        """조건 미리보기 업데이트"""
        self.preview_label.setText(preview_text)
        
        # 유효성에 따른 스타일 변경
        if is_valid:
            style = """
                QLabel {
                    padding: 10px;
                    background-color: #e8f5e8;
                    border: 1px solid #4CAF50;
                    border-radius: 4px;
                    color: #2e7d32;
                }
            """
        else:
            style = """
                QLabel {
                    padding: 10px;
                    background-color: #ffeaea;
                    border: 1px solid #f44336;
                    border-radius: 4px;
                    color: #c62828;
                }
            """
        self.preview_label.setStyleSheet(style)
        self.create_button.setEnabled(is_valid)
    
    def show_success_message(self, message: str):
        """성공 메시지 표시"""
        QMessageBox.information(self, "성공", message)
        self.reset_form()
    
    def show_error_message(self, message: str):
        """에러 메시지 표시"""
        QMessageBox.warning(self, "오류", message)
    
    def show_validation_error(self, field: str, message: str):
        """필드별 검증 오류 표시"""
        QToolTip.showText(
            self._get_widget_by_field(field).mapToGlobal(QPoint(0, 0)),
            message
        )
    
    # ======== 사용자 이벤트 핸들러들 ========
    
    def on_variable_changed(self):
        """변수 선택 변경 시"""
        if self.presenter:
            selected_variable_id = self.variable_combo.currentData()
            self.presenter.on_variable_selected(selected_variable_id)
    
    def on_condition_changed(self):
        """조건 설정 변경 시"""
        if self.presenter:
            condition_data = self.get_condition_form_data()
            self.presenter.on_condition_changed(condition_data)
    
    def on_create_clicked(self):
        """조건 생성 버튼 클릭"""
        if self.presenter:
            form_data = self.get_full_form_data()
            self.presenter.on_create_condition(form_data)
    
    def on_reset_clicked(self):
        """초기화 버튼 클릭"""
        self.reset_form()
        if self.presenter:
            self.presenter.on_form_reset()
    
    # ======== 데이터 수집 메서드들 ========
    
    def get_full_form_data(self) -> dict:
        """전체 폼 데이터 수집"""
        return {
            'variable_id': self.variable_combo.currentData(),
            'parameters': self.get_parameter_values(),
            'operator': self.operator_combo.currentText(),
            'target_value': self.target_value_input.text()
        }
    
    def get_condition_form_data(self) -> dict:
        """조건 설정 부분만 수집"""
        return {
            'operator': self.operator_combo.currentText(),
            'target_value': self.target_value_input.text()
        }
    
    def get_parameter_values(self) -> dict:
        """파라미터 값들 수집"""
        values = {}
        for param_name, widget in self.parameter_widgets.items():
            values[param_name] = self._extract_widget_value(widget)
        return values
    
    # ======== 헬퍼 메서드들 ========
    
    def _create_parameter_widget(self, config: ParameterConfig) -> QWidget:
        """파라미터 타입별 위젯 생성"""
        if config.type == 'integer':
            widget = QSpinBox()
            widget.setRange(config.min_value, config.max_value)
            widget.setValue(config.default_value)
            return widget
        elif config.type == 'float':
            widget = QDoubleSpinBox()
            widget.setRange(config.min_value, config.max_value)
            widget.setValue(config.default_value)
            widget.setDecimals(2)
            return widget
        elif config.type == 'enum':
            widget = QComboBox()
            widget.addItems(config.enum_options)
            return widget
        else:
            widget = QLineEdit()
            widget.setText(str(config.default_value))
            return widget
    
    def clear_parameter_widgets(self):
        """파라미터 위젯들 제거"""
        for widget in self.parameter_widgets.values():
            widget.deleteLater()
        self.parameter_widgets.clear()
        
        # FormLayout에서 모든 행 제거
        while self.parameter_layout.rowCount() > 0:
            self.parameter_layout.removeRow(0)
    
    def reset_form(self):
        """폼 초기화"""
        self.variable_combo.setCurrentIndex(-1)
        self.operator_combo.setCurrentIndex(0)
        self.target_value_input.clear()
        self.clear_parameter_widgets()
        self.preview_label.setText("조건을 설정하면 미리보기가 표시됩니다")
        self.create_button.setEnabled(False)
```

### 2. Presenter 구현
```python
# presentation/presenters/condition_builder_presenter.py
class ConditionBuilderPresenter:
    """조건 생성 Presenter - View와 Application Layer 중재"""
    
    def __init__(
        self, 
        view: ConditionBuilderView,
        variable_query_service: VariableQueryService,
        condition_creation_service: ConditionCreationService,
        condition_validator: ConditionValidationService
    ):
        self.view = view
        self.variable_query_service = variable_query_service
        self.condition_creation_service = condition_creation_service
        self.condition_validator = condition_validator
        
        # View에 자신을 주입
        self.view.presenter = self
        
        # 초기화
        self.current_variable = None
        self.initialize_view()
    
    def initialize_view(self):
        """View 초기화"""
        try:
            # 사용 가능한 변수 목록 로딩
            variables_result = self.variable_query_service.get_available_variables()
            if variables_result.success:
                self.view.set_available_variables(variables_result.data)
            else:
                self.view.show_error_message("변수 목록을 불러올 수 없습니다")
        except Exception as e:
            self.view.show_error_message(f"초기화 오류: {str(e)}")
    
    def on_variable_selected(self, variable_id: str):
        """변수 선택 처리"""
        if not variable_id:
            self.view.show_parameter_widgets([])
            return
        
        try:
            # 선택된 변수 정보 조회
            variable_result = self.variable_query_service.get_variable_detail(
                variable_id
            )
            
            if variable_result.success:
                self.current_variable = variable_result.data
                
                # 파라미터 위젯 표시
                parameter_configs = self._convert_to_parameter_configs(
                    self.current_variable.parameters
                )
                self.view.show_parameter_widgets(parameter_configs)
                
                # 조건 미리보기 업데이트
                self._update_condition_preview()
            else:
                self.view.show_error_message("변수 정보를 불러올 수 없습니다")
                
        except Exception as e:
            self.view.show_error_message(f"변수 선택 오류: {str(e)}")
    
    def on_condition_changed(self, condition_data: dict):
        """조건 설정 변경 처리"""
        self._update_condition_preview()
    
    def on_create_condition(self, form_data: dict):
        """조건 생성 처리"""
        try:
            # 1. 폼 데이터 검증
            validation_result = self._validate_form_data(form_data)
            if not validation_result.is_valid:
                for error in validation_result.errors:
                    self.view.show_validation_error(error.field, error.message)
                return
            
            # 2. Command 객체 생성
            command = CreateConditionCommand(
                variable_id=VariableId(form_data['variable_id']),
                operator=form_data['operator'],
                target_value=form_data['target_value'],
                parameters=form_data['parameters']
            )
            
            # 3. 비즈니스 로직 실행
            result = self.condition_creation_service.create_condition(command)
            
            if result.success:
                self.view.show_success_message(
                    f"조건 '{result.data.condition.name}'이 생성되었습니다"
                )
                
                # 생성된 조건을 상위 컨테이너에 알림 (이벤트 발행)
                self._notify_condition_created(result.data.condition)
            else:
                self.view.show_error_message(result.error)
                
        except Exception as e:
            self.view.show_error_message(f"조건 생성 오류: {str(e)}")
    
    def on_form_reset(self):
        """폼 초기화 처리"""
        self.current_variable = None
        self._update_condition_preview()
    
    # ======== 내부 헬퍼 메서드들 ========
    
    def _update_condition_preview(self):
        """조건 미리보기 업데이트"""
        if not self.current_variable:
            self.view.update_preview("변수를 먼저 선택하세요", False)
            return
        
        form_data = self.view.get_condition_form_data()
        
        if not form_data['operator'] or not form_data['target_value']:
            self.view.update_preview("조건을 설정하세요", False)
            return
        
        try:
            # 미리보기 텍스트 생성
            preview_text = f"{self.current_variable.display_name} {form_data['operator']} {form_data['target_value']}"
            
            # 유효성 검증
            is_valid = self._validate_condition_logic(form_data)
            
            self.view.update_preview(preview_text, is_valid)
            
        except Exception as e:
            self.view.update_preview(f"오류: {str(e)}", False)
    
    def _validate_form_data(self, form_data: dict) -> ValidationResult:
        """폼 데이터 종합 검증"""
        errors = []
        
        # 필수 필드 검증
        if not form_data.get('variable_id'):
            errors.append(ValidationError('variable_id', '변수를 선택하세요'))
        
        if not form_data.get('operator'):
            errors.append(ValidationError('operator', '연산자를 선택하세요'))
        
        if not form_data.get('target_value'):
            errors.append(ValidationError('target_value', '목표값을 입력하세요'))
        
        # 비즈니스 로직 검증
        if not errors:
            try:
                business_validation = self.condition_validator.validate_condition(
                    form_data['variable_id'],
                    form_data['operator'],
                    form_data['target_value']
                )
                
                if not business_validation.is_valid:
                    errors.extend(business_validation.errors)
                    
            except Exception as e:
                errors.append(ValidationError('general', str(e)))
        
        return ValidationResult(len(errors) == 0, errors)
    
    def _validate_condition_logic(self, condition_data: dict) -> bool:
        """조건 로직 유효성 검증"""
        try:
            return self.condition_validator.validate_condition_syntax(
                self.current_variable.id,
                condition_data['operator'],
                condition_data['target_value']
            ).is_valid
        except:
            return False
    
    def _convert_to_parameter_configs(self, parameters: List[ParameterDto]) -> List[ParameterConfig]:
        """DTO를 UI 설정 객체로 변환"""
        configs = []
        for param in parameters:
            config = ParameterConfig(
                name=param.name,
                display_name=param.display_name,
                type=param.type,
                default_value=param.default_value,
                min_value=param.min_value,
                max_value=param.max_value,
                enum_options=param.enum_options
            )
            configs.append(config)
        return configs
    
    def _notify_condition_created(self, condition: ConditionDto):
        """조건 생성 알림 (이벤트 발행)"""
        # 상위 Presenter나 이벤트 시스템에 알림
        if hasattr(self.view.parent(), 'on_condition_created'):
            self.view.parent().on_condition_created(condition)
```

### 3. Model 연동 (Application Layer)
```python
# application/queries/variable_query_service.py
class VariableQueryService:
    """변수 조회 서비스 - Application Layer"""
    
    def __init__(self, variable_repo: VariableRepository):
        self.variable_repo = variable_repo
    
    def get_available_variables(self) -> Result[List[VariableDto]]:
        """사용 가능한 변수 목록 조회"""
        try:
            variables = self.variable_repo.find_all_active()
            variable_dtos = [
                VariableDto.from_domain(var) for var in variables
            ]
            return Result.ok(variable_dtos)
        except Exception as e:
            return Result.fail(f"변수 목록 조회 실패: {str(e)}")
    
    def get_variable_detail(self, variable_id: str) -> Result[VariableDetailDto]:
        """특정 변수 상세 정보 조회"""
        try:
            variable = self.variable_repo.find_by_id(VariableId(variable_id))
            if not variable:
                return Result.fail("존재하지 않는 변수입니다")
            
            parameters = self.variable_repo.find_parameters_by_variable_id(
                variable.id
            )
            
            detail_dto = VariableDetailDto(
                id=variable.id.value,
                name=variable.name,
                display_name=variable.display_name,
                description=variable.description,
                parameters=[
                    ParameterDto.from_domain(param) for param in parameters
                ]
            )
            
            return Result.ok(detail_dto)
        except Exception as e:
            return Result.fail(f"변수 상세 조회 실패: {str(e)}")
```

## 🔄 MVP 상호작용 패턴

### 사용자 액션 처리 흐름
```
1. [User] 버튼 클릭/텍스트 입력
   ↓
2. [View] 이벤트 핸들러 실행
   ↓
3. [View] Presenter 메서드 호출
   ↓
4. [Presenter] 데이터 검증/변환
   ↓
5. [Presenter] Application Service 호출
   ↓
6. [Presenter] 결과에 따른 View 업데이트
```

### 데이터 표시 흐름
```
1. [Presenter] Application Service에서 데이터 조회
   ↓
2. [Presenter] Domain 객체 → DTO 변환
   ↓
3. [Presenter] View 업데이트 메서드 호출
   ↓
4. [View] UI 위젯에 데이터 표시
```

## 🧪 MVP 패턴 테스트 전략

### View 테스트 (UI Test)
```python
# tests/presentation/views/test_condition_builder_view.py
class TestConditionBuilderView:
    
    def test_variable_selection_triggers_presenter_call(self, qtbot):
        """변수 선택 시 Presenter 호출 테스트"""
        # Given
        view = ConditionBuilderView()
        presenter = Mock()
        view.presenter = presenter
        
        # When
        view.variable_combo.addItem("RSI", "RSI")
        view.variable_combo.setCurrentIndex(0)
        
        # Then
        presenter.on_variable_selected.assert_called_once_with("RSI")
    
    def test_form_data_collection(self):
        """폼 데이터 수집 테스트"""
        # Given
        view = ConditionBuilderView()
        view.variable_combo.addItem("RSI", "RSI")
        view.variable_combo.setCurrentIndex(0)
        view.operator_combo.setCurrentText(">")
        view.target_value_input.setText("70")
        
        # When
        form_data = view.get_full_form_data()
        
        # Then
        assert form_data['variable_id'] == "RSI"
        assert form_data['operator'] == ">"
        assert form_data['target_value'] == "70"
```

### Presenter 테스트 (Unit Test)
```python
# tests/presentation/presenters/test_condition_builder_presenter.py
class TestConditionBuilderPresenter:
    
    def test_variable_selection_updates_view(self):
        """변수 선택 시 View 업데이트 테스트"""
        # Given
        view = Mock()
        variable_service = Mock()
        presenter = ConditionBuilderPresenter(view, variable_service, None, None)
        
        variable_detail = VariableDetailDto(
            id="RSI",
            name="rsi",
            display_name="RSI 지표",
            parameters=[
                ParameterDto(name="period", type="integer", default_value=14)
            ]
        )
        variable_service.get_variable_detail.return_value = Result.ok(variable_detail)
        
        # When
        presenter.on_variable_selected("RSI")
        
        # Then
        view.show_parameter_widgets.assert_called_once()
        variable_service.get_variable_detail.assert_called_once_with("RSI")
```

## 🔍 다음 단계

- **[데이터베이스 수정](06_DATABASE_MODIFICATION.md)**: 스키마 변경 방법
- **[상태 관리](08_STATE_MANAGEMENT.md)**: 복잡한 UI 상태 처리
- **[테스팅 전략](16_TESTING_STRATEGY.md)**: UI/Presenter 테스트

---
**💡 핵심**: "MVP 패턴으로 UI 로직과 비즈니스 로직을 완전히 분리하면 테스트와 유지보수가 훨씬 쉬워집니다!"
