#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
통합 E2E 테스트: 실시간 거래 시나리오 (모의 데이터 기반)
"""
import unittest
from unittest.mock import MagicMock
from upbit_auto_trading.business_logic.trader.trading_settings import TradingSettings
from upbit_auto_trading.business_logic.trader.order_manager import OrderManager
from upbit_auto_trading.business_logic.trader.trading_state import TradingState

class DummyWebSocket:
    def __init__(self, prices):
        self.prices = prices
        self.idx = 0
    async def recv(self):
        if self.idx < len(self.prices):
            price = self.prices[self.idx]
            self.idx += 1
            return {"symbol": "KRW-BTC", "trade_price": price}
        raise StopAsyncIteration

class TestE2ERealtimeTrade(unittest.TestCase):
    def setUp(self):
        print("실시간 거래 시나리오 테스트 시작...")
        self.settings = TradingSettings(
            max_trade_amount=100000,
            min_trade_amount=5000,
            allowed_coins=["KRW-BTC"],
            risk_level="medium"
        )
        self.manager = OrderManager()
        self.state = TradingState()
        # 모의 실시간 가격 데이터 (급등 조건 포함)
        self.mock_prices = [50000000, 50010000, 50050000, 50100000, 51000000]
        self.ws = DummyWebSocket(self.mock_prices)

    def test_realtime_trade_flow(self):
        """실시간 데이터 수신 → 조건 충족 시 자동 주문 → 포지션/상태 반영"""
        import asyncio
        async def run_flow():
            order_sent = False
            entry_price = None
            for _ in self.mock_prices:
                msg = await self.ws.recv()
                price = msg["trade_price"]
                # 거래 조건: 가격이 51000000 이상이면 매수
                if not order_sent and price >= 51000000:
                    order = self.manager.create_order("KRW-BTC", "buy", 0.01, price)
                    send_result = self.manager.send_order(order)
                    self.assertTrue(send_result)
                    self.assertEqual(order.status, "sent")
                    self.state.update_position("KRW-BTC", 0.01)
                    self.state.update_entry_price("KRW-BTC", price)
                    self.state.record_trade("KRW-BTC", "buy", 0.01, price)
                    entry_price = price
                    order_sent = True
            # PNL 계산 (마지막 가격 기준)
            if entry_price:
                pnl = self.state.calculate_pnl("KRW-BTC", self.mock_prices[-1])
                print(f"실시간 거래 성공, 진입가: {entry_price}, 최종 PNL: {pnl}")
                self.assertEqual(pnl, 0.01 * (self.mock_prices[-1] - entry_price))
            else:
                print("거래 조건 미충족, 주문 없음.")
                self.assertTrue(True)
        asyncio.run(run_flow())

    def tearDown(self):
        print("실시간 거래 시나리오 테스트 종료.")

if __name__ == '__main__':
    unittest.main()
