"""
Query Service Facade 구현
Query 실행을 위한 고수준 인터페이스 제공
"""

from typing import List
import logging

from upbit_auto_trading.application.queries.query_dispatcher import QueryDispatcher
from upbit_auto_trading.application.queries.dto.strategy_query_dto import (
    StrategyListQuery, StrategyListResponse, StrategyDetailQuery, StrategyDetailResponse,
    StrategySortField
)
from upbit_auto_trading.application.queries.dto.dashboard_query_dto import (
    DashboardQuery, DashboardResponse
)

class QueryService:
    """Query 실행을 위한 Facade 클래스"""

    def __init__(self, dispatcher: QueryDispatcher):
        self._dispatcher = dispatcher
        self._logger = logging.getLogger(__name__)

    # 전략 관련 쿼리
    def get_strategy_list(self, query: StrategyListQuery) -> StrategyListResponse:
        """전략 목록 조회"""
        return self._dispatcher.dispatch(query)

    def get_strategy_detail(self, strategy_id: str,
                            include_triggers: bool = True,
                            include_backtest_history: bool = True,
                            include_performance_metrics: bool = True) -> StrategyDetailResponse:
        """전략 상세 조회"""
        query = StrategyDetailQuery(
            strategy_id=strategy_id,
            include_triggers=include_triggers,
            include_backtest_history=include_backtest_history,
            include_performance_metrics=include_performance_metrics
        )
        return self._dispatcher.dispatch(query)

    # 대시보드 관련 쿼리
    def get_dashboard_data(self, date_range_days: int = 30,
                          include_performance_charts: bool = True,
                          include_trigger_stats: bool = True) -> DashboardResponse:
        """대시보드 데이터 조회"""
        query = DashboardQuery(
            date_range_days=date_range_days,
            include_performance_charts=include_performance_charts,
            include_trigger_stats=include_trigger_stats
        )
        return self._dispatcher.dispatch(query)

    # 검색 및 필터링 편의 메서드
    def search_strategies_by_name(self, name_pattern: str, limit: int = 10) -> StrategyListResponse:
        """이름으로 전략 검색"""
        query = StrategyListQuery(
            name_search=name_pattern,
            page_size=limit,
            sort_field=StrategySortField.NAME
        )
        return self._dispatcher.dispatch(query)

    def get_active_strategies(self, page: int = 1, page_size: int = 20) -> StrategyListResponse:
        """활성 전략 목록 조회"""
        query = StrategyListQuery(
            status_filter="ACTIVE",
            page=page,
            page_size=page_size,
            sort_field=StrategySortField.UPDATED_AT
        )
        return self._dispatcher.dispatch(query)

    def get_strategies_by_tags(self, tags: List[str], page: int = 1, page_size: int = 20) -> StrategyListResponse:
        """태그별 전략 조회"""
        query = StrategyListQuery(
            tag_filter=tags,
            page=page,
            page_size=page_size
        )
        return self._dispatcher.dispatch(query)
