"""
Market Data Cache - 통합 캐시 시스템

Layer 2: 최적화된 캐시 & 성능 시스템
- FastCache (200ms TTL) + MemoryRealtimeCache (TTL+LRU)
- AdaptiveTTL (시장 상황별 동적 조정)
- 성능 모니터링 (적중률, 응답시간)
- 자동 정리 메커니즘
"""
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, time as dt_time
from collections import OrderedDict
from dataclasses import dataclass, field
import statistics

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .market_data_models import (
    CacheItem, CacheMetrics, MarketCondition, TimeZoneActivity,
    PerformanceMetrics
)

logger = create_component_logger("MarketDataCache")


@dataclass
class CacheEntry:
    """통합 캐시 엔트리"""
    data: Any
    timestamp: datetime
    ttl_seconds: float
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        return datetime.now() > (self.timestamp + timedelta(seconds=self.ttl_seconds))

    def update_access(self) -> None:
        """접근 정보 업데이트"""
        self.access_count += 1
        self.last_access = datetime.now()


class FastCache:
    """
    고속 메모리 캐시 - 200ms TTL 고정

    중복 요청 완전 차단을 위한 초단기 캐시
    """

    def __init__(self, default_ttl: float = 0.2):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        self._lock = threading.RLock()

        logger.info(f"FastCache 초기화: TTL {default_ttl}초")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터 조회"""
        with self._lock:
            current_time = time.time()

            # 키가 없으면 미스
            if key not in self._cache:
                self._misses += 1
                return None

            # TTL 체크
            if current_time - self._timestamps[key] > self._default_ttl:
                # 만료된 데이터 삭제
                del self._cache[key]
                del self._timestamps[key]
                self._misses += 1
                return None

            self._hits += 1
            return self._cache[key]

    def set(self, key: str, data: Dict[str, Any]) -> None:
        """캐시에 데이터 저장"""
        with self._lock:
            self._cache[key] = data
            self._timestamps[key] = time.time()

    def clear(self) -> None:
        """캐시 전체 삭제"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            logger.info("FastCache 전체 삭제")

    def cleanup_expired(self) -> int:
        """만료된 데이터 정리"""
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, timestamp in self._timestamps.items():
                if current_time - timestamp > self._default_ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]

            if expired_keys:
                logger.debug(f"FastCache 만료 정리: {len(expired_keys)}개")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'total_keys': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': round(hit_rate, 2),
                'ttl': self._default_ttl,
                'type': 'FastCache'
            }


class MemoryRealtimeCache:
    """
    TTL + LRU 하이브리드 캐시

    실시간 데이터를 위한 고급 메모리 캐시
    """

    def __init__(self, maxsize: int = 1000, default_ttl: float = 60.0):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        logger.info(f"MemoryRealtimeCache 초기화: maxsize={maxsize}, TTL={default_ttl}초")

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # 만료 확인
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None

            # LRU 갱신
            entry.update_access()
            self._cache.move_to_end(key)
            self._hits += 1

            return entry.data

    def set(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        """캐시에 데이터 저장"""
        with self._lock:
            ttl = ttl or self.default_ttl

            # 기존 키 업데이트
            if key in self._cache:
                self._cache[key] = CacheEntry(data, datetime.now(), ttl)
                self._cache.move_to_end(key)
                return

            # 새 키 추가
            self._cache[key] = CacheEntry(data, datetime.now(), ttl)

            # 최대 크기 초과시 LRU 제거
            while len(self._cache) > self.maxsize:
                oldest_key, _ = self._cache.popitem(last=False)
                self._evictions += 1
                logger.debug(f"LRU 제거: {oldest_key}")

    def cleanup_expired(self) -> int:
        """만료된 데이터 정리"""
        with self._lock:
            expired_keys = []

            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"MemoryCache 만료 정리: {len(expired_keys)}개")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'total_keys': len(self._cache),
                'maxsize': self.maxsize,
                'hits': self._hits,
                'misses': self._misses,
                'evictions': self._evictions,
                'hit_rate': round(hit_rate, 2),
                'ttl': self.default_ttl,
                'type': 'MemoryRealtimeCache'
            }


