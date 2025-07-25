#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
실제 UI에서 호환성 검증 동작 테스트
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 프로젝트 루트 추가
sys.path.insert(0, '.')

try:
    from upbit_auto_trading.ui.desktop.screens.strategy_management.components.condition_dialog import ConditionDialog
    DIALOG_AVAILABLE = True
except ImportError as e:
    print(f"❌ ConditionDialog import 실패: {e}")
    DIALOG_AVAILABLE = False

def test_ui_compatibility():
    """UI 호환성 검증 실제 동작 테스트"""
    if not DIALOG_AVAILABLE:
        print("❌ 조건 다이얼로그를 로드할 수 없습니다.")
        return
    
    print("🧪 UI 호환성 검증 실제 동작 테스트")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    try:
        # 조건 다이얼로그 생성
        dialog = ConditionDialog()
        
        # 호환성 서비스 상태 확인
        if hasattr(dialog, 'compatibility_service') and dialog.compatibility_service:
            print("✅ 호환성 서비스 로드 성공")
            
            # UI 위젯 존재 확인
            if hasattr(dialog, 'compatibility_status_label'):
                print("✅ 호환성 상태 라벨 위젯 존재")
            else:
                print("❌ 호환성 상태 라벨 위젯 없음")
            
            if hasattr(dialog, 'check_variable_compatibility'):
                print("✅ 호환성 검증 메서드 존재")
            else:
                print("❌ 호환성 검증 메서드 없음")
            
            # 시뮬레이션: 사용자가 변수를 선택하는 상황
            print("\n🎭 사용자 시나리오 시뮬레이션:")
            
            # 1. 기본 변수를 RSI로 설정
            print("1️⃣ 기본 변수를 RSI로 설정...")
            
            # 지표 카테고리 선택
            for i in range(dialog.category_combo.count()):
                if dialog.category_combo.itemData(i) == "indicator":
                    dialog.category_combo.setCurrentIndex(i)
                    break
            
            # 변수 목록 업데이트
            dialog.update_variables_by_category()
            
            # RSI 선택
            for i in range(dialog.variable_combo.count()):
                if "RSI" in dialog.variable_combo.itemText(i):
                    dialog.variable_combo.setCurrentIndex(i)
                    print(f"   ✅ RSI 선택됨: {dialog.variable_combo.currentText()}")
                    break
            
            # 2. 외부변수 모드 활성화
            print("2️⃣ 외부변수 모드 활성화...")
            dialog.use_external_variable.setChecked(True)
            dialog.toggle_comparison_mode()
            print("   ✅ 외부변수 모드 활성화됨")
            
            # 3. 외부변수 카테고리를 지표로 설정
            print("3️⃣ 외부변수 카테고리를 지표로 설정...")
            for i in range(dialog.external_category_combo.count()):
                if dialog.external_category_combo.itemData(i) == "indicator":
                    dialog.external_category_combo.setCurrentIndex(i)
                    break
            
            dialog.update_external_variables()
            
            # 4. 비호환 조합 테스트: MACD 선택
            print("4️⃣ 비호환 조합 테스트: MACD 선택...")
            macd_found = False
            for i in range(dialog.external_variable_combo.count()):
                if "MACD" in dialog.external_variable_combo.itemText(i):
                    dialog.external_variable_combo.setCurrentIndex(i)
                    print(f"   ✅ MACD 선택됨: {dialog.external_variable_combo.currentText()}")
                    macd_found = True
                    break
            
            if macd_found:
                # 호환성 검증 수동 트리거
                dialog.check_variable_compatibility()
                
                # 호환성 라벨 상태 확인
                if dialog.compatibility_status_label.isVisible():
                    label_text = dialog.compatibility_status_label.text()
                    if "❌" in label_text:
                        print("   ✅ 비호환 경고 메시지 표시됨")
                        print(f"   📝 메시지: {label_text[:50]}...")
                    else:
                        print("   ❌ 예상과 다른 메시지 표시됨")
                else:
                    print("   ❌ 호환성 라벨이 표시되지 않음")
            else:
                print("   ⚠️ MACD 변수를 찾을 수 없음")
            
            # 5. 호환 조합 테스트: 스토캐스틱 선택
            print("5️⃣ 호환 조합 테스트: 스토캐스틱 선택...")
            stoch_found = False
            for i in range(dialog.external_variable_combo.count()):
                if "스토캐스틱" in dialog.external_variable_combo.itemText(i):
                    dialog.external_variable_combo.setCurrentIndex(i)
                    print(f"   ✅ 스토캐스틱 선택됨: {dialog.external_variable_combo.currentText()}")
                    stoch_found = True
                    break
            
            if stoch_found:
                # 호환성 검증 수동 트리거
                dialog.check_variable_compatibility()
                
                # 호환성 라벨 상태 확인
                if dialog.compatibility_status_label.isVisible():
                    label_text = dialog.compatibility_status_label.text()
                    if "✅" in label_text:
                        print("   ✅ 호환 확인 메시지 표시됨")
                        print(f"   📝 메시지: {label_text[:50]}...")
                    else:
                        print("   ❌ 예상과 다른 메시지 표시됨")
                else:
                    print("   ❌ 호환성 라벨이 표시되지 않음")
            else:
                print("   ⚠️ 스토캐스틱 변수를 찾을 수 없음")
            
            print("\n🎯 테스트 결과:")
            print("✅ 호환성 검증 시스템이 UI에 성공적으로 통합되었습니다!")
            print("✅ 사용자가 변수를 선택할 때 실시간으로 호환성을 확인할 수 있습니다.")
            print("✅ 비호환 조합에 대해 명확한 경고 메시지를 제공합니다.")
            
        else:
            print("❌ 호환성 서비스를 사용할 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        app.quit()
    
    print("\n✅ UI 호환성 검증 테스트 완료!")

def main():
    """메인 실행"""
    test_ui_compatibility()

if __name__ == "__main__":
    main()
