"""
매매 전략 관리 화면의 메인 모듈
- 전략 목록, 에디터, 상세 정보 패널을 통합 관리
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
    QPushButton, QLabel, QToolBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

from .components.strategy_list import StrategyListWidget
from .components.strategy_editor import StrategyEditorWidget
from .components.strategy_details import StrategyDetailsWidget

class StrategyManagementScreen(QWidget):
    # 백테스팅 요청 시그널
    backtest_requested = pyqtSignal(str)  # 전략 ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 매매 전략 관리")
        self.current_strategy_id = None
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 툴바 추가
        toolbar_layout = QHBoxLayout()
        
        # 새 전략 생성 버튼
        self.new_strategy_btn = QPushButton("➕ 새 전략 생성")
        self.new_strategy_btn.clicked.connect(self.create_new_strategy)
        toolbar_layout.addWidget(self.new_strategy_btn)
        
        # 백테스팅 실행 버튼
        self.backtest_btn = QPushButton("🔬 백테스팅 실행")
        self.backtest_btn.clicked.connect(self.run_backtest)
        self.backtest_btn.setEnabled(False)
        toolbar_layout.addWidget(self.backtest_btn)
        
        toolbar_layout.addStretch()
        
        # 상태 라벨
        self.status_label = QLabel("전략을 선택하거나 새로 생성하세요.")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        toolbar_layout.addWidget(self.status_label)
        
        layout.addLayout(toolbar_layout)
        
        # 메인 컨텐츠를 스플리터로 3분할
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 1. 왼쪽: 전략 목록 (30%)
        self.strategy_list = StrategyListWidget(self)
        main_splitter.addWidget(self.strategy_list)
        
        # 2. 중앙: 전략 에디터 (40%)
        self.strategy_editor = StrategyEditorWidget(self)
        main_splitter.addWidget(self.strategy_editor)
        
        # 3. 오른쪽: 상세 정보 (30%)
        self.strategy_details = StrategyDetailsWidget(self)
        main_splitter.addWidget(self.strategy_details)
        
        # 스플리터 비율 설정
        main_splitter.setSizes([300, 400, 300])
        
        layout.addWidget(main_splitter)
    
    def setup_connections(self):
        """시그널/슬롯 연결"""
        self.strategy_list.strategy_selected.connect(self.on_strategy_selected)
        self.strategy_editor.strategy_saved.connect(self.on_strategy_saved)
    
    def create_new_strategy(self):
        """새 전략 생성"""
        self.strategy_editor.create_new_strategy()
        self.current_strategy_id = None
        self.backtest_btn.setEnabled(False)
        self.status_label.setText("새 전략을 생성하고 있습니다...")
    
    def on_strategy_selected(self, strategy_id):
        """전략 목록에서 전략 선택 시"""
        self.current_strategy_id = strategy_id
        self.strategy_editor.load_strategy(strategy_id)
        self.strategy_details.load_strategy(strategy_id)
        self.backtest_btn.setEnabled(True)
        self.status_label.setText(f"전략 ID: {strategy_id}")
    
    def on_strategy_saved(self, strategy_id):
        """전략 저장 완료 시"""
        self.current_strategy_id = strategy_id
        self.strategy_list.refresh_list()
        self.strategy_details.load_strategy(strategy_id)
        self.backtest_btn.setEnabled(True)
        self.status_label.setText(f"전략이 저장되었습니다. ID: {strategy_id}")
    
    def run_backtest(self):
        """백테스팅 실행"""
        if not self.current_strategy_id:
            QMessageBox.warning(self, "경고", "백테스팅을 실행할 전략을 선택하세요.")
            return
        
        reply = QMessageBox.question(
            self,
            "백테스팅 실행",
            f"선택된 전략으로 백테스팅을 실행하시겠습니까?\n\n전략 ID: {self.current_strategy_id}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.backtest_requested.emit(self.current_strategy_id)
            self.status_label.setText("백테스팅이 실행되었습니다...")
