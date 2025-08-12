"""
역할 기반 전략 시스템

진입 전략(Entry Strategy)과 관리 전략(Management Strategy)을 명확히 분리한 새로운 전략 구조입니다.

이 모듈은 다음과 같은 전략 역할을 정의합니다:
- 진입 전략: 포지션이 없을 때 최초 진입 신호 생성
- 관리 전략: 포지션이 있을 때 리스크 관리 및 수익 최적화
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StrategyRole(Enum):
    """전략 역할 분류"""
    ENTRY = "entry"         # 진입 전략
    MANAGEMENT = "management"  # 관리 전략

class SignalType(Enum):
    """신호 타입 분류"""
    # 진입 신호
    BUY = "BUY"
    SELL = "SELL"  
    HOLD = "HOLD"
    
    # 관리 신호
    ADD_BUY = "ADD_BUY"        # 추가 매수 (물타기/불타기)
    ADD_SELL = "ADD_SELL"      # 부분 매도
    CLOSE_POSITION = "CLOSE_POSITION"  # 전체 청산
    UPDATE_STOP = "UPDATE_STOP"        # 스탑 가격 업데이트

@dataclass
class PositionInfo:
    """포지션 정보"""
    direction: str          # "LONG" | "SHORT"
    entry_price: float      # 진입 가격
    entry_time: datetime    # 진입 시간
    quantity: float         # 수량
    stop_price: Optional[float] = None  # 스탑 가격
    unrealized_pnl: float = 0.0        # 미실현 손익
    management_history: List[Dict] = None  # 관리 이력
    
    def __post_init__(self):
        if self.management_history is None:
            self.management_history = []

@dataclass
class TradingSignal:
    """매매 신호 데이터"""
    signal_type: SignalType
    timestamp: datetime
    price: float
    quantity: Optional[float] = None    # 수량 (관리 전략용)
    stop_price: Optional[float] = None  # 스탑 가격 (트레일링용)
    confidence: float = 1.0             # 신호 신뢰도
    metadata: Dict[str, Any] = None     # 추가 정보
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseStrategy(ABC):
    """모든 전략의 기본 클래스"""
    
    def __init__(self, parameters: Dict[str, Any]):
        self.parameters = parameters.copy()
        self.name = self.__class__.__name__
        self.created_at = datetime.now()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 파라미터 유효성 검사
        if not self.validate_parameters(parameters):
            self.logger.warning("잘못된 파라미터, 기본값 사용")
            self.parameters = self.get_default_parameters()
    
    @abstractmethod
    def get_strategy_role(self) -> StrategyRole:
        """전략 역할 반환: 'entry' | 'management'"""
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """필요한 기술적 지표 목록"""
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """파라미터 유효성 검사"""
        pass
    
    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """기본 파라미터"""
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 기본 정보"""
        return {
            "name": self.name,
            "role": self.get_strategy_role().value,
            "parameters": self.parameters,
            "created_at": self.created_at
        }

class EntryStrategy(BaseStrategy):
    """진입 전략 기본 클래스
    
    역할: 포지션이 없는 상태에서 최초 진입 신호를 생성
    조건: 현재 포지션이 없을 때만 활성화
    출력: BUY, SELL, HOLD 신호
    """
    
    def get_strategy_role(self) -> StrategyRole:
        return StrategyRole.ENTRY
    
    @abstractmethod
    def generate_entry_signal(self, market_data: pd.DataFrame, 
                            position_status: Optional[PositionInfo] = None) -> TradingSignal:
        """진입 신호 생성
        
        Args:
            market_data: 시장 데이터 (OHLCV + 지표)
            position_status: 현재 포지션 상태 (None이면 포지션 없음)
            
        Returns:
            TradingSignal: BUY, SELL, HOLD 중 하나
        """
        pass
    
    def can_activate(self, position_status: Optional[PositionInfo]) -> bool:
        """진입 전략 활성화 조건: 포지션이 없을 때만"""
        return position_status is None

class ManagementStrategy(BaseStrategy):
    """관리 전략 기본 클래스
    
    역할: 이미 진입한 포지션의 리스크 관리 및 수익 극대화
    조건: 활성 포지션이 존재할 때만 활성화  
    출력: ADD_BUY, ADD_SELL, CLOSE_POSITION, UPDATE_STOP 신호
    """
    
    def get_strategy_role(self) -> StrategyRole:
        return StrategyRole.MANAGEMENT
    
    @abstractmethod
    def generate_management_signal(self, market_data: pd.DataFrame,
                                 position_info: PositionInfo) -> TradingSignal:
        """관리 신호 생성
        
        Args:
            market_data: 시장 데이터 (OHLCV + 지표)
            position_info: 현재 포지션 정보
            
        Returns:
            TradingSignal: ADD_BUY, ADD_SELL, CLOSE_POSITION, UPDATE_STOP, HOLD 중 하나
        """
        pass
    
    def can_activate(self, position_status: Optional[PositionInfo]) -> bool:
        """관리 전략 활성화 조건: 포지션이 있을 때만"""
        return position_status is not None
    
    def calculate_position_metrics(self, current_price: float, 
                                 position_info: PositionInfo) -> Dict[str, float]:
        """포지션 메트릭 계산 헬퍼"""
        if position_info.direction == "LONG":
            unrealized_pnl_pct = (current_price - position_info.entry_price) / position_info.entry_price * 100
        else:  # SHORT
            unrealized_pnl_pct = (position_info.entry_price - current_price) / position_info.entry_price * 100
            
        return {
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "unrealized_pnl_amount": unrealized_pnl_pct * position_info.quantity * position_info.entry_price / 100,
            "holding_time_hours": (datetime.now() - position_info.entry_time).total_seconds() / 3600
        }

# ============================================================================
# 진입 전략 구현체들 (6개)
# ============================================================================

