"""
포트폴리오 요약 위젯 모듈

이 모듈은 포트폴리오 요약 위젯을 구현합니다.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush

# 차트 라이브러리 임포트
import pyqtgraph as pg
import numpy as np

class PortfolioSummaryWidget(QWidget):
    """
    포트폴리오 요약 위젯
    
    보유 자산의 구성을 보여주는 도넛 차트와 목록을 표시합니다.
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
        self.setObjectName("widget-portfolio-summary")
        self.setMinimumHeight(300)
        
        # 스타일 설정
        self.setStyleSheet("""
            QLabel#widget-title {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            }
            
            QTableWidget {
                border: none;
                background-color: transparent;
            }
            
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        # 샘플 데이터 (실제로는 API에서 가져와야 함)
        self.portfolio_data = [
            {"symbol": "BTC", "name": "비트코인", "weight": 45.0, "color": "#F7931A"},
            {"symbol": "ETH", "name": "이더리움", "weight": 30.0, "color": "#627EEA"},
            {"symbol": "XRP", "name": "리플", "weight": 15.0, "color": "#23292F"},
            {"symbol": "ADA", "name": "에이다", "weight": 5.0, "color": "#3CC8C8"},
            {"symbol": "SOL", "name": "솔라나", "weight": 5.0, "color": "#00FFA3"}
        ]
        
        # UI 설정
        self._setup_ui()
    
    def _setup_ui(self):
        """UI 설정"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 위젯 제목
        title_label = QLabel("포트폴리오 요약")
        title_label.setObjectName("widget-title")
        main_layout.addWidget(title_label)
        
        # 내용 레이아웃
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 10, 0, 0)
        
        # 도넛 차트 영역
        self.chart_widget = pg.PlotWidget()
        self.chart_widget.setBackground('w')
        self.chart_widget.setAspectLocked(True)
        self.chart_widget.hideAxis('left')
        self.chart_widget.hideAxis('bottom')
        content_layout.addWidget(self.chart_widget, 1)
        
        # 포트폴리오 목록 영역
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(3)
        self.portfolio_table.setHorizontalHeaderLabels(["코인", "심볼", "비중(%)"])
        self.portfolio_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.portfolio_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.portfolio_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.portfolio_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.portfolio_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.portfolio_table.verticalHeader().setVisible(False)
        self.portfolio_table.setAlternatingRowColors(True)
        self.portfolio_table.itemClicked.connect(self._on_table_item_clicked)
        content_layout.addWidget(self.portfolio_table, 1)
        
        # 메인 레이아웃에 추가
        main_layout.addLayout(content_layout)
        
        # 초기 데이터 로드
        self.refresh_data()
    
    def refresh_data(self):
        """데이터 새로고침"""
        try:
            # 실제 구현에서는 API를 통해 데이터를 가져와야 함
            # 여기서는 샘플 데이터 사용
            
            # 도넛 차트 업데이트
            self._update_chart()
            
            # 테이블 업데이트
            self._update_table()
        except Exception as e:
            print(f"포트폴리오 요약 위젯 데이터 새로고침 중 오류 발생: {e}")
    
    def _update_chart(self):
        """도넛 차트 업데이트"""
        self.chart_widget.clear()
        
        # 도넛 차트 데이터 준비
        weights = [item["weight"] for item in self.portfolio_data]
        colors = [item["color"] for item in self.portfolio_data]
        
        # 파이 차트 그리기
        total = sum(weights)
        start_angle = 0
        
        for i, (weight, color) in enumerate(zip(weights, colors)):
            angle = weight / total * 360
            
            # 파이 조각 그리기
            pie = pg.QtWidgets.QGraphicsEllipseItem(-100, -100, 200, 200)
            pie.setStartAngle(int(start_angle * 16))  # QPainter는 1/16도 단위 사용
            pie.setSpanAngle(int(angle * 16))
            pie.setBrush(pg.mkBrush(color))
            pie.setPen(pg.mkPen(None))
            self.chart_widget.addItem(pie)
            
            start_angle += angle
        
        # 중앙 원 그리기 (도넛 효과)
        center = pg.QtWidgets.QGraphicsEllipseItem(-60, -60, 120, 120)
        center.setBrush(pg.mkBrush('w'))
        center.setPen(pg.mkPen(None))
        self.chart_widget.addItem(center)
    
    def _update_table(self):
        """테이블 업데이트"""
        self.portfolio_table.setRowCount(0)
        
        for i, item in enumerate(self.portfolio_data):
            row_position = self.portfolio_table.rowCount()
            self.portfolio_table.insertRow(row_position)
            
            # 코인명
            name_item = QTableWidgetItem(item["name"])
            self.portfolio_table.setItem(row_position, 0, name_item)
            
            # 심볼
            symbol_item = QTableWidgetItem(item["symbol"])
            self.portfolio_table.setItem(row_position, 1, symbol_item)
            
            # 비중
            weight_item = QTableWidgetItem(f"{item['weight']:.1f}%")
            weight_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.portfolio_table.setItem(row_position, 2, weight_item)
            
            # 색상 표시
            color = QColor(item["color"])
            for col in range(3):
                self.portfolio_table.item(row_position, col).setBackground(QBrush(color.lighter(180)))
    
    def _on_table_item_clicked(self, item):
        """
        테이블 항목 클릭 이벤트 핸들러
        
        Args:
            item (QTableWidgetItem): 클릭된 항목
        """
        row = item.row()
        symbol = self.portfolio_table.item(row, 1).text()
        self.coin_selected.emit(symbol)