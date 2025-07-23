#!/usr/bin/env python3
"""
조건 생성 다이얼로그 v3 (완전 작동 버전)
- 변수별 맞춤 플레이스홀더
- 변수 지원 현황 안내
- 지표별 파라미터 동적 변화
"""

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
    QLabel, QMessageBox, QDialog, QComboBox, QLineEdit, QSpinBox, 
    QTextEdit, QButtonGroup, QRadioButton, QApplication, QScrollArea,
    QCheckBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict

class ConditionDialog(QDialog):
    """조건 생성 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_condition = None
        self.variable_params = {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("🎯 조건 생성기 v3")
        self.setMinimumSize(700, 700)  # 폭과 높이 모두 증가
        layout = QVBoxLayout()
        
        # 1. 변수 선택
        self.create_variable_section(layout)
        
        # 2. 비교 설정
        self.create_comparison_section(layout)
        
        # 2-1. 외부 변수 설정 (골든크로스용)
        self.create_external_variable_section(layout)
        
        # 3. 조건 정보
        self.create_info_section(layout)
        
        # 4. 미리보기
        self.create_preview_section(layout)
        
        # 5. 버튼
        self.create_buttons(layout)
        
        self.setLayout(layout)
        self.connect_events()
        self.update_variables_by_category()
    
    def create_variable_section(self, layout):
        """변수 선택 섹션"""
        group = QGroupBox("📊 1단계: 변수 선택")
        group_layout = QVBoxLayout()
        
        # 범주 + 지원 현황 버튼
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("범주:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("지표", "indicator")
        self.category_combo.addItem("시장가", "price") 
        self.category_combo.addItem("자본", "capital")
        self.category_combo.addItem("상태", "state")
        category_layout.addWidget(self.category_combo)
        
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
        category_layout.addWidget(info_btn)
        group_layout.addLayout(category_layout)
        
        # 변수 선택
        var_layout = QHBoxLayout()
        var_layout.addWidget(QLabel("변수:"))
        self.variable_combo = QComboBox()
        var_layout.addWidget(self.variable_combo)
        
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
        var_layout.addWidget(help_btn)
        
        group_layout.addLayout(var_layout)
        
        # 파라미터 영역 (스크롤 가능)
        param_scroll = QScrollArea()
        param_scroll.setMinimumHeight(120)  # 최소 5줄 높이 확보
        param_scroll.setMaximumHeight(200)  # 최대 높이 제한
        param_scroll.setWidgetResizable(True)
        param_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        param_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.param_widget = QWidget()
        self.param_layout = QVBoxLayout(self.param_widget)
        param_scroll.setWidget(self.param_widget)
        group_layout.addWidget(param_scroll)
        
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
        trend_help = QLabel("� 정적: 단순 비교 | 상승중: 값이 증가 추세 | 하락중: 값이 감소 추세 | 양방향: 변화량 감지")
        trend_help.setStyleSheet("color: #666; font-size: 10px; font-style: italic; margin-top: 5px;")
        trend_help.setWordWrap(True)
        trend_layout.addWidget(trend_help)
        
        group_layout.addLayout(trend_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
    
    def create_external_variable_section(self, layout):
        """외부 변수 설정 섹션 (골든크로스용)"""
        self.external_variable_widget = QGroupBox("🔗 2-1단계: 외부 변수 설정 (골든크로스 등)")
        self.external_variable_widget.setMinimumWidth(650)  # 최소 폭 더 증가
        self.external_variable_widget.setMinimumHeight(150)  # 최소 높이 설정
        group_layout = QVBoxLayout()
        group_layout.setSpacing(10)  # 위젯 간 간격 증가
        
        # 범주 선택
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("범주:"))
        
        self.external_category_combo = QComboBox()
        self.external_category_combo.setMinimumWidth(100)  # 최소 폭 설정
        self.external_category_combo.addItem("지표", "indicator")
        self.external_category_combo.addItem("시장가", "price")
        self.external_category_combo.addItem("자본", "capital")
        self.external_category_combo.addItem("상태", "state")
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
        self.external_variable_combo.setMinimumWidth(150)  # 최소 폭 설정
        var_layout.addWidget(self.external_variable_combo)
        var_layout.addStretch()  # 여백 추가
        group_layout.addLayout(var_layout)
        
        # 외부 변수 파라미터 (스크롤 가능)
        param_scroll = QScrollArea()
        param_scroll.setMinimumHeight(80)  # 최소 높이
        param_scroll.setMaximumHeight(120)  # 최대 높이 제한
        param_scroll.setWidgetResizable(True)
        param_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        param_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        param_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: transparent;
            }
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
        """)
        
        param_container = QWidget()
        param_container.setStyleSheet("background: transparent;")
        self.external_param_layout = QVBoxLayout(param_container)
        self.external_param_layout.setContentsMargins(5, 5, 5, 5)  # 스크롤 내부 여백
        self.external_param_layout.setSpacing(5)
        
        param_scroll.setWidget(param_container)
        group_layout.addWidget(param_scroll)
        
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
    
    def create_buttons(self, layout):
        """버튼 섹션"""
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ 취소")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("💾 저장")
        save_btn.setStyleSheet("""
            background: #28a745; 
            color: white; 
            padding: 8px 16px; 
            font-weight: bold;
            border: none;
            border-radius: 4px;
        """)
        save_btn.clicked.connect(self.save_condition)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
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
        
        if selected_category == "indicator":
            indicators = [
                ("RSI", "RSI 지표"),
                ("SMA", "단순이동평균"),
                ("EMA", "지수이동평균"),
                ("BOLLINGER_BAND", "볼린저밴드"),
                ("MACD", "MACD 지표")
            ]
            for var_id, var_name in indicators:
                self.variable_combo.addItem(f"📈 {var_name}", var_id)
                
        elif selected_category == "price":
            prices = [
                ("CURRENT_PRICE", "현재가"),
                ("OPEN_PRICE", "시가"),
                ("HIGH_PRICE", "고가"),
                ("LOW_PRICE", "저가"),
                ("VOLUME", "거래량")
            ]
            for var_id, var_name in prices:
                self.variable_combo.addItem(f"💰 {var_name}", var_id)
                
        elif selected_category == "capital":
            capitals = [
                ("CASH_BALANCE", "현금 잔고"),
                ("COIN_BALANCE", "코인 보유량"),
                ("TOTAL_BALANCE", "총 자산")
            ]
            for var_id, var_name in capitals:
                self.variable_combo.addItem(f"🏦 {var_name}", var_id)
                
        elif selected_category == "state":
            states = [
                ("PROFIT_PERCENT", "현재 수익률(%)"),
                ("PROFIT_AMOUNT", "현재 수익 금액"),
                ("POSITION_SIZE", "포지션 크기"),
                ("AVG_BUY_PRICE", "평균 매수가")
            ]
            for var_id, var_name in states:
                self.variable_combo.addItem(f"📊 {var_name}", var_id)
    
    def update_variable_params(self):
        """변수별 파라미터 UI 생성"""
        # 기존 위젯 제거
        for i in reversed(range(self.param_layout.count())):
            child = self.param_layout.takeAt(i)
            if child and child.widget():
                child.widget().deleteLater()
        
        var_id = self.variable_combo.currentData()
        if not var_id:
            return
        
        # 변수별 파라미터 정의
        params = self.get_variable_parameters(var_id)
        
        if params:
            param_label = QLabel("📋 파라미터:")
            param_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
            self.param_layout.addWidget(param_label)
            
            self.variable_params[var_id] = {}
            
            for param_name, param_config in params.items():
                param_row = QHBoxLayout()
                param_row.addWidget(QLabel(f"{param_config['label']}:"))
                
                if param_config['type'] == 'int':
                    widget = QSpinBox()
                    widget.setRange(param_config.get('min', 1), param_config.get('max', 100))
                    widget.setValue(param_config.get('default', 14))
                    widget.setSuffix(param_config.get('suffix', ''))
                    widget.valueChanged.connect(self.update_preview)
                elif param_config['type'] == 'float':
                    widget = QLineEdit()
                    widget.setText(str(param_config.get('default', 1.0)))
                    widget.setPlaceholderText(param_config.get('placeholder', ''))
                    widget.textChanged.connect(self.update_preview)
                else:  # enum
                    widget = QComboBox()
                    for option in param_config.get('options', []):
                        widget.addItem(option)
                    
                    # enum의 기본값 설정
                    default_value = param_config.get('default')
                    if default_value and default_value in param_config.get('options', []):
                        index = param_config['options'].index(default_value)
                        widget.setCurrentIndex(index)
                    
                    widget.currentTextChanged.connect(self.update_preview)
                
                param_row.addWidget(widget)
                
                # 도움말
                if 'help' in param_config:
                    help_label = QLabel(f"💡 {param_config['help']}")
                    help_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
                    param_row.addWidget(help_label)
                
                param_widget = QWidget()
                param_widget.setLayout(param_row)
                self.param_layout.addWidget(param_widget)
                self.variable_params[var_id][param_name] = widget
    
    def get_variable_parameters(self, var_id: str) -> Dict:
        """변수별 파라미터 정의"""
        params = {
            "RSI": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "min": 2,
                    "max": 50,
                    "default": 14,
                    "suffix": " 봉",
                    "help": "RSI 계산 기간 (일반적으로 14)"
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간 (전략 기본값 사용 시 무시)"
                }
            },
            "SMA": {
                "period": {
                    "label": "기간", 
                    "type": "int",
                    "min": 1,
                    "max": 240,
                    "default": 20,
                    "suffix": " 봉",
                    "help": "단기: 5,10,20 / 중기: 60,120 / 장기: 200,240"
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간"
                }
            },
            "EMA": {
                "period": {
                    "label": "기간",
                    "type": "int", 
                    "min": 1,
                    "max": 240,
                    "default": 12,
                    "suffix": " 봉",
                    "help": "지수이동평균 계산 기간"
                },
                "exponential_factor": {
                    "label": "지수 계수",
                    "type": "float",
                    "default": 2.0,
                    "placeholder": "2.0",
                    "help": "지수 가중치 (2/(기간+1)이 표준)"
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간"
                }
            },
            "BOLLINGER_BAND": {
                "period": {
                    "label": "기간",
                    "type": "int",
                    "min": 10,
                    "max": 50,
                    "default": 20,
                    "suffix": " 봉",
                    "help": "볼린저밴드 계산 기간 (통상 20)"
                },
                "std_dev": {
                    "label": "표준편차 배수",
                    "type": "float", 
                    "default": 2.0,
                    "placeholder": "2.0",
                    "help": "밴드 폭 (1.0=68%, 2.0=95%, 2.5=99%)"
                },
                "band_position": {
                    "label": "밴드 위치",
                    "type": "enum",
                    "options": ["상단", "중앙선", "하단"],
                    "default": "상단",
                    "help": "비교할 볼린저밴드 위치"
                },
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "봉 단위 시간"
                }
            },
            "MACD": {
                "fast_period": {
                    "label": "빠른선 기간",
                    "type": "int",
                    "min": 5,
                    "max": 30,
                    "default": 12,
                    "suffix": " 봉",
                    "help": "MACD 빠른 이동평균 (12EMA)"
                },
                "slow_period": {
                    "label": "느린선 기간", 
                    "type": "int",
                    "min": 15,
                    "max": 50,
                    "default": 26,
                    "suffix": " 봉",
                    "help": "MACD 느린 이동평균 (26EMA)"
                },
                "signal_period": {
                    "label": "시그널선 기간",
                    "type": "int",
                    "min": 5,
                    "max": 20,
                    "default": 9,
                    "suffix": " 봉",
                    "help": "MACD의 9일 이동평균 (매매신호)"
                },
                "macd_type": {
                    "label": "MACD 종류",
                    "type": "enum",
                    "options": ["MACD선", "시그널선", "히스토그램"],
                    "default": "MACD선",
                    "help": "MACD선: 빠른선-느린선, 시그널선: MACD의 이평, 히스토그램: MACD-시그널"
                }
            },
            "CURRENT_PRICE": {
                "price_type": {
                    "label": "가격 종류",
                    "type": "enum",
                    "options": ["현재가", "매수호가", "매도호가", "중간가"],
                    "default": "현재가",
                    "help": "실시간 거래에서 사용할 가격 기준"
                },
                "backtest_mode": {
                    "label": "백테스팅 모드",
                    "type": "enum",
                    "options": ["실시간(라이브전용)", "종가기준"],
                    "default": "실시간(라이브전용)",
                    "help": "백테스팅 시 해당 타임프레임 종가를 현재가로 사용"
                }
            },
            "PROFIT_PERCENT": {
                "calculation_method": {
                    "label": "계산 방식",
                    "type": "enum",
                    "options": ["미실현", "실현", "전체"],
                    "default": "미실현",
                    "help": "미실현: 현재가 기준, 실현: 매도 완료분, 전체: 포트폴리오 전체"
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "options": ["현재포지션", "전체포지션", "포트폴리오"],
                    "default": "현재포지션",
                    "help": "수익률 계산 범위"
                },
                "include_fees": {
                    "label": "수수료 포함",
                    "type": "enum",
                    "options": ["포함", "제외"],
                    "default": "포함",
                    "help": "거래 수수료 및 슬리피지 포함 여부"
                }
            },
            "OPEN_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "시가 기준 봉 단위 (당일 시작가 등)"
                }
            },
            "HIGH_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "고가 기준 봉 단위"
                }
            },
            "LOW_PRICE": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "저가 기준 봉 단위"
                }
            },
            "VOLUME": {
                "timeframe": {
                    "label": "타임프레임",
                    "type": "enum",
                    "options": ["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"],
                    "default": "포지션 설정 따름",
                    "help": "거래량 기준 봉 단위"
                },
                "volume_type": {
                    "label": "거래량 종류",
                    "type": "enum",
                    "options": ["거래량", "거래대금", "상대거래량"],
                    "default": "거래량",
                    "help": "거래량: 코인수량, 거래대금: 원화금액, 상대거래량: 평균대비 비율"
                }
            },
            "TOTAL_BALANCE": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "options": ["KRW", "USD", "BTC"],
                    "default": "KRW",
                    "help": "총 자산 표시 기준 통화"
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "options": ["포지션제한", "계좌전체"],
                    "default": "포지션제한",
                    "help": "포지션 할당 자본 vs 전체 계좌"
                }
            },
            "CASH_BALANCE": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "options": ["KRW", "USD", "BTC"],
                    "default": "KRW",
                    "help": "현금 잔고 표시 기준 통화"
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "options": ["포지션제한", "계좌전체"],
                    "default": "포지션제한",
                    "help": "포지션 할당 vs 전체 사용가능 현금"
                }
            },
            "COIN_BALANCE": {
                "coin_unit": {
                    "label": "표시 단위",
                    "type": "enum",
                    "options": ["코인수량", "원화가치", "USD가치"],
                    "default": "코인수량",
                    "help": "코인 보유량 표시 방식"
                },
                "scope": {
                    "label": "범위",
                    "type": "enum",
                    "options": ["현재코인", "전체코인"],
                    "default": "현재코인",
                    "help": "현재 거래중인 코인 vs 보유한 모든 코인"
                }
            },
            "PROFIT_AMOUNT": {
                "currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "options": ["KRW", "USD", "BTC"],
                    "default": "KRW",
                    "help": "수익 금액 표시 통화"
                },
                "calculation_method": {
                    "label": "계산 방식",
                    "type": "enum",
                    "options": ["미실현", "실현", "전체"],
                    "default": "미실현",
                    "help": "미실현: 현재가기준, 실현: 매도완료, 전체: 누적"
                },
                "include_fees": {
                    "label": "수수료 포함",
                    "type": "enum",
                    "options": ["포함", "제외"],
                    "default": "포함",
                    "help": "거래 수수료 및 슬리피지 포함 여부"
                }
            },
            "POSITION_SIZE": {
                "unit_type": {
                    "label": "단위 형태",
                    "type": "enum",
                    "options": ["수량", "금액", "비율"],
                    "default": "수량",
                    "help": "수량: 코인개수, 금액: 원화가치, 비율: 포트폴리오대비%"
                }
            },
            "AVG_BUY_PRICE": {
                "display_currency": {
                    "label": "표시 통화",
                    "type": "enum",
                    "options": ["원화", "USD", "코인단위"],
                    "default": "원화",
                    "help": "평균 매수가 표시 통화 (수수료 포함된 평단가)"
                }
            }
        }
        
        return params.get(var_id, {})
    
    def update_variable_description(self):
        """변수 설명 업데이트"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            self.variable_description.setText("변수를 선택하면 설명이 표시됩니다.")
            return
        
        descriptions = {
            "RSI": "RSI(상대강도지수): 0~100 범위의 모멘텀 지표. 70 이상은 과매수, 30 이하는 과매도",
            "SMA": "단순이동평균: 일정 기간의 가격 평균. 추세 방향성 판단에 사용",
            "EMA": "지수이동평균: 최근 가격에 더 큰 가중치. 빠른 신호",
            "BB_UPPER": "볼린저밴드 상단: 저항선 역할. 돌파 시 강한 상승",
            "BB_LOWER": "볼린저밴드 하단: 지지선 역할. 이탈 시 강한 하락",
            "MACD": "MACD: 이동평균 수렴확산. 추세 변화 감지",
            "CURRENT_PRICE": "현재가: 실시간 시장 가격",
            "PROFIT_PERCENT": "현재 수익률: 매수가 대비 수익률(%)"
        }
        
        desc = descriptions.get(var_id, "설명 준비 중...")
        self.variable_description.setText(f"📖 {desc}")
    
    def update_placeholders(self):
        """변수별 플레이스홀더 업데이트"""
        var_id = self.variable_combo.currentData()
        if not var_id:
            return
        
        # 비교값 플레이스홀더
        target_placeholders = {
            "RSI": "예: 70 (과매수), 30 (과매도), 50 (중립)",
            "SMA": "예: 현재가 기준 또는 다른 SMA(골든크로스용)",
            "EMA": "예: 현재가 기준 또는 다른 EMA(크로스용)", 
            "BB_UPPER": "예: 상방돌파>현재가, 상단터치=현재가",
            "BB_LOWER": "예: 하방이탈<현재가, 하단지지=현재가",
            "MACD": "예: 0 (시그널교차), 양수 (상승), 음수 (하락)",
            "CURRENT_PRICE": "예: 50000 (목표가), 비율: 1.05 (5%상승)",
            "PROFIT_PERCENT": "예: 5 (익절), -3 (손절), 10 (목표수익)"
        }
        
        # 조건명 플레이스홀더
        name_placeholders = {
            "RSI": "예: RSI 과매수 신호",
            "SMA": "예: 20일선 돌파",
            "EMA": "예: 12일 지수이평 상승",
            "BB_UPPER": "예: 볼린저 상단 돌파",
            "BB_LOWER": "예: 볼린저 하단 지지",
            "MACD": "예: MACD 골든크로스",
            "CURRENT_PRICE": "예: 목표가 도달",
            "PROFIT_PERCENT": "예: 수익률 5% 달성"
        }
        
        # 설명 플레이스홀더
        desc_placeholders = {
            "RSI": "RSI가 70을 넘어 과매수 구간 진입 시 매도 신호",
            "SMA": "가격이 20일 이동평균선 상향 돌파 시 상승 추세 확인",
            "EMA": "12일 지수이동평균 상승 추세 시 매수 타이밍",
            "BB_UPPER": "볼린저밴드 상단 돌파 시 강한 상승 모멘텀",
            "BB_LOWER": "볼린저밴드 하단 지지 시 반등 기대",
            "MACD": "MACD 골든크로스 시점 포착",
            "CURRENT_PRICE": "목표 가격 도달 시 수익 실현",
            "PROFIT_PERCENT": "목표 수익률 달성 시 포지션 정리"
        }
        
        self.target_input.setPlaceholderText(target_placeholders.get(var_id, "비교값 입력"))
        self.condition_name.setPlaceholderText(name_placeholders.get(var_id, "조건 이름"))
        self.condition_description.setPlaceholderText(desc_placeholders.get(var_id, "조건 설명"))
    
    def update_preview(self):
        """미리보기 업데이트"""
        try:
            var_text = self.variable_combo.currentText()
            if not var_text:
                return
            
            var_id = self.variable_combo.currentData()
            operator = self.operator_combo.currentData()
            condition_name = self.condition_name.text() or "[자동 생성]"
            
            # 비교 대상 설정
            if self.use_external_variable.isChecked():
                external_var_text = self.external_variable_combo.currentText()
                target = external_var_text or "[외부변수]"
                target_type = "🔗 외부변수"
            else:
                target = self.target_input.text() or "[값]"
                target_type = "💰 고정값"
            
            # 파라미터 정보
            param_text = ""
            if var_id in self.variable_params:
                params = []
                for param_name, widget in self.variable_params[var_id].items():
                    if isinstance(widget, QSpinBox):
                        value = widget.value()
                    elif isinstance(widget, QLineEdit):
                        value = widget.text()
                    elif isinstance(widget, QComboBox):
                        value = widget.currentText()
                    else:
                        value = "?"
                    params.append(f"{param_name}={value}")
                
                if params:
                    param_text = f" ({', '.join(params)})"
            
            # 추세 정보
            trend_text = ""
            for button in self.trend_group.buttons():
                if button.isChecked():
                    trend_id = button.property("trend_id")
                    if trend_id != "static":
                        trend_text = f" [{button.text()}]"
                    break
            
            preview_text = f"""