class MovingAverageCrossEntry(EntryStrategy):
    """이동평균 교차 진입 전략
    
    전략적 역할: 진입 전략
    개념: 가격의 추세 방향을 부드럽게 보여주는 선으로, 단기선과 장기선의 교차를 통해 추세의 시작을 포착
    실제 사용: "1시간봉 차트에서 5 이평선이 20 이평선을 상향 돌파하는 '골든 크로스'가 발생하면 매수"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "short_period": 5,      # 단기 이평선 기간
            "long_period": 20,      # 장기 이평선 기간
            "ma_type": "SMA"        # "SMA" | "EMA"
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["short_period", "long_period"]
        if not all(key in parameters for key in required):
            return False
        
        short = parameters.get("short_period", 0)
        long = parameters.get("long_period", 0)
        
        return (isinstance(short, int) and isinstance(long, int) and 
                short > 0 and long > 0 and short < long)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        ma_type = self.parameters.get("ma_type", "SMA")
        return [
            {
                "name": ma_type,
                "params": {
                    "window": self.parameters["short_period"], 
                    "column": "close"
                }
            },
            {
                "name": ma_type,
                "params": {
                    "window": self.parameters["long_period"], 
                    "column": "close"
                }
            }
        ]
    
    def generate_entry_signal(self, market_data: pd.DataFrame, 
                            position_status: Optional[PositionInfo] = None) -> TradingSignal:
        """골든크로스/데드크로스 진입 신호"""
        if len(market_data) < 2:
            return TradingSignal(SignalType.HOLD, datetime.now(), market_data.iloc[-1]['close'])
        
        short_period = self.parameters["short_period"]
        long_period = self.parameters["long_period"]
        ma_type = self.parameters.get("ma_type", "SMA")
        
        short_col = f"{ma_type}_{short_period}"
        long_col = f"{ma_type}_{long_period}"
        
        current = market_data.iloc[-1]
        previous = market_data.iloc[-2]
        
        # 골든크로스: 단기선이 장기선을 상향 돌파
        if (previous[short_col] <= previous[long_col] and 
            current[short_col] > current[long_col]):
            return TradingSignal(
                SignalType.BUY, 
                datetime.now(), 
                current['close'],
                confidence=0.8,
                metadata={"pattern": "golden_cross"}
            )
        
        # 데드크로스: 단기선이 장기선을 하향 돌파  
        elif (previous[short_col] >= previous[long_col] and 
              current[short_col] < current[long_col]):
            return TradingSignal(
                SignalType.SELL, 
                datetime.now(), 
                current['close'],
                confidence=0.8,
                metadata={"pattern": "death_cross"}
            )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current['close'])

class RSIEntry(EntryStrategy):
    """RSI 과매수/과매도 진입 전략
    
    전략적 역할: 진입 전략
    개념: 가격의 상승 압력과 하락 압력 간의 상대적인 강도를 측정하여 과매수/과매도 상태를 판단
    실제 사용: "4시간봉 차트에서 RSI 지표가 30 미만(과매도)으로 떨어졌다가, 다시 30선을 상향 돌파하는 첫 번째 캔들의 종가에 매수"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "rsi_period": 14,       # RSI 계산 기간
            "oversold": 30,         # 과매도 기준
            "overbought": 70        # 과매수 기준
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["rsi_period", "oversold", "overbought"]
        if not all(key in parameters for key in required):
            return False
            
        period = parameters.get("rsi_period", 0)
        oversold = parameters.get("oversold", 0)
        overbought = parameters.get("overbought", 100)
        
        return (isinstance(period, int) and period > 0 and
                0 <= oversold < overbought <= 100)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "RSI",
                "params": {
                    "window": self.parameters["rsi_period"],
                    "column": "close"
                }
            }
        ]
    
    def generate_entry_signal(self, market_data: pd.DataFrame, 
                            position_status: Optional[PositionInfo] = None) -> TradingSignal:
        """RSI 과매도 반등/과매수 반락 진입 신호"""
        if len(market_data) < 2:
            return TradingSignal(SignalType.HOLD, datetime.now(), market_data.iloc[-1]['close'])
        
        rsi_period = self.parameters["rsi_period"]
        oversold = self.parameters["oversold"]
        overbought = self.parameters["overbought"]
        
        rsi_col = f"RSI_{rsi_period}"
        current = market_data.iloc[-1]
        previous = market_data.iloc[-2]
        
        # 과매도 구간에서 상향 돌파시 매수
        if (previous[rsi_col] < oversold and current[rsi_col] >= oversold):
            return TradingSignal(
                SignalType.BUY,
                datetime.now(),
                current['close'], 
                confidence=0.75,
                metadata={"rsi_value": current[rsi_col], "pattern": "oversold_reversal"}
            )
        
        # 과매수 구간에서 하향 돌파시 매도
        elif (previous[rsi_col] > overbought and current[rsi_col] <= overbought):
            return TradingSignal(
                SignalType.SELL,
                datetime.now(),
                current['close'],
                confidence=0.75, 
                metadata={"rsi_value": current[rsi_col], "pattern": "overbought_reversal"}
            )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current['close'])

class BollingerBandsEntry(EntryStrategy):
    """볼린저 밴드 진입 전략
    
    전략적 역할: 진입 전략  
    개념: 이동평균선을 중심으로 표준편차를 이용한 상하단 밴드를 만들어 가격의 상대적 고점과 저점을 판단
    실제 사용: "가격이 볼린저 밴드 하단을 강하게 뚫고 내려간 후, 다시 밴드 안으로 복귀하는 첫 번째 양봉 캔들에서 과매도 반등을 노리고 매수"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "period": 20,           # 중심선 기간
            "std_multiplier": 2.0,  # 표준편차 승수
            "entry_type": "reversal" # "reversal" | "breakout"
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["period", "std_multiplier"]
        if not all(key in parameters for key in required):
            return False
            
        period = parameters.get("period", 0)
        std_mult = parameters.get("std_multiplier", 0)
        
        return (isinstance(period, int) and period > 0 and
                isinstance(std_mult, (int, float)) and std_mult > 0)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "BBANDS",
                "params": {
                    "window": self.parameters["period"],
                    "std": self.parameters["std_multiplier"],
                    "column": "close"
                }
            }
        ]
    
    def generate_entry_signal(self, market_data: pd.DataFrame, 
                            position_status: Optional[PositionInfo] = None) -> TradingSignal:
        """볼린저 밴드 터치 후 반전 신호"""
        if len(market_data) < 2:
            return TradingSignal(SignalType.HOLD, datetime.now(), market_data.iloc[-1]['close'])
        
        period = self.parameters["period"]
        entry_type = self.parameters.get("entry_type", "reversal")
        
        upper_col = f"BBANDS_UPPER_{period}"
        lower_col = f"BBANDS_LOWER_{period}"
        
        current = market_data.iloc[-1]
        previous = market_data.iloc[-2]
        
        if entry_type == "reversal":
            # 하단 밴드 터치 후 복귀시 매수
            if (previous['close'] < previous[lower_col] and 
                current['close'] >= current[lower_col]):
                return TradingSignal(
                    SignalType.BUY,
                    datetime.now(),
                    current['close'],
                    confidence=0.7,
                    metadata={"pattern": "lower_band_reversal"}
                )
            
            # 상단 밴드 터치 후 복귀시 매도
            elif (previous['close'] > previous[upper_col] and 
                  current['close'] <= current[upper_col]):
                return TradingSignal(
                    SignalType.SELL,
                    datetime.now(), 
                    current['close'],
                    confidence=0.7,
                    metadata={"pattern": "upper_band_reversal"}
                )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current['close'])

class VolatilityBreakoutEntry(EntryStrategy):
    """변동성 돌파 진입 전략 (래리 윌리엄스)
    
    전략적 역할: 진입 전략
    개념: 일정 기간의 변동폭을 기준으로 돌파시 추세 시작으로 판단
    실제 사용: "전일 고가 + (전일 변동폭 * 0.5) 돌파시 매수, 전일 저가 - (전일 변동폭 * 0.5) 돌파시 매도"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "lookback_period": 1,   # 변동폭 계산 기간
            "k_value": 0.5,         # 돌파 계수
            "close_on_day_end": True # 당일 종가 청산 여부
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["lookback_period", "k_value"]
        if not all(key in parameters for key in required):
            return False
            
        period = parameters.get("lookback_period", 0)
        k_value = parameters.get("k_value", 0)
        
        return (isinstance(period, int) and period > 0 and
                isinstance(k_value, (int, float)) and 0 < k_value <= 1)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "HIGH_LOW_RANGE",
                "params": {
                    "window": self.parameters["lookback_period"]
                }
            }
        ]
    
    def generate_entry_signal(self, market_data: pd.DataFrame, 
                            position_status: Optional[PositionInfo] = None) -> TradingSignal:
        """변동성 돌파 진입 신호"""
        if len(market_data) < 2:
            return TradingSignal(SignalType.HOLD, datetime.now(), market_data.iloc[-1]['close'])
        
        k_value = self.parameters["k_value"]
        current = market_data.iloc[-1]
        previous = market_data.iloc[-2]
        
        # 전일 변동폭 계산
        prev_range = previous['high'] - previous['low']
        
        # 돌파 기준가 계산
        buy_trigger = previous['high'] + (prev_range * k_value)
        sell_trigger = previous['low'] - (prev_range * k_value)
        
        # 상향 돌파시 매수
        if current['close'] > buy_trigger:
            return TradingSignal(
                SignalType.BUY,
                datetime.now(),
                current['close'],
                confidence=0.8,
                metadata={"trigger_price": buy_trigger, "pattern": "volatility_breakout_up"}
            )
        
        # 하향 돌파시 매도
        elif current['close'] < sell_trigger:
            return TradingSignal(
                SignalType.SELL,
                datetime.now(),
                current['close'],
                confidence=0.8,
                metadata={"trigger_price": sell_trigger, "pattern": "volatility_breakout_down"}
            )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current['close'])

