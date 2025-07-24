"""
전략 메이커 - 트리거들을 조합하여 완전한 매매 전략 생성
"""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QMessageBox, QTextEdit, QFrame, QListWidget, QListWidgetItem,
    QLineEdit, QSpinBox, QDoubleSpinBox, QTabWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from datetime import datetime

# Common 스타일 시스템 임포트
from upbit_auto_trading.ui.desktop.common.components import (
    PrimaryButton, SecondaryButton, DangerButton,
    StyledLineEdit, StyledComboBox
)
from upbit_auto_trading.ui.desktop.common.styles.style_manager import StyleManager

from .condition_storage import ConditionStorage
from .strategy_storage import StrategyStorage


class StrategyMaker(QWidget):
    """전략 메이커 - 트리거 조합으로 매매 전략 생성"""
    
    # 시그널 정의
    strategy_created = pyqtSignal(dict)  # 전략 생성 완료
    strategy_tested = pyqtSignal(dict, dict)  # 전략, 테스트 결과
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 전략 메이커")
        
        # 스타일 매니저 초기화
        self.style_manager = StyleManager()
        
        # 스토리지 초기화
        self.condition_storage = ConditionStorage()
        self.strategy_storage = StrategyStorage()
        
        # 현재 전략 상태
        self.current_strategy = {
            'name': '',
            'description': '',
            'entry_conditions': [],  # 진입 조건들
            'exit_conditions': [],   # 청산 조건들
            'risk_management': {},   # 리스크 관리 설정
            'position_sizing': {},   # 포지션 사이징
            'created_at': None
        }
        
        self.init_ui()
        self.load_available_triggers()
        
        # 초기 리스트 크기 조정
        QTimer.singleShot(100, self.adjust_list_size)  # UI 생성 후 약간의 지연을 두고 실행
    
    def init_ui(self):
        """UI 초기화 - 3단계 워크플로우"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 메인 워크플로우 영역 (3단계)
        workflow_widget = QWidget()
        workflow_layout = QHBoxLayout(workflow_widget)
        workflow_layout.setContentsMargins(2, 2, 2, 2)
        workflow_layout.setSpacing(5)
        
        # 1단계: 트리거 선택 및 조합 (좌측)
        self.trigger_selection_area = self.create_trigger_selection_area()
        workflow_layout.addWidget(self.trigger_selection_area, 2)
        
        # 2단계: 전략 구성 (중앙)
        self.strategy_composition_area = self.create_strategy_composition_area()
        workflow_layout.addWidget(self.strategy_composition_area, 3)
        
        # 3단계: 리스크 관리 & 검증 (우측)
        self.risk_validation_area = self.create_risk_validation_area()
        workflow_layout.addWidget(self.risk_validation_area, 2)
        
        main_layout.addWidget(workflow_widget)
        
        print("✅ 전략 메이커 UI 초기화 완료")
    
    # def create_header(self, layout):
    #     """상단 헤더 생성"""
    #     header_widget = QWidget()
    #     header_widget.setStyleSheet("""
    #         QWidget {
    #             background-color: #e67e22;
    #             border-radius: 8px;
    #             padding: 10px;
    #             margin: 2px;
    #         }
    #     """)
    #     header_layout = QHBoxLayout(header_widget)
    #     header_layout.setContentsMargins(8, 8, 8, 8)
    #     
    #     # 제목 및 설명
    #     title_label = QLabel("⚙️ 전략 메이커")
    #     title_label.setStyleSheet("""
    #         font-size: 16px;
    #         font-weight: bold;
    #         color: white;
    #         background: transparent;
    #     """)
    #     header_layout.addWidget(title_label)
    #     
    #     subtitle_label = QLabel("트리거 조합 → 매수/매도 전략 → 리스크 관리")
    #     subtitle_label.setStyleSheet("""
    #         font-size: 12px;
    #         color: #f8f9fa;
    #         background: transparent;
    #         margin-left: 20px;
    #     """)
    #     header_layout.addWidget(subtitle_label)
    #     
    #     header_layout.addStretch()
    #     
    #     # 현재 전략 상태
    #     self.strategy_status_label = QLabel("새 전략 생성 중...")
    #     self.strategy_status_label.setStyleSheet("""
    #         background-color: white;
    #         color: #e67e22;
    #         border: 1px solid white;
    #         border-radius: 4px;
    #         padding: 8px 12px;
    #         font-weight: bold;
    #         font-size: 11px;
    #     """)
    #     header_layout.addWidget(self.strategy_status_label)
    #     
    #     layout.addWidget(header_widget)
    
    def create_trigger_selection_area(self):
        """1단계: 트리거 선택 및 조합 영역"""
        group = QGroupBox("① 트리거 선택 & 조합")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 사용 가능한 트리거 리스트
        triggers_label = QLabel("📋 사용 가능한 트리거:")
        layout.addWidget(triggers_label)
        
        # 트리거 검색
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.trigger_search = QLineEdit()
        self.trigger_search.setPlaceholderText("트리거 검색...")
        self.trigger_search.textChanged.connect(self.filter_available_triggers)
        search_layout.addWidget(self.trigger_search)
        layout.addLayout(search_layout)
        
        # 사용 가능한 트리거 리스트
        self.available_triggers_list = QListWidget()
        self.available_triggers_list.itemDoubleClicked.connect(self.add_trigger_to_strategy)
        # 트리거 선택 시 상세 정보 표시
        self.available_triggers_list.itemClicked.connect(self.show_trigger_details)
        layout.addWidget(self.available_triggers_list, 1)  # 스트레치 팩터로 남은 공간을 모두 사용
        
        # 트리거 상세 정보 영역
        details_label = QLabel("📋 트리거 상세 정보:")
        layout.addWidget(details_label)
        
        # 상세 정보 표시 영역
        self.trigger_details_area = QTextEdit()
        self.trigger_details_area.setReadOnly(True)
        self.trigger_details_area.setPlainText("트리거를 선택하면 상세 정보가 표시됩니다.")
        layout.addWidget(self.trigger_details_area, 0)  # 고정 크기로 설정
        
        return group
    
    def create_strategy_composition_area(self):
        """2단계: 전략 구성 영역"""
        group = QGroupBox("② 전략 구성")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 전략 기본 정보
        info_frame = QFrame()
        info_frame.setStyleSheet("QFrame { border: 1px solid black; }")  # 임시 테두리
        info_frame.setFixedHeight(80)  # 높이 고정 (2줄 입력 필드에 적절한 크기)
        info_layout = QGridLayout(info_frame)
        info_layout.setContentsMargins(4, 4, 4, 4)
        info_layout.setSpacing(4)
        
        # 전략명
        name_label = QLabel("전략명:")
        info_layout.addWidget(name_label, 0, 0)
        self.strategy_name_input = StyledLineEdit()
        self.strategy_name_input.setPlaceholderText("예: RSI 골든크로스 전략")
        self.strategy_name_input.textChanged.connect(self.update_strategy_status)
        info_layout.addWidget(self.strategy_name_input, 0, 1)
        
        # 전략 설명
        desc_label = QLabel("설명:")
        info_layout.addWidget(desc_label, 1, 0)
        self.strategy_desc_input = StyledLineEdit()
        self.strategy_desc_input.setPlaceholderText("전략에 대한 간단한 설명")
        info_layout.addWidget(self.strategy_desc_input, 1, 1)
        
        layout.addWidget(info_frame, 0)  # 스트레치 팩터 0으로 고정
        
        # 탭 위젯으로 진입/청산 조건 분리 (크기 제한 적용)
        condition_tabs = QTabWidget()
        condition_tabs.setMaximumHeight(550)  # 탭 전체 높이 제한 (매매량 설정 프레임 크기 2배 증가로 인한 조정)
        condition_tabs.setStyleSheet("QTabWidget { border: 1px solid black; }")  # 임시 테두리
        
        # 매수 조건 탭
        entry_tab = self.create_entry_conditions_tab()
        condition_tabs.addTab(entry_tab, "📈 매수")
        
        # 매도 조건 탭
        exit_tab = self.create_exit_conditions_tab()
        condition_tabs.addTab(exit_tab, "📉 매도")
        
        layout.addWidget(condition_tabs, 0)  # 스트레치 팩터 0으로 설정하여 크기 제한
        
        # 전략 미리보기
        preview_label = QLabel("📋 전략 미리보기:")
        layout.addWidget(preview_label)
        
        self.strategy_preview = QTextEdit()
        self.strategy_preview.setReadOnly(True)
        # 높이 제한 제거하여 남는 공간을 모두 사용하도록 변경
        self.strategy_preview.setPlainText("전략명과 조건을 설정하면 미리보기가 표시됩니다.")
        layout.addWidget(self.strategy_preview, 1)  # 스트레치 팩터 1로 설정하여 확장 가능하게
        
        return group
    
    def create_entry_conditions_tab(self):
        """진입 조건 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)  # 간격을 더 작게 설정
        
        # 조합 방식 설정 (상단에 고정)
        combo_frame = QFrame()
        combo_frame.setFixedHeight(60)  # 높이 고정으로 상단에 붙이기
        combo_layout = QVBoxLayout(combo_frame)
        combo_layout.setContentsMargins(0, 0, 0, 0)
        combo_layout.setSpacing(2)
        
        combination_title = QLabel("🔗 매수 조건 조합 방식")
        combination_title.setStyleSheet("font-weight: bold; margin: 0px; padding: 2px;")
        combo_layout.addWidget(combination_title)
        
        self.entry_logic_combo = StyledComboBox()
        self.entry_logic_combo.addItems(["AND (모든 조건)", "OR (하나라도)", "사용자 정의"])
        combo_layout.addWidget(self.entry_logic_combo)
        
        layout.addWidget(combo_frame, 0)  # 스트레치 팩터 0 (고정 크기)
        
        # 선택된 진입 조건들
        self.entry_conditions_list = QListWidget()
        self.entry_conditions_list.setMinimumHeight(60)  # 최소 높이 설정
        # 최대 높이는 동적으로 조정되므로 초기값만 설정
        self.entry_conditions_list.setMaximumHeight(60)  # 초기값
        # 크기 정책: 수평으로는 확장, 수직으로는 고정된 범위 내에서만 조정
        self.entry_conditions_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # 아이템 추가/제거 시 크기 재조정을 위한 연결
        self.entry_conditions_list.itemSelectionChanged.connect(self.adjust_list_size)
        layout.addWidget(self.entry_conditions_list, 1)  # 스트레치 팩터 1 (확장 가능)
        
        # 진입 조건 버튼들
        entry_buttons = QHBoxLayout()
        entry_buttons.setSpacing(4)
        
        add_entry_btn = PrimaryButton("➕ 조건 추가")
        add_entry_btn.clicked.connect(lambda: self.add_condition_to_strategy('entry'))
        
        remove_entry_btn = DangerButton("➖ 조건 제거")
        remove_entry_btn.clicked.connect(lambda: self.remove_condition_from_strategy('entry'))
        
        entry_buttons.addWidget(add_entry_btn)
        entry_buttons.addWidget(remove_entry_btn)
        entry_buttons.addStretch()
        
        layout.addLayout(entry_buttons, 0)  # 스트레치 팩터 0 (고정 크기)
        
        # 매매량 설정 프레임 추가
        position_frame = self.create_position_sizing_frame('entry')
        layout.addWidget(position_frame, 0)  # 스트레치 팩터 0 (고정 크기)
        
        return widget
    
    def create_exit_conditions_tab(self):
        """청산 조건 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)  # 간격을 더 작게 설정
        
        # 조합 방식 설정 (상단에 고정)
        combo_frame = QFrame()
        combo_frame.setFixedHeight(60)  # 높이 고정으로 상단에 붙이기
        combo_layout = QVBoxLayout(combo_frame)
        combo_layout.setContentsMargins(0, 0, 0, 0)
        combo_layout.setSpacing(2)
        
        combination_title = QLabel("🔗 매도 조건 조합 방식")
        combination_title.setStyleSheet("font-weight: bold; margin: 0px; padding: 2px;")
        combo_layout.addWidget(combination_title)
        
        self.exit_logic_combo = StyledComboBox()
        self.exit_logic_combo.addItems(["AND (모든 조건)", "OR (하나라도)", "사용자 정의"])
        combo_layout.addWidget(self.exit_logic_combo)
        
        layout.addWidget(combo_frame, 0)  # 스트레치 팩터 0 (고정 크기)
        
        # 선택된 청산 조건들
        self.exit_conditions_list = QListWidget()
        self.exit_conditions_list.setMinimumHeight(60)  # 최소 높이 설정
        # 최대 높이는 동적으로 조정되므로 초기값만 설정
        self.exit_conditions_list.setMaximumHeight(60)  # 초기값
        # 크기 정책: 수평으로는 확장, 수직으로는 고정된 범위 내에서만 조정
        self.exit_conditions_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # 아이템 추가/제거 시 크기 재조정을 위한 연결
        self.exit_conditions_list.itemSelectionChanged.connect(self.adjust_list_size)
        layout.addWidget(self.exit_conditions_list, 1)  # 스트레치 팩터 1 (확장 가능)
        
        # 청산 조건 버튼들
        exit_buttons = QHBoxLayout()
        exit_buttons.setSpacing(4)
        
        add_exit_btn = PrimaryButton("➕ 조건 추가")
        add_exit_btn.clicked.connect(lambda: self.add_condition_to_strategy('exit'))
        
        remove_exit_btn = DangerButton("➖ 조건 제거")
        remove_exit_btn.clicked.connect(lambda: self.remove_condition_from_strategy('exit'))
        
        exit_buttons.addWidget(add_exit_btn)
        exit_buttons.addWidget(remove_exit_btn)
        exit_buttons.addStretch()
        
        layout.addLayout(exit_buttons, 0)  # 스트레치 팩터 0 (고정 크기)
        
        # 매매량 설정 프레임 추가
        position_frame = self.create_position_sizing_frame('exit')
        layout.addWidget(position_frame, 0)  # 스트레치 팩터 0 (고정 크기)
        
        return widget
    
    def create_risk_validation_area(self):
        """3단계: 리스크 관리 & 검증 영역"""
        group = QGroupBox("③ 리스크 관리 & 검증")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 리스크 관리 설정
        risk_frame = QFrame()
        risk_layout = QGridLayout(risk_frame)
        risk_layout.setContentsMargins(4, 4, 4, 4)
        risk_layout.setSpacing(3)
        
        # 손절 설정
        stop_label = QLabel("💥 손절률 (%):")
        risk_layout.addWidget(stop_label, 0, 0)
        self.stop_loss_input = QDoubleSpinBox()
        self.stop_loss_input.setRange(0.1, 20.0)
        self.stop_loss_input.setValue(3.0)
        self.stop_loss_input.setSuffix("%")
        risk_layout.addWidget(self.stop_loss_input, 0, 1)
        
        # 익절 설정
        profit_label = QLabel("💰 익절률 (%):")
        risk_layout.addWidget(profit_label, 1, 0)
        self.take_profit_input = QDoubleSpinBox()
        self.take_profit_input.setRange(0.5, 50.0)
        self.take_profit_input.setValue(10.0)
        self.take_profit_input.setSuffix("%")
        risk_layout.addWidget(self.take_profit_input, 1, 1)
        
        # 포지션 사이징
        position_label = QLabel("📊 포지션 크기 (%):")
        risk_layout.addWidget(position_label, 2, 0)
        self.position_size_input = QDoubleSpinBox()
        self.position_size_input.setRange(1.0, 100.0)
        self.position_size_input.setValue(10.0)
        self.position_size_input.setSuffix("%")
        risk_layout.addWidget(self.position_size_input, 2, 1)
        
        # 최대 동시 포지션
        max_label = QLabel("🔄 최대 동시 포지션:")
        risk_layout.addWidget(max_label, 3, 0)
        self.max_positions_input = QSpinBox()
        self.max_positions_input.setRange(1, 10)
        self.max_positions_input.setValue(3)
        risk_layout.addWidget(self.max_positions_input, 3, 1)
        
        layout.addWidget(risk_frame)
        
        # 전략 검증 버튼들
        validation_label = QLabel("🔍 전략 검증:")
        layout.addWidget(validation_label)
        
        # 구문 검증
        syntax_btn = SecondaryButton("✅ 구문 검증")
        syntax_btn.clicked.connect(self.validate_strategy_syntax)
        layout.addWidget(syntax_btn)
        
        # 빠른 시뮬레이션
        simulate_btn = PrimaryButton("🎮 빠른 시뮬레이션")
        simulate_btn.clicked.connect(self.run_quick_simulation)
        layout.addWidget(simulate_btn)
        
        # 히스토리컬 백테스트
        backtest_btn = DangerButton("📊 히스토리컬 백테스트")
        backtest_btn.clicked.connect(self.run_historical_backtest)
        layout.addWidget(backtest_btn)
        
        # 검증 결과
        validation_result_label = QLabel("📋 검증 결과:")
        layout.addWidget(validation_result_label)
        
        self.validation_result = QTextEdit()
        self.validation_result.setReadOnly(True)
        self.validation_result.setPlainText("검증을 실행하면 결과가 표시됩니다.")
        layout.addWidget(self.validation_result)
        
        return group
    
    # def create_action_bar(self, layout):
    #     """하단 액션 바 생성"""
    #     action_widget = QWidget()
    #     action_widget.setStyleSheet("""
    #         QWidget {
    #             background-color: #2c3e50;
    #             border-radius: 8px;
    #             padding: 8px;
    #             margin: 2px;
    #         }
    #     """)
    #     action_layout = QHBoxLayout(action_widget)
    #     action_layout.setContentsMargins(8, 8, 8, 8)
    #     
    #     # 전략 진행 상태
    #     progress_label = QLabel("진행 상태:")
    #     progress_label.setStyleSheet("color: white; font-weight: bold;")
    #     action_layout.addWidget(progress_label)
    #     
    #     self.progress_bar = QProgressBar()
    #     self.progress_bar.setRange(0, 100)
    #     self.progress_bar.setValue(0)
    #     self.progress_bar.setStyleSheet("""
    #         QProgressBar {
    #             border: 2px solid white;
    #             border-radius: 8px;
    #             text-align: center;
    #             background-color: #34495e;
    #         }
    #         QProgressBar::chunk {
    #             background-color: #e67e22;
    #             border-radius: 6px;
    #         }
    #     """)
    #     action_layout.addWidget(self.progress_bar)
    #     
    #     action_layout.addStretch()
    #     
    #     # 주요 액션 버튼들
    #     clear_btn = QPushButton("🗑️ 초기화")
    #     clear_btn.setStyleSheet(self.get_white_button_style())
    #     clear_btn.setMinimumHeight(40)
    #     clear_btn.clicked.connect(self.clear_strategy)
    #     action_layout.addWidget(clear_btn)
    #     
    #     load_btn = QPushButton("📂 불러오기")
    #     load_btn.setStyleSheet(self.get_white_button_style())
    #     load_btn.setMinimumHeight(40)
    #     load_btn.clicked.connect(self.load_strategy)
    #     action_layout.addWidget(load_btn)
    #     
    #     save_btn = QPushButton("💾 저장")
    #     save_btn.setStyleSheet(self.get_white_button_style())
    #     save_btn.setMinimumHeight(40)
    #     save_btn.clicked.connect(self.save_strategy)
    #     action_layout.addWidget(save_btn)
    #     
    #     deploy_btn = QPushButton("🚀 배포")
    #     deploy_btn.setStyleSheet("""
    #         QPushButton {
    #             background-color: #e74c3c;
    #             color: white;
    #             border: 2px solid white;
    #             border-radius: 8px;
    #             padding: 10px 20px;
    #             font-weight: bold;
    #             font-size: 12px;
    #             min-height: 40px;
    #         }
    #         QPushButton:hover {
    #             background-color: #c0392b;
    #         }
    #         QPushButton:pressed {
    #             background-color: #a93226;
    #         }
    #     """)
    #     deploy_btn.clicked.connect(self.deploy_strategy)
    #     action_layout.addWidget(deploy_btn)
    #     
    #     layout.addWidget(action_widget)
    
    def create_position_sizing_frame(self, position_type):
        """매매량 설정 프레임 생성 - Phase 1 구현"""
        frame = QFrame()
        
        # 매수/매도에 따른 색상 구분
        if position_type == 'entry':
            border_color = "#28a745"
            accent_color = "#28a745"
            title = "💰 매수 거래량 설정"
        else:
            border_color = "#dc3545"
            accent_color = "#dc3545"
            title = "💰 매도 거래량 설정"
            
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                margin-top: 2px;
                padding: 6px;
                border: 2px solid black;
            }
        """)
        frame.setFixedHeight(200)  # 고정 높이 설정으로 크기 안정화
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(3)  # 간격을 줄여서 더 컴팩트하게
        
        # 제목 (상단에 고정)
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {accent_color};
                font-weight: bold;
                font-size: 14px;
                margin: 0px;
                padding: 4px;
                border: 1px solid {accent_color};
                background-color: white;
            }}
        """)
        title_label.setFixedHeight(30)  # 제목 높이 고정
        layout.addWidget(title_label)
        
        # 모드 선택 (Phase 1.3)
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(0, 0, 0, 0)
        
        # 모드 선택 버튼들
        if position_type == 'entry':
            self.entry_mode_buttons = {}
            modes = [("고정 금액", "fixed"), ("비율 기반", "ratio"), ("동적 조절", "dynamic")]
        else:
            self.exit_mode_buttons = {}
            modes = [("고정 금액", "fixed"), ("비율 기반", "ratio"), ("동적 조절", "dynamic")]
        
        for mode_text, mode_key in modes:
            btn = SecondaryButton(mode_text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, pt=position_type, mk=mode_key:
                                self.on_position_mode_changed(pt, mk))
            
            if position_type == 'entry':
                self.entry_mode_buttons[mode_key] = btn
            else:
                self.exit_mode_buttons[mode_key] = btn
                
            mode_layout.addWidget(btn)
        
        # 기본값으로 "고정 금액" 선택
        if position_type == 'entry':
            self.entry_mode_buttons["fixed"].setChecked(True)
        else:
            self.exit_mode_buttons["fixed"].setChecked(True)
            
        layout.addLayout(mode_layout)
        
        # 입력 영역 (Phase 1.4, 1.5)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 2, 0, 0)
        
        # 값 입력
        input_label = QLabel("금액:")
        input_label.setStyleSheet("font-size: 11px; margin: 0px; padding: 0px;")
        input_layout.addWidget(input_label)
        
        if position_type == 'entry':
            self.entry_amount_input = QDoubleSpinBox()
            self.entry_amount_input.setRange(1000, 10000000)
            self.entry_amount_input.setValue(50000)
            self.entry_amount_input.setSuffix(" KRW")
            self.entry_amount_input.setStyleSheet("""
                QDoubleSpinBox {
                    border: none;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 11px;
                    max-height: 24px;
                    min-height: 24px;
                    background-color: white;
                }
            """)
            input_layout.addWidget(self.entry_amount_input)
        else:
            self.exit_amount_input = QDoubleSpinBox()
            self.exit_amount_input.setRange(1000, 10000000)
            self.exit_amount_input.setValue(50000)
            self.exit_amount_input.setSuffix(" KRW")
            self.exit_amount_input.setStyleSheet("""
                QDoubleSpinBox {
                    border: none;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 11px;
                    max-height: 24px;
                    min-height: 24px;
                    background-color: white;
                }
            """)
            input_layout.addWidget(self.exit_amount_input)
        
        input_layout.addStretch()
        
        # 고급 설정 버튼 (Phase 1.6)
        advanced_btn = SecondaryButton("🔧 고급 설정")
        advanced_btn.clicked.connect(lambda: self.open_advanced_position_settings(position_type))
        input_layout.addWidget(advanced_btn)
        
        layout.addLayout(input_layout)
        
        # 미리보기 영역 (Phase 1.7)
        preview_label = QLabel("📋 현재 설정:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 4px; font-size: 11px; margin: 0px; padding: 0px;")
        layout.addWidget(preview_label)
        
        if position_type == 'entry':
            self.entry_preview_label = QLabel("고정 금액: 50,000 KRW")
        else:
            self.exit_preview_label = QLabel("고정 금액: 50,000 KRW")
        
        preview_widget = QLabel("고정 금액: 50,000 KRW" if position_type == 'entry' else "고정 금액: 50,000 KRW")
        preview_widget.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
                color: #666;
                max-height: 24px;
                min-height: 24px;
            }}
        """)
        
        if position_type == 'entry':
            self.entry_preview_label = preview_widget
        else:
            self.exit_preview_label = preview_widget
            
        layout.addWidget(preview_widget)
        
        return frame
    
    def on_position_mode_changed(self, position_type, mode):
        """포지션 모드 변경 처리"""
        # 해당 포지션 타입의 다른 버튼들 비활성화
        if position_type == 'entry':
            buttons = self.entry_mode_buttons
            amount_input = self.entry_amount_input
            preview_label = self.entry_preview_label
        else:
            buttons = self.exit_mode_buttons
            amount_input = self.exit_amount_input
            preview_label = self.exit_preview_label
        
        # 다른 버튼들 비활성화
        for btn_key, btn in buttons.items():
            if btn_key != mode:
                btn.setChecked(False)
        
        # 모드에 따른 입력 필드 업데이트
        if mode == "fixed":
            amount_input.setSuffix(" KRW")
            amount_input.setRange(1000, 10000000)
            amount_input.setValue(50000)
            preview_label.setText("고정 금액: 50,000 KRW")
        elif mode == "ratio":
            amount_input.setSuffix(" %")
            amount_input.setRange(0.1, 100.0)
            amount_input.setValue(10.0)
            preview_label.setText("자산의 10% (예상: 약 50,000 KRW)")
        elif mode == "dynamic":
            amount_input.setSuffix(" %")
            amount_input.setRange(1.0, 50.0)
            amount_input.setValue(5.0)
            preview_label.setText("동적 조절: 기본 5% + 변수 연동")
        
        print(f"✅ {position_type} 포지션 모드 변경: {mode}")
    
    def open_advanced_position_settings(self, position_type):
        """고급 포지션 설정 다이얼로그 열기 (Phase 2에서 구현 예정)"""
        QMessageBox.information(self, "고급 설정",
                                f"{position_type} 포지션의 고급 설정은 Phase 2에서 구현됩니다.\n"
                                "현재 Phase 1 - 기본 UI 구현 중입니다.")
        print(f"🔧 {position_type} 고급 설정 요청 (Phase 2에서 구현)")
    
    def check_position_size_conflict(self, strategy_id, new_settings):
        """포지션 사이징 충돌 감지 및 해결 (Phase 1.8)"""
        try:
            # 기존 전략에서 포지션 설정 확인
            existing_strategy = self.strategy_storage.get_strategy(strategy_id) if strategy_id else None
            
            if existing_strategy and 'position_sizing' in existing_strategy:
                existing_settings = existing_strategy['position_sizing']
                
                # 설정이 다른 경우 충돌 감지
                if existing_settings != new_settings:
                    # 사용자에게 충돌 해결 옵션 제공
                    result = self.show_conflict_dialog(existing_settings, new_settings)
                    return result
            
            return True
        except Exception as e:
            print(f"❌ 포지션 충돌 감지 오류: {e}")
            return True
    
    def show_conflict_dialog(self, existing_settings, new_settings):
        """충돌 해결 다이얼로그 표시"""
        from PyQt6.QtWidgets import QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ 포지션 설정 충돌 감지")
        dialog.setFixedSize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        # 메시지
        msg_label = QLabel("이미 전략에 설정된 거래량 설정이 존재합니다.")
        msg_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(msg_label)
        
        # 기존 설정 표시
        existing_label = QLabel(f"기존 설정: {self.format_position_settings(existing_settings)}")
        existing_label.setStyleSheet("color: #dc3545; padding: 8px; border: 1px solid #dc3545; border-radius: 4px;")
        layout.addWidget(existing_label)
        
        # 새 설정 표시
        new_label = QLabel(f"새 설정: {self.format_position_settings(new_settings)}")
        new_label.setStyleSheet("color: #28a745; padding: 8px; border: 1px solid #28a745; border-radius: 4px; margin-top: 10px;")
        layout.addWidget(new_label)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        keep_btn = SecondaryButton("기존 설정 유지")
        
        replace_btn = PrimaryButton("새 설정으로 교체")
        
        cancel_btn = DangerButton("취소")
        
        button_layout.addWidget(keep_btn)
        button_layout.addWidget(replace_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # 클릭 이벤트 처리
        result = None
        
        def on_keep():
            nonlocal result
            result = "keep"
            dialog.accept()
            
        def on_replace():
            nonlocal result
            result = "replace"
            dialog.accept()
            
        def on_cancel():
            nonlocal result
            result = "cancel"
            dialog.reject()
        
        keep_btn.clicked.connect(on_keep)
        replace_btn.clicked.connect(on_replace)
        cancel_btn.clicked.connect(on_cancel)
        
        dialog.exec()
        return result
    
    def format_position_settings(self, settings):
        """포지션 설정을 읽기 쉬운 형태로 포맷"""
        if not settings:
            return "설정 없음"
        
        mode = settings.get('mode', 'fixed')
        value = settings.get('value', 0)
        
        if mode == 'fixed':
            return f"고정 금액: {value:,} KRW"
        elif mode == 'ratio':
            return f"비율 기반: {value}%"
        elif mode == 'dynamic':
            return f"동적 조절: 기본 {value}% + 변수 연동"
        else:
            return f"알 수 없는 모드: {mode}"
    
    def validate_position_priority(self, context="strategy"):
        """포지션 사이징 우선순위 검증 (Phase 1.9)"""
        """
        우선순위 체계:
        1. 포지션 등록 (최우선) > 2. 전략 조합 > 3. 개별 전략 > 4. 시스템 기본값
        """
        priority_levels = {
            "position_registration": 1,  # 포지션 등록
            "strategy_combination": 2,   # 전략 조합  
            "individual_strategy": 3,    # 개별 전략
            "system_default": 4          # 시스템 기본값
        }
        
        current_priority = priority_levels.get(context, 4)
        
        print(f"📊 포지션 우선순위 검증: {context} (레벨 {current_priority})")
        
        # 더 높은 우선순위 설정이 있는지 확인
        if hasattr(self, 'current_position_priority'):
            if self.current_position_priority < current_priority:
                print(f"⚠️ 더 높은 우선순위 설정이 존재합니다 (레벨 {self.current_position_priority})")
                return False
        
        # 현재 우선순위 저장
        self.current_position_priority = current_priority
        return True
    
    def disable_individual_sizing_on_combination(self):
        """전략 조합 시 개별 매매량 설정 비활성화"""
        print("🔄 전략 조합 모드: 개별 전략 매매량 설정 비활성화")
        
        # 개별 전략의 포지션 사이징 비활성화
        if hasattr(self, 'entry_mode_buttons'):
            for btn in self.entry_mode_buttons.values():
                btn.setEnabled(False)
        
        if hasattr(self, 'exit_mode_buttons'):
            for btn in self.exit_mode_buttons.values():
                btn.setEnabled(False)
        
        # 우선순위를 조합 모드로 설정
        self.current_position_priority = 2  # strategy_combination
        
        # 안내 메시지 표시
        QMessageBox.information(self, "전략 조합 모드", 
                               "전략 조합 시 개별 전략의 매매량 설정이 비활성화됩니다.\n"
                               "조합 완성 후 통합 매매량을 설정해주세요.")

    def load_available_triggers(self):
        """사용 가능한 트리거 로드"""
        try:
            conditions = self.condition_storage.get_all_conditions()
            self.available_triggers_list.clear()
            
            for condition in conditions:
                name = condition.get('name', 'Unknown')
                variable = condition.get('variable_name', 'Unknown')
                operator = condition.get('operator', '?')
                target = condition.get('target_value', '?')
                category = condition.get('category', 'unknown')
                
                # 카테고리 아이콘
                category_icons = {
                    "indicator": "📈",
                    "price": "💰", 
                    "capital": "🏦",
                    "state": "📊",
                    "custom": "⚙️",
                    "unknown": "❓"
                }
                icon = category_icons.get(category, "❓")
                
                # 리스트 아이템 생성
                item_text = f"{icon} {name} | {variable} {operator} {target}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, condition)
                self.available_triggers_list.addItem(item)
            
            print(f"✅ {len(conditions)}개 트리거 로드 완료")
            
        except Exception as e:
            print(f"❌ 트리거 로드 실패: {e}")
    
    def filter_available_triggers(self, text):
        """트리거 필터링"""
        search_text = text.lower()
        
        for i in range(self.available_triggers_list.count()):
            item = self.available_triggers_list.item(i)
            if item is not None:  # None 체크 추가
                item_text = item.text().lower()
                item.setHidden(search_text not in item_text)
    
    def show_trigger_details(self, item):
        """선택된 트리거의 상세 정보 표시"""
        try:
            condition_data = item.data(Qt.ItemDataRole.UserRole)
            if not condition_data:
                return
            
            # 상세 정보 구성
            details_text = "🔍 트리거 상세 정보\n"
            details_text += "=" * 30 + "\n\n"
            
            # 기본 정보
            name = condition_data.get('name', 'Unknown')
            details_text += f"📌 이름: {name}\n"
            
            variable = condition_data.get('variable_name', 'Unknown')
            details_text += f"📊 변수: {variable}\n"
            
            operator = condition_data.get('operator', '?')
            target = condition_data.get('target_value', '?')
            details_text += f"🔢 조건: {variable} {operator} {target}\n"
            
            category = condition_data.get('category', 'unknown')
            category_names = {
                "indicator": "기술적 지표",
                "price": "가격 조건", 
                "capital": "자본 관리",
                "state": "상태 확인",
                "custom": "사용자 정의",
                "unknown": "미분류"
            }
            details_text += f"🏷️ 카테고리: {category_names.get(category, category)}\n\n"
            
            # 외부 변수 정보
            external_var = condition_data.get('external_variable')
            if external_var:
                if isinstance(external_var, str):
                    try:
                        external_var = json.loads(external_var)
                    except json.JSONDecodeError:
                        pass
                
                if isinstance(external_var, dict):
                    ext_var_name = external_var.get('variable_name', 'Unknown')
                    ext_var_id = external_var.get('variable_id', 'Unknown')
                    ext_params = external_var.get('parameters') or external_var.get('variable_params')
                    
                    details_text += f"🔗 외부 변수: {ext_var_name} ({ext_var_id})\n"
                    if ext_params:
                        if isinstance(ext_params, dict):
                            param_str = ", ".join([f"{k}={v}" for k, v in ext_params.items()])
                            details_text += f"⚙️ 외부 파라미터: {param_str}\n"
                        else:
                            details_text += f"⚙️ 외부 파라미터: {ext_params}\n"
                else:
                    details_text += f"🔗 외부 변수: {external_var}\n"
                
            # 주 변수 파라미터 정보
            variable_params = condition_data.get('variable_params')
            if variable_params:
                if isinstance(variable_params, str):
                    try:
                        variable_params = json.loads(variable_params)
                    except json.JSONDecodeError:
                        pass
                
                if isinstance(variable_params, dict):
                    param_str = ", ".join([f"{k}={v}" for k, v in variable_params.items()])
                    details_text += f"⚙️ 주 파라미터: {param_str}\n"
                else:
                    details_text += f"⚙️ 주 파라미터: {variable_params}\n"
            
            # 생성 정보
            created_at = condition_data.get('created_at')
            if created_at:
                details_text += f"📅 생성일: {created_at}\n"
            
            # ID 정보
            condition_id = condition_data.get('id')
            if condition_id:
                details_text += f"🆔 ID: {condition_id}\n"
            
            details_text += "\n" + "=" * 30 + "\n"
            details_text += "💡 더블클릭하면 전략에 추가됩니다."
            
            self.trigger_details_area.setPlainText(details_text)
            
        except Exception as e:
            self.trigger_details_area.setPlainText(f"❌ 상세 정보 로드 실패: {e}")
    
    
    def add_trigger_to_strategy(self, item):
        """트리거를 전략에 추가 (더블클릭 시)"""
        # 진입/청산 선택 다이얼로그 표시
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("트리거 추가")
        dialog.setFixedSize(300, 150)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("이 트리거를 어디에 추가하시겠습니까?"))
        
        entry_radio = QRadioButton("📈 진입(매수) 조건")
        exit_radio = QRadioButton("📉 청산(매도) 조건")
        entry_radio.setChecked(True)
        
        layout.addWidget(entry_radio)
        layout.addWidget(exit_radio)
        
        buttons = QHBoxLayout()
        ok_btn = QPushButton("확인")
        cancel_btn = QPushButton("취소")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            condition_data = item.data(Qt.ItemDataRole.UserRole)
            
            if entry_radio.isChecked():
                self.add_condition_to_list(condition_data, 'entry')
            else:
                self.add_condition_to_list(condition_data, 'exit')
            
            self.update_strategy_preview()
            self.update_progress()
    
    def add_condition_to_list(self, condition_data, condition_type):
        """조건을 리스트에 추가"""
        name = condition_data.get('name', 'Unknown')
        variable = condition_data.get('variable_name', 'Unknown')
        operator = condition_data.get('operator', '?')
        target = condition_data.get('target_value', '?')
        
        item_text = f"{name} | {variable} {operator} {target}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, condition_data)
        
        if condition_type == 'entry':
            self.entry_conditions_list.addItem(item)
            self.current_strategy['entry_conditions'].append(condition_data)
        else:
            self.exit_conditions_list.addItem(item)
            self.current_strategy['exit_conditions'].append(condition_data)
    
    def add_condition_to_strategy(self, condition_type):
        """선택된 트리거를 전략에 추가"""
        current_item = self.available_triggers_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "경고", "추가할 트리거를 선택해주세요.")
            return
        
        condition_data = current_item.data(Qt.ItemDataRole.UserRole)
        self.add_condition_to_list(condition_data, condition_type)
        self.update_strategy_preview()
        self.update_progress()
        
        # 리스트 크기 자동 조정
        self.adjust_list_size()
    
    def remove_condition_from_strategy(self, condition_type):
        """선택된 조건을 전략에서 제거"""
        if condition_type == 'entry':
            current_item = self.entry_conditions_list.currentItem()
            list_widget = self.entry_conditions_list
            conditions_list = self.current_strategy['entry_conditions']
        else:
            current_item = self.exit_conditions_list.currentItem()
            list_widget = self.exit_conditions_list
            conditions_list = self.current_strategy['exit_conditions']
        
        if not current_item:
            QMessageBox.warning(self, "경고", "제거할 조건을 선택해주세요.")
            return
        
        # 리스트에서 제거
        row = list_widget.row(current_item)
        list_widget.takeItem(row)
        
        # 전략 데이터에서도 제거
        if row < len(conditions_list):
            conditions_list.pop(row)
        
        self.update_strategy_preview()
        self.update_progress()
        
        # 리스트 크기 자동 조정
        self.adjust_list_size()
    
    def update_strategy_status(self):
        """전략 상태 업데이트"""
        strategy_name = self.strategy_name_input.text().strip()
        if strategy_name:
            # self.strategy_status_label.setText(f"전략: {strategy_name}")
            self.current_strategy['name'] = strategy_name
        else:
            # self.strategy_status_label.setText("새 전략 생성 중...")
            self.current_strategy['name'] = ''
        
        self.update_strategy_preview()
        self.update_progress()
    
    def update_strategy_preview(self):
        """전략 미리보기 업데이트"""
        strategy_name = self.current_strategy.get('name', '무제')
        entry_conditions = self.current_strategy.get('entry_conditions', [])
        exit_conditions = self.current_strategy.get('exit_conditions', [])
        
        preview_text = f"📋 전략: {strategy_name}\n\n"
        
        # 진입 조건들
        if entry_conditions:
            preview_text += "📈 진입(매수) 조건:\n"
            entry_logic = self.entry_logic_combo.currentText()
            preview_text += f"   조합 방식: {entry_logic}\n"
            for i, condition in enumerate(entry_conditions, 1):
                name = condition.get('name', 'Unknown')
                variable = condition.get('variable_name', 'Unknown')
                operator = condition.get('operator', '?')
                target = condition.get('target_value', '?')
                preview_text += f"   {i}. {name}: {variable} {operator} {target}\n"
        else:
            preview_text += "📈 진입 조건: 없음\n"
        
        preview_text += "\n"
        
        # 청산 조건들
        if exit_conditions:
            preview_text += "📉 청산(매도) 조건:\n"
            exit_logic = self.exit_logic_combo.currentText()
            preview_text += f"   조합 방식: {exit_logic}\n"
            for i, condition in enumerate(exit_conditions, 1):
                name = condition.get('name', 'Unknown')
                variable = condition.get('variable_name', 'Unknown')
                operator = condition.get('operator', '?')
                target = condition.get('target_value', '?')
                preview_text += f"   {i}. {name}: {variable} {operator} {target}\n"
        else:
            preview_text += "📉 청산 조건: 없음\n"
        
        # 리스크 관리
        preview_text += f"\n💥 손절률: {self.stop_loss_input.value()}%\n"
        preview_text += f"💰 익절률: {self.take_profit_input.value()}%\n"
        preview_text += f"📊 포지션 크기: {self.position_size_input.value()}%\n"
        preview_text += f"🔄 최대 동시 포지션: {self.max_positions_input.value()}개"
        
        self.strategy_preview.setPlainText(preview_text)
    
    def update_progress(self):
        """진행 상태 업데이트"""
        progress = 0
        
        # 전략명 설정 (20%)
        if self.current_strategy.get('name'):
            progress += 20
        
        # 진입 조건 설정 (30%)
        if self.current_strategy.get('entry_conditions'):
            progress += 30
        
        # 청산 조건 설정 (30%)
        if self.current_strategy.get('exit_conditions'):
            progress += 30
        
        # 리스크 관리 설정 (20%)
        if (self.stop_loss_input.value() > 0 and 
            self.take_profit_input.value() > 0 and 
            self.position_size_input.value() > 0):
            progress += 20
        
        # self.progress_bar.setValue(progress)
    
    def validate_strategy_syntax(self):
        """전략 구문 검증"""
        try:
            result = "✅ 구문 검증 결과:\n\n"
            
            # 기본 정보 검증
            if not self.current_strategy.get('name'):
                result += "❌ 전략명이 필요합니다.\n"
            else:
                result += "✅ 전략명 설정됨\n"
            
            # 진입 조건 검증
            if not self.current_strategy.get('entry_conditions'):
                result += "❌ 진입 조건이 필요합니다.\n"
            else:
                result += f"✅ 진입 조건 {len(self.current_strategy['entry_conditions'])}개 설정됨\n"
            
            # 청산 조건 검증
            if not self.current_strategy.get('exit_conditions'):
                result += "⚠️ 청산 조건이 없습니다 (리스크 관리만 사용)\n"
            else:
                result += f"✅ 청산 조건 {len(self.current_strategy['exit_conditions'])}개 설정됨\n"
            
            # 리스크 관리 검증
            if self.stop_loss_input.value() <= 0:
                result += "⚠️ 손절률이 0입니다.\n"
            else:
                result += f"✅ 손절률: {self.stop_loss_input.value()}%\n"
            
            if self.take_profit_input.value() <= 0:
                result += "⚠️ 익절률이 0입니다.\n"
            else:
                result += f"✅ 익절률: {self.take_profit_input.value()}%\n"
            
            # result += f"\n📊 전체 완성도: {self.progress_bar.value()}%"
            result += f"\n📊 전체 완성도: 진행 중"
            
            self.validation_result.setPlainText(result)
            
        except Exception as e:
            self.validation_result.setPlainText(f"❌ 검증 중 오류 발생: {e}")
    
    def run_quick_simulation(self):
        """빠른 시뮬레이션 실행"""
        # if self.progress_bar.value() < 50:
        #     QMessageBox.warning(self, "경고", "전략이 충분히 설정되지 않았습니다.")
        #     return
        
        try:
            result = "🎮 빠른 시뮬레이션 결과:\n\n"
            result += f"전략: {self.current_strategy.get('name', '무제')}\n"
            result += f"진입 조건: {len(self.current_strategy.get('entry_conditions', []))}개\n"
            result += f"청산 조건: {len(self.current_strategy.get('exit_conditions', []))}개\n\n"
            
            # 가상 시뮬레이션 (실제로는 백테스팅 엔진 연동)
            import random
            trades = random.randint(5, 15)
            win_rate = random.uniform(0.4, 0.8)
            wins = int(trades * win_rate)
            losses = trades - wins
            
            result += f"📊 시뮬레이션 결과 (30일):\n"
            result += f"총 거래: {trades}회\n"
            result += f"승리: {wins}회\n"
            result += f"패배: {losses}회\n"
            result += f"승률: {win_rate*100:.1f}%\n"
            result += f"예상 수익률: {random.uniform(-5, 15):.1f}%\n\n"
            result += "⚠️ 이는 가상 시뮬레이션입니다."
            
            self.validation_result.setPlainText(result)
            
        except Exception as e:
            self.validation_result.setPlainText(f"❌ 시뮬레이션 중 오류 발생: {e}")
    
    def run_historical_backtest(self):
        """히스토리컬 백테스트 실행"""
        # if self.progress_bar.value() < 80:
        #     QMessageBox.warning(self, "경고", "전략이 완전히 설정되지 않았습니다.")
        #     return
        
        QMessageBox.information(self, "백테스트", 
                               "히스토리컬 백테스트가 시작됩니다.\n"
                               "백테스팅 탭으로 이동하여 결과를 확인하세요.")
        
        # TODO: 실제 백테스팅 엔진과 연동
        self.validation_result.setPlainText("📊 히스토리컬 백테스트가 백그라운드에서 실행 중입니다...")
    
    def clear_strategy(self):
        """전략 초기화"""
        reply = QMessageBox.question(self, "초기화", 
                                   "현재 전략을 초기화하시겠습니까?\n저장되지 않은 변경사항은 사라집니다.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_strategy = {
                'name': '',
                'description': '',
                'entry_conditions': [],
                'exit_conditions': [],
                'risk_management': {},
                'position_sizing': {},
                'created_at': None
            }
            
            self.strategy_name_input.clear()
            self.strategy_desc_input.clear()
            self.entry_conditions_list.clear()
            self.exit_conditions_list.clear()
            
            self.stop_loss_input.setValue(3.0)
            self.take_profit_input.setValue(10.0)
            self.position_size_input.setValue(10.0)
            self.max_positions_input.setValue(3)
            
            self.update_strategy_preview()
            self.update_progress()
            
            # self.strategy_status_label.setText("새 전략 생성 중...")
            self.validation_result.setPlainText("전략이 초기화되었습니다.")
    
    def load_strategy(self):
        """기존 전략 불러오기"""
        # TODO: 전략 선택 다이얼로그 구현
        QMessageBox.information(self, "불러오기", "전략 불러오기 기능은 곧 구현됩니다.")
    
    def save_strategy(self):
        """전략 저장"""
        if not self.current_strategy.get('name'):
            QMessageBox.warning(self, "경고", "전략명을 입력해주세요.")
            return
        
        # if self.progress_bar.value() < 50:
        #     QMessageBox.warning(self, "경고", "전략이 충분히 설정되지 않았습니다.")
        #     return
        
        try:
            # 현재 전략 데이터 완성
            self.current_strategy.update({
                'name': self.strategy_name_input.text().strip(),
                'description': self.strategy_desc_input.text().strip(),
                'risk_management': {
                    'stop_loss': self.stop_loss_input.value(),
                    'take_profit': self.take_profit_input.value(),
                    'position_size': self.position_size_input.value(),
                    'max_positions': self.max_positions_input.value()
                },
                'entry_logic': self.entry_logic_combo.currentText(),
                'exit_logic': self.exit_logic_combo.currentText(),
                'created_at': datetime.now().isoformat()
            })
            
            # 데이터베이스에 저장
            strategy_id = self.strategy_storage.save_strategy(self.current_strategy)
            
            QMessageBox.information(self, "저장 완료", 
                                   f"전략 '{self.current_strategy['name']}'이 저장되었습니다.\n"
                                   f"ID: {strategy_id}")
            
            # 시그널 발생
            self.strategy_created.emit(self.current_strategy)
            
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"전략 저장 중 오류가 발생했습니다:\n{e}")
    
    def deploy_strategy(self):
        """전략 배포 (실거래 연동)"""
        # if self.progress_bar.value() < 100:
        #     QMessageBox.warning(self, "경고", "전략이 완전히 설정되지 않았습니다.")
        #     return
        
        reply = QMessageBox.question(self, "배포 확인", 
                                   f"전략 '{self.current_strategy.get('name', '무제')}'을 실거래에 배포하시겠습니까?\n\n"
                                   "⚠️ 실제 자금이 사용됩니다!",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: 실거래 배포 구현
            QMessageBox.information(self, "배포", "전략이 실거래에 배포되었습니다.\n실시간 거래 화면에서 모니터링하세요.")
    
    def adjust_list_size(self):
        """리스트 위젯의 크기를 내용에 맞게 동적으로 조정"""
        try:
            # 진입 조건 리스트 크기 조정
            if hasattr(self, 'entry_conditions_list'):
                item_count = self.entry_conditions_list.count()
                if item_count == 0:
                    new_height = 60  # 최소 높이 (빈 상태)
                else:
                    # 아이템 개수에 따른 높이 계산 (아이템당 25px + 여백 10px)
                    # 최대 5줄까지만 표시, 그 이상은 스크롤
                    display_items = min(item_count, 5)
                    new_height = display_items * 25 + 10
                    new_height = max(new_height, 60)  # 최소 높이 보장
                self.entry_conditions_list.setMaximumHeight(new_height)
                self.entry_conditions_list.setMinimumHeight(new_height)
            
            # 청산 조건 리스트 크기 조정  
            if hasattr(self, 'exit_conditions_list'):
                item_count = self.exit_conditions_list.count()
                if item_count == 0:
                    new_height = 60  # 최소 높이 (빈 상태)
                else:
                    # 아이템 개수에 따른 높이 계산 (아이템당 25px + 여백 10px)
                    # 최대 5줄까지만 표시, 그 이상은 스크롤
                    display_items = min(item_count, 5)
                    new_height = display_items * 25 + 10
                    new_height = max(new_height, 60)  # 최소 높이 보장
                self.exit_conditions_list.setMaximumHeight(new_height)
                self.exit_conditions_list.setMinimumHeight(new_height)
                
            # 레이아웃 업데이트 요청
            self.update()
            
        except Exception as e:
            print(f"❌ 리스트 크기 조정 오류: {e}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    window = StrategyMaker()
    window.show()
    
    sys.exit(app.exec())
