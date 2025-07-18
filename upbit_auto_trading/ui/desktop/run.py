"""
애플리케이션 실행 모듈

이 모듈은 업비트 자동매매 시스템의 UI를 실행하는 진입점을 제공합니다.
"""

import sys
from upbit_auto_trading.ui.desktop.app import Application
from upbit_auto_trading.ui.desktop.main_window import MainWindow
from upbit_auto_trading.ui.desktop.utils.logging_manager import LoggingManager


def main():
    """
    메인 함수
    
    애플리케이션을 초기화하고 메인 윈도우를 생성한 후 실행합니다.
    """
    logger = LoggingManager().get_logger("main")
    logger.info("업비트 자동매매 시스템 시작")
    
    try:
        # 애플리케이션 초기화
        app = Application()
        app.initialize()
        
        # 메인 윈도우 생성 및 표시
        logger.info("메인 윈도우 생성")
        main_window = MainWindow()
        main_window.show()
        
        # 애플리케이션 실행
        logger.info("애플리케이션 실행")
        exit_code = app.run()
        
        logger.info(f"애플리케이션 종료 (코드: {exit_code})")
        return exit_code
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())