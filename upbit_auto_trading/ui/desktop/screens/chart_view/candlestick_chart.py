"""
캔들스틱 차트 모듈

이 모듈은 PyQtGraph를 사용하여 캔들스틱 차트를 구현합니다.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

import pyqtgraph as pg
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class CandlestickItem(pg.GraphicsObject):
    """캔들스틱 아이템 클래스"""
    
    def __init__(self, data):
        """캔들스틱 아이템 초기화"""
        super().__init__()
        
        # 데이터 저장
        self.data = data
        
        # 색상 설정
        self.bull_color = QColor(76, 175, 80)  # 상승봉 색상 (녹색)
        self.bear_color = QColor(244, 67, 54)  # 하락봉 색상 (적색)
        
        # 경계 상자 생성
        self.picture = None
        self.generatePicture()
    
    def generatePicture(self):
        """캔들스틱 그림 생성"""
        # 그림 객체 생성
        self.picture = pg.QtGui.QPicture()
        
        # 페인터 생성
        painter = pg.QtGui.QPainter(self.picture)
        
        # 안티앨리어싱 활성화
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 데이터 순회
        for i in range(len(self.data)):
            # 캔들 데이터 추출
            t = i  # x 좌표 (인덱스)
            open_price = self.data['open'].iloc[i]
            high_price = self.data['high'].iloc[i]
            low_price = self.data['low'].iloc[i]
            close_price = self.data['close'].iloc[i]
            
            # 상승/하락 여부 확인
            is_bull = close_price >= open_price
            
            # 색상 설정
            color = self.bull_color if is_bull else self.bear_color
            
            # 캔들 몸통 그리기
            painter.setPen(pg.mkPen(color))
            painter.setBrush(pg.mkBrush(color))
            
            # 캔들 몸통 너비 설정 (0.8은 캔들 사이 간격을 위한 값)
            rect_width = 0.8
            
            # 캔들 몸통 그리기
            rect = QRectF(
                t - rect_width/2,
                min(open_price, close_price),
                rect_width,
                abs(close_price - open_price)
            )
            painter.drawRect(rect)
            
            # 캔들 심지 그리기
            painter.setPen(pg.mkPen(color, width=1))
            
            # 상단 심지
            painter.drawLine(
                pg.QtCore.QPointF(t, high_price),
                pg.QtCore.QPointF(t, max(open_price, close_price))
            )
            
            # 하단 심지
            painter.drawLine(
                pg.QtCore.QPointF(t, min(open_price, close_price)),
                pg.QtCore.QPointF(t, low_price)
            )
        
        # 페인터 종료
        painter.end()
    
    def paint(self, painter, option, widget):
        """캔들스틱 그리기"""
        painter.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        """경계 상자 반환"""
        # 데이터가 없는 경우 기본 경계 상자 반환
        if len(self.data) == 0:
            return QRectF(0, 0, 1, 1)
        
        # 데이터 범위 계산
        min_x = 0
        max_x = len(self.data)
        min_y = self.data['low'].min()
        max_y = self.data['high'].max()
        
        # 여백 추가
        margin = (max_y - min_y) * 0.1
        
        # 경계 상자 반환
        return QRectF(min_x - 1, min_y - margin, max_x + 1, (max_y - min_y) + 2 * margin)


class CandlestickChart(pg.PlotWidget):
    """캔들스틱 차트 클래스"""
    
    def __init__(self, parent=None):
        """캔들스틱 차트 초기화"""
        super().__init__(parent)
        
        # 데이터 초기화
        self.data = None
        self.candlesticks = None
        self.indicator_overlays = {}
        self.trade_markers = []
        
        # 뷰 범위 초기화
        self.view_range = [0, 100, 0, 100]  # [xMin, xMax, yMin, yMax]
        
        # 차트 설정
        self._setup_chart()
    
    def _setup_chart(self):
        """차트 설정"""
        # 배경색 설정
        self.setBackground('w')
        
        # 그리드 설정
        self.showGrid(x=True, y=True, alpha=0.3)
        
        # 십자선 설정
        self.crosshair = pg.CrosshairROI((0, 0), size=(0, 0), movable=False)
        self.addItem(self.crosshair)
        self.crosshair.setZValue(1000)  # 최상위 레이어에 표시
        
        # 마우스 이벤트 연결
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)
        
        # 축 설정
        self.getAxis('bottom').setLabel('시간')
        self.getAxis('left').setLabel('가격')
        
        # 뷰박스 설정
        self.setMouseEnabled(x=True, y=True)  # 마우스로 확대/축소 및 이동 가능
        self.enableAutoRange(False)  # 자동 범위 조정 비활성화
        
        # 범례 설정
        self.legend = self.addLegend()
    
    def update_data(self, data):
        """데이터 업데이트"""
        # 데이터 저장
        self.data = data
        
        # 기존 캔들스틱 제거
        if self.candlesticks is not None:
            self.removeItem(self.candlesticks)
        
        # 새 캔들스틱 생성
        self.candlesticks = CandlestickItem(data)
        self.addItem(self.candlesticks)
        
        # 뷰 범위 설정
        self._update_view_range()
        
        # 날짜 축 설정
        self._setup_date_axis()
        
        # 기존 지표 오버레이 업데이트
        for indicator_id, overlay in self.indicator_overlays.items():
            self.removeItem(overlay)
        
        self.indicator_overlays = {}
    
    def _update_view_range(self):
        """뷰 범위 업데이트"""
        if self.data is None or len(self.data) == 0:
            return
        
        # 데이터 범위 계산
        min_x = 0
        max_x = len(self.data) - 1
        min_y = self.data['low'].min()
        max_y = self.data['high'].max()
        
        # 여백 추가
        y_margin = (max_y - min_y) * 0.1
        
        # 뷰 범위 설정
        self.view_range = [min_x, max_x, min_y - y_margin, max_y + y_margin]
        self.setXRange(min_x, max_x)
        self.setYRange(min_y - y_margin, max_y + y_margin)
    
    def _setup_date_axis(self):
        """날짜 축 설정"""
        if self.data is None or len(self.data) == 0:
            return
        
        # 날짜 문자열 변환 함수
        def timestamp_to_str(x):
            if x < 0 or x >= len(self.data):
                return ""
            
            # 인덱스를 정수로 변환
            idx = int(x)
            if idx >= len(self.data):
                idx = len(self.data) - 1
            
            # 날짜 포맷팅
            date = self.data.index[idx]
            return date.strftime('%Y-%m-%d')
        
        # 축 설정
        axis = self.getAxis('bottom')
        axis.setTicks([[(i, timestamp_to_str(i)) for i in range(0, len(self.data), max(1, len(self.data) // 10))]])
    
    def _on_mouse_moved(self, pos):
        """마우스 이동 이벤트 처리"""
        # 뷰포트 좌표로 변환
        view_pos = self.getViewBox().mapSceneToView(pos)
        
        # 십자선 위치 업데이트
        self.crosshair.setPos((view_pos.x(), view_pos.y()))
    
    def add_indicator_overlay(self, indicator_id, indicator_data):
        """지표 오버레이 추가"""
        if self.data is None or len(self.data) == 0:
            return
        
        # 지표 유형 확인
        if indicator_id.startswith("SMA") or indicator_id.startswith("EMA"):
            # 이동 평균선
            data = indicator_data[indicator_id]
            
            # 색상 설정
            if indicator_id.startswith("SMA"):
                color = (0, 0, 255)  # 파란색
            else:
                color = (255, 165, 0)  # 주황색
            
            # 선 그리기
            overlay = self.plot(
                x=range(len(data)),
                y=data.values,
                pen=pg.mkPen(color=color, width=2),
                name=indicator_id
            )
            
            # 오버레이 저장
            self.indicator_overlays[indicator_id] = overlay
        
        elif indicator_id.startswith("BBANDS"):
            # 볼린저 밴드
            upper = indicator_data[f"{indicator_id}_upper"]
            middle = indicator_data[f"{indicator_id}_middle"]
            lower = indicator_data[f"{indicator_id}_lower"]
            
            # 상단 밴드
            upper_overlay = self.plot(
                x=range(len(upper)),
                y=upper.values,
                pen=pg.mkPen(color=(255, 0, 0), width=1),
                name=f"{indicator_id} 상단"
            )
            
            # 중간 밴드
            middle_overlay = self.plot(
                x=range(len(middle)),
                y=middle.values,
                pen=pg.mkPen(color=(0, 0, 255), width=1),
                name=f"{indicator_id} 중간"
            )
            
            # 하단 밴드
            lower_overlay = self.plot(
                x=range(len(lower)),
                y=lower.values,
                pen=pg.mkPen(color=(255, 0, 0), width=1),
                name=f"{indicator_id} 하단"
            )
            
            # 밴드 영역 채우기
            fill = pg.FillBetweenItem(
                upper_overlay,
                lower_overlay,
                brush=pg.mkBrush(color=(255, 0, 0, 50))
            )
            self.addItem(fill)
            
            # 오버레이 저장
            self.indicator_overlays[f"{indicator_id}_upper"] = upper_overlay
            self.indicator_overlays[f"{indicator_id}_middle"] = middle_overlay
            self.indicator_overlays[f"{indicator_id}_lower"] = lower_overlay
            self.indicator_overlays[f"{indicator_id}_fill"] = fill
        
        elif indicator_id.startswith("RSI"):
            # RSI (별도의 플롯 영역에 표시)
            data = indicator_data[indicator_id]
            
            # 새 플롯 영역 생성
            rsi_plot = self.scene().addPlot(row=1, col=0)
            rsi_plot.setMaximumHeight(100)
            rsi_plot.setXLink(self)  # x축 연결
            
            # RSI 선 그리기
            rsi_line = rsi_plot.plot(
                x=range(len(data)),
                y=data.values,
                pen=pg.mkPen(color=(128, 0, 128), width=2),
                name=indicator_id
            )
            
            # 과매수/과매도 영역 표시
            rsi_plot.addLine(y=70, pen=pg.mkPen(color=(255, 0, 0), style=Qt.PenStyle.DashLine))
            rsi_plot.addLine(y=30, pen=pg.mkPen(color=(0, 255, 0), style=Qt.PenStyle.DashLine))
            
            # 축 설정
            rsi_plot.setYRange(0, 100)
            rsi_plot.getAxis('left').setLabel('RSI')
            
            # 오버레이 저장
            self.indicator_overlays[indicator_id] = rsi_plot
        
        elif indicator_id.startswith("MACD"):
            # MACD (별도의 플롯 영역에 표시)
            macd_line = indicator_data[f"{indicator_id}_line"]
            signal_line = indicator_data[f"{indicator_id}_signal"]
            histogram = indicator_data[f"{indicator_id}_histogram"]
            
            # 새 플롯 영역 생성
            macd_plot = self.scene().addPlot(row=2, col=0)
            macd_plot.setMaximumHeight(100)
            macd_plot.setXLink(self)  # x축 연결
            
            # MACD 선 그리기
            macd_line_plot = macd_plot.plot(
                x=range(len(macd_line)),
                y=macd_line.values,
                pen=pg.mkPen(color=(0, 0, 255), width=2),
                name=f"{indicator_id} MACD"
            )
            
            # 시그널 선 그리기
            signal_line_plot = macd_plot.plot(
                x=range(len(signal_line)),
                y=signal_line.values,
                pen=pg.mkPen(color=(255, 165, 0), width=2),
                name=f"{indicator_id} Signal"
            )
            
            # 히스토그램 그리기
            bar_width = 0.8
            for i in range(len(histogram)):
                if i >= len(histogram):
                    continue
                
                value = histogram.iloc[i]
                color = (0, 255, 0) if value >= 0 else (255, 0, 0)
                
                bar = pg.BarGraphItem(
                    x=[i],
                    height=[value],
                    width=bar_width,
                    brush=pg.mkBrush(color=color)
                )
                macd_plot.addItem(bar)
            
            # 축 설정
            macd_plot.getAxis('left').setLabel('MACD')
            
            # 오버레이 저장
            self.indicator_overlays[f"{indicator_id}_plot"] = macd_plot
            self.indicator_overlays[f"{indicator_id}_line"] = macd_line_plot
            self.indicator_overlays[f"{indicator_id}_signal"] = signal_line_plot
        
        elif indicator_id.startswith("Stochastic"):
            # 스토캐스틱 (별도의 플롯 영역에 표시)
            k_line = indicator_data[f"{indicator_id}_k"]
            d_line = indicator_data[f"{indicator_id}_d"]
            
            # 새 플롯 영역 생성
            stoch_plot = self.scene().addPlot(row=3, col=0)
            stoch_plot.setMaximumHeight(100)
            stoch_plot.setXLink(self)  # x축 연결
            
            # %K 선 그리기
            k_line_plot = stoch_plot.plot(
                x=range(len(k_line)),
                y=k_line.values,
                pen=pg.mkPen(color=(0, 0, 255), width=2),
                name=f"{indicator_id} %K"
            )
            
            # %D 선 그리기
            d_line_plot = stoch_plot.plot(
                x=range(len(d_line)),
                y=d_line.values,
                pen=pg.mkPen(color=(255, 165, 0), width=2),
                name=f"{indicator_id} %D"
            )
            
            # 과매수/과매도 영역 표시
            stoch_plot.addLine(y=80, pen=pg.mkPen(color=(255, 0, 0), style=Qt.PenStyle.DashLine))
            stoch_plot.addLine(y=20, pen=pg.mkPen(color=(0, 255, 0), style=Qt.PenStyle.DashLine))
            
            # 축 설정
            stoch_plot.setYRange(0, 100)
            stoch_plot.getAxis('left').setLabel('Stochastic')
            
            # 오버레이 저장
            self.indicator_overlays[f"{indicator_id}_plot"] = stoch_plot
            self.indicator_overlays[f"{indicator_id}_k"] = k_line_plot
            self.indicator_overlays[f"{indicator_id}_d"] = d_line_plot
    
    def remove_indicator_overlay(self, indicator_id):
        """지표 오버레이 제거"""
        # 지표 유형 확인
        if indicator_id.startswith("BBANDS"):
            # 볼린저 밴드
            self.removeItem(self.indicator_overlays.get(f"{indicator_id}_upper"))
            self.removeItem(self.indicator_overlays.get(f"{indicator_id}_middle"))
            self.removeItem(self.indicator_overlays.get(f"{indicator_id}_lower"))
            self.removeItem(self.indicator_overlays.get(f"{indicator_id}_fill"))
            
            # 오버레이 삭제
            self.indicator_overlays.pop(f"{indicator_id}_upper", None)
            self.indicator_overlays.pop(f"{indicator_id}_middle", None)
            self.indicator_overlays.pop(f"{indicator_id}_lower", None)
            self.indicator_overlays.pop(f"{indicator_id}_fill", None)
        
        elif indicator_id.startswith("RSI"):
            # RSI
            rsi_plot = self.indicator_overlays.get(indicator_id)
            if rsi_plot:
                self.scene().removeItem(rsi_plot)
            
            # 오버레이 삭제
            self.indicator_overlays.pop(indicator_id, None)
        
        elif indicator_id.startswith("MACD"):
            # MACD
            macd_plot = self.indicator_overlays.get(f"{indicator_id}_plot")
            if macd_plot:
                self.scene().removeItem(macd_plot)
            
            # 오버레이 삭제
            self.indicator_overlays.pop(f"{indicator_id}_plot", None)
            self.indicator_overlays.pop(f"{indicator_id}_line", None)
            self.indicator_overlays.pop(f"{indicator_id}_signal", None)
        
        elif indicator_id.startswith("Stochastic"):
            # 스토캐스틱
            stoch_plot = self.indicator_overlays.get(f"{indicator_id}_plot")
            if stoch_plot:
                self.scene().removeItem(stoch_plot)
            
            # 오버레이 삭제
            self.indicator_overlays.pop(f"{indicator_id}_plot", None)
            self.indicator_overlays.pop(f"{indicator_id}_k", None)
            self.indicator_overlays.pop(f"{indicator_id}_d", None)
        
        else:
            # 일반 지표
            overlay = self.indicator_overlays.get(indicator_id)
            if overlay:
                self.removeItem(overlay)
            
            # 오버레이 삭제
            self.indicator_overlays.pop(indicator_id, None)
    
    def add_trade_marker(self, marker):
        """거래 마커 추가"""
        if self.data is None or len(self.data) == 0:
            return
        
        # 마커 타임스탬프에 해당하는 인덱스 찾기
        timestamp = marker.timestamp
        
        # 가장 가까운 인덱스 찾기
        closest_idx = 0
        min_diff = float('inf')
        
        for i, date in enumerate(self.data.index):
            diff = abs((date - timestamp).total_seconds())
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
        
        # 마커 위치 설정
        marker.setPos(closest_idx, marker.price)
        
        # 마커 추가
        self.addItem(marker)
        
        # 마커 목록에 추가
        self.trade_markers.append(marker)
    
    def remove_trade_marker(self, marker):
        """거래 마커 제거"""
        # 마커 제거
        self.removeItem(marker)
        
        # 마커 목록에서 제거
        if marker in self.trade_markers:
            self.trade_markers.remove(marker)
    
    def zoom_in(self):
        """확대"""
        # 현재 뷰 범위 가져오기
        x_min, x_max = self.getViewBox().viewRange()[0]
        y_min, y_max = self.getViewBox().viewRange()[1]
        
        # 중심점 계산
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        
        # 범위 축소 (확대)
        x_range = (x_max - x_min) * 0.8
        y_range = (y_max - y_min) * 0.8
        
        # 새 범위 설정
        self.setXRange(x_center - x_range/2, x_center + x_range/2)
        self.setYRange(y_center - y_range/2, y_center + y_range/2)
        
        # 뷰 범위 업데이트
        self.view_range = [x_center - x_range/2, x_center + x_range/2, y_center - y_range/2, y_center + y_range/2]
    
    def zoom_out(self):
        """축소"""
        # 현재 뷰 범위 가져오기
        x_min, x_max = self.getViewBox().viewRange()[0]
        y_min, y_max = self.getViewBox().viewRange()[1]
        
        # 중심점 계산
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        
        # 범위 확대 (축소)
        x_range = (x_max - x_min) * 1.25
        y_range = (y_max - y_min) * 1.25
        
        # 새 범위 설정
        self.setXRange(x_center - x_range/2, x_center + x_range/2)
        self.setYRange(y_center - y_range/2, y_center + y_range/2)
        
        # 뷰 범위 업데이트
        self.view_range = [x_center - x_range/2, x_center + x_range/2, y_center - y_range/2, y_center + y_range/2]
    
    def save_image(self, file_path):
        """차트 이미지 저장"""
        # 이미지로 내보내기
        exporter = pg.exporters.ImageExporter(self.plotItem)
        exporter.export(file_path)