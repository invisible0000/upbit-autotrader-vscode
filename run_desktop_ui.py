"""
데스크톱 UI 실행 스크립트
"""
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 메인 애플리케이션 실행
from upbit_auto_trading.ui.desktop.main import run_app

if __name__ == "__main__":
    run_app()