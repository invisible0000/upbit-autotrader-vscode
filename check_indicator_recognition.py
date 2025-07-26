#!/usr/bin/env python3
"""
조건 다이얼로그가 실제로 인식하는 지표 목록 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
    
    print("🔍 조건 다이얼로그 지표 인식 상태 확인")
    print("=" * 50)
    
    vd = VariableDefinitions()
    category_vars = vd.get_category_variables()
    indicator_vars = category_vars.get('indicator', [])
    
    print(f'📊 **인식된 지표 목록** ({len(indicator_vars)}개):')
    for i, (var_id, var_name) in enumerate(indicator_vars, 1):
        print(f'  {i:2d}. {var_id}: {var_name}')
    
    print(f'\n✅ 총 {len(indicator_vars)}개 지표 인식됨')
    
    print('\n🔍 **ATR, VOLUME_SMA 확인**:')
    atr_found = any(var_id == 'ATR' for var_id, _ in indicator_vars)
    volume_sma_found = any(var_id == 'VOLUME_SMA' for var_id, _ in indicator_vars)
    print(f'  • ATR: {"✅ 발견" if atr_found else "❌ 누락"}')
    print(f'  • VOLUME_SMA: {"✅ 발견" if volume_sma_found else "❌ 누락"}')
    
    print('\n📋 **각 지표별 파라미터 확인**:')
    test_indicators = ['ATR', 'VOLUME_SMA', 'SMA', 'EMA', 'RSI']
    for indicator in test_indicators:
        params = vd.get_variable_parameters(indicator)
        if params:
            param_count = len(params)
            print(f'  • {indicator}: ✅ {param_count}개 파라미터')
        else:
            print(f'  • {indicator}: ❌ 파라미터 없음')
    
    print('\n🎯 **Step 4.1 결과 요약**:')
    success_count = 0
    total_tests = 4
    
    # 1. 지표 인식 테스트
    if len(indicator_vars) > 0:
        print('  ✅ 지표 목록 로딩: 성공')
        success_count += 1
    else:
        print('  ❌ 지표 목록 로딩: 실패')
    
    # 2. 새 지표 인식 테스트
    if atr_found and volume_sma_found:
        print('  ✅ 새 지표 인식: 성공 (2/2)')
        success_count += 1
    elif atr_found or volume_sma_found:
        print('  🔶 새 지표 인식: 부분 성공 (1/2)')
        success_count += 0.5
    else:
        print('  ❌ 새 지표 인식: 실패 (0/2)')
    
    # 3. 파라미터 정의 테스트
    param_success = sum(1 for indicator in test_indicators if vd.get_variable_parameters(indicator))
    if param_success >= 4:
        print(f'  ✅ 파라미터 정의: 성공 ({param_success}/5)')
        success_count += 1
    elif param_success >= 2:
        print(f'  🔶 파라미터 정의: 부분 성공 ({param_success}/5)')
        success_count += 0.5
    else:
        print(f'  ❌ 파라미터 정의: 실패 ({param_success}/5)')
    
    # 4. 전체 범주 확인
    total_categories = len(category_vars)
    if total_categories >= 4:
        print(f'  ✅ 범주 구성: 성공 ({total_categories}개 범주)')
        success_count += 1
    else:
        print(f'  🔶 범주 구성: 부족 ({total_categories}개 범주)')
        success_count += 0.5
    
    success_rate = (success_count / total_tests) * 100
    print(f'\n📈 **Step 4.1 성공률**: {success_count}/{total_tests} ({success_rate:.1f}%)')
    
    if success_rate >= 90:
        print('🎉 **Step 4.1 조건 다이얼로그 연동 테스트 성공!**')
    elif success_rate >= 70:
        print('🔶 **Step 4.1 부분 성공 - 일부 개선 필요**')
    else:
        print('❌ **Step 4.1 실패 - 추가 작업 필요**')

except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("조건 다이얼로그 연동에 문제가 있습니다.")
except Exception as e:
    print(f"❌ 테스트 실행 중 오류 발생: {e}")
