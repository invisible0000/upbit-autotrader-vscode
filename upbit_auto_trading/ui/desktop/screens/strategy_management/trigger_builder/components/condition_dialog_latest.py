#!/usr/bin/env python3
"""
리팩토링된 조건 다이얼로그 - 컴포넌트 기반 아키텍처
"""

import sys
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
    QLabel, QMessageBox, QDialog, QComboBox, QLineEdit, 
    QButtonGroup, QRadioButton, QApplication, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Any, Optional

# 공통 컴포넌트 import
try:
    from upbit_auto_trading.ui.desktop.common.components import (
        PrimaryButton, SecondaryButton, DangerButton,
        StyledLineEdit, StyledComboBox, StyledCheckBox, StyledGroupBox,
        CardWidget, FormRow
    )
    STYLED_COMPONENTS_AVAILABLE = True
except ImportError:
    # 공통 컴포넌트가 없을 경우 기본 위젯 사용
    PrimaryButton = QPushButton
    SecondaryButton = QPushButton
    DangerButton = QPushButton
    StyledLineEdit = QLineEdit
    StyledComboBox = QComboBox
    StyledCheckBox = QCheckBox
    StyledGroupBox = QGroupBox
    CardWidget = QWidget
    FormRow = QWidget
    STYLED_COMPONENTS_AVAILABLE = False

# 컴포넌트들을 절대 경로로 import
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.variable_definitions import VariableDefinitions
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.parameter_widgets import ParameterWidgetFactory
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_validator import ConditionValidator
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_builder import ConditionBuilder
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_storage import ConditionStorage
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.preview_components import PreviewGenerator

# 변수 호환성 검증 import
try:
    from .chart_variable_service import get_chart_variable_service
    COMPATIBILITY_SERVICE_AVAILABLE = True
except ImportError:
    COMPATIBILITY_SERVICE_AVAILABLE = False
    print("⚠️ 차트 변수 호환성 서비스를 사용할 수 없습니다.")

