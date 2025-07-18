"""
차트 뷰 통합 테스트

이 모듈은 차트 뷰 화면의 기능을 테스트합니다.
- 캔들스틱 차트 렌더링
- 기술적 지표 오버레이
- 거래 시점 마커
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
from upbit_auto_trading.ui.desktop.screens.chart_view.candlestick_chart import CandlestickChart
from upbit_auto_trading.ui.desktop.screens.chart_view.indicator_overlay import IndicatorOverlay
from upbit_auto_trading.ui.desktop.screens.chart_view.trade_marker import TradeMarker


class TestChartView(unittest.TestCase):
    """차트 뷰 화면 테스트 클래스"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # QApplication 인스턴스가 없으면 생성
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
        
        # 테스트용 OHLCV 데이터 생성
        cls.test_data = cls._generate_test_data()
        
        # 테스트용 거래 데이터 생성
        cls.test_trades = cls._generate_test_trades()
    
    @staticmethod
    def _generate_test_data(rows=100):
        """테스트용 OHLCV 데이터 생성"""
        print("테스트용 OHLCV 데이터 생성")
        
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
        
        print(f"생성된 데이터 샘플:\n{df.head()}")
        return df
    
    @staticmethod
    def _generate_test_trades(count=10):
        """테스트용 거래 데이터 생성"""
        print("테스트용 거래 데이터 생성")
        
        # 시작 날짜 설정
        start_date = datetime.now() - timedelta(days=90)
        
        # 시드 설정으로 재현 가능한 랜덤 데이터 생성
        np.random.seed(42)
        
        # 거래 데이터 생성
        trades = []
        
        for i in range(count):
            # 랜덤 날짜 (최근 90일 내)
            trade_date = start_date + timedelta(days=np.random.randint(0, 90))
            
            # 매수/매도 여부
            trade_type = "buy" if i % 2 == 0 else "sell"
            
            # 가격 및 수량
            price = np.random.uniform(40000, 60000)
            quantity = np.random.uniform(0.1, 1.0)
            
            # 거래 데이터 추가
            trades.append({
                'timestamp': trade_date,
                'type': trade_type,
                'price': price,
                'quantity': quantity
            })
        
        # DataFrame 생성
        df = pd.DataFrame(trades)
        print(f"생성된 거래 데이터 샘플:\n{df.head()}")
        return df

    def setUp(self):
        """각 테스트 전 설정"""
        # 차트 뷰 화면 생성
        self.chart_view = ChartViewScreen()
    
    def tearDown(self):
        """각 테스트 후 정리"""
        if hasattr(self, 'chart_view'):
            self.chart_view.close()
    
    def test_08_3_1_chart_view_initialization(self):
        """=== 테스트 id 08_3_1: chart_view_initialization ===
        차트 뷰 화면이 올바르게 초기화되는지 테스트
        """
        print("\n=== 테스트 id 08_3_1: chart_view_initialization ===")
        
        # 차트 뷰 화면이 생성되었는지 확인
        self.assertIsNotNone(self.chart_view)
        
        # 캔들스틱 차트가 생성되었는지 확인
        self.assertIsNotNone(self.chart_view.candlestick_chart)
        
        # 기본 UI 요소들이 생성되었는지 확인
        self.assertIsNotNone(self.chart_view.symbol_selector)
        self.assertIsNotNone(self.chart_view.timeframe_selector)
        self.assertIsNotNone(self.chart_view.indicator_selector)
        
        print("차트 뷰 화면 초기화 테스트 완료")
    
    def test_08_3_2_candlestick_chart_rendering(self):
        """=== 테스트 id 08_3_2: candlestick_chart_rendering ===
        캔들스틱 차트가 데이터를 올바르게 렌더링하는지 테스트
        """
        print("\n=== 테스트 id 08_3_2: candlestick_chart_rendering ===")
        
        # 테스트 데이터로 차트 업데이트
        self.chart_view.candlestick_chart.update_data(self.test_data)
        
        # 차트에 데이터가 설정되었는지 확인
        self.assertIsNotNone(self.chart_view.candlestick_chart.data)
        self.assertEqual(len(self.chart_view.candlestick_chart.data), len(self.test_data))
        
        # 캔들스틱 아이템이 생성되었는지 확인
        self.assertGreater(len(self.chart_view.candlestick_chart.candlesticks), 0)
        
        print("캔들스틱 차트 렌더링 테스트 완료")
    
    def test_08_3_3_indicator_overlay(self):
        """=== 테스트 id 08_3_3: indicator_overlay ===
        기술적 지표 오버레이가 올바르게 작동하는지 테스트
        """
        print("\n=== 테스트 id 08_3_3: indicator_overlay ===")
        
        # 테스트 데이터로 차트 업데이트
        self.chart_view.candlestick_chart.update_data(self.test_data)
        
        # 이동 평균선 추가
        self.chart_view.add_indicator("SMA", {"window": 20})
        
        # 지표가 추가되었는지 확인
        self.assertIn("SMA_20", self.chart_view.active_indicators)
        
        # 지표 데이터가 계산되었는지 확인
        indicator_data = self.chart_view.indicator_data.get("SMA_20")
        self.assertIsNotNone(indicator_data)
        self.assertEqual(len(indicator_data), len(self.test_data) - 19)  # SMA 20은 처음 19개 데이터에 대해 NaN 값을 가짐
        
        # 볼린저 밴드 추가
        self.chart_view.add_indicator("BBANDS", {"window": 20, "num_std": 2})
        
        # 지표가 추가되었는지 확인
        self.assertIn("BBANDS_20_2", self.chart_view.active_indicators)
        
        # 지표 데이터가 계산되었는지 확인 (상단, 중간, 하단 밴드)
        upper_band = self.chart_view.indicator_data.get("BBANDS_20_2_upper")
        middle_band = self.chart_view.indicator_data.get("BBANDS_20_2_middle")
        lower_band = self.chart_view.indicator_data.get("BBANDS_20_2_lower")
        
        self.assertIsNotNone(upper_band)
        self.assertIsNotNone(middle_band)
        self.assertIsNotNone(lower_band)
        
        print("기술적 지표 오버레이 테스트 완료")
    
    def test_08_3_4_trade_markers(self):
        """=== 테스트 id 08_3_4: trade_markers ===
        거래 시점 마커가 올바르게 표시되는지 테스트
        """
        print("\n=== 테스트 id 08_3_4: trade_markers ===")
        
        # 테스트 데이터로 차트 업데이트
        self.chart_view.candlestick_chart.update_data(self.test_data)
        
        # 거래 마커 추가
        self.chart_view.add_trade_markers(self.test_trades)
        
        # 거래 마커가 추가되었는지 확인
        self.assertEqual(len(self.chart_view.trade_markers), len(self.test_trades))
        
        # 매수/매도 마커가 올바르게 구분되는지 확인
        buy_markers = [marker for marker in self.chart_view.trade_markers if marker.trade_type == "buy"]
        sell_markers = [marker for marker in self.chart_view.trade_markers if marker.trade_type == "sell"]
        
        self.assertEqual(len(buy_markers), len([t for t in self.test_trades.itertuples() if t.type == "buy"]))
        self.assertEqual(len(sell_markers), len([t for t in self.test_trades.itertuples() if t.type == "sell"]))
        
        print("거래 시점 마커 테스트 완료")
    
    def test_08_3_5_timeframe_change(self):
        """=== 테스트 id 08_3_5: timeframe_change ===
        시간대 변경이 올바르게 작동하는지 테스트
        """
        print("\n=== 테스트 id 08_3_5: timeframe_change ===")
        
        # 테스트 데이터로 차트 업데이트
        self.chart_view.candlestick_chart.update_data(self.test_data)
        
        # 초기 시간대 확인
        initial_timeframe = self.chart_view.current_timeframe
        
        # 시간대 변경
        new_timeframe = "1h" if initial_timeframe != "1h" else "1d"
        self.chart_view.change_timeframe(new_timeframe)
        
        # 시간대가 변경되었는지 확인
        self.assertEqual(self.chart_view.current_timeframe, new_timeframe)
        
        # 차트 데이터가 리샘플링되었는지 확인
        self.assertIsNotNone(self.chart_view.candlestick_chart.data)
        
        print("시간대 변경 테스트 완료")
    
    def test_08_3_6_chart_interaction(self):
        """=== 테스트 id 08_3_6: chart_interaction ===
        차트 상호작용(확대/축소, 이동)이 올바르게 작동하는지 테스트
        """
        print("\n=== 테스트 id 08_3_6: chart_interaction ===")
        
        # 테스트 데이터로 차트 업데이트
        self.chart_view.candlestick_chart.update_data(self.test_data)
        
        # 초기 뷰 범위 저장
        initial_view_range = self.chart_view.candlestick_chart.view_range.copy()
        
        # 확대 동작 시뮬레이션
        self.chart_view.candlestick_chart.zoom_in()
        
        # 뷰 범위가 변경되었는지 확인
        current_view_range = self.chart_view.candlestick_chart.view_range
        self.assertNotEqual(initial_view_range, current_view_range)
        
        # 축소 동작 시뮬레이션
        self.chart_view.candlestick_chart.zoom_out()
        
        # 뷰 범위가 원래대로 돌아왔는지 확인
        restored_view_range = self.chart_view.candlestick_chart.view_range
        self.assertAlmostEqual(initial_view_range[0], restored_view_range[0], delta=0.1)
        self.assertAlmostEqual(initial_view_range[1], restored_view_range[1], delta=0.1)
        
        print("차트 상호작용 테스트 완료")
    
    def test_08_3_7_save_chart_image(self):
        """=== 테스트 id 08_3_7: save_chart_image ===
        차트 이미지 저장 기능이 올바르게 작동하는지 테스트
        """
        print("\n=== 테스트 id 08_3_7: save_chart_image ===")
        
        # 테스트 데이터로 차트 업데이트
        self.chart_view.candlestick_chart.update_data(self.test_data)
        
        # 임시 파일 경로 생성
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.close()
        
        try:
            # 차트 이미지 저장
            self.chart_view.save_chart_image(temp_file.name)
            
            # 파일이 생성되었는지 확인
            self.assertTrue(os.path.exists(temp_file.name))
            
            # 파일 크기가 0보다 큰지 확인
            self.assertGreater(os.path.getsize(temp_file.name), 0)
            
            print(f"차트 이미지가 저장됨: {temp_file.name}")
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        
        print("차트 이미지 저장 테스트 완료")


if __name__ == '__main__':
    unittest.main()