"""
데스크톱 UI 실행 스크립트
"""
import sys
import os
import traceback
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 디버그 로거 import
try:
    from upbit_auto_trading.utils.debug_logger import get_logger
    logger = get_logger("MainApp")
except ImportError:
    # 폴백: 기본 print 사용
    class FallbackLogger:
        def info(self, msg):
            print(f"ℹ️ [MainApp] {msg}")

        def success(self, msg):
            print(f"✅ [MainApp] {msg}")

        def error(self, msg):
            print(f"❌ [MainApp] {msg}")

        def debug(self, msg):
            if os.getenv('DEBUG_MODE', 'false').lower() == 'true':
                print(f"🔍 [MainApp] {msg}")
    
    logger = FallbackLogger()


# --- 오류 로깅 기능 추가 시작 ---
def exception_handler(exc_type, exc_value, exc_traceback):
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file_path = os.path.join(log_dir, "gui_error.log")
    with open(log_file_path, 'a', encoding='utf-8') as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n{'=' * 50}\n")
        f.write(f"오류 발생 시간: {now}\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    try:
        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "애플리케이션 오류", f"오류가 발생했습니다. 'logs/gui_error.log' 파일을 확인해주세요.\n\n{error_message}")
    except ImportError:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = exception_handler
# --- 오류 로깅 기능 추가 끝 ---

if __name__ == "__main__":
    logger.info("데스크톱 UI 시작")
    
    # 작업 디렉토리를 프로젝트 루트로 설정 (YAML 파일 경로 문제 해결)
    project_root = os.path.abspath(os.path.dirname(__file__))
    os.chdir(project_root)
    logger.debug(f"작업 디렉토리 설정: {os.getcwd()}")
    
    # QApplication 생성
    logger.debug("QApplication 생성 중...")
    app = QApplication(sys.argv)
    logger.debug("QApplication 생성 완료")
    
    # 메인 윈도우 생성 및 실행
    try:
        logger.debug("MainWindow import 시도...")
        from upbit_auto_trading.ui.desktop.main_window import MainWindow
        logger.debug("MainWindow import 성공")
        
        logger.debug("MainWindow 인스턴스 생성 중...")
        main_window = MainWindow()
        logger.debug("MainWindow 인스턴스 생성 완료")
        
        logger.success("애플리케이션 시작 완료")
        main_window.show()
        
        # 애플리케이션 이벤트 루프 시작
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"애플리케이션 시작 중 오류 발생: {e}")
        traceback.print_exc()
        sys.exit(1)