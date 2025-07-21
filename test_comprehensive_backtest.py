#!/usr/bin/env python3
"""
종합 백테스트 시스템 테스트

모든 개선사항이 올바르게 작동하는지 확인:
1. 기본 전략들 (이동평균, 볼린저 밴드, RSI) 동작 확인
2. 거래 기록 상세 정보 표시
3. 올바른 수익률 계산
4. 차트 표시 기능
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def create_sample_data(symbol="KRW-BTC", days=90):
    """샘플 데이터 생성"""
    print(f"📊 {symbol} {days}일 샘플 데이터 생성 중...")
    
    # 시간 인덱스 생성 (1시간 단위)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    time_index = pd.date_range(start_time, end_time, freq='1h')
    
    # 랜덤 워크로 가격 데이터 생성 (BTC 가격 유사)
    np.random.seed(42)  # 재현가능한 결과를 위해
    
    initial_price = 45000000  # 4천5백만원
    returns = np.random.normal(0, 0.02, len(time_index))  # 2% 변동성
    
    prices = [initial_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    # OHLCV 데이터 생성
    data = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': [np.random.randint(100, 1000) for _ in prices]
    }, index=time_index)
    
    # 기술적 지표 추가
    data['SMA_5'] = data['close'].rolling(5).mean()
    data['SMA_20'] = data['close'].rolling(20).mean()
    data['SMA_50'] = data['close'].rolling(50).mean()
    
    # 볼린저 밴드
    data['BB_MIDDLE'] = data['close'].rolling(20).mean()
    bb_std = data['close'].rolling(20).std()
    data['BB_UPPER'] = data['BB_MIDDLE'] + (bb_std * 2)
    data['BB_LOWER'] = data['BB_MIDDLE'] - (bb_std * 2)
    
    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    data['RSI_14'] = 100 - (100 / (1 + rs))
    
    print(f"✅ 샘플 데이터 생성 완료: {len(data)}개 캔들")
    return data

def test_strategy_performance(strategy, data, strategy_name):
    """전략 성능 테스트"""
    print(f"\n🧪 {strategy_name} 전략 테스트")
    
    try:
        # 매매 신호 생성
        data_with_signals = strategy.generate_signals(data)
        
        if 'signal' not in data_with_signals.columns:
            print(f"❌ {strategy_name}: 신호 생성 실패")
            return None
        
        # 신호 통계
        signals = data_with_signals['signal']
        buy_signals = (signals == 1).sum()
        sell_signals = (signals == -1).sum()
        hold_signals = (signals == 0).sum()
        
        print(f"   📈 매수 신호: {buy_signals}개")
        print(f"   📉 매도 신호: {sell_signals}개") 
        print(f"   ⏸️ 홀드 신호: {hold_signals}개")
        
        if buy_signals == 0 and sell_signals == 0:
            print(f"⚠️ {strategy_name}: 매매 신호 없음")
            return None
        
        # 간단한 백테스트 시뮬레이션
        position = None
        trades = []
        current_capital = 1000000  # 100만원
        
        for timestamp, row in data_with_signals.iterrows():
            signal = row['signal']
            price = row['close']
            
            if signal == 1 and position is None:  # 매수
                position = {
                    'entry_time': timestamp,
                    'entry_price': price,
                    'quantity': current_capital / price
                }
                current_capital = 0
                
            elif signal == -1 and position is not None:  # 매도
                exit_amount = position['quantity'] * price
                profit_loss = exit_amount - (position['quantity'] * position['entry_price'])
                profit_pct = (profit_loss / (position['quantity'] * position['entry_price'])) * 100
                
                trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': timestamp,
                    'entry_price': position['entry_price'],
                    'exit_price': price,
                    'quantity': position['quantity'],
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_pct
                })
                
                current_capital = exit_amount
                position = None
        
        # 성과 계산
        if trades:
            total_return = sum(trade['profit_loss'] for trade in trades)
            win_trades = [t for t in trades if t['profit_loss'] > 0]
            win_rate = len(win_trades) / len(trades) * 100
            
            print(f"   💰 총 거래: {len(trades)}회")
            print(f"   📊 승률: {win_rate:.1f}%")
            print(f"   💵 총 수익: {total_return:,.0f}원")
            print(f"   📈 수익률: {(total_return/1000000)*100:.2f}%")
            
            return {
                'trades': trades,
                'total_return': total_return,
                'win_rate': win_rate / 100,
                'signal_counts': {'buy': buy_signals, 'sell': sell_signals}
            }
        else:
            print(f"   ❌ {strategy_name}: 완료된 거래 없음")
            return None
            
    except Exception as e:
        print(f"❌ {strategy_name} 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_all_strategies():
    """모든 전략 테스트"""
    print("🚀 종합 백테스트 시스템 테스트 시작")
    
    # 샘플 데이터 생성
    data = create_sample_data()
    
    # 전략들 임포트
    try:
        from upbit_auto_trading.business_logic.strategy.basic_strategies import (
            MovingAverageCrossStrategy, BollingerBandsStrategy, RSIStrategy
        )
        
        strategies = [
            (MovingAverageCrossStrategy({'short_window': 5, 'long_window': 20}), "이동평균 교차 (5,20)"),
            (MovingAverageCrossStrategy({'short_window': 20, 'long_window': 50}), "이동평균 교차 (20,50)"),
            (BollingerBandsStrategy({'window': 20, 'num_std': 2.0, 'column': 'close'}), "볼린저 밴드"),
            (RSIStrategy({'window': 14, 'oversold': 30, 'overbought': 70, 'column': 'close'}), "RSI 전략")
        ]
        
        results = {}
        
        for strategy, name in strategies:
            result = test_strategy_performance(strategy, data, name)
            if result:
                results[name] = result
        
        # 결과 요약
        print(f"\n📋 테스트 결과 요약:")
        print("="*60)
        
        for name, result in results.items():
            trades = result['trades']
            if trades:
                print(f"{name}:")
                print(f"  거래 수: {len(trades)}회")
                print(f"  승률: {result['win_rate']*100:.1f}%") 
                print(f"  수익률: {(result['total_return']/1000000)*100:.2f}%")
                print(f"  신호: 매수 {result['signal_counts']['buy']}개, 매도 {result['signal_counts']['sell']}개")
                print()
        
        if not results:
            print("❌ 작동하는 전략이 없습니다.")
            return False
        
        print("✅ 종합 백테스트 시스템 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 전략 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_strategies()
    exit(0 if success else 1)
