"""
전략 에디터 위젯
- 시각적 전략 편집 도구
- 전략 유형별 파라미터 설정
- 전략 저장/테스트 기능
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QSpinBox, QGroupBox
)
from PyQt6.QtCore import pyqtSignal

class StrategyEditorWidget(QWidget):
    # 시그널 정의
    strategy_updated = pyqtSignal(str)  # 전략 ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. 상단: 전략 기본 정보
        info_group = QGroupBox("전략 기본 정보")
        info_layout = QVBoxLayout(info_group)
        
        # 전략 유형 선택
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("전략 유형:"))
        self.strategy_type = QComboBox()
        self.strategy_type.addItems(["이동평균 교차", "RSI", "변동성 돌파", "볼린저 밴드"])
        type_row.addWidget(self.strategy_type)
        info_layout.addLayout(type_row)
        
        layout.addWidget(info_group)
        
        # 2. 중앙: 파라미터 설정
        params_group = QGroupBox("파라미터 설정")
        params_layout = QVBoxLayout(params_group)
        
        # 이동평균선 기간 설정
        ma_row = QHBoxLayout()
        ma_row.addWidget(QLabel("단기 이평:"))
        self.short_ma = QSpinBox()
        self.short_ma.setRange(1, 200)
        self.short_ma.setValue(5)
        ma_row.addWidget(self.short_ma)
        
        ma_row.addWidget(QLabel("장기 이평:"))
        self.long_ma = QSpinBox()
        self.long_ma.setRange(1, 200)
        self.long_ma.setValue(20)
        ma_row.addWidget(self.long_ma)
        
        params_layout.addLayout(ma_row)
        
        # RSI 설정
        rsi_row = QHBoxLayout()
        rsi_row.addWidget(QLabel("RSI 기간:"))
        self.rsi_period = QSpinBox()
        self.rsi_period.setRange(1, 100)
        self.rsi_period.setValue(14)
        rsi_row.addWidget(self.rsi_period)
        
        rsi_row.addWidget(QLabel("과매수:"))
        self.rsi_high = QSpinBox()
        self.rsi_high.setRange(50, 100)
        self.rsi_high.setValue(70)
        rsi_row.addWidget(self.rsi_high)
        
        rsi_row.addWidget(QLabel("과매도:"))
        self.rsi_low = QSpinBox()
        self.rsi_low.setRange(0, 50)
        self.rsi_low.setValue(30)
        rsi_row.addWidget(self.rsi_low)
        
        params_layout.addLayout(rsi_row)
        
        layout.addWidget(params_group)
        
        # 3. 하단: 액션 버튼
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("전략 저장")
        self.save_btn.clicked.connect(self.save_strategy)
        self.test_btn = QPushButton("백테스트 실행")
        self.test_btn.clicked.connect(self.run_backtest)
        
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.test_btn)
        layout.addLayout(btn_row)
    
    def load_strategy(self, strategy_id):
        """전략 불러오기"""
        print(f"[DEBUG] 전략 불러오기: {strategy_id}")
        # TODO: DB에서 전략 정보 조회하여 UI에 표시
    
    def save_strategy(self):
        """전략 저장"""
        # TODO: 현재 설정된 전략 정보를 DB에 저장
        print("[DEBUG] 전략 저장")
        self.strategy_updated.emit("current_strategy_id")
    
    def run_backtest(self):
        """백테스트 실행"""
        # TODO: 백테스트 실행 및 결과 표시
        print("[DEBUG] 백테스트 실행")