class MACDEntry(EntryStrategy):
    """MACD 진입 전략
    
    전략적 역할: 진입 전략
    개념: 두 이동평균선의 차이를 이용해 추세의 방향과 힘(모멘텀)의 변화를 파악
    실제 사용: "일봉 차트에서 MACD선이 시그널선을 상향 돌파하고, 동시에 MACD 오실레이터(막대)가 0선 위에 있을 때 매수"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "fast_period": 12,      # 빠른 EMA 기간
            "slow_period": 26,      # 느린 EMA 기간
            "signal_period": 9,     # 시그널 라인 기간
            "histogram_threshold": 0 # 히스토그램 임계값
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["fast_period", "slow_period", "signal_period"]
        if not all(key in parameters for key in required):
            return False
            
        fast = parameters.get("fast_period", 0)
        slow = parameters.get("slow_period", 0)
        signal = parameters.get("signal_period", 0)
        
        return (isinstance(fast, int) and isinstance(slow, int) and isinstance(signal, int) and
                fast > 0 and slow > 0 and signal > 0 and fast < slow)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "MACD",
                "params": {
                    "fast": self.parameters["fast_period"],
                    "slow": self.parameters["slow_period"],
                    "signal": self.parameters["signal_period"],
                    "column": "close"
                }
            }
        ]
    
    def generate_entry_signal(self, market_data: pd.DataFrame, 
                            position_status: Optional[PositionInfo] = None) -> TradingSignal:
        """MACD 교차 진입 신호"""
        if len(market_data) < 2:
            return TradingSignal(SignalType.HOLD, datetime.now(), market_data.iloc[-1]['close'])
        
        fast = self.parameters["fast_period"]
        slow = self.parameters["slow_period"]
        signal_period = self.parameters["signal_period"]
        hist_threshold = self.parameters.get("histogram_threshold", 0)
        
        macd_col = f"MACD_{fast}_{slow}"
        signal_col = f"MACD_SIGNAL_{signal_period}"
        hist_col = f"MACD_HIST_{fast}_{slow}_{signal_period}"
        
        current = market_data.iloc[-1]
        previous = market_data.iloc[-2]
        
        # MACD 라인이 시그널 라인을 상향 돌파 + 히스토그램이 임계값 이상
        if (previous[macd_col] <= previous[signal_col] and 
            current[macd_col] > current[signal_col] and 
            current[hist_col] > hist_threshold):
            return TradingSignal(
                SignalType.BUY,
                datetime.now(),
                current['close'],
                confidence=0.8,
                metadata={"macd_value": current[macd_col], "pattern": "macd_bullish_cross"}
            )
        
        # MACD 라인이 시그널 라인을 하향 돌파 + 히스토그램이 임계값 이하
        elif (previous[macd_col] >= previous[signal_col] and 
              current[macd_col] < current[signal_col] and 
              current[hist_col] < hist_threshold):
            return TradingSignal(
                SignalType.SELL,
                datetime.now(),
                current['close'],
                confidence=0.8,
                metadata={"macd_value": current[macd_col], "pattern": "macd_bearish_cross"}
            )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current['close'])

class StochasticEntry(EntryStrategy):
    """스토캐스틱 진입 전략
    
    전략적 역할: 진입 전략
    개념: 일정 기간의 가격 변동폭 내에서 현재 가격의 상대적인 위치를 나타냄
    실제 사용: "15분봉 차트에서 스토캐스틱 %K선이 20 미만(과매도)으로 하락했다가 %D선을 상향 돌파하는 '골든 크로스'가 발생하면 매수"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "k_period": 14,         # %K 기간
            "d_period": 3,          # %D 기간
            "oversold": 20,         # 과매도 기준
            "overbought": 80        # 과매수 기준
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["k_period", "d_period", "oversold", "overbought"]
        if not all(key in parameters for key in required):
            return False
            
        k_period = parameters.get("k_period", 0)
        d_period = parameters.get("d_period", 0)
        oversold = parameters.get("oversold", 0)
        overbought = parameters.get("overbought", 100)
        
        return (isinstance(k_period, int) and isinstance(d_period, int) and
                k_period > 0 and d_period > 0 and
                0 <= oversold < overbought <= 100)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "STOCH",
                "params": {
                    "k_period": self.parameters["k_period"],
                    "d_period": self.parameters["d_period"]
                }
            }
        ]
    
    def generate_entry_signal(self, market_data: pd.DataFrame, 
                            position_status: Optional[PositionInfo] = None) -> TradingSignal:
        """스토캐스틱 교차 진입 신호"""
        if len(market_data) < 2:
            return TradingSignal(SignalType.HOLD, datetime.now(), market_data.iloc[-1]['close'])
        
        k_period = self.parameters["k_period"]
        d_period = self.parameters["d_period"]
        oversold = self.parameters["oversold"]
        overbought = self.parameters["overbought"]
        
        k_col = f"STOCH_K_{k_period}"
        d_col = f"STOCH_D_{d_period}"
        
        current = market_data.iloc[-1]
        previous = market_data.iloc[-2]
        
        # 과매도 구간에서 %K가 %D를 상향 돌파시 매수
        if (current[k_col] < oversold and 
            previous[k_col] <= previous[d_col] and 
            current[k_col] > current[d_col]):
            return TradingSignal(
                SignalType.BUY,
                datetime.now(),
                current['close'],
                confidence=0.75,
                metadata={"k_value": current[k_col], "pattern": "stoch_bullish_cross_oversold"}
            )
        
        # 과매수 구간에서 %K가 %D를 하향 돌파시 매도
        elif (current[k_col] > overbought and 
              previous[k_col] >= previous[d_col] and 
              current[k_col] < current[d_col]):
            return TradingSignal(
                SignalType.SELL,
                datetime.now(),
                current['close'],
                confidence=0.75,
                metadata={"k_value": current[k_col], "pattern": "stoch_bearish_cross_overbought"}
            )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current['close'])

# ============================================================================
# 관리 전략 구현체들 (6개)
# ============================================================================

