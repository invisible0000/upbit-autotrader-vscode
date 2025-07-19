#!/usr/bin/env python3
"""
트레이딩뷰 스타일 차트 뷰 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen

def main():
    app = QApplication(sys.argv)
    
    # 차트 뷰 생성
    window = ChartViewScreen()
    window.setWindowTitle("Upbit AutoTrader - 차트 뷰 (트레이딩뷰 스타일)")
    window.resize(1400, 800)
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    main()
