#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3.1: 트리거 빌더 변수 로딩 테스트
=======================================

트리거 빌더에서 새 지표들이 변수 목록에 나타나는지 확인하고,
각 지표의 메타데이터가 올바르게 표시되는지 검증합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "upbit_auto_trading"))

print("🧪 Step 3.1 트리거 빌더 변수 로딩 테스트")
print("=" * 60)

def test_variable_definitions_loading():
    """variable_definitions.py에서 새 지표들이 로딩되는지 테스트"""
    print("1️⃣ variable_definitions.py 모듈 로딩 테스트:")
    
    try:
        # variable_definitions.py 직접 로딩 시도
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
        
        print("  ✅ variable_definitions.py 모듈 로딩 성공")
        
        # 모든 카테고리 변수 확인 (하이브리드 시스템)
        all_category_vars = VariableDefinitions.get_category_variables()
        print(f"  📋 사용 가능한 카테고리: {len(all_category_vars)}개")
        for category in all_category_vars.keys():
            print(f"    • {category}")
        
        # 기본 카테고리 변수 확인
        print("\n2️⃣ 카테고리별 변수 확인:")
        
        # 각 카테고리별로 변수 확인
        for category_name, variables in all_category_vars.items():
            print(f"  📈 {category_name}: {len(variables)}개")
            for var in variables[:3]:  # 처음 3개만 표시
                if isinstance(var, tuple):
                    print(f"    • {var[0]}: {var[1]}")
                elif isinstance(var, dict):
                    print(f"    • {var.get('id', 'N/A')}: {var.get('name', 'N/A')}")
                else:
                    print(f"    • {var}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ variable_definitions.py 로딩 실패: {e}")
        return False

def test_specific_indicators():
    """특정 새 지표들이 올바르게 로딩되는지 테스트"""
    print("\n3️⃣ 새 지표 개별 테스트:")
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
        
        # 테스트할 지표들 (기존 시스템과 호환되는 이름 사용)
        test_indicators = [
            'SMA',           # 단순이동평균
            'EMA',           # 지수이동평균  
            'RSI',           # 상대강도지수
            'MACD',          # MACD
            'BOLLINGER_BAND',  # 볼린저밴드 (기존 시스템과 호환)
            'STOCHASTIC',    # 스토캐스틱 (새로 추가)
            'ATR',           # 평균진실범위
            'VOLUME_SMA'     # 거래량 이동평균
        ]
        
        success_count = 0
        for indicator in test_indicators:
            try:
                params = VariableDefinitions.get_variable_parameters(indicator)
                if params:
                    print(f"  ✅ {indicator}: 파라미터 {len(params)}개")
                    # 첫 번째 파라미터 정보 표시
                    if params:
                        first_param_key = list(params.keys())[0]
                        first_param = params[first_param_key]
                        print(f"    예시: {first_param_key} - {first_param.get('label', 'N/A')} ({first_param.get('type', 'N/A')})")
                    success_count += 1
                else:
                    print(f"  ⚠️ {indicator}: 파라미터 없음")
            except Exception as e:
                print(f"  ❌ {indicator}: 오류 - {e}")
        
        print(f"\n  📊 성공률: {success_count}/{len(test_indicators)} ({success_count / len(test_indicators) * 100:.1f}%)")
        return success_count >= len(test_indicators) * 0.8  # 80% 이상 성공
        
    except Exception as e:
        print(f"  ❌ 지표 테스트 실패: {e}")
        return False

