"""
데스크톱 UI 실행 스크립트
"""
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


# --- 오류 로깅 기능 추가 시작 ---
import traceback
from datetime import datetime

def exception_handler(exc_type, exc_value, exc_traceback):
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file_path = os.path.join(log_dir, "gui_error.log")
    with open(log_file_path, 'a', encoding='utf-8') as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'='*50}\n")
        f.write(f"오류 발생 시간: {now}\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    try:
        from PyQt6.QtWidgets import QMessageBox
        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "애플리케이션 오류", f"오류가 발생했습니다. 'logs/gui_error.log' 파일을 확인해주세요.\n\n{error_message}")
    except ImportError:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
sys.excepthook = exception_handler
# --- 오류 로깅 기능 추가 끝 ---

# 메인 애플리케이션 실행
from upbit_auto_trading.ui.desktop.main import run_app

if __name__ == "__main__":
    run_app()