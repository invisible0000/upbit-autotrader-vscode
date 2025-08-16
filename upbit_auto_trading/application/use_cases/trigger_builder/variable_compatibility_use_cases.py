"""
Variable Compatibility Check UseCase
- 두 변수 간 호환성 검증을 위한 UseCase
- UI에서 실시간 호환성 검토 요청 처리
"""
import logging

from upbit_auto_trading.domain.trigger_builder.repositories.i_trading_variable_repository import ITradingVariableRepository
from upbit_auto_trading.domain.trigger_builder.services.variable_compatibility_service import VariableCompatibilityService
from upbit_auto_trading.application.dto.trigger_builder.variable_compatibility_dto import (
    VariableCompatibilityRequestDTO,
    VariableCompatibilityResultDTO
)


class CheckVariableCompatibilityUseCase:
    """변수 간 호환성 검증 UseCase"""

    def __init__(self, repository: ITradingVariableRepository,
                 compatibility_service: VariableCompatibilityService):
        self._repository = repository
        self._compatibility_service = compatibility_service
        self._logger = logging.getLogger(__name__)

    async def execute(self, request: VariableCompatibilityRequestDTO) -> VariableCompatibilityResultDTO:
        """두 변수 간 호환성 검증

        Args:
            request: 호환성 검증 요청 DTO

        Returns:
            VariableCompatibilityResultDTO: 호환성 검증 결과
        """
        try:
            # 기본 변수 조회
            main_variable = await self._repository.get_by_id(request.main_variable_id)
            if not main_variable:
                return VariableCompatibilityResultDTO.create_error(
                    f"기본 변수를 찾을 수 없습니다: {request.main_variable_id}"
                )

            # 외부 변수가 지정된 경우 호환성 검증
            if request.external_variable_id:
                external_variable = await self._repository.get_by_id(request.external_variable_id)
                if not external_variable:
                    return VariableCompatibilityResultDTO.create_error(
                        f"외부 변수를 찾을 수 없습니다: {request.external_variable_id}"
                    )

                # 호환성 검증
                is_compatible = self._compatibility_service.can_compare_variables(
                    main_variable, external_variable
                )

                if is_compatible:
                    return VariableCompatibilityResultDTO.create_success(
                        main_variable_id=request.main_variable_id,
                        external_variable_id=request.external_variable_id,
                        message=f"{main_variable.display_name_ko}와(과) {external_variable.display_name_ko}는 호환됩니다",
                        detail=f"두 변수 모두 {main_variable.comparison_group.value} 비교 그룹에 속합니다"
                    )
                else:
                    incompatibility_reason = self._compatibility_service.get_incompatibility_reason(
                        main_variable, external_variable
                    )
                    return VariableCompatibilityResultDTO.create_incompatible(
                        main_variable_id=request.main_variable_id,
                        external_variable_id=request.external_variable_id,
                        message=f"{main_variable.display_name_ko}와(과) {external_variable.display_name_ko}는 호환되지 않습니다",
                        detail=incompatibility_reason
                    )
            else:
                # 외부 변수가 없는 경우 - 기본 변수만 선택된 상태
                return VariableCompatibilityResultDTO.create_pending(
                    main_variable_id=request.main_variable_id,
                    message=f"{main_variable.display_name_ko} 선택됨",
                    detail="외부 변수를 선택하면 호환성을 검토합니다"
                )

        except Exception as e:
            self._logger.error(f"호환성 검증 실패: {e}")
            return VariableCompatibilityResultDTO.create_error(
                f"호환성 검증 중 오류가 발생했습니다: {str(e)}"
            )


class GetVariableCompatibilityInfoUseCase:
    """변수 호환성 정보 조회 UseCase"""

    def __init__(self, repository: ITradingVariableRepository,
                 compatibility_service: VariableCompatibilityService):
        self._repository = repository
        self._compatibility_service = compatibility_service
        self._logger = logging.getLogger(__name__)

    async def execute(self, variable_id: str) -> VariableCompatibilityResultDTO:
        """특정 변수의 호환성 정보 조회

        Args:
            variable_id: 조회할 변수 ID

        Returns:
            VariableCompatibilityResultDTO: 변수 호환성 정보
        """
        try:
            variable = await self._repository.get_by_id(variable_id)
            if not variable:
                return VariableCompatibilityResultDTO.create_error(
                    f"변수를 찾을 수 없습니다: {variable_id}"
                )

            # 호환 가능한 비교 그룹들 조회
            compatible_groups = self._compatibility_service.get_compatible_comparison_groups(
                variable.comparison_group
            )

            # 호환 가능한 변수 개수 조회
            compatible_variables = await self._repository.get_compatible_variables(variable_id)

            group_names = [group.value for group in compatible_groups]

            return VariableCompatibilityResultDTO.create_info(
                main_variable_id=variable_id,
                message=f"{variable.display_name_ko} 호환성 정보",
                detail=f"호환 그룹: {', '.join(group_names)} | 호환 변수: {len(compatible_variables)}개",
                compatible_groups=group_names,
                compatible_count=len(compatible_variables)
            )

        except Exception as e:
            self._logger.error(f"호환성 정보 조회 실패 ({variable_id}): {e}")
            return VariableCompatibilityResultDTO.create_error(
                f"호환성 정보 조회 중 오류가 발생했습니다: {str(e)}"
            )
