"""
하이브리드 지표 계산 시스템 테스트
"""
import sys
sys.path.append('.')
import pandas as pd
import numpy as np
from trading_variables import IndicatorCalculator

def test_hybrid_system():
    """하이브리드 지표 시스템 테스트"""
    
    print('📊 하이브리드 지표 계산 시스템 테스트')
    print('=' * 50)
    
    # 샘플 데이터 생성
    dates = pd.date_range('2024-01-01', periods=50, freq='D')
    data = pd.DataFrame({
        'close': np.random.randn(50).cumsum() + 100,
        'open': np.random.randn(50).cumsum() + 100,
        'high': np.random.randn(50).cumsum() + 105,
        'low': np.random.randn(50).cumsum() + 95,
        'volume': np.random.randint(1000, 10000, 50)
    }, index=dates)
    
    print(f'샘플 데이터 생성: {len(data)}개 일봉')
    print(f'가격 범위: {data["close"].min():.1f} ~ {data["close"].max():.1f}')
    
    # 계산기 초기화
    calc = IndicatorCalculator()
    
    # 1. 핵심 지표 테스트 (코드 기반)
    print('\n🔥 핵심 지표 (코드 기반 - 고성능)')
    sma = calc.calculate('SMA', data, period=10)
    ema = calc.calculate('EMA', data, period=10)
    rsi = calc.calculate('RSI', data, period=14)
    
    print(f'SMA(10) 최근 3값: {sma.tail(3).round(2).tolist()}')
    print(f'EMA(10) 최근 3값: {ema.tail(3).round(2).tolist()}')
    print(f'RSI(14) 최근 3값: {rsi.tail(3).round(2).tolist()}')
    
    # 2. 복합 지표 테스트
    print('\n📈 복합 지표 테스트')
    macd = calc.calculate('MACD', data, fast=12, slow=26, signal=9)
    bollinger = calc.calculate('BOLLINGER_BANDS', data, period=20, std_dev=2.0)
    
    print(f'MACD 최근값: {macd.tail(1)["macd"].iloc[0]:.4f}')
    print(f'볼린저 상단: {bollinger.tail(1)["upper"].iloc[0]:.2f}')
    print(f'볼린저 하단: {bollinger.tail(1)["lower"].iloc[0]:.2f}')
    
    # 3. 사용 가능한 지표 조회
    print('\n📋 사용 가능한 지표 목록')
    indicators = calc.get_available_indicators()
    
    core_count = len(indicators['core'])
    custom_count = len(indicators['custom'])
    
    print(f'핵심 지표: {core_count}개')
    for i, ind in enumerate(indicators['core'][:3]):
        print(f'  {i+1}. {ind["id"]}: {ind["performance"]} 성능')
    
    print(f'사용자 정의: {custom_count}개')
    for i, ind in enumerate(indicators['custom'][:2]):
        print(f'  {i+1}. {ind["id"]}: {ind["name_ko"]}')
    
    # 4. 성능 비교
    print('\n⚡ 성능 특성')
    print('핵심 지표 (코드기반): 최고 성능, 타입 안전, 개발자만 추가')
    print('사용자 정의 (DB기반): 유연성, 실시간 추가, 사용자 확장 가능')
    
    print('\n✅ 하이브리드 시스템 테스트 완료!')
    print('💡 결론: 성능 중시 지표는 코드로, 유연성 중시는 DB로!')

if __name__ == "__main__":
    test_hybrid_system()
