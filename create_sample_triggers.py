"""
샘플 트리거 생성 스크립트
통합 조건 관리 시스템 테스트용 예제 트리거들을 생성합니다.
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(__file__))

from components.condition_storage import ConditionStorage

def create_sample_triggers():
    """실용적인 샘플 트리거들을 생성"""
    
    storage = ConditionStorage()
    
    # 샘플 트리거 데이터
    sample_conditions = [
        {
            'name': '🟢 RSI 과매도 구매 신호',
            'description': 'RSI가 30 이하로 떨어지면 과매도 상태로 판단하여 구매 신호 발생',
            'variable_id': 'rsi_14',
            'variable_name': 'rsi',
            'variable_params': {'period': 14},
            'operator': '<=',
            'comparison_type': 'value',
            'target_value': '30',
            'category': 'technical_buy'
        },
        {
            'name': '🔴 RSI 과매수 매도 신호',
            'description': 'RSI가 70 이상으로 올라가면 과매수 상태로 판단하여 매도 신호 발생',
            'variable_id': 'rsi_14',
            'variable_name': 'rsi',
            'variable_params': {'period': 14},
            'operator': '>=',
            'comparison_type': 'value',
            'target_value': '70',
            'category': 'technical_sell'
        },
        {
            'name': '📈 골든크로스 (20-60일)',
            'description': '20일 이동평균이 60일 이동평균을 상향 돌파하는 골든크로스 패턴',
            'variable_id': 'ma_cross_20_60',
            'variable_name': 'moving_average',
            'variable_params': {'short_period': 20, 'long_period': 60},
            'operator': '>',
            'comparison_type': 'cross_up',
            'target_value': 'ma_60',
            'category': 'trend_signal'
        },
        {
            'name': '📉 데드크로스 (20-60일)',
            'description': '20일 이동평균이 60일 이동평균을 하향 돌파하는 데드크로스 패턴',
            'variable_id': 'ma_cross_20_60',
            'variable_name': 'moving_average',
            'variable_params': {'short_period': 20, 'long_period': 60},
            'operator': '<',
            'comparison_type': 'cross_down',
            'target_value': 'ma_60',
            'category': 'trend_signal'
        },
        {
            'name': '💥 급락 감지 (-5% 이상)',
            'description': '5분 내 5% 이상 급락 시 매수 기회로 판단',
            'variable_id': 'price_change_5m',
            'variable_name': 'price_change_rate',
            'variable_params': {'timeframe': '5m'},
            'operator': '<=',
            'comparison_type': 'value',
            'target_value': '-5.0',
            'category': 'volatility_buy'
        },
        {
            'name': '🚀 급등 감지 (+5% 이상)',
            'description': '5분 내 5% 이상 급등 시 매도 기회로 판단',
            'variable_id': 'price_change_5m',
            'variable_name': 'price_change_rate',
            'variable_params': {'timeframe': '5m'},
            'operator': '>=',
            'comparison_type': 'value',
            'target_value': '5.0',
            'category': 'volatility_sell'
        },
        {
            'name': '📊 MACD 골든크로스',
            'description': 'MACD 라인이 시그널 라인을 상향 돌파할 때 매수 신호',
            'variable_id': 'macd_12_26_9',
            'variable_name': 'macd',
            'variable_params': {'fast': 12, 'slow': 26, 'signal': 9},
            'operator': '>',
            'comparison_type': 'cross_up',
            'target_value': 'macd_signal',
            'category': 'momentum_buy'
        },
        {
            'name': '📊 MACD 데드크로스',
            'description': 'MACD 라인이 시그널 라인을 하향 돌파할 때 매도 신호',
            'variable_id': 'macd_12_26_9',
            'variable_name': 'macd',
            'variable_params': {'fast': 12, 'slow': 26, 'signal': 9},
            'operator': '<',
            'comparison_type': 'cross_down',
            'target_value': 'macd_signal',
            'category': 'momentum_sell'
        },
        {
            'name': '💰 거래량 급증 (3배 이상)',
            'description': '평균 거래량 대비 3배 이상 거래량 급증 시 관심 신호',
            'variable_id': 'volume_ratio_20',
            'variable_name': 'volume_ratio',
            'variable_params': {'average_period': 20},
            'operator': '>=',
            'comparison_type': 'value',
            'target_value': '3.0',
            'category': 'volume_signal'
        },
        {
            'name': '🎯 볼린저밴드 하한 터치',
            'description': '가격이 볼린저밴드 하한선에 터치하면 반등 매수 신호',
            'variable_id': 'bb_20_2',
            'variable_name': 'bollinger_bands',
            'variable_params': {'period': 20, 'std_dev': 2},
            'operator': '<=',
            'comparison_type': 'value',
            'target_value': 'bb_lower',
            'category': 'reversal_buy'
        },
        {
            'name': '🎯 볼린거밴드 상한 터치',
            'description': '가격이 볼린저밴드 상한선에 터치하면 되돌림 매도 신호',
            'variable_id': 'bb_20_2',
            'variable_name': 'bollinger_bands',
            'variable_params': {'period': 20, 'std_dev': 2},
            'operator': '>=',
            'comparison_type': 'value',
            'target_value': 'bb_upper',
            'category': 'reversal_sell'
        },
        {
            'name': '⚡ 스토캐스틱 과매도',
            'description': 'Stochastic %K가 20 이하에서 %D를 상향 돌파하면 매수 신호',
            'variable_id': 'stoch_14_3',
            'variable_name': 'stochastic',
            'variable_params': {'k_period': 14, 'd_period': 3},
            'operator': '>',
            'comparison_type': 'cross_up_in_oversold',
            'target_value': 'stoch_d',
            'category': 'oscillator_buy'
        }
    ]
    
    print("📝 샘플 트리거 생성 시작...")
    
    created_count = 0
    for condition in sample_conditions:
        try:
            # created_at 추가
            condition['created_at'] = datetime.now().isoformat()
            
            # 조건 저장
            success, message, condition_id = storage.save_condition(condition)
            
            if success:
                created_count += 1
                print(f"✅ {condition['name']} 생성 완료")
            else:
                print(f"❌ {condition['name']} 생성 실패: {message}")
                
        except Exception as e:
            print(f"❌ {condition['name']} 생성 중 예외 발생: {e}")
    
    print(f"\n🎉 샘플 트리거 생성 완료: {created_count}개")
    print("이제 통합 조건 관리 시스템에서 시뮬레이션을 테스트할 수 있습니다!")
    
    return created_count

if __name__ == "__main__":
    print("=== 샘플 트리거 생성 스크립트 ===")
    
    try:
        count = create_sample_triggers()
        print(f"\n✅ 스크립트 실행 완료 - {count}개 트리거 생성됨")
    except Exception as e:
        print(f"\n❌ 스크립트 실행 실패: {e}")
        import traceback
        traceback.print_exc()
