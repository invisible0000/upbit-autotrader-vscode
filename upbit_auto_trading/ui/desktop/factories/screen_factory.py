"""
화면 팩토리 모듈

이 모듈은 업비트 자동매매 시스템의 화면을 생성하는 팩토리 클래스를 제공합니다.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class ScreenFactory:
    """화면 생성 팩토리 클래스"""
    
    _instance = None
    _initialized = False
    _screen_cache = {}
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super(ScreenFactory, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """초기화"""
        if self._initialized:
            return
        
        self._initialized = True
    
    def create_screen(self, screen_type, use_cache=True):
        """
        화면 인스턴스 생성
        
        Args:
            screen_type (str): 화면 유형
            use_cache (bool): 캐시 사용 여부
            
        Returns:
            QWidget: 생성된 화면 인스턴스
        """
        # 캐시에서 화면 반환
        if use_cache and screen_type in self._screen_cache:
            return self._screen_cache[screen_type]
        
        # 화면 생성
        screen = None
        
        if screen_type == "dashboard":
            from upbit_auto_trading.ui.desktop.screens.dashboard.dashboard_screen import DashboardScreen
            screen = DashboardScreen()
        elif screen_type == "chart_view":
            from upbit_auto_trading.ui.desktop.screens.chart_view.chart_view_screen import ChartViewScreen
            screen = ChartViewScreen()
        elif screen_type == "settings":
            from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
            screen = SettingsScreen()
        else:
            # 임시 화면 생성
            screen = self._create_placeholder_screen(screen_type)
        
        # 캐시에 화면 저장
        if use_cache:
            self._screen_cache[screen_type] = screen
        
        return screen
    
    def _create_placeholder_screen(self, screen_name):
        """
        임시 화면 생성
        
        Args:
            screen_name (str): 화면 이름
            
        Returns:
            QWidget: 생성된 임시 화면
        """
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        
        label = QLabel(f"{screen_name} 화면 (구현 예정)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        return placeholder
    
    def clear_cache(self):
        """화면 캐시 초기화"""
        self._screen_cache.clear()