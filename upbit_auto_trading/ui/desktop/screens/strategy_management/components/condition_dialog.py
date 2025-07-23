#!/usr/bin/env python3
"""
리팩토링된 조건 다이얼로그 - 컴포넌트 기반 아키텍처
"""

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
    QLabel, QMessageBox, QDialog, QComboBox, QLineEdit, QTextEdit, 
    QButtonGroup, QRadioButton, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Any, Optional

from .variable_definitions import VariableDefinitions
from .parameter_widgets import ParameterWidgetFactory
from .condition_validator import ConditionValidator
from .condition_builder import ConditionBuilder
from .condition_storage import ConditionStorage
from .preview_components import PreviewGenerator

class ConditionDialog(QWidget):
    """리팩토링된 조건 생성 위젯 (다이얼로그에서 위젯으로 변경)"""
    
    # 시그널 정의
    condition_saved = pyqtSignal(dict)  # 조건 저장 완료 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 컴포넌트 초기화
        self.variable_definitions = VariableDefinitions()
        self.validator = ConditionValidator()
        self.builder = ConditionBuilder()
        self.storage = ConditionStorage()
        self.preview_generator = PreviewGenerator()
        
        # UI 관련 속성
        self.current_condition = None
        self.parameter_factory = ParameterWidgetFactory(update_callback=self.update_preview)
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🎯 조건 생성기 v4 (컴포넌트 기반)")
        self.setMinimumSize(500, 400)  # 크기 대폭 줄이기
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # 마진 줄이기
        layout.setSpacing(3)  # 간격 줄이기
        
        # 1. 변수 선택
        self.create_variable_section(layout)
        
        # 2. 비교 설정
        self.create_comparison_section(layout)
        
        # 2-1. 외부 변수 설정
        self.create_external_variable_section(layout)
        
        # 3. 조건 정보
        self.create_info_section(layout)
        
        # 4. 미리보기
        self.create_preview_section(layout)
        
        self.setLayout(layout)
        self.connect_events()
        self.update_variables_by_category()
    
    def create_variable_section(self, layout):
        """변수 선택 섹션"""
        group = QGroupBox("📊 1단계: 변수 선택")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        group_layout.setSpacing(3)  # 간격 줄이기
        
        # 범주 + 변수 선택을 한 줄로 합치기
        category_var_layout = QHBoxLayout()
        
        # 범주 선택
        category_var_layout.addWidget(QLabel("범주:"))
        
        self.category_combo = QComboBox()
        category_variables = self.variable_definitions.get_category_variables()
        for category_id, variables in category_variables.items():
            category_names = {
                "indicator": "지표",
                "price": "시장가", 
                "capital": "자본",
                "state": "상태"
            }
            self.category_combo.addItem(category_names.get(category_id, category_id), category_id)
        
        category_var_layout.addWidget(self.category_combo)
        
        # 간격 추가
        category_var_layout.addSpacing(20)
        
        # 변수 선택
        category_var_layout.addWidget(QLabel("변수:"))
        self.variable_combo = QComboBox()
        category_var_layout.addWidget(self.variable_combo)
        
        # 변수별 헬프 버튼
        help_btn = QPushButton("❓")
        help_btn.setMaximumWidth(30)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ffca2c;
            }
        """)
        help_btn.clicked.connect(self.show_variable_help)
        category_var_layout.addWidget(help_btn)
        
        # 지원 현황 버튼
        info_btn = QPushButton("📋 지원 현황")
        info_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        info_btn.clicked.connect(self.show_variable_info)
        category_var_layout.addWidget(info_btn)
        
        group_layout.addLayout(category_var_layout)
        
        # 파라미터 영역 (스크롤 가능)
        self.param_scroll, self.param_layout = self.parameter_factory.create_scrollable_parameter_area()
        group_layout.addWidget(self.param_scroll)
        
        # 변수 설명
        self.variable_description = QLabel("변수를 선택하면 설명이 표시됩니다.")
        self.variable_description.setStyleSheet("""
            background: #f8f9fa; 
            padding: 10px; 
            border-radius: 6px; 
            color: #666;
            font-style: italic;
        """)
        self.variable_description.setWordWrap(True)
        group_layout.addWidget(self.variable_description)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_comparison_section(self, layout):
        """비교 설정 섹션"""
        group = QGroupBox("⚖️ 2단계: 비교 설정")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        group_layout.setSpacing(3)  # 간격 줄이기
        
        # 연산자
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("연산자:"))
        
        self.operator_combo = QComboBox()
        operators = [
            (">", "초과 (크다)"),
            (">=", "이상 (크거나 같다)"),
            ("<", "미만 (작다)"),
            ("<=", "이하 (작거나 같다)"),
            ("~=", "근사값 (±1% 범위)"),
            ("!=", "다름")
        ]
        for op_symbol, op_desc in operators:
            self.operator_combo.addItem(f"{op_symbol} - {op_desc}", op_symbol)
        op_layout.addWidget(self.operator_combo)
        group_layout.addLayout(op_layout)
        
        # 외부값 사용 체크박스
        comparison_type_layout = QHBoxLayout()
        self.use_external_variable = QPushButton("🔄 외부값 사용")
        self.use_external_variable.setCheckable(True)
        self.use_external_variable.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:checked {
                background-color: #28a745;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:checked:hover {
                background-color: #218838;
            }
        """)
        self.use_external_variable.clicked.connect(self.toggle_comparison_mode)
        comparison_type_layout.addWidget(self.use_external_variable)
        comparison_type_layout.addStretch()
        group_layout.addLayout(comparison_type_layout)
        
        # 비교값 입력
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("비교값:"))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("예: 70, 30, 0.5")
        target_layout.addWidget(self.target_input)
        group_layout.addLayout(target_layout)
        
        # 추세 방향성
        trend_layout = QVBoxLayout()
        trend_layout.addWidget(QLabel("추세 방향성:"))
        
        trend_buttons_layout = QHBoxLayout()
        self.trend_group = QButtonGroup()
        
        trend_options = [
            ("static", "정적 비교"),
            ("rising", "상승중"),
            ("falling", "하락중"),
            ("both", "양방향")
        ]
        
        for trend_id, trend_name in trend_options:
            radio = QRadioButton(trend_name)
            radio.setProperty("trend_id", trend_id)
            self.trend_group.addButton(radio)
            trend_buttons_layout.addWidget(radio)
            
            if trend_id == "static":
                radio.setChecked(True)
        
        trend_layout.addLayout(trend_buttons_layout)
        
        # 추세 도움말
        trend_help = QLabel("💡 정적: 단순 비교 | 상승중: 값이 증가 추세 | 하락중: 값이 감소 추세 | 양방향: 변화량 감지")
        trend_help.setStyleSheet("color: #666; font-size: 10px; font-style: italic; margin-top: 5px;")
        trend_help.setWordWrap(True)
        trend_layout.addWidget(trend_help)
        
        group_layout.addLayout(trend_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_external_variable_section(self, layout):
        """외부 변수 설정 섹션"""
        self.external_variable_widget = QGroupBox("🔗 2-1단계: 외부 변수 설정 (골든크로스 등)")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        group_layout.setSpacing(3)  # 간격 줄이기
        
        # 범주 선택
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("범주:"))
        
        self.external_category_combo = QComboBox()
        category_variables = self.variable_definitions.get_category_variables()
        for category_id, variables in category_variables.items():
            category_names = {
                "indicator": "지표",
                "price": "시장가",
                "capital": "자본", 
                "state": "상태"
            }
            self.external_category_combo.addItem(category_names.get(category_id, category_id), category_id)
        category_layout.addWidget(self.external_category_combo)
        
        # 외부 변수 안내
        info_label = QLabel("💡 골든크로스: SMA(20) > SMA(60) 같은 조건 생성")
        info_label.setStyleSheet("color: #17a2b8; font-size: 10px; font-style: italic;")
        category_layout.addWidget(info_label)
        category_layout.addStretch()
        group_layout.addLayout(category_layout)
        
        # 변수 선택
        var_layout = QHBoxLayout()
        var_layout.addWidget(QLabel("변수:"))
        self.external_variable_combo = QComboBox()
        var_layout.addWidget(self.external_variable_combo)
        var_layout.addStretch()
        group_layout.addLayout(var_layout)
        
        # 외부 변수 파라미터 (스크롤 가능)
        self.external_param_scroll, self.external_param_layout = self.parameter_factory.create_scrollable_parameter_area(80, 120)
        group_layout.addWidget(self.external_param_scroll)
        
        # 외부 변수 설명
        self.external_variable_description = QLabel("외부 변수를 선택하면 설명이 표시됩니다.")
        self.external_variable_description.setStyleSheet("""
            background: #f8f9fa; 
            padding: 8px; 
            border-radius: 4px; 
            color: #666;
            font-style: italic;
            font-size: 11px;
        """)
        self.external_variable_description.setWordWrap(True)
        group_layout.addWidget(self.external_variable_description)
        
        # 초기에는 비활성화
        self.external_variable_widget.setEnabled(False)
        self.external_variable_widget.setStyleSheet("QGroupBox { color: #999; }")
        
        self.external_variable_widget.setLayout(group_layout)
        layout.addWidget(self.external_variable_widget)
    
    def create_info_section(self, layout):
        """조건 정보 섹션"""
        group = QGroupBox("📝 3단계: 조건 정보")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        group_layout.setSpacing(3)  # 간격 줄이기
        
        # 조건 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("이름:"))
        self.condition_name = QLineEdit()
        self.condition_name.setPlaceholderText("예: RSI 과매수 진입")
        name_layout.addWidget(self.condition_name)
        group_layout.addLayout(name_layout)
        
        # 설명
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("설명:"))
        self.condition_description = QTextEdit()
        self.condition_description.setPlaceholderText("이 조건이 언제 발생하는지 설명해주세요.")
        self.condition_description.setMaximumHeight(60)
        desc_layout.addWidget(self.condition_description)
        group_layout.addLayout(desc_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_preview_section(self, layout):
        """미리보기 섹션"""
        group = QGroupBox("👀 미리보기")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)  # 패딩 줄이기
        group_layout.setSpacing(3)  # 간격 줄이기
        
        self.preview_label = QLabel("조건을 설정하면 미리보기가 표시됩니다.")
        self.preview_label.setStyleSheet("""
            background: #f8f9fa; 
            padding: 8px;  /* 패딩 줄이기 */
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;  /* 폰트 크기 줄이기 */
        """)
        self.preview_label.setWordWrap(True)
        group_layout.addWidget(self.preview_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def connect_events(self):
        """이벤트 연결"""
        self.category_combo.currentTextChanged.connect(self.update_variables_by_category)
        self.variable_combo.currentTextChanged.connect(self.update_variable_params)
        self.variable_combo.currentTextChanged.connect(self.update_variable_description)
        self.variable_combo.currentTextChanged.connect(self.update_placeholders)
        
        # 외부 변수 관련 이벤트
        self.external_category_combo.currentTextChanged.connect(self.update_external_variables)
        self.external_variable_combo.currentTextChanged.connect(self.update_external_variable_params)
        self.external_variable_combo.currentTextChanged.connect(self.update_preview)
        
        # 미리보기 업데이트
        self.variable_combo.currentTextChanged.connect(self.update_preview)
        self.operator_combo.currentTextChanged.connect(self.update_preview)
        self.target_input.textChanged.connect(self.update_preview)
        self.condition_name.textChanged.connect(self.update_preview)
        
        for button in self.trend_group.buttons():
            button.toggled.connect(self.update_preview)
    
    def update_variables_by_category(self):
        """카테고리별 변수 필터링"""
        self.variable_combo.clear()
        
        selected_category = self.category_combo.currentData()
        category_variables = self.variable_definitions.get_category_variables()
        
        if selected_category in category_variables:
            for var_id, var_name in category_variables[selected_category]:
                icon_map = {
                    "indicator": "📈",
                    "price": "💰",
                    "capital": "🏦", 
                    "state": "📊"
                }
                icon = icon_map.get(selected_category, "🔹")
                self.variable_combo.addItem(f"{icon} {var_name}", var_id)
    
    def update_variable_params(self):
        """변수별 파라미터 UI 생성"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            return
        
        # 기존 위젯 제거
        self.parameter_factory.clear_parameter_widgets(self.param_layout)
        
        # 변수별 파라미터 정의
        params = self.variable_definitions.get_variable_parameters(var_id)
        
        if params:
            self.parameter_factory.create_parameter_widgets(var_id, params, self.param_layout)
    
    def update_variable_description(self):
        """변수 설명 업데이트"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            self.variable_description.setText("변수를 선택하면 설명이 표시됩니다.")
            return
        
        descriptions = self.variable_definitions.get_variable_descriptions()
        desc = descriptions.get(var_id, "설명 준비 중...")
        self.variable_description.setText(f"📖 {desc}")
    
    def update_placeholders(self):
        """변수별 플레이스홀더 업데이트"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            return
        
        placeholders = self.variable_definitions.get_variable_placeholders()
        var_placeholders = placeholders.get(var_id, {})
        
        self.target_input.setPlaceholderText(var_placeholders.get("target", "비교값 입력"))
        self.condition_name.setPlaceholderText(var_placeholders.get("name", "조건 이름"))
        self.condition_description.setPlaceholderText(var_placeholders.get("description", "조건 설명"))
    
    def toggle_comparison_mode(self):
        """비교 모드 전환"""
        is_external = self.use_external_variable.isChecked()
        
        # 외부 변수 섹션 활성화/비활성화
        self.external_variable_widget.setEnabled(is_external)
        
        # 비교값 입력 비활성화/활성화
        self.target_input.setEnabled(not is_external)
        
        if is_external:
            self.target_input.setPlaceholderText("외부 변수 사용 중...")
            self.target_input.setStyleSheet("background-color: #f8f9fa; color: #6c757d;")
            self.use_external_variable.setText("🔄 고정값 사용")
            self.external_variable_widget.setStyleSheet("QGroupBox { color: #000; }")
            self.update_external_variables()
        else:
            self.target_input.setStyleSheet("")
            self.use_external_variable.setText("🔄 외부값 사용")
            self.external_variable_widget.setStyleSheet("QGroupBox { color: #999; }")
            self.update_placeholders()
        
        self.update_preview()
    
    def update_external_variables(self):
        """외부 변수 목록 업데이트"""
        self.external_variable_combo.clear()
        
        selected_category = self.external_category_combo.currentData()
        category_variables = self.variable_definitions.get_category_variables()
        
        if selected_category in category_variables:
            for var_id, var_name in category_variables[selected_category]:
                icon_map = {
                    "indicator": "📈",
                    "price": "💰",
                    "capital": "🏦",
                    "state": "📊"
                }
                icon = icon_map.get(selected_category, "🔹")
                self.external_variable_combo.addItem(f"{icon} {var_name}", var_id)
        
        self.update_external_variable_params()
    
    def update_external_variable_params(self):
        """외부 변수 파라미터 업데이트"""
        external_var_id = self.external_variable_combo.currentData()
        if not external_var_id:
            return
        
        # 기존 파라미터 제거
        self.parameter_factory.clear_parameter_widgets(self.external_param_layout)
        
        # 외부 변수 설명 업데이트
        descriptions = self.variable_definitions.get_variable_descriptions()
        desc = descriptions.get(external_var_id, "외부 변수 설명")
        self.external_variable_description.setText(f"📖 {desc}")
        
        # 파라미터 생성
        params = self.variable_definitions.get_variable_parameters(external_var_id)
        if params:
            self.parameter_factory.create_parameter_widgets(
                f"{external_var_id}_external", params, self.external_param_layout
            )
    
    def update_preview(self):
        """미리보기 업데이트"""
        condition_data = self.collect_condition_data()
        if condition_data:
            preview_text = self.preview_generator.generate_condition_preview(condition_data)
            self.preview_label.setText(preview_text)
    
    def collect_condition_data(self) -> Optional[Dict[str, Any]]:
        """현재 UI 상태에서 조건 데이터 수집 (이름 검증 추가)"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            return None
        
        # 조건 이름 검증
        condition_name = self.condition_name.text().strip()
        if not condition_name:
            QMessageBox.warning(self, "⚠️ 경고", "조건 이름이 비어 있으면 저장할 수 없습니다.\n조건 이름을 입력해주세요.")
            return None
        
        # 추세 방향성
        trend_direction = "static"
        for button in self.trend_group.buttons():
            if button.isChecked():
                trend_direction = button.property("trend_id")
                break
        
        # 외부 변수 정보
        external_variable_info = None
        if self.use_external_variable.isChecked():
            external_var_id = self.external_variable_combo.currentData()
            if external_var_id:
                external_variable_info = {
                    'variable_id': external_var_id,
                    'variable_name': self.external_variable_combo.currentText(),
                    'category': self.external_category_combo.currentData()
                }
        
        condition_data = {
            'name': condition_name,  # 자동 생성 제거
            'description': self.condition_description.toPlainText().strip(),
            'variable_id': var_id,
            'variable_name': self.variable_combo.currentText(),
            'variable_params': self.parameter_factory.get_parameter_values(var_id),
            'operator': self.operator_combo.currentData(),
            'target_value': self.target_input.text().strip() if not self.use_external_variable.isChecked() else None,
            'external_variable': external_variable_info,
            'trend_direction': trend_direction,
            'comparison_type': 'external' if self.use_external_variable.isChecked() else 'fixed'
        }
        
        return condition_data
    
    def load_condition(self, condition_data: Dict[str, Any]):
        """기존 조건을 UI에 로드 (편집용)"""
        try:
            # 조건명 설정
            self.condition_name.setText(condition_data.get('name', ''))
            
            # 설명 설정
            self.condition_description.setPlainText(condition_data.get('description', ''))
            
            # 카테고리 설정
            category = condition_data.get('category', 'custom')
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == category:
                    self.category_combo.setCurrentIndex(i)
                    break
            
            # 변수 설정
            variable_id = condition_data.get('variable_id')
            if variable_id:
                self.update_variables_by_category()  # 카테고리별 변수 업데이트
                for i in range(self.variable_combo.count()):
                    if self.variable_combo.itemData(i) == variable_id:
                        self.variable_combo.setCurrentIndex(i)
                        break
            
            # 변수 파라미터 설정
            variable_params = condition_data.get('variable_params', {})
            if variable_params and hasattr(self, 'parameter_factory'):
                self.parameter_factory.set_parameter_values(variable_id, variable_params)
            
            # 연산자 설정
            operator = condition_data.get('operator', '>')
            for i in range(self.operator_combo.count()):
                if self.operator_combo.itemData(i) == operator:
                    self.operator_combo.setCurrentIndex(i)
                    break
            
            # 비교 타입에 따른 설정
            comparison_type = condition_data.get('comparison_type', 'fixed')
            external_variable = condition_data.get('external_variable')
            
            if comparison_type == 'external' and external_variable:
                # 외부 변수 사용
                self.use_external_variable.setChecked(True)
                
                # 외부 변수 카테고리 설정
                ext_category = external_variable.get('category', 'custom')
                for i in range(self.external_category_combo.count()):
                    if self.external_category_combo.itemData(i) == ext_category:
                        self.external_category_combo.setCurrentIndex(i)
                        break
                
                # 외부 변수 설정
                ext_var_id = external_variable.get('variable_id')
                if ext_var_id:
                    self.update_external_variables_by_category()
                    for i in range(self.external_variable_combo.count()):
                        if self.external_variable_combo.itemData(i) == ext_var_id:
                            self.external_variable_combo.setCurrentIndex(i)
                            break
            else:
                # 고정값 사용
                self.use_external_variable.setChecked(False)
                target_value = condition_data.get('target_value', '')
                self.target_input.setText(str(target_value))
            
            # 추세 방향 설정
            trend_direction = condition_data.get('trend_direction', 'static')
            for button in self.trend_group.buttons():
                if button.property("trend_id") == trend_direction:
                    button.setChecked(True)
                    break
            
            # UI 업데이트
            self.update_external_variable_visibility()
            self.update_preview()
            
            print(f"✅ 조건 로드 완료: {condition_data.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ 조건 로드 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"조건 로드 중 오류가 발생했습니다:\n{e}")

    def save_condition(self):
        """조건 저장 (덮어쓰기 확인 포함)"""
        try:
            condition_data = self.collect_condition_data()
            if not condition_data:
                QMessageBox.warning(self, "⚠️ 경고", "변수를 선택해주세요.")
                return
            
            # 조건 빌드 및 검증
            is_valid, message, built_condition = self.builder.validate_and_build(condition_data)
            
            if not is_valid or built_condition is None:
                QMessageBox.warning(self, "⚠️ 검증 오류", message)
                return
            
            # 첫 번째 저장 시도 (덮어쓰기 없이)
            success, save_message, condition_id = self.storage.save_condition(built_condition, overwrite=False)
            
            if not success and "이미 존재합니다" in save_message:
                # 덮어쓰기 확인 다이얼로그
                reply = QMessageBox.question(
                    self, "🔄 덮어쓰기 확인", 
                    f"{save_message}\n\n기존 조건을 덮어쓰시겠습니까?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 덮어쓰기로 다시 저장
                    success, save_message, condition_id = self.storage.save_condition(built_condition, overwrite=True)
                else:
                    return  # 사용자가 취소함
            
            if success:
                self.current_condition = built_condition
                if condition_id is not None:
                    self.current_condition['id'] = condition_id
                
                # 시그널 발생
                self.condition_saved.emit(self.current_condition)
                
                QMessageBox.information(self, "✅ 성공", save_message)
                # self.accept()  # 창을 닫지 않고 계속 사용 가능하도록
            else:
                QMessageBox.critical(self, "❌ 오류", save_message)
                
        except Exception as e:
            QMessageBox.critical(self, "❌ 오류", f"조건 저장 중 오류:\n{str(e)}")
    
    def refresh_data(self):
        """데이터 새로고침"""
        try:
            # 변수 콤보박스 새로고침
            self.update_variables_by_category()
            
            # 미리보기 새로고침
            self.update_preview()
            
            print("✅ 조건 다이얼로그 데이터 새로고침 완료")
            
        except Exception as e:
            print(f"❌ 조건 다이얼로그 새로고침 실패: {e}")
    
    def show_variable_info(self):
        """변수 지원 현황 정보"""
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("📋 변수 지원 현황")
        info_dialog.setMinimumSize(500, 350)
        
        layout = QVBoxLayout()
        
        info_text = """
🎯 현재 지원되는 변수들:

📈 기술 지표:
• RSI - 상대강도지수 (과매수/과매도)
• SMA - 단순이동평균 (추세 확인)  
• EMA - 지수이동평균 (빠른 신호)
• BOLLINGER_BAND - 볼린저밴드 (변동성)
• MACD - 추세 변화 감지

💰 시장 데이터:
• CURRENT_PRICE - 현재가
• OPEN_PRICE - 시가
• HIGH_PRICE - 고가
• LOW_PRICE - 저가
• VOLUME - 거래량

🏦 자본 관리:
• CASH_BALANCE - 현금 잔고
• COIN_BALANCE - 코인 보유량
• TOTAL_BALANCE - 총 자산

📊 포지션 상태:
• PROFIT_PERCENT - 수익률(%)
• PROFIT_AMOUNT - 수익 금액
• POSITION_SIZE - 포지션 크기
• AVG_BUY_PRICE - 평균 매수가

💡 각 변수마다 개별 파라미터 설정 가능!
        """
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("""
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Malgun Gothic';
            line-height: 1.5;
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        close_btn = QPushButton("확인")
        close_btn.clicked.connect(info_dialog.accept)
        layout.addWidget(close_btn)
        
        info_dialog.setLayout(layout)
        info_dialog.exec()
    
    def show_variable_help(self):
        """현재 선택된 변수의 상세 도움말"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            QMessageBox.information(self, "💡 도움말", "먼저 변수를 선택해주세요.")
            return
        
        # TODO: 상세 도움말 다이얼로그 구현
        QMessageBox.information(self, "💡 도움말", f"{var_id} 변수의 상세 도움말을 준비 중입니다.")
    
    def get_condition_data(self):
        """생성된 조건 데이터 반환"""
        return self.current_condition

# 실행 코드
if __name__ == "__main__":
    print("🚀 조건 생성기 v4 (컴포넌트 기반) 시작!")
    
    app = QApplication(sys.argv)
    
    print("📊 위젯 생성 중...")
    widget = ConditionDialog()
    
    print("🎯 위젯 표시!")
    widget.show()
    
    app.exec()
    print("🔚 프로그램 종료!")
