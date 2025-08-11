"""
YAML Parser
===========

YAML 파일 파싱, 검증, 포맷팅을 담당하는 Infrastructure 컴포넌트입니다.

주요 기능:
- YAML 구문 검증
- 안전한 파싱
- 포맷팅 및 정규화
- 오류 상세 정보 제공
"""

import yaml
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger


logger = create_component_logger("YamlParser")


@dataclass
class ValidationResult:
    """YAML 검증 결과"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    parsed_data: Optional[Dict[str, Any]] = None

    @property
    def has_errors(self) -> bool:
        """오류 존재 여부"""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """경고 존재 여부"""
        return len(self.warnings) > 0

    @property
    def message_count(self) -> int:
        """전체 메시지 수"""
        return len(self.errors) + len(self.warnings)

    def get_summary(self) -> str:
        """검증 결과 요약"""
        if self.is_valid:
            if self.has_warnings:
                return f"✅ 유효 (경고 {len(self.warnings)}개)"
            return "✅ 유효"
        return f"❌ 무효 (오류 {len(self.errors)}개)"


class YamlParser:
    """
    YAML 파서

    YAML 파일의 파싱, 검증, 포맷팅을 담당합니다.
    """

    def __init__(self):
        """YAML 파서 초기화"""
        # 안전한 로더 설정
        self.safe_loader = yaml.SafeLoader
        self.safe_dumper = yaml.SafeDumper

        logger.info("YamlParser 초기화 완료")

    def parse_yaml_content(self, content: str) -> Dict[str, Any]:
        """
        YAML 내용을 딕셔너리로 파싱

        Args:
            content: YAML 텍스트

        Returns:
            Dict[str, Any]: 파싱된 데이터

        Raises:
            yaml.YAMLError: YAML 파싱 오류
            ValueError: 유효하지 않은 입력
        """
        if not content or not content.strip():
            logger.warning("빈 YAML 내용 파싱 시도")
            return {}

        try:
            parsed_data = yaml.safe_load(content)

            # None인 경우 빈 딕셔너리 반환
            if parsed_data is None:
                logger.debug("YAML 파싱 결과가 None, 빈 딕셔너리 반환")
                return {}

            # 딕셔너리가 아닌 경우 오류
            if not isinstance(parsed_data, dict):
                raise ValueError(f"YAML 루트는 딕셔너리여야 합니다. 현재 타입: {type(parsed_data)}")

            logger.debug(f"YAML 파싱 성공: {len(parsed_data)}개 키")
            return parsed_data

        except yaml.YAMLError as e:
            error_msg = f"YAML 파싱 오류: {self._format_yaml_error(e)}"
            logger.error(error_msg)
            raise yaml.YAMLError(error_msg) from e

        except Exception as e:
            error_msg = f"YAML 파싱 중 예상치 못한 오류: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def validate_yaml_syntax(self, content: str) -> ValidationResult:
        """
        YAML 구문 유효성 검증

        Args:
            content: YAML 텍스트

        Returns:
            ValidationResult: 검증 결과
        """
        errors = []
        warnings = []
        parsed_data = None

        try:
            # 빈 내용 체크
            if not content.strip():
                warnings.append("YAML 내용이 비어있습니다")
                return ValidationResult(
                    is_valid=True,
                    errors=errors,
                    warnings=warnings,
                    parsed_data={}
                )

            # YAML 파싱 시도
            parsed_data = yaml.safe_load(content)

            # 구조 검증
            structure_warnings = self._validate_structure(parsed_data)
            warnings.extend(structure_warnings)

            # 내용 검증
            content_warnings = self._validate_content(content)
            warnings.extend(content_warnings)

            logger.debug(f"YAML 검증 완료: 경고 {len(warnings)}개")
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                parsed_data=parsed_data if isinstance(parsed_data, dict) else None
            )

        except yaml.YAMLError as e:
            error_msg = f"YAML 구문 오류: {self._format_yaml_error(e)}"
            errors.append(error_msg)
            logger.warning(f"YAML 검증 실패: {error_msg}")

        except Exception as e:
            error_msg = f"YAML 검증 중 오류: {str(e)}"
            errors.append(error_msg)
            logger.error(f"YAML 검증 예외: {error_msg}")

        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            parsed_data=None
        )

    def format_yaml_content(self, content: str) -> str:
        """
        YAML 내용 포맷팅

        Args:
            content: 원본 YAML 텍스트

        Returns:
            str: 포맷된 YAML 텍스트
        """
        try:
            # 파싱 후 재직렬화로 포맷팅
            parsed_data = self.parse_yaml_content(content)

            formatted = yaml.safe_dump(
                parsed_data,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=False,
                width=80
            )

            logger.debug("YAML 포맷팅 성공")
            return formatted

        except Exception as e:
            logger.warning(f"YAML 포맷팅 실패: {e}")
            return content

    def normalize_yaml_content(self, content: str) -> str:
        """
        YAML 내용 정규화 (일관된 형식 적용)

        Args:
            content: 원본 YAML 텍스트

        Returns:
            str: 정규화된 YAML 텍스트
        """
        try:
            parsed_data = self.parse_yaml_content(content)

            # 정규화된 형식으로 직렬화
            normalized = yaml.safe_dump(
                parsed_data,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=True,  # 키 정렬
                width=100,
                explicit_start=False,
                explicit_end=False
            )

            logger.debug("YAML 정규화 성공")
            return normalized.strip() + '\n'

        except Exception as e:
            logger.warning(f"YAML 정규화 실패: {e}")
            return content

    def merge_yaml_contents(self, base_content: str, override_content: str) -> str:
        """
        두 YAML 내용 병합

        Args:
            base_content: 기본 YAML 내용
            override_content: 덮어쓸 YAML 내용

        Returns:
            str: 병합된 YAML 내용
        """
        try:
            base_data = self.parse_yaml_content(base_content)
            override_data = self.parse_yaml_content(override_content)

            # 딥 머지 수행
            merged_data = self._deep_merge_dict(base_data, override_data)

            # 병합 결과를 YAML로 직렬화
            merged_yaml = yaml.safe_dump(
                merged_data,
                default_flow_style=False,
                allow_unicode=True,
                indent=2,
                sort_keys=False
            )

            logger.debug("YAML 병합 성공")
            return merged_yaml

        except Exception as e:
            logger.error(f"YAML 병합 실패: {e}")
            return base_content

    def extract_section(self, content: str, section_path: str) -> Optional[str]:
        """
        YAML에서 특정 섹션 추출

        Args:
            content: YAML 내용
            section_path: 섹션 경로 (점 표기법, 예: "logging.level")

        Returns:
            Optional[str]: 추출된 섹션의 YAML 표현 (없으면 None)
        """
        try:
            data = self.parse_yaml_content(content)

            # 경로를 따라 데이터 탐색
            keys = section_path.split('.')
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    logger.debug(f"섹션 경로 '{section_path}'를 찾을 수 없음")
                    return None

            # 추출된 데이터를 YAML로 직렬화
            section_yaml = yaml.safe_dump(
                current,
                default_flow_style=False,
                allow_unicode=True,
                indent=2
            )

            return section_yaml

        except Exception as e:
            logger.warning(f"YAML 섹션 추출 실패: {e}")
            return None

    def _format_yaml_error(self, error: yaml.YAMLError) -> str:
        """YAML 오류 메시지 포맷팅"""
        if hasattr(error, 'problem_mark'):
            mark = error.problem_mark
            return f"{error.problem} (라인 {mark.line + 1}, 열 {mark.column + 1})"
        return str(error)

    def _validate_structure(self, data: Any) -> List[str]:
        """데이터 구조 검증"""
        warnings = []

        if data is None:
            warnings.append("YAML 내용이 비어있습니다")
        elif not isinstance(data, dict):
            warnings.append(f"루트 객체가 딕셔너리가 아닙니다: {type(data)}")
        elif len(data) == 0:
            warnings.append("루트 딕셔너리가 비어있습니다")

        return warnings

    def _validate_content(self, content: str) -> List[str]:
        """내용 검증"""
        warnings = []

        lines = content.splitlines()

        # 탭 사용 경고
        for i, line in enumerate(lines, 1):
            if '\t' in line:
                warnings.append(f"라인 {i}: 탭 문자 사용 (스페이스 권장)")

        # 길이 경고
        if len(content) > 10000:
            warnings.append("YAML 내용이 매우 깁니다 (10KB 초과)")

        return warnings

    def _deep_merge_dict(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """딕셔너리 딥 머지"""
        result = base.copy()

        for key, value in override.items():
            if (key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value

        return result
