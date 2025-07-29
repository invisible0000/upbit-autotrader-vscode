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
    # 폴백: 환경변수 제어되는 print 사용
    class FallbackLogger:
        def _should_log(self, level="info"):
            """환경변수 기반 로그 제어"""
            debug_mode = os.getenv('UPBIT_DEBUG_MODE', 'true').lower() == 'true'
            env_mode = os.getenv('UPBIT_ENV', 'development').lower()
            
            # 프로덕션에서는 error만 허용
            if env_mode == 'production':
                return level in ['error']
            
            # 디버그 비활성화 시 debug 레벨 숨김
            if not debug_mode and level == 'debug':
                return False
            
            return True

        def info(self, msg):
            if self._should_log('info'):
                print(f"ℹ️ [MainApp] {msg}")

        def success(self, msg):
            if self._should_log('success'):
                print(f"✅ [MainApp] {msg}")

        def error(self, msg):
            if self._should_log('error'):
                print(f"❌ [MainApp] {msg}")

        def debug(self, msg):
            if self._should_log('debug'):
                print(f"🔍 [MainApp] {msg}")
    
    logger = FallbackLogger()


# --- 오류 로깅 기능 추가 시작 ---
def exception_handler(exc_type, exc_value, exc_traceback):
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file_path = os.path.join(log_dir, "gui_error.log")
    
    # 에러 정보 생성
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_content = []
    error_content.append(f"{'=' * 50}")
    error_content.append(f"오류 발생 시간: {now}")
    
    # traceback을 문자열로 수집
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    error_content.extend(tb_lines)
    error_content.append("")  # 빈 줄 추가
    
    # 새 에러 + 기존 내용 (역순 삽입)
    new_error_text = "\n".join(error_content)
    
    try:
        # 기존 내용 읽기 (파일이 있다면)
        existing_content = ""
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # 새 에러를 맨 위에 + 기존 내용 (역순 로깅)
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(new_error_text)
            if existing_content:
                f.write(existing_content)
    except Exception as e:
        # 로그 쓰기 실패 시 기본 append 방식으로 폴백
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(new_error_text)
    
    try:
        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "애플리케이션 오류", f"오류가 발생했습니다. 'logs/gui_error.log' 파일을 확인해주세요.\n\n{error_message}")
    except ImportError:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = exception_handler
# --- 오류 로깅 기능 추가 끝 ---

if __name__ == "__main__":
    # 작업 디렉토리를 프로젝트 루트로 설정
    project_root = os.path.abspath(os.path.dirname(__file__))
    os.chdir(project_root)
    
    # QApplication 생성
    app = QApplication(sys.argv)
    
    # 메인 윈도우 생성 및 실행
    try:
        from upbit_auto_trading.ui.desktop.main_window import MainWindow
        main_window = MainWindow()
        main_window.show()
        logger.success("애플리케이션 시작됨")
        
        # 애플리케이션 이벤트 루프 시작
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"애플리케이션 시작 실패: {e}")
        traceback.print_exc()
        sys.exit(1)