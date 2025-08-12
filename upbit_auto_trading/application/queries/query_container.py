"""
Query Service Container 구현
Query Service들의 의존성 주입 및 생명 주기 관리
"""

from upbit_auto_trading.application.queries.query_dispatcher import QueryDispatcher
from upbit_auto_trading.application.queries.query_service import QueryService
from upbit_auto_trading.application.queries.handlers.strategy_query_handler import (
    StrategyListQueryHandler, StrategyDetailQueryHandler
)
from upbit_auto_trading.application.queries.handlers.dashboard_query_handler import DashboardQueryHandler
from upbit_auto_trading.application.queries.dto.strategy_query_dto import (
    StrategyListQuery, StrategyDetailQuery
)
from upbit_auto_trading.application.queries.dto.dashboard_query_dto import DashboardQuery

class QueryServiceContainer:
    """Query Service들의 의존성 주입 컨테이너"""

    def __init__(self, repository_container):
        self._repo_container = repository_container
        self._dispatcher = None
        self._query_service = None

    def get_query_service(self) -> QueryService:
        """Query Service 반환"""
        if self._query_service is None:
            self._query_service = QueryService(self.get_dispatcher())
        return self._query_service

    def get_dispatcher(self) -> QueryDispatcher:
        """Query Dispatcher 반환"""
        if self._dispatcher is None:
            self._dispatcher = self._create_dispatcher()
        return self._dispatcher

    def _create_dispatcher(self) -> QueryDispatcher:
        """Query Dispatcher 생성 및 핸들러 등록"""
        dispatcher = QueryDispatcher()

        # Strategy Query Handlers 등록
        strategy_list_handler = StrategyListQueryHandler(
            self._repo_container.get_strategy_repository(),
            self._repo_container.get_backtest_repository()
        )
        dispatcher.register_handler(StrategyListQuery, strategy_list_handler)

        strategy_detail_handler = StrategyDetailQueryHandler(
            self._repo_container.get_strategy_repository(),
            self._repo_container.get_trigger_repository(),
            self._repo_container.get_backtest_repository()
        )
        dispatcher.register_handler(StrategyDetailQuery, strategy_detail_handler)

        # Dashboard Query Handler 등록
        dashboard_handler = DashboardQueryHandler(
            self._repo_container.get_strategy_repository(),
            self._repo_container.get_trigger_repository(),
            self._repo_container.get_backtest_repository()
        )
        dispatcher.register_handler(DashboardQuery, dashboard_handler)

        return dispatcher

    def get_registered_handlers_info(self) -> dict:
        """등록된 핸들러 정보 반환"""
        if self._dispatcher is None:
            return {}
        return self._dispatcher.get_registered_handlers()

    def cleanup(self):
        """리소스 정리"""
        self._dispatcher = None
        self._query_service = None
