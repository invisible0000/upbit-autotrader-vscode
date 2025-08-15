"""
Trading Variable DTO Classes
- Application Layer와 외부 계층 간 데이터 전달 객체
- 도메인 엔티티와 UI 간 격리 제공
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class TradingVariableListDTO:
    """트레이딩 변수 목록 응답 DTO"""
    success: bool
    total_count: int
    grouped_variables: Dict[str, List[Dict[str, Any]]]
    categories: List[str]
    error_message: Optional[str] = None
    search_info: Optional[Dict[str, Any]] = None
    compatibility_info: Optional[Dict[str, Any]] = None


@dataclass
class TradingVariableDetailDTO:
    """트레이딩 변수 상세 정보 DTO"""
    success: bool
    variable_id: Optional[str] = None
    display_name_ko: Optional[str] = None
    display_name_en: Optional[str] = None
    description: Optional[str] = None
    purpose_category: Optional[str] = None
    chart_category: Optional[str] = None
    comparison_group: Optional[str] = None
    parameter_required: Optional[bool] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    is_meta_variable: Optional[bool] = None
    is_dynamic_management: Optional[bool] = None
    error_message: Optional[str] = None


@dataclass
class VariableSearchRequestDTO:
    """트레이딩 변수 검색 요청 DTO"""
    search_term: Optional[str] = None
    category: Optional[str] = None
    comparison_group: Optional[str] = None
    compatible_with: Optional[str] = None
    language: str = "ko"
    limit: Optional[int] = None
    offset: Optional[int] = None


@dataclass
class VariableParameterDTO:
    """변수 파라미터 DTO"""
    parameter_name: str
    display_name_ko: str
    display_name_en: str
    parameter_type: str
    default_value: Any
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class VariableCompatibilityDTO:
    """변수 호환성 정보 DTO"""
    target_variable_id: str
    compatible_variables: List[str]
    incompatible_variables: List[str]
    compatibility_reasons: Dict[str, str]
    recommended_combinations: List[List[str]]


@dataclass
class VariableCreateRequestDTO:
    """변수 생성 요청 DTO"""
    variable_id: str
    display_name_ko: str
    display_name_en: str
    description: str
    purpose_category: str
    chart_category: str
    comparison_group: str
    parameter_required: bool
    parameters: List[VariableParameterDTO] = field(default_factory=list)
    source: str = "user"


@dataclass
class VariableUpdateRequestDTO:
    """변수 수정 요청 DTO"""
    variable_id: str
    display_name_ko: Optional[str] = None
    display_name_en: Optional[str] = None
    description: Optional[str] = None
    purpose_category: Optional[str] = None
    chart_category: Optional[str] = None
    comparison_group: Optional[str] = None
    parameter_required: Optional[bool] = None
    is_active: Optional[bool] = None
    parameters: Optional[List[VariableParameterDTO]] = None


@dataclass
class BulkVariableOperationDTO:
    """변수 일괄 작업 DTO"""
    operation_type: str  # 'create', 'update', 'delete', 'activate', 'deactivate'
    variable_ids: List[str] = field(default_factory=list)
    variables: List[VariableCreateRequestDTO] = field(default_factory=list)
    updates: Dict[str, VariableUpdateRequestDTO] = field(default_factory=dict)


@dataclass
class VariableValidationResultDTO:
    """변수 검증 결과 DTO"""
    success: bool
    variable_id: str
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    compatibility_issues: List[str] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)


@dataclass
class VariableStatsDTO:
    """변수 통계 정보 DTO"""
    total_variables: int
    active_variables: int
    inactive_variables: int
    variables_by_category: Dict[str, int]
    variables_by_comparison_group: Dict[str, int]
    meta_variables_count: int
    dynamic_management_variables_count: int
    variables_with_parameters: int
    last_updated: Optional[str] = None
