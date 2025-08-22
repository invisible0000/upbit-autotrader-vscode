"""
라우팅 컨텍스트 모델

Usage Context와 Network Policy를 정의하여 적응형 라우팅의 기준을 제공합니다.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class UsageContext(Enum):
    """사용 컨텍스트 타입"""
    REALTIME_TRADING = "realtime_trading"     # 실거래 봇 (최고 우선순위)
    MARKET_SCANNING = "market_scanning"       # 시장 스캐닝 (대량 심볼)
    STRATEGY_BACKTESTING = "backtesting"      # 백테스팅 (성능보다 안정성)
    PORTFOLIO_MONITORING = "monitoring"       # 포트폴리오 모니터링
    RESEARCH_ANALYSIS = "research"            # 연구/분석 목적
    SYSTEM_MAINTENANCE = "maintenance"        # 시스템 유지보수


class NetworkPolicy(Enum):
    """네트워크 정책"""
    AGGRESSIVE = "aggressive"     # 최고 성능, 네트워크 사용량 무시
    BALANCED = "balanced"         # 성능과 효율성 균형
    CONSERVATIVE = "conservative"  # 네트워크 효율성 우선
    MINIMAL = "minimal"           # 최소 네트워크 사용


@dataclass(frozen=True)
class RoutingContext:
    """라우팅 컨텍스트

    라우팅 결정에 필요한 모든 컨텍스트 정보를 포함합니다.
    """
    usage_context: UsageContext
    network_policy: NetworkPolicy
    session_id: str
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """생성 시간 자동 설정"""
        if self.created_at is None:
            object.__setattr__(self, 'created_at', datetime.now())

    @property
    def requires_realtime(self) -> bool:
        """실시간 데이터 필요 여부"""
        return self.usage_context in [
            UsageContext.REALTIME_TRADING,
            UsageContext.PORTFOLIO_MONITORING
        ]

    @property
    def allows_batch_delay(self) -> bool:
        """배치 지연 허용 여부"""
        return self.usage_context in [
            UsageContext.MARKET_SCANNING,
            UsageContext.STRATEGY_BACKTESTING,
            UsageContext.RESEARCH_ANALYSIS
        ]

    @property
    def priority_weight(self) -> float:
        """우선순위 가중치 (0.0-1.0)"""
        weights = {
            UsageContext.REALTIME_TRADING: 1.0,
            UsageContext.PORTFOLIO_MONITORING: 0.8,
            UsageContext.MARKET_SCANNING: 0.6,
            UsageContext.RESEARCH_ANALYSIS: 0.4,
            UsageContext.STRATEGY_BACKTESTING: 0.3,
            UsageContext.SYSTEM_MAINTENANCE: 0.1
        }
        return weights.get(self.usage_context, 0.5)

    @property
    def network_tolerance(self) -> float:
        """네트워크 사용량 허용도 (0.0-1.0)"""
        tolerances = {
            NetworkPolicy.AGGRESSIVE: 1.0,
            NetworkPolicy.BALANCED: 0.7,
            NetworkPolicy.CONSERVATIVE: 0.4,
            NetworkPolicy.MINIMAL: 0.2
        }
        return tolerances.get(self.network_policy, 0.5)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'usage_context': self.usage_context.value,
            'network_policy': self.network_policy.value,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'requires_realtime': self.requires_realtime,
            'allows_batch_delay': self.allows_batch_delay,
            'priority_weight': self.priority_weight,
            'network_tolerance': self.network_tolerance
        }

    @classmethod
    def create_trading_context(cls, session_id: str, user_id: Optional[str] = None) -> 'RoutingContext':
        """실거래 컨텍스트 생성"""
        return cls(
            usage_context=UsageContext.REALTIME_TRADING,
            network_policy=NetworkPolicy.AGGRESSIVE,
            session_id=session_id,
            user_id=user_id
        )

    @classmethod
    def create_scanning_context(cls, session_id: str, symbols_count: int = 1) -> 'RoutingContext':
        """시장 스캐닝 컨텍스트 생성"""
        # 대량 심볼 처리시 Conservative 정책 적용
        policy = NetworkPolicy.CONSERVATIVE if symbols_count > 50 else NetworkPolicy.BALANCED

        return cls(
            usage_context=UsageContext.MARKET_SCANNING,
            network_policy=policy,
            session_id=session_id
        )

    @classmethod
    def create_research_context(cls, session_id: str) -> 'RoutingContext':
        """연구/분석 컨텍스트 생성"""
        return cls(
            usage_context=UsageContext.RESEARCH_ANALYSIS,
            network_policy=NetworkPolicy.MINIMAL,
            session_id=session_id
        )
