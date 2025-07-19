"""
백테스팅 화면 메인 모듈
- 전략/포트폴리오 백테스트 실행
- 결과 분석 및 시각화
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout
from .components.backtest_setup import BacktestSetupWidget
from .components.backtest_results import BacktestResultsWidget

class BacktestingScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("백테스팅")
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        # 전체를 감싸는 수평 레이아웃 (좌우 2분할)
        layout = QHBoxLayout(self)
        
        # 1. 왼쪽: 백테스트 설정 패널
        self.setup_panel = BacktestSetupWidget(self)
        layout.addWidget(self.setup_panel, stretch=1)  # 1/3 비율
        
        # 2. 오른쪽: 백테스트 결과 패널
        self.results_panel = BacktestResultsWidget(self)
        layout.addWidget(self.results_panel, stretch=2)  # 2/3 비율
        
        # 시그널/슬롯 연결
        self.setup_panel.backtest_started.connect(self.start_backtest)
    
    def start_backtest(self, config):
        """백테스트 실행"""
        print("[DEBUG] 백테스트 설정:", config)
        # TODO: 실제 백테스트 실행 로직 구현
        self.results_panel.clear_results()  # 이전 결과 초기화
        self.results_panel.show_loading(True)  # 로딩 표시
        
        # TODO: 실제 백테스트 실행 및 결과 처리
        # self.results_panel.update_results(results)
        # self.results_panel.show_loading(False)
