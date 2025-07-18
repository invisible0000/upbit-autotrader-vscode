"""
알림 팩토리 테스트

이 모듈은 NotificationFactory 클래스에 대한 단위 테스트를 포함합니다.
- 가격 알림 생성 테스트
- 거래 알림 생성 테스트
- 시스템 알림 생성 테스트
"""

import os
import sys
import unittest
from datetime import datetime

# 테스트 환경 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# 테스트 대상 모듈 임포트
from show_notification_center import NotificationFactory
from upbit_auto_trading.ui.desktop.models.notification import NotificationType


class TestNotificationFactory(unittest.TestCase):
    """알림 팩토리 테스트 클래스"""

    def setUp(self):
        """각 테스트 전 설정"""
        print("\n=== 테스트 id 08_5_7: test_notification_factory ===")
        # 테스트 전 NotificationFactory의 ID 카운터 초기화
        NotificationFactory._next_id = 1

    def test_create_price_alert(self):
        """가격 알림 생성 테스트"""
        print("가격 알림 생성 테스트 시작")
        
        # 가격 상승 알림 생성
        symbol = "KRW-BTC"
        price = 50000000
        test_time = datetime.now()
        
        notification = NotificationFactory.create_price_alert(
            symbol=symbol,
            price=price,
            is_above=True,
            timestamp=test_time
        )
        
        # 알림 속성 검증
        self.assertEqual(notification.id, 1)
        self.assertEqual(notification.type, NotificationType.PRICE_ALERT)
        self.assertEqual(notification.title, "가격 알림")
        self.assertEqual(notification.message, "KRW-BTC 가격이 50,000,000원을 초과했습니다.")
        self.assertEqual(notification.timestamp, test_time)
        self.assertEqual(notification.related_symbol, symbol)
        self.assertFalse(notification.is_read)
        
        # 가격 하락 알림 생성
        notification2 = NotificationFactory.create_price_alert(
            symbol="KRW-ETH",
            price=3000000,
            is_above=False,
            timestamp=test_time
        )
        
        # 두 번째 알림 속성 검증
        self.assertEqual(notification2.id, 2)  # ID가 증가해야 함
        self.assertEqual(notification2.message, "KRW-ETH 가격이 3,000,000원을 미만으로 떨어졌습니다.")
        
        print("가격 알림 생성 테스트 완료")

    def test_create_trade_alert(self):
        """거래 알림 생성 테스트"""
        print("거래 알림 생성 테스트 시작")
        
        # 매수 알림 생성
        symbol = "KRW-BTC"
        price = 49500000
        quantity = 0.01
        test_time = datetime.now()
        
        notification = NotificationFactory.create_trade_alert(
            symbol=symbol,
            price=price,
            quantity=quantity,
            is_buy=True,
            timestamp=test_time
        )
        
        # 알림 속성 검증
        self.assertEqual(notification.id, 1)
        self.assertEqual(notification.type, NotificationType.TRADE_ALERT)
        self.assertEqual(notification.title, "거래 알림")
        self.assertEqual(notification.message, "KRW-BTC 매수 주문이 체결되었습니다. 체결 가격: 49,500,000원, 수량: 0.01 BTC")
        self.assertEqual(notification.timestamp, test_time)
        self.assertEqual(notification.related_symbol, symbol)
        self.assertFalse(notification.is_read)
        
        # 매도 알림 생성
        notification2 = NotificationFactory.create_trade_alert(
            symbol="KRW-ETH",
            price=3050000,
            quantity=0.5,
            is_buy=False,
            timestamp=test_time
        )
        
        # 두 번째 알림 속성 검증
        self.assertEqual(notification2.id, 2)  # ID가 증가해야 함
        self.assertEqual(notification2.message, "KRW-ETH 매도 주문이 체결되었습니다. 체결 가격: 3,050,000원, 수량: 0.5 ETH")
        
        print("거래 알림 생성 테스트 완료")

    def test_create_system_alert(self):
        """시스템 알림 생성 테스트"""
        print("시스템 알림 생성 테스트 시작")
        
        # 시스템 알림 생성
        message = "데이터베이스 연결이 복구되었습니다."
        test_time = datetime.now()
        
        notification = NotificationFactory.create_system_alert(
            message=message,
            timestamp=test_time
        )
        
        # 알림 속성 검증
        self.assertEqual(notification.id, 1)
        self.assertEqual(notification.type, NotificationType.SYSTEM_ALERT)
        self.assertEqual(notification.title, "시스템 알림")
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.timestamp, test_time)
        self.assertIsNone(notification.related_symbol)
        self.assertFalse(notification.is_read)
        
        print("시스템 알림 생성 테스트 완료")

    def test_id_generation(self):
        """ID 생성 테스트"""
        print("ID 생성 테스트 시작")
        
        # 여러 알림 생성하여 ID가 순차적으로 증가하는지 확인
        notifications = [
            NotificationFactory.create_price_alert("KRW-BTC", 50000000),
            NotificationFactory.create_trade_alert("KRW-BTC", 49500000, 0.01),
            NotificationFactory.create_system_alert("테스트 메시지")
        ]
        
        # ID 검증
        for i, notification in enumerate(notifications, 1):
            self.assertEqual(notification.id, i)
        
        print("ID 생성 테스트 완료")


if __name__ == '__main__':
    unittest.main()