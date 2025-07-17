#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
포트폴리오 백테스트 기능 테스트 모듈

이 모듈은 포트폴리오 백테스트 실행, 성과 지표 계산, 결과 시각화 기능을 테스트합니다.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import logging

from upbit_auto_trading.business_logic.portfolio.portfolio_backtest import PortfolioBacktest
from upbit_auto_trading.business_logic.backtester.backtest_runner import BacktestRunner
from upbit_auto_trading.business_logic.portfolio.portfolio_manager import PortfolioManager
from upbit_auto_trading.business_logic.portfolio.portfolio_performance import PortfolioPerformance
from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface


class TestPortfolioBacktest(unittest.TestCase):
    """포트폴리오 백테스트 기능 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 세션 모의 객체 생성
        self.mock_session = MagicMock()
        
        # 포트폴리오 관리자 모의 객체 생성
        self.portfolio_manager = MagicMock(spec=PortfolioManager)
        
        # 포트폴리오 성과 계산기 모의 객체 생성
        self.portfolio_performance = MagicMock(spec=PortfolioPerformance)
        
        # 백테스트 설정
        self.backtest_config = {
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 3, 31),
            "initial_capital": 10000000,  # 1천만원
            "fee_rate": 0.0005,  # 0.05%
            "slippage": 0.0002,  # 0.02%
            "timeframe": "1d"
        }
        
        # 포트폴리오 정보 설정
        self.portfolio_id = "test-portfolio-id"
        self.portfolio_data = {
            "id": self.portfolio_id,
            "name": "테스트 포트폴리오",
            "description": "테스트용 포트폴리오",
            "coins": [
                {
                    "symbol": "KRW-BTC",
                    "strategy_id": "strategy-1",
                    "weight": 0.6
                },
                {
                    "symbol": "KRW-ETH",
                    "strategy_id": "strategy-2",
                    "weight": 0.4
                }
            ]
        }
        
        # 포트폴리오 관리자 모의 객체 설정
        self.portfolio_manager.get_portfolio.return_value = self.portfolio_data
        
        # 전략 모의 객체 생성
        self.mock_strategy1 = MagicMock(spec=StrategyInterface)
        self.mock_strategy2 = MagicMock(spec=StrategyInterface)
        
        # 백테스트 러너 모의 객체 생성
        self.mock_backtest_runner1 = MagicMock(spec=BacktestRunner)
        self.mock_backtest_runner2 = MagicMock(spec=BacktestRunner)
        
        # 백테스트 결과 설정
        self.backtest_result1 = {
            "trades": [{"id": "trade-1", "profit_loss": 500000}],
            "performance_metrics": {
                "total_return": 500000,
                "total_return_percent": 8.33,
                "max_drawdown": 3.5,
                "win_rate": 60.0
            },
            "equity_curve": pd.DataFrame({
                "close": [60000000, 61000000, 62000000],
                "equity": [6000000, 6100000, 6500000]
            }, index=[
                datetime(2023, 1, 1),
                datetime(2023, 2, 1),
                datetime(2023, 3, 1)
            ])
        }
        
        self.backtest_result2 = {
            "trades": [{"id": "trade-2", "profit_loss": 300000}],
            "performance_metrics": {
                "total_return": 300000,
                "total_return_percent": 7.5,
                "max_drawdown": 2.8,
                "win_rate": 55.0
            },
            "equity_curve": pd.DataFrame({
                "close": [40000000, 41000000, 42000000],
                "equity": [4000000, 4050000, 4300000]
            }, index=[
                datetime(2023, 1, 1),
                datetime(2023, 2, 1),
                datetime(2023, 3, 1)
            ])
        }
        
        # 백테스트 러너 모의 객체 설정
        self.mock_backtest_runner1.execute_backtest.return_value = self.backtest_result1
        self.mock_backtest_runner2.execute_backtest.return_value = self.backtest_result2
        
        # 포트폴리오 백테스트 객체 생성
        self.portfolio_backtest = PortfolioBacktest(
            self.portfolio_manager,
            self.portfolio_performance,
            self.mock_session
        )

    def test_07_3_1_portfolio_backtest_initialization(self):
        """=== 테스트 id 07_3_1: 포트폴리오 백테스트 초기화 테스트 ==="""
        print("\n=== 테스트 id 07_3_1: 포트폴리오 백테스트 초기화 테스트 ===")
        
        # 포트폴리오 백테스트 객체가 올바르게 초기화되었는지 확인
        self.assertIsNotNone(self.portfolio_backtest)
        self.assertEqual(self.portfolio_backtest.portfolio_manager, self.portfolio_manager)
        self.assertEqual(self.portfolio_backtest.portfolio_performance, self.portfolio_performance)
        self.assertEqual(self.portfolio_backtest.session, self.mock_session)
        
        print("포트폴리오 백테스트 객체가 올바르게 초기화되었습니다.")

    @patch("upbit_auto_trading.business_logic.portfolio.portfolio_backtest.BacktestRunner")
    @patch("upbit_auto_trading.business_logic.portfolio.portfolio_backtest.StrategyFactory")
    def test_07_3_2_run_portfolio_backtest(self, mock_strategy_factory_class, mock_backtest_runner_class):
        """=== 테스트 id 07_3_2: 포트폴리오 백테스트 실행 테스트 ==="""
        print("\n=== 테스트 id 07_3_2: 포트폴리오 백테스트 실행 테스트 ===")
        
        # 전략 팩토리 인스턴스 모의 객체 설정
        mock_strategy_factory = mock_strategy_factory_class.return_value
        mock_strategy_factory.get_strategy.side_effect = [self.mock_strategy1, self.mock_strategy2]
        
        # 백테스트 러너 클래스 모의 객체 설정
        mock_backtest_runner_class.side_effect = [self.mock_backtest_runner1, self.mock_backtest_runner2]
        
        # 포트폴리오 백테스트 실행
        result = self.portfolio_backtest.run_portfolio_backtest(self.portfolio_id, self.backtest_config)
        
        # 포트폴리오 정보 조회 확인
        self.portfolio_manager.get_portfolio.assert_called_once_with(self.portfolio_id)
        
        # 전략 팩토리 생성 확인
        mock_strategy_factory_class.assert_called_once_with(self.mock_session)
        
        # 전략 팩토리 호출 확인
        mock_strategy_factory.get_strategy.assert_any_call("strategy-1", self.mock_session)
        mock_strategy_factory.get_strategy.assert_any_call("strategy-2", self.mock_session)
        
        # 백테스트 러너 생성 확인
        mock_backtest_runner_class.assert_any_call(self.mock_strategy1, {
            **self.backtest_config,
            "symbol": "KRW-BTC"
        })
        mock_backtest_runner_class.assert_any_call(self.mock_strategy2, {
            **self.backtest_config,
            "symbol": "KRW-ETH"
        })
        
        # 백테스트 실행 확인
        self.mock_backtest_runner1.execute_backtest.assert_called_once()
        self.mock_backtest_runner2.execute_backtest.assert_called_once()
        
        # 결과 확인
        self.assertIn("portfolio_id", result)
        self.assertIn("backtest_results", result)
        self.assertIn("portfolio_performance", result)
        self.assertIn("combined_equity_curve", result)
        
        # 백테스트 결과 확인
        self.assertEqual(len(result["backtest_results"]), 2)
        self.assertEqual(result["backtest_results"][0]["symbol"], "KRW-BTC")
        self.assertEqual(result["backtest_results"][1]["symbol"], "KRW-ETH")
        
        print("포트폴리오 백테스트가 올바르게 실행되었습니다.")

    def test_07_3_3_calculate_portfolio_performance_metrics(self):
        """=== 테스트 id 07_3_3: 포트폴리오 성과 지표 계산 테스트 ==="""
        print("\n=== 테스트 id 07_3_3: 포트폴리오 성과 지표 계산 테스트 ===")
        
        # 백테스트 결과 설정
        backtest_results = [
            {
                "symbol": "KRW-BTC",
                "weight": 0.6,
                "result": self.backtest_result1
            },
            {
                "symbol": "KRW-ETH",
                "weight": 0.4,
                "result": self.backtest_result2
            }
        ]
        
        # 포트폴리오 성과 지표 계산
        metrics = self.portfolio_backtest.calculate_portfolio_performance_metrics(backtest_results)
        
        # 성과 지표 확인
        self.assertIn("total_return", metrics)
        self.assertIn("total_return_percent", metrics)
        self.assertIn("max_drawdown", metrics)
        self.assertIn("win_rate", metrics)
        self.assertIn("sharpe_ratio", metrics)
        self.assertIn("coin_performances", metrics)
        
        # 가중 평균 계산 확인
        expected_total_return_percent = 0.6 * 8.33 + 0.4 * 7.5
        self.assertAlmostEqual(metrics["total_return_percent"], expected_total_return_percent, places=1)
        
        # 코인별 성과 확인
        self.assertEqual(len(metrics["coin_performances"]), 2)
        self.assertEqual(metrics["coin_performances"][0]["symbol"], "KRW-BTC")
        self.assertEqual(metrics["coin_performances"][1]["symbol"], "KRW-ETH")
        
        print("포트폴리오 성과 지표가 올바르게 계산되었습니다.")

    def test_07_3_4_combine_equity_curves(self):
        """=== 테스트 id 07_3_4: 자본 곡선 결합 테스트 ==="""
        print("\n=== 테스트 id 07_3_4: 자본 곡선 결합 테스트 ===")
        
        # 백테스트 결과 설정
        backtest_results = [
            {
                "symbol": "KRW-BTC",
                "weight": 0.6,
                "result": self.backtest_result1
            },
            {
                "symbol": "KRW-ETH",
                "weight": 0.4,
                "result": self.backtest_result2
            }
        ]
        
        # 초기 자본 설정
        initial_capital = 10000000
        
        # 자본 곡선 결합
        combined_curve = self.portfolio_backtest.combine_equity_curves(backtest_results, initial_capital)
        
        # 결합된 자본 곡선 확인
        self.assertIsInstance(combined_curve, pd.DataFrame)
        self.assertIn("equity", combined_curve.columns)
        self.assertEqual(len(combined_curve), 3)  # 3개의 데이터 포인트
        
        # 첫 번째 데이터 포인트 확인
        expected_first_equity = 0.6 * 6000000 + 0.4 * 4000000
        self.assertAlmostEqual(combined_curve["equity"].iloc[0], expected_first_equity, delta=1)
        
        # 마지막 데이터 포인트 확인
        expected_last_equity = 0.6 * 6500000 + 0.4 * 4300000
        self.assertAlmostEqual(combined_curve["equity"].iloc[-1], expected_last_equity, delta=1)
        
        print("자본 곡선이 올바르게 결합되었습니다.")

    def test_07_3_5_visualize_portfolio_backtest_results(self):
        """=== 테스트 id 07_3_5: 포트폴리오 백테스트 결과 시각화 테스트 ==="""
        print("\n=== 테스트 id 07_3_5: 포트폴리오 백테스트 결과 시각화 테스트 ===")
        
        # 백테스트 결과 설정
        backtest_results = [
            {
                "symbol": "KRW-BTC",
                "weight": 0.6,
                "result": self.backtest_result1
            },
            {
                "symbol": "KRW-ETH",
                "weight": 0.4,
                "result": self.backtest_result2
            }
        ]
        
        # 포트폴리오 성과 지표 설정
        portfolio_metrics = {
            "total_return": 420000,
            "total_return_percent": 8.0,
            "max_drawdown": 3.2,
            "win_rate": 58.0,
            "sharpe_ratio": 1.5,
            "coin_performances": [
                {
                    "symbol": "KRW-BTC",
                    "weight": 0.6,
                    "return_percent": 8.33,
                    "contribution": 5.0
                },
                {
                    "symbol": "KRW-ETH",
                    "weight": 0.4,
                    "return_percent": 7.5,
                    "contribution": 3.0
                }
            ]
        }
        
        # 결합된 자본 곡선 설정
        combined_equity_curve = pd.DataFrame({
            "equity": [10000000, 10200000, 10420000]
        }, index=[
            datetime(2023, 1, 1),
            datetime(2023, 2, 1),
            datetime(2023, 3, 1)
        ])
        
        # 포트폴리오 백테스트 결과 시각화
        figures = self.portfolio_backtest.visualize_portfolio_backtest_results(
            backtest_results,
            portfolio_metrics,
            combined_equity_curve
        )
        
        # 결과 확인
        self.assertIn("equity_curve", figures)
        self.assertIn("coin_contribution", figures)
        self.assertIn("performance_comparison", figures)
        
        print("포트폴리오 백테스트 결과가 올바르게 시각화되었습니다.")


if __name__ == "__main__":
    unittest.main()