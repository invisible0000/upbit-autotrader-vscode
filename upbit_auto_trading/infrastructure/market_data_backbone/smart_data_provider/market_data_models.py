"""
Market Data Models - 통합 모델 시스템

모든 SmartDataProvider V4.0의 데이터 모델을 통합 관리
- DataResponse, Priority (핵심 API 모델)
- CacheModels (캐시 성능 지표)
- CollectionModels (빈 캔들 추적)
- 성능 지표 모델
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from enum import Enum
from decimal import Decimal


# =====================================
# 🎯 핵심 API 모델
# =====================================

@dataclass
class DataResponse:
    """
    통합 데이터 응답 모델

    모든 API 메서드의 표준 응답 형식
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    cache_hit: bool = False
    response_time_ms: float = 0.0
    data_source: str = "unknown"

    @classmethod
    def create_success(cls, data: Dict[str, Any], **metadata) -> 'DataResponse':
        """성공 응답 생성"""
        return cls(
            success=True,
            data=data,
            cache_hit=metadata.get('cache_hit', False),
            response_time_ms=metadata.get('response_time_ms', 0.0),
            data_source=metadata.get('data_source', 'api')
        )

    @classmethod
    def create_error(cls, error: str, **metadata) -> 'DataResponse':
        """실패 응답 생성"""
        return cls(
            success=False,
            error_message=error,
            cache_hit=metadata.get('cache_hit', False),
            response_time_ms=metadata.get('response_time_ms', 0.0),
            data_source=metadata.get('data_source', 'error')
        )

    def get(self, key: Optional[str] = None) -> Any:
        """키별 데이터 반환 또는 전체 Dict 반환"""
        if key:
            return self.data.get(key, {})
        return self.data

    def get_single(self, symbol: str) -> Dict[str, Any]:
        """단일 심볼 데이터 반환"""
        return self.data.get(symbol, {})

    def get_all(self) -> Dict[str, Any]:
        """전체 Dict 데이터 반환"""
        return self.data


class Priority(Enum):
    """
    통합 우선순위 시스템

    SmartRouter와 완전 호환되는 우선순위 정책
    """
    CRITICAL = 1    # 실거래봇 (< 50ms)
    HIGH = 2        # 실시간 모니터링 (< 100ms)
    NORMAL = 3      # 차트뷰어 (< 500ms)
    LOW = 4         # 백테스터 (백그라운드)

    @property
    def max_response_time_ms(self) -> float:
        """우선순위별 최대 응답 시간 (밀리초)"""
        response_times = {
            Priority.CRITICAL: 50.0,
            Priority.HIGH: 100.0,
            Priority.NORMAL: 500.0,
            Priority.LOW: 5000.0
        }
        return response_times[self]

    @property
    def description(self) -> str:
        """우선순위 설명"""
        descriptions = {
            Priority.CRITICAL: "실거래봇 (최우선)",
            Priority.HIGH: "실시간 모니터링",
            Priority.NORMAL: "차트뷰어",
            Priority.LOW: "백테스터 (백그라운드)"
        }
        return descriptions[self]

    @property
    def smart_router_priority(self) -> str:
        """SmartRouter 호환 우선순위 문자열"""
        mapping = {
            Priority.CRITICAL: "high",
            Priority.HIGH: "high",
            Priority.NORMAL: "normal",
            Priority.LOW: "low"
        }
        return mapping[self]

    def __str__(self) -> str:
        return self.description


# =====================================
# 💾 캐시 성능 모델
# =====================================

@dataclass(frozen=True)
class CacheItem:
    """캐시 아이템"""
    key: str
    data: Any
    cached_at: datetime
    ttl_seconds: float
    source: str  # "fast_cache", "memory_cache", "smart_router"

    @property
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        age_seconds = (datetime.now() - self.cached_at).total_seconds()
        return age_seconds > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """캐시 생성 후 경과 시간 (초)"""
        return (datetime.now() - self.cached_at).total_seconds()


