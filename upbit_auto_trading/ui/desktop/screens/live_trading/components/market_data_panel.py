"""
시장 데이터 패널 컴포넌트
- 실시간 오더북 (호가창)
- 시장 정보 표시
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QFrame, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

class MarketDataPanel(QWidget):
    """시장 데이터 패널 - 오더북 및 시장 정보"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_coin = "BTC-KRW"
        self.init_ui()
        self.setup_timer()
        self.load_sample_data()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel("📈 실시간 오더북")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        layout.addWidget(title_label)
        
        # 현재 코인 및 가격 정보
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        # 코인 정보
        coin_layout = QHBoxLayout()
        self.coin_label = QLabel("BTC-KRW")
        self.coin_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        coin_layout.addWidget(self.coin_label)
        
        coin_layout.addStretch()
        
        self.price_change_label = QLabel("+2.5%")
        self.price_change_label.setStyleSheet("font-size: 12px; color: #28a745; font-weight: bold;")
        coin_layout.addWidget(self.price_change_label)
        
        info_layout.addLayout(coin_layout)
        
        # 현재가 정보
        price_layout = QHBoxLayout()
        self.current_price_label = QLabel("45,000,000")
        self.current_price_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #007bff;")
        price_layout.addWidget(self.current_price_label)
        
        price_layout.addStretch()
        
        self.volume_label = QLabel("거래량: 1,234.56")
        self.volume_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        price_layout.addWidget(self.volume_label)
        
        info_layout.addLayout(price_layout)
        
        layout.addWidget(info_frame)
        
        # 오더북 테이블
        self.orderbook_table = QTableWidget()
        self.setup_orderbook_table()
        layout.addWidget(self.orderbook_table)
    
    def setup_orderbook_table(self):
        """오더북 테이블 설정"""
        # 컬럼 설정: 매도 호가, 매도 잔량, 가격, 매수 잔량, 매수 호가
        columns = ["매도잔량", "가격", "매수잔량"]
        self.orderbook_table.setColumnCount(len(columns))
        self.orderbook_table.setHorizontalHeaderLabels(columns)
        
        # 테이블 속성 설정
        self.orderbook_table.setAlternatingRowColors(False)
        self.orderbook_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.orderbook_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.orderbook_table.setShowGrid(False)
        
        # 헤더 숨기기 (오더북은 보통 헤더 없이 표시)
        self.orderbook_table.verticalHeader().setVisible(False)
        
        # 컬럼 크기 조정
        header = self.orderbook_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 매도잔량
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 가격
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 매수잔량
        
        # 행 개수 설정 (일반적으로 10~20개 호가)
        self.orderbook_table.setRowCount(20)
        
        # 테이블 높이 제한
        self.orderbook_table.setMaximumHeight(400)
    
    def setup_timer(self):
        """실시간 업데이트 타이머"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_orderbook)
        self.update_timer.start(500)  # 0.5초마다 업데이트
    
    def load_sample_data(self):
        """샘플 오더북 데이터 로드 (개발용)"""
        import random
        
        base_price = 45000000  # BTC 기준가
        
        # 매도 호가 (기준가보다 높음, 10개)
        ask_orders = []
        for i in range(10):
            price = base_price + (i + 1) * 10000
            volume = random.uniform(0.1, 5.0)
            ask_orders.append({"price": price, "volume": volume})
        
        # 매수 호가 (기준가보다 낮음, 10개)
        bid_orders = []
        for i in range(10):
            price = base_price - (i + 1) * 10000
            volume = random.uniform(0.1, 5.0)
            bid_orders.append({"price": price, "volume": volume})
        
        self.update_orderbook_data(ask_orders, bid_orders)
    
    def update_orderbook_data(self, ask_orders, bid_orders):
        """오더북 데이터 업데이트"""
        # 매도 호가는 높은 가격부터 (역순)
        ask_orders.reverse()
        
        # 테이블 업데이트
        for i in range(10):
            row = i
            
            # 매도 호가 (상위 10개 행)
            if i < len(ask_orders):
                ask = ask_orders[i]
                
                # 매도 잔량 (빨간색)
                ask_volume_item = QTableWidgetItem(f"{ask['volume']:.4f}")
                ask_volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                ask_volume_item.setBackground(QColor("#ffe6e6"))  # 연한 빨간색 배경
                ask_volume_item.setForeground(QColor("#dc3545"))
                self.orderbook_table.setItem(row, 0, ask_volume_item)
                
                # 가격 (빨간색)
                price_item = QTableWidgetItem(f"{ask['price']:,}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                price_item.setBackground(QColor("#ffe6e6"))
                price_item.setForeground(QColor("#dc3545"))
                price_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                self.orderbook_table.setItem(row, 1, price_item)
                
                # 매수 잔량 (빈 칸)
                empty_item = QTableWidgetItem("")
                empty_item.setBackground(QColor("#ffe6e6"))
                self.orderbook_table.setItem(row, 2, empty_item)
        
        # 매수 호가 (하위 10개 행)
        for i in range(10):
            row = i + 10
            
            if i < len(bid_orders):
                bid = bid_orders[i]
                
                # 매도 잔량 (빈 칸)
                empty_item = QTableWidgetItem("")
                empty_item.setBackground(QColor("#e6f3ff"))
                self.orderbook_table.setItem(row, 0, empty_item)
                
                # 가격 (파란색)
                price_item = QTableWidgetItem(f"{bid['price']:,}")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                price_item.setBackground(QColor("#e6f3ff"))  # 연한 파란색 배경
                price_item.setForeground(QColor("#007bff"))
                price_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                self.orderbook_table.setItem(row, 1, price_item)
                
                # 매수 잔량 (파란색)
                bid_volume_item = QTableWidgetItem(f"{bid['volume']:.4f}")
                bid_volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                bid_volume_item.setBackground(QColor("#e6f3ff"))
                bid_volume_item.setForeground(QColor("#007bff"))
                self.orderbook_table.setItem(row, 2, bid_volume_item)
    
    def update_orderbook(self):
        """실시간 오더북 업데이트"""
        # TODO: 실제 API에서 오더북 데이터 조회
        # 임시로 약간의 변동 시뮬레이션
        import random
        
        # 현재가 약간 변동
        current_price_text = self.current_price_label.text().replace(",", "")
        try:
            current_price = float(current_price_text)
            variation = random.uniform(-0.001, 0.001)  # 0.1% 내외 변동
            new_price = current_price * (1 + variation)
            self.current_price_label.setText(f"{new_price:,.0f}")
            
            # 변동률 색상 업데이트
            if variation >= 0:
                self.price_change_label.setStyleSheet("font-size: 12px; color: #28a745; font-weight: bold;")
                self.price_change_label.setText(f"+{abs(variation)*100:.2f}%")
            else:
                self.price_change_label.setStyleSheet("font-size: 12px; color: #dc3545; font-weight: bold;")
                self.price_change_label.setText(f"-{abs(variation)*100:.2f}%")
                
        except ValueError:
            pass
    
    def set_coin(self, coin_symbol):
        """표시할 코인 변경"""
        self.current_coin = coin_symbol
        self.coin_label.setText(coin_symbol)
        
        # TODO: 해당 코인의 오더북 데이터 조회
        self.load_sample_data()
    
    def refresh_data(self):
        """데이터 새로고침"""
        print(f"[DEBUG] {self.current_coin} 시장 데이터 새로고침")
        self.load_sample_data()
