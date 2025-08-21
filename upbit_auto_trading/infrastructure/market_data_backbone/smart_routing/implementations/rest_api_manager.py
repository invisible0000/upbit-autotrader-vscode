"""
REST API 호출 관리 서비스

업비트 REST API 호출과 재시도 로직을 관리하는 서비스입니다.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from decimal import Decimal

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_client import UpbitClient

logger = create_component_logger("RestApiManager")


class RestApiManager:
    """REST API 호출 관리 서비스

    WARM_CACHE_REST와 COLD_REST Tier를 위한 REST API 호출을 관리합니다.
    """

    def __init__(self, upbit_client: UpbitClient):
        """REST API 관리자 초기화

        Args:
            upbit_client: 업비트 클라이언트 인스턴스
        """
        logger.info("RestApiManager 초기화 시작")

        self.upbit_client = upbit_client

        # 재시도 설정
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,  # 첫 번째 재시도 지연 (초)
            'max_delay': 10.0,  # 최대 재시도 지연 (초)
            'backoff_multiplier': 2.0,  # 지수 백오프 배수
            'jitter_range': 0.1  # 지터 범위 (0.1 = ±10%)
        }

        # Rate Limiting (업비트 REST API 제한)
        self.rate_limit_config = {
            'public_per_second': 10,  # 공개 API: 초당 10회
            'private_per_second': 8,  # 개인 API: 초당 8회
            'public_per_minute': 600,  # 공개 API: 분당 600회
            'private_per_minute': 200  # 개인 API: 분당 200회
        }

        # Rate Limit 추적
        self.request_timestamps = {
            'public': [],
            'private': []
        }
        self.last_request_time = {
            'public': 0.0,
            'private': 0.0
        }

        # 성능 메트릭
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0,
            'avg_response_time_ms': 0.0,
            'avg_retry_delay_ms': 0.0,
            'rate_limit_hits': 0
        }

        logger.info("RestApiManager 초기화 완료")

    async def get_ticker_data_warm(
        self,
        symbols: List[str],
        enable_retry: bool = True
    ) -> Dict[str, Any]:
        """Warm 캐시용 티커 데이터 요청 (WARM_CACHE_REST Tier)

        Args:
            symbols: 요청할 심볼 리스트
            enable_retry: 재시도 활성화 여부

        Returns:
            티커 데이터 응답
        """
        logger.info(f"Warm 티커 요청: {len(symbols)}개 심볼")

        return await self._request_ticker_data(
            symbols=symbols,
            tier_type='warm',
            enable_retry=enable_retry,
            timeout=5.0
        )

    async def get_ticker_data_cold(
        self,
        symbols: List[str],
        enable_retry: bool = True
    ) -> Dict[str, Any]:
        """Cold 저장소용 티커 데이터 요청 (COLD_REST Tier)

        Args:
            symbols: 요청할 심볼 리스트
            enable_retry: 재시도 활성화 여부

        Returns:
            티커 데이터 응답
        """
        logger.info(f"Cold 티커 요청: {len(symbols)}개 심볼")

        return await self._request_ticker_data(
            symbols=symbols,
            tier_type='cold',
            enable_retry=enable_retry,
            timeout=10.0
        )

    async def _request_ticker_data(
        self,
        symbols: List[str],
        tier_type: str,
        enable_retry: bool,
        timeout: float
    ) -> Dict[str, Any]:
        """티커 데이터 요청 (공통 로직)

        Args:
            symbols: 요청할 심볼 리스트
            tier_type: Tier 유형 ('warm' 또는 'cold')
            enable_retry: 재시도 활성화 여부
            timeout: 요청 타임아웃 (초)

        Returns:
            티커 데이터 응답
        """
        start_time = time.time()

        try:
            # Rate Limit 체크
            await self._wait_for_rate_limit('public', tier_type)

            # 실제 API 호출
            if enable_retry:
                response = await self._execute_with_retry(
                    self._call_ticker_api,
                    symbols,
                    timeout
                )
            else:
                response = await self._call_ticker_api(symbols, timeout)

            # 응답 처리
            processed_response = await self._process_ticker_response(
                response, symbols, tier_type, start_time
            )

            # 메트릭 업데이트
            self.metrics['successful_requests'] += 1
            response_time = (time.time() - start_time) * 1000
            self._update_avg_response_time(response_time)

            return processed_response

        except Exception as e:
            logger.error(f"티커 데이터 요청 실패 ({tier_type}): {e}")
            self.metrics['failed_requests'] += 1

            # 에러 응답 반환
            return {
                'success': False,
                'error': str(e),
                'tier_type': tier_type,
                'symbols_requested': symbols,
                'response_time_ms': (time.time() - start_time) * 1000
            }

    async def _call_ticker_api(self, symbols: List[str], timeout: float) -> List[Dict]:
        """실제 업비트 티커 API 호출

        Args:
            symbols: 요청할 심볼 리스트
            timeout: 요청 타임아웃 (초)

        Returns:
            API 응답 데이터
        """
        logger.debug(f"업비트 티커 API 호출: {len(symbols)}개 심볼")

        try:
            # 업비트 클라이언트를 통한 API 호출
            response = await asyncio.wait_for(
                self.upbit_client.get_ticker(symbols),
                timeout=timeout
            )

            self.metrics['total_requests'] += 1
            return response

        except asyncio.TimeoutError:
            logger.warning(f"API 호출 타임아웃: {timeout}초")
            raise Exception(f"API 호출 타임아웃 ({timeout}초)")

        except Exception as e:
            logger.error(f"API 호출 오류: {e}")
            raise

    async def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        """재시도 로직이 포함된 함수 실행

        Args:
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자

        Returns:
            함수 실행 결과
        """
        last_exception = None

        for attempt in range(self.retry_config['max_retries'] + 1):
            try:
                if attempt > 0:
                    # 재시도 지연 계산
                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"재시도 {attempt}/{self.retry_config['max_retries']}: "
                               f"{delay:.2f}초 대기")

                    await asyncio.sleep(delay)
                    self.metrics['retry_attempts'] += 1
                    self._update_avg_retry_delay(delay * 1000)  # ms로 변환

                # 함수 실행
                result = await func(*args, **kwargs)

                if attempt > 0:
                    logger.info(f"✅ 재시도 성공: {attempt}번째 시도에서 성공")

                return result

            except Exception as e:
                last_exception = e

                # 마지막 시도인 경우 에러 발생
                if attempt >= self.retry_config['max_retries']:
                    logger.error(f"❌ 모든 재시도 실패: {e}")
                    break

                # 재시도 가능한 에러인지 확인
                if not self._is_retryable_error(e):
                    logger.warning(f"재시도 불가능한 오류: {e}")
                    break

                logger.warning(f"재시도 가능한 오류 발생: {e}")

        # 재시도 실패
        if last_exception:
            raise last_exception
        else:
            raise Exception("알 수 없는 오류로 재시도 실패")

    def _calculate_retry_delay(self, attempt: int) -> float:
        """재시도 지연 시간 계산 (지수 백오프 + 지터)

        Args:
            attempt: 시도 횟수 (1부터 시작)

        Returns:
            지연 시간 (초)
        """
        # 지수 백오프
        delay = self.retry_config['base_delay'] * (
            self.retry_config['backoff_multiplier'] ** (attempt - 1)
        )

        # 최대 지연시간 제한
        delay = min(delay, self.retry_config['max_delay'])

        # 지터 추가 (랜덤성)
        import random
        jitter = delay * self.retry_config['jitter_range'] * (2 * random.random() - 1)
        delay += jitter

        return max(delay, 0.1)  # 최소 0.1초

    def _is_retryable_error(self, error: Exception) -> bool:
        """재시도 가능한 에러인지 확인

        Args:
            error: 발생한 에러

        Returns:
            재시도 가능 여부
        """
        error_message = str(error).lower()

        # 재시도 가능한 에러 패턴
        retryable_patterns = [
            'timeout',
            'connection',
            'network',
            'temporarily unavailable',
            'rate limit',
            'too many requests',
            'server error',
            '5xx'
        ]

        # 재시도 불가능한 에러 패턴
        non_retryable_patterns = [
            'authentication',
            'authorization',
            'invalid',
            'bad request',
            '4xx'
        ]

        # 재시도 불가능한 패턴 체크
        for pattern in non_retryable_patterns:
            if pattern in error_message:
                return False

        # 재시도 가능한 패턴 체크
        for pattern in retryable_patterns:
            if pattern in error_message:
                return True

        # 기본적으로 재시도 허용 (보수적 접근)
        return True

    async def _wait_for_rate_limit(self, api_type: str, tier_type: str) -> None:
        """Rate Limit 대기

        Args:
            api_type: API 타입 ('public' 또는 'private')
            tier_type: Tier 타입 ('warm' 또는 'cold')
        """
        current_time = time.time()

        # Tier별 Rate Limit 조정
        if tier_type == 'warm':
            # Warm Tier는 더 빠른 응답을 위해 더 여유롭게
            rate_factor = 0.8  # 80% 사용률로 제한
        else:  # cold
            # Cold Tier는 안정성 우선
            rate_factor = 0.6  # 60% 사용률로 제한

        # 초당 제한
        per_second_limit = self.rate_limit_config[f'{api_type}_per_second']
        safe_interval = (1.0 / per_second_limit) * rate_factor

        # 마지막 요청 이후 경과 시간
        time_elapsed = current_time - self.last_request_time[api_type]

        if time_elapsed < safe_interval:
            wait_time = safe_interval - time_elapsed
            logger.debug(f"Rate Limit 대기 ({api_type}): {wait_time:.3f}초")
            await asyncio.sleep(wait_time)

        self.last_request_time[api_type] = time.time()
        self.request_timestamps[api_type].append(self.last_request_time[api_type])

        # 1분 이상 된 타임스탬프 제거
        cutoff_time = current_time - 60.0
        self.request_timestamps[api_type] = [
            t for t in self.request_timestamps[api_type] if t > cutoff_time
        ]

        # 분당 제한 체크
        requests_per_minute = len(self.request_timestamps[api_type])
        minute_limit = self.rate_limit_config[f'{api_type}_per_minute']

        if requests_per_minute >= minute_limit * rate_factor:
            self.metrics['rate_limit_hits'] += 1
            logger.warning(f"분당 Rate Limit 임계점 도달 ({api_type}): "
                          f"{requests_per_minute}/{minute_limit}")

    async def _process_ticker_response(
        self,
        response: List[Dict],
        symbols: List[str],
        tier_type: str,
        start_time: float
    ) -> Dict[str, Any]:
        """티커 응답 처리

        Args:
            response: API 응답 데이터
            symbols: 요청한 심볼 리스트
            tier_type: Tier 유형
            start_time: 요청 시작 시간

        Returns:
            처리된 응답 데이터
        """
        response_time = (time.time() - start_time) * 1000

        # 응답 데이터 정리
        ticker_data = {}
        for item in response:
            if 'market' in item:
                symbol = item['market']
                ticker_data[symbol] = {
                    'symbol': symbol,
                    'data': item,
                    'collected_at': time.time(),
                    'source': f'rest_{tier_type}'
                }

        # 성공률 계산
        collected_symbols = list(ticker_data.keys())
        success_rate = len(collected_symbols) / len(symbols) if symbols else 0.0
        missing_symbols = [s for s in symbols if s not in collected_symbols]

        logger.info(f"REST API 응답 처리 완료 ({tier_type}): "
                   f"{len(collected_symbols)}/{len(symbols)} "
                   f"({success_rate:.1%}), {response_time:.1f}ms")

        if missing_symbols:
            logger.warning(f"누락된 심볼: {missing_symbols}")

        return {
            'success': True,
            'collected_data': ticker_data,
            'success_rate': success_rate,
            'response_time_ms': response_time,
            'symbols_collected': len(collected_symbols),
            'symbols_missing': missing_symbols,
            'tier_type': tier_type,
            'timestamp': time.time()
        }

    def _update_avg_response_time(self, response_time_ms: float) -> None:
        """평균 응답 시간 업데이트"""
        current_avg = self.metrics['avg_response_time_ms']
        total_requests = self.metrics['total_requests']

        # 이동 평균 계산
        self.metrics['avg_response_time_ms'] = (
            (current_avg * (total_requests - 1) + response_time_ms) / total_requests
        )

    def _update_avg_retry_delay(self, delay_ms: float) -> None:
        """평균 재시도 지연 시간 업데이트"""
        current_avg = self.metrics['avg_retry_delay_ms']
        retry_attempts = self.metrics['retry_attempts']

        if retry_attempts > 0:
            # 이동 평균 계산
            self.metrics['avg_retry_delay_ms'] = (
                (current_avg * (retry_attempts - 1) + delay_ms) / retry_attempts
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회

        Returns:
            상세한 성능 메트릭
        """
        current_time = time.time()

        # 최근 1분간 요청 수
        recent_public = len([t for t in self.request_timestamps['public']
                           if current_time - t < 60.0])
        recent_private = len([t for t in self.request_timestamps['private']
                            if current_time - t < 60.0])

        # 성공률 계산
        total_requests = self.metrics['total_requests']
        success_rate = (self.metrics['successful_requests'] / total_requests) if total_requests > 0 else 0.0

        return {
            'requests': {
                'total': self.metrics['total_requests'],
                'successful': self.metrics['successful_requests'],
                'failed': self.metrics['failed_requests'],
                'success_rate': success_rate
            },
            'retry': {
                'total_attempts': self.metrics['retry_attempts'],
                'avg_delay_ms': self.metrics['avg_retry_delay_ms']
            },
            'performance': {
                'avg_response_time_ms': self.metrics['avg_response_time_ms'],
                'rate_limit_hits': self.metrics['rate_limit_hits']
            },
            'rate_limit_status': {
                'public_requests_last_minute': recent_public,
                'private_requests_last_minute': recent_private,
                'public_limit_per_minute': self.rate_limit_config['public_per_minute'],
                'private_limit_per_minute': self.rate_limit_config['private_per_minute'],
                'public_usage_percentage': (recent_public / self.rate_limit_config['public_per_minute']) * 100,
                'private_usage_percentage': (recent_private / self.rate_limit_config['private_per_minute']) * 100
            }
        }

    def reset_metrics(self) -> None:
        """메트릭 초기화"""
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0,
            'avg_response_time_ms': 0.0,
            'avg_retry_delay_ms': 0.0,
            'rate_limit_hits': 0
        }
        self.request_timestamps = {'public': [], 'private': []}
        self.last_request_time = {'public': 0.0, 'private': 0.0}
        logger.info("REST API 메트릭 초기화 완료")
