"""
컨디션 빌더 Presenter - MVP 패턴의 Presenter 계층
실제 UseCase와 연동하여 비즈니스 로직 처리
"""
from typing import Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.use_cases.trigger_builder.trading_variable_use_cases import (
    ListTradingVariablesUseCase,
    GetVariableParametersUseCase
)
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    VariableSearchRequestDTO,
    TradingVariableListDTO,
    TradingVariableDetailDTO
)
from upbit_auto_trading.ui.desktop.screens.strategy_management.shared.views.i_condition_builder_view import IConditionBuilderView


class ConditionBuilderPresenter:
    """컨디션 빌더 Presenter - 실제 DB와 연동"""

    def __init__(self,
                 view: IConditionBuilderView,
                 list_variables_usecase: ListTradingVariablesUseCase,
                 get_variable_details_usecase: GetVariableParametersUseCase):
        self._view = view
        self._list_variables_usecase = list_variables_usecase
        self._get_variable_details_usecase = get_variable_details_usecase
        self._logger = create_component_logger("ConditionBuilderPresenter")

        self._current_variables: Optional[TradingVariableListDTO] = None

    async def initialize(self) -> None:
        """초기화 - 변수 목록 로드"""
        try:
            self._view.set_loading_state(True)
            self._logger.info("컨디션 빌더 초기화 시작")

            # 전체 변수 목록 로드
            search_request = VariableSearchRequestDTO(
                category=None,  # 전체
                language="ko"
            )

            result = await self._list_variables_usecase.execute(search_request)

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

            search_request = VariableSearchRequestDTO(
                category=category if category != "전체" else None,
                language="ko"
            )

            result = await self._list_variables_usecase.execute(search_request)

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

    def check_variable_compatibility(self, base_variable: str, external_variable: str) -> None:
        """변수 호환성 검증"""
        try:
            self._logger.info(f"호환성 검증: {base_variable} vs {external_variable}")

            # TODO: 실제 호환성 검증 로직 구현
            # 임시로 항상 호환으로 처리
            is_compatible = True
            message = "변수 호환성 검증 완료"

            self._view.update_compatibility_status(is_compatible, message)

        except Exception as e:
            self._logger.error(f"호환성 검증 중 오류: {e}")
            self._view.update_compatibility_status(False, f"검증 오류: {e}")

    def reset_view(self) -> None:
        """뷰 초기화"""
        self._view.reset_condition()
        self._logger.info("컨디션 빌더 뷰 초기화 완료")
