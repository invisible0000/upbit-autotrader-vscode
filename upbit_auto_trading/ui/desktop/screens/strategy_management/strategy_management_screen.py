"""
매매 전략 관리 화면의 메인 모듈
- 전략 목록, 에디터, 상세 정보 패널을 통합 관리
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from .components.strategy_list import StrategyListWidget
from .components.strategy_editor import StrategyEditorWidget
from .components.strategy_details import StrategyDetailsWidget

class StrategyManagementScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("매매 전략 관리")
        self.init_ui()
    
    def init_ui(self):
        # 전체를 감싸는 수평 레이아웃 (좌우 3분할)
        layout = QHBoxLayout(self)
        
        # 1. 왼쪽: 전략 목록
        self.strategy_list = StrategyListWidget(self)
        layout.addWidget(self.strategy_list)
        
        # 2. 중앙: 전략 에디터
        self.strategy_editor = StrategyEditorWidget(self)
        layout.addWidget(self.strategy_editor)
        
        # 3. 오른쪽: 상세 정보
        self.strategy_details = StrategyDetailsWidget(self)
        layout.addWidget(self.strategy_details)
        
        # 시그널/슬롯 연결
        self.strategy_list.strategy_selected.connect(self.on_strategy_selected)
        self.strategy_editor.strategy_updated.connect(self.on_strategy_updated)
    
    def on_strategy_selected(self, strategy_id):
        """전략 목록에서 전략 선택 시"""
        self.strategy_editor.load_strategy(strategy_id)
        self.strategy_details.load_strategy(strategy_id)
    
    def on_strategy_updated(self, strategy_id):
        """전략 수정 시"""
        self.strategy_list.refresh_list()
        self.strategy_details.load_strategy(strategy_id)
