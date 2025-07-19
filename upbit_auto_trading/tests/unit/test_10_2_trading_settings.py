#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
upbit_auto_trading.tests.unit.test_10_2_trading_settings

거래 설정 관리 기능에 대한 단위 테스트.
- 거래 설정 객체의 생성, 변경, 검증 기능을 테스트합니다.
"""
import unittest
from upbit_auto_trading.business_logic.trader.trading_settings import TradingSettings

class TestTradingSettings(unittest.TestCase):
    def setUp(self):
        print("Setting up for a new test...")
    def tearDown(self):
        print("Tearing down the test.")

    def test_initialization(self):
        """거래 설정 객체 초기화 테스트."""
        settings = TradingSettings(
            max_trade_amount=100000,
            min_trade_amount=5000,
            allowed_coins=["KRW-BTC", "KRW-ETH"],
            risk_level="medium"
        )
        self.assertEqual(settings.max_trade_amount, 100000)
        self.assertEqual(settings.min_trade_amount, 5000)
        self.assertListEqual(settings.allowed_coins, ["KRW-BTC", "KRW-ETH"])
        self.assertEqual(settings.risk_level, "medium")
        print(f"초기화된 거래 설정: {settings}")

    def test_update_settings(self):
        """거래 설정 변경 테스트."""
        settings = TradingSettings(
            max_trade_amount=100000,
            min_trade_amount=5000,
            allowed_coins=["KRW-BTC"],
            risk_level="low"
        )
        settings.max_trade_amount = 200000
        settings.allowed_coins.append("KRW-ETH")
        settings.risk_level = "high"
        self.assertEqual(settings.max_trade_amount, 200000)
        self.assertListEqual(settings.allowed_coins, ["KRW-BTC", "KRW-ETH"])
        self.assertEqual(settings.risk_level, "high")
        print(f"변경된 거래 설정: {settings}")

    def test_validate_settings(self):
        """거래 설정 유효성 검증 테스트."""
        settings = TradingSettings(
            max_trade_amount=100000,
            min_trade_amount=5000,
            allowed_coins=["KRW-BTC"],
            risk_level="low"
        )
        self.assertTrue(settings.is_valid())
        settings.max_trade_amount = 0
        self.assertFalse(settings.is_valid())
        print(f"유효성 검증 결과: {settings.is_valid()}")

if __name__ == '__main__':
    unittest.main()
