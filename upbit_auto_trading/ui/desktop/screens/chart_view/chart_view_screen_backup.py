"""
차트 뷰 화면 모듈

이 모듈은 캔들스틱 차트, 기술적 지표 오버레이, 거래 시점 마커를 포함하는
차트 뷰 화면을 구현합니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QPushButton, QLabel, QSplitter, QFrame,
    QScrollArea, QCheckBox, QGroupBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QIcon

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

from .candlestick_chart import CandlestickChart
from .indicator_overlay import IndicatorOverlay
from .trade_marker import TradeMarker


class ChartViewScreen(QWidget):
    """차트 뷰 화면 클래스"""
    
    def __init__(self, parent=None):
        """차트 뷰 화면 초기화"""
        super().__init__(parent)
        
        # 상태 변수 초기화
        self.current_symbol = "KRW-BTC"  # 기본 심볼
        self.current_timeframe = "1d"    # 기본 시간대
        self.active_indicators = set()   # 활성화된 지표 목록
        self.indicator_data = {}         # 지표 데이터
        self.trade_markers = []          # 거래 마커 목록
        
        # UI 초기화
        self._init_ui()
    
    def _init_ui(self):
        """UI 요소 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        
        # 상단 컨트롤 영역
        control_layout = QHBoxLayout()
        
        # 심볼 선택기
        self.symbol_selector = QComboBox()
        self.symbol_selector.addItems(["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-DOGE"])
        self.symbol_selector.setCurrentText(self.current_symbol)
        self.symbol_selector.currentTextChanged.connect(self._on_symbol_changed)
        
        # 시간대 선택기
        self.timeframe_selector = QComboBox()
        self.timeframe_selector.addItems(["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"])
        self.timeframe_selector.setCurrentText(self.current_timeframe)
        self.timeframe_selector.currentTextChanged.connect(self._on_timeframe_changed)
        
        # 지표 선택기
        self.indicator_selector = QComboBox()
        self.indicator_selector.addItems(["SMA", "EMA", "BBANDS", "RSI", "MACD", "Stochastic"])
        
        # 지표 추가 버튼
        self.add_indicator_btn = QPushButton("지표 추가")
        self.add_indicator_btn.clicked.connect(self._on_add_indicator)
        
        # 이미지 저장 버튼
        self.save_image_btn = QPushButton("차트 저장")
        self.save_image_btn.clicked.connect(self._on_save_image)
        
        # 컨트롤 레이아웃에 위젯 추가
        control_layout.addWidget(QLabel("심볼:"))
        control_layout.addWidget(self.symbol_selector)
        control_layout.addWidget(QLabel("시간대:"))
        control_layout.addWidget(self.timeframe_selector)
        control_layout.addWidget(QLabel("지표:"))
        control_layout.addWidget(self.indicator_selector)
        control_layout.addWidget(self.add_indicator_btn)
        control_layout.addWidget(self.save_image_btn)
        control_layout.addStretch(1)
        
        # 메인 레이아웃에 컨트롤 영역 추가
        main_layout.addLayout(control_layout)
        
        # 차트와 사이드바를 포함하는 스플리터
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 캔들스틱 차트 생성
        self.candlestick_chart = CandlestickChart()
        
        # 사이드바 (활성 지표 목록)
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # 활성 지표 그룹
        indicators_group = QGroupBox("활성 지표")
        indicators_layout = QVBoxLayout(indicators_group)
        
        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 지표 컨테이너
        self.indicator_container = QWidget()
        self.indicator_layout = QVBoxLayout(self.indicator_container)
        self.indicator_layout.addStretch(1)
        
        # 스크롤 영역에 지표 컨테이너 설정
        scroll_area.setWidget(self.indicator_container)
        
        # 지표 그룹에 스크롤 영역 추가
        indicators_layout.addWidget(scroll_area)
        
        # 사이드바에 지표 그룹 추가
        sidebar_layout.addWidget(indicators_group)
        
        # 거래 마커 그룹
        markers_group = QGroupBox("거래 마커")
        markers_layout = QVBoxLayout(markers_group)
        
        # 마커 표시 체크박스
        self.show_markers_cb = QCheckBox("거래 마커 표시")
        self.show_markers_cb.setChecked(True)
        self.show_markers_cb.stateChanged.connect(self._on_show_markers_changed)
        
        # 마커 그룹에 체크박스 추가
        markers_layout.addWidget(self.show_markers_cb)
        
        # 사이드바에 마커 그룹 추가
        sidebar_layout.addWidget(markers_group)
        sidebar_layout.addStretch(1)
        
        # 스플리터에 차트와 사이드바 추가
        splitter.addWidget(self.candlestick_chart)
        splitter.addWidget(sidebar)
        
        # 스플리터 비율 설정 (차트:사이드바 = 7:3)
        splitter.setSizes([700, 300])
        
        # 메인 레이아웃에 스플리터 추가
        main_layout.addWidget(splitter)
        
        # 상태 표시줄
        status_layout = QHBoxLayout()
        self.status_label = QLabel("준비됨")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)
        
        # 메인 레이아웃에 상태 표시줄 추가
        main_layout.addLayout(status_layout)
        
        # 초기 데이터 로드
        self._load_initial_data()
    
    def _load_initial_data(self):
        """초기 데이터 로드"""
        # 실제 구현에서는 데이터베이스나 API에서 데이터를 로드
        # 테스트를 위해 임시 데이터 생성
        self._generate_sample_data()
        
        # 상태 업데이트
        self.status_label.setText(f"{self.current_symbol} ({self.current_timeframe}) 데이터 로드됨")
    
    def _generate_sample_data(self, rows=100):
        """샘플 OHLCV 데이터 생성 (테스트용)"""
        # 시작 날짜 설정
        start_date = datetime.now() - timedelta(days=rows)
        
        # 날짜 인덱스 생성
        dates = [start_date + timedelta(days=i) for i in range(rows)]
        
        # 시드 설정으로 재현 가능한 랜덤 데이터 생성
        np.random.seed(42)
        
        # 초기 가격 설정
        base_price = 50000.0
        
        # 가격 변동 생성
        changes = np.random.normal(0, 1000, rows)
        
        # OHLCV 데이터 생성
        data = []
        current_price = base_price
        
        for i in range(rows):
            # 당일 변동폭
            daily_change = changes[i]
            daily_volatility = abs(daily_change) * 0.5
            
            # OHLCV 계산
            open_price = current_price
            close_price = current_price + daily_change
            high_price = max(open_price, close_price) + np.random.uniform(0, daily_volatility)
            low_price = min(open_price, close_price) - np.random.uniform(0, daily_volatility)
            volume = np.random.uniform(1000, 10000)
            
            # 데이터 추가
            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            # 다음 봉의 시가는 현재 봉의 종가
            current_price = close_price
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # 차트 업데이트
        self.candlestick_chart.update_data(df)
    
    @pyqtSlot(str)
    def _on_symbol_changed(self, symbol):
        """심볼 변경 시 호출되는 슬롯"""
        self.current_symbol = symbol
        # 실제 구현에서는 새 심볼에 대한 데이터 로드
        self._load_initial_data()
    
    @pyqtSlot(str)
    def _on_timeframe_changed(self, timeframe):
        """시간대 변경 시 호출되는 슬롯"""
        self.current_timeframe = timeframe
        # 시간대 변경 처리
        self.change_timeframe(timeframe)
    
    def change_timeframe(self, timeframe):
        """시간대 변경 처리"""
        # 실제 구현에서는 데이터 리샘플링 또는 새 시간대 데이터 로드
        self._load_initial_data()
        
        # 상태 업데이트
        self.status_label.setText(f"{self.current_symbol} ({timeframe}) 데이터 로드됨")
    
    @pyqtSlot()
    def _on_add_indicator(self):
        """지표 추가 버튼 클릭 시 호출되는 슬롯"""
        indicator_type = self.indicator_selector.currentText()
        
        # 지표 유형에 따라 파라미터 설정
        if indicator_type == "SMA":
            self.add_indicator("SMA", {"window": 20})
        elif indicator_type == "EMA":
            self.add_indicator("EMA", {"window": 20})
        elif indicator_type == "BBANDS":
            self.add_indicator("BBANDS", {"window": 20, "num_std": 2})
        elif indicator_type == "RSI":
            self.add_indicator("RSI", {"window": 14})
        elif indicator_type == "MACD":
            self.add_indicator("MACD", {"fast": 12, "slow": 26, "signal": 9})
        elif indicator_type == "Stochastic":
            self.add_indicator("Stochastic", {"k": 14, "d": 3})
    
    def add_indicator(self, indicator_type, params):
        """지표 추가"""
        # 지표 ID 생성
        if indicator_type == "BBANDS":
            indicator_id = f"{indicator_type}_{params['window']}_{params['num_std']}"
        elif indicator_type == "MACD":
            indicator_id = f"{indicator_type}_{params['fast']}_{params['slow']}_{params['signal']}"
        elif indicator_type == "Stochastic":
            indicator_id = f"{indicator_type}_{params['k']}_{params['d']}"
        else:
            indicator_id = f"{indicator_type}_{params['window']}"
        
        # 이미 추가된 지표인지 확인
        if indicator_id in self.active_indicators:
            self.status_label.setText(f"지표 {indicator_id}는 이미 추가되었습니다.")
            return
        
        # 지표 계산
        if indicator_type == "SMA":
            # 단순 이동 평균
            window = params['window']
            data = self.candlestick_chart.data['close'].rolling(window=window).mean()
            self.indicator_data[indicator_id] = data
        
        elif indicator_type == "EMA":
            # 지수 이동 평균
            window = params['window']
            data = self.candlestick_chart.data['close'].ewm(span=window, adjust=False).mean()
            self.indicator_data[indicator_id] = data
        
        elif indicator_type == "BBANDS":
            # 볼린저 밴드
            window = params['window']
            num_std = params['num_std']
            
            # 중간 밴드 (SMA)
            middle = self.candlestick_chart.data['close'].rolling(window=window).mean()
            
            # 표준 편차
            std = self.candlestick_chart.data['close'].rolling(window=window).std()
            
            # 상단 및 하단 밴드
            upper = middle + (std * num_std)
            lower = middle - (std * num_std)
            
            # 데이터 저장
            self.indicator_data[f"{indicator_id}_upper"] = upper
            self.indicator_data[f"{indicator_id}_middle"] = middle
            self.indicator_data[f"{indicator_id}_lower"] = lower
        
        elif indicator_type == "RSI":
            # 상대 강도 지수
            window = params['window']
            
            # 가격 변화
            delta = self.candlestick_chart.data['close'].diff()
            
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
            
            self.indicator_data[indicator_id] = rsi
        
        elif indicator_type == "MACD":
            # MACD (Moving Average Convergence Divergence)
            fast = params['fast']
            slow = params['slow']
            signal = params['signal']
            
            # 빠른 EMA
            fast_ema = self.candlestick_chart.data['close'].ewm(span=fast, adjust=False).mean()
            
            # 느린 EMA
            slow_ema = self.candlestick_chart.data['close'].ewm(span=slow, adjust=False).mean()
            
            # MACD 라인
            macd_line = fast_ema - slow_ema
            
            # 시그널 라인
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            
            # 히스토그램
            histogram = macd_line - signal_line
            
            # 데이터 저장
            self.indicator_data[f"{indicator_id}_line"] = macd_line
            self.indicator_data[f"{indicator_id}_signal"] = signal_line
            self.indicator_data[f"{indicator_id}_histogram"] = histogram
        
        elif indicator_type == "Stochastic":
            # 스토캐스틱 오실레이터
            k_period = params['k']
            d_period = params['d']
            
            # 최근 k_period 동안의 최고가/최저가
            low_min = self.candlestick_chart.data['low'].rolling(window=k_period).min()
            high_max = self.candlestick_chart.data['high'].rolling(window=k_period).max()
            
            # %K 계산
            k = 100 * ((self.candlestick_chart.data['close'] - low_min) / (high_max - low_min))
            
            # %D 계산 (K의 이동 평균)
            d = k.rolling(window=d_period).mean()
            
            # 데이터 저장
            self.indicator_data[f"{indicator_id}_k"] = k
            self.indicator_data[f"{indicator_id}_d"] = d
        
        # 활성 지표 목록에 추가
        self.active_indicators.add(indicator_id)
        
        # 지표 컨트롤 위젯 추가
        indicator_widget = QWidget()
        indicator_layout = QHBoxLayout(indicator_widget)
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        
        # 지표 이름 레이블
        indicator_label = QLabel(indicator_id)
        
        # 지표 제거 버튼
        remove_btn = QPushButton("제거")
        remove_btn.setFixedSize(QSize(40, 20))
        remove_btn.clicked.connect(lambda: self._remove_indicator(indicator_id))
        
        # 레이아웃에 위젯 추가
        indicator_layout.addWidget(indicator_label)
        indicator_layout.addWidget(remove_btn)
        indicator_layout.addStretch(1)
        
        # 지표 컨테이너에 위젯 추가
        self.indicator_layout.insertWidget(self.indicator_layout.count() - 1, indicator_widget)
        
        # 차트에 지표 오버레이 추가
        self.candlestick_chart.add_indicator_overlay(indicator_id, self.indicator_data)
        
        # 상태 업데이트
        self.status_label.setText(f"지표 {indicator_id} 추가됨")
    
    def _remove_indicator(self, indicator_id):
        """지표 제거"""
        # 활성 지표 목록에서 제거
        if indicator_id in self.active_indicators:
            self.active_indicators.remove(indicator_id)
        
        # 지표 데이터 제거
        if indicator_id.startswith("BBANDS"):
            self.indicator_data.pop(f"{indicator_id}_upper", None)
            self.indicator_data.pop(f"{indicator_id}_middle", None)
            self.indicator_data.pop(f"{indicator_id}_lower", None)
        elif indicator_id.startswith("MACD"):
            self.indicator_data.pop(f"{indicator_id}_line", None)
            self.indicator_data.pop(f"{indicator_id}_signal", None)
            self.indicator_data.pop(f"{indicator_id}_histogram", None)
        elif indicator_id.startswith("Stochastic"):
            self.indicator_data.pop(f"{indicator_id}_k", None)
            self.indicator_data.pop(f"{indicator_id}_d", None)
        else:
            self.indicator_data.pop(indicator_id, None)
        
        # 차트에서 지표 오버레이 제거
        self.candlestick_chart.remove_indicator_overlay(indicator_id)
        
        # 지표 컨트롤 위젯 제거
        for i in range(self.indicator_layout.count()):
            widget = self.indicator_layout.itemAt(i).widget()
            if widget:
                label = widget.findChild(QLabel)
                if label and label.text() == indicator_id:
                    widget.deleteLater()
                    break
        
        # 상태 업데이트
        self.status_label.setText(f"지표 {indicator_id} 제거됨")
    
    def add_trade_markers(self, trades_df):
        """거래 마커 추가"""
        # 기존 마커 제거
        for marker in self.trade_markers:
            self.candlestick_chart.remove_trade_marker(marker)
        
        self.trade_markers = []
        
        # 새 마커 추가
        for trade in trades_df.itertuples():
            marker = TradeMarker(
                timestamp=trade.timestamp,
                price=trade.price,
                trade_type=trade.type
            )
            self.trade_markers.append(marker)
            self.candlestick_chart.add_trade_marker(marker)
        
        # 상태 업데이트
        self.status_label.setText(f"{len(self.trade_markers)}개의 거래 마커 추가됨")
    
    @pyqtSlot(int)
    def _on_show_markers_changed(self, state):
        """거래 마커 표시 체크박스 상태 변경 시 호출되는 슬롯"""
        show = state == Qt.CheckState.Checked.value
        
        for marker in self.trade_markers:
            marker.setVisible(show)
        
        # 차트 업데이트
        self.candlestick_chart.update()
    
    @pyqtSlot()
    def _on_save_image(self):
        """차트 이미지 저장 버튼 클릭 시 호출되는 슬롯"""
        # 파일 저장 대화상자 표시
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "차트 이미지 저장",
            f"{self.current_symbol}_{self.current_timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "이미지 파일 (*.png *.jpg)"
        )
        
        if file_path:
            self.save_chart_image(file_path)
    
    def save_chart_image(self, file_path):
        """차트 이미지 저장"""
        # 차트 이미지 저장
        self.candlestick_chart.save_image(file_path)
        
        # 상태 업데이트
        self.status_label.setText(f"차트 이미지 저장됨: {os.path.basename(file_path)}")