"""
전략 파라미터 편집 다이얼로그
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QGroupBox, QScrollArea, QWidget, QTextEdit
)
from PyQt6.QtCore import Qt
from typing import Dict, Any
import json

class ParameterEditorDialog(QDialog):
    """전략 파라미터 편집 다이얼로그"""
    
    # 실제 전략 타입을 UI 전략 타입으로 매핑 (reverse mapping)
    STRATEGY_TYPE_REVERSE_MAPPING = {
        "moving_average_cross": "이동평균 교차",
        "rsi_reversal": "RSI 과매수/과매도", 
        "bollinger_band_mean_reversion": "볼린저 밴드",
        "volatility_breakout": "변동성 돌파",
        "macd_cross": "MACD 교차",
        "stochastic": "스토캐스틱",
        # RSI 기본 타입도 지원
        "rsi": "RSI",
        # 관리 전략들
        "fixed_stop_loss": "고정 손절",
        "trailing_stop": "트레일링 스탑",
        "target_profit": "목표 익절",
        "partial_profit": "부분 익절",
        "time_based_exit": "시간 기반 청산",
        "volatility_based_management": "변동성 기반 관리"
    }
    
    # 파라미터 설명 및 기본값 정의
    PARAMETER_INFO = {
        "이동평균 교차": {
            "short_period": {
                "name": "단기 이동평균 기간",
                "description": "단기 이동평균을 계산할 기간 (일반적으로 5-20)",
                "type": "int",
                "default": 5,
                "min": 2,
                "max": 50
            },
            "long_period": {
                "name": "장기 이동평균 기간", 
                "description": "장기 이동평균을 계산할 기간 (일반적으로 20-200)",
                "type": "int",
                "default": 20,
                "min": 10,
                "max": 500
            },
            "ma_type": {
                "name": "이동평균 유형",
                "description": "이동평균 계산 방식 (SMA: 단순, EMA: 지수)",
                "type": "str",
                "default": "SMA",
                "options": ["SMA", "EMA"]
            }
        },
        "RSI": {
            "period": {
                "name": "RSI 계산 기간",
                "description": "RSI를 계산할 기간 (일반적으로 14)",
                "type": "int", 
                "default": 14,
                "min": 2,
                "max": 100
            },
            "oversold": {
                "name": "과매도 기준선",
                "description": "RSI 과매도 기준 (일반적으로 30)",
                "type": "float",
                "default": 30.0,
                "min": 10.0,
                "max": 50.0
            },
            "overbought": {
                "name": "과매수 기준선",
                "description": "RSI 과매수 기준 (일반적으로 70)",
                "type": "float",
                "default": 70.0,
                "min": 50.0,
                "max": 90.0
            }
        },
        "RSI 과매수/과매도": {
            "period": {
                "name": "RSI 계산 기간",
                "description": "RSI를 계산할 기간 (일반적으로 14)",
                "type": "int", 
                "default": 14,
                "min": 2,
                "max": 100
            },
            "oversold_threshold": {
                "name": "과매도 기준선",
                "description": "RSI 과매도 기준 (일반적으로 30)",
                "type": "float",
                "default": 30.0,
                "min": 10.0,
                "max": 50.0
            },
            "overbought_threshold": {
                "name": "과매수 기준선",
                "description": "RSI 과매수 기준 (일반적으로 70)",
                "type": "float",
                "default": 70.0,
                "min": 50.0,
                "max": 90.0
            }
        },
        "볼린저 밴드": {
            "period": {
                "name": "이동평균 기간",
                "description": "볼린저 밴드 중심선 기간 (일반적으로 20)",
                "type": "int",
                "default": 20,
                "min": 5,
                "max": 100
            },
            "std_dev": {
                "name": "표준편차 배수",
                "description": "밴드 폭을 결정하는 표준편차 배수 (일반적으로 2.0)",
                "type": "float",
                "default": 2.0,
                "min": 0.5,
                "max": 3.0
            }
        },
        "변동성 돌파": {
            "period": {
                "name": "변동성 계산 기간",
                "description": "변동성을 계산할 기간 (일반적으로 20)",
                "type": "int",
                "default": 20,
                "min": 5,
                "max": 100
            },
            "k_value": {
                "name": "돌파 계수 (K)",
                "description": "돌파 기준을 결정하는 계수 (일반적으로 0.5)",
                "type": "float",
                "default": 0.5,
                "min": 0.1,
                "max": 2.0
            }
        },
        "MACD 교차": {
            "fast_period": {
                "name": "빠른 EMA 기간",
                "description": "MACD 빠른 EMA 기간 (일반적으로 12)",
                "type": "int",
                "default": 12,
                "min": 5,
                "max": 50
            },
            "slow_period": {
                "name": "느린 EMA 기간",
                "description": "MACD 느린 EMA 기간 (일반적으로 26)",
                "type": "int",
                "default": 26,
                "min": 10,
                "max": 100
            },
            "signal_period": {
                "name": "시그널 EMA 기간",
                "description": "MACD 시그널 라인 기간 (일반적으로 9)",
                "type": "int",
                "default": 9,
                "min": 3,
                "max": 30
            }
        },
        "스토캐스틱": {
            "k_period": {
                "name": "%K 계산 기간",
                "description": "스토캐스틱 %K 계산 기간 (일반적으로 14)",
                "type": "int",
                "default": 14,
                "min": 5,
                "max": 50
            },
            "d_period": {
                "name": "%D 평활 기간",
                "description": "스토캐스틱 %D 평활 기간 (일반적으로 3)",
                "type": "int",
                "default": 3,
                "min": 1,
                "max": 10
            },
            "oversold": {
                "name": "과매도 기준",
                "description": "스토캐스틱 과매도 기준 (일반적으로 20)",
                "type": "float",
                "default": 20.0,
                "min": 10.0,
                "max": 30.0
            },
            "overbought": {
                "name": "과매수 기준",
                "description": "스토캐스틱 과매수 기준 (일반적으로 80)",
                "type": "float",
                "default": 80.0,
                "min": 70.0,
                "max": 90.0
            }
        },
        # 관리 전략 파라미터들
        "고정 손절": {
            "stop_loss_percent": {
                "name": "손절 비율 (%)",
                "description": "포지션 대비 손실이 이 비율에 도달하면 자동 손절",
                "type": "float",
                "default": 5.0,
                "min": 1.0,
                "max": 20.0
            }
        },
        "트레일링 스탑": {
            "trail_percent": {
                "name": "트레일링 비율 (%)",
                "description": "최고가 대비 하락 비율 (손절선이 따라가는 비율)",
                "type": "float",
                "default": 3.0,
                "min": 1.0,
                "max": 10.0
            },
            "min_profit_percent": {
                "name": "최소 수익 비율 (%)",
                "description": "트레일링 스탑이 작동하기 위한 최소 수익률",
                "type": "float",
                "default": 2.0,
                "min": 0.5,
                "max": 10.0
            }
        },
        "목표 익절": {
            "take_profit_percent": {
                "name": "목표 수익률 (%)",
                "description": "이 수익률에 도달하면 자동으로 익절",
                "type": "float",
                "default": 10.0,
                "min": 2.0,
                "max": 50.0
            }
        },
        "부분 익절": {
            "first_target_percent": {
                "name": "1차 목표 수익률 (%)",
                "description": "첫 번째 부분 익절 목표 수익률",
                "type": "float",
                "default": 5.0,
                "min": 2.0,
                "max": 20.0
            },
            "first_sell_ratio": {
                "name": "1차 매도 비율 (%)",
                "description": "첫 번째 목표 도달 시 매도할 포지션 비율",
                "type": "float",
                "default": 50.0,
                "min": 10.0,
                "max": 90.0
            },
            "second_target_percent": {
                "name": "2차 목표 수익률 (%)",
                "description": "두 번째 부분 익절 목표 수익률",
                "type": "float",
                "default": 10.0,
                "min": 5.0,
                "max": 30.0
            }
        },
        "시간 기반 청산": {
            "max_hold_hours": {
                "name": "최대 보유 시간 (시간)",
                "description": "이 시간이 지나면 자동으로 포지션 청산",
                "type": "int",
                "default": 24,
                "min": 1,
                "max": 168
            }
        },
        "변동성 기반 관리": {
            "volatility_threshold": {
                "name": "변동성 임계값",
                "description": "이 변동성을 초과하면 관리 액션 실행",
                "type": "float",
                "default": 2.0,
                "min": 1.0,
                "max": 5.0
            },
            "action": {
                "name": "관리 액션",
                "description": "변동성 임계값 초과 시 실행할 액션",
                "type": "str",
                "default": "reduce_position",
                "options": ["reduce_position", "close_position", "increase_stop"]
            }
        }
    }
    
    def __init__(self, strategy_type: str, current_parameters: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.strategy_type = strategy_type
        self.current_parameters = current_parameters.copy()
        self.parameter_widgets = {}
        
        self.setWindowTitle(f"{strategy_type} - 파라미터 설정")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        self.init_ui()
        self.load_parameters()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 전략 정보 표시
        info_group = QGroupBox(f"📈 {self.strategy_type}")
        info_layout = QVBoxLayout(info_group)
        
        description = self.get_strategy_description()
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding: 10px; background: #f5f5f5; border-radius: 5px;")
        info_layout.addWidget(desc_label)
        
        layout.addWidget(info_group)
        
        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 파라미터 편집 그룹
        params_group = QGroupBox("⚙️ 파라미터 설정")
        self.params_layout = QFormLayout(params_group)
        
        scroll_layout.addWidget(params_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 버튼 그룹
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("🔄 기본값으로 복원")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        
        self.cancel_button = QPushButton("❌ 취소")
        self.cancel_button.clicked.connect(self.reject)
        
        self.save_button = QPushButton("💾 저장")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setDefault(True)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def get_strategy_description(self) -> str:
        """전략 설명 반환"""
        descriptions = {
            # 진입 전략
            "이동평균 교차": "단기 이동평균이 장기 이동평균을 상향/하향 돌파할 때 매수/매도 신호를 생성합니다.",
            "RSI 과매수/과매도": "RSI 지표가 과매도/과매수 구간에서 벗어날 때 매수/매도 신호를 생성합니다.",
            "볼린저 밴드": "가격이 볼린저 밴드 하단/상단에 터치 후 반전할 때 매수/매도 신호를 생성합니다.",
            "변동성 돌파": "당일 고점이 전일 고점 + (전일 고점-전일 저점) × K를 돌파할 때 매수 신호를 생성합니다.",
            "MACD 교차": "MACD 라인이 시그널 라인을 상향/하향 교차할 때 매수/매도 신호를 생성합니다.",
            "스토캐스틱": "스토캐스틱 %K, %D가 과매도/과매수 구간에서 교차할 때 매수/매도 신호를 생성합니다.",
            # 관리 전략  
            "고정 손절": "포지션 손실이 설정한 비율에 도달하면 자동으로 손절합니다.",
            "트레일링 스탑": "수익이 발생한 상태에서 가격이 하락할 때 손절선을 따라 올려가며 수익을 보호합니다.",
            "목표 익절": "설정한 목표 수익률에 도달하면 자동으로 익절합니다.",
            "부분 익절": "여러 단계의 목표가에서 포지션을 부분적으로 익절하여 리스크를 줄입니다.",
            "시간 기반 청산": "설정한 최대 보유 시간이 지나면 자동으로 포지션을 청산합니다.",
            "변동성 기반 관리": "시장 변동성이 임계값을 초과하면 포지션을 조정하거나 청산합니다."
        }
        return descriptions.get(self.strategy_type, "전략에 대한 설명이 없습니다.")
    
    def create_parameter_widget(self, param_key: str, param_info: Dict[str, Any]) -> QWidget:
        """파라미터 타입에 따른 위젯 생성"""
        param_type = param_info.get("type", "str")
        
        # options가 있는 경우 드롭다운 사용
        if "options" in param_info:
            from PyQt6.QtWidgets import QComboBox
            widget = QComboBox()
            options = param_info["options"]
            widget.addItems(options)
            
            # 현재 값 설정
            current_value = str(self.current_parameters.get(param_key, param_info.get("default", "")))
            if current_value in options:
                widget.setCurrentText(current_value)
            
        elif param_type == "int":
            widget = QSpinBox()
            widget.setMinimum(param_info.get("min", 1))
            widget.setMaximum(param_info.get("max", 1000))
            widget.setValue(self.current_parameters.get(param_key, param_info.get("default", 1)))
            
        elif param_type == "float":
            widget = QDoubleSpinBox()
            widget.setMinimum(param_info.get("min", 0.0))
            widget.setMaximum(param_info.get("max", 100.0))
            widget.setDecimals(2)
            widget.setSingleStep(0.1)
            widget.setValue(self.current_parameters.get(param_key, param_info.get("default", 1.0)))
            
        elif param_type == "bool":
            widget = QCheckBox()
            widget.setChecked(self.current_parameters.get(param_key, param_info.get("default", False)))
            
        else:  # str
            widget = QLineEdit()
            widget.setText(str(self.current_parameters.get(param_key, param_info.get("default", ""))))
        
        return widget
    
    def load_parameters(self):
        """파라미터 위젯 생성 및 로드"""
        # 실제 전략 타입을 UI 전략 타입으로 변환
        ui_strategy_type = self.STRATEGY_TYPE_REVERSE_MAPPING.get(self.strategy_type, self.strategy_type)
        
        if ui_strategy_type not in self.PARAMETER_INFO:
            # 알 수 없는 전략 타입인 경우 JSON 편집기 사용
            print(f"[DEBUG] 알 수 없는 전략 타입: {self.strategy_type} (UI 타입: {ui_strategy_type})")
            print(f"[DEBUG] 사용 가능한 타입들: {list(self.PARAMETER_INFO.keys())}")
            self.create_json_editor()
            return
        
        param_info_dict = self.PARAMETER_INFO[ui_strategy_type]
        
        for param_key, param_info in param_info_dict.items():
            # 라벨 생성 (범위 정보 포함)
            label_text = f"{param_info['name']}:"
            
            # 범위 정보 추가
            param_type = param_info.get("type", "str")
            if param_type in ["int", "float"] and "min" in param_info and "max" in param_info:
                min_val = param_info["min"]
                max_val = param_info["max"]
                label_text += f" ({min_val}~{max_val})"
            elif "options" in param_info:
                options = param_info["options"]
                label_text += f" ({'/'.join(options)})"
            
            # 위젯 생성
            widget = self.create_parameter_widget(param_key, param_info)
            self.parameter_widgets[param_key] = widget
            
            # 설명 라벨 생성
            desc_label = QLabel(param_info.get("description", ""))
            desc_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
            desc_label.setWordWrap(True)
            
            # 폼에 추가
            widget_layout = QVBoxLayout()
            widget_layout.addWidget(widget)
            widget_layout.addWidget(desc_label)
            widget_layout.setContentsMargins(0, 0, 0, 10)
            
            widget_container = QWidget()
            widget_container.setLayout(widget_layout)
            
            self.params_layout.addRow(label_text, widget_container)
    
    def create_json_editor(self):
        """JSON 편집기 생성 (알 수 없는 전략 타입용)"""
        json_text = json.dumps(self.current_parameters, indent=2, ensure_ascii=False)
        
        self.json_editor = QTextEdit()
        self.json_editor.setPlainText(json_text)
        self.json_editor.setMinimumHeight(200)
        
        desc_label = QLabel("⚠️ 이 전략 타입의 파라미터 정의가 없어 JSON 형식으로 편집합니다.")
        desc_label.setStyleSheet("color: #ff6b35; font-weight: bold; padding: 10px;")
        
        self.params_layout.addRow("JSON 파라미터:", QWidget())
        self.params_layout.addRow(desc_label)
        self.params_layout.addRow(self.json_editor)
        
        self.parameter_widgets["__json__"] = self.json_editor
    
    def reset_to_defaults(self):
        """기본값으로 복원"""
        # 실제 전략 타입을 UI 전략 타입으로 변환
        ui_strategy_type = self.STRATEGY_TYPE_REVERSE_MAPPING.get(self.strategy_type, self.strategy_type)
        
        if ui_strategy_type not in self.PARAMETER_INFO:
            return
            
        param_info_dict = self.PARAMETER_INFO[ui_strategy_type]
        
        for param_key, param_info in param_info_dict.items():
            if param_key not in self.parameter_widgets:
                continue
                
            widget = self.parameter_widgets[param_key]
            default_value = param_info.get("default")
            
            if isinstance(widget, QSpinBox):
                widget.setValue(default_value)
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(default_value)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(default_value)
            elif isinstance(widget, QLineEdit):
                widget.setText(str(default_value))
    
    def get_parameters(self) -> Dict[str, Any]:
        """현재 설정된 파라미터 반환"""
        if "__json__" in self.parameter_widgets:
            # JSON 편집기 사용 중
            try:
                json_text = self.parameter_widgets["__json__"].toPlainText()
                return json.loads(json_text)
            except json.JSONDecodeError:
                return self.current_parameters
        
        parameters = {}
        
        if self.strategy_type not in self.PARAMETER_INFO:
            return self.current_parameters
            
        param_info_dict = self.PARAMETER_INFO[self.strategy_type]
        
        for param_key, param_info in param_info_dict.items():
            if param_key not in self.parameter_widgets:
                continue
                
            widget = self.parameter_widgets[param_key]
            
            if isinstance(widget, QSpinBox):
                parameters[param_key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                parameters[param_key] = widget.value()
            elif isinstance(widget, QCheckBox):
                parameters[param_key] = widget.isChecked()
            elif hasattr(widget, 'currentText'):  # QComboBox
                parameters[param_key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                text = widget.text()
                # 타입에 따라 변환
                param_type = param_info.get("type", "str")
                if param_type == "int":
                    try:
                        parameters[param_key] = int(text)
                    except ValueError:
                        parameters[param_key] = param_info.get("default", 1)
                elif param_type == "float":
                    try:
                        parameters[param_key] = float(text)
                    except ValueError:
                        parameters[param_key] = param_info.get("default", 1.0)
                else:
                    parameters[param_key] = text
        
        # 기존 파라미터 중 여기서 다루지 않는 것들은 유지
        for key, value in self.current_parameters.items():
            if key not in parameters:
                parameters[key] = value
        
        return parameters
