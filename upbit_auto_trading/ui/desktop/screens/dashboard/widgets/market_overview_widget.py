"""
시장 개요 위젯 모듈

이 모듈은 시장 개요 위젯을 구현합니다.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush

class MarketOverviewWidget(QWidget):
    """
    시장 개요 위젯
    
    주기적으로 수집된 대표 코인들의 시세(Ticker) 정보를 표시합니다.
    """
    
    # 코인 선택 시그널
    coin_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """
        초기화
        
        Args:
            parent (QWidget, optional): 부모 위젯
        """
        super().__init__(parent)
        self.setObjectName("widget-market-overview")
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
        """)
        
        # 샘플 데이터 (실제로는 API에서 가져와야 함)
        self.market_data = [
            {
                "symbol": "BTC",
                "name": "비트코인",
                "current_price": 51000000,
                "change_24h": 2.5,
                "volume_24h": 1500000000000
            },
            {
                "symbol": "ETH",
                "name": "이더리움",
                "current_price": 2940000,
                "change_24h": -1.8,
                "volume_24h": 800000000000
            },
            {
                "symbol": "XRP",
                "name": "리플",
                "current_price": 520,
                "change_24h": 3.2,
                "volume_24h": 300000000000
            },
            {
                "symbol": "ADA",
                "name": "에이다",
                "current_price": 450,
                "change_24h": 1.5,
                "volume_24h": 150000000000
            },
            {
                "symbol": "SOL",
                "name": "솔라나",
                "current_price": 120000,
                "change_24h": -0.8,
                "volume_24h": 200000000000
            },
            {
                "symbol": "DOT",
                "name": "폴카닷",
                "current_price": 15000,
                "change_24h": 0.5,
                "volume_24h": 80000000000
            },
            {
                "symbol": "DOGE",
                "name": "도지코인",
                "current_price": 100,
                "change_24h": -2.3,
                "volume_24h": 120000000000
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
        title_label = QLabel("시장 개요")
        title_label.setObjectName("widget-title")
        header_layout.addWidget(title_label)
        
        # 여백 추가
        header_layout.addStretch()
        
        # 새로고침 버튼
        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # 시장 개요 테이블
        self.market_table = QTableWidget()
        self.market_table.setColumnCount(5)
        self.market_table.setHorizontalHeaderLabels([
            "코인", "현재가(KRW)", "24시간 변동(%)", "24시간 거래대금(KRW)", "차트"
        ])
        
        # 테이블 설정
        self.market_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.market_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.market_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.market_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.market_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.market_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.market_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.market_table.verticalHeader().setVisible(False)
        self.market_table.setAlternatingRowColors(True)
        self.market_table.itemDoubleClicked.connect(self._on_table_item_double_clicked)
        
        main_layout.addWidget(self.market_table)
        
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
            print(f"시장 개요 위젯 데이터 새로고침 중 오류 발생: {e}")
    
    def _update_table(self):
        """테이블 업데이트"""
        self.market_table.setRowCount(0)
        
        for market in self.market_data:
            row_position = self.market_table.rowCount()
            self.market_table.insertRow(row_position)
            
            # 코인명
            coin_item = QTableWidgetItem(f"{market['name']} ({market['symbol']})")
            self.market_table.setItem(row_position, 0, coin_item)
            
            # 현재가
            price_item = QTableWidgetItem(f"{market['current_price']:,}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.market_table.setItem(row_position, 1, price_item)
            
            # 24시간 변동
            change_item = QTableWidgetItem(f"{market['change_24h']:+.2f}%")
            change_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # 상승/하락에 따라 색상 설정
            if market["change_24h"] > 0:
                change_item.setForeground(QBrush(QColor("#27ae60")))  # 녹색
            elif market["change_24h"] < 0:
                change_item.setForeground(QBrush(QColor("#e74c3c")))  # 붉은색
            
            self.market_table.setItem(row_position, 2, change_item)
            
            # 24시간 거래대금
            volume_item = QTableWidgetItem(f"{market['volume_24h']:,.0f}")
            volume_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.market_table.setItem(row_position, 3, volume_item)
            
            # 차트 버튼
            chart_button = QPushButton("차트 보기")
            chart_button.clicked.connect(lambda checked, symbol=market["symbol"]: self._view_chart(symbol))
            self.market_table.setCellWidget(row_position, 4, chart_button)
    
    def _view_chart(self, symbol):
        """
        차트 보기
        
        Args:
            symbol (str): 코인 심볼
        """
        # 코인 선택 시그널 발생
        self.coin_selected.emit(symbol)
    
    def _on_table_item_double_clicked(self, item):
        """
        테이블 항목 더블 클릭 이벤트 핸들러
        
        Args:
            item (QTableWidgetItem): 클릭된 항목
        """
        row = item.row()
        symbol = self.market_data[row]["symbol"]
        self.coin_selected.emit(symbol)