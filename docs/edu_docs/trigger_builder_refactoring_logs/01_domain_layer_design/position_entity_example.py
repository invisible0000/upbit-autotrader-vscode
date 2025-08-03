#!/usr/bin/env python3
"""
포지션 도메인 엔티티 (Position Domain Entity) - 예시 설계
================================================================

포지션은 특정 종목에 대한 매매 전략의 실행 인스턴스입니다.
하나의 전략과 설정을 가지며, 실시간 포지션 상태를 관리합니다.

Design Principles:
- Strategy Execution Instance: 전략의 실행 단위
- Real-time State Management: 실시간 포지션 상태 추적
- Configuration Management: 포지션별 설정 관리
- Lifecycle Management: 생성부터 종료까지 완전한 생명주기
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ..value_objects.strategy_id import StrategyId
from .strategy import Strategy
from .management_rule import PositionState
from ..exceptions.domain_exceptions import DomainException


class PositionStatus(Enum):
    """포지션 상태"""
    WAITING = "waiting"          # 진입 대기
    ACTIVE = "active"            # 활성 포지션
    CLOSED = "closed"            # 종료된 포지션
    SUSPENDED = "suspended"      # 일시 중단


class PositionConfigurationError(DomainException):
    """포지션 설정 오류"""
    pass


@dataclass
class PositionConfiguration:
    """포지션 설정 값 객체"""
    symbol: str                              # 거래 종목
    initial_amount: Decimal                  # 초기 투자 금액
    max_position_size: Decimal               # 최대 포지션 크기
    risk_per_trade: Decimal                  # 거래당 리스크 (%)
    max_drawdown_limit: Decimal              # 최대 손실 한도 (%)
    auto_rebalance: bool = True              # 자동 리밸런싱
    
    def __post_init__(self):
        if self.initial_amount <= 0:
            raise ValueError("초기 투자 금액은 0보다 커야 합니다")
        if self.risk_per_trade <= 0 or self.risk_per_trade > 50:
            raise ValueError("거래당 리스크는 0%~50% 범위여야 합니다")


@dataclass
class Position:
    """
    포지션 도메인 엔티티
    
    특정 종목에 대한 전략 실행 인스턴스:
    - 하나의 전략 참조
    - 포지션별 설정
    - 실시간 상태 관리
    - 도메인 이벤트 발생
    """
    
    position_id: str
    strategy: Strategy                       # 실행할 전략
    configuration: PositionConfiguration     # 포지션 설정
    status: PositionStatus = PositionStatus.WAITING
    created_at: datetime = field(default_factory=datetime.now)
    activated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # 실시간 상태
    current_position_state: Optional[PositionState] = None
    total_invested: Decimal = field(default_factory=lambda: Decimal("0"))
    realized_profit: Decimal = field(default_factory=lambda: Decimal("0"))
    
    # 도메인 이벤트
    _domain_events: List[Dict[str, Any]] = field(default_factory=list, init=False, repr=False)
    
    def __post_init__(self):
        self._record_domain_event("position_created", {
            "position_id": self.position_id,
            "strategy_id": str(self.strategy.strategy_id),
            "symbol": self.configuration.symbol
        })
    
    def activate(self) -> None:
        """포지션 활성화"""
        if self.status == PositionStatus.WAITING:
            self.status = PositionStatus.ACTIVE
            self.activated_at = datetime.now()
            self._record_domain_event("position_activated", {
                "position_id": self.position_id
            })
    
    def update_position_state(self, new_state: PositionState) -> None:
        """포지션 상태 업데이트"""
        old_state = self.current_position_state
        self.current_position_state = new_state
        
        self._record_domain_event("position_state_updated", {
            "position_id": self.position_id,
            "old_profit_rate": float(old_state.get_profit_rate()) if old_state else 0,
            "new_profit_rate": float(new_state.get_profit_rate())
        })
    
    def close_position(self, reason: str) -> None:
        """포지션 종료"""
        if self.status == PositionStatus.ACTIVE:
            self.status = PositionStatus.CLOSED
            self.closed_at = datetime.now()
            
            final_profit = self.current_position_state.get_profit_amount() if self.current_position_state else Decimal("0")
            self.realized_profit = final_profit
            
            self._record_domain_event("position_closed", {
                "position_id": self.position_id,
                "reason": reason,
                "final_profit": float(final_profit)
            })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """포지션 성과 요약"""
        if self.current_position_state:
            profit_rate = self.current_position_state.get_profit_rate()
            profit_amount = self.current_position_state.get_profit_amount()
            holding_time = self.current_position_state.get_holding_time()
        else:
            profit_rate = Decimal("0")
            profit_amount = Decimal("0")
            holding_time = None
        
        return {
            "position_id": self.position_id,
            "status": self.status.value,
            "symbol": self.configuration.symbol,
            "profit_rate": float(profit_rate),
            "profit_amount": float(profit_amount),
            "holding_time_hours": holding_time.total_seconds() / 3600 if holding_time else 0,
            "total_invested": float(self.total_invested),
            "realized_profit": float(self.realized_profit)
        }
    
    def _record_domain_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """도메인 이벤트 기록"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "aggregate_id": self.position_id,
            "event_data": event_data
        }
        self._domain_events.append(event)


# 포지션 팩토리 함수
def create_position(position_id: str, strategy: Strategy, symbol: str, 
                   initial_amount: Decimal) -> Position:
    """포지션 생성 팩토리"""
    config = PositionConfiguration(
        symbol=symbol,
        initial_amount=initial_amount,
        max_position_size=initial_amount * Decimal("2"),  # 2배까지 확장 가능
        risk_per_trade=Decimal("2"),  # 2% 리스크
        max_drawdown_limit=Decimal("10")  # 10% 최대 손실
    )
    
    return Position(
        position_id=position_id,
        strategy=strategy,
        configuration=config
    )
