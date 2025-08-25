"""
Fast Cache - 단순하고 빠른 캐시 시스템

V4.0에서는 복잡한 캐시 관리를 제거하고
200ms TTL 고정으로 단순성과 성능을 확보
"""

import time
from typing import Dict, Any, Optional
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("FastCache")


class FastCache:
    """
    고속 메모리 캐시
    - 200ms 고정 TTL
    - 단순한 메모리 구조
    - 자동 만료 정리
    """

    def __init__(self, default_ttl: float = 0.2):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        logger.info(f"FastCache 초기화: TTL {default_ttl}초")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터 조회"""
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
        self._cache[key] = data
        self._timestamps[key] = time.time()

    def clear(self) -> None:
        """캐시 전체 삭제"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("FastCache 전체 삭제")

    def cleanup_expired(self) -> int:
        """만료된 데이터 정리"""
        current_time = time.time()
        expired_keys = []

        for key, timestamp in self._timestamps.items():
            if current_time - timestamp > self._default_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]
            del self._timestamps[key]

        if expired_keys:
            logger.debug(f"만료된 캐시 {len(expired_keys)}개 정리")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'total_keys': len(self._cache),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': round(hit_rate, 2),
            'ttl': self._default_ttl
        }
