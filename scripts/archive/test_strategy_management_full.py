"""
전체 전략 관리 화면 테스트 스크립트

새로 구현된 전략 조합 탭이 포함된 전체 화면을 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from PyQt6.QtWidgets import QApplication, QMainWindow
from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import StrategyManagementScreen

def test_strategy_management_screen():
    """전략 관리 화면 전체 테스트"""
    print("🧪 전략 관리 화면 전체 테스트 시작")
    
    app = QApplication(sys.argv)
    
    # 메인 윈도우 생성
    main_window = QMainWindow()
    main_window.setWindowTitle("📊 매매 전략 관리 - 통합 테스트")
    main_window.setGeometry(100, 100, 1400, 900)
    
    # 전략 관리 화면 생성
    strategy_screen = StrategyManagementScreen()
    main_window.setCentralWidget(strategy_screen)
    
    # 시그널 연결 테스트
    def on_backtest_requested(target):
        print(f"🧪 백테스트 요청: {target}")
    
    strategy_screen.backtest_requested.connect(on_backtest_requested)
    
    print("✅ 3탭 화면 초기화 완료:")
    print("   📈 진입 전략 탭")
    print("   🛡️ 관리 전략 탭")
    print("   🔗 전략 조합 탭 (NEW!)")
    print("\n🎯 테스트 포인트:")
    print("1. 전략 조합 탭으로 이동")
    print("2. 드래그 앤 드롭으로 전략 조합 구성")
    print("3. 실시간 검증 및 미리보기 확인")
    print("4. 조합 저장 및 불러오기 테스트")
    print("5. 백테스트 연동 테스트")
    
    # 조합 탭으로 자동 전환
    strategy_screen.tab_widget.setCurrentIndex(2)
    
    # 윈도우 표시
    main_window.show()
    
    return app.exec()

if __name__ == "__main__":
    test_strategy_management_screen()
