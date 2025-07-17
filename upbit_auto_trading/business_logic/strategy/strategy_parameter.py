"""
전략 매개변수 관리 모듈

이 모듈은 전략 매개변수의 정의, 검증, 관리를 위한 클래스를 제공합니다.
"""
from typing import Dict, Any, List, Union, Optional, Type
import json


class ParameterDefinition:
    """
    전략 매개변수 정의 클래스
    
    매개변수의 타입, 범위, 기본값 등을 정의합니다.
    """
    
    def __init__(
        self,
        name: str,
        param_type: Type,
        default_value: Any,
        description: str = "",
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        choices: Optional[List[Any]] = None
    ):
        """
        매개변수 정의 초기화
        
        Args:
            name: 매개변수 이름
            param_type: 매개변수 타입 (int, float, str, bool 등)
            default_value: 기본값
            description: 매개변수 설명
            min_value: 최소값 (숫자 타입에만 적용)
            max_value: 최대값 (숫자 타입에만 적용)
            choices: 선택 가능한 값 목록 (열거형 매개변수에 적용)
        """
        self.name = name
        self.param_type = param_type
        self.default_value = default_value
        self.description = description
        self.min_value = min_value
        self.max_value = max_value
        self.choices = choices
    
    def validate(self, value: Any) -> bool:
        """
        매개변수 값 유효성 검사
        
        Args:
            value: 검사할 값
            
        Returns:
            유효성 여부
        """
        # 타입 검사
        if not isinstance(value, self.param_type):
            return False
        
        # 숫자 범위 검사
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        
        # 선택 목록 검사
        if self.choices is not None and value not in self.choices:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        매개변수 정의를 딕셔너리로 변환
        
        Returns:
            매개변수 정의 딕셔너리
        """
        return {
            "name": self.name,
            "type": self.param_type.__name__,
            "default_value": self.default_value,
            "description": self.description,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "choices": self.choices
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterDefinition':
        """
        딕셔너리에서 매개변수 정의 생성
        
        Args:
            data: 매개변수 정의 딕셔너리
            
        Returns:
            매개변수 정의 객체
        """
        # 타입 문자열을 실제 타입으로 변환
        type_map = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool
        }
        
        param_type = type_map.get(data["type"], str)
        
        return cls(
            name=data["name"],
            param_type=param_type,
            default_value=data["default_value"],
            description=data.get("description", ""),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            choices=data.get("choices")
        )


class StrategyParameterManager:
    """
    전략 매개변수 관리 클래스
    
    전략의 매개변수 정의와 값을 관리합니다.
    """
    
    def __init__(self, parameter_definitions: List[ParameterDefinition]):
        """
        매개변수 관리자 초기화
        
        Args:
            parameter_definitions: 매개변수 정의 목록
        """
        self.parameter_definitions = {param.name: param for param in parameter_definitions}
        self.parameter_values = {param.name: param.default_value for param in parameter_definitions}
    
    def set_parameter(self, name: str, value: Any) -> bool:
        """
        매개변수 값 설정
        
        Args:
            name: 매개변수 이름
            value: 설정할 값
            
        Returns:
            설정 성공 여부
        """
        if name not in self.parameter_definitions:
            return False
        
        param_def = self.parameter_definitions[name]
        if not param_def.validate(value):
            return False
        
        self.parameter_values[name] = value
        return True
    
    def get_parameter(self, name: str) -> Any:
        """
        매개변수 값 조회
        
        Args:
            name: 매개변수 이름
            
        Returns:
            매개변수 값
        """
        return self.parameter_values.get(name)
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """
        모든 매개변수 값 조회
        
        Returns:
            모든 매개변수 값 딕셔너리
        """
        return self.parameter_values.copy()
    
    def set_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        여러 매개변수 값 설정
        
        Args:
            parameters: 매개변수 이름과 값 딕셔너리
            
        Returns:
            모든 매개변수 설정 성공 여부
        """
        success = True
        temp_values = self.parameter_values.copy()
        
        for name, value in parameters.items():
            if name in self.parameter_definitions:
                param_def = self.parameter_definitions[name]
                if param_def.validate(value):
                    temp_values[name] = value
                else:
                    success = False
                    break
        
        if success:
            self.parameter_values = temp_values
        
        return success
    
    def reset_to_defaults(self) -> None:
        """
        모든 매개변수를 기본값으로 재설정
        """
        self.parameter_values = {
            param.name: param.default_value 
            for param in self.parameter_definitions.values()
        }
    
    def get_parameter_definitions(self) -> List[Dict[str, Any]]:
        """
        모든 매개변수 정의 조회
        
        Returns:
            매개변수 정의 딕셔너리 목록
        """
        return [param.to_dict() for param in self.parameter_definitions.values()]
    
    def to_json(self) -> str:
        """
        매개변수 값을 JSON 문자열로 변환
        
        Returns:
            JSON 문자열
        """
        return json.dumps(self.parameter_values)
    
    def from_json(self, json_str: str) -> bool:
        """
        JSON 문자열에서 매개변수 값 설정
        
        Args:
            json_str: JSON 문자열
            
        Returns:
            설정 성공 여부
        """
        try:
            parameters = json.loads(json_str)
            return self.set_parameters(parameters)
        except json.JSONDecodeError:
            return False