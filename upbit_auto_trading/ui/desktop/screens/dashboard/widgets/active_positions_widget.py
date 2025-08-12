"""
활성 거래 목록 위젯 모듈

이 모듈은 활성 거래 목록 위젯을 구현합니다.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QIcon

class ActivePositionsWidget(QWidget):
    """
    활성 거래 목록 위젯
    
    현재 진입해 있는 모든 포지션의 상세 내역을 테이블 형태로 표시합니다.
    """
    
    # 포지션 청산 시그널
    position_closed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        초기화
        
        Args:
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        self.setObjectName("widget-active-positions")
        self.setMinimumHeight(250)
        
        # 스타일 설정
        self.setStyleSheet("""
            QLabel#widget-title {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            QTableWidget {
                border: none;
            }
            
            QTableWidget::item {
                padding: 5px;
            }
            
            QPushButton#close-position-button {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 3px;
                border-radius: 3px;
            }
            
            QPushButton#close-position-button:hover {
                background-color: #c0392b;
            }
        """)
        
        # 샘플 데이터 (실제로는 API에서 가져와야 함)
        self.positions_data = [
            {
                "id": "pos-001",
                "symbol": "BTC",
                "name": "비트코인",
                "entry_time": "2025-07-18 09:30:00",
                "entry_price": 50000000,
                "current_price": 51000000,
                "quantity": 0.01,
                "profit_loss": 2.0,
                "profit_loss_amount": 100000
            },
            {
                "id": "pos-002",
                "symbol": "ETH",
                "name": "이더리움",
                "entry_time": "2025-07-18 10:15:00",
                "entry_price": 3000000,
                "current_price": 2940000,
                "quantity": 0.1,
                "profit_loss": -2.0,
                "profit_loss_amount": -60000
            },
            {
                "id": "pos-003",
                "symbol": "XRP",
                "name": "리플",
                "entry_time": "2025-07-18 11:00:00",
                "entry_price": 500,
                "current_price": 520,
                "quantity": 1000,
                "profit_loss": 4.0,
                "profit_loss_amount": 20000
            }
        ]
        
        # UI 설정
        self._setup_ui()
    
    def _setup_ui(self):
        """UI 설정"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 헤더 레이아웃
        header_layout = QHBoxLayout()
        
        # 위젯 제목
        title_label = QLabel("활성 거래 목록")
        title_label.setObjectName("widget-title")
        header_layout.addWidget(title_label)
        
        # 여백 추가
        header_layout.addStretch()
        
        # 새로고침 버튼
        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # 거래 목록 테이블
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "코인", "진입 시간", "진입가", "현재가", "수량", "평가손익(%)", "평가손익(KRW)", "청산"
        ])
        
        # 테이블 설정
        self.positions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.positions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.positions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.positions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.positions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.positions_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.positions_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.positions_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.positions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.positions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.positions_table.verticalHeader().setVisible(False)
        self.positions_table.setAlternatingRowColors(True)
        
        main_layout.addWidget(self.positions_table)
        
        # 초기 데이터 로드
        self.refresh_data()
    
    def refresh_data(self):
        """데이터 새로고침"""
        try:
            # 실제 구현에서는 API를 통해 데이터를 가져와야 함
            # 여기서는 샘플 데이터 사용
            
            # 테이블 업데이트
            self._update_table()
        except Exception as e:
            print(f"활성 거래 목록 위젯 데이터 새로고침 중 오류 발생: {e}")
    
    def _update_table(self):
        """테이블 업데이트"""
        self.positions_table.setRowCount(0)
        
        for position in self.positions_data:
            row_position = self.positions_table.rowCount()
            self.positions_table.insertRow(row_position)
            
            # 코인명
            coin_item = QTableWidgetItem(f"{position['name']} ({position['symbol']})")
            self.positions_table.setItem(row_position, 0, coin_item)
            
            # 진입 시간
            entry_time_item = QTableWidgetItem(position["entry_time"])
            self.positions_table.setItem(row_position, 1, entry_time_item)
            
            # 진입가
            entry_price_item = QTableWidgetItem(f"{position['entry_price']:,}")
            entry_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.positions_table.setItem(row_position, 2, entry_price_item)
            
            # 현재가
            current_price_item = QTableWidgetItem(f"{position['current_price']:,}")
            current_price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.positions_table.setItem(row_position, 3, current_price_item)
            
            # 수량
            quantity_item = QTableWidgetItem(f"{position['quantity']}")
            quantity_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.positions_table.setItem(row_position, 4, quantity_item)
            
            # 평가손익(%)
            profit_loss_item = QTableWidgetItem(f"{position['profit_loss']:+.2f}%")
            profit_loss_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # 수익/손실에 따라 색상 설정
            if position["profit_loss"] > 0:
                profit_loss_item.setForeground(QBrush(QColor("#27ae60")))  # 녹색
            elif position["profit_loss"] < 0:
                profit_loss_item.setForeground(QBrush(QColor("#e74c3c")))  # 붉은색
            
            self.positions_table.setItem(row_position, 5, profit_loss_item)
            
            # 평가손익(KRW)
            profit_loss_amount_item = QTableWidgetItem(f"{position['profit_loss_amount']:+,}")
            profit_loss_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # 수익/손실에 따라 색상 설정
            if position["profit_loss_amount"] > 0:
                profit_loss_amount_item.setForeground(QBrush(QColor("#27ae60")))  # 녹색
            elif position["profit_loss_amount"] < 0:
                profit_loss_amount_item.setForeground(QBrush(QColor("#e74c3c")))  # 붉은색
            
            self.positions_table.setItem(row_position, 6, profit_loss_amount_item)
            
            # 청산 버튼
            close_button = QPushButton("청산")
            close_button.setObjectName("close-position-button")
            close_button.setProperty("position_id", position["id"])
            close_button.clicked.connect(lambda checked, pid=position["id"]: self._confirm_close_position(pid))
            self.positions_table.setCellWidget(row_position, 7, close_button)
    
    def _confirm_close_position(self, position_id):
        """
        포지션 청산 확인
        
        Args:
            position_id (str): 포지션 ID
        """
        # 확인 대화상자 표시
        reply = QMessageBox.question(
            self,
            "포지션 청산 확인",
            "정말 이 포지션을 청산하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 실제 구현에서는 API를 통해 포지션 청산 요청을 보내야 함
            print(f"포지션 청산: {position_id}")
            
            # 시그널 발생
            self.position_closed.emit(position_id)
            
            # 데이터 새로고침
            # 실제 구현에서는 포지션 목록에서 해당 포지션을 제거하고 테이블을 업데이트해야 함
            self.positions_data = [p for p in self.positions_data if p["id"] != position_id]
            self.refresh_data()