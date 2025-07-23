#!/usr/bin/env python3
"""
새로운 전략 관리 화면 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PyQt6.QtWidgets import QApplication
from upbit_auto_trading.ui.desktop.screens.strategy_management.new_strategy_management_screen import NewStrategyManagementScreen

def test_new_strategy_management():
    """새 전략 관리 화면 테스트"""
    print("🚀 새로운 전략 관리 화면 테스트 시작")
    
    app = QApplication(sys.argv)
    
    try:
        # 새 전략 관리 화면 생성
        window = NewStrategyManagementScreen()
        
        # 시그널 연결 테스트
        window.strategy_saved.connect(lambda data: print(f"📊 전략 저장됨: {data.get('name', 'Unknown')}"))
        
        # 화면 표시
        window.show()
        
        print("✅ 새 전략 관리 화면 테스트 성공!")
        print("🎯 조건 빌더 탭에서 조건을 생성해보세요!")
        
        # 이벤트 루프 실행
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 새 전략 관리 화면 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_strategy_management()
