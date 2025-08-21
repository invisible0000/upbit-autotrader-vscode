"""
Market Data Cache

HOT_CACHE Tier를 위한 고성능 메모리 캐시 시스템입니다.
TTL 기반 만료 정책과 성능 메트릭을 제공합니다.

핵심 기능:
- 0.1ms 목표 응답시간 (HOT_CACHE Tier)
- TTL 기반 자동 만료
- 메모리 사용량 최적화
- 히트/미스 성능 메트릭
"""

import asyncio
import time
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
import sys

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("MarketDataCache")


@dataclass
class CacheEntry:
    """캐시 엔트리"""
    data: Any
    created_at: float
    ttl_seconds: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """만료 여부 확인"""
        return time.time() - self.created_at > self.ttl_seconds

    @property
    def expires_at(self) -> float:
        """만료 시간"""
        return self.created_at + self.ttl_seconds


class MarketDataCache:
    """
    Market Data Cache

    HOT_CACHE Tier를 위한 고성능 메모리 캐시 시스템입니다.
    0.1ms 목표 응답시간으로 최고 성능을 제공합니다.
    """

    def __init__(self, max_size: int = 10000, cleanup_interval: float = 60.0):
        """캐시 초기화

        Args:
            max_size: 최대 캐시 엔트리 수
            cleanup_interval: 정리 작업 간격 (초)
        """
        logger.info(f"MarketDataCache 초기화 - 최대 크기: {max_size}, 정리 간격: {cleanup_interval}초")

        # 캐시 저장소
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()  # asyncio 호환 락

        # 설정
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval

        # 성능 메트릭
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'cleanup_runs': 0,
            'total_response_time': 0.0,
            'avg_response_time_ms': 0.0
        }

        # 데이터 타입별 기본 TTL (초)
        self.default_ttl = {
            'ticker': 30.0,      # 30초 (실시간성 중요)
            'orderbook': 10.0,   # 10초 (매우 빠른 변화)
            'trade': 60.0,       # 1분 (체결 내역)
            'candle': 300.0,     # 5분 (상대적으로 안정)
            'default': 60.0      # 기본 1분
        }

        # 정리 작업 태스크
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("MarketDataCache 초기화 완료")

    async def start(self) -> None:
        """캐시 시스템 시작 (정리 작업 시작)"""
        if not self._running:
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("캐시 정리 작업 시작")

    async def stop(self) -> None:
        """캐시 시스템 정지"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("캐시 정리 작업 정지")

    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회

        Args:
            key: 캐시 키

        Returns:
            캐시된 데이터 또는 None
        """
        start_time = time.time()

        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self.metrics['misses'] += 1
                self._update_response_time(start_time)
                return None

            # 만료 확인
            if entry.is_expired:
                del self._cache[key]
                self.metrics['misses'] += 1
                self.metrics['evictions'] += 1
                logger.debug(f"캐시 만료로 삭제: {key}")
                self._update_response_time(start_time)
                return None

            # 히트 처리
            entry.access_count += 1
            entry.last_accessed = time.time()
            self.metrics['hits'] += 1
            self._update_response_time(start_time)

            logger.debug(f"캐시 히트: {key} (접근 {entry.access_count}회)")
            return entry.data

    async def set(self, key: str, data: Any, ttl: Optional[float] = None, data_type: str = 'default') -> None:
        """캐시에 데이터 저장

        Args:
            key: 캐시 키
            data: 저장할 데이터
            ttl: TTL (초), None이면 데이터 타입별 기본값 사용
            data_type: 데이터 타입 (TTL 결정용)
        """
        if ttl is None:
            ttl = self.default_ttl.get(data_type, self.default_ttl['default'])

        start_time = time.time()

        async with self._lock:
            # 크기 제한 확인
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            # 엔트리 생성
            entry = CacheEntry(
                data=data,
                created_at=time.time(),
                ttl_seconds=ttl
            )

            self._cache[key] = entry
            self.metrics['sets'] += 1

            logger.debug(f"캐시 저장: {key} (TTL: {ttl}초, 타입: {data_type})")

        self._update_response_time(start_time)

    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제

        Args:
            key: 삭제할 캐시 키

        Returns:
            삭제 성공 여부
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.metrics['deletes'] += 1
                logger.debug(f"캐시 삭제: {key}")
                return True
            return False

    async def clear(self) -> None:
        """모든 캐시 데이터 삭제"""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self.metrics['deletes'] += count
            logger.info(f"캐시 전체 삭제: {count}개 엔트리")

    async def get_keys(self, pattern: Optional[str] = None) -> Set[str]:
        """캐시 키 목록 조회

        Args:
            pattern: 필터링 패턴 (substring 검사)

        Returns:
            키 집합
        """
        async with self._lock:
            if pattern is None:
                return set(self._cache.keys())
            else:
                return {key for key in self._cache.keys() if pattern in key}

    def get_size(self) -> int:
        """현재 캐시 크기"""
        return len(self._cache)

    async def get_memory_usage(self) -> Dict[str, Any]:
        """메모리 사용량 정보"""
        async with self._lock:
            total_size = sum(sys.getsizeof(entry.data) for entry in self._cache.values())
            return {
                'entry_count': len(self._cache),
                'total_size_bytes': total_size,
                'avg_size_bytes': total_size / max(len(self._cache), 1),
                'max_size': self.max_size,
                'usage_ratio': len(self._cache) / self.max_size
            }

    def get_metrics(self) -> Dict[str, Any]:
        """캐시 성능 메트릭 조회"""
        total_requests = self.metrics['hits'] + self.metrics['misses']
        hit_rate = self.metrics['hits'] / max(total_requests, 1)

        return {
            **self.metrics,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'miss_rate': 1.0 - hit_rate,
            'size': len(self._cache),  # 현재 캐시 크기
            'memory_usage': self.get_memory_usage()
        }

    def reset_metrics(self) -> None:
        """성능 메트릭 초기화"""
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'cleanup_runs': 0,
            'total_response_time': 0.0,
            'avg_response_time_ms': 0.0
        }
        logger.info("캐시 메트릭 초기화 완료")

    def _evict_lru(self) -> None:
        """LRU 방식으로 가장 오래된 엔트리 제거"""
        if not self._cache:
            return

        # 가장 오래 전에 접근한 엔트리 찾기
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]
        self.metrics['evictions'] += 1
        logger.debug(f"LRU 제거: {lru_key}")

    def _update_response_time(self, start_time: float) -> None:
        """응답 시간 메트릭 업데이트"""
        response_time_ms = (time.time() - start_time) * 1000
        self.metrics['total_response_time'] += response_time_ms

        total_operations = (
            self.metrics['hits'] + self.metrics['misses'] + self.metrics['sets']
        )
        if total_operations > 0:
            self.metrics['avg_response_time_ms'] = (
                self.metrics['total_response_time'] / total_operations
            )

    async def _cleanup_loop(self) -> None:
        """주기적 캐시 정리 작업"""
        logger.info(f"캐시 정리 루프 시작 (간격: {self.cleanup_interval}초)")

        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)

                if not self._running:
                    break

                await self._cleanup_expired()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"캐시 정리 중 오류: {str(e)}")

        logger.info("캐시 정리 루프 종료")

    async def _cleanup_expired(self) -> None:
        """만료된 엔트리 정리"""
        expired_keys = []

        async with self._lock:
            for key, entry in self._cache.items():
                if entry.is_expired:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

        if expired_keys:
            self.metrics['evictions'] += len(expired_keys)
            logger.debug(f"만료된 엔트리 정리: {len(expired_keys)}개")

        self.metrics['cleanup_runs'] += 1

    def __len__(self) -> int:
        """캐시 크기"""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """키 존재 여부 확인 (만료 무시)"""
        return key in self._cache

    def __repr__(self) -> str:
        """문자열 표현"""
        return f"MarketDataCache(size={len(self._cache)}, max_size={self.max_size})"
