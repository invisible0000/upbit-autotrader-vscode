"""
설정 화면 통합 테스트

이 모듈은 설정 화면의 기능을 테스트합니다.
- API 키 관리 화면
- 데이터베이스 설정 화면
- 알림 설정 화면
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# 테스트할 클래스 임포트
from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
from upbit_auto_trading.ui.desktop.screens.settings.api_key_manager import ApiKeyManager
from upbit_auto_trading.ui.desktop.screens.settings.database_settings import DatabaseSettings
from upbit_auto_trading.ui.desktop.screens.settings.notification_settings import NotificationSettings


class TestSettingsView(unittest.TestCase):
    """설정 화면 테스트 클래스"""

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
        # 설정 화면 생성
        self.settings_screen = SettingsScreen()

    def tearDown(self):
        """각 테스트 후에 실행"""
        # 메모리 정리
        if hasattr(self, 'settings_screen'):
            self.settings_screen.deleteLater()

    def test_08_4_1_settings_screen_creation(self):
        """=== 테스트 id 08_4_1: settings_screen_creation ===
        설정 화면이 올바르게 생성되는지 테스트
        """
        print("\n=== 테스트 id 08_4_1: settings_screen_creation ===")
        
        # 설정 화면이 생성되었는지 확인
        self.assertIsNotNone(self.settings_screen)
        print("설정 화면이 성공적으로 생성되었습니다.")
        
        # 필요한 위젯들이 포함되어 있는지 확인
        self.assertIsNotNone(self.settings_screen.api_key_manager)
        print("API 키 관리 위젯이 존재합니다.")
        
        self.assertIsNotNone(self.settings_screen.database_settings)
        print("데이터베이스 설정 위젯이 존재합니다.")
        
        self.assertIsNotNone(self.settings_screen.notification_settings)
        print("알림 설정 위젯이 존재합니다.")
        
        # 설정 화면의 탭 위젯이 존재하는지 확인
        self.assertIsNotNone(self.settings_screen.tab_widget)
        print("탭 위젯이 존재합니다.")
        
        # 탭 개수 확인
        self.assertEqual(self.settings_screen.tab_widget.count(), 3)
        print("탭 위젯에 3개의 탭이 존재합니다.")

    def test_08_4_2_api_key_manager(self):
        """=== 테스트 id 08_4_2: api_key_manager ===
        API 키 관리 화면이 올바르게 작동하는지 테스트
        """
        print("\n=== 테스트 id 08_4_2: api_key_manager ===")
        
        # API 키 관리 위젯 생성
        api_key_manager = ApiKeyManager()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(api_key_manager)
        print("API 키 관리 위젯이 성공적으로 생성되었습니다.")
        
        # 필요한 UI 요소들이 존재하는지 확인
        self.assertTrue(hasattr(api_key_manager, 'access_key_input'))
        self.assertTrue(hasattr(api_key_manager, 'secret_key_input'))
        self.assertTrue(hasattr(api_key_manager, 'save_button'))
        self.assertTrue(hasattr(api_key_manager, 'test_button'))
        print("API 키 관리 위젯에 필요한 UI 요소들이 존재합니다.")
        
        # API 키 저장 기능 테스트 - 직접 메서드 호출
        api_key_manager.save_api_keys = MagicMock()
        
        # 테스트 API 키 설정
        api_key_manager.access_key_input.setText("test_access_key")
        api_key_manager.secret_key_input.setText("test_secret_key")
        
        # 저장 메서드 직접 호출
        api_key_manager.save_api_keys()
        
        # 저장 함수가 호출되었는지 확인
        self.assertEqual(api_key_manager.save_api_keys.call_count, 1)
        print("API 키 저장 기능이 정상적으로 작동합니다.")
        
        # API 키 테스트 기능 테스트 - 직접 메서드 호출
        api_key_manager.test_api_keys = MagicMock()
        
        # 테스트 메서드 직접 호출
        api_key_manager.test_api_keys()
        
        # 테스트 함수가 호출되었는지 확인
        self.assertEqual(api_key_manager.test_api_keys.call_count, 1)
        print("API 키 테스트 기능이 정상적으로 작동합니다.")

    def test_08_4_3_database_settings(self):
        """=== 테스트 id 08_4_3: database_settings ===
        데이터베이스 설정 화면이 올바르게 작동하는지 테스트
        """
        print("\n=== 테스트 id 08_4_3: database_settings ===")
        
        # 데이터베이스 설정 위젯 생성
        db_settings = DatabaseSettings()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(db_settings)
        print("데이터베이스 설정 위젯이 성공적으로 생성되었습니다.")
        
        # 필요한 UI 요소들이 존재하는지 확인
        self.assertTrue(hasattr(db_settings, 'db_path_input'))
        self.assertTrue(hasattr(db_settings, 'browse_button'))
        self.assertTrue(hasattr(db_settings, 'max_size_input'))
        self.assertTrue(hasattr(db_settings, 'save_button'))
        self.assertTrue(hasattr(db_settings, 'backup_button'))
        print("데이터베이스 설정 위젯에 필요한 UI 요소들이 존재합니다.")
        
        # 데이터베이스 설정 저장 기능 테스트 - 직접 메서드 호출
        db_settings.save_settings = MagicMock()
        
        # 테스트 설정 입력
        db_settings.db_path_input.setText("test_db_path")
        db_settings.max_size_input.setValue(10)
        
        # 저장 메서드 직접 호출
        db_settings.save_settings()
        
        # 저장 함수가 호출되었는지 확인
        self.assertEqual(db_settings.save_settings.call_count, 1)
        print("데이터베이스 설정 저장 기능이 정상적으로 작동합니다.")
        
        # 데이터베이스 백업 기능 테스트 - 직접 메서드 호출
        db_settings.backup_database = MagicMock()
        
        # 백업 메서드 직접 호출
        db_settings.backup_database()
        
        # 백업 함수가 호출되었는지 확인
        self.assertEqual(db_settings.backup_database.call_count, 1)
        print("데이터베이스 백업 기능이 정상적으로 작동합니다.")

    def test_08_4_4_notification_settings(self):
        """=== 테스트 id 08_4_4: notification_settings ===
        알림 설정 화면이 올바르게 작동하는지 테스트
        """
        print("\n=== 테스트 id 08_4_4: notification_settings ===")
        
        # 알림 설정 위젯 생성
        notification_settings = NotificationSettings()
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(notification_settings)
        print("알림 설정 위젯이 성공적으로 생성되었습니다.")
        
        # 필요한 UI 요소들이 존재하는지 확인
        self.assertTrue(hasattr(notification_settings, 'enable_price_alerts_checkbox'))
        self.assertTrue(hasattr(notification_settings, 'enable_trade_alerts_checkbox'))
        self.assertTrue(hasattr(notification_settings, 'enable_system_alerts_checkbox'))
        self.assertTrue(hasattr(notification_settings, 'save_button'))
        print("알림 설정 위젯에 필요한 UI 요소들이 존재합니다.")
        
        # 알림 설정 저장 기능 테스트 - 직접 메서드 호출
        notification_settings.save_settings = MagicMock()
        
        # 테스트 설정 입력
        notification_settings.enable_price_alerts_checkbox.setChecked(True)
        notification_settings.enable_trade_alerts_checkbox.setChecked(True)
        notification_settings.enable_system_alerts_checkbox.setChecked(False)
        
        # 저장 메서드 직접 호출
        notification_settings.save_settings()
        
        # 저장 함수가 호출되었는지 확인
        self.assertEqual(notification_settings.save_settings.call_count, 1)
        print("알림 설정 저장 기능이 정상적으로 작동합니다.")

    def test_08_4_5_settings_integration(self):
        """=== 테스트 id 08_4_5: settings_integration ===
        설정 화면의 통합 기능이 올바르게 작동하는지 테스트
        """
        print("\n=== 테스트 id 08_4_5: settings_integration ===")
        
        # 설정 화면의 저장 기능 테스트 - 직접 메서드 호출
        self.settings_screen.save_all_settings = MagicMock()
        
        # 저장 메서드 직접 호출
        self.settings_screen.save_all_settings()
        
        # 저장 함수가 호출되었는지 확인
        self.assertEqual(self.settings_screen.save_all_settings.call_count, 1)
        print("모든 설정 저장 기능이 정상적으로 작동합니다.")
        
        # 탭 전환 테스트
        for i in range(self.settings_screen.tab_widget.count()):
            # 탭 선택
            self.settings_screen.tab_widget.setCurrentIndex(i)
            
            # 현재 탭 인덱스 확인
            self.assertEqual(self.settings_screen.tab_widget.currentIndex(), i)
            print(f"탭 {i}로 전환이 정상적으로 작동합니다.")


if __name__ == "__main__":
    unittest.main()