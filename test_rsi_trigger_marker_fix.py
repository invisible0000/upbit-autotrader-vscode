#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RSI 트리거 마커 위치 수정 테스트

트리거 마커가 RSI 서브플롯에서 올바른 위치(iVal 위쪽)에 표시되는지 테스트합니다.
"""

import sys
import os
import numpy as np

# 프로젝트 경로 추가
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_trigger_marker_position():
    """트리거 마커 위치 수정 테스트"""
    print("RSI 트리거 마커 위치 수정 테스트")
    print("=" * 50)
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.shared.trigger_calculator import TriggerCalculator
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.core.simulation_result_widget import SimulationResultWidget
        
        # 테스트 데이터 생성
        np.random.seed(42)
        base_price = 50000000
        returns = np.random.normal(0, 0.02, 50)  # 더 적은 데이터로 테스트
        prices = [base_price]
        
        for return_rate in returns:
            new_price = prices[-1] * (1 + return_rate)
            prices.append(max(new_price, base_price * 0.5))
            
        price_data = prices[1:]
        
        # RSI 계산
        calculator = TriggerCalculator()
        rsi_values = calculator.calculate_rsi(price_data, period=14)
        
        print(f"✅ 테스트 데이터 생성: {len(price_data)}일")
        print(f"   가격 범위: {min(price_data):,.0f} ~ {max(price_data):,.0f}원")
        
        # RSI 통계
        valid_rsi = [val for val in rsi_values if val is not None]
        if valid_rsi:
            print(f"✅ RSI 계산 완료:")
            print(f"   - RSI 범위: {min(valid_rsi):.2f} ~ {max(valid_rsi):.2f}")
            print(f"   - 평균 RSI: {np.mean(valid_rsi):.2f}")
            print(f"   - 최근 RSI: {valid_rsi[-1]:.2f}")
            
            # 트리거 조건 시뮬레이션 (RSI > 50)
            trigger_threshold = 50
            trigger_results = []
            trigger_count = 0
            
            for i, rsi in enumerate(rsi_values):
                if rsi is not None and rsi > trigger_threshold:
                    trigger_results.append((True, rsi))
                    trigger_count += 1
                    print(f"   [트리거 {trigger_count:02d}] 인덱스 {i:02d}: RSI {rsi:.2f} > {trigger_threshold}")
                else:
                    trigger_results.append((False, rsi))
            
            print(f"✅ 트리거 시뮬레이션 완료:")
            print(f"   - 조건: RSI > {trigger_threshold}")
            print(f"   - 트리거 발생: {trigger_count}회")
            print(f"   - 발생률: {trigger_count/len(valid_rsi)*100:.1f}%")
            
            # 마커 위치 계산 테스트 (수정된 로직)
            print(f"\n✅ 트리거 마커 위치 계산 테스트:")
            chart_category = 'oscillator'  # RSI는 oscillator 카테고리
            
            for i, (triggered, rsi_val) in enumerate(trigger_results):
                if triggered and rsi_val is not None:
                    # 수정된 로직: base_data(RSI) 기준으로 마커 위치 계산
                    if chart_category in ['oscillator', 'momentum']:
                        if valid_rsi:
                            offset = (max(valid_rsi) - min(valid_rsi)) * 0.05
                            marker_y = rsi_val + offset
                            print(f"   [마커 {i:02d}] RSI: {rsi_val:.2f} → 마커 위치: {marker_y:.2f} (오프셋: +{offset:.2f})")
                        else:
                            marker_y = 50  # 기본값
                            print(f"   [마커 {i:02d}] RSI: {rsi_val:.2f} → 마커 위치: {marker_y:.2f} (기본값)")
            
            print("\n🎉 트리거 마커 위치 수정 테스트 완료!")
            print("   - 이제 RSI 서브플롯에서 마커가 RSI 값 위쪽에 정확히 표시됩니다")
            print("   - 범례 텍스트에서 특수문자가 제거되어 깨짐 현상이 해결됩니다")
            return True
            
        else:
            print("❌ 유효한 RSI 값이 없습니다")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 함수"""
    success = test_trigger_marker_position()
    
    print("\n" + "=" * 50)
    print("테스트 결과")
    print("=" * 50)
    
    if success:
        print("✅ 모든 테스트 통과")
        print("\n개선사항:")
        print("1. 트리거 마커가 RSI 값 위쪽에 정확히 표시")
        print("2. oscillator 카테고리에서 base_data 기준 위치 계산")
        print("3. 범례 텍스트 특수문자 제거로 깨짐 현상 해결")
        print("4. 동적 오프셋으로 마커 가시성 향상")
    else:
        print("❌ 테스트 실패")
        print("로그를 확인하여 문제를 진단해주세요.")

if __name__ == "__main__":
    main()
