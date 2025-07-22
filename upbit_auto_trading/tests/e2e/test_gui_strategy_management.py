#!/usr/bin/env python3
"""
전략 관리 시스템 테스트
"""

import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from upbit_auto_trading.ui.desktop.screens.strategy_management.strategy_management_screen import StrategyManagementScreen

def main():
    app = QApplication(sys.argv)
    
    # 전략 관리 화면 생성
    strategy_screen = StrategyManagementScreen()
    strategy_screen.resize(1200, 800)
    strategy_screen.show()
    
    print("🚀 전략 관리 시스템이 시작되었습니다!")
    print("📝 새 전략을 생성하거나 기존 전략을 선택하여 편집할 수 있습니다.")
    print("🔬 백테스팅 기능은 전략을 선택한 후 사용할 수 있습니다.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