class ConditionDialog(QWidget):
    """리팩토링된 조건 생성 위젯 (다이얼로그에서 위젯으로 변경)"""
    
    # 시그널 정의
    condition_saved = pyqtSignal(dict)  # 조건 저장 완료 시그널
    edit_mode_changed = pyqtSignal(bool)  # 편집 모드 변경 시그널
    
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
        
        # 편집 모드 관련 속성
        self.edit_mode = False
        self.edit_condition_id = None
        self.editing_condition_name = None
        
        # 호환성 상태 표시용 라벨
        self.compatibility_status_label = None
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🎯 조건 생성기 v4 (컴포넌트 기반)")
        self.setMinimumSize(500, 400)  # 크기 대폭 줄이기
        layout = QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)  # 마진 더 줄이기
        layout.setSpacing(2)  # 간격 더 줄이기
        
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
        group = StyledGroupBox("📊 1단계: 변수 선택")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(2)
        
        # 범주 + 변수 선택을 한 줄로 합치기
        category_var_layout = QHBoxLayout()
        
        # 범주 선택
        category_var_layout.addWidget(QLabel("범주:"))
        
        self.category_combo = StyledComboBox()
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
        self.variable_combo = StyledComboBox()
        category_var_layout.addWidget(self.variable_combo)
        
        # 변수별 헬프 버튼
        help_btn = QPushButton("?")
        help_btn.setMaximumWidth(30)
        help_btn.setMinimumWidth(30)
        help_btn.setFixedHeight(25)
        help_btn.setToolTip("선택한 변수의 상세 도움말")
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                color: #495057;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:pressed {
                background-color: #adb5bd;
            }
        """)
        help_btn.clicked.connect(self.show_variable_help)
        category_var_layout.addWidget(help_btn)
        
        # 지원 현황 버튼
        info_btn = PrimaryButton("📋 지원 현황")
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
        group = StyledGroupBox("⚖️ 2단계: 비교 설정")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(2)
        
        # 비교값, 연산자, 외부값 사용 버튼을 한 줄로 배치
        comparison_layout = QHBoxLayout()
        
        # 비교값
        comparison_layout.addWidget(QLabel("비교값:"))
        self.target_input = StyledLineEdit("예: 70, 30, 0.5")
        self.target_input.setMinimumWidth(100)  # 비교값 입력 박스 폭 확장
        comparison_layout.addWidget(self.target_input)
        
        # 간격 추가
        comparison_layout.addSpacing(15)
        
        # 연산자
        comparison_layout.addWidget(QLabel("연산자:"))
        
        self.operator_combo = StyledComboBox()
        self.operator_combo.setMaximumWidth(130)  # 연산자 콤보박스 폭 제한
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
        comparison_layout.addWidget(self.operator_combo)
        
        # 간격 추가
        comparison_layout.addSpacing(15)
        
        # 외부값 사용 버튼
        self.use_external_variable = SecondaryButton("🔄 외부값 사용")
        self.use_external_variable.setCheckable(True)
        self.use_external_variable.setMaximumWidth(120)  # 외부값 사용 버튼 폭 늘리기
        self.use_external_variable.setMinimumWidth(120)  # 최소 폭도 설정
        self.use_external_variable.clicked.connect(self.toggle_comparison_mode)
        comparison_layout.addWidget(self.use_external_variable)
        comparison_layout.addStretch()
        group_layout.addLayout(comparison_layout)
        
        # 추세 방향성을 한 줄로 배치
        trend_layout = QHBoxLayout()
        trend_layout.addWidget(QLabel("추세 방향성:"))
        trend_layout.addSpacing(10)  # 레이블과 첫 번째 라디오 버튼 사이 간격
        
        self.trend_group = QButtonGroup()
        
        trend_options = [
            ("rising", "상승 추세"),
            ("falling", "하락 추세"),
            ("both", "추세 무관")
        ]
        
        for i, (trend_id, trend_name) in enumerate(trend_options):
            radio = QRadioButton(trend_name)
            radio.setProperty("trend_id", trend_id)
            self.trend_group.addButton(radio)
            trend_layout.addWidget(radio)
            
            # 라디오 버튼들 사이에 간격 추가 (마지막 제외)
            if i < len(trend_options) - 1:
                trend_layout.addSpacing(15)
            
            if trend_id == "both":  # 기본값을 "추세 무관"으로 변경
                radio.setChecked(True)
        
        trend_layout.addStretch()
        group_layout.addLayout(trend_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_external_variable_section(self, layout):
        """외부 변수 설정 섹션"""
        self.external_variable_widget = StyledGroupBox("🔗 2-1단계: 외부 변수 설정 (골든크로스 등)")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(2)
        
        # 범주와 변수 선택을 한 줄로 배치
        category_var_layout = QHBoxLayout()
        
        # 범주 선택
        category_var_layout.addWidget(QLabel("범주:"))
        
        self.external_category_combo = StyledComboBox()
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
        
        # 간격 추가
        category_var_layout.addSpacing(20)
        
        # 변수 선택
        category_var_layout.addWidget(QLabel("변수:"))
        self.external_variable_combo = StyledComboBox()
        self.external_variable_combo.setMinimumWidth(250)  # 2.5배 폭 확장
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
        self.external_param_scroll, self.external_param_layout = (
            self.parameter_factory.create_scrollable_parameter_area(80, 120)
        )
        group_layout.addWidget(self.external_param_scroll)
        
        # 초기에는 비활성화
        self.external_variable_widget.setEnabled(False)
        self.external_variable_widget.setStyleSheet("QGroupBox { color: #999; }")
        
        self.external_variable_widget.setLayout(group_layout)
        layout.addWidget(self.external_variable_widget)
    
    def create_info_section(self, layout):
        """조건 정보 섹션"""
        group = StyledGroupBox("📝 3단계: 조건 정보")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(4, 4, 4, 4)
        group_layout.setSpacing(2)
        
        # 조건 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("이름:"))
        self.condition_name = StyledLineEdit("예: RSI 과매수 진입")
        name_layout.addWidget(self.condition_name)
        group_layout.addLayout(name_layout)
        
        # 설명
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("설명:"))
        self.condition_description = StyledLineEdit()
        self.condition_description.setPlaceholderText("이 조건이 언제 발생하는지 설명해주세요.")
        desc_layout.addWidget(self.condition_description)
        group_layout.addLayout(desc_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_preview_section(self, layout):
        """미리보기 섹션"""
        group = StyledGroupBox("👀 미리보기")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(4, 4, 4, 4)
        group_layout.setSpacing(2)
        
        self.preview_label = QLabel("조건을 설정하면 미리보기가 표시됩니다.")
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                padding: 6px;
                border: 2px dashed #dee2e6;
                border-radius: 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
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
    
    def update_variable_description(self):
        """변수 설명 업데이트 - 설명 박스가 제거됨"""
        # 변수 설명 박스가 제거되어서 더 이상 사용하지 않음
        pass
    
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
            self.target_input.setStyleSheet("""
                QLineEdit {
                    background-color: #f8f9fa;
                    color: #6c757d;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 4px 8px;
                }
            """)
            self.use_external_variable.setText("🔄 고정값 사용")
            self.update_external_variables()
            # 외부변수 모드로 전환 시 호환성 검증
            self.check_variable_compatibility()
        else:
            # 기본 스타일로 복원
            self.target_input.setStyleSheet("")
            self.use_external_variable.setText("🔄 외부값 사용")
            self.update_placeholders()
            # 고정값 모드로 전환 시 호환성 라벨 숨기기
            self.update_compatibility_for_fixed_mode()
        
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
    
    def update_preview(self):
        """미리보기 업데이트"""
        condition_data = self.collect_condition_data_for_preview()
        if condition_data:
            preview_text = self.preview_generator.generate_condition_preview(condition_data)
            self.preview_label.setText(preview_text)
    
    def collect_condition_data_for_preview(self) -> Optional[Dict[str, Any]]:
        """미리보기용 조건 데이터 수집 (이름 검증 없음)"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            return None
        
        # 조건 이름 (검증 없이 가져오기)
        condition_name = self.condition_name.text().strip()
        if not condition_name:
            condition_name = "이름 미입력"  # 미리보기용 기본값
        
        # 추세 방향성
        trend_direction = "both"  # 기본값 변경
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

    def collect_condition_data(self) -> Optional[Dict[str, Any]]:
        """현재 UI 상태에서 조건 데이터 수집 (이름 검증 추가)"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            return None
        
        # 조건 이름 검증
        condition_name = self.condition_name.text().strip()
        if not condition_name:
            # 편집 모드가 아닌 경우 더 명확한 안내
            if not self.edit_mode:
                QMessageBox.warning(self, "⚠️ 경고", 
                                  "조건 이름이 비어 있습니다.\n\n"
                                  "💡 조건을 저장하려면:\n"
                                  "1. 조건 이름을 입력해주세요\n"
                                  "2. 또는 편집하고 싶은 트리거를 먼저 선택하고 '편집' 버튼을 누르세요")
            else:
                QMessageBox.warning(self, "⚠️ 경고", "조건 이름이 비어 있으면 저장할 수 없습니다.\n조건 이름을 입력해주세요.")
            return None
        
        # 추세 방향성
        trend_direction = "both"  # 기본값 변경
        for button in self.trend_group.buttons():
            if button.isChecked():
                trend_direction = button.property("trend_id")
                break
        
        # 외부 변수 정보
        external_variable_info = None
        if self.use_external_variable.isChecked():
            external_var_id = self.external_variable_combo.currentData()
            if external_var_id:
                # 외부변수의 파라미터 수집
                external_param_key = f"{external_var_id}_external"
                external_params = self.parameter_factory.get_parameter_values(external_param_key)
                
                external_variable_info = {
                    'variable_id': external_var_id,
                    'variable_name': self.external_variable_combo.currentText(),
                    'category': self.external_category_combo.currentData(),
                    'variable_params': external_params  # 외부변수 파라미터 추가
                }
        
        condition_data = {
            'name': condition_name,  # 자동 생성 제거
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
    
    def load_condition(self, condition_data: Dict[str, Any]):
        """기존 조건을 UI에 로드 (편집용)"""
        try:
            print(f"🔧 조건 로드 시작: ID {condition_data.get('id')}")
            
            # 편집 모드 설정
            self.edit_mode = True
            self.edit_condition_id = condition_data.get('id')
            self.editing_condition_name = condition_data.get('name', '')
            
            # 편집 모드 변경 시그널 발생
            self.edit_mode_changed.emit(True)
            
            # 조건 정보 로드
            self.condition_name.setText(condition_data.get('name', ''))
            self.condition_name.setReadOnly(False)  # 편집 모드에서도 이름 수정 가능
            
            # 윈도우 타이틀 변경
            self.setWindowTitle(f"🔧 조건 편집: {condition_data.get('name', 'Unknown')}")
            
            # 설명 설정
            self.condition_description.setText(condition_data.get('description', ''))
            
            # 변수 ID에서 카테고리 찾기 (더 정확한 방법)
            variable_id = condition_data.get('variable_id')
            if variable_id:
                # variable_id에서 카테고리를 찾아서 설정
                category = self.variable_definitions.get_variable_category(variable_id)
                print(f"🔍 변수 ID '{variable_id}'의 카테고리: '{category}'")
                
                # 카테고리 콤보박스 설정
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == category:
                        self.category_combo.setCurrentIndex(i)
                        print(f"✅ 카테고리 설정: {category}")
                        break
                
                # 카테고리가 변경되었으므로 변수 목록 업데이트
                self.update_variables_by_category()
                
                # 변수 콤보박스에서 해당 변수 찾아서 설정
                for i in range(self.variable_combo.count()):
                    if self.variable_combo.itemData(i) == variable_id:
                        self.variable_combo.setCurrentIndex(i)
                        print(f"✅ 변수 설정: {variable_id}")
                        break
                
                # 변수가 변경되었으므로 파라미터 위젯 업데이트
                self.update_variable_params()
                self.update_variable_description()
                self.update_placeholders()
            else:
                print("⚠️ variable_id가 없습니다.")
            
            # 변수 파라미터 설정
            variable_params = condition_data.get('variable_params', {})
            if variable_params:
                # 파라미터 위젯이 생성된 후 값 설정
                if isinstance(variable_params, str):
                    try:
                        variable_params = json.loads(variable_params)
                    except json.JSONDecodeError:
                        variable_params = {}
                
                # 파라미터 값 복원 (variable_id 타입 검증 추가)
                if variable_id and isinstance(variable_id, str):
                    self.parameter_factory.set_parameter_values(variable_id, variable_params)
                    print(f"✅ 주 변수 파라미터 복원: {variable_params}")
                else:
                    print(f"Warning: variable_id가 올바르지 않습니다: {variable_id}")
            
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
                    self.update_external_variables()
                    for i in range(self.external_variable_combo.count()):
                        if self.external_variable_combo.itemData(i) == ext_var_id:
                            self.external_variable_combo.setCurrentIndex(i)
                            break
                    
                    # 외부 변수 파라미터 복원
                    ext_variable_params = external_variable.get('variable_params') or external_variable.get('parameters')
                    if ext_variable_params:
                        if isinstance(ext_variable_params, str):
                            try:
                                ext_variable_params = json.loads(ext_variable_params)
                            except json.JSONDecodeError:
                                ext_variable_params = {}
                        
                        # 외부 변수 파라미터 값 복원
                        if ext_var_id and isinstance(ext_var_id, str):
                            # 외부변수 파라미터 키는 "{variable_id}_external" 형식으로 생성됨
                            external_param_key = f"{ext_var_id}_external"
                            self.parameter_factory.set_parameter_values(external_param_key, ext_variable_params)
                            print(f"✅ 외부 변수 파라미터 복원: {external_param_key} = {ext_variable_params}")
                        else:
                            print(f"Warning: 외부 변수 variable_id가 올바르지 않습니다: {ext_var_id}")
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
            
            # UI 업데이트 - 외부 변수 모드에 따른 UI 상태 설정
            if self.use_external_variable.isChecked():
                self.external_variable_widget.setEnabled(True)
                self.target_input.setEnabled(False)
                self.target_input.setPlaceholderText("외부 변수 사용 중...")
                self.use_external_variable.setText("🔄 고정값 사용")
            else:
                self.external_variable_widget.setEnabled(False)
                self.target_input.setEnabled(True)
                self.use_external_variable.setText("🔄 외부값 사용")
            
            self.update_preview()
            
            print(f"✅ 조건 로드 완료: {condition_data.get('name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ 조건 로드 실패: {e}")
            QMessageBox.critical(self, "❌ 오류", f"조건 로드 중 오류가 발생했습니다:\n{e}")

    def save_condition(self):
        """조건 저장 (편집 모드에서는 업데이트, 신규는 생성)"""
        try:
            # 먼저 조건 이름 검증 (우선순위)
            condition_name = self.condition_name.text().strip()
            if not condition_name:
                QMessageBox.warning(self, "⚠️ 경고", "조건 이름이 비어 있으면 저장할 수 없습니다.\n조건 이름을 입력해주세요.")
                return
            
            # 변수 선택 검증
            var_id = self.variable_combo.currentData()
            if not var_id:
                QMessageBox.warning(self, "⚠️ 경고", "변수를 선택해주세요.")
                return
            
            # 외부변수 사용 시 호환성 최종 검증
            if self.use_external_variable.isChecked():
                base_variable_id = self.get_current_variable_id()
                external_variable_id = self.external_variable_combo.currentData()
                
                if external_variable_id and self.compatibility_service:
                    is_compatible, reason = self.compatibility_service.is_compatible_external_variable(
                        base_variable_id, external_variable_id
                    )
                    
                    if not is_compatible:
                        # 사용자 친화적 오류 메시지 표시
                        base_var_name = self.variable_combo.currentText()
                        external_var_name = self.external_variable_combo.currentText()
                        
                        user_message = self._generate_user_friendly_compatibility_message(
                            base_variable_id, external_variable_id, 
                            base_var_name, external_var_name, reason
                        )
                        
                        QMessageBox.warning(
                            self, "⚠️ 호환성 오류", 
                            f"선택한 변수들은 호환되지 않아 저장할 수 없습니다.\n\n{user_message}\n\n"
                            "호환되는 변수를 선택한 후 다시 저장해주세요."
                        )
                        return
            
            # 조건 데이터 수집
            condition_data = self.collect_condition_data()
            if not condition_data:
                QMessageBox.warning(self, "⚠️ 경고", "조건 데이터를 생성할 수 없습니다.")
                return
            
            # 조건 빌드 및 검증
            is_valid, message, built_condition = self.builder.validate_and_build(condition_data)
            
            if not is_valid or built_condition is None:
                QMessageBox.warning(self, "⚠️ 검증 오류", message)
                return
            
            # 편집 모드인지 확인
            if self.edit_mode and self.edit_condition_id:
                # 편집 모드: 기존 조건 덮어쓰기
                built_condition['id'] = self.edit_condition_id
                # 편집 모드에서는 사용자가 입력한 이름 사용 (변경 허용)
                # built_condition['name']은 이미 collect_condition_data()에서 설정됨
                
                success, save_message, condition_id = self.storage.save_condition(built_condition, overwrite=True)
                operation_type = "편집 완료"
                
                if success:
                    self.current_condition = built_condition
                    if condition_id is not None:
                        self.current_condition['id'] = condition_id
                    
                    # 편집 모드 해제
                    self.exit_edit_mode()
                    
                    # 시그널 발생
                    self.condition_saved.emit(self.current_condition)
                    
                    QMessageBox.information(self, "✅ 성공", f"조건 {operation_type} 완료: {save_message}")
                else:
                    QMessageBox.critical(self, "❌ 오류", save_message)
                    
            else:
                # 신규 생성 모드
                # 첫 번째 저장 시도 (덮어쓰기 없이)
                success, save_message, condition_id = self.storage.save_condition(built_condition, overwrite=False)
                operation_type = "생성"
                
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
                        operation_type = "덮어쓰기"
                    else:
                        return  # 사용자가 취소함
                
                if success:
                    self.current_condition = built_condition
                    if condition_id is not None:
                        self.current_condition['id'] = condition_id
                    
                    # 시그널 발생
                    self.condition_saved.emit(self.current_condition)
                    
                    QMessageBox.information(self, "✅ 성공", f"조건 {operation_type} 완료: {save_message}")
                    # self.accept()  # 창을 닫지 않고 계속 사용 가능하도록
                else:
                    QMessageBox.critical(self, "❌ 오류", save_message)
                
        except Exception as e:
            QMessageBox.critical(self, "❌ 오류", f"조건 저장 중 오류:\n{str(e)}")
    
    def exit_edit_mode(self):
        """편집 모드 해제"""
        self.edit_mode = False
        self.edit_condition_id = None
        self.editing_condition_name = None
        
        # 이름 입력 상자를 다시 편집 가능하게 변경
        self.condition_name.setReadOnly(False)
        self.condition_name.setStyleSheet("")
        
        # 윈도우 타이틀 초기화
        self.setWindowTitle("🎯 조건 생성기 v4 (컴포넌트 기반)")
        
        # 편집 모드 변경 시그널 발생
        self.edit_mode_changed.emit(False)
        
        print("✅ 편집 모드 해제 완료")
    
    def clear_all_inputs(self):
        """모든 입력 필드 초기화"""
        try:
            # 조건 이름과 설명 초기화
            self.condition_name.clear()
            self.condition_description.clear()
            
            # 비교값 초기화 (문제 해결의 핵심)
            self.target_input.clear()
            
            # 콤보박스 초기값으로 설정
            if self.category_combo.count() > 0:
                self.category_combo.setCurrentIndex(0)
            if self.variable_combo.count() > 0:
                self.variable_combo.setCurrentIndex(0)
            if self.operator_combo.count() > 0:
                self.operator_combo.setCurrentIndex(0)
            
            # 외부 변수 관련 필드 초기화
            if hasattr(self, 'external_category_combo') and self.external_category_combo.count() > 0:
                self.external_category_combo.setCurrentIndex(0)
            if hasattr(self, 'external_variable_combo') and self.external_variable_combo.count() > 0:
                self.external_variable_combo.setCurrentIndex(0)
            
            # 외부값 사용 버튼 초기화
            if hasattr(self, 'use_external_variable'):
                self.use_external_variable.setChecked(False)
                self.toggle_comparison_mode()  # 외부값 모드 해제
            
            # 추세 방향성 라디오 버튼 초기화 (추세 무관으로)
            if hasattr(self, 'trend_group'):
                for button in self.trend_group.buttons():
                    if button.property("trend_id") == "both":
                        button.setChecked(True)
                    else:
                        button.setChecked(False)
            
            # 편집 모드 해제
            self.edit_mode = False
            self.edit_condition_id = None
            self.editing_condition_name = None
            
            # 미리보기 초기화
            self.preview_label.setText("조건을 설정하면 미리보기가 표시됩니다.")
            
            # 변수별 파라미터 위젯 초기화
            self.update_variables_by_category()
            
            print("✅ 모든 입력 필드 완전 초기화 완료 (비교값 포함)")
            
        except Exception as e:
            print(f"❌ 입력 필드 초기화 실패: {e}")
    
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
        
        # variable_definitions에서 변수 정보 동적으로 생성
        category_variables = self.variable_definitions.get_category_variables()
        descriptions = self.variable_definitions.get_variable_descriptions()
        
        info_text = "🎯 현재 지원되는 변수들:\n\n"
        
        category_names = {
            "indicator": "📈 기술 지표:",
            "price": "💰 시장 데이터:",
            "capital": "🏦 자본 관리:",
            "state": "📊 포지션 상태:"
        }
        
        for category_id, variables in category_variables.items():
            category_name = category_names.get(category_id, f"🔹 {category_id}:")
            info_text += f"{category_name}\n"
            
            for var_id, var_name in variables:
                desc = descriptions.get(var_id, "설명 준비 중")
                info_text += f"• {var_name} - {desc}\n"
            
            info_text += "\n"
        
        info_text += "💡 각 변수마다 개별 파라미터 설정 가능!\n"
        info_text += "❓ 변수별 상세 도움말은 헬프 버튼(❓)을 클릭하세요."
        
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
        
        # variable_definitions에서 변수 설명 가져오기
        descriptions = self.variable_definitions.get_variable_descriptions()
        desc = descriptions.get(var_id, f"{var_id} 변수의 설명이 준비되지 않았습니다.")
        
        # 변수별 파라미터 정보도 포함
        params = self.variable_definitions.get_variable_parameters(var_id)
        param_info = ""
        if params:
            param_info = "\n\n📋 파라미터:\n"
            for param_name, param_config in params.items():
                label = param_config.get('label', param_name)
                help_text = param_config.get('help', '설명 없음')
                param_info += f"• {label}: {help_text}\n"
        
        # 플레이스홀더 예시도 포함
        placeholders = self.variable_definitions.get_variable_placeholders()
        example_info = ""
        if var_id in placeholders:
            var_placeholders = placeholders[var_id]
            example_info = "\n\n💡 사용 예시:\n"
            if 'target' in var_placeholders:
                example_info += f"• 비교값: {var_placeholders['target']}\n"
            if 'name' in var_placeholders:
                example_info += f"• 조건명: {var_placeholders['name']}\n"
            if 'description' in var_placeholders:
                example_info += f"• 설명: {var_placeholders['description']}\n"
        
        full_help = f"📖 {desc}{param_info}{example_info}"
        
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle(f"💡 {var_id} 변수 도움말")
        help_dialog.setMinimumSize(500, 300)
        
        layout = QVBoxLayout()
        
        help_label = QLabel(full_help)
        help_label.setStyleSheet("""
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Malgun Gothic';
            line-height: 1.5;
        """)
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        close_btn = QPushButton("확인")
        close_btn.clicked.connect(help_dialog.accept)
        layout.addWidget(close_btn)
        
        help_dialog.setLayout(layout)
        help_dialog.exec()
    
    def check_variable_compatibility(self):
        """변수 호환성 검증 및 UI 업데이트"""
        if not self.compatibility_service:
            self.compatibility_status_label.hide()
            return
        
        # 기본 변수와 외부변수 ID 가져오기
        base_variable_id = self.get_current_variable_id()
        external_variable_id = self.external_variable_combo.currentData()
        
        # 외부변수가 선택되지 않았으면 호환성 표시 숨김
        if not external_variable_id or not base_variable_id:
            self.compatibility_status_label.hide()
            return
        
        # 외부변수 모드가 아니면 검증하지 않음
        if not self.use_external_variable.isChecked():
            self.compatibility_status_label.hide()
            return
        
        try:
            # 호환성 검증 수행
            is_compatible, reason = self.compatibility_service.is_compatible_external_variable(
                base_variable_id, external_variable_id
            )
            
            # 변수명 가져오기 (사용자 친화적 표시용)
            base_var_name = self.variable_combo.currentText()
            external_var_name = self.external_variable_combo.currentText()
            
            if is_compatible:
                # 호환 가능한 경우
                self.compatibility_status_label.setText(
                    f"✅ {base_var_name}와(과) {external_var_name}는 호환됩니다."
                )
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
                
                # 저장 버튼 활성화 (만약 비활성화되어 있었다면)
                if hasattr(self, 'save_btn'):
                    self.save_btn.setEnabled(True)
                    
            else:
                # 호환되지 않는 경우
                user_message = self._generate_user_friendly_compatibility_message(
                    base_variable_id, external_variable_id, base_var_name, external_var_name, reason
                )
                
                self.compatibility_status_label.setText(user_message)
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
                
                # 저장 버튼 비활성화 (호환되지 않는 조합 저장 방지)
                if hasattr(self, 'save_btn'):
                    self.save_btn.setEnabled(False)
            
            # 라벨 표시
            self.compatibility_status_label.show()
            
            # 디버깅 로그
            print(f"🔍 호환성 검증: {base_var_name} ↔ {external_var_name} = {is_compatible}")
            if not is_compatible:
                print(f"   사유: {reason}")
                
        except Exception as e:
            # 오류 발생 시
            self.compatibility_status_label.setText(
                f"⚠️ 호환성 검사 중 오류가 발생했습니다: {str(e)}"
            )
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
    
    def _generate_user_friendly_compatibility_message(self, base_var_id: str, external_var_id: str, 
                                                    base_var_name: str, external_var_name: str, 
                                                    reason: str) -> str:
        """사용자 친화적인 호환성 오류 메시지 생성"""
        
        # 특정 조합에 대한 맞춤 메시지
        specific_messages = {
            ('rsi', 'macd'): f"❌ {base_var_name}(오실레이터)와 {external_var_name}(모멘텀 지표)는 서로 다른 카테고리로 비교할 수 없습니다.\n\n💡 제안: RSI와 비교하려면 같은 오실레이터인 '스토캐스틱'을 선택해보세요.",
            
            ('rsi', 'volume'): f"❌ {base_var_name}(0-100% 지표)와 {external_var_name}(거래량)은 완전히 다른 단위로 의미있는 비교가 불가능합니다.\n\n💡 제안: RSI와 비교하려면 같은 퍼센트 지표인 '스토캐스틱'을 선택해보세요.",
            
            ('current_price', 'rsi'): f"❌ {base_var_name}(원화)와 {external_var_name}(퍼센트)는 단위가 달라 비교할 수 없습니다.\n\n💡 제안: 현재가와 비교하려면 같은 가격 지표인 '이동평균'이나 '볼린저밴드'를 선택해보세요.",
            
            ('current_price', 'volume'): f"❌ {base_var_name}(가격)과 {external_var_name}(거래량)은 의미가 달라 비교할 수 없습니다.\n\n💡 제안: 현재가와 비교하려면 같은 가격 지표인 '이동평균'을 선택해보세요.",
            
            ('macd', 'rsi'): f"❌ {base_var_name}(모멘텀 지표)와 {external_var_name}(오실레이터)는 서로 다른 카테고리로 비교할 수 없습니다.\n\n💡 제안: MACD와 비교할 수 있는 모멘텀 지표를 추가로 등록하거나, 다른 변수를 선택해보세요."
        }
        
        key = (base_var_id, external_var_id)
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
    
    def update_compatibility_for_fixed_mode(self):
        """고정값 비교 모드에서 호환성 라벨 숨기기"""
        if hasattr(self, 'compatibility_status_label'):
            self.compatibility_status_label.hide()
            
            # 저장 버튼 다시 활성화 (고정값 모드에서는 호환성 제약 없음)
            if hasattr(self, 'save_btn'):
                self.save_btn.setEnabled(True)
            # 서비스 없으면 호환성 표시 숨김
            self.compatibility_status_label.hide()
            return
        
        # 현재 선택된 변수들 가져오기
        base_var_name = self.variable_combo.currentText()
        external_var_name = self.external_variable_combo.currentText()
        
        # 외부변수가 선택되지 않았으면 상태 숨김
        if not external_var_name or external_var_name == "선택하세요":
            self.compatibility_status_label.hide()
            return
        
        # 변수명을 ID로 변환
        base_var_id = self._get_variable_id_by_name(base_var_name)
        external_var_id = self.external_variable_combo.currentData()
        
        if not base_var_id or not external_var_id:
            self.compatibility_status_label.hide()
            return
        
        try:
            # 호환성 검증
            is_compatible, reason = self.compatibility_service.is_compatible_external_variable(
                base_var_id, external_var_id
            )
            
            # UI 업데이트
            self._update_compatibility_ui(
                is_compatible, base_var_name, external_var_name, reason
            )
            
            # 로그 출력
            status_text = "✅ 호환" if is_compatible else "❌ 비호환"
            print(f"🔍 변수 호환성: {base_var_name} ↔ {external_var_name} = {status_text}")
            if not is_compatible:
                print(f"   사유: {reason}")
                
        except Exception as e:
            # 오류 발생 시 경고 표시
            self._update_compatibility_ui(
                False, base_var_name, external_var_name, f"검증 오류: {e}"
            )
            print(f"❌ 호환성 검증 오류: {e}")
    
    def _get_variable_id_by_name(self, variable_name):
        """변수명으로 ID 조회"""
        # 현재 선택된 변수의 데이터에서 ID 추출
        current_data = self.variable_combo.currentData()
        if current_data:
            return current_data
        
        # 매핑 테이블로 폴백 (기본 변수들)
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
    
    def _update_compatibility_ui(self, is_compatible, base_var_name, 
                                external_var_name, reason):
        """호환성 상태에 따른 UI 업데이트"""
        if is_compatible:
            # 호환 가능 - 초록색 메시지
            message = f"✅ {base_var_name}와(과) {external_var_name}는 호환됩니다."
            self.compatibility_status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0;
                    font-size: 12px;
                }
            """)
            
            # 저장 버튼 활성화 (있다면)
            if hasattr(self, 'save_button'):
                self.save_button.setEnabled(True)
                
        else:
            # 호환 불가 - 빨간색 경고 메시지
            message = self._generate_user_friendly_message(
                base_var_name, external_var_name, reason
            )
            self.compatibility_status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 5px 0;
                    font-size: 12px;
                }
            """)
            
            # 저장 버튼 비활성화 (있다면)
            if hasattr(self, 'save_button'):
                self.save_button.setEnabled(False)
        
        self.compatibility_status_label.setText(message)
        self.compatibility_status_label.show()
    
    def _generate_user_friendly_message(self, base_var, external_var, reason):
        """사용자 친화적인 오류 메시지 생성"""
        # 특정 조합에 대한 맞춤 메시지
        specific_messages = {
            ('RSI', 'MACD'): (
                f"❌ {base_var}(오실레이터)와 {external_var}(모멘텀 지표)는 "
                f"서로 다른 카테고리로 비교할 수 없습니다.\n\n"
                f"💡 제안: RSI와 비교하려면 같은 오실레이터인 '스토캐스틱'을 선택해보세요."
            ),
            ('RSI', '거래량'): (
                f"❌ {base_var}(0-100% 지표)와 {external_var}(거래량)은 "
                f"완전히 다른 단위로 의미있는 비교가 불가능합니다.\n\n"
                f"💡 제안: RSI와 비교하려면 같은 퍼센트 지표인 '스토캐스틱'을 선택해보세요."
            ),
            ('현재가', 'RSI'): (
                f"❌ {base_var}(원화)와 {external_var}(퍼센트)는 "
                f"단위가 달라 비교할 수 없습니다.\n\n"
                f"💡 제안: 현재가와 비교하려면 같은 가격 지표인 '이동평균'이나 '볼린저밴드'를 선택해보세요."
            ),
            ('현재가', '거래량'): (
                f"❌ {base_var}(가격)과 {external_var}(거래량)은 "
                f"의미가 달라 비교할 수 없습니다.\n\n"
                f"💡 제안: 현재가와 비교하려면 같은 가격 지표인 '이동평균'을 선택해보세요."
            ),
        }
        
        key = (base_var, external_var)
        if key in specific_messages:
            return specific_messages[key]
        
        # 기본 메시지
        return (
            f"❌ {base_var}와(과) {external_var}는 호환되지 않습니다.\n\n"
            f"사유: {reason}\n\n"
            f"💡 제안: 같은 카테고리나 호환되는 단위의 변수를 선택해주세요."
        )
    
    
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
