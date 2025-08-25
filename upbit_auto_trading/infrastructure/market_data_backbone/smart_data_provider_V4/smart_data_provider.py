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
from .response_models import DataResponse, Priority
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
                return DataResponse.create_success(
                    data=cached_data,
                    source="fast_cache",
                    cache_hit=True,
                    response_time_ms=(time.time() - start_time) * 1000
                )

            # 2. SmartRouter 직접 호출 (배치 처리)
            result = await self.batch_processor.process_symbols(
                symbols=symbols,
                processor_func=self._call_smart_router_ticker,
                priority=priority
            )

            if result.get('success', False):
                self._api_calls += 1

                # 캐시 저장
                data = result.get('data', {})
                self.cache.set(cache_key, data)

                logger.debug(f"티커 성공: {symbols}")
                return DataResponse.create_success(
                    data=data,
                    source="smart_router",
                    cache_hit=False,
                    response_time_ms=(time.time() - start_time) * 1000
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

            result = await self.smart_router.get_tickers(symbols=symbols)
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
                result = await self.smart_router.get_candles(
                    symbols=[symbols],
                    timeframe=kwargs.get('timeframe'),
                    count=kwargs.get('count'),
                    end_time=kwargs.get('end_time')
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
