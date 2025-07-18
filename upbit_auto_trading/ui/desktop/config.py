"""
애플리케이션 설정 관리 모듈

이 모듈은 업비트 자동매매 시스템의 설정을 관리하는 클래스를 제공합니다.
"""

from PyQt6.QtWidgets import QApplication


class AppConfig:
    """애플리케이션 설정 관리 클래스"""
    
    # 애플리케이션 기본 정보
    APP_NAME = "업비트 자동매매 시스템"
    APP_VERSION = "1.0.0"
    ORGANIZATION_NAME = "UpbitAutoTrading"
    
    # UI 설정
    MIN_WIDTH = 1280
    MIN_HEIGHT = 720
    
    # 테마 설정
    DEFAULT_THEME = "light"  # "light" 또는 "dark"
    
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