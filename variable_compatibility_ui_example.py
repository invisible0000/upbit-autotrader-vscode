
# 조건 다이얼로그에 추가할 호환성 검증 코드 예제

class EnhancedConditionDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.compatibility_validator = VariableCompatibilityValidator()
        self.setup_ui()
    
    def setup_ui(self):
        # 기존 UI 설정...
        
        # 외부변수 콤보박스에 시그널 연결
        self.external_variable_combo.currentTextChanged.connect(
            self.on_external_variable_changed
        )
        
        # 기본 변수 콤보박스에 시그널 연결  
        self.base_variable_combo.currentTextChanged.connect(
            self.on_base_variable_changed
        )
        
        # 호환성 상태 라벨
        self.compatibility_status_label = QLabel()
        self.compatibility_status_label.setWordWrap(True)
        layout.addWidget(self.compatibility_status_label)
    
    def on_base_variable_changed(self, variable_name):
        """기본 변수 변경 시 호환 가능한 외부변수만 표시"""
        if not variable_name:
            return
        
        # 변수명을 ID로 변환 (실제 구현에서는 매핑 테이블 필요)
        base_variable_id = self.get_variable_id_by_name(variable_name)
        
        # 호환 가능한 변수들만 외부변수 콤보박스에 추가
        compatible_vars = self.compatibility_validator.get_compatible_variables(
            base_variable_id
        )
        
        self.external_variable_combo.clear()
        self.external_variable_combo.addItem("선택하세요", "")
        
        for var in compatible_vars:
            self.external_variable_combo.addItem(var['name'], var['id'])
        
        # 상태 업데이트
        self.update_compatibility_status()
    
    def on_external_variable_changed(self, external_variable_name):
        """외부변수 변경 시 호환성 검사"""
        self.update_compatibility_status()
    
    def update_compatibility_status(self):
        """호환성 상태 업데이트"""
        base_var_name = self.base_variable_combo.currentText()
        external_var_name = self.external_variable_combo.currentText()
        
        if not base_var_name or not external_var_name or external_var_name == "선택하세요":
            self.compatibility_status_label.setText("")
            return
        
        # 변수명을 ID로 변환
        base_var_id = self.get_variable_id_by_name(base_var_name)
        external_var_id = self.get_variable_id_by_name(external_var_name)
        
        if not base_var_id or not external_var_id:
            return
        
        # 호환성 검증
        is_compatible, user_msg, log_msg = self.compatibility_validator.validate_compatibility(
            base_var_id, external_var_id
        )
        
        if is_compatible:
            self.compatibility_status_label.setText(
                f'<span style="color: green;">{user_msg}</span>'
            )
            self.save_button.setEnabled(True)
        else:
            self.compatibility_status_label.setText(
                f'<span style="color: red;">{user_msg}</span>'
            )
            self.save_button.setEnabled(False)  # 저장 버튼 비활성화
        
        print(log_msg)  # 로깅
    
    def get_variable_id_by_name(self, variable_name):
        """변수명으로 ID 조회 (실제 구현 필요)"""
        name_to_id = {
            "RSI": "rsi",
            "MACD": "macd", 
            "스토캐스틱": "stochastic",
            "현재가": "current_price",
            "이동평균": "moving_average",
            "볼린저밴드": "bollinger_band",
            "거래량": "volume"
        }
        return name_to_id.get(variable_name, "")
    
    def save_condition(self):
        """조건 저장 (호환성 재검증 포함)"""
        # 최종 호환성 재검증
        base_var_id = self.get_variable_id_by_name(self.base_variable_combo.currentText())
        external_var_id = self.get_variable_id_by_name(self.external_variable_combo.currentText())
        
        if external_var_id:
            is_compatible, user_msg, log_msg = self.compatibility_validator.validate_compatibility(
                base_var_id, external_var_id
            )
            
            if not is_compatible:
                QMessageBox.warning(self, "호환성 오류", user_msg)
                return False
        
        # 기존 저장 로직 계속...
        return super().save_condition()
