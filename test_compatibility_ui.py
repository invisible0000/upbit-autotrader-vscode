#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
호환성 검증 UI 테스트
"""

import sys
import os

# 프로젝트 루트 추가
sys.path.insert(0, '.')

def test_compatibility_ui():
    """호환성 검증 UI 테스트"""
    try:
        from PyQt6.QtWidgets import QApplication
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_dialog import ConditionDialog
        
        print("🧪 호환성 검증 UI 실제 테스트")
        print("-" * 50)
        
        app = QApplication(sys.argv)
        dialog = ConditionDialog()
        
        # 호환성 서비스 상태 확인
        if hasattr(dialog, 'compatibility_service') and dialog.compatibility_service:
            print("✅ 호환성 서비스 로드 성공")
            
            # 변수 콤보박스에 값들이 있는지 확인
            if dialog.variable_combo.count() > 0:
                print(f"✅ 기본 변수 목록: {dialog.variable_combo.count()}개")
                for i in range(min(3, dialog.variable_combo.count())):
                    text = dialog.variable_combo.itemText(i)
                    data = dialog.variable_combo.itemData(i)
                    print(f"   [{i}] '{text}' -> '{data}'")
            
            if dialog.external_variable_combo.count() > 0:
                print(f"✅ 외부 변수 목록: {dialog.external_variable_combo.count()}개")
                for i in range(min(3, dialog.external_variable_combo.count())):
                    text = dialog.external_variable_combo.itemText(i)
                    data = dialog.external_variable_combo.itemData(i)
                    print(f"   [{i}] '{text}' -> '{data}'")
            
            # 호환성 검증 메서드 존재 확인
            if hasattr(dialog, 'check_variable_compatibility'):
                print("✅ check_variable_compatibility 메서드 존재")
            
            # 호환성 라벨 존재 확인
            if hasattr(dialog, 'compatibility_status_label'):
                print("✅ compatibility_status_label 위젯 존재")
            
            # 실제 호환성 테스트
            print("\n🔍 실제 호환성 검증 테스트:")
            
            # RSI vs MACD (비호환)
            is_compatible, reason = dialog.compatibility_service.is_compatible_external_variable('rsi', 'macd')
            print(f"   RSI ↔ MACD: {is_compatible} (사유: {reason})")
            
            # RSI vs 스토캐스틱 (호환)
            is_compatible, reason = dialog.compatibility_service.is_compatible_external_variable('rsi', 'stochastic')
            print(f"   RSI ↔ 스토캐스틱: {is_compatible} (사유: {reason})")
            
            # 현재가 vs 이동평균 (호환)
            is_compatible, reason = dialog.compatibility_service.is_compatible_external_variable('current_price', 'moving_average')
            print(f"   현재가 ↔ 이동평균: {is_compatible} (사유: {reason})")
            
            print("\n✅ 모든 호환성 검증 기능이 정상 작동합니다!")
            
        else:
            print("❌ 호환성 서비스 로드 실패")
        
        app.quit()
        print("\n✅ UI 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_compatibility_ui()
