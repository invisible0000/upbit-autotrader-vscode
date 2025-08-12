"""
전략 인터페이스 모듈

이 모듈은 모든 거래 전략이 구현해야 하는 기본 인터페이스를 정의합니다.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd

class StrategyInterface(ABC):
    """
    거래 전략 인터페이스
    
    모든 거래 전략은 이 인터페이스를 구현해야 합니다.
    """
    
    @abstractmethod
    def __init__(self, parameters: Dict[str, Any]):
        """
        전략 초기화
        
        Args:
            parameters: 전략 매개변수 딕셔너리
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        주어진 데이터에 대한 매매 신호 생성
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            
        Returns:
            매매 신호가 추가된 DataFrame
            - 'signal' 컬럼: 1 (매수), -1 (매도), 0 (홀드)
        """
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """
        전략에 필요한 기술적 지표 목록 반환
        
        Returns:
            필요한 지표 목록
            예: [
                {
                    "name": "SMA",
                    "params": {
                        "window": 20,
                        "column": "close"
                    }
                },
                {
                    "name": "RSI",
                    "params": {
                        "window": 14
                    }
                }
            ]
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        현재 전략 매개변수 반환
        
        Returns:
            전략 매개변수 딕셔너리
        """
        pass
    
    @abstractmethod
    def set_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        전략 매개변수 설정
        
        Args:
            parameters: 새 전략 매개변수 딕셔너리
            
        Returns:
            설정 성공 여부
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        전략 매개변수 유효성 검사
        
        Args:
            parameters: 검사할 매개변수 딕셔너리
            
        Returns:
            유효성 여부
        """
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        전략 정보 반환
        
        Returns:
            전략 정보 딕셔너리 (이름, 설명, 매개변수 등)
        """
        pass
    
    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        기본 매개변수 반환
        
        Returns:
            기본 매개변수 딕셔너리
        """
        pass