@dataclass
class CacheMetrics:
    """캐시 성능 지표"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    fast_cache_hits: int = 0
    memory_cache_hits: int = 0
    smart_router_calls: int = 0

    @property
    def hit_rate(self) -> float:
        """전체 캐시 적중률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def fast_cache_rate(self) -> float:
        """FastCache 적중률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return (self.fast_cache_hits / self.total_requests) * 100


# =====================================
# 📊 수집 상태 모델
# =====================================

class CollectionStatus(Enum):
    """캔들 수집 상태"""
    COLLECTED = "COLLECTED"  # 정상 수집 완료
    EMPTY = "EMPTY"          # 거래가 없어서 빈 캔들
    PENDING = "PENDING"      # 아직 수집하지 않음
    FAILED = "FAILED"        # 수집 실패


@dataclass(frozen=True)
class CollectionStatusRecord:
    """수집 상태 레코드"""
    id: Optional[int]
    symbol: str
    timeframe: str
    target_time: datetime
    collection_status: CollectionStatus
    last_attempt_at: Optional[datetime] = None
    attempt_count: int = 0
    api_response_code: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create_pending(cls, symbol: str, timeframe: str, target_time: datetime) -> 'CollectionStatusRecord':
        """새로운 PENDING 상태 레코드 생성"""
        return cls(
            id=None,
            symbol=symbol,
            timeframe=timeframe,
            target_time=target_time,
            collection_status=CollectionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )


@dataclass
class CandleWithStatus:
    """상태가 포함된 캔들 데이터"""
    # 캔들 데이터
    symbol: str
    timeframe: str
    timestamp: datetime
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[Decimal] = None

    # 상태 정보
    collection_status: CollectionStatus = CollectionStatus.PENDING
    is_empty: bool = False


# =====================================
# 📈 성능 지표 모델
# =====================================

@dataclass
class PerformanceMetrics:
    """성능 지표"""
    # 요청 통계
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # 응답 시간 통계
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0

    # 캐시 통계
    cache_metrics: CacheMetrics = field(default_factory=CacheMetrics)

    # 데이터 통계
    symbols_per_second: float = 0.0
    data_volume_mb: float = 0.0

    @property
    def success_rate(self) -> float:
        """성공률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100


# =====================================
# 🌐 시장 상황 모델
# =====================================

class MarketCondition(Enum):
    """시장 상황"""
    ACTIVE = "ACTIVE"           # 활발한 거래 (높은 변동성)
    NORMAL = "NORMAL"           # 정상 거래
    QUIET = "QUIET"             # 조용한 거래 (낮은 변동성)
    CLOSED = "CLOSED"           # 시장 휴무
    UNKNOWN = "UNKNOWN"         # 상황 불명


class TimeZoneActivity(Enum):
    """시간대별 활동성"""
    ASIA_PRIME = "ASIA_PRIME"       # 아시아 주 거래시간 (09:00-18:00 KST)
    EUROPE_PRIME = "EUROPE_PRIME"   # 유럽 주 거래시간 (15:00-24:00 KST)
    US_PRIME = "US_PRIME"           # 미국 주 거래시간 (22:00-07:00 KST)
    OFF_HOURS = "OFF_HOURS"         # 비활성 시간대


# =====================================
# ⏳ 백그라운드 작업 모델
# =====================================

class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"        # 대기 중
    RUNNING = "running"        # 실행 중
    COMPLETED = "completed"    # 완료
    FAILED = "failed"          # 실패
    CANCELLED = "cancelled"    # 취소


@dataclass
class ProgressStep:
    """진행률 스텝"""
    step_id: str
    description: str
    total_items: int
    completed_items: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """진행률 (%)"""
        if self.total_items == 0:
            return 100.0
        return min(100.0, (self.completed_items / self.total_items) * 100)

    @property
    def is_completed(self) -> bool:
        """완료 여부"""
        return self.completed_items >= self.total_items
