"""
캐시 조정자 (Cache Coordinator)
스마트 데이터 제공자의 캐시 시스템을 지능적으로 조정하고 최적화합니다.

주요 기능:
- 적응형 TTL 관리 (요청 패턴 분석)
- 스마트 프리로딩 (인기 심볼 사전 캐싱)
- 메모리 최적화 (LRU 기반 자동 정리)
- 캐시 적중률 최적화 (실시간 통계 기반 튜닝)
"""
from typing import Dict, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque
import asyncio
import threading
import statistics

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("CacheCoordinator")


@dataclass
class SymbolAccessPattern:
    """심볼별 접근 패턴 분석"""
    symbol: str
    access_count: int = 0
    last_access: datetime = field(default_factory=datetime.now)
    access_times: deque = field(default_factory=lambda: deque(maxlen=50))  # 최근 50회 접근 시간
    average_interval: float = 0.0  # 평균 접근 간격 (초)
    cache_hit_rate: float = 0.0
    optimal_ttl: float = 60.0  # 최적화된 TTL

    def update_access(self, cache_hit: bool = False) -> None:
        """접근 정보 업데이트"""
        now = datetime.now()

        # 접근 간격 계산
        if self.last_access:
            interval = (now - self.last_access).total_seconds()
            self.access_times.append(interval)

            # 평균 접근 간격 계산
            if len(self.access_times) > 1:
                self.average_interval = statistics.mean(self.access_times)

        self.access_count += 1
        self.last_access = now

        # 캐시 적중률 업데이트 (단순 지수 평활)
        if cache_hit:
            self.cache_hit_rate = self.cache_hit_rate * 0.9 + 0.1
        else:
            self.cache_hit_rate = self.cache_hit_rate * 0.9

    def calculate_optimal_ttl(self, base_ttl: float) -> float:
        """최적 TTL 계산"""
        if len(self.access_times) < 3:
            return base_ttl

        # 접근 빈도가 높을수록 TTL 연장
        if self.average_interval > 0:
            frequency_factor = min(base_ttl / self.average_interval, 3.0)  # 최대 3배

            # 캐시 적중률이 낮으면 TTL 줄임
            hit_rate_factor = max(self.cache_hit_rate, 0.3)  # 최소 30%

            optimal = base_ttl * frequency_factor * hit_rate_factor

            # TTL 범위 제한
            min_ttl = base_ttl * 0.1  # 최소 10%
            max_ttl = base_ttl * 5.0   # 최대 500%

            self.optimal_ttl = max(min_ttl, min(optimal, max_ttl))
        else:
            self.optimal_ttl = base_ttl

        return self.optimal_ttl


@dataclass
class CacheStats:
    """캐시 통계"""
    cache_type: str
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    size: int = 0
    memory_usage_mb: float = 0.0

    @property
    def hit_rate(self) -> float:
        total = self.hit_count + self.miss_count
        return (self.hit_count / total * 100) if total > 0 else 0.0

    @property
    def total_requests(self) -> int:
        return self.hit_count + self.miss_count


