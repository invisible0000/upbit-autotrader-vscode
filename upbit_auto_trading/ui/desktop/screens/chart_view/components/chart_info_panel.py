"""
차트 정보 패널 컴포넌트
- 현재 선택된 코인 정보
- 실시간 가격 정보
- 시장 정보 표시
- 상태 정보
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
import datetime

class PriceInfoWidget(QWidget):
    """가격 정보 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_price = 0.0
        self.prev_price = 0.0
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 현재 가격
        self.price_label = QLabel("₩ 0")
        self.price_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.price_label)
        
        # 변화량과 변화율
        change_layout = QHBoxLayout()
        
        self.change_amount_label = QLabel("0")
        self.change_amount_label.setFont(QFont("Arial", 12))
        self.change_amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.change_percent_label = QLabel("(0.00%)")
        self.change_percent_label.setFont(QFont("Arial", 12))
        self.change_percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        change_layout.addWidget(self.change_amount_label)
        change_layout.addWidget(self.change_percent_label)
        layout.addLayout(change_layout)
        
        # 초기 색상 설정
        self.update_color(0)
    
    def update_price(self, current_price, prev_close=None):
        """가격 정보 업데이트"""
        self.prev_price = self.current_price
        self.current_price = current_price
        
        # 가격 표시
        self.price_label.setText(f"₩ {current_price:,.0f}")
        
        if prev_close is not None:
            # 변화량 계산
            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close) * 100 if prev_close > 0 else 0
            
            # 변화량 표시
            self.change_amount_label.setText(f"{change_amount:+,.0f}")
            self.change_percent_label.setText(f"({change_percent:+.2f}%)")
            
            # 색상 업데이트
            self.update_color(change_amount)
    
    def update_color(self, change):
        """가격 변화에 따른 색상 업데이트"""
        if change > 0:
            # 상승 (빨간색)
            color = "#dc3545"
        elif change < 0:
            # 하락 (파란색)
            color = "#007bff"
        else:
            # 보합 (검정색)
            color = "#333333"
        
        self.price_label.setStyleSheet(f"color: {color};")
        self.change_amount_label.setStyleSheet(f"color: {color};")
        self.change_percent_label.setStyleSheet(f"color: {color};")


