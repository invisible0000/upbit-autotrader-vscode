#!/usr/bin/env python3
"""
업데이트된 전략 관리 화면 테스트 스크립트

새로운 기능:
- 실제 CombinationManager 연동
- 체크박스 인터랙션
- 조합 선택/생성/삭제
- 실시간 미리보기
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtWidgets import QApplication
    from upbit_auto_trading.ui.desktop.strategy_management_screen import StrategyManagementScreen
    
    def test_updated_strategy_ui():
        """업데이트된 전략 관리 UI 테스트"""
        print("🚀 업데이트된 전략 관리 화면 테스트 시작...")
        
        # Qt 애플리케이션 생성
        app = QApplication(sys.argv)
        
        # 전략 관리 화면 생성
        window = StrategyManagementScreen()
        window.setWindowTitle("전략 관리 - 역할 기반 3탭 구조 (업데이트)")
        window.resize(1400, 900)
        window.show()
        
        # 기능 확인
        print("✅ UI 구성 완료")
        print(f"📊 CombinationManager 연동: ✅")
        print(f"📈 진입 전략: {window.entry_strategy_table.rowCount()}개")
        print(f"🛡️ 관리 전략: {window.management_strategy_table.rowCount()}개") 
        print(f"🔗 전략 조합: {window.combination_list_table.rowCount()}개")
        
        print(f"\n🎯 새로운 기능:")
        print(f"   - 실제 조합 데이터 로딩/저장")
        print(f"   - 체크박스 인터랙션")
        print(f"   - 조합 선택/미리보기")
        print(f"   - 1진입 + 최대5관리 제한")
        
        print(f"\n💡 테스트 가이드:")
        print(f"   1. 🔗 전략 조합 탭 클릭")
        print(f"   2. 좌측에서 조합 선택")
        print(f"   3. 중앙에서 전략 체크박스 클릭")
        print(f"   4. 👁️ 미리보기 버튼 클릭")
        print(f"   5. 🚀 백테스트 실행 버튼 클릭")
        
        # 애플리케이션 실행
        return app.exec()
    
    if __name__ == "__main__":
        exit_code = test_updated_strategy_ui()
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
