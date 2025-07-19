#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
upbit_auto_trading.tests.unit.test_10_5_trading_state

거래 상태 관리 기능에 대한 단위 테스트.
- 포지션 추적, 수익/손실 계산, 거래 내역 기록 기능을 테스트합니다.
"""
import unittest
from upbit_auto_trading.business_logic.trader.trading_state import TradingState

class TestTradingState(unittest.TestCase):
    def setUp(self):
        print("Setting up for a new test...")
    def tearDown(self):
        print("Tearing down the test.")

    def test_position_tracking(self):
        """포지션 추적 테스트."""
        state = TradingState()
        state.update_position("KRW-BTC", 0.05)
        self.assertEqual(state.positions["KRW-BTC"], 0.05)
        print(f"포지션: {state.positions}")

    def test_pnl_calculation(self):
        """수익/손실 계산 테스트."""
        state = TradingState()
        state.update_position("KRW-BTC", 0.05)
        state.update_entry_price("KRW-BTC", 50000000)
        pnl = state.calculate_pnl("KRW-BTC", 51000000)
        self.assertEqual(pnl, 0.05 * (51000000 - 50000000))
        print(f"PNL: {pnl}")

    def test_trade_history(self):
        """거래 내역 기록 테스트."""
        state = TradingState()
        state.record_trade("KRW-BTC", "buy", 0.05, 50000000)
        self.assertEqual(len(state.trade_history), 1)
        print(f"거래 내역: {state.trade_history}")

if __name__ == '__main__':
    unittest.main()
