#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
import numpy as np

def analyze_market_patterns():
    """실제 시장 데이터에서 시나리오별 패턴 분석"""
    db_path = 'upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/data/sampled_market_data.sqlite3'
    
    conn = sqlite3.connect(db_path)
    
    # 전체 데이터 로드
    query = """
    SELECT timestamp, close 
    FROM market_data 
    WHERE symbol = 'KRW-BTC' AND timeframe = '1d'
    ORDER BY timestamp ASC
    """
    
    df = pd.read_sql_query(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    df['close'] = pd.to_numeric(df['close'])
    
    # 100일 단위로 세그먼트 분석
    segment_size = 100
    segments = []
    
    for i in range(0, len(df) - segment_size, 10):  # 10일씩 이동하면서 분석
        segment = df.iloc[i:i+segment_size]
        if len(segment) == segment_size:
            start_price = segment['close'].iloc[0]
            end_price = segment['close'].iloc[-1]
            change_percent = (end_price / start_price - 1) * 100
            
            # 변동성 계산 (일일 변동률의 표준편차)
            daily_returns = segment['close'].pct_change().dropna()
            volatility = daily_returns.std() * 100
            
            # 추세 계산 (선형 회귀 기울기)
            x = np.arange(len(segment))
            y = segment['close'].values
            slope = np.polyfit(x, y, 1)[0]
            
            segments.append({
                'start_idx': i,
                'start_date': segment.index[0],
                'end_date': segment.index[-1],
                'start_price': start_price,
                'end_price': end_price,
                'change_percent': change_percent,
                'volatility': volatility,
                'slope': slope,
                'max_price': segment['close'].max(),
                'min_price': segment['close'].min()
            })
    
    segments_df = pd.DataFrame(segments)
    
    print("=== 시장 패턴 분석 결과 ===")
    print(f"총 분석 세그먼트: {len(segments_df)}개")
    print(f"변동률 범위: {segments_df['change_percent'].min():.2f}% ~ {segments_df['change_percent'].max():.2f}%")
    
    # 시나리오별 최적 구간 찾기
    scenarios = {
        '급등': {'change_min': 15, 'change_max': 100, 'description': '15% 이상 급등'},
        '상승 추세': {'change_min': 5, 'change_max': 15, 'description': '5~15% 상승'},
        '횡보': {'change_min': -3, 'change_max': 3, 'description': '-3~3% 횡보'},
        '하락 추세': {'change_min': -15, 'change_max': -5, 'description': '-15~-5% 하락'},
        '급락': {'change_min': -100, 'change_max': -15, 'description': '-15% 이상 급락'}
    }
    
    print("\n=== 시나리오별 최적 구간 ===")
    for scenario, criteria in scenarios.items():
        candidates = segments_df[
            (segments_df['change_percent'] >= criteria['change_min']) & 
            (segments_df['change_percent'] <= criteria['change_max'])
        ].sort_values('volatility')  # 변동성이 낮은 것부터 (더 안정적인 패턴)
        
        print(f"\n📊 {scenario} ({criteria['description']})")
        if len(candidates) > 0:
            best = candidates.iloc[0]
            print(f"  ✅ 최적 구간: offset {best['start_idx']}")
            print(f"  📅 기간: {best['start_date'].strftime('%Y-%m-%d')} ~ {best['end_date'].strftime('%Y-%m-%d')}")
            print(f"  📈 변동률: {best['change_percent']:+.2f}%")
            print(f"  💫 변동성: {best['volatility']:.2f}%")
            print(f"  💰 가격: {best['start_price']:,.0f} → {best['end_price']:,.0f}")
            
            # 다른 후보들도 표시
            if len(candidates) > 1:
                print(f"  📋 다른 후보: {len(candidates)-1}개")
        else:
            print(f"  ❌ 해당 조건의 구간 없음")
    
    conn.close()

if __name__ == "__main__":
    analyze_market_patterns()
