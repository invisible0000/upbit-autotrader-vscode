#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
포트폴리오 성과 계산 기능 테스트

이 테스트 모듈은 포트폴리오 성과 계산 기능을 검증합니다.
- 포트폴리오 가중치 계산 기능
- 포트폴리오 수익률 계산 기능
- 포트폴리오 위험 지표 계산 기능
"""

import unittest
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from upbit_auto_trading.data_layer.models import Base, Portfolio, PortfolioCoin, Strategy, Backtest
from upbit_auto_trading.business_logic.portfolio.portfolio_manager import PortfolioManager
from upbit_auto_trading.business_logic.portfolio.portfolio_performance import PortfolioPerformance


class TestPortfolioPerformance(unittest.TestCase):
    """포트폴리오 성과 계산 기능 테스트 클래스"""

    def setUp(self):
        """테스트 환경 설정"""
        # 인메모리 SQLite 데이터베이스 생성
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        
        # 세션 생성
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # 테스트용 전략 생성
        self.strategy1 = Strategy(
            id=str(uuid.uuid4()),
            name="이동평균 교차 전략",
            description="단기 이동평균이 장기 이동평균을 상향 돌파할 때 매수, 하향 돌파할 때 매도",
            parameters={"short_window": 20, "long_window": 60}
        )
        
        self.strategy2 = Strategy(
            id=str(uuid.uuid4()),
            name="RSI 전략",
            description="RSI가 30 이하일 때 매수, 70 이상일 때 매도",
            parameters={"rsi_window": 14, "oversold": 30, "overbought": 70}
        )
        
        self.session.add_all([self.strategy1, self.strategy2])
        self.session.commit()
        
        # 테스트용 포트폴리오 생성
        self.portfolio_manager = PortfolioManager(self.session)
        self.portfolio_id = self.portfolio_manager.create_portfolio(
            name="테스트 포트폴리오",
            description="성과 계산 테스트용 포트폴리오"
        )
        
        # 코인 추가
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=self.portfolio_id,
            symbol="KRW-BTC",
            strategy_id=self.strategy1.id,
            weight=0.6
        )
        
        self.portfolio_manager.add_coin_to_portfolio(
            portfolio_id=self.portfolio_id,
            symbol="KRW-ETH",
            strategy_id=self.strategy2.id,
            weight=0.4
        )
        
        # 테스트용 백테스트 결과 생성
        self.end_date = datetime.utcnow()
        self.start_date = self.end_date - timedelta(days=30)
        
        # BTC 백테스트 결과
        self.btc_backtest = Backtest(
            id=str(uuid.uuid4()),
            strategy_id=self.strategy1.id,
            symbol="KRW-BTC",
            timeframe="1h",
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=1000000.0,
            performance_metrics={
                "total_return": 0.15,  # 15% 수익
                "annualized_return": 0.25,  # 25% 연간 수익률
                "max_drawdown": 0.08,  # 8% 최대 손실폭
                "volatility": 0.12,  # 12% 변동성
                "sharpe_ratio": 1.8,  # 샤프 비율
                "win_rate": 0.65,  # 65% 승률
                "trades_count": 12  # 총 거래 횟수
            }
        )
        
        # ETH 백테스트 결과
        self.eth_backtest = Backtest(
            id=str(uuid.uuid4()),
            strategy_id=self.strategy2.id,
            symbol="KRW-ETH",
            timeframe="1h",
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=1000000.0,
            performance_metrics={
                "total_return": 0.08,  # 8% 수익
                "annualized_return": 0.15,  # 15% 연간 수익률
                "max_drawdown": 0.12,  # 12% 최대 손실폭
                "volatility": 0.18,  # 18% 변동성
                "sharpe_ratio": 1.2,  # 샤프 비율
                "win_rate": 0.55,  # 55% 승률
                "trades_count": 15  # 총 거래 횟수
            }
        )
        
        self.session.add_all([self.btc_backtest, self.eth_backtest])
        self.session.commit()
        
        # 포트폴리오 성과 계산기 생성
        self.portfolio_performance = PortfolioPerformance(self.session)
        
        print("=== 테스트 id 06_2_1: test_calculate_portfolio_weights ===")
        print("=== 테스트 id 06_2_2: test_calculate_expected_return ===")
        print("=== 테스트 id 06_2_3: test_calculate_portfolio_volatility ===")
        print("=== 테스트 id 06_2_4: test_calculate_portfolio_sharpe_ratio ===")
        print("=== 테스트 id 06_2_5: test_calculate_portfolio_max_drawdown ===")
        print("=== 테스트 id 06_2_6: test_calculate_portfolio_performance ===")
        print("=== 테스트 id 06_2_7: test_calculate_correlation_matrix ===")
        print("=== 테스트 id 06_2_8: test_optimize_portfolio_weights ===")

    def tearDown(self):
        """테스트 환경 정리"""
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_calculate_portfolio_weights(self):
        """포트폴리오 가중치 계산 테스트"""
        print("\n[테스트 시작] 포트폴리오 가중치 계산 테스트")
        
        # 가중치 계산
        weights = self.portfolio_performance.calculate_portfolio_weights(self.portfolio_id)
        
        # 검증
        self.assertIsNotNone(weights)
        self.assertEqual(len(weights), 2)
        self.assertIn("KRW-BTC", weights)
        self.assertIn("KRW-ETH", weights)
        self.assertEqual(weights["KRW-BTC"], 0.6)
        self.assertEqual(weights["KRW-ETH"], 0.4)
        
        # 가중치 합계 검증
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        
        print(f"계산된 가중치: {weights}")
        print(f"가중치 합계: {sum(weights.values())}")
        print("[테스트 완료] 포트폴리오 가중치 계산 테스트 성공")

    def test_calculate_expected_return(self):
        """포트폴리오 기대 수익률 계산 테스트"""
        print("\n[테스트 시작] 포트폴리오 기대 수익률 계산 테스트")
        
        # 기대 수익률 계산
        expected_return = self.portfolio_performance.calculate_expected_return(self.portfolio_id)
        
        # 수동 계산 (검증용)
        manual_expected_return = 0.6 * 0.15 + 0.4 * 0.08  # 0.6*BTC수익률 + 0.4*ETH수익률
        
        # 검증
        self.assertIsNotNone(expected_return)
        self.assertAlmostEqual(expected_return, manual_expected_return)
        
        print(f"계산된 기대 수익률: {expected_return:.4f} ({expected_return*100:.2f}%)")
        print(f"수동 계산 기대 수익률: {manual_expected_return:.4f} ({manual_expected_return*100:.2f}%)")
        print("[테스트 완료] 포트폴리오 기대 수익률 계산 테스트 성공")

    def test_calculate_portfolio_volatility(self):
        """포트폴리오 변동성 계산 테스트"""
        print("\n[테스트 시작] 포트폴리오 변동성 계산 테스트")
        
        # 상관관계 행렬 모의 객체 생성 (BTC와 ETH 사이의 상관관계 0.5로 가정)
        correlation_matrix = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=["KRW-BTC", "KRW-ETH"],
            columns=["KRW-BTC", "KRW-ETH"]
        )
        
        # 변동성 계산 (상관관계 행렬 모의 객체 사용)
        with patch.object(self.portfolio_performance, 'calculate_correlation_matrix', return_value=correlation_matrix):
            volatility = self.portfolio_performance.calculate_portfolio_volatility(self.portfolio_id)
        
        # 수동 계산 (검증용)
        weights = np.array([0.6, 0.4])
        individual_volatilities = np.array([0.12, 0.18])
        cov_matrix = np.outer(individual_volatilities, individual_volatilities) * correlation_matrix.values
        manual_volatility = np.sqrt(weights.T @ cov_matrix @ weights)
        
        # 검증
        self.assertIsNotNone(volatility)
        self.assertAlmostEqual(volatility, manual_volatility, places=6)
        
        print(f"계산된 포트폴리오 변동성: {volatility:.4f} ({volatility*100:.2f}%)")
        print(f"수동 계산 포트폴리오 변동성: {manual_volatility:.4f} ({manual_volatility*100:.2f}%)")
        print(f"개별 자산 변동성: BTC={0.12*100:.2f}%, ETH={0.18*100:.2f}%")
        print("[테스트 완료] 포트폴리오 변동성 계산 테스트 성공")

    def test_calculate_portfolio_sharpe_ratio(self):
        """포트폴리오 샤프 비율 계산 테스트"""
        print("\n[테스트 시작] 포트폴리오 샤프 비율 계산 테스트")
        
        # 무위험 수익률 설정 (연 3%)
        risk_free_rate = 0.03
        
        # 기대 수익률과 변동성 모의 객체 생성
        expected_return = 0.12  # 12% 기대 수익률
        volatility = 0.09  # 9% 변동성
        
        # 샤프 비율 계산 (모의 객체 사용)
        with patch.object(self.portfolio_performance, 'calculate_expected_return', return_value=expected_return):
            with patch.object(self.portfolio_performance, 'calculate_portfolio_volatility', return_value=volatility):
                sharpe_ratio = self.portfolio_performance.calculate_portfolio_sharpe_ratio(
                    self.portfolio_id, risk_free_rate
                )
        
        # 수동 계산 (검증용)
        manual_sharpe_ratio = (expected_return - risk_free_rate) / volatility
        
        # 검증
        self.assertIsNotNone(sharpe_ratio)
        self.assertAlmostEqual(sharpe_ratio, manual_sharpe_ratio)
        
        print(f"계산된 샤프 비율: {sharpe_ratio:.4f}")
        print(f"수동 계산 샤프 비율: {manual_sharpe_ratio:.4f}")
        print(f"기대 수익률: {expected_return*100:.2f}%, 변동성: {volatility*100:.2f}%, 무위험 수익률: {risk_free_rate*100:.2f}%")
        print("[테스트 완료] 포트폴리오 샤프 비율 계산 테스트 성공")

    def test_calculate_portfolio_max_drawdown(self):
        """포트폴리오 최대 손실폭 계산 테스트"""
        print("\n[테스트 시작] 포트폴리오 최대 손실폭 계산 테스트")
        
        # 최대 손실폭 계산
        max_drawdown = self.portfolio_performance.calculate_portfolio_max_drawdown(self.portfolio_id)
        
        # 수동 계산 (검증용)
        # 가중 평균으로 계산 (실제로는 더 복잡한 계산이 필요할 수 있음)
        manual_max_drawdown = 0.6 * 0.08 + 0.4 * 0.12  # 0.6*BTC최대손실폭 + 0.4*ETH최대손실폭
        
        # 검증
        self.assertIsNotNone(max_drawdown)
        self.assertAlmostEqual(max_drawdown, manual_max_drawdown)
        
        print(f"계산된 최대 손실폭: {max_drawdown:.4f} ({max_drawdown*100:.2f}%)")
        print(f"수동 계산 최대 손실폭: {manual_max_drawdown:.4f} ({manual_max_drawdown*100:.2f}%)")
        print(f"개별 자산 최대 손실폭: BTC={0.08*100:.2f}%, ETH={0.12*100:.2f}%")
        print("[테스트 완료] 포트폴리오 최대 손실폭 계산 테스트 성공")

    def test_calculate_portfolio_performance(self):
        """포트폴리오 전체 성과 계산 테스트"""
        print("\n[테스트 시작] 포트폴리오 전체 성과 계산 테스트")
        
        # 상관관계 행렬 모의 객체 생성
        correlation_matrix = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=["KRW-BTC", "KRW-ETH"],
            columns=["KRW-BTC", "KRW-ETH"]
        )
        
        # 상관관계 행렬 계산 함수 모의 객체화
        with patch.object(self.portfolio_performance, 'calculate_correlation_matrix', return_value=correlation_matrix):
            # 포트폴리오 성과 계산
            performance = self.portfolio_performance.calculate_portfolio_performance(
                self.portfolio_id, risk_free_rate=0.03
            )
        
        # 검증
        self.assertIsNotNone(performance)
        self.assertIn("expected_return", performance)
        self.assertIn("volatility", performance)
        self.assertIn("sharpe_ratio", performance)
        self.assertIn("max_drawdown", performance)
        self.assertIn("coin_contributions", performance)
        
        # 코인 기여도 검증
        self.assertEqual(len(performance["coin_contributions"]), 2)
        
        # 코인별 기여도 확인
        coin_contributions = {coin["symbol"]: coin for coin in performance["coin_contributions"]}
        self.assertIn("KRW-BTC", coin_contributions)
        self.assertIn("KRW-ETH", coin_contributions)
        
        print(f"포트폴리오 성과:")
        print(f"- 기대 수익률: {performance['expected_return']*100:.2f}%")
        print(f"- 변동성: {performance['volatility']*100:.2f}%")
        print(f"- 샤프 비율: {performance['sharpe_ratio']:.4f}")
        print(f"- 최대 손실폭: {performance['max_drawdown']*100:.2f}%")
        print(f"코인별 기여도:")
        for coin in performance["coin_contributions"]:
            print(f"- {coin['symbol']}: 가중치={coin['weight']*100:.1f}%, "
                  f"수익률={coin['expected_return']*100:.2f}%, "
                  f"기여도={coin['contribution']*100:.2f}%")
        print("[테스트 완료] 포트폴리오 전체 성과 계산 테스트 성공")

    def test_calculate_correlation_matrix(self):
        """자산 간 상관관계 행렬 계산 테스트"""
        print("\n[테스트 시작] 자산 간 상관관계 행렬 계산 테스트")
        
        # 테스트용 가격 데이터 생성
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        
        # BTC 가격 데이터 (상승 추세)
        btc_prices = pd.Series(
            np.linspace(10000000, 12000000, len(dates)) + np.random.normal(0, 200000, len(dates)),
            index=dates
        )
        
        # ETH 가격 데이터 (BTC와 약간의 상관관계)
        eth_prices = pd.Series(
            np.linspace(2000000, 2300000, len(dates)) + 0.5 * np.random.normal(0, 50000, len(dates)),
            index=dates
        )
        
        # 가격 데이터 DataFrame 생성
        price_data = pd.DataFrame({
            "KRW-BTC": btc_prices,
            "KRW-ETH": eth_prices
        })
        
        # 가격 데이터 로드 함수 모의 객체화
        with patch.object(self.portfolio_performance, '_load_price_data', return_value=price_data):
            # 상관관계 행렬 계산
            correlation_matrix = self.portfolio_performance.calculate_correlation_matrix(
                ["KRW-BTC", "KRW-ETH"], self.start_date, self.end_date
            )
        
        # 검증
        self.assertIsNotNone(correlation_matrix)
        self.assertIsInstance(correlation_matrix, pd.DataFrame)
        self.assertEqual(correlation_matrix.shape, (2, 2))
        self.assertEqual(list(correlation_matrix.index), ["KRW-BTC", "KRW-ETH"])
        self.assertEqual(list(correlation_matrix.columns), ["KRW-BTC", "KRW-ETH"])
        
        # 대각선 요소는 1.0이어야 함
        self.assertEqual(correlation_matrix.loc["KRW-BTC", "KRW-BTC"], 1.0)
        self.assertEqual(correlation_matrix.loc["KRW-ETH", "KRW-ETH"], 1.0)
        
        # 상관관계 값은 -1.0에서 1.0 사이여야 함
        self.assertTrue(-1.0 <= correlation_matrix.loc["KRW-BTC", "KRW-ETH"] <= 1.0)
        self.assertTrue(-1.0 <= correlation_matrix.loc["KRW-ETH", "KRW-BTC"] <= 1.0)
        
        # 상관관계 행렬은 대칭이어야 함
        self.assertEqual(
            correlation_matrix.loc["KRW-BTC", "KRW-ETH"],
            correlation_matrix.loc["KRW-ETH", "KRW-BTC"]
        )
        
        print(f"계산된 상관관계 행렬:\n{correlation_matrix}")
        print(f"BTC-ETH 상관관계: {correlation_matrix.loc['KRW-BTC', 'KRW-ETH']:.4f}")
        print("[테스트 완료] 자산 간 상관관계 행렬 계산 테스트 성공")

    def test_optimize_portfolio_weights(self):
        """포트폴리오 가중치 최적화 테스트"""
        print("\n[테스트 시작] 포트폴리오 가중치 최적화 테스트")
        
        # 테스트용 데이터 준비
        symbols = ["KRW-BTC", "KRW-ETH"]
        expected_returns = {"KRW-BTC": 0.15, "KRW-ETH": 0.08}
        
        # 상관관계 행렬 모의 객체 생성
        correlation_matrix = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=symbols,
            columns=symbols
        )
        
        # 변동성 데이터
        volatilities = {"KRW-BTC": 0.12, "KRW-ETH": 0.18}
        
        # 상관관계 행렬 계산 함수 모의 객체화
        with patch.object(self.portfolio_performance, 'calculate_correlation_matrix', return_value=correlation_matrix):
            # 가중치 최적화 (최대 샤프 비율)
            optimized_weights = self.portfolio_performance.optimize_portfolio_weights(
                symbols=symbols,
                expected_returns=expected_returns,
                volatilities=volatilities,
                start_date=self.start_date,
                end_date=self.end_date,
                risk_free_rate=0.03,
                optimization_goal="sharpe"
            )
        
        # 검증
        self.assertIsNotNone(optimized_weights)
        self.assertEqual(len(optimized_weights), 2)
        self.assertIn("KRW-BTC", optimized_weights)
        self.assertIn("KRW-ETH", optimized_weights)
        
        # 가중치 합계는 1.0이어야 함
        self.assertAlmostEqual(sum(optimized_weights.values()), 1.0)
        
        # 가중치는 0.0에서 1.0 사이여야 함
        for weight in optimized_weights.values():
            self.assertTrue(0.0 <= weight <= 1.0)
        
        print(f"최적화된 가중치: {optimized_weights}")
        print(f"가중치 합계: {sum(optimized_weights.values())}")
        print("[테스트 완료] 포트폴리오 가중치 최적화 테스트 성공")


if __name__ == '__main__':
    unittest.main()