class AdaptiveTtlManager:
    """
    적응형 TTL 관리자

    시장 상황별 동적 TTL 조정
    """

    def __init__(self):
        self._base_ttl = 0.2  # 기본 200ms
        self._current_condition = MarketCondition.NORMAL
        self._current_timezone = TimeZoneActivity.OFF_HOURS

        # TTL 조정 배율
        self._condition_multipliers = {
            MarketCondition.ACTIVE: 0.5,    # 50% 단축 (빠른 변화)
            MarketCondition.NORMAL: 1.0,    # 기본값
            MarketCondition.QUIET: 2.0,     # 200% 연장 (느린 변화)
            MarketCondition.CLOSED: 5.0,    # 500% 연장 (변화 없음)
            MarketCondition.UNKNOWN: 1.0    # 기본값
        }

        self._timezone_multipliers = {
            TimeZoneActivity.ASIA_PRIME: 0.8,     # 20% 단축
            TimeZoneActivity.EUROPE_PRIME: 0.9,   # 10% 단축
            TimeZoneActivity.US_PRIME: 0.7,       # 30% 단축
            TimeZoneActivity.OFF_HOURS: 1.5       # 50% 연장
        }

    def get_adaptive_ttl(self, data_type: str = "ticker") -> float:
        """적응형 TTL 계산"""
        # 데이터 타입별 기본 TTL
        base_ttls = {
            "ticker": 0.2,      # 200ms
            "orderbook": 0.3,   # 300ms
            "trades": 30.0,     # 30초
            "candles": 60.0     # 60초
        }

        base_ttl = base_ttls.get(data_type, self._base_ttl)

        # 시장 상황 배율
        condition_multiplier = self._condition_multipliers[self._current_condition]

        # 시간대 배율
        timezone_multiplier = self._timezone_multipliers[self._current_timezone]

        # 최종 TTL 계산
        adaptive_ttl = base_ttl * condition_multiplier * timezone_multiplier

        # 최소/최대 제한
        return max(0.1, min(300.0, adaptive_ttl))

    def update_market_condition(self, condition: MarketCondition) -> None:
        """시장 상황 업데이트"""
        if self._current_condition != condition:
            logger.info(f"시장 상황 변경: {self._current_condition.value} → {condition.value}")
            self._current_condition = condition

    def detect_timezone_activity(self) -> TimeZoneActivity:
        """현재 시간대 활동성 자동 감지"""
        current_hour = datetime.now().hour

        if 9 <= current_hour < 18:
            return TimeZoneActivity.ASIA_PRIME
        elif 15 <= current_hour < 24:
            return TimeZoneActivity.EUROPE_PRIME
        elif current_hour >= 22 or current_hour < 7:
            return TimeZoneActivity.US_PRIME
        else:
            return TimeZoneActivity.OFF_HOURS

    def get_ttl_stats(self) -> Dict[str, Any]:
        """TTL 통계 반환"""
        return {
            'base_ttl': self._base_ttl,
            'current_condition': self._current_condition.value,
            'current_timezone': self._current_timezone.value,
            'adaptive_ttls': {
                data_type: self.get_adaptive_ttl(data_type)
                for data_type in ["ticker", "orderbook", "trades", "candles"]
            }
        }


