#!/usr/bin/env python3
"""
지표 문제 해결 테스트 스크립트

이 스크립트는 다음 문제들을 테스트합니다:
1. 이동평균선이 나타났다가 화면 갱신되면 지워지는 문제
2. 지수이동평균선도 나타났다가 사라지는 문제  
3. 볼린저밴드가 작동하지 않는 문제
4. MACD와 RSI 서브플롯 문제
"""

import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import QTimer
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen

class IndicatorTestWindow(QMainWindow):
    """지표 테스트 창"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("지표 문제 해결 테스트")
        self.setGeometry(100, 100, 1400, 800)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 테스트 버튼들
        button_layout = QHBoxLayout()
        
        self.test_sma_btn = QPushButton("SMA 테스트")
        self.test_sma_btn.clicked.connect(self.test_sma)
        button_layout.addWidget(self.test_sma_btn)
        
        self.test_ema_btn = QPushButton("EMA 테스트")
        self.test_ema_btn.clicked.connect(self.test_ema)
        button_layout.addWidget(self.test_ema_btn)
        
        self.test_bb_btn = QPushButton("볼린저밴드 테스트")
        self.test_bb_btn.clicked.connect(self.test_bollinger_bands)
        button_layout.addWidget(self.test_bb_btn)
        
        self.test_rsi_btn = QPushButton("RSI 테스트")
        self.test_rsi_btn.clicked.connect(self.test_rsi)
        button_layout.addWidget(self.test_rsi_btn)
        
        self.test_macd_btn = QPushButton("MACD 테스트")
        self.test_macd_btn.clicked.connect(self.test_macd)
        button_layout.addWidget(self.test_macd_btn)
        
        self.refresh_btn = QPushButton("데이터 새로고침 (지표 지속성 테스트)")
        self.refresh_btn.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        # 차트 뷰 추가
        self.chart_view = ChartViewScreen()
        layout.addWidget(self.chart_view)
        
        # 테스트 데이터 생성
        self.generate_test_data()
        
        print("🚀 지표 테스트 창이 초기화되었습니다.")
        print("📊 각 버튼을 클릭하여 지표를 테스트하세요.")
        print("🔄 '데이터 새로고침' 버튼으로 지표 지속성을 확인하세요.")
    
    def generate_test_data(self):
        """테스트용 캔들 데이터 생성"""
        # 200개의 테스트 캔들 데이터 생성
        dates = pd.date_range(start='2024-01-01', periods=200, freq='D')
        
        # 랜덤한 가격 데이터 생성 (실제 캔들과 유사하게)
        base_price = 50000  # 기준 가격
        prices = []
        current_price = base_price
        
        for _ in range(200):
            # 일일 변동률 (-5% ~ +5%)
            change = np.random.uniform(-0.05, 0.05)
            current_price = current_price * (1 + change)
            
            # OHLC 생성
            open_price = current_price
            close_price = current_price * (1 + np.random.uniform(-0.03, 0.03))
            high_price = max(open_price, close_price) * (1 + np.random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - np.random.uniform(0, 0.02))
            volume = np.random.uniform(1000, 10000)
            
            prices.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_price = close_price
        
        # DataFrame 생성
        test_data = pd.DataFrame(prices, index=dates)
        
        # 차트 뷰에 데이터 설정
        self.chart_view.chart_data = test_data
        self.chart_view.update_chart(preserve_viewport=False)
        
        print(f"✅ 테스트 데이터 생성 완료: {len(test_data)}개 캔들")
    
    def test_sma(self):
        """SMA 테스트"""
        print("\n🔵 SMA(20) 테스트 시작...")
        params = {"type": "SMA", "period": 20, "color": "#2196F3"}
        indicator_id = "SMA_20_test"
        
        # 지표 계산 및 추가
        self.chart_view.active_indicators[indicator_id] = params
        self.chart_view.calculate_and_add_indicator(indicator_id, params)
        
        # 우측 지표 패널에도 추가
        self.chart_view.indicator_panel.add_indicator("이동평균 (SMA)", params)
        
        print(f"✅ SMA 추가 완료: {indicator_id}")
        print(f"📊 활성 지표 수: {len(self.chart_view.active_indicators)}")
    
    def test_ema(self):
        """EMA 테스트"""
        print("\n🟠 EMA(20) 테스트 시작...")
        params = {"type": "EMA", "period": 20, "color": "#FF9800"}
        indicator_id = "EMA_20_test"
        
        # 지표 계산 및 추가
        self.chart_view.active_indicators[indicator_id] = params
        self.chart_view.calculate_and_add_indicator(indicator_id, params)
        
        # 우측 지표 패널에도 추가
        self.chart_view.indicator_panel.add_indicator("지수이동평균 (EMA)", params)
        
        print(f"✅ EMA 추가 완료: {indicator_id}")
        print(f"📊 활성 지표 수: {len(self.chart_view.active_indicators)}")
    
    def test_bollinger_bands(self):
        """볼린저밴드 테스트"""
        print("\n🟣 볼린저밴드(20,2) 테스트 시작...")
        params = {"type": "BBANDS", "period": 20, "std": 2.0, "color": "#9C27B0"}
        indicator_id = "BBANDS_20_2_test"
        
        # 지표 계산 및 추가
        self.chart_view.active_indicators[indicator_id] = params
        self.chart_view.calculate_and_add_indicator(indicator_id, params)
        
        # 우측 지표 패널에도 추가
        self.chart_view.indicator_panel.add_indicator("볼린저밴드 (BBANDS)", params)
        
        print(f"✅ 볼린저밴드 추가 완료: {indicator_id}")
        print(f"📊 활성 지표 수: {len(self.chart_view.active_indicators)}")
    
    def test_rsi(self):
        """RSI 테스트"""
        print("\n🔴 RSI(14) 테스트 시작...")
        params = {"type": "RSI", "period": 14, "color": "#F44336"}
        indicator_id = "RSI_14_test"
        
        # 지표 계산 및 추가
        self.chart_view.active_indicators[indicator_id] = params
        self.chart_view.calculate_and_add_indicator(indicator_id, params)
        
        # 우측 지표 패널에도 추가
        self.chart_view.indicator_panel.add_indicator("RSI", params)
        
        print(f"✅ RSI 추가 완료: {indicator_id}")
        print(f"📊 활성 지표 수: {len(self.chart_view.active_indicators)}")
        print("⚠️  RSI는 서브플롯으로 표시되어야 하지만 현재는 메인 차트에 표시됩니다.")
    
    def test_macd(self):
        """MACD 테스트"""
        print("\n🟢 MACD(12,26,9) 테스트 시작...")
        params = {"type": "MACD", "fast": 12, "slow": 26, "signal": 9, "color": "#4CAF50"}
        indicator_id = "MACD_12_26_9_test"
        
        # 지표 계산 및 추가
        self.chart_view.active_indicators[indicator_id] = params
        self.chart_view.calculate_and_add_indicator(indicator_id, params)
        
        # 우측 지표 패널에도 추가
        self.chart_view.indicator_panel.add_indicator("MACD", params)
        
        print(f"✅ MACD 추가 완료: {indicator_id}")
        print(f"📊 활성 지표 수: {len(self.chart_view.active_indicators)}")
        print("⚠️  MACD는 서브플롯으로 표시되어야 하지만 현재는 메인 차트에 표시됩니다.")
    
    def refresh_data(self):
        """데이터 새로고침 - 지표 지속성 테스트"""
        print("\n🔄 데이터 새로고침 시작...")
        print(f"🔍 새로고침 전 활성 지표 수: {len(self.chart_view.active_indicators)}")
        
        # 차트 업데이트 (뷰포트 보존)
        self.chart_view.update_chart(preserve_viewport=True)
        
        print(f"🔍 새로고침 후 활성 지표 수: {len(self.chart_view.active_indicators)}")
        print("✅ 데이터 새로고침 완료")
        print("❓ 지표들이 여전히 표시되는지 확인하세요.")


def main():
    """메인 함수"""
    print("🧪 지표 문제 해결 테스트 시작")
    
    app = QApplication(sys.argv)
    
    # 테스트 창 생성 및 표시
    test_window = IndicatorTestWindow()
    test_window.show()
    
    print("📌 테스트 가이드:")
    print("1. 각 지표 버튼을 차례로 클릭하여 지표를 추가하세요")
    print("2. '데이터 새로고침' 버튼을 눌러 지표가 사라지는지 확인하세요")
    print("3. 볼린저밴드가 제대로 표시되는지 확인하세요")
    print("4. RSI와 MACD가 서브플롯에 표시되는지 확인하세요")
    
    # 애플리케이션 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
