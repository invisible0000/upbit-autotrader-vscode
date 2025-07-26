"""
수정된 IndicatorCalculator 테스트
기존 DB 시스템과의 호환성 확인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from indicator_calculator import IndicatorCalculator
import pandas as pd
import numpy as np
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_indicator_calculator():
    """수정된 IndicatorCalculator 테스트"""
    
    print("🧪 IndicatorCalculator 호환성 테스트 시작")
    
    # 샘플 데이터 생성
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    sample_data = pd.DataFrame({
        'close': np.random.randn(50).cumsum() + 100,
        'open': np.random.randn(50).cumsum() + 100,
        'high': np.random.randn(50).cumsum() + 105,
        'low': np.random.randn(50).cumsum() + 95,
        'volume': np.random.randint(1000, 10000, 50)
    }, index=dates)
    
    try:
        # 계산기 생성 (기존 DB 경로 사용)
        print("\n1️⃣ IndicatorCalculator 초기화...")
        calc = IndicatorCalculator()
        print("✅ 초기화 성공")
        
        # 핵심 지표 테스트
        print("\n2️⃣ 핵심 지표 계산 테스트...")
        sma_20 = calc.calculate('SMA', sample_data, period=20)
        rsi_14 = calc.calculate('RSI', sample_data, period=14)
        
        print(f"✅ SMA(20) 계산 완료: {len(sma_20)} 값")
        print(f"✅ RSI(14) 계산 완료: {len(rsi_14)} 값")
        
        # 사용자 정의 지표 테스트
        print("\n3️⃣ 사용자 정의 지표 테스트...")
        price_momentum = calc.calculate('PRICE_MOMENTUM', sample_data)
        print(f"✅ PRICE_MOMENTUM 계산 완료: {len(price_momentum)} 값")
        
        # 사용 가능한 지표 목록 확인
        print("\n4️⃣ 지표 목록 확인...")
        all_indicators = calc.get_available_indicators()
        print(f"✅ 핵심 지표: {len(all_indicators['core'])}개")
        print(f"✅ 사용자 정의: {len(all_indicators['custom'])}개")
        
        # 상세 정보 출력
        print("\n📊 핵심 지표 목록:")
        for indicator in all_indicators['core'][:3]:  # 처음 3개만
            print(f"  - {indicator['id']}: {indicator['name']}")
        
        print("\n📊 사용자 정의 지표 목록:")
        for indicator in all_indicators['custom']:
            print(f"  - {indicator['id']}: {indicator['name_ko']}")
            print(f"    수식: {indicator['formula']}")
        
        # 새로운 지표 추가 테스트
        print("\n5️⃣ 새 지표 추가 테스트...")
        success = calc.add_custom_indicator(
            'TEST_INDICATOR',
            '테스트 지표',
            '테스트용 간단한 지표',
            'close * 1.1',
            '단순 테스트용 지표'
        )
        
        if success:
            print("✅ 새 지표 추가 성공")
            test_result = calc.calculate('TEST_INDICATOR', sample_data)
            print(f"✅ 새 지표 계산 완료: {len(test_result)} 값")
        else:
            print("❌ 새 지표 추가 실패")
        
        print("\n🎉 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        print(f"상세 오류:\n{traceback.format_exc()}")

if __name__ == "__main__":
    test_indicator_calculator()
