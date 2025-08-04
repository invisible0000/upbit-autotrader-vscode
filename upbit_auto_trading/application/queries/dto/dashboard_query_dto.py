"""
대시보드 관련 Query DTO 정의
실시간 모니터링 및 성과 지표를 위한 데이터 전송 객체들
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class DashboardQuery:
    """대시보드 조회 쿼리"""
    date_range_days: int = 30
    include_performance_charts: bool = True
    include_trigger_stats: bool = True


@dataclass
class PerformanceMetric:
    """성과 지표"""
    metric_name: str
    current_value: float
    previous_value: Optional[float]
    change_percentage: Optional[float]
    trend: str  # UP, DOWN, STABLE


@dataclass
class TriggerStatistic:
    """트리거 통계"""
    variable_type: str
    total_count: int
    active_count: int
    success_rate: float
    avg_execution_time_ms: float


@dataclass
class DashboardResponse:
    """대시보드 응답 DTO"""
    summary_stats: Dict[str, Any]
    performance_metrics: List[PerformanceMetric]
    trigger_statistics: List[TriggerStatistic]
    active_strategies_count: int
    recent_backtest_results: List[Dict[str, Any]]
    system_health: Dict[str, Any]
    generated_at: datetime