🎯 조건명: {condition_name}

📊 조건식: {var_text}{param_text} {operator} {target}{trend_text}

🔍 비교 유형: {target_type}

📝 해석: "{var_text}"이(가) "{target}"보다 {operator}일 때 신호 발생
            """.strip()
            
            self.preview_label.setText(preview_text)
            
        except Exception as e:
            self.preview_label.setText(f"미리보기 생성 중 오류: {str(e)}")
    
    def save_condition(self):
        """조건 저장"""
        try:
            if not self.variable_combo.currentData():
                QMessageBox.warning(self, "⚠️ 경고", "변수를 선택해주세요.")
                return
            
            if not self.condition_name.text().strip():
                QMessageBox.warning(self, "⚠️ 경고", "조건 이름을 입력해주세요.")
                return
            
            # 외부 변수 사용 시 검증
            if self.use_external_variable.isChecked():
                if not self.external_variable_combo.currentData():
                    QMessageBox.warning(self, "⚠️ 경고", "외부 변수를 선택해주세요.")
                    return
            else:
                if not self.target_input.text().strip():
                    QMessageBox.warning(self, "⚠️ 경고", "비교값을 입력해주세요.")
                    return
            
            var_id = self.variable_combo.currentData()
            
            # 파라미터 수집
            params = {}
            if var_id in self.variable_params:
                for param_name, widget in self.variable_params[var_id].items():
                    if isinstance(widget, QSpinBox):
                        params[param_name] = widget.value()
                    elif isinstance(widget, QLineEdit):
                        params[param_name] = widget.text()
                    elif isinstance(widget, QComboBox):
                        params[param_name] = widget.currentText()
            
            # 추세 방향성
            trend_direction = "static"
            for button in self.trend_group.buttons():
                if button.isChecked():
                    trend_direction = button.property("trend_id")
                    break
            
            # 외부 변수 정보 수집
            external_variable_info = None
            if self.use_external_variable.isChecked():
                external_variable_info = {
                    'variable_id': self.external_variable_combo.currentData(),
                    'variable_name': self.external_variable_combo.currentText(),
                    'category': self.external_category_combo.currentData()
                }
            
            self.current_condition = {
                'name': self.condition_name.text().strip(),
                'description': self.condition_description.toPlainText().strip(),
                'variable_id': var_id,
                'variable_name': self.variable_combo.currentText(),
                'variable_params': params,
                'operator': self.operator_combo.currentData(),
                'target_value': self.target_input.text().strip() if not self.use_external_variable.isChecked() else None,
                'external_variable': external_variable_info,
                'trend_direction': trend_direction,
                'comparison_type': 'external' if self.use_external_variable.isChecked() else 'fixed'
            }
            
            QMessageBox.information(self, "✅ 성공", f"조건 '{self.current_condition['name']}'이 저장되었습니다!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "❌ 오류", f"조건 저장 중 오류:\n{str(e)}")
    
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
• BB_UPPER/LOWER - 볼린저밴드 (변동성)
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
        
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle(f"💡 {self.variable_combo.currentText()} 상세 가이드")
        help_dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # 변수별 상세 도움말
        help_contents = {
            "RSI": """
