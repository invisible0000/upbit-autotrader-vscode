"""
차트 뷰 테스트 스크립트

이 스크립트는 차트 뷰 화면을 독립적으로 테스트합니다.
"""

import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication

# 예외 처리 함수 정의
def exception_handler(exc_type, exc_value, exc_traceback):
    """예외 처리 함수"""
    # 에러 로그 파일에 예외 정보 기록
    with open('chart_view_error.log', 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*50}\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    
    # 기본 예외 처리기도 호출
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

# 예외 처리 함수 설정
sys.excepthook = exception_handler

# 현재 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    # 차트 뷰 화면 임포트
    from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
    
    def main():
        """메인 함수"""
        # QApplication 인스턴스 생성
        app = QApplication(sys.argv)
        
        # 차트 뷰 화면 생성
        chart_view = ChartViewScreen()
        
        # 화면 표시
        chart_view.show()
        
        # 애플리케이션 실행
        sys.exit(app.exec())
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"모듈 임포트 오류: {e}")
    with open('chart_view_error.log', 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"모듈 임포트 오류: {e}\n")
        traceback.print_exc(file=f)
    sys.exit(1)
except Exception as e:
    print(f"예기치 않은 오류: {e}")
    with open('chart_view_error.log', 'a', encoding='utf-8') as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"예기치 않은 오류: {e}\n")
        traceback.print_exc(file=f)
    sys.exit(1)