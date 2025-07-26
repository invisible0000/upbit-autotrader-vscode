#!/usr/bin/env python3
"""
미니 차트 로직 연동 테스트
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

def test_mini_chart_integration():
    """미니 차트 개선 로직 연동 테스트"""
    print("🧪 미니 차트 개선 로직 연동 테스트 시작")
    print("=" * 50)
    
    try:
        # SimulationResultWidget 임포트 테스트
        from simulation_result_widget import SimulationResultWidget
        print("✅ SimulationResultWidget 임포트 성공")
        
        # 개선된 차트 메서드 존재 확인
        widget = SimulationResultWidget()
        if hasattr(widget, 'update_simulation_chart'):
            print("✅ update_simulation_chart 메서드 확인됨")
            
            # 메서드 시그니처 확인
            import inspect
            sig = inspect.signature(widget.update_simulation_chart)
            params = list(sig.parameters.keys())
            
            expected_params = ['scenario', 'price_data', 'trigger_results', 
                              'base_variable_data', 'external_variable_data', 'variable_info']
            
            print(f"📋 메서드 파라미터: {params}")
            
            # 필수 파라미터 확인
            has_base_variable_data = 'base_variable_data' in params
            has_external_variable_data = 'external_variable_data' in params
            has_variable_info = 'variable_info' in params
            
            if has_base_variable_data and has_external_variable_data and has_variable_info:
                print("✅ 개선된 파라미터 지원 확인됨")
                return True
            else:
                print(f"❌ 개선된 파라미터 누락:")
                if not has_base_variable_data:
                    print("  - base_variable_data 파라미터 없음")
                if not has_external_variable_data:
                    print("  - external_variable_data 파라미터 없음")
                if not has_variable_info:
                    print("  - variable_info 파라미터 없음")
                return False
        else:
            print("❌ update_simulation_chart 메서드 없음")
            return False
            
    except ImportError as e:
        print(f"❌ SimulationResultWidget 임포트 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def test_integrated_condition_manager_update():
    """IntegratedConditionManager 업데이트 확인"""
    print("\n🔍 IntegratedConditionManager 업데이트 확인")
    print("-" * 40)
    
    try:
        from integrated_condition_manager import IntegratedConditionManager
        print("✅ IntegratedConditionManager 임포트 성공")
        
        # 클래스 인스턴스 생성 시도 (UI 없이)
        # 실제 UI 생성하지 않고 클래스 정의만 확인
        import inspect
        
        # update_chart_with_simulation_results 메서드 시그니처 확인
        if hasattr(IntegratedConditionManager, 'update_chart_with_simulation_results'):
            method = getattr(IntegratedConditionManager, 'update_chart_with_simulation_results')
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            
            print(f"📋 차트 업데이트 메서드 파라미터: {params}")
            
            # 개선된 파라미터 확인
            has_base_variable = 'base_variable_data' in params
            has_external_variable = 'external_variable_data' in params 
            has_variable_info = 'variable_info' in params
            
            if has_base_variable and has_external_variable and has_variable_info:
                print("✅ 개선된 차트 업데이트 메서드 확인됨")
                return True
            else:
                print("❌ 기존 차트 업데이트 메서드 (개선 필요)")
                return False
        else:
            print("❌ update_chart_with_simulation_results 메서드 없음")
            return False
            
    except Exception as e:
        print(f"❌ IntegratedConditionManager 확인 실패: {e}")
        return False

if __name__ == "__main__":
    chart_test = test_mini_chart_integration()
    manager_test = test_integrated_condition_manager_update()
    
    if chart_test and manager_test:
        print(f"\n🚀 미니 차트 개선 로직 연동이 완료되었습니다!")
        print(f"🔧 이제 integrated_condition_manager.py에서 개선된 차트 시스템을 사용합니다.")
    else:
        print(f"\n🔧 미니 차트 개선 로직 연동에 문제가 있습니다. 수정이 필요합니다.")
        if not chart_test:
            print("  - SimulationResultWidget 관련 문제")
        if not manager_test:
            print("  - IntegratedConditionManager 관련 문제")
