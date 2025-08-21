"""
라우팅 응답 모델

시장 데이터 라우팅 결과와 성능 메트릭을 포함한 응답 모델입니다.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .routing_request import RoutingRequest


class RoutingTier(Enum):
    """라우팅 계층"""
    HOT_CACHE = "hot_cache"           # Tier 1: 0.1ms (메모리 직접)
    LIVE_SUBSCRIPTION = "live_sub"    # Tier 2: 0.2ms (개별 구독)
    BATCH_SNAPSHOT = "batch_snap"     # Tier 3: 11.20ms (배치 구독)
    WARM_CACHE_REST = "warm_rest"     # Tier 4: 200ms (캐시+REST)
    COLD_REST = "cold_rest"           # Tier 5: 500ms (순수 REST)


class ResponseStatus(Enum):
    """응답 상태"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


@dataclass(frozen=True)
class PerformanceMetrics:
    """성능 메트릭"""
    response_time_ms: float
    data_freshness_ms: int  # 데이터 신선도 (현재시간 - 데이터시간)
    cache_hit_ratio: float  # 캐시 적중률 (0.0-1.0)
    network_bytes: int      # 네트워크 사용량 (bytes)
    symbols_per_second: float  # 처리된 심볼/초

    @property
    def is_realtime_quality(self) -> bool:
        """실시간 품질 여부 (5초 이내 데이터)"""
        return self.data_freshness_ms <= 5000

    @property
    def performance_grade(self) -> str:
        """성능 등급 (A-F)"""
        if self.response_time_ms <= 1:
            return "A+"
        elif self.response_time_ms <= 10:
            return "A"
        elif self.response_time_ms <= 50:
            return "B"
        elif self.response_time_ms <= 200:
            return "C"
        elif self.response_time_ms <= 500:
            return "D"
        else:
            return "F"


@dataclass(frozen=True)
class RoutingResponse:
    """라우팅 응답

    요청 처리 결과와 성능 정보를 포함한 응답입니다.
    """
    request_id: str
    status: ResponseStatus
    tier_used: RoutingTier
    data: Dict[str, Any]  # 심볼별 데이터
    performance: PerformanceMetrics

    # 타이밍 정보
    requested_at: datetime
    processed_at: datetime
    responded_at: datetime

    # 추가 정보
    symbols_requested: int
    symbols_delivered: int
    fallback_tiers_used: Optional[List[RoutingTier]] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """후처리"""
        if self.fallback_tiers_used is None:
            object.__setattr__(self, 'fallback_tiers_used', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
        if self.errors is None:
            object.__setattr__(self, 'errors', [])

    @property
    def success_rate(self) -> float:
        """성공률 (0.0-1.0)"""
        if self.symbols_requested == 0:
            return 0.0
        return self.symbols_delivered / self.symbols_requested

    @property
    def is_complete_success(self) -> bool:
        """완전 성공 여부"""
        return self.status == ResponseStatus.SUCCESS and self.success_rate == 1.0

    @property
    def total_processing_time_ms(self) -> float:
        """총 처리 시간 (ms)"""
        return (self.responded_at - self.requested_at).total_seconds() * 1000

    @property
    def has_warnings(self) -> bool:
        """경고 존재 여부"""
        return (self.warnings is not None) and len(self.warnings) > 0

    @property
    def has_errors(self) -> bool:
        """오류 존재 여부"""
        return (self.errors is not None) and len(self.errors) > 0

    @property
    def used_fallback(self) -> bool:
        """폴백 사용 여부"""
        return (self.fallback_tiers_used is not None) and len(self.fallback_tiers_used) > 0

    def get_symbol_data(self, symbol: str) -> Optional[Any]:
        """특정 심볼 데이터 조회"""
        return self.data.get(symbol)

    def get_all_symbols(self) -> List[str]:
        """모든 심볼 목록 조회"""
        return list(self.data.keys())

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'request_id': self.request_id,
            'status': self.status.value,
            'tier_used': self.tier_used.value,
            'success_rate': self.success_rate,
            'symbols_requested': self.symbols_requested,
            'symbols_delivered': self.symbols_delivered,
            'total_processing_time_ms': self.total_processing_time_ms,
            'performance': {
                'response_time_ms': self.performance.response_time_ms,
                'data_freshness_ms': self.performance.data_freshness_ms,
                'cache_hit_ratio': self.performance.cache_hit_ratio,
                'network_bytes': self.performance.network_bytes,
                'symbols_per_second': self.performance.symbols_per_second,
                'performance_grade': self.performance.performance_grade,
                'is_realtime_quality': self.performance.is_realtime_quality
            },
            'timing': {
                'requested_at': self.requested_at.isoformat(),
                'processed_at': self.processed_at.isoformat(),
                'responded_at': self.responded_at.isoformat()
            },
            'fallback_tiers_used': [tier.value for tier in (self.fallback_tiers_used or [])],
            'warnings': self.warnings or [],
            'errors': self.errors or [],
            'has_warnings': self.has_warnings,
            'has_errors': self.has_errors,
            'used_fallback': self.used_fallback,
            'metadata': self.metadata
        }

    @classmethod
    def create_success_response(
        cls,
        request: RoutingRequest,
        tier_used: RoutingTier,
        data: Dict[str, Any],
        performance: PerformanceMetrics,
        processed_at: datetime,
        responded_at: datetime
    ) -> 'RoutingResponse':
        """성공 응답 생성"""
        return cls(
            request_id=request.request_id or "unknown",
            status=ResponseStatus.SUCCESS,
            tier_used=tier_used,
            data=data,
            performance=performance,
            requested_at=request.requested_at or datetime.now(),
            processed_at=processed_at,
            responded_at=responded_at,
            symbols_requested=len(request.symbols),
            symbols_delivered=len(data)
        )

    @classmethod
    def create_partial_response(
        cls,
        request: RoutingRequest,
        tier_used: RoutingTier,
        data: Dict[str, Any],
        performance: PerformanceMetrics,
        processed_at: datetime,
        responded_at: datetime,
        errors: List[str],
        fallback_tiers: Optional[List[RoutingTier]] = None
    ) -> 'RoutingResponse':
        """부분 성공 응답 생성"""
        return cls(
            request_id=request.request_id or "unknown",
            status=ResponseStatus.PARTIAL_SUCCESS,
            tier_used=tier_used,
            data=data,
            performance=performance,
            requested_at=request.requested_at or datetime.now(),
            processed_at=processed_at,
            responded_at=responded_at,
            symbols_requested=len(request.symbols),
            symbols_delivered=len(data),
            fallback_tiers_used=fallback_tiers,
            errors=errors
        )

    @classmethod
    def create_error_response(
        cls,
        request: RoutingRequest,
        tier_used: RoutingTier,
        error_message: str,
        processed_at: datetime,
        responded_at: datetime
    ) -> 'RoutingResponse':
        """오류 응답 생성"""
        # 기본 성능 메트릭 (오류 상황)
        performance = PerformanceMetrics(
            response_time_ms=(responded_at - processed_at).total_seconds() * 1000,
            data_freshness_ms=0,
            cache_hit_ratio=0.0,
            network_bytes=0,
            symbols_per_second=0.0
        )

        return cls(
            request_id=request.request_id or "unknown",
            status=ResponseStatus.FAILED,
            tier_used=tier_used,
            data={},
            performance=performance,
            requested_at=request.requested_at or datetime.now(),
            processed_at=processed_at,
            responded_at=responded_at,
            symbols_requested=len(request.symbols),
            symbols_delivered=0,
            errors=[error_message]
        )
