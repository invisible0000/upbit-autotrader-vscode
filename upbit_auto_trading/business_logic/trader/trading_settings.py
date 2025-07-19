#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
upbit_auto_trading.business_logic.trader.trading_settings

거래 설정 관리 기능을 위한 클래스 정의.
"""
class TradingSettings:
    def __init__(self, max_trade_amount, min_trade_amount, allowed_coins, risk_level):
        self.max_trade_amount = max_trade_amount
        self.min_trade_amount = min_trade_amount
        self.allowed_coins = allowed_coins
        self.risk_level = risk_level
    def __repr__(self):
        return (f"TradingSettings(max_trade_amount={self.max_trade_amount}, "
                f"min_trade_amount={self.min_trade_amount}, "
                f"allowed_coins={self.allowed_coins}, "
                f"risk_level='{self.risk_level}')")
    def is_valid(self):
        # 간단한 유효성 검증: 최대 거래금액이 0보다 크고, 최소 거래금액이 0보다 크며, 코인 리스트가 비어있지 않아야 함
        return (
            self.max_trade_amount > 0 and
            self.min_trade_amount > 0 and
            isinstance(self.allowed_coins, list) and len(self.allowed_coins) > 0 and
            self.risk_level in ["low", "medium", "high"]
        )
