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

# 기존 완성된 컴포넌트들 import (절대 경로)
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.variable_definitions import VariableDefinitions
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.parameter_widgets import ParameterWidgetFactory
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_validator import ConditionValidator
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_builder import ConditionBuilder
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_storage import ConditionStorage
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.preview_components import PreviewGenerator

# 변수 호환성 검증 서비스 import
try:
    from .chart_variable_service import get_chart_variable_service
    COMPATIBILITY_SERVICE_AVAILABLE = True
except ImportError:
    COMPATIBILITY_SERVICE_AVAILABLE = False
    print("⚠️ 차트 변수 호환성 서비스를 사용할 수 없습니다.")

class ConditionDialog(QWidget):
    """리팩토링된 조건 생성 위젯"""
    
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
        
        # 호환성 검증 서비스 초기화
        if COMPATIBILITY_SERVICE_AVAILABLE:
            self.compatibility_service = get_chart_variable_service()
        else:
            self.compatibility_service = None
        
        # UI 관련 속성
        self.current_condition = None
        self.parameter_factory = ParameterWidgetFactory(update_callback=self.update_preview)
        
        # 편집 모드 관리
        self.is_edit_mode = False
        self.current_condition_id = None
        
        # 호환성 상태 표시용 라벨 (나중에 UI에서 생성)
        self.compatibility_status_label = None
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🎯 조건 생성기 v4 (컴포넌트 기반)")
        self.setMinimumSize(500, 400)  # 크기 대폭 축소
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)  # 마진 축소
        layout.setSpacing(3)  # 간격 축소
        
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
        
        # 5. 버튼 섹션
        self.create_button_section(layout)
        
        self.setLayout(layout)
        self.connect_events()
        self.update_variables_by_category()
        
        # UI 초기화 완료 플래그 설정
        self._ui_initialized = True
    
    def create_variable_section(self, layout):
        """변수 선택 섹션"""
        group = QGroupBox("📊 1단계: 변수 선택")
        group_layout = QVBoxLayout()
        
        # 범주 + 변수 선택을 한 줄로 통합
        category_var_layout = QHBoxLayout()
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
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_comparison_section(self, layout):
        """비교 설정 섹션"""
        group = QGroupBox("⚖️ 2단계: 비교 설정")
        group_layout = QVBoxLayout()
        
        # 연산자 + 비교값 + 외부값 사용을 한 줄로 통합
        comparison_main_layout = QHBoxLayout()
        comparison_main_layout.addWidget(QLabel("연산자:"))
        
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
        comparison_main_layout.addWidget(self.operator_combo)
        
        comparison_main_layout.addWidget(QLabel("비교값:"))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("예: 70, 30, 0.5")
        comparison_main_layout.addWidget(self.target_input)
        
        # 외부값 사용 버튼
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
        comparison_main_layout.addWidget(self.use_external_variable)
        
        group_layout.addLayout(comparison_main_layout)
        
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
        
        # 범주 + 변수 선택을 한 줄로 통합
        category_var_layout = QHBoxLayout()
        category_var_layout.addWidget(QLabel("범주:"))
        
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
        category_var_layout.addWidget(self.external_category_combo)
        
        category_var_layout.addWidget(QLabel("변수:"))
        self.external_variable_combo = QComboBox()
        category_var_layout.addWidget(self.external_variable_combo)
        category_var_layout.addStretch()
        
        group_layout.addLayout(category_var_layout)
        
        # 호환성 상태 표시 라벨 추가
        self.compatibility_status_label = QLabel()
        self.compatibility_status_label.setWordWrap(True)
        self.compatibility_status_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                border-radius: 4px;
                margin: 5px 0;
                font-size: 12px;
            }
        """)
        self.compatibility_status_label.hide()  # 초기에는 숨김
        group_layout.addWidget(self.compatibility_status_label)
        
        # 외부 변수 파라미터 (스크롤 가능)
        self.external_param_scroll, self.external_param_layout = self.parameter_factory.create_scrollable_parameter_area(80, 120)
        group_layout.addWidget(self.external_param_scroll)
        
        # 초기에는 비활성화
        self.external_variable_widget.setEnabled(False)
        self.external_variable_widget.setStyleSheet("QGroupBox { color: #999; }")
        
        self.external_variable_widget.setLayout(group_layout)
        layout.addWidget(self.external_variable_widget)
    
    def create_info_section(self, layout):
        """조건 정보 섹션"""
        group = QGroupBox("📝 3단계: 조건 정보")
        group_layout = QVBoxLayout()
        
        # 조건 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("이름:"))
        self.condition_name = QLineEdit()
        self.condition_name.setPlaceholderText("예: RSI 과매수 진입")
        name_layout.addWidget(self.condition_name)
        group_layout.addLayout(name_layout)
        
        # 설명을 한 줄로 압축
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("설명:"))
        self.condition_description = QLineEdit()
        self.condition_description.setPlaceholderText("이 조건이 언제 발생하는지 설명해주세요.")
        desc_layout.addWidget(self.condition_description)
        group_layout.addLayout(desc_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_preview_section(self, layout):
        """미리보기 섹션"""
        group = QGroupBox("👀 미리보기")
        group_layout = QVBoxLayout()
        
        self.preview_label = QLabel("조건을 설정하면 미리보기가 표시됩니다.")
        self.preview_label.setStyleSheet("""
            background: #f8f9fa; 
            padding: 15px; 
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
        """)
        self.preview_label.setWordWrap(True)
        group_layout.addWidget(self.preview_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_button_section(self, layout):
        """버튼 섹션"""
        button_layout = QHBoxLayout()
        
        # 새 조건 버튼 (편집 모드 해제용)
        self.new_condition_btn = QPushButton("🆕 새 조건")
        self.new_condition_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117a8b;
            }
        """)
        self.new_condition_btn.clicked.connect(self._exit_edit_mode)
        button_layout.addWidget(self.new_condition_btn)
        
        button_layout.addStretch()  # 가운데 공간
        
        # 저장 버튼
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.save_btn.clicked.connect(self.save_condition)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def connect_events(self):
        """이벤트 연결"""
        self.category_combo.currentTextChanged.connect(self.update_variables_by_category)
        self.variable_combo.currentTextChanged.connect(self.update_variable_params)
        self.variable_combo.currentTextChanged.connect(self.update_placeholders)
        
        # 외부 변수 관련 이벤트
        self.external_category_combo.currentTextChanged.connect(self.update_external_variables)
        self.external_variable_combo.currentTextChanged.connect(self.update_external_variable_params)
        self.external_variable_combo.currentTextChanged.connect(self.check_variable_compatibility)
        self.external_variable_combo.currentTextChanged.connect(self.update_preview)
        
        # 기본 변수 변경 시에도 호환성 검사
        self.variable_combo.currentTextChanged.connect(self.check_variable_compatibility)
        
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
            
            # 편집 모드에서 pending 파라미터가 있으면 적용
            if hasattr(self, '_pending_main_params') and self._pending_main_params:
                pending = self._pending_main_params
                if pending['variable_id'] == var_id:
                    print(f"🔄 주변수 파라미터 적용: {var_id} -> {pending['parameters']}")
                    self.parameter_factory.set_parameter_values(var_id, pending['parameters'])
                    # pending 파라미터 제거
                    del self._pending_main_params
    
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
            # 외부변수 모드 전환 시 호환성 검증
            self.check_variable_compatibility()
        else:
            self.target_input.setStyleSheet("")
            self.use_external_variable.setText("🔄 외부값 사용")
            self.external_variable_widget.setStyleSheet("QGroupBox { color: #999; }")
            self.update_placeholders()
            # 고정값 모드로 전환 시 호환성 라벨 숨기기
            if self.compatibility_status_label:
                self.compatibility_status_label.hide()
        
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
        
        # 파라미터 생성
        params = self.variable_definitions.get_variable_parameters(external_var_id)
        if params:
            self.parameter_factory.create_parameter_widgets(
                f"{external_var_id}_external", params, self.external_param_layout
            )
            
            # 편집 모드에서 pending 파라미터가 있으면 적용
            if hasattr(self, '_pending_external_params') and self._pending_external_params:
                pending = self._pending_external_params
                if pending['variable_id'] == external_var_id:
                    print(f"🔄 외부변수 파라미터 적용: {external_var_id} -> {pending['parameters']}")
                    self.parameter_factory.set_parameter_values(
                        f"{external_var_id}_external", 
                        pending['parameters']
                    )
                    # pending 파라미터 제거
                    del self._pending_external_params
    
    def update_preview(self):
        """미리보기 업데이트"""
        # UI 초기화 완료 여부 확인
        if not hasattr(self, '_ui_initialized') or not self._ui_initialized:
            return
            
        condition_data = self.collect_condition_data()
        if condition_data:
            preview_text = self.preview_generator.generate_condition_preview(condition_data)
            self.preview_label.setText(preview_text)
    
    def collect_condition_data(self) -> Optional[Dict[str, Any]]:
        """현재 UI 상태에서 조건 데이터 수집"""
        var_id = self.variable_combo.currentData()
        if not var_id:
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
        
        # 이름 검증 - 조용히 처리 (경고창 없이)
        condition_name = self.condition_name.text().strip()
        if not condition_name:
            return None  # 경고창 없이 조용히 None 반환
        
        condition_data = {
            'name': condition_name,
            'description': self.condition_description.text().strip(),
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
    
    def save_condition(self):
        """조건 저장 (덮어쓰기 확인 포함)"""
        try:
            # UI 초기화 완료 여부 확인
            if not hasattr(self, '_ui_initialized') or not self._ui_initialized:
                print("[DEBUG] UI 초기화 미완료 - save_condition 호출 무시")
                return
                
            # 변수 선택 상태를 미리 확인 (경고창 없이)
            if not self.variable_combo.currentData():
                print("[DEBUG] 변수 미선택 - save_condition 호출 무시")
                return
            
            # 조건명 입력 확인 (저장 시에만 경고)
            condition_name = self.condition_name.text().strip()
            if not condition_name:
                QMessageBox.warning(self, "⚠️ 경고", "조건명을 입력해주세요.")
                return
            
            # 외부변수 사용 시 호환성 최종 검증
            if (hasattr(self, 'use_external_variable') and 
                self.use_external_variable.isChecked() and 
                self.compatibility_service):
                
                base_variable_name = self.variable_combo.currentText()
                external_variable_name = self.external_variable_combo.currentText()
                
                if external_variable_name and base_variable_name:
                    is_compatible, reason = self.compatibility_service.is_compatible_external_variable(
                        base_variable_name, external_variable_name
                    )
                    
                    if not is_compatible:
                        # 사용자 친화적 오류 메시지 표시
                        base_var_name = self.variable_combo.currentText()
                        external_var_name = self.external_variable_combo.currentText()
                        
                        user_message = self._generate_user_friendly_compatibility_message(
                            base_variable_name, external_variable_name, 
                            base_var_name, external_var_name, reason
                        )
                        
                        QMessageBox.warning(
                            self, "⚠️ 호환성 오류", 
                            f"선택한 변수들은 호환되지 않아 저장할 수 없습니다.\n\n{user_message}\n\n"
                            "호환되는 변수를 선택한 후 다시 저장해주세요."
                        )
                        return
                
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
                
                # 편집 모드에 따른 메시지 표시
                if self.is_edit_mode:
                    QMessageBox.information(self, "✅ 업데이트 완료", "조건이 성공적으로 업데이트되었습니다.")
                    # 편집 모드 해제는 사용자가 직접 닫기 버튼을 누르거나 새 조건 버튼을 누를 때
                else:
                    QMessageBox.information(self, "✅ 저장 완료", save_message)
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
    
    def load_condition(self, condition_data: Dict[str, Any]):
        """기존 조건 데이터를 UI에 로드 (편집용)"""
        try:
            print(f"🔄 조건 로드 시작: {condition_data.get('name', 'Unknown')}")
            
            # 편집 모드 활성화
            self.is_edit_mode = True
            self.current_condition_id = condition_data.get('id')
            
            # 1. 조건 이름과 설명
            self.condition_name.setText(condition_data.get('name', ''))
            self.condition_description.setText(condition_data.get('description', ''))
            
            # 편집 모드 UI 설정
            self._setup_edit_mode_ui()
            
            # 2. 변수 선택
            variable_id = condition_data.get('variable_id', '')
            if variable_id:
                # 변수의 카테고리 찾기
                category_variables = self.variable_definitions.get_category_variables()
                target_category = None
                
                for category_id, variables in category_variables.items():
                    for var_id, var_name in variables:
                        if var_id == variable_id:
                            target_category = category_id
                            break
                    if target_category:
                        break
                
                if target_category:
                    # 카테고리 설정
                    for i in range(self.category_combo.count()):
                        if self.category_combo.itemData(i) == target_category:
                            self.category_combo.setCurrentIndex(i)
                            break
                    
                    # 변수 업데이트 및 선택
                    self.update_variables_by_category()
                    for i in range(self.variable_combo.count()):
                        if self.variable_combo.itemData(i) == variable_id:
                            self.variable_combo.setCurrentIndex(i)
                            break
            
            # 3. 연산자 설정
            operator = condition_data.get('operator', '>')
            for i in range(self.operator_combo.count()):
                if self.operator_combo.itemData(i) == operator:
                    self.operator_combo.setCurrentIndex(i)
                    break
            
            # 4. 대상값 설정
            target_value = condition_data.get('target_value', '')
            if target_value:
                self.target_input.setText(str(target_value))
            
            # 5. 외부 변수 설정 (있는 경우)
            external_variable = condition_data.get('external_variable')
            if external_variable:
                self.use_external_variable.setChecked(True)
                self.toggle_comparison_mode()
                
                # 외부 변수 카테고리와 변수 설정
                ext_category = external_variable.get('category', '')
                ext_variable_id = external_variable.get('variable_id', '')
                
                # 외부 카테고리 설정
                for i in range(self.external_category_combo.count()):
                    if self.external_category_combo.itemData(i) == ext_category:
                        self.external_category_combo.setCurrentIndex(i)
                        break
                
                # 외부 변수 설정
                self.update_external_variables()
                for i in range(self.external_variable_combo.count()):
                    if self.external_variable_combo.itemData(i) == ext_variable_id:
                        self.external_variable_combo.setCurrentIndex(i)
                        break
            
            # 6. 추세 방향성 설정
            trend_direction = condition_data.get('trend_direction', 'static')
            for button in self.trend_group.buttons():
                if button.property("trend_id") == trend_direction:
                    button.setChecked(True)
                    break
            
            # 7. 파라미터 복원
            self._restore_parameters(condition_data)
            
            # 8. 미리보기 업데이트
            self.update_preview()
            
            print(f"✅ 조건 로드 완료: {condition_data.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ 조건 로드 실패: {e}")
            QMessageBox.warning(self, "⚠️ 로드 오류", f"조건 로드 중 오류가 발생했습니다:\n{str(e)}")
    
    def _restore_parameters(self, condition_data: Dict[str, Any]):
        """파라미터 복원"""
        try:
            # 주 변수 파라미터 복원
            variable_id = condition_data.get('variable_id', '')
            variable_params = condition_data.get('variable_params')
            
            if variable_id and variable_params:
                if isinstance(variable_params, str):
                    import json
                    variable_params = json.loads(variable_params)
                
                print(f"🔄 주변수 파라미터 복원 예약: {variable_id} -> {variable_params}")
                # 주변수 파라미터는 변수 선택 후에 복원되어야 함
                self._pending_main_params = {
                    'variable_id': variable_id,
                    'parameters': variable_params
                }
            
            # 외부 변수 파라미터 복원
            external_variable = condition_data.get('external_variable')
            if external_variable:
                if isinstance(external_variable, str):
                    import json
                    external_variable = json.loads(external_variable)
                
                ext_variable_id = external_variable.get('variable_id', '')
                ext_parameters = external_variable.get('parameters', {})
                
                if ext_variable_id and ext_parameters:
                    print(f"🔄 외부변수 파라미터 복원 예약: {ext_variable_id} -> {ext_parameters}")
                    # 외부변수 파라미터는 변수 선택 후에 복원되어야 함
                    self._pending_external_params = {
                        'variable_id': ext_variable_id,
                        'parameters': ext_parameters
                    }
                    
        except Exception as e:
            print(f"⚠️ 파라미터 복원 실패: {e}")
    
    def _setup_edit_mode_ui(self):
        """편집 모드 UI 설정"""
        if self.is_edit_mode:
            # 조건 이름을 읽기 전용으로 설정
            self.condition_name.setReadOnly(True)
            self.condition_name.setStyleSheet("""
                QLineEdit {
                    background-color: #f0f0f0;
                    color: #666666;
                    border: 2px solid #ddd;
                }
            """)
            
            # 윈도우 타이틀 변경
            condition_name = self.condition_name.text() or 'Unknown'
            self.setWindowTitle(f"🔧 조건 편집: {condition_name}")
    
    def _exit_edit_mode(self):
        """편집 모드 해제"""
        self.is_edit_mode = False
        self.current_condition_id = None
        
        # 조건 이름 필드를 다시 편집 가능하게 설정
        self.condition_name.setReadOnly(False)
        self.condition_name.setStyleSheet("")
        
        # 윈도우 타이틀 복원
        self.setWindowTitle("🎯 조건 생성기 v4 (컴포넌트 기반)")
        
        # 폼 초기화
        self.condition_name.clear()
        self.condition_description.clear()
        self.target_input.clear()
        
        # 콤보박스 초기화
        self.category_combo.setCurrentIndex(0)
        self.variable_combo.setCurrentIndex(0)
        self.operator_combo.setCurrentIndex(0)
        
        # 외부변수 체크박스 해제
        self.use_external_variable.setChecked(False)
        self.toggle_comparison_mode()
        
        # 미리보기 업데이트
        self.update_preview()
    
    def check_variable_compatibility(self):
        """변수 호환성 검증 및 UI 업데이트"""
        if not self.compatibility_service:
            # 서비스가 없으면 호환성 표시 숨김
            if self.compatibility_status_label:
                self.compatibility_status_label.hide()
            return
        
        # 기본 변수와 외부변수 이름 가져오기
        base_variable_name = self.variable_combo.currentText()
        external_variable_name = self.external_variable_combo.currentText()
        
        # 외부변수가 선택되지 않았거나 외부변수 모드가 아니면 호환성 표시 숨김
        if (not external_variable_name or not base_variable_name or 
            not hasattr(self, 'use_external_variable') or 
            not self.use_external_variable.isChecked()):
            if self.compatibility_status_label:
                self.compatibility_status_label.hide()
            return
        
        try:
            # 호환성 검증 수행
            is_compatible, reason = self.compatibility_service.is_compatible_external_variable(
                base_variable_name, external_variable_name
            )
            
            # 변수명 가져오기 (사용자 친화적 표시용)
            base_var_name = self.variable_combo.currentText()
            external_var_name = self.external_variable_combo.currentText()
            
            if is_compatible:
                # 호환 가능한 경우
                message = f"✅ {base_var_name}와(과) {external_var_name}는 호환됩니다."
                self.compatibility_status_label.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        border-radius: 4px;
                        margin: 5px 0;
                        font-size: 12px;
                        background-color: #d4edda;
                        color: #155724;
                        border: 1px solid #c3e6cb;
                    }
                """)
            else:
                # 호환되지 않는 경우
                message = self._generate_user_friendly_compatibility_message(
                    base_variable_name, external_variable_name, base_var_name, external_var_name, reason
                )
                self.compatibility_status_label.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        border-radius: 4px;
                        margin: 5px 0;
                        font-size: 12px;
                        background-color: #f8d7da;
                        color: #721c24;
                        border: 1px solid #f5c6cb;
                    }
                """)
            
            # 메시지 설정 및 라벨 표시
            self.compatibility_status_label.setText(message)
            self.compatibility_status_label.show()
            
            # 디버깅 로그
            print(f"🔍 호환성 검증: {base_var_name} ↔ {external_var_name} = {is_compatible}")
            if not is_compatible:
                print(f"   사유: {reason}")
                
        except Exception as e:
            # 오류 발생 시
            error_message = f"⚠️ 호환성 검사 중 오류가 발생했습니다: {str(e)}"
            self.compatibility_status_label.setText(error_message)
            self.compatibility_status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0;
                    font-size: 12px;
                    background-color: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeaa7;
                }
            """)
            self.compatibility_status_label.show()
            print(f"❌ 호환성 검증 오류: {e}")
    
    def _generate_user_friendly_compatibility_message(self, base_var_name_id: str, external_var_name_id: str, 
                                                    base_var_name: str, external_var_name: str, 
                                                    reason: str) -> str:
        """사용자 친화적인 호환성 오류 메시지 생성"""
        # 특정 조합에 대한 맞춤 메시지
        specific_messages = {
            ('rsi', 'macd'): f"❌ {base_var_name}(오실레이터)와 {external_var_name}(모멘텀 지표)는 서로 다른 카테고리로 비교할 수 없습니다.\n\n💡 제안: RSI와 비교하려면 같은 오실레이터인 '스토캐스틱'을 선택해보세요.",
            
            ('rsi', 'volume'): f"❌ {base_var_name}(0-100% 지표)와 {external_var_name}(거래량)은 완전히 다른 단위로 의미있는 비교가 불가능합니다.\n\n💡 제안: RSI와 비교하려면 같은 퍼센트 지표인 '스토캐스틱'을 선택해보세요.",
            
            ('current_price', 'rsi'): f"❌ {base_var_name}(원화)와 {external_var_name}(퍼센트)는 단위가 달라 비교할 수 없습니다.\n\n💡 제안: 현재가와 비교하려면 같은 가격 지표인 '이동평균'이나 '볼린저밴드'를 선택해보세요.",
            
            ('current_price', 'volume'): f"❌ {base_var_name}(가격)과 {external_var_name}(거래량)은 의미가 달라 비교할 수 없습니다.\n\n💡 제안: 현재가와 비교하려면 같은 가격 지표인 '이동평균'을 선택해보세요.",
        }
        
        key = (base_var_name_id, external_var_name_id)
        if key in specific_messages:
            return specific_messages[key]
        
        # 기본 메시지
        return f"❌ {base_var_name}와(과) {external_var_name}는 호환되지 않습니다.\n\n사유: {reason}\n\n💡 제안: 같은 카테고리나 호환되는 단위의 변수를 선택해주세요."
    
    def get_current_variable_id(self) -> str:
        """현재 선택된 기본 변수의 ID 반환"""
        # 먼저 콤보박스의 currentData()에서 직접 가져오기
        var_id = self.variable_combo.currentData()
        if var_id:
            return var_id
        
        # 콤보박스 데이터가 없으면 변수명으로 매핑
        variable_name = self.variable_combo.currentText()
        
        # 아이콘 제거하고 순수 변수명만 추출
        if " " in variable_name:
            clean_name = variable_name.split(" ", 1)[-1]  # 첫 번째 공백 뒤의 텍스트
        else:
            clean_name = variable_name
        
        # 변수명을 ID로 매핑
        name_to_id_mapping = {
            "RSI 지표": "rsi",
            "RSI": "rsi",
            "MACD 지표": "macd", 
            "MACD": "macd",
            "스토캐스틱": "stochastic",
            "현재가": "current_price",
            "이동평균": "moving_average",
            "볼린저밴드": "bollinger_band",
            "거래량": "volume",
            "기하평균": "geometric_mean",
            "CCI": "cci",
            "DMI": "dmi"
        }
        
        # 정확한 매핑 찾기
        mapped_id = name_to_id_mapping.get(clean_name)
        if mapped_id:
            return mapped_id
        
        # 부분 매칭 시도
        for name_key, id_value in name_to_id_mapping.items():
            if name_key.lower() in clean_name.lower() or clean_name.lower() in name_key.lower():
                return id_value
        
        # 마지막 폴백: 변수명을 소문자로 변환하고 공백을 언더스코어로
        return clean_name.lower().replace(" ", "_").replace("지표", "")



# 실행 코드
if __name__ == "__main__":
    print("🚀 조건 생성기 v4 (컴포넌트 기반) 시작!")
    
    app = QApplication(sys.argv)
    
    print("📊 위젯 생성 중...")
    widget = ConditionDialog()
    
    print("🎯 위젯 표시!")
    widget.show()
    
    print("🔚 이벤트 루프 시작!")
    sys.exit(app.exec())
