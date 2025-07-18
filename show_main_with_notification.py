"""
메인 윈도우와 알림 센터 샘플 GUI 화면 출력 스크립트
"""
import sys
from PyQt6.QtWidgets import QApplication
from upbit_auto_trading.ui.desktop.main_window import MainWindow
from upbit_auto_trading.ui.desktop.models.notification import Notification, NotificationType
from datetime import datetime, timedelta

def main():
    """메인 함수"""
    # QApplication 인스턴스 생성
    app = QApplication(sys.argv)
    
    # 메인 윈도우 인스턴스 생성
    main_window = MainWindow()
    
    # 알림 센터로 화면 전환
    main_window._change_screen("monitoring")
    
    # 메인 윈도우 표시
    main_window.show()
    
    # 애플리케이션 실행
    sys.exit(app.exec())

if __name__ == "__main__":
    main()