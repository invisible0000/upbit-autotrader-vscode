"""
전략 목록을 표시하는 위젯
- 기존 전략 목록 표시
- 새 전략 생성 버튼
- 전략 선택/삭제 기능
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import pyqtSignal

class StrategyListWidget(QWidget):
    # 시그널 정의
    strategy_selected = pyqtSignal(str)  # 전략 ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 새 전략 생성 버튼
        self.create_btn = QPushButton("새 전략 생성 +")
        self.create_btn.clicked.connect(self.create_new_strategy)
        layout.addWidget(self.create_btn)
        
        # 전략 목록 테이블
        self.table = QTableWidget(0, 3)  # 행은 0개로 시작, 열은 3개
        self.table.setHorizontalHeaderLabels(["전략명", "유형", "승률"])
        self.table.cellClicked.connect(self.on_strategy_selected)
        layout.addWidget(self.table)
        
        # 초기 데이터 로드
        self.refresh_list()
    
    def refresh_list(self):
        """전략 목록 새로고침"""
        # TODO: DB에서 전략 목록 조회
        self.table.clearContents()
        self.table.setRowCount(0)
        
        # 테스트용 더미 데이터
        dummy_data = [
            ("골든크로스 전략", "이동평균", "67%"),
            ("RSI 반등", "기술적지표", "72%"),
            ("변동성 돌파", "가격변동", "65%")
        ]
        
        for row, (name, type_, winrate) in enumerate(dummy_data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(type_))
            self.table.setItem(row, 2, QTableWidgetItem(winrate))
    
    def create_new_strategy(self):
        """새 전략 생성"""
        # TODO: 새 전략 생성 로직
        print("[DEBUG] 새 전략 생성 요청")
        self.strategy_selected.emit("new")
    
    def on_strategy_selected(self, row, col):
        """전략 선택 시"""
        strategy_name = self.table.item(row, 0).text()
        # TODO: 실제 전략 ID로 변경
        self.strategy_selected.emit(f"strategy_{row}")
