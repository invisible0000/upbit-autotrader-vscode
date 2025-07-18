"""
통합 UI 테스트 모듈

이 모듈은 모든 UI 화면을 통합하여 테스트하는 환경을 제공합니다.
- 메인 윈도우
- 대시보드
- 차트 뷰
- 설정 화면
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication

# 메인 윈도우 임포트
from upbit_auto_trading.ui.desktop.main_window import MainWindow


class AppConfig:
    """애플리케이션 설정 관리 클래스"""
    
    APP_NAME = "업비트 자동매매 시스템 - 통합 UI 테스트"
    APP_VERSION = "1.0.0"
    ORGANIZATION_NAME = "UpbitAutoTrading"
    MIN_WIDTH = 1280
    MIN_HEIGHT = 720
    
    @classmethod
    def apply_to_app(cls, app):
        """
        애플리케이션에 설정 적용
        
        Args:
            app (QApplication): 애플리케이션 인스턴스
        """
        app.setApplicationName(cls.APP_NAME)
        app.setApplicationVersion(cls.APP_VERSION)
        app.setOrganizationName(cls.ORGANIZATION_NAME)


def setup_logging():
    """
    로깅 설정
    
    Returns:
        logging.Logger: 로거 인스턴스
    """
    logger = logging.getLogger("upbit_auto_trading")
    logger.setLevel(logging.DEBUG)
    
    # 이미 핸들러가 설정되어 있으면 추가하지 않음
    if logger.hasHandlers():
        return logger
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    
    # 파일 핸들러
    file_handler = logging.FileHandler("upbit_auto_trading_ui.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger


def create_application():
    """
    애플리케이션 인스턴스 생성 및 설정
    
    Returns:
        QApplication: 생성된 애플리케이션 인스턴스
    """
    app = QApplication(sys.argv)
    AppConfig.apply_to_app(app)
    return app


def run_integrated_test():
    """
    통합 UI 테스트 실행
    
    이 함수는 업비트 자동매매 시스템의 모든 UI 컴포넌트를 통합하여 테스트하는
    환경을 제공합니다. 메인 윈도우를 생성하고 표시한 후 애플리케이션 이벤트 루프를
    시작합니다.
    """
    logger = setup_logging()
    logger.info("통합 UI 테스트 시작")
    
    try:
        app = create_application()
        
        logger.info("메인 윈도우 생성")
        main_window = MainWindow()
        main_window.show()
        
        logger.info("애플리케이션 실행")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_integrated_test()