"""
통합 조건 관리 시스템 테스트 스크립트
"""

from PyQt6.QtWidgets import QApplication
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(__file__))

def test_integrated_manager():
    """통합 조건 관리자 테스트"""
    
    print("=== 통합 조건 관리 시스템 테스트 ===")
    
    # QApplication 생성
    app = QApplication(sys.argv)
    
    try:
        # 통합 조건 관리자 import 및 실행
        from integrated_condition_manager import IntegratedConditionManager
        
        print("✅ IntegratedConditionManager 로딩 성공")
        
        # 윈도우 생성
        window = IntegratedConditionManager()
        window.show()
        
        print("✅ 윈도우 표시 완료")
        print("📝 3x2 그리드 레이아웃으로 구성된 통합 관리 화면을 확인하세요!")
        
        # 이벤트 루프 시작
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integrated_manager()
