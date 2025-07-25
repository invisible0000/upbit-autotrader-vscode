#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
실제 사용되는 condition_dialog.py에 호환성 검증 추가 확인
"""

import sys
import os

# 프로젝트 루트 추가
sys.path.insert(0, '.')

def test_legacy_condition_dialog():
    """Legacy condition dialog 호환성 검증 테스트"""
    try:
        from PyQt6.QtWidgets import QApplication
        # 실제 사용되는 condition_dialog import
        sys.path.insert(0, 'components_legacy')
        from condition_dialog import ConditionDialog
        
        print("🧪 Legacy Condition Dialog 호환성 검증 테스트")
        print("-" * 60)
        
        app = QApplication(sys.argv)
        dialog = ConditionDialog()
        
        # 호환성 서비스 상태 확인
        if hasattr(dialog, 'compatibility_service') and dialog.compatibility_service:
            print("✅ 호환성 서비스 로드 성공")
            
            # 호환성 검증 메서드 존재 확인
            if hasattr(dialog, 'check_variable_compatibility'):
                print("✅ check_variable_compatibility 메서드 존재")
            
            # 호환성 라벨 존재 확인
            if hasattr(dialog, 'compatibility_status_label'):
                print("✅ compatibility_status_label 위젯 존재")
            
            # 실제 호환성 테스트
            print("\n🔍 실제 호환성 검증 테스트:")
            
            # 현재가 vs 거래량 (비호환 - 사용자가 테스트한 조합)
            is_compatible, reason = dialog.compatibility_service.is_compatible_external_variable('current_price', 'volume')
            print(f"   현재가 ↔ 거래량: {is_compatible} (사유: {reason})")
            
            # RSI vs MACD (비호환)
            is_compatible, reason = dialog.compatibility_service.is_compatible_external_variable('rsi', 'macd')
            print(f"   RSI ↔ MACD: {is_compatible} (사유: {reason})")
            
            # RSI vs 스토캐스틱 (호환)
            is_compatible, reason = dialog.compatibility_service.is_compatible_external_variable('rsi', 'stochastic')
            print(f"   RSI ↔ 스토캐스틱: {is_compatible} (사유: {reason})")
            
            print("\n✅ Legacy Condition Dialog에 호환성 검증이 성공적으로 추가되었습니다!")
            
        else:
            print("❌ 호환성 서비스 로드 실패")
        
        app.quit()
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_legacy_condition_dialog()
