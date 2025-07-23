#!/usr/bin/env python3
"""
통합 조건 관리자 차트 기능 데모
"""

import sys
import os
sys.path.append('.')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from upbit_auto_trading.ui.desktop.screens.strategy_management.integrated_condition_manager import IntegratedConditionManager

class ChartDemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 통합 조건 관리자 - 차트 기능 데모")
        self.setGeometry(100, 100, 1400, 900)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 통합 조건 관리자 임베드
        self.condition_manager = IntegratedConditionManager()
        layout.addWidget(self.condition_manager)
        
        print("✅ 차트 데모 창 초기화 완료")

def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    
    # 데모 창 생성
    window = ChartDemoWindow()
    window.show()
    
    print("📊 차트 기능 데모를 시작합니다!")
    print("1. 트리거를 선택하세요")
    print("2. 우측 상단의 시뮬레이션 버튼을 클릭하세요")
    print("3. 우측 하단의 차트에서 결과를 확인하세요")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
