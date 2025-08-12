"""
거래 데이터 제공자 모듈

이 모듈은 거래 데이터 제공 기능을 정의합니다.
- 거래 데이터 제공 인터페이스
- 업비트 거래 데이터 제공자 구현
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import time
import threading

# 데이터 계층 모듈 임포트
from upbit_auto_trading.data_layer.upbit_api import UpbitAPI

class TradeDataProvider(ABC):
    """거래 데이터 제공자 인터페이스"""
    
    @abstractmethod
    def get_orders(self) -> Dict[str, Dict[str, Any]]:
        """주문 데이터 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 주문 ID별 주문 데이터
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """포지션 데이터 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 심볼별 포지션 데이터
        """
        pass
    
    @abstractmethod
    def get_trades(self) -> List[Dict[str, Any]]:
        """체결 내역 조회
        
        Returns:
            List[Dict[str, Any]]: 체결 내역 목록
        """
        pass

class UpbitTradeDataProvider(TradeDataProvider):
    """업비트 거래 데이터 제공자"""
    
    def __init__(self, update_interval: int = 10):
        """초기화
        
        Args:
            update_interval: 데이터 업데이트 간격 (초)
        """
        self.upbit_api = UpbitAPI()
        self.orders = {}
        self.positions = {}
        self.trades = []
        self.update_interval = update_interval
        self.last_update_time = 0
        self.update_thread = None
        self.is_updating = False
        self.lock = threading.Lock()
    
    def get_orders(self) -> Dict[str, Dict[str, Any]]:
        """주문 데이터 조회"""
        with self.lock:
            return self.orders.copy()
    
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """포지션 데이터 조회"""
        with self.lock:
            return self.positions.copy()
    
    def get_trades(self) -> List[Dict[str, Any]]:
        """체결 내역 조회"""
        with self.lock:
            return self.trades.copy()
    
    def start_updating(self):
        """데이터 업데이트 시작"""
        if self.is_updating:
            return
        
        self.is_updating = True
        
        def update_task():
            while self.is_updating:
                try:
                    self._update_trade_data()
                except Exception as e:
                    print(f"거래 데이터 업데이트 중 오류 발생: {e}")
                
                time.sleep(self.update_interval)
        
        self.update_thread = threading.Thread(target=update_task, daemon=True)
        self.update_thread.start()
    
    def stop_updating(self):
        """데이터 업데이트 중지"""
        self.is_updating = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
    
    def _update_trade_data(self):
        """거래 데이터 업데이트"""
        current_time = time.time()
        
        # 마지막 업데이트 이후 일정 시간이 지났는지 확인
        if current_time - self.last_update_time < self.update_interval:
            return
        
        try:
            # 주문 내역 조회
            orders = self.upbit_api.get_orders()
            
            # 잔고 조회
            balances = self.upbit_api.get_balances()
            
            # 체결 내역 조회
            trades = self.upbit_api.get_trades()
            
            # 데이터 업데이트
            with self.lock:
                # 주문 데이터 업데이트
                self.orders = {}
                for order in orders:
                    self.orders[order["uuid"]] = order
                
                # 포지션 데이터 업데이트
                self.positions = {}
                for balance in balances:
                    if float(balance["balance"]) > 0:
                        symbol = f"KRW-{balance['currency']}"
                        if symbol == "KRW-KRW":
                            continue
                        
                        # 현재가 조회
                        ticker = self.upbit_api.get_ticker(symbol)
                        if not ticker:
                            continue
                        
                        current_price = ticker["trade_price"]
                        avg_buy_price = float(balance.get("avg_buy_price", 0))
                        quantity = float(balance["balance"])
                        
                        # 수익/손실 계산
                        if avg_buy_price > 0:
                            profit_loss = (current_price - avg_buy_price) * quantity
                            profit_loss_percentage = (current_price - avg_buy_price) / avg_buy_price * 100
                        else:
                            profit_loss = 0
                            profit_loss_percentage = 0
                        
                        self.positions[symbol] = {
                            "symbol": symbol,
                            "side": "long",  # 업비트는 현물 거래만 지원하므로 항상 long
                            "entry_price": avg_buy_price,
                            "current_price": current_price,
                            "quantity": quantity,
                            "profit_loss": profit_loss,
                            "profit_loss_percentage": profit_loss_percentage,
                            "entry_time": None  # 업비트 API에서는 진입 시간 정보를 제공하지 않음
                        }
                
                # 체결 내역 업데이트
                self.trades = trades
            
            # 마지막 업데이트 시간 기록
            self.last_update_time = current_time
            
        except Exception as e:
            print(f"거래 데이터 업데이트 중 오류 발생: {e}")
    
    def set_update_interval(self, interval: int):
        """업데이트 간격 설정
        
        Args:
            interval: 업데이트 간격 (초)
        """
        self.update_interval = max(1, interval)  # 최소 1초