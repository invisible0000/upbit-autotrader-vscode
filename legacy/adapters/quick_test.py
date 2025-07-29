"""
Phase 4 어댑터 검증 스크립트
"""

def test_adapter_import():
    """어댑터 import 테스트"""
    try:
        # 상대 경로로 어댑터 import 시도
        from mini_simulation_adapter import get_trigger_builder_adapter
        print("✅ 어댑터 import 성공")
        
        # 어댑터 인스턴스 생성
        adapter = get_trigger_builder_adapter()
        print("✅ 어댑터 인스턴스 생성 성공")
        
        # 기본 정보 확인
        info = adapter.get_adapter_info()
        print(f"📊 어댑터 정보:")
        print(f"   - 공통 시스템 사용: {info['using_common_system']}")
        print(f"   - 사용 가능한 소스: {info['available_sources']}")
        print(f"   - 버전: {info['adapter_version']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 어댑터 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Phase 4 어댑터 검증 시작")
    success = test_adapter_import()
    print(f"🎯 결과: {'성공' if success else '실패'}")
