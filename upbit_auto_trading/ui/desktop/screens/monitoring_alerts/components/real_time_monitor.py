"""
실시간 모니터링 위젯
- 실시간 시장 데이터 표시
- 선택 종목 모니터링
- 미니 차트 표시
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QFrame, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressBar, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor
import random
import datetime

class RealTimeMonitorWidget(QWidget):
    """실시간 모니터링 위젯"""
    
    # 시그널 정의
    price_changed = pyqtSignal(str, float)  # 코인, 가격
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_coins = ["BTC-KRW", "ETH-KRW", "ADA-KRW"]
        self.price_data = {}
        self.init_ui()
        self.start_real_time_updates()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 상단: 주요 지수 모니터
        top_layout = QHBoxLayout()
        
        # 시장 개요
        market_overview = self.create_market_overview()
        top_layout.addWidget(market_overview, stretch=2)
        
        # 선택 종목 모니터
        selected_monitor = self.create_selected_coins_monitor()
        top_layout.addWidget(selected_monitor, stretch=3)
        
        layout.addLayout(top_layout)
        
        # 하단: 상세 모니터링 테이블
        monitoring_table = self.create_monitoring_table()
        layout.addWidget(monitoring_table)
    
    def create_market_overview(self):
        """시장 개요 위젯 생성"""
        group = QGroupBox("📈 시장 개요")
        group.setStyleSheet("""
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
        
        layout = QVBoxLayout(group)
        
        # 시장 상태 표시
        self.market_status_label = QLabel("🟢 시장 개장")
        self.market_status_label.setStyleSheet("font-size: 14px; color: #28a745; font-weight: bold;")
        layout.addWidget(self.market_status_label)
        
        # 업비트 총 거래량
        self.total_volume_label = QLabel("총 거래량: 0 KRW")
        self.total_volume_label.setStyleSheet("font-size: 12px; color: #495057;")
        layout.addWidget(self.total_volume_label)
        
        # 활성 종목 수
        self.active_coins_label = QLabel("활성 종목: 0개")
        self.active_coins_label.setStyleSheet("font-size: 12px; color: #495057;")
        layout.addWidget(self.active_coins_label)
        
        # 24시간 변화율 요약
        summary_frame = QFrame()
        summary_frame.setFrameStyle(QFrame.Shape.Box)
        summary_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: #f8f9fa;
                padding: 8px;
            }
        """)
        summary_layout = QVBoxLayout(summary_frame)
        
        self.rising_count_label = QLabel("상승: 0개")
        self.rising_count_label.setStyleSheet("font-size: 11px; color: #dc3545;")
        summary_layout.addWidget(self.rising_count_label)
        
        self.falling_count_label = QLabel("하락: 0개") 
        self.falling_count_label.setStyleSheet("font-size: 11px; color: #007bff;")
        summary_layout.addWidget(self.falling_count_label)
        
        self.unchanged_count_label = QLabel("보합: 0개")
        self.unchanged_count_label.setStyleSheet("font-size: 11px; color: #6c757d;")
        summary_layout.addWidget(self.unchanged_count_label)
        
        layout.addWidget(summary_frame)
        layout.addStretch()
        
        return group
    
    def create_selected_coins_monitor(self):
        """선택 종목 모니터 위젯 생성"""
        group = QGroupBox("⭐ 관심 종목 모니터")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # 종목 선택 영역
        selection_layout = QHBoxLayout()
        
        selection_layout.addWidget(QLabel("모니터링 종목:"))
        
        self.coin_selector = QComboBox()
        self.coin_selector.addItems([
            "BTC-KRW", "ETH-KRW", "ADA-KRW", "DOT-KRW", "SOL-KRW",
            "MATIC-KRW", "AVAX-KRW", "ATOM-KRW"
        ])
        self.coin_selector.currentTextChanged.connect(self.add_monitoring_coin)
        selection_layout.addWidget(self.coin_selector)
        
        add_btn = QPushButton("추가")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_btn.clicked.connect(self.add_selected_coin)
        selection_layout.addWidget(add_btn)
        
        selection_layout.addStretch()
        layout.addLayout(selection_layout)
        
        # 선택된 종목들의 실시간 정보
        self.selected_coins_grid = QGridLayout()
        layout.addLayout(self.selected_coins_grid)
        
        # 초기 종목들 표시
        self.update_selected_coins_display()
        
        return group
    
    def create_monitoring_table(self):
        """모니터링 테이블 생성"""
        group = QGroupBox("📊 실시간 시세 모니터")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # 테이블 생성
        self.monitoring_table = QTableWidget()
        self.monitoring_table.setColumnCount(7)
        self.monitoring_table.setHorizontalHeaderLabels([
            "코인", "현재가", "전일대비", "변화율", "거래량", "거래대금", "상태"
        ])
        
        # 테이블 스타일
        self.monitoring_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                gridline-color: #e9ecef;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
        """)
        
        # 테이블 설정
        header = self.monitoring_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)    # 코인
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # 현재가
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # 전일대비
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # 변화율
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # 거래량
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # 거래대금
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)    # 상태
            
            self.monitoring_table.setColumnWidth(0, 100)  # 코인
            self.monitoring_table.setColumnWidth(1, 120)  # 현재가
            self.monitoring_table.setColumnWidth(2, 100)  # 전일대비
            self.monitoring_table.setColumnWidth(3, 80)   # 변화율
            self.monitoring_table.setColumnWidth(6, 80)   # 상태
        
        self.monitoring_table.setAlternatingRowColors(True)
        self.monitoring_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.monitoring_table)
        
        # 초기 데이터 로드
        self.load_monitoring_data()
        
        return group
    
    def update_selected_coins_display(self):
        """선택된 종목 표시 업데이트"""
        # 기존 위젯들 제거
        for i in reversed(range(self.selected_coins_grid.count())):
            child = self.selected_coins_grid.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 선택된 종목들 표시
        for i, coin in enumerate(self.selected_coins):
            coin_widget = self.create_coin_monitor_widget(coin)
            row = i // 3
            col = i % 3
            self.selected_coins_grid.addWidget(coin_widget, row, col)
    
    def create_coin_monitor_widget(self, coin):
        """개별 코인 모니터 위젯 생성"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        
        # 코인명
        coin_label = QLabel(coin)
        coin_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        layout.addWidget(coin_label)
        
        # 가격 정보
        price = self.get_mock_price(coin)
        price_label = QLabel(f"{price:,} KRW")
        price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007bff;")
        layout.addWidget(price_label)
        
        # 변화율
        change_rate = random.uniform(-5, 5)
        color = "#dc3545" if change_rate >= 0 else "#007bff"
        sign = "+" if change_rate >= 0 else ""
        change_label = QLabel(f"{sign}{change_rate:.2f}%")
        change_label.setStyleSheet(f"font-size: 12px; color: {color};")
        layout.addWidget(change_label)
        
        # 미니 차트 (간단한 표시)
        chart_widget = MiniChartWidget(coin)
        chart_widget.setFixedHeight(50)
        layout.addWidget(chart_widget)
        
        # 제거 버튼
        remove_btn = QPushButton("제거")
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_monitoring_coin(coin))
        layout.addWidget(remove_btn)
        
        return widget
    
    def add_selected_coin(self):
        """선택된 코인 추가"""
        coin = self.coin_selector.currentText()
        if coin not in self.selected_coins:
            self.selected_coins.append(coin)
            self.update_selected_coins_display()
    
    def remove_monitoring_coin(self, coin):
        """모니터링 코인 제거"""
        if coin in self.selected_coins:
            self.selected_coins.remove(coin)
            self.update_selected_coins_display()
    
    def load_monitoring_data(self):
        """모니터링 테이블 데이터 로드"""
        coins = [
            "BTC-KRW", "ETH-KRW", "ADA-KRW", "DOT-KRW", "SOL-KRW",
            "MATIC-KRW", "AVAX-KRW", "ATOM-KRW", "LINK-KRW", "XRP-KRW"
        ]
        
        self.monitoring_table.setRowCount(len(coins))
        
        for row, coin in enumerate(coins):
            # 코인명
            self.monitoring_table.setItem(row, 0, QTableWidgetItem(coin))
            
            # 현재가
            price = self.get_mock_price(coin)
            price_item = QTableWidgetItem(f"{price:,}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.monitoring_table.setItem(row, 1, price_item)
            
            # 전일대비
            price_diff = random.randint(-1000000, 1000000)
            diff_item = QTableWidgetItem(f"{price_diff:+,}")
            diff_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            color = "#dc3545" if price_diff >= 0 else "#007bff"
            diff_item.setForeground(QColor(color))
            self.monitoring_table.setItem(row, 2, diff_item)
            
            # 변화율
            change_rate = random.uniform(-10, 10)
            change_item = QTableWidgetItem(f"{change_rate:+.2f}%")
            change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            color = "#dc3545" if change_rate >= 0 else "#007bff"
            change_item.setForeground(QColor(color))
            self.monitoring_table.setItem(row, 3, change_item)
            
            # 거래량
            volume = random.randint(1000000, 100000000)
            volume_item = QTableWidgetItem(f"{volume:,}")
            volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.monitoring_table.setItem(row, 4, volume_item)
            
            # 거래대금
            trade_value = price * volume
            value_item = QTableWidgetItem(f"{trade_value/1000000:.1f}M")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.monitoring_table.setItem(row, 5, value_item)
            
            # 상태
            status = random.choice(["정상", "주의", "활발"])
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if status == "정상":
                status_item.setForeground(QColor("#28a745"))
            elif status == "주의":
                status_item.setForeground(QColor("#ffc107"))
            else:
                status_item.setForeground(QColor("#dc3545"))
            self.monitoring_table.setItem(row, 6, status_item)
    
    def start_real_time_updates(self):
        """실시간 업데이트 시작"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_real_time_data)
        self.update_timer.start(3000)  # 3초마다 업데이트
        
        # 시장 상태 업데이트
        self.market_timer = QTimer()
        self.market_timer.timeout.connect(self.update_market_overview)
        self.market_timer.start(5000)  # 5초마다 업데이트
    
    def update_real_time_data(self):
        """실시간 데이터 업데이트"""
        # 모니터링 테이블 업데이트
        for row in range(self.monitoring_table.rowCount()):
            coin_item = self.monitoring_table.item(row, 0)
            if coin_item:
                coin = coin_item.text()
                new_price = self.get_mock_price(coin, fluctuate=True)
                
                # 가격 업데이트
                price_item = self.monitoring_table.item(row, 1)
                if price_item:
                    price_item.setText(f"{new_price:,}")
                
                # 가격 변경 시그널 발송
                self.price_changed.emit(coin, new_price)
        
        # 선택된 종목 모니터 업데이트
        self.update_selected_coins_display()
    
    def update_market_overview(self):
        """시장 개요 업데이트"""
        # 총 거래량 (임시 데이터)
        total_volume = random.randint(500000000000, 2000000000000)
        self.total_volume_label.setText(f"총 거래량: {total_volume/1000000000000:.1f}조 KRW")
        
        # 활성 종목 수
        active_count = random.randint(180, 220)
        self.active_coins_label.setText(f"활성 종목: {active_count}개")
        
        # 상승/하락 종목 수
        rising = random.randint(50, 120)
        falling = random.randint(50, 120)
        unchanged = active_count - rising - falling
        
        self.rising_count_label.setText(f"상승: {rising}개")
        self.falling_count_label.setText(f"하락: {falling}개")
        self.unchanged_count_label.setText(f"보합: {unchanged}개")
    
    def get_mock_price(self, coin, fluctuate=False):
        """모의 가격 데이터 생성"""
        base_prices = {
            "BTC-KRW": 45000000,
            "ETH-KRW": 2800000,
            "ADA-KRW": 500,
            "DOT-KRW": 8000,
            "SOL-KRW": 120000,
            "MATIC-KRW": 1200,
            "AVAX-KRW": 45000,
            "ATOM-KRW": 12000,
            "LINK-KRW": 20000,
            "XRP-KRW": 700
        }
        
        base_price = base_prices.get(coin, 10000)
        
        if fluctuate and coin in self.price_data:
            # 이전 가격에서 약간 변동
            prev_price = self.price_data[coin]
            change_rate = random.uniform(-0.02, 0.02)  # ±2% 변동
            new_price = prev_price * (1 + change_rate)
        else:
            # 기본 가격에서 ±10% 변동
            change_rate = random.uniform(-0.1, 0.1)
            new_price = base_price * (1 + change_rate)
        
        self.price_data[coin] = new_price
        return int(new_price)
    
    def add_monitoring_coin(self, coin):
        """모니터링 코인 추가 (콤보박스에서)"""
        # 콤보박스 선택 변경시 자동으로 호출되지 않도록 방지
        pass

