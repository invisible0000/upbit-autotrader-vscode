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
        """변수별 파라미터 위젯 생성 - 반응형"""
        from PyQt6.QtWidgets import QSizePolicy  # QSizePolicy 임포트 추가
        
        if not params:
            # 컨텍스트 기반 상태 메시지 생성
            status_info = self._get_parameter_status_info(var_id)
            info_label = QLabel(status_info['message'])
            info_label.setStyleSheet(f"""
                QLabel {{
                    color: {status_info['color']};
                    font-style: italic;
                    background-color: {status_info['bg_color']};
                    border: 1px solid {status_info['border_color']};
                    border-radius: 4px;
                    padding: 10px;
                    margin-top: 8px;
                    text-align: center;
                    font-weight: {status_info['font_weight']};
                }}
            """)
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info_label)
            return {}
        
        # 파라미터 라벨 추가
        param_label = QLabel("📋 파라미터:")
        param_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(param_label)
        
        var_widgets = {}
        
        for param_name, param_config in params.items():
            param_row = QHBoxLayout()
            
            # 라벨 추가
            label = QLabel(f"{param_config['label']}:")
            label.setMinimumWidth(80)  # 라벨 최소 폭 설정
            param_row.addWidget(label)
            
            # 위젯 타입별 생성
            widget = self._create_widget_by_type(param_config)
            widget.setMinimumWidth(100)  # 입력 위젯 최소 폭 설정
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)  # 확장 가능
            param_row.addWidget(widget, 1)  # 스트레치 팩터 1
            
            # 범위 표시 추가 (콤팩트하게)
            range_label = self._create_range_label(param_config)
            if range_label:
                param_row.addWidget(range_label)
            
            # 도움말 추가
            if 'help' in param_config:
                help_label = QLabel(f"💡 {param_config['help']}")
                help_label.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
                help_label.setWordWrap(True)
                param_row.addWidget(help_label)
            
            # 여백 추가
            param_row.addStretch()
            
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
        
        if param_type == 'integer':
            widget = QSpinBox()
            min_val = int(param_config.get('min', 1))
            max_val = int(param_config.get('max', 100))
            default_val = int(param_config.get('default', 14))
            
            widget.setRange(min_val, max_val)
            widget.setValue(default_val)
            widget.setSuffix(param_config.get('suffix', ''))
            
            widget.setStyleSheet("""
                QSpinBox {
                    padding: 3px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                }
                QSpinBox::up-button {
                    subcontrol-origin: border;
                    subcontrol-position: top right;
                    width: 16px;
                    border-left: 1px solid #ddd;
                    border-bottom: 1px solid #ddd;
                    border-top-right-radius: 3px;
                    background-color: #f8f9fa;
                }
                QSpinBox::up-button:hover {
                    background-color: #e9ecef;
                }
                QSpinBox::up-arrow {
                    image: none;
                    border-left: 3px solid transparent;
                    border-right: 3px solid transparent;
                    border-bottom: 5px solid #495057;
                    margin: 0px;
                }
                QSpinBox::down-button {
                    subcontrol-origin: border;
                    subcontrol-position: bottom right;
                    width: 16px;
                    border-left: 1px solid #ddd;
                    border-top: 1px solid #ddd;
                    border-bottom-right-radius: 3px;
                    background-color: #f8f9fa;
                }
                QSpinBox::down-button:hover {
                    background-color: #e9ecef;
                }
                QSpinBox::down-arrow {
                    image: none;
                    border-left: 3px solid transparent;
                    border-right: 3px solid transparent;
                    border-top: 5px solid #495057;
                    margin: 0px;
                }
            """)
            
            if self.update_callback:
                widget.valueChanged.connect(self.update_callback)
                
        elif param_type == 'float':
            widget = QLineEdit()
            widget.setText(str(param_config.get('default', 1.0)))
            widget.setPlaceholderText(str(param_config.get('placeholder', '')))
            
            # float 검증 함수 연결
            widget.textChanged.connect(lambda text, w=widget, config=param_config: self._validate_float_input(text, w, config))
            
            if self.update_callback:
                widget.textChanged.connect(self.update_callback)
                
        else:  # enum
            widget = QComboBox()
            # 하드코딩된 스타일 제거 - QSS 테마를 따름
            
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
    
    def _create_range_label(self, param_config: Dict[str, Any]) -> Optional[QLabel]:
        """파라미터 범위 표시 라벨 생성 (콤팩트)"""
        param_type = param_config['type']
        
        if param_type == 'int':
            min_val = param_config.get('min', 1)
            max_val = param_config.get('max', 100)
            range_text = f"({min_val}-{max_val})"
            
        elif param_type == 'float':
            min_val = param_config.get('min')
            max_val = param_config.get('max')
            if min_val is not None and max_val is not None:
                range_text = f"({min_val}-{max_val})"
            else:
                return None  # float는 범위가 명시되지 않으면 표시하지 않음
                
        else:  # enum
            options = param_config.get('options', [])
            if options:
                if len(options) <= 3:
                    range_text = f"({'/'.join(options)})"
                else:
                    range_text = f"({len(options)}개 선택)"
            else:
                return None
        
        # 범위 라벨 생성
        range_label = QLabel(range_text)
        range_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 9px;
                font-weight: normal;
                padding: 2px 4px;
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 3px;
                margin-left: 2px;
            }
        """)
        range_label.setMaximumWidth(80)  # 최대 폭 제한
        
        return range_label
    
    def _validate_float_input(self, text: str, widget: QLineEdit, param_config: Dict[str, Any]):
        """float 입력 유효성 검증"""
        if not text.strip():
            # 빈 값은 기본 스타일
            widget.setStyleSheet("")
            return
        
        try:
            value = float(text)
            min_val = param_config.get('min')
            max_val = param_config.get('max')
            
            # 범위 검증
            is_valid = True
            if min_val is not None and value < min_val:
                is_valid = False
            if max_val is not None and value > max_val:
                is_valid = False
            
            if is_valid:
                # 유효한 값 - 정상 스타일
                widget.setStyleSheet("""
                    QLineEdit {
                        border: 1px solid #28a745;
                        background-color: #f8fff8;
                    }
                """)
            else:
                # 범위 밖 값 - 경고 스타일
                widget.setStyleSheet("""
                    QLineEdit {
                        border: 1px solid #dc3545;
                        background-color: #fff5f5;
                        color: #dc3545;
                    }
                """)
                
        except ValueError:
            # 잘못된 형식 - 오류 스타일
            widget.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #dc3545;
                    background-color: #fff5f5;
                    color: #dc3545;
                }
            """)
    
    def create_scrollable_parameter_area(self, min_height: int = 120, 
                                       max_height: int = 300) -> tuple:  # 최대 높이 증가 (200→300)
        """스크롤 가능한 파라미터 영역 생성 - 반응형"""
        from PyQt6.QtWidgets import QSizePolicy  # QSizePolicy 임포트 추가
        
        param_scroll = QScrollArea()
        param_scroll.setMinimumHeight(min_height)
        param_scroll.setMaximumHeight(max_height)
        param_scroll.setWidgetResizable(True)
        param_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        param_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 확장 가능하도록 설정
        param_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        param_widget = QWidget()
        param_layout = QVBoxLayout(param_widget)
        param_layout.setContentsMargins(4, 4, 4, 4)  # 마진 설정
        param_layout.setSpacing(2)  # 간격 설정
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
    
    def set_parameter_values(self, var_id: str, values: Dict[str, Any]):
        """특정 변수의 파라미터 값들 설정"""
        if var_id not in self.widgets or not values:
            return
        
        for param_name, value in values.items():
            if param_name in self.widgets[var_id]:
                widget = self.widgets[var_id][param_name]
                
                if isinstance(widget, QSpinBox):
                    if isinstance(value, (int, float)):
                        widget.setValue(int(value))
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    # 콤보박스에서 값 찾아서 설정
                    for i in range(widget.count()):
                        if widget.itemText(i) == str(value):
                            widget.setCurrentIndex(i)
                            break
    
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
    
    def _get_parameter_status_info(self, var_id: str) -> Dict[str, str]:
        """변수의 파라미터 상태 정보 반환 (UI 표시용)"""
        from .variable_definitions import VariableDefinitions
        
        try:
            return VariableDefinitions.get_parameter_status_info(var_id)
        except Exception as e:
            # 폴백: DB 접근 실패 시 기본 에러 메시지
            return {
                'message': f'⚠️ 파라미터 정보를 불러올 수 없습니다: {str(e)}',
                'color': '#d32f2f',
                'bg_color': '#ffebee',
                'border_color': '#f44336',
                'font_weight': 'bold',
                'status_type': 'error_db_access'
            }
