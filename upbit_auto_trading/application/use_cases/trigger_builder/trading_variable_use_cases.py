"""
Trading Variable UseCase
- 트레이딩 변수 관련 비즈니스 로직 처리
- Repository와 Domain Service를 조합하여 복잡한 로직 구현
"""
import logging

from upbit_auto_trading.domain.trigger_builder.repositories.i_trading_variable_repository import ITradingVariableRepository
from upbit_auto_trading.domain.trigger_builder.services.variable_compatibility_service import VariableCompatibilityService
from upbit_auto_trading.domain.trigger_builder.enums import VariableCategory, ComparisonGroup
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    TradingVariableListDTO, TradingVariableDetailDTO, VariableSearchRequestDTO
)


class ListTradingVariablesUseCase:
    """트레이딩 변수 목록 조회 UseCase"""

    def __init__(self, repository: ITradingVariableRepository):
        self._repository = repository
        self._logger = logging.getLogger(__name__)

    async def execute(self) -> TradingVariableListDTO:
        """활성화된 모든 트레이딩 변수 목록 조회

        Returns:
            TradingVariableListDTO: 변수 목록 및 메타데이터
        """
        try:
            variables = await self._repository.get_all_active()

            # 카테고리별 그룹화
            grouped_variables = {}
            for category in VariableCategory:
                category_vars = [var for var in variables if var.purpose_category == category]
                if category_vars:
                    grouped_variables[category.value] = [
                        {
                            'variable_id': var.variable_id,
                            'display_name_ko': var.display_name_ko,
                            'display_name_en': var.display_name_en,
                            'description': var.description,
                            'parameter_required': var.parameter_required,
                            'comparison_group': var.comparison_group.value
                        }
                        for var in category_vars
                    ]

            return TradingVariableListDTO(
                success=True,
                total_count=len(variables),
                grouped_variables=grouped_variables,
                categories=list(grouped_variables.keys())
            )

        except Exception as e:
            self._logger.error(f"변수 목록 조회 실패: {e}")
            return TradingVariableListDTO(
                success=False,
                error_message=str(e),
                total_count=0,
                grouped_variables={},
                categories=[]
            )


class GetVariableParametersUseCase:
    """변수 파라미터 조회 UseCase"""

    def __init__(self, repository: ITradingVariableRepository):
        self._repository = repository
        self._logger = logging.getLogger(__name__)

    async def execute(self, variable_id: str) -> TradingVariableDetailDTO:
        """특정 변수의 상세 정보 및 파라미터 조회

        Args:
            variable_id: 조회할 변수 ID

        Returns:
            TradingVariableDetailDTO: 변수 상세 정보
        """
        try:
            variable = await self._repository.get_by_id(variable_id)

            if not variable:
                return TradingVariableDetailDTO(
                    success=False,
                    error_message=f"변수를 찾을 수 없습니다: {variable_id}"
                )

            # 파라미터 정보 구성
            parameters = []
            for param in variable.parameters:
                parameters.append({
                    'parameter_name': param.parameter_name,
                    'display_name_ko': param.display_name_ko,
                    'display_name_en': param.display_name_en,
                    'parameter_type': param.parameter_type,
                    'default_value': param.default_value,
                    'min_value': param.min_value,
                    'max_value': param.max_value,
                    'description': param.description
                })

            return TradingVariableDetailDTO(
                success=True,
                variable_id=variable.variable_id,
                display_name_ko=variable.display_name_ko,
                display_name_en=variable.display_name_en,
                description=variable.description,
                purpose_category=variable.purpose_category.value,
                chart_category=variable.chart_category.value,
                comparison_group=variable.comparison_group.value,
                parameter_required=variable.parameter_required,
                parameters=parameters,
                is_meta_variable=variable.is_meta_variable(),
                is_dynamic_management=variable.is_dynamic_management_variable()
            )

        except Exception as e:
            self._logger.error(f"변수 상세 조회 실패 ({variable_id}): {e}")
            return TradingVariableDetailDTO(
                success=False,
                error_message=str(e)
            )


