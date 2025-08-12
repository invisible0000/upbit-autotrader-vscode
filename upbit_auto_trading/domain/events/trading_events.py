"""
거래 관련 도메인 이벤트
Trade, Order, Position과 관련된 모든 비즈니스 이벤트 정의
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from . import DomainEvent

@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    """주문 생성 이벤트"""
    order_id: str
    strategy_id: str
    symbol: str
    order_type: str  # 'market', 'limit'
    side: str  # 'buy', 'sell'
    quantity: float
    price: Optional[float] = None
    order_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "order.placed"

    @property
    def aggregate_id(self) -> str:
        return self.order_id

@dataclass(frozen=True)
class OrderExecuted(DomainEvent):
    """주문 체결 이벤트"""
    order_id: str
    trade_id: str
    strategy_id: str
    symbol: str
    side: str
    executed_quantity: float
    executed_price: float
    execution_fee: float
    execution_timestamp: datetime
    remaining_quantity: float = 0.0

    @property
    def event_type(self) -> str:
        return "order.executed"

    @property
    def aggregate_id(self) -> str:
        return self.order_id

@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    """주문 취소 이벤트"""
    order_id: str
    strategy_id: str
    symbol: str
    cancellation_reason: str
    cancelled_by: Optional[str] = None
    remaining_quantity: float = 0.0

    @property
    def event_type(self) -> str:
        return "order.cancelled"

    @property
    def aggregate_id(self) -> str:
        return self.order_id

@dataclass(frozen=True)
class OrderFailed(DomainEvent):
    """주문 실패 이벤트"""
    order_id: str
    strategy_id: str
    symbol: str
    failure_reason: str
    error_code: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "order.failed"

    @property
    def aggregate_id(self) -> str:
        return self.order_id

@dataclass(frozen=True)
class PositionOpened(DomainEvent):
    """포지션 개설 이벤트"""
    position_id: str
    strategy_id: str
    symbol: str
    side: str  # 'long', 'short'
    entry_price: float
    quantity: float
    entry_timestamp: datetime
    initial_stop_loss: Optional[float] = None
    initial_take_profit: Optional[float] = None

    @property
    def event_type(self) -> str:
        return "position.opened"

    @property
    def aggregate_id(self) -> str:
        return self.position_id

@dataclass(frozen=True)
class PositionClosed(DomainEvent):
    """포지션 종료 이벤트"""
    position_id: str
    strategy_id: str
    symbol: str
    exit_price: float
    exit_quantity: float
    exit_timestamp: datetime
    profit_loss: float
    profit_loss_percent: float
    holding_duration_seconds: float
    closure_reason: str  # 'take_profit', 'stop_loss', 'manual', 'timeout'

    @property
    def event_type(self) -> str:
        return "position.closed"

    @property
    def aggregate_id(self) -> str:
        return self.position_id

@dataclass(frozen=True)
class PositionUpdated(DomainEvent):
    """포지션 업데이트 이벤트"""
    position_id: str
    strategy_id: str
    symbol: str
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    updated_fields: Dict[str, Any]
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    @property
    def event_type(self) -> str:
        return "position.updated"

    @property
    def aggregate_id(self) -> str:
        return self.position_id

@dataclass(frozen=True)
class TradeCompleted(DomainEvent):
    """거래 완료 이벤트"""
    trade_id: str
    strategy_id: str
    symbol: str
    trade_type: str  # 'round_trip', 'partial'
    entry_price: float
    exit_price: float
    quantity: float
    profit_loss: float
    profit_loss_percent: float
    commission_total: float
    holding_duration_seconds: float
    entry_timestamp: datetime
    exit_timestamp: datetime

    @property
    def event_type(self) -> str:
        return "trade.completed"

    @property
    def aggregate_id(self) -> str:
        return self.trade_id

@dataclass(frozen=True)
class RiskLimitExceeded(DomainEvent):
    """리스크 한계 초과 이벤트"""
    strategy_id: str
    symbol: str
    risk_type: str  # 'max_drawdown', 'position_size', 'daily_loss'
    current_value: float
    limit_value: float
    risk_percentage: float
    triggered_action: str  # 'stop_trading', 'reduce_position', 'alert_only'

    @property
    def event_type(self) -> str:
        return "risk.limit.exceeded"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id

@dataclass(frozen=True)
class MarginCallTriggered(DomainEvent):
    """마진콜 발생 이벤트"""
    strategy_id: str
    symbol: str
    current_margin_ratio: float
    required_margin_ratio: float
    position_value: float
    available_margin: float
    liquidation_risk: bool

    @property
    def event_type(self) -> str:
        return "margin.call.triggered"

    @property
    def aggregate_id(self) -> str:
        return self.strategy_id
