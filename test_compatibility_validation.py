#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3.2: 통합 호환성 검증 테스트
=================================

새로 구현된 통합 호환성 검증기(CompatibilityValidator)가 
트리거 빌더에서 올바르게 작동하는지 테스트합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "upbit_auto_trading"))

print("🧪 Step 3.2 통합 호환성 검증 테스트")
print("=" * 60)


def test_compatibility_validator():
    """통합 호환성 검증기 테스트"""
    print("1️⃣ 통합 호환성 검증기 테스트:")
    
    try:
        from upbit_auto_trading.utils.trading_variables.compatibility_validator import CompatibilityValidator
        
        validator = CompatibilityValidator()
        print("  ✅ CompatibilityValidator 로딩 성공")
        
        # 기본 호환성 테스트 케이스
        test_cases = [
            # 호환 가능한 경우
            ('SMA', 'EMA', True, "같은 가격 지표"),
            ('RSI', 'STOCHASTIC', True, "같은 오실레이터"),
            ('CURRENT_PRICE', 'BOLLINGER_BAND', True, "가격과 가격 지표"),
            
            # 호환 불가능한 경우  
            ('SMA', 'VOLUME_SMA', False, "가격 vs 거래량"),
            ('RSI', 'ATR', False, "오실레이터 vs 변동성"),
            ('MACD', 'CASH_BALANCE', False, "지표 vs 자본"),
        ]
        
        success_count = 0
        total_tests = len(test_cases)
        
        for var1, var2, expected, description in test_cases:
            try:
                is_compatible, reason, details = validator.validate_compatibility(var1, var2)
                confidence = details.get('confidence_score', 0.0)
                
                if is_compatible == expected:
                    status = "✅"
                    success_count += 1
                else:
                    status = "❌"
                
                print(f"  {status} {var1} ↔ {var2}: {is_compatible} ({confidence:.1f}%) - {reason}")
                print(f"    예상: {expected} ({description})")
                
            except Exception as e:
                print(f"  ❌ {var1} ↔ {var2}: 오류 - {e}")
        
        success_rate = (success_count / total_tests) * 100
        print(f"\n  📊 호환성 검증 성공률: {success_count}/{total_tests} ({success_rate:.1f}%)")
        
        return success_rate >= 80  # 80% 이상 성공
        
    except Exception as e:
        print(f"  ❌ 통합 호환성 검증기 테스트 실패: {e}")
        return False


def test_complex_condition_compatibility():
    """복합 조건 호환성 검증 테스트"""
    print("\n2️⃣ 복합 조건 호환성 테스트:")
    
    try:
        from upbit_auto_trading.utils.trading_variables.compatibility_validator import CompatibilityValidator
        
        validator = CompatibilityValidator()
        
        # 복합 조건 테스트 케이스
        complex_conditions = [
            # 호환 가능한 조합
            (['SMA', 'EMA', 'CURRENT_PRICE'], True, "가격 오버레이 그룹"),
            (['RSI', 'STOCHASTIC'], True, "오실레이터 그룹"),
            
            # 호환 불가능한 조합
            (['SMA', 'RSI', 'VOLUME_SMA'], False, "서로 다른 카테고리 혼합"),
            (['ATR', 'CASH_BALANCE', 'PROFIT_PERCENT'], False, "완전히 다른 타입들"),
        ]
        
        success_count = 0
        for variables, expected, description in complex_conditions:
            try:
                overall_compatible, details = validator.validate_multiple_compatibility(variables)
                overall_score = details.get('overall_score', 0.0)
                incompatible_pairs = details.get('incompatible_pairs', [])
                
                if overall_compatible == expected:
                    status = "✅"
                    success_count += 1
                else:
                    status = "❌"
                
                print(f"  {status} {'+'.join(variables)}: 전체 호환성 {overall_compatible} ({overall_score:.1f}%)")
                print(f"    예상: {expected} ({description})")
                
                if incompatible_pairs:
                    pair_names = [f"{pair[0]}↔{pair[1]}" for pair in incompatible_pairs]
                    print(f"    비호환 쌍: {', '.join(pair_names)}")
                
            except Exception as e:
                print(f"  ❌ {'+'.join(variables)}: 오류 - {e}")
        
        success_rate = (success_count / len(complex_conditions)) * 100
        print(f"\n  📊 복합 조건 검증 성공률: {success_count}/{len(complex_conditions)} ({success_rate:.1f}%)")
        
        return success_rate >= 75  # 75% 이상 성공
        
    except Exception as e:
        print(f"  ❌ 복합 조건 호환성 테스트 실패: {e}")
        return False


