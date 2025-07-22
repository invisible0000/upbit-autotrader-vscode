#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
실제 매매전략 구현 및 백테스팅 테스트

이동평균 크로스오버 전략을 구현하고 실제 데이터로 백테스팅을 수행합니다.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'upbit_auto_trading'))

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from upbit_auto_trading.data_layer.collectors.data_collector import DataCollector
from upbit_auto_trading.data_layer.storage.market_data_storage import MarketDataStorage
from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface


class MovingAverageCrossStrategy(StrategyInterface):
    """이동평균 크로스오버 전략"""
    
    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        """
        Args:
            parameters: 전략 매개변수
        """
        if parameters is None:
            parameters = self.get_default_parameters()
            
        self.parameters = parameters
        self.short_period = parameters.get('short_period', 5)
        self.long_period = parameters.get('long_period', 20)
        
    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            'name': f"MA Cross ({self.short_period}, {self.long_period})",
            'description': '이동평균 크로스오버 전략',
            'version': '1.0',
            'author': 'System'
        }
        
    def get_default_parameters(self) -> Dict[str, Any]:
        """기본 매개변수 반환"""
        return {
            'short_period': 5,
            'long_period': 20
        }
        
    def get_parameters(self) -> Dict[str, Any]:
        """현재 매개변수 반환"""
        return self.parameters.copy()
        
    def set_parameters(self, parameters: Dict[str, Any]) -> bool:
        """매개변수 설정"""
        if self.validate_parameters(parameters):
            self.parameters.update(parameters)
            self.short_period = self.parameters.get('short_period', 5)
            self.long_period = self.parameters.get('long_period', 20)
            return True
        return False
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """매개변수 유효성 검사"""
        short = parameters.get('short_period', 5)
        long = parameters.get('long_period', 20)
        
        if not isinstance(short, int) or not isinstance(long, int):
            return False
        if short <= 0 or long <= 0:
            return False
        if short >= long:
            return False
            
        return True
        
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 지표 목록 반환"""
        return [
            {
                "name": "SMA",
                "params": {
                    "window": self.short_period,
                    "column": "close"
                }
            },
            {
                "name": "SMA", 
                "params": {
                    "window": self.long_period,
                    "column": "close"
                }
            }
        ]
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        df = data.copy()
        
        # 이동평균 계산
        df[f'MA_{self.short_period}'] = df['close'].rolling(window=self.short_period).mean()
        df[f'MA_{self.long_period}'] = df['close'].rolling(window=self.long_period).mean()
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """매매 신호 생성"""
        df = self.calculate_indicators(data)
        
        # 골든크로스/데드크로스 신호
        short_ma = df[f'MA_{self.short_period}']
        long_ma = df[f'MA_{self.long_period}']
        
        # 신호 초기화
        df['signal'] = 0
        df['position'] = 0
        
        # 골든크로스: 단기 MA가 장기 MA를 상향돌파 (매수)
        golden_cross = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        df.loc[golden_cross, 'signal'] = 1
        
        # 데드크로스: 단기 MA가 장기 MA를 하향돌파 (매도)
        dead_cross = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))
        df.loc[dead_cross, 'signal'] = -1
        
        # 포지션 계산 (전략에 따른 보유 상태)
        df['position'] = df['signal'].replace(0, np.nan).ffill().fillna(0)
        
        return df


class SimpleBacktester:
    """간단한 백테스터"""
    
    def __init__(self, initial_capital=10000000):  # 1000만원
        self.initial_capital = initial_capital
        
    def run_backtest(self, strategy: StrategyInterface, data: pd.DataFrame):
        """백테스트 실행"""
        strategy_info = strategy.get_strategy_info()
        print(f"\n=== 백테스트 실행: {strategy_info['name']} ===")
        
        # 전략 신호 생성
        df = strategy.generate_signals(data)
        
        # 백테스트 결과 계산
        results = self._calculate_returns(df)
        
        # 거래 기록 생성
        trades = self._generate_trades(df)
        
        # 결과 출력
        self._print_results(results, trades)
        
        return {
            'strategy_name': strategy_info['name'],
            'data': df,
            'results': results,
            'trades': trades
        }
    
    def _calculate_returns(self, df: pd.DataFrame):
        """수익률 계산"""
        # 매매 수수료 (0.05%)
        commission = 0.0005
        
        # 자산 변화 추적
        cash = self.initial_capital
        shares = 0
        portfolio_values = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # 매수 신호
            if row['signal'] == 1 and shares == 0:
                shares = cash / row['close'] * (1 - commission)
                cash = 0
                
            # 매도 신호  
            elif row['signal'] == -1 and shares > 0:
                cash = shares * row['close'] * (1 - commission)
                shares = 0
            
            # 포트폴리오 가치 계산
            if shares > 0:
                portfolio_value = shares * row['close']
            else:
                portfolio_value = cash
                
            portfolio_values.append(portfolio_value)
        
        df['portfolio_value'] = portfolio_values
        
        # 성과 지표 계산
        total_return = (portfolio_values[-1] - self.initial_capital) / self.initial_capital * 100
        
        # 최대 손실폭 (MDD) 계산
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (np.array(portfolio_values) - peak) / peak * 100
        max_drawdown = np.min(drawdown)
        
        # Buy & Hold 수익률
        buy_hold_return = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
        
        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'buy_hold_return': buy_hold_return,
            'final_value': portfolio_values[-1],
            'portfolio_values': portfolio_values
        }
    
    def _generate_trades(self, df: pd.DataFrame):
        """거래 기록 생성"""
        trades = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            if row['signal'] != 0:
                trades.append({
                    'date': row['timestamp'] if 'timestamp' in row else i,
                    'action': '매수' if row['signal'] == 1 else '매도',
                    'price': row['close'],
                    'signal': row['signal']
                })
        
        return trades
    
    def _print_results(self, results, trades):
        """결과 출력"""
        print(f"📊 백테스트 결과:")
        print(f"  총 수익률: {results['total_return']:.2f}%")
        print(f"  최대 손실폭(MDD): {results['max_drawdown']:.2f}%")
        print(f"  Buy & Hold 수익률: {results['buy_hold_return']:.2f}%")
        print(f"  최종 자산: {results['final_value']:,.0f}원")
        print(f"  거래 횟수: {len(trades)}회")
        
        if trades:
            print(f"\n📋 거래 기록:")
            for trade in trades:
                print(f"  {trade['date']} - {trade['action']}: {trade['price']:,.0f}원")


def test_strategy_backtest():
    """실제 전략 백테스팅 테스트"""
    print("=== 실제 매매전략 백테스팅 테스트 ===")
    
    # 1. 데이터 로드
    storage = MarketDataStorage()
    collector = DataCollector()
    
    symbol = "KRW-BTC"
    timeframe = "1d"
    
    # 더 많은 데이터 수집 (90일)
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()
    
    print(f"📊 데이터 수집: {symbol} ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})")
    
    # 데이터 수집
    data = collector.collect_historical_ohlcv(symbol, timeframe, start_date, end_date)
    
    if data.empty:
        print("❌ 데이터를 찾을 수 없습니다.")
        return
    
    print(f"✅ 데이터 로드 완료: {len(data)}개")
    
    # 2. 전략 생성 및 백테스트
    strategies = [
        MovingAverageCrossStrategy({'short_period': 5, 'long_period': 20}),   # 빠른 전략
        MovingAverageCrossStrategy({'short_period': 10, 'long_period': 30}),  # 보통 전략  
        MovingAverageCrossStrategy({'short_period': 20, 'long_period': 50}),  # 느린 전략
    ]
    
    backtester = SimpleBacktester(initial_capital=10000000)
    
    results = []
    for strategy in strategies:
        result = backtester.run_backtest(strategy, data)
        results.append(result)
    
    # 3. 결과 비교
    print("\n" + "="*50)
    print("📈 전략 성과 비교")
    print("="*50)
    
    for result in results:
        r = result['results']
        print(f"{result['strategy_name']:20} | "
              f"수익률: {r['total_return']:6.2f}% | "
              f"MDD: {r['max_drawdown']:6.2f}% | "
              f"거래: {len(result['trades']):2d}회")
    
    return results


if __name__ == "__main__":
    results = test_strategy_backtest()
    
    if results:
        print(f"\n✅ 백테스팅 완료! {len(results)}개 전략 테스트됨")
        print("\n💡 이제 GUI에서 이 결과들을 시각화할 수 있습니다.")
    else:
        print("\n❌ 백테스팅 실패!")
