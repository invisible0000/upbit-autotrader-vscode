"""
리팩토링된 차트 뷰 화면
- 컴포넌트 기반 아키텍처
- UI 사양서 준수
- 향상된 사용자 경험
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTabWidget, QGroupBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QIcon

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# 컴포넌트 임포트
from .components.chart_control_panel import ChartControlPanel
from .components.indicator_management_panel import IndicatorManagementPanel
from .components.chart_info_panel import ChartInfoPanel
from .components.enhanced_candlestick_chart import CandlestickChart

# 기존 컴포넌트 임포트 (점진적 마이그레이션)
try:
    from .indicator_overlay import IndicatorOverlay
    from .trade_marker import TradeMarker
except ImportError:
    # 임시 더미 클래스
    class IndicatorOverlay:
        def __init__(self, *args, **kwargs): pass
    
    class TradeMarker:
        def __init__(self, *args, **kwargs): pass


class ChartViewScreen(QWidget):
    """리팩토링된 차트 뷰 화면"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 상태 변수
        self.current_symbol = "BTC-KRW"
        self.current_timeframe = "1d"
        self.chart_data = None
        self.active_indicators = {}
        self.trade_markers = []
        
        # UI 초기화
        self.init_ui()
        
        # 이벤트 연결
        self.connect_signals()
        
        # 초기 데이터 로드
        self.load_initial_data()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 메인 스플리터 (가로 분할)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 좌측 패널 (차트 영역)
        left_panel = self.create_chart_area()
        main_splitter.addWidget(left_panel)
        
        # 우측 패널 (컨트롤 및 정보)
        right_panel = self.create_control_area()
        main_splitter.addWidget(right_panel)
        
        # 스플리터 비율 설정 (차트:컨트롤 = 7:3)
        main_splitter.setSizes([700, 300])
        main_splitter.setChildrenCollapsible(False)
        
        layout.addWidget(main_splitter)
    
    def create_chart_area(self):
        """차트 영역 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 차트 컨트롤 패널
        self.chart_control = ChartControlPanel()
        layout.addWidget(self.chart_control)
        
        # 메인 차트
        chart_group = QGroupBox("📊 차트")
        chart_group.setStyleSheet("""
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
        chart_layout = QVBoxLayout(chart_group)
        
        # 캔들스틱 차트
        self.candlestick_chart = CandlestickChart()
        chart_layout.addWidget(self.candlestick_chart)
        
        layout.addWidget(chart_group)
        
        return widget
    
    def create_control_area(self):
        """컨트롤 영역 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 탭 위젯
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 정보 탭
        self.chart_info_panel = ChartInfoPanel()
        tab_widget.addTab(self.chart_info_panel, "📊 정보")
        
        # 지표 관리 탭
        self.indicator_panel = IndicatorManagementPanel()
        tab_widget.addTab(self.indicator_panel, "📈 지표")
        
        layout.addWidget(tab_widget)
        
        return widget
    
    def connect_signals(self):
        """시그널 연결"""
        # 차트 컨트롤 패널 시그널
        self.chart_control.symbol_changed.connect(self.on_symbol_changed)
        self.chart_control.timeframe_changed.connect(self.on_timeframe_changed)
        self.chart_control.indicator_added.connect(self.on_indicator_added_from_control)
        self.chart_control.chart_saved.connect(self.on_save_chart)
        self.chart_control.settings_changed.connect(self.on_chart_settings_changed)
        
        # 지표 관리 패널 시그널
        self.indicator_panel.indicator_added.connect(self.on_indicator_added)
        self.indicator_panel.indicator_removed.connect(self.on_indicator_removed)
        self.indicator_panel.indicator_visibility_changed.connect(self.on_indicator_visibility_changed)
        self.indicator_panel.indicator_settings_changed.connect(self.on_indicator_settings_changed)
    
    def load_initial_data(self):
        """초기 데이터 로드"""
        # 샘플 데이터 생성 (실제 환경에서는 API에서 데이터 로드)
        self.chart_data = self.generate_sample_data()
        
        # 차트 업데이트
        self.update_chart()
        
        # 정보 패널 업데이트
        self.chart_info_panel.set_symbol_and_timeframe(
            self.current_symbol, 
            self.current_timeframe
        )
        self.chart_info_panel.set_data_count(len(self.chart_data))
        
        # 실시간 시뮬레이션 시작
        self.start_realtime_simulation()
    
    def generate_sample_data(self, rows=200):
        """샘플 데이터 생성"""
        # 시작 날짜 설정
        start_date = datetime.now() - timedelta(days=rows)
        
        # 날짜 인덱스 생성
        dates = [start_date + timedelta(days=i) for i in range(rows)]
        
        # 시드 설정
        np.random.seed(42)
        
        # 초기 가격
        base_price = 50000000.0  # 5천만원
        
        # 가격 변동 생성 (트렌드 포함)
        trend = np.linspace(0, 0.3, rows)  # 30% 상승 트렌드
        volatility = np.random.normal(0, 0.02, rows)  # 2% 변동성
        
        # OHLCV 데이터 생성
        data = []
        current_price = base_price
        
        for i in range(rows):
            # 일간 변동 계산
            daily_change = trend[i] + volatility[i]
            daily_volatility = abs(volatility[i]) * 0.5
            
            # OHLCV 계산
            open_price = current_price
            close_price = current_price * (1 + daily_change)
            
            # 고가와 저가 계산
            price_range = [open_price, close_price]
            high_addition = np.random.uniform(0, daily_volatility * current_price)
            low_subtraction = np.random.uniform(0, daily_volatility * current_price)
            
            high_price = max(price_range) + high_addition
            low_price = min(price_range) - low_subtraction
            
            # 거래량 생성
            volume = np.random.lognormal(10, 1)  # 로그 정규 분포
            
            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_price = close_price
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def update_chart(self):
        """차트 업데이트"""
        if self.chart_data is not None:
            self.candlestick_chart.update_data(self.chart_data)
            
            # 활성 지표 업데이트
            for indicator_id, params in self.active_indicators.items():
                self.calculate_and_add_indicator(indicator_id, params)
    
    def start_realtime_simulation(self):
        """실시간 시뮬레이션 시작"""
        # 실시간 업데이트 타이머
        self.realtime_timer = QTimer()
        self.realtime_timer.timeout.connect(self.simulate_realtime_update)
        self.realtime_timer.start(2000)  # 2초마다 업데이트
        
        # 가격 정보 시뮬레이션
        if self.chart_data is not None and len(self.chart_data) > 0:
            last_price = self.chart_data['close'].iloc[-1]
            self.chart_info_panel.simulate_price_update(last_price)
    
    def simulate_realtime_update(self):
        """실시간 업데이트 시뮬레이션"""
        if self.chart_data is not None and len(self.chart_data) > 0:
            # 마지막 가격 기준으로 새로운 봉 생성
            last_close = self.chart_data['close'].iloc[-1]
            
            # 새로운 가격 생성
            change_percent = np.random.normal(0, 0.01)  # 1% 변동성
            new_close = last_close * (1 + change_percent)
            
            # 새로운 봉 데이터
            new_timestamp = self.chart_data.index[-1] + timedelta(days=1)
            
            volatility = abs(change_percent) * 0.5
            open_price = last_close
            close_price = new_close
            high_price = max(open_price, close_price) * (1 + np.random.uniform(0, volatility))
            low_price = min(open_price, close_price) * (1 - np.random.uniform(0, volatility))
            volume = np.random.lognormal(10, 1)
            
            # 새로운 데이터 추가
            new_row = pd.DataFrame({
                'open': [open_price],
                'high': [high_price],
                'low': [low_price],
                'close': [close_price],
                'volume': [volume]
            }, index=[new_timestamp])
            
            # 데이터 합치기 (최대 500개 봉 유지)
            self.chart_data = pd.concat([self.chart_data, new_row])
            if len(self.chart_data) > 500:
                self.chart_data = self.chart_data.tail(500)
            
            # 차트 업데이트
            self.update_chart()
            
            # 정보 패널 업데이트
            self.chart_info_panel.simulate_price_update(new_close)
            self.chart_info_panel.set_data_count(len(self.chart_data))
    
    @pyqtSlot(str)
    def on_symbol_changed(self, symbol):
        """심볼 변경 처리"""
        self.current_symbol = symbol
        
        # 새로운 데이터 로드 (실제 환경에서는 API 호출)
        self.chart_data = self.generate_sample_data()
        self.update_chart()
        
        # 정보 패널 업데이트
        self.chart_info_panel.set_symbol_and_timeframe(symbol, self.current_timeframe)
        self.chart_info_panel.set_data_count(len(self.chart_data))
    
    @pyqtSlot(str)
    def on_timeframe_changed(self, timeframe_display):
        """시간대 변경 처리"""
        # 표시용 시간대를 내부 형식으로 변환
        timeframe_map = {
            "1분": "1m", "3분": "3m", "5분": "5m", "15분": "15m", "30분": "30m",
            "1시간": "1h", "4시간": "4h", "1일": "1d", "1주": "1w", "1월": "1M"
        }
        
        self.current_timeframe = timeframe_map.get(timeframe_display, "1d")
        
        # 데이터 리샘플링 (실제 환경에서는 새로운 시간대 데이터 로드)
        self.resample_data()
        self.update_chart()
        
        # 정보 패널 업데이트
        self.chart_info_panel.set_symbol_and_timeframe(
            self.current_symbol, 
            self.current_timeframe
        )
    
    @pyqtSlot(str, dict)
    def on_indicator_added_from_control(self, indicator_name, params):
        """컨트롤 패널에서 지표 추가"""
        self.indicator_panel.add_indicator(indicator_name, params)
    
    @pyqtSlot(str, dict)
    def on_indicator_added(self, indicator_id, params):
        """지표 추가 처리"""
        self.active_indicators[indicator_id] = params
        self.calculate_and_add_indicator(indicator_id, params)
    
    @pyqtSlot(str)
    def on_indicator_removed(self, indicator_id):
        """지표 제거 처리"""
        if indicator_id in self.active_indicators:
            del self.active_indicators[indicator_id]
            # 차트에서 지표 제거
            self.candlestick_chart.remove_indicator_overlay(indicator_id)
    
    @pyqtSlot(str, bool)
    def on_indicator_visibility_changed(self, indicator_id, visible):
        """지표 가시성 변경"""
        # 차트에서 지표 가시성 토글
        self.candlestick_chart.set_indicator_visibility(indicator_id, visible)
    
    @pyqtSlot(str, dict)
    def on_indicator_settings_changed(self, indicator_id, new_params):
        """지표 설정 변경"""
        self.active_indicators[indicator_id] = new_params
        self.calculate_and_add_indicator(indicator_id, new_params)
    
    @pyqtSlot()
    def on_save_chart(self):
        """차트 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "차트 저장",
            f"{self.current_symbol}_{self.current_timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG 파일 (*.png);;JPG 파일 (*.jpg)"
        )
        
        if file_path:
            self.save_chart_image(file_path)
    
    @pyqtSlot(dict)
    def on_chart_settings_changed(self, settings):
        """차트 설정 변경"""
        # 차트 표시 옵션 적용
        self.candlestick_chart.set_volume_visible(settings.get('show_volume', True))
        self.candlestick_chart.set_grid_visible(settings.get('show_grid', True))
        self.candlestick_chart.set_crosshair_visible(settings.get('show_crosshair', True))
    
    def calculate_and_add_indicator(self, indicator_id, params):
        """지표 계산 및 추가"""
        if self.chart_data is None or len(self.chart_data) == 0:
            return
        
        indicator_type = params.get('type', '')
        
        try:
            if indicator_type == 'SMA':
                data = self.calculate_sma(params['period'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data, params)
                
            elif indicator_type == 'EMA':
                data = self.calculate_ema(params['period'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data, params)
                
            elif indicator_type == 'BBANDS':
                data = self.calculate_bollinger_bands(params['period'], params['std'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data, params)
                
            elif indicator_type == 'RSI':
                data = self.calculate_rsi(params['period'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data, params)
                
            elif indicator_type == 'MACD':
                data = self.calculate_macd(params['fast'], params['slow'], params['signal'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data, params)
                
            elif indicator_type == 'Stochastic':
                data = self.calculate_stochastic(params['k'], params['d'])
                self.candlestick_chart.add_indicator_overlay(indicator_id, data, params)
                
        except Exception as e:
            QMessageBox.warning(
                self, "지표 계산 오류", 
                f"지표 '{indicator_id}' 계산 중 오류가 발생했습니다:\n{str(e)}"
            )
    
    def calculate_sma(self, period):
        """단순 이동 평균 계산"""
        return self.chart_data['close'].rolling(window=period).mean()
    
    def calculate_ema(self, period):
        """지수 이동 평균 계산"""
        return self.chart_data['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_bollinger_bands(self, period, std_multiplier):
        """볼린저 밴드 계산"""
        sma = self.chart_data['close'].rolling(window=period).mean()
        std = self.chart_data['close'].rolling(window=period).std()
        
        upper = sma + (std * std_multiplier)
        lower = sma - (std * std_multiplier)
        
        return pd.DataFrame({
            'upper': upper,
            'middle': sma,
            'lower': lower
        })
    
    def calculate_rsi(self, period):
        """RSI 계산"""
        delta = self.chart_data['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, fast_period, slow_period, signal_period):
        """MACD 계산"""
        fast_ema = self.chart_data['close'].ewm(span=fast_period).mean()
        slow_ema = self.chart_data['close'].ewm(span=slow_period).mean()
        
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
    
    def calculate_stochastic(self, k_period, d_period):
        """스토캐스틱 계산"""
        low_min = self.chart_data['low'].rolling(window=k_period).min()
        high_max = self.chart_data['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((self.chart_data['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return pd.DataFrame({
            'k': k_percent,
            'd': d_percent
        })
    
    def resample_data(self):
        """데이터 리샘플링"""
        if self.chart_data is None:
            return
        
        # 시간대별 리샘플링 규칙
        resample_rules = {
            '1m': '1T', '3m': '3T', '5m': '5T', '15m': '15T', '30m': '30T',
            '1h': '1H', '4h': '4H', '1d': '1D', '1w': '1W', '1M': '1M'
        }
        
        rule = resample_rules.get(self.current_timeframe, '1D')
        
        # 리샘플링 수행
        resampled = self.chart_data.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        self.chart_data = resampled
    
    def save_chart_image(self, file_path):
        """차트 이미지 저장"""
        try:
            self.candlestick_chart.save_image(file_path)
            QMessageBox.information(
                self, "저장 완료", 
                f"차트가 성공적으로 저장되었습니다:\n{os.path.basename(file_path)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "저장 실패", 
                f"차트 저장 중 오류가 발생했습니다:\n{str(e)}"
            )
    
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
    
    def get_current_data(self):
        """현재 차트 데이터 반환"""
        return self.chart_data.copy() if self.chart_data is not None else None
