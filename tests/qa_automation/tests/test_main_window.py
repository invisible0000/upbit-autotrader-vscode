"""
메인 윈도우 테스트 모듈

이 모듈은 업비트 자동매매 시스템의 메인 윈도우 기능을 테스트합니다.
"""

import unittest
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QPoint

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 테스트할 클래스 임포트
from upbit_auto_trading.ui.desktop.main_window import MainWindow


class TestMainWindow(unittest.TestCase):
    """메인 윈도우 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # QApplication 인스턴스가 없으면 생성
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """각 테스트 전에 실행"""
        # 메인 윈도우 생성
        self.window = MainWindow()
    
    def test_window_title(self):
        """윈도우 제목 테스트"""
        print("\n=== 테스트: 윈도우 제목 ===")
        
        # 윈도우 제목 확인
        self.assertEqual(self.window.windowTitle(), "업비트 자동매매 시스템")
        print("윈도우 제목이 올바르게 설정되었습니다.")
    
    def test_window_size(self):
        """윈도우 크기 테스트"""
        print("\n=== 테스트: 윈도우 크기 ===")
        
        # 최소 크기 확인
        min_size = self.window.minimumSize()
        self.assertEqual(min_size.width(), 1280)
        self.assertEqual(min_size.height(), 720)
        print("윈도우 최소 크기가 올바르게 설정되었습니다.")
        
        # 현재 크기 확인
        current_size = self.window.size()
        self.assertGreaterEqual(current_size.width(), 1280)
        self.assertGreaterEqual(current_size.height(), 720)
        print("윈도우 현재 크기가 최소 크기 이상입니다.")
    
    def test_navigation_bar(self):
        """네비게이션 바 테스트"""
        print("\n=== 테스트: 네비게이션 바 ===")
        
        # 네비게이션 바 존재 확인
        self.assertIsNotNone(self.window.nav_bar)
        print("네비게이션 바가 존재합니다.")
        
        # 네비게이션 버튼 존재 확인
        self.assertTrue(hasattr(self.window.nav_bar, 'btn_dashboard'))
        self.assertTrue(hasattr(self.window.nav_bar, 'btn_chart'))
        self.assertTrue(hasattr(self.window.nav_bar, 'btn_settings'))
        print("네비게이션 버튼들이 존재합니다.")
        
        # 기본 선택 버튼 확인
        self.assertTrue(self.window.nav_bar.btn_dashboard.isChecked())
        print("대시보드 버튼이 기본적으로 선택되어 있습니다.")
    
    def test_navigation_buttons(self):
        """네비게이션 버튼 테스트"""
        print("\n=== 테스트: 네비게이션 버튼 ===")
        
        # 대시보드 버튼 클릭
        QTest.mouseClick(self.window.nav_bar.btn_dashboard, Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.stack_widget.currentIndex(), 0)
        self.assertTrue(self.window.nav_bar.btn_dashboard.isChecked())
        print("대시보드 버튼 클릭 시 대시보드 화면으로 전환됩니다.")
        
        # 차트 뷰 버튼 클릭
        QTest.mouseClick(self.window.nav_bar.btn_chart, Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.stack_widget.currentIndex(), 1)
        self.assertTrue(self.window.nav_bar.btn_chart.isChecked())
        print("차트 뷰 버튼 클릭 시 차트 뷰 화면으로 전환됩니다.")
        
        # 설정 버튼 클릭
        QTest.mouseClick(self.window.nav_bar.btn_settings, Qt.MouseButton.LeftButton)
        self.assertEqual(self.window.stack_widget.currentIndex(), 8)
        self.assertTrue(self.window.nav_bar.btn_settings.isChecked())
        print("설정 버튼 클릭 시 설정 화면으로 전환됩니다.")
    
    def test_theme_toggle(self):
        """테마 전환 테스트"""
        print("\n=== 테스트: 테마 전환 ===")
        
        # 초기 테마 확인
        initial_theme = self.window.style_manager.current_theme
        print(f"초기 테마: {initial_theme}")
        
        # 테마 전환
        self.window._toggle_theme()
        
        # 테마가 전환되었는지 확인
        current_theme = self.window.style_manager.current_theme
        self.assertNotEqual(current_theme, initial_theme)
        print(f"테마가 {initial_theme}에서 {current_theme}로 전환되었습니다.")
        
        # 다시 원래 테마로 전환
        self.window._toggle_theme()
        self.assertEqual(self.window.style_manager.current_theme, initial_theme)
        print(f"테마가 다시 {initial_theme}로 전환되었습니다.")
    
    def test_status_bar(self):
        """상태 바 테스트"""
        print("\n=== 테스트: 상태 바 ===")
        
        # 상태 바 존재 확인
        self.assertIsNotNone(self.window.status_bar)
        print("상태 바가 존재합니다.")
        
        # 상태 바 메서드 존재 확인
        self.assertTrue(hasattr(self.window.status_bar, 'set_api_status'))
        self.assertTrue(hasattr(self.window.status_bar, 'set_db_status'))
        self.assertTrue(hasattr(self.window.status_bar, 'show_message'))
        print("상태 바 메서드들이 존재합니다.")
        
        # 상태 바 메시지 표시
        self.window.status_bar.show_message("테스트 메시지")
        print("상태 바에 메시지가 표시됩니다.")
    
    def test_menu_bar(self):
        """메뉴 바 테스트"""
        print("\n=== 테스트: 메뉴 바 ===")
        
        # 메뉴 바 존재 확인
        self.assertIsNotNone(self.window.menuBar())
        print("메뉴 바가 존재합니다.")
        
        # 메뉴 항목 확인
        menus = [menu.title() for menu in self.window.menuBar().findChildren(QMenu)]
        self.assertIn("파일", menus)
        self.assertIn("보기", menus)
        self.assertIn("도움말", menus)
        print("필요한 메뉴 항목들이 존재합니다.")
    
    def test_about_dialog(self):
        """정보 대화상자 테스트"""
        print("\n=== 테스트: 정보 대화상자 ===")
        
        # 정보 대화상자 메서드 존재 확인
        self.assertTrue(hasattr(self.window, '_show_about_dialog'))
        print("정보 대화상자 메서드가 존재합니다.")
        
        # 정보 대화상자 표시 (실제로는 표시하지 않음)
        # 대화상자가 표시되면 테스트가 중단되므로 모의 객체로 대체
        original_about = QMessageBox.about
        try:
            # 모의 객체로 대체
            QMessageBox.about = MagicMock()
            
            # 정보 대화상자 표시
            self.window._show_about_dialog()
            
            # 함수가 호출되었는지 확인
            QMessageBox.about.assert_called_once()
            print("정보 대화상자가 표시됩니다.")
        finally:
            # 원래 함수 복원
            QMessageBox.about = original_about
    
    def test_settings_save_load(self):
        """설정 저장 및 로드 테스트"""
        print("\n=== 테스트: 설정 저장 및 로드 ===")
        
        # 설정 저장 및 로드 메서드 존재 확인
        self.assertTrue(hasattr(self.window, '_load_settings'))
        self.assertTrue(hasattr(self.window, '_save_settings'))
        print("설정 저장 및 로드 메서드가 존재합니다.")
        
        # 설정 저장
        self.window._save_settings()
        print("설정이 저장되었습니다.")
        
        # 설정 로드
        self.window._load_settings()
        print("설정이 로드되었습니다.")
    
    def tearDown(self):
        """각 테스트 후에 실행"""
        # 메모리 정리
        self.window.close()
        self.window.deleteLater()


if __name__ == "__main__":
    unittest.main()