🎯 RSI (상대강도지수) 완벽 가이드

📊 개념:
• 0~100 범위의 모멘텀 오실레이터
• 과매수/과매도 구간 판단에 활용
• 일정 기간 동안의 상승폭과 하락폭 비율 계산

📈 해석법:
• RSI > 70: 과매수 구간 (매도 신호)
• RSI < 30: 과매도 구간 (매수 신호)  
• RSI = 50: 중립 (상승/하락 균형)

⚙️ 파라미터:
• 기간: 14일이 표준 (단기 9일, 장기 21일)
• 타임프레임: 봉 단위 설정

💡 활용 팁:
• 다이버전스: 가격 신고점이지만 RSI는 하락
• 70/30 돌파보다는 재진입이 더 신뢰성 높음
• 횡보장에서 효과적, 추세장에서는 한계
            """,
            "SMA": """
🎯 SMA (단순이동평균) 완벽 가이드

📊 개념:
• 일정 기간의 가격을 단순 평균한 선
• 추세 방향과 지지/저항 역할
• 가격 노이즈 제거 효과

📈 기간별 특성:
• 단기: 5,10,20일 - 빠른 반응, 잦은 신호
• 중기: 60,120일 - 중기 추세 확인  
• 장기: 200,240일 - 주요 추세선

