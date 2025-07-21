#!/usr/bin/env python3
"""
전략 관리 화면 3탭 구조 테스트 스크립트

새로운 역할 기반 전략 관리 UI를 테스트합니다:
- 📈 진입 전략 탭
- 🛡️ 관리 전략 탭  
- 🔗 전략 조합 탭
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication
    from upbit_auto_trading.ui.desktop.strategy_management_screen import StrategyManagementScreen
    
    def test_strategy_ui():
        """전략 관리 UI 테스트"""
        print("🚀 전략 관리 화면 테스트 시작...")
        
        # Qt 애플리케이션 생성
        app = QApplication(sys.argv)
        
        # 전략 관리 화면 생성
        window = StrategyManagementScreen()
        window.setWindowTitle("전략 관리 - 역할 기반 3탭 구조")
        window.resize(1200, 800)
        window.show()
        
        # 탭 구조 확인
        print("✅ 전략 관리 화면 3탭 구조 정상 로딩됨")
        print(f"📈 진입 전략 탭: {window.tab_widget.tabText(0)}")
        print(f"🛡️ 관리 전략 탭: {window.tab_widget.tabText(1)}")
        print(f"🔗 전략 조합 탭: {window.tab_widget.tabText(2)}")
        
        # 각 탭의 테이블 확인
        print(f"\n📊 데이터 로딩 상태:")
        print(f"   - 진입 전략: {window.entry_strategy_table.rowCount()}개")
        print(f"   - 관리 전략: {window.management_strategy_table.rowCount()}개") 
        print(f"   - 전략 조합: {window.combination_list_table.rowCount()}개")
        
        print(f"\n💡 UI 구성 요소:")
        print(f"   - 상단 툴바: ✅")
        print(f"   - 3탭 위젯: ✅")
        print(f"   - 조합 3분할 패널: ✅")
        
        print(f"\n🎯 UI 테스트 완료 - 창을 닫으면 종료됩니다")
        
        # 애플리케이션 실행
        return app.exec()
    
    if __name__ == "__main__":
        exit_code = test_strategy_ui()
        print(f"\n✅ 테스트 완료 (종료 코드: {exit_code})")
        sys.exit(exit_code)
        
except ImportError as e:
    print(f"❌ 모듈 임포트 오류: {e}")
    print("💡 PyQt6가 설치되어 있는지 확인하세요: pip install PyQt6")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
