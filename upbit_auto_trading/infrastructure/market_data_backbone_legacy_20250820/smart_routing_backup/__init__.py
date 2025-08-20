"""
스마트 라우팅 패키지 초기화

4-파일 구조:
- pattern_analyzer.py: 요청 패턴 분석 (95 lines)
- rate_limiter.py: API 레이트 제한 관리 (43 lines)
- router.py: 스마트 채널 라우팅 (246 lines)
- subscription_manager.py: WebSocket 구독 관리 (397 lines)
"""

from .router import SmartChannelRouter, FieldMapper, create_smart_router
from .pattern_analyzer import IntervalAnalyzer, RequestPatternTracker
from .rate_limiter import RateLimitGuard
from .subscription_manager import WebSocketSubscriptionManager, SubscriptionStatus, create_subscription_manager

__all__ = [
    "SmartChannelRouter",
    "FieldMapper",
    "create_smart_router",
    "IntervalAnalyzer",
    "RequestPatternTracker",
    "RateLimitGuard",
    "WebSocketSubscriptionManager",
    "SubscriptionStatus",
    "create_subscription_manager"
]
