"""
Smart Data Provider V4.0 - 메인 API

Layer 1: 통합 API 인터페이스
- 지능형 단일/다중 심볼 처리
- 계층적 캐시 시스템 통합
- 실시간 데이터 관리 통합
- 성능 최적화 (목표: 500+ symbols/sec)
- SmartRouter 호환성
"""
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .market_data_models import DataResponse, Priority, PerformanceMetrics
from .market_data_manager import MarketDataManager
from .market_data_cache import MarketDataCache
from .realtime_data_manager import RealtimeDataManager
from ..smart_routing.smart_router import SmartRouter
from ..smart_routing.models import DataRequest, DataType

logger = create_component_logger("SmartDataProvider")


@dataclass
class BatchRequestResult:
    """배치 요청 결과"""
    successful_symbols: List[str]
    failed_symbols: List[str]
    total_response_time_ms: float
    symbols_per_second: float
    cache_hit_rate: float
    individual_responses: Dict[str, Dict[str, Any]]


class SmartDataProvider:
    """Smart Data Provider V4.0 - 메인 클래스"""

    def __init__(self, max_workers: int = 10):
        # Layer 3: 데이터 관리
        self.data_manager = MarketDataManager()

        # Layer 2: 캐시 & 실시간
        self.cache_system = MarketDataCache()
        self.realtime_manager = RealtimeDataManager()

        # Layer 1: API 처리
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)

        # SmartRouter 통합 (실제 API 통신)
        self.smart_router = SmartRouter()

        # SmartRouter 사전 초기화 (WebSocket 연결 포함)
        self._initialize_smart_router()

        # 통계 및 모니터링
        self._request_count = 0
        self._start_time = time.time()
        self._lock = threading.RLock()

        # 성능 최적화 설정
        self._batch_threshold = 5  # 5개 이상일 때 배치 처리
        self._max_batch_size = 50  # 최대 50개씩 배치 처리

        logger.info(f"SmartDataProvider V4.0 초기화: max_workers={max_workers}")
        self._log_initialization_complete()

    def _initialize_smart_router(self) -> None:
        """SmartRouter 사전 초기화 (WebSocket 연결 포함)"""
        import asyncio
        try:
            # 이벤트 루프 확보
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # SmartRouter 비동기 초기화 (WebSocket 연결 포함)
            loop.run_until_complete(self.smart_router.initialize())
            logger.info("✅ SmartRouter 사전 초기화 완료 (WebSocket 연결됨)")

        except Exception as e:
            logger.warning(f"SmartRouter 초기화 중 오류: {e} - 데이터 요청 시 재시도")

    def _log_initialization_complete(self) -> None:
        """초기화 완료 로그"""
        logger.info("=" * 60)
        logger.info("🚀 Smart Data Provider V4.0 초기화 완료")
        logger.info("=" * 60)
        logger.info("📊 Layer 1: 지능형 API 처리 (단일/배치)")
        logger.info("⚡ Layer 2: 통합 캐시 + 실시간 관리")
        logger.info("🗄️  Layer 3: 데이터 관리 + DB 통합")
        logger.info("🎯 성능 목표: 500+ symbols/sec")
        logger.info("=" * 60)

    # =================================================================
    # 단일 심볼 처리 (SmartRouter 호환)
    # =================================================================

    def get_ticker(self, symbol: str, priority: Priority = Priority.NORMAL) -> DataResponse:
        """단일 심볼 티커 조회 (SmartRouter 호환)"""
        return self._get_single_data(symbol, "ticker", priority)

    def invalidate_cache(self, symbol: Optional[str] = None, data_type: Optional[str] = None) -> None:
        """캐시 무효화

        Args:
            symbol: 특정 심볼 캐시만 무효화 (None이면 모든 심볼)
            data_type: 특정 데이터 타입만 무효화 (None이면 모든 타입)
        """
        if symbol and data_type:
            # 특정 심볼의 특정 데이터 타입만 무효화
            cache_key = f"{data_type}_{symbol}"
            # FastCache는 delete 메서드가 없으므로 직접 삭제
            if hasattr(self.cache_system.fast_cache, '_cache'):
                with self.cache_system.fast_cache._lock:
                    self.cache_system.fast_cache._cache.pop(cache_key, None)
                    self.cache_system.fast_cache._timestamps.pop(cache_key, None)
            logger.info(f"캐시 무효화: {cache_key}")
        elif symbol:
            # 특정 심볼의 모든 데이터 타입 무효화
            data_types = ["ticker", "orderbook", "trades"]
            for dt in data_types:
                cache_key = f"{dt}_{symbol}"
                if hasattr(self.cache_system.fast_cache, '_cache'):
                    with self.cache_system.fast_cache._lock:
                        self.cache_system.fast_cache._cache.pop(cache_key, None)
                        self.cache_system.fast_cache._timestamps.pop(cache_key, None)
            logger.info(f"심볼 {symbol}의 모든 캐시 무효화")
        else:
            # 전체 캐시 무효화
            self.cache_system.fast_cache.clear()
            logger.info("전체 캐시 무효화")

    def _get_from_memory_cache_only(self, cache_key: str) -> Optional[dict]:
        """메모리 캐시에서만 조회 (DB 조회 안함)

        실시간 데이터(티커/호가/체결)는 메모리 캐시만 확인
        """
        # FastCache 먼저 확인 (가장 빠름)
        cached_data = self.cache_system.fast_cache.get(cache_key)
        if cached_data:
            return cached_data

        # MemoryRealtimeCache 확인
        if hasattr(self.cache_system, 'memory_cache'):
            cached_data = self.cache_system.memory_cache.get(cache_key)
            if cached_data:
                return cached_data

        return None

    def _store_in_memory_cache_only(self, cache_key: str, data: dict, data_type: str) -> None:
        """메모리 캐시에만 저장 (DB 저장 안함)

        실시간 데이터(티커/호가/체결)는 메모리 캐시만 사용
        """
        # FastCache에 저장 (200ms TTL)
        self.cache_system.fast_cache.set(cache_key, data)

        # MemoryRealtimeCache에 저장 (60초 TTL)
        if hasattr(self.cache_system, 'memory_cache'):
            ttl = 60.0 if data_type == "ticker" else 30.0  # 티커는 60초, 나머지는 30초
            self.cache_system.memory_cache.set(cache_key, data, ttl)

    def validate_data_integrity(self, data: dict, data_type: str) -> bool:
        """데이터 무결성 검증

        Args:
            data: 검증할 데이터
            data_type: 데이터 타입

        Returns:
            데이터가 유효한지 여부
        """
        if not isinstance(data, dict):
            return False

        if data_type == "ticker":
            required_fields = ["market", "trade_price", "timestamp"]
            return all(field in data for field in required_fields)
        elif data_type == "orderbook":
            required_fields = ["market", "orderbook_units"]
            return all(field in data for field in required_fields)
        elif data_type == "trades":
            required_fields = ["market", "trade_price", "trade_volume"]
            return all(field in data for field in required_fields)

        return True  # 기타 데이터 타입은 기본적으로 유효하다고 가정

    def get_orderbook(self, symbol: str, priority: Priority = Priority.NORMAL) -> DataResponse:
        """단일 심볼 호가 조회"""
        return self._get_single_data(symbol, "orderbook", priority)

    def get_trades(self, symbol: str, priority: Priority = Priority.NORMAL) -> DataResponse:
        """단일 심볼 체결 내역 조회"""
        return self._get_single_data(symbol, "trades", priority)

    def get_candles(
        self,
        symbol: str,
        candle_type: str = "1m",
        count: int = 200,
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """단일 심볼 캔들 조회"""
        cache_key = f"candles_{symbol}_{candle_type}_{count}"

        # 캐시 확인
        cached_data = self.cache_system.get(cache_key, "candles")
        if cached_data:
            return DataResponse(
                success=True,
                data=cached_data,
                error_message=None,
                cache_hit=True,
                response_time_ms=0.1,
                data_source="cache"
            )

        # 데이터 관리자를 통한 조회
        start_time = time.time()

        try:
            candle_data = self.data_manager.get_candle_data(symbol, candle_type, count)

            response_time_ms = (time.time() - start_time) * 1000

            if candle_data:
                # 캔들 데이터를 Dict 형태로 포장
                response_data = {
                    'symbol': symbol,
                    'candle_type': candle_type,
                    'count': count,
                    'candles': candle_data
                }

                # 캐시 저장
                self.cache_system.set(cache_key, response_data, "candles")

                return DataResponse(
                    success=True,
                    data=response_data,
                    error_message=None,
                    cache_hit=False,
                    response_time_ms=response_time_ms,
                    data_source="database"
                )
            else:
                return DataResponse(
                    success=False,
                    data=None,
                    error_message=f"캔들 데이터 없음: {symbol}",
                    cache_hit=False,
                    response_time_ms=response_time_ms,
                    data_source="database"
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"캔들 조회 오류 ({symbol}): {e}")

            return DataResponse(
                success=False,
                data=None,
                error_message=str(e),
                cache_hit=False,
                response_time_ms=response_time_ms,
                data_source="error"
            )

    def _get_single_data(self, symbol: str, data_type: str, priority: Priority) -> DataResponse:
        """단일 심볼 데이터 조회 (공통 로직)"""
        cache_key = f"{data_type}_{symbol}"

        # 🔧 데이터 타입별 캐시 조회 전략
        start_time = time.time()
        cached_data = None

        if data_type in ["ticker", "orderbook", "trades"]:
            # 실시간 데이터는 메모리 캐시만 확인
            cached_data = self._get_from_memory_cache_only(cache_key)
        else:
            # 캔들 데이터는 통합 캐시 확인 (DB + 메모리)
            cached_data = self.cache_system.get(cache_key, data_type)

        if cached_data:
            cache_time_ms = (time.time() - start_time) * 1000
            return DataResponse.create_success(
                data=cached_data,
                cache_hit=True,
                response_time_ms=cache_time_ms,
                data_source="cache"
            )

        try:
            # SmartRouter를 통한 실제 API 호출
            from ..smart_routing.models import RealtimePriority

            data_request = DataRequest(
                symbols=[symbol],
                data_type=DataType.TICKER if data_type == "ticker" else DataType.ORDERBOOK,
                realtime_priority=RealtimePriority.MEDIUM
            )

            # SmartRouter 비동기 호출을 동기적으로 처리
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            router_response = loop.run_until_complete(self.smart_router.get_data(data_request))

            # 🔧 SmartRouter 응답 구조 검증 및 데이터 추출
            if not router_response.get("success"):
                error_msg = router_response.get("error", "SmartRouter 요청 실패")
                raise Exception(error_msg)

            # SmartRouter의 "data" 필드가 완전한 티커 데이터를 포함
            # 심볼별 분리 구조가 아닌 직접 데이터 구조
            router_data = router_response.get("data")
            if not router_data:
                raise Exception("SmartRouter에서 데이터를 반환하지 않음")

            # 단일 심볼 요청의 경우 router_data가 직접 티커 데이터
            # 다중 심볼의 경우 {symbol: data} 구조일 수 있음
            if isinstance(router_data, dict):
                # market 필드가 있으면 직접 티커 데이터
                if 'market' in router_data or 'trade_price' in router_data:
                    api_data = router_data
                # 심볼을 키로 하는 구조인지 확인
                elif symbol in router_data:
                    api_data = router_data[symbol]
                else:
                    # 예상치 못한 구조 - 전체 데이터 사용
                    logger.warning(f"예상치 못한 SmartRouter 데이터 구조: {list(router_data.keys())}")
                    api_data = router_data
            else:
                api_data = router_data

            # 메타데이터에서 데이터 소스 정보 추출
            metadata = router_response.get("metadata", {})
            data_source = metadata.get("channel", "unknown")

            # 🔧 데이터 무결성 검증
            if not self.validate_data_integrity(api_data, data_type):
                logger.error(f"데이터 무결성 검증 실패 - symbol: {symbol}, data_type: {data_type}")
                logger.error(f"유효하지 않은 데이터: {api_data}")
                raise Exception(f"데이터 무결성 검증 실패: {data_type} 데이터가 필수 필드를 포함하지 않음")

            response_time_ms = (time.time() - start_time) * 1000

            # 🔧 데이터 타입별 캐시 전략 적용
            # 티커/호가/체결: 메모리 캐시만 사용 (DB 저장 안함)
            # 캔들: DB + 메모리 캐시 사용 (데이터 원천)
            try:
                if data_type in ["ticker", "orderbook", "trades"]:
                    # 실시간 데이터는 메모리 캐시만 사용
                    self._store_in_memory_cache_only(cache_key, api_data, data_type)
                    logger.debug(f"메모리 캐시 저장 성공: {cache_key} ({data_type})")
                else:
                    # 캔들 데이터는 DB + 메모리 캐시 모두 사용
                    self.cache_system.set(cache_key, api_data, data_type)
                    logger.debug(f"DB+메모리 캐시 저장 성공: {cache_key} ({data_type})")
            except Exception as cache_error:
                logger.warning(f"캐시 저장 실패: {cache_error} - 데이터는 반환됨")

            # 통계 업데이트
            with self._lock:
                self._request_count += 1

            return DataResponse.create_success(
                data=api_data,
                cache_hit=False,
                response_time_ms=response_time_ms,
                data_source=data_source,
                data_type=data_type,
                data_timestamp=datetime.now()
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"데이터 조회 오류 ({symbol}, {data_type}): {e}")

            return DataResponse.create_error(
                error=str(e),
                cache_hit=False,
                response_time_ms=response_time_ms,
                data_source="error"
            )

    # =================================================================
    # 다중 심볼 처리 (배치 최적화)
    # =================================================================

    def get_multiple_tickers(
        self,
        symbols: List[str],
        priority: Priority = Priority.NORMAL
    ) -> BatchRequestResult:
        """다중 심볼 티커 조회"""
        return self._get_multiple_data(symbols, "ticker", priority)

    def get_multiple_orderbooks(
        self,
        symbols: List[str],
        priority: Priority = Priority.NORMAL
    ) -> BatchRequestResult:
        """다중 심볼 호가 조회"""
        return self._get_multiple_data(symbols, "orderbook", priority)

    def _get_multiple_data(
        self,
        symbols: List[str],
        data_type: str,
        priority: Priority
    ) -> BatchRequestResult:
        """다중 심볼 데이터 조회 (지능형 배치 처리)"""
        start_time = time.time()

        # 입력 검증
        if not symbols:
            return BatchRequestResult(
                successful_symbols=[],
                failed_symbols=[],
                total_response_time_ms=0.0,
                symbols_per_second=0.0,
                cache_hit_rate=0.0,
                individual_responses={}
            )

        logger.info(f"다중 {data_type} 조회 시작: {len(symbols)}개 심볼")

        # 배치 크기에 따른 처리 방식 결정
        if len(symbols) < self._batch_threshold:
            # 소규모: 순차 처리
            return self._process_sequential(symbols, data_type, priority, start_time)
        else:
            # 대규모: 병렬 배치 처리
            return self._process_parallel_batches(symbols, data_type, priority, start_time)

    def _process_sequential(
        self,
        symbols: List[str],
        data_type: str,
        priority: Priority,
        start_time: float
    ) -> BatchRequestResult:
        """순차 처리 (소규모 요청용)"""
        successful_symbols = []
        failed_symbols = []
        individual_responses = {}
        cache_hits = 0

        for symbol in symbols:
            response = self._get_single_data(symbol, data_type, priority)

            if response.success:
                successful_symbols.append(symbol)
                individual_responses[symbol] = response.data

                if response.cache_hit:
                    cache_hits += 1
            else:
                failed_symbols.append(symbol)
                individual_responses[symbol] = {'error': response.error_message}

        total_time_ms = (time.time() - start_time) * 1000
        symbols_per_second = len(symbols) / (total_time_ms / 1000) if total_time_ms > 0 else 0
        cache_hit_rate = (cache_hits / len(symbols) * 100) if symbols else 0

        logger.info(f"순차 처리 완료: {len(successful_symbols)}/{len(symbols)} 성공, {symbols_per_second:.1f} symbols/sec")

        return BatchRequestResult(
            successful_symbols=successful_symbols,
            failed_symbols=failed_symbols,
            total_response_time_ms=total_time_ms,
            symbols_per_second=symbols_per_second,
            cache_hit_rate=cache_hit_rate,
            individual_responses=individual_responses
        )

    def _process_parallel_batches(
        self,
        symbols: List[str],
        data_type: str,
        priority: Priority,
        start_time: float
    ) -> BatchRequestResult:
        """병렬 배치 처리 (대규모 요청용)"""
        # 배치로 분할
        batches = [
            symbols[i:i + self._max_batch_size]
            for i in range(0, len(symbols), self._max_batch_size)
        ]

        logger.info(f"병렬 배치 처리: {len(symbols)}개 심볼을 {len(batches)}개 배치로 분할")

        successful_symbols = []
        failed_symbols = []
        individual_responses = {}
        total_cache_hits = 0

        # 배치 병렬 실행
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self._process_batch, batch, data_type, priority): batch
                for batch in batches
            }

            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]

                try:
                    batch_result = future.result()

                    successful_symbols.extend(batch_result.successful_symbols)
                    failed_symbols.extend(batch_result.failed_symbols)
                    individual_responses.update(batch_result.individual_responses)

                    # 캐시 히트 계산
                    total_cache_hits += batch_result.cache_hit_rate * len(batch) / 100

                except Exception as e:
                    logger.error(f"배치 처리 오류: {e}")
                    failed_symbols.extend(batch)

                    for symbol in batch:
                        individual_responses[symbol] = {'error': str(e)}

        total_time_ms = (time.time() - start_time) * 1000
        symbols_per_second = len(symbols) / (total_time_ms / 1000) if total_time_ms > 0 else 0
        cache_hit_rate = (total_cache_hits / len(symbols) * 100) if symbols else 0

        logger.info(f"병렬 배치 처리 완료: {len(successful_symbols)}/{len(symbols)} 성공, {symbols_per_second:.1f} symbols/sec")

        return BatchRequestResult(
            successful_symbols=successful_symbols,
            failed_symbols=failed_symbols,
            total_response_time_ms=total_time_ms,
            symbols_per_second=symbols_per_second,
            cache_hit_rate=cache_hit_rate,
            individual_responses=individual_responses
        )

    def _process_batch(self, batch_symbols: List[str], data_type: str, priority: Priority) -> BatchRequestResult:
        """단일 배치 처리"""
        start_time = time.time()

        successful_symbols = []
        failed_symbols = []
        individual_responses = {}
        cache_hits = 0

        for symbol in batch_symbols:
            response = self._get_single_data(symbol, data_type, priority)

            if response.success:
                successful_symbols.append(symbol)
                individual_responses[symbol] = response.data

                if response.cache_hit:
                    cache_hits += 1
            else:
                failed_symbols.append(symbol)
                individual_responses[symbol] = {'error': response.error_message}

        total_time_ms = (time.time() - start_time) * 1000
        symbols_per_second = len(batch_symbols) / (total_time_ms / 1000) if total_time_ms > 0 else 0
        cache_hit_rate = (cache_hits / len(batch_symbols) * 100) if batch_symbols else 0

        return BatchRequestResult(
            successful_symbols=successful_symbols,
            failed_symbols=failed_symbols,
            total_response_time_ms=total_time_ms,
            symbols_per_second=symbols_per_second,
            cache_hit_rate=cache_hit_rate,
            individual_responses=individual_responses
        )

    # =================================================================
    # 실시간 데이터 관리
    # =================================================================

    def subscribe_realtime_data(
        self,
        symbols: List[str],
        data_types: Optional[List[str]] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """실시간 데이터 구독"""
        subscription_id = f"sub_{int(time.time() * 1000)}"
        data_types = data_types or ["ticker"]

        success = self.realtime_manager.subscribe_to_symbols(
            subscription_id, symbols, data_types, callback
        )

        if success:
            logger.info(f"실시간 구독 생성: {subscription_id}, {len(symbols)}개 심볼")
            return subscription_id
        else:
            logger.error(f"실시간 구독 실패: {symbols}")
            return ""

    def unsubscribe_realtime_data(self, subscription_id: str) -> bool:
        """실시간 데이터 구독 해제"""
        return self.realtime_manager.unsubscribe_symbols(subscription_id)

    # =================================================================
    # 통계 및 모니터링
    # =================================================================

    def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 지표 조회"""
        with self._lock:
            elapsed_time = time.time() - self._start_time
            throughput = self._request_count / elapsed_time if elapsed_time > 0 else 0

            return PerformanceMetrics(
                total_requests=self._request_count,
                successful_requests=self._request_count,  # 실제로는 더 정확한 계산 필요
                failed_requests=0,
                avg_response_time_ms=0.0,  # 실제로는 평균 계산 필요
                min_response_time_ms=0.0,
                max_response_time_ms=0.0,
                symbols_per_second=round(throughput, 2)
            )

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """종합 상태 정보"""
        # 각 레이어별 통계 수집
        cache_stats = self.cache_system.get_comprehensive_stats()
        realtime_stats = self.realtime_manager.get_comprehensive_stats()
        data_manager_stats = self.data_manager.get_comprehensive_status()
        performance_metrics = self.get_performance_metrics()

        return {
            'system_info': {
                'version': '4.0',
                'uptime_seconds': time.time() - self._start_time,
                'max_workers': self.max_workers,
                'batch_threshold': self._batch_threshold,
                'max_batch_size': self._max_batch_size
            },
            'performance': {
                'total_requests': performance_metrics.total_requests,
                'symbols_per_second': performance_metrics.symbols_per_second,
                'target_symbols_per_second': 500
            },
            'layer_1_api': {
                'request_count': self._request_count,
                'thread_pool_workers': self.max_workers
            },
            'layer_2_cache': cache_stats,
            'layer_2_realtime': realtime_stats,
            'layer_3_data': data_manager_stats,
            'timestamp': datetime.now().isoformat()
        }

    def __del__(self):
        """소멸자 - 리소스 정리"""
        try:
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=True)
            logger.info("SmartDataProvider V4.0 정리 완료")
        except Exception:
            pass