class AveragingDownManagement(ManagementStrategy):
    """물타기 관리 전략
    
    전략적 역할: 관리 전략
    개념: 하락 시 추가 매수로 평단가 낮추기
    실제 사용: "매수 포지션 진입 후 -5%마다 추가 매수를 최대 3번까지 실행, 절대 손절선 -30%"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "trigger_drop_percent": 5.0,          # 추가 매수 트리거 (%)
            "max_additional_buys": 3,             # 최대 추가 매수 횟수
            "additional_quantity_ratio": 1.0,     # 추가 매수 수량 비율
            "stop_loss_percent": -30.0            # 절대 손절선 (%)
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["trigger_drop_percent", "max_additional_buys", "stop_loss_percent"]
        if not all(key in parameters for key in required):
            return False
            
        trigger = parameters.get("trigger_drop_percent", 0)
        max_buys = parameters.get("max_additional_buys", 0)
        stop_loss = parameters.get("stop_loss_percent", 0)
        
        return (isinstance(trigger, (int, float)) and trigger > 0 and
                isinstance(max_buys, int) and max_buys >= 0 and
                isinstance(stop_loss, (int, float)) and stop_loss < 0)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return []  # 가격 기반 계산만 필요
    
    def generate_management_signal(self, market_data: pd.DataFrame,
                                 position_info: PositionInfo) -> TradingSignal:
        """물타기 관리 신호"""
        current_price = market_data.iloc[-1]['close']
        metrics = self.calculate_position_metrics(current_price, position_info)
        
        trigger_drop = self.parameters["trigger_drop_percent"]
        max_buys = self.parameters["max_additional_buys"]
        stop_loss = self.parameters["stop_loss_percent"]
        additional_ratio = self.parameters.get("additional_quantity_ratio", 1.0)
        
        # 절대 손절선 체크
        if metrics["unrealized_pnl_pct"] <= stop_loss:
            return TradingSignal(
                SignalType.CLOSE_POSITION,
                datetime.now(),
                current_price,
                quantity=position_info.quantity,
                metadata={"reason": "stop_loss", "pnl_pct": metrics["unrealized_pnl_pct"]}
            )
        
        # 추가 매수 이력 확인
        additional_buys = len([h for h in position_info.management_history 
                              if h.get('action') == 'ADD_BUY'])
        
        # 추가 매수 조건: 하락폭이 트리거에 도달하고 최대 횟수 미만
        if (additional_buys < max_buys and 
            metrics["unrealized_pnl_pct"] <= -trigger_drop * (additional_buys + 1)):
            
            additional_quantity = position_info.quantity * additional_ratio
            return TradingSignal(
                SignalType.ADD_BUY,
                datetime.now(),
                current_price,
                quantity=additional_quantity,
                metadata={
                    "averaging_down_count": additional_buys + 1,
                    "pnl_pct": metrics["unrealized_pnl_pct"]
                }
            )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current_price)

class PyramidingManagement(ManagementStrategy):
    """불타기 관리 전략
    
    전략적 역할: 관리 전략  
    개념: 상승 시 추가 매수로 수익 극대화
    실제 사용: "매수 포지션이 +3%씩 상승할 때마다 추가 매수를 최대 2번까지, 수량은 80%씩 감소"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "trigger_rise_percent": 3.0,          # 추가 매수 트리거 (%)
            "max_additional_buys": 2,             # 최대 추가 매수 횟수
            "quantity_decrease_ratio": 0.8,       # 수량 감소 비율
            "profit_protection": True             # 손익분기점 보호
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["trigger_rise_percent", "max_additional_buys"]
        if not all(key in parameters for key in required):
            return False
            
        trigger = parameters.get("trigger_rise_percent", 0)
        max_buys = parameters.get("max_additional_buys", 0)
        
        return (isinstance(trigger, (int, float)) and trigger > 0 and
                isinstance(max_buys, int) and max_buys >= 0)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return []
    
    def generate_management_signal(self, market_data: pd.DataFrame,
                                 position_info: PositionInfo) -> TradingSignal:
        """불타기 관리 신호"""
        current_price = market_data.iloc[-1]['close']
        metrics = self.calculate_position_metrics(current_price, position_info)
        
        trigger_rise = self.parameters["trigger_rise_percent"]
        max_buys = self.parameters["max_additional_buys"]
        decrease_ratio = self.parameters.get("quantity_decrease_ratio", 0.8)
        profit_protection = self.parameters.get("profit_protection", True)
        
        # 추가 매수 이력 확인
        additional_buys = len([h for h in position_info.management_history 
                              if h.get('action') == 'ADD_BUY'])
        
        # 추가 매수 조건: 상승폭이 트리거에 도달하고 최대 횟수 미만
        if (additional_buys < max_buys and 
            metrics["unrealized_pnl_pct"] >= trigger_rise * (additional_buys + 1)):
            
            # 수량은 기하급수적으로 감소
            additional_quantity = position_info.quantity * (decrease_ratio ** (additional_buys + 1))
            
            return TradingSignal(
                SignalType.ADD_BUY,
                datetime.now(),
                current_price,
                quantity=additional_quantity,
                metadata={
                    "pyramiding_count": additional_buys + 1,
                    "pnl_pct": metrics["unrealized_pnl_pct"]
                }
            )
        
        # 수익 보호: 손익분기점 아래로 떨어지면 전량 청산
        if profit_protection and additional_buys > 0 and metrics["unrealized_pnl_pct"] <= 0:
            return TradingSignal(
                SignalType.CLOSE_POSITION,
                datetime.now(),
                current_price,
                quantity=position_info.quantity,
                metadata={"reason": "profit_protection", "pnl_pct": metrics["unrealized_pnl_pct"]}
            )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current_price)

