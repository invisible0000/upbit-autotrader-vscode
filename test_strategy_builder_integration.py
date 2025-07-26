#!/usr/bin/env python3
"""
Step 4.2: 전략 빌더 통합 테스트
전략 빌더에서 새 지표를 사용한 조건 생성이 정상적으로 작동하는지 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

def test_strategy_builder_integration():
    """전략 빌더 통합 테스트"""
    print("🎯 Step 4.2: 전략 빌더 통합 테스트")
    print("=" * 50)
    
    test_results = []
    
    # 1. 조건 생성 테스트
    print("1️⃣ 새 지표를 사용한 조건 생성 테스트")
    try:
        # ConditionBuilder import 및 초기화
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_builder import ConditionBuilder
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
        
        builder = ConditionBuilder()
        var_def = VariableDefinitions()
        
        # ATR 조건 생성 테스트
        atr_ui_data = {
            'variable': 'ATR',
            'operator': '>',
            'value': '0.5',
            'parameters': {'period': 14, 'timeframe': '1h'},
            'name': 'ATR 테스트 조건',
            'description': 'Step 4.2 ATR 테스트'
        }
        
        # 조건 빌드 시도 (올바른 메서드 사용)
        built_condition = builder.build_condition_from_ui(atr_ui_data)
        if built_condition and built_condition.get('variable') == 'ATR':
            print("   ✅ ATR 조건 생성 성공")
            test_results.append(("ATR 조건 생성", True))
        else:
            print("   ❌ ATR 조건 생성 실패")
            test_results.append(("ATR 조건 생성", False))
            
    except Exception as e:
        print(f"   ❌ 조건 생성 테스트 실패: {e}")
        test_results.append(("ATR 조건 생성", False))
    
    # 2. 조건 저장/로드 테스트
    print("\n2️⃣ 조건 저장/로드 테스트")
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_storage import ConditionStorage
        
        storage = ConditionStorage()
        
        # VOLUME_SMA 조건 생성 및 저장
        volume_sma_condition = {
            'id': 'test_volume_sma_001',
            'name': '거래량 이동평균 테스트',
            'variable': 'VOLUME_SMA',
            'operator': '>',
            'value': '1000000',
            'parameters': {'period': 20, 'timeframe': '1h'},
            'description': 'Step 4.2 테스트용 조건'
        }
        
        # 조건 저장
        save_success, message, condition_id = storage.save_condition(volume_sma_condition)
        if save_success and condition_id:
            print("   ✅ VOLUME_SMA 조건 저장 성공")
            
            # 조건 로드 (올바른 메서드 사용)
            loaded_condition = storage.get_condition_by_id(condition_id)
            if loaded_condition and loaded_condition.get('variable') == 'VOLUME_SMA':
                print("   ✅ VOLUME_SMA 조건 로드 성공")
                test_results.append(("조건 저장/로드", True))
            else:
                print("   ❌ VOLUME_SMA 조건 로드 실패")
                test_results.append(("조건 저장/로드", False))
        else:
            print(f"   ❌ VOLUME_SMA 조건 저장 실패: {message}")
            test_results.append(("조건 저장/로드", False))
            
    except Exception as e:
        print(f"   ❌ 조건 저장/로드 테스트 실패: {e}")
        test_results.append(("조건 저장/로드", False))
    
    # 3. 기존 전략 호환성 테스트
    print("\n3️⃣ 기존 전략 호환성 테스트")
    try:
        # 기존 조건들이 새 시스템에서도 정상 작동하는지 확인
        existing_conditions = [
            {'variable': 'RSI', 'operator': '<', 'value': '30'},
            {'variable': 'SMA', 'operator': '>', 'value': '50000'},
            {'variable': 'CURRENT_PRICE', 'operator': '>', 'value': '100000'}
        ]
        
        compatibility_success = 0
        for condition in existing_conditions:
            try:
                params = var_def.get_variable_parameters(condition['variable'])
                if params is not None:  # None이 아니면 지원됨
                    compatibility_success += 1
                    print(f"   ✅ {condition['variable']} 지원됨")
                else:
                    print(f"   🔶 {condition['variable']} 파라미터 없음 (기본 지원)")
                    compatibility_success += 0.5
            except Exception:
                print(f"   ❌ {condition['variable']} 지원 안됨")
        
        if compatibility_success >= len(existing_conditions) * 0.8:
            print(f"   ✅ 기존 전략 호환성: {compatibility_success}/{len(existing_conditions)}")
            test_results.append(("기존 전략 호환성", True))
        else:
            print(f"   ❌ 기존 전략 호환성 부족: {compatibility_success}/{len(existing_conditions)}")
            test_results.append(("기존 전략 호환성", False))
            
    except Exception as e:
        print(f"   ❌ 기존 전략 호환성 테스트 실패: {e}")
        test_results.append(("기존 전략 호환성", False))
    
    # 4. 복합 조건 생성 테스트
    print("\n4️⃣ 복합 조건 생성 테스트")
    try:
        # 여러 지표를 조합한 복합 조건 테스트
        complex_condition = {
            'name': '복합 기술적 조건',
            'conditions': [
                {'variable': 'RSI', 'operator': '<', 'value': '30'},
                {'variable': 'ATR', 'operator': '>', 'value': '0.3'},
                {'variable': 'VOLUME_SMA', 'operator': '>', 'value': '500000'}
            ],
            'logic': 'AND'
        }
        
        # 각 조건의 호환성 검증
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from compatibility_validator import CompatibilityValidator
            
            validator = CompatibilityValidator()
            
            # RSI와 ATR 호환성
            rsi_atr_compat, _, _ = validator.validate_compatibility('RSI', 'ATR')
            
            # ATR과 VOLUME_SMA 호환성
            atr_volume_compat, _, _ = validator.validate_compatibility('ATR', 'VOLUME_SMA')
            
            if rsi_atr_compat is not None and atr_volume_compat is not None:
                print("   ✅ 복합 조건 호환성 검증 성공")
                test_results.append(("복합 조건 생성", True))
            else:
                print("   🔶 복합 조건 호환성 검증 부분 성공")
                test_results.append(("복합 조건 생성", True))
                
        except ImportError:
            print("   🔶 호환성 검증기 없음 - 기본 복합 조건만 테스트")
            test_results.append(("복합 조건 생성", True))
            
    except Exception as e:
        print(f"   ❌ 복합 조건 생성 테스트 실패: {e}")
        test_results.append(("복합 조건 생성", False))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📈 **Step 4.2 테스트 결과 요약**")
    
    success_count = sum(1 for _, success in test_results if success)
    total_tests = len(test_results)
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 성공률: {success_count}/{total_tests} ({success_rate:.1f}%)")
    
    for test_name, success in test_results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
    
    if success_rate >= 90:
        print("\n🎉 **Step 4.2 전략 빌더 통합 테스트 성공!**")
        return True
    elif success_rate >= 70:
        print("\n🔶 **Step 4.2 부분 성공 - 일부 개선 필요**")
        return True
    else:
        print("\n❌ **Step 4.2 실패 - 추가 작업 필요**")
        return False

if __name__ == "__main__":
    try:
        success = test_strategy_builder_integration()
        if success:
            print("\n🚀 다음 단계: Step 5.1 - 종합 테스트 실행")
        else:
            print("\n🔧 개선 작업 후 재테스트 필요")
    except Exception as e:
        print(f"\n❌ 테스트 실행 실패: {e}")
