"""
실시간 거래 화면 메인 모듈
- 활성 전략 실시간 모니터링
- 수동 주문 실행
- 거래 내역 관리
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt
from .components.active_strategies_panel import ActiveStrategiesPanel
from .components.manual_order_panel import ManualOrderPanel
from .components.market_data_panel import MarketDataPanel
from .components.trade_history_panel import TradeHistoryPanel
from .components.emergency_controls import EmergencyControls

class LiveTradingScreen(QWidget):
    """
    실시간 거래 화면
    - 실시간 전략 관리
    - 수동 주문 기능
    - 거래 내역 모니터링
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("실시간 거래")
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃 (수직)
        main_layout = QVBoxLayout(self)
        
        # 1. 상단: 긴급 제어 패널
        self.emergency_controls = EmergencyControls(self)
        main_layout.addWidget(self.emergency_controls)
        
        # 2. 중앙: 메인 콘텐츠 영역 (수평 분할)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter, stretch=1)
        
        # 2-1. 왼쪽: 전략 관리 및 시장 데이터 (수직 분할)
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(left_splitter)
        
        # 활성 전략 패널 (상단)
        self.active_strategies_panel = ActiveStrategiesPanel(self)
        left_splitter.addWidget(self.active_strategies_panel)
        
        # 시장 데이터 패널 (하단)
        self.market_data_panel = MarketDataPanel(self)
        left_splitter.addWidget(self.market_data_panel)
        
        # 왼쪽 분할 비율 설정 (7:3)
        left_splitter.setSizes([700, 300])
        
        # 2-2. 중앙: 수동 주문 패널
        self.manual_order_panel = ManualOrderPanel(self)
        main_splitter.addWidget(self.manual_order_panel)
        
        # 2-3. 오른쪽: 거래 내역 패널
        self.trade_history_panel = TradeHistoryPanel(self)
        main_splitter.addWidget(self.trade_history_panel)
        
        # 메인 분할 비율 설정 (5:2:3)
        main_splitter.setSizes([500, 200, 300])
    
    def setup_connections(self):
        """컴포넌트 간 시그널/슬롯 연결"""
        # 긴급 정지 버튼 연결
        self.emergency_controls.emergency_stop_all.connect(self.stop_all_strategies)
        
        # 활성 전략에서 개별 정지 요청
        self.active_strategies_panel.strategy_stop_requested.connect(self.stop_strategy)
        
        # 수동 주문 완료 시 거래 내역 갱신
        self.manual_order_panel.order_placed.connect(self.trade_history_panel.refresh_data)
        
        # 전략 상태 변경 시 활성 전략 목록 갱신
        self.emergency_controls.strategy_stopped.connect(self.active_strategies_panel.refresh_data)
    
    def stop_all_strategies(self):
        """모든 활성 전략 중지"""
        print("[DEBUG] 모든 전략 중지 요청")
        # TODO: 실제 전략 중지 로직 구현
        self.active_strategies_panel.stop_all_strategies()
    
    def stop_strategy(self, strategy_id):
        """특정 전략 중지"""
        print(f"[DEBUG] 전략 {strategy_id} 중지 요청")
        # TODO: 실제 전략 중지 로직 구현
        self.active_strategies_panel.stop_strategy(strategy_id)
    
    def refresh_all_data(self):
        """모든 패널 데이터 새로고침"""
        self.active_strategies_panel.refresh_data()
        self.market_data_panel.refresh_data()
        self.trade_history_panel.refresh_data()
    
    def showEvent(self, event):
        """화면 표시 시 데이터 새로고침"""
        super().showEvent(event)
        self.refresh_all_data()
