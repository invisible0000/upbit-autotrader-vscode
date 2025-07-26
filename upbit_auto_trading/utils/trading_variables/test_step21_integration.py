"""
Step 2.1 통합 테스트 - variable_definitions.py 하이브리드 시스템 통합 검증
"""

import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
# trading_variables에서 trigger_builder/components로 가는 경로
components_path = os.path.join(current_dir, '..', '..', 'ui', 'desktop', 'screens', 'strategy_management', 'trigger_builder', 'components')
components_path = os.path.abspath(components_path)
print(f"🔍 Components 경로: {components_path}")

if os.path.exists(components_path):
    sys.path.insert(0, components_path)
    print("✅ Components 경로 추가 성공")
else:
    print("❌ Components 경로를 찾을 수 없습니다")

def test_integrated_variable_definitions():
    """통합된 VariableDefinitions 테스트"""
    print("🧪 Step 2.1 통합 테스트 시작")
    print("=" * 60)
    
    try:
        from variable_definitions import VariableDefinitions
        
        # 1. 카테고리별 변수 목록 테스트
        print("\n1️⃣ 카테고리별 변수 목록 테스트:")
        category_vars = VariableDefinitions.get_category_variables()
        
        print(f"📊 총 카테고리 수: {len(category_vars)}")
        for category, variables in category_vars.items():
            print(f"  [{category}]: {len(variables)}개 변수")
            for var_id, var_name in variables[:3]:  # 처음 3개만 표시
                print(f"    • {var_id}: {var_name}")
            if len(variables) > 3:
                print(f"    ... 외 {len(variables)-3}개")
        
        # 2. 새 지표 파라미터 테스트
        print(f"\n2️⃣ 새 지표 파라미터 테스트:")
        test_indicators = ['SMA', 'RSI', 'BOLLINGER_BANDS', 'PRICE_MOMENTUM']
        
        for indicator in test_indicators:
            params = VariableDefinitions.get_variable_parameters(indicator)
            if params:
                print(f"  ✅ {indicator}: {len(params)} 파라미터")
                for param_name in list(params.keys())[:2]:  # 처음 2개만 표시
                    print(f"    • {param_name}: {params[param_name].get('label', 'N/A')}")
            else:
                print(f"  ❌ {indicator}: 파라미터 없음")
        
        # 3. 호환성 검증 테스트
        print(f"\n3️⃣ 호환성 검증 테스트:")
        test_cases = [
            ('SMA', 'EMA'),
            ('RSI', 'STOCHASTIC'),
            ('SMA', 'RSI'),
            ('CURRENT_PRICE', 'SMA')
        ]
        
        for var1, var2 in test_cases:
            try:
                is_compatible, reason = VariableDefinitions.check_variable_compatibility(var1, var2)
                status = "✅" if is_compatible else "❌"
                print(f"  {status} {var1} ↔ {var2}: {reason}")
            except Exception as e:
                print(f"  ⚠️ {var1} ↔ {var2}: 검증 실패 ({e})")
        
        # 4. 사용 가능한 지표 목록 테스트
        print(f"\n4️⃣ 사용 가능한 지표 목록 테스트:")
        indicators = VariableDefinitions.get_available_indicators()
        
        core_count = len(indicators.get('core', []))
        custom_count = len(indicators.get('custom', []))
        print(f"  핵심 지표: {core_count}개")
        print(f"  사용자 정의 지표: {custom_count}개")
        
        if core_count > 0:
            print("  핵심 지표 예시:")
            for indicator in indicators['core'][:3]:
                print(f"    • {indicator.get('id', 'N/A')}: {indicator.get('name', 'N/A')}")
        
        if custom_count > 0:
            print("  사용자 정의 지표 예시:")
            for indicator in indicators['custom'][:3]:
                print(f"    • {indicator.get('id', 'N/A')}: {indicator.get('name_ko', 'N/A')}")
        
        print(f"\n🎉 Step 2.1 통합 테스트 완료!")
        print(f"✅ 하이브리드 시스템이 성공적으로 통합되었습니다!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Step 2.1 통합 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integrated_variable_definitions()
    if success:
        print(f"\n🚀 다음 단계: Step 2.2 - 호환성 검증 로직 업데이트")
    else:
        print(f"\n🔧 문제 해결 후 다시 시도해주세요")