⚙️ 골든/데드크로스:
• 골든크로스: 단기선이 장기선 상향돌파 (매수)
• 데드크로스: 단기선이 장기선 하향돌파 (매도)
• 예: 20일선이 60일선 돌파

💡 활용 팁:
• 기울기로 추세 강도 판단
• 가격-이평선 거리로 과열 확인
• 여러 이평선 배열로 추세 안정성 체크
            """,
            "EMA": """
🎯 EMA (지수이동평균) 완벽 가이드

📊 개념:
• 최근 가격에 더 큰 가중치를 준 이동평균
• SMA보다 빠른 신호, 민감한 반응
• 지수 계수 = 2/(기간+1)

📈 SMA vs EMA:
• EMA는 최신 데이터 중시
• 추세 변화를 더 빠르게 감지
• 단점: 거짓 신호 증가 가능성

⚙️ 파라미터:
• 지수 계수: 표준 2.0 (커질수록 민감)
• 기간: 12일(단기), 26일(중기) 많이 사용

💡 활용 팁:
• MACD의 기본 구성 요소
• 단기매매에 SMA보다 유리
• 12/26 EMA 조합이 가장 대중적
            """,
            "BB_UPPER": """
🎯 볼린저밴드 완벽 가이드

📊 개념:
• 중심선(20일 SMA) + 상하한선(표준편차)
• 변동성에 따라 밴드 폭이 확대/축소
• 상대적 고가/저가 판단 도구

