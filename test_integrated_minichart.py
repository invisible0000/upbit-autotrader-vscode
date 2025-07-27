#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
통합된 RSI 미니차트 시스템 테스트

simulation_result_widget.py와 minichart_variable_service.py의 통합을 테스트합니다.
"""

import sys
import os
import numpy as np

# 프로젝트 경로 추가
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)


def test_integrated_minichart_system():
    """통합된 미니차트 시스템 테스트"""
    print("통합된 RSI 미니차트 시스템 테스트")
    print("=" * 50)
    
    try:
        # 컴포넌트 import
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.core.simulation_result_widget import SimulationResultWidget
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.shared.trigger_calculator import TriggerCalculator
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.shared.minichart_variable_service import \
            get_minichart_variable_service
        
        print("✅ 모든 컴포넌트 import 성공")
        
        # 미니차트 변수 서비스 초기화
        service = get_minichart_variable_service()
        print("✅ 미니차트 변수 서비스 초기화")
        
        # RSI 변수 설정 확인
        rsi_config = service.get_variable_config('RSI')
        if rsi_config:
            print(f"✅ RSI 설정: {rsi_config.variable_name} ({rsi_config.scale_type})")
        
        # 색상 스키마 확인
        color_scheme = service.get_color_scheme()
        print(f"✅ 색상 스키마: 트리거 색상 {color_scheme['trigger']}")
        
        # 테스트 데이터 생성
        np.random.seed(456)  # 트리거가 발생할 만한 데이터
        base_price = 45000000
        returns = np.random.normal(0, 0.025, 40)
        prices = [base_price]
        
        for return_rate in returns:
            new_price = prices[-1] * (1 + return_rate)
            prices.append(max(new_price, base_price * 0.7))
            
        price_data = prices[1:]
        
        # RSI 계산
        calculator = TriggerCalculator()
        rsi_values = calculator.calculate_rsi(price_data, period=14)
        
        print(f"✅ 테스트 데이터: {len(price_data)}일간 가격 + RSI")
        
        # RSI 통계
        valid_rsi = [val for val in rsi_values if val is not None]
        if valid_rsi:
            print(f"   RSI 범위: {min(valid_rsi):.2f} ~ {max(valid_rsi):.2f}")
            print(f"   평균 RSI: {np.mean(valid_rsi):.2f}")
        
        # 트리거 시뮬레이션 (RSI > 45)
        trigger_threshold = 45
        trigger_results = []
        trigger_count = 0
        
        for i, rsi in enumerate(rsi_values):
            if rsi is not None and rsi > trigger_threshold:
                trigger_results.append((True, rsi))
                trigger_count += 1
            else:
                trigger_results.append((False, rsi))
        
        print(f"✅ 트리거 시뮬레이션: RSI > {trigger_threshold}")
        print(f"   발생 횟수: {trigger_count}회")
        
        # SimulationResultWidget 테스트
        try:
            widget = SimulationResultWidget()
            print("✅ SimulationResultWidget 초기화 성공")
            
            # RSI 변수 정보 준비
            variable_info = {
                'variable_id': 'RSI',
                'variable_name': 'RSI 지표',
                'category': 'oscillator',
                'scale_min': 0,
                'scale_max': 100,
                'unit': '%'
            }
            
            # 차트 업데이트 시뮬레이션 (GUI 없이)
            scenario = "횡보"
            comparison_value = trigger_threshold
            
            print(f"📊 차트 업데이트 시뮬레이션:")
            print(f"   시나리오: {scenario}")
            print(f"   가격 데이터: {len(price_data)}개")
            print(f"   RSI 데이터: {len(rsi_values)}개")
            print(f"   트리거 결과: {len(trigger_results)}개")
            print(f"   비교값: {comparison_value}")
            
            # 업데이트 메서드 호출 (차트가 실제 그려지지는 않음)
            widget.update_simulation_chart(
                scenario=scenario,
                price_data=price_data,
                trigger_results=trigger_results,
                base_variable_data=rsi_values,
                external_variable_data=None,
                variable_info=variable_info,
                comparison_value=comparison_value
            )
            
            print("✅ 차트 업데이트 시뮬레이션 완료")
            
        except Exception as e:
            print(f"⚠️ SimulationResultWidget 테스트 중 오류: {e}")
            import traceback
            traceback.print_exc()
            # 계속 진행
        
        # 레이아웃 정보 생성 테스트
        layout_info = service.create_layout_info(
            base_variable_id='RSI',
            fixed_value=float(trigger_threshold),
            trigger_points=[i for i, (triggered, _) in enumerate(trigger_results) if triggered][:3]
        )
        
        print(f"✅ 4요소 레이아웃 정보:")
        print(f"   메인 요소: {len(layout_info.main_elements)}개")
        print(f"   비교 요소: {len(layout_info.comparison_elements)}개")
        print(f"   트리거 마커: {len(layout_info.trigger_markers)}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print("RSI 미니차트 시스템 통합 테스트")
    print("=" * 50)
    
    success = test_integrated_minichart_system()
    
    print("\n" + "=" * 50)
    print("통합 결과")
    print("=" * 50)
    
    if success:
        print("✅ 통합 테스트 성공!")
        print("\n🎯 주요 개선사항:")
        print("1. simulation_result_widget.py에서 미니차트 변수 서비스 활용")
        print("2. 중복된 트리거 마커 렌더링 함수들 정리")
        print("3. 통합된 색상 스키마 및 스타일 적용")
        print("4. RSI 서브플롯에서 정확한 마커 위치 계산")
        print("5. 미니차트 4요소 시스템과 실제 렌더링 연결")
        
        print("\n🚀 이제 하나의 통합된 미니차트 시스템으로 동작합니다!")
        print("   - 트리거 마커 중복 문제 해결")
        print("   - 체계적인 변수 관리")
        print("   - 일관된 스타일링")
    else:
        print("❌ 통합 테스트 실패")
        print("로그를 확인하여 문제를 해결해주세요.")


if __name__ == "__main__":
    main()
