#!/usr/bin/env python3
"""실제 샘플 데이터 사용 확인 테스트"""

import sys
import os

# 시뮬레이션 엔진 경로 추가
sys.path.append('upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation')

def test_real_sample_data_usage():
    """실제 샘플 데이터 사용 확인"""
    
    print("🧪 실제 샘플 데이터 사용 확인 테스트")
    print("=" * 60)
    
    from engines.simulation_engines import get_simulation_engine
    
    # Robust 엔진으로 데이터 로드
    engine = get_simulation_engine("robust")
    data = engine.load_market_data(limit=5)
    
    print(f"🎯 사용된 엔진: {engine.name}")
    print(f"📊 로드된 데이터:")
    print(f"   레코드 수: {len(data)}")
    print(f"   컬럼: {list(data.columns)}")
    
    if len(data) > 0:
        print(f"📋 실제 데이터 내용:")
        for idx, row in data.head().iterrows():
            print(f"  {idx+1}: {row['timestamp']} | close: {row['close']:,.0f} | volume: {row['volume']:.2f}")
        
        # 샘플 DB의 특정 데이터와 비교 (2025-07-23 데이터가 있는지 확인)
        recent_data = data[data['timestamp'].dt.date.astype(str) == '2025-07-23']
        if not recent_data.empty:
            print(f"✅ 2025-07-23 데이터 확인됨 (실제 샘플 DB 데이터 사용 중)")
            print(f"   close: {recent_data.iloc[0]['close']:,.0f}")
        else:
            print(f"⚠️ 2025-07-23 데이터 없음 (합성 데이터일 가능성)")
            
        # 가격 범위 확인 (샘플 DB는 1억6천만원대)
        avg_close = data['close'].mean()
        print(f"📈 평균 종가: {avg_close:,.0f}원")
        
        if 150000000 <= avg_close <= 170000000:
            print(f"✅ 가격 범위가 샘플 DB와 일치 (실제 데이터 사용 중)")
        else:
            print(f"⚠️ 가격 범위가 다름 (합성 데이터일 가능성)")

if __name__ == "__main__":
    test_real_sample_data_usage()
