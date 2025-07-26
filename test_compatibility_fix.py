#!/usr/bin/env python3
"""
호환성 검증 시스템 테스트
TASK-20250727-12: Step 2.1 호환성 검증 오류 수정 테스트
"""

import sys
import os

# 경로 설정
project_root = os.path.dirname(os.path.abspath(__file__))
trigger_builder_path = os.path.join(project_root, 'upbit_auto_trading', 'ui', 'desktop', 'screens', 'strategy_management', 'trigger_builder', 'components')
sys.path.insert(0, trigger_builder_path)

def test_compatibility_validation():
    """새로운 호환성 검증 시스템 테스트"""
    print("🧪 호환성 검증 시스템 테스트 시작")
    print("=" * 50)
    
    try:
        from compatibility_validator import check_compatibility
        print("✅ 새로운 호환성 검증기 임포트 성공")
        
        # 테스트 케이스들
        test_cases = [
            ('SMA', 'EMA'),           # trend ↔ trend (호환 예상)
            ('SMA', 'CURRENT_PRICE'), # trend ↔ price (호환 예상)
            ('RSI', 'STOCHASTIC'),    # oscillator ↔ oscillator (호환 예상)
            ('RSI', 'SMA'),           # oscillator ↔ trend (비호환 예상)
            ('CURRENT_PRICE', 'VOLUME'), # price ↔ volume (비호환 예상)
        ]
        
        print("\n🔍 호환성 검증 테스트:")
        for var1, var2 in test_cases:
            try:
                is_compatible, reason = check_compatibility(var1, var2)
                status = "✅ 호환" if is_compatible else "❌ 비호환"
                print(f"  {status} | {var1} ↔ {var2}: {reason}")
            except Exception as e:
                print(f"  ⚠️ 오류 | {var1} ↔ {var2}: {e}")
        
        print(f"\n🎯 핵심 테스트: SMA ↔ EMA 호환성")
        is_compatible, reason = check_compatibility('SMA', 'EMA')
        if is_compatible:
            print(f"✅ SUCCESS: SMA와 EMA가 호환됩니다! ({reason})")
            return True
        else:
            print(f"❌ FAIL: SMA와 EMA가 호환되지 않습니다. ({reason})")
            return False
            
    except ImportError as e:
        print(f"❌ 호환성 검증기 임포트 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_compatibility_validation()
    if success:
        print(f"\n🚀 호환성 검증 시스템이 정상 작동합니다!")
        print(f"🔧 이제 condition_dialog.py에서 새 시스템을 사용할 수 있습니다.")
    else:
        print(f"\n🔧 호환성 검증 시스템에 문제가 있습니다. 수정이 필요합니다.")
