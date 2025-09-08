"""
⚡ CandleCache Infrastructure Service
고속 메모리 캐시를 통한 캔들 데이터 성능 최적화

주요 기능:
- TTL 60초 기반 자동 만료
- 청크 단위 캐시 저장/조회
- 완전 범위 확인으로 즉시 반환
- LRU 방식 메모리 관리
- 캐시 통계 및 모니터링

Created: 2025-09-08
Purpose: CandleDataProvider 성능 최적화
"""

import sys
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .models import CandleData, CacheKey, CacheEntry, CacheStats

logger = create_component_logger("CandleCache")


class CandleCache:
    """고속 메모리 캐시 Infrastructure Service"""

    def __init__(self, max_memory_mb: int = 100, default_ttl_seconds: int = 60):
        """
        Args:
            max_memory_mb: 최대 메모리 사용량 (MB)
            default_ttl_seconds: 기본 TTL (초)
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds

        # 캐시 저장소 (LRU를 위한 OrderedDict)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # 통계 추적
        self._stats = CacheStats(
            total_entries=0,
            total_memory_bytes=0,
            hit_count=0,
            miss_count=0,
            eviction_count=0,
            expired_count=0
        )

        logger.info(f"CandleCache 초기화 완료 - 최대 메모리: {max_memory_mb}MB, TTL: {default_ttl_seconds}초")

    # === 캐시 저장 ===

    def store_chunk(self, symbol: str, timeframe: str, start_time: datetime,
                    candles: List[CandleData], ttl_seconds: Optional[int] = None) -> bool:
        """청크 단위 캐시 저장

        Args:
            symbol: 심볼 (KRW-BTC)
            timeframe: 타임프레임 (1m, 5m, etc.)
            start_time: 시작 시간
            candles: 캔들 데이터 리스트
            ttl_seconds: TTL (기본값 사용시 None)

        Returns:
            저장 성공 여부
        """
        if not candles:
            logger.warning(f"빈 캔들 데이터 저장 시도: {symbol} {timeframe}")
            return False

        try:
            # 캐시 키 생성
            cache_key = CacheKey(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                count=len(candles)
            )

            # 데이터 크기 계산 (대략적)
            data_size = self._estimate_data_size(candles)

            # 캐시 엔트리 생성
            entry = CacheEntry(
                key=cache_key,
                candles=candles.copy(),  # 복사본 저장
                created_at=datetime.now(timezone.utc),
                ttl_seconds=ttl_seconds or self.default_ttl_seconds,
                data_size_bytes=data_size
            )

            # 메모리 공간 확보
            self._ensure_memory_space(data_size)

            # 캐시에 저장
            key_str = cache_key.to_string()
            self._cache[key_str] = entry

            # 통계 업데이트
            self._stats.total_entries = len(self._cache)
            self._stats.total_memory_bytes += data_size

            logger.debug(f"캐시 저장 완료: {key_str} ({data_size:,} bytes)")
            return True

        except Exception as e:
            logger.error(f"캐시 저장 실패: {symbol} {timeframe}, {e}")
            return False

    # === 캐시 조회 ===

    def get_cached_chunk(self, symbol: str, timeframe: str, start_time: datetime,
                         count: int) -> Optional[List[CandleData]]:
        """청크 단위 캐시 조회

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            count: 요청 개수

        Returns:
            캐시된 캔들 데이터 (없거나 만료시 None)
        """
        try:
            # 캐시 키 생성
            cache_key = CacheKey(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                count=count
            )
            key_str = cache_key.to_string()

            # 캐시 확인
            if key_str not in self._cache:
                self._stats.miss_count += 1
                logger.debug(f"캐시 미스: {key_str}")
                return None

            entry = self._cache[key_str]

            # 만료 확인
            if entry.is_expired(datetime.now(timezone.utc)):
                logger.debug(f"캐시 만료: {key_str}")
                self._remove_entry(key_str)
                self._stats.miss_count += 1
                self._stats.expired_count += 1
                return None

            # LRU 업데이트 (최근 사용으로 이동)
            self._cache.move_to_end(key_str)

            # 히트 통계 업데이트
            self._stats.hit_count += 1

            logger.debug(f"캐시 히트: {key_str} (남은 TTL: {entry.get_remaining_ttl(datetime.now(timezone.utc))}초)")
            return entry.candles.copy()  # 복사본 반환

        except Exception as e:
            logger.error(f"캐시 조회 실패: {symbol} {timeframe}, {e}")
            self._stats.miss_count += 1
            return None

    def has_complete_range(self, symbol: str, timeframe: str, start_time: datetime,
                           count: int) -> bool:
        """요청 범위가 캐시에 완전히 존재하는지 확인

        Args:
            symbol: 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            count: 요청 개수

        Returns:
            완전 데이터 존재 여부
        """
        try:
            # 정확히 일치하는 캐시 확인
            cached_data = self.get_cached_chunk(symbol, timeframe, start_time, count)
            if cached_data and len(cached_data) >= count:
                logger.debug(f"완전 캐시 범위 확인: {symbol} {timeframe} ({count}개)")
                return True

            # TODO: 향후 확장 - 여러 청크를 조합하여 완전 범위 구성 가능한지 확인
            # 현재는 단일 청크만 지원

            return False

        except Exception as e:
            logger.error(f"완전 범위 확인 실패: {symbol} {timeframe}, {e}")
            return False

    # === 캐시 관리 ===

    def clear_expired(self) -> int:
        """만료된 캐시 엔트리 정리

        Returns:
            제거된 엔트리 수
        """
        current_time = datetime.now(timezone.utc)
        expired_keys = []

        for key_str, entry in self._cache.items():
            if entry.is_expired(current_time):
                expired_keys.append(key_str)

        for key_str in expired_keys:
            self._remove_entry(key_str)
            self._stats.expired_count += 1

        if expired_keys:
            logger.debug(f"만료된 캐시 {len(expired_keys)}개 정리 완료")

        return len(expired_keys)

    def clear_all(self) -> int:
        """모든 캐시 엔트리 삭제

        Returns:
            제거된 엔트리 수
        """
        cleared_count = len(self._cache)
        self._cache.clear()
        self._stats = CacheStats(
            total_entries=0,
            total_memory_bytes=0,
            hit_count=self._stats.hit_count,    # 누적 통계는 유지
            miss_count=self._stats.miss_count,
            eviction_count=self._stats.eviction_count,
            expired_count=self._stats.expired_count
        )

        logger.info(f"전체 캐시 {cleared_count}개 정리 완료")
        return cleared_count

    def get_cache_stats(self) -> CacheStats:
        """캐시 통계 정보 반환"""
        # 실시간 통계 업데이트
        self._stats.total_entries = len(self._cache)
        return self._stats

    # === 내부 메서드 ===

    def _estimate_data_size(self, candles: List[CandleData]) -> int:
        """캔들 데이터 크기 추정

        Args:
            candles: 캔들 데이터 리스트

        Returns:
            추정 메모리 크기 (bytes)
        """
        if not candles:
            return 0

        # 샘플 데이터로 크기 추정
        sample_size = sys.getsizeof(candles[0])
        # 각 필드별 대략적 크기 (문자열, float, int 등)
        estimated_per_candle = sample_size + 200  # 여유분 포함

        return len(candles) * estimated_per_candle

    def _ensure_memory_space(self, required_bytes: int) -> None:
        """필요한 메모리 공간 확보

        Args:
            required_bytes: 필요한 메모리 크기
        """
        # 현재 메모리 사용량 계산
        current_memory = self._stats.total_memory_bytes

        # 메모리 한계 확인
        if current_memory + required_bytes <= self.max_memory_bytes:
            return

        # LRU 방식으로 오래된 엔트리 제거
        target_memory = self.max_memory_bytes - required_bytes
        removed_count = 0

        while current_memory > target_memory and self._cache:
            # 가장 오래된 엔트리 제거 (FIFO)
            oldest_key = next(iter(self._cache))
            oldest_entry = self._cache[oldest_key]

            self._remove_entry(oldest_key)
            current_memory -= oldest_entry.data_size_bytes
            removed_count += 1
            self._stats.eviction_count += 1

        if removed_count > 0:
            logger.debug(f"메모리 확보를 위해 {removed_count}개 캐시 엔트리 제거")

    def _remove_entry(self, key_str: str) -> None:
        """캐시 엔트리 제거

        Args:
            key_str: 제거할 캐시 키
        """
        if key_str in self._cache:
            entry = self._cache[key_str]
            del self._cache[key_str]
            self._stats.total_memory_bytes -= entry.data_size_bytes
            self._stats.total_entries = len(self._cache)

    # === 디버깅 및 모니터링 ===

    def get_cache_info(self) -> Dict:
        """캐시 상태 정보 반환 (디버깅용)"""
        stats = self.get_cache_stats()

        return {
            "cache_entries": stats.total_entries,
            "memory_usage_mb": round(stats.get_memory_mb(), 2),
            "memory_limit_mb": round(self.max_memory_bytes / (1024 * 1024), 2),
            "hit_rate": round(stats.get_hit_rate() * 100, 1),
            "total_hits": stats.hit_count,
            "total_misses": stats.miss_count,
            "total_evictions": stats.eviction_count,
            "total_expired": stats.expired_count,
            "default_ttl_seconds": self.default_ttl_seconds
        }

    def print_cache_status(self) -> None:
        """캐시 상태 출력 (디버깅용)"""
        info = self.get_cache_info()

        print(f"""
🔄 CandleCache 상태:
  📊 엔트리: {info['cache_entries']}개
  💾 메모리: {info['memory_usage_mb']}MB / {info['memory_limit_mb']}MB
  🎯 히트율: {info['hit_rate']}%
  ✅ 히트: {info['total_hits']}회
  ❌ 미스: {info['total_misses']}회
  🗑️  제거: {info['total_evictions']}회
  ⏰ 만료: {info['total_expired']}회
  🕒 TTL: {info['default_ttl_seconds']}초
        """)
