"""
업비트 Rate Limiter 타입 정의
- 모든 Enum, dataclass, 설정 타입들
- 검색 키워드: types, enum, dataclass, config
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class UpbitRateLimitGroup(Enum):
    """업비트 API Rate Limit 그룹 (공식 문서 기준)"""
    REST_PUBLIC = "rest_public"              # 10 RPS
    REST_PRIVATE_DEFAULT = "rest_private_default"  # 30 RPS
    REST_PRIVATE_ORDER = "rest_private_order"      # 8 RPS
    REST_PRIVATE_CANCEL_ALL = "rest_private_cancel_all"  # 0.5 RPS (2초당 1회)
    WEBSOCKET = "websocket"                  # 5 RPS AND 100 RPM


class AdaptiveStrategy(Enum):
    """적응형 전략"""
    CONSERVATIVE = "conservative"  # Zero-429 우선
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class WaiterState(Enum):
    """대기자 상태"""
    WAITING = "waiting"
    READY = "ready"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class TaskHealth(Enum):
    """태스크 건강 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class UnifiedRateLimiterConfig:
    """통합 Rate Limiter 설정"""
    # 기본 GCRA 설정
    rps: float
    burst_capacity: int

    # 🆕 사용자 승인 설계: base_window_size와 upbit_monitoring_interval
    base_window_size: Optional[int] = None           # 업비트 기준 최대 허용량 (보통 RPS와 동일)
    upbit_monitoring_interval: float = 1.0           # 업비트 기본 모니터링 간격 (초)

    # 호환성 제거: timestamp_window_size 완전 제거, burst_capacity가 윈도우 크기 결정

    # 🆕 웹소켓 복합 제한 설정
    rpm: Optional[int] = None                        # 분당 요청 제한 (100 RPM 등)
    rpm_burst_capacity: Optional[int] = None         # 분당 버스트 용량 (10개 등)
    rpm_monitoring_interval: float = 60.0            # RPM 모니터링 간격 (초)
    enable_dual_limit: bool = False                  # 이중 제한 활성화 (RPS + RPM)

    # 동적 조정 설정
    enable_dynamic_adjustment: bool = True
    error_429_threshold: int = 1  # Zero-429 정책
    error_429_window: float = 60.0
    reduction_ratio: float = 0.8
    min_ratio: float = 0.5
    recovery_delay: float = 300.0  # 5분 보수적 복구
    recovery_step: float = 0.05
    recovery_interval: float = 30.0

    # 예방적 스로틀링 설정
    enable_preventive_throttling: bool = True
    preventive_window: float = 30.0  # 429 에러 후 예방 윈도우 (초)
    max_preventive_delay: float = 0.5  # 최대 지연 (초)
    preventive_decay_factor: float = 0.5  # 시간 경과에 따른 지연 감소 (새 옵션)

    # 전략
    strategy: AdaptiveStrategy = AdaptiveStrategy.CONSERVATIVE

    @classmethod
    def from_rps(cls, rps: float, burst_capacity: int = None, **kwargs):
        """RPS 기반 설정 생성"""
        if burst_capacity is None:
            burst_capacity = max(1, int(rps))

        return cls(rps=rps, burst_capacity=burst_capacity, **kwargs)

    @property
    def emission_interval(self) -> float:
        """토큰 배출 간격"""
        return 1.0 / self.rps

    @property
    def increment(self) -> float:
        """TAT 증가량"""
        return self.emission_interval


@dataclass
class WaiterInfo:
    """대기자 정보"""
    future: asyncio.Future
    requested_at: float
    ready_at: float
    group: UpbitRateLimitGroup
    endpoint: str
    state: WaiterState = WaiterState.WAITING
    waiter_id: str = ""
    timeout_task: Optional[asyncio.Task] = None  # 타임아웃 태스크
    created_at: float = 0.0  # 생성 시간


@dataclass
class GroupStats:
    """그룹별 통계 및 동적 상태"""
    # 기본 통계
    total_requests: int = 0
    total_waits: int = 0
    total_wait_time: float = 0.0
    concurrent_waiters: int = 0
    max_concurrent_waiters: int = 0
    race_conditions_prevented: int = 0

    # 429 관련
    error_429_count: int = 0
    error_429_history: List[float] = field(default_factory=list)

    # 동적 조정
    current_rate_ratio: float = 1.0
    last_reduction_time: Optional[float] = None
    last_recovery_time: Optional[float] = None
    original_config: Optional[UnifiedRateLimiterConfig] = None

    def add_429_error(self, timestamp: float):
        """429 에러 기록"""
        self.error_429_count += 1
        self.error_429_history.append(timestamp)

        # 1시간 이상 된 기록 정리
        cutoff = timestamp - 3600.0
        self.error_429_history = [t for t in self.error_429_history if t > cutoff]


# === 모니터링 관련 타입들 ===

@dataclass
class Rate429Event:
    """429 에러 이벤트 상세 정보"""
    timestamp: float
    datetime_str: str
    endpoint: str
    method: str
    retry_after: Optional[float]
    attempt_number: int
    rate_limiter_type: str  # 'dynamic' or 'legacy'
    current_rate_ratio: Optional[float]  # 동적 리미터의 현재 비율
    response_headers: Dict[str, str]
    response_body: str
    context: Dict[str, Any]  # 추가 컨텍스트 정보


@dataclass
class HourlyStats:
    """시간대별 통계"""
    hour: int
    total_requests: int = 0
    error_429_count: int = 0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    rate_reductions: int = 0  # 동적 조정 발생 횟수


# === 타이밍 관련 타입들 ===

@dataclass
class TimeConfig:
    """시간 관리 설정"""
    # Redis 방식: 2017년 1월 1일을 기준점으로 사용 (큰 숫자 방지)
    EPOCH_OFFSET: float = 1483228800.0  # 2017-01-01 00:00:00 UTC

    # 정밀도 설정
    NANOSECOND_PRECISION: bool = True
    DECIMAL_PRECISION: int = 28

    # Clock drift 보상
    DRIFT_CHECK_INTERVAL: float = 60.0  # 1분마다 드리프트 체크
    MAX_DRIFT_TOLERANCE: float = 0.001  # 1ms 드리프트 허용
