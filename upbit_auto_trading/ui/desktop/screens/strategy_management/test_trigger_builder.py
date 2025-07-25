"""
Trigger Builder Test
트리거 빌더 컴포넌트 테스트 스크립트
"""

import sys
import os

# 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QMainWindow
from trigger_builder.trigger_builder_screen import TriggerBuilderScreen


def test_trigger_builder():
    """트리거 빌더 테스트"""
    app = QApplication([])
    
    try:
        # 메인 윈도우 생성
        window = QMainWindow()
        window.setWindowTitle("트리거 빌더 테스트")
        window.setGeometry(100, 100, 1200, 800)
        
        # 트리거 빌더 스크린 생성
        trigger_screen = TriggerBuilderScreen()
        window.setCentralWidget(trigger_screen)
        
        # 윈도우 표시
        window.show()
        
        print("✅ 트리거 빌더 테스트 시작")
        print("   윈도우를 닫으면 테스트가 종료됩니다.")
        
        # 이벤트 루프 실행
        app.exec()
        
    except Exception as e:
        print(f"❌ 트리거 빌더 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_trigger_builder()
