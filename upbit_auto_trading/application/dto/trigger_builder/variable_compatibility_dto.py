"""
Variable Compatibility DTO
- 변수 호환성 검증 요청/응답을 위한 DTO
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class VariableCompatibilityRequestDTO:
    """변수 호환성 검증 요청 DTO"""
    main_variable_id: str
    external_variable_id: Optional[str] = None

    @classmethod
    def create(cls, main_variable_id: str, external_variable_id: Optional[str] = None) -> 'VariableCompatibilityRequestDTO':
        """호환성 검증 요청 DTO 생성"""
        return cls(
            main_variable_id=main_variable_id,
            external_variable_id=external_variable_id
        )


@dataclass(frozen=True)
class VariableCompatibilityResultDTO:
    """변수 호환성 검증 결과 DTO"""
    success: bool
    is_compatible: Optional[bool]  # None: 미정, True: 호환, False: 비호환
    main_variable_id: str
    external_variable_id: Optional[str]
    message: str
    detail: str
    error_message: Optional[str] = None
    compatible_groups: Optional[List[str]] = None
    compatible_count: Optional[int] = None

    @classmethod
    def create_success(cls, main_variable_id: str, external_variable_id: str,
                      message: str, detail: str) -> 'VariableCompatibilityResultDTO':
        """호환 성공 결과 생성"""
        return cls(
            success=True,
            is_compatible=True,
            main_variable_id=main_variable_id,
            external_variable_id=external_variable_id,
            message=message,
            detail=detail
        )

    @classmethod
    def create_incompatible(cls, main_variable_id: str, external_variable_id: str,
                           message: str, detail: str) -> 'VariableCompatibilityResultDTO':
        """비호환 결과 생성"""
        return cls(
            success=True,
            is_compatible=False,
            main_variable_id=main_variable_id,
            external_variable_id=external_variable_id,
            message=message,
            detail=detail
        )

    @classmethod
    def create_pending(cls, main_variable_id: str, message: str,
                      detail: str) -> 'VariableCompatibilityResultDTO':
        """대기 상태 결과 생성 (외부 변수 미선택)"""
        return cls(
            success=True,
            is_compatible=None,
            main_variable_id=main_variable_id,
            external_variable_id=None,
            message=message,
            detail=detail
        )

    @classmethod
    def create_info(cls, main_variable_id: str, message: str, detail: str,
                   compatible_groups: List[str], compatible_count: int) -> 'VariableCompatibilityResultDTO':
        """정보 조회 결과 생성"""
        return cls(
            success=True,
            is_compatible=None,
            main_variable_id=main_variable_id,
            external_variable_id=None,
            message=message,
            detail=detail,
            compatible_groups=compatible_groups,
            compatible_count=compatible_count
        )

    @classmethod
    def create_error(cls, error_message: str) -> 'VariableCompatibilityResultDTO':
        """오류 결과 생성"""
        return cls(
            success=False,
            is_compatible=None,
            main_variable_id="",
            external_variable_id=None,
            message="호환성 검증 실패",
            detail="",
            error_message=error_message
        )
