"""
Intelligent Cache Management System for LLM Agent Logging
지능형 캐싱 시스템 - 반복적 연산 최적화
"""
import time
import threading
from typing import Dict, Any, Optional, Callable, TypeVar, Generic, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import pickle
import weakref

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """캐시 엔트리"""
    value: T
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0


@dataclass
class CacheStats:
    """캐시 통계"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    memory_usage_bytes: int = 0
    entry_count: int = 0


class LRUCache(Generic[T]):
    """LRU (Least Recently Used) 캐시 구현"""

    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl

        # OrderedDict를 사용한 LRU 구현
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = threading.RLock()

        # 통계
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[T]:
        """캐시에서 값 조회"""
        with self._lock:
            self.stats.total_requests += 1

            if key not in self._cache:
                self.stats.cache_misses += 1
                return None

            entry = self._cache[key]

            # TTL 확인
            if self._is_expired(entry):
                del self._cache[key]
                self.stats.cache_misses += 1
                self.stats.evictions += 1
                return None

            # LRU 업데이트 - 맨 뒤로 이동
            self._cache.move_to_end(key)
            entry.last_accessed = datetime.now()
            entry.access_count += 1

            self.stats.cache_hits += 1
            return entry.value

    def put(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """캐시에 값 저장"""
        with self._lock:
            now = datetime.now()

            # 값 크기 계산
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = 0

            entry = CacheEntry(
                value=value,
                created_at=now,
                last_accessed=now,
                access_count=0,
                ttl_seconds=ttl or self.default_ttl,
                size_bytes=size_bytes
            )

            # 기존 키가 있으면 업데이트
            if key in self._cache:
                old_entry = self._cache[key]
                self.stats.memory_usage_bytes -= old_entry.size_bytes

            self._cache[key] = entry
            self._cache.move_to_end(key)

            self.stats.memory_usage_bytes += size_bytes
            self.stats.entry_count = len(self._cache)

            # 크기 제한 확인
            self._evict_if_needed()

    def _is_expired(self, entry: CacheEntry[T]) -> bool:
        """엔트리 만료 확인"""
        if entry.ttl_seconds is None:
            return False

        age = (datetime.now() - entry.created_at).total_seconds()
        return age > entry.ttl_seconds

    def _evict_if_needed(self) -> None:
        """필요시 오래된 엔트리 제거"""
        while len(self._cache) > self.max_size:
            # 가장 오래된 엔트리 제거 (OrderedDict의 FIFO 특성 활용)
            key, entry = self._cache.popitem(last=False)
            self.stats.memory_usage_bytes -= entry.size_bytes
            self.stats.evictions += 1

        self.stats.entry_count = len(self._cache)

    def clear(self) -> None:
        """캐시 모든 엔트리 제거"""
        with self._lock:
            self._cache.clear()
            self.stats.memory_usage_bytes = 0
            self.stats.entry_count = 0

    def remove(self, key: str) -> bool:
        """특정 키 제거"""
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                self.stats.memory_usage_bytes -= entry.size_bytes
                self.stats.entry_count = len(self._cache)
                return True
            return False

    def cleanup_expired(self) -> int:
        """만료된 엔트리들 정리"""
        with self._lock:
            expired_keys = []

            for key, entry in self._cache.items():
                if self._is_expired(entry):
                    expired_keys.append(key)

            for key in expired_keys:
                entry = self._cache.pop(key)
                self.stats.memory_usage_bytes -= entry.size_bytes
                self.stats.evictions += 1

            self.stats.entry_count = len(self._cache)
            return len(expired_keys)


class CacheManager:
    """캐시 관리자 - 다중 캐시 통합 관리"""

    def __init__(self, cleanup_interval: float = 300.0):  # 5분마다 정리
        self.cleanup_interval = cleanup_interval

        # 등록된 캐시들
        self._caches: Dict[str, LRUCache] = {}
        self._cache_configs: Dict[str, Dict[str, Any]] = {}

        # 정리 스레드
        self._cleanup_thread = None
        self._cleanup_running = False

        # 함수 캐시 (데코레이터용)
        self._function_caches: Dict[str, LRUCache] = {}

        # 글로벌 통계
        self._global_stats = CacheStats()

    def register_cache(self, name: str, max_size: int = 1000,
                      default_ttl: Optional[int] = None) -> LRUCache:
        """새 캐시 등록"""
        cache = LRUCache(max_size=max_size, default_ttl=default_ttl)
        self._caches[name] = cache
        self._cache_configs[name] = {
            'max_size': max_size,
            'default_ttl': default_ttl
        }

        print(f"✅ 캐시 등록됨: {name} (max_size={max_size}, ttl={default_ttl})")
        return cache

    def get_cache(self, name: str) -> Optional[LRUCache]:
        """등록된 캐시 조회"""
        return self._caches.get(name)

    def start_cleanup_thread(self):
        """정리 스레드 시작"""
        if self._cleanup_running:
            return

        self._cleanup_running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="CacheCleanup"
        )
        self._cleanup_thread.start()
        print("🧹 캐시 정리 스레드 시작")

    def stop_cleanup_thread(self):
        """정리 스레드 중지"""
        self._cleanup_running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2.0)
        print("🛑 캐시 정리 스레드 중지")

    def _cleanup_loop(self):
        """정리 루프"""
        while self._cleanup_running:
            try:
                self._perform_cleanup()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                print(f"❌ 캐시 정리 오류: {e}")
                time.sleep(10.0)

    def _perform_cleanup(self):
        """정리 작업 수행"""
        total_cleaned = 0

        for name, cache in self._caches.items():
            cleaned = cache.cleanup_expired()
            total_cleaned += cleaned

            if cleaned > 0:
                print(f"🧹 캐시 '{name}': {cleaned}개 만료 엔트리 정리됨")

        # 글로벌 통계 업데이트
        self._update_global_stats()

    def _update_global_stats(self):
        """글로벌 통계 업데이트"""
        self._global_stats = CacheStats()

        for cache in self._caches.values():
            stats = cache.stats
            self._global_stats.total_requests += stats.total_requests
            self._global_stats.cache_hits += stats.cache_hits
            self._global_stats.cache_misses += stats.cache_misses
            self._global_stats.evictions += stats.evictions
            self._global_stats.memory_usage_bytes += stats.memory_usage_bytes
            self._global_stats.entry_count += stats.entry_count

    def cached_function(self, cache_name: str = "function_cache",
                       max_size: int = 1000, ttl: Optional[int] = None):
        """함수 결과 캐싱 데코레이터"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            # 함수별 캐시 생성
            func_cache_name = f"{cache_name}_{func.__name__}"

            if func_cache_name not in self._function_caches:
                self._function_caches[func_cache_name] = LRUCache(
                    max_size=max_size,
                    default_ttl=ttl
                )

            cache = self._function_caches[func_cache_name]

            def wrapper(*args, **kwargs) -> T:
                # 캐시 키 생성
                cache_key = self._generate_function_cache_key(func.__name__, args, kwargs)

                # 캐시에서 조회
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # 함수 실행 및 캐싱
                result = func(*args, **kwargs)
                cache.put(cache_key, result, ttl)

                return result

            return wrapper
        return decorator

    def _generate_function_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """함수 캐시 키 생성"""
        # args와 kwargs를 포함한 고유 키 생성
        key_data = {
            'function': func_name,
            'args': args,
            'kwargs': sorted(kwargs.items())
        }

        # 해시로 키 생성
        serialized = pickle.dumps(key_data, protocol=pickle.HIGHEST_PROTOCOL)
        return hashlib.md5(serialized).hexdigest()

    def clear_all_caches(self):
        """모든 캐시 정리"""
        cleared_count = 0

        for name, cache in self._caches.items():
            cache.clear()
            cleared_count += 1
            print(f"🗑️ 캐시 '{name}' 정리됨")

        for name, cache in self._function_caches.items():
            cache.clear()
            cleared_count += 1
            print(f"🗑️ 함수 캐시 '{name}' 정리됨")

        print(f"✅ 총 {cleared_count}개 캐시 정리 완료")

    def get_performance_report(self) -> Dict[str, Any]:
        """캐시 성능 리포트 생성"""
        self._update_global_stats()

        cache_details = {}
        for name, cache in self._caches.items():
            stats = cache.stats
            hit_rate = (stats.cache_hits / max(stats.total_requests, 1)) * 100

            cache_details[name] = {
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': stats.total_requests,
                'cache_hits': stats.cache_hits,
                'cache_misses': stats.cache_misses,
                'entry_count': stats.entry_count,
                'memory_usage_kb': round(stats.memory_usage_bytes / 1024, 2),
                'evictions': stats.evictions,
                'config': self._cache_configs.get(name, {})
            }

        # 글로벌 히트율 계산
        global_hit_rate = (self._global_stats.cache_hits /
                          max(self._global_stats.total_requests, 1)) * 100

        return {
            'global_stats': {
                'total_hit_rate_percent': round(global_hit_rate, 2),
                'total_requests': self._global_stats.total_requests,
                'total_memory_usage_mb': round(self._global_stats.memory_usage_bytes / 1024 / 1024, 2),
                'total_entries': self._global_stats.entry_count,
                'total_evictions': self._global_stats.evictions
            },
            'cache_details': cache_details,
            'function_caches': {
                name: {
                    'entry_count': cache.stats.entry_count,
                    'memory_usage_kb': round(cache.stats.memory_usage_bytes / 1024, 2)
                }
                for name, cache in self._function_caches.items()
            }
        }

    def optimize_cache_sizes(self):
        """캐시 크기 최적화"""
        for name, cache in self._caches.items():
            stats = cache.stats

            # 히트율이 낮으면 크기 줄이기
            if stats.total_requests > 100:
                hit_rate = stats.cache_hits / stats.total_requests

                if hit_rate < 0.3:  # 30% 미만
                    new_size = max(100, int(cache.max_size * 0.7))
                    cache.max_size = new_size
                    print(f"📉 캐시 '{name}' 크기 축소: {new_size} (히트율: {hit_rate:.1%})")

                elif hit_rate > 0.8 and stats.evictions > 10:  # 80% 이상이고 제거 빈번
                    new_size = min(10000, int(cache.max_size * 1.3))
                    cache.max_size = new_size
                    print(f"📈 캐시 '{name}' 크기 확장: {new_size} (히트율: {hit_rate:.1%})")

    def cleanup(self):
        """리소스 정리"""
        self.stop_cleanup_thread()
        self.clear_all_caches()
        print("✅ CacheManager 정리 완료")
