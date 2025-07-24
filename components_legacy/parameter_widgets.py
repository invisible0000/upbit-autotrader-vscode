#!/usr/bin/env python3
"""
파라미터 위젯 팩토리 - UI 위젯 생성 및 관리
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSpinBox, 
    QLineEdit, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt
from typing import Dict, Any, Callable, Optional

class ParameterWidgetFactory:
    """파라미터 위젯 생성 및 관리 팩토리"""
    
    def __init__(self, update_callback: Optional[Callable] = None):
        self.update_callback = update_callback
        self.widgets = {}
    
    def create_parameter_widgets(self, var_id: str, params: Dict[str, Any], 
                                layout: QVBoxLayout) -> Dict[str, QWidget]:
        """변수별 파라미터 위젯 생성"""
        if not params:
            return {}
        
        # 파라미터 라벨 추가
        param_label = QLabel("📋 파라미터:")
        param_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(param_label)
        
        var_widgets = {}
        
        for param_name, param_config in params.items():
            param_row = QHBoxLayout()
            param_row.addWidget(QLabel(f"{param_config['label']}:"))
            
            # 위젯 타입별 생성
            widget = self._create_widget_by_type(param_config)
            param_row.addWidget(widget)
            
            # 도움말 추가
            if 'help' in param_config:
                help_label = QLabel(f"💡 {param_config['help']}")
                help_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
                param_row.addWidget(help_label)
            
            # 위젯을 컨테이너에 추가
            param_widget = QWidget()
            param_widget.setLayout(param_row)
            layout.addWidget(param_widget)
            
            var_widgets[param_name] = widget
        
        self.widgets[var_id] = var_widgets
        return var_widgets
    
    def _create_widget_by_type(self, param_config: Dict[str, Any]) -> QWidget:
        """파라미터 타입별 위젯 생성"""
        param_type = param_config['type']
        
        if param_type == 'int':
            widget = QSpinBox()
            widget.setRange(param_config.get('min', 1), param_config.get('max', 100))
            widget.setValue(param_config.get('default', 14))
            widget.setSuffix(param_config.get('suffix', ''))
            if self.update_callback:
                widget.valueChanged.connect(self.update_callback)
                
        elif param_type == 'float':
            widget = QLineEdit()
            widget.setText(str(param_config.get('default', 1.0)))
            widget.setPlaceholderText(param_config.get('placeholder', ''))
            if self.update_callback:
                widget.textChanged.connect(self.update_callback)
                
        else:  # enum
            widget = QComboBox()
            widget.setStyleSheet(self._get_combobox_style())
            
            for option in param_config.get('options', []):
                widget.addItem(option)
            
            # enum의 기본값 설정
            default_value = param_config.get('default')
            if default_value and default_value in param_config.get('options', []):
                index = param_config['options'].index(default_value)
                widget.setCurrentIndex(index)
            
            if self.update_callback:
                widget.currentTextChanged.connect(self.update_callback)
        
        return widget
    
    def _get_combobox_style(self) -> str:
        """콤보박스 스타일 반환"""
        return """
            QComboBox {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 1px 18px 1px 3px;
                color: black;
                selection-background-color: #3daee9;
            }
            QComboBox:hover {
                border: 1px solid #999;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #ccc;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
                background-color: #f0f0f0;
            }
            QComboBox::down-arrow {
                image: none;
                border: 1px solid black;
                width: 0px;
                height: 0px;
                border-style: solid;
                border-width: 4px 3px 0 3px;
                border-color: #666 transparent transparent transparent;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                selection-background-color: #3daee9;
            }
        """
    
    def create_scrollable_parameter_area(self, min_height: int = 120, 
                                       max_height: int = 200) -> tuple:
        """스크롤 가능한 파라미터 영역 생성"""
        param_scroll = QScrollArea()
        param_scroll.setMinimumHeight(min_height)
        param_scroll.setMaximumHeight(max_height)
        param_scroll.setWidgetResizable(True)
        param_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        param_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        param_widget = QWidget()
        param_layout = QVBoxLayout(param_widget)
        param_scroll.setWidget(param_widget)
        
        return param_scroll, param_layout
    
    def get_parameter_values(self, var_id: str) -> Dict[str, Any]:
        """특정 변수의 파라미터 값들 반환"""
        if var_id not in self.widgets:
            return {}
        
        values = {}
        for param_name, widget in self.widgets[var_id].items():
            if isinstance(widget, QSpinBox):
                values[param_name] = widget.value()
            elif isinstance(widget, QLineEdit):
                values[param_name] = widget.text()
            elif isinstance(widget, QComboBox):
                values[param_name] = widget.currentText()
            else:
                values[param_name] = None
        
        return values
    
    def clear_parameter_widgets(self, layout: QVBoxLayout):
        """파라미터 위젯들 제거"""
        for i in reversed(range(layout.count())):
            child = layout.takeAt(i)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.deleteLater()
    
    def get_all_parameter_values(self) -> Dict[str, Dict[str, Any]]:
        """모든 변수의 파라미터 값들 반환"""
        all_values = {}
        for var_id in self.widgets:
            all_values[var_id] = self.get_parameter_values(var_id)
        return all_values
