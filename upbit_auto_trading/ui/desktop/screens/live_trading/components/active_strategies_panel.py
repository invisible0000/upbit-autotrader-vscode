"""
활성 전략 패널 컴포넌트
- 실시간 전략 현황 모니터링
- 개별 전략 제어
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QFrame,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

class ActiveStrategiesPanel(QWidget):
    """활성 전략 현황 패널"""
    
    # 시그널 정의
    strategy_stop_requested = pyqtSignal(str)  # strategy_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_timer()
        self.load_sample_data()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목 및 상태 표시
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 활성 전략 현황")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 새로고침 버튼
        refresh_button = QPushButton("🔄 새로고침")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)
        
        # 전략 테이블
        self.strategies_table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.strategies_table)
        
        # 하단 요약 정보
        summary_frame = QFrame()
        summary_frame.setFrameStyle(QFrame.Shape.Box)
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        summary_layout = QHBoxLayout(summary_frame)
        
        self.total_profit_label = QLabel("총 평가손익: +0.00%")
        self.total_profit_label.setStyleSheet("font-weight: bold; color: #28a745;")
        summary_layout.addWidget(self.total_profit_label)
        
        summary_layout.addStretch()
        
        self.total_value_label = QLabel("총 평가금액: 0 KRW")
        self.total_value_label.setStyleSheet("font-weight: bold; color: #495057;")
        summary_layout.addWidget(self.total_value_label)
        
        layout.addWidget(summary_frame)
    
    def setup_table(self):
        """테이블 설정"""
        # 컬럼 설정
        columns = [
            "전략명", "코인", "진입가격", "현재가격", "수량", 
            "평가손익", "수익률", "상태", "제어"
        ]
        self.strategies_table.setColumnCount(len(columns))
        self.strategies_table.setHorizontalHeaderLabels(columns)
        
        # 테이블 속성 설정
        self.strategies_table.setAlternatingRowColors(True)
        self.strategies_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.strategies_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # 컬럼 크기 조정
        header = self.strategies_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 전략명
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)     # 코인
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)     # 진입가격
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)     # 현재가격
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)     # 수량
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)     # 평가손익
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)     # 수익률
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)     # 상태
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)     # 제어
        
        # 컬럼 너비 설정
        self.strategies_table.setColumnWidth(1, 80)   # 코인
        self.strategies_table.setColumnWidth(2, 100)  # 진입가격
        self.strategies_table.setColumnWidth(3, 100)  # 현재가격
        self.strategies_table.setColumnWidth(4, 80)   # 수량
        self.strategies_table.setColumnWidth(5, 100)  # 평가손익
        self.strategies_table.setColumnWidth(6, 80)   # 수익률
        self.strategies_table.setColumnWidth(7, 80)   # 상태
        self.strategies_table.setColumnWidth(8, 80)   # 제어
    
    def setup_timer(self):
        """실시간 업데이트 타이머"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_real_time_data)
        self.update_timer.start(1000)  # 1초마다 업데이트
    
    def load_sample_data(self):
        """샘플 데이터 로드 (개발용)"""
        sample_strategies = [
            {
                "id": "strategy_001",
                "name": "BTC 추세 전략",
                "coin": "BTC",
                "entry_price": 45000000,
                "current_price": 46500000,
                "quantity": 0.1,
                "status": "활성"
            },
            {
                "id": "strategy_002", 
                "name": "ETH 스윙 전략",
                "coin": "ETH",
                "entry_price": 2800000,
                "current_price": 2750000,
                "quantity": 2.5,
                "status": "활성"
            }
        ]
        
        self.update_table_data(sample_strategies)
    
    def update_table_data(self, strategies):
        """테이블 데이터 업데이트"""
        self.strategies_table.setRowCount(len(strategies))
        
        for row, strategy in enumerate(strategies):
            # 기본 정보
            self.strategies_table.setItem(row, 0, QTableWidgetItem(strategy["name"]))
            self.strategies_table.setItem(row, 1, QTableWidgetItem(strategy["coin"]))
            self.strategies_table.setItem(row, 2, QTableWidgetItem(f"{strategy['entry_price']:,}"))
            self.strategies_table.setItem(row, 3, QTableWidgetItem(f"{strategy['current_price']:,}"))
            self.strategies_table.setItem(row, 4, QTableWidgetItem(f"{strategy['quantity']}"))
            
            # 손익 계산
            entry_value = strategy["entry_price"] * strategy["quantity"]
            current_value = strategy["current_price"] * strategy["quantity"]
            profit_loss = current_value - entry_value
            profit_rate = (profit_loss / entry_value) * 100
            
            # 평가손익 (색상 적용)
            profit_item = QTableWidgetItem(f"{profit_loss:,.0f}")
            if profit_loss >= 0:
                profit_item.setForeground(QColor("#28a745"))  # 녹색
            else:
                profit_item.setForeground(QColor("#dc3545"))  # 빨간색
            self.strategies_table.setItem(row, 5, profit_item)
            
            # 수익률 (색상 적용)
            rate_item = QTableWidgetItem(f"{profit_rate:+.2f}%")
            if profit_rate >= 0:
                rate_item.setForeground(QColor("#28a745"))
            else:
                rate_item.setForeground(QColor("#dc3545"))
            self.strategies_table.setItem(row, 6, rate_item)
            
            # 상태
            status_item = QTableWidgetItem(strategy["status"])
            if strategy["status"] == "활성":
                status_item.setForeground(QColor("#007bff"))
            self.strategies_table.setItem(row, 7, status_item)
            
            # 제어 버튼
            stop_button = QPushButton("중지")
            stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            stop_button.clicked.connect(lambda checked, sid=strategy["id"]: self.stop_strategy(sid))
            self.strategies_table.setCellWidget(row, 8, stop_button)
    
    def update_real_time_data(self):
        """실시간 데이터 업데이트"""
        # TODO: 실제 API에서 현재가 조회
        # 임시로 랜덤 변동 시뮬레이션
        import random
        
        for row in range(self.strategies_table.rowCount()):
            current_price_item = self.strategies_table.item(row, 3)
            if current_price_item:
                current_price = float(current_price_item.text().replace(",", ""))
                # 0.1% 내외의 랜덤 변동
                variation = random.uniform(-0.001, 0.001)
                new_price = current_price * (1 + variation)
                current_price_item.setText(f"{new_price:,.0f}")
                
                # 손익 재계산
                self.recalculate_profit_loss(row)
    
    def recalculate_profit_loss(self, row):
        """특정 행의 손익 재계산"""
        try:
            entry_price = float(self.strategies_table.item(row, 2).text().replace(",", ""))
            current_price = float(self.strategies_table.item(row, 3).text().replace(",", ""))
            quantity = float(self.strategies_table.item(row, 4).text())
            
            entry_value = entry_price * quantity
            current_value = current_price * quantity
            profit_loss = current_value - entry_value
            profit_rate = (profit_loss / entry_value) * 100
            
            # 평가손익 업데이트
            profit_item = self.strategies_table.item(row, 5)
            profit_item.setText(f"{profit_loss:,.0f}")
            if profit_loss >= 0:
                profit_item.setForeground(QColor("#28a745"))
            else:
                profit_item.setForeground(QColor("#dc3545"))
            
            # 수익률 업데이트
            rate_item = self.strategies_table.item(row, 6)
            rate_item.setText(f"{profit_rate:+.2f}%")
            if profit_rate >= 0:
                rate_item.setForeground(QColor("#28a745"))
            else:
                rate_item.setForeground(QColor("#dc3545"))
                
        except (ValueError, AttributeError):
            pass
    
    def stop_strategy(self, strategy_id):
        """개별 전략 중지"""
        reply = QMessageBox.question(
            self,
            "전략 중지",
            f"전략 '{strategy_id}'을(를) 중지하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.strategy_stop_requested.emit(strategy_id)
            print(f"[DEBUG] 전략 {strategy_id} 중지 요청")
    
    def stop_all_strategies(self):
        """모든 전략 중지"""
        print("[DEBUG] 모든 전략 중지")
        # TODO: 실제 구현
    
    def refresh_data(self):
        """데이터 새로고침"""
        print("[DEBUG] 활성 전략 데이터 새로고침")
        # TODO: 실제 API에서 데이터 조회
        self.load_sample_data()