class TrailingStopManagement(ManagementStrategy):
    """트레일링 스탑 관리 전략
    
    전략적 역할: 관리 전략
    개념: 동적 손절가 조정으로 수익 보호
    실제 사용: "매수 포지션 진입 후, 가격이 PSAR 점 위에 있는 동안에는 계속 포지션을 유지. 가격이 PSAR 점을 하향 돌파하면 즉시 전량 매도"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "trailing_distance": 5.0,            # 추적 거리 (%)
            "activation_profit": 3.0,            # 활성화 최소 수익률 (%)
            "stop_type": "percentage"            # "percentage" | "atr"
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["trailing_distance", "activation_profit"]
        if not all(key in parameters for key in required):
            return False
            
        distance = parameters.get("trailing_distance", 0)
        activation = parameters.get("activation_profit", 0)
        
        return (isinstance(distance, (int, float)) and distance > 0 and
                isinstance(activation, (int, float)) and activation >= 0)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        stop_type = self.parameters.get("stop_type", "percentage")
        if stop_type == "atr":
            return [{"name": "ATR", "params": {"window": 14}}]
        return []
    
    def generate_management_signal(self, market_data: pd.DataFrame,
                                 position_info: PositionInfo) -> TradingSignal:
        """트레일링 스탑 관리 신호"""
        current_price = market_data.iloc[-1]['close']
        metrics = self.calculate_position_metrics(current_price, position_info)
        
        trailing_distance = self.parameters["trailing_distance"]
        activation_profit = self.parameters["activation_profit"]
        stop_type = self.parameters.get("stop_type", "percentage")
        
        # 활성화 조건: 최소 수익률 달성
        if metrics["unrealized_pnl_pct"] < activation_profit:
            return TradingSignal(SignalType.HOLD, datetime.now(), current_price)
        
        # 스탑 가격 계산
        if stop_type == "percentage":
            if position_info.direction == "LONG":
                new_stop_price = current_price * (1 - trailing_distance / 100)
            else:  # SHORT
                new_stop_price = current_price * (1 + trailing_distance / 100)
        else:  # ATR 기반
            atr_value = market_data.iloc[-1].get('ATR_14', current_price * 0.02)  # 기본값 2%
            if position_info.direction == "LONG":
                new_stop_price = current_price - (atr_value * 2)
            else:
                new_stop_price = current_price + (atr_value * 2)
        
        # 스탑 가격 업데이트 (더 유리한 방향으로만)
        current_stop = position_info.stop_price or 0
        
        if position_info.direction == "LONG":
            if new_stop_price > current_stop:
                # 스탑 가격이 더 높아짐 (유리)
                if current_price <= new_stop_price:
                    # 스탑 가격에 도달하면 청산
                    return TradingSignal(
                        SignalType.CLOSE_POSITION,
                        datetime.now(),
                        current_price,
                        quantity=position_info.quantity,
                        metadata={"reason": "trailing_stop_hit", "stop_price": new_stop_price}
                    )
                else:
                    # 스탑 가격 업데이트
                    return TradingSignal(
                        SignalType.UPDATE_STOP,
                        datetime.now(),
                        current_price,
                        stop_price=new_stop_price,
                        metadata={"trailing_stop_updated": True}
                    )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current_price)

class FixedTargetManagement(ManagementStrategy):
    """고정 익절/손절 관리 전략
    
    전략적 역할: 관리 전략
    개념: 진입가 대비 고정 % 도달 시 청산
    실제 사용: "매수 포지션 진입 후 +10% 도달시 익절, -5% 도달시 손절"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "profit_target": 10.0,               # 익절 목표 (%)
            "stop_loss": 5.0,                    # 손절 기준 (%)
            "partial_profit_enabled": False      # 부분 익절 사용 여부
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["profit_target", "stop_loss"]
        if not all(key in parameters for key in required):
            return False
            
        profit = parameters.get("profit_target", 0)
        stop = parameters.get("stop_loss", 0)
        
        return (isinstance(profit, (int, float)) and profit > 0 and
                isinstance(stop, (int, float)) and stop > 0)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return []
    
    def generate_management_signal(self, market_data: pd.DataFrame,
                                 position_info: PositionInfo) -> TradingSignal:
        """고정 익절/손절 관리 신호"""
        current_price = market_data.iloc[-1]['close']
        metrics = self.calculate_position_metrics(current_price, position_info)
        
        profit_target = self.parameters["profit_target"]
        stop_loss = self.parameters["stop_loss"]
        
        # 익절 조건
        if metrics["unrealized_pnl_pct"] >= profit_target:
            return TradingSignal(
                SignalType.CLOSE_POSITION,
                datetime.now(),
                current_price,
                quantity=position_info.quantity,
                metadata={"reason": "take_profit", "pnl_pct": metrics["unrealized_pnl_pct"]}
            )
        
        # 손절 조건
        elif metrics["unrealized_pnl_pct"] <= -stop_loss:
            return TradingSignal(
                SignalType.CLOSE_POSITION,
                datetime.now(),
                current_price,
                quantity=position_info.quantity,
                metadata={"reason": "stop_loss", "pnl_pct": metrics["unrealized_pnl_pct"]}
            )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current_price)

