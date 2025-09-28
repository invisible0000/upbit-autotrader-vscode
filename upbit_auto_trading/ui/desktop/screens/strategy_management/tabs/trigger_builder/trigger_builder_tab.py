"""
트리거 빌더 탭 - MVP 패턴 연결 (QAsync 통합)
"""

import asyncio
from PyQt6.QtWidgets import QWidget

# QAsync 통합 import
try:
    from qasync import asyncSlot
    QASYNC_AVAILABLE = True
except ImportError:
    QASYNC_AVAILABLE = False

    def asyncSlot(*args):
        def decorator(func):
            return func
        return decorator

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer
from upbit_auto_trading.domain.trigger_builder.services.variable_compatibility_service import VariableCompatibilityService
from upbit_auto_trading.application.use_cases.trigger_builder.trading_variable_use_cases import (
    ListTradingVariablesUseCase,
    GetVariableParametersUseCase,
    SearchTradingVariablesUseCase
)
from upbit_auto_trading.application.use_cases.trigger_builder.variable_compatibility_use_cases import (
    CheckVariableCompatibilityUseCase
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
            check_compatibility_usecase = CheckVariableCompatibilityUseCase(
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
                search_variables_usecase=search_variables_usecase,
                check_compatibility_usecase=check_compatibility_usecase
            )

            # 시그널 연결
            self._connect_signals()

            # 레이아웃 설정
            from PyQt6.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self._view)

            # 즉시 초기화 실행
            self._schedule_async(self.initialize())

            self._logger.info("트리거 빌더 탭 MVP 패턴 설정 완료")

        except Exception as e:
            self._logger.error(f"MVP 패턴 설정 실패: {e}")
            raise

    def _connect_signals(self):
        """View 시그널과 Presenter 메서드 연결"""
        try:
            # 변수 선택 시그널 연결
            self._view.variable_selected.connect(
                lambda name: self._schedule_async(self._presenter.handle_variable_selected(name))
            )

            # 외부 변수 선택 시그널 연결
            self._view.external_variable_selected.connect(
                lambda name: self._schedule_async(self._presenter.handle_external_variable_selected(name))
            )

            # 검색 요청 시그널 연결
            self._view.search_requested.connect(
                lambda term, category: self._schedule_async(
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

            # 호환성 검토 시그널 연결
            self._view.compatibility_check_requested.connect(
                lambda main_id, external_id: self._schedule_async(
                    self._presenter.handle_compatibility_check(main_id, external_id)
                )
            )

            self._logger.info("시그널 연결 완료")

        except Exception as e:
            self._logger.error(f"시그널 연결 실패: {e}")
            raise

    def _schedule_async(self, coroutine):
        """
        QAsync 환경에서 비동기 메서드 스케줄링

        ❌ 이전: 동기/비동기 분기 + run_until_complete/asyncio.run
        ✅ 현재: QAsync 환경 가정 + create_task 스케줄링
        """
        try:
            if not QASYNC_AVAILABLE:
                self._logger.error("QAsync가 설치되지 않았습니다")
                return

            # QAsync 환경에서는 항상 실행 중인 루프 가정
            loop = asyncio.get_running_loop()
            task = loop.create_task(coroutine)

            # 에러 핸들링을 위한 콜백 등록
            def task_done_callback(finished_task):
                if finished_task.exception():
                    exc = finished_task.exception()
                    self._logger.error(f"비동기 작업 실패: {exc}")
                else:
                    self._logger.debug("비동기 작업 완료")

            task.add_done_callback(task_done_callback)
            return task

        except RuntimeError as e:
            self._logger.error(f"QAsync 환경이 아닙니다: {e}")
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