class PerformanceMonitor:
    """성능 모니터링 시스템"""

    def __init__(self):
        self._response_times: List[float] = []
        self._start_time = time.time()
        self._request_count = 0
        self._error_count = 0

    def record_request(self, response_time_ms: float, success: bool = True) -> None:
        """요청 기록"""
        self._request_count += 1
        self._response_times.append(response_time_ms)

        if not success:
            self._error_count += 1

        # 최근 1000개 기록만 유지
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-1000:]

    def get_performance_stats(self) -> PerformanceMetrics:
        """성능 통계 반환"""
        if not self._response_times:
            return PerformanceMetrics()

        avg_response_time = statistics.mean(self._response_times)
        min_response_time = min(self._response_times)
        max_response_time = max(self._response_times)

        # 처리량 계산 (requests per second)
        elapsed_time = time.time() - self._start_time
        throughput = self._request_count / elapsed_time if elapsed_time > 0 else 0

        return PerformanceMetrics(
            total_requests=self._request_count,
            successful_requests=self._request_count - self._error_count,
            failed_requests=self._error_count,
            avg_response_time_ms=round(avg_response_time, 2),
            min_response_time_ms=round(min_response_time, 2),
            max_response_time_ms=round(max_response_time, 2),
            symbols_per_second=round(throughput, 2)
        )


class MarketDataCache:
    """통합 캐시 시스템 - Layer 2 메인 클래스"""

    def __init__(self):
        self.fast_cache = FastCache(default_ttl=0.2)
        self.memory_cache = MemoryRealtimeCache(maxsize=1000, default_ttl=60.0)
        self.adaptive_ttl_manager = AdaptiveTtlManager()
        self.performance_monitor = PerformanceMonitor()

        # 자동 정리 스케줄러
        self._last_cleanup = time.time()
        self._cleanup_interval = 60.0  # 60초마다 정리

        logger.info("MarketDataCache 통합 시스템 초기화 완료")

    def get(self, key: str, data_type: str = "ticker") -> Optional[Dict[str, Any]]:
        """계층적 캐시 조회"""
        start_time = time.time()

        # 1. FastCache 먼저 확인 (200ms TTL)
        data = self.fast_cache.get(key)
        if data:
            response_time_ms = (time.time() - start_time) * 1000
            self.performance_monitor.record_request(response_time_ms, True)
            return data

        # 2. MemoryCache 확인 (적응형 TTL)
        data = self.memory_cache.get(key)
        if data:
            # FastCache에도 저장 (이중 캐싱)
            self.fast_cache.set(key, data)
            response_time_ms = (time.time() - start_time) * 1000
            self.performance_monitor.record_request(response_time_ms, True)
            return data

        # 캐시 미스
        response_time_ms = (time.time() - start_time) * 1000
        self.performance_monitor.record_request(response_time_ms, False)
        return None

    def set(self, key: str, data: Dict[str, Any], data_type: str = "ticker") -> None:
        """계층적 캐시 저장"""
        # 적응형 TTL 계산
        adaptive_ttl = self.adaptive_ttl_manager.get_adaptive_ttl(data_type)

        # 두 캐시에 모두 저장
        self.fast_cache.set(key, data)
        self.memory_cache.set(key, data, adaptive_ttl)

    def cleanup_if_needed(self) -> None:
        """필요시 자동 정리"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup()
            self._last_cleanup = current_time

    def _cleanup(self) -> None:
        """캐시 정리 실행"""
        fast_cleaned = self.fast_cache.cleanup_expired()
        memory_cleaned = self.memory_cache.cleanup_expired()

        if fast_cleaned > 0 or memory_cleaned > 0:
            logger.info(f"캐시 정리 완료: FastCache {fast_cleaned}개, MemoryCache {memory_cleaned}개")

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 캐시 통계"""
        self.cleanup_if_needed()

        fast_stats = self.fast_cache.get_stats()
        memory_stats = self.memory_cache.get_stats()
        ttl_stats = self.adaptive_ttl_manager.get_ttl_stats()
        performance_stats = self.performance_monitor.get_performance_stats()

        return {
            'fast_cache': fast_stats,
            'memory_cache': memory_stats,
            'adaptive_ttl': ttl_stats,
            'performance': {
                'total_requests': performance_stats.total_requests,
                'success_rate': performance_stats.success_rate,
                'avg_response_time_ms': performance_stats.avg_response_time_ms,
                'symbols_per_second': performance_stats.symbols_per_second
            },
            'last_cleanup': datetime.fromtimestamp(self._last_cleanup).isoformat()
        }
