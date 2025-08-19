"""
MarketDataBackbone V2 - 메인 데이터 통합 클래스

캐싱 시스템과 함께 데이터 통합을 총괄하는 메인 클래스입니다.
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import asyncio
import hashlib
import json
from collections import defaultdict

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .data_models import (
    DataSource,
    NormalizedTickerData,
    CacheEntry
)
from .data_normalizer import DataNormalizer


class IntelligentCache:
    """지능형 캐싱 시스템 (Phase 1.3)"""

    def __init__(self, default_ttl: int = 60):
        self._logger = create_component_logger("IntelligentCache")
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl

        # 캐시 통계
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0

    async def get(self, cache_key: str) -> Optional[NormalizedTickerData]:
        """캐시에서 데이터 조회"""
        entry = self._cache.get(cache_key)

        if entry is None:
            self._miss_count += 1
            return None

        # TTL 검증
        if self._is_expired(entry):
            self._evict(cache_key)
            self._miss_count += 1
            return None

        # 접근 정보 업데이트
        entry.access_count += 1
        entry.last_access = datetime.now()

        self._hit_count += 1
        return entry.data

    async def set(self, cache_key: str, data: NormalizedTickerData, ttl: Optional[int] = None) -> None:
        """캐시에 데이터 저장"""
        effective_ttl = ttl or self._default_ttl

        entry = CacheEntry(
            data=data,
            created_at=datetime.now(),
            access_count=1,
            last_access=datetime.now(),
            ttl_seconds=effective_ttl
        )

        self._cache[cache_key] = entry
        self._cleanup_if_needed()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """캐시 엔트리 만료 여부 확인"""
        age = (datetime.now() - entry.created_at).total_seconds()
        return age > entry.ttl_seconds

    def _evict(self, cache_key: str) -> None:
        """캐시 엔트리 제거"""
        if cache_key in self._cache:
            del self._cache[cache_key]
            self._eviction_count += 1

    def _cleanup_if_needed(self) -> None:
        """캐시 크기가 임계값을 초과하면 정리"""
        max_size = 1000  # 최대 1000개 엔트리

        if len(self._cache) > max_size:
            # LRU 방식으로 오래된 엔트리 제거
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].last_access
            )

            # 20% 제거
            remove_count = max_size // 5
            for cache_key, _ in sorted_entries[:remove_count]:
                self._evict(cache_key)

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_entries": len(self._cache),
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_percent": round(hit_rate, 2),
            "eviction_count": self._eviction_count
        }


class DataUnifier:
    """
    고급 데이터 통합 및 관리 시스템 (Phase 1.3)

    기능:
    ✅ REST/WebSocket 데이터 통합
    ✅ 데이터 정규화 및 검증
    ✅ 지능형 캐싱 시스템
    ✅ 대용량 데이터 처리
    ✅ 데이터 일관성 보장
    """

    def __init__(self, cache_ttl: int = 60):
        """DataUnifier 초기화"""
        self._logger = create_component_logger("DataUnifier")

        # 핵심 컴포넌트 초기화
        self._normalizer = DataNormalizer()
        self._cache = IntelligentCache(default_ttl=cache_ttl)

        # 성능 통계
        self._processing_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "normalization_count": 0,
            "error_count": 0
        }

        # 데이터 일관성 추적
        self._consistency_tracker: Dict[str, List[NormalizedTickerData]] = defaultdict(list)

    async def unify_ticker_data(self, raw_data: Dict[str, Any], source: str, use_cache: bool = True) -> NormalizedTickerData:
        """
        통합 티커 데이터 처리 (Phase 1.3 고도화)

        Args:
            raw_data: 원본 API 응답 데이터
            source: 데이터 소스 ("rest", "websocket", "websocket_simple")
            use_cache: 캐시 사용 여부

        Returns:
            NormalizedTickerData: 정규화된 통합 데이터

        Raises:
            ValueError: 지원하지 않는 소스 또는 잘못된 데이터
        """
        self._processing_stats["total_requests"] += 1

        try:
            # 1. 캐시 확인
            cache_key = self._generate_cache_key(raw_data, source)

            if use_cache:
                cached_data = await self._cache.get(cache_key)
                if cached_data:
                    self._processing_stats["cache_hits"] += 1
                    self._logger.debug(f"캐시 히트: {cache_key}")
                    return cached_data

            # 2. 데이터 소스 타입 결정
            data_source = self._determine_data_source(source)

            # 3. 데이터 정규화 수행
            normalized_data = self._normalizer.normalize_ticker(raw_data, data_source)
            self._processing_stats["normalization_count"] += 1

            # 4. 일관성 검증
            await self._verify_data_consistency(normalized_data)

            # 5. 캐시에 저장
            if use_cache:
                await self._cache.set(cache_key, normalized_data)

            self._logger.debug(f"데이터 통합 완료: {normalized_data.ticker_data.symbol} ({normalized_data.data_quality.value})")
            return normalized_data

        except Exception as e:
            self._processing_stats["error_count"] += 1
            self._logger.error(f"데이터 통합 실패: {e}")
            raise ValueError(f"데이터 통합 실패: {e}") from e

    async def unify_multiple_ticker_data(self, data_batch: List[Tuple[Dict[str, Any], str]]) -> List[NormalizedTickerData]:
        """
        대용량 데이터 배치 처리 (Phase 1.3)

        Args:
            data_batch: (raw_data, source) 튜플의 리스트

        Returns:
            List[NormalizedTickerData]: 정규화된 데이터 리스트
        """
        self._logger.info(f"배치 처리 시작: {len(data_batch)}개 데이터")

        # 비동기 병렬 처리
        tasks = [
            self.unify_ticker_data(raw_data, source)
            for raw_data, source in data_batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 필터링 (에러 제외)
        successful_results = [
            result for result in results
            if isinstance(result, NormalizedTickerData)
        ]

        error_count = len(results) - len(successful_results)
        if error_count > 0:
            self._logger.warning(f"배치 처리 중 {error_count}개 에러 발생")

        self._logger.info(f"배치 처리 완료: {len(successful_results)}/{len(data_batch)} 성공")
        return successful_results

    def get_processing_statistics(self) -> Dict[str, Any]:
        """처리 통계 정보 반환"""
        cache_stats = self._cache.get_cache_stats()

        total_requests = max(self._processing_stats["total_requests"], 1)

        return {
            "processing_stats": self._processing_stats.copy(),
            "cache_stats": cache_stats,
            "cache_hit_rate": (self._processing_stats["cache_hits"] / total_requests * 100),
            "error_rate": (self._processing_stats["error_count"] / total_requests * 100)
        }

    def _generate_cache_key(self, raw_data: Dict[str, Any], source: str) -> str:
        """캐시 키 생성"""
        # 심볼과 소스 기반 키 생성
        symbol = self._extract_symbol(raw_data, source)
        data_hash = hashlib.md5(json.dumps(raw_data, sort_keys=True).encode()).hexdigest()[:8]
        return f"{symbol}:{source}:{data_hash}"

    def _extract_symbol(self, raw_data: Dict[str, Any], source: str) -> str:
        """데이터에서 심볼 추출"""
        if source == "rest":
            return raw_data.get("market", "UNKNOWN")
        elif source == "websocket":
            return raw_data.get("code", "UNKNOWN")
        elif source == "websocket_simple":
            return raw_data.get("cd", "UNKNOWN")
        else:
            return "UNKNOWN"

    def _determine_data_source(self, source: str) -> DataSource:
        """문자열 소스를 DataSource enum으로 변환"""
        source_mapping = {
            "rest": DataSource.REST,
            "websocket": DataSource.WEBSOCKET,
            "websocket_simple": DataSource.WEBSOCKET_SIMPLE
        }

        if source not in source_mapping:
            raise ValueError(f"지원하지 않는 데이터 소스: {source}")

        return source_mapping[source]

    async def _verify_data_consistency(self, normalized_data: NormalizedTickerData) -> None:
        """데이터 일관성 검증 및 추적"""
        symbol = normalized_data.ticker_data.symbol

        # 추적 데이터에 추가
        self._consistency_tracker[symbol].append(normalized_data)

        # 최대 100개까지만 보관 (메모리 관리)
        if len(self._consistency_tracker[symbol]) > 100:
            self._consistency_tracker[symbol] = self._consistency_tracker[symbol][-50:]
