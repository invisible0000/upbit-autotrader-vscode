"""
트리거 빌더 Presenter - MVP 패턴
"""

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.use_cases.trigger_builder.trading_variable_use_cases import (
    ListTradingVariablesUseCase,
    GetVariableParametersUseCase,
    SearchTradingVariablesUseCase
)
from upbit_auto_trading.application.dto.trigger_builder.trading_variable_dto import (
    VariableSearchRequestDTO
)
from ..views.i_trigger_builder_view import ITriggerBuilderView


class TriggerBuilderPresenter:
    """트리거 빌더 메인 Presenter - MVP 패턴"""

    def __init__(
        self,
        view: ITriggerBuilderView,
        list_variables_usecase: ListTradingVariablesUseCase,
        get_variable_details_usecase: GetVariableParametersUseCase,
        search_variables_usecase: SearchTradingVariablesUseCase
    ):
        self._view = view
        self._list_variables_usecase = list_variables_usecase
        self._get_variable_details_usecase = get_variable_details_usecase
        self._search_variables_usecase = search_variables_usecase
        self._logger = create_component_logger("TriggerBuilderPresenter")

    async def initialize_view(self) -> None:
        """View 초기화 - 변수 목록 로드"""
        try:
            self._logger.info("트리거 빌더 초기화 시작")

            # 변수 목록 로드
            variables_result = await self._list_variables_usecase.execute()
            if variables_result.success:
                self._view.display_variables(variables_result)
                self._logger.info(f"변수 목록 로드 완료: {variables_result.total_count}개")
            else:
                self._view.show_error_message(f"변수 목록 로드 실패: {variables_result.error_message}")

        except Exception as e:
            self._logger.error(f"초기화 중 오류: {e}")
            self._view.show_error_message(f"초기화 실패: {str(e)}")

    async def handle_variable_selected(self, variable_name: str) -> None:
        """변수 선택 처리"""
        try:
            self._logger.info(f"변수 선택: {variable_name}")

            # 변수 상세 정보 로드
            details_result = await self._get_variable_details_usecase.execute(variable_name)
            if details_result.success:
                self._view.show_variable_details(details_result)
                self._logger.info(f"변수 상세 정보 로드 완료: {variable_name}")
            else:
                self._view.show_error_message(f"변수 상세 정보 로드 실패: {details_result.error_message}")

        except Exception as e:
            self._logger.error(f"변수 선택 처리 중 오류: {e}")
            self._view.show_error_message(f"변수 선택 처리 실패: {str(e)}")

    async def handle_search_variables(self, search_term: str, category: str = "") -> None:
        """변수 검색 처리"""
        try:
            self._logger.info(f"변수 검색: {search_term}, 카테고리: {category}")

            # 검색 요청 DTO 생성
            search_request = VariableSearchRequestDTO(
                search_term=search_term,
                category=category if category else None
            )

            # 검색 실행
            search_result = await self._search_variables_usecase.execute(search_request)
            if search_result.success:
                self._view.display_variables(search_result)
                self._logger.info(f"검색 완료: {search_result.total_count}개 결과")
            else:
                self._view.show_error_message(f"검색 실패: {search_result.error_message}")

        except Exception as e:
            self._logger.error(f"변수 검색 중 오류: {e}")
            self._view.show_error_message(f"검색 실패: {str(e)}")

    def handle_simulation_start(self, scenario_type: str) -> None:
        """시뮬레이션 시작 처리 - 실제 데이터 연동"""
        try:
            self._logger.info(f"시뮬레이션 시작 요청: {scenario_type}")
            self._view.enable_simulation_controls(False)
            self._view.update_simulation_progress(0)

            # 시뮬레이션 결과 위젯에 직접 실행 요청
            self._view.run_simulation(scenario_type)

        except Exception as e:
            self._logger.error(f"시뮬레이션 시작 중 오류: {e}")
            self._view.show_error_message(f"시뮬레이션 시작 실패: {str(e)}")
            self._view.enable_simulation_controls(True)

    def handle_data_source_changed(self, source_type: str) -> None:
        """데이터 소스 변경 처리"""
        try:
            self._logger.info(f"데이터 소스 변경: {source_type}")
            self._view.update_data_source(source_type)

        except Exception as e:
            self._logger.error(f"데이터 소스 변경 중 오류: {e}")
            self._view.show_error_message(f"데이터 소스 변경 실패: {str(e)}")

    def handle_simulation_stop(self) -> None:
        """시뮬레이션 중지 처리"""
        try:
            self._logger.info("시뮬레이션 중지 요청")
            self._view.enable_simulation_controls(True)
            self._view.update_simulation_progress(0)

        except Exception as e:
            self._logger.error(f"시뮬레이션 중지 중 오류: {e}")
            self._view.show_error_message(f"시뮬레이션 중지 실패: {str(e)}")
