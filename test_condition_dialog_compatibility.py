#!/usr/bin/env python3
"""
조건 다이얼로그 호환성 검증 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.core.condition_dialog import ConditionDialog

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 조건 다이얼로그 호환성 테스트")
        self.setGeometry(100, 100, 600, 500)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 레이아웃
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 조건 다이얼로그 추가
        try:
            self.condition_dialog = ConditionDialog()
            layout.addWidget(self.condition_dialog)
            
            # 시그널 연결
            self.condition_dialog.condition_saved.connect(self.on_condition_saved)
            
            print("✅ 조건 다이얼로그 로딩 성공!")
            
        except Exception as e:
            print(f"❌ 조건 다이얼로그 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def on_condition_saved(self, condition_data):
        print(f"📥 조건 저장됨: {condition_data}")

def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
