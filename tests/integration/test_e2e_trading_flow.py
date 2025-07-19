#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
통합 엔드투엔드(E2E) 테스트: 전체 거래 플로우 시나리오 자동 검증
"""
import unittest
from upbit_auto_trading.business_logic.trader.trading_settings import TradingSettings
from upbit_auto_trading.business_logic.trader.order_manager import OrderManager
from upbit_auto_trading.business_logic.trader.trading_state import TradingState

class TestE2ETradingFlow(unittest.TestCase):
    def setUp(self):
        print("E2E 테스트 시작: 거래 환경 초기화...")
        self.settings = TradingSettings(
            max_trade_amount=100000,
            min_trade_amount=5000,
            allowed_coins=["KRW-BTC"],
            risk_level="medium"
        )
        self.manager = OrderManager()
        self.state = TradingState()

    def test_full_trading_flow(self):
        """거래 설정 → 주문 생성/전송 → 포지션/상태 관리까지 전체 플로우 검증"""
        # 거래 설정 확인
        self.assertTrue(self.settings.is_valid())
        # 주문 생성 및 전송
        order = self.manager.create_order("KRW-BTC", "buy", 0.01, 50000000)
        send_result = self.manager.send_order(order)
        self.assertTrue(send_result)
        self.assertEqual(order.status, "sent")
        # 포지션/상태 반영
        self.state.update_position("KRW-BTC", 0.01)
        self.state.update_entry_price("KRW-BTC", 50000000)
        self.state.record_trade("KRW-BTC", "buy", 0.01, 50000000)
        # PNL 계산
        pnl = self.state.calculate_pnl("KRW-BTC", 51000000)
        self.assertEqual(pnl, 0.01 * (51000000 - 50000000))
        print(f"E2E 거래 플로우 성공, PNL: {pnl}")

    def tearDown(self):
        print("E2E 테스트 종료.")

if __name__ == '__main__':
    unittest.main()
