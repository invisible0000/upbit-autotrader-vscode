"""
Market Data Router 인터페이스

Test 08-11 검증 기반 5-Tier 적응형 라우팅을 위한 핵심 인터페이스입니다.
Usage Context와 네트워크 효율성을 고려한 지능형 데이터 라우팅을 제공합니다.

핵심 혁신:
1. Usage Context 기반 자동 Tier 선택
2. 네트워크 사용량 실시간 최적화
3. 5-Tier 성능 보장 (0.1ms ~ 500ms)
4. 189개 심볼까지 확장 가능 (Test 검증)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

from ..models.routing_context import RoutingContext, UsageContext, NetworkPolicy
from ..models.routing_request import RoutingRequest
from ..models.routing_response import RoutingResponse


class RoutingTier(Enum):
    """라우팅 계층"""
    HOT_CACHE = "hot_cache"           # Tier 1: 0.1ms (메모리 직접)
    LIVE_SUBSCRIPTION = "live_sub"    # Tier 2: 0.2ms (개별 구독)
    BATCH_SNAPSHOT = "batch_snap"     # Tier 3: 11.20ms (배치 구독)
    WARM_CACHE_REST = "warm_rest"     # Tier 4: 200ms (캐시+REST)
    COLD_REST = "cold_rest"           # Tier 5: 500ms (순수 REST)


class DataType(Enum):
    """데이터 타입"""
    CANDLE = "candle"
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADE = "trade"


class Priority(Enum):
    """우선순위"""
    CRITICAL = "critical"     # 실거래봇 (최고 성능)
    HIGH = "high"            # 실시간 모니터링
    NORMAL = "normal"        # 일반 요청
    LOW = "low"             # 백테스팅 등


class IMarketDataRouter(ABC):
    """Market Data Router 인터페이스

    Test 08-11 검증 기반 5-Tier 적응형 라우팅 시스템
    """

    @abstractmethod
    async def route_data_request(
        self,
        request: RoutingRequest,
        context: RoutingContext,
        priority: Priority = Priority.NORMAL
    ) -> RoutingResponse:
        """데이터 요청 라우팅

        Args:
            request: 라우팅 요청 (심볼, 데이터 타입 등)
            context: 사용 컨텍스트 (REALTIME_TRADING, MARKET_SCANNING 등)
            priority: 우선순위 (CRITICAL ~ LOW)

        Returns:
            최적화된 라우팅으로 제공된 데이터 응답
        """
        pass

    @abstractmethod
    async def get_optimal_tier(
        self,
        request: RoutingRequest,
        context: RoutingContext,
        current_network_usage: float
    ) -> RoutingTier:
        """최적 라우팅 Tier 결정

        Args:
            request: 라우팅 요청
            context: 사용 컨텍스트
            current_network_usage: 현재 네트워크 사용량 (0.0-1.0)

        Returns:
            최적 라우팅 Tier
        """
        pass

    @abstractmethod
    async def optimize_network_usage(
        self,
        usage_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """네트워크 사용량 최적화

        Args:
            usage_threshold: 네트워크 사용량 임계값 (0.8 = 80%)

        Returns:
            최적화 결과 및 권장사항
        """
        pass

    @abstractmethod
    async def get_routing_stats(self) -> Dict[str, Any]:
        """라우팅 통계 조회

        Returns:
            Tier별 사용률, 성능 지표, 네트워크 사용량 등
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """라우터 상태 확인

        Returns:
            각 Tier 상태, 전체 시스템 건강도
        """
        pass
