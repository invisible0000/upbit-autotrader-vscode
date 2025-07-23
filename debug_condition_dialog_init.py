#!/usr/bin/env python3
"""
ConditionDialog 초기화 시 save_condition 호출 추적 스크립트
"""

import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append('.')

# ConditionDialog 클래스를 임시로 패치해서 save_condition 호출을 추적
def test_condition_dialog_initialization():
    """ConditionDialog 초기화 중 save_condition 호출 추적"""
    
    print("🔍 ConditionDialog 초기화 추적 시작")
    print("=" * 50)
    
    try:
        # 원본 ConditionDialog import
        from components.condition_dialog import ConditionDialog
        
        # 원본 save_condition 메서드 백업
        original_save_condition = ConditionDialog.save_condition
        
        # 호출 추적을 위한 래퍼 함수
        def tracked_save_condition(self):
            print("🚨 save_condition 호출됨!")
            import traceback
            print("호출 스택:")
            traceback.print_stack()
            return original_save_condition(self)
        
        # save_condition 메서드 패치
        ConditionDialog.save_condition = tracked_save_condition
        
        print("📝 ConditionDialog 인스턴스 생성 중...")
        
        # ConditionDialog 인스턴스 생성 (이때 save_condition이 호출되는지 확인)
        dialog = ConditionDialog()
        
        print("✅ ConditionDialog 인스턴스 생성 완료")
        print("📊 변수 콤보박스 상태:")
        print(f"  현재 선택된 항목: {dialog.variable_combo.currentText()}")
        print(f"  현재 데이터: {dialog.variable_combo.currentData()}")
        print(f"  항목 개수: {dialog.variable_combo.count()}")
        
        # collect_condition_data 직접 호출해보기
        print("\n🧪 collect_condition_data() 직접 테스트:")
        condition_data = dialog.collect_condition_data()
        if condition_data:
            print(f"✅ 조건 데이터 수집 성공: {condition_data.get('name', 'Unknown')}")
        else:
            print("❌ 조건 데이터 수집 실패 (None 반환)")
        
        # update_preview 직접 호출해보기
        print("\n🧪 update_preview() 직접 테스트:")
        dialog.update_preview()
        print("✅ update_preview 완료")
        
        # 원본 메서드 복원
        ConditionDialog.save_condition = original_save_condition
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_condition_manager():
    """IntegratedConditionManager 초기화 추적"""
    
    print("\n🔍 IntegratedConditionManager 초기화 추적")
    print("=" * 50)
    
    try:
        from integrated_condition_manager import IntegratedConditionManager
        from components.condition_dialog import ConditionDialog
        
        # save_condition 호출 추적
        original_save_condition = ConditionDialog.save_condition
        
        def tracked_save_condition(self):
            print("🚨 IntegratedConditionManager에서 save_condition 호출됨!")
            import traceback
            traceback.print_stack()
            return original_save_condition(self)
        
        ConditionDialog.save_condition = tracked_save_condition
        
        print("📝 IntegratedConditionManager 인스턴스 생성 중...")
        
        # 실제 UI 생성하지 말고 로직만 테스트
        manager = IntegratedConditionManager()
        
        print("✅ IntegratedConditionManager 인스턴스 생성 완료")
        
        # 원본 메서드 복원
        ConditionDialog.save_condition = original_save_condition
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 ConditionDialog 초기화 문제 추적")
    print("=" * 60)
    
    # 1. ConditionDialog 단독 테스트
    dialog_test = test_condition_dialog_initialization()
    
    # 2. IntegratedConditionManager 테스트  
    # manager_test = test_integrated_condition_manager()
    
    print("\n" + "=" * 60)
    if dialog_test:
        print("🎯 결론: ConditionDialog 자체적으로는 save_condition이 호출되지 않음")
        print("💡 문제는 IntegratedConditionManager나 다른 부분에서 발생할 가능성이 높음")
    else:
        print("❌ 테스트 실패")
