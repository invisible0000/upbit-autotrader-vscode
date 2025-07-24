#!/usr/bin/env python3
"""
전략 메이커 UI 실행 테스트
"""

import sys
from PyQt6.QtWidgets import QApplication

def test_strategy_maker_ui():
    """전략 메이커 UI 테스트"""
    app = QApplication(sys.argv)
    
    try:
        # 전략 메이커 단독 실행
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.strategy_maker import StrategyMaker
        
        print("🎯 전략 메이커 UI 생성 중...")
        strategy_maker = StrategyMaker()
        strategy_maker.setWindowTitle("전략 메이커 테스트")
        strategy_maker.resize(1400, 900)
        strategy_maker.show()
        
        print("✅ 전략 메이커 UI 생성 완료!")
        print("💡 창을 닫으면 테스트가 종료됩니다.")
        
        # 이벤트 루프 시작
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ UI 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def test_integrated_strategy_screen():
    """통합 전략 관리 화면 테스트"""
    app = QApplication(sys.argv)
    
    try:
        # 전체 전략 관리 화면 실행
        from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import StrategyManagementScreen
        
        print("🎯 통합 전략 관리 화면 생성 중...")
        strategy_screen = StrategyManagementScreen()
        strategy_screen.setWindowTitle("통합 전략 관리 테스트")
        strategy_screen.resize(1600, 1000)
        strategy_screen.show()
        
        # 전략 메이커 탭으로 이동
        strategy_screen.tab_widget.setCurrentIndex(1)  # 전략 메이커 탭
        
        print("✅ 통합 전략 관리 화면 생성 완료!")
        print("💡 창을 닫으면 테스트가 종료됩니다.")
        
        # 이벤트 루프 시작
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 통합 화면 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--integrated":
        print("🚀 통합 전략 관리 화면 테스트 시작")
        test_integrated_strategy_screen()
    else:
        print("🚀 전략 메이커 단독 UI 테스트 시작")
        print("💡 통합 화면 테스트: python test_strategy_maker_ui.py --integrated")
        test_strategy_maker_ui()
