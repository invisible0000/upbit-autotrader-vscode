#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
upbit_auto_trading.business_logic.trader.trading_state

거래 상태 관리 기능을 위한 클래스 정의.
"""
class TradingState:
    def __init__(self):
        self.positions = {}
        self.entry_prices = {}
        self.trade_history = []
    def update_position(self, symbol, amount):
        self.positions[symbol] = amount
    def update_entry_price(self, symbol, price):
        self.entry_prices[symbol] = price
    def calculate_pnl(self, symbol, current_price):
        if symbol in self.positions and symbol in self.entry_prices:
            return self.positions[symbol] * (current_price - self.entry_prices[symbol])
        return 0
    def record_trade(self, symbol, side, amount, price):
        self.trade_history.append({
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price
        })

    def get_position(self, symbol):
        return self.positions.get(symbol, 0)

    def get_entry_price(self, symbol):
        return self.entry_prices.get(symbol, 0)
