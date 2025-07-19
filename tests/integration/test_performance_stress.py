#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
통합 성능/스트레스 테스트: 대량 주문/데이터 처리 및 시스템 안정성 검증
"""
import unittest
import time
from upbit_auto_trading.business_logic.trader.order_manager import OrderManager
from upbit_auto_trading.business_logic.trader.trading_state import TradingState

class TestPerformanceStress(unittest.TestCase):
    def setUp(self):
        print("성능/스트레스 테스트 시작...")
        self.manager = OrderManager()
        self.state = TradingState()
        self.num_orders = 1000
        self.symbol = "KRW-BTC"
        self.price = 50000000
        self.amount = 0.01

    def test_bulk_order_performance(self):
        """1000건 주문 생성/전송/상태 관리 성능 측정"""
        start_time = time.time()
        for i in range(self.num_orders):
            order = self.manager.create_order(self.symbol, "buy", self.amount, self.price)
            send_result = self.manager.send_order(order)
            self.assertTrue(send_result)
            self.assertEqual(order.status, "sent")
            self.state.update_position(self.symbol, self.amount)
            self.state.update_entry_price(self.symbol, self.price)
            self.state.record_trade(self.symbol, "buy", self.amount, self.price)
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"1000건 주문 처리 시간: {elapsed:.3f}초")
        self.assertLess(elapsed, 5.0)  # 5초 이내 처리 기대
        self.assertEqual(len(self.state.trade_history), self.num_orders)

    def test_stress_order_handling(self):
        """과부하 상황에서 데이터 손실/오류 없는지 검증"""
        errors = 0
        for i in range(self.num_orders):
            try:
                order = self.manager.create_order(self.symbol, "buy", self.amount, self.price)
                self.manager.send_order(order)
                self.state.update_position(self.symbol, self.amount)
                self.state.update_entry_price(self.symbol, self.price)
                self.state.record_trade(self.symbol, "buy", self.amount, self.price)
            except Exception as e:
                errors += 1
        print(f"스트레스 테스트 오류 발생 건수: {errors}")
        self.assertEqual(errors, 0)
        self.assertEqual(len(self.state.trade_history), self.num_orders)

    def tearDown(self):
        print("성능/스트레스 테스트 종료.")

if __name__ == '__main__':
    unittest.main()
