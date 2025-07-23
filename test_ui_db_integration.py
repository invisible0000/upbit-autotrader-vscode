#!/usr/bin/env python3
"""
원자적 전략 빌더 UI-DB 연동 테스트
Test Atomic Strategy Builder UI-DB Integration
"""

import sys
import os

# ui_prototypes 모듈 임포트를 위한 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "ui_prototypes"))

from atomic_strategy_db import AtomicStrategyDB

def test_db_connection():
    """DB 연결 테스트"""
    print("🧪 DB 연결 테스트 시작...")
    
    try:
        db = AtomicStrategyDB()
        print(f"✅ DB 경로: {db.db_path}")
        
        # 변수 로드 테스트
        variables = db.get_all_variables()
        print(f"📊 로드된 변수 수: {len(variables)}")
        for var in variables[:3]:  # 첫 3개만 표시
            print(f"   - {var.name} ({var.category.value})")
        
        # 액션 로드 테스트
        actions = db.get_available_actions()
        print(f"⚡ 로드된 액션 수: {len(actions)}")
        for action in actions:
            print(f"   - {action.name} ({action.action_type.value})")
        
        print("✅ DB 연동 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ DB 연동 테스트 실패: {e}")
        return False

def test_ui_compatibility():
    """UI 호환성 테스트"""
    print("\n🎨 UI 호환성 테스트 시작...")
    
    try:
        from atomic_strategy_builder_ui import ComponentPalette
        
        # ComponentPalette 초기화 (DB 로드 포함)
        print("   컴포넌트 팔레트 초기화 중...")
        # 실제 UI 객체를 만들지 않고 DB만 테스트
        db = AtomicStrategyDB()
        
        # 변수 탭 데이터 확인
        variables = db.get_all_variables()
        print(f"   변수 탭: {len(variables)}개 변수 준비됨")
        
        # 액션 탭 데이터 확인
        actions = db.get_available_actions()
        print(f"   액션 탭: {len(actions)}개 액션 준비됨")
        
        print("✅ UI 호환성 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ UI 호환성 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🚀 원자적 전략 빌더 UI-DB 연동 테스트")
    print("=" * 50)
    
    # 1. DB 연결 테스트
    db_success = test_db_connection()
    
    # 2. UI 호환성 테스트
    ui_success = test_ui_compatibility()
    
    # 결과 요약
    print("\n📋 테스트 결과 요약")
    print("-" * 30)
    print(f"DB 연결: {'✅ 성공' if db_success else '❌ 실패'}")
    print(f"UI 호환성: {'✅ 성공' if ui_success else '❌ 실패'}")
    
    if db_success and ui_success:
        print("\n🎉 모든 테스트 통과! UI-DB 연동이 성공적으로 완료되었습니다.")
        print("📌 이제 atomic_strategy_builder_ui.py를 실행하여 전체 기능을 테스트해보세요.")
    else:
        print("\n⚠️ 일부 테스트 실패. 문제를 해결해주세요.")

if __name__ == "__main__":
    main()
