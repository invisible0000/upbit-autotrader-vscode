#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
upbit_auto_trading.business_logic.trader.order_manager

주문 실행 및 관리 기능을 위한 클래스 정의.
"""
class Order:
    def __init__(self, symbol, side, amount, price):
        self.symbol = symbol
        self.side = side
        self.amount = amount
        self.price = price
        self.status = "created"
    def __repr__(self):
        return (f"Order(symbol={self.symbol}, side={self.side}, amount={self.amount}, "
                f"price={self.price}, status={self.status})")

class OrderManager:
    def create_order(self, symbol, side, amount, price):
        return Order(symbol, side, amount, price)
    def send_order(self, order):
        order.status = "sent"
        return True
    def cancel_order(self, order):
        if order.status == "sent":
            order.status = "cancelled"
            return True
        return False
    def modify_order(self, order, price=None, amount=None):
        if order.status == "sent":
            if price is not None:
                order.price = price
            if amount is not None:
                order.amount = amount
            return True
        return False
