"""
메인 애플리케이션 모듈
"""
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(__file__)  # desktop 폴더
ui_dir = os.path.dirname(current_dir)    # ui 폴더
upbit_auto_trading_dir = os.path.dirname(ui_dir)  # upbit_auto_trading 폴더
project_root = os.path.dirname(upbit_auto_trading_dir)  # 프로젝트 루트

sys.path.insert(0, project_root)

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