📈 구성 요소:
• 중심선: 20일 단순이동평균
• 상단선: 중심선 + (2 × 표준편차)
• 하단선: 중심선 - (2 × 표준편차)

⚙️ 파라미터:
• 기간: 20일이 표준
• 표준편차: 2.0 (68%→95% 신뢰구간)
• 1.0=68%, 2.0=95%, 2.5=99%

💡 해석법:
• 상단 터치: 과매수 가능성 (조정 예상)
• 상단 돌파: 강한 상승 모멘텀 (추세 연속)
• 밴드 수축: 변동성 축소 (큰 움직임 예고)
• 밴드 확장: 변동성 증가 (추세 가속)

🎯 전략:
• 밴드 안에서 역방향 매매
• 밴드 돌파 시 추세 추종
            """,
            "MACD": """
🎯 MACD 완벽 가이드

📊 개념:
• Moving Average Convergence Divergence
• 두 이동평균선의 수렴/확산 분석
• 추세 변화의 선행 지표

📈 구성 요소:
• MACD선: 12EMA - 26EMA
• 시그널선: MACD의 9일 이동평균
• 히스토그램: MACD - 시그널

⚙️ 표준 설정:
• 빠른선: 12일 EMA
• 느린선: 26일 EMA  
• 시그널: 9일 EMA

