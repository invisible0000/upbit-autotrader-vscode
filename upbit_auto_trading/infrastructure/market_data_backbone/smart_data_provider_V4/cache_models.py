"""
캐시 모델 정의
Smart Data Provider의 캐시 관련 모델을 정의합니다.
"""
from dataclasses import dataclass
from typing import Any, Optional, Dict
from datetime import datetime


@dataclass(frozen=True)
class CacheItem:
    """캐시 아이템"""
    key: str
    data: Any
    cached_at: datetime
    ttl_seconds: float
    source: str  # "sqlite", "memory", "api"

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
    sqlite_hits: int = 0
    memory_hits: int = 0
    api_calls: int = 0

    @property
    def hit_rate(self) -> float:
        """캐시 적중률 (%)"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def miss_rate(self) -> float:
        """캐시 미스율 (%)"""
        return 100.0 - self.hit_rate

    def add_hit(self, source: str) -> None:
        """캐시 히트 기록"""
        self.total_requests += 1
        self.cache_hits += 1

        if source == "sqlite":
            self.sqlite_hits += 1
        elif source == "memory":
            self.memory_hits += 1

    def add_miss(self) -> None:
        """캐시 미스 기록"""
        self.total_requests += 1
        self.cache_misses += 1

    def add_api_call(self) -> None:
        """API 호출 기록"""
        self.api_calls += 1

    def reset(self) -> None:
        """통계 초기화"""
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.sqlite_hits = 0
        self.memory_hits = 0
        self.api_calls = 0

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "sqlite_hits": self.sqlite_hits,
            "memory_hits": self.memory_hits,
            "api_calls": self.api_calls,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate
        }
