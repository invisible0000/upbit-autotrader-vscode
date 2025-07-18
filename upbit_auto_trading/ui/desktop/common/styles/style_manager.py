"""
스타일 관리자 모듈
"""
import os
from enum import Enum
from PyQt6.QtWidgets import QApplication


class Theme(Enum):
    """테마 열거형"""
    LIGHT = "light"
    DARK = "dark"


class StyleManager:
    """
    애플리케이션 스타일 관리자
    
    스타일 시트를 로드하고 적용하는 기능을 제공합니다.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StyleManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._current_theme = Theme.LIGHT
        self._style_sheets = {}
        self._load_style_sheets()
    
    def _load_style_sheets(self):
        """스타일 시트 파일 로드"""
        styles_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 기본 스타일 시트 로드
        default_style_path = os.path.join(styles_dir, "default_style.qss")
        with open(default_style_path, "r", encoding="utf-8") as file:
            self._style_sheets[Theme.LIGHT] = file.read()
        
        # 다크 모드 스타일 시트 로드
        dark_style_path = os.path.join(styles_dir, "dark_style.qss")
        with open(dark_style_path, "r", encoding="utf-8") as file:
            self._style_sheets[Theme.DARK] = file.read()
    
    def apply_theme(self, theme=None):
        """
        테마 적용
        
        Args:
            theme (Theme, optional): 적용할 테마. None인 경우 현재 테마 적용.
        """
        if theme is not None:
            self._current_theme = theme
        
        QApplication.instance().setStyleSheet(self._style_sheets[self._current_theme])
    
    def toggle_theme(self):
        """테마 전환"""
        if self._current_theme == Theme.LIGHT:
            self._current_theme = Theme.DARK
        else:
            self._current_theme = Theme.LIGHT
        
        self.apply_theme()
    
    @property
    def current_theme(self):
        """현재 테마 반환"""
        return self._current_theme