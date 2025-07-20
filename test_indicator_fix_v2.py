#!/usr/bin/env python3
"""
향상된 지표 시스템 테스트 스크립트
- 지표 추가/제거/갱신 시나리오 테스트
- 지표 영속성 및 범례 관리 테스트
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer, pyqtSignal
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("향상된 지표 시스템 테스트")
        self.setGeometry(100, 100, 1400, 900)
        
        # 메인 위젯
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 테스트 컨트롤 패널
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # 테스트 버튼들
        self.add_sma_btn = QPushButton("SMA 추가")
        self.add_sma_btn.clicked.connect(self.add_sma)
        control_layout.addWidget(self.add_sma_btn)
        
        self.add_bb_btn = QPushButton("볼린저 밴드 추가")
        self.add_bb_btn.clicked.connect(self.add_bollinger_bands)
        control_layout.addWidget(self.add_bb_btn)
        
        self.add_rsi_btn = QPushButton("RSI 추가")
        self.add_rsi_btn.clicked.connect(self.add_rsi)
        control_layout.addWidget(self.add_rsi_btn)
        
        self.refresh_btn = QPushButton("차트 갱신 (문제 재현)")
        self.refresh_btn.clicked.connect(self.refresh_chart_data)
        control_layout.addWidget(self.refresh_btn)
        
        self.clear_all_btn = QPushButton("모든 지표 제거")
        self.clear_all_btn.clicked.connect(self.clear_all_indicators)
        control_layout.addWidget(self.clear_all_btn)
        
        # 상태 표시
        self.status_label = QLabel("테스트 준비 완료")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_panel)
        
        # 차트 화면
        self.chart_screen = ChartViewScreen()
        layout.addWidget(self.chart_screen)
        
        # 테스트 데이터 생성
        self.generate_test_data()
        
        # 자동 갱신 타이머 (선택적)
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.auto_refresh)
        
        # 테스트 카운터
        self.test_counter = 0
        
    def generate_test_data(self):
        """테스트용 캔들스틱 데이터 생성"""
        print("📊 테스트 데이터 생성 중...")
        
        # 200개의 캔들 데이터 생성
        periods = 200
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='h')
        
        # 실제 가격 움직임과 유사한 데이터 생성
        np.random.seed(42)
        price_base = 50000
        returns = np.random.normal(0, 0.02, periods)
        price_changes = np.cumprod(1 + returns)
        
        prices = price_base * price_changes
        
        # OHLCV 데이터 생성
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            # 약간의 변동성 추가
            high = price * np.random.uniform(1.001, 1.02)
            low = price * np.random.uniform(0.98, 0.999)
            open_price = prices[i-1] if i > 0 else price
            close = price
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        self.test_data = pd.DataFrame(data)
        self.test_data.set_index('timestamp', inplace=True)
        
        # 차트에 데이터 설정 (올바른 초기화 방식)
        self.chart_screen.current_symbol = "TEST"
        self.chart_screen.current_timeframe = "1h"
        self.chart_screen.chart_data = self.test_data
        
        # API 호출 방지를 위해 업비트 API를 Mock으로 대체
        class MockUpbitAPI:
            def get_candles(self, symbol, timeframe, count):
                return None  # API 호출하지 않음
            def get_candles_before(self, symbol, timeframe, before_timestamp, count):
                return None  # API 호출하지 않음
        
        # API 호출 방지
        original_api = self.chart_screen.upbit_api
        self.chart_screen.upbit_api = MockUpbitAPI()
        
        # 차트 업데이트 (API 호출 없이)
        self.chart_screen.candlestick_chart.update_data(self.test_data)
        
        # 원래 API 복원 (필요시)
        self.chart_screen.upbit_api = original_api
        
        print(f"✅ 테스트 데이터 생성 완료 ({len(self.test_data)}개 캔들)")
        self.status_label.setText("테스트 데이터 로드 완료")
        
    def add_sma(self):
        """SMA 지표 추가 테스트"""
        print("\n🔴 SMA 추가 테스트 시작")
        try:
            self.chart_screen.calculate_and_add_indicator('SMA', {'period': 20})
            self.status_label.setText("SMA(20) 추가됨")
            print("✅ SMA 추가 성공")
        except Exception as e:
            print(f"❌ SMA 추가 실패: {e}")
            self.status_label.setText(f"SMA 추가 실패: {e}")
    
    def add_bollinger_bands(self):
        """볼린저 밴드 지표 추가 테스트"""
        print("\n🟡 볼린저 밴드 추가 테스트 시작")
        try:
            self.chart_screen.calculate_and_add_indicator('BBANDS', {'period': 20, 'std_dev': 2})
            self.status_label.setText("볼린저 밴드 추가됨")
            print("✅ 볼린저 밴드 추가 성공")
        except Exception as e:
            print(f"❌ 볼린저 밴드 추가 실패: {e}")
            self.status_label.setText(f"볼린저 밴드 추가 실패: {e}")
    
    def add_rsi(self):
        """RSI 지표 추가 테스트"""
        print("\n🟢 RSI 추가 테스트 시작")
        try:
            self.chart_screen.calculate_and_add_indicator('RSI', {'period': 14})
            self.status_label.setText("RSI(14) 추가됨")
            print("✅ RSI 추가 성공")
        except Exception as e:
            print(f"❌ RSI 추가 실패: {e}")
            self.status_label.setText(f"RSI 추가 실패: {e}")
    
    def refresh_chart_data(self):
        """차트 데이터 갱신으로 문제 재현"""
        print("\n🔄 차트 갱신 테스트 시작")
        self.test_counter += 1
        
        # 현재 활성 지표 확인
        current_indicators = list(self.chart_screen.active_indicators.keys())
        print(f"  현재 활성 지표: {current_indicators}")
        
        # 새로운 캔들 데이터 추가 (실제 업데이트 시나리오)
        new_timestamp = self.test_data.index[-1] + timedelta(hours=1)
        last_close = self.test_data['close'].iloc[-1]
        new_price = last_close * np.random.uniform(0.99, 1.01)
        
        new_candle = pd.DataFrame({
            'open': [last_close],
            'high': [new_price * np.random.uniform(1.001, 1.01)],
            'low': [new_price * np.random.uniform(0.99, 0.999)],
            'close': [new_price],
            'volume': [np.random.uniform(100, 1000)]
        }, index=[new_timestamp])
        
        # 데이터 업데이트
        self.test_data = pd.concat([self.test_data, new_candle])
        self.chart_screen.chart_data = self.test_data
        
        # 차트 업데이트 (여기서 지표가 사라지는 문제 발생 가능)
        print("  차트 데이터 업데이트 중...")
        self.chart_screen.candlestick_chart.update_data(self.test_data)
        
        # 업데이트 후 지표 상태 확인
        updated_indicators = list(self.chart_screen.active_indicators.keys())
        print(f"  업데이트 후 활성 지표: {updated_indicators}")
        
        # 범례 상태 확인
        legend_items = []
        if hasattr(self.chart_screen.candlestick_chart, 'legend') and self.chart_screen.candlestick_chart.legend:
            legend_items = [item.text for item in self.chart_screen.candlestick_chart.legend.items]
        print(f"  현재 범례 항목: {legend_items}")
        
        self.status_label.setText(f"갱신 #{self.test_counter} 완료 - 지표: {len(updated_indicators)}개")
        
        if len(current_indicators) != len(updated_indicators):
            print(f"⚠️ 지표 수 변경 감지! {len(current_indicators)} → {len(updated_indicators)}")
        
        print("🔄 차트 갱신 테스트 완료")
    
    def clear_all_indicators(self):
        """모든 지표 제거 테스트"""
        print("\n🗑️ 모든 지표 제거 테스트 시작")
        
        indicators_to_remove = list(self.chart_screen.active_indicators.keys())
        print(f"  제거할 지표: {indicators_to_remove}")
        
        for indicator_id in indicators_to_remove:
            try:
                self.chart_screen.on_indicator_removed(indicator_id)
                print(f"  ✅ {indicator_id} 제거 완료")
            except Exception as e:
                print(f"  ❌ {indicator_id} 제거 실패: {e}")
        
        remaining_indicators = list(self.chart_screen.active_indicators.keys())
        print(f"  남은 지표: {remaining_indicators}")
        
        self.status_label.setText("모든 지표 제거 완료")
        print("🗑️ 모든 지표 제거 테스트 완료")
    
    def auto_refresh(self):
        """자동 갱신 (선택적)"""
        self.refresh_chart_data()
    
    def start_auto_refresh(self, interval_ms=5000):
        """자동 갱신 시작"""
        self.auto_refresh_timer.start(interval_ms)
        print(f"🔄 자동 갱신 시작 (간격: {interval_ms}ms)")
    
    def stop_auto_refresh(self):
        """자동 갱신 중지"""
        self.auto_refresh_timer.stop()
        print("⏹️ 자동 갱신 중지")

def main():
    print("🚀 향상된 지표 시스템 테스트 시작")
    
    app = QApplication(sys.argv)
    
    # 테스트 윈도우 생성
    window = TestWindow()
    window.show()
    
    # 테스트 시나리오 설명
    print("\n📋 테스트 시나리오:")
    print("1. 'SMA 추가' - SMA 지표 추가")
    print("2. '볼린저 밴드 추가' - 볼린저 밴드 지표 추가") 
    print("3. 'RSI 추가' - RSI 지표 추가")
    print("4. '차트 갱신' - 새 데이터로 차트 업데이트 (지표 영속성 테스트)")
    print("5. '모든 지표 제거' - 지표 및 범례 완전 제거 테스트")
    print("\n🔍 각 단계에서 콘솔 로그를 확인하여 지표 상태를 모니터링하세요.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
