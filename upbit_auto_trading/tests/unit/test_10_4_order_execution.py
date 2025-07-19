#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
upbit_auto_trading.tests.unit.test_10_4_order_execution

주문 실행 및 관리 기능에 대한 단위 테스트.
- 주문 생성, 전송, 상태 추적, 취소/수정 기능을 테스트합니다.
"""
import unittest
from upbit_auto_trading.business_logic.trader.order_manager import OrderManager, Order

class TestOrderExecution(unittest.TestCase):
    def setUp(self):
        print("Setting up for a new test...")
    def tearDown(self):
        print("Tearing down the test.")

    def test_create_order(self):
        """주문 생성 테스트."""
        manager = OrderManager()
        order = manager.create_order("KRW-BTC", "buy", 0.01, 50000000)
        self.assertIsInstance(order, Order)
        self.assertEqual(order.symbol, "KRW-BTC")
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.amount, 0.01)
        self.assertEqual(order.price, 50000000)
        print(f"생성된 주문: {order}")

    def test_send_order(self):
        """주문 전송 테스트."""
        manager = OrderManager()
        order = manager.create_order("KRW-BTC", "buy", 0.01, 50000000)
        result = manager.send_order(order)
        self.assertTrue(result)
        self.assertEqual(order.status, "sent")
        print(f"전송된 주문: {order}")

    def test_cancel_order(self):
        """주문 취소 테스트."""
        manager = OrderManager()
        order = manager.create_order("KRW-BTC", "buy", 0.01, 50000000)
        manager.send_order(order)
        result = manager.cancel_order(order)
        self.assertTrue(result)
        self.assertEqual(order.status, "cancelled")
        print(f"취소된 주문: {order}")

    def test_modify_order(self):
        """주문 수정 테스트."""
        manager = OrderManager()
        order = manager.create_order("KRW-BTC", "buy", 0.01, 50000000)
        manager.send_order(order)
        result = manager.modify_order(order, price=51000000, amount=0.02)
        self.assertTrue(result)
        self.assertEqual(order.price, 51000000)
        self.assertEqual(order.amount, 0.02)
        print(f"수정된 주문: {order}")

if __name__ == '__main__':
    unittest.main()
