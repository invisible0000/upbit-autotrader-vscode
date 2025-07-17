"""
기본 매매 전략 테스트 모듈
개발 순서: 5.2 기본 매매 전략 구현
"""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.business_logic.strategy.base_strategy import BaseStrategy
from upbit_auto_trading.business_logic.strategy.strategy_factory import StrategyFactory
from upbit_auto_trading.business_logic.strategy.basic_strategies import (
    MovingAverageCrossStrategy,
    BollingerBandsStrategy,
    RSIStrategy
)
from upbit_auto_trading.data_layer.processors.data_processor import DataProcessor


class TestBasicTradingStrategies(unittest.TestCase):
    """기본 매매 전략 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        print("\n===== 테스트 시작: {} =====".format(self._testMethodName))
        
        # 테스트용 OHLCV 데이터 생성
        dates = pd.date_range(start="2023-01-01", periods=100, freq="1D")
        self.test_data = pd.DataFrame({
            "timestamp": dates,
            "open": np.random.normal(100, 5, 100),
            "high": np.random.normal(105, 5, 100),
            "low": np.random.normal(95, 5, 100),
            "close": np.random.normal(100, 5, 100),
            "volume": np.random.normal(1000, 200, 100),
            "symbol": ["KRW-BTC"] * 100,
            "timeframe": ["1d"] * 100
        })
        
        # 데이터 일관성 보장 (high >= open, close, low / low <= open, close, high)
        for i in range(len(self.test_data)):
            values = [self.test_data.loc[i, "open"], self.test_data.loc[i, "close"]]
            self.test_data.loc[i, "high"] = max(values) + abs(np.random.normal(1, 0.5))
            self.test_data.loc[i, "low"] = min(values) - abs(np.random.normal(1, 0.5))
            self.test_data.loc[i, "volume"] = abs(self.test_data.loc[i, "volume"])
        
        print(f"테스트 데이터 생성 완료: {len(self.test_data)}개의 OHLCV 데이터")
        
        # 데이터 처리기 인스턴스 생성
        self.processor = DataProcessor()
        
        # 전략 팩토리 인스턴스 생성
        self.factory = StrategyFactory()
        
        # 전략 등록
        self.factory.register_strategy("ma_cross", MovingAverageCrossStrategy)
        self.factory.register_strategy("bollinger_bands", BollingerBandsStrategy)
        self.factory.register_strategy("rsi", RSIStrategy)
    
    def tearDown(self):
        """테스트 정리"""
        print("\n===== 테스트 종료: {} =====".format(self._testMethodName))
    
    def test_05_2_1_moving_average_cross_strategy_initialization(self):
        """이동 평균 교차 전략 초기화 테스트"""
        print("\n=== 테스트 id 5_2_1: test_moving_average_cross_strategy_initialization ===")
        
        # 유효한 매개변수로 전략 생성
        valid_params = {
            "short_window": 10,
            "long_window": 30
        }
        strategy = MovingAverageCrossStrategy(valid_params)
        
        # 전략 정보 확인
        self.assertEqual(strategy.name, "MovingAverageCrossStrategy")
        self.assertIn("이동 평균 교차", strategy.description)
        self.assertEqual(strategy.parameters["short_window"], 10)
        self.assertEqual(strategy.parameters["long_window"], 30)
        
        # 유효하지 않은 매개변수로 전략 생성 (기본값 사용)
        invalid_params = {
            "short_window": 50,
            "long_window": 20  # short_window > long_window (유효하지 않음)
        }
        strategy = MovingAverageCrossStrategy(invalid_params)
        
        # 기본값 확인
        default_params = strategy.get_default_parameters()
        self.assertEqual(strategy.parameters["short_window"], default_params["short_window"])
        self.assertEqual(strategy.parameters["long_window"], default_params["long_window"])
        
        print("이동 평균 교차 전략 초기화 테스트 통과")
    
    def test_05_2_2_moving_average_cross_strategy_required_indicators(self):
        """이동 평균 교차 전략 필요 지표 테스트"""
        print("\n=== 테스트 id 5_2_2: test_moving_average_cross_strategy_required_indicators ===")
        
        # 전략 생성
        strategy = MovingAverageCrossStrategy({
            "short_window": 10,
            "long_window": 30
        })
        
        # 필요 지표 확인
        indicators = strategy.get_required_indicators()
        
        # 두 개의 SMA 지표가 필요해야 함
        self.assertEqual(len(indicators), 2)
        
        # 첫 번째 지표 (단기 이동 평균)
        self.assertEqual(indicators[0]["name"], "SMA")
        self.assertEqual(indicators[0]["params"]["window"], 10)
        self.assertEqual(indicators[0]["params"]["column"], "close")
        
        # 두 번째 지표 (장기 이동 평균)
        self.assertEqual(indicators[1]["name"], "SMA")
        self.assertEqual(indicators[1]["params"]["window"], 30)
        self.assertEqual(indicators[1]["params"]["column"], "close")
        
        print("이동 평균 교차 전략 필요 지표 테스트 통과")
    
    def test_05_2_3_moving_average_cross_strategy_generate_signals(self):
        """이동 평균 교차 전략 신호 생성 테스트"""
        print("\n=== 테스트 id 5_2_3: test_moving_average_cross_strategy_generate_signals ===")
        
        # 전략 생성
        strategy = MovingAverageCrossStrategy({
            "short_window": 10,
            "long_window": 30
        })
        
        # 필요한 지표 계산
        data = self.test_data.copy()
        for indicator in strategy.get_required_indicators():
            data = self.processor.calculate_indicators(data, [indicator])
        
        # 신호 생성
        result = strategy.generate_signals(data)
        
        # 결과 검증
        self.assertIn("signal", result.columns)
        
        # 신호 값 검증 (1, -1, 0 중 하나여야 함)
        unique_signals = result["signal"].unique()
        for signal in unique_signals:
            self.assertIn(signal, [0, 1, -1])
        
        # 신호 로직 검증
        short_col = f"SMA_{strategy.parameters['short_window']}"
        long_col = f"SMA_{strategy.parameters['long_window']}"
        
        # 단기 이동 평균이 장기 이동 평균보다 크면 매수 신호(1)
        buy_signals = result[result["signal"] == 1]
        if not buy_signals.empty:
            self.assertTrue((buy_signals[short_col] > buy_signals[long_col]).all())
        
        # 단기 이동 평균이 장기 이동 평균보다 작으면 매도 신호(-1)
        sell_signals = result[result["signal"] == -1]
        if not sell_signals.empty:
            self.assertTrue((sell_signals[short_col] < sell_signals[long_col]).all())
        
        print("이동 평균 교차 전략 신호 생성 테스트 통과")
    
    def test_05_2_4_bollinger_bands_strategy_initialization(self):
        """볼린저 밴드 전략 초기화 테스트"""
        print("\n=== 테스트 id 5_2_4: test_bollinger_bands_strategy_initialization ===")
        
        # 유효한 매개변수로 전략 생성
        valid_params = {
            "window": 20,
            "num_std": 2.0,
            "column": "close"
        }
        strategy = BollingerBandsStrategy(valid_params)
        
        # 전략 정보 확인
        self.assertEqual(strategy.name, "BollingerBandsStrategy")
        self.assertIn("볼린저 밴드", strategy.description)
        self.assertEqual(strategy.parameters["window"], 20)
        self.assertEqual(strategy.parameters["num_std"], 2.0)
        self.assertEqual(strategy.parameters["column"], "close")
        
        # 유효하지 않은 매개변수로 전략 생성 (기본값 사용)
        invalid_params = {
            "window": 0,  # 0 이하는 유효하지 않음
            "num_std": -1.0  # 음수는 유효하지 않음
        }
        strategy = BollingerBandsStrategy(invalid_params)
        
        # 기본값 확인
        default_params = strategy.get_default_parameters()
        self.assertEqual(strategy.parameters["window"], default_params["window"])
        self.assertEqual(strategy.parameters["num_std"], default_params["num_std"])
        
        print("볼린저 밴드 전략 초기화 테스트 통과")
    
    def test_05_2_5_bollinger_bands_strategy_required_indicators(self):
        """볼린저 밴드 전략 필요 지표 테스트"""
        print("\n=== 테스트 id 5_2_5: test_bollinger_bands_strategy_required_indicators ===")
        
        # 전략 생성
        strategy = BollingerBandsStrategy({
            "window": 20,
            "num_std": 2.0,
            "column": "close"
        })
        
        # 필요 지표 확인
        indicators = strategy.get_required_indicators()
        
        # 볼린저 밴드 지표가 필요해야 함
        self.assertEqual(len(indicators), 1)
        self.assertEqual(indicators[0]["name"], "BOLLINGER_BANDS")
        self.assertEqual(indicators[0]["params"]["window"], 20)
        self.assertEqual(indicators[0]["params"]["num_std"], 2.0)
        self.assertEqual(indicators[0]["params"]["column"], "close")
        
        print("볼린저 밴드 전략 필요 지표 테스트 통과")
    
    def test_05_2_6_bollinger_bands_strategy_generate_signals(self):
        """볼린저 밴드 전략 신호 생성 테스트"""
        print("\n=== 테스트 id 5_2_6: test_bollinger_bands_strategy_generate_signals ===")
        
        # 전략 생성
        strategy = BollingerBandsStrategy({
            "window": 20,
            "num_std": 2.0,
            "column": "close"
        })
        
        # 필요한 지표 계산
        data = self.test_data.copy()
        for indicator in strategy.get_required_indicators():
            data = self.processor.calculate_indicators(data, [indicator])
        
        # 신호 생성
        result = strategy.generate_signals(data)
        
        # 결과 검증
        self.assertIn("signal", result.columns)
        
        # 신호 값 검증 (1, -1, 0 중 하나여야 함)
        unique_signals = result["signal"].unique()
        for signal in unique_signals:
            self.assertIn(signal, [0, 1, -1])
        
        # 신호 로직 검증
        column = strategy.parameters["column"]
        
        # 가격이 하단 밴드보다 낮으면 매수 신호(1)
        buy_signals = result[result["signal"] == 1]
        if not buy_signals.empty:
            self.assertTrue((buy_signals[column] <= buy_signals["BB_LOWER"]).all())
        
        # 가격이 상단 밴드보다 높으면 매도 신호(-1)
        sell_signals = result[result["signal"] == -1]
        if not sell_signals.empty:
            self.assertTrue((sell_signals[column] >= sell_signals["BB_UPPER"]).all())
        
        print("볼린저 밴드 전략 신호 생성 테스트 통과")
    
    def test_05_2_7_rsi_strategy_initialization(self):
        """RSI 전략 초기화 테스트"""
        print("\n=== 테스트 id 5_2_7: test_rsi_strategy_initialization ===")
        
        # 유효한 매개변수로 전략 생성
        valid_params = {
            "window": 14,
            "oversold": 30,
            "overbought": 70,
            "column": "close"
        }
        strategy = RSIStrategy(valid_params)
        
        # 전략 정보 확인
        self.assertEqual(strategy.name, "RSIStrategy")
        self.assertIn("RSI", strategy.description)
        self.assertEqual(strategy.parameters["window"], 14)
        self.assertEqual(strategy.parameters["oversold"], 30)
        self.assertEqual(strategy.parameters["overbought"], 70)
        self.assertEqual(strategy.parameters["column"], "close")
        
        # 유효하지 않은 매개변수로 전략 생성 (기본값 사용)
        invalid_params = {
            "window": 0,  # 0 이하는 유효하지 않음
            "oversold": 40,
            "overbought": 30  # oversold > overbought는 유효하지 않음
        }
        strategy = RSIStrategy(invalid_params)
        
        # 기본값 확인
        default_params = strategy.get_default_parameters()
        self.assertEqual(strategy.parameters["window"], default_params["window"])
        self.assertEqual(strategy.parameters["oversold"], default_params["oversold"])
        self.assertEqual(strategy.parameters["overbought"], default_params["overbought"])
        
        print("RSI 전략 초기화 테스트 통과")
    
    def test_05_2_8_rsi_strategy_required_indicators(self):
        """RSI 전략 필요 지표 테스트"""
        print("\n=== 테스트 id 5_2_8: test_rsi_strategy_required_indicators ===")
        
        # 전략 생성
        strategy = RSIStrategy({
            "window": 14,
            "oversold": 30,
            "overbought": 70,
            "column": "close"
        })
        
        # 필요 지표 확인
        indicators = strategy.get_required_indicators()
        
        # RSI 지표가 필요해야 함
        self.assertEqual(len(indicators), 1)
        self.assertEqual(indicators[0]["name"], "RSI")
        self.assertEqual(indicators[0]["params"]["window"], 14)
        self.assertEqual(indicators[0]["params"]["column"], "close")
        
        print("RSI 전략 필요 지표 테스트 통과")
    
    def test_05_2_9_rsi_strategy_generate_signals(self):
        """RSI 전략 신호 생성 테스트"""
        print("\n=== 테스트 id 5_2_9: test_rsi_strategy_generate_signals ===")
        
        # 전략 생성
        strategy = RSIStrategy({
            "window": 14,
            "oversold": 30,
            "overbought": 70,
            "column": "close"
        })
        
        # 필요한 지표 계산
        data = self.test_data.copy()
        for indicator in strategy.get_required_indicators():
            data = self.processor.calculate_indicators(data, [indicator])
        
        # 신호 생성
        result = strategy.generate_signals(data)
        
        # 결과 검증
        self.assertIn("signal", result.columns)
        
        # 신호 값 검증 (1, -1, 0 중 하나여야 함)
        unique_signals = result["signal"].unique()
        for signal in unique_signals:
            self.assertIn(signal, [0, 1, -1])
        
        # 신호 로직 검증
        rsi_col = f"RSI_{strategy.parameters['window']}"
        
        # RSI가 oversold 이하면 매수 신호(1)
        buy_signals = result[result["signal"] == 1]
        if not buy_signals.empty:
            self.assertTrue((buy_signals[rsi_col] <= strategy.parameters["oversold"]).all())
        
        # RSI가 overbought 이상이면 매도 신호(-1)
        sell_signals = result[result["signal"] == -1]
        if not sell_signals.empty:
            self.assertTrue((sell_signals[rsi_col] >= strategy.parameters["overbought"]).all())
        
        print("RSI 전략 신호 생성 테스트 통과")
    
    def test_05_2_10_strategy_factory_integration(self):
        """전략 팩토리 통합 테스트"""
        print("\n=== 테스트 id 5_2_10: test_strategy_factory_integration ===")
        
        # 전략 팩토리를 통해 전략 생성
        ma_strategy = self.factory.create_strategy("ma_cross")
        bb_strategy = self.factory.create_strategy("bollinger_bands")
        rsi_strategy = self.factory.create_strategy("rsi")
        
        # 전략 인스턴스 확인
        self.assertIsInstance(ma_strategy, MovingAverageCrossStrategy)
        self.assertIsInstance(bb_strategy, BollingerBandsStrategy)
        self.assertIsInstance(rsi_strategy, RSIStrategy)
        
        # 사용 가능한 전략 목록 확인
        strategies = self.factory.get_available_strategies()
        self.assertEqual(len(strategies), 3)
        
        # 전략 ID 확인
        strategy_ids = [s["id"] for s in strategies]
        self.assertIn("ma_cross", strategy_ids)
        self.assertIn("bollinger_bands", strategy_ids)
        self.assertIn("rsi", strategy_ids)
        
        print("전략 팩토리 통합 테스트 통과")


if __name__ == "__main__":
    unittest.main()