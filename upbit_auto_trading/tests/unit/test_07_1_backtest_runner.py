"""
백테스트 실행기 테스트 모듈

이 모듈은 백테스트 실행기의 기능을 테스트합니다.
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

from upbit_auto_trading.business_logic.backtester.backtest_runner import BacktestRunner
from upbit_auto_trading.business_logic.strategy.basic_strategies import MovingAverageCrossStrategy


class TestBacktestRunner(unittest.TestCase):
    """
    백테스트 실행기 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        print("\n=== 테스트 id 07_1_1: test_init_backtest_runner ===")
        # 테스트용 전략 생성
        self.strategy = MovingAverageCrossStrategy({
            "short_window": 5,
            "long_window": 10
        })
        
        # 테스트용 백테스트 설정
        self.backtest_config = {
            "symbol": "KRW-BTC",
            "timeframe": "1h",
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 1, 31),
            "initial_capital": 1000000.0,
            "fee_rate": 0.0005,  # 0.05% 수수료
            "slippage": 0.0002,  # 0.02% 슬리피지
        }
        
        # 테스트용 데이터 생성
        self.create_test_data()
        
        # 백테스트 실행기 생성
        self.backtest_runner = BacktestRunner(self.strategy, self.backtest_config)
    
    def create_test_data(self):
        """
        테스트용 OHLCV 데이터 생성
        """
        # 테스트 기간 동안의 시간 인덱스 생성
        start_date = self.backtest_config["start_date"]
        end_date = self.backtest_config["end_date"]
        timeframe = self.backtest_config["timeframe"]
        
        # 시간 간격 설정
        if timeframe == "1m":
            freq = "1min"
        elif timeframe == "5m":
            freq = "5min"
        elif timeframe == "15m":
            freq = "15min"
        elif timeframe == "30m":
            freq = "30min"
        elif timeframe == "1h":
            freq = "1h"
        elif timeframe == "4h":
            freq = "4h"
        elif timeframe == "1d":
            freq = "1D"
        else:
            freq = "1H"  # 기본값
        
        # 시간 인덱스 생성
        timestamps = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # 기본 데이터 생성
        n = len(timestamps)
        base_price = 50000.0
        
        # 랜덤 가격 변동 생성
        np.random.seed(42)  # 재현 가능한 결과를 위한 시드 설정
        price_changes = np.random.normal(0, 1, n) * base_price * 0.01
        
        # 누적 가격 변동 계산
        cumulative_changes = np.cumsum(price_changes)
        
        # OHLCV 데이터 생성
        close_prices = base_price + cumulative_changes
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = base_price
        
        high_prices = np.maximum(open_prices, close_prices) * (1 + np.random.random(n) * 0.01)
        low_prices = np.minimum(open_prices, close_prices) * (1 - np.random.random(n) * 0.01)
        volumes = np.random.random(n) * 10 + 1  # 1-11 범위의 거래량
        
        # DataFrame 생성
        self.test_data = pd.DataFrame({
            'timestamp': timestamps,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        })
        
        # timestamp를 인덱스로 설정
        self.test_data.set_index('timestamp', inplace=True)
        
        # 이동 평균 계산
        self.test_data['SMA_5'] = self.test_data['close'].rolling(window=5).mean()
        self.test_data['SMA_10'] = self.test_data['close'].rolling(window=10).mean()
    
    def test_init_backtest_runner(self):
        """
        백테스트 실행기 초기화 테스트
        """
        self.assertEqual(self.backtest_runner.strategy, self.strategy)
        self.assertEqual(self.backtest_runner.config, self.backtest_config)
        self.assertEqual(self.backtest_runner.symbol, self.backtest_config["symbol"])
        self.assertEqual(self.backtest_runner.timeframe, self.backtest_config["timeframe"])
        self.assertEqual(self.backtest_runner.start_date, self.backtest_config["start_date"])
        self.assertEqual(self.backtest_runner.end_date, self.backtest_config["end_date"])
        self.assertEqual(self.backtest_runner.initial_capital, self.backtest_config["initial_capital"])
        self.assertEqual(self.backtest_runner.current_capital, self.backtest_config["initial_capital"])
        self.assertEqual(self.backtest_runner.fee_rate, self.backtest_config["fee_rate"])
        self.assertEqual(self.backtest_runner.slippage, self.backtest_config["slippage"])
        self.assertEqual(len(self.backtest_runner.trades), 0)
        self.assertIsNone(self.backtest_runner.position)
    
    @patch('upbit_auto_trading.business_logic.backtester.backtest_runner.MarketDataStorage')
    def test_load_market_data(self, mock_storage_class):
        """
        시장 데이터 로드 테스트
        """
        print("\n=== 테스트 id 07_1_2: test_load_market_data ===")
        # Mock 설정
        mock_storage_instance = mock_storage_class.return_value
        mock_storage_instance.load_market_data.return_value = self.test_data
        
        # 시장 데이터 로드
        data = self.backtest_runner.load_market_data()
        
        # 검증
        self.assertIsNotNone(data)
        self.assertEqual(len(data), len(self.test_data))
        mock_storage_instance.load_market_data.assert_called_once_with(
            self.backtest_config["symbol"],
            self.backtest_config["timeframe"],
            self.backtest_config["start_date"],
            self.backtest_config["end_date"]
        )
    
    @patch('upbit_auto_trading.business_logic.backtester.backtest_runner.IndicatorProcessor')
    def test_prepare_data(self, mock_processor_class):
        """
        데이터 준비 테스트
        """
        print("\n=== 테스트 id 07_1_3: test_prepare_data ===")
        # Mock 설정
        mock_processor_instance = mock_processor_class.return_value
        mock_processor_instance.calculate_indicators.return_value = self.test_data
        
        # 데이터 준비
        with patch.object(self.backtest_runner, 'load_market_data', return_value=self.test_data):
            data = self.backtest_runner.prepare_data()
        
        # 검증
        self.assertIsNotNone(data)
        self.assertEqual(len(data), len(self.test_data))
        mock_processor_instance.calculate_indicators.assert_called_once()
    
    def test_generate_signals(self):
        """
        매매 신호 생성 테스트
        """
        print("\n=== 테스트 id 07_1_4: test_generate_signals ===")
        # 신호 생성
        data_with_signals = self.backtest_runner.generate_signals(self.test_data)
        
        # 검증
        self.assertIsNotNone(data_with_signals)
        self.assertIn('signal', data_with_signals.columns)
        
        # 신호 값이 -1, 0, 1 중 하나인지 확인
        unique_signals = data_with_signals['signal'].unique()
        for signal in unique_signals:
            self.assertIn(signal, [-1, 0, 1])
    
    def test_execute_backtest(self):
        """
        백테스트 실행 테스트
        """
        print("\n=== 테스트 id 07_1_5: test_execute_backtest ===")
        # 백테스트 실행
        with patch.object(self.backtest_runner, 'prepare_data', return_value=self.test_data):
            with patch.object(self.backtest_runner, 'generate_signals', return_value=self.test_data.assign(signal=[1, 0, -1] * (len(self.test_data) // 3) + [0] * (len(self.test_data) % 3))):
                results = self.backtest_runner.execute_backtest()
        
        # 검증
        self.assertIsNotNone(results)
        self.assertIn('trades', results)
        self.assertIn('performance_metrics', results)
        self.assertIn('equity_curve', results)
    
    def test_process_signals(self):
        """
        신호 처리 테스트
        """
        print("\n=== 테스트 id 07_1_6: test_process_signals ===")
        # 테스트 데이터 준비
        test_data = self.test_data.copy()
        test_data['signal'] = [0] * 5 + [1] + [0] * 5 + [-1] + [0] * (len(test_data) - 12)
        
        # 신호 처리
        self.backtest_runner.process_signals(test_data)
        
        # 검증
        self.assertGreater(len(self.backtest_runner.trades), 0)
    
    def test_calculate_performance_metrics(self):
        """
        성과 지표 계산 테스트
        """
        print("\n=== 테스트 id 07_1_7: test_calculate_performance_metrics ===")
        # 테스트 데이터 준비
        test_data = self.test_data.copy()
        test_data['signal'] = [0] * 5 + [1] + [0] * 5 + [-1] + [0] * (len(test_data) - 12)
        
        # 거래 실행
        self.backtest_runner.process_signals(test_data)
        
        # 성과 지표 계산
        metrics = self.backtest_runner.calculate_performance_metrics()
        
        # 검증
        self.assertIsNotNone(metrics)
        self.assertIn('total_return', metrics)
        self.assertIn('max_drawdown', metrics)
        self.assertIn('win_rate', metrics)
        self.assertIn('profit_factor', metrics)
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('sortino_ratio', metrics)
        self.assertIn('trades_count', metrics)
    
    def test_generate_equity_curve(self):
        """
        자본 곡선 생성 테스트
        """
        print("\n=== 테스트 id 07_1_8: test_generate_equity_curve ===")
        # 테스트 데이터 준비
        test_data = self.test_data.copy()
        test_data['signal'] = [0] * 5 + [1] + [0] * 5 + [-1] + [0] * (len(test_data) - 12)
        
        # 거래 실행
        self.backtest_runner.process_signals(test_data)
        
        # 자본 곡선 생성
        equity_curve = self.backtest_runner.generate_equity_curve(test_data)
        
        # 검증
        self.assertIsNotNone(equity_curve)
        self.assertEqual(len(equity_curve), len(test_data))
        self.assertIn('equity', equity_curve.columns)
    
    def test_execute_buy_order(self):
        """
        매수 주문 실행 테스트
        """
        print("\n=== 테스트 id 07_1_9: test_execute_buy_order ===")
        # 초기 자본 저장
        initial_capital = self.backtest_runner.current_capital
        
        # 매수 주문 실행
        timestamp = self.test_data.index[10]
        price = self.test_data.loc[timestamp, 'close']
        self.backtest_runner.execute_buy_order(timestamp, price)
        
        # 검증
        self.assertIsNotNone(self.backtest_runner.position)
        self.assertEqual(self.backtest_runner.position['side'], 'long')
        self.assertEqual(self.backtest_runner.position['entry_price'], price * (1 + self.backtest_runner.slippage))
        self.assertLess(self.backtest_runner.current_capital, initial_capital)
    
    def test_execute_sell_order(self):
        """
        매도 주문 실행 테스트
        """
        print("\n=== 테스트 id 07_1_10: test_execute_sell_order ===")
        # 매수 주문 실행
        buy_timestamp = self.test_data.index[10]
        buy_price = self.test_data.loc[buy_timestamp, 'close']
        self.backtest_runner.execute_buy_order(buy_timestamp, buy_price)
        
        # 매수 후 자본 저장
        after_buy_capital = self.backtest_runner.current_capital
        
        # 매도 주문 실행
        sell_timestamp = self.test_data.index[15]
        sell_price = self.test_data.loc[sell_timestamp, 'close']
        self.backtest_runner.execute_sell_order(sell_timestamp, sell_price)
        
        # 검증
        self.assertIsNone(self.backtest_runner.position)
        self.assertNotEqual(self.backtest_runner.current_capital, after_buy_capital)
        self.assertEqual(len(self.backtest_runner.trades), 1)
    
    def test_calculate_trade_metrics(self):
        """
        거래 지표 계산 테스트
        """
        print("\n=== 테스트 id 07_1_11: test_calculate_trade_metrics ===")
        # 매수 주문 실행
        buy_timestamp = self.test_data.index[10]
        buy_price = self.test_data.loc[buy_timestamp, 'close']
        self.backtest_runner.execute_buy_order(buy_timestamp, buy_price)
        
        # 매도 주문 실행
        sell_timestamp = self.test_data.index[15]
        sell_price = self.test_data.loc[sell_timestamp, 'close']
        self.backtest_runner.execute_sell_order(sell_timestamp, sell_price)
        
        # 거래 지표 계산
        trade = self.backtest_runner.trades[0]
        metrics = self.backtest_runner.calculate_trade_metrics(trade)
        
        # 검증
        self.assertIsNotNone(metrics)
        self.assertIn('profit_loss', metrics)
        self.assertIn('profit_loss_percent', metrics)
        self.assertIn('duration', metrics)
    
    def test_reset(self):
        """
        백테스트 초기화 테스트
        """
        print("\n=== 테스트 id 07_1_12: test_reset ===")
        # 매수 주문 실행
        buy_timestamp = self.test_data.index[10]
        buy_price = self.test_data.loc[buy_timestamp, 'close']
        self.backtest_runner.execute_buy_order(buy_timestamp, buy_price)
        
        # 매도 주문 실행
        sell_timestamp = self.test_data.index[15]
        sell_price = self.test_data.loc[sell_timestamp, 'close']
        self.backtest_runner.execute_sell_order(sell_timestamp, sell_price)
        
        # 초기화
        self.backtest_runner.reset()
        
        # 검증
        self.assertEqual(self.backtest_runner.current_capital, self.backtest_config["initial_capital"])
        self.assertEqual(len(self.backtest_runner.trades), 0)
        self.assertIsNone(self.backtest_runner.position)


if __name__ == '__main__':
    unittest.main()