"""
Smart Routing System - Market Data Backbone 핵심 컴포넌트

Test 08-11 검증 기반 5-Tier 적응형 라우팅 시스템입니다.
Usage Context와 네트워크 효율성을 고려한 지능형 데이터 라우팅을 제공합니다.

핵심 성능 지표 (Test 검증 완료):
- Tier 1 Hot Cache: 0.1ms (메모리 직접 액세스)
- Tier 2 Live Subscription: 0.2ms (개별 구독, 6개 이하)
- Tier 3 Batch Snapshot: 11.20ms, 5,241 symbols/sec (189개 심볼)
- Tier 4 Warm Cache + REST: 200ms (중빈도 요청)
- Tier 5 Cold REST: 500ms (과거 데이터, 저빈도)

주요 혁신사항:
1. Usage Context 기반 적응형 라우팅
2. 네트워크 사용량 실시간 최적화
3. 지능형 구독 생명주기 관리
4. 5-Tier 캐시 계층으로 성능과 효율성 양립
5. 기존 20-21개 → 189개 확장 (9배 확장성)

마켓 데이터 백본 통합:
- Layer 1: Smart Routing (이 모듈)
- Layer 2: Market Data Coordinator
- Layer 3: Market Data Storage
- Layer 4: Market Data Backbone API

레거시 백업: legacy/smart_routing_legacy_20250821_162914/
호환성: 기존 IDataRouter 인터페이스 유지
"""

from .core.adaptive_routing_engine import AdaptiveRoutingEngine
from .simple_smart_router import SimpleSmartRouter, get_simple_router, initialize_simple_router
from .improved_simple_router import ImprovedSimpleRouter, get_improved_router, initialize_improved_router

from .interfaces.market_data_router import IMarketDataRouter

from .models.routing_context import RoutingContext, UsageContext, NetworkPolicy
from .models.routing_request import RoutingRequest, DataType, TimeFrame
from .models.routing_response import RoutingResponse, RoutingTier, ResponseStatus, PerformanceMetrics

__version__ = "1.0.0"
__all__ = [
    # 핵심 엔진
    "AdaptiveRoutingEngine",

    # 단순 인터페이스
    "SimpleSmartRouter",
    "get_simple_router",
    "initialize_simple_router",

    # 개선된 인터페이스
    "ImprovedSimpleRouter",
    "get_improved_router",
    "initialize_improved_router",

    # 인터페이스
    "IMarketDataRouter",

    # 모델
    "RoutingContext",
    "UsageContext",
    "NetworkPolicy",
    "RoutingRequest",
    "DataType",
    "TimeFrame",
    "RoutingResponse",
    "RoutingTier",
    "ResponseStatus",
    "PerformanceMetrics"
]

# 마켓 데이터 백본 통합 정보
BACKBONE_LAYER = 1
BACKBONE_COMPONENT = "Smart Routing"
BACKBONE_VERSION = "1.0.0"
