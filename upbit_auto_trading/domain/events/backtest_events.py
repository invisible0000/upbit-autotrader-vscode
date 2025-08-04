"""
백테스팅 관련 도메인 이벤트
Backtest Aggregate와 관련된 모든 비즈니스 이벤트 정의
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from . import DomainEvent


@dataclass(frozen=True)
class BacktestStarted(DomainEvent):
    """백테스트 시작 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    timeframe: str
    backtest_settings: Dict[str, Any] = field(default_factory=dict)
    started_by: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "backtest.started"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestDataLoaded(DomainEvent):
    """백테스트 데이터 로드 완료 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    data_points_count: int
    data_start_date: datetime
    data_end_date: datetime
    indicators_calculated: List[str]
    data_load_duration_ms: float

    @property
    def event_type(self) -> str:
        return "backtest.data.loaded"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestSignalGenerated(DomainEvent):
    """백테스트 중 신호 생성 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    signal_timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    signal_price: float
    signal_strength: float
    signal_reason: str
    technical_indicators: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "backtest.signal.generated"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestTradeExecuted(DomainEvent):
    """백테스트 중 거래 실행 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    trade_id: str
    trade_type: str  # 'buy', 'sell'
    execution_timestamp: datetime
    execution_price: float
    execution_quantity: float
    commission: float
    current_capital: float
    current_position: float

    @property
    def event_type(self) -> str:
        return "backtest.trade.executed"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestPositionOpened(DomainEvent):
    """백테스트 중 포지션 개설 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    position_id: str
    entry_timestamp: datetime
    entry_price: float
    position_size: float
    position_value: float

    @property
    def event_type(self) -> str:
        return "backtest.position.opened"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestPositionClosed(DomainEvent):
    """백테스트 중 포지션 종료 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    position_id: str
    exit_timestamp: datetime
    exit_price: float
    position_size: float
    profit_loss: float
    profit_loss_percent: float
    holding_duration_seconds: float

    @property
    def event_type(self) -> str:
        return "backtest.position.closed"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestProgressUpdated(DomainEvent):
    """백테스트 진행률 업데이트 이벤트"""
    backtest_id: str
    strategy_id: str
    progress_percent: float
    current_date: datetime
    processed_points: int
    total_points: int
    estimated_remaining_seconds: float
    current_performance: Dict[str, float] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "backtest.progress.updated"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestCompleted(DomainEvent):
    """백테스트 완료 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    execution_duration_seconds: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    average_holding_time_hours: float
    final_capital: float
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "backtest.completed"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestFailed(DomainEvent):
    """백테스트 실패 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    failure_stage: str  # 'data_loading', 'signal_generation', 'trade_execution', 'metric_calculation'
    error_message: str
    error_type: str
    stack_trace: Optional[str] = None
    partial_results: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "backtest.failed"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestStopped(DomainEvent):
    """백테스트 중단 이벤트"""
    backtest_id: str
    strategy_id: str
    symbol: str
    stop_reason: str
    progress_when_stopped: float
    stopped_by: Optional[str] = None
    partial_results: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "backtest.stopped"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestResultSaved(DomainEvent):
    """백테스트 결과 저장 이벤트"""
    backtest_id: str
    strategy_id: str
    result_storage_id: str
    storage_location: str
    result_summary: Dict[str, Any]
    save_timestamp: datetime

    @property
    def event_type(self) -> str:
        return "backtest.result.saved"

    @property
    def aggregate_id(self) -> str:
        return self.backtest_id


@dataclass(frozen=True)
class BacktestComparisonCompleted(DomainEvent):
    """백테스트 비교 완료 이벤트"""
    comparison_id: str
    backtest_ids: List[str]
    strategy_ids: List[str]
    comparison_metrics: Dict[str, Any]
    best_performing_strategy: str
    comparison_summary: str

    @property
    def event_type(self) -> str:
        return "backtest.comparison.completed"

    @property
    def aggregate_id(self) -> str:
        return self.comparison_id
