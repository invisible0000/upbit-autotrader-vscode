"""
SmartDataProvider V4.0 - 통합 지능형 API

기존 SmartDataProvider의 18.5배 성능 문제를 해결하는 완전 새로운 구현
- 목표: 500+ 심볼/초 처리 성능
- 원칙: 최소 레이어, 직접 연결, 고속 캐시
- 지능형 API: 단일/다중 심볼 자동 처리
"""

import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .response_models import DataResponse, Priority, DataSourceInfo
from .fast_cache import FastCache
from .batch_processor import BatchProcessor

logger = create_component_logger("SmartDataProvider")


class SmartDataProvider:
    """
    SmartDataProvider V4.0 - 통합 지능형 API

    주요 개선사항:
    1. 지능형 API: get_ticker(symbol/symbols) 자동 처리
    2. 직접 SmartRouter 연결 (어댑터 계층 제거)
    3. 고속 캐시: 200ms TTL 고정
    4. 배치 처리: 다중 심볼 동시 처리
    """

    def __init__(self, smart_router=None):
        """
        SmartDataProvider V4.0 초기화

        Args:
            smart_router: SmartRouter 인스턴스 (직접 연결)
        """
        self.smart_router = smart_router
        self.cache = FastCache(default_ttl=0.2)  # 200ms TTL
        self.batch_processor = BatchProcessor()

        # 성능 카운터
        self._request_count = 0
        self._cache_hits = 0
        self._api_calls = 0

        logger.info("SmartDataProvider V4.0 초기화 완료")

    # =====================================
    # 🎯 핵심 지능형 API 메서드
    # =====================================

    async def get_ticker(self, symbols: Union[str, List[str]],
                        priority: int = Priority.NORMAL) -> DataResponse:
        """
        지능형 티커 조회 - 단일/다중 자동 처리

        Args:
            symbols: 단일 심볼(str) 또는 다중 심볼(List[str])
            priority: 요청 우선순위

        Returns:
            DataResponse: 티커 데이터

        Examples:
            # 단일 심볼
            ticker = await provider.get_ticker("KRW-BTC")

            # 다중 심볼
            tickers = await provider.get_ticker(["KRW-BTC", "KRW-ETH"])
        """
        start_time = time.time()
        self._request_count += 1

        logger.debug(f"티커 요청: {symbols}, priority={priority}")

        # 입력 검증
        if not self.batch_processor.validate_symbols(symbols):
            return DataResponse.create_error(
                error="유효하지 않은 심볼",
                response_time_ms=(time.time() - start_time) * 1000
            )

        try:
            # 캐시 키 생성
            cache_key = self._generate_cache_key("ticker", symbols)

            # 1. 캐시 조회
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self._cache_hits += 1
                logger.debug(f"티커 캐시 히트: {symbols}")

                # 🚀 캐시 데이터 소스 정보 생성
                cache_age_ms = (time.time() - start_time) * 1000
                cache_source = DataSourceInfo(
                    channel="cache",
                    cache_info={
                        "ttl_ms": 200,  # FastCache TTL
                        "age_ms": cache_age_ms,
                        "hit_rate": self._cache_hits / max(1, self._cache_hits + self._api_calls)
                    },
                    reliability=0.95,  # 캐시 신뢰도
                    latency_ms=cache_age_ms
                )

                return DataResponse.create_success(
                    data=cached_data,
                    data_source=cache_source,
                    source="fast_cache",  # 기존 호환성
                    cache_hit=True,
                    response_time_ms=cache_age_ms
                )

            # 2. SmartRouter 직접 호출 (배치 처리)
            result = await self.batch_processor.process_symbols(
                symbols=symbols,
                processor_func=self._call_smart_router_ticker,
                priority=priority
            )

            if result.get('success', False):
                self._api_calls += 1

                # 디버깅: SmartRouter 응답 구조 확인
                logger.debug("SmartRouter 응답:")
                logger.debug(f"  - result 키들: {list(result.keys())}")
                logger.debug(f"  - result 내용: {result}")

                # 캐시 저장
                data = result.get('data', {})
                logger.debug(f"캐시에 저장할 데이터: {data}")
                self.cache.set(cache_key, data)

                # 🚀 SmartRouter 응답에서 데이터 소스 정보 추출
                response_time_ms = (time.time() - start_time) * 1000
                router_metadata = result.get('metadata', {})

                # SmartRouter의 채널 정보를 DataSourceInfo로 변환
                router_source = self._extract_source_info_from_router(router_metadata, response_time_ms)

                logger.debug(f"티커 성공: {symbols}")
                return DataResponse.create_success(
                    data=data,
                    data_source=router_source,
                    source="smart_router",  # 기존 호환성
                    cache_hit=False,
                    response_time_ms=response_time_ms
                )
            else:
                return DataResponse.create_error(
                    error=result.get('error', 'SmartRouter 호출 실패'),
                    response_time_ms=(time.time() - start_time) * 1000
                )

        except Exception as e:
            logger.error(f"티커 조회 실패: {symbols}, {e}")
            return DataResponse.create_error(
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000
            )

    async def get_candle(self, symbols: Union[str, List[str]],
                        timeframe: str,
                        count: Optional[int] = None,
                        start_time: Optional[str] = None,
                        end_time: Optional[str] = None,
                        priority: int = Priority.NORMAL) -> DataResponse:
        """
        지능형 캔들 조회 - 단일/다중 자동 처리

        Args:
            symbols: 단일 심볼(str) 또는 다중 심볼(List[str])
            timeframe: 타임프레임 (1m, 5m, 15m, 1h, 1d 등)
            count: 캔들 개수
            start_time: 시작 시간
            end_time: 종료 시간
            priority: 요청 우선순위

        Returns:
            DataResponse: 캔들 데이터
        """
        start_time_ms = time.time()
        self._request_count += 1

        logger.debug(f"캔들 요청: {symbols} {timeframe}, count={count}")

        # 입력 검증
        if not self.batch_processor.validate_symbols(symbols):
            return DataResponse.create_error(
                error="유효하지 않은 심볼",
                response_time_ms=(time.time() - start_time_ms) * 1000
            )

        try:
            # 배치 처리로 SmartRouter 직접 호출
            result = await self.batch_processor.process_symbols(
                symbols=symbols,
                processor_func=self._call_smart_router_candles,
                timeframe=timeframe,
                count=count,
                start_time=start_time,
                end_time=end_time,
                priority=priority
            )

            if result.get('success', False):
                self._api_calls += 1
                data = result.get('data', {})

                logger.debug(f"캔들 성공: {symbols} {timeframe}")
                return DataResponse.create_success(
                    data=data,
                    source="smart_router",
                    response_time_ms=(time.time() - start_time_ms) * 1000
                )
            else:
                return DataResponse.create_error(
                    error=result.get('error', 'SmartRouter 호출 실패'),
                    response_time_ms=(time.time() - start_time_ms) * 1000
                )

        except Exception as e:
            logger.error(f"캔들 조회 실패: {symbols} {timeframe}, {e}")
            return DataResponse.create_error(
                error=str(e),
                response_time_ms=(time.time() - start_time_ms) * 1000
            )

    # =====================================
    # 🔧 내부 헬퍼 메서드
    # =====================================

    async def _call_smart_router_ticker(self, symbols: Union[str, List[str]], **kwargs) -> Dict[str, Any]:
        """SmartRouter 티커 호출"""
        if not self.smart_router:
            return {'success': False, 'error': 'SmartRouter 없음'}

        try:
            # SmartRouter는 단일/다중 모두 처리 가능
            if isinstance(symbols, str):
                symbols = [symbols]  # 리스트로 통일

            # SmartRouter V2.0 API 호출 (get_ticker 사용)
            result = await self.smart_router.get_ticker(symbols=symbols)
            return result

        except Exception as e:
            logger.error(f"SmartRouter 티커 호출 실패: {e}")
            return {'success': False, 'error': str(e)}

    async def _call_smart_router_candles(self, symbols: Union[str, List[str]], **kwargs) -> Dict[str, Any]:
        """SmartRouter 캔들 호출"""
        if not self.smart_router:
            return {'success': False, 'error': 'SmartRouter 없음'}

        try:
            # 단일 심볼 처리 (SmartRouter는 캔들에서 단일 심볼만 지원)
            if isinstance(symbols, str):
                # SmartRouter V2.0 API 호출 (interval 파라미터 사용)
                result = await self.smart_router.get_candles(
                    symbols=[symbols],
                    interval=kwargs.get('timeframe', '1m'),
                    count=kwargs.get('count', 1),
                    to=kwargs.get('to')
                )
                return result
            else:
                # 다중 심볼은 순차 처리 (추후 최적화 가능)
                # TODO: SmartRouter 배치 캔들 지원시 개선
                raise NotImplementedError("다중 심볼 캔들 조회는 추후 구현")

        except Exception as e:
            logger.error(f"SmartRouter 캔들 호출 실패: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_cache_key(self, data_type: str, symbols: Union[str, List[str]]) -> str:
        """캐시 키 생성"""
        if isinstance(symbols, str):
            return f"{data_type}:{symbols}"
        else:
            symbols_str = ",".join(sorted(symbols))
            return f"{data_type}:{symbols_str}"

    # =====================================
    # 📊 통계 및 관리
    # =====================================

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        cache_stats = self.cache.get_stats()

        return {
            'requests': self._request_count,
            'cache_hits': self._cache_hits,
            'api_calls': self._api_calls,
            'cache_stats': cache_stats,
            'hit_rate': round(self._cache_hits / self._request_count * 100, 2) if self._request_count > 0 else 0
        }

    def cleanup_cache(self) -> None:
        """캐시 정리"""
        cleaned = self.cache.cleanup_expired()
        logger.info(f"캐시 정리 완료: {cleaned}개 삭제")

    # =====================================
    # 🔄 호환성 API (기존 코드 지원)
    # =====================================

    async def get_tickers(self, symbols: List[str], priority: int = Priority.NORMAL) -> DataResponse:
        """기존 API 호환성 - get_ticker로 리다이렉트"""
        logger.debug("기존 get_tickers() 호출 -> get_ticker()로 리다이렉트")
        return await self.get_ticker(symbols, priority)

    async def get_candles(self, symbol: str, timeframe: str, **kwargs) -> DataResponse:
        """기존 API 호환성 - get_candle로 리다이렉트"""
        logger.debug("기존 get_candles() 호출 -> get_candle()로 리다이렉트")
        return await self.get_candle(symbol, timeframe, **kwargs)

    # 🚀 데이터 소스 정보 헬퍼 메서드들 - 추측 제거 버전
    def _extract_source_info_from_router(self, router_metadata: Dict[str, Any], response_time_ms: float) -> DataSourceInfo:
        """SmartRouter 메타데이터에서 정확한 DataSourceInfo 추출 - 추측 없음"""

        # 🚀 2단계: SmartRouter의 명확한 소스 정보 사용
        reliability_score = router_metadata.get('reliability_score', 0.8)
        channel = router_metadata.get('channel', 'rest_api')

        # WebSocket 데이터 처리 - 실제 스트림 타입 확인
        if channel == "websocket":
            # 실제 스트림 타입을 SmartRouter에서 추출한 정보로 확인
            stream_info = router_metadata.get('stream_info', {})
            actual_stream_type = stream_info.get('stream_type', 'realtime')

            return DataSourceInfo(
                channel="websocket",
                stream_type=actual_stream_type,  # 실제 스트림 타입 사용
                reliability=reliability_score,
                latency_ms=response_time_ms,
                cache_info={
                    "stream_info": stream_info,
                    "data_freshness": router_metadata.get('data_freshness', {}),
                    "is_live_stream": actual_stream_type == "realtime",
                    "raw_stream_type": stream_info.get('raw_stream_type', 'unknown')
                }
            )
        else:
            # REST API 데이터
            freshness_info = router_metadata.get('data_freshness', {})

            return DataSourceInfo(
                channel="rest_api",
                reliability=reliability_score,
                latency_ms=response_time_ms,
                cache_info={
                    "estimated_delay_ms": freshness_info.get('estimated_delay_ms', 100),
                    "server_timestamp": freshness_info.get('timestamp')
                }
            )

    def _detect_stream_type(self, router_metadata: Dict[str, Any]) -> Optional[str]:
        """WebSocket 스트림 타입 감지 - 더 이상 추측하지 않음"""
        # SmartRouter에서 명확한 source_type 제공하므로 추측 불필요
        source_type = router_metadata.get('source_type', '')

        if source_type == "websocket_realtime":
            return "realtime"
        elif source_type == "websocket_snapshot":
            return "snapshot"
        else:
            return None  # WebSocket이 아니거나 불명확한 경우

    def cleanup(self) -> None:
        """리소스 정리"""
        logger.info("SmartDataProvider V4.0 정리 완료")
