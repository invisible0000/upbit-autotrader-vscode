"""
시장 데이터 제공자 모듈

이 모듈은 시장 데이터 제공 기능을 정의합니다.
- 시장 데이터 제공 인터페이스
- 업비트 시장 데이터 제공자 구현
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import time
import threading

# 데이터 계층 모듈 임포트
from upbit_auto_trading.data_layer.upbit_api import UpbitAPI
from upbit_auto_trading.data_layer.data_processor import DataProcessor


class MarketDataProvider(ABC):
    """시장 데이터 제공자 인터페이스"""
    
    @abstractmethod
    def get_market_data(self) -> Dict[str, Dict[str, Any]]:
        """시장 데이터 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 심볼별 시장 데이터
        """
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[str]:
        """모니터링 대상 심볼 목록 조회
        
        Returns:
            List[str]: 심볼 목록
        """
        pass
    
    @abstractmethod
    def add_symbol(self, symbol: str) -> bool:
        """모니터링 대상 심볼 추가
        
        Args:
            symbol: 코인 심볼
            
        Returns:
            bool: 성공 여부
        """
        pass
    
    @abstractmethod
    def remove_symbol(self, symbol: str) -> bool:
        """모니터링 대상 심볼 제거
        
        Args:
            symbol: 코인 심볼
            
        Returns:
            bool: 성공 여부
        """
        pass


class UpbitMarketDataProvider(MarketDataProvider):
    """업비트 시장 데이터 제공자"""
    
    def __init__(self, update_interval: int = 10):
        """초기화
        
        Args:
            update_interval: 데이터 업데이트 간격 (초)
        """
        self.upbit_api = UpbitAPI()
        self.data_processor = DataProcessor()
        self.symbols = []
        self.market_data = {}
        self.update_interval = update_interval
        self.last_update_time = {}
        self.update_thread = None
        self.is_updating = False
        self.lock = threading.Lock()
    
    def get_market_data(self) -> Dict[str, Dict[str, Any]]:
        """시장 데이터 조회"""
        with self.lock:
            return self.market_data.copy()
    
    def get_symbols(self) -> List[str]:
        """모니터링 대상 심볼 목록 조회"""
        return self.symbols.copy()
    
    def add_symbol(self, symbol: str) -> bool:
        """모니터링 대상 심볼 추가"""
        if symbol in self.symbols:
            return False
        
        self.symbols.append(symbol)
        return True
    
    def remove_symbol(self, symbol: str) -> bool:
        """모니터링 대상 심볼 제거"""
        if symbol not in self.symbols:
            return False
        
        self.symbols.remove(symbol)
        with self.lock:
            if symbol in self.market_data:
                del self.market_data[symbol]
        
        return True
    
    def start_updating(self):
        """데이터 업데이트 시작"""
        if self.is_updating:
            return
        
        self.is_updating = True
        
        def update_task():
            while self.is_updating:
                try:
                    self._update_market_data()
                except Exception as e:
                    print(f"시장 데이터 업데이트 중 오류 발생: {e}")
                
                time.sleep(self.update_interval)
        
        self.update_thread = threading.Thread(target=update_task, daemon=True)
        self.update_thread.start()
    
    def stop_updating(self):
        """데이터 업데이트 중지"""
        self.is_updating = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
    
    def _update_market_data(self):
        """시장 데이터 업데이트"""
        current_time = time.time()
        
        for symbol in self.symbols:
            # 마지막 업데이트 이후 일정 시간이 지났는지 확인
            if symbol in self.last_update_time and \
               current_time - self.last_update_time[symbol] < self.update_interval:
                continue
            
            try:
                # 가격 데이터 조회
                ticker = self.upbit_api.get_ticker(symbol)
                if not ticker:
                    continue
                
                # 캔들 데이터 조회 (최근 10개)
                candles = self.upbit_api.get_candles(symbol, interval="minute1", count=10)
                
                # 기술적 지표 계산
                indicator_data = {}
                if candles:
                    indicator_data = self.data_processor.calculate_indicators(candles)
                
                # 시장 데이터 업데이트
                with self.lock:
                    self.market_data[symbol] = {
                        "price_data": ticker,
                        "indicator_data": indicator_data,
                        "candle_data": candles
                    }
                
                # 마지막 업데이트 시간 기록
                self.last_update_time[symbol] = current_time
                
            except Exception as e:
                print(f"{symbol} 데이터 업데이트 중 오류 발생: {e}")
    
    def set_update_interval(self, interval: int):
        """업데이트 간격 설정
        
        Args:
            interval: 업데이트 간격 (초)
        """
        self.update_interval = max(1, interval)  # 최소 1초