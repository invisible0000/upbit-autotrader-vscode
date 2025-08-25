"""
SmartDataProvider V4.0 - Ultra-Fast Performance Edition

기존 SmartDataProvider의 18.5배 성능 문제를 해결하는 완전 새로운 구현
- 목표: 500+ 심볼/초 처리 성능
- 원칙: 최소 레이어, 직접 연결, Ultra-Short TTL 캐시
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..models.responses import DataResponse
from ..models.priority import Priority

logger = create_component_logger("SmartDataProviderV4")


# =====================================
# 🎛️ 캐시 제어 플래그 (쉬운 검색/변경용)
# =====================================
CACHE_CONFIG = {
    # 🔍 검색 키워드: "TICKER_CACHE_ENABLED"
    'TICKER_CACHE_ENABLED': True,     # 티커 캐시 ON/OFF
    'TICKER_CACHE_TTL': 0.2,          # 티커 캐시 수명 (초)

    # 🔍 검색 키워드: "ORDERBOOK_CACHE_ENABLED"
    'ORDERBOOK_CACHE_ENABLED': True,  # 호가 캐시 ON/OFF
    'ORDERBOOK_CACHE_TTL': 0.3,       # 호가 캐시 수명 (초)

    # 🔍 검색 키워드: "TRADES_CACHE_ENABLED"
    'TRADES_CACHE_ENABLED': True,     # 체결 캐시 ON/OFF
    'TRADES_CACHE_TTL': 30.0,         # 체결 캐시 수명 (초)
}


class UltraFastCache:
    """
    Ultra-Fast 메모리 캐시 시스템
    - 200ms TTL로 중복 요청 완전 차단
    - 메모리 효율적 구조
    - 런타임 제어 가능
    """

    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._timestamps: Dict[str, float] = {}
        self._config = CACHE_CONFIG.copy()
        self._hits = 0
        self._misses = 0

    def get(self, key: str, data_type: str) -> Optional[Dict]:
        """캐시에서 데이터 조회"""
        # 캐시 비활성화 체크
        enabled_key = f"{data_type.upper()}_CACHE_ENABLED"
        if not self._config.get(enabled_key, False):
            return None

        if key not in self._cache:
            self._misses += 1
            return None

        # TTL 체크
        ttl_key = f"{data_type.upper()}_CACHE_TTL"
        max_age = self._config.get(ttl_key, 0.2)

        cached_time = self._timestamps.get(key, 0)
        age = time.time() - cached_time

        if age > max_age:
            # 만료된 캐시 삭제
            del self._cache[key]
            del self._timestamps[key]
            self._misses += 1
            return None

        self._hits += 1
        return self._cache[key]

    def set(self, key: str, data: Dict, data_type: str) -> None:
        """캐시에 데이터 저장"""
        enabled_key = f"{data_type.upper()}_CACHE_ENABLED"
        if not self._config.get(enabled_key, False):
            return

        self._cache[key] = data
        self._timestamps[key] = time.time()

    def clear_type(self, data_type: str) -> None:
        """특정 타입의 모든 캐시 삭제"""
        prefix = f"{data_type}:"
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
        for key in keys_to_remove:
            del self._cache[key]
            del self._timestamps[key]

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0

        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
            'cache_size': len(self._cache),
            'config': self._config.copy()
        }

    # =====================================
    # 🎛️ 실시간 캐시 제어 API
    # =====================================

    def disable_ticker_cache(self):
        """🔍 검색: disable_ticker_cache - 티커 캐시 비활성화"""
        self._config['TICKER_CACHE_ENABLED'] = False
        self.clear_type('ticker')
        logger.warning("티커 캐시 비활성화됨")

    def enable_ticker_cache(self, ttl: float = 0.2):
        """🔍 검색: enable_ticker_cache - 티커 캐시 활성화"""
        self._config['TICKER_CACHE_ENABLED'] = True
        self._config['TICKER_CACHE_TTL'] = ttl
        logger.info(f"티커 캐시 활성화됨 (TTL: {ttl}초)")

    def disable_orderbook_cache(self):
        """🔍 검색: disable_orderbook_cache - 호가 캐시 비활성화"""
        self._config['ORDERBOOK_CACHE_ENABLED'] = False
        self.clear_type('orderbook')
        logger.warning("호가 캐시 비활성화됨")

    def enable_orderbook_cache(self, ttl: float = 0.3):
        """🔍 검색: enable_orderbook_cache - 호가 캐시 활성화"""
        self._config['ORDERBOOK_CACHE_ENABLED'] = True
        self._config['ORDERBOOK_CACHE_TTL'] = ttl
        logger.info(f"호가 캐시 활성화됨 (TTL: {ttl}초)")


class SmartDataProviderV4:
    """
    Smart Data Provider V4.0 - Ultra-Fast Performance Edition

    🚀 성능 목표: 500+ 심볼/초 (기존 대비 18.5배 향상)

    핵심 설계 원칙:
    - SmartRouter 직접 연결 (어댑터 제거)
    - Ultra-Short TTL 캐시 (200ms)
    - 배치 처리 최적화
    - 최소 데이터 변환
    """

    def __init__(self):
        """V4.0 초기화 - 최소 의존성"""
        # SmartRouter 직접 연결
        try:
            from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.smart_router import (
                get_smart_router
            )
            from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.models import (
                RealtimePriority
            )
            self.smart_router = get_smart_router()
            self.RealtimePriority = RealtimePriority
            self._is_available = True
            logger.info("SmartRouter 직접 연결 성공 (V4.0)")
        except Exception as e:
            logger.error(f"SmartRouter 연결 실패: {e}")
            self.smart_router = None
            self._is_available = False

        # Ultra-Fast 캐시 시스템
        self.cache = UltraFastCache()

        # 성능 메트릭
        self._request_count = 0
        self._api_calls = 0

        logger.info("SmartDataProvider V4.0 초기화 완료 - Ultra-Fast Performance")

    async def _ensure_smart_router_ready(self):
        """SmartRouter 준비 상태 확인"""
        if not self._is_available:
            raise Exception("SmartRouter 사용 불가")

        if self.smart_router and not self.smart_router.is_initialized:
            await self.smart_router.initialize()

    def _map_priority(self, priority: Priority) -> 'RealtimePriority':
        """Priority 매핑"""
        priority_map = {
            Priority.LOW: self.RealtimePriority.LOW,
            Priority.NORMAL: self.RealtimePriority.MEDIUM,
            Priority.HIGH: self.RealtimePriority.HIGH
        }
        return priority_map.get(priority, self.RealtimePriority.HIGH)

    # =====================================
    # 🚀 Ultra-Fast 티커 API
    # =====================================

    async def get_ticker(self, symbol: str, priority: Priority = Priority.HIGH) -> DataResponse:
        """
        Ultra-Fast 단일 티커 조회

        성능 최적화:
        - 200ms TTL 캐시로 중복 요청 차단
        - SmartRouter 직접 호출
        - 최소 데이터 변환
        """
        start_time = time.time()
        self._request_count += 1

        cache_key = f"ticker:{symbol}"

        # 1. Ultra-Fast 캐시 체크
        cached_data = self.cache.get(cache_key, 'ticker')
        if cached_data:
            response_time = (time.time() - start_time) * 1000
            logger.debug(f"티커 캐시 히트: {symbol}, {response_time:.1f}ms")

            return DataResponse.create_success(
                data=cached_data,
                source="ultra_fast_cache",
                response_time_ms=response_time,
                cache_hit=True,
                priority_used=priority
            )

        # 2. SmartRouter 직접 호출
        await self._ensure_smart_router_ready()

        try:
            smart_priority = self._map_priority(priority)
            result = await self.smart_router.get_ticker(
                symbols=[symbol],
                realtime_priority=smart_priority
            )

            if result.get('success', False):
                ticker_data = result.get('data')
                response_time = (time.time() - start_time) * 1000

                # 3. 캐시 저장
                if ticker_data:
                    # 단일 심볼이므로 첫 번째 데이터 추출
                    if isinstance(ticker_data, list) and ticker_data:
                        single_ticker = ticker_data[0]
                    else:
                        single_ticker = ticker_data

                    self.cache.set(cache_key, single_ticker, 'ticker')
                    self._api_calls += 1

                    logger.debug(f"티커 API 성공: {symbol}, {response_time:.1f}ms")

                    return DataResponse.create_success(
                        data=single_ticker,
                        source="smart_router_direct",
                        response_time_ms=response_time,
                        cache_hit=False,
                        priority_used=priority
                    )

            # SmartRouter 실패
            error_msg = result.get('error', 'Unknown error')
            logger.warning(f"SmartRouter 티커 실패: {symbol}, {error_msg}")

            return DataResponse(
                success=False,
                error=f"티커 조회 실패: {error_msg}",
                metadata={
                    'source': 'smart_router_error',
                    'response_time_ms': (time.time() - start_time) * 1000,
                    'cache_hit': False,
                    'priority_used': priority
                }
            )

        except Exception as e:
            logger.error(f"티커 조회 예외: {symbol}, {e}")
            return DataResponse(
                success=False,
                error=f"티커 조회 예외: {str(e)}",
                metadata={
                    'source': 'exception',
                    'response_time_ms': (time.time() - start_time) * 1000,
                    'cache_hit': False,
                    'priority_used': priority
                }
            )

    async def get_tickers(self, symbols: List[str], priority: Priority = Priority.HIGH) -> DataResponse:
        """
        Ultra-Fast 다중 티커 조회 (배치 처리)

        핵심 최적화:
        - 전체 심볼을 단일 요청으로 처리 (분할 금지)
        - 캐시된 심볼과 신규 심볼 구분 처리
        - 최소 데이터 변환
        """
        start_time = time.time()
        self._request_count += 1

        if not symbols:
            return DataResponse(
                success=False,
                error="심볼 리스트가 필요합니다",
                metadata={
                    'source': 'validation_error',
                    'response_time_ms': (time.time() - start_time) * 1000,
                    'cache_hit': False,
                    'priority_used': priority
                }
            )

        # 1. 캐시 데이터 수집
        cached_tickers = []
        uncached_symbols = []

        for symbol in symbols:
            cache_key = f"ticker:{symbol}"
            cached_data = self.cache.get(cache_key, 'ticker')
            if cached_data:
                cached_tickers.append(cached_data)
            else:
                uncached_symbols.append(symbol)

        logger.debug(f"티커 배치: 캐시 {len(cached_tickers)}개, API {len(uncached_symbols)}개")

        # 2. API 호출 (캐시되지 않은 심볼들만)
        fresh_tickers = []
        if uncached_symbols:
            await self._ensure_smart_router_ready()

            try:
                smart_priority = self._map_priority(priority)
                result = await self.smart_router.get_ticker(
                    symbols=uncached_symbols,  # 🚀 배치 처리!
                    realtime_priority=smart_priority
                )

                if result.get('success', False):
                    fresh_data = result.get('data', [])
                    if isinstance(fresh_data, list):
                        fresh_tickers = fresh_data
                    else:
                        fresh_tickers = [fresh_data] if fresh_data else []

                    # 3. 신규 데이터 캐시 저장
                    for i, symbol in enumerate(uncached_symbols):
                        if i < len(fresh_tickers):
                            cache_key = f"ticker:{symbol}"
                            self.cache.set(cache_key, fresh_tickers[i], 'ticker')

                    self._api_calls += 1
                    logger.debug(f"티커 배치 API 성공: {len(fresh_tickers)}개")

                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.warning(f"배치 티커 API 실패: {error_msg}")

                    # 캐시된 데이터라도 있으면 부분 성공
                    if cached_tickers:
                        logger.info(f"부분 성공: 캐시 {len(cached_tickers)}개 반환")
                    else:
                        return DataResponse(
                            success=False,
                            error=f"배치 티커 조회 실패: {error_msg}",
                            metadata={
                                'source': 'smart_router_batch_error',
                                'response_time_ms': (time.time() - start_time) * 1000,
                                'cache_hit': False,
                                'priority_used': priority
                            }
                        )

            except Exception as e:
                logger.error(f"배치 티커 예외: {e}")
                if not cached_tickers:
                    return DataResponse(
                        success=False,
                        error=f"배치 티커 조회 예외: {str(e)}",
                        metadata={
                            'source': 'batch_exception',
                            'response_time_ms': (time.time() - start_time) * 1000,
                            'cache_hit': False,
                            'priority_used': priority
                        }
                    )

        # 4. 결과 병합 및 반환
        all_tickers = cached_tickers + fresh_tickers
        response_time = (time.time() - start_time) * 1000
        cache_hit = len(cached_tickers) > 0

        logger.info(f"배치 티커 완료: {len(symbols)}개 요청, {len(all_tickers)}개 반환, {response_time:.1f}ms")

        return DataResponse.create_success(
            data=all_tickers,
            source="ultra_fast_batch" if cache_hit else "smart_router_batch",
            response_time_ms=response_time,
            cache_hit=cache_hit,
            priority_used=priority,
            records_count=len(all_tickers)
        )

    # =====================================
    # 🚀 Ultra-Fast 호가 API
    # =====================================

    async def get_orderbook(self, symbol: str, priority: Priority = Priority.HIGH) -> DataResponse:
        """Ultra-Fast 호가 조회"""
        start_time = time.time()
        self._request_count += 1

        cache_key = f"orderbook:{symbol}"

        # 1. Ultra-Fast 캐시 체크
        cached_data = self.cache.get(cache_key, 'orderbook')
        if cached_data:
            response_time = (time.time() - start_time) * 1000
            logger.debug(f"호가 캐시 히트: {symbol}, {response_time:.1f}ms")

            return DataResponse.create_success(
                data=cached_data,
                source="ultra_fast_cache",
                response_time_ms=response_time,
                cache_hit=True,
                priority_used=priority
            )

        # 2. SmartRouter 직접 호출
        await self._ensure_smart_router_ready()

        try:
            smart_priority = self._map_priority(priority)
            result = await self.smart_router.get_orderbook(
                symbols=[symbol],
                realtime_priority=smart_priority
            )

            if result.get('success', False):
                orderbook_data = result.get('data')
                response_time = (time.time() - start_time) * 1000

                # 3. 캐시 저장
                if orderbook_data:
                    # 단일 심볼이므로 첫 번째 데이터 추출
                    if isinstance(orderbook_data, list) and orderbook_data:
                        single_orderbook = orderbook_data[0]
                    else:
                        single_orderbook = orderbook_data

                    self.cache.set(cache_key, single_orderbook, 'orderbook')
                    self._api_calls += 1

                    logger.debug(f"호가 API 성공: {symbol}, {response_time:.1f}ms")

                    return DataResponse.create_success(
                        data=single_orderbook,
                        source="smart_router_direct",
                        response_time_ms=response_time,
                        cache_hit=False,
                        priority_used=priority
                    )

            # SmartRouter 실패
            error_msg = result.get('error', 'Unknown error')
            logger.warning(f"SmartRouter 호가 실패: {symbol}, {error_msg}")

            return DataResponse(
                success=False,
                error=f"호가 조회 실패: {error_msg}",
                metadata={
                    'source': 'smart_router_error',
                    'response_time_ms': (time.time() - start_time) * 1000,
                    'cache_hit': False,
                    'priority_used': priority
                }
            )

        except Exception as e:
            logger.error(f"호가 조회 예외: {symbol}, {e}")
            return DataResponse(
                success=False,
                error=f"호가 조회 예외: {str(e)}",
                metadata={
                    'source': 'exception',
                    'response_time_ms': (time.time() - start_time) * 1000,
                    'cache_hit': False,
                    'priority_used': priority
                }
            )

    # =====================================
    # 📊 성능 및 관리 API
    # =====================================

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        cache_stats = self.cache.get_stats()

        return {
            'version': 'V4.0 Ultra-Fast',
            'requests': {
                'total': self._request_count,
                'api_calls': self._api_calls,
                'api_efficiency': (self._request_count - self._api_calls) / self._request_count * 100
                                 if self._request_count > 0 else 0
            },
            'cache': cache_stats,
            'smart_router_available': self._is_available
        }

    def reset_stats(self):
        """통계 초기화"""
        self._request_count = 0
        self._api_calls = 0
        self.cache._hits = 0
        self.cache._misses = 0
        logger.info("성능 통계 초기화 완료")

    # 캐시 제어 API (위임)
    def disable_ticker_cache(self):
        """티커 캐시 비활성화"""
        self.cache.disable_ticker_cache()

    def enable_ticker_cache(self, ttl: float = 0.2):
        """티커 캐시 활성화"""
        self.cache.enable_ticker_cache(ttl)

    def disable_orderbook_cache(self):
        """호가 캐시 비활성화"""
        self.cache.disable_orderbook_cache()

    def enable_orderbook_cache(self, ttl: float = 0.3):
        """호가 캐시 활성화"""
        self.cache.enable_orderbook_cache(ttl)

    def __str__(self) -> str:
        stats = self.get_performance_stats()
        requests = stats.get('requests', {})
        cache = stats.get('cache', {})

        return (f"SmartDataProviderV4("
                f"requests={requests.get('total', 0)}, "
                f"api_efficiency={requests.get('api_efficiency', 0):.1f}%, "
                f"cache_hit_rate={cache.get('hit_rate', 0):.1f}%, "
                f"cache_size={cache.get('cache_size', 0)})")


# =====================================
# 🎛️ 캐시 제어 API (전역 접근)
# =====================================

def disable_all_caches():
    """🔍 검색: disable_all_caches - 모든 캐시 긴급 비활성화"""
    CACHE_CONFIG['TICKER_CACHE_ENABLED'] = False
    CACHE_CONFIG['ORDERBOOK_CACHE_ENABLED'] = False
    CACHE_CONFIG['TRADES_CACHE_ENABLED'] = False
    logger.warning("모든 캐시 긴급 비활성화됨")

def enable_all_caches():
    """🔍 검색: enable_all_caches - 모든 캐시 활성화"""
    CACHE_CONFIG['TICKER_CACHE_ENABLED'] = True
    CACHE_CONFIG['ORDERBOOK_CACHE_ENABLED'] = True
    CACHE_CONFIG['TRADES_CACHE_ENABLED'] = True
    logger.info("모든 캐시 활성화됨")
