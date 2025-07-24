"""
설정 화면 테스트 모듈

이 모듈은 업비트 자동매매 시스템의 설정 화면 기능을 테스트합니다.
"""

import unittest
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# 테스트할 클래스 임포트
from upbit_auto_trading.ui.desktop.screens.settings.settings_screen import SettingsScreen
from upbit_auto_trading.ui.desktop.screens.settings.api_key_manager import ApiKeyManager
from upbit_auto_trading.ui.desktop.screens.settings.database_settings import DatabaseSettings
from upbit_auto_trading.ui.desktop.screens.settings.notification_settings import NotificationSettings


class TestSettings(unittest.TestCase):
    """설정 화면 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # QApplication 인스턴스가 없으면 생성
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
        
        # 테스트용 임시 디렉토리 생성
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.settings_dir = cls.temp_dir.name
        
        # 원래 설정 경로 백업
        cls.original_settings_dir = os.path.expanduser("~/.upbit_auto_trading")
        cls.original_settings_exists = os.path.exists(cls.original_settings_dir)
        
        if cls.original_settings_exists:
            cls.original_settings_backup = tempfile.TemporaryDirectory()
            if os.path.isdir(cls.original_settings_dir):
                for item in os.listdir(cls.original_settings_dir):
                    src = os.path.join(cls.original_settings_dir, item)
                    dst = os.path.join(cls.original_settings_backup.name, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
        
        # 테스트용 설정 경로 설정
        os.environ["UPBIT_AUTO_TRADING_SETTINGS_DIR"] = cls.settings_dir
    
    def setUp(self):
        """각 테스트 전에 실행"""
        # 설정 화면 생성
        self.settings_screen = SettingsScreen()
    
    def test_settings_screen_creation(self):
        """설정 화면 생성 테스트"""
        print("\n=== 테스트: 설정 화면 생성 ===")
        
        # 설정 화면이 생성되었는지 확인
        self.assertIsNotNone(self.settings_screen)
        print("설정 화면이 생성되었습니다.")
        
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
    
    def test_api_key_manager(self):
        """API 키 관리 테스트"""
        print("\n=== 테스트: API 키 관리 ===")
        
        # API 키 관리 위젯 가져오기
        api_key_manager = self.settings_screen.api_key_manager
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(api_key_manager)
        print("API 키 관리 위젯이 생성되었습니다.")
        
        # 필요한 UI 요소들이 존재하는지 확인
        self.assertTrue(hasattr(api_key_manager, 'access_key_input'))
        self.assertTrue(hasattr(api_key_manager, 'secret_key_input'))
        self.assertTrue(hasattr(api_key_manager, 'save_button'))
        self.assertTrue(hasattr(api_key_manager, 'test_button'))
        print("API 키 관리 위젯에 필요한 UI 요소들이 존재합니다.")
        
        # API 키 저장 테스트
        with patch('upbit_auto_trading.ui.desktop.screens.settings.api_key_manager.QMessageBox') as mock_message_box:
            # 테스트 API 키 설정
            api_key_manager.access_key_input.setText("test_access_key")
            api_key_manager.secret_key_input.setText("test_secret_key")
            api_key_manager.trade_permission_checkbox.setChecked(True)
            
            # 저장 메서드 직접 호출
            api_key_manager.save_api_keys()
            
            # 메시지 박스가 표시되었는지 확인
            mock_message_box.information.assert_called_once()
            print("API 키 저장 시 정보 메시지가 표시됩니다.")
        
        # API 키 테스트 테스트
        with patch('upbit_auto_trading.ui.desktop.screens.settings.api_key_manager.QMessageBox') as mock_message_box:
            # 테스트 메서드 직접 호출
            api_key_manager.test_api_keys()
            
            # 메시지 박스가 표시되었는지 확인
            mock_message_box.information.assert_called_once()
            print("API 키 테스트 시 정보 메시지가 표시됩니다.")
    
    def test_database_settings(self):
        """데이터베이스 설정 테스트"""
        print("\n=== 테스트: 데이터베이스 설정 ===")
        
        # 데이터베이스 설정 위젯 가져오기
        db_settings = self.settings_screen.database_settings
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(db_settings)
        print("데이터베이스 설정 위젯이 생성되었습니다.")
        
        # 필요한 UI 요소들이 존재하는지 확인
        self.assertTrue(hasattr(db_settings, 'db_path_input'))
        self.assertTrue(hasattr(db_settings, 'browse_button'))
        self.assertTrue(hasattr(db_settings, 'max_size_input'))
        self.assertTrue(hasattr(db_settings, 'save_button'))
        self.assertTrue(hasattr(db_settings, 'backup_button'))
        print("데이터베이스 설정 위젯에 필요한 UI 요소들이 존재합니다.")
        
        # 데이터베이스 설정 저장 테스트
        with patch('upbit_auto_trading.ui.desktop.screens.settings.database_settings.QMessageBox') as mock_message_box:
            # 테스트 설정 입력
            db_settings.db_path_input.setText("test_db_path")
            db_settings.max_size_input.setValue(20)
            
            # 저장 메서드 직접 호출
            db_settings.save_settings()
            
            # 메시지 박스가 표시되었는지 확인
            mock_message_box.information.assert_called_once()
            print("데이터베이스 설정 저장 시 정보 메시지가 표시됩니다.")
        
        # 데이터베이스 백업 테스트
        with patch('upbit_auto_trading.ui.desktop.screens.settings.database_settings.QMessageBox') as mock_message_box, \
             patch('upbit_auto_trading.ui.desktop.screens.settings.database_settings.shutil.copy2') as mock_copy:
            # 백업 메서드 직접 호출
            db_settings.backup_database()
            
            # 메시지 박스가 표시되었는지 확인
            mock_message_box.information.assert_called_once()
            print("데이터베이스 백업 시 정보 메시지가 표시됩니다.")
    
    def test_notification_settings(self):
        """알림 설정 테스트"""
        print("\n=== 테스트: 알림 설정 ===")
        
        # 알림 설정 위젯 가져오기
        notification_settings = self.settings_screen.notification_settings
        
        # 위젯이 생성되었는지 확인
        self.assertIsNotNone(notification_settings)
        print("알림 설정 위젯이 생성되었습니다.")
        
        # 필요한 UI 요소들이 존재하는지 확인
        self.assertTrue(hasattr(notification_settings, 'enable_price_alerts_checkbox'))
        self.assertTrue(hasattr(notification_settings, 'enable_trade_alerts_checkbox'))
        self.assertTrue(hasattr(notification_settings, 'enable_system_alerts_checkbox'))
        self.assertTrue(hasattr(notification_settings, 'save_button'))
        print("알림 설정 위젯에 필요한 UI 요소들이 존재합니다.")
        
        # 알림 설정 저장 테스트
        with patch('upbit_auto_trading.ui.desktop.screens.settings.notification_settings.QMessageBox') as mock_message_box:
            # 테스트 설정 입력
            notification_settings.enable_price_alerts_checkbox.setChecked(True)
            notification_settings.enable_trade_alerts_checkbox.setChecked(True)
            notification_settings.enable_system_alerts_checkbox.setChecked(False)
            
            # 저장 메서드 직접 호출
            notification_settings.save_settings()
            
            # 메시지 박스가 표시되었는지 확인
            mock_message_box.information.assert_called_once()
            print("알림 설정 저장 시 정보 메시지가 표시됩니다.")
    
    def test_settings_integration(self):
        """설정 통합 테스트"""
        print("\n=== 테스트: 설정 통합 ===")
        
        # 모든 설정 저장 테스트
        with patch.object(self.settings_screen.api_key_manager, 'save_settings') as mock_api_save, \
             patch.object(self.settings_screen.database_settings, 'save_settings') as mock_db_save, \
             patch.object(self.settings_screen.notification_settings, 'save_settings') as mock_notification_save:
            
            # 모든 설정 저장 메서드 직접 호출
            self.settings_screen.save_all_settings()
            
            # 각 설정 저장 메서드가 호출되었는지 확인
            mock_api_save.assert_called_once()
            mock_db_save.assert_called_once()
            mock_notification_save.assert_called_once()
            print("모든 설정 저장 기능이 정상적으로 작동합니다.")
        
        # 탭 전환 테스트
        for i in range(self.settings_screen.tab_widget.count()):
            # 탭 선택
            self.settings_screen.tab_widget.setCurrentIndex(i)
            
            # 현재 탭 인덱스 확인
            self.assertEqual(self.settings_screen.tab_widget.currentIndex(), i)
            print(f"탭 {i}로 전환이 정상적으로 작동합니다.")
    
    def tearDown(self):
        """각 테스트 후에 실행"""
        # 메모리 정리
        self.settings_screen.close()
        self.settings_screen.deleteLater()
    
    @classmethod
    def tearDownClass(cls):
        """테스트 클래스 정리"""
        # 테스트용 임시 디렉토리 정리
        cls.temp_dir.cleanup()
        
        # 원래 설정 경로 복원
        if cls.original_settings_exists:
            if os.path.isdir(cls.original_settings_dir):
                shutil.rmtree(cls.original_settings_dir)
            os.makedirs(cls.original_settings_dir, exist_ok=True)
            
            for item in os.listdir(cls.original_settings_backup.name):
                src = os.path.join(cls.original_settings_backup.name, item)
                dst = os.path.join(cls.original_settings_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            cls.original_settings_backup.cleanup()
        
        # 환경 변수 복원
        if "UPBIT_AUTO_TRADING_SETTINGS_DIR" in os.environ:
            del os.environ["UPBIT_AUTO_TRADING_SETTINGS_DIR"]


if __name__ == "__main__":
    unittest.main()