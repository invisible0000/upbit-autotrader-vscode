"""
거래 내역 패널 컴포넌트
- 미체결 주문 목록
- 최근 체결 내역
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QTabWidget, QHeaderView, QAbstractItemView,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

class TradeHistoryPanel(QWidget):
    """거래 내역 패널"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_timer()
        self.load_sample_data()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel("📋 거래 내역")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        layout.addWidget(title_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        
        # 미체결 주문 탭
        self.pending_orders_widget = QWidget()
        self.setup_pending_orders_tab()
        self.tab_widget.addTab(self.pending_orders_widget, "미체결 주문")
        
        # 체결 내역 탭
        self.completed_orders_widget = QWidget()
        self.setup_completed_orders_tab()
        self.tab_widget.addTab(self.completed_orders_widget, "체결 내역")
        
        layout.addWidget(self.tab_widget)
    
    def setup_pending_orders_tab(self):
        """미체결 주문 탭 설정"""
        layout = QVBoxLayout(self.pending_orders_widget)
        
        # 상단 정보
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        info_layout = QHBoxLayout(info_frame)
        
        self.pending_count_label = QLabel("미체결 주문: 0건")
        self.pending_count_label.setStyleSheet("font-weight: bold; color: #856404;")
        info_layout.addWidget(self.pending_count_label)
        
        info_layout.addStretch()
        
        # 전체 취소 버튼
        cancel_all_button = QPushButton("전체 취소")
        cancel_all_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        cancel_all_button.clicked.connect(self.cancel_all_orders)
        info_layout.addWidget(cancel_all_button)
        
        layout.addWidget(info_frame)
        
        # 미체결 주문 테이블
        self.pending_table = QTableWidget()
        self.setup_pending_table()
        layout.addWidget(self.pending_table)
    
    def setup_completed_orders_tab(self):
        """체결 내역 탭 설정"""
        layout = QVBoxLayout(self.completed_orders_widget)
        
        # 상단 정보
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #d1ecf1;
                border: 1px solid #bee5eb;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        info_layout = QHBoxLayout(info_frame)
        
        self.completed_count_label = QLabel("오늘 체결: 0건")
        self.completed_count_label.setStyleSheet("font-weight: bold; color: #0c5460;")
        info_layout.addWidget(self.completed_count_label)
        
        info_layout.addStretch()
        
        # 새로고침 버튼
        refresh_button = QPushButton("새로고침")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        refresh_button.clicked.connect(self.refresh_data)
        info_layout.addWidget(refresh_button)
        
        layout.addWidget(info_frame)
        
        # 체결 내역 테이블
        self.completed_table = QTableWidget()
        self.setup_completed_table()
        layout.addWidget(self.completed_table)
    
    def setup_pending_table(self):
        """미체결 주문 테이블 설정"""
        columns = ["시간", "코인", "구분", "주문가격", "수량", "상태", "취소"]
        self.pending_table.setColumnCount(len(columns))
        self.pending_table.setHorizontalHeaderLabels(columns)
        
        # 테이블 속성
        self.pending_table.setAlternatingRowColors(True)
        self.pending_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.pending_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # 컬럼 크기 조정
        header = self.pending_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)     # 시간
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)     # 코인
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)     # 구분
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)   # 주문가격
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)     # 수량
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)     # 상태
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)     # 취소
        
        self.pending_table.setColumnWidth(0, 80)   # 시간
        self.pending_table.setColumnWidth(1, 80)   # 코인
        self.pending_table.setColumnWidth(2, 60)   # 구분
        self.pending_table.setColumnWidth(4, 80)   # 수량
        self.pending_table.setColumnWidth(5, 60)   # 상태
        self.pending_table.setColumnWidth(6, 60)   # 취소
    
    def setup_completed_table(self):
        """체결 내역 테이블 설정"""
        columns = ["시간", "코인", "구분", "체결가격", "체결수량", "수수료", "상세"]
        self.completed_table.setColumnCount(len(columns))
        self.completed_table.setHorizontalHeaderLabels(columns)
        
        # 테이블 속성
        self.completed_table.setAlternatingRowColors(True)
        self.completed_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.completed_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # 컬럼 크기 조정
        header = self.completed_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)     # 시간
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)     # 코인
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)     # 구분
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)   # 체결가격
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)     # 체결수량
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)     # 수수료
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)     # 상세
        
        self.completed_table.setColumnWidth(0, 80)   # 시간
        self.completed_table.setColumnWidth(1, 80)   # 코인
        self.completed_table.setColumnWidth(2, 60)   # 구분
        self.completed_table.setColumnWidth(4, 80)   # 체결수량
        self.completed_table.setColumnWidth(5, 80)   # 수수료
        self.completed_table.setColumnWidth(6, 60)   # 상세
    
    def setup_timer(self):
        """실시간 업데이트 타이머"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(5000)  # 5초마다 업데이트
    
    def load_sample_data(self):
        """샘플 데이터 로드 (개발용)"""
        # 미체결 주문 샘플
        pending_orders = [
            {
                "time": "14:30:25",
                "coin": "BTC",
                "side": "매수",
                "price": 44500000,
                "quantity": 0.1,
                "status": "대기",
                "uuid": "order_001"
            },
            {
                "time": "14:25:10",
                "coin": "ETH", 
                "side": "매도",
                "price": 2850000,
                "quantity": 1.5,
                "status": "대기",
                "uuid": "order_002"
            }
        ]
        
        # 체결 내역 샘플
        completed_orders = [
            {
                "time": "14:20:45",
                "coin": "BTC",
                "side": "매수",
                "price": 45000000,
                "quantity": 0.05,
                "fee": 11250
            },
            {
                "time": "13:45:20",
                "coin": "ETH",
                "side": "매도",
                "price": 2800000,
                "quantity": 2.0,
                "fee": 2800
            }
        ]
        
        self.update_pending_orders(pending_orders)
        self.update_completed_orders(completed_orders)
    
    def update_pending_orders(self, orders):
        """미체결 주문 업데이트"""
        self.pending_table.setRowCount(len(orders))
        self.pending_count_label.setText(f"미체결 주문: {len(orders)}건")
        
        for row, order in enumerate(orders):
            self.pending_table.setItem(row, 0, QTableWidgetItem(order["time"]))
            self.pending_table.setItem(row, 1, QTableWidgetItem(order["coin"]))
            
            # 구분 (매수/매도 색상)
            side_item = QTableWidgetItem(order["side"])
            if order["side"] == "매수":
                side_item.setForeground(QColor("#dc3545"))
            else:
                side_item.setForeground(QColor("#007bff"))
            self.pending_table.setItem(row, 2, side_item)
            
            self.pending_table.setItem(row, 3, QTableWidgetItem(f"{order['price']:,}"))
            self.pending_table.setItem(row, 4, QTableWidgetItem(f"{order['quantity']}"))
            self.pending_table.setItem(row, 5, QTableWidgetItem(order["status"]))
            
            # 취소 버튼
            cancel_button = QPushButton("취소")
            cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 3px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            cancel_button.clicked.connect(lambda checked, uuid=order["uuid"]: self.cancel_order(uuid))
            self.pending_table.setCellWidget(row, 6, cancel_button)
    
    def update_completed_orders(self, orders):
        """체결 내역 업데이트"""
        self.completed_table.setRowCount(len(orders))
        self.completed_count_label.setText(f"오늘 체결: {len(orders)}건")
        
        for row, order in enumerate(orders):
            self.completed_table.setItem(row, 0, QTableWidgetItem(order["time"]))
            self.completed_table.setItem(row, 1, QTableWidgetItem(order["coin"]))
            
            # 구분 (매수/매도 색상)
            side_item = QTableWidgetItem(order["side"])
            if order["side"] == "매수":
                side_item.setForeground(QColor("#dc3545"))
            else:
                side_item.setForeground(QColor("#007bff"))
            self.completed_table.setItem(row, 2, side_item)
            
            self.completed_table.setItem(row, 3, QTableWidgetItem(f"{order['price']:,}"))
            self.completed_table.setItem(row, 4, QTableWidgetItem(f"{order['quantity']}"))
            self.completed_table.setItem(row, 5, QTableWidgetItem(f"{order['fee']:,}"))
            
            # 상세 버튼
            detail_button = QPushButton("상세")
            detail_button.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 3px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            detail_button.clicked.connect(lambda checked, o=order: self.show_order_detail(o))
            self.completed_table.setCellWidget(row, 6, detail_button)
    
    def cancel_order(self, order_uuid):
        """주문 취소"""
        reply = QMessageBox.question(
            self,
            "주문 취소",
            f"주문 {order_uuid}을(를) 취소하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            print(f"[DEBUG] 주문 취소: {order_uuid}")
            # TODO: 실제 API 호출
            QMessageBox.information(self, "취소 완료", "주문이 취소되었습니다.")
            self.refresh_data()
    
    def cancel_all_orders(self):
        """전체 주문 취소"""
        if self.pending_table.rowCount() == 0:
            QMessageBox.information(self, "알림", "취소할 주문이 없습니다.")
            return
        
        reply = QMessageBox.question(
            self,
            "전체 주문 취소",
            "모든 미체결 주문을 취소하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            print("[DEBUG] 전체 주문 취소")
            # TODO: 실제 API 호출
            QMessageBox.information(self, "취소 완료", "모든 주문이 취소되었습니다.")
            self.refresh_data()
    
    def show_order_detail(self, order):
        """주문 상세 정보 표시"""
        detail_message = f"""주문 상세 정보:

시간: {order['time']}
코인: {order['coin']}
구분: {order['side']}
체결가격: {order['price']:,} KRW
체결수량: {order['quantity']}
수수료: {order['fee']:,} KRW
총 체결금액: {order['price'] * order['quantity']:,.0f} KRW"""
        
        QMessageBox.information(self, "주문 상세 정보", detail_message)
    
    def update_data(self):
        """실시간 데이터 업데이트"""
        # TODO: 실제 API에서 데이터 조회
        pass
    
    def refresh_data(self):
        """데이터 새로고침"""
        print("[DEBUG] 거래 내역 데이터 새로고침")
        # TODO: 실제 API에서 데이터 조회
        self.load_sample_data()
