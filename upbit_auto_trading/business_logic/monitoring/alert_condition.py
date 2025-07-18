"""
알림 조건 모듈

이 모듈은 다양한 유형의 알림 조건을 정의합니다.
- 가격 알림 조건
- 기술적 지표 알림 조건
- 패턴 인식 알림 조건
"""

import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


class AlertCondition(ABC):
    """알림 조건 기본 클래스"""
    
    def __init__(self, symbol: str, name: str):
        """초기화
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            name: 알림 조건 이름
        """
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.name = name
        self.created_at = datetime.now()
        self.last_triggered_at = None
        self.is_active = True
    
    @abstractmethod
    def check_condition(self, data: Dict[str, Any]) -> bool:
        """조건 검사
        
        Args:
            data: 검사할 데이터
            
        Returns:
            bool: 조건 충족 여부
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """알림 조건을 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 알림 조건 딕셔너리
        """
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "symbol": self.symbol,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "is_active": self.is_active
        }
    
    def update_last_triggered(self):
        """마지막 발생 시간 업데이트"""
        self.last_triggered_at = datetime.now()


class PriceAlertCondition(AlertCondition):
    """가격 알림 조건 클래스"""
    
    def __init__(self, symbol: str, price: float, is_above: bool, name: str):
        """초기화
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            price: 기준 가격
            is_above: True면 가격이 기준 이상일 때 알림, False면 가격이 기준 이하일 때 알림
            name: 알림 조건 이름
        """
        super().__init__(symbol, name)
        self.price = price
        self.is_above = is_above
    
    def check_condition(self, data: Dict[str, Any]) -> bool:
        """가격 조건 검사
        
        Args:
            data: 가격 데이터 (trade_price 필드 필요)
            
        Returns:
            bool: 조건 충족 여부
        """
        if "trade_price" not in data:
            return False
        
        current_price = data["trade_price"]
        
        if self.is_above:
            return current_price >= self.price
        else:
            return current_price <= self.price
    
    def to_dict(self) -> Dict[str, Any]:
        """알림 조건을 딕셔너리로 변환"""
        data = super().to_dict()
        data.update({
            "price": self.price,
            "is_above": self.is_above
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceAlertCondition':
        """딕셔너리에서 알림 조건 생성
        
        Args:
            data: 알림 조건 딕셔너리
            
        Returns:
            PriceAlertCondition: 생성된 알림 조건 객체
        """
        condition = cls(
            symbol=data["symbol"],
            price=data["price"],
            is_above=data["is_above"],
            name=data["name"]
        )
        condition.id = data["id"]
        condition.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("last_triggered_at"):
            condition.last_triggered_at = datetime.fromisoformat(data["last_triggered_at"])
        condition.is_active = data["is_active"]
        return condition


class IndicatorAlertCondition(AlertCondition):
    """기술적 지표 알림 조건 클래스"""
    
    def __init__(self, symbol: str, indicator_name: str, threshold: Union[float, str], 
                 comparison: str, name: str):
        """초기화
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            indicator_name: 지표 이름 (예: "rsi_14", "macd")
            threshold: 기준값 (숫자 또는 다른 지표 이름)
            comparison: 비교 연산자 (">", "<", ">=", "<=", "==")
            name: 알림 조건 이름
        """
        super().__init__(symbol, name)
        self.indicator_name = indicator_name
        self.threshold = threshold
        self.comparison = comparison
    
    def check_condition(self, data: Dict[str, Any]) -> bool:
        """지표 조건 검사
        
        Args:
            data: 지표 데이터
            
        Returns:
            bool: 조건 충족 여부
        """
        if self.indicator_name not in data:
            return False
        
        indicator_value = data[self.indicator_name]
        
        # 임계값이 다른 지표인 경우
        if isinstance(self.threshold, str) and self.threshold in data:
            threshold_value = data[self.threshold]
        else:
            threshold_value = self.threshold
        
        # 비교 연산 수행
        if self.comparison == ">":
            return indicator_value > threshold_value
        elif self.comparison == "<":
            return indicator_value < threshold_value
        elif self.comparison == ">=":
            return indicator_value >= threshold_value
        elif self.comparison == "<=":
            return indicator_value <= threshold_value
        elif self.comparison == "==":
            return indicator_value == threshold_value
        else:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """알림 조건을 딕셔너리로 변환"""
        data = super().to_dict()
        data.update({
            "indicator_name": self.indicator_name,
            "threshold": self.threshold,
            "comparison": self.comparison
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndicatorAlertCondition':
        """딕셔너리에서 알림 조건 생성"""
        condition = cls(
            symbol=data["symbol"],
            indicator_name=data["indicator_name"],
            threshold=data["threshold"],
            comparison=data["comparison"],
            name=data["name"]
        )
        condition.id = data["id"]
        condition.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("last_triggered_at"):
            condition.last_triggered_at = datetime.fromisoformat(data["last_triggered_at"])
        condition.is_active = data["is_active"]
        return condition


class PatternAlertCondition(AlertCondition):
    """패턴 인식 알림 조건 클래스"""
    
    def __init__(self, symbol: str, pattern_type: str, timeframe: str, 
                 min_candles: int, name: str):
        """초기화
        
        Args:
            symbol: 코인 심볼 (예: "KRW-BTC")
            pattern_type: 패턴 유형 (예: "uptrend", "downtrend", "double_top", "double_bottom")
            timeframe: 시간대 (예: "1m", "5m", "15m", "1h", "4h", "1d")
            min_candles: 패턴 인식에 필요한 최소 캔들 수
            name: 알림 조건 이름
        """
        super().__init__(symbol, name)
        self.pattern_type = pattern_type
        self.timeframe = timeframe
        self.min_candles = min_candles
    
    def check_condition(self, data: Dict[str, Any]) -> bool:
        """패턴 조건 검사
        
        Args:
            data: 캔들 데이터를 포함한 딕셔너리
            
        Returns:
            bool: 조건 충족 여부
        """
        if "candle_data" not in data:
            return False
        
        candle_data = data["candle_data"]
        return self.check_pattern(candle_data)
    
    def check_pattern(self, candles: List[Dict[str, Any]]) -> bool:
        """패턴 검사
        
        Args:
            candles: 캔들 데이터 목록
            
        Returns:
            bool: 패턴 인식 여부
        """
        if len(candles) < self.min_candles:
            return False
        
        # 패턴 유형에 따른 검사
        if self.pattern_type == "uptrend":
            return self._check_uptrend(candles)
        elif self.pattern_type == "downtrend":
            return self._check_downtrend(candles)
        elif self.pattern_type == "double_top":
            return self._check_double_top(candles)
        elif self.pattern_type == "double_bottom":
            return self._check_double_bottom(candles)
        else:
            return False
    
    def _check_uptrend(self, candles: List[Dict[str, Any]]) -> bool:
        """상승 추세 검사
        
        Args:
            candles: 캔들 데이터 목록
            
        Returns:
            bool: 상승 추세 여부
        """
        # 간단한 구현: 연속적으로 종가가 상승하는지 확인
        for i in range(1, len(candles)):
            if candles[i]["trade_price"] <= candles[i-1]["trade_price"]:
                return False
        return True
    
    def _check_downtrend(self, candles: List[Dict[str, Any]]) -> bool:
        """하락 추세 검사
        
        Args:
            candles: 캔들 데이터 목록
            
        Returns:
            bool: 하락 추세 여부
        """
        # 간단한 구현: 연속적으로 종가가 하락하는지 확인
        for i in range(1, len(candles)):
            if candles[i]["trade_price"] >= candles[i-1]["trade_price"]:
                return False
        return True
    
    def _check_double_top(self, candles: List[Dict[str, Any]]) -> bool:
        """더블 탑 패턴 검사
        
        Args:
            candles: 캔들 데이터 목록
            
        Returns:
            bool: 더블 탑 패턴 여부
        """
        # 실제 구현에서는 더 복잡한 알고리즘 필요
        # 여기서는 간단한 예시만 제공
        return False
    
    def _check_double_bottom(self, candles: List[Dict[str, Any]]) -> bool:
        """더블 바텀 패턴 검사
        
        Args:
            candles: 캔들 데이터 목록
            
        Returns:
            bool: 더블 바텀 패턴 여부
        """
        # 실제 구현에서는 더 복잡한 알고리즘 필요
        # 여기서는 간단한 예시만 제공
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """알림 조건을 딕셔너리로 변환"""
        data = super().to_dict()
        data.update({
            "pattern_type": self.pattern_type,
            "timeframe": self.timeframe,
            "min_candles": self.min_candles
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PatternAlertCondition':
        """딕셔너리에서 알림 조건 생성"""
        condition = cls(
            symbol=data["symbol"],
            pattern_type=data["pattern_type"],
            timeframe=data["timeframe"],
            min_candles=data["min_candles"],
            name=data["name"]
        )
        condition.id = data["id"]
        condition.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("last_triggered_at"):
            condition.last_triggered_at = datetime.fromisoformat(data["last_triggered_at"])
        condition.is_active = data["is_active"]
        return condition