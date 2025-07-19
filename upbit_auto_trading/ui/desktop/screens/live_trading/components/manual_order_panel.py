"""
수동 주문 패널 컴포넌트
- 수동 매수/매도 주문
- 주문 유형 선택
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QFrame, QGroupBox, QSpinBox,
    QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette

class ManualOrderPanel(QWidget):
    """수동 주문 패널"""
    
    # 시그널 정의
    order_placed = pyqtSignal(dict)  # 주문 정보
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title_label = QLabel("💰 수동 주문")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #495057;")
        layout.addWidget(title_label)
        
        # 주문 패널 그룹
        order_group = QGroupBox("주문 입력")
        order_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        order_layout = QVBoxLayout(order_group)
        
        # 코인 선택
        coin_layout = QHBoxLayout()
        coin_layout.addWidget(QLabel("코인:"))
        self.coin_combo = QComboBox()
        self.coin_combo.addItems(["BTC-KRW", "ETH-KRW", "ADA-KRW", "DOT-KRW", "SOL-KRW"])
        self.coin_combo.currentTextChanged.connect(self.on_coin_changed)
        coin_layout.addWidget(self.coin_combo)
        coin_layout.addStretch()
        order_layout.addLayout(coin_layout)
        
        # 현재 가격 표시
        self.current_price_label = QLabel("현재가: --")
        self.current_price_label.setStyleSheet("color: #007bff; font-weight: bold;")
        order_layout.addWidget(self.current_price_label)
        
        # 주문 유형
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("주문 유형:"))
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["지정가", "시장가"])
        self.order_type_combo.currentTextChanged.connect(self.on_order_type_changed)
        type_layout.addWidget(self.order_type_combo)
        type_layout.addStretch()
        order_layout.addLayout(type_layout)
        
        # 주문 가격 (지정가인 경우만)
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("주문 가격:"))
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("KRW")
        self.price_input.textChanged.connect(self.calculate_total)
        price_layout.addWidget(self.price_input)
        order_layout.addLayout(price_layout)
        
        # 수량 입력
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("수량:"))
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setDecimals(8)
        self.quantity_input.setMaximum(999999.99999999)
        self.quantity_input.valueChanged.connect(self.calculate_total)
        quantity_layout.addWidget(self.quantity_input)
        order_layout.addLayout(quantity_layout)
        
        # 예상 체결 금액
        self.total_label = QLabel("예상 체결 금액: 0 KRW")
        self.total_label.setStyleSheet("color: #28a745; font-weight: bold;")
        order_layout.addWidget(self.total_label)
        
        # 매수/매도 버튼
        buttons_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("매수")
        self.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.buy_button.clicked.connect(lambda: self.place_order("buy"))
        buttons_layout.addWidget(self.buy_button)
        
        self.sell_button = QPushButton("매도")
        self.sell_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.sell_button.clicked.connect(lambda: self.place_order("sell"))
        buttons_layout.addWidget(self.sell_button)
        
        order_layout.addLayout(buttons_layout)
        layout.addWidget(order_group)
        
        # 계좌 잔고 정보
        balance_group = QGroupBox("잔고 정보")
        balance_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        balance_layout = QVBoxLayout(balance_group)
        
        self.krw_balance_label = QLabel("KRW 잔고: 0")
        self.krw_balance_label.setStyleSheet("color: #495057;")
        balance_layout.addWidget(self.krw_balance_label)
        
        self.coin_balance_label = QLabel("코인 잔고: 0")
        self.coin_balance_label.setStyleSheet("color: #495057;")
        balance_layout.addWidget(self.coin_balance_label)
        
        layout.addWidget(balance_group)
        
        # 스페이서
        layout.addStretch()
        
        # 초기 설정
        self.on_coin_changed()
        self.on_order_type_changed()
    
    def on_coin_changed(self):
        """코인 변경 시 처리"""
        selected_coin = self.coin_combo.currentText()
        print(f"[DEBUG] 선택된 코인: {selected_coin}")
        
        # TODO: 실제 현재가 조회
        # 임시 가격 설정
        sample_prices = {
            "BTC-KRW": 45000000,
            "ETH-KRW": 2800000,
            "ADA-KRW": 500,
            "DOT-KRW": 8000,
            "SOL-KRW": 120000
        }
        
        current_price = sample_prices.get(selected_coin, 0)
        self.current_price_label.setText(f"현재가: {current_price:,} KRW")
        self.price_input.setText(str(current_price))
        
        # 코인 잔고 업데이트 (임시)
        coin_symbol = selected_coin.split("-")[0]
        self.coin_balance_label.setText(f"{coin_symbol} 잔고: 0.00000000")
        
        self.calculate_total()
    
    def on_order_type_changed(self):
        """주문 유형 변경 시 처리"""
        order_type = self.order_type_combo.currentText()
        
        if order_type == "시장가":
            self.price_input.setEnabled(False)
            self.price_input.setPlaceholderText("시장가 (자동)")
        else:
            self.price_input.setEnabled(True)
            self.price_input.setPlaceholderText("KRW")
        
        self.calculate_total()
    
    def calculate_total(self):
        """예상 체결 금액 계산"""
        try:
            price_text = self.price_input.text().replace(",", "")
            if not price_text:
                price = 0
            else:
                price = float(price_text)
            
            quantity = self.quantity_input.value()
            total = price * quantity
            
            self.total_label.setText(f"예상 체결 금액: {total:,.0f} KRW")
            
            # 버튼 활성화/비활성화
            valid_order = price > 0 and quantity > 0
            self.buy_button.setEnabled(valid_order)
            self.sell_button.setEnabled(valid_order)
            
        except ValueError:
            self.total_label.setText("예상 체결 금액: 0 KRW")
            self.buy_button.setEnabled(False)
            self.sell_button.setEnabled(False)
    
    def place_order(self, side):
        """주문 실행"""
        try:
            coin = self.coin_combo.currentText()
            order_type = self.order_type_combo.currentText()
            price = float(self.price_input.text().replace(",", "")) if self.price_input.text() else 0
            quantity = self.quantity_input.value()
            
            if quantity <= 0:
                QMessageBox.warning(self, "주문 오류", "수량을 입력해주세요.")
                return
            
            if order_type == "지정가" and price <= 0:
                QMessageBox.warning(self, "주문 오류", "주문 가격을 입력해주세요.")
                return
            
            # 주문 확인 대화상자
            order_info = {
                "side": "매수" if side == "buy" else "매도",
                "coin": coin,
                "type": order_type,
                "price": price,
                "quantity": quantity,
                "total": price * quantity
            }
            
            message = f"""주문 내용을 확인해주세요:

