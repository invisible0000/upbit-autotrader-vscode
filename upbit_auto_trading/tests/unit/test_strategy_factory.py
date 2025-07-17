"""
전략 팩토리 테스트 모듈
"""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.business_logic.strategy.base_strategy import BaseStrategy
from upbit_auto_trading.business_logic.strategy.strategy_factory import StrategyFactory


# 테스트용 전략 클래스
class MockStrategy(BaseStrategy):
    """테스트용 모의 전략 클래스"""
    
    name = "MockStrategy"
    description = "테스트용 모의 전략"
    version = "1.0.0"
    
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__(parameters)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "SMA",
                "params": {
                    "window": self.parameters.get("window", 20),
                    "column": "close"
                }
            }
        ]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        if "window" not in parameters:
            return False
        if not isinstance(parameters["window"], int) or parameters["window"] <= 0:
            return False
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {"window": 20}


# 테스트용 전략 클래스 (정적 메서드 포함)
class StaticMockStrategy(BaseStrategy):
    """정적 메서드를 포함한 테스트용 모의 전략 클래스"""
    
    name = "StaticMockStrategy"
    description = "정적 메서드를 포함한 테스트용 모의 전략"
    version = "1.0.0"
    
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__(parameters)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "SMA",
                "params": {
                    "window": self.parameters.get("window", 20),
                    "column": "close"
                }
            }
        ]
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        if "window" not in parameters:
            return False
        if not isinstance(parameters["window"], int) or parameters["window"] <= 0:
            return False
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {"window": 20}
    
    @staticmethod
    def get_default_parameters_static() -> Dict[str, Any]:
        return {"window": 30}


class TestStrategyFactory(unittest.TestCase):
    """전략 팩토리 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.factory = StrategyFactory()
        
        # 테스트 전략 등록
        self.factory.register_strategy("mock_strategy", MockStrategy)
        self.factory.register_strategy("static_mock_strategy", StaticMockStrategy)
    
    def test_register_strategy(self):
        """전략 등록 테스트"""
        # 유효한 전략 클래스 등록
        result = self.factory.register_strategy("another_strategy", MockStrategy)
        self.assertTrue(result)
        self.assertIn("another_strategy", self.factory.strategy_classes)
        
        # 유효하지 않은 클래스 등록 시도
        class InvalidClass:
            pass
        
        result = self.factory.register_strategy("invalid_strategy", InvalidClass)
        self.assertFalse(result)
        self.assertNotIn("invalid_strategy", self.factory.strategy_classes)
    
    def test_create_strategy(self):
        """전략 생성 테스트"""
        # 매개변수 제공하여 생성
        params = {"window": 30}
        strategy = self.factory.create_strategy("mock_strategy", params)
        
        self.assertIsNotNone(strategy)
        self.assertIsInstance(strategy, MockStrategy)
        self.assertEqual(strategy.get_parameters()["window"], 30)
        
        # 매개변수 없이 생성 (기본값 사용)
        strategy = self.factory.create_strategy("mock_strategy")
        
        self.assertIsNotNone(strategy)
        self.assertIsInstance(strategy, MockStrategy)
        self.assertEqual(strategy.get_parameters()["window"], 20)
        
        # 정적 메서드를 가진 전략 생성
        strategy = self.factory.create_strategy("static_mock_strategy")
        
        self.assertIsNotNone(strategy)
        self.assertIsInstance(strategy, StaticMockStrategy)
        self.assertEqual(strategy.get_parameters()["window"], 20)
        
        # 존재하지 않는 전략 ID로 생성 시도
        strategy = self.factory.create_strategy("non_existent_strategy")
        self.assertIsNone(strategy)
    
    def test_get_available_strategies(self):
        """사용 가능한 전략 목록 조회 테스트"""
        strategies = self.factory.get_available_strategies()
        
        self.assertEqual(len(strategies), 2)
        
        # 첫 번째 전략 정보 확인
        mock_strategy_info = next(s for s in strategies if s["id"] == "mock_strategy")
        self.assertEqual(mock_strategy_info["name"], "MockStrategy")
        self.assertEqual(mock_strategy_info["description"], "테스트용 모의 전략")
        self.assertEqual(mock_strategy_info["version"], "1.0.0")
        
        # 두 번째 전략 정보 확인
        static_strategy_info = next(s for s in strategies if s["id"] == "static_mock_strategy")
        self.assertEqual(static_strategy_info["name"], "StaticMockStrategy")
        self.assertEqual(static_strategy_info["description"], "정적 메서드를 포함한 테스트용 모의 전략")
        self.assertEqual(static_strategy_info["version"], "1.0.0")
    
    @patch("importlib.import_module")
    def test_load_strategies_from_module(self, mock_import):
        """모듈에서 전략 로드 테스트"""
        # 모의 모듈 설정
        mock_module = MagicMock()
        mock_module.__name__ = "test_module"
        
        # 모의 전략 클래스 설정
        class TestStrategy1(BaseStrategy):
            def get_required_indicators(self): pass
            def validate_parameters(self, parameters): pass
            def get_default_parameters(self): pass
        
        class TestStrategy2(BaseStrategy):
            def get_required_indicators(self): pass
            def validate_parameters(self, parameters): pass
            def get_default_parameters(self): pass
        
        class NotAStrategy:
            pass
        
        # 모듈 내 클래스 설정
        mock_module.TestStrategy1 = TestStrategy1
        mock_module.TestStrategy2 = TestStrategy2
        mock_module.NotAStrategy = NotAStrategy
        mock_module.BaseStrategy = BaseStrategy
        
        # 모듈 가져오기 모의 설정
        mock_import.return_value = mock_module
        
        # 모듈에서 전략 로드
        count = self.factory.load_strategies_from_module("test_module")
        
        # 결과 검증
        self.assertEqual(count, 2)  # 2개의 전략이 로드되어야 함
        self.assertIn("teststrategy1", self.factory.strategy_classes)
        self.assertIn("teststrategy2", self.factory.strategy_classes)
        self.assertNotIn("notastrategy", self.factory.strategy_classes)
        self.assertNotIn("basestrategy", self.factory.strategy_classes)
        
        # 예외 발생 시 테스트
        mock_import.side_effect = ImportError("모듈을 찾을 수 없습니다.")
        count = self.factory.load_strategies_from_module("non_existent_module")
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()