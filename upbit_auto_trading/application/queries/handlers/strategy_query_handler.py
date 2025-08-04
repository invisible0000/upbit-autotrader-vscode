"""
전략 관련 Query Handler 구현
전략 목록 조회, 전략 상세 조회 등의 읽기 전용 작업을 처리
"""

from typing import List, Optional, Dict, Any
import logging

from upbit_auto_trading.application.queries.handlers.base_query_handler import BaseQueryHandler
from upbit_auto_trading.application.queries.dto.strategy_query_dto import (
    StrategyListQuery, StrategyListResponse, StrategyListItem,
    StrategyDetailQuery, StrategyDetailResponse
)


class StrategyListQueryHandler(BaseQueryHandler[StrategyListQuery, StrategyListResponse]):
    """전략 목록 조회 Query Handler"""

    def __init__(self, strategy_repository, backtest_repository):
        self._strategy_repository = strategy_repository
        self._backtest_repository = backtest_repository
        self._logger = logging.getLogger(__name__)

    def handle(self, query: StrategyListQuery) -> StrategyListResponse:
        """전략 목록 조회 처리"""
        self.validate_query(query)

        # 1. 전략 목록 조회 (필터링 및 정렬 포함)
        strategies = self._strategy_repository.find_with_filters(
            status=query.status_filter,
            tags=query.tag_filter,
            name_pattern=query.name_search,
            created_after=query.created_after,
            created_before=query.created_before,
            include_deleted=query.include_deleted,
            sort_field=query.sort_field.value,
            sort_direction=query.sort_direction.value,
            limit=query.page_size,
            offset=(query.page - 1) * query.page_size
        )

        # 2. 총 개수 조회
        total_count = self._strategy_repository.count_with_filters(
            status=query.status_filter,
            tags=query.tag_filter,
            name_pattern=query.name_search,
            created_after=query.created_after,
            created_before=query.created_before,
            include_deleted=query.include_deleted
        )

        # 3. 응답 DTO 생성
        items = []
        for strategy in strategies:
            # 최근 백테스트 정보 조회
            last_backtest = self._backtest_repository.find_latest_by_strategy(
                strategy.strategy_id
            )

            item = StrategyListItem(
                strategy_id=strategy.strategy_id.value,
                name=strategy.name,
                status=strategy.status.value,
                tags=strategy.tags or [],
                entry_triggers_count=len(strategy.entry_triggers),
                exit_triggers_count=len(strategy.exit_triggers),
                last_backtest_date=last_backtest.completed_at if last_backtest else None,
                last_backtest_performance=last_backtest.total_return if last_backtest else None,
                created_at=strategy.created_at,
                updated_at=strategy.updated_at
            )
            items.append(item)

        return StrategyListResponse(
            items=items,
            total_count=total_count,
            page=query.page,
            page_size=query.page_size,
            has_next=(query.page * query.page_size) < total_count,
            has_previous=query.page > 1
        )

    def validate_query(self, query: StrategyListQuery) -> None:
        """쿼리 유효성 검증"""
        if query.page < 1:
            raise ValueError("페이지 번호는 1 이상이어야 합니다")
        if query.page_size < 1 or query.page_size > 100:
            raise ValueError("페이지 크기는 1-100 사이여야 합니다")


class StrategyDetailQueryHandler(BaseQueryHandler[StrategyDetailQuery, StrategyDetailResponse]):
    """전략 상세 조회 Query Handler"""

    def __init__(self, strategy_repository, trigger_repository, backtest_repository):
        self._strategy_repository = strategy_repository
        self._trigger_repository = trigger_repository
        self._backtest_repository = backtest_repository
        self._logger = logging.getLogger(__name__)

    def handle(self, query: StrategyDetailQuery) -> StrategyDetailResponse:
        """전략 상세 조회 처리"""
        from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId

        # 1. 전략 기본 정보 조회
        strategy = self._strategy_repository.find_by_id(StrategyId(query.strategy_id))
        if not strategy:
            raise ValueError(f"존재하지 않는 전략입니다: {query.strategy_id}")

        # 2. 트리거 정보 조회 (옵션)
        triggers = []
        if query.include_triggers:
            strategy_triggers = self._trigger_repository.find_by_strategy_id(
                strategy.strategy_id
            )
            triggers = [
                {
                    "trigger_id": t.trigger_id.value,
                    "trigger_name": t.trigger_name,
                    "variable_id": t.variable.variable_id,
                    "operator": t.operator.value,
                    "target_value": t.target_value,
                    "trigger_type": t.trigger_type.value,
                    "is_active": t.is_active
                }
                for t in strategy_triggers
            ]

        # 3. 백테스트 히스토리 조회 (옵션)
        backtest_history = []
        if query.include_backtest_history:
            backtests = self._backtest_repository.find_by_strategy_id(
                strategy.strategy_id, limit=10
            )
            backtest_history = [
                {
                    "backtest_id": bt.backtest_id,
                    "completed_at": bt.completed_at,
                    "total_return": bt.total_return,
                    "max_drawdown": bt.max_drawdown,
                    "sharpe_ratio": bt.sharpe_ratio,
                    "total_trades": bt.total_trades
                }
                for bt in backtests
            ]

        # 4. 성과 지표 계산 (옵션)
        performance_metrics = {}
        if query.include_performance_metrics:
            performance_metrics = self._calculate_performance_metrics(
                strategy.strategy_id
            )

        return StrategyDetailResponse(
            strategy_id=strategy.strategy_id.value,
            name=strategy.name,
            description=strategy.description,
            status=strategy.status.value,
            tags=strategy.tags or [],
            triggers=triggers,
            backtest_history=backtest_history,
            performance_metrics=performance_metrics,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        )

    def _calculate_performance_metrics(self, strategy_id) -> Dict[str, Any]:
        """성과 지표 계산"""
        backtests = self._backtest_repository.find_by_strategy_id(strategy_id)

        if not backtests:
            return {"status": "no_data"}

        returns = [bt.total_return for bt in backtests if bt.total_return is not None]
        drawdowns = [bt.max_drawdown for bt in backtests if bt.max_drawdown is not None]

        return {
            "avg_return": sum(returns) / len(returns) if returns else 0,
            "max_return": max(returns) if returns else 0,
            "min_return": min(returns) if returns else 0,
            "avg_drawdown": sum(drawdowns) / len(drawdowns) if drawdowns else 0,
            "max_drawdown": max(drawdowns) if drawdowns else 0,
            "total_backtests": len(backtests),
            "profitable_backtests": len([r for r in returns if r > 0])
        }
