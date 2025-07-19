"""
포트폴리오 구성 화면 메인 모듈
- 포트폴리오 생성 및 관리
- 자산 배분 설정 및 시각화
- 성과 예측 및 백테스트 연동
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from .components.portfolio_list_panel import PortfolioListPanel
from .components.portfolio_composition_panel import PortfolioCompositionPanel
from .components.portfolio_performance_panel import PortfolioPerformancePanel

class PortfolioConfigurationScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("포트폴리오 구성")
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        # 전체를 감싸는 수평 레이아웃 (3분할)
        layout = QHBoxLayout(self)
        
        # 1. 왼쪽: 포트폴리오 목록 패널
        self.portfolio_list_panel = PortfolioListPanel(self)
        layout.addWidget(self.portfolio_list_panel, stretch=1)  # 1/4 비율
        
        # 2. 중앙: 포트폴리오 구성 패널
        self.composition_panel = PortfolioCompositionPanel(self)
        layout.addWidget(self.composition_panel, stretch=2)  # 2/4 비율
        
        # 3. 오른쪽: 성과 분석 패널
        self.performance_panel = PortfolioPerformancePanel(self)
        layout.addWidget(self.performance_panel, stretch=1)  # 1/4 비율
        
        # 시그널/슬롯 연결
        self.connect_signals()
    
    def connect_signals(self):
        """시그널/슬롯 연결"""
        # 포트폴리오 선택 시 구성 패널 업데이트
        self.portfolio_list_panel.portfolio_selected.connect(
            self.composition_panel.load_portfolio
        )
        
        # 포트폴리오 변경 시 성과 패널 업데이트
        self.composition_panel.portfolio_changed.connect(
            self.performance_panel.update_performance
        )
        
        # 새 포트폴리오 생성 시 목록 갱신
        self.composition_panel.portfolio_saved.connect(
            self.portfolio_list_panel.refresh_list
        )
        
        # 백테스트 실행 시그널 연결
        self.performance_panel.backtest_requested.connect(
            self.start_backtest
        )
        
        # 실시간 거래 시작 시그널 연결
        self.performance_panel.live_trading_requested.connect(
            self.start_live_trading
        )
    
    def start_backtest(self, portfolio_data):
        """백테스트 시작"""
        print("[DEBUG] 포트폴리오 백테스트 시작:", portfolio_data)
        # TODO: 백테스팅 화면으로 전환하며 포트폴리오 데이터 전달
        # self.parent().change_screen("backtesting", portfolio_data)
    
    def start_live_trading(self, portfolio_data):
        """실시간 거래 시작"""
        print("[DEBUG] 포트폴리오 실시간 거래 시작:", portfolio_data)
        # TODO: 실시간 거래 화면으로 전환하며 포트폴리오 데이터 전달
        # self.parent().change_screen("live_trading", portfolio_data)
