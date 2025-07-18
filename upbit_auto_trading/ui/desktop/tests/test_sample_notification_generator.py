"""
샘플 알림 생성기 테스트

이 모듈은 샘플 알림 생성 함수에 대한 단위 테스트를 포함합니다.
- 샘플 알림 생성 테스트
- 알림 개수 지정 테스트
"""

import os
import sys
import unittest

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# 테스트 대상 모듈 임포트
from show_notification_center import create_sample_notifications, BTC_SYMBOL, ETH_SYMBOL
from upbit_auto_trading.ui.desktop.models.notification import NotificationType


class TestSampleNotificationGenerator(unittest.TestCase):
    """샘플 알림 생성기 테스트 클래스"""

    def setUp(self):
        """각 테스트 전 설정"""
        print("\n=== 테스트 id 08_5_8: test_sample_notification_generator ===")

    def test_default_sample_count(self):
        """기본 샘플 개수 테스트"""
        print("기본 샘플 개수 테스트 시작")
        
        # 기본 개수(5개)로 샘플 알림 생성
        notifications = create_sample_notifications()
        
        # 알림 개수 검증
        self.assertEqual(len(notifications), 5)
        
        # 알림 유형 검증
        self.assertEqual(notifications[0].type, NotificationType.PRICE_ALERT)
        self.assertEqual(notifications[1].type, NotificationType.TRADE_ALERT)
        self.assertEqual(notifications[2].type, NotificationType.SYSTEM_ALERT)
        self.assertEqual(notifications[3].type, NotificationType.PRICE_ALERT)
        self.assertEqual(notifications[4].type, NotificationType.TRADE_ALERT)
        
        # 관련 코인 심볼 검증
        self.assertEqual(notifications[0].related_symbol, BTC_SYMBOL)
        self.assertEqual(notifications[3].related_symbol, ETH_SYMBOL)
        
        print("기본 샘플 개수 테스트 완료")

    def test_custom_sample_count(self):
        """사용자 지정 샘플 개수 테스트"""
        print("사용자 지정 샘플 개수 테스트 시작")
        
        # 사용자 지정 개수(3개)로 샘플 알림 생성
        notifications = create_sample_notifications(count=3)
        
        # 알림 개수 검증
        self.assertEqual(len(notifications), 3)
        
        # 사용자 지정 개수(8개)로 샘플 알림 생성
        notifications = create_sample_notifications(count=8)
        
        # 알림 개수 검증
        self.assertEqual(len(notifications), 8)
        
        # 기본 샘플(5개)이 반복되는지 확인
        self.assertEqual(notifications[5].type, notifications[0].type)
        self.assertEqual(notifications[6].type, notifications[1].type)
        self.assertEqual(notifications[7].type, notifications[2].type)
        
        print("사용자 지정 샘플 개수 테스트 완료")

    def test_notification_properties(self):
        """알림 속성 테스트"""
        print("알림 속성 테스트 시작")
        
        # 샘플 알림 생성
        notifications = create_sample_notifications(count=5)
        
        # 각 알림의 필수 속성 검증
        for notification in notifications:
            # 모든 알림은 ID를 가져야 함
            self.assertIsNotNone(notification.id)
            
            # 모든 알림은 제목을 가져야 함
            self.assertIsNotNone(notification.title)
            self.assertNotEqual(notification.title, "")
            
            # 모든 알림은 메시지를 가져야 함
            self.assertIsNotNone(notification.message)
            self.assertNotEqual(notification.message, "")
            
            # 모든 알림은 타임스탬프를 가져야 함
            self.assertIsNotNone(notification.timestamp)
            
            # 시스템 알림을 제외한 모든 알림은 관련 코인 심볼을 가져야 함
            if notification.type != NotificationType.SYSTEM_ALERT:
                self.assertIsNotNone(notification.related_symbol)
                self.assertIn(notification.related_symbol, [BTC_SYMBOL, ETH_SYMBOL])
        
        print("알림 속성 테스트 완료")


if __name__ == '__main__':
    unittest.main()