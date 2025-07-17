"""
전략 패키지

이 패키지는 매매 전략 관련 클래스와 기능을 제공합니다.
"""
from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.business_logic.strategy.base_strategy import BaseStrategy
from upbit_auto_trading.business_logic.strategy.strategy_parameter import ParameterDefinition, StrategyParameterManager
from upbit_auto_trading.business_logic.strategy.strategy_factory import StrategyFactory

# 전략 팩토리 인스턴스 생성
strategy_factory = StrategyFactory()

__all__ = [
    'StrategyInterface',
    'BaseStrategy',
    'ParameterDefinition',
    'StrategyParameterManager',
    'StrategyFactory',
    'strategy_factory'
]