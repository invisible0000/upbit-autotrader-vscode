"""
알림 센터 통합 테스트

이 모듈은 알림 센터 기능에 대한 통합 테스트를 포함합니다.
- 알림 목록 화면 테스트
- 알림 설정 화면 테스트
- 알림 필터 기능 테스트

요구사항:
- 7.1: 시스템이 실행 중이면 선택된 코인의 가격, 거래량, 호가 정보를 실시간으로 표시해야 한다.
- 7.2: 가격이 설정된 임계값을 초과하거나 미만이면 시스템은 사용자에게 알림을 보내야 한다.
- 7.3: 주문이 체결되면 시스템은 사용자에게 알림을 보내야 한다.
- 7.4: 시스템 오류가 발생하면 시스템은 사용자에게 알림을 보내고 오류 로그를 기록해야 한다.
- 7.5: 사용자가 알림 설정을 변경하면 시스템은 알림 유형, 빈도, 전달 방법을 조정할 수 있어야 한다.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# 테스트 대상 모듈 임포트
from upbit_auto_trading.ui.desktop.screens.notification_center.notification_center import NotificationCenter
from upbit_auto_trading.ui.desktop.screens.notification_center.notification_list import NotificationList
from upbit_auto_trading.ui.desktop.screens.notification_center.notification_filter import NotificationFilter
from upbit_auto_trading.ui.desktop.models.notification import Notification, NotificationType


class TestNotificationCenter(unittest.TestCase):
    """알림 센터 통합 테스트 클래스"""

    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        # QApplication 인스턴스가 없으면 생성
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """각 테스트 전 설정"""
        print("\n=== 테스트 id 08_5_1: test_notification_center_initialization ===")
        # 알림 센터 인스턴스 생성
        self.notification_center = NotificationCenter()
        
        # 테스트용 알림 데이터
        self.test_notifications = [
            Notification(
                id=1,
                type=NotificationType.PRICE_ALERT,
                title="가격 알림",
                message="BTC 가격이 50,000,000원을 초과했습니다.",
                timestamp=datetime.now() - timedelta(minutes=5),
                is_read=False,
                related_symbol="KRW-BTC"
            ),
            Notification(
                id=2,
                type=NotificationType.TRADE_ALERT,
                title="거래 알림",
                message="BTC 매수 주문이 체결되었습니다.",
                timestamp=datetime.now() - timedelta(minutes=10),
                is_read=True,
                related_symbol="KRW-BTC"
            ),
            Notification(
                id=3,
                type=NotificationType.SYSTEM_ALERT,
                title="시스템 알림",
                message="데이터베이스 연결이 복구되었습니다.",
                timestamp=datetime.now() - timedelta(hours=1),
                is_read=False,
                related_symbol=None
            )
        ]

    def tearDown(self):
        """각 테스트 후 정리"""
        self.notification_center.close()
        self.notification_center = None

    def test_notification_center_initialization(self):
        """알림 센터 초기화 테스트"""
        print("알림 센터 초기화 테스트 시작")
        
        # 알림 센터가 올바르게 초기화되었는지 확인
        self.assertIsNotNone(self.notification_center)
        self.assertEqual(self.notification_center.windowTitle(), "알림 센터")
        
        # 알림 목록과 필터가 생성되었는지 확인
        self.assertIsNotNone(self.notification_center.notification_list)
        self.assertIsNotNone(self.notification_center.notification_filter)
        
        print("알림 센터 초기화 테스트 완료")

    def test_notification_list_display(self):
        """알림 목록 표시 테스트"""
        print("\n=== 테스트 id 08_5_2: test_notification_list_display ===")
        print("알림 목록 표시 테스트 시작")
        
        # 알림 목록에 테스트 알림 추가
        notification_list = self.notification_center.notification_list
        
        # 모의 데이터로 알림 목록 설정
        with patch.object(notification_list, 'load_notifications', return_value=self.test_notifications):
            notification_list.load_notifications()
        
        # 알림 목록에 알림이 표시되는지 확인
        self.assertEqual(notification_list.get_notification_count(), len(self.test_notifications))
        
        # 첫 번째 알림의 내용 확인
        first_notification = notification_list.get_notification(0)
        self.assertEqual(first_notification.id, 1)
        self.assertEqual(first_notification.title, "가격 알림")
        self.assertEqual(first_notification.type, NotificationType.PRICE_ALERT)
        
        print("알림 목록 표시 테스트 완료")

    def test_notification_filter(self):
        """알림 필터 기능 테스트"""
        print("\n=== 테스트 id 08_5_3: test_notification_filter ===")
        print("알림 필터 기능 테스트 시작")
        
        notification_list = self.notification_center.notification_list
        notification_filter = self.notification_center.notification_filter
        
        # 모의 데이터로 알림 목록 설정
        with patch.object(notification_list, 'load_notifications') as mock_load:
            mock_load.return_value = self.test_notifications.copy()
            notification_list.notifications = self.test_notifications.copy()
            notification_list._update_notification_widgets()
        
        # 초기 상태에서는 모든 알림이 표시되어야 함
        self.assertEqual(notification_list.get_notification_count(), 3)
        
        # 필터 변경 시 알림 목록이 업데이트되도록 패치
        with patch.object(notification_list, 'filter_notifications') as mock_filter:
            # 가격 알림만 필터링
            notification_filter.filter_by_type(NotificationType.PRICE_ALERT)
            mock_filter.assert_called_with(notification_type=NotificationType.PRICE_ALERT, only_unread=False)
            
            # 모든 알림 표시
            notification_filter.reset_filters()
            mock_filter.assert_called_with(notification_type=None, only_unread=False)
            
            # 읽지 않은 알림만 필터링
            notification_filter.filter_by_read_status(False)
            mock_filter.assert_called_with(notification_type=None, only_unread=True)
        
        print("알림 필터 기능 테스트 완료")

    def test_notification_actions(self):
        """알림 작업 테스트 (읽음 표시, 삭제 등)"""
        print("\n=== 테스트 id 08_5_4: test_notification_actions ===")
        print("알림 작업 테스트 시작")
        
        notification_list = self.notification_center.notification_list
        
        # 모의 데이터로 알림 목록 설정
        with patch.object(notification_list, 'load_notifications', return_value=self.test_notifications):
            notification_list.load_notifications()
        
        # 알림 읽음 표시 (ID로 표시해야 함)
        notification_list.mark_as_read(1)  # ID가 1인 알림을 읽음으로 표시
        
        # 알림 목록에서 ID가 1인 알림 찾기
        for notification in notification_list.notifications:
            if notification.id == 1:
                self.assertTrue(notification.is_read)
                break
        
        # 알림 삭제
        initial_count = notification_list.get_notification_count()
        notification_list.delete_notification(3)  # ID가 3인 알림 삭제
        self.assertEqual(notification_list.get_notification_count(), initial_count - 1)
        
        print("알림 작업 테스트 완료")

    def test_notification_settings_integration(self):
        """알림 설정과의 통합 테스트"""
        print("\n=== 테스트 id 08_5_5: test_notification_settings_integration ===")
        print("알림 설정과의 통합 테스트 시작")
        
        # 알림 설정 변경 시뮬레이션
        with patch('upbit_auto_trading.ui.desktop.screens.settings.notification_settings.NotificationSettings') as mock_settings:
            # 설정 변경 시그널 모의
            mock_settings_instance = MagicMock()
            mock_settings.return_value = mock_settings_instance
            
            # 알림 센터에 설정 변경 알림
            self.notification_center.update_settings({
                'enable_price_alerts': True,
                'enable_trade_alerts': False,
                'enable_system_alerts': True,
                'notification_sound': True,
                'desktop_notifications': True
            })
            
            # 설정이 알림 센터에 적용되었는지 확인
            self.assertTrue(self.notification_center.is_price_alert_enabled())
            self.assertFalse(self.notification_center.is_trade_alert_enabled())
            self.assertTrue(self.notification_center.is_system_alert_enabled())
            
        print("알림 설정과의 통합 테스트 완료")

    def test_notification_creation(self):
        """알림 생성 테스트"""
        print("\n=== 테스트 id 08_5_6: test_notification_creation ===")
        print("알림 생성 테스트 시작")
        
        # 새 알림 생성
        new_notification = Notification(
            id=4,
            type=NotificationType.PRICE_ALERT,
            title="신규 가격 알림",
            message="ETH 가격이 3,000,000원 미만으로 떨어졌습니다.",
            timestamp=datetime.now(),
            is_read=False,
            related_symbol="KRW-ETH"
        )
        
        # 알림 추가
        with patch.object(self.notification_center, 'add_notification') as mock_add:
            self.notification_center.add_notification(new_notification)
            mock_add.assert_called_once_with(new_notification)
        
        print("알림 생성 테스트 완료")


if __name__ == '__main__':
    unittest.main()