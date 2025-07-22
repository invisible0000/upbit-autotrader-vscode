"""
전략 조합 탭 테스트 스크립트

새로 구현된 StrategyCombinationTab의 UI 및 기능을 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from PyQt6.QtWidgets import QApplication, QMainWindow
from upbit_auto_trading.ui.desktop.screens.strategy_management.components.strategy_combination_tab import StrategyCombinationTab

def test_combination_tab():
    """전략 조합 탭 테스트"""
    print("🧪 전략 조합 탭 UI 테스트 시작")
    
    app = QApplication(sys.argv)
    
    # 메인 윈도우 생성
    main_window = QMainWindow()
    main_window.setWindowTitle("🔗 전략 조합 탭 테스트")
    main_window.setGeometry(100, 100, 1200, 800)
    
    # 전략 조합 탭 생성
    combination_tab = StrategyCombinationTab()
    main_window.setCentralWidget(combination_tab)
    
    # 시그널 연결 테스트
    def on_combination_created(name):
        print(f"✅ 조합 생성됨: {name}")
    
    def on_backtest_requested(name):
        print(f"🧪 백테스트 요청됨: {name}")
    
    combination_tab.combination_created.connect(on_combination_created)
    combination_tab.backtest_requested.connect(on_backtest_requested)
    
    print("✅ UI 컴포넌트 초기화 완료")
    print("📋 2x2 그리드 레이아웃:")
    print("   ┌─────────────────┬─────────────────┐")
    print("   │ 전략 선택 영역    │ 조합 설정 영역    │")
    print("   ├─────────────────┼─────────────────┤") 
    print("   │ 미리보기 영역     │ 제어 영역        │")
    print("   └─────────────────┴─────────────────┘")
    print("\n💡 사용법:")
    print("1. 왼쪽 상단에서 전략을 선택하고 오른쪽 상단 드롭존에 드래그")
    print("2. 왼쪽 하단에서 조합 미리보기 확인")
    print("3. 오른쪽 하단에서 저장/백테스트 실행")
    
    # 윈도우 표시
    main_window.show()
    
    return app.exec()

if __name__ == "__main__":
    test_combination_tab()
