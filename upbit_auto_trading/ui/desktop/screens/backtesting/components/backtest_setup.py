"""
백테스트 설정 위젯
- 전략/포트폴리오 선택
- 테스트 기간 설정
- 초기 자본금 설정
- 거래 수수료/슬리피지 설정
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QDateEdit
)
from PyQt6.QtCore import pyqtSignal, QDate

class BacktestSetupWidget(QWidget):
    # 백테스트 시작 시그널 (설정 정보를 딕셔너리로 전달)
    backtest_started = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 1. 전략/포트폴리오 선택
        strategy_group = QGroupBox("테스트 대상 선택")
        strategy_layout = QVBoxLayout(strategy_group)
        
        self.test_type = QComboBox()
        self.test_type.addItems(["개별 전략", "포트폴리오"])
        strategy_layout.addWidget(self.test_type)
        
        self.target_selector = QComboBox()
        self.update_target_list()  # 선택된 유형에 따라 목록 업데이트
        strategy_layout.addWidget(self.target_selector)
        
        layout.addWidget(strategy_group)
        
        # 2. 테스트 기간 설정
        period_group = QGroupBox("테스트 기간")
        period_layout = QVBoxLayout(period_group)
        
        start_date_layout = QHBoxLayout()
        start_date_layout.addWidget(QLabel("시작일:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))  # 1달 전
        start_date_layout.addWidget(self.start_date)
        period_layout.addLayout(start_date_layout)
        
        end_date_layout = QHBoxLayout()
        end_date_layout.addWidget(QLabel("종료일:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())  # 오늘
        end_date_layout.addWidget(self.end_date)
        period_layout.addLayout(end_date_layout)
        
        layout.addWidget(period_group)
        
        # 3. 자본금 및 거래 설정
        trading_group = QGroupBox("거래 설정")
        trading_layout = QVBoxLayout(trading_group)
        
        # 초기 자본
        capital_layout = QHBoxLayout()
        capital_layout.addWidget(QLabel("초기 자본:"))
        self.initial_capital = QSpinBox()
        self.initial_capital.setRange(10000, 1000000000)
        self.initial_capital.setValue(10000000)  # 1천만원
        self.initial_capital.setSingleStep(1000000)  # 100만원 단위
        self.initial_capital.setSuffix(" 원")
        capital_layout.addWidget(self.initial_capital)
        trading_layout.addLayout(capital_layout)
        
        # 거래 수수료
        fee_layout = QHBoxLayout()
        fee_layout.addWidget(QLabel("거래 수수료:"))
        self.trading_fee = QDoubleSpinBox()
        self.trading_fee.setRange(0, 1)
        self.trading_fee.setValue(0.05)  # 0.05%
        self.trading_fee.setSingleStep(0.01)
        self.trading_fee.setSuffix(" %")
        fee_layout.addWidget(self.trading_fee)
        trading_layout.addLayout(fee_layout)
        
        # 슬리피지
        slippage_layout = QHBoxLayout()
        slippage_layout.addWidget(QLabel("슬리피지:"))
        self.slippage = QDoubleSpinBox()
        self.slippage.setRange(0, 1)
        self.slippage.setValue(0.1)  # 0.1%
        self.slippage.setSingleStep(0.1)
        self.slippage.setSuffix(" %")
        slippage_layout.addWidget(self.slippage)
        trading_layout.addLayout(slippage_layout)
        
        layout.addWidget(trading_group)
        
        # 4. 실행 버튼
        self.run_btn = QPushButton("백테스트 실행")
        self.run_btn.clicked.connect(self.run_backtest)
        layout.addWidget(self.run_btn)
        
        # 남은 공간을 위쪽으로 밀어냄
        layout.addStretch(1)
        
        # 이벤트 연결
        self.test_type.currentIndexChanged.connect(self.update_target_list)
    
    def update_target_list(self):
        """선택된 유형에 따라 테스트 대상 목록 업데이트"""
        self.target_selector.clear()
        
        if self.test_type.currentText() == "개별 전략":
            # TODO: 전략 목록 로드
            strategies = ["골든크로스", "RSI 반등", "변동성 돌파"]  # 임시 데이터
            self.target_selector.addItems(strategies)
        else:
            # TODO: 포트폴리오 목록 로드
            portfolios = ["안정형 포트폴리오", "공격형 포트폴리오"]  # 임시 데이터
            self.target_selector.addItems(portfolios)
    
    def run_backtest(self):
        """백테스트 실행"""
        config = {
            'test_type': self.test_type.currentText(),
            'target': self.target_selector.currentText(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'initial_capital': self.initial_capital.value(),
            'trading_fee': self.trading_fee.value(),
            'slippage': self.slippage.value()
        }
        
        self.backtest_started.emit(config)
