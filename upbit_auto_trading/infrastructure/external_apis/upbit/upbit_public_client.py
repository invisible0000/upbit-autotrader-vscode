from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import (
    BaseApiClient, RateLimitConfig, ApiClientError
)


class UpbitPublicClient(BaseApiClient):
    """Upbit 공개 API 클라이언트 - 기존 UpbitAPI 메서드들 기반"""

    def __init__(self):
        # Upbit 공개 API 제한: 초당 10회, 분당 600회 (기존 설정 보존)
        rate_config = RateLimitConfig(
            requests_per_second=10,
            requests_per_minute=600,
            burst_limit=100
        )

        super().__init__(
            base_url='https://api.upbit.com/v1',
            rate_limit_config=rate_config,
            timeout=30,
            max_retries=3
        )

    def _prepare_headers(self, method: str, endpoint: str,
                         params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """공개 API용 헤더 준비 (인증 불필요)"""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    async def get_markets(self, is_details: bool = False) -> List[Dict[str, Any]]:
        """마켓 코드 조회 - 기존 get_markets 메서드 기반"""
        params = {'isDetails': 'true' if is_details else 'false'}

        response = await self._make_request('GET', '/market/all', params=params)

        if not response.success:
            raise ApiClientError(f"마켓 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_candles_minutes(self, market: str, unit: int = 1,
                                  to: Optional[str] = None, count: int = 200) -> List[Dict[str, Any]]:
        """분봉 캔들 조회 - 기존 get_candles 로직 기반"""
        if unit not in [1, 3, 5, 15, 10, 30, 60, 240]:
            raise ValueError(f"유효하지 않은 분봉 단위: {unit}")

        if count > 200:
            raise ValueError("한 번에 최대 200개까지만 조회 가능합니다")

        params = {
            'market': market,
            'count': count
        }

        if to:
            params['to'] = to

        response = await self._make_request('GET', f'/candles/minutes/{unit}', params=params)

        if not response.success:
            raise ApiClientError(f"분봉 캔들 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_candles_days(self, market: str, to: Optional[str] = None,
                               count: int = 200, converting_price_unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """일봉 캔들 조회"""
        if count > 200:
            raise ValueError("한 번에 최대 200개까지만 조회 가능합니다")

        params = {
            'market': market,
            'count': count
        }

        if to:
            params['to'] = to

        if converting_price_unit:
            params['convertingPriceUnit'] = converting_price_unit

        response = await self._make_request('GET', '/candles/days', params=params)

        if not response.success:
            raise ApiClientError(f"일봉 캔들 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_candles_weeks(self, market: str, to: Optional[str] = None,
                                count: int = 200) -> List[Dict[str, Any]]:
        """주봉 캔들 조회"""
        if count > 200:
            raise ValueError("한 번에 최대 200개까지만 조회 가능합니다")

        params = {
            'market': market,
            'count': count
        }

        if to:
            params['to'] = to

        response = await self._make_request('GET', '/candles/weeks', params=params)

        if not response.success:
            raise ApiClientError(f"주봉 캔들 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_candles_months(self, market: str, to: Optional[str] = None,
                                 count: int = 200) -> List[Dict[str, Any]]:
        """월봉 캔들 조회"""
        if count > 200:
            raise ValueError("한 번에 최대 200개까지만 조회 가능합니다")

        params = {
            'market': market,
            'count': count
        }

        if to:
            params['to'] = to

        response = await self._make_request('GET', '/candles/months', params=params)

        if not response.success:
            raise ApiClientError(f"월봉 캔들 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_orderbook(self, markets: List[str]) -> List[Dict[str, Any]]:
        """호가 정보 조회"""
        if len(markets) > 5:
            raise ValueError("한 번에 최대 5개 마켓까지만 조회 가능합니다")

        params = {'markets': ','.join(markets)}

        response = await self._make_request('GET', '/orderbook', params=params)

        if not response.success:
            raise ApiClientError(f"호가 정보 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_tickers(self, markets: List[str]) -> List[Dict[str, Any]]:
        """현재가 정보 조회"""
        if len(markets) > 100:
            raise ValueError("한 번에 최대 100개 마켓까지만 조회 가능합니다")

        params = {'markets': ','.join(markets)}

        response = await self._make_request('GET', '/ticker', params=params)

        if not response.success:
            raise ApiClientError(f"현재가 정보 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_trades_ticks(self, market: str, to: Optional[str] = None,
                               count: int = 200, cursor: Optional[str] = None,
                               days_ago: Optional[int] = None) -> List[Dict[str, Any]]:
        """최근 체결 내역 조회"""
        if count > 500:
            raise ValueError("한 번에 최대 500개까지만 조회 가능합니다")

        params = {
            'market': market,
            'count': count
        }

        if to:
            params['to'] = to
        if cursor:
            params['cursor'] = cursor
        if days_ago is not None:
            params['daysAgo'] = days_ago

        response = await self._make_request('GET', '/trades/ticks', params=params)

        if not response.success:
            raise ApiClientError(f"체결 내역 조회 실패: {response.error_message}",
                                 response.status_code, response.data)

        return response.data

    async def get_market_data_batch(self, market: str, days: int = 30) -> Dict[str, Any]:
        """마켓 데이터 일괄 조회 (캔들 + 현재가 + 호가)"""
        try:
            # 병렬로 데이터 조회
            tasks = [
                self.get_candles_days(market, count=min(days, 200)),
                self.get_tickers([market]),
                self.get_orderbook([market])
            ]

            candles, tickers, orderbook = await asyncio.gather(*tasks)

            return {
                'market': market,
                'candles': candles,
                'ticker': tickers[0] if tickers else None,
                'orderbook': orderbook[0] if orderbook else None,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self._logger.error(f"마켓 데이터 일괄 조회 실패 {market}: {e}")
            raise ApiClientError(f"마켓 데이터 일괄 조회 실패: {str(e)}")

    async def get_krw_markets(self) -> List[str]:
        """KRW 마켓 목록 조회 - 기존 get_markets 필터링 로직 기반"""
        markets = await self.get_markets()
        return [market['market'] for market in markets if market['market'].startswith('KRW-')]