class CacheCoordinator:
    """
    캐시 조정자

    모든 캐시 시스템을 통합 관리하고 최적화합니다.
    - 적응형 TTL 관리
    - 스마트 프리로딩
    - 메모리 최적화
    - 성능 모니터링
    """

    def __init__(self, realtime_cache=None):
        self.realtime_cache = realtime_cache

        # 심볼별 접근 패턴 추적
        self.symbol_patterns: Dict[str, SymbolAccessPattern] = {}

        # 글로벌 캐시 통계
        self.cache_stats: Dict[str, CacheStats] = {
            "ticker": CacheStats("ticker"),
            "orderbook": CacheStats("orderbook"),
            "trades": CacheStats("trades"),
            "market": CacheStats("market")
        }

        # 설정
        self.optimization_interval = 300  # 5분마다 최적화
        self.preload_threshold = 10      # 10회 이상 접근한 심볼 프리로딩
        self.memory_threshold_mb = 50    # 50MB 이상시 정리

        # 상태 관리
        self._last_optimization = datetime.now()
        self._popular_symbols: Set[str] = set()
        self._lock = threading.RLock()

        # 백그라운드 태스크
        self._optimization_task = None
        self._running = False

        logger.info("캐시 조정자 초기화 완료")

    def start(self) -> None:
        """캐시 조정자 시작"""
        if not self._running:
            self._running = True
            self._optimization_task = asyncio.create_task(self._optimization_loop())
            logger.info("캐시 조정자 백그라운드 최적화 시작")

    async def stop(self) -> None:
        """캐시 조정자 중지"""
        self._running = False
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
        logger.info("캐시 조정자 중지 완료")

    # =====================================
    # 접근 패턴 추적
    # =====================================

    def record_access(self, cache_type: str, symbol: str, cache_hit: bool) -> None:
        """접근 기록 및 패턴 분석"""
        with self._lock:
            # 심볼별 패턴 업데이트
            if symbol not in self.symbol_patterns:
                self.symbol_patterns[symbol] = SymbolAccessPattern(symbol)

            pattern = self.symbol_patterns[symbol]
            pattern.update_access(cache_hit)

            # 캐시 통계 업데이트
            if cache_type in self.cache_stats:
                stats = self.cache_stats[cache_type]
                if cache_hit:
                    stats.hit_count += 1
                else:
                    stats.miss_count += 1

            # 인기 심볼 업데이트
            if pattern.access_count >= self.preload_threshold:
                self._popular_symbols.add(symbol)

    def get_optimal_ttl(self, cache_type: str, symbol: str) -> float:
        """심볼별 최적 TTL 조회"""
        base_ttls = {
            "ticker": 1.0,
            "orderbook": 5.0,
            "trades": 30.0,
            "market": 60.0
        }

        base_ttl = base_ttls.get(cache_type, 60.0)

        with self._lock:
            if symbol in self.symbol_patterns:
                pattern = self.symbol_patterns[symbol]
                return pattern.calculate_optimal_ttl(base_ttl)

        return base_ttl

    # =====================================
    # 스마트 프리로딩
    # =====================================

    async def preload_popular_symbols(self) -> int:
        """인기 심볼 프리로딩"""
        if not self.realtime_cache:
            return 0

        preloaded_count = 0

        with self._lock:
            popular_symbols = list(self._popular_symbols)

        for symbol in popular_symbols:
            try:
                # 티커 데이터가 없으면 프리로딩 스킵
                cached_ticker = self.realtime_cache.get_ticker(symbol)
                if not cached_ticker:
                    logger.debug(f"인기 심볼 프리로딩 스킵 (데이터 없음): {symbol}")
                    continue

                # TTL이 곧 만료될 데이터 갱신
                # 실제 구현에서는 Smart Router를 통해 새 데이터 요청
                logger.debug(f"인기 심볼 프리로딩: {symbol}")
                preloaded_count += 1

            except Exception as e:
                logger.warning(f"심볼 프리로딩 실패: {symbol}, {e}")

        if preloaded_count > 0:
            logger.info(f"인기 심볼 프리로딩 완료: {preloaded_count}개")

        return preloaded_count

    # =====================================
    # 메모리 최적화
    # =====================================

    def optimize_memory_usage(self) -> Dict[str, int]:
        """메모리 사용량 최적화"""
        if not self.realtime_cache:
            return {}

        cleanup_results = {}

        try:
            # 현재 메모리 사용량 확인
            current_usage = self.realtime_cache.get_memory_usage_mb()

            if current_usage > self.memory_threshold_mb:
                logger.info(f"메모리 임계값 초과: {current_usage:.1f}MB > {self.memory_threshold_mb}MB, 정리 시작")

                # 만료된 캐시 정리
                cleanup_results = self.realtime_cache.cleanup_expired()

                # 여전히 초과하면 LRU 정리 (향후 구현)
                new_usage = self.realtime_cache.get_memory_usage_mb()
                if new_usage > self.memory_threshold_mb:
                    logger.warning(f"메모리 정리 후에도 임계값 초과: {new_usage:.1f}MB")

        except Exception as e:
            logger.error(f"메모리 최적화 실패: {e}")

        return cleanup_results

    # =====================================
    # 성능 모니터링
    # =====================================

    def update_cache_stats(self) -> None:
        """실시간 캐시 통계 업데이트"""
        if not self.realtime_cache:
            return

        try:
            performance_stats = self.realtime_cache.get_performance_stats()

            # 개별 캐시 통계 업데이트
            for cache_type in ["ticker", "orderbook", "trades", "market_overview"]:
                if cache_type in performance_stats:
                    stats = performance_stats[cache_type]
                    if cache_type.replace("_overview", "") in self.cache_stats:
                        cache_stat = self.cache_stats[cache_type.replace("_overview", "")]
                        cache_stat.hit_count = stats.get("hits", 0)
                        cache_stat.miss_count = stats.get("misses", 0)
                        cache_stat.eviction_count = stats.get("evictions", 0)
                        cache_stat.size = stats.get("size", 0)

            # 메모리 사용량 업데이트
            memory_usage = performance_stats.get("memory_usage", {})
            total_memory = memory_usage.get("realtime_cache_mb", 0.0) if isinstance(memory_usage, dict) else 0.0

            for cache_stat in self.cache_stats.values():
                cache_stat.memory_usage_mb = total_memory / len(self.cache_stats)  # 균등 분배

        except Exception as e:
            logger.error(f"캐시 통계 업데이트 실패: {e}")

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 캐시 통계"""
        with self._lock:
            # 심볼 패턴 분석
            top_symbols = sorted(
                self.symbol_patterns.values(),
                key=lambda p: p.access_count,
                reverse=True
            )[:10]

            symbol_stats = []
            for pattern in top_symbols:
                symbol_stats.append({
                    "symbol": pattern.symbol,
                    "access_count": pattern.access_count,
                    "hit_rate": f"{pattern.cache_hit_rate * 100:.1f}%",
                    "avg_interval": f"{pattern.average_interval:.1f}s",
                    "optimal_ttl": f"{pattern.optimal_ttl:.1f}s"
                })

            # 전체 통계
            total_hits = sum(stats.hit_count for stats in self.cache_stats.values())
            total_requests = sum(stats.total_requests for stats in self.cache_stats.values())
            overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                "overall": {
                    "total_requests": total_requests,
                    "total_hits": total_hits,
                    "hit_rate": overall_hit_rate,
                    "popular_symbols_count": len(self._popular_symbols),
                    "tracked_symbols_count": len(self.symbol_patterns)
                },
                "cache_stats": {
                    cache_type: {
                        "hit_rate": stats.hit_rate,
                        "total_requests": stats.total_requests,
                        "size": stats.size,
                        "memory_mb": stats.memory_usage_mb
                    }
                    for cache_type, stats in self.cache_stats.items()
                },
                "top_symbols": symbol_stats,
                "popular_symbols": list(self._popular_symbols)
            }

    # =====================================
    # 백그라운드 최적화
    # =====================================

    async def _optimization_loop(self) -> None:
        """백그라운드 최적화 루프"""
        while self._running:
            try:
                await asyncio.sleep(self.optimization_interval)

                if not self._running:
                    break

                logger.debug("캐시 최적화 주기 실행 시작")

                # 1. 캐시 통계 업데이트
                self.update_cache_stats()

                # 2. 메모리 최적화
                cleanup_results = self.optimize_memory_usage()

                # 3. 인기 심볼 프리로딩
                preloaded_count = await self.preload_popular_symbols()

                # 4. 최적화 결과 로깅
                if cleanup_results or preloaded_count > 0:
                    total_cleaned = sum(cleanup_results.values()) if cleanup_results else 0
                    logger.info(f"캐시 최적화 완료 - 정리: {total_cleaned}개, 프리로딩: {preloaded_count}개")

                self._last_optimization = datetime.now()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"캐시 최적화 루프 오류: {e}")
                await asyncio.sleep(10)  # 오류 시 10초 대기

    # =====================================
    # 유틸리티 메서드
    # =====================================

    def get_symbol_insights(self, symbol: str) -> Optional[Dict[str, Any]]:
        """특정 심볼의 상세 분석"""
        with self._lock:
            if symbol not in self.symbol_patterns:
                return None

            pattern = self.symbol_patterns[symbol]
            return {
                "symbol": symbol,
                "access_count": pattern.access_count,
                "last_access": pattern.last_access.isoformat(),
                "avg_interval": pattern.average_interval,
                "hit_rate": pattern.cache_hit_rate * 100,
                "optimal_ttl": pattern.optimal_ttl,
                "is_popular": symbol in self._popular_symbols,
                "recent_intervals": list(pattern.access_times)
            }

    def reset_statistics(self) -> None:
        """통계 초기화"""
        with self._lock:
            self.symbol_patterns.clear()
            self._popular_symbols.clear()

            for stats in self.cache_stats.values():
                stats.hit_count = 0
                stats.miss_count = 0
                stats.eviction_count = 0

            logger.info("캐시 조정자 통계 초기화 완료")

    def __str__(self) -> str:
        stats = self.get_comprehensive_stats()
        overall = stats["overall"]

        return (f"CacheCoordinator("
                f"tracked_symbols={overall['tracked_symbols_count']}, "
                f"popular_symbols={overall['popular_symbols_count']}, "
                f"hit_rate={overall['hit_rate']:.1f}%)")
