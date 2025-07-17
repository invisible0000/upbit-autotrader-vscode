"""
백테스트 결과 분석기 테스트 모듈

이 모듈은 백테스트 결과 분석기의 기능을 테스트합니다.
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# matplotlib 및 seaborn 임포트 시도
try:
    import matplotlib
    matplotlib.use('Agg')  # 헤드리스 환경에서 실행하기 위한 백엔드 설정
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    print("경고: matplotlib 또는 seaborn을 찾을 수 없습니다. 시각화 테스트가 제한됩니다.")

from upbit_auto_trading.business_logic.backtester.backtest_analyzer import BacktestAnalyzer
from upbit_auto_trading.business_logic.backtester.backtest_runner import BacktestRunner
from upbit_auto_trading.business_logic.strategy.basic_strategies import MovingAverageCrossStrategy


class TestBacktestAnalyzer(unittest.TestCase):
    """
    백테스트 결과 분석기 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        print("\n=== 테스트 id 07_2_1: test_init_backtest_analyzer ===")
        # 테스트용 백테스트 결과 생성
        self.create_test_backtest_results()
        
        # 백테스트 분석기 생성
        self.analyzer = BacktestAnalyzer(self.backtest_results)
    
    def create_test_backtest_results(self):
        """
        테스트용 백테스트 결과 생성
        """
        # 테스트용 전략 생성
        strategy = MovingAverageCrossStrategy({
            "short_window": 5,
            "long_window": 10
        })
        
        # 테스트용 백테스트 설정
        backtest_config = {
            "symbol": "KRW-BTC",
            "timeframe": "1h",
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 1, 31),
            "initial_capital": 1000000.0,
            "fee_rate": 0.0005,  # 0.05% 수수료
            "slippage": 0.0002,  # 0.02% 슬리피지
        }
        
        # 테스트용 OHLCV 데이터 생성
        self.create_test_data(backtest_config)
        
        # 테스트용 거래 내역 생성
        self.create_test_trades()
        
        # 테스트용 성과 지표 생성
        self.create_test_performance_metrics()
        
        # 테스트용 자본 곡선 생성
        self.create_test_equity_curve()
        
        # 백테스트 결과 생성
        self.backtest_results = {
            "trades": self.test_trades,
            "performance_metrics": self.test_performance_metrics,
            "equity_curve": self.test_equity_curve,
            "config": backtest_config,
            "strategy": strategy
        }
    
    def create_test_data(self, config):
        """
        테스트용 OHLCV 데이터 생성
        """
        # 테스트 기간 동안의 시간 인덱스 생성
        start_date = config["start_date"]
        end_date = config["end_date"]
        timeframe = config["timeframe"]
        
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
    
    def create_test_trades(self):
        """
        테스트용 거래 내역 생성
        """
        # 10개의 테스트 거래 생성
        self.test_trades = []
        
        # 시간 간격 설정
        start_time = datetime(2023, 1, 1, 0, 0, 0)
        
        for i in range(10):
            # 매수 시간
            entry_time = start_time + timedelta(hours=i*12)
            
            # 매도 시간
            exit_time = entry_time + timedelta(hours=6)
            
            # 가격 설정
            entry_price = 50000.0 + i * 1000.0
            
            # 홀수 번째 거래는 이익, 짝수 번째 거래는 손실
            if i % 2 == 0:
                exit_price = entry_price * 1.05  # 5% 이익
                profit_loss = entry_price * 0.05 * 0.01  # 수량 0.01
                profit_loss_percent = 5.0
            else:
                exit_price = entry_price * 0.97  # 3% 손실
                profit_loss = entry_price * -0.03 * 0.01  # 수량 0.01
                profit_loss_percent = -3.0
            
            # 수수료 계산
            entry_fee = entry_price * 0.01 * 0.0005  # 0.05% 수수료
            exit_fee = exit_price * 0.01 * 0.0005  # 0.05% 수수료
            
            # 거래 생성
            trade = {
                'id': f'trade-{i}',
                'symbol': 'KRW-BTC',
                'entry_time': entry_time,
                'entry_price': entry_price,
                'exit_time': exit_time,
                'exit_price': exit_price,
                'quantity': 0.01,
                'side': 'long',
                'entry_fee': entry_fee,
                'exit_fee': exit_fee,
                'profit_loss': profit_loss,
                'profit_loss_percent': profit_loss_percent,
                'duration': exit_time - entry_time,
                'total_fee': entry_fee + exit_fee
            }
            
            self.test_trades.append(trade)
    
    def create_test_performance_metrics(self):
        """
        테스트용 성과 지표 생성
        """
        # 성과 지표 생성
        self.test_performance_metrics = {
            'total_return': 10000.0,
            'total_return_percent': 10.0,
            'annualized_return': 120.0,
            'max_drawdown': 5.0,
            'win_rate': 60.0,
            'profit_factor': 2.0,
            'sharpe_ratio': 1.5,
            'sortino_ratio': 2.0,
            'trades_count': 10,
            'avg_profit_per_trade': 1000.0,
            'avg_profit_percent_per_trade': 1.0,
            'avg_holding_period': timedelta(hours=6)
        }
    
    def create_test_equity_curve(self):
        """
        테스트용 자본 곡선 생성
        """
        # 자본 곡선 생성
        self.test_equity_curve = self.test_data[['close']].copy()
        
        # 초기 자본
        initial_capital = 1000000.0
        
        # 자본 곡선 생성
        n = len(self.test_equity_curve)
        equity = np.linspace(initial_capital, initial_capital * 1.1, n)  # 10% 수익률로 선형 증가
        
        # 약간의 변동성 추가
        np.random.seed(42)
        noise = np.random.normal(0, 1, n) * initial_capital * 0.005
        equity = equity + noise
        
        # 자본 곡선에 추가
        self.test_equity_curve['equity'] = equity
    
    def test_init_backtest_analyzer(self):
        """
        백테스트 분석기 초기화 테스트
        """
        self.assertEqual(self.analyzer.results, self.backtest_results)
        self.assertEqual(self.analyzer.trades, self.test_trades)
        self.assertEqual(self.analyzer.performance_metrics, self.test_performance_metrics)
        self.assertEqual(self.analyzer.equity_curve.equals(self.test_equity_curve), True)
    
    def test_calculate_advanced_metrics(self):
        """
        고급 성과 지표 계산 테스트
        """
        print("\n=== 테스트 id 07_2_2: test_calculate_advanced_metrics ===")
        # 고급 성과 지표 계산
        advanced_metrics = self.analyzer.calculate_advanced_metrics()
        
        # 검증
        self.assertIsNotNone(advanced_metrics)
        self.assertIn('calmar_ratio', advanced_metrics)
        self.assertIn('ulcer_index', advanced_metrics)
        self.assertIn('profit_to_max_drawdown', advanced_metrics)
        self.assertIn('avg_profit_to_avg_loss', advanced_metrics)
        self.assertIn('win_loss_ratio', advanced_metrics)
        self.assertIn('expectancy', advanced_metrics)
        
        # 값 검증
        self.assertGreaterEqual(advanced_metrics['calmar_ratio'], 0)
        self.assertGreaterEqual(advanced_metrics['ulcer_index'], 0)
        self.assertGreaterEqual(advanced_metrics['profit_to_max_drawdown'], 0)
    
    def test_analyze_trades(self):
        """
        거래 분석 테스트
        """
        print("\n=== 테스트 id 07_2_3: test_analyze_trades ===")
        # 거래 분석
        trade_analysis = self.analyzer.analyze_trades()
        
        # 검증
        self.assertIsNotNone(trade_analysis)
        self.assertIn('profitable_trades', trade_analysis)
        self.assertIn('losing_trades', trade_analysis)
        self.assertIn('avg_profit_trade', trade_analysis)
        self.assertIn('avg_loss_trade', trade_analysis)
        self.assertIn('max_profit_trade', trade_analysis)
        self.assertIn('max_loss_trade', trade_analysis)
        self.assertIn('avg_holding_period_profit', trade_analysis)
        self.assertIn('avg_holding_period_loss', trade_analysis)
        self.assertIn('profit_by_day_of_week', trade_analysis)
        self.assertIn('profit_by_hour', trade_analysis)
        
        # 값 검증
        self.assertEqual(trade_analysis['profitable_trades'] + trade_analysis['losing_trades'], len(self.test_trades))
        self.assertGreaterEqual(trade_analysis['avg_profit_trade'], 0)
        self.assertLessEqual(trade_analysis['avg_loss_trade'], 0)
    
    def test_analyze_drawdowns(self):
        """
        손실폭 분석 테스트
        """
        print("\n=== 테스트 id 07_2_4: test_analyze_drawdowns ===")
        # 손실폭 분석
        drawdowns = self.analyzer.analyze_drawdowns()
        
        # 검증
        self.assertIsNotNone(drawdowns)
        self.assertIsInstance(drawdowns, pd.DataFrame)
        self.assertIn('drawdown_percent', drawdowns.columns)
        self.assertIn('duration', drawdowns.columns)
        self.assertIn('start_date', drawdowns.columns)
        self.assertIn('end_date', drawdowns.columns)
        self.assertIn('recovery_date', drawdowns.columns)
    
    def test_analyze_monthly_returns(self):
        """
        월별 수익률 분석 테스트
        """
        print("\n=== 테스트 id 07_2_5: test_analyze_monthly_returns ===")
        # 월별 수익률 분석
        monthly_returns = self.analyzer.analyze_monthly_returns()
        
        # 검증
        self.assertIsNotNone(monthly_returns)
        self.assertIsInstance(monthly_returns, pd.DataFrame)
        
        # 2023년 1월 데이터만 있으므로 1개의 행만 있어야 함
        self.assertEqual(len(monthly_returns), 1)
    
    def test_plot_equity_curve(self):
        """
        자본 곡선 시각화 테스트
        """
        print("\n=== 테스트 id 07_2_6: test_plot_equity_curve ===")
        
        # 시각화 라이브러리가 없으면 테스트 스킵
        if not VISUALIZATION_AVAILABLE:
            print("시각화 라이브러리가 없어 테스트를 건너뜁니다.")
            self.skipTest("matplotlib 또는 seaborn이 설치되지 않았습니다.")
            return
            
        # 자본 곡선 시각화
        fig = self.analyzer.plot_equity_curve()
        
        # 검증
        self.assertIsNotNone(fig)
    
    def test_plot_drawdowns(self):
        """
        손실폭 시각화 테스트
        """
        print("\n=== 테스트 id 07_2_7: test_plot_drawdowns ===")
        
        # 시각화 라이브러리가 없으면 테스트 스킵
        if not VISUALIZATION_AVAILABLE:
            print("시각화 라이브러리가 없어 테스트를 건너뜁니다.")
            self.skipTest("matplotlib 또는 seaborn이 설치되지 않았습니다.")
            return
            
        # 손실폭 시각화
        fig = self.analyzer.plot_drawdowns()
        
        # 검증
        self.assertIsNotNone(fig)
    
    def test_plot_monthly_returns(self):
        """
        월별 수익률 시각화 테스트
        """
        print("\n=== 테스트 id 07_2_8: test_plot_monthly_returns ===")
        
        # 시각화 라이브러리가 없으면 테스트 스킵
        if not VISUALIZATION_AVAILABLE:
            print("시각화 라이브러리가 없어 테스트를 건너뜁니다.")
            self.skipTest("matplotlib 또는 seaborn이 설치되지 않았습니다.")
            return
            
        # 월별 수익률 시각화
        fig = self.analyzer.plot_monthly_returns()
        
        # 검증
        self.assertIsNotNone(fig)
    
    def test_plot_trade_analysis(self):
        """
        거래 분석 시각화 테스트
        """
        print("\n=== 테스트 id 07_2_9: test_plot_trade_analysis ===")
        
        # 시각화 라이브러리가 없으면 테스트 스킵
        if not VISUALIZATION_AVAILABLE:
            print("시각화 라이브러리가 없어 테스트를 건너뜁니다.")
            self.skipTest("matplotlib 또는 seaborn이 설치되지 않았습니다.")
            return
            
        # 거래 분석 시각화
        fig = self.analyzer.plot_trade_analysis()
        
        # 검증
        self.assertIsNotNone(fig)
    
    def test_generate_report(self):
        """
        보고서 생성 테스트
        """
        print("\n=== 테스트 id 07_2_10: test_generate_report ===")
        # 보고서 생성
        report = self.analyzer.generate_report()
        
        # 검증
        self.assertIsNotNone(report)
        self.assertIn('summary', report)
        self.assertIn('performance_metrics', report)
        self.assertIn('advanced_metrics', report)
        self.assertIn('trade_analysis', report)
        self.assertIn('drawdowns', report)
        self.assertIn('monthly_returns', report)
        self.assertIn('figures', report)


if __name__ == '__main__':
    unittest.main()