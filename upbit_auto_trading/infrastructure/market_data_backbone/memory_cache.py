"""
차트뷰어 메모리 캐시 시스템

기존 인프라와 호환되는 차트뷰어 전용 메모리 캐시입니다.
LRU 정책 기반 메모리 관리로 기존 시스템과 격리된 캐시를 제공합니다.

주요 기능:
- LRU 정책 기반 메모리 관리
- 차트뷰어 전용 메모리 할당 (기존 시스템과 격리)
- 압축 저장 및 빠른 범위 검색
- 타임프레임별 캐시 분리
- 메모리 사용량 모니터링
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import time
import threading
import gzip
import pickle
from collections import OrderedDict

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    key: str
    data: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    compressed_size: int = 0
    original_size: int = 0

    def update_access(self) -> None:
        """접근 정보 업데이트"""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """캐시 통계"""
    total_entries: int = 0
    total_memory_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    compression_ratio: float = 0.0
    last_cleanup: Optional[datetime] = None

    @property
    def hit_ratio(self) -> float:
        """캐시 히트율"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0


class ChartMemoryCache:
    """
    차트뷰어 메모리 캐시 시스템

    기존 시스템과 격리된 차트뷰어 전용 메모리 캐시입니다.
    LRU 정책으로 메모리를 관리하며, 압축 저장을 통해 효율성을 높입니다.
    """

    def __init__(self, max_memory_mb: int = 256, max_entries: int = 10000,
                 cleanup_interval_seconds: int = 300, compression_enabled: bool = True):
        """
        Args:
            max_memory_mb: 최대 메모리 사용량 (MB) - 차트뷰어 전용 할당
            max_entries: 최대 엔트리 수
            cleanup_interval_seconds: 정리 작업 간격 (초)
            compression_enabled: 압축 저장 활성화
        """
        self.logger = create_component_logger("ChartMemoryCache")

        # 차트뷰어 전용 메모리 설정 (기존 시스템과 격리)
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._max_entries = max_entries
        self._compression_enabled = compression_enabled
        self._cleanup_interval = cleanup_interval_seconds

        # LRU 캐시 저장소 (OrderedDict로 LRU 구현)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # 통계 정보
        self._stats = CacheStats()

        # 타임프레임별 캐시 분리
        self._timeframe_caches: Dict[str, OrderedDict[str, CacheEntry]] = {}
        self._timeframe_stats: Dict[str, CacheStats] = {}

        # 백그라운드 정리 작업
        self._cleanup_timer: Optional[threading.Timer] = None
        self._is_running = True

        # 리소스 모니터 (선택적 연동)
        self._resource_monitor: Optional[Any] = None

        self.logger.info(
            f"차트뷰어 메모리 캐시 초기화: "
            f"최대 메모리 {max_memory_mb}MB, 최대 엔트리 {max_entries}개 "
            f"(기존 시스템과 격리, 압축: {'ON' if compression_enabled else 'OFF'})"
        )

        # 정리 작업 시작
        self._start_cleanup_timer()

    def put(self, key: str, data: Any, timeframe: str = "default") -> bool:
        """
        캐시에 데이터 저장 (LRU 정책 적용)

        Args:
            key: 캐시 키
            data: 저장할 데이터
            timeframe: 타임프레임 (캐시 분리용)

        Returns:
            저장 성공 여부
        """
        try:
            with self._lock:
                # 타임프레임별 캐시 분리
                if timeframe not in self._timeframe_caches:
                    self._timeframe_caches[timeframe] = OrderedDict()
                    self._timeframe_stats[timeframe] = CacheStats()

                cache = self._timeframe_caches[timeframe]
                stats = self._timeframe_stats[timeframe]

                # 데이터 압축 및 크기 계산
                compressed_data, original_size, compressed_size = self._compress_data(data)

                # 메모리 한계 확인 (차트뷰어 전용 할당 내에서)
                current_memory = self._calculate_total_memory()
                if current_memory + compressed_size > self._max_memory_bytes:
                    # LRU 정책으로 공간 확보
                    freed_memory = self._evict_lru_entries(compressed_size)
                    if freed_memory < compressed_size:
                        self.logger.warning(
                            f"메모리 부족으로 캐시 저장 실패: {key} "
                            f"(필요: {compressed_size}, 확보: {freed_memory})"
                        )
                        return False

                # 기존 엔트리 제거 (있는 경우)
                if key in cache:
                    old_entry = cache[key]
                    del cache[key]
                    stats.total_memory_bytes -= old_entry.compressed_size
                    stats.total_entries -= 1

                # 새 엔트리 생성
                entry = CacheEntry(
                    key=key,
                    data=compressed_data,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    access_count=1,
                    compressed_size=compressed_size,
                    original_size=original_size
                )

                # LRU 순서로 삽입 (맨 끝에)
                cache[key] = entry

                # 통계 업데이트
                stats.total_entries += 1
                stats.total_memory_bytes += compressed_size
                self._update_global_stats()

                self.logger.debug(
                    f"캐시 저장 완료: {key} (TF: {timeframe}) "
                    f"압축률: {compressed_size/original_size:.2f}, "
                    f"총 메모리: {current_memory/1024/1024:.1f}MB"
                )

                return True

        except Exception as e:
            self.logger.error(f"캐시 저장 실패: {key} - {e}")
            return False

    def get(self, key: str, timeframe: str = "default") -> Optional[Any]:
        """
        캐시에서 데이터 조회 (LRU 정책 적용)

        Args:
            key: 캐시 키
            timeframe: 타임프레임

        Returns:
            캐시된 데이터 또는 None
        """
        try:
            with self._lock:
                if timeframe not in self._timeframe_caches:
                    self._timeframe_stats[timeframe] = CacheStats()
                    self._timeframe_stats[timeframe].miss_count += 1
                    self._update_global_stats()
                    return None

                cache = self._timeframe_caches[timeframe]
                stats = self._timeframe_stats[timeframe]

                if key not in cache:
                    stats.miss_count += 1
                    self._update_global_stats()
                    return None

                # LRU 정책: 접근된 항목을 맨 끝으로 이동
                entry = cache[key]
                del cache[key]
                entry.update_access()
                cache[key] = entry

                # 통계 업데이트
                stats.hit_count += 1
                self._update_global_stats()

                # 리소스 모니터 업데이트
                self._update_resource_metrics()

                # 데이터 압축 해제
                decompressed_data = self._decompress_data(entry.data)

                self.logger.debug(f"캐시 히트: {key} (TF: {timeframe})")
                return decompressed_data

        except Exception as e:
            self.logger.error(f"캐시 조회 실패: {key} - {e}")
            return None

    def get_range(self, start_key: str, end_key: str,
                  timeframe: str = "default") -> List[Tuple[str, Any]]:
        """
        범위 검색 (빠른 범위 검색)

        Args:
            start_key: 시작 키
            end_key: 종료 키
            timeframe: 타임프레임

        Returns:
            키-값 쌍 리스트
        """
        try:
            with self._lock:
                if timeframe not in self._timeframe_caches:
                    return []

                cache = self._timeframe_caches[timeframe]
                result = []

                for key, entry in cache.items():
                    if start_key <= key <= end_key:
                        # LRU 업데이트
                        entry.update_access()
                        decompressed_data = self._decompress_data(entry.data)
                        result.append((key, decompressed_data))

                # 통계 업데이트
                stats = self._timeframe_stats[timeframe]
                if result:
                    stats.hit_count += len(result)
                else:
                    stats.miss_count += 1
                self._update_global_stats()

                self.logger.debug(
                    f"범위 검색: {start_key}~{end_key} (TF: {timeframe}) "
                    f"결과: {len(result)}개"
                )

                return result

        except Exception as e:
            self.logger.error(f"범위 검색 실패: {start_key}~{end_key} - {e}")
            return []

    def remove(self, key: str, timeframe: str = "default") -> bool:
        """캐시에서 데이터 제거"""
        try:
            with self._lock:
                if timeframe not in self._timeframe_caches:
                    return False

                cache = self._timeframe_caches[timeframe]
                stats = self._timeframe_stats[timeframe]

                if key not in cache:
                    return False

                entry = cache[key]
                del cache[key]

                # 통계 업데이트
                stats.total_entries -= 1
                stats.total_memory_bytes -= entry.compressed_size
                self._update_global_stats()

                self.logger.debug(f"캐시 제거: {key} (TF: {timeframe})")
                return True

        except Exception as e:
            self.logger.error(f"캐시 제거 실패: {key} - {e}")
            return False

    def clear(self, timeframe: Optional[str] = None) -> None:
        """캐시 정리"""
        try:
            with self._lock:
                if timeframe:
                    # 특정 타임프레임만 정리
                    if timeframe in self._timeframe_caches:
                        self._timeframe_caches[timeframe].clear()
                        self._timeframe_stats[timeframe] = CacheStats()
                        self.logger.info(f"타임프레임 캐시 정리: {timeframe}")
                else:
                    # 전체 캐시 정리
                    self._timeframe_caches.clear()
                    self._timeframe_stats.clear()
                    self._stats = CacheStats()
                    self.logger.info("전체 캐시 정리 완료")

                self._update_global_stats()

        except Exception as e:
            self.logger.error(f"캐시 정리 실패: {e}")

    def _compress_data(self, data: Any) -> Tuple[bytes, int, int]:
        """데이터 압축"""
        try:
            # 직렬화
            serialized = pickle.dumps(data)
            original_size = len(serialized)

            if self._compression_enabled:
                # gzip 압축
                compressed = gzip.compress(serialized, compresslevel=6)
                compressed_size = len(compressed)
                return compressed, original_size, compressed_size
            else:
                return serialized, original_size, original_size

        except Exception as e:
            self.logger.error(f"데이터 압축 실패: {e}")
            # 압축 실패시 원본 데이터 반환
            serialized = pickle.dumps(data)
            size = len(serialized)
            return serialized, size, size

    def _decompress_data(self, compressed_data: bytes) -> Any:
        """데이터 압축 해제"""
        try:
            if self._compression_enabled:
                # gzip 압축 해제 시도
                try:
                    decompressed = gzip.decompress(compressed_data)
                    return pickle.loads(decompressed)
                except (gzip.BadGzipFile, pickle.PickleError):
                    # 압축되지 않은 데이터일 수 있음
                    return pickle.loads(compressed_data)
            else:
                return pickle.loads(compressed_data)

        except Exception as e:
            self.logger.error(f"데이터 압축 해제 실패: {e}")
            return None

    def _evict_lru_entries(self, required_memory: int) -> int:
        """LRU 정책으로 엔트리 제거"""
        freed_memory = 0
        evicted_count = 0

        try:
            # 모든 타임프레임에서 가장 오래된 항목부터 제거
            all_entries = []
            for timeframe, cache in self._timeframe_caches.items():
                for key, entry in cache.items():
                    all_entries.append((timeframe, key, entry))

            # 마지막 접근 시간 기준으로 정렬 (오래된 것부터)
            all_entries.sort(key=lambda x: x[2].last_accessed)

            for timeframe, key, entry in all_entries:
                if freed_memory >= required_memory:
                    break

                # 엔트리 제거
                cache = self._timeframe_caches[timeframe]
                stats = self._timeframe_stats[timeframe]

                if key in cache:
                    del cache[key]
                    freed_memory += entry.compressed_size
                    evicted_count += 1

                    # 통계 업데이트
                    stats.total_entries -= 1
                    stats.total_memory_bytes -= entry.compressed_size
                    stats.eviction_count += 1

            if evicted_count > 0:
                self.logger.info(
                    f"LRU 제거 완료: {evicted_count}개 엔트리, "
                    f"{freed_memory/1024/1024:.1f}MB 확보"
                )

            self._update_global_stats()
            return freed_memory

        except Exception as e:
            self.logger.error(f"LRU 제거 실패: {e}")
            return 0

    def _calculate_total_memory(self) -> int:
        """총 메모리 사용량 계산"""
        total = 0
        for stats in self._timeframe_stats.values():
            total += stats.total_memory_bytes
        return total

    def _update_global_stats(self) -> None:
        """글로벌 통계 업데이트"""
        self._stats.total_entries = sum(s.total_entries for s in self._timeframe_stats.values())
        self._stats.total_memory_bytes = sum(s.total_memory_bytes for s in self._timeframe_stats.values())
        self._stats.hit_count = sum(s.hit_count for s in self._timeframe_stats.values())
        self._stats.miss_count = sum(s.miss_count for s in self._timeframe_stats.values())
        self._stats.eviction_count = sum(s.eviction_count for s in self._timeframe_stats.values())

        # 압축률 계산
        total_original = 0
        total_compressed = 0
        for timeframe, cache in self._timeframe_caches.items():
            for entry in cache.values():
                total_original += entry.original_size
                total_compressed += entry.compressed_size

        if total_original > 0:
            self._stats.compression_ratio = total_compressed / total_original

    def _cleanup_expired_entries(self) -> None:
        """만료된 엔트리 정리"""
        try:
            with self._lock:
                current_time = time.time()
                expired_keys = []

                # 30분 이상 접근되지 않은 엔트리 찾기
                expiry_threshold = current_time - (30 * 60)  # 30분

                for timeframe, cache in self._timeframe_caches.items():
                    timeframe_expired = []
                    for key, entry in cache.items():
                        if entry.last_accessed < expiry_threshold:
                            timeframe_expired.append(key)

                    # 만료된 엔트리 제거
                    for key in timeframe_expired:
                        if key in cache:
                            entry = cache[key]
                            del cache[key]

                            # 통계 업데이트
                            stats = self._timeframe_stats[timeframe]
                            stats.total_entries -= 1
                            stats.total_memory_bytes -= entry.compressed_size
                            expired_keys.append(f"{timeframe}:{key}")

                if expired_keys:
                    self.logger.info(f"만료된 캐시 정리: {len(expired_keys)}개 엔트리")

                self._update_global_stats()
                self._stats.last_cleanup = datetime.now()

        except Exception as e:
            self.logger.error(f"만료 엔트리 정리 실패: {e}")

    def _start_cleanup_timer(self) -> None:
        """정리 작업 타이머 시작"""
        try:
            if self._is_running:
                self._cleanup_expired_entries()

                # 다음 정리 작업 예약
                self._cleanup_timer = threading.Timer(
                    self._cleanup_interval,
                    self._start_cleanup_timer
                )
                self._cleanup_timer.daemon = True
                self._cleanup_timer.start()

        except Exception as e:
            self.logger.error(f"정리 타이머 실행 실패: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        with self._lock:
            self._update_global_stats()

            timeframe_stats = {}
            for tf, stats in self._timeframe_stats.items():
                timeframe_stats[tf] = {
                    'entries': stats.total_entries,
                    'memory_mb': stats.total_memory_bytes / 1024 / 1024,
                    'hit_ratio': stats.hit_ratio,
                    'hits': stats.hit_count,
                    'misses': stats.miss_count,
                    'evictions': stats.eviction_count
                }

            return {
                'global_stats': {
                    'total_entries': self._stats.total_entries,
                    'total_memory_mb': self._stats.total_memory_bytes / 1024 / 1024,
                    'max_memory_mb': self._max_memory_bytes / 1024 / 1024,
                    'memory_usage_percent': (self._stats.total_memory_bytes / self._max_memory_bytes) * 100,
                    'hit_ratio': self._stats.hit_ratio,
                    'compression_ratio': self._stats.compression_ratio,
                    'last_cleanup': self._stats.last_cleanup.isoformat() if self._stats.last_cleanup else None
                },
                'timeframe_stats': timeframe_stats,
                'configuration': {
                    'max_memory_mb': self._max_memory_bytes / 1024 / 1024,
                    'max_entries': self._max_entries,
                    'compression_enabled': self._compression_enabled,
                    'cleanup_interval_seconds': self._cleanup_interval
                }
            }

    def get_memory_usage(self) -> Dict[str, float]:
        """메모리 사용량 상세 정보 (기존 시스템과 격리)"""
        with self._lock:
            current_memory = self._calculate_total_memory()

            return {
                'used_mb': current_memory / 1024 / 1024,
                'max_mb': self._max_memory_bytes / 1024 / 1024,
                'usage_percent': (current_memory / self._max_memory_bytes) * 100,
                'available_mb': (self._max_memory_bytes - current_memory) / 1024 / 1024,
                'is_memory_isolated': True,  # 기존 시스템과 격리됨
                'entries_count': self._stats.total_entries
            }

    def set_resource_monitor(self, resource_monitor: Any) -> None:
        """리소스 모니터 설정 (선택적)"""
        self._resource_monitor = resource_monitor
        self.logger.debug("리소스 모니터 연동 설정됨")

    def _update_resource_metrics(self) -> None:
        """리소스 모니터에 캐시 메트릭스 업데이트"""
        if not self._resource_monitor:
            return

        try:
            # 캐시 성능 메트릭스 계산
            hit_ratio = self._stats.hit_ratio
            cache_efficiency = min(1.0, hit_ratio * 1.2)  # 히트율 기반 효율성

            # 메모리 사용량
            current_memory = sum(
                sum(entry.compressed_size for entry in cache.values())
                for cache in self._timeframe_caches.values()
            )
            memory_usage_mb = current_memory / 1024 / 1024

            # 리소스 모니터에 업데이트
            metrics = {
                'cache_hits': self._stats.hit_count,
                'cache_misses': self._stats.miss_count,
                'cache_hit_ratio': hit_ratio,
                'cache_memory_mb': memory_usage_mb,
                'cache_efficiency': cache_efficiency,
                'cache_operations': self._stats.hit_count + self._stats.miss_count
            }

            self._resource_monitor.update_chart_metrics(metrics)

        except Exception as e:
            self.logger.error(f"리소스 메트릭스 업데이트 실패: {e}")

    def shutdown(self) -> None:
        """캐시 시스템 종료"""
        try:
            self._is_running = False

            # 정리 타이머 중지
            if self._cleanup_timer:
                self._cleanup_timer.cancel()
                self._cleanup_timer = None

            # 캐시 정리
            self.clear()

            self.logger.info("차트뷰어 메모리 캐시 종료 완료")

        except Exception as e:
            self.logger.error(f"캐시 종료 실패: {e}")

    def __del__(self):
        """소멸자"""
        if hasattr(self, '_is_running') and self._is_running:
            self.shutdown()
