#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
upbit_auto_trading.tests.unit.test_10_3_market_monitoring

실시간 시장 모니터링 기능에 대한 단위 테스트.
- 실시간 가격 변동, 거래량, 주요 이벤트 감지 기능을 테스트합니다.
"""
import unittest
from upbit_auto_trading.business_logic.monitoring.market_monitor import MarketMonitor

class TestMarketMonitor(unittest.TestCase):
    def setUp(self):
        print("Setting up for a new test...")
    def tearDown(self):
        print("Tearing down the test.")

    def test_initialization(self):
        """시장 모니터 객체 초기화 테스트."""
        monitor = MarketMonitor(["KRW-BTC", "KRW-ETH"])
        self.assertEqual(monitor.coins, ["KRW-BTC", "KRW-ETH"])
        print(f"초기화된 모니터: {monitor}")

    def test_update_market_data(self):
        """시장 데이터 갱신 테스트."""
        monitor = MarketMonitor(["KRW-BTC"])
        monitor.update_market_data("KRW-BTC", price=50000000, volume=100.5)
        self.assertEqual(monitor.market_data["KRW-BTC"]["price"], 50000000)
        self.assertEqual(monitor.market_data["KRW-BTC"]["volume"], 100.5)
        print(f"시장 데이터: {monitor.market_data}")

    def test_detect_event(self):
        """주요 이벤트 감지 테스트."""
        monitor = MarketMonitor(["KRW-BTC"])
        monitor.update_market_data("KRW-BTC", price=50000000, volume=100.5)
        event = monitor.detect_event("KRW-BTC")
        self.assertIn(event, ["price_spike", "normal"])
        print(f"감지된 이벤트: {event}")

if __name__ == '__main__':
    unittest.main()
