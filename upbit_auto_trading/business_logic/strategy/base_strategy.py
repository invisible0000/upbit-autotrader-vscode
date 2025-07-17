"""
기본 전략 클래스 모듈

이 모듈은 모든 거래 전략의 기본이 되는 추상 클래스를 제공합니다.
"""
from abc import abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import logging
from datetime import datetime

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface


class BaseStrategy(StrategyInterface):
    """
    기본 전략 추상 클래스
    
    모든 구체적인 전략 클래스는 이 클래스를 상속받아야 합니다.
    공통 기능을 구현하고 특정 전략에 맞게 확장할 수 있는 기반을 제공합니다.
    """
    
    def __init__(self, parameters: Dict[str, Any]):
        """
        기본 전략 초기화
        
        Args:
            parameters: 전략 매개변수 딕셔너리
        """
        self.logger = logging.getLogger(__name__)
        
        # 기본 정보 초기화
        self.name = "BaseStrategy"
        self.description = "기본 전략 클래스"
        self.version = "1.0.0"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # 매개변수 유효성 검사 및 설정
        if not self.validate_parameters(parameters):
            self.logger.error("전략 매개변수가 유효하지 않습니다.")
            # 유효하지 않은 경우 기본 매개변수 사용
            self.parameters = self.get_default_parameters()
            self.logger.info("기본 매개변수를 사용합니다.")
        else:
            self.parameters = parameters.copy()
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        주어진 데이터에 대한 매매 신호 생성
        
        이 메서드는 하위 클래스에서 구현해야 합니다.
        
        Args:
            data: OHLCV 데이터가 포함된 DataFrame
            
        Returns:
            매매 신호가 추가된 DataFrame
        """
        # 기본 구현은 모든 데이터에 대해 홀드 신호 반환
        result = data.copy()
        if 'signal' not in result.columns:
            result['signal'] = 0
        return result
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        현재 전략 매개변수 반환
        
        Returns:
            전략 매개변수 딕셔너리
        """
        return self.parameters.copy()
    
    def set_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        전략 매개변수 설정
        
        Args:
            parameters: 새 전략 매개변수 딕셔너리
            
        Returns:
            설정 성공 여부
        """
        if not self.validate_parameters(parameters):
            self.logger.error("전략 매개변수가 유효하지 않습니다.")
            return False
        
        self.parameters = parameters.copy()
        self.updated_at = datetime.now()
        return True
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        전략 정보 반환
        
        Returns:
            전략 정보 딕셔너리 (이름, 설명, 매개변수 등)
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": self.get_parameters(),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @abstractmethod
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        """
        전략에 필요한 기술적 지표 목록 반환
        
        이 메서드는 하위 클래스에서 구현해야 합니다.
        
        Returns:
            필요한 지표 목록
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        전략 매개변수 유효성 검사
        
        이 메서드는 하위 클래스에서 구현해야 합니다.
        
        Args:
            parameters: 검사할 매개변수 딕셔너리
            
        Returns:
            유효성 여부
        """
        pass
    
    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        기본 매개변수 반환
        
        이 메서드는 하위 클래스에서 구현해야 합니다.
        
        Returns:
            기본 매개변수 딕셔너리
        """
        pass