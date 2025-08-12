"""
대시보드 관련 Query Handler 구현
실시간 모니터링 데이터 및 성과 지표 조회를 처리
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from upbit_auto_trading.application.queries.handlers.base_query_handler import BaseQueryHandler
from upbit_auto_trading.application.queries.dto.dashboard_query_dto import (
    DashboardQuery, DashboardResponse, PerformanceMetric, TriggerStatistic
)

class DashboardQueryHandler(BaseQueryHandler[DashboardQuery, DashboardResponse]):
    """대시보드 조회 Query Handler"""

    def __init__(self, strategy_repository, trigger_repository, backtest_repository):
        self._strategy_repository = strategy_repository
        self._trigger_repository = trigger_repository
        self._backtest_repository = backtest_repository
        self._logger = logging.getLogger(__name__)

    def handle(self, query: DashboardQuery) -> DashboardResponse:
        """대시보드 조회 처리"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=query.date_range_days)

        # 1. 요약 통계 생성
        summary_stats = self._generate_summary_stats(start_date, end_date)

        # 2. 성과 지표 계산
        performance_metrics = []
        if query.include_performance_charts:
            performance_metrics = self._calculate_performance_metrics(start_date, end_date)

        # 3. 트리거 통계 생성
        trigger_statistics = []
        if query.include_trigger_stats:
            trigger_statistics = self._generate_trigger_statistics(start_date, end_date)

        # 4. 활성 전략 수 계산
        active_strategies_count = self._strategy_repository.count_active_strategies()

        # 5. 최근 백테스트 결과 조회
        recent_backtest_results = self._get_recent_backtest_results(limit=5)

        # 6. 시스템 상태 체크
        system_health = self._check_system_health()

        return DashboardResponse(
            summary_stats=summary_stats,
            performance_metrics=performance_metrics,
            trigger_statistics=trigger_statistics,
            active_strategies_count=active_strategies_count,
            recent_backtest_results=recent_backtest_results,
            system_health=system_health,
            generated_at=datetime.now()
        )

    def _generate_summary_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """요약 통계 생성"""
        total_strategies = self._strategy_repository.count_all_strategies()
        active_strategies = self._strategy_repository.count_active_strategies()
        total_triggers = self._trigger_repository.count_all_triggers()

        period_backtests = self._backtest_repository.count_backtests_in_period(
            start_date, end_date
        )

        return {
            "total_strategies": total_strategies,
            "active_strategies": active_strategies,
            "inactive_strategies": total_strategies - active_strategies,
            "total_triggers": total_triggers,
            "period_backtests": period_backtests,
            "strategy_utilization_rate": (active_strategies / total_strategies * 100) if total_strategies > 0 else 0
        }

    def _calculate_performance_metrics(self, start_date: datetime, end_date: datetime) -> List[PerformanceMetric]:
        """성과 지표 계산"""
        # 현재 기간 데이터
        current_backtests = self._backtest_repository.find_completed_in_period(
            start_date, end_date
        )

        # 이전 기간 데이터 (비교용)
        prev_start = start_date - timedelta(days=(end_date - start_date).days)
        prev_end = start_date
        previous_backtests = self._backtest_repository.find_completed_in_period(
            prev_start, prev_end
        )

        metrics = []

        # 평균 수익률
        current_avg_return = self._calculate_avg_return(current_backtests)
        previous_avg_return = self._calculate_avg_return(previous_backtests)

        metrics.append(PerformanceMetric(
            metric_name="평균 수익률",
            current_value=current_avg_return,
            previous_value=previous_avg_return,
            change_percentage=self._calculate_change_percentage(current_avg_return, previous_avg_return),
            trend=self._determine_trend(current_avg_return, previous_avg_return)
        ))

        # 평균 샤프 비율
        current_avg_sharpe = self._calculate_avg_sharpe(current_backtests)
        previous_avg_sharpe = self._calculate_avg_sharpe(previous_backtests)

        metrics.append(PerformanceMetric(
            metric_name="평균 샤프 비율",
            current_value=current_avg_sharpe,
            previous_value=previous_avg_sharpe,
            change_percentage=self._calculate_change_percentage(current_avg_sharpe, previous_avg_sharpe),
            trend=self._determine_trend(current_avg_sharpe, previous_avg_sharpe)
        ))

        return metrics

    def _generate_trigger_statistics(self, start_date: datetime, end_date: datetime) -> List[TriggerStatistic]:
        """트리거 통계 생성"""
        trigger_stats = self._trigger_repository.get_trigger_statistics_by_variable_type(
            start_date, end_date
        )

        statistics = []
        for stat in trigger_stats:
            statistics.append(TriggerStatistic(
                variable_type=stat["variable_type"],
                total_count=stat["total_count"],
                active_count=stat["active_count"],
                success_rate=stat["success_rate"],
                avg_execution_time_ms=stat["avg_execution_time_ms"]
            ))

        return statistics

    def _get_recent_backtest_results(self, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 백테스트 결과 조회"""
        recent_backtests = self._backtest_repository.find_recent_completed(limit)

        results = []
        for backtest in recent_backtests:
            strategy = self._strategy_repository.find_by_id(backtest.strategy_id)
            results.append({
                "backtest_id": backtest.backtest_id,
                "strategy_name": strategy.name if strategy else "Unknown",
                "completed_at": backtest.completed_at,
                "total_return": backtest.total_return,
                "max_drawdown": backtest.max_drawdown,
                "sharpe_ratio": backtest.sharpe_ratio
            })

        return results

    def _check_system_health(self) -> Dict[str, Any]:
        """시스템 상태 체크"""
        # 기본적인 시스템 상태 지표들
        return {
            "database_status": "healthy",  # 실제로는 DB 연결 체크
            "memory_usage_percentage": 45.2,  # 실제로는 시스템 메모리 사용률
            "active_connections": 12,  # 실제로는 활성 연결 수
            "last_error_count": 0,  # 최근 24시간 에러 수
            "uptime_hours": 72.5  # 시스템 가동 시간
        }

    def _calculate_avg_return(self, backtests: List) -> float:
        """평균 수익률 계산"""
        returns = [bt.total_return for bt in backtests if bt.total_return is not None]
        return sum(returns) / len(returns) if returns else 0.0

    def _calculate_avg_sharpe(self, backtests: List) -> float:
        """평균 샤프 비율 계산"""
        sharpes = [bt.sharpe_ratio for bt in backtests if bt.sharpe_ratio is not None]
        return sum(sharpes) / len(sharpes) if sharpes else 0.0

    def _calculate_change_percentage(self, current: float, previous: float) -> Optional[float]:
        """변화율 계산"""
        if previous == 0:
            return None
        return ((current - previous) / previous) * 100

    def _determine_trend(self, current: float, previous: float) -> str:
        """트렌드 결정"""
        if previous == 0:
            return "STABLE"

        change = ((current - previous) / previous) * 100
        if change > 5:
            return "UP"
        elif change < -5:
            return "DOWN"
        else:
            return "STABLE"
