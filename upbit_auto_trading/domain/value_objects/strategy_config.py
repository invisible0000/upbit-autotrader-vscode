"""
전략 설정 값 객체 (StrategyConfig)

구체적인 전략 인스턴스의 설정을 나타내는 값 객체입니다.
전략 정의(StrategyDefinition)와 실제 매개변수 값을 조합한 것입니다.
기존 SQLAlchemy StrategyConfig 모델을 도메인 값 객체로 변환한 것입니다.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass(frozen=True)
class StrategyConfig:
    """
    전략 설정 값 객체

    전략 정의와 구체적인 매개변수를 결합한 실행 가능한 전략 설정:
    - config_id: 고유 설정 식별자
    - strategy_definition_id: 기본 전략 정의 ID
    - strategy_name: 사용자 정의 전략 이름
    - parameters: 실제 매개변수 값들
    - priority: 우선순위 (관리 전략에서 사용)
    """

    config_id: str
    strategy_definition_id: str
    strategy_name: str
    parameters: Dict[str, Any]
    priority: int = 1
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """생성 후 유효성 검증"""
        if not self.config_id:
            raise ValueError("전략 설정 ID는 필수입니다")

        if not self.strategy_definition_id:
            raise ValueError("전략 정의 ID는 필수입니다")

        if not self.strategy_name:
            raise ValueError("전략 이름은 필수입니다")

        if not isinstance(self.parameters, dict):
            raise ValueError("매개변수는 딕셔너리 형태여야 합니다")

        if self.priority < 1:
            raise ValueError("우선순위는 1 이상이어야 합니다")

        # created_at이 None이면 현재 시간으로 설정
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.now())

    def __str__(self) -> str:
        """문자열 표현"""
        return f"{self.strategy_name} ({self.config_id})"

    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"StrategyConfig(id='{self.config_id}', name='{self.strategy_name}', priority={self.priority})"

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """특정 매개변수 값 가져오기"""
        return self.parameters.get(key, default)

    def has_parameter(self, key: str) -> bool:
        """매개변수 존재 여부 확인"""
        return key in self.parameters

    def get_required_parameters(self) -> list[str]:
        """필수 매개변수 목록 (전략 정의에서 가져와야 함)"""
        # 실제로는 StrategyDefinition에서 schema를 가져와서 검증해야 함
        # 지금은 기본적인 공통 매개변수들만 반환
        common_required = ["enabled", "position_size"]
        return [param for param in common_required if param in self.parameters]

    def validate_parameters(self, parameter_schema: Dict[str, Any]) -> bool:
        """매개변수 스키마 기반 유효성 검증"""
        if not parameter_schema:
            return True

        # 필수 매개변수 확인
        required_params = parameter_schema.get("required", [])
        for param in required_params:
            if param not in self.parameters:
                return False

        # 타입 검증 (간단한 구현)
        properties = parameter_schema.get("properties", {})
        for param_name, param_value in self.parameters.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type and not self._validate_parameter_type(param_value, expected_type):
                    return False

        return True

    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """매개변수 타입 검증"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            return True  # 알 수 없는 타입은 통과

        return isinstance(value, expected_python_type)

    def with_parameter(self, key: str, value: Any) -> "StrategyConfig":
        """매개변수를 추가/수정한 새 인스턴스 반환 (불변성 유지)"""
        new_parameters = self.parameters.copy()
        new_parameters[key] = value

        return StrategyConfig(
            config_id=self.config_id,
            strategy_definition_id=self.strategy_definition_id,
            strategy_name=self.strategy_name,
            parameters=new_parameters,
            priority=self.priority,
            created_at=self.created_at
        )

    def with_priority(self, new_priority: int) -> "StrategyConfig":
        """우선순위를 변경한 새 인스턴스 반환"""
        return StrategyConfig(
            config_id=self.config_id,
            strategy_definition_id=self.strategy_definition_id,
            strategy_name=self.strategy_name,
            parameters=self.parameters,
            priority=new_priority,
            created_at=self.created_at
        )

    def is_enabled(self) -> bool:
        """전략이 활성화되어 있는지 확인"""
        return self.get_parameter("enabled", True)

    def get_position_size(self) -> float:
        """포지션 크기 반환"""
        return self.get_parameter("position_size", 1.0)

    def get_display_info(self) -> Dict[str, Any]:
        """사용자 친화적 표시 정보"""
        return {
            "name": self.strategy_name,
            "definition": self.strategy_definition_id,
            "priority": self.priority,
            "enabled": self.is_enabled(),
            "position_size": self.get_position_size(),
            "created": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "Unknown"
        }

    @classmethod
    def create_default(cls, config_id: str, strategy_definition_id: str,
                      strategy_name: str) -> "StrategyConfig":
        """기본 설정으로 전략 설정 생성"""
        default_parameters = {
            "enabled": True,
            "position_size": 1.0,
            "risk_level": "medium"
        }

        return cls(
            config_id=config_id,
            strategy_definition_id=strategy_definition_id,
            strategy_name=strategy_name,
            parameters=default_parameters,
            priority=1,
            created_at=datetime.now()
        )