class SearchTradingVariablesUseCase:
    """트레이딩 변수 검색 UseCase"""

    def __init__(self, repository: ITradingVariableRepository,
                 compatibility_service: VariableCompatibilityService):
        self._repository = repository
        self._compatibility_service = compatibility_service
        self._logger = logging.getLogger(__name__)

    async def execute(self, search_request: VariableSearchRequestDTO) -> TradingVariableListDTO:
        """트레이딩 변수 검색

        Args:
            search_request: 검색 요청 DTO

        Returns:
            TradingVariableListDTO: 검색 결과
        """
        try:
            variables = []

            # 검색어로 검색
            if search_request.search_term:
                search_results = await self._repository.search_by_name(
                    search_request.search_term,
                    search_request.language
                )
                variables.extend(search_results)

            # 카테고리로 필터링
            if search_request.category:
                try:
                    category = VariableCategory(search_request.category)
                    category_results = await self._repository.get_by_category(category)

                    # 검색어 결과와 교집합
                    if search_request.search_term:
                        variables = [var for var in variables if var in category_results]
                    else:
                        variables.extend(category_results)
                except ValueError:
                    self._logger.warning(f"유효하지 않은 카테고리: {search_request.category}")

            # 비교 그룹으로 필터링
            if search_request.comparison_group:
                try:
                    group = ComparisonGroup(search_request.comparison_group)
                    group_results = await self._repository.get_by_comparison_group(group)

                    # 기존 결과와 교집합
                    if variables:
                        variables = [var for var in variables if var in group_results]
                    else:
                        variables.extend(group_results)
                except ValueError:
                    self._logger.warning(f"유효하지 않은 비교 그룹: {search_request.comparison_group}")

            # 호환성 필터링
            if search_request.compatible_with:
                compatible_vars = await self._repository.get_compatible_variables(
                    search_request.compatible_with
                )

                if variables:
                    variables = [var for var in variables if var in compatible_vars]
                else:
                    variables.extend(compatible_vars)

            # 중복 제거
            unique_variables = []
            seen_ids = set()
            for var in variables:
                if var.variable_id not in seen_ids:
                    unique_variables.append(var)
                    seen_ids.add(var.variable_id)

            # 결과가 없으면 전체 목록 반환 (검색 조건이 없는 경우)
            if not unique_variables and not any([
                search_request.search_term,
                search_request.category,
                search_request.comparison_group,
                search_request.compatible_with
            ]):
                unique_variables = await self._repository.get_all_active()

            # 카테고리별 그룹화
            grouped_variables = {}
            for category in VariableCategory:
                category_vars = [var for var in unique_variables if var.purpose_category == category]
                if category_vars:
                    grouped_variables[category.value] = [
                        {
                            'variable_id': var.variable_id,
                            'display_name_ko': var.display_name_ko,
                            'display_name_en': var.display_name_en,
                            'description': var.description,
                            'parameter_required': var.parameter_required,
                            'comparison_group': var.comparison_group.value
                        }
                        for var in category_vars
                    ]

            return TradingVariableListDTO(
                success=True,
                total_count=len(unique_variables),
                grouped_variables=grouped_variables,
                categories=list(grouped_variables.keys()),
                search_info={
                    'search_term': search_request.search_term,
                    'category': search_request.category,
                    'comparison_group': search_request.comparison_group,
                    'compatible_with': search_request.compatible_with,
                    'language': search_request.language
                }
            )

        except Exception as e:
            self._logger.error(f"변수 검색 실패: {e}")
            return TradingVariableListDTO(
                success=False,
                error_message=str(e),
                total_count=0,
                grouped_variables={},
                categories=[]
            )


class GetCompatibleVariablesUseCase:
    """호환 가능한 변수 조회 UseCase"""

    def __init__(self, repository: ITradingVariableRepository,
                 compatibility_service: VariableCompatibilityService):
        self._repository = repository
        self._compatibility_service = compatibility_service
        self._logger = logging.getLogger(__name__)

    async def execute(self, variable_id: str) -> TradingVariableListDTO:
        """특정 변수와 호환 가능한 변수들 조회

        Args:
            variable_id: 기준 변수 ID

        Returns:
            TradingVariableListDTO: 호환 가능한 변수 목록
        """
        try:
            target_variable = await self._repository.get_by_id(variable_id)
            if not target_variable:
                return TradingVariableListDTO(
                    success=False,
                    error_message=f"변수를 찾을 수 없습니다: {variable_id}",
                    total_count=0,
                    grouped_variables={},
                    categories=[]
                )

            # 호환 가능한 변수들 조회
            compatible_vars = await self._repository.get_compatible_variables(variable_id)

            # 추천 우선순위 적용
            recommended_vars = self._compatibility_service.get_recommended_variables_for_category(
                target_variable.purpose_category,
                compatible_vars
            )

            # 카테고리별 그룹화
            grouped_variables = {}
            for category in VariableCategory:
                category_vars = [var for var in recommended_vars if var.purpose_category == category]
                if category_vars:
                    grouped_variables[category.value] = [
                        {
                            'variable_id': var.variable_id,
                            'display_name_ko': var.display_name_ko,
                            'display_name_en': var.display_name_en,
                            'description': var.description,
                            'parameter_required': var.parameter_required,
                            'comparison_group': var.comparison_group.value,
                            'is_recommended': var.purpose_category == target_variable.purpose_category
                        }
                        for var in category_vars
                    ]

            return TradingVariableListDTO(
                success=True,
                total_count=len(recommended_vars),
                grouped_variables=grouped_variables,
                categories=list(grouped_variables.keys()),
                compatibility_info={
                    'target_variable_id': variable_id,
                    'target_comparison_group': target_variable.comparison_group.value,
                    'target_category': target_variable.purpose_category.value
                }
            )

        except Exception as e:
            self._logger.error(f"호환 변수 조회 실패 ({variable_id}): {e}")
            return TradingVariableListDTO(
                success=False,
                error_message=str(e),
                total_count=0,
                grouped_variables={},
                categories=[]
            )
