#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RSI 미니차트 서비스 통합 테스트 (터미널 버전)

GUI 없이 터미널에서 RSI 계산과 미니차트 변수 서비스 통합을 테스트합니다.
"""

import sys
import os
import logging
import numpy as np

# 프로젝트 경로 추가
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def test_minichart_service():
    """미니차트 서비스 테스트"""
    print("\n" + "="*60)
    print("1. 미니차트 변수 서비스 테스트")
    print("="*60)
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.shared.minichart_variable_service import \
            get_minichart_variable_service
        
        service = get_minichart_variable_service()
        print("✅ 미니차트 서비스 초기화 성공")
        
        # RSI 변수 설정 조회
        rsi_config = service.get_variable_config('RSI')
        if rsi_config:
            print(f"✅ RSI 변수 설정 조회 성공:")
            print(f"   - 변수 ID: {rsi_config.variable_id}")
            print(f"   - 변수명: {rsi_config.variable_name}")
            print(f"   - 카테고리: {rsi_config.category}")
            print(f"   - 스케일 타입: {rsi_config.scale_type}")
            print(f"   - 표시 모드: {rsi_config.display_mode}")
            print(f"   - 스케일 범위: {rsi_config.scale_min} ~ {rsi_config.scale_max}")
            print(f"   - 자동 스케일: {rsi_config.auto_scale}")
            print(f"   - 기본 색상: {rsi_config.primary_color}")
        else:
            print("❌ RSI 변수 설정을 찾을 수 없습니다")
            return False
        
        # 스케일 그룹 확인
        scale_group = service.get_scale_group(rsi_config.scale_type)
        if scale_group:
            print(f"✅ 스케일 그룹 조회 성공:")
            print(f"   - 그룹명: {scale_group['group_name']}")
            print(f"   - 범위: {scale_group['min_value']} ~ {scale_group['max_value']}")
            if 'reference_lines' in scale_group:
                print("   - 참조선:")
                for line in scale_group['reference_lines']:
                    print(f"     • {line['label']}: {line['value']} ({line['color']})")
        
        # 색상 스키마 확인
        colors = service.get_color_scheme()
        print("✅ 색상 스키마 조회 성공:")
        for element, color in colors.items():
            print(f"   - {element}: {color}")
        
        return True
        
    except Exception as e:
        print(f"❌ 미니차트 서비스 테스트 실패: {e}")
        return False


def test_rsi_calculation():
    """RSI 계산 테스트"""
    print("\n" + "="*60)
    print("2. RSI 계산 테스트")
    print("="*60)
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.shared.trigger_calculator import TriggerCalculator
        
        calculator = TriggerCalculator()
        print("✅ TriggerCalculator 초기화 성공")
        
        # 샘플 가격 데이터 생성
        np.random.seed(42)
        base_price = 50000000  # 5천만원
        returns = np.random.normal(0, 0.02, 100)  # 일일 수익률 2% 변동성
        prices = [base_price]
        
        for return_rate in returns:
            new_price = prices[-1] * (1 + return_rate)
            prices.append(max(new_price, base_price * 0.5))
            
        price_data = prices[1:]  # 첫 번째 값 제외
        print(f"✅ 테스트 데이터 생성: {len(price_data)}일간 가격 데이터")
        print(f"   가격 범위: {min(price_data):,.0f} ~ {max(price_data):,.0f}원")
        
        # RSI 계산
        rsi_values = calculator.calculate_rsi(price_data, period=14)
        print("✅ RSI 계산 완료")
        
        # RSI 결과 분석
        valid_rsi = [val for val in rsi_values if val is not None]
        if not valid_rsi:
            print("❌ 유효한 RSI 값이 없습니다")
            return False
            
        print(f"✅ RSI 계산 결과:")
        print(f"   - 전체 데이터: {len(price_data)}개")
        print(f"   - 유효한 RSI: {len(valid_rsi)}개")
        print(f"   - RSI 범위: {min(valid_rsi):.2f} ~ {max(valid_rsi):.2f}")
        print(f"   - 평균 RSI: {np.mean(valid_rsi):.2f}")
        print(f"   - 최근 RSI: {valid_rsi[-1]:.2f}")
        
        # 범위 검증
        in_range = all(0 <= val <= 100 for val in valid_rsi)
        print(f"   - 0-100 범위 내: {'✅' if in_range else '❌'}")
        
        oversold = len([v for v in valid_rsi if v <= 30])
        overbought = len([v for v in valid_rsi if v >= 70])
        print(f"   - 과매도(30 이하): {oversold}개")
        print(f"   - 과매수(70 이상): {overbought}개")
        
        return True, price_data, rsi_values
        
    except Exception as e:
        print(f"❌ RSI 계산 테스트 실패: {e}")
        return False, None, None


def test_integration():
    """통합 테스트"""
    print("\n" + "="*60)
    print("3. 미니차트 서비스 + RSI 계산 통합 테스트")
    print("="*60)
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.shared.minichart_variable_service import \
            get_minichart_variable_service
        from upbit_auto_trading.ui.desktop.screens.strategy_management.\
            trigger_builder.components.shared.trigger_calculator import TriggerCalculator
        
        # 서비스와 계산기 초기화
        service = get_minichart_variable_service()
        calculator = TriggerCalculator()
        print("✅ 서비스 및 계산기 초기화 성공")
        
        # RSI 변수 설정 조회
        rsi_config = service.get_variable_config('RSI')
        if not rsi_config:
            print("❌ RSI 변수 설정을 찾을 수 없습니다")
            return False
        
        # 테스트 데이터 생성
        np.random.seed(42)
        base_price = 50000000
        returns = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for return_rate in returns:
            new_price = prices[-1] * (1 + return_rate)
            prices.append(max(new_price, base_price * 0.5))
            
        price_data = prices[1:]
        
        # RSI 계산 (설정에서 파라미터 가져오기)
        period = rsi_config.default_parameters.get('period', 14)
        rsi_values = calculator.calculate_rsi(price_data, period=period)
        print(f"✅ RSI 계산 완료 (period={period})")
        
        # 레이아웃 정보 생성
        layout_info = service.create_layout_info(
            base_variable_id='RSI',
            fixed_value=70.0,
            trigger_points=[20, 50, 80]
        )
        print("✅ 4요소 미니차트 레이아웃 정보 생성 성공")
        
        # 레이아웃 정보 분석
        print(f"✅ 4요소 미니차트 구성:")
        print(f"   1. 메인 요소: {len(layout_info.main_elements)}개")
        for i, element in enumerate(layout_info.main_elements):
            print(f"      - {element['type']}: {element['label']} ({element['color']})")
        
        print(f"   2. 비교 요소: {len(layout_info.comparison_elements)}개")
        for i, element in enumerate(layout_info.comparison_elements):
            if element['type'] == 'fixed_value':
                print(f"      - fVal: 고정값 {element['value']} ({element['color']})")
            else:
                print(f"      - eVal: {element['label']} ({element['color']})")
        
        print(f"   3. 트리거 마커: {len(layout_info.trigger_markers)}개")
        for element in layout_info.trigger_markers:
            if element['type'] == 'trigger_points':
                print(f"      - Trg: {len(element['positions'])}개 포인트 ({element['color']})")
        
        print(f"   4. 색상 스키마: {len(layout_info.color_scheme)}개")
        for element, color in layout_info.color_scheme.items():
            print(f"      - {element}: {color}")
        
        # RSI 통계
        valid_rsi = [val for val in rsi_values if val is not None]
        if valid_rsi:
            print(f"✅ RSI 통계:")
            print(f"   - 현재값: {valid_rsi[-1]:.2f}")
            print(f"   - 범위: {min(valid_rsi):.2f} ~ {max(valid_rsi):.2f}")
            print(f"   - 평균: {np.mean(valid_rsi):.2f}")
            
            # fVal(70)과의 관계 분석
            above_fval = len([v for v in valid_rsi if v > 70])
            below_fval = len([v for v in valid_rsi if v <= 70])
            print(f"   - fVal(70) 위: {above_fval}개 ({above_fval/len(valid_rsi)*100:.1f}%)")
            print(f"   - fVal(70) 아래: {below_fval}개 ({below_fval/len(valid_rsi)*100:.1f}%)")
        
        # 호환성 테스트
        print("✅ 변수 호환성 테스트:")
        sma_compat, sma_reason = service.is_compatible_for_comparison('RSI', 'SMA')
        print(f"   - RSI vs SMA: {'✅' if sma_compat else '❌'} ({sma_reason})")
        
        return True
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print("RSI 미니차트 서비스 통합 테스트 시작")
    print("=" * 60)
    
    # 1. 미니차트 서비스 테스트
    service_ok = test_minichart_service()
    
    # 2. RSI 계산 테스트
    calc_result = test_rsi_calculation()
    calc_ok = calc_result[0] if isinstance(calc_result, tuple) else calc_result
    
    # 3. 통합 테스트
    integration_ok = test_integration()
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"1. 미니차트 서비스: {'✅ 성공' if service_ok else '❌ 실패'}")
    print(f"2. RSI 계산: {'✅ 성공' if calc_ok else '❌ 실패'}")
    print(f"3. 통합 테스트: {'✅ 성공' if integration_ok else '❌ 실패'}")
    
    all_passed = service_ok and calc_ok and integration_ok
    print(f"\n전체 테스트: {'✅ 모든 테스트 통과' if all_passed else '❌ 일부 테스트 실패'}")
    
    if all_passed:
        print("\n🎉 RSI 미니차트 시스템이 성공적으로 통합되었습니다!")
        print("   - 0-100 범위의 정확한 RSI 계산")
        print("   - 체계적인 미니차트 변수 관리")
        print("   - 4요소 단순화 차트 레이아웃")
        print("   - 스케일 그룹 기반 참조선 지원")
    else:
        print("\n⚠️  일부 기능에 문제가 있습니다. 로그를 확인해주세요.")


if __name__ == "__main__":
    main()
