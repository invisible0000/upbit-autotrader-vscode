"""
메모리 실시간 캐시 시스템
티커, 호가, 체결 데이터 등 실시간 데이터의 메모리 캐시를 관리합니다.
"""
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import OrderedDict
import threading

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("MemoryRealtimeCache")


@dataclass
class CacheEntry:
    """캐시 엔트리"""
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


class TTLCache:
    """TTL(Time To Live) 기반 캐시"""

    def __init__(self, maxsize: int = 1000, default_ttl: float = 60.0):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

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
                logger.debug(f"캐시 만료: {key}")
                return None

            # LRU 갱신 (맨 끝으로 이동)
            self._cache.move_to_end(key)
            entry.update_access()
            self._hits += 1

            return entry.data

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """캐시에 데이터 저장"""
        with self._lock:
            ttl = ttl or self.default_ttl

            # 기존 키가 있으면 삭제
            if key in self._cache:
                del self._cache[key]

            # 용량 체크 및 LRU 삭제
            while len(self._cache) >= self.maxsize:
                oldest_key, _ = self._cache.popitem(last=False)  # FIFO
                self._evictions += 1
                logger.debug(f"캐시 용량 초과로 삭제: {oldest_key}")

            # 새 엔트리 추가
            entry = CacheEntry(
                data=value,
                timestamp=datetime.now(),
                ttl_seconds=ttl
            )
            self._cache[key] = entry

    def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """캐시 전체 삭제"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """만료된 엔트리 정리"""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"만료된 캐시 {len(expired_keys)}개 정리 완료")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """캐시 통계"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate
            }

    def __len__(self) -> int:
        return len(self._cache)


class MemoryRealtimeCache:
    """
    실시간 데이터 메모리 캐시 시스템

    - 체결: 최근 체결 내역 (TTL: 30초)
    - 시장 개요: 전체 마켓 정보 (TTL: 60초)

    Note: 호가와 티커는 실시간성 보장을 위해 캐시에서 제외됨
    """

    def __init__(self):
        # 데이터 타입별 전용 캐시 (호가/티커 제외)
        self.trades_cache = TTLCache(maxsize=100, default_ttl=30.0)     # 체결: 30초
        self.market_overview_cache = TTLCache(maxsize=50, default_ttl=60.0)  # 시장 개요: 60초

        # 통합 통계
        self._total_requests = 0
        self._total_hits = 0
        self._lock = threading.RLock()

        # 자동 정리 관련
        self._last_cleanup = datetime.now()
        self._cleanup_interval = 60  # 60초마다 정리

        logger.info("메모리 실시간 캐시 시스템 초기화 완료 (호가/티커 캐시 제외)")

    # =====================================
    # 체결 캐시 API
    # =====================================

    def get_trades(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """체결 데이터 조회"""
        self._update_stats()
        return self.trades_cache.get(f"trades:{symbol}")

    def set_trades(self, symbol: str, trades_data: List[Dict[str, Any]], ttl: Optional[float] = None) -> None:
        """체결 데이터 저장"""
        self.trades_cache.set(f"trades:{symbol}", trades_data, ttl)
        logger.debug(f"체결 캐시 저장: {symbol}, {len(trades_data)}개")

    # =====================================
    # 시장 개요 캐시 API
    # =====================================

    def get_market_overview(self, cache_key: str = "all_markets") -> Optional[Dict[str, Any]]:
        """시장 개요 데이터 조회"""
        self._update_stats()
        return self.market_overview_cache.get(f"market:{cache_key}")

    def set_market_overview(self,
                            overview_data: Dict[str, Any],
                            cache_key: str = "all_markets",
                            ttl: Optional[float] = None) -> None:
        """시장 개요 데이터 저장"""
        self.market_overview_cache.set(f"market:{cache_key}", overview_data, ttl)
        logger.debug(f"시장 개요 캐시 저장: {cache_key}")

    # =====================================
    # 통합 관리 API
    # =====================================

    def invalidate_symbol(self, symbol: str) -> None:
        """특정 심볼의 모든 캐시 무효화 (체결 캐시만)"""
        self.trades_cache.delete(f"trades:{symbol}")
        logger.debug(f"심볼 캐시 무효화: {symbol}")

    def invalidate_all(self) -> None:
        """모든 캐시 무효화"""
        self.trades_cache.clear()
        self.market_overview_cache.clear()
        logger.info("전체 캐시 무효화 완료")

    def cleanup_expired(self) -> Dict[str, int]:
        """만료된 캐시 정리"""
        results = {
            "trades": self.trades_cache.cleanup_expired(),
            "market_overview": self.market_overview_cache.cleanup_expired()
        }

        total_cleaned = sum(results.values())
        if total_cleaned > 0:
            logger.info(f"만료된 캐시 정리 완료: {total_cleaned}개")

        self._last_cleanup = datetime.now()
        return results

    def auto_cleanup_if_needed(self) -> None:
        """필요시 자동 정리 실행"""
        if (datetime.now() - self._last_cleanup).total_seconds() > self._cleanup_interval:
            self.cleanup_expired()

    # =====================================
    # 성능 모니터링
    # =====================================

    def get_performance_stats(self) -> Dict[str, Union[int, float, Dict]]:
        """성능 통계"""
        with self._lock:
            # 개별 캐시 통계 (호가/티커 제외)
            trades_stats = self.trades_cache.get_stats()
            market_stats = self.market_overview_cache.get_stats()

            # 통합 통계
            total_hits = (trades_stats["hits"] + market_stats["hits"])
            total_misses = (trades_stats["misses"] + market_stats["misses"])
            total_requests = total_hits + total_misses
            overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

            total_entries = (len(self.trades_cache) + len(self.market_overview_cache))

            return {
                "overall": {
                    "total_requests": total_requests,
                    "total_hits": total_hits,
                    "total_misses": total_misses,
                    "hit_rate": overall_hit_rate
                },
                "trades": trades_stats,
                "market_overview": market_stats,
                "memory_usage": {
                    "total_entries": total_entries
                }
            }

    def get_memory_usage_mb(self) -> float:
        """메모리 사용량 추정 (MB)"""
        # 간단한 추정: 엔트리당 평균 1KB로 가정
        total_entries = (
            len(self.trades_cache) +
            len(self.market_overview_cache)
        )
        return total_entries * 1.0 / 1024  # KB → MB

    def _update_stats(self) -> None:
        """통계 업데이트"""
        with self._lock:
            self._total_requests += 1

        # 자동 정리 체크
        self.auto_cleanup_if_needed()

    # =====================================
    # 디버깅 및 유틸리티
    # =====================================

    def get_cache_keys(self, cache_type: str) -> List[str]:
        """캐시 키 목록 조회"""
        cache_map = {
            "trades": self.trades_cache,
            "market": self.market_overview_cache
        }

        if cache_type not in cache_map:
            return []

        return list(cache_map[cache_type]._cache.keys())

    def __str__(self) -> str:
        stats = self.get_performance_stats()
        overall = stats.get("overall", {})
        memory_usage = stats.get("memory_usage", {})
        memory_mb = self.get_memory_usage_mb()

        total_entries = memory_usage.get("total_entries", 0) if isinstance(memory_usage, dict) else 0
        hit_rate = overall.get("hit_rate", 0.0) if isinstance(overall, dict) else 0.0

        return (f"MemoryRealtimeCache("
                f"entries={total_entries}, "
                f"hit_rate={hit_rate:.1f}%, "
                f"memory≈{memory_mb:.1f}MB)")
