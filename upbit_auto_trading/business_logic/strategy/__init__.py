"""
전략 패키지

이 패키지는 매매 전략 관련 클래스와 기능을 제공합니다.
"""
from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.business_logic.strategy.base_strategy import BaseStrategy
from upbit_auto_trading.business_logic.strategy.strategy_parameter import ParameterDefinition, StrategyParameterManager
from upbit_auto_trading.business_logic.strategy.strategy_factory import StrategyFactory
from upbit_auto_trading.business_logic.strategy.strategy_manager import StrategyManager, get_strategy_manager
from upbit_auto_trading.business_logic.strategy.basic_strategies import (
    MovingAverageCrossStrategy,
    BollingerBandsStrategy,
    RSIStrategy
)

# 전략 팩토리 인스턴스 생성
strategy_factory = StrategyFactory()

# 기본 전략 등록
strategy_factory.register_strategy("moving_average_cross", MovingAverageCrossStrategy)
strategy_factory.register_strategy("bollinger_bands", BollingerBandsStrategy)
strategy_factory.register_strategy("rsi", RSIStrategy)

__all__ = [
    'StrategyInterface',
    'BaseStrategy',
    'ParameterDefinition',
    'StrategyParameterManager',
    'StrategyFactory',
    'strategy_factory',
    'StrategyManager',
    'get_strategy_manager',
    'MovingAverageCrossStrategy',
    'BollingerBandsStrategy',
    'RSIStrategy'
]