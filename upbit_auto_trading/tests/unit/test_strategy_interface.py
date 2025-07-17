"""
전략 인터페이스 테스트 모듈
"""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from upbit_auto_trading.business_logic.strategy.strategy_interface import StrategyInterface
from upbit_auto_trading.business_logic.strategy.base_strategy import BaseStrategy


# 테스트용 구체적인 전략 클래스
class TestStrategy(BaseStrategy):
    """테스트용 전략 클래스"""
    
    def __init__(self, parameters: Dict[str, Any]):
        self.name = "TestStrategy"
        self.description = "테스트용 전략"
        super().__init__(parameters)
    
    def get_required_indicators(self) -> List[Dict[str, Any]]:
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
        # 필수 매개변수 확인
        required_params = ["short_window", "long_window"]
        for param in required_params:
            if param not in parameters:
                return False
        
        # 값 유효성 검사
        if not isinstance(parameters["short_window"], int) or parameters["short_window"] <= 0:
            return False
        if not isinstance(parameters["long_window"], int) or parameters["long_window"] <= 0:
            return False
        if parameters["short_window"] >= parameters["long_window"]:
            return False
        
        return True
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "short_window": 20,
            "long_window": 50
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        # 부모 클래스의 기본 구현 호출
        result = super().generate_signals(data)
        
        # 이동 평균 계산 (실제로는 데이터에 이미 포함되어 있어야 함)
        short_window = self.parameters["short_window"]
        long_window = self.parameters["long_window"]
        
        short_col = f"SMA_{short_window}"
        long_col = f"SMA_{long_window}"
        
        # 테스트를 위해 컬럼이 없으면 직접 계산
        if short_col not in data.columns:
            result[short_col] = data["close"].rolling(window=short_window).mean()
        if long_col not in data.columns:
            result[long_col] = data["close"].rolling(window=long_window).mean()
        
        # 신호 생성
        result["signal"] = 0
        result.loc[result[short_col] > result[long_col], "signal"] = 1
        result.loc[result[short_col] < result[long_col], "signal"] = -1
        
        return result


class TestStrategyInterface(unittest.TestCase):
    """전략 인터페이스 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트 데이터 생성
        self.test_data = pd.DataFrame({
            "timestamp": pd.date_range(start="2023-01-01", periods=100),
            "open": np.random.normal(100, 5, 100),
            "high": np.random.normal(105, 5, 100),
            "low": np.random.normal(95, 5, 100),
            "close": np.random.normal(100, 5, 100),
            "volume": np.random.normal(1000, 200, 100)
        })
        
        # 테스트 매개변수
        self.valid_params = {
            "short_window": 10,
            "long_window": 30
        }
        
        self.invalid_params = {
            "short_window": 50,
            "long_window": 20  # short_window > long_window (유효하지 않음)
        }
        
        # 테스트 전략 인스턴스
        self.strategy = TestStrategy(self.valid_params)
    
    def test_strategy_initialization(self):
        """전략 초기화 테스트"""
        # 유효한 매개변수로 초기화
        strategy = TestStrategy(self.valid_params)
        self.assertEqual(strategy.name, "TestStrategy")
        self.assertEqual(strategy.description, "테스트용 전략")
        self.assertEqual(strategy.parameters["short_window"], 10)
        self.assertEqual(strategy.parameters["long_window"], 30)
        
        # 유효하지 않은 매개변수로 초기화 (기본값 사용)
        strategy = TestStrategy(self.invalid_params)
        self.assertEqual(strategy.parameters["short_window"], 20)  # 기본값
        self.assertEqual(strategy.parameters["long_window"], 50)  # 기본값
    
    def test_get_parameters(self):
        """매개변수 조회 테스트"""
        params = self.strategy.get_parameters()
        self.assertEqual(params["short_window"], 10)
        self.assertEqual(params["long_window"], 30)
        
        # 반환된 딕셔너리 수정이 원본에 영향을 주지 않는지 확인
        params["short_window"] = 15
        self.assertEqual(self.strategy.parameters["short_window"], 10)
    
    def test_set_parameters(self):
        """매개변수 설정 테스트"""
        # 유효한 매개변수 설정
        new_params = {
            "short_window": 15,
            "long_window": 40
        }
        result = self.strategy.set_parameters(new_params)
        self.assertTrue(result)
        self.assertEqual(self.strategy.parameters["short_window"], 15)
        self.assertEqual(self.strategy.parameters["long_window"], 40)
        
        # 유효하지 않은 매개변수 설정
        result = self.strategy.set_parameters(self.invalid_params)
        self.assertFalse(result)
        # 매개변수가 변경되지 않아야 함
        self.assertEqual(self.strategy.parameters["short_window"], 15)
        self.assertEqual(self.strategy.parameters["long_window"], 40)
    
    def test_validate_parameters(self):
        """매개변수 유효성 검사 테스트"""
        self.assertTrue(self.strategy.validate_parameters(self.valid_params))
        self.assertFalse(self.strategy.validate_parameters(self.invalid_params))
        
        # 필수 매개변수 누락
        missing_params = {"short_window": 10}
        self.assertFalse(self.strategy.validate_parameters(missing_params))
        
        # 타입 오류
        type_error_params = {
            "short_window": "10",  # 문자열 (int 필요)
            "long_window": 30
        }
        self.assertFalse(self.strategy.validate_parameters(type_error_params))
    
    def test_get_strategy_info(self):
        """전략 정보 조회 테스트"""
        info = self.strategy.get_strategy_info()
        self.assertEqual(info["name"], "TestStrategy")
        self.assertEqual(info["description"], "테스트용 전략")
        self.assertEqual(info["parameters"]["short_window"], 10)
        self.assertEqual(info["parameters"]["long_window"], 30)
        self.assertIn("version", info)
        self.assertIn("created_at", info)
        self.assertIn("updated_at", info)
    
    def test_get_required_indicators(self):
        """필요한 지표 조회 테스트"""
        indicators = self.strategy.get_required_indicators()
        self.assertEqual(len(indicators), 2)
        
        # 첫 번째 지표 (단기 이동 평균)
        self.assertEqual(indicators[0]["name"], "SMA")
        self.assertEqual(indicators[0]["params"]["window"], 10)
        self.assertEqual(indicators[0]["params"]["column"], "close")
        
        # 두 번째 지표 (장기 이동 평균)
        self.assertEqual(indicators[1]["name"], "SMA")
        self.assertEqual(indicators[1]["params"]["window"], 30)
        self.assertEqual(indicators[1]["params"]["column"], "close")
    
    def test_generate_signals(self):
        """매매 신호 생성 테스트"""
        # 신호 생성
        result = self.strategy.generate_signals(self.test_data)
        
        # 결과 검증
        self.assertIn("signal", result.columns)
        self.assertIn(f"SMA_{self.strategy.parameters['short_window']}", result.columns)
        self.assertIn(f"SMA_{self.strategy.parameters['long_window']}", result.columns)
        
        # 신호 값 검증 (1, -1, 0 중 하나여야 함)
        unique_signals = result["signal"].unique()
        for signal in unique_signals:
            self.assertIn(signal, [0, 1, -1])
        
        # NaN 값이 없어야 함 (이동 평균 계산 초기 부분 제외)
        non_nan_signals = result["signal"].iloc[self.strategy.parameters["long_window"]:]
        self.assertFalse(non_nan_signals.isna().any())


if __name__ == "__main__":
    unittest.main()