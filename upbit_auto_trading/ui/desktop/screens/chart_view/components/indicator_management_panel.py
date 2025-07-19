"""
지표 관리 패널 컴포넌트
- 활성 지표 목록 표시
- 지표 추가/제거
- 지표 설정 변경
- 지표 가시성 토글
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QCheckBox, QScrollArea, QFrame, QLineEdit,
    QSpinBox, QDoubleSpinBox, QFormLayout, QDialog, QDialogButtonBox,
    QComboBox, QColorDialog, QSlider, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor

class IndicatorConfigDialog(QDialog):
    """지표 설정 대화상자"""
    
    def __init__(self, indicator_type, parent=None):
        super().__init__(parent)
        self.indicator_type = indicator_type
        self.setWindowTitle(f"{indicator_type} 설정")
        self.setModal(True)
        self.resize(400, 300)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 설정 폼
        form_group = QGroupBox(f"{self.indicator_type} 파라미터")
        form_layout = QFormLayout(form_group)
        
        # 지표별 파라미터 설정
        if self.indicator_type == "이동평균 (SMA)":
            self.setup_sma_params(form_layout)
        elif self.indicator_type == "지수이동평균 (EMA)":
            self.setup_ema_params(form_layout)
        elif self.indicator_type == "볼린저밴드 (BBANDS)":
            self.setup_bollinger_params(form_layout)
        elif self.indicator_type == "RSI":
            self.setup_rsi_params(form_layout)
        elif self.indicator_type == "MACD":
            self.setup_macd_params(form_layout)
        elif self.indicator_type == "스토캐스틱":
            self.setup_stochastic_params(form_layout)
        
        layout.addWidget(form_group)
        
        # 색상 설정
        color_group = QGroupBox("색상 설정")
        color_layout = QVBoxLayout(color_group)
        
        color_button_layout = QHBoxLayout()
        self.color_btn = QPushButton("색상 선택")
        self.color_btn.setFixedHeight(30)
        self.color_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.color_btn.clicked.connect(self.select_color)
        self.selected_color = QColor("#2196F3")
        
        color_button_layout.addWidget(QLabel("지표 색상:"))
        color_button_layout.addWidget(self.color_btn)
        color_button_layout.addStretch()
        
        color_layout.addLayout(color_button_layout)
        layout.addWidget(color_group)
        
        # 미리보기 (향후 확장 가능)
        preview_group = QGroupBox("미리보기")
        preview_layout = QVBoxLayout(preview_group)
        preview_label = QLabel("지표 미리보기는 추후 구현 예정입니다.")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_label)
        layout.addWidget(preview_group)
        
        # 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def setup_sma_params(self, layout):
        """SMA 파라미터 설정"""
        self.sma_period = QSpinBox()
        self.sma_period.setRange(1, 500)
        self.sma_period.setValue(20)
        layout.addRow("기간:", self.sma_period)
    
    def setup_ema_params(self, layout):
        """EMA 파라미터 설정"""
        self.ema_period = QSpinBox()
        self.ema_period.setRange(1, 500)
        self.ema_period.setValue(20)
        layout.addRow("기간:", self.ema_period)
    
    def setup_bollinger_params(self, layout):
        """볼린저 밴드 파라미터 설정"""
        self.bb_period = QSpinBox()
        self.bb_period.setRange(1, 200)
        self.bb_period.setValue(20)
        layout.addRow("기간:", self.bb_period)
        
        self.bb_std = QDoubleSpinBox()
        self.bb_std.setRange(0.1, 5.0)
        self.bb_std.setValue(2.0)
        self.bb_std.setSingleStep(0.1)
        layout.addRow("표준편차 배수:", self.bb_std)
    
    def setup_rsi_params(self, layout):
        """RSI 파라미터 설정"""
        self.rsi_period = QSpinBox()
        self.rsi_period.setRange(2, 100)
        self.rsi_period.setValue(14)
        layout.addRow("기간:", self.rsi_period)
        
        self.rsi_overbought = QSpinBox()
        self.rsi_overbought.setRange(50, 100)
        self.rsi_overbought.setValue(70)
        layout.addRow("과매수 기준:", self.rsi_overbought)
        
        self.rsi_oversold = QSpinBox()
        self.rsi_oversold.setRange(0, 50)
        self.rsi_oversold.setValue(30)
        layout.addRow("과매도 기준:", self.rsi_oversold)
    
    def setup_macd_params(self, layout):
        """MACD 파라미터 설정"""
        self.macd_fast = QSpinBox()
        self.macd_fast.setRange(1, 100)
        self.macd_fast.setValue(12)
        layout.addRow("빠른 기간:", self.macd_fast)
        
        self.macd_slow = QSpinBox()
        self.macd_slow.setRange(1, 200)
        self.macd_slow.setValue(26)
        layout.addRow("느린 기간:", self.macd_slow)
        
        self.macd_signal = QSpinBox()
        self.macd_signal.setRange(1, 50)
        self.macd_signal.setValue(9)
        layout.addRow("시그널 기간:", self.macd_signal)
    
    def setup_stochastic_params(self, layout):
        """스토캐스틱 파라미터 설정"""
        self.stoch_k = QSpinBox()
        self.stoch_k.setRange(1, 100)
        self.stoch_k.setValue(14)
        layout.addRow("%K 기간:", self.stoch_k)
        
        self.stoch_d = QSpinBox()
        self.stoch_d.setRange(1, 50)
        self.stoch_d.setValue(3)
        layout.addRow("%D 기간:", self.stoch_d)
        
        self.stoch_smooth = QSpinBox()
        self.stoch_smooth.setRange(1, 10)
        self.stoch_smooth.setValue(3)
        layout.addRow("평활화:", self.stoch_smooth)
    
    def select_color(self):
        """색상 선택"""
        color = QColorDialog.getColor(self.selected_color, self)
        if color.isValid():
            self.selected_color = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; color: white;")
    
    def get_params(self):
        """파라미터 반환"""
        params = {"color": self.selected_color.name()}
        
        if self.indicator_type == "이동평균 (SMA)":
            params.update({"type": "SMA", "period": self.sma_period.value()})
        elif self.indicator_type == "지수이동평균 (EMA)":
            params.update({"type": "EMA", "period": self.ema_period.value()})
        elif self.indicator_type == "볼린저밴드 (BBANDS)":
            params.update({
                "type": "BBANDS",
                "period": self.bb_period.value(),
                "std": self.bb_std.value()
            })
        elif self.indicator_type == "RSI":
            params.update({
                "type": "RSI",
                "period": self.rsi_period.value(),
                "overbought": self.rsi_overbought.value(),
                "oversold": self.rsi_oversold.value()
            })
        elif self.indicator_type == "MACD":
            params.update({
                "type": "MACD",
                "fast": self.macd_fast.value(),
                "slow": self.macd_slow.value(),
                "signal": self.macd_signal.value()
            })
        elif self.indicator_type == "스토캐스틱":
            params.update({
                "type": "Stochastic",
                "k": self.stoch_k.value(),
                "d": self.stoch_d.value(),
                "smooth": self.stoch_smooth.value()
            })
        
        return params


class IndicatorItem(QWidget):
    """개별 지표 항목"""
    
    # 시그널 정의
    visibility_changed = pyqtSignal(str, bool)
    settings_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    
    def __init__(self, indicator_id, indicator_name, params, parent=None):
        super().__init__(parent)
        self.indicator_id = indicator_id
        self.indicator_name = indicator_name
        self.params = params
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 가시성 토글
        self.visibility_toggle = QCheckBox()
        self.visibility_toggle.setChecked(True)
        self.visibility_toggle.stateChanged.connect(
            lambda state: self.visibility_changed.emit(
                self.indicator_id, 
                state == Qt.CheckState.Checked.value
            )
        )
        layout.addWidget(self.visibility_toggle)
        
        # 지표 이름과 파라미터
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.indicator_name)
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        info_layout.addWidget(name_label)
        
        # 파라미터 표시
        param_text = self.format_params()
        param_label = QLabel(param_text)
        param_label.setFont(QFont("Arial", 8))
        param_label.setStyleSheet("color: #666;")
        info_layout.addWidget(param_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # 설정 버튼
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(25, 25)
        self.settings_btn.setToolTip("지표 설정")
        self.settings_btn.clicked.connect(
            lambda: self.settings_requested.emit(self.indicator_id)
        )
        layout.addWidget(self.settings_btn)
        
        # 제거 버튼
        self.remove_btn = QPushButton("❌")
        self.remove_btn.setFixedSize(25, 25)
        self.remove_btn.setToolTip("지표 제거")
        self.remove_btn.clicked.connect(
            lambda: self.remove_requested.emit(self.indicator_id)
        )
        layout.addWidget(self.remove_btn)
        
        # 스타일 설정
        self.setStyleSheet("""
            IndicatorItem {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin: 2px;
            }
            IndicatorItem:hover {
                background-color: #e9ecef;
            }
        """)
    
    def format_params(self):
        """파라미터 형식화"""
        if self.params["type"] == "SMA":
            return f"기간: {self.params['period']}"
        elif self.params["type"] == "EMA":
            return f"기간: {self.params['period']}"
        elif self.params["type"] == "BBANDS":
            return f"기간: {self.params['period']}, 표준편차: {self.params['std']}"
        elif self.params["type"] == "RSI":
            return f"기간: {self.params['period']}"
        elif self.params["type"] == "MACD":
            return f"빠름: {self.params['fast']}, 느림: {self.params['slow']}, 시그널: {self.params['signal']}"
        elif self.params["type"] == "Stochastic":
            return f"K: {self.params['k']}, D: {self.params['d']}"
        return ""


class IndicatorManagementPanel(QWidget):
    """지표 관리 패널"""
    
    # 시그널 정의
    indicator_added = pyqtSignal(str, dict)
    indicator_removed = pyqtSignal(str)
    indicator_visibility_changed = pyqtSignal(str, bool)
    indicator_settings_changed = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_indicators = {}  # indicator_id -> IndicatorItem
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 헤더
        header_layout = QHBoxLayout()
        header_label = QLabel("📈 기술적 지표")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # 지표 추가 버튼
        self.add_indicator_btn = QPushButton("+ 지표 추가")
        self.add_indicator_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.add_indicator_btn.clicked.connect(self.show_add_indicator_dialog)
        header_layout.addWidget(self.add_indicator_btn)
        
        layout.addLayout(header_layout)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 활성 지표 목록
        self.indicators_scroll = QScrollArea()
        self.indicators_scroll.setWidgetResizable(True)
        self.indicators_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.indicators_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 지표 컨테이너
        self.indicators_container = QWidget()
        self.indicators_layout = QVBoxLayout(self.indicators_container)
        self.indicators_layout.setContentsMargins(0, 0, 0, 0)
        self.indicators_layout.addStretch()
        
        self.indicators_scroll.setWidget(self.indicators_container)
        layout.addWidget(self.indicators_scroll)
        
        # 빈 상태 메시지
        self.empty_label = QLabel("아직 추가된 지표가 없습니다.\n'지표 추가' 버튼을 클릭하여 지표를 추가해보세요.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.empty_label)
        
        self.update_empty_state()
    
    def show_add_indicator_dialog(self):
        """지표 추가 대화상자 표시"""
        indicators = [
            "이동평균 (SMA)", "지수이동평균 (EMA)", "볼린저밴드 (BBANDS)",
            "RSI", "MACD", "스토캐스틱"
        ]
        
        # 간단한 선택 대화상자 (향후 개선 가능)
        from PyQt6.QtWidgets import QInputDialog
        
        indicator_type, ok = QInputDialog.getItem(
            self, "지표 선택", "추가할 지표를 선택하세요:", indicators, 0, False
        )
        
        if ok and indicator_type:
            # 지표 설정 대화상자 표시
            config_dialog = IndicatorConfigDialog(indicator_type, self)
            if config_dialog.exec() == QDialog.DialogCode.Accepted:
                params = config_dialog.get_params()
                self.add_indicator(indicator_type, params)
    
    def add_indicator(self, indicator_name, params):
        """지표 추가"""
        # 지표 ID 생성
        indicator_id = self.generate_indicator_id(indicator_name, params)
        
        # 중복 확인
        if indicator_id in self.active_indicators:
            QMessageBox.warning(
                self, "중복 지표", 
                f"동일한 설정의 {indicator_name} 지표가 이미 추가되어 있습니다."
            )
            return
        
        # 지표 아이템 생성
        indicator_item = IndicatorItem(indicator_id, indicator_name, params)
        indicator_item.visibility_changed.connect(self.indicator_visibility_changed.emit)
        indicator_item.settings_requested.connect(self.on_indicator_settings_requested)
        indicator_item.remove_requested.connect(self.remove_indicator)
        
        # 레이아웃에 추가 (stretch 앞에)
        self.indicators_layout.insertWidget(
            self.indicators_layout.count() - 1, indicator_item
        )
        
        # 활성 지표 목록에 추가
        self.active_indicators[indicator_id] = indicator_item
        
        # 상태 업데이트
        self.update_empty_state()
        
        # 시그널 발송
        self.indicator_added.emit(indicator_id, params)
    
    def remove_indicator(self, indicator_id):
        """지표 제거"""
        if indicator_id in self.active_indicators:
            # 위젯 제거
            indicator_item = self.active_indicators[indicator_id]
            indicator_item.deleteLater()
            
            # 딕셔너리에서 제거
            del self.active_indicators[indicator_id]
            
            # 상태 업데이트
            self.update_empty_state()
            
            # 시그널 발송
            self.indicator_removed.emit(indicator_id)
    
    def on_indicator_settings_requested(self, indicator_id):
        """지표 설정 요청 처리"""
        if indicator_id in self.active_indicators:
            indicator_item = self.active_indicators[indicator_id]
            
            # 설정 대화상자 표시
            config_dialog = IndicatorConfigDialog(indicator_item.indicator_name, self)
            
            # 현재 설정으로 초기화 (향후 구현)
            
            if config_dialog.exec() == QDialog.DialogCode.Accepted:
                new_params = config_dialog.get_params()
                
                # 설정 변경 시그널 발송
                self.indicator_settings_changed.emit(indicator_id, new_params)
                
                # 아이템 업데이트
                indicator_item.params = new_params
                # UI 업데이트는 indicator_item에서 처리 (향후 구현)
    
    def generate_indicator_id(self, indicator_name, params):
        """지표 ID 생성"""
        base_name = params["type"]
        
        if params["type"] == "SMA":
            return f"SMA_{params['period']}"
        elif params["type"] == "EMA":
            return f"EMA_{params['period']}"
        elif params["type"] == "BBANDS":
            return f"BBANDS_{params['period']}_{params['std']}"
        elif params["type"] == "RSI":
            return f"RSI_{params['period']}"
        elif params["type"] == "MACD":
            return f"MACD_{params['fast']}_{params['slow']}_{params['signal']}"
        elif params["type"] == "Stochastic":
            return f"STOCH_{params['k']}_{params['d']}"
        
        return f"{base_name}_{len(self.active_indicators)}"
    
    def update_empty_state(self):
        """빈 상태 UI 업데이트"""
        has_indicators = len(self.active_indicators) > 0
        self.empty_label.setVisible(not has_indicators)
        self.indicators_scroll.setVisible(has_indicators)
    
    def get_active_indicators(self):
        """활성 지표 목록 반환"""
        return list(self.active_indicators.keys())
    
    def clear_all_indicators(self):
        """모든 지표 제거"""
        for indicator_id in list(self.active_indicators.keys()):
            self.remove_indicator(indicator_id)
