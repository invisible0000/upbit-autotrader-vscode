"""
📝 Candle Cache Models
캔들 데이터 캐시 관련 모델들

Created: 2025-09-22
Purpose: 캐시 키, 엔트리, 통계 등 캐시 시스템 전용 모델
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

# TYPE_CHECKING을 사용하여 순환 import 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .candle_core_models import CandleData


@dataclass
class CacheKey:
    """캐시 키 구조화"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int

    def __post_init__(self):
        """캐시 키 검증"""
        if not self.symbol:
            raise ValueError("심볼은 필수입니다")
        if not self.timeframe:
            raise ValueError("타임프레임은 필수입니다")
        if self.count <= 0:
            raise ValueError(f"개수는 1 이상이어야 합니다: {self.count}")

    def to_string(self) -> str:
        """캐시 키를 문자열로 변환"""
        return f"candles_{self.symbol}_{self.timeframe}_{self.start_time.isoformat()}_{self.count}"


@dataclass
class CacheEntry:
    """캐시 엔트리 (데이터 + 메타데이터)"""
    key: CacheKey
    candles: List['CandleData']
    created_at: datetime
    ttl_seconds: int
    data_size_bytes: int

    def __post_init__(self):
        """캐시 엔트리 검증"""
        if self.ttl_seconds <= 0:
            raise ValueError(f"TTL은 1 이상이어야 합니다: {self.ttl_seconds}")
        if self.data_size_bytes < 0:
            raise ValueError(f"데이터 크기는 0 이상이어야 합니다: {self.data_size_bytes}")
        if len(self.candles) != self.key.count:
            raise ValueError(f"캔들 개수({len(self.candles)})와 키 개수({self.key.count})가 다릅니다")

    def is_expired(self, current_time: datetime) -> bool:
        """캐시 만료 여부 확인"""
        elapsed_seconds = (current_time - self.created_at).total_seconds()
        return elapsed_seconds > self.ttl_seconds

    def get_remaining_ttl(self, current_time: datetime) -> int:
        """남은 TTL 초 반환"""
        elapsed_seconds = (current_time - self.created_at).total_seconds()
        remaining = self.ttl_seconds - elapsed_seconds
        return max(0, int(remaining))


@dataclass
class CacheStats:
    """캐시 통계 정보"""
    total_entries: int
    total_memory_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    expired_count: int

    def __post_init__(self):
        """통계 검증"""
        if any(count < 0 for count in [self.total_entries, self.total_memory_bytes,
                                       self.hit_count, self.miss_count,
                                       self.eviction_count, self.expired_count]):
            raise ValueError("모든 통계 값은 0 이상이어야 합니다")

    def get_hit_rate(self) -> float:
        """캐시 히트율 계산"""
        total_requests = self.hit_count + self.miss_count
        if total_requests == 0:
            return 0.0
        return self.hit_count / total_requests

    def get_memory_mb(self) -> float:
        """메모리 사용량 MB 반환"""
        return self.total_memory_bytes / (1024 * 1024)
