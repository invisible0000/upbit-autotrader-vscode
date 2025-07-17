"""
전략 매개변수 관리 테스트 모듈
"""
import unittest
import json
from typing import Dict, Any, List

from upbit_auto_trading.business_logic.strategy.strategy_parameter import ParameterDefinition, StrategyParameterManager


class TestParameterDefinition(unittest.TestCase):
    """매개변수 정의 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 정수형 매개변수 정의
        self.int_param = ParameterDefinition(
            name="period",
            param_type=int,
            default_value=20,
            description="이동 평균 기간",
            min_value=1,
            max_value=200
        )
        
        # 실수형 매개변수 정의
        self.float_param = ParameterDefinition(
            name="threshold",
            param_type=float,
            default_value=0.05,
            description="신호 임계값",
            min_value=0.0,
            max_value=1.0
        )
        
        # 문자열 매개변수 정의 (선택 목록 포함)
        self.str_param = ParameterDefinition(
            name="method",
            param_type=str,
            default_value="sma",
            description="이동 평균 방법",
            choices=["sma", "ema", "wma"]
        )
        
        # 불리언 매개변수 정의
        self.bool_param = ParameterDefinition(
            name="use_high_low",
            param_type=bool,
            default_value=False,
            description="고가/저가 사용 여부"
        )
    
    def test_validate_int_parameter(self):
        """정수형 매개변수 유효성 검사 테스트"""
        # 유효한 값
        self.assertTrue(self.int_param.validate(20))
        self.assertTrue(self.int_param.validate(1))
        self.assertTrue(self.int_param.validate(200))
        
        # 유효하지 않은 값 (범위 밖)
        self.assertFalse(self.int_param.validate(0))
        self.assertFalse(self.int_param.validate(201))
        
        # 유효하지 않은 값 (타입 불일치)
        self.assertFalse(self.int_param.validate(20.5))
        self.assertFalse(self.int_param.validate("20"))
    
    def test_validate_float_parameter(self):
        """실수형 매개변수 유효성 검사 테스트"""
        # 유효한 값
        self.assertTrue(self.float_param.validate(0.05))
        self.assertTrue(self.float_param.validate(0.0))
        self.assertTrue(self.float_param.validate(1.0))
        
        # 유효하지 않은 값 (범위 밖)
        self.assertFalse(self.float_param.validate(-0.1))
        self.assertFalse(self.float_param.validate(1.1))
        
        # 유효하지 않은 값 (타입 불일치)
        self.assertFalse(self.float_param.validate("0.05"))
    
    def test_validate_str_parameter(self):
        """문자열 매개변수 유효성 검사 테스트"""
        # 유효한 값 (선택 목록 내)
        self.assertTrue(self.str_param.validate("sma"))
        self.assertTrue(self.str_param.validate("ema"))
        self.assertTrue(self.str_param.validate("wma"))
        
        # 유효하지 않은 값 (선택 목록 외)
        self.assertFalse(self.str_param.validate("rma"))
        
        # 유효하지 않은 값 (타입 불일치)
        self.assertFalse(self.str_param.validate(123))
    
    def test_validate_bool_parameter(self):
        """불리언 매개변수 유효성 검사 테스트"""
        # 유효한 값
        self.assertTrue(self.bool_param.validate(True))
        self.assertTrue(self.bool_param.validate(False))
        
        # 유효하지 않은 값 (타입 불일치)
        self.assertFalse(self.bool_param.validate("True"))
        self.assertFalse(self.bool_param.validate(1))
    
    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        # 정수형 매개변수
        int_dict = self.int_param.to_dict()
        self.assertEqual(int_dict["name"], "period")
        self.assertEqual(int_dict["type"], "int")
        self.assertEqual(int_dict["default_value"], 20)
        self.assertEqual(int_dict["min_value"], 1)
        self.assertEqual(int_dict["max_value"], 200)
        
        # 문자열 매개변수 (선택 목록 포함)
        str_dict = self.str_param.to_dict()
        self.assertEqual(str_dict["name"], "method")
        self.assertEqual(str_dict["type"], "str")
        self.assertEqual(str_dict["default_value"], "sma")
        self.assertEqual(str_dict["choices"], ["sma", "ema", "wma"])
    
    def test_from_dict(self):
        """딕셔너리에서 생성 테스트"""
        # 정수형 매개변수
        int_dict = {
            "name": "period",
            "type": "int",
            "default_value": 20,
            "description": "이동 평균 기간",
            "min_value": 1,
            "max_value": 200
        }
        
        param = ParameterDefinition.from_dict(int_dict)
        self.assertEqual(param.name, "period")
        self.assertEqual(param.param_type, int)
        self.assertEqual(param.default_value, 20)
        self.assertEqual(param.min_value, 1)
        self.assertEqual(param.max_value, 200)
        
        # 문자열 매개변수 (선택 목록 포함)
        str_dict = {
            "name": "method",
            "type": "str",
            "default_value": "sma",
            "description": "이동 평균 방법",
            "choices": ["sma", "ema", "wma"]
        }
        
        param = ParameterDefinition.from_dict(str_dict)
        self.assertEqual(param.name, "method")
        self.assertEqual(param.param_type, str)
        self.assertEqual(param.default_value, "sma")
        self.assertEqual(param.choices, ["sma", "ema", "wma"])


class TestStrategyParameterManager(unittest.TestCase):
    """전략 매개변수 관리자 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 매개변수 정의 목록
        self.param_defs = [
            ParameterDefinition(
                name="short_window",
                param_type=int,
                default_value=20,
                description="단기 이동 평균 기간",
                min_value=1,
                max_value=100
            ),
            ParameterDefinition(
                name="long_window",
                param_type=int,
                default_value=50,
                description="장기 이동 평균 기간",
                min_value=10,
                max_value=200
            ),
            ParameterDefinition(
                name="signal_line",
                param_type=int,
                default_value=9,
                description="시그널 라인 기간",
                min_value=1,
                max_value=50
            ),
            ParameterDefinition(
                name="method",
                param_type=str,
                default_value="sma",
                description="이동 평균 방법",
                choices=["sma", "ema", "wma"]
            )
        ]
        
        # 매개변수 관리자 생성
        self.param_manager = StrategyParameterManager(self.param_defs)
    
    def test_initialization(self):
        """초기화 테스트"""
        # 기본값으로 초기화되었는지 확인
        self.assertEqual(self.param_manager.get_parameter("short_window"), 20)
        self.assertEqual(self.param_manager.get_parameter("long_window"), 50)
        self.assertEqual(self.param_manager.get_parameter("signal_line"), 9)
        self.assertEqual(self.param_manager.get_parameter("method"), "sma")
    
    def test_set_parameter(self):
        """단일 매개변수 설정 테스트"""
        # 유효한 값 설정
        self.assertTrue(self.param_manager.set_parameter("short_window", 15))
        self.assertEqual(self.param_manager.get_parameter("short_window"), 15)
        
        # 유효하지 않은 값 설정 (범위 밖)
        self.assertFalse(self.param_manager.set_parameter("short_window", 0))
        self.assertEqual(self.param_manager.get_parameter("short_window"), 15)  # 변경되지 않아야 함
        
        # 유효하지 않은 값 설정 (타입 불일치)
        self.assertFalse(self.param_manager.set_parameter("short_window", "15"))
        self.assertEqual(self.param_manager.get_parameter("short_window"), 15)  # 변경되지 않아야 함
        
        # 존재하지 않는 매개변수 설정
        self.assertFalse(self.param_manager.set_parameter("unknown_param", 100))
    
    def test_set_parameters(self):
        """여러 매개변수 설정 테스트"""
        # 유효한 값 설정
        new_params = {
            "short_window": 15,
            "long_window": 60,
            "method": "ema"
        }
        
        self.assertTrue(self.param_manager.set_parameters(new_params))
        self.assertEqual(self.param_manager.get_parameter("short_window"), 15)
        self.assertEqual(self.param_manager.get_parameter("long_window"), 60)
        self.assertEqual(self.param_manager.get_parameter("method"), "ema")
        self.assertEqual(self.param_manager.get_parameter("signal_line"), 9)  # 변경되지 않아야 함
        
        # 일부 유효하지 않은 값 포함 (모두 변경되지 않아야 함)
        invalid_params = {
            "short_window": 15,
            "long_window": 300,  # 범위 밖
            "method": "ema"
        }
        
        self.assertFalse(self.param_manager.set_parameters(invalid_params))
        self.assertEqual(self.param_manager.get_parameter("short_window"), 15)  # 이전 값 유지
        self.assertEqual(self.param_manager.get_parameter("long_window"), 60)  # 이전 값 유지
        self.assertEqual(self.param_manager.get_parameter("method"), "ema")  # 이전 값 유지
    
    def test_get_all_parameters(self):
        """모든 매개변수 조회 테스트"""
        params = self.param_manager.get_all_parameters()
        self.assertEqual(len(params), 4)
        self.assertEqual(params["short_window"], 20)
        self.assertEqual(params["long_window"], 50)
        self.assertEqual(params["signal_line"], 9)
        self.assertEqual(params["method"], "sma")
        
        # 반환된 딕셔너리 수정이 원본에 영향을 주지 않는지 확인
        params["short_window"] = 15
        self.assertEqual(self.param_manager.get_parameter("short_window"), 20)
    
    def test_reset_to_defaults(self):
        """기본값으로 재설정 테스트"""
        # 값 변경
        self.param_manager.set_parameter("short_window", 15)
        self.param_manager.set_parameter("method", "ema")
        
        # 기본값으로 재설정
        self.param_manager.reset_to_defaults()
        
        # 기본값으로 재설정되었는지 확인
        self.assertEqual(self.param_manager.get_parameter("short_window"), 20)
        self.assertEqual(self.param_manager.get_parameter("method"), "sma")
    
    def test_get_parameter_definitions(self):
        """매개변수 정의 조회 테스트"""
        defs = self.param_manager.get_parameter_definitions()
        self.assertEqual(len(defs), 4)
        
        # 첫 번째 매개변수 정의 확인
        short_window_def = next(d for d in defs if d["name"] == "short_window")
        self.assertEqual(short_window_def["type"], "int")
        self.assertEqual(short_window_def["default_value"], 20)
        self.assertEqual(short_window_def["min_value"], 1)
        self.assertEqual(short_window_def["max_value"], 100)
    
    def test_json_serialization(self):
        """JSON 직렬화 테스트"""
        # 값 변경
        self.param_manager.set_parameter("short_window", 15)
        self.param_manager.set_parameter("method", "ema")
        
        # JSON 직렬화
        json_str = self.param_manager.to_json()
        
        # JSON 파싱
        params = json.loads(json_str)
        self.assertEqual(params["short_window"], 15)
        self.assertEqual(params["method"], "ema")
    
    def test_json_deserialization(self):
        """JSON 역직렬화 테스트"""
        # JSON 문자열
        json_str = '{"short_window": 15, "long_window": 60, "method": "ema"}'
        
        # JSON 역직렬화
        self.assertTrue(self.param_manager.from_json(json_str))
        
        # 값 확인
        self.assertEqual(self.param_manager.get_parameter("short_window"), 15)
        self.assertEqual(self.param_manager.get_parameter("long_window"), 60)
        self.assertEqual(self.param_manager.get_parameter("method"), "ema")
        self.assertEqual(self.param_manager.get_parameter("signal_line"), 9)  # 변경되지 않아야 함
        
        # 유효하지 않은 JSON 문자열
        self.assertFalse(self.param_manager.from_json("invalid json"))
        
        # 유효하지 않은 값이 포함된 JSON 문자열
        invalid_json = '{"short_window": 0, "long_window": 60}'  # short_window가 범위 밖
        self.assertFalse(self.param_manager.from_json(invalid_json))


if __name__ == "__main__":
    unittest.main()