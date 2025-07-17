#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
백테스트 결과 저장 및 비교 기능 테스트 모듈

이 모듈은 백테스트 결과를 저장하고, 불러오고, 비교하는 기능을 테스트합니다.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, ANY
import logging
import json
import os
import tempfile
import shutil

from upbit_auto_trading.business_logic.backtester.backtest_results_manager import BacktestResultsManager
from upbit_auto_trading.data_layer.models import Backtest


class TestBacktestResultsManagement(unittest.TestCase):
    """백테스트 결과 저장 및 비교 기능 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        # 로깅 설정
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 세션 모의 객체 생성
        self.mock_session = MagicMock()
        
        # 임시 디렉토리 생성 (파일 저장 테스트용)
        self.temp_dir = tempfile.mkdtemp()
        
        # 백테스트 결과 관리자 생성
        self.results_manager = BacktestResultsManager(self.mock_session, results_dir=self.temp_dir)
        
        # 테스트용 백테스트 결과 생성
        self.backtest_result1 = {
            "id": "backtest-1",
            "strategy_id": "strategy-1",
            "symbol": "KRW-BTC",
            "timeframe": "1h",
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 3, 31),
            "initial_capital": 10000000,
            "trades": [
                {
                    "id": "trade-1",
                    "entry_time": datetime(2023, 1, 5),
                    "exit_time": datetime(2023, 1, 10),
                    "entry_price": 25000000,
                    "exit_price": 27000000,
                    "quantity": 0.4,
                    "profit_loss": 800000,
                    "profit_loss_percent": 8.0
                }
            ],
            "performance_metrics": {
                "total_return": 800000,
                "total_return_percent": 8.0,
                "max_drawdown": 3.5,
                "win_rate": 60.0,
                "sharpe_ratio": 1.2
            },
            "equity_curve": pd.DataFrame({
                "equity": [10000000, 10400000, 10800000]
            }, index=[
                datetime(2023, 1, 1),
                datetime(2023, 2, 1),
                datetime(2023, 3, 1)
            ])
        }
        
        self.backtest_result2 = {
            "id": "backtest-2",
            "strategy_id": "strategy-2",
            "symbol": "KRW-ETH",
            "timeframe": "1h",
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 3, 31),
            "initial_capital": 10000000,
            "trades": [
                {
                    "id": "trade-2",
                    "entry_time": datetime(2023, 1, 15),
                    "exit_time": datetime(2023, 1, 20),
                    "entry_price": 1800000,
                    "exit_price": 1900000,
                    "quantity": 5.0,
                    "profit_loss": 500000,
                    "profit_loss_percent": 5.0
                }
            ],
            "performance_metrics": {
                "total_return": 500000,
                "total_return_percent": 5.0,
                "max_drawdown": 2.8,
                "win_rate": 55.0,
                "sharpe_ratio": 1.0
            },
            "equity_curve": pd.DataFrame({
                "equity": [10000000, 10250000, 10500000]
            }, index=[
                datetime(2023, 1, 1),
                datetime(2023, 2, 1),
                datetime(2023, 3, 1)
            ])
        }
        
        # 포트폴리오 백테스트 결과
        self.portfolio_backtest_result = {
            "id": "portfolio-backtest-1",
            "portfolio_id": "portfolio-1",
            "timeframe": "1h",
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 3, 31),
            "initial_capital": 10000000,
            "backtest_results": [
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
            ],
            "portfolio_performance": {
                "total_return": 680000,
                "total_return_percent": 6.8,
                "max_drawdown": 3.2,
                "win_rate": 58.0,
                "sharpe_ratio": 1.1
            },
            "combined_equity_curve": pd.DataFrame({
                "equity": [10000000, 10340000, 10680000]
            }, index=[
                datetime(2023, 1, 1),
                datetime(2023, 2, 1),
                datetime(2023, 3, 1)
            ])
        }

    def tearDown(self):
        """테스트 정리"""
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir)

    def test_07_4_1_save_backtest_result(self):
        """=== 테스트 id 07_4_1: 백테스트 결과 저장 테스트 ==="""
        print("\n=== 테스트 id 07_4_1: 백테스트 결과 저장 테스트 ===")
        
        # 백테스트 결과 저장
        result_id = self.results_manager.save_backtest_result(self.backtest_result1)
        
        # 결과 ID 확인
        self.assertIsNotNone(result_id)
        self.assertEqual(result_id, "backtest-1")
        
        # 데이터베이스 저장 확인
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        
        # 파일 저장 확인
        result_file_path = os.path.join(self.temp_dir, f"{result_id}.json")
        self.assertTrue(os.path.exists(result_file_path))
        
        print(f"백테스트 결과가 성공적으로 저장되었습니다. 결과 ID: {result_id}")

    def test_07_4_2_load_backtest_result(self):
        """=== 테스트 id 07_4_2: 백테스트 결과 불러오기 테스트 ==="""
        print("\n=== 테스트 id 07_4_2: 백테스트 결과 불러오기 테스트 ===")
        
        # 먼저 결과 저장
        result_id = self.results_manager.save_backtest_result(self.backtest_result1)
        
        # 모의 객체 설정
        mock_backtest = MagicMock()
        mock_backtest.id = result_id
        mock_backtest.performance_metrics = json.dumps(self.backtest_result1["performance_metrics"])
        self.mock_session.query().filter().first.return_value = mock_backtest
        
        # 결과 불러오기
        loaded_result = self.results_manager.load_backtest_result(result_id)
        
        # 결과 확인
        self.assertIsNotNone(loaded_result)
        self.assertEqual(loaded_result["id"], result_id)
        self.assertEqual(loaded_result["strategy_id"], self.backtest_result1["strategy_id"])
        self.assertEqual(loaded_result["symbol"], self.backtest_result1["symbol"])
        
        # 성과 지표 확인
        self.assertIn("performance_metrics", loaded_result)
        self.assertEqual(loaded_result["performance_metrics"]["total_return_percent"], 
                         self.backtest_result1["performance_metrics"]["total_return_percent"])
        
        print(f"백테스트 결과를 성공적으로 불러왔습니다. 결과 ID: {result_id}")

    def test_07_4_3_save_portfolio_backtest_result(self):
        """=== 테스트 id 07_4_3: 포트폴리오 백테스트 결과 저장 테스트 ==="""
        print("\n=== 테스트 id 07_4_3: 포트폴리오 백테스트 결과 저장 테스트 ===")
        
        # 포트폴리오 백테스트 결과 저장
        result_id = self.results_manager.save_portfolio_backtest_result(self.portfolio_backtest_result)
        
        # 결과 ID 확인
        self.assertIsNotNone(result_id)
        self.assertEqual(result_id, "portfolio-backtest-1")
        
        # 데이터베이스 저장 확인
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        
        # 파일 저장 확인
        result_file_path = os.path.join(self.temp_dir, f"{result_id}.json")
        self.assertTrue(os.path.exists(result_file_path))
        
        print(f"포트폴리오 백테스트 결과가 성공적으로 저장되었습니다. 결과 ID: {result_id}")

    def test_07_4_4_load_portfolio_backtest_result(self):
        """=== 테스트 id 07_4_4: 포트폴리오 백테스트 결과 불러오기 테스트 ==="""
        print("\n=== 테스트 id 07_4_4: 포트폴리오 백테스트 결과 불러오기 테스트 ===")
        
        # 먼저 결과 저장
        result_id = self.results_manager.save_portfolio_backtest_result(self.portfolio_backtest_result)
        
        # 모의 객체 설정
        mock_backtest = MagicMock()
        mock_backtest.id = result_id
        mock_backtest.portfolio_id = "portfolio-1"
        mock_backtest.performance_metrics = json.dumps(self.portfolio_backtest_result["portfolio_performance"])
        self.mock_session.query().filter().first.return_value = mock_backtest
        
        # 결과 불러오기
        loaded_result = self.results_manager.load_portfolio_backtest_result(result_id)
        
        # 결과 확인
        self.assertIsNotNone(loaded_result)
        self.assertEqual(loaded_result["id"], result_id)
        self.assertEqual(loaded_result["portfolio_id"], self.portfolio_backtest_result["portfolio_id"])
        
        # 성과 지표 확인
        self.assertIn("portfolio_performance", loaded_result)
        self.assertEqual(loaded_result["portfolio_performance"]["total_return_percent"], 
                         self.portfolio_backtest_result["portfolio_performance"]["total_return_percent"])
        
        print(f"포트폴리오 백테스트 결과를 성공적으로 불러왔습니다. 결과 ID: {result_id}")

    def test_07_4_5_list_backtest_results(self):
        """=== 테스트 id 07_4_5: 백테스트 결과 목록 조회 테스트 ==="""
        print("\n=== 테스트 id 07_4_5: 백테스트 결과 목록 조회 테스트 ===")
        
        # 결과 저장
        self.results_manager.save_backtest_result(self.backtest_result1)
        self.results_manager.save_backtest_result(self.backtest_result2)
        
        # 모의 객체 설정
        mock_backtest1 = MagicMock()
        mock_backtest1.id = "backtest-1"
        mock_backtest1.strategy_id = "strategy-1"
        mock_backtest1.symbol = "KRW-BTC"
        mock_backtest1.created_at = datetime(2023, 3, 31)
        mock_backtest1.performance_metrics = json.dumps(self.backtest_result1["performance_metrics"])
        
        mock_backtest2 = MagicMock()
        mock_backtest2.id = "backtest-2"
        mock_backtest2.strategy_id = "strategy-2"
        mock_backtest2.symbol = "KRW-ETH"
        mock_backtest2.created_at = datetime(2023, 3, 31)
        mock_backtest2.performance_metrics = json.dumps(self.backtest_result2["performance_metrics"])
        
        self.mock_session.query().all.return_value = [mock_backtest1, mock_backtest2]
        
        # 결과 목록 조회
        results = self.results_manager.list_backtest_results()
        
        # 결과 확인
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "backtest-1")
        self.assertEqual(results[1]["id"], "backtest-2")
        
        print(f"백테스트 결과 목록을 성공적으로 조회했습니다. 결과 수: {len(results)}")

    def test_07_4_6_compare_backtest_results(self):
        """=== 테스트 id 07_4_6: 백테스트 결과 비교 테스트 ==="""
        print("\n=== 테스트 id 07_4_6: 백테스트 결과 비교 테스트 ===")
        
        # 결과 저장
        self.results_manager.save_backtest_result(self.backtest_result1)
        self.results_manager.save_backtest_result(self.backtest_result2)
        
        # 모의 객체 설정 - load_backtest_result 메서드 모의
        self.results_manager.load_backtest_result = MagicMock(side_effect=[
            self.backtest_result1,
            self.backtest_result2
        ])
        
        # 결과 비교
        comparison = self.results_manager.compare_backtest_results(["backtest-1", "backtest-2"])
        
        # 결과 확인
        self.assertIsNotNone(comparison)
        self.assertIn("results", comparison)
        self.assertEqual(len(comparison["results"]), 2)
        self.assertIn("comparison_metrics", comparison)
        self.assertIn("visualization", comparison)
        
        # 비교 지표 확인
        metrics = comparison["comparison_metrics"]
        self.assertIn("total_return_percent", metrics)
        self.assertIn("max_drawdown", metrics)
        self.assertIn("win_rate", metrics)
        self.assertIn("sharpe_ratio", metrics)
        
        print("백테스트 결과를 성공적으로 비교했습니다.")

    def test_07_4_7_delete_backtest_result(self):
        """=== 테스트 id 07_4_7: 백테스트 결과 삭제 테스트 ==="""
        print("\n=== 테스트 id 07_4_7: 백테스트 결과 삭제 테스트 ===")
        
        # 결과 저장
        result_id = self.results_manager.save_backtest_result(self.backtest_result1)
        
        # 모의 객체 설정
        mock_backtest = MagicMock()
        mock_backtest.id = result_id
        self.mock_session.query().filter().first.return_value = mock_backtest
        
        # 결과 삭제
        success = self.results_manager.delete_backtest_result(result_id)
        
        # 결과 확인
        self.assertTrue(success)
        self.mock_session.delete.assert_called_once_with(mock_backtest)
        self.mock_session.commit.assert_called()
        
        # 파일 삭제 확인
        result_file_path = os.path.join(self.temp_dir, f"{result_id}.json")
        self.assertFalse(os.path.exists(result_file_path))
        
        print(f"백테스트 결과를 성공적으로 삭제했습니다. 결과 ID: {result_id}")


if __name__ == "__main__":
    unittest.main()