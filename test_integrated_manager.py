#!/usr/bin/env python3
"""
통합 조건 관리자 테스트 스크립트
기능 구현 완료 후 테스트
"""

import sys
import os
from PyQt6.QtWidgets import QApplication

# 현재 디렉터리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from integrated_condition_manager import IntegratedConditionManager
    
    def test_integrated_manager():
        """통합 조건 관리자 기능 테스트"""
        print("🚀 통합 조건 관리 시스템 테스트 시작")
        print("📋 구현된 기능들:")
        print("   ✅ 검색 기능 (실시간 필터링)")
        print("   ✅ 트리거 편집 기능")
        print("   ✅ 트리거 삭제 기능 (확인 다이얼로그)")
        print("   ✅ 클립보드 복사 기능")
        print("   ✅ 실제 조건 기반 시뮬레이션")
        print("   ✅ 시나리오별 가상 데이터 생성")
        print("   ✅ 화면 비율 조정 (1:2:1)")
        print("")
        
        app = QApplication(sys.argv)
        
        try:
            # 통합 관리자 생성
            manager = IntegratedConditionManager()
            manager.show()
            
            print("✅ 통합 조건 관리 시스템 로드 완료")
            print("📋 레이아웃: 3x2 그리드 (비율 1:2:1)")
            print("   좌측(좁게): 조건 빌더")
            print("   중앙(넓게): 트리거 리스트 + 상세정보")
            print("   우측(좁게): 시뮬레이션 + 테스트결과")
            print("")
            print("🎮 테스트 방법:")
            print("   1. 좌측에서 조건을 생성/저장")
            print("   2. 중앙에서 트리거 검색/선택")
            print("   3. 우측에서 시나리오 시뮬레이션")
            print("   4. 편집/삭제/복사 기능 테스트")
            
            # 이벤트 루프 실행
            sys.exit(app.exec())
            
        except Exception as e:
            print(f"❌ 통합 관리자 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        test_integrated_manager()

except ImportError as e:
    print(f"❌ Import 실패: {e}")
    print("📁 현재 디렉터리:", current_dir)
    print("📋 필요한 파일들:")
    print("   - integrated_condition_manager.py")
    print("   - components/condition_dialog.py")
    print("   - components/condition_storage.py")
    print("   - components/condition_loader.py")
    
    # 파일 존재 확인
    required_files = [
        "integrated_condition_manager.py",
        "components/condition_dialog.py",
        "components/condition_storage.py",
        "components/condition_loader.py"
    ]
    
    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        status = "✅" if os.path.exists(full_path) else "❌"
        print(f"   {status} {file_path}")
