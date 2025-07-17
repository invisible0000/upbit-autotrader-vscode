#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
포트폴리오 성과 계산 모듈

포트폴리오 가중치 계산, 수익률 계산, 위험 지표 계산 등의 기능을 제공합니다.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from scipy.optimize import minimize

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from upbit_auto_trading.data_layer.models import Portfolio, PortfolioCoin, Strategy, Backtest, OHLCV


class PortfolioPerformance:
    """포트폴리오 성과 계산 클래스"""

    def __init__(self, session: Session):
        """
        포트폴리오 성과 계산기 초기화
        
        Args:
            session: SQLAlchemy 세션
        """
        self.session = session

    def calculate_portfolio_weights(self, portfolio_id: str) -> Dict[str, float]:
        """
        포트폴리오 가중치 계산
        
        Args:
            portfolio_id: 포트폴리오 ID
            
        Returns:
            코인별 가중치 딕셔너리 (예: {"KRW-BTC": 0.6, "KRW-ETH": 0.4})
        """
        try:
            # 포트폴리오 존재 여부 확인
            portfolio = self.session.query(Portfolio).filter_by(id=portfolio_id).first()
            if not portfolio:
                raise ValueError(f"ID가 {portfolio_id}인 포트폴리오를 찾을 수 없습니다.")
            
            # 코인이 없는 경우
            if not portfolio.coins:
                return {}
            
            # 코인별 가중치 계산
            weights = {coin.symbol: coin.weight for coin in portfolio.coins}
            
            return weights
        except SQLAlchemyError as e:
            raise ValueError(f"포트폴리오 가중치 계산 중 오류 발생: {str(e)}")

    def calculate_expected_return(self, portfolio_id: str) -> float:
        """
        포트폴리오 기대 수익률 계산
        
        Args:
            portfolio_id: 포트폴리오 ID
            
        Returns:
            포트폴리오 기대 수익률 (예: 0.12 = 12%)
        """
        try:
            # 포트폴리오 가중치 계산
            weights = self.calculate_portfolio_weights(portfolio_id)
            
            # 코인이 없는 경우
            if not weights:
                return 0.0
            
            # 각 코인의 백테스트 결과 조회
            expected_returns = {}
            for symbol in weights.keys():
                # 해당 코인의 가장 최근 백테스트 결과 조회
                backtest = self.session.query(Backtest).filter_by(symbol=symbol).order_by(
                    Backtest.end_date.desc()
                ).first()
                
                if backtest and backtest.performance_metrics and "total_return" in backtest.performance_metrics:
                    expected_returns[symbol] = backtest.performance_metrics["total_return"]
                else:
                    # 백테스트 결과가 없는 경우 0.0으로 설정
                    expected_returns[symbol] = 0.0
            
            # 가중 평균 수익률 계산
            portfolio_return = sum(weights[symbol] * expected_returns[symbol] for symbol in weights.keys())
            
            return portfolio_return
        except SQLAlchemyError as e:
            raise ValueError(f"포트폴리오 기대 수익률 계산 중 오류 발생: {str(e)}")

    def calculate_correlation_matrix(self, symbols: List[str], 
                                    start_date: datetime, 
                                    end_date: datetime) -> pd.DataFrame:
        """
        자산 간 상관관계 행렬 계산
        
        Args:
            symbols: 코인 심볼 리스트
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            상관관계 행렬 (pandas DataFrame)
        """
        try:
            # 가격 데이터 로드
            price_data = self._load_price_data(symbols, start_date, end_date)
            
            # 일별 수익률 계산
            returns_data = price_data.pct_change().dropna()
            
            # 상관관계 행렬 계산
            correlation_matrix = returns_data.corr()
            
            return correlation_matrix
        except Exception as e:
            # 오류 발생 시 단위 행렬 반환 (상관관계 없음 가정)
            print(f"상관관계 행렬 계산 중 오류 발생: {str(e)}")
            return pd.DataFrame(np.eye(len(symbols)), index=symbols, columns=symbols)

    def _load_price_data(self, symbols: List[str], 
                        start_date: datetime, 
                        end_date: datetime) -> pd.DataFrame:
        """
        가격 데이터 로드
        
        Args:
            symbols: 코인 심볼 리스트
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            가격 데이터 (pandas DataFrame)
        """
        # 결과 DataFrame 초기화
        price_data = pd.DataFrame()
        
        for symbol in symbols:
            # 일봉 데이터 조회
            ohlcv_data = self.session.query(OHLCV).filter(
                OHLCV.symbol == symbol,
                OHLCV.timestamp >= start_date,
                OHLCV.timestamp <= end_date,
                OHLCV.timeframe == '1d'  # 일봉 데이터 사용
            ).order_by(OHLCV.timestamp).all()
            
            # 데이터가 없는 경우 다음 심볼로 넘어감
            if not ohlcv_data:
                continue
            
            # 종가 데이터 추출
            dates = [data.timestamp for data in ohlcv_data]
            closes = [data.close for data in ohlcv_data]
            
            # DataFrame에 추가
            symbol_data = pd.Series(closes, index=dates, name=symbol)
            price_data[symbol] = symbol_data
        
        return price_data

    def calculate_portfolio_volatility(self, portfolio_id: str) -> float:
        """
        포트폴리오 변동성 계산
        
        Args:
            portfolio_id: 포트폴리오 ID
            
        Returns:
            포트폴리오 변동성 (예: 0.08 = 8%)
        """
        try:
            # 포트폴리오 가중치 계산
            weights = self.calculate_portfolio_weights(portfolio_id)
            
            # 코인이 없는 경우
            if not weights:
                return 0.0
            
            symbols = list(weights.keys())
            
            # 각 코인의 변동성 조회
            volatilities = {}
            for symbol in symbols:
                # 해당 코인의 가장 최근 백테스트 결과 조회
                backtest = self.session.query(Backtest).filter_by(symbol=symbol).order_by(
                    Backtest.end_date.desc()
                ).first()
                
                if backtest and backtest.performance_metrics and "volatility" in backtest.performance_metrics:
                    volatilities[symbol] = backtest.performance_metrics["volatility"]
                else:
                    # 백테스트 결과가 없는 경우 0.0으로 설정
                    volatilities[symbol] = 0.0
            
            # 상관관계 행렬 계산
            # 백테스트 기간 사용
            start_date = min(b.start_date for b in self.session.query(Backtest).filter(
                Backtest.symbol.in_(symbols)
            ).all())
            end_date = max(b.end_date for b in self.session.query(Backtest).filter(
                Backtest.symbol.in_(symbols)
            ).all())
            
            correlation_matrix = self.calculate_correlation_matrix(symbols, start_date, end_date)
            
            # 공분산 행렬 계산
            volatility_vector = np.array([volatilities[s] for s in symbols])
            cov_matrix = np.outer(volatility_vector, volatility_vector) * correlation_matrix.values
            
            # 포트폴리오 가중치 벡터
            weight_vector = np.array([weights[s] for s in symbols])
            
            # 포트폴리오 변동성 계산
            portfolio_volatility = np.sqrt(weight_vector.T @ cov_matrix @ weight_vector)
            
            return portfolio_volatility
        except Exception as e:
            raise ValueError(f"포트폴리오 변동성 계산 중 오류 발생: {str(e)}")

    def calculate_portfolio_sharpe_ratio(self, portfolio_id: str, risk_free_rate: float = 0.02) -> float:
        """
        포트폴리오 샤프 비율 계산
        
        Args:
            portfolio_id: 포트폴리오 ID
            risk_free_rate: 무위험 수익률 (기본값: 2%)
            
        Returns:
            포트폴리오 샤프 비율
        """
        try:
            # 기대 수익률 계산
            expected_return = self.calculate_expected_return(portfolio_id)
            
            # 변동성 계산
            volatility = self.calculate_portfolio_volatility(portfolio_id)
            
            # 변동성이 0인 경우 (위험이 없는 경우)
            if volatility == 0:
                return 0.0
            
            # 샤프 비율 계산
            sharpe_ratio = (expected_return - risk_free_rate) / volatility
            
            return sharpe_ratio
        except Exception as e:
            raise ValueError(f"포트폴리오 샤프 비율 계산 중 오류 발생: {str(e)}")

    def calculate_portfolio_max_drawdown(self, portfolio_id: str) -> float:
        """
        포트폴리오 최대 손실폭 계산
        
        Args:
            portfolio_id: 포트폴리오 ID
            
        Returns:
            포트폴리오 최대 손실폭 (예: 0.15 = 15%)
        """
        try:
            # 포트폴리오 가중치 계산
            weights = self.calculate_portfolio_weights(portfolio_id)
            
            # 코인이 없는 경우
            if not weights:
                return 0.0
            
            # 각 코인의 최대 손실폭 조회
            max_drawdowns = {}
            for symbol in weights.keys():
                # 해당 코인의 가장 최근 백테스트 결과 조회
                backtest = self.session.query(Backtest).filter_by(symbol=symbol).order_by(
                    Backtest.end_date.desc()
                ).first()
                
                if backtest and backtest.performance_metrics and "max_drawdown" in backtest.performance_metrics:
                    max_drawdowns[symbol] = backtest.performance_metrics["max_drawdown"]
                else:
                    # 백테스트 결과가 없는 경우 0.0으로 설정
                    max_drawdowns[symbol] = 0.0
            
            # 가중 평균 최대 손실폭 계산
            # 참고: 실제로는 더 복잡한 계산이 필요할 수 있음
            portfolio_max_drawdown = sum(weights[symbol] * max_drawdowns[symbol] for symbol in weights.keys())
            
            return portfolio_max_drawdown
        except Exception as e:
            raise ValueError(f"포트폴리오 최대 손실폭 계산 중 오류 발생: {str(e)}")

    def calculate_portfolio_performance(self, portfolio_id: str, risk_free_rate: float = 0.02) -> Dict:
        """
        포트폴리오 전체 성과 계산
        
        Args:
            portfolio_id: 포트폴리오 ID
            risk_free_rate: 무위험 수익률 (기본값: 2%)
            
        Returns:
            포트폴리오 성과 지표 딕셔너리
        """
        try:
            # 포트폴리오 가중치 계산
            weights = self.calculate_portfolio_weights(portfolio_id)
            
            # 코인이 없는 경우
            if not weights:
                return {
                    "expected_return": 0.0,
                    "volatility": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "coin_contributions": []
                }
            
            # 기대 수익률 계산
            expected_return = self.calculate_expected_return(portfolio_id)
            
            # 변동성 계산
            volatility = self.calculate_portfolio_volatility(portfolio_id)
            
            # 샤프 비율 계산
            sharpe_ratio = self.calculate_portfolio_sharpe_ratio(portfolio_id, risk_free_rate)
            
            # 최대 손실폭 계산
            max_drawdown = self.calculate_portfolio_max_drawdown(portfolio_id)
            
            # 코인별 기여도 계산
            coin_contributions = []
            for symbol, weight in weights.items():
                # 해당 코인의 가장 최근 백테스트 결과 조회
                backtest = self.session.query(Backtest).filter_by(symbol=symbol).order_by(
                    Backtest.end_date.desc()
                ).first()
                
                if backtest and backtest.performance_metrics and "total_return" in backtest.performance_metrics:
                    coin_return = backtest.performance_metrics["total_return"]
                else:
                    coin_return = 0.0
                
                # 기여도 계산
                contribution = weight * coin_return
                
                coin_contributions.append({
                    "symbol": symbol,
                    "weight": weight,
                    "expected_return": coin_return,
                    "contribution": contribution
                })
            
            # 결과 딕셔너리 구성
            performance = {
                "expected_return": expected_return,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "coin_contributions": coin_contributions
            }
            
            return performance
        except Exception as e:
            raise ValueError(f"포트폴리오 성과 계산 중 오류 발생: {str(e)}")

    def optimize_portfolio_weights(self, symbols: List[str], 
                                  expected_returns: Dict[str, float],
                                  volatilities: Dict[str, float],
                                  start_date: datetime,
                                  end_date: datetime,
                                  risk_free_rate: float = 0.02,
                                  optimization_goal: str = "sharpe") -> Dict[str, float]:
        """
        포트폴리오 가중치 최적화
        
        Args:
            symbols: 코인 심볼 리스트
            expected_returns: 코인별 기대 수익률 딕셔너리
            volatilities: 코인별 변동성 딕셔너리
            start_date: 시작 날짜
            end_date: 종료 날짜
            risk_free_rate: 무위험 수익률 (기본값: 2%)
            optimization_goal: 최적화 목표 ("sharpe", "return", "risk")
            
        Returns:
            최적화된 가중치 딕셔너리
        """
        try:
            # 상관관계 행렬 계산
            correlation_matrix = self.calculate_correlation_matrix(symbols, start_date, end_date)
            
            # 공분산 행렬 계산
            volatility_vector = np.array([volatilities[s] for s in symbols])
            cov_matrix = np.outer(volatility_vector, volatility_vector) * correlation_matrix.values
            
            # 기대 수익률 벡터
            returns_vector = np.array([expected_returns[s] for s in symbols])
            
            # 최적화 목적 함수 정의
            def objective(weights):
                weights = np.array(weights)
                port_return = np.sum(weights * returns_vector)
                port_volatility = np.sqrt(weights.T @ cov_matrix @ weights)
                
                if optimization_goal == "sharpe":
                    # 샤프 비율 최대화 (음수로 반환하여 최소화 문제로 변환)
                    return -((port_return - risk_free_rate) / port_volatility)
                elif optimization_goal == "return":
                    # 수익률 최대화 (음수로 반환하여 최소화 문제로 변환)
                    return -port_return
                elif optimization_goal == "risk":
                    # 변동성 최소화
                    return port_volatility
                else:
                    # 기본값: 샤프 비율 최대화
                    return -((port_return - risk_free_rate) / port_volatility)
            
            # 제약 조건 정의
            constraints = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # 가중치 합계 = 1
            )
            
            # 경계 조건 정의 (각 가중치는 0과 1 사이)
            bounds = tuple((0, 1) for _ in range(len(symbols)))
            
            # 초기 가중치 (균등 배분)
            initial_weights = np.array([1.0 / len(symbols)] * len(symbols))
            
            # 최적화 실행
            result = minimize(
                objective,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            # 최적화 결과 확인
            if not result.success:
                # 최적화 실패 시 균등 배분 반환
                return {symbol: 1.0 / len(symbols) for symbol in symbols}
            
            # 최적화된 가중치 딕셔너리 생성
            optimized_weights = {symbols[i]: result.x[i] for i in range(len(symbols))}
            
            return optimized_weights
        except Exception as e:
            # 오류 발생 시 균등 배분 반환
            print(f"포트폴리오 가중치 최적화 중 오류 발생: {str(e)}")
            return {symbol: 1.0 / len(symbols) for symbol in symbols}