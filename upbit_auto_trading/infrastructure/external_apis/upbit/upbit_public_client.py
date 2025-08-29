"""
업비트 공개 API 클라이언트 - 업비트 전용 단순화 버전

업비트 전용으로 최적화된 구현
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional, Union

from .upbit_rate_limiter import UpbitRateLimiter, create_upbit_public_limiter


class UpbitPublicClient:
    """
    업비트 전용 공개 API 클라이언트

    특징:
    - 업비트 전용 최적화
    - 업비트 Rate Limiter 사용
    - 간단하고 직관적인 구조
    - 기존 인터페이스 호환성 유지
    """

    BASE_URL = "https://api.upbit.com/v1"

    def __init__(self, rate_limiter: Optional[UpbitRateLimiter] = None):
        """
        업비트 공개 API 클라이언트 초기화

        Args:
            rate_limiter: 업비트 Rate Limiter (기본값: 자동 생성)
        """
        self.rate_limiter = rate_limiter or create_upbit_public_limiter("upbit_public")
        self._session: Optional[aiohttp.ClientSession] = None
        self._logger = logging.getLogger("UpbitPublicClient")

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

    async def close(self) -> None:
        """리소스 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

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
        for attempt in range(max_retries):
            # Rate Limit 적용
            await self.rate_limiter.acquire(endpoint, method)

            try:
                async with self._session.request(method, url, params=params, **kwargs) as response:
                    # Rate Limit 헤더 업데이트
                    self.rate_limiter.update_from_upbit_headers(dict(response.headers))

                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 429:
                        # 429 오류 시 지수 백오프로 재시도
                        retry_number = attempt + 1
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 0.5  # 0.5, 1.0, 2.0초
                            self._logger.warning(
                                f"[{endpoint}] 429 오류로 재시도 {retry_number}/{max_retries}, "
                                f"{wait_time:.1f}초 대기 후 재시도"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            self._logger.error(f"[{endpoint}] 429 오류 최대 재시도 초과 {max_retries}/{max_retries}: {error_text}")
                            # 429 전용 예외로 명확히 구분
                            raise Exception(f"Rate Limit 초과 (429): {endpoint} - 최대 재시도 {max_retries}회 초과")
                    else:
                        error_text = await response.text()
                        self._logger.error(f"[{endpoint}] API 오류 {response.status}: {error_text}")
                        raise Exception(f"업비트 API 오류 {response.status}: {error_text}")
            except aiohttp.ClientError as e:
                retry_number = attempt + 1
                self._logger.error(f"[{endpoint}] 네트워크 오류: {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    self._logger.warning(f"[{endpoint}] 네트워크 재시도 {retry_number}/{max_retries}, {wait_time:.1f}초 대기")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception(f"네트워크 오류: {e}")
            except Exception as e:
                # 이미 처리된 429 예외는 그대로 전파
                if "Rate Limit 초과 (429)" in str(e):
                    raise
                # 기타 예외는 재시도 없이 바로 전파
                raise

    # ================================================================
    # 시세 조회 API
    # ================================================================

    async def get_market_all(self, is_details: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        마켓 코드 목록 조회

        Returns:
            Dict[market_code, market_info]: 마켓 코드를 키로 하는 딕셔너리
            예: {
                'KRW-BTC': {
                    'market': 'KRW-BTC',
                    'korean_name': '비트코인',
                    'english_name': 'Bitcoin'
                },
                ...
            }
        """
        params = {}
        if is_details:
            params['isDetails'] = 'true'

        # 원본 API 응답 (리스트 형태)
        markets_list = await self._make_request('/market/all', params=params)

        # Dict 형태로 변환 (market 코드를 키로 사용)
        markets_dict = {}
        for market_info in markets_list:
            market_code = market_info.get('market')
            if market_code:
                markets_dict[market_code] = market_info

        return markets_dict

    async def get_candle_seconds(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """초 캔들 조회 (1초 고정)"""
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to

        return await self._make_request('/candles/seconds', params=params)

    async def get_candle_minutes(
        self,
        market: str,
        unit: int = 1,
        to: Optional[str] = None,
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """분 캔들 조회"""
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to

        return await self._make_request(f'/candles/minutes/{unit}', params=params)

    async def get_candle_days(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
        converting_price_unit: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """일 캔들 조회"""
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to
        if converting_price_unit:
            params['convertingPriceUnit'] = converting_price_unit

        return await self._make_request('/candles/days', params=params)

    async def get_candle_weeks(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """주 캔들 조회"""
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to

        return await self._make_request('/candles/weeks', params=params)

    async def get_candle_months(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """월 캔들 조회"""
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to

        return await self._make_request('/candles/months', params=params)

    async def get_candle_years(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """연 캔들 조회"""
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to

        return await self._make_request('/candles/years', params=params)

    async def get_trades_ticks(
        self,
        market: str,
        to: Optional[str] = None,
        count: int = 1,
        cursor: Optional[str] = None,
        days_ago: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """최근 체결 내역 조회"""
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to
        if cursor:
            params['cursor'] = cursor
        if days_ago:
            params['daysAgo'] = days_ago

        return await self._make_request('/trades/ticks', params=params)

    async def get_ticker(self, markets: Union[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """
        현재가 정보 조회

        Returns:
            Dict[market_code, ticker_info]: 마켓 코드를 키로 하는 딕셔너리
            예: {
                'KRW-BTC': {
                    'market': 'KRW-BTC',
                    'trade_price': 145831000,
                    'change': 'RISE',
                    'change_rate': 0.0234,
                    ...
                },
                ...
            }
        """
        if isinstance(markets, str):
            markets_param = markets
        else:
            markets_param = ','.join(markets)

        params = {'markets': markets_param}
        result = await self._make_request('/ticker', params=params)

        # Dict 형태로 변환 (market 코드를 키로 사용)
        ticker_dict = {}
        for ticker_info in result:
            market_code = ticker_info.get('market')
            if market_code:
                ticker_dict[market_code] = ticker_info

        return ticker_dict

    async def get_orderbook(self, markets: Union[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """
        호가 정보 조회

        Returns:
            Dict[market_code, orderbook_info]: 마켓 코드를 키로 하는 딕셔너리
            예: {
                'KRW-BTC': {
                    'market': 'KRW-BTC',
                    'timestamp': 1625097600000,
                    'orderbook_units': [
                        {
                            'ask_price': 50000000,
                            'bid_price': 49950000,
                            'ask_size': 0.1,
                            'bid_size': 0.2
                        },
                        ...
                    ]
                },
                ...
            }
        """
        if isinstance(markets, str):
            markets_param = markets
        else:
            markets_param = ','.join(markets)

        params = {'markets': markets_param}
        result = await self._make_request('/orderbook', params=params)

        # Dict 형태로 변환 (market 코드를 키로 사용)
        orderbook_dict = {}
        for orderbook_info in result:
            market_code = orderbook_info.get('market')
            if market_code:
                orderbook_dict[market_code] = orderbook_info

        return orderbook_dict

    # ================================================================
    # 편의 메서드들
    # ================================================================

    async def get_single_ticker(self, market: str) -> Dict[str, Any]:
        """단일 마켓 현재가 조회"""
        result = await self.get_ticker(market)
        return result.get(market, {})

    async def get_single_orderbook(self, market: str) -> Dict[str, Any]:
        """단일 마켓 호가 조회"""
        result = await self.get_orderbook(market)
        return result.get(market, {})

    async def get_krw_markets(self) -> List[str]:
        """KRW 마켓 목록 조회"""
        markets = await self.get_market_all()
        return [market_code for market_code in markets.keys() if market_code.startswith('KRW-')]

    async def get_btc_markets(self) -> List[str]:
        """BTC 마켓 목록 조회"""
        markets = await self.get_market_all()
        return [market_code for market_code in markets.keys() if market_code.startswith('BTC-')]

    async def get_usdt_markets(self) -> List[str]:
        """USDT 마켓 목록 조회"""
        markets = await self.get_market_all()
        return [market_code for market_code in markets.keys() if market_code.startswith('USDT-')]

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Rate Limit 상태 조회"""
        return self.rate_limiter.get_status()

    # ================================================================
    # 편의 메서드들 - 캔들 데이터 처리
    # ================================================================

    def convert_candles_to_dict(self, candles: List[Dict[str, Any]],
                                key_field: str = "candle_date_time_utc") -> Dict[str, Dict[str, Any]]:
        """
        캔들 List를 Dict로 변환 (필요한 경우)

        Args:
            candles: 캔들 데이터 리스트
            key_field: Dict의 키로 사용할 필드명

        Returns:
            Dict[time_key, candle_data]: 시간을 키로 하는 딕셔너리

        Example:
            candles_list = await client.get_candle_minutes("KRW-BTC", count=5)
            candles_dict = client.convert_candles_to_dict(candles_list)
            specific_candle = candles_dict["2025-07-01T12:00:00"]
        """
        candles_dict = {}
        for candle in candles:
            key = candle.get(key_field)
            if key:
                candles_dict[key] = candle
        return candles_dict

    def get_latest_candle(self, candles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        최신 캔들 데이터 조회

        Args:
            candles: 캔들 데이터 리스트 (최신순 정렬됨)

        Returns:
            Dict: 최신 캔들 데이터 (없으면 None)
        """
        return candles[0] if candles else None

    def filter_candles_by_time_range(self, candles: List[Dict[str, Any]],
                                     start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """
        시간 범위로 캔들 데이터 필터링

        Args:
            candles: 캔들 데이터 리스트
            start_time: 시작 시간 (ISO 형식)
            end_time: 종료 시간 (ISO 형식)

        Returns:
            List: 필터링된 캔들 데이터
        """
        filtered_candles = []
        for candle in candles:
            candle_time = candle.get("candle_date_time_utc", "")
            if start_time <= candle_time <= end_time:
                filtered_candles.append(candle)
        return filtered_candles


# ================================================================
# 편의 팩토리 함수
# ================================================================

def create_upbit_public_client() -> UpbitPublicClient:
    """업비트 공개 API 클라이언트 생성 (편의 함수)"""
    return UpbitPublicClient()
