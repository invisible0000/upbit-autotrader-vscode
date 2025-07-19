#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
멀티코인 엔드투엔드 통합 테스트: 여러 코인 동시 거래/모니터링/포지션/PNL 검증
"""
import unittest
from upbit_auto_trading.business_logic.trader.order_manager import OrderManager
from upbit_auto_trading.business_logic.trader.trading_state import TradingState

class TestE2EMultiCoin(unittest.TestCase):
    def setUp(self):
        print("멀티코인 E2E 테스트 시작...")
        self.manager = OrderManager()
        self.state = TradingState()
        self.symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        self.prices = {"KRW-BTC": 50000000, "KRW-ETH": 3500000, "KRW-XRP": 800}
        self.amounts = {"KRW-BTC": 0.01, "KRW-ETH": 0.1, "KRW-XRP": 100}

    def test_multicoin_trading_flow(self):
        """각 코인별 주문/포지션/PNL 동시 검증"""
        for symbol in self.symbols:
            order = self.manager.create_order(symbol, "buy", self.amounts[symbol], self.prices[symbol])
            send_result = self.manager.send_order(order)
            self.assertTrue(send_result)
            self.assertEqual(order.status, "sent")
            self.state.update_position(symbol, self.amounts[symbol])
            self.state.update_entry_price(symbol, self.prices[symbol])
            self.state.record_trade(symbol, "buy", self.amounts[symbol], self.prices[symbol])
        # 포지션/PNL 검증
        for symbol in self.symbols:
            pos = self.state.get_position(symbol)
            entry = self.state.get_entry_price(symbol)
            self.assertEqual(pos, self.amounts[symbol])
            self.assertEqual(entry, self.prices[symbol])
            pnl = self.state.calculate_pnl(symbol, self.prices[symbol] * 1.05)  # 5% 상승 가정
            print(f"{symbol} 포지션: {pos}, 진입가: {entry}, PNL(5% 상승): {pnl}")
            self.assertGreater(pnl, 0)
        self.assertEqual(len(self.state.trade_history), len(self.symbols))

    def tearDown(self):
        print("멀티코인 E2E 테스트 종료.")

if __name__ == '__main__':
    unittest.main()
