"""
VariableParameter Value Object
- 변수의 파라미터 정보를 나타내는 값 객체
- 불변성 보장 (frozen=True)
"""
from dataclasses import dataclass
from typing import Any, Optional
from upbit_auto_trading.domain.exceptions.validation_exceptions import ValidationError


@dataclass(frozen=True)
class VariableParameter:
    """변수 파라미터 값 객체"""
    parameter_name: str
    display_name_ko: str
    display_name_en: str
    parameter_type: str  # integer, decimal, string, boolean
    default_value: Any
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    description: Optional[str] = None

    def __post_init__(self):
        """생성 후 검증"""
        self._validate()

    def _validate(self):
        """파라미터 유효성 검증"""
        if not self.parameter_name or not self.parameter_name.strip():
            raise ValidationError("parameter_name은 비어있을 수 없습니다")

        if not self.display_name_ko or not self.display_name_ko.strip():
            raise ValidationError("display_name_ko는 비어있을 수 없습니다")

        if not self.display_name_en or not self.display_name_en.strip():
            raise ValidationError("display_name_en은 비어있을 수 없습니다")

        if not self.parameter_type or not self.parameter_type.strip():
            raise ValidationError("parameter_type은 비어있을 수 없습니다")

        valid_types = {"integer", "decimal", "string", "boolean"}
        if self.parameter_type not in valid_types:
            raise ValidationError(f"parameter_type은 {valid_types} 중 하나여야 합니다")

        # 타입별 기본값 검증
        self._validate_default_value()

        # 범위 검증
        self._validate_range()

    def _validate_default_value(self):
        """기본값 타입 검증"""
        if self.parameter_type == "integer":
            if not isinstance(self.default_value, int):
                raise ValidationError("integer 타입의 기본값은 정수여야 합니다")
        elif self.parameter_type == "decimal":
            if not isinstance(self.default_value, (int, float)):
                raise ValidationError("decimal 타입의 기본값은 숫자여야 합니다")
        elif self.parameter_type == "string":
            if not isinstance(self.default_value, str):
                raise ValidationError("string 타입의 기본값은 문자열이어야 합니다")
        elif self.parameter_type == "boolean":
            if not isinstance(self.default_value, bool):
                raise ValidationError("boolean 타입의 기본값은 불린이어야 합니다")

    def _validate_range(self):
        """범위 검증"""
        if self.parameter_type in ("integer", "decimal"):
            if self.min_value is not None and self.max_value is not None:
                if self.min_value > self.max_value:
                    raise ValidationError("min_value는 max_value보다 작거나 같아야 합니다")

            if self.min_value is not None and self.default_value < self.min_value:
                raise ValidationError("기본값은 최소값보다 크거나 같아야 합니다")

            if self.max_value is not None and self.default_value > self.max_value:
                raise ValidationError("기본값은 최대값보다 작거나 같아야 합니다")

    def validate_value(self, value: Any) -> bool:
        """주어진 값이 이 파라미터의 제약조건을 만족하는지 검증"""
        try:
            # 타입 검증
            if self.parameter_type == "integer":
                if not isinstance(value, int):
                    return False
            elif self.parameter_type == "decimal":
                if not isinstance(value, (int, float)):
                    return False
            elif self.parameter_type == "string":
                if not isinstance(value, str):
                    return False
            elif self.parameter_type == "boolean":
                if not isinstance(value, bool):
                    return False

            # 범위 검증
            if self.parameter_type in ("integer", "decimal"):
                if self.min_value is not None and value < self.min_value:
                    return False
                if self.max_value is not None and value > self.max_value:
                    return False

            return True
        except Exception:
            return False
