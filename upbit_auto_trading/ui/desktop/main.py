"""
메인 애플리케이션 모듈
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from upbit_auto_trading.ui.desktop.main_window import MainWindow


def run_app():
    """애플리케이션 실행"""
    # 애플리케이션 인스턴스 생성
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("업비트 자동매매 시스템")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("UpbitAutoTrading")
    
    # 메인 윈도우 생성 및 표시
    main_window = MainWindow()
    main_window.show()
    
    # 애플리케이션 실행
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()