class MarketInfoWidget(QWidget):
    """시장 정보 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QGridLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 24시간 정보
        self.add_info_item(layout, 0, "24시간 고가", "0", "high_24h")
        self.add_info_item(layout, 1, "24시간 저가", "0", "low_24h")
        self.add_info_item(layout, 2, "24시간 거래량", "0", "volume_24h")
        self.add_info_item(layout, 3, "24시간 거래대금", "0", "trade_value_24h")
        
        # 기타 정보
        self.add_info_item(layout, 4, "전일 종가", "0", "prev_close")
        self.add_info_item(layout, 5, "시가", "0", "open_price")
    
    def add_info_item(self, layout, row, label_text, value_text, attr_name):
        """정보 항목 추가"""
        # 라벨
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 9))
        label.setStyleSheet("color: #666;")
        layout.addWidget(label, row, 0)
        
        # 값
        value_label = QLabel(value_text)
        value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(value_label, row, 1)
        
        # 속성으로 저장
        setattr(self, f"{attr_name}_label", value_label)
    
    def update_market_info(self, market_data):
        """시장 정보 업데이트"""
        if not market_data:
            return
        
        # 24시간 정보
        if "high_price" in market_data:
            self.high_24h_label.setText(f"₩ {float(market_data['high_price']):,.0f}")
        
        if "low_price" in market_data:
            self.low_24h_label.setText(f"₩ {float(market_data['low_price']):,.0f}")
        
        if "acc_trade_volume_24h" in market_data:
            volume = float(market_data['acc_trade_volume_24h'])
            if volume >= 1000000:
                self.volume_24h_label.setText(f"{volume/1000000:.1f}M")
            elif volume >= 1000:
                self.volume_24h_label.setText(f"{volume/1000:.1f}K")
            else:
                self.volume_24h_label.setText(f"{volume:.1f}")
        
        if "acc_trade_price_24h" in market_data:
            trade_value = float(market_data['acc_trade_price_24h'])
            if trade_value >= 1000000000:
                self.trade_value_24h_label.setText(f"₩ {trade_value/1000000000:.1f}B")
            elif trade_value >= 1000000:
                self.trade_value_24h_label.setText(f"₩ {trade_value/1000000:.1f}M")
            else:
                self.trade_value_24h_label.setText(f"₩ {trade_value:,.0f}")
        
        # 기타 정보
        if "prev_closing_price" in market_data:
            self.prev_close_label.setText(f"₩ {float(market_data['prev_closing_price']):,.0f}")
        
        if "opening_price" in market_data:
            self.open_price_label.setText(f"₩ {float(market_data['opening_price']):,.0f}")


class ChartStatusWidget(QWidget):
    """차트 상태 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 연결 상태
        connection_layout = QHBoxLayout()
        self.connection_indicator = QLabel("●")
        self.connection_indicator.setFont(QFont("Arial", 12))
        self.connection_indicator.setStyleSheet("color: #28a745;")  # 녹색 (연결됨)
        
        self.connection_label = QLabel("실시간 연결됨")
        self.connection_label.setFont(QFont("Arial", 9))
        
        connection_layout.addWidget(self.connection_indicator)
        connection_layout.addWidget(self.connection_label)
        connection_layout.addStretch()
        
        layout.addLayout(connection_layout)
        
        # 마지막 업데이트 시간
        self.last_update_label = QLabel("마지막 업데이트: --")
        self.last_update_label.setFont(QFont("Arial", 8))
        self.last_update_label.setStyleSheet("color: #666;")
        layout.addWidget(self.last_update_label)
        
        # 차트 정보
        self.chart_info_label = QLabel("데이터 로딩 중...")
        self.chart_info_label.setFont(QFont("Arial", 8))
        self.chart_info_label.setStyleSheet("color: #666;")
        layout.addWidget(self.chart_info_label)
    
    def update_connection_status(self, connected):
        """연결 상태 업데이트"""
        if connected:
            self.connection_indicator.setStyleSheet("color: #28a745;")  # 녹색
            self.connection_label.setText("실시간 연결됨")
        else:
            self.connection_indicator.setStyleSheet("color: #dc3545;")  # 빨간색
            self.connection_label.setText("연결 끊김")
    
    def update_last_update_time(self):
        """마지막 업데이트 시간 갱신"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.last_update_label.setText(f"마지막 업데이트: {current_time}")
    
    def update_chart_info(self, symbol, timeframe, data_count=0):
        """차트 정보 업데이트"""
        self.chart_info_label.setText(f"{symbol} | {timeframe} | {data_count}개 봉")


class ChartInfoPanel(QWidget):
    """차트 정보 패널"""
    
    # 시그널 정의
    symbol_info_updated = pyqtSignal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_symbol = "BTC-KRW"
        self.current_timeframe = "1d"
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 심볼 정보 헤더
        header_layout = QHBoxLayout()
        
        self.symbol_label = QLabel(self.current_symbol)
        self.symbol_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(self.symbol_label)
        
        self.timeframe_label = QLabel(f"({self.current_timeframe})")
        self.timeframe_label.setFont(QFont("Arial", 12))
        self.timeframe_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.timeframe_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 가격 정보
        self.price_info = PriceInfoWidget()
        layout.addWidget(self.price_info)
        
        # 구분선
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line1)
        
        # 시장 정보
        market_group = QGroupBox("시장 정보")
        market_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
        """)
        market_layout = QVBoxLayout(market_group)
        
        self.market_info = MarketInfoWidget()
        market_layout.addWidget(self.market_info)
        
        layout.addWidget(market_group)
        
        # 구분선
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line2)
        
        # 상태 정보
        status_group = QGroupBox("상태")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """)
        status_layout = QVBoxLayout(status_group)
        
        self.chart_status = ChartStatusWidget()
        status_layout.addWidget(self.chart_status)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
    
    def setup_timer(self):
        """타이머 설정"""
        # 실시간 업데이트를 위한 타이머 (실제 환경에서는 WebSocket 사용)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_realtime_data)
        self.update_timer.start(1000)  # 1초마다 업데이트
    
    def set_symbol_and_timeframe(self, symbol, timeframe):
        """심볼과 시간대 설정"""
        self.current_symbol = symbol
        self.current_timeframe = timeframe
        
        # UI 업데이트
        self.symbol_label.setText(symbol)
        self.timeframe_label.setText(f"({timeframe})")
        
        # 차트 정보 업데이트
        self.chart_status.update_chart_info(symbol, timeframe)
    
    def update_price_data(self, price_data):
        """가격 데이터 업데이트"""
        if not price_data:
            return
        
        current_price = float(price_data.get('trade_price', 0))
        prev_close = float(price_data.get('prev_closing_price', 0))
        
        self.price_info.update_price(current_price, prev_close)
    
    def update_market_data(self, market_data):
        """시장 데이터 업데이트"""
        self.market_info.update_market_info(market_data)
    
    def update_realtime_data(self):
        """실시간 데이터 업데이트 (시뮬레이션)"""
        # 실제 환경에서는 WebSocket이나 API를 통해 실시간 데이터 수신
        self.chart_status.update_last_update_time()
        
        # 연결 상태 시뮬레이션
        import random
        if random.random() > 0.95:  # 5% 확률로 연결 끊김 시뮬레이션
            self.chart_status.update_connection_status(False)
        else:
            self.chart_status.update_connection_status(True)
    
    def set_data_count(self, count):
        """데이터 개수 설정"""
        self.chart_status.update_chart_info(
            self.current_symbol, 
            self.current_timeframe, 
            count
        )
    
    def simulate_price_update(self, base_price=50000000):
        """가격 업데이트 시뮬레이션 (테스트용)"""
        import random
        
        # 가격 변동 시뮬레이션
        change_percent = random.uniform(-0.05, 0.05)  # -5% ~ +5%
        current_price = base_price * (1 + change_percent)
        
        # 시장 데이터 시뮬레이션
        market_data = {
            'trade_price': str(current_price),
            'prev_closing_price': str(base_price),
            'high_price': str(current_price * 1.02),
            'low_price': str(current_price * 0.98),
            'acc_trade_volume_24h': str(random.uniform(1000, 10000)),
            'acc_trade_price_24h': str(random.uniform(1000000000, 10000000000)),
            'opening_price': str(base_price * 0.999)
        }
        
        self.update_price_data(market_data)
        self.update_market_data(market_data)