def test_alternative_suggestions():
    """대안 제안 기능 테스트"""
    print("\n3️⃣ 대안 제안 기능 테스트:")
    
    try:
        from upbit_auto_trading.utils.trading_variables.compatibility_validator import CompatibilityValidator
        
        validator = CompatibilityValidator()
        
        # 대안 제안 테스트
        test_targets = [
            ('SMA', ['EMA', 'BOLLINGER_BAND', 'RSI', 'VOLUME_SMA']),
            ('RSI', ['STOCHASTIC', 'MACD', 'ATR', 'CURRENT_PRICE']),
        ]
        
        success_count = 0
        for target_var, candidates in test_targets:
            try:
                alternatives = validator.suggest_compatible_alternatives(target_var, candidates)
                
                print(f"  🎯 {target_var}와 호환 가능한 대안들:")
                if alternatives:
                    for alt_var, confidence, reason in alternatives:
                        print(f"    • {alt_var}: {confidence:.1f}% - {reason}")
                    success_count += 1
                else:
                    print(f"    ⚠️ 호환 가능한 대안 없음")
                
            except Exception as e:
                print(f"  ❌ {target_var}: 오류 - {e}")
        
        success_rate = (success_count / len(test_targets)) * 100
        print(f"\n  📊 대안 제안 성공률: {success_count}/{len(test_targets)} ({success_rate:.1f}%)")
        
        return success_rate >= 50  # 50% 이상 성공
        
    except Exception as e:
        print(f"  ❌ 대안 제안 기능 테스트 실패: {e}")
        return False


def test_trigger_builder_integration():
    """트리거 빌더 통합 테스트"""
    print("\n4️⃣ 트리거 빌더 통합 테스트:")
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
        
        # 실제 트리거 빌더에서 호환성 검증 테스트
        test_pairs = [
            ('SMA', 'EMA'),
            ('RSI', 'STOCHASTIC'),  
            ('SMA', 'RSI'),
            ('CURRENT_PRICE', 'BOLLINGER_BAND')
        ]
        
        success_count = 0
        for var1, var2 in test_pairs:
            try:
                is_compatible, reason = VariableDefinitions.check_variable_compatibility(var1, var2)
                print(f"  🔍 {var1} ↔ {var2}: {is_compatible} - {reason}")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ {var1} ↔ {var2}: 오류 - {e}")
        
        success_rate = (success_count / len(test_pairs)) * 100
        print(f"\n  📊 트리거 빌더 통합 성공률: {success_count}/{len(test_pairs)} ({success_rate:.1f}%)")
        
        return success_rate >= 75
        
    except Exception as e:
        print(f"  ❌ 트리거 빌더 통합 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("🚀 Step 3.2 시작: 통합 호환성 검증 테스트\n")
    
    test_results = {
        'compatibility_validator': test_compatibility_validator(),
        'complex_condition_compatibility': test_complex_condition_compatibility(),
        'alternative_suggestions': test_alternative_suggestions(),
        'trigger_builder_integration': test_trigger_builder_integration()
    }
    
    print("\n" + "=" * 60)
    print("📊 Step 3.2 테스트 결과 요약:")
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
    
    if success_rate >= 75:
        print("🎉 Step 3.2 테스트 완료! 통합 호환성 검증 시스템 작동 성공!")
        print("🚀 다음 단계: Step 4.1 - 조건 다이얼로그 연동 테스트")
    else:
        print("⚠️ Step 3.2 테스트에서 문제 발견. 호환성 검증 로직 개선 필요.")
    
    return success_rate >= 75


if __name__ == "__main__":
    main()