💡 신호 해석:
• 골든크로스: MACD > 시그널 (매수)
• 데드크로스: MACD < 시그널 (매도)
• 제로선 돌파: 추세 전환 확인
• 다이버전스: 가격과 MACD 반대 방향

🎯 히스토그램:
• 양수→음수: 상승 모멘텀 약화
• 음수→양수: 하락 모멘텀 약화
• 크기: 추세 강도 (클수록 강함)
            """
        }
        
        content = help_contents.get(var_id, "이 변수에 대한 상세 가이드를 준비 중입니다.")
        
        help_label = QLabel(content)
        help_label.setStyleSheet("""
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Malgun Gothic';
            line-height: 1.6;
        """)
        help_label.setWordWrap(True)
        
        scroll = QScrollArea()
        scroll.setWidget(help_label)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        close_btn = QPushButton("확인")
        close_btn.clicked.connect(help_dialog.accept)
        layout.addWidget(close_btn)
        
        help_dialog.setLayout(layout)
        help_dialog.exec()
    
    def toggle_comparison_mode(self):
        """비교 모드 전환 (고정값 <-> 외부변수)"""
        is_external = self.use_external_variable.isChecked()
        
        # 외부 변수 섹션 활성화/비활성화
        self.external_variable_widget.setEnabled(is_external)
        
        # 비교값 입력 비활성화/활성화
        self.target_input.setEnabled(not is_external)
        
        if is_external:
            # 외부 변수 사용 시
            self.target_input.setPlaceholderText("외부 변수 사용 중...")
            self.target_input.setStyleSheet("background-color: #f8f9fa; color: #6c757d;")
            self.use_external_variable.setText("🔄 고정값 사용")
            
            # 외부 변수 섹션 활성화 스타일
            self.external_variable_widget.setStyleSheet("QGroupBox { color: #000; }")
            
            # 외부 변수 목록 업데이트
            self.update_external_variables()
        else:
            # 고정값 사용 시
            self.target_input.setStyleSheet("")
            self.use_external_variable.setText("🔄 외부값 사용")
            
            # 외부 변수 섹션 비활성화 스타일
            self.external_variable_widget.setStyleSheet("QGroupBox { color: #999; }")
            
            # placeholder 원상복구
            self.update_placeholders()
        
        # 미리보기 업데이트
        self.update_preview()
    
    def update_external_variables(self):
        """외부 변수 목록 업데이트"""
        self.external_variable_combo.clear()
        
        selected_category = self.external_category_combo.currentData()
        
        if selected_category == "indicator":
            indicators = [
                ("RSI", "RSI 지표"),
                ("SMA", "단순이동평균"),
                ("EMA", "지수이동평균"),
                ("BOLLINGER_BAND", "볼린저밴드"),
                ("MACD", "MACD 지표")
            ]
            for var_id, var_name in indicators:
                self.external_variable_combo.addItem(f"📈 {var_name}", var_id)
                
        elif selected_category == "price":
            prices = [
                ("CURRENT_PRICE", "현재가"),
                ("OPEN_PRICE", "시가"),
                ("HIGH_PRICE", "고가"),
                ("LOW_PRICE", "저가"),
                ("VOLUME", "거래량")
            ]
            for var_id, var_name in prices:
                self.external_variable_combo.addItem(f"💰 {var_name}", var_id)
                
        elif selected_category == "capital":
            capitals = [
                ("CASH_BALANCE", "현금 잔고"),
                ("COIN_BALANCE", "코인 보유량"),
                ("TOTAL_BALANCE", "총 자산")
            ]
            for var_id, var_name in capitals:
                self.external_variable_combo.addItem(f"🏦 {var_name}", var_id)
                
        elif selected_category == "state":
            states = [
                ("PROFIT_PERCENT", "현재 수익률(%)"),
                ("PROFIT_AMOUNT", "현재 수익 금액"),
                ("POSITION_SIZE", "포지션 크기"),
                ("AVG_BUY_PRICE", "평균 매수가")
            ]
            for var_id, var_name in states:
                self.external_variable_combo.addItem(f"📊 {var_name}", var_id)
        
        # 외부 변수 파라미터 업데이트
        self.update_external_variable_params()
    
    def update_external_variable_params(self):
        """외부 변수 파라미터 업데이트"""
        # 기존 파라미터 제거
        for i in reversed(range(self.external_param_layout.count())):
            child = self.external_param_layout.takeAt(i)
            if child and child.widget():
                child.widget().deleteLater()
        
        external_var_id = self.external_variable_combo.currentData()
        if not external_var_id:
            self.external_variable_description.setText("외부 변수를 선택하면 설명이 표시됩니다.")
            return
        
        # 외부 변수 설명 업데이트
        descriptions = {
            "RSI": "RSI 지표 - 골든크로스: RSI > 다른 RSI",
            "SMA": "단순이동평균 - 골든크로스: 단기선 > 장기선",
            "EMA": "지수이동평균 - 크로스 분석용",
            "BOLLINGER_BAND": "볼린저밴드 - 상단/중앙/하단 위치별 비교",
            "MACD": "MACD - 시그널선과 교차 분석",
            "CURRENT_PRICE": "현재가 - 다른 가격/지표와 비교"
        }
        desc = descriptions.get(external_var_id, "외부 변수 설명")
        self.external_variable_description.setText(f"📖 {desc}")
        
        # 모든 파라미터 표시 (1단계와 동일)
        params = self.get_variable_parameters(external_var_id)
        if params:
            param_label = QLabel("📋 파라미터:")
            param_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
            self.external_param_layout.addWidget(param_label)
            
            for param_name, param_config in params.items():
                # 파라미터 행 레이아웃
                param_row = QHBoxLayout()
                
                # 라벨
                label = QLabel(f"{param_config['label']}:")
                label.setMinimumWidth(100)
                param_row.addWidget(label)
                
                # 위젯 타입별 생성
                if param_config['type'] == 'int':
                    widget = QSpinBox()
                    widget.setRange(param_config.get('min', 1), param_config.get('max', 100))
                    widget.setValue(param_config.get('default', 14))
                    widget.setSuffix(param_config.get('suffix', ''))
                elif param_config['type'] == 'float':
                    widget = QLineEdit()
                    widget.setText(str(param_config.get('default', 1.0)))
                    widget.setPlaceholderText(param_config.get('placeholder', ''))
                else:  # enum
                    widget = QComboBox()
                    widget.setStyleSheet("""
                        QComboBox {
                            background-color: white;
                            border: 1px solid #ccc;
                            border-radius: 3px;
                            padding: 1px 18px 1px 3px;
                            color: black;
                            min-width: 100px;
                        }
                    """)
                    for option in param_config.get('options', []):
                        widget.addItem(option)
                    
                    # enum의 기본값 설정
                    default_value = param_config.get('default')
                    if default_value and default_value in param_config.get('options', []):
                        index = param_config['options'].index(default_value)
                        widget.setCurrentIndex(index)
                
                param_row.addWidget(widget)
                
                # 도움말
                if 'help' in param_config:
                    help_label = QLabel(f"💡 {param_config['help']}")
                    help_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
                    param_row.addWidget(help_label)
                
                param_widget = QWidget()
                param_widget.setLayout(param_row)
                self.external_param_layout.addWidget(param_widget)
    
    def get_condition_data(self):
        """생성된 조건 데이터 반환"""
        return self.current_condition

# 실행 코드
if __name__ == "__main__":
    print("🚀 조건 생성기 v3 시작!")
    
    app = QApplication(sys.argv)
    
    print("📊 다이얼로그 생성 중...")
    dialog = ConditionDialog()
    
    print("🎯 다이얼로그 표시!")
    result = dialog.exec()
    
    if result == QDialog.DialogCode.Accepted:
        condition_data = dialog.get_condition_data()
        print("✅ 생성된 조건:", condition_data)
    else:
        print("❌ 조건 생성이 취소되었습니다.")
    
    print("🔚 프로그램 종료!")
