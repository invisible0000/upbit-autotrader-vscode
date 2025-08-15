"""
트리거 빌더 탭 - MVP 패턴 연결
"""

from PyQt6.QtWidgets import QWidget

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer
from upbit_auto_trading.domain.trigger_builder.services.variable_compatibility_service import VariableCompatibilityService
from upbit_auto_trading.application.use_cases.trigger_builder.trading_variable_use_cases import (
    ListTradingVariablesUseCase,
    GetVariableParametersUseCase,
    SearchTradingVariablesUseCase
)

from .presenters.trigger_builder_presenter import TriggerBuilderPresenter
from .widgets.trigger_builder_widget import TriggerBuilderWidget


class TriggerBuilderTab(QWidget):
    """트리거 빌더 탭 - MVP 패턴으로 구성"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = create_component_logger("TriggerBuilderTab")
        self._setup_mvp()

    def _setup_mvp(self):
        """MVP 패턴 설정"""
        try:
            # Repository 및 UseCase 의존성 주입
            repository_container = RepositoryContainer()
            trading_variable_repository = repository_container.get_trading_variable_repository()
            compatibility_service = VariableCompatibilityService()

            # UseCase 인스턴스 생성
            list_variables_usecase = ListTradingVariablesUseCase(
                trading_variable_repository
            )
            get_variable_details_usecase = GetVariableParametersUseCase(
                trading_variable_repository
            )
            search_variables_usecase = SearchTradingVariablesUseCase(
                trading_variable_repository,
                compatibility_service
            )

            # View (Widget) 생성
            self._view = TriggerBuilderWidget(self)

            # Presenter 생성 및 연결
            self._presenter = TriggerBuilderPresenter(
                view=self._view,
                list_variables_usecase=list_variables_usecase,
                get_variable_details_usecase=get_variable_details_usecase,
                search_variables_usecase=search_variables_usecase
            )

            # 시그널 연결
            self._connect_signals()

            # 레이아웃 설정
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self._view)

            # 즉시 초기화 실행
            self._run_async(self.initialize())

            self._logger.info("트리거 빌더 탭 MVP 패턴 설정 완료")

        except Exception as e:
            self._logger.error(f"MVP 패턴 설정 실패: {e}")
            raise

    def _connect_signals(self):
        """View 시그널과 Presenter 메서드 연결"""
        try:
            # 변수 선택 시그널 연결
            self._view.variable_selected.connect(
                lambda name: self._run_async(self._presenter.handle_variable_selected(name))
            )

            # 검색 요청 시그널 연결
            self._view.search_requested.connect(
                lambda term, category: self._run_async(
                    self._presenter.handle_search_variables(term, category)
                )
            )

            # 시뮬레이션 시그널 연결
            self._view.simulation_start_requested.connect(
                self._presenter.handle_simulation_start
            )
            self._view.simulation_stop_requested.connect(
                self._presenter.handle_simulation_stop
            )

            self._logger.info("시그널 연결 완료")

        except Exception as e:
            self._logger.error(f"시그널 연결 실패: {e}")
            raise

    def _run_async(self, coroutine):
        """비동기 메서드를 동기적으로 실행"""
        import asyncio
        try:
            # 이벤트 루프가 이미 실행 중인지 확인
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 경우 태스크로 예약
                asyncio.create_task(coroutine)
            else:
                # 실행 중이 아닌 경우 새로 실행
                loop.run_until_complete(coroutine)
        except RuntimeError:
            # 이벤트 루프가 없는 경우 새로 생성
            asyncio.run(coroutine)
        except Exception as e:
            self._logger.error(f"비동기 실행 실패: {e}")

    async def initialize(self):
        """탭 초기화 - 외부에서 호출"""
        try:
            await self._presenter.initialize_view()
            self._logger.info("트리거 빌더 탭 초기화 완료")
        except Exception as e:
            self._logger.error(f"탭 초기화 실패: {e}")
            raise