class MiniChartWidget(QWidget):
    """미니 차트 위젯"""
    
    def __init__(self, coin, parent=None):
        super().__init__(parent)
        self.coin = coin
        self.data_points = []
        self.generate_mock_data()
    
    def generate_mock_data(self):
        """모의 차트 데이터 생성"""
        base_value = 100
        for i in range(20):
            change = random.uniform(-5, 5)
            base_value += change
            self.data_points.append(max(50, min(150, base_value)))
    
    def paintEvent(self, event):
        """차트 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.data_points:
            return
        
        # 그리기 영역
        rect = self.rect().adjusted(5, 5, -5, -5)
        width = rect.width()
        height = rect.height()
        
        # 데이터 정규화
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        value_range = max_val - min_val if max_val != min_val else 1
        
        # 선 그리기
        if len(self.data_points) > 1:
            points = []
            for i, value in enumerate(self.data_points):
                x = rect.left() + (i * width / (len(self.data_points) - 1))
                y = rect.bottom() - ((value - min_val) / value_range * height)
                points.append((int(x), int(y)))
            
            # 추세에 따른 색상 결정
            trend_color = "#28a745" if self.data_points[-1] >= self.data_points[0] else "#dc3545"
            
            painter.setPen(QPen(QColor(trend_color), 2))
            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])
