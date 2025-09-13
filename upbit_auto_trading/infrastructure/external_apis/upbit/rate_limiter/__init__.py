"""
업비트 Rate Limiter 통합 모듈
- 공개 API 노출 및 편의 함수 제공
- 검색 키워드: init, api, export, public
"""

# 메인 Rate Limiter 클래스
from .upbit_rate_limiter import (
    UnifiedUpbitRateLimiter,
    get_unified_rate_limiter,
    unified_gate_rest_public,
    unified_gate_rest_private,
    notify_unified_429_error,
    get_global_rate_limiter  # 레거시 호환
)

# 타입 정의들
from .upbit_rate_limiter_types import (
    UpbitRateLimitGroup,
    AdaptiveStrategy,
    WaiterState,
    TaskHealth,
    UnifiedRateLimiterConfig,
    WaiterInfo,
    GroupStats,
    Rate429Event,
    HourlyStats,
    TimeConfig
)

# 보조 매니저들
from .upbit_rate_limiter_managers import (
    SelfHealingTaskManager,
    TimeoutAwareRateLimiter,
    AtomicTATManager
)

# 모니터링 시스템
from .upbit_rate_limiter_monitoring import (
    RateLimitMonitor,
    get_rate_limit_monitor,
    log_429_error,
    log_request_success,
    get_daily_429_report
)

# 타이밍 시스템
from .upbit_rate_limiter_timing import (
    PrecisionTimeManager,
    PreciseRateLimitTimer,
    get_global_time_manager,
    get_precise_now,
    calculate_precise_wait,
    create_precision_timer
)

# 공개 API
__all__ = [
    # 메인 클래스
    "UnifiedUpbitRateLimiter",

    # 전역 함수들
    "get_unified_rate_limiter",
    "unified_gate_rest_public",
    "unified_gate_rest_private",
    "notify_unified_429_error",

    # 타입들
    "UpbitRateLimitGroup",
    "AdaptiveStrategy",
    "UnifiedRateLimiterConfig",
    "WaiterState",
    "TaskHealth",

    # 모니터링
    "get_rate_limit_monitor",
    "log_429_error",
    "log_request_success",
    "get_daily_429_report",

    # 타이밍
    "get_global_time_manager",
    "get_precise_now",

    # 레거시 호환
    "get_global_rate_limiter"
]

# 버전 정보
__version__ = "2.0.0"
__author__ = "Upbit Auto Trading System"
__description__ = "통합 업비트 Rate Limiter - Lock-Free + Dynamic + Zero-429"
