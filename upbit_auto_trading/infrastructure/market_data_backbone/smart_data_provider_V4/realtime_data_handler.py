"""
실시간 데이터 처리기

모든 실시간 마켓 데이터 요청을 전담 처리합니다.
- 티커, 호가창, 체결 내역 데이터
- 실시간 캐시 최적화
- WebSocket 연동 준비
"""
from typing import List, Dict, Any
import time

from upbit_auto_trading.infrastructure.logging import create_component_logger
from ..models.priority import Priority
from ..models.responses import DataResponse, ResponseMetadata
from ..adapters.smart_router_adapter import SmartRouterAdapter
from ..cache.memory_realtime_cache import MemoryRealtimeCache
from ..cache.cache_coordinator import CacheCoordinator

logger = create_component_logger("RealtimeDataHandler")


class RealtimeDataHandler:
    """
    실시간 데이터 전담 처리기

    Smart Data Provider에서 실시간 데이터 관련 기능을 분리한 클래스입니다.
    - 티커 데이터 (단일/다중)
    - 호가창 데이터
    - 체결 내역 데이터
    - 실시간 캐시 최적화
    """

    def __init__(self,
                 smart_router: SmartRouterAdapter,
                 realtime_cache: MemoryRealtimeCache,
                 cache_coordinator: CacheCoordinator):
        """
        Args:
            smart_router: Smart Router 어댑터
            realtime_cache: 메모리 실시간 캐시
            cache_coordinator: 캐시 조정자
        """
        self.smart_router = smart_router
        self.realtime_cache = realtime_cache
        self.cache_coordinator = cache_coordinator

        # 성능 모니터링
        self._request_count = 0
        self._cache_hits = 0
        self._api_calls = 0

        logger.info("실시간 데이터 처리기 초기화 완료")

    # =====================================
    # 티커 데이터 API
    # =====================================

    async def get_ticker(self,
                         symbol: str,
                         priority: Priority = Priority.HIGH) -> DataResponse:
        """
        실시간 티커 조회

        Args:
            symbol: 심볼
            priority: 요청 우선순위

        Returns:
            DataResponse 객체
        """
        start_time_ms = time.time() * 1000
        self._request_count += 1

        logger.debug(f"티커 조회 요청: {symbol}, priority={priority}")

        try:
            # 1. 새로운 메모리 캐시 확인
            cached_ticker = self.realtime_cache.get_ticker(symbol)

            if cached_ticker:
                self._cache_hits += 1
                # 캐시 조정자에 적중 기록
                self.cache_coordinator.record_access("ticker", symbol, cache_hit=True)

                response_time = time.time() * 1000 - start_time_ms

                metadata = ResponseMetadata(
                    priority_used=priority,
                    source="memory_cache",
                    response_time_ms=response_time,
                    cache_hit=True
                )

                logger.debug(f"티커 캐시 히트: {symbol}, {response_time:.1f}ms")

                return DataResponse(
                    success=True,
                    data=cached_ticker,
                    metadata=metadata
                )

            # 2. Smart Router 연동
            logger.debug(f"티커 캐시 미스: {symbol}, Smart Router 연동 시도")

            # 캐시 조정자에 미스 기록
            self.cache_coordinator.record_access("ticker", symbol, cache_hit=False)

            try:
                smart_result = await self.smart_router.get_ticker(symbol, priority)

                if smart_result.get('success', False):
                    ticker_data = smart_result.get('data')
                    if ticker_data:
                        # 새로운 메모리 캐시에 저장 (최적 TTL 적용)
                        optimal_ttl = self.cache_coordinator.get_optimal_ttl("ticker", symbol)
                        self.realtime_cache.set_ticker(symbol, ticker_data, ttl=optimal_ttl)

                        response_time = time.time() * 1000 - start_time_ms
                        logger.info(f"Smart Router 티커 성공: {symbol}, TTL={optimal_ttl:.1f}s, {response_time:.1f}ms")

                        return DataResponse(
                            success=True,
                            data=ticker_data,
                            metadata=ResponseMetadata(
                                priority_used=priority,
                                source="smart_router",
                                response_time_ms=response_time,
                                cache_hit=False
                            )
                        )
                else:
                    logger.error(f"Smart Router 티커 실패: {symbol}, {smart_result.get('error')}")

            except Exception as e:
                logger.error(f"Smart Router 티커 연동 오류: {symbol}, {e}")

            return DataResponse(
                success=False,
                error="티커 데이터 조회 실패",
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="failed",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

        except Exception as e:
            logger.error(f"티커 조회 실패: {symbol}, {e}")
            return DataResponse(
                success=False,
                error=str(e),
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="error",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

    async def get_tickers(self,
                          symbols: List[str],
                          priority: Priority = Priority.HIGH) -> DataResponse:
        """
        다중 심볼 티커 조회

        Args:
            symbols: 심볼 리스트
            priority: 요청 우선순위

        Returns:
            DataResponse 객체
        """
        start_time_ms = time.time() * 1000
        self._request_count += 1

        logger.debug(f"다중 티커 조회: {len(symbols) if symbols else 0}개 심볼, priority={priority}")

        # 기본 입력 검증만 유지
        if not symbols or not isinstance(symbols, list):
            logger.warning("심볼 리스트가 비어있거나 유효하지 않음")
            return DataResponse(
                success=False,
                error="심볼 리스트가 필요합니다",
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="validation_error",
                    response_time_ms=time.time() * 1000 - start_time_ms,
                    cache_hit=False
                )
            )

        try:
            # 캐시 최적화 구현
            results = {}
            cache_hits = 0
            uncached_symbols = []

            # 1. 캐시에서 먼저 조회
            for symbol in symbols:
                cached_data = self.realtime_cache.get_ticker(symbol)
                if cached_data:
                    results[symbol] = cached_data
                    cache_hits += 1
                else:
                    uncached_symbols.append(symbol)

            # 캐시 조회 결과를 간결하게 로그 출력
            if cache_hits > 0 or len(uncached_symbols) > 0:
                logger.info(f"📊 캐시 조회 결과: {cache_hits}개 히트, {len(uncached_symbols)}개 미스")
            else:
                logger.debug(f"캐시 조회 결과: {cache_hits}개 히트, {len(uncached_symbols)}개 미스")

            # 2. 캐시 미스된 심볼들을 한번에 조회 (분할 없음)
            if uncached_symbols:
                try:
                    # Smart Router 배치 조회는 향후 구현 예정
                    # 현재는 바로 업비트 API 폴백 처리
                    raise Exception("Smart Router 배치 조회 미구현")

                except Exception as router_error:
                    logger.warning(f"Smart Router 배치 조회 실패: {router_error}, 업비트 API 폴백")

                    # 폴백: 업비트 API 직접 전체 조회 (분할 없음)
                    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient

                    # aiohttp 세션 정리를 위해 async context manager 사용
                    async with UpbitPublicClient() as upbit_client:
                        # 모든 심볼을 한번에 조회 (업비트 API는 실제로 분할이 필요 없음)
                        try:
                            tickers = await upbit_client.get_tickers(uncached_symbols)
                            saved_count = 0
                            for ticker in tickers:
                                symbol = ticker['market']
                                results[symbol] = ticker
                                # 캐시에 저장
                                self.realtime_cache.set_ticker(symbol, ticker)
                                saved_count += 1

                            logger.info(f"업비트 API 전체 조회 성공: {len(tickers)}개 심볼")
                            if saved_count > 0:
                                logger.info(f"📦 티커 배치 캐시 저장 완료: {saved_count}개 심볼 (로그 간소화)")
                        except Exception as api_error:
                            logger.error(f"업비트 API 조회 실패: {api_error}")

            response_time = time.time() * 1000 - start_time_ms

            metadata = ResponseMetadata(
                priority_used=priority,
                source="mixed" if cache_hits > 0 else "api_batch",
                response_time_ms=response_time,
                cache_hit=cache_hits > 0,
                records_count=len(results)
            )

            return DataResponse(
                success=True,
                data=results,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"다중 티커 조회 실패: {e}")
            return DataResponse(
                success=False,
                error=str(e),
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="error",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

    # =====================================
    # 호가창 데이터 API
    # =====================================

    async def get_orderbook(self,
                            symbol: str,
                            priority: Priority = Priority.HIGH) -> DataResponse:
        """
        호가창 조회

        Args:
            symbol: 심볼
            priority: 요청 우선순위

        Returns:
            DataResponse 객체
        """
        start_time_ms = time.time() * 1000
        self._request_count += 1

        logger.debug(f"호가창 조회: {symbol}, priority={priority}")

        try:
            # 1. 메모리 캐시 확인
            cached_orderbook = self.realtime_cache.get_orderbook(symbol)

            if cached_orderbook:
                self._cache_hits += 1
                # 캐시 조정자에 적중 기록
                self.cache_coordinator.record_access("orderbook", symbol, cache_hit=True)

                response_time = time.time() * 1000 - start_time_ms

                metadata = ResponseMetadata(
                    priority_used=priority,
                    source="memory_cache",
                    response_time_ms=response_time,
                    cache_hit=True
                )

                logger.debug(f"호가 캐시 히트: {symbol}, {response_time:.1f}ms")

                return DataResponse(
                    success=True,
                    data=cached_orderbook,
                    metadata=metadata
                )

            # 2. Smart Router 연동
            logger.debug(f"호가 캐시 미스: {symbol}, Smart Router 연동 시도")

            # 캐시 조정자에 미스 기록
            self.cache_coordinator.record_access("orderbook", symbol, cache_hit=False)

            try:
                smart_result = await self.smart_router.get_orderbook(symbol, priority)

                if smart_result.get('success', False):
                    orderbook_data = smart_result.get('data')
                    if orderbook_data:
                        # 메모리 캐시에 저장 (최적 TTL 적용)
                        optimal_ttl = self.cache_coordinator.get_optimal_ttl("orderbook", symbol)
                        self.realtime_cache.set_orderbook(symbol, orderbook_data, ttl=optimal_ttl)

                        response_time = time.time() * 1000 - start_time_ms
                        logger.info(f"Smart Router 호가 성공: {symbol}, TTL={optimal_ttl:.1f}s, {response_time:.1f}ms")

                        return DataResponse(
                            success=True,
                            data=orderbook_data,
                            metadata=ResponseMetadata(
                                priority_used=priority,
                                source="smart_router",
                                response_time_ms=response_time,
                                cache_hit=False
                            )
                        )
                else:
                    logger.error(f"Smart Router 호가 실패: {symbol}, {smart_result.get('error')}")

            except Exception as e:
                logger.error(f"Smart Router 호가 연동 오류: {symbol}, {e}")

            return DataResponse(
                success=False,
                error="호가창 조회 실패",
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="failed",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

        except Exception as e:
            logger.error(f"호가창 조회 실패: {symbol}, {e}")
            return DataResponse(
                success=False,
                error=str(e),
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="error",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

    # =====================================
    # 체결 내역 API
    # =====================================

    async def get_trades(self,
                         symbol: str,
                         count: int = 100,
                         priority: Priority = Priority.NORMAL) -> DataResponse:
        """
        체결 내역 조회

        Args:
            symbol: 심볼
            count: 조회할 체결 개수
            priority: 요청 우선순위

        Returns:
            DataResponse 객체
        """
        start_time_ms = time.time() * 1000
        self._request_count += 1

        logger.debug(f"체결 내역 조회: {symbol}, count={count}, priority={priority}")

        # 체결 개수 범위 검증 (업비트 API 공식 한계: 500개)
        if count <= 0 or count > 500:  # 업비트 공식 최대값
            logger.warning(f"유효하지 않은 체결 개수: {count}")
            return DataResponse(
                success=False,
                error=f"체결 개수는 1~500 범위여야 합니다. 입력값: {count} (업비트 공식 한계)",
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="validation_error",
                    response_time_ms=time.time() * 1000 - start_time_ms,
                    cache_hit=False
                )
            )

        try:
            # 1. 메모리 캐시 확인
            cached_trades = self.realtime_cache.get_trades(symbol)

            if cached_trades:
                self._cache_hits += 1
                # 캐시 조정자에 적중 기록
                self.cache_coordinator.record_access("trades", symbol, cache_hit=True)

                response_time = time.time() * 1000 - start_time_ms

                # 요청된 개수만큼 반환
                trades_data = cached_trades[:count] if len(cached_trades) > count else cached_trades

                metadata = ResponseMetadata(
                    priority_used=priority,
                    source="memory_cache",
                    response_time_ms=response_time,
                    cache_hit=True,
                    records_count=len(trades_data)
                )

                logger.debug(f"체결 캐시 히트: {symbol}, {len(trades_data)}개, {response_time:.1f}ms")

                return DataResponse(
                    success=True,
                    data=trades_data,
                    metadata=metadata
                )

            # 2. Smart Router 연동
            logger.debug(f"체결 캐시 미스: {symbol}, Smart Router 연동 시도")

            # 캐시 조정자에 미스 기록
            self.cache_coordinator.record_access("trades", symbol, cache_hit=False)

            try:
                smart_result = await self.smart_router.get_trades(symbol, count, priority)

                if smart_result.get('success', False):
                    raw_trades_data = smart_result.get('data', {})

                    # Smart Router 응답에서 실제 체결 리스트 추출
                    if isinstance(raw_trades_data, dict):
                        trades_data = raw_trades_data.get('data', [])
                    else:
                        trades_data = raw_trades_data if isinstance(raw_trades_data, list) else []

                    if trades_data:
                        # 메모리 캐시에 저장 (최적 TTL 적용)
                        optimal_ttl = self.cache_coordinator.get_optimal_ttl("trades", symbol)
                        self.realtime_cache.set_trades(symbol, trades_data, ttl=optimal_ttl)

                        response_time = time.time() * 1000 - start_time_ms
                        logger.info(f"Smart Router 체결 성공: {symbol}, {len(trades_data)}개, "
                                    f"TTL={optimal_ttl:.1f}s, {response_time:.1f}ms")

                        return DataResponse(
                            success=True,
                            data=trades_data,
                            metadata=ResponseMetadata(
                                priority_used=priority,
                                source="smart_router",
                                response_time_ms=response_time,
                                cache_hit=False,
                                records_count=len(trades_data)
                            )
                        )
                else:
                    logger.error(f"Smart Router 체결 실패: {symbol}, {smart_result.get('error')}")

            except Exception as e:
                logger.error(f"Smart Router 체결 연동 오류: {symbol}, {e}")

            return DataResponse(
                success=False,
                error="체결 내역 조회 실패",
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="failed",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

        except Exception as e:
            logger.error(f"체결 내역 조회 실패: {symbol}, {e}")
            return DataResponse(
                success=False,
                error=str(e),
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="error",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

    # =====================================
    # 성능 및 통계
    # =====================================

    def get_performance_stats(self) -> Dict[str, Any]:
        """실시간 데이터 처리기 성능 통계 조회"""
        cache_hit_rate = (self._cache_hits / self._request_count * 100) if self._request_count > 0 else 0

        return {
            "realtime_handler_stats": {
                "total_requests": self._request_count,
                "cache_hits": self._cache_hits,
                "api_calls": self._api_calls,
                "cache_hit_rate": cache_hit_rate
            }
        }

    def reset_stats(self) -> None:
        """통계 초기화"""
        self._request_count = 0
        self._cache_hits = 0
        self._api_calls = 0
        logger.info("실시간 데이터 처리기 통계 초기화 완료")

    def __str__(self) -> str:
        stats = self.get_performance_stats()
        handler_stats = stats.get("realtime_handler_stats", {})

        total_requests = handler_stats.get("total_requests", 0)
        cache_hit_rate = handler_stats.get("cache_hit_rate", 0)

        return (f"RealtimeDataHandler("
                f"requests={total_requests}, "
                f"cache_hit_rate={cache_hit_rate:.1f}%)")
