"""
지표 오버레이 모듈

이 모듈은 차트에 기술적 지표를 오버레이하는 기능을 제공합니다.
"""

import pyqtgraph as pg
import pandas as pd
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class IndicatorOverlay:
    """지표 오버레이 클래스"""
    
    @staticmethod
    def create_sma_overlay(chart, data, window, color=None):
        """단순 이동 평균 오버레이 생성"""
        if color is None:
            color = (0, 0, 255)  # 기본 색상: 파란색
        
        # 이동 평균 계산
        sma = data.rolling(window=window).mean()
        
        # 선 그리기
        return chart.plot(
            x=range(len(sma)),
            y=sma.values,
            pen=pg.mkPen(color=color, width=2),
            name=f"SMA({window})"
        )
    
    @staticmethod
    def create_ema_overlay(chart, data, window, color=None):
        """지수 이동 평균 오버레이 생성"""
        if color is None:
            color = (255, 165, 0)  # 기본 색상: 주황색
        
        # 지수 이동 평균 계산
        ema = data.ewm(span=window, adjust=False).mean()
        
        # 선 그리기
        return chart.plot(
            x=range(len(ema)),
            y=ema.values,
            pen=pg.mkPen(color=color, width=2),
            name=f"EMA({window})"
        )
    
    @staticmethod
    def create_bollinger_bands_overlay(chart, data, window=20, num_std=2):
        """볼린저 밴드 오버레이 생성"""
        # 중간 밴드 (SMA)
        middle = data.rolling(window=window).mean()
        
        # 표준 편차
        std = data.rolling(window=window).std()
        
        # 상단 및 하단 밴드
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        
        # 상단 밴드 그리기
        upper_overlay = chart.plot(
            x=range(len(upper)),
            y=upper.values,
            pen=pg.mkPen(color=(255, 0, 0), width=1),
            name=f"BB Upper({window}, {num_std})"
        )
        
        # 중간 밴드 그리기
        middle_overlay = chart.plot(
            x=range(len(middle)),
            y=middle.values,
            pen=pg.mkPen(color=(0, 0, 255), width=1),
            name=f"BB Middle({window})"
        )
        
        # 하단 밴드 그리기
        lower_overlay = chart.plot(
            x=range(len(lower)),
            y=lower.values,
            pen=pg.mkPen(color=(255, 0, 0), width=1),
            name=f"BB Lower({window}, {num_std})"
        )
        
        # 밴드 영역 채우기
        fill = pg.FillBetweenItem(
            upper_overlay,
            lower_overlay,
            brush=pg.mkBrush(color=(255, 0, 0, 50))
        )
        chart.addItem(fill)
        
        return {
            'upper': upper_overlay,
            'middle': middle_overlay,
            'lower': lower_overlay,
            'fill': fill
        }
    
    @staticmethod
    def create_rsi_overlay(chart, data, window=14):
        """RSI 오버레이 생성"""
        # 새 플롯 영역 생성
        rsi_plot = chart.scene().addPlot(row=1, col=0)
        rsi_plot.setMaximumHeight(100)
        rsi_plot.setXLink(chart)  # x축 연결
        
        # 가격 변화
        delta = data.diff()
        
        # 상승/하락 구분
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 평균 상승/하락
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        # 상대 강도
        rs = avg_gain / avg_loss
        
        # RSI 계산
        rsi = 100 - (100 / (1 + rs))
        
        # RSI 선 그리기
        rsi_line = rsi_plot.plot(
            x=range(len(rsi)),
            y=rsi.values,
            pen=pg.mkPen(color=(128, 0, 128), width=2),
            name=f"RSI({window})"
        )
        
        # 과매수/과매도 영역 표시
        rsi_plot.addLine(y=70, pen=pg.mkPen(color=(255, 0, 0), style=Qt.PenStyle.DashLine))
        rsi_plot.addLine(y=30, pen=pg.mkPen(color=(0, 255, 0), style=Qt.PenStyle.DashLine))
        
        # 축 설정
        rsi_plot.setYRange(0, 100)
        rsi_plot.getAxis('left').setLabel('RSI')
        
        return {
            'plot': rsi_plot,
            'line': rsi_line
        }
    
    @staticmethod
    def create_macd_overlay(chart, data, fast=12, slow=26, signal=9):
        """MACD 오버레이 생성"""
        # 새 플롯 영역 생성
        macd_plot = chart.scene().addPlot(row=2, col=0)
        macd_plot.setMaximumHeight(100)
        macd_plot.setXLink(chart)  # x축 연결
        
        # 빠른 EMA
        fast_ema = data.ewm(span=fast, adjust=False).mean()
        
        # 느린 EMA
        slow_ema = data.ewm(span=slow, adjust=False).mean()
        
        # MACD 라인
        macd_line = fast_ema - slow_ema
        
        # 시그널 라인
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        
        # 히스토그램
        histogram = macd_line - signal_line
        
        # MACD 라인 그리기
        macd_line_plot = macd_plot.plot(
            x=range(len(macd_line)),
            y=macd_line.values,
            pen=pg.mkPen(color=(0, 0, 255), width=2),
            name=f"MACD({fast},{slow})"
        )
        
        # 시그널 라인 그리기
        signal_line_plot = macd_plot.plot(
            x=range(len(signal_line)),
            y=signal_line.values,
            pen=pg.mkPen(color=(255, 165, 0), width=2),
            name=f"Signal({signal})"
        )
        
        # 히스토그램 그리기
        bar_items = []
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
            bar_items.append(bar)
        
        # 축 설정
        macd_plot.getAxis('left').setLabel('MACD')
        
        return {
            'plot': macd_plot,
            'macd_line': macd_line_plot,
            'signal_line': signal_line_plot,
            'histogram': bar_items
        }
    
    @staticmethod
    def create_stochastic_overlay(chart, data_high, data_low, data_close, k_period=14, d_period=3):
        """스토캐스틱 오실레이터 오버레이 생성"""
        # 새 플롯 영역 생성
        stoch_plot = chart.scene().addPlot(row=3, col=0)
        stoch_plot.setMaximumHeight(100)
        stoch_plot.setXLink(chart)  # x축 연결
        
        # 최근 k_period 동안의 최고가/최저가
        low_min = data_low.rolling(window=k_period).min()
        high_max = data_high.rolling(window=k_period).max()
        
        # %K 계산
        k = 100 * ((data_close - low_min) / (high_max - low_min))
        
        # %D 계산 (K의 이동 평균)
        d = k.rolling(window=d_period).mean()
        
        # %K 선 그리기
        k_line_plot = stoch_plot.plot(
            x=range(len(k)),
            y=k.values,
            pen=pg.mkPen(color=(0, 0, 255), width=2),
            name=f"%K({k_period})"
        )
        
        # %D 선 그리기
        d_line_plot = stoch_plot.plot(
            x=range(len(d)),
            y=d.values,
            pen=pg.mkPen(color=(255, 165, 0), width=2),
            name=f"%D({d_period})"
        )
        
        # 과매수/과매도 영역 표시
        stoch_plot.addLine(y=80, pen=pg.mkPen(color=(255, 0, 0), style=Qt.PenStyle.DashLine))
        stoch_plot.addLine(y=20, pen=pg.mkPen(color=(0, 255, 0), style=Qt.PenStyle.DashLine))
        
        # 축 설정
        stoch_plot.setYRange(0, 100)
        stoch_plot.getAxis('left').setLabel('Stochastic')
        
        return {
            'plot': stoch_plot,
            'k_line': k_line_plot,
            'd_line': d_line_plot
        }