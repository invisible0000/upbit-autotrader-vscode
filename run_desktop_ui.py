"""
데스크톱 UI 실행 스크립트
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox

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
        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "애플리케이션 오류", f"오류가 발생했습니다. 'logs/gui_error.log' 파일을 확인해주세요.\n\n{error_message}")
    except ImportError:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = exception_handler
# --- 오류 로깅 기능 추가 끝 ---

if __name__ == "__main__":
    print("=== 데스크톱 UI 시작 ===")
    
    # 작업 디렉토리를 프로젝트 루트로 설정 (YAML 파일 경로 문제 해결)
    project_root = os.path.abspath(os.path.dirname(__file__))
    os.chdir(project_root)
    print(f"📁 작업 디렉토리 설정: {os.getcwd()}")
    
    # QApplication 생성
    print("QApplication 생성 중...")
    app = QApplication(sys.argv)
    print("QApplication 생성 완료")
    
    # 메인 윈도우 생성 및 실행
    try:
        print("MainWindow import 시도...")
        from upbit_auto_trading.ui.desktop.main_window import MainWindow
        print("MainWindow import 성공")
        
        print("MainWindow 인스턴스 생성 중...")
        main_window = MainWindow()
        print("MainWindow 인스턴스 생성 완료")
        
        print("윈도우 표시 중...")
        main_window.show()
        print("윈도우 표시 완료")
        
        print("이벤트 루프 시작...")
        # 애플리케이션 이벤트 루프 시작
        sys.exit(app.exec())
    except Exception as e:
        print(f"애플리케이션 시작 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)