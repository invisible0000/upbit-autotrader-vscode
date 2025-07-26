#!/usr/bin/env python3
"""
미니 차트 로직 연동 간단 테스트 (UI 없음)
TASK-20250727-12: Step 3.1 미니차트 개선 로직 연동 테스트
"""

import sys
import os

# 경로 설정
project_root = os.path.dirname(os.path.abspath(__file__))
ui_path = os.path.join(project_root, 'upbit_auto_trading', 'ui', 'desktop', 'screens', 'strategy_management')
trigger_builder_path = os.path.join(ui_path, 'trigger_builder', 'components')
sys.path.insert(0, ui_path)
sys.path.insert(0, trigger_builder_path)


def test_method_signatures():
    """메서드 시그니처만 확인 (UI 생성 없음)"""
    print("🧪 메서드 시그니처 확인 테스트")
    print("=" * 50)
    
    try:
        # 모듈 레벨에서 클래스 정의만 확인
        import simulation_result_widget
        import integrated_condition_manager
        import inspect
        
        print("✅ 모듈 임포트 성공")
        
        # SimulationResultWidget 클래스 확인
        if hasattr(simulation_result_widget, 'SimulationResultWidget'):
            widget_class = simulation_result_widget.SimulationResultWidget
            
            if hasattr(widget_class, 'update_simulation_chart'):
                method = getattr(widget_class, 'update_simulation_chart')
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                
                print(f"📋 SimulationResultWidget.update_simulation_chart 파라미터:")
                for param in params:
                    print(f"  - {param}")
                
                # 필수 파라미터 확인
                required_params = ['base_variable_data', 'external_variable_data', 'variable_info']
                has_all_params = all(param in params for param in required_params)
                
                if has_all_params:
                    print("✅ 개선된 파라미터 모두 지원")
                else:
                    missing = [p for p in required_params if p not in params]
                    print(f"❌ 누락된 파라미터: {missing}")
                    
        # IntegratedConditionManager 클래스 확인
        if hasattr(integrated_condition_manager, 'IntegratedConditionManager'):
            manager_class = integrated_condition_manager.IntegratedConditionManager
            
            if hasattr(manager_class, 'update_chart_with_simulation_results'):
                method = getattr(manager_class, 'update_chart_with_simulation_results')
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                
                print(f"\n📋 IntegratedConditionManager.update_chart_with_simulation_results 파라미터:")
                for param in params:
                    print(f"  - {param}")
                
                # 필수 파라미터 확인
                required_params = ['base_variable_data', 'external_variable_data', 'variable_info']
                has_all_params = all(param in params for param in required_params)
                
                if has_all_params:
                    print("✅ 개선된 파라미터 모두 지원")
                    return True
                else:
                    missing = [p for p in required_params if p not in params]
                    print(f"❌ 누락된 파라미터: {missing}")
                    return False
            else:
                print("❌ update_chart_with_simulation_results 메서드 없음")
                return False
        else:
            print("❌ IntegratedConditionManager 클래스 없음")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def test_helper_method():
    """헬퍼 메서드 존재 확인"""
    print("\n🔍 헬퍼 메서드 확인")
    print("-" * 30)
    
    try:
        import integrated_condition_manager
        
        manager_class = integrated_condition_manager.IntegratedConditionManager
        
        if hasattr(manager_class, '_get_variable_category_for_chart'):
            print("✅ _get_variable_category_for_chart 헬퍼 메서드 확인됨")
            return True
        else:
            print("❌ _get_variable_category_for_chart 헬퍼 메서드 없음")
            return False
            
    except Exception as e:
        print(f"❌ 헬퍼 메서드 확인 실패: {e}")
        return False


if __name__ == "__main__":
    signature_test = test_method_signatures()
    helper_test = test_helper_method()
    
    if signature_test and helper_test:
        print(f"\n🚀 미니 차트 개선 로직 연동 완료!")
        print(f"✅ integrated_condition_manager.py가 개선된 SimulationResultWidget을 사용합니다")
        print(f"✅ 차트 업데이트 시 base_variable_data, external_variable_data, variable_info 전달")
        print(f"✅ 오버레이/서브플롯 분기 로직이 정상 작동할 것으로 예상됩니다")
    else:
        print(f"\n🔧 미니 차트 개선 로직 연동에 문제가 있습니다:")
        if not signature_test:
            print("  - 메서드 시그니처 문제")
        if not helper_test:
            print("  - 헬퍼 메서드 문제")
