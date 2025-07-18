"""
애플리케이션 모듈

이 모듈은 업비트 자동매매 시스템의 애플리케이션 클래스를 제공합니다.
"""

import sys
from PyQt6.QtWidgets import QApplication

from upbit_auto_trading.ui.desktop.config import AppConfig
from upbit_auto_trading.ui.desktop.utils.logging_manager import LoggingManager


class Application:
    """애플리케이션 싱글톤 클래스"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(Application, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """초기화"""
        if self._initialized:
            return
        
        self._initialized = True
        self._app = None
        self._logger = LoggingManager().get_logger("app")
    
    def initialize(self, args=None):
        """
        애플리케이션 초기화
        
        Args:
            args (list, optional): 명령행 인수
        """
        if args is None:
            args = sys.argv
        
        # 애플리케이션 인스턴스 생성
        self._app = QApplication(args)
        
        # 애플리케이션 설정 적용
        AppConfig.apply_to_app(self._app)
        
        self._logger.info("애플리케이션 초기화 완료")
        
        return self._app
    
    def run(self):
        """
        애플리케이션 실행
        
        Returns:
            int: 종료 코드
        """
        if self._app is None:
            self.initialize()
        
        self._logger.info("애플리케이션 실행")
        return self._app.exec()
    
    def quit(self, exit_code=0):
        """
        애플리케이션 종료
        
        Args:
            exit_code (int): 종료 코드
        """
        if self._app is not None:
            self._logger.info(f"애플리케이션 종료 (코드: {exit_code})")
            self._app.exit(exit_code)
    
    @property
    def app(self):
        """QApplication 인스턴스 반환"""
        if self._app is None:
            self.initialize()
        return self._app