"""
원자적 컴포넌트 기반 전략 빌더 UI
- 위계적 컴포넌트 조합을 위한 직관적 드래그앤드롭 인터페이스
- 실시간 옵션 제안 및 설명 시스템
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTabWidget, QGroupBox, QPushButton, 
                           QScrollArea, QLabel, QComboBox, QLineEdit, QSpinBox,
                           QSlider, QDialog, QDialogButtonBox, QInputDialog,
                           QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
from typing import Dict, List, Any, Optional
from atomic_strategy_components import *

class ComponentPalette(QWidget):
    """컴포넌트 팔레트 - 사용자가 선택할 수 있는 모든 원자적 요소들"""
    
    componentSelected = pyqtSignal(str, dict)  # component_type, component_data
    
    def __init__(self):
        super().__init__()
        self.builder = StrategyBuilder()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 카테고리별 탭
        tab_widget = QTabWidget()
        
        # 1. 변수 탭
        variables_tab = self.create_variables_tab()
        tab_widget.addTab(variables_tab, "📊 변수")
        
        # 2. 조건 탭  
        conditions_tab = self.create_conditions_tab()
        tab_widget.addTab(conditions_tab, "🎯 조건")
        
        # 3. 액션 탭
        actions_tab = self.create_actions_tab()
        tab_widget.addTab(actions_tab, "⚡ 액션")
        
        layout.addWidget(tab_widget)
        self.setLayout(layout)
    
    def create_variables_tab(self):
        """변수 선택 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 카테고리별 그룹
        for category in VariableCategory:
            group = QGroupBox(category.value)
            group_layout = QVBoxLayout()
            
            variables = [v for v in self.builder.variables.values() 
                        if v.category == category]
            
            for variable in variables:
                btn = QPushButton(f"{variable.ui_icon} {variable.name}")
                btn.setToolTip(variable.description)
                btn.clicked.connect(
                    lambda checked, v=variable: self.show_variable_config(v)
                )
                group_layout.addWidget(btn)
            
            group.setLayout(group_layout)
            layout.addWidget(group)
        
        widget.setLayout(layout)
        return widget
    
    def create_conditions_tab(self):
        """조건 선택 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 기본 조건들
        basic_group = QGroupBox("기본 조건")
        basic_layout = QVBoxLayout()
        
        for condition in self.builder.conditions.values():
            btn = QPushButton(f"{condition.ui_icon} {condition.name}")
            btn.setToolTip(condition.description)
            btn.clicked.connect(
                lambda checked, c=condition: self.select_condition(c)
            )
            basic_layout.addWidget(btn)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # 커스텀 조건 생성
        custom_group = QGroupBox("커스텀 조건 생성")
        custom_layout = QVBoxLayout()
        
        create_btn = QPushButton("🔧 새 조건 만들기")
        create_btn.clicked.connect(self.create_custom_condition)
        custom_layout.addWidget(create_btn)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_actions_tab(self):
        """액션 선택 탭"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        for action in self.builder.actions.values():
            btn = QPushButton(f"{action.ui_icon} {action.name}")
            btn.setToolTip(action.description)
            btn.clicked.connect(
                lambda checked, a=action: self.select_action(a)
            )
            layout.addWidget(btn)
        
        widget.setLayout(layout)
        return widget
    
    def show_variable_config(self, variable: Variable):
        """변수 설정 다이얼로그"""
        dialog = VariableConfigDialog(variable, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config_data = dialog.get_config()
            self.componentSelected.emit("variable", {
                "variable": variable,
                "config": config_data
            })
    
    def select_condition(self, condition: Condition):
        """조건 선택"""
        self.componentSelected.emit("condition", {"condition": condition})
    
    def select_action(self, action: Action):
        """액션 선택"""
        self.componentSelected.emit("action", {"action": action})
    
    def create_custom_condition(self):
        """커스텀 조건 생성 다이얼로그"""
        dialog = CustomConditionDialog(self.builder, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            condition_id = dialog.get_condition_id()
            if condition_id:
                condition = self.builder.conditions[condition_id]
                self.componentSelected.emit("condition", {"condition": condition})

class VariableConfigDialog(QDialog):
    """변수 설정 다이얼로그 - 파라미터 조정"""
    
    def __init__(self, variable: Variable, parent=None):
        super().__init__(parent)
        self.variable = variable
        self.config_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(f"{self.variable.name} 설정")
        layout = QVBoxLayout()
        
        # 설명
        desc_label = QLabel(self.variable.description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 도움말
        if self.variable.ui_help_text:
            help_label = QLabel(f"💡 {self.variable.ui_help_text}")
            help_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addWidget(help_label)
        
        layout.addWidget(QLabel(""))  # 간격
        
        # 파라미터 설정 위젯들
        for param_name, default_value in self.variable.parameters.items():
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel(f"{param_name}:"))
            
            # 위젯 타입에 따라 다른 입력 방식
            if self.variable.ui_widget_type == "slider":
                constraints = self.variable.ui_constraints
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setMinimum(constraints.get("min", 1))
                slider.setMaximum(constraints.get("max", 100))
                slider.setValue(default_value)
                
                value_label = QLabel(str(default_value))
                slider.valueChanged.connect(
                    lambda v, lbl=value_label: lbl.setText(str(v))
                )
                
                param_layout.addWidget(slider)
                param_layout.addWidget(value_label)
                self.config_widgets[param_name] = slider
                
            elif self.variable.ui_widget_type == "multi_slider":
                constraints = self.variable.ui_constraints.get(param_name, {})
                if param_name in constraints:
                    slider = QSlider(Qt.Orientation.Horizontal)
                    slider.setMinimum(int(constraints.get("min", 1) * 10))
                    slider.setMaximum(int(constraints.get("max", 100) * 10))
                    slider.setValue(int(default_value * 10))
                    
                    value_label = QLabel(str(default_value))
                    slider.valueChanged.connect(
                        lambda v, lbl=value_label: lbl.setText(str(v/10))
                    )
                    
                    param_layout.addWidget(slider)
                    param_layout.addWidget(value_label)
                    self.config_widgets[param_name] = slider
                else:
                    # 기본 숫자 입력
                    spinbox = QSpinBox()
                    spinbox.setValue(default_value)
                    param_layout.addWidget(spinbox)
                    self.config_widgets[param_name] = spinbox
            else:
                # 기본 숫자 입력
                spinbox = QSpinBox()
                spinbox.setValue(default_value)
                param_layout.addWidget(spinbox)
                self.config_widgets[param_name] = spinbox
            
            layout.addLayout(param_layout)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_config(self) -> Dict[str, Any]:
        """설정된 파라미터 반환"""
        config = {}
        for param_name, widget in self.config_widgets.items():
            if isinstance(widget, QSlider):
                if self.variable.ui_widget_type == "multi_slider":
                    config[param_name] = widget.value() / 10
                else:
                    config[param_name] = widget.value()
            elif isinstance(widget, QSpinBox):
                config[param_name] = widget.value()
        return config

class CustomConditionDialog(QDialog):
    """커스텀 조건 생성 다이얼로그"""
    
    def __init__(self, builder: StrategyBuilder, parent=None):
        super().__init__(parent)
        self.builder = builder
        self.condition_id = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("새 조건 만들기")
        layout = QVBoxLayout()
        
        # 변수 선택
        layout.addWidget(QLabel("변수 선택:"))
        self.variable_combo = QComboBox()
        for var_id, variable in self.builder.variables.items():
            self.variable_combo.addItem(f"{variable.name} ({var_id})", var_id)
        layout.addWidget(self.variable_combo)
        
        # 연산자 선택
        layout.addWidget(QLabel("연산자:"))
        self.operator_combo = QComboBox()
        for op in Operator:
            self.operator_combo.addItem(f"{op.value}", op)
        layout.addWidget(self.operator_combo)
        
        # 비교 대상
        layout.addWidget(QLabel("비교 대상:"))
        self.target_type = QComboBox()
        self.target_type.addItem("고정값", "fixed")
        self.target_type.addItem("다른 변수", "variable")
        self.target_type.currentTextChanged.connect(self.on_target_type_changed)
        layout.addWidget(self.target_type)
        
        # 비교 대상 입력
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("값 입력 (예: 30)")
        layout.addWidget(self.target_input)
        
        self.target_variable_combo = QComboBox()
        for var_id, variable in self.builder.variables.items():
            self.target_variable_combo.addItem(f"{variable.name}", var_id)
        self.target_variable_combo.setVisible(False)
        layout.addWidget(self.target_variable_combo)
        
        # 조건 이름
        layout.addWidget(QLabel("조건 이름 (선택사항):"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("자동 생성됨")
        layout.addWidget(self.name_input)
        
        # 미리보기
        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("background: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.preview_label)
        
        # 실시간 미리보기 업데이트
        self.variable_combo.currentTextChanged.connect(self.update_preview)
        self.operator_combo.currentTextChanged.connect(self.update_preview)
        self.target_input.textChanged.connect(self.update_preview)
        self.target_variable_combo.currentTextChanged.connect(self.update_preview)
        self.name_input.textChanged.connect(self.update_preview)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.create_condition)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.update_preview()
    
    def on_target_type_changed(self):
        """비교 대상 타입 변경 시"""
        is_variable = self.target_type.currentData() == "variable"
        self.target_input.setVisible(not is_variable)
        self.target_variable_combo.setVisible(is_variable)
        self.update_preview()
    
    def update_preview(self):
        """조건 미리보기 업데이트"""
        try:
            var_id = self.variable_combo.currentData()
            if not var_id:
                return
                
            variable = self.builder.variables[var_id]
            operator = self.operator_combo.currentData()
            
            if self.target_type.currentData() == "variable":
                target = self.target_variable_combo.currentData()
                target_display = self.builder.variables[target].name if target else "?"
            else:
                target = self.target_input.text() or "?"
                target_display = target
            
            preview_text = f"📊 {variable.name} {operator.value if operator else '?'} {target_display}"
            
            if self.name_input.text():
                preview_text = f"✏️ {self.name_input.text()}\n{preview_text}"
            
            self.preview_label.setText(preview_text)
            
        except Exception as e:
            self.preview_label.setText(f"미리보기 오류: {e}")
    
    def create_condition(self):
        """조건 생성"""
        try:
            var_id = self.variable_combo.currentData()
            operator = self.operator_combo.currentData()
            
            if self.target_type.currentData() == "variable":
                target = self.target_variable_combo.currentData()
            else:
                target_text = self.target_input.text()
                try:
                    target = float(target_text)
                except ValueError:
                    target = target_text
            
            name = self.name_input.text() if self.name_input.text() else None
            
            self.condition_id = self.builder.create_custom_condition(
                variable_id=var_id,
                operator=operator,
                target=target,
                name=name
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "오류", f"조건 생성 실패: {e}")
    
    def get_condition_id(self) -> Optional[str]:
        return self.condition_id

class RuleCard(QWidget):
    """규칙을 시각적으로 표현하는 카드"""
    
    def __init__(self, rule: Rule, builder: StrategyBuilder):
        super().__init__()
        self.rule = rule
        self.builder = builder
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 규칙 헤더
        header_layout = QHBoxLayout()
        
        # 역할에 따른 색상과 아이콘
        role_colors = {
            RuleRole.ENTRY: "#4CAF50",
            RuleRole.EXIT: "#F44336", 
            RuleRole.SCALE_IN: "#2196F3",
            RuleRole.RISK_FILTER: "#FF9800"
        }
        
        role_icons = {
            RuleRole.ENTRY: "🚀",
            RuleRole.EXIT: "🛑",
            RuleRole.SCALE_IN: "➕",
            RuleRole.RISK_FILTER: "🛡️"
        }
        
        role_label = QLabel(f"{role_icons.get(self.rule.role, '❓')} {self.rule.role.value}")
        role_label.setStyleSheet(f"background: {role_colors.get(self.rule.role, '#666')}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
        header_layout.addWidget(role_label)
        
        header_layout.addStretch()
        
        # 삭제 버튼
        delete_btn = QPushButton("❌")
        delete_btn.setMaximumSize(30, 30)
        delete_btn.clicked.connect(self.delete_rule)
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # 규칙 이름
        name_label = QLabel(self.rule.name)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)
        
        # 조건들
        conditions_layout = QVBoxLayout()
        for i, condition_id in enumerate(self.rule.conditions):
            condition = self.builder.conditions[condition_id]
            
            condition_layout = QHBoxLayout()
            
            # AND/OR 표시 (첫 번째가 아닌 경우)
            if i > 0:
                logic_label = QLabel(f"  {self.rule.logic_combination.value}  ")
                logic_label.setStyleSheet("background: #e0e0e0; padding: 2px 6px; border-radius: 3px; font-weight: bold;")
                condition_layout.addWidget(logic_label)
            
            condition_btn = QPushButton(f"{condition.ui_icon} {condition.name}")
            condition_btn.setStyleSheet("text-align: left; background: #f5f5f5; border: 1px solid #ddd; padding: 6px;")
            condition_btn.setToolTip(condition.description)
            condition_layout.addWidget(condition_btn)
            
            conditions_layout.addLayout(condition_layout)
        
        layout.addLayout(conditions_layout)
        
        # 액션
        action = self.builder.actions[self.rule.action]
        action_btn = QPushButton(f"➡️ {action.ui_icon} {action.name}")
        action_btn.setStyleSheet("background: #e8f5e8; border: 2px solid #4CAF50; padding: 8px; font-weight: bold;")
        action_btn.setToolTip(action.description)
        layout.addWidget(action_btn)
        
        # 카드 스타일
        self.setStyleSheet("""
            RuleCard {
                background: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin: 5px;
                padding: 10px;
            }
            RuleCard:hover {
                border-color: #2196F3;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
        """)
        
        self.setLayout(layout)
    
    def delete_rule(self):
        """규칙 삭제"""
        self.parent().remove_rule_card(self)

class StrategyCanvas(QWidget):
    """전략 캔버스 - 드래그앤드롭으로 규칙과 전략 조합"""
    
    def __init__(self):
        super().__init__()
        self.builder = StrategyBuilder()
        self.rule_cards = []  # RuleCard 객체들
        self.current_strategy_id = None
        self.temp_conditions = []  # 임시 조건 저장
        self.temp_actions = []     # 임시 액션 저장
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 툴바
        toolbar = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ 캔버스 초기화")
        clear_btn.clicked.connect(self.clear_canvas)
        toolbar.addWidget(clear_btn)
        
        # 규칙 생성 버튼 추가
        create_rule_btn = QPushButton("🔧 규칙 만들기")
        create_rule_btn.clicked.connect(self.create_rule_dialog)
        toolbar.addWidget(create_rule_btn)
        
        validate_btn = QPushButton("✅ 전략 검증")
        validate_btn.clicked.connect(self.validate_strategy)
        toolbar.addWidget(validate_btn)
        
        save_btn = QPushButton("💾 전략 저장")
        save_btn.clicked.connect(self.save_strategy)
        toolbar.addWidget(save_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 임시 컴포넌트 영역
        temp_area = QGroupBox("📦 선택된 컴포넌트들")
        temp_layout = QHBoxLayout()
        
        # 조건들
        self.temp_conditions_widget = QWidget()
        self.temp_conditions_layout = QVBoxLayout()
        self.temp_conditions_widget.setLayout(self.temp_conditions_layout)
        temp_layout.addWidget(QLabel("조건:"))
        temp_layout.addWidget(self.temp_conditions_widget)
        
        # 액션들  
        self.temp_actions_widget = QWidget()
        self.temp_actions_layout = QVBoxLayout()
        self.temp_actions_widget.setLayout(self.temp_actions_layout)
        temp_layout.addWidget(QLabel("액션:"))
        temp_layout.addWidget(self.temp_actions_widget)
        
        temp_area.setLayout(temp_layout)
        layout.addWidget(temp_area)
        
        # 스크롤 영역 (규칙 카드들)
        scroll = QScrollArea()
        self.canvas_widget = QWidget()
        self.canvas_layout = QVBoxLayout()
        self.canvas_widget.setLayout(self.canvas_layout)
        scroll.setWidget(self.canvas_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # 상태 표시
        self.status_label = QLabel("전략 캔버스가 비어있습니다")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def add_component(self, component_type: str, component_data: dict):
        """컴포넌트 추가"""
        if component_type == "condition":
            condition = component_data["condition"]
            self.temp_conditions.append(condition)
            self.update_temp_display()
            
        elif component_type == "action":
            action = component_data["action"]
            self.temp_actions.append(action)
            self.update_temp_display()
    
    def update_temp_display(self):
        """임시 컴포넌트 표시 업데이트"""
        # 기존 위젯 제거
        for i in reversed(range(self.temp_conditions_layout.count())):
            item = self.temp_conditions_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        for i in reversed(range(self.temp_actions_layout.count())):
            item = self.temp_actions_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        # 조건들 표시
        for condition in self.temp_conditions:
            btn = QPushButton(f"{condition.ui_icon} {condition.name}")
            btn.setStyleSheet("background: #fff3cd; border: 1px solid #ffeaa7; padding: 4px;")
            btn.setToolTip(condition.description)
            self.temp_conditions_layout.addWidget(btn)
        
        # 액션들 표시
        for action in self.temp_actions:
            btn = QPushButton(f"{action.ui_icon} {action.name}")
            btn.setStyleSheet("background: #d1ecf1; border: 1px solid #bee5eb; padding: 4px;")
            btn.setToolTip(action.description)
            self.temp_actions_layout.addWidget(btn)
    
    def create_rule_dialog(self):
        """규칙 생성 다이얼로그"""
        if not self.temp_conditions or not self.temp_actions:
            QMessageBox.warning(self, "경고", "규칙을 만들려면 최소 1개의 조건과 1개의 액션이 필요합니다")
            return
        
        dialog = RuleCreationDialog(self.temp_conditions, self.temp_actions, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rule_data = dialog.get_rule_data()
            self.create_rule_from_data(rule_data)
    
    def create_rule_from_data(self, rule_data: dict):
        """규칙 데이터로부터 규칙 생성"""
        # 규칙 생성
        condition_ids = [c.id for c in rule_data["conditions"]]
        rule_id = self.builder.create_rule(
            name=rule_data["name"],
            role=rule_data["role"],
            condition_ids=condition_ids,
            logic=rule_data["logic"],
            action_id=rule_data["action"].id
        )
        
        # 규칙 카드 생성
        rule = self.builder.rules[rule_id]
        rule_card = RuleCard(rule, self.builder)
        self.rule_cards.append(rule_card)
        self.canvas_layout.addWidget(rule_card)
        
        # 임시 컴포넌트 초기화
        self.temp_conditions.clear()
        self.temp_actions.clear()
        self.update_temp_display()
        self.update_status()
    
    def remove_rule_card(self, rule_card: RuleCard):
        """규칙 카드 제거"""
        if rule_card in self.rule_cards:
            self.rule_cards.remove(rule_card)
            rule_card.deleteLater()
            self.update_status()
    
    def clear_canvas(self):
        """캔버스 초기화"""
        for rule_card in self.rule_cards:
            rule_card.deleteLater()
        
        self.rule_cards.clear()
        self.temp_conditions.clear()
        self.temp_actions.clear()
        self.current_strategy_id = None
        self.update_temp_display()
        self.update_status()
    
    def validate_strategy(self):
        """전략 검증"""
        if not self.rule_cards:
            QMessageBox.information(self, "정보", "검증할 규칙이 없습니다")
            return
        
        # 임시 전략 생성하여 검증
        rule_ids = [card.rule.id for card in self.rule_cards]
        temp_strategy_id = self.builder.create_strategy(
            "임시 검증 전략", rule_ids, "검증용 임시 전략"
        )
        
        validation = self.builder.validate_strategy(temp_strategy_id)
        
        # 검증 결과 표시
        if validation["is_valid"]:
            msg = "✅ 전략이 유효합니다!\n\n"
            if validation["has_entry"]:
                msg += "• 진입 규칙: 있음\n"
            if validation["has_exit"]:
                msg += "• 청산 규칙: 있음\n"
            
            QMessageBox.information(self, "검증 성공", msg)
        else:
            msg = "❌ 전략에 문제가 있습니다:\n\n"
            for error in validation["errors"]:
                msg += f"• {error}\n"
            
            if validation["warnings"]:
                msg += "\n⚠️ 경고사항:\n"
                for warning in validation["warnings"]:
                    msg += f"• {warning}\n"
            
            QMessageBox.warning(self, "검증 실패", msg)
    
    def save_strategy(self):
        """전략 저장"""
        if not self.rule_cards:
            QMessageBox.information(self, "정보", "저장할 규칙이 없습니다")
            return
        
        # 전략 이름 입력
        name, ok = QInputDialog.getText(self, "전략 저장", "전략 이름:")
        if not ok or not name:
            return
        
        description, ok = QInputDialog.getMultiLineText(
            self, "전략 설명", "전략 설명 (선택사항):"
        )
        if not ok:
            description = ""
        
        # 전략 생성
        rule_ids = [card.rule.id for card in self.rule_cards]
        strategy_id = self.builder.create_strategy(name, rule_ids, description)
        self.current_strategy_id = strategy_id
        
        QMessageBox.information(self, "저장 완료", f"전략 '{name}'이 저장되었습니다")
        self.update_status()
    
    def update_status(self):
        """상태 표시 업데이트"""
        if not self.rule_cards:
            self.status_label.setText("전략 캔버스가 비어있습니다")
        else:
            entry_count = sum(1 for card in self.rule_cards if card.rule.role == RuleRole.ENTRY)
            exit_count = sum(1 for card in self.rule_cards if card.rule.role == RuleRole.EXIT)
            
            status = f"규칙 {len(self.rule_cards)}개 | 진입 {entry_count}개 | 청산 {exit_count}개"
            if self.current_strategy_id:
                strategy = self.builder.strategies[self.current_strategy_id]
                status += f" | 저장됨: {strategy.name}"
            
            self.status_label.setText(status)

class RuleCreationDialog(QDialog):
    """규칙 생성 다이얼로그"""
    
    def __init__(self, conditions: List[Condition], action_list: List[Action], parent=None):
        super().__init__(parent)
        self.conditions = conditions
        self.action_list = action_list
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("새 규칙 만들기")
        layout = QVBoxLayout()
        
        # 규칙 이름
        layout.addWidget(QLabel("규칙 이름:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("예: RSI 과매도 진입 규칙")
        layout.addWidget(self.name_input)
        
        # 역할 선택
        layout.addWidget(QLabel("규칙 역할:"))
        self.role_combo = QComboBox()
        for role in RuleRole:
            self.role_combo.addItem(f"{role.value}", role)
        layout.addWidget(self.role_combo)
        
        # 조건 논리 조합
        if len(self.conditions) > 1:
            layout.addWidget(QLabel("조건 조합 방식:"))
            self.logic_combo = QComboBox()
            self.logic_combo.addItem("AND (모든 조건 만족)", LogicCombination.AND)
            self.logic_combo.addItem("OR (하나라도 만족)", LogicCombination.OR)
            layout.addWidget(self.logic_combo)
        
        # 조건 목록
        layout.addWidget(QLabel("선택된 조건들:"))
        for condition in self.conditions:
            condition_label = QLabel(f"• {condition.ui_icon} {condition.name}")
            condition_label.setStyleSheet("padding: 4px; background: #f0f0f0; border-radius: 4px;")
            layout.addWidget(condition_label)
        
        # 액션 선택
        layout.addWidget(QLabel("실행할 액션:"))
        self.action_combo = QComboBox()
        for action in self.action_list:
            self.action_combo.addItem(f"{action.ui_icon} {action.name}", action)
        layout.addWidget(self.action_combo)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_rule_data(self) -> dict:
        """규칙 데이터 반환"""
        logic = LogicCombination.AND
        if len(self.conditions) > 1:
            logic = self.logic_combo.currentData()
        
        return {
            "name": self.name_input.text() or "새 규칙",
            "role": self.role_combo.currentData(),
            "conditions": self.conditions,
            "logic": logic,
            "action": self.action_combo.currentData()
        }

class AtomicStrategyBuilderUI(QMainWindow):
    """원자적 전략 빌더 메인 UI"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("🧬 원자적 전략 빌더 - 컴포넌트 조합 시스템")
        self.setGeometry(100, 100, 1400, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout()
        
        # 왼쪽: 컴포넌트 팔레트
        palette = ComponentPalette()
        palette.setMaximumWidth(400)
        main_layout.addWidget(palette)
        
        # 오른쪽: 전략 캔버스
        canvas = StrategyCanvas()
        main_layout.addWidget(canvas)
        
        # 팔레트와 캔버스 연결
        palette.componentSelected.connect(canvas.add_component)
        
        central_widget.setLayout(main_layout)
        
        # 상태바
        status_bar = self.statusBar()
        if status_bar:
            status_bar.showMessage("원자적 컴포넌트 조합으로 전략을 만들어보세요")

def main():
    app = QApplication(sys.argv)
    
    # 스타일 설정
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin: 5px 0px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px 16px;
            text-align: left;
        }
        QPushButton:hover {
            background-color: #e3f2fd;
            border-color: #2196f3;
        }
        QPushButton:pressed {
            background-color: #bbdefb;
        }
    """)
    
    window = AtomicStrategyBuilderUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
