"""
차트 컨트롤 패널 컴포넌트
- 심볼 선택
- 시간대 선택
- 지표 추가/제거
- 차트 설정
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QComboBox,
    QPushButton, QLabel, QCheckBox, QGroupBox,
    QSpinBox, QDoubleSpinBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon

class ChartControlPanel(QWidget):
    """차트 컨트롤 패널"""

    # 시그널 정의
    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)
    indicator_added = pyqtSignal(str, dict)
    chart_saved = pyqtSignal()
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 기본 컨트롤 영역
        basic_controls = self.create_basic_controls()
        layout.addWidget(basic_controls)

        # 지표 컨트롤 영역
        indicator_controls = self.create_indicator_controls()
        layout.addWidget(indicator_controls)

        # 차트 설정 영역
        chart_settings = self.create_chart_settings()
        layout.addWidget(chart_settings)

        # 액션 버튼 영역
        action_buttons = self.create_action_buttons()
        layout.addWidget(action_buttons)

        layout.addStretch()

    def create_basic_controls(self):
        """기본 컨트롤 생성"""
        group = QGroupBox("📊 차트 기본 설정")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        layout = QFormLayout(group)

        # 심볼 선택기
        self.symbol_selector = QComboBox()
        self.symbol_selector.addItems([
            "BTC-KRW", "ETH-KRW", "XRP-KRW", "ADA-KRW",
            "DOT-KRW", "DOGE-KRW", "SOL-KRW", "MATIC-KRW",
            "LINK-KRW", "LTC-KRW"
        ])
        self.symbol_selector.setCurrentText("BTC-KRW")
        self.symbol_selector.currentTextChanged.connect(self.symbol_changed.emit)
        layout.addRow("종목:", self.symbol_selector)

        # 시간대 선택기
        self.timeframe_selector = QComboBox()
        self.timeframe_selector.addItems([
            "1분", "3분", "5분", "15분", "30분",
            "1시간", "4시간", "1일", "1주", "1월"
        ])
        self.timeframe_selector.setCurrentText("1일")
        self.timeframe_selector.currentTextChanged.connect(self.timeframe_changed.emit)
        layout.addRow("시간대:", self.timeframe_selector)

        return group

    def create_indicator_controls(self):
        """지표 컨트롤 생성"""
        group = QGroupBox("📈 기술적 지표")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)

        layout = QVBoxLayout(group)

        # 지표 선택 영역
        indicator_layout = QHBoxLayout()

        # 지표 선택기
        self.indicator_selector = QComboBox()
        self.indicator_selector.addItems([
            "이동평균 (SMA)", "지수이동평균 (EMA)", "볼린저밴드 (BBANDS)",
            "RSI", "MACD", "스토캐스틱", "거래량", "ATR"
        ])
        indicator_layout.addWidget(self.indicator_selector)

        # 지표 추가 버튼
        self.add_indicator_btn = QPushButton("지표 추가")
        self.add_indicator_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.add_indicator_btn.clicked.connect(self.on_add_indicator)
        indicator_layout.addWidget(self.add_indicator_btn)

        layout.addLayout(indicator_layout)

        # 지표 파라미터 설정 영역
        self.indicator_params_group = QGroupBox("지표 파라미터")
        self.indicator_params_layout = QFormLayout(self.indicator_params_group)
        layout.addWidget(self.indicator_params_group)

        # 초기 파라미터 설정
        self.update_indicator_params()

        # 지표 선택 변경 시 파라미터 업데이트
        self.indicator_selector.currentTextChanged.connect(self.update_indicator_params)

        return group

    def create_chart_settings(self):
        """차트 설정 생성"""
        group = QGroupBox("⚙️ 차트 설정")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)

        layout = QVBoxLayout(group)

        # 차트 표시 옵션
        self.show_volume = QCheckBox("거래량 표시")
        self.show_volume.setChecked(True)
        self.show_volume.stateChanged.connect(self.on_settings_changed)
        layout.addWidget(self.show_volume)

        self.show_grid = QCheckBox("격자 표시")
        self.show_grid.setChecked(True)
        self.show_grid.stateChanged.connect(self.on_settings_changed)
        layout.addWidget(self.show_grid)

        self.show_crosshair = QCheckBox("십자선 표시")
        self.show_crosshair.setChecked(True)
        self.show_crosshair.stateChanged.connect(self.on_settings_changed)
        layout.addWidget(self.show_crosshair)

        # 색상 설정
        color_layout = QFormLayout()

        self.bull_color_btn = QPushButton("상승봉 색상")
        self.bull_color_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        color_layout.addRow("상승봉:", self.bull_color_btn)

        self.bear_color_btn = QPushButton("하락봉 색상")
        self.bear_color_btn.setStyleSheet("background-color: #F44336; color: white;")
        color_layout.addRow("하락봉:", self.bear_color_btn)

        layout.addLayout(color_layout)

        return group

    def create_action_buttons(self):
        """액션 버튼 생성"""
        group = QGroupBox("🔧 액션")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)

        layout = QVBoxLayout(group)

        # 차트 저장 버튼
        self.save_chart_btn = QPushButton("📷 차트 저장")
        self.save_chart_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.save_chart_btn.clicked.connect(self.chart_saved.emit)
        layout.addWidget(self.save_chart_btn)

        # 차트 초기화 버튼
        self.reset_chart_btn = QPushButton("🔄 차트 초기화")
        self.reset_chart_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.reset_chart_btn.clicked.connect(self.on_reset_chart)
        layout.addWidget(self.reset_chart_btn)

        return group

    def update_indicator_params(self):
        """지표 파라미터 업데이트"""
        # 기존 파라미터 위젯 제거
        for i in reversed(range(self.indicator_params_layout.count())):
            child = self.indicator_params_layout.itemAt(i)
            if child.widget():
                child.widget().deleteLater()

        indicator_type = self.indicator_selector.currentText()

        if "이동평균 (SMA)" in indicator_type:
            self.sma_period = QSpinBox()
            self.sma_period.setRange(1, 200)
            self.sma_period.setValue(20)
            self.indicator_params_layout.addRow("기간:", self.sma_period)

        elif "지수이동평균 (EMA)" in indicator_type:
            self.ema_period = QSpinBox()
            self.ema_period.setRange(1, 200)
            self.ema_period.setValue(20)
            self.indicator_params_layout.addRow("기간:", self.ema_period)

        elif "볼린저밴드" in indicator_type:
            self.bb_period = QSpinBox()
            self.bb_period.setRange(1, 200)
            self.bb_period.setValue(20)
            self.indicator_params_layout.addRow("기간:", self.bb_period)

            self.bb_std = QDoubleSpinBox()
            self.bb_std.setRange(0.1, 5.0)
            self.bb_std.setValue(2.0)
            self.bb_std.setSingleStep(0.1)
            self.indicator_params_layout.addRow("표준편차:", self.bb_std)

        elif "RSI" in indicator_type:
            self.rsi_period = QSpinBox()
            self.rsi_period.setRange(1, 100)
            self.rsi_period.setValue(14)
            self.indicator_params_layout.addRow("기간:", self.rsi_period)

        elif "MACD" in indicator_type:
            self.macd_fast = QSpinBox()
            self.macd_fast.setRange(1, 100)
            self.macd_fast.setValue(12)
            self.indicator_params_layout.addRow("빠른 기간:", self.macd_fast)

            self.macd_slow = QSpinBox()
            self.macd_slow.setRange(1, 100)
            self.macd_slow.setValue(26)
            self.indicator_params_layout.addRow("느린 기간:", self.macd_slow)

            self.macd_signal = QSpinBox()
            self.macd_signal.setRange(1, 50)
            self.macd_signal.setValue(9)
            self.indicator_params_layout.addRow("시그널 기간:", self.macd_signal)

        elif "스토캐스틱" in indicator_type:
            self.stoch_k = QSpinBox()
            self.stoch_k.setRange(1, 100)
            self.stoch_k.setValue(14)
            self.indicator_params_layout.addRow("%K 기간:", self.stoch_k)

            self.stoch_d = QSpinBox()
            self.stoch_d.setRange(1, 50)
            self.stoch_d.setValue(3)
            self.indicator_params_layout.addRow("%D 기간:", self.stoch_d)

    def on_add_indicator(self):
        """지표 추가"""
        indicator_type = self.indicator_selector.currentText()
        params = {}

        if "이동평균 (SMA)" in indicator_type:
            params = {"type": "SMA", "period": self.sma_period.value()}
        elif "지수이동평균 (EMA)" in indicator_type:
            params = {"type": "EMA", "period": self.ema_period.value()}
        elif "볼린저밴드" in indicator_type:
            params = {
                "type": "BBANDS",
                "period": self.bb_period.value(),
                "std": self.bb_std.value()
            }
        elif "RSI" in indicator_type:
            params = {"type": "RSI", "period": self.rsi_period.value()}
        elif "MACD" in indicator_type:
            params = {
                "type": "MACD",
                "fast": self.macd_fast.value(),
                "slow": self.macd_slow.value(),
                "signal": self.macd_signal.value()
            }
        elif "스토캐스틱" in indicator_type:
            params = {
                "type": "Stochastic",
                "k": self.stoch_k.value(),
                "d": self.stoch_d.value()
            }

        self.indicator_added.emit(indicator_type, params)

    def on_settings_changed(self):
        """설정 변경"""
        settings = {
            "show_volume": self.show_volume.isChecked(),
            "show_grid": self.show_grid.isChecked(),
            "show_crosshair": self.show_crosshair.isChecked()
        }
        self.settings_changed.emit(settings)

    def on_reset_chart(self):
        """차트 초기화"""
        # 여기에서 차트 초기화 로직 구현
        pass

    def get_current_symbol(self):
        """현재 선택된 심볼 반환"""
        return self.symbol_selector.currentText()

    def get_current_timeframe(self):
        """현재 선택된 시간대 반환"""
        timeframe_map = {
            "1분": "1m", "3분": "3m", "5분": "5m", "15분": "15m", "30분": "30m",
            "1시간": "1h", "4시간": "4h", "1일": "1d", "1주": "1w", "1월": "1M"
        }
        return timeframe_map.get(self.timeframe_selector.currentText(), "1d")

    def set_symbol(self, symbol):
        """심볼 설정"""
        self.symbol_selector.setCurrentText(symbol)

    def set_timeframe(self, timeframe):
        """시간대 설정 (API 친화적 값 → 표시용 한글 변환)"""
        timeframe_reverse_map = {
            "position_follow": "포지션 설정 따름",
            "1m": "1분", "3m": "3분", "5m": "5분", "10m": "10분", "15m": "15분", "30m": "30분",
            "1h": "1시간", "4h": "4시간", "1d": "1일", "1w": "1주", "1M": "1월"
        }
        display_timeframe = timeframe_reverse_map.get(timeframe, "1일")
        self.timeframe_selector.setCurrentText(display_timeframe)
