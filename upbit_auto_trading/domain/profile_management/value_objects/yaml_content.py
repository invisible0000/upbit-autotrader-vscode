"""
YAML Content Value Object
=========================

YAML 컨텐츠를 관리하는 Value Object입니다.
YAML 구문 검증과 안전한 파싱을 제공합니다.

DDD Value Object 특징:
- 불변 객체 (immutable)
- YAML 구문 유효성 자동 검증
- 안전한 파싱 및 직렬화 제공
"""

import yaml
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("YamlContent")

@dataclass(frozen=True)
class YamlContent:
    """
    YAML 컨텐츠 Value Object

    YAML 형식의 설정 내용을 안전하게 관리합니다.
    구문 검증, 파싱, 직렬화 기능을 제공합니다.

    Attributes:
        raw_content: 원본 YAML 텍스트
        is_valid: YAML 구문 유효성 여부
        validation_errors: 검증 오류 메시지들
    """

    raw_content: str
    is_valid: Optional[bool] = None
    validation_errors: Optional[List[str]] = None

    def __post_init__(self):
        """Value Object 초기화 후 검증"""
        # dataclass frozen=True이므로 object.__setattr__ 사용
        if self.is_valid is None or self.validation_errors is None:
            is_valid, errors = self._validate_yaml()
            object.__setattr__(self, 'is_valid', is_valid)
            object.__setattr__(self, 'validation_errors', errors)

    def _validate_yaml(self) -> tuple[bool, List[str]]:
        """YAML 구문 유효성 검증"""
        errors = []

        if not self.raw_content.strip():
            errors.append("YAML 내용이 비어있습니다")
            return False, errors

        try:
            # YAML 파싱 시도
            yaml.safe_load(self.raw_content)
            logger.debug("YAML 구문 검증 성공")
            return True, []

        except yaml.YAMLError as e:
            error_msg = f"YAML 구문 오류: {str(e)}"
            errors.append(error_msg)
            logger.warning(f"YAML 구문 검증 실패: {error_msg}")
            return False, errors

        except Exception as e:
            error_msg = f"YAML 검증 중 예상치 못한 오류: {str(e)}"
            errors.append(error_msg)
            logger.error(f"YAML 검증 예외: {error_msg}")
            return False, errors

    def parse_to_dict(self) -> Optional[Dict[str, Any]]:
        """YAML을 딕셔너리로 파싱"""
        if not self.is_valid:
            logger.warning("유효하지 않은 YAML을 파싱하려고 시도")
            return None

        try:
            result = yaml.safe_load(self.raw_content)
            if isinstance(result, dict):
                return result
            else:
                logger.warning(f"YAML 파싱 결과가 딕셔너리가 아님: {type(result)}")
                return None

        except Exception as e:
            logger.error(f"YAML 파싱 실패: {e}")
            return None

    def get_formatted_content(self) -> str:
        """포맷된 YAML 내용 반환"""
        if not self.is_valid:
            return self.raw_content

        try:
            parsed = self.parse_to_dict()
            if parsed is not None:
                return yaml.safe_dump(
                    parsed,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                    sort_keys=False
                )
        except Exception as e:
            logger.warning(f"YAML 포맷팅 실패: {e}")

        return self.raw_content

    def get_line_count(self) -> int:
        """라인 수 반환"""
        return len(self.raw_content.splitlines())

    def get_char_count(self) -> int:
        """문자 수 반환"""
        return len(self.raw_content)

    def is_empty(self) -> bool:
        """비어있는 내용인지 확인"""
        return not self.raw_content.strip()

    def has_key(self, key_path: str) -> bool:
        """특정 키 존재 여부 확인 (점 표기법 지원)"""
        if not self.is_valid:
            return False

        try:
            data = self.parse_to_dict()
            if data is None:
                return False

            keys = key_path.split('.')
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return False

            return True

        except Exception:
            return False

    def get_value(self, key_path: str, default: Any = None) -> Any:
        """특정 키의 값 추출 (점 표기법 지원)"""
        if not self.is_valid:
            return default

        try:
            data = self.parse_to_dict()
            if data is None:
                return default

            keys = key_path.split('.')
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default

            return current

        except Exception:
            return default

    def get_validation_summary(self) -> str:
        """검증 결과 요약"""
        if self.is_valid:
            return f"✅ 유효한 YAML ({self.get_line_count()}줄, {self.get_char_count()}자)"
        else:
            error_count = len(self.validation_errors) if self.validation_errors else 0
            return f"❌ 유효하지 않은 YAML ({error_count}개 오류)"

    def get_error_details(self) -> str:
        """오류 상세 정보"""
        if self.is_valid or not self.validation_errors:
            return ""

        return "\n".join(f"• {error}" for error in self.validation_errors)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'YamlContent':
        """딕셔너리에서 YAML Content 생성"""
        try:
            yaml_text = yaml.safe_dump(
                data,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=False
            )
            return cls(raw_content=yaml_text)
        except Exception as e:
            logger.error(f"딕셔너리에서 YAML 생성 실패: {e}")
            return cls(raw_content="")

    @classmethod
    def empty(cls) -> 'YamlContent':
        """빈 YAML Content 생성"""
        return cls(raw_content="")

    def __str__(self) -> str:
        """문자열 표현"""
        return self.raw_content

    def __repr__(self) -> str:
        """디버깅 표현"""
        status = "valid" if self.is_valid else "invalid"
        preview = self.raw_content[:50].replace('\n', '\\n')
        return f"YamlContent({status}, '{preview}...')"

    def __len__(self) -> int:
        """길이 (문자 수)"""
        return len(self.raw_content)