class PartialExitManagement(ManagementStrategy):
    """부분 청산 관리 전략
    
    전략적 역할: 관리 전략
    개념: 단계별 익절로 리스크 감소
    실제 사용: "매수 포지션이 +5% 도달시 30% 청산, +10% 도달시 30% 청산, +15% 도달시 나머지 40% 청산"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "profit_levels": [5.0, 10.0, 15.0],  # 익절 단계 (%)
            "exit_ratios": [0.3, 0.3, 0.4],      # 각 단계별 청산 비율
            "trailing_after_partial": True       # 부분 청산 후 트레일링 적용
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["profit_levels", "exit_ratios"]
        if not all(key in parameters for key in required):
            return False
            
        levels = parameters.get("profit_levels", [])
        ratios = parameters.get("exit_ratios", [])
        
        return (isinstance(levels, list) and isinstance(ratios, list) and
                len(levels) == len(ratios) and
                all(isinstance(x, (int, float)) and x > 0 for x in levels) and
                all(isinstance(x, (int, float)) and 0 < x <= 1 for x in ratios))
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return []
    
    def generate_management_signal(self, market_data: pd.DataFrame,
                                 position_info: PositionInfo) -> TradingSignal:
        """부분 청산 관리 신호"""
        current_price = market_data.iloc[-1]['close']
        metrics = self.calculate_position_metrics(current_price, position_info)
        
        profit_levels = self.parameters["profit_levels"]
        exit_ratios = self.parameters["exit_ratios"]
        
        # 부분 청산 이력 확인
        partial_exits = [h for h in position_info.management_history 
                        if h.get('action') == 'ADD_SELL']
        current_exit_level = len(partial_exits)
        
        # 다음 익절 단계 확인
        if current_exit_level < len(profit_levels):
            target_level = profit_levels[current_exit_level]
            
            if metrics["unrealized_pnl_pct"] >= target_level:
                exit_ratio = exit_ratios[current_exit_level]
                exit_quantity = position_info.quantity * exit_ratio
                
                # 마지막 단계면 전량 청산
                if current_exit_level == len(profit_levels) - 1:
                    exit_quantity = position_info.quantity
                
                return TradingSignal(
                    SignalType.ADD_SELL,
                    datetime.now(),
                    current_price,
                    quantity=exit_quantity,
                    metadata={
                        "partial_exit_level": current_exit_level + 1,
                        "exit_ratio": exit_ratio,
                        "pnl_pct": metrics["unrealized_pnl_pct"]
                    }
                )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current_price)

class TimeBasedExitManagement(ManagementStrategy):
    """시간 기반 청산 관리 전략
    
    전략적 역할: 관리 전략
    개념: 최대 보유 기간 도달 시 강제 청산
    실제 사용: "매수 포지션 진입 후 24시간이 경과하면 손익에 관계없이 전량 청산"
    """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "max_holding_hours": 24,             # 최대 보유 시간
            "force_exit_on_loss": True,          # 손실 시에도 강제 청산
            "exit_market_close": True            # 장 마감 전 청산
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        required = ["max_holding_hours"]
        if not all(key in parameters for key in required):
            return False
            
        hours = parameters.get("max_holding_hours", 0)
        return isinstance(hours, (int, float)) and hours > 0
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return []
    
    def generate_management_signal(self, market_data: pd.DataFrame,
                                 position_info: PositionInfo) -> TradingSignal:
        """시간 기반 청산 관리 신호"""
        current_price = market_data.iloc[-1]['close']
        metrics = self.calculate_position_metrics(current_price, position_info)
        
        max_hours = self.parameters["max_holding_hours"]
        force_exit_on_loss = self.parameters.get("force_exit_on_loss", True)
        
        # 최대 보유 시간 체크
        if metrics["holding_time_hours"] >= max_hours:
            # 손실 시에도 강제 청산할지 확인
            if force_exit_on_loss or metrics["unrealized_pnl_pct"] >= 0:
                return TradingSignal(
                    SignalType.CLOSE_POSITION,
                    datetime.now(),
                    current_price,
                    quantity=position_info.quantity,
                    metadata={
                        "reason": "time_based_exit",
                        "holding_hours": metrics["holding_time_hours"],
                        "pnl_pct": metrics["unrealized_pnl_pct"]
                    }
                )
        
        return TradingSignal(SignalType.HOLD, datetime.now(), current_price)

# ============================================================================
# 전략 조합 시스템
# ============================================================================

@dataclass 
class StrategyCombination:
    """전략 조합 설정"""
    combination_id: str
    name: str
    description: str
    
    # 필수: 진입 전략 (1개만)
    entry_strategy: Dict[str, Any]  # {"strategy_class": class, "parameters": dict}
    
    # 선택: 관리 전략 (0~N개)
    management_strategies: List[Dict[str, Any]] = None  # [{"strategy_class": class, "parameters": dict, "priority": int}]
    
    # 조합 설정
    execution_order: str = "parallel"  # "parallel" | "sequential"
    conflict_resolution: str = "priority"  # "priority" | "merge" | "conservative"
    
    created_at: datetime = None
    
    def __post_init__(self):
        if self.management_strategies is None:
            self.management_strategies = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def validate(self) -> bool:
        """조합 유효성 검증"""
        if not self.entry_strategy:
            return False
        
        if len(self.management_strategies) > 5:
            return False  # 최대 5개 관리 전략
        
        return True

# ============================================================================
# 충돌 해결 시스템
# ============================================================================

class ConflictResolver:
    """관리 전략 신호 충돌 해결 시스템"""
    
    @staticmethod
    def resolve_management_conflicts(signals: List[TradingSignal], 
                                   resolution_method: str = "priority") -> TradingSignal:
        """
        여러 관리 전략 신호 충돌 해결
        
        Args:
            signals: 각 관리 전략의 신호 목록
            resolution_method: "priority" | "merge" | "conservative"
        
        Returns:
            최종 실행할 단일 신호
        """
        if not signals:
            return TradingSignal(SignalType.HOLD, datetime.now(), 0)
        
        # HOLD가 아닌 신호만 필터링
        active_signals = [s for s in signals if s.signal_type != SignalType.HOLD]
        
        if not active_signals:
            return signals[0]  # 모두 HOLD이면 첫 번째 반환
        
        if resolution_method == "priority":
            return ConflictResolver._resolve_by_priority(active_signals)
        elif resolution_method == "merge":
            return ConflictResolver._resolve_by_merge(active_signals)
        elif resolution_method == "conservative":
            return ConflictResolver._resolve_conservative(active_signals)
        else:
            raise ValueError(f"알 수 없는 해결 방법: {resolution_method}")
    
    @staticmethod
    def _resolve_by_priority(signals: List[TradingSignal]) -> TradingSignal:
        """우선순위 기준 해결: 신뢰도가 높은 신호 채택"""
        return max(signals, key=lambda x: x.confidence)
    
    @staticmethod
    def _resolve_by_merge(signals: List[TradingSignal]) -> TradingSignal:
        """신호 병합: 수량 합산, 가격 평균"""
        # 신호 타입별 그룹화
        buy_signals = [s for s in signals if s.signal_type == SignalType.ADD_BUY]
        sell_signals = [s for s in signals if s.signal_type == SignalType.ADD_SELL]
        close_signals = [s for s in signals if s.signal_type == SignalType.CLOSE_POSITION]
        stop_signals = [s for s in signals if s.signal_type == SignalType.UPDATE_STOP]
        
        # 우선순위: CLOSE > UPDATE_STOP > ADD_SELL > ADD_BUY
        if close_signals:
            return close_signals[0]
        
        if stop_signals:
            # 가장 보수적인 스탑 가격 선택
            best_stop = min(stop_signals, key=lambda x: x.stop_price or float('inf'))
            return best_stop
        
        if sell_signals:
            # 매도 수량 합산
            total_quantity = sum(s.quantity or 0 for s in sell_signals)
            avg_price = sum(s.price * (s.quantity or 1) for s in sell_signals) / sum(s.quantity or 1 for s in sell_signals)
            
            return TradingSignal(
                SignalType.ADD_SELL,
                datetime.now(),
                avg_price,
                quantity=total_quantity,
                metadata={"merged_signals": len(sell_signals)}
            )
        
        if buy_signals:
            # 매수 수량 합산
            total_quantity = sum(s.quantity or 0 for s in buy_signals)
            avg_price = sum(s.price * (s.quantity or 1) for s in buy_signals) / sum(s.quantity or 1 for s in buy_signals)
            
            return TradingSignal(
                SignalType.ADD_BUY,
                datetime.now(),
                avg_price,
                quantity=total_quantity,
                metadata={"merged_signals": len(buy_signals)}
            )
        
        return signals[0]
    
    @staticmethod
    def _resolve_conservative(signals: List[TradingSignal]) -> TradingSignal:
        """보수적 해결: 위험 감소 우선"""
        # 우선순위: CLOSE_POSITION > ADD_SELL > UPDATE_STOP > ADD_BUY
        
        close_signals = [s for s in signals if s.signal_type == SignalType.CLOSE_POSITION]
        if close_signals:
            return close_signals[0]
        
        sell_signals = [s for s in signals if s.signal_type == SignalType.ADD_SELL]
        if sell_signals:
            return sell_signals[0]
        
        stop_signals = [s for s in signals if s.signal_type == SignalType.UPDATE_STOP]
        if stop_signals:
            return stop_signals[0]
        
        buy_signals = [s for s in signals if s.signal_type == SignalType.ADD_BUY]
        if buy_signals:
            return buy_signals[0]
        
        return signals[0]

# ============================================================================
# 상태 기반 백테스팅 엔진
# ============================================================================

class PositionState(Enum):
    """포지션 상태"""
    WAITING_ENTRY = "waiting_entry"        # 진입 대기
    POSITION_MANAGEMENT = "position_management"  # 포지션 관리
    POSITION_EXIT = "position_exit"        # 포지션 종료

class RoleBasedBacktestEngine:
    """역할 기반 백테스팅 엔진
    
    포지션 상태에 따라 적절한 전략 역할을 활성화하여 백테스트를 실행합니다.
    """
    
    def __init__(self, strategy_combination: StrategyCombination):
        self.combination = strategy_combination
        self.entry_strategy = self._load_entry_strategy()
        self.management_strategies = self._load_management_strategies()
        
        # 백테스트 상태
        self.position: Optional[PositionInfo] = None
        self.state = PositionState.WAITING_ENTRY
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []
        
        # 충돌 해결기
        self.conflict_resolver = ConflictResolver()
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _load_entry_strategy(self) -> EntryStrategy:
        """진입 전략 로드"""
        strategy_info = self.combination.entry_strategy
        strategy_class = strategy_info["strategy_class"]
        parameters = strategy_info["parameters"]
        return strategy_class(parameters)
    
    def _load_management_strategies(self) -> List[ManagementStrategy]:
        """관리 전략들 로드"""
        strategies = []
        for strategy_info in self.combination.management_strategies:
            strategy_class = strategy_info["strategy_class"]
            parameters = strategy_info["parameters"]
            strategy = strategy_class(parameters)
            strategy.priority = strategy_info.get("priority", 0)
            strategies.append(strategy)
        
        # 우선순위 순으로 정렬
        strategies.sort(key=lambda x: x.priority, reverse=True)
        return strategies
    
    def process_market_data(self, market_data: pd.DataFrame, 
                          initial_capital: float = 1000000) -> Dict[str, Any]:
        """시장 데이터 처리 및 상태별 로직 실행"""
        
        current_capital = initial_capital
        
        for i in range(len(market_data)):
            current_row = market_data.iloc[:i+1]  # 현재까지의 데이터
            
            if len(current_row) < 2:
                continue  # 최소 2개 데이터 필요
            
            timestamp = current_row.index[-1]
            current_price = current_row.iloc[-1]['close']
            
            if self.state == PositionState.WAITING_ENTRY:
                # 진입 대기: 진입 전략만 활성화
                signal = self.entry_strategy.generate_entry_signal(current_row, self.position)
                
                if signal.signal_type in [SignalType.BUY, SignalType.SELL]:
                    # 포지션 진입
                    self.position = self._enter_position(signal, timestamp, current_capital)
                    self.state = PositionState.POSITION_MANAGEMENT
                    
                    self.logger.info(f"포지션 진입: {signal.signal_type.value} @ {current_price}")
                    
            elif self.state == PositionState.POSITION_MANAGEMENT:
                # 포지션 관리: 관리 전략들만 활성화
                management_signals = []
                
                for strategy in self.management_strategies:
                    if strategy.can_activate(self.position):
                        mgmt_signal = strategy.generate_management_signal(current_row, self.position)
                        if mgmt_signal.signal_type != SignalType.HOLD:
                            management_signals.append(mgmt_signal)
                
                # 신호 충돌 해결
                if management_signals:
                    final_signal = self.conflict_resolver.resolve_management_conflicts(
                        management_signals, 
                        self.combination.conflict_resolution
                    )
                    
                    # 관리 액션 실행
                    if final_signal.signal_type == SignalType.CLOSE_POSITION:
                        # 포지션 청산
                        trade = self._close_position(final_signal, timestamp)
                        self.trades.append(trade)
                        self.position = None
                        self.state = PositionState.WAITING_ENTRY
                        
                        self.logger.info(f"포지션 청산: {final_signal.metadata.get('reason', 'unknown')} @ {current_price}")
                        
                    else:
                        # 기타 관리 액션 (추가매수, 부분매도, 스탑업데이트)
                        self._execute_management_action(final_signal, timestamp)
                
                # 포지션 상태 업데이트
                if self.position:
                    self.position.unrealized_pnl = self._calculate_unrealized_pnl(current_price)
            
            # 자본 업데이트 및 기록
            current_capital = self._calculate_current_capital(current_capital, current_price)
            self.equity_curve.append({
                "timestamp": timestamp,
                "capital": current_capital,
                "price": current_price,
                "position_value": self._get_position_value(current_price) if self.position else 0
            })
        
        # 백테스트 결과 생성
        return self._generate_backtest_results(initial_capital, current_capital)
    
    def _enter_position(self, signal: TradingSignal, timestamp, capital: float) -> PositionInfo:
        """포지션 진입"""
        quantity = capital * 0.95 / signal.price  # 95% 자본 사용 (수수료 고려)
        
        return PositionInfo(
            direction="LONG" if signal.signal_type == SignalType.BUY else "SHORT",
            entry_price=signal.price,
            entry_time=timestamp,
            quantity=quantity,
            management_history=[]
        )
    
    def _close_position(self, signal: TradingSignal, timestamp) -> Dict:
        """포지션 청산"""
        if not self.position:
            return {}
        
        pnl = (signal.price - self.position.entry_price) * self.position.quantity
        if self.position.direction == "SHORT":
            pnl = -pnl
        
        pnl_pct = (pnl / (self.position.entry_price * self.position.quantity)) * 100
        
        trade = {
            "entry_time": self.position.entry_time,
            "exit_time": timestamp,
            "direction": self.position.direction,
            "entry_price": self.position.entry_price,
            "exit_price": signal.price,
            "quantity": self.position.quantity,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "exit_reason": signal.metadata.get("reason", "unknown"),
            "management_history": self.position.management_history.copy()
        }
        
        return trade
    
    def _execute_management_action(self, signal: TradingSignal, timestamp):
        """관리 액션 실행"""
        if not self.position:
            return
        
        if signal.signal_type == SignalType.ADD_BUY:
            # 추가 매수
            self.position.quantity += signal.quantity or 0
            # 평단가 재계산 로직 필요
            
        elif signal.signal_type == SignalType.ADD_SELL:
            # 부분 매도
            self.position.quantity -= signal.quantity or 0
            
        elif signal.signal_type == SignalType.UPDATE_STOP:
            # 스탑 가격 업데이트
            self.position.stop_price = signal.stop_price
        
        # 관리 이력 기록
        self.position.management_history.append({
            "timestamp": timestamp,
            "action": signal.signal_type.value,
            "price": signal.price,
            "quantity": signal.quantity,
            "metadata": signal.metadata
        })
    
    def _calculate_unrealized_pnl(self, current_price: float) -> float:
        """미실현 손익 계산"""
        if not self.position:
            return 0
        
        pnl = (current_price - self.position.entry_price) * self.position.quantity
        if self.position.direction == "SHORT":
            pnl = -pnl
        
        return pnl
    
    def _calculate_current_capital(self, initial_capital: float, current_price: float) -> float:
        """현재 자본 계산"""
        if not self.position:
            return initial_capital + sum(trade["pnl"] for trade in self.trades)
        
        realized_pnl = sum(trade["pnl"] for trade in self.trades)
        unrealized_pnl = self._calculate_unrealized_pnl(current_price)
        
        return initial_capital + realized_pnl + unrealized_pnl
    
    def _get_position_value(self, current_price: float) -> float:
        """포지션 가치 계산"""
        if not self.position:
            return 0
        
        return self.position.quantity * current_price
    
    def _generate_backtest_results(self, initial_capital: float, final_capital: float) -> Dict[str, Any]:
        """백테스트 결과 생성"""
        total_return = (final_capital - initial_capital) / initial_capital * 100
        
        win_trades = [t for t in self.trades if t["pnl"] > 0]
        lose_trades = [t for t in self.trades if t["pnl"] <= 0]
        
        win_rate = len(win_trades) / len(self.trades) * 100 if self.trades else 0
        
        return {
            "combination_info": {
                "name": self.combination.name,
                "entry_strategy": self.entry_strategy.__class__.__name__,
                "management_strategies": [s.__class__.__name__ for s in self.management_strategies]
            },
            "performance": {
                "initial_capital": initial_capital,
                "final_capital": final_capital,
                "total_return_pct": total_return,
                "total_trades": len(self.trades),
                "win_trades": len(win_trades),
                "lose_trades": len(lose_trades),
                "win_rate_pct": win_rate
            },
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "strategy_contribution": self._analyze_strategy_contribution()
        }
    
    def _analyze_strategy_contribution(self) -> Dict[str, Any]:
        """전략별 기여도 분석"""
        entry_contribution = {
            "successful_entries": len([t for t in self.trades if t["pnl"] > 0]),
            "total_entries": len(self.trades)
        }
        
        management_contribution = {}
        for strategy in self.management_strategies:
            strategy_name = strategy.__class__.__name__
            # 각 관리 전략의 액션 횟수 계산
            actions = 0
            for trade in self.trades:
                actions += len([h for h in trade["management_history"] 
                              if strategy_name in str(h.get("metadata", {}))])
            
            management_contribution[strategy_name] = {
                "total_actions": actions,
                "strategy_priority": getattr(strategy, 'priority', 0)
            }
        
        return {
            "entry_strategy": entry_contribution,
            "management_strategies": management_contribution
        }

@dataclass 
class StrategyCombination:
    """전략 조합 설정"""
    combination_id: str
    name: str
    description: str
    
    # 필수: 진입 전략 (1개만)
    entry_strategy: Dict[str, Any]  # {"strategy_class": class, "parameters": dict}
    
    # 선택: 관리 전략 (0~N개)
    management_strategies: List[Dict[str, Any]] = None  # [{"strategy_class": class, "parameters": dict, "priority": int}]
    
    # 조합 설정
    execution_order: str = "parallel"  # "parallel" | "sequential"
    conflict_resolution: str = "priority"  # "priority" | "merge" | "conservative"
    
    created_at: datetime = None
    
    def __post_init__(self):
        if self.management_strategies is None:
            self.management_strategies = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def validate(self) -> bool:
        """조합 유효성 검증"""
        if not self.entry_strategy:
            return False
        
        if len(self.management_strategies) > 5:
            return False  # 최대 5개 관리 전략
        
        return True

if __name__ == "__main__":
    # ============================================================================
    # 테스트 및 사용 예시
    # ============================================================================
    
    import numpy as np
    
    def create_sample_data(length: int = 100) -> pd.DataFrame:
        """샘플 시장 데이터 생성"""
        dates = pd.date_range('2023-01-01', periods=length, freq='1h')
        
        # 기본 가격 데이터
        np.random.seed(42)
        price = 50000
        prices = []
        
        for _ in range(length):
            price += np.random.normal(0, price * 0.02)  # 2% 변동성
            prices.append(max(price, 1000))  # 최소가 방지
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(100, 1000, length)
        })
        
        # 기술적 지표 추가 (간단한 계산)
        data['SMA_5'] = data['close'].rolling(5).mean()
        data['SMA_20'] = data['close'].rolling(20).mean()
        data['RSI_14'] = 50 + np.random.normal(0, 15, length)  # 간단한 RSI 시뮬레이션
        data['BBANDS_UPPER_20'] = data['close'] * 1.02
        data['BBANDS_LOWER_20'] = data['close'] * 0.98
        
        return data.set_index('timestamp')
    
    
    def test_individual_strategies():
        """개별 전략 테스트"""
        print("=== 개별 전략 테스트 ===")
        
        # 샘플 데이터 생성
        data = create_sample_data(50)
        
        # 진입 전략 테스트
        print("\n1. 진입 전략 테스트")
        ma_strategy = MovingAverageCrossEntry({
            "short_period": 5,
            "long_period": 20,
            "ma_type": "SMA"
        })
        
        signal = ma_strategy.generate_entry_signal(data)
        print(f"이동평균 교차 신호: {signal.signal_type.value} @ {signal.price:.0f}")
        print(f"메타데이터: {signal.metadata}")
        
        rsi_strategy = RSIEntry({
            "rsi_period": 14,
            "oversold": 30,
            "overbought": 70
        })
        
        signal = rsi_strategy.generate_entry_signal(data)
        print(f"RSI 신호: {signal.signal_type.value} @ {signal.price:.0f}")
        
        # 관리 전략 테스트
        print("\n2. 관리 전략 테스트")
        
        # 샘플 포지션 생성
        sample_position = PositionInfo(
            direction="LONG",
            entry_price=50000,
            entry_time=datetime.now(),
            quantity=1.0,
            management_history=[]
        )
        
        # 현재가가 45000 (10% 하락)이라고 가정
        current_data = data.copy()
        current_data.iloc[-1, current_data.columns.get_loc('close')] = 45000
        
        averaging_strategy = AveragingDownManagement({
            "trigger_drop_percent": 5.0,
            "max_additional_buys": 3,
            "stop_loss_percent": -30.0
        })
        
        mgmt_signal = averaging_strategy.generate_management_signal(current_data, sample_position)
        print(f"물타기 신호: {mgmt_signal.signal_type.value}")
        if mgmt_signal.quantity:
            print(f"추가 매수 수량: {mgmt_signal.quantity:.4f}")
        print(f"메타데이터: {mgmt_signal.metadata}")
    
    
    def test_strategy_combination():
        """전략 조합 테스트"""
        print("\n=== 전략 조합 테스트 ===")
        
        # 전략 조합 생성: RSI 진입 + 물타기 + 트레일링 스탑
        combination = StrategyCombination(
            combination_id="rsi_averaging_trailing",
            name="RSI 진입 + 물타기 + 트레일링 스탑",
            description="RSI 과매도 진입 후 물타기와 트레일링 스탑으로 관리",
            entry_strategy={
                "strategy_class": RSIEntry,
                "parameters": {"rsi_period": 14, "oversold": 30, "overbought": 70}
            },
            management_strategies=[
                {
                    "strategy_class": AveragingDownManagement,
                    "parameters": {
                        "trigger_drop_percent": 5.0,
                        "max_additional_buys": 2,
                        "stop_loss_percent": -20.0
                    },
                    "priority": 1
                },
                {
                    "strategy_class": TrailingStopManagement,
                    "parameters": {
                        "trailing_distance": 3.0,
                        "activation_profit": 2.0
                    },
                    "priority": 2
                }
            ],
            conflict_resolution="conservative"
        )
        
        print(f"조합 이름: {combination.name}")
        print(f"진입 전략: {combination.entry_strategy['strategy_class'].__name__}")
        print(f"관리 전략 수: {len(combination.management_strategies)}")
        print(f"충돌 해결 방식: {combination.conflict_resolution}")
        print(f"유효성 검사: {combination.validate()}")
    
    
    def test_backtest_engine():
        """백테스트 엔진 테스트"""
        print("\n=== 백테스트 엔진 테스트 ===")
        
        # 전략 조합 생성
        combination = StrategyCombination(
            combination_id="simple_ma_test",
            name="간단한 이동평균 테스트",
            description="이동평균 교차 진입 + 고정 익절/손절",
            entry_strategy={
                "strategy_class": MovingAverageCrossEntry,
                "parameters": {"short_period": 5, "long_period": 20}
            },
            management_strategies=[
                {
                    "strategy_class": FixedTargetManagement,
                    "parameters": {"profit_target": 5.0, "stop_loss": 3.0},
                    "priority": 1
                }
            ]
        )
        
        # 백테스트 엔진 생성
        engine = RoleBasedBacktestEngine(combination)
        
        # 샘플 데이터로 백테스트 실행
        data = create_sample_data(200)
        results = engine.process_market_data(data, initial_capital=1000000)
        
        print(f"백테스트 결과:")
        print(f"- 초기 자본: {results['performance']['initial_capital']:,.0f} KRW")
        print(f"- 최종 자본: {results['performance']['final_capital']:,.0f} KRW")
        print(f"- 총 수익률: {results['performance']['total_return_pct']:.2f}%")
        print(f"- 총 거래 횟수: {results['performance']['total_trades']}")
        print(f"- 승률: {results['performance']['win_rate_pct']:.1f}%")
        
        if results['trades']:
            print(f"\n거래 내역 (최근 3건):")
            for trade in results['trades'][-3:]:
                print(f"  {trade['direction']} | 진입: {trade['entry_price']:.0f} → 청산: {trade['exit_price']:.0f} | "
                      f"손익: {trade['pnl_pct']:.2f}% | 이유: {trade['exit_reason']}")
    
    
    # 테스트 실행
    try:
        test_individual_strategies()
        test_strategy_combination()
        test_backtest_engine()
        
        print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
