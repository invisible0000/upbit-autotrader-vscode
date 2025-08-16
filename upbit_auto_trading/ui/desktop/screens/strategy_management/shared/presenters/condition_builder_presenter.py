"""
컨디션 빌더 Presenter - MVP 패턴의 Presenter 계층
실제 UseCase와 연동하여 비즈니스 로직 처리
"""
from typing import Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.use_cases.trigger_builder.trading_variable_use_cases import (
    ListTradingVariablesUseCase,
    GetVariableParametersUseCase,
    SearchTradingVariablesUseCase
)
from upbit_auto_trading.application.use_cases.trigger_builder.variable_compatibility_use_cases import (
    CheckVariableCompatibilityUseCase
)
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    VariableSearchRequestDTO,
    TradingVariableListDTO,
    TradingVariableDetailDTO
)
from upbit_auto_trading.application.dto.trigger_builder.variable_compatibility_dto import (
    VariableCompatibilityRequestDTO
)
from upbit_auto_trading.ui.desktop.screens.strategy_management.shared.views.i_condition_builder_view import IConditionBuilderView


class ConditionBuilderPresenter:
    """컨디션 빌더 Presenter - 실제 DB와 연동"""

    def __init__(self,
                 view: IConditionBuilderView,
                 list_variables_usecase: ListTradingVariablesUseCase,
                 get_variable_details_usecase: GetVariableParametersUseCase,
                 check_compatibility_usecase: CheckVariableCompatibilityUseCase):
        self._view = view
        self._list_variables_usecase = list_variables_usecase
        self._get_variable_details_usecase = get_variable_details_usecase
        self._check_compatibility_usecase = check_compatibility_usecase
        self._logger = create_component_logger("ConditionBuilderPresenter")

        self._current_variables: Optional[TradingVariableListDTO] = None

    async def initialize(self) -> None:
        """초기화 - 변수 목록 로드"""
        try:
            self._view.set_loading_state(True)
            self._logger.info("컨디션 빌더 초기화 시작")

            # 전체 변수 목록 로드 (파라미터 없이 호출)
            result = await self._list_variables_usecase.execute()

            if result.success:
                self._current_variables = result
                self._view.display_variables(result)
                self._logger.info(f"변수 목록 로드 완료: {result.total_count}개")
            else:
                self._logger.error(f"변수 목록 로드 실패: {result.error_message}")

        except Exception as e:
            self._logger.error(f"초기화 중 오류: {e}")
        finally:
            self._view.set_loading_state(False)

    async def search_variables(self, search_term: str, category: Optional[str] = None) -> None:
        """변수 검색"""
        try:
            self._view.set_loading_state(True)
            self._logger.info(f"변수 검색: {search_term}, 카테고리: {category}")

            search_request = VariableSearchRequestDTO(
                search_term=search_term if search_term else None,
                category=category,
                language="ko"
            )

            result = await self._list_variables_usecase.execute(search_request)

            if result.success:
                self._current_variables = result
                self._view.display_variables(result)
                self._logger.info(f"검색 완료: {result.total_count}개 변수")
            else:
                self._logger.error(f"검색 실패: {result.error_message}")

        except Exception as e:
            self._logger.error(f"검색 중 오류: {e}")
        finally:
            self._view.set_loading_state(False)

    async def select_variable(self, variable_id: str) -> None:
        """변수 선택 - 상세 정보 로드"""
        try:
            self._logger.info(f"변수 선택: {variable_id}")

            result = await self._get_variable_details_usecase.execute(variable_id)

            if result.success:
                self._view.show_variable_details(result)
                self._logger.info(f"변수 상세 정보 로드 완료: {variable_id}")
            else:
                self._logger.error(f"변수 상세 정보 로드 실패: {result.error_message}")

        except Exception as e:
            self._logger.error(f"변수 선택 중 오류: {e}")

    async def select_external_variable(self, variable_id: str) -> None:
        """외부 변수 선택 - 상세 정보 로드"""
        try:
            self._logger.info(f"외부 변수 선택: {variable_id}")

            result = await self._get_variable_details_usecase.execute(variable_id)

            if result.success:
                self._view.show_external_variable_details(result)
                self._logger.info(f"외부 변수 상세 정보 로드 완료: {variable_id}")
            else:
                self._logger.error(f"외부 변수 상세 정보 로드 실패: {result.error_message}")

        except Exception as e:
            self._logger.error(f"외부 변수 선택 중 오류: {e}")

    async def filter_by_category(self, category: str) -> None:
        """카테고리별 필터링"""
        try:
            self._view.set_loading_state(True)
            self._logger.info(f"카테고리 필터링: {category}")

            # 전체 목록을 다시 로드하고 UI에서 필터링하도록 함
            if category == "전체":
                result = await self._list_variables_usecase.execute()
            else:
                result = await self._list_variables_usecase.execute()

            if result.success:
                self._current_variables = result
                self._view.display_variables(result)
                self._logger.info(f"카테고리 필터링 완료: {result.total_count}개")
            else:
                self._logger.error(f"카테고리 필터링 실패: {result.error_message}")

        except Exception as e:
            self._logger.error(f"카테고리 필터링 중 오류: {e}")
        finally:
            self._view.set_loading_state(False)

    async def check_variable_compatibility(self, main_variable_id: str, external_variable_id: str = "") -> None:
        """변수 호환성 검증"""
        try:
            self._logger.info(f"호환성 검증: {main_variable_id} vs {external_variable_id}")

            # 호환성 검증 요청 생성
            request = VariableCompatibilityRequestDTO.create(
                main_variable_id=main_variable_id,
                external_variable_id=external_variable_id if external_variable_id else None
            )

            # 호환성 검증 실행
            result = await self._check_compatibility_usecase.execute(request)

            if result.success:
                if result.is_compatible is None:
                    # 대기 상태 (외부 변수 미선택)
                    self._view.update_compatibility_status(True, result.message, result.detail)
                elif result.is_compatible:
                    # 호환
                    self._view.update_compatibility_status(True, result.message, result.detail)
                else:
                    # 비호환
                    self._view.update_compatibility_status(False, result.message, result.detail)

                self._logger.info(f"호환성 검증 완료: {result.is_compatible}")
            else:
                # 오류 발생
                self._view.update_compatibility_status(False, "호환성 검증 실패", result.error_message or "알 수 없는 오류")
                self._logger.error(f"호환성 검증 실패: {result.error_message}")

        except Exception as e:
            self._logger.error(f"호환성 검증 중 오류: {e}")
            self._view.update_compatibility_status(False, "호환성 검증 오류", f"시스템 오류: {str(e)}")

    def reset_view(self) -> None:
        """뷰 초기화"""
        self._view.reset_condition()
        self._logger.info("컨디션 빌더 뷰 초기화 완료")
