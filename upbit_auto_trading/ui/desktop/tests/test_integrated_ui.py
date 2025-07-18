"""
통합 UI 테스트 모듈

이 모듈은 업비트 자동매매 시스템의 UI 컴포넌트를 테스트하는 클래스를 제공합니다.
"""

import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from upbit_auto_trading.ui.desktop.main_window import MainWindow


class IntegratedUITest(unittest.TestCase):
    """통합 UI 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        cls.app = QApplication([])
    
    def setUp(self):
        """테스트 설정"""
        self.main_window = MainWindow()
    
    def test_main_window_creation(self):
        """
        메인 윈도우 생성 테스트
        
        이 테스트는 메인 윈도우가 올바르게 생성되는지 확인합니다.
        """
        self.assertIsNotNone(self.main_window)
        self.assertEqual(self.main_window.windowTitle(), "업비트 자동매매 시스템")
    
    def test_navigation(self):
        """
        네비게이션 테스트
        
        이 테스트는 화면 전환이 올바르게 작동하는지 확인합니다.
        """
        # 대시보드 화면으로 이동
        self.main_window._change_screen("dashboard")
        self.assertEqual(self.main_window.stack_widget.currentIndex(), 0)
        
        # 차트 뷰 화면으로 이동
        self.main_window._change_screen("chart_view")
        self.assertEqual(self.main_window.stack_widget.currentIndex(), 1)
    
    def test_theme_toggle(self):
        """
        테마 전환 테스트
        
        이 테스트는 테마 전환 기능이 올바르게 작동하는지 확인합니다.
        """
        # 초기 테마 확인
        initial_theme = self.main_window.style_manager.current_theme
        
        # 테마 전환
        self.main_window._toggle_theme()
        
        # 테마가 변경되었는지 확인
        self.assertNotEqual(self.main_window.style_manager.current_theme, initial_theme)
    
    def tearDown(self):
        """테스트 정리"""
        self.main_window.close()
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        cls.app.quit()


if __name__ == "__main__":
    unittest.main()