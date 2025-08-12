"""
거래 마커 모듈

이 모듈은 차트에 거래 시점을 표시하는 마커를 구현합니다.
"""

import pyqtgraph as pg
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF

class TradeMarker(pg.GraphicsObject):
    """거래 마커 클래스"""
    
    def __init__(self, timestamp, price, trade_type="buy", size=10):
        """거래 마커 초기화"""
        super().__init__()
        
        # 데이터 저장
        self.timestamp = timestamp
        self.price = price
        self.trade_type = trade_type.lower()  # "buy" 또는 "sell"
        self.size = size
        
        # 색상 설정
        self.buy_color = QColor(76, 175, 80)  # 매수 색상 (녹색)
        self.sell_color = QColor(244, 67, 54)  # 매도 색상 (적색)
        
        # 그림 생성
        self.picture = None
        self.generatePicture()
    
    def generatePicture(self):
        """마커 그림 생성"""
        # 그림 객체 생성
        self.picture = pg.QtGui.QPicture()
        
        # 페인터 생성
        painter = pg.QtGui.QPainter(self.picture)
        
        # 안티앨리어싱 활성화
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 색상 설정
        color = self.buy_color if self.trade_type == "buy" else self.sell_color
        
        # 마커 그리기
        if self.trade_type == "buy":
            # 매수 마커 (삼각형 - 위쪽 방향)
            painter.setPen(pg.mkPen(color, width=2))
            painter.setBrush(pg.mkBrush(color))
            
            # 삼각형 꼭지점 계산
            half_size = self.size / 2
            
            # 삼각형 그리기
            triangle = QPolygonF([
                QPointF(0, -half_size),  # 상단 꼭지점
                QPointF(-half_size, half_size),  # 좌측 하단 꼭지점
                QPointF(half_size, half_size)  # 우측 하단 꼭지점
            ])
            painter.drawPolygon(triangle)
        else:
            # 매도 마커 (삼각형 - 아래쪽 방향)
            painter.setPen(pg.mkPen(color, width=2))
            painter.setBrush(pg.mkBrush(color))
            
            # 삼각형 꼭지점 계산
            half_size = self.size / 2
            
            # 삼각형 그리기
            triangle = QPolygonF([
                QPointF(0, half_size),  # 하단 꼭지점
                QPointF(-half_size, -half_size),  # 좌측 상단 꼭지점
                QPointF(half_size, -half_size)  # 우측 상단 꼭지점
            ])
            painter.drawPolygon(triangle)
        
        # 페인터 종료
        painter.end()
    
    def paint(self, painter, option, widget):
        """마커 그리기"""
        painter.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        """경계 상자 반환"""
        # 마커 크기에 따른 경계 상자 반환
        half_size = self.size / 2
        return pg.QtCore.QRectF(-half_size, -half_size, self.size, self.size)
    
    def setVisible(self, visible):
        """마커 표시 여부 설정"""
        self.setOpacity(1.0 if visible else 0.0)