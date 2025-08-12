"""
기본 매매 전략 모듈

이 모듈은 기본적인 매매 전략 클래스를 제공합니다.
- 이동 평균 교차 전략
- 볼린저 밴드 전략
- RSI 기반 전략
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import logging

from upbit_auto_trading.business_logic.strategy.base_strategy import BaseStrategy

class MovingAverageCrossStrategy(BaseStrategy):
    """
    이동 평균 교차 전략
    
    단기 이동 평균이 장기 이동 평균을 상향 돌파하면 매수 신호,
    단기 이동 평균이 장기 이동 평균을 하향 돌파하면 매도 신호를 생성합니다.
    """
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        이동 평균 교차 전략 초기화
        
        Args:
            parameters: 전략 매개변수 딕셔너리
        """
        super().__init__(parameters)
        self.name = "MovingAverageCrossStrategy"
        self.description = "이동 평균 교차 전략 (단기 이동 평균이 장기 이동 평균을 돌파할 때 매매 신호 생성)"
        self.version = "1.0.0"
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """
        전략에 필요한 기술적 지표 목록 반환
        
        Returns:
            필요한 지표 목록
        """
        return [
            {
                "name": "SMA",
                "params": {
                    "window": self.parameters.get("short_window", 20),
                    "column": "close"
                }
            },
            {
                "name": "SMA",
                "params": {
                    "window": self.parameters.get("long_window", 50),
                    "column": "close"
                }
            }
        ]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        전략 매개변수 유효성 검사
        
        Args:
            parameters: 검사할 매개변수 딕셔너리
            
        Returns:
            유효성 여부
        """
        # 필수 매개변수 확인
        if "short_window" not in parameters or "long_window" not in parameters:
            return False
        
        # 타입 및 값 범위 확인
        if not isinstance(parameters["short_window"], int) or parameters["short_window"] <= 0:
            return False
        if not isinstance(parameters["long_window"], int) or parameters["long_window"] <= 0:
            return False
        
        # 단기 이동 평균 기간은 장기 이동 평균 기간보다 작아야 함
        if parameters["short_window"] >= parameters["long_window"]:
            return False
        
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        기본 매개변수 반환
        
        Returns:
            기본 매개변수 딕셔너리
        """
        return {
            "short_window": 20,
            "long_window": 50
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        주어진 데이터에 대한 매매 신호 생성
        
        Args:
            data: OHLCV 데이터와 기술적 지표가 포함된 DataFrame
            
        Returns:
            매매 신호가 추가된 DataFrame
        """
        # 데이터 복사
        result = data.copy()
        
        # 필요한 컬럼 확인
        short_window = self.parameters["short_window"]
        long_window = self.parameters["long_window"]
        short_col = f"SMA_{short_window}"
        long_col = f"SMA_{long_window}"
        
        # 필요한 지표가 없으면 기본 신호 반환
        if short_col not in result.columns or long_col not in result.columns:
            self.logger.warning(f"필요한 지표가 데이터에 없습니다: {short_col}, {long_col}")
            return super().generate_signals(result)
        
        # 신호 초기화
        result["signal"] = 0
        
        # 단기 이동 평균이 장기 이동 평균보다 크면 매수 신호(1)
        result.loc[result[short_col] > result[long_col], "signal"] = 1
        
        # 단기 이동 평균이 장기 이동 평균보다 작으면 매도 신호(-1)
        result.loc[result[short_col] < result[long_col], "signal"] = -1
        
        # NaN 값이 있는 경우 0(홀드)으로 설정
        result["signal"] = result["signal"].fillna(0)
        
        return result

class BollingerBandsStrategy(BaseStrategy):
    """
    볼린저 밴드 전략
    
    가격이 하단 밴드 아래로 내려가면 매수 신호,
    가격이 상단 밴드 위로 올라가면 매도 신호를 생성합니다.
    """
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        볼린저 밴드 전략 초기화
        
        Args:
            parameters: 전략 매개변수 딕셔너리
        """
        super().__init__(parameters)
        self.name = "BollingerBandsStrategy"
        self.description = "볼린저 밴드 전략 (가격이 밴드를 벗어날 때 매매 신호 생성)"
        self.version = "1.0.0"
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """
        전략에 필요한 기술적 지표 목록 반환
        
        Returns:
            필요한 지표 목록
        """
        return [
            {
                "name": "BOLLINGER_BANDS",
                "params": {
                    "window": self.parameters.get("window", 20),
                    "num_std": self.parameters.get("num_std", 2.0),
                    "column": self.parameters.get("column", "close")
                }
            }
        ]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        전략 매개변수 유효성 검사
        
        Args:
            parameters: 검사할 매개변수 딕셔너리
            
        Returns:
            유효성 여부
        """
        # 필수 매개변수 확인 및 기본값 설정
        window = parameters.get("window", 20)
        num_std = parameters.get("num_std", 2.0)
        column = parameters.get("column", "close")
        
        # 타입 및 값 범위 확인
        if not isinstance(window, int) or window <= 0:
            return False
        if not isinstance(num_std, (int, float)) or num_std <= 0:
            return False
        if not isinstance(column, str) or not column:
            return False
        
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        기본 매개변수 반환
        
        Returns:
            기본 매개변수 딕셔너리
        """
        return {
            "window": 20,
            "num_std": 2.0,
            "column": "close"
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        주어진 데이터에 대한 매매 신호 생성
        
        Args:
            data: OHLCV 데이터와 기술적 지표가 포함된 DataFrame
            
        Returns:
            매매 신호가 추가된 DataFrame
        """
        # 데이터 복사
        result = data.copy()
        
        # 필요한 컬럼 확인
        column = self.parameters.get("column", "close")
        
        # 필요한 지표가 없으면 기본 신호 반환
        if "BB_UPPER" not in result.columns or "BB_LOWER" not in result.columns or "BB_MIDDLE" not in result.columns:
            self.logger.warning("필요한 볼린저 밴드 지표가 데이터에 없습니다.")
            return super().generate_signals(result)
        
        # 신호 초기화
        result["signal"] = 0
        
        # 가격이 하단 밴드보다 낮으면 매수 신호(1)
        result.loc[result[column] <= result["BB_LOWER"], "signal"] = 1
        
        # 가격이 상단 밴드보다 높으면 매도 신호(-1)
        result.loc[result[column] >= result["BB_UPPER"], "signal"] = -1
        
        # NaN 값이 있는 경우 0(홀드)으로 설정
        result["signal"] = result["signal"].fillna(0)
        
        return result

class RSIStrategy(BaseStrategy):
    """
    RSI 기반 전략
    
    RSI가 과매도 수준 이하로 내려가면 매수 신호,
    RSI가 과매수 수준 이상으로 올라가면 매도 신호를 생성합니다.
    """
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        RSI 전략 초기화
        
        Args:
            parameters: 전략 매개변수 딕셔너리
        """
        super().__init__(parameters)
        self.name = "RSIStrategy"
        self.description = "RSI 기반 전략 (과매수/과매도 수준에서 매매 신호 생성)"
        self.version = "1.0.0"
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """
        전략에 필요한 기술적 지표 목록 반환
        
        Returns:
            필요한 지표 목록
        """
        return [
            {
                "name": "RSI",
                "params": {
                    "window": self.parameters.get("window", 14),
                    "column": self.parameters.get("column", "close")
                }
            }
        ]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        전략 매개변수 유효성 검사
        
        Args:
            parameters: 검사할 매개변수 딕셔너리
            
        Returns:
            유효성 여부
        """
        # 필수 매개변수 확인 및 기본값 설정
        window = parameters.get("window", 14)
        oversold = parameters.get("oversold", 30)
        overbought = parameters.get("overbought", 70)
        column = parameters.get("column", "close")
        
        # 타입 및 값 범위 확인
        if not isinstance(window, int) or window <= 0:
            return False
        if not isinstance(oversold, (int, float)) or oversold < 0 or oversold > 100:
            return False
        if not isinstance(overbought, (int, float)) or overbought < 0 or overbought > 100:
            return False
        if not isinstance(column, str) or not column:
            return False
        
        # 과매도 수준은 과매수 수준보다 작아야 함
        if oversold >= overbought:
            return False
        
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        기본 매개변수 반환
        
        Returns:
            기본 매개변수 딕셔너리
        """
        return {
            "window": 14,
            "oversold": 30,
            "overbought": 70,
            "column": "close"
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        주어진 데이터에 대한 매매 신호 생성
        
        Args:
            data: OHLCV 데이터와 기술적 지표가 포함된 DataFrame
            
        Returns:
            매매 신호가 추가된 DataFrame
        """
        # 데이터 복사
        result = data.copy()
        
        # 필요한 컬럼 확인
        window = self.parameters["window"]
        rsi_col = f"RSI_{window}"
        
        # 필요한 지표가 없으면 기본 신호 반환
        if rsi_col not in result.columns:
            self.logger.warning(f"필요한 지표가 데이터에 없습니다: {rsi_col}")
            return super().generate_signals(result)
        
        # 신호 초기화
        result["signal"] = 0
        
        # RSI가 과매도 수준 이하면 매수 신호(1)
        result.loc[result[rsi_col] <= self.parameters["oversold"], "signal"] = 1
        
        # RSI가 과매수 수준 이상이면 매도 신호(-1)
        result.loc[result[rsi_col] >= self.parameters["overbought"], "signal"] = -1
        
        # NaN 값이 있는 경우 0(홀드)으로 설정
        result["signal"] = result["signal"].fillna(0)
        
        return result