코인: {order_info['coin']}
주문 유형: {order_info['type']}
주문 구분: {order_info['side']}
수량: {order_info['quantity']}
{f"가격: {order_info['price']:,} KRW" if order_type == "지정가" else ""}
예상 체결 금액: {order_info['total']:,.0f} KRW

주문을 실행하시겠습니까?"""
            
            reply = QMessageBox.question(
                self,
                "주문 확인",
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.execute_order(order_info)
                
        except ValueError:
            QMessageBox.warning(self, "주문 오류", "올바른 값을 입력해주세요.")
    
    def execute_order(self, order_info):
        """실제 주문 실행"""
        print(f"[DEBUG] 주문 실행: {order_info}")
        
        # TODO: 실제 API 호출
        # result = upbit_api.place_order(...)
        
        # 성공 메시지
        QMessageBox.information(
            self,
            "주문 완료",
            f"주문이 성공적으로 접수되었습니다.\n\n"
            f"코인: {order_info['coin']}\n"
            f"구분: {order_info['side']}\n"
            f"수량: {order_info['quantity']}"
        )
        
        # 입력 필드 초기화
        self.quantity_input.setValue(0)
        self.calculate_total()
        
        # 주문 완료 시그널 발송
        self.order_placed.emit(order_info)
    
    def update_balance(self, krw_balance, coin_balances):
        """잔고 정보 업데이트"""
        self.krw_balance_label.setText(f"KRW 잔고: {krw_balance:,}")
        
        selected_coin = self.coin_combo.currentText().split("-")[0]
        coin_balance = coin_balances.get(selected_coin, 0)
        self.coin_balance_label.setText(f"{selected_coin} 잔고: {coin_balance}")
