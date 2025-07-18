"""
거래 알림 기능 테스트 모듈

이 모듈은 거래 알림 기능을 테스트합니다.
- 주문 체결 알림 기능 테스트
- 수익/손실 알림 기능 테스트
- 포지션 변경 알림 기능 테스트
"""

import unittest
import os
import sys
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# 테스트 대상 모듈 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트 대상 모듈 임포트
from upbit_auto_trading.business_logic.monitoring.trade_monitor import TradeMonitor
from upbit_auto_trading.business_logic.monitoring.alert_manager import AlertManager
from upbit_auto_trading.ui.desktop.models.notification import NotificationType


class TestTradeNotifications(unittest.TestCase):
    """거래 알림 기능 테스트 클래스"""
    
    def setUp(self):
        """각 테스트 전 설정"""
        print("\n=== 테스트 id 09_2_1: test_trade_notifications ===")
        
        # 테스트용 알림 관리자 생성
        self.alert_manager = AlertManager()
        
        # 테스트용 거래 모니터 생성
        self.trade_monitor = TradeMonitor(self.alert_manager)
        
        # 테스트용 코인 심볼
        self.test_symbol = "KRW-BTC"
        
        # 테스트용 주문 데이터
        self.order_data = {
            "uuid": "test-order-uuid",
            "side": "bid",  # bid: 매수, ask: 매도
            "ord_type": "limit",  # limit: 지정가, market: 시장가
            "price": 50000000,
            "state": "wait",  # wait: 체결 대기, done: 체결 완료, cancel: 취소
            "market": "KRW-BTC",
            "created_at": datetime.now().isoformat(),
            "volume": 0.01,
            "remaining_volume": 0.01,
            "reserved_fee": 250,
            "remaining_fee": 250,
            "paid_fee": 0,
            "locked": 500250,
            "executed_volume": 0,
            "trades_count": 0
        }
        
        # 테스트용 체결 데이터
        self.trade_data = {
            "uuid": "test-trade-uuid",
            "market": "KRW-BTC",
            "side": "bid",
            "price": 50000000,
            "volume": 0.01,
            "funds": 500000,
            "created_at": datetime.now().isoformat()
        }
        
        # 테스트용 포지션 데이터
        self.position_data = {
            "symbol": "KRW-BTC",
            "side": "long",  # long: 매수 포지션, short: 매도 포지션
            "entry_price": 50000000,
            "current_price": 50000000,
            "quantity": 0.01,
            "profit_loss": 0,
            "profit_loss_percentage": 0,
            "entry_time": datetime.now().isoformat()
        }
    
    def test_order_execution_notification(self):
        """주문 체결 알림 테스트"""
        print("주문 체결 알림 테스트 시작")
        
        # 알림 관리자 초기화
        self.alert_manager = AlertManager()
        self.trade_monitor = TradeMonitor(self.alert_manager)
        
        # 체결 전 주문 상태
        self.order_data["state"] = "wait"
        
        # 주문 모니터링 시작
        self.trade_monitor.add_order_to_monitor(self.order_data["uuid"], self.order_data)
        
        # 체결 전 알림 개수 확인
        notifications_before = self.alert_manager.get_notifications()
        print(f"체결 전 알림 개수: {len(notifications_before)}")
        
        # 주문 체결 상태로 변경
        executed_order = self.order_data.copy()
        executed_order["state"] = "done"
        executed_order["remaining_volume"] = 0
        executed_order["executed_volume"] = 0.01
        executed_order["trades_count"] = 1
        executed_order["paid_fee"] = 250
        executed_order["remaining_fee"] = 0
        
        # 주문 상태 업데이트 및 알림 생성
        self.trade_monitor.update_order_status(executed_order["uuid"], executed_order)
        
        # 체결 후 알림 개수 확인
        notifications_after = self.alert_manager.get_notifications()
        print(f"체결 후 알림 개수: {len(notifications_after)}")
        
        # 알림 생성 확인
        self.assertEqual(len(notifications_after), 1)
        
        # 알림 내용 확인
        notification = notifications_after[0]
        self.assertEqual(notification.type, NotificationType.TRADE_ALERT)
        self.assertEqual(notification.related_symbol, self.test_symbol)
        print(f"생성된 알림: {notification.title} - {notification.message}")
        
        print("주문 체결 알림 테스트 완료")
    
    def test_profit_loss_notification(self):
        """수익/손실 알림 테스트"""
        print("수익/손실 알림 테스트 시작")
        
        # 알림 관리자 초기화
        self.alert_manager = AlertManager()
        self.trade_monitor = TradeMonitor(self.alert_manager)
        
        # 포지션 모니터링 시작
        self.trade_monitor.add_position_to_monitor(self.test_symbol, self.position_data)
        
        # 수익 임계값 설정 (5%)
        self.trade_monitor.set_profit_threshold(5.0)
        
        # 손실 임계값 설정 (3%)
        self.trade_monitor.set_loss_threshold(3.0)
        
        # 초기 알림 개수 확인
        notifications_before = self.alert_manager.get_notifications()
        print(f"초기 알림 개수: {len(notifications_before)}")
        
        # 수익 발생 상황 시뮬레이션 (10% 상승)
        profit_position = self.position_data.copy()
        profit_position["current_price"] = int(profit_position["entry_price"] * 1.1)
        profit_position["profit_loss"] = int(profit_position["entry_price"] * 0.1 * profit_position["quantity"])
        profit_position["profit_loss_percentage"] = 10.0
        
        # 포지션 상태 업데이트 및 알림 생성
        self.trade_monitor.update_position(self.test_symbol, profit_position)
        
        # 수익 알림 확인
        profit_notifications = self.alert_manager.get_notifications()
        print(f"수익 발생 후 알림 개수: {len(profit_notifications)}")
        
        # 알림 생성 확인
        self.assertEqual(len(profit_notifications), 1)
        
        # 알림 내용 확인
        profit_notification = profit_notifications[0]
        self.assertEqual(profit_notification.type, NotificationType.TRADE_ALERT)
        self.assertEqual(profit_notification.related_symbol, self.test_symbol)
        print(f"수익 알림: {profit_notification.title} - {profit_notification.message}")
        
        # 손실 발생 상황 시뮬레이션 (5% 하락)
        loss_position = self.position_data.copy()
        loss_position["current_price"] = int(loss_position["entry_price"] * 0.95)
        loss_position["profit_loss"] = int(loss_position["entry_price"] * -0.05 * loss_position["quantity"])
        loss_position["profit_loss_percentage"] = -5.0
        
        # 포지션 상태 업데이트 및 알림 생성
        self.trade_monitor.update_position(self.test_symbol, loss_position)
        
        # 손실 알림 확인
        loss_notifications = self.alert_manager.get_notifications()
        print(f"손실 발생 후 알림 개수: {len(loss_notifications)}")
        
        # 알림 생성 확인
        self.assertEqual(len(loss_notifications), 2)
        
        # 알림 내용 확인
        loss_notification = loss_notifications[0]
        self.assertEqual(loss_notification.type, NotificationType.TRADE_ALERT)
        self.assertEqual(loss_notification.related_symbol, self.test_symbol)
        print(f"손실 알림: {loss_notification.title} - {loss_notification.message}")
        
        print("수익/손실 알림 테스트 완료")
    
    def test_position_change_notification(self):
        """포지션 변경 알림 테스트"""
        print("포지션 변경 알림 테스트 시작")
        
        # 알림 관리자 초기화
        self.alert_manager = AlertManager()
        self.trade_monitor = TradeMonitor(self.alert_manager)
        
        # 초기 알림 개수 확인
        notifications_before = self.alert_manager.get_notifications()
        print(f"초기 알림 개수: {len(notifications_before)}")
        
        # 포지션 생성 알림
        self.trade_monitor.notify_position_opened(self.test_symbol, self.position_data)
        
        # 포지션 생성 알림 확인
        open_notifications = self.alert_manager.get_notifications()
        print(f"포지션 생성 후 알림 개수: {len(open_notifications)}")
        
        # 알림 생성 확인
        self.assertEqual(len(open_notifications), 1)
        
        # 알림 내용 확인
        open_notification = open_notifications[0]
        self.assertEqual(open_notification.type, NotificationType.TRADE_ALERT)
        self.assertEqual(open_notification.related_symbol, self.test_symbol)
        print(f"포지션 생성 알림: {open_notification.title} - {open_notification.message}")
        
        # 포지션 종료 알림
        closed_position = self.position_data.copy()
        closed_position["current_price"] = int(closed_position["entry_price"] * 1.05)
        closed_position["profit_loss"] = int(closed_position["entry_price"] * 0.05 * closed_position["quantity"])
        closed_position["profit_loss_percentage"] = 5.0
        
        self.trade_monitor.notify_position_closed(self.test_symbol, closed_position)
        
        # 포지션 종료 알림 확인
        close_notifications = self.alert_manager.get_notifications()
        print(f"포지션 종료 후 알림 개수: {len(close_notifications)}")
        
        # 알림 생성 확인
        self.assertEqual(len(close_notifications), 2)
        
        # 알림 내용 확인
        close_notification = close_notifications[0]
        self.assertEqual(close_notification.type, NotificationType.TRADE_ALERT)
        self.assertEqual(close_notification.related_symbol, self.test_symbol)
        print(f"포지션 종료 알림: {close_notification.title} - {close_notification.message}")
        
        print("포지션 변경 알림 테스트 완료")
    
    def test_multiple_notifications(self):
        """다중 알림 테스트"""
        print("다중 알림 테스트 시작")
        
        # 알림 관리자 초기화
        self.alert_manager = AlertManager()
        self.trade_monitor = TradeMonitor(self.alert_manager)
        
        # 여러 코인에 대한 포지션 생성
        symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        
        for symbol in symbols:
            position = self.position_data.copy()
            position["symbol"] = symbol
            self.trade_monitor.notify_position_opened(symbol, position)
        
        # 알림 개수 확인
        notifications = self.alert_manager.get_notifications()
        self.assertEqual(len(notifications), len(symbols))
        print(f"생성된 알림 개수: {len(notifications)}")
        
        # 각 코인별 알림 확인 (역순으로 저장되므로 인덱스 조정)
        for i, symbol in enumerate(reversed(symbols)):
            self.assertEqual(notifications[i].related_symbol, symbol)
            print(f"{symbol} 알림: {notifications[i].title} - {notifications[i].message}")
        
        print("다중 알림 테스트 완료")
    
    def test_notification_settings(self):
        """알림 설정 테스트"""
        print("알림 설정 테스트 시작")
        
        # 알림 관리자 초기화
        self.alert_manager = AlertManager()
        self.trade_monitor = TradeMonitor(self.alert_manager)
        
        # 기본 설정 확인
        self.assertTrue(self.trade_monitor.is_order_notification_enabled())
        self.assertTrue(self.trade_monitor.is_profit_loss_notification_enabled())
        self.assertTrue(self.trade_monitor.is_position_notification_enabled())
        
        # 주문 알림 비활성화
        self.trade_monitor.set_order_notification_enabled(False)
        self.assertFalse(self.trade_monitor.is_order_notification_enabled())
        
        # 주문 체결 시 알림이 생성되지 않아야 함
        executed_order = self.order_data.copy()
        executed_order["state"] = "done"
        
        # 주문 상태 업데이트 및 알림 생성 시도
        self.trade_monitor.update_order_status(executed_order["uuid"], executed_order)
        
        # 알림이 생성되지 않았는지 확인
        notifications = self.alert_manager.get_notifications()
        self.assertEqual(len(notifications), 0)
        print("주문 알림 비활성화 테스트 완료")
        
        # 주문 알림 다시 활성화
        self.trade_monitor.set_order_notification_enabled(True)
        self.assertTrue(self.trade_monitor.is_order_notification_enabled())
        
        # 주문 체결 시 알림이 생성되어야 함
        # 이전 주문 상태를 wait로 변경하여 done으로 변경 시 알림이 발생하도록 함
        wait_order = self.order_data.copy()
        wait_order["state"] = "wait"
        self.trade_monitor.add_order_to_monitor(wait_order["uuid"], wait_order)
        
        # 주문 상태 업데이트 및 알림 생성 시도
        self.trade_monitor.update_order_status(executed_order["uuid"], executed_order)
        
        # 알림이 생성되었는지 확인
        notifications = self.alert_manager.get_notifications()
        self.assertEqual(len(notifications), 1)
        print("주문 알림 활성화 테스트 완료")
        
        print("알림 설정 테스트 완료")


if __name__ == "__main__":
    unittest.main()