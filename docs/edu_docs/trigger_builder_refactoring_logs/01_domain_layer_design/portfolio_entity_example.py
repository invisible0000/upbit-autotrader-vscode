#!/usr/bin/env python3
"""
포트폴리오 도메인 엔티티 (Portfolio Domain Entity) - 예시 설계
===============================================================

포트폴리오는 여러 포지션들의 그룹과 전체적인 리스크 관리 설정을 담당합니다.
포지션들 간의 상관관계와 전체 포트폴리오 수준의 리스크를 관리합니다.

Design Principles:
- Position Group Management: 여러 포지션의 그룹 관리
- Portfolio-level Risk Management: 포트폴리오 수준 리스크 제어
- Correlation Management: 포지션 간 상관관계 관리
- Dynamic Rebalancing: 동적 리밸런싱
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum


class PortfolioStatus(Enum):
    """포트폴리오 상태"""
    INACTIVE = "inactive"        # 비활성
    ACTIVE = "active"           # 활성
    PAUSED = "paused"           # 일시정지
    LIQUIDATING = "liquidating"  # 청산 중


@dataclass
class PortfolioConfiguration:
    """포트폴리오 설정"""
    max_total_exposure: Decimal              # 최대 총 노출도
    max_correlation_threshold: Decimal       # 최대 상관관계 임계값
    rebalance_frequency_hours: int           # 리밸런싱 주기 (시간)
    emergency_stop_loss: Decimal             # 비상 손절선 (%)
    diversification_rules: Dict[str, Any]    # 분산투자 규칙
    
    def __post_init__(self):
        if self.max_total_exposure <= 0:
            raise ValueError("최대 총 노출도는 0보다 커야 합니다")


@dataclass
class Portfolio:
    """
    포트폴리오 도메인 엔티티
    
    여러 포지션들의 그룹과 포트폴리오 수준 관리:
    - 포지션들의 컬렉션
    - 포트폴리오 설정
    - 리스크 관리
    - 성과 추적
    """
    
    portfolio_id: str
    name: str
    configuration: PortfolioConfiguration
    positions: List[str] = field(default_factory=list)  # Position IDs
    status: PortfolioStatus = PortfolioStatus.INACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    
    # 성과 추적
    total_invested: Decimal = field(default_factory=lambda: Decimal("0"))
    total_profit_loss: Decimal = field(default_factory=lambda: Decimal("0"))
    
    # 도메인 이벤트
    _domain_events: List[Dict[str, Any]] = field(default_factory=list, init=False, repr=False)
    
    def add_position(self, position_id: str) -> None:
        """포지션 추가"""
        if position_id not in self.positions:
            self.positions.append(position_id)
            self._record_domain_event("position_added_to_portfolio", {
                "portfolio_id": self.portfolio_id,
                "position_id": position_id,
                "total_positions": len(self.positions)
            })
    
    def remove_position(self, position_id: str) -> None:
        """포지션 제거"""
        if position_id in self.positions:
            self.positions.remove(position_id)
            self._record_domain_event("position_removed_from_portfolio", {
                "portfolio_id": self.portfolio_id,
                "position_id": position_id,
                "remaining_positions": len(self.positions)
            })
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """포트폴리오 요약"""
        return {
            "portfolio_id": self.portfolio_id,
            "name": self.name,
            "status": self.status.value,
            "total_positions": len(self.positions),
            "total_invested": float(self.total_invested),
            "total_profit_loss": float(self.total_profit_loss),
            "profit_loss_rate": float(self.total_profit_loss / self.total_invested * 100) if self.total_invested > 0 else 0
        }
    
    def _record_domain_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """도메인 이벤트 기록"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "aggregate_id": self.portfolio_id,
            "event_data": event_data
        }
        self._domain_events.append(event)
