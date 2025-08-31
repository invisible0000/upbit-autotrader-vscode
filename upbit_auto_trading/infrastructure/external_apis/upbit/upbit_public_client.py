"""
업비트 공개 API 클라이언트 - GCRA Rate Limiter 기반

GCRA 알고리즘 기반 Rate Limiter 사용
"""
import asyncio
import aiohttp
import time
from typing import List, Dict, Any, Optional, Union

from .upbit_rate_limiter import get_global_rate_limiter, UpbitGCRARateLimiter


class UpbitPublicClient:
    """
    업비트 전용 공개 API 클라이언트 - GCRA 기반

    특징:
    - GCRA Rate Limiter 사용
    - 전역 공유 Rate Limiter 지원
    - 버스트 처리 지원
    """

    BASE_URL = "https://api.upbit.com/v1"

    def __init__(self, rate_limiter: Optional[UpbitGCRARateLimiter] = None):
        """
        업비트 공개 API 클라이언트 초기화

        Args:
            rate_limiter: GCRA Rate Limiter (기본값: 전역 공유)
        """
        self._rate_limiter = rate_limiter
        self._session: Optional[aiohttp.ClientSession] = None

        # 429 재시도 통계
        self.retry_stats = {
            'total_429_retries': 0,
            'last_request_429_retries': 0
        }

        # 📊 순수 HTTP 응답 시간 추적 (Rate Limiter 대기 시간 제외)
        self._last_http_response_time: float = 0.0

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self) -> None:
        """HTTP 세션 확보"""
        if not self._session or self._session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'Accept': 'application/json'}
            )

    async def _ensure_rate_limiter(self) -> UpbitGCRARateLimiter:
        """Rate Limiter 확보 (전역 공유 우선)"""
        if self._rate_limiter is None:
            self._rate_limiter = await get_global_rate_limiter()
        return self._rate_limiter

    async def close(self) -> None:
        """리소스 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def get_last_http_response_time(self) -> float:
        """
        마지막 HTTP 요청의 순수 서버 응답 시간 조회 (Rate Limiter 대기 시간 제외)

        Returns:
            float: 응답 시간 (밀리초)
        """
        return self._last_http_response_time

    async def _make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        업비트 API 요청 실행

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드
            params: 쿼리 파라미터

        Returns:
            API 응답 데이터
        """
        await self._ensure_session()

        url = f"{self.BASE_URL}{endpoint}"

        if not self._session:
            raise Exception("세션이 초기화되지 않았습니다")

        # Rate Limiter와 HTTP 요청을 원자적으로 처리
        max_retries = 3

        # 요청별 429 재시도 카운터 초기화
        self.retry_stats['last_request_429_retries'] = 0

        for attempt in range(max_retries):
            # Rate Limit 적용
            rate_limiter = await self._ensure_rate_limiter()
            await rate_limiter.acquire(endpoint, method)

            try:
                # 🎯 순수 HTTP 요청 시간 측정 시작
                http_start_time = time.perf_counter()

                async with self._session.request(method, url, params=params, **kwargs) as response:
                    http_end_time = time.perf_counter()

                    # 순수 HTTP 응답 시간 저장 (Rate Limiter 대기 시간 제외)
                    self._last_http_response_time = (http_end_time - http_start_time) * 1000  # ms 단위

                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 429:
                        # 429 응답 처리
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            rate_limiter.handle_429_response(float(retry_after))

                        # 429 재시도 카운터 업데이트
                        self.retry_stats['last_request_429_retries'] += 1
                        self.retry_stats['total_429_retries'] += 1

                        # 429 오류 시 지수 백오프로 재시도
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 0.5  # 0.5, 1.0, 2.0초
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception(f"429 오류로 {max_retries}회 재시도 후에도 실패")
                    else:
                        error_text = await response.text()
                        raise Exception(f"API 오류 (상태: {response.status}): {error_text}")

            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.3  # 타임아웃 재시도
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"타임아웃으로 {max_retries}회 재시도 후에도 실패")

            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
                    continue
                else:
                    raise e

        raise Exception("모든 재시도 실패")

    # ================================================================
    # 업비트 API 메서드들
    # ================================================================

    async def get_ticker(self, markets: Union[str, List[str]]) -> Any:
        """현재가 정보 조회"""
        if isinstance(markets, str):
            markets = [markets]

        params = {'markets': ','.join(markets)}
        return await self._make_request('/ticker', params=params)

    async def get_tickers(self, quote_currency: Optional[str] = None) -> Any:
        """전체 마켓 현재가 정보 조회"""
        params = {}
        if quote_currency:
            params['quote_currency'] = quote_currency
        return await self._make_request('/ticker', params=params)

    async def get_orderbook(self, markets: Union[str, List[str]]) -> Any:
        """호가 정보 조회"""
        if isinstance(markets, str):
            markets = [markets]

        params = {'markets': ','.join(markets)}
        return await self._make_request('/orderbook', params=params)

    async def get_trades(self, market: str, count: int = 100) -> Any:
        """최근 체결 내역 조회"""
        params = {'market': market}
        if count:
            params['count'] = str(count)
        return await self._make_request('/trades', params=params)

    async def get_candles_minutes(self, unit: int, market: str, count: int = 200) -> Any:
        """분봉 정보 조회"""
        endpoint = f'/candles/minutes/{unit}'
        params = {'market': market, 'count': str(count)}
        return await self._make_request(endpoint, params=params)

    async def get_candles_days(self, market: str, count: int = 200) -> Any:
        """일봉 정보 조회"""
        params = {'market': market, 'count': str(count)}
        return await self._make_request('/candles/days', params=params)

    async def get_candles_weeks(self, market: str, count: int = 200) -> Any:
        """주봉 정보 조회"""
        params = {'market': market, 'count': str(count)}
        return await self._make_request('/candles/weeks', params=params)

    async def get_candles_months(self, market: str, count: int = 200) -> Any:
        """월봉 정보 조회"""
        params = {'market': market, 'count': str(count)}
        return await self._make_request('/candles/months', params=params)

    async def get_markets(self) -> Any:
        """마켓 코드 목록 조회"""
        return await self._make_request('/market/all')


# ================================================================
# 편의 팩토리 함수
# ================================================================

async def create_upbit_public_client() -> UpbitPublicClient:
    """
    업비트 공개 API 클라이언트 생성 (편의 함수)

    자동으로 글로벌 공유 Rate Limiter 적용
    서브시스템에서는 반드시 이 함수를 사용해야 함
    """
    # 🌍 글로벌 공유 Rate Limiter 사용 (IP 기반 10 RPS 제한 준수)
    rate_limiter = await get_global_rate_limiter()
    return UpbitPublicClient(rate_limiter=rate_limiter)
