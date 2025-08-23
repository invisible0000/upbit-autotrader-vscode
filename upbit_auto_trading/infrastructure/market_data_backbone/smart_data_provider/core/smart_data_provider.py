"""
Smart Data Provider 메인 클래스
모든 마켓 데이터 요청의 단일 진입점을 제공합니다.
"""
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
import time
import asyncio

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.repositories.candle_repository_interface import CandleRepositoryInterface
from upbit_auto_trading.infrastructure.repositories.sqlite_candle_repository import SqliteCandleRepository
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseConnectionProvider
from ..models.priority import Priority
from ..models.responses import DataResponse, ResponseMetadata
from ..adapters.smart_router_adapter import SmartRouterAdapter
from ..cache.memory_realtime_cache import MemoryRealtimeCache
from ..cache.cache_coordinator import CacheCoordinator
from ..cache.storage_performance_monitor import get_performance_monitor
from ..processing.request_splitter import RequestSplitter
from ..processing.response_merger import ResponseMerger

logger = create_component_logger("SmartDataProvider")


class SmartDataProvider:
    """
    스마트 데이터 제공자

    모든 마켓 데이터 요청을 통합 처리하는 메인 클래스입니다.
    - SQLite 캐시 + 메모리 캐시 이중 시스템
    - 우선순위 기반 요청 처리
    - Smart Router V2.0 연동
    - 자동 분할/병합 처리
    """

    def __init__(self,
                 candle_repository: Optional[CandleRepositoryInterface] = None,
                 db_path: str = "data/market_data.sqlite3"):
        """
        Args:
            candle_repository: 캔들 Repository (의존성 주입)
            db_path: 레거시 호환성을 위한 DB 경로 (Repository가 없을 때만 사용)
        """
        self.db_path = db_path

        # Repository 패턴 사용 (DDD 준수)
        if candle_repository:
            self.candle_repository = candle_repository
        else:
            # 레거시 호환성: DatabaseManager 자동 초기화
            db_provider = DatabaseConnectionProvider()
            if not hasattr(db_provider, '_db_manager') or db_provider._db_manager is None:
                db_provider.initialize({
                    "market_data": db_path,
                    "settings": "data/settings.sqlite3",
                    "strategies": "data/strategies.sqlite3"
                })
            self.candle_repository = SqliteCandleRepository(db_provider.get_manager())
            logger.info("SqliteCandleRepository 자동 초기화 완료 (레거시 호환성)")

        # Smart Router 어댑터
        self.smart_router = SmartRouterAdapter()

        # 새로운 메모리 실시간 캐시 시스템
        self.realtime_cache = MemoryRealtimeCache()

        # 캐시 조정자 (Phase 2.3)
        self.cache_coordinator = CacheCoordinator(self.realtime_cache)

        # 성능 모니터 (Phase 2.4)
        self.performance_monitor = get_performance_monitor()

        # 요청 분할 및 병합 처리기 (Phase 3.1)
        self.request_splitter = RequestSplitter()
        self.response_merger = ResponseMerger()

        # 기존 메모리 캐시 (호환성 유지)
        self._memory_cache: Dict[str, Dict] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # 성능 모니터링
        self._request_count = 0
        self._cache_hits = 0
        self._api_calls = 0

        logger.info("Smart Data Provider 초기화 완료 - 캐시 조정자 포함")

    # =====================================
    # 유틸리티 메서드
    # =====================================

    # 검증 로직은 validation/input_validator.py로 분리됨
    # 마켓 API에서 받은 데이터는 검증 불필요

    # =====================================
    # 캔들 데이터 API
    # =====================================

    async def get_candles(self,
                         symbol: str,
                         timeframe: str,
                         count: Optional[int] = None,
                         start_time: Optional[str] = None,
                         end_time: Optional[str] = None,
                         priority: Priority = Priority.NORMAL) -> DataResponse:
        """
        캔들 데이터 조회

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m', '1h')
            count: 조회할 캔들 개수 (기본: 200)
            start_time: 시작 시간 (ISO format)
            end_time: 종료 시간 (ISO format)
            priority: 요청 우선순위

        Returns:
            DataResponse 객체
        """
        start_time_ms = time.time() * 1000
        self._request_count += 1

        logger.debug(f"캔들 데이터 요청: {symbol} {timeframe}, count={count}, priority={priority}")

        # 기본 캔들 개수 검증 (0 이하만 방지)
        if count is not None and count <= 0:
            logger.warning(f"유효하지 않은 캔들 개수: {count}")
            return DataResponse(
                success=False,
                error=f"캔들 개수는 1 이상이어야 합니다. 입력값: {count}",
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="validation_error",
                    response_time_ms=time.time() * 1000 - start_time_ms,
                    cache_hit=False
                )
            )

        try:
            # 1. SQLite 캐시에서 조회
            cached_data = await self._get_candles_from_cache(
                symbol, timeframe, count, start_time, end_time
            )

            if cached_data:
                self._cache_hits += 1
                end_time_ms = time.time() * 1000
                response_time = end_time_ms - start_time_ms

                metadata = ResponseMetadata(
                    priority_used=priority,
                    source="sqlite_cache",
                    response_time_ms=response_time,
                    cache_hit=True,
                    records_count=len(cached_data)
                )

                logger.info(f"캔들 캐시 히트: {symbol} {timeframe}, {len(cached_data)}개, {response_time:.1f}ms")

                return DataResponse(
                    success=True,
                    data=cached_data,
                    metadata=metadata
                )

            # 2. 요청 분할 검사 및 Smart Router 호출
            logger.info(f"캔들 캐시 미스: {symbol} {timeframe}, Smart Router 시도")

            # RequestSplitter로 대용량 요청 분할 검사
            datetime_start = None
            datetime_end = None
            if start_time:
                try:
                    datetime_start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                except:
                    logger.warning(f"시작 시간 파싱 실패: {start_time}")
            if end_time:
                try:
                    datetime_end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                except:
                    logger.warning(f"종료 시간 파싱 실패: {end_time}")

            # 분할 요청 생성
            split_requests = self.request_splitter.split_candle_request(
                request_id=f"candle_{symbol}_{timeframe}_{int(time.time())}",
                symbol=symbol,
                timeframe=timeframe,
                count=count,
                start_time=datetime_start,
                end_time=datetime_end
            )

            if len(split_requests) > 1:
                logger.info(f"대용량 캔들 요청 분할: {len(split_requests)}개 요청으로 분할")

                # 분할된 요청들을 병렬 처리
                all_candle_data = []

                for split_req in split_requests:
                    logger.debug(f"분할 요청 처리: {split_req.split_id} ({split_req.split_index + 1}/{split_req.total_splits})")

                    # 분할된 요청의 시간을 문자열로 변환
                    split_start_str = split_req.start_time.isoformat() if split_req.start_time else None
                    split_end_str = split_req.end_time.isoformat() if split_req.end_time else None

                    split_result = await self.smart_router.get_candles(
                        symbol=split_req.symbol,
                        timeframe=split_req.timeframe,
                        count=split_req.count,
                        start_time=split_start_str,
                        end_time=split_end_str,
                        priority=priority
                    )

                    if split_result.get('success', False):
                        # Smart Router 응답에서 실제 캔들 리스트 추출
                        raw_data = split_result.get('data', {})
                        if isinstance(raw_data, dict):
                            split_candles = raw_data.get('_candles_list', [])
                        else:
                            split_candles = raw_data if isinstance(raw_data, list) else []

                        all_candle_data.extend(split_candles)
                        logger.debug(f"분할 요청 완료: {len(split_candles)}개 캔들")
                    else:
                        error_msg = split_result.get('error', f'분할 요청 실패: {split_req.split_id}')
                        logger.error(f"분할 요청 실패: {error_msg}")
                        return DataResponse(
                            success=False,
                            error=f"분할 요청 실패: {error_msg}",
                            metadata=ResponseMetadata(
                                priority_used=priority,
                                source="split_request_error",
                                response_time_ms=time.time() * 1000 - start_time_ms,
                                cache_hit=False
                            )
                        )

                # 분할된 결과 병합
                logger.info(f"분할 요청 완료: 총 {len(all_candle_data)}개 캔들 수집")

                end_time_ms = time.time() * 1000
                response_time = end_time_ms - start_time_ms

                metadata = ResponseMetadata(
                    priority_used=priority,
                    source="smart_router_split",
                    response_time_ms=response_time,
                    cache_hit=False,
                    records_count=len(all_candle_data)
                )

                # API로 받은 데이터를 SQLite 캐시에 저장
                try:
                    await self._save_candles_to_cache(symbol, timeframe, all_candle_data)
                    logger.debug(f"분할 캔들 데이터 캐시 저장 완료: {symbol} {timeframe}, {len(all_candle_data)}개")
                except Exception as e:
                    logger.warning(f"분할 캔들 데이터 캐시 저장 실패: {symbol} {timeframe}, {e}")

                return DataResponse(
                    success=True,
                    data=all_candle_data,
                    metadata=metadata
                )
            else:
                # 단일 요청 처리 (기존 로직)
                smart_router_result = await self.smart_router.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    count=count,
                    start_time=start_time,
                    end_time=end_time,
                priority=priority
            )

            if smart_router_result.get('success', False):
                # Smart Router 성공
                self._api_calls += 1
                raw_data = smart_router_result.get('data', {})

                # Smart Router 응답에서 실제 캔들 리스트 추출
                if isinstance(raw_data, dict):
                    api_data = raw_data.get('_candles_list', [])
                else:
                    api_data = raw_data if isinstance(raw_data, list) else []

                end_time_ms = time.time() * 1000
                response_time = end_time_ms - start_time_ms

                metadata = ResponseMetadata(
                    priority_used=priority,
                    source=smart_router_result.get('source', 'smart_router'),
                    response_time_ms=response_time,
                    cache_hit=False,
                    records_count=len(api_data)
                )

                logger.info(f"Smart Router 캔들 성공: {symbol} {timeframe}, {len(api_data)}개")

                # API로 받은 데이터를 SQLite 캐시에 저장
                try:
                    await self._save_candles_to_cache(symbol, timeframe, api_data)
                    logger.debug(f"캔들 데이터 캐시 저장 완료: {symbol} {timeframe}, {len(api_data)}개")
                except Exception as e:
                    logger.warning(f"캔들 데이터 캐시 저장 실패: {symbol} {timeframe}, {e}")

                return DataResponse(
                    success=True,
                    data=api_data,
                    metadata=metadata
                )
            else:
                # Smart Router 실패
                error_msg = smart_router_result.get('error', 'Smart Router 연동 실패')
                logger.warning(f"Smart Router 캔들 실패: {symbol} {timeframe}, {error_msg}")

            return DataResponse(
                success=False,
                error="캔들 데이터 조회 실패 - 캐시 미스 및 API 호출 실패",
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="failed",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

        except Exception as e:
            logger.error(f"캔들 데이터 조회 실패: {symbol} {timeframe}, {e}")
            return DataResponse(
                success=False,
                error=str(e),
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="error",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )

    async def _get_candles_from_cache(self,
                                      symbol: str,
                                      timeframe: str,
                                      count: Optional[int],
                                      start_time: Optional[str],
                                      end_time: Optional[str]) -> Optional[List[Dict]]:
        """SQLite 캐시에서 캔들 데이터 조회 (Repository 패턴 사용)"""
        try:
            candles = await self.candle_repository.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
                limit=count
            )

            if candles:
                logger.debug(f"캐시에서 {len(candles)}개 캔들 조회됨: {symbol} {timeframe}")
                return candles

        except Exception as e:
            logger.error(f"캔들 캐시 조회 실패: {symbol} {timeframe}, {e}")

        return None

    # =====================================
    # 실시간 데이터 API
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

            logger.debug(f"캐시 조회 결과: {cache_hits}개 히트, {len(uncached_symbols)}개 미스")

            # 2. 캐시 미스된 심볼들을 한번에 조회 (분할 없음)
            if uncached_symbols:
                try:
                    # Smart Router를 통한 배치 조회 시도
                    batch_response = await self.smart_router.get_tickers_batch(
                        symbols=uncached_symbols,
                        priority=priority
                    )

                    if batch_response.get('success', False) and batch_response.get('data'):
                        batch_data = batch_response.get('data', {})
                        for symbol in uncached_symbols:
                            if symbol in batch_data and batch_data[symbol]:
                                results[symbol] = batch_data[symbol]
                                # 캐시에 저장
                                self.realtime_cache.set_ticker(symbol, batch_data[symbol])

                        logger.info(f"Smart Router 배치 조회 성공: {len(batch_data)}개 심볼")
                    else:
                        logger.warning("Smart Router 배치 조회 실패, 폴백 처리")
                        raise Exception("Smart Router 배치 조회 실패")

                except Exception as router_error:
                    logger.warning(f"Smart Router 배치 조회 실패: {router_error}, 업비트 API 폴백")

                    # 폴백: 업비트 API 직접 전체 조회 (분할 없음)
                    from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
                    upbit_client = UpbitPublicClient()

                    # 모든 심볼을 한번에 조회 (업비트 API는 실제로 분할이 필요 없음)
                    try:
                        tickers = await upbit_client.get_tickers(uncached_symbols)
                        for ticker in tickers:
                            symbol = ticker['market']
                            results[symbol] = ticker
                            # 캐시에 저장
                            self.realtime_cache.set_ticker(symbol, ticker)

                        logger.info(f"업비트 API 전체 조회 성공: {len(tickers)}개 심볼")
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

            # 2. Smart Router 연동 (향후 구현)
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
    # 메모리 캐시 관리
    # =====================================

    def _get_from_memory_cache(self, key: str, max_age_seconds: float = 60.0) -> Optional[Dict]:
        """메모리 캐시에서 데이터 조회"""
        if key not in self._memory_cache:
            return None

        cached_time = self._cache_timestamps.get(key)
        if not cached_time:
            return None

        age_seconds = (datetime.now() - cached_time).total_seconds()
        if age_seconds > max_age_seconds:
            # 만료된 캐시 삭제
            del self._memory_cache[key]
            del self._cache_timestamps[key]
            return None

        return self._memory_cache[key]

    def _set_memory_cache(self, key: str, data: Dict) -> None:
        """메모리 캐시에 데이터 저장"""
        self._memory_cache[key] = data
        self._cache_timestamps[key] = datetime.now()

    def clear_memory_cache(self) -> None:
        """메모리 캐시 전체 삭제"""
        # 기존 캐시 삭제
        self._memory_cache.clear()
        self._cache_timestamps.clear()

        # 새로운 실시간 캐시 삭제
        self.realtime_cache.invalidate_all()

        logger.info("메모리 캐시 전체 삭제 완료")

    def invalidate_symbol_cache(self, symbol: str) -> None:
        """특정 심볼의 모든 캐시 무효화"""
        self.realtime_cache.invalidate_symbol(symbol)
        logger.info(f"심볼 캐시 무효화 완료: {symbol}")

    def cleanup_expired_cache(self) -> Dict[str, int]:
        """만료된 캐시 정리"""
        return self.realtime_cache.cleanup_expired()

    def get_cache_status(self) -> Dict[str, Any]:
        """캐시 상태 조회"""
        realtime_stats = self.realtime_cache.get_performance_stats()

        return {
            "realtime_cache": {
                "ticker_keys": len(self.realtime_cache.get_cache_keys("ticker")),
                "orderbook_keys": len(self.realtime_cache.get_cache_keys("orderbook")),
                "trades_keys": len(self.realtime_cache.get_cache_keys("trades")),
                "market_keys": len(self.realtime_cache.get_cache_keys("market")),
                "performance": realtime_stats
            },
            "legacy_cache": {
                "size": len(self._memory_cache),
                "keys": list(self._memory_cache.keys())[:10]  # 최대 10개만 표시
            }
        }

    # =====================================
    # 내부 유틸리티 메서드
    # =====================================

    async def _save_candles_to_cache(self, symbol: str, timeframe: str, candles_data: List[Dict]) -> None:
        """API로 받은 캔들 데이터를 SQLite 캐시에 저장 (Repository 패턴 사용)"""
        try:
            if not candles_data:
                return

            # Repository를 통한 데이터 저장 (FOREIGN KEY 제약 자동 해결)
            success_count = await self.candle_repository.insert_candles(symbol, timeframe, candles_data)

            if success_count > 0:
                logger.debug(f"캔들 캐시 저장 완료: {symbol} {timeframe}, {success_count}/{len(candles_data)}개")
            else:
                logger.warning(f"캔들 캐시 저장 실패: {symbol} {timeframe}, 저장된 데이터 없음")

        except Exception as e:
            logger.error(f"캔들 캐시 저장 오류: {symbol} {timeframe}, {e}")
            # Repository에서 예외가 발생해도 상위 로직은 계속 진행 (API 데이터는 이미 반환됨)

    def _format_candle_for_cache(self, candle: Dict) -> Optional[Dict]:
        """API 캔들 데이터를 캐시 저장용 포맷으로 변환 (업비트 API는 이미 완전 호환)"""
        try:
            # 업비트 API 응답은 이미 DB 스키마와 100% 호환되므로 그대로 반환
            return candle
        except Exception as e:
            logger.warning(f"캔들 데이터 포맷 변환 실패: {e}")
            return None

    # =====================================
    # 성능 및 통계
    # =====================================

    def get_performance_stats(self) -> Dict[str, Union[int, float, Dict]]:
        """성능 통계 조회 (캐시 조정자 통계 포함)"""
        cache_hit_rate = (self._cache_hits / self._request_count * 100) if self._request_count > 0 else 0

        # 새로운 메모리 캐시 통계
        realtime_cache_stats = self.realtime_cache.get_performance_stats()
        memory_usage = realtime_cache_stats.get("memory_usage", {})
        total_entries = memory_usage.get("total_entries", 0) if isinstance(memory_usage, dict) else 0

        # 캐시 조정자 종합 통계
        coordinator_stats = self.cache_coordinator.get_comprehensive_stats()

        return {
            "provider_stats": {
                "total_requests": self._request_count,
                "cache_hits": self._cache_hits,
                "api_calls": self._api_calls,
                "cache_hit_rate": cache_hit_rate,
                "legacy_memory_cache_size": len(self._memory_cache)
            },
            "realtime_cache_stats": realtime_cache_stats,
            "cache_coordinator_stats": coordinator_stats,
            "memory_usage": {
                "realtime_cache_mb": self.realtime_cache.get_memory_usage_mb(),
                "total_entries": total_entries
            }
        }

    def reset_stats(self) -> None:
        """통계 초기화"""
        self._request_count = 0
        self._cache_hits = 0
        self._api_calls = 0
        logger.info("성능 통계 초기화 완료")

    # === Smart Candle Collector 기능 ===

    async def get_continuous_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        include_empty: bool = True,
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """
        연속된 캔들 데이터 조회 (빈 캔들 포함/제외 선택 가능)

        Args:
            symbol: 거래 심볼
            timeframe: 타임프레임
            start_time: 시작 시간
            end_time: 종료 시간
            include_empty: 빈 캔들 포함 여부 (True: 차트용, False: 지표용)
            priority: 요청 우선순위

        Returns:
            연속된 캔들 데이터 응답
        """
        from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.processing.collection_status_manager import (
            CollectionStatusManager
        )

        self._request_count += 1
        start_time_ms = time.time() * 1000

        logger.info(
            f"연속 캔들 요청: {symbol} {timeframe} "
            f"{start_time.strftime('%Y-%m-%d %H:%M')} ~ {end_time.strftime('%Y-%m-%d %H:%M')} "
            f"(빈 캔들 {'포함' if include_empty else '제외'})"
        )

        try:
            # CollectionStatusManager 초기화
            collection_manager = CollectionStatusManager(self.db_path)

            if include_empty:
                # 차트용: 빈 캔들을 채워서 연속 데이터 제공
                # 1. 기존 get_candles로 실제 데이터 조회
                candles_response = await self.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                    priority=priority
                )

                if not candles_response.success:
                    return candles_response

                # 2. 빈 캔들 채움 처리
                candles_data = candles_response.data or []
                continuous_candles = collection_manager.fill_empty_candles(
                    candles=candles_data,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time,
                    end_time=end_time
                )

                # 3. CandleWithStatus를 Dict로 변환
                result_data = []
                for candle_with_status in continuous_candles:
                    candle_dict = {
                        'market': candle_with_status.market,
                        'candle_date_time_utc': candle_with_status.candle_date_time_utc.isoformat() + 'Z',
                        'candle_date_time_kst': candle_with_status.candle_date_time_kst.isoformat() + 'Z',
                        'opening_price': float(candle_with_status.opening_price),
                        'high_price': float(candle_with_status.high_price),
                        'low_price': float(candle_with_status.low_price),
                        'trade_price': float(candle_with_status.trade_price),
                        'timestamp': candle_with_status.timestamp,
                        'candle_acc_trade_price': float(candle_with_status.candle_acc_trade_price),
                        'candle_acc_trade_volume': float(candle_with_status.candle_acc_trade_volume),
                        'unit': candle_with_status.unit,
                        'is_empty': candle_with_status.is_empty,
                        'collection_status': candle_with_status.collection_status.value
                    }
                    result_data.append(candle_dict)

                end_time_ms = time.time() * 1000
                response_time = end_time_ms - start_time_ms

                cache_hit = candles_response.metadata.cache_hit if candles_response.metadata else False

                metadata = ResponseMetadata(
                    priority_used=priority,
                    source="continuous_with_empty",
                    response_time_ms=response_time,
                    cache_hit=cache_hit,
                    records_count=len(result_data)
                )

                logger.info(f"연속 캔들 응답 (빈 캔들 포함): {len(result_data)}개")
                return DataResponse(success=True, data=result_data, metadata=metadata)

            else:
                # 지표용: 실제 거래 데이터만 제공 (기존 get_candles와 동일)
                logger.debug("지표용 데이터 요청 - 기존 get_candles 사용")
                response = await self.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                    priority=priority
                )

                # 메타데이터에 source 정보 업데이트 (새로운 ResponseMetadata 생성)
                if response.success and response.metadata:
                    new_metadata = ResponseMetadata(
                        priority_used=response.metadata.priority_used,
                        source=f"{response.metadata.source}_indicators_only",
                        response_time_ms=response.metadata.response_time_ms,
                        cache_hit=response.metadata.cache_hit,
                        records_count=response.metadata.records_count
                    )
                    response = DataResponse(
                        success=response.success,
                        data=response.data,
                        error=response.error,
                        metadata=new_metadata
                    )

                return response

        except Exception as e:
            logger.error(f"연속 캔들 조회 실패: {symbol} {timeframe}, {e}")
            end_time_ms = time.time() * 1000
            response_time = end_time_ms - start_time_ms

            return DataResponse(
                success=False,
                error=f"연속 캔들 조회 실패: {str(e)}",
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="continuous_candles_error",
                    response_time_ms=response_time,
                    cache_hit=False
                )
            )

    def __str__(self) -> str:
        stats = self.get_performance_stats()
        provider_stats = stats.get("provider_stats", {})
        memory_usage = stats.get("memory_usage", {})

        # 안전한 값 추출
        total_requests = provider_stats.get("total_requests", 0) if isinstance(provider_stats, dict) else 0
        cache_hit_rate = provider_stats.get("cache_hit_rate", 0) if isinstance(provider_stats, dict) else 0
        total_entries = memory_usage.get("total_entries", 0) if isinstance(memory_usage, dict) else 0
        cache_mb = memory_usage.get("realtime_cache_mb", 0) if isinstance(memory_usage, dict) else 0

        return (f"SmartDataProvider("
                f"requests={total_requests}, "
                f"cache_hit_rate={cache_hit_rate:.1f}%, "
                f"realtime_cache={total_entries} entries, "
                f"memory≈{cache_mb:.1f}MB)")

    async def get_markets(self,
                          is_details: bool = False,
                          priority: Priority = Priority.NORMAL) -> DataResponse:
        """
        마켓 목록 조회

        Args:
            is_details: 상세 정보 포함 여부
            priority: 요청 우선순위

        Returns:
            DataResponse 객체
        """
        start_time_ms = time.time() * 1000
        self._request_count += 1

        logger.debug(f"마켓 목록 조회: is_details={is_details}, priority={priority}")

        try:
            # 현재 Smart Router는 마켓 목록 조회를 지원하지 않으므로
            # 직접 UpbitPublicClient 사용
            from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
            upbit_client = UpbitPublicClient()
            markets_data = await upbit_client.get_markets(is_details=is_details)

            response_time = time.time() * 1000 - start_time_ms
            return DataResponse(
                success=True,
                data=markets_data,
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="upbit_api_direct",
                    response_time_ms=response_time,
                    cache_hit=False,
                    records_count=len(markets_data)
                )
            )

        except Exception as e:
            logger.error(f"마켓 목록 조회 실패: {e}")
            return DataResponse(
                success=False,
                error=str(e),
                metadata=ResponseMetadata(
                    priority_used=priority,
                    source="error",
                    response_time_ms=time.time() * 1000 - start_time_ms
                )
            )