def test_integrated_manager_access():
    """IntegratedVariableManager가 올바르게 연동되는지 테스트"""
    print("\n4️⃣ IntegratedVariableManager 연동 테스트:")
    
    try:
        # variable_definitions에서 IntegratedVariableManager 접근 테스트
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
        
        # 통합 지표 카테고리에서 변수 가져오기
        all_vars = []
        category_vars = VariableDefinitions.get_category_variables()
        
        for category, vars_in_cat in category_vars.items():
            try:
                all_vars.extend(vars_in_cat)
                print(f"  ✅ {category}: {len(vars_in_cat)}개 변수 로딩")
            except Exception as e:
                print(f"  ⚠️ {category}: {e}")
        
        print(f"  📊 총 변수 개수: {len(all_vars)}개")
        
        # 하이브리드 지표 확인 (SMA, EMA, RSI 등)
        hybrid_indicators = ['SMA', 'EMA', 'RSI', 'MACD']
        found_hybrids = []
        
        for var in all_vars:
            if isinstance(var, tuple):
                var_id = var[0]
            elif isinstance(var, dict):
                var_id = var.get('id', '')
            else:
                var_id = str(var)
            
            if var_id in hybrid_indicators:
                found_hybrids.append(var)
        
        print(f"  🔄 하이브리드 지표 발견: {len(found_hybrids)}/{len(hybrid_indicators)}개")
        for var in found_hybrids:
            if isinstance(var, tuple):
                print(f"    • {var[0]}: {var[1]}")
            elif isinstance(var, dict):
                print(f"    • {var.get('id', 'N/A')}: {var.get('name', 'N/A')}")
        
        return len(found_hybrids) >= 2  # 최소 2개 이상 발견
        
    except Exception as e:
        print(f"  ❌ IntegratedVariableManager 연동 실패: {e}")
        return False

def test_trigger_builder_ui_simulation():
    """트리거 빌더 UI에서 실제로 사용할 수 있는지 시뮬레이션"""
    print("\n5️⃣ 트리거 빌더 UI 시뮬레이션:")
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
        
        print("  🎯 시나리오: 사용자가 SMA 지표를 선택하는 과정")
        
        # Step 1: 카테고리 목록 가져오기
        category_vars = VariableDefinitions.get_category_variables()
        print(f"  1️⃣ 카테고리 목록: {len(category_vars)}개")
        
        # Step 2: indicator 카테고리 확인
        if 'indicator' in category_vars:
            indicator_vars = category_vars['indicator']
            print(f"  2️⃣ 지표 변수: {len(indicator_vars)}개")
            
            # Step 3: SMA 지표 찾기
            sma_var = None
            for var in indicator_vars:
                if isinstance(var, tuple) and var[0] == 'SMA':
                    sma_var = var
                    break
                elif isinstance(var, dict) and var.get('id') == 'SMA':
                    sma_var = var
                    break
            
            if sma_var:
                if isinstance(sma_var, tuple):
                    print(f"  3️⃣ SMA 지표 발견: {sma_var[1]}")
                else:
                    print(f"  3️⃣ SMA 지표 발견: {sma_var.get('name', 'N/A')}")
                
                # Step 4: SMA 파라미터 가져오기
                sma_params = VariableDefinitions.get_variable_parameters('SMA')
                print(f"  4️⃣ SMA 파라미터: {len(sma_params)}개")
                for i, (param_key, param_info) in enumerate(sma_params.items()):
                    print(f"    {i + 1}. {param_key}: {param_info.get('label', 'N/A')} ({param_info.get('type', 'N/A')})")
                
                print("  ✅ UI 시뮬레이션 성공!")
                return True
            else:
                print("  ❌ SMA 지표를 찾을 수 없음")
                return False
        else:
            print("  ❌ indicator 카테고리를 찾을 수 없음")
            return False
            
    except Exception as e:
        print(f"  ❌ UI 시뮬레이션 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 Step 3.1 시작: 트리거 빌더 변수 로딩 테스트\n")
    
    test_results = {
        'variable_definitions_loading': test_variable_definitions_loading(),
        'specific_indicators': test_specific_indicators(),
        'integrated_manager_access': test_integrated_manager_access(),
        'trigger_builder_ui_simulation': test_trigger_builder_ui_simulation()
    }
    
    print("\n" + "=" * 60)
    print("📊 Step 3.1 테스트 결과 요약:")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n🎯 전체 성공률: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 Step 3.1 테스트 완료! 트리거 빌더 변수 로딩 성공!")
        print("🚀 다음 단계: Step 3.2 - 호환성 검증 테스트")
    else:
        print("⚠️ Step 3.1 테스트에서 문제 발견. 수정이 필요합니다.")
    
    return success_rate >= 80

if __name__ == "__main__":
    main()
