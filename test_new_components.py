"""
새로운 컴포넌트 시스템 임포트 테스트
"""
import sys
import os

# 현재 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_trigger_imports():
    """트리거 컴포넌트 임포트 테스트"""
    try:
        from upbit_auto_trading.component_system.triggers import (
            PriceChangeTrigger, PriceChangeConfig,
            TRIGGER_CLASSES, get_trigger_class
        )
        print("✅ 트리거 컴포넌트 기본 임포트 성공")
        
        # 전체 트리거 목록 확인
        print(f"사용 가능한 트리거: {list(TRIGGER_CLASSES.keys())}")
        return True
    except Exception as e:
        print(f"❌ 트리거 컴포넌트 임포트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_base_imports():
    """기본 컴포넌트 임포트 테스트"""
    try:
        from upbit_auto_trading.component_system.base import (
            ComponentBase, TriggerComponent, ComponentResult, ExecutionContext
        )
        print("✅ 기본 컴포넌트 임포트 성공")
        return True
    except Exception as e:
        print(f"❌ 기본 컴포넌트 임포트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """테스트 실행"""
    print("🔍 새로운 컴포넌트 시스템 테스트 시작\n")
    
    tests = [
        test_base_imports,
        test_trigger_imports,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 결과: {passed}/{len(tests)} 통과")


if __name__ == "__main__":
    main()
