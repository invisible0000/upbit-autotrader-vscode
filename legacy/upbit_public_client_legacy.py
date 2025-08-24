"""
업비트 공개 API 클라이언트 - 통합 베이스 구조 적용

Union[str, List[str]] 패턴 완전 지원하는 간결한 구현
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import asyncio

from upbit_auto_trading.infrastructure.external_apis.common.api_client_base import (
    BaseApiClient, RateLimitConfig, ApiClientError
)


class UpbitPublicClient(BaseApiClient):
    """업비트 공개 API 클라이언트 - Union 패턴 지원"""

    def __init__(self):
        rate_config = RateLimitConfig.upbit_public_api()
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

    def _normalize_input(self, symbols: Union[str, List[str]]) -> tuple[List[str], bool]:
        """입력을 표준화하고 원본 형태 기억"""
        if isinstance(symbols, str):
            return [symbols], True
        elif isinstance(symbols, list):
            return symbols, False
        else:
            raise ValueError(f"지원하지 않는 입력 타입: {type(symbols)}")

    def _format_response(self, data: List[Any], was_single_input: bool) -> Union[Any, List[Any]]:
        """응답을 원본 입력 형태에 맞게 변환"""
        if was_single_input:
            return data[0] if data else None
        return data

    # =================================================================
    # 핵심 API 메서드들 - Union 패턴 적용
    # =================================================================

    async def get_ticker(self, symbol: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """현재가 정보 조회 - Union 패턴 지원

        Args:
            symbol: 마켓 코드 또는 마켓 코드 리스트

        Returns:
            단일 입력 시: Dict[str, Any] (단일 티커 정보)
            리스트 입력 시: List[Dict[str, Any]] (여러 티커 정보 리스트)
        """
        symbols_list, is_single_input = self._normalize_input(symbol)

        params = {'markets': ','.join(symbols_list)}
        response = await self._make_request('GET', '/ticker', params=params)

        if not response.success:
            raise ApiClientError(f"현재가 조회 실패: {response.error_message}")

        return self._format_response(response.data, is_single_input)

    async def get_orderbook(self, symbol: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """호가 정보 조회 - Union 패턴 지원

        Args:
            symbol: 마켓 코드 또는 마켓 코드 리스트
        """
        symbols_list, is_single_input = self._normalize_input(symbol)

        params = {'markets': ','.join(symbols_list)}
        response = await self._make_request('GET', '/orderbook', params=params)

        if not response.success:
            raise ApiClientError(f"호가 조회 실패: {response.error_message}")

        return self._format_response(response.data, is_single_input)

    async def get_candle(self, symbol: str, timeframe: str = '1d',
                         count: int = 200, to: Optional[str] = None) -> List[Dict[str, Any]]:
        """캔들 정보 조회 - 단일 심볼만 지원

        Args:
            symbol: 마켓 코드 (단일만 지원)
            timeframe: 시간프레임 ('1m', '5m', '1h', '1d', '1w', '1M')
            count: 조회할 캔들 개수 (최대 200)
            to: 마지막 캔들 시각
        """
        if isinstance(symbol, list):
            raise ValueError("캔들 API는 단일 심볼만 지원합니다.")

        # 시간프레임 매핑
        endpoint_map = {
            '1m': '/candles/minutes/1',
            '5m': '/candles/minutes/5',
            '15m': '/candles/minutes/15',
            '30m': '/candles/minutes/30',
            '1h': '/candles/minutes/60',
            '4h': '/candles/minutes/240',
            '1d': '/candles/days',
            '1w': '/candles/weeks',
            '1M': '/candles/months'
        }

        endpoint = endpoint_map.get(timeframe)
        if not endpoint:
            raise ValueError(f"지원하지 않는 시간프레임: {timeframe}")

        params = {'market': symbol, 'count': min(count, 200)}
        if to:
            params['to'] = to

        response = await self._make_request('GET', endpoint, params=params)

        if not response.success:
            raise ApiClientError(f"캔들 조회 실패: {response.error_message}")

        return response.data

    async def get_trade(self, symbol: str, count: int = 200) -> List[Dict[str, Any]]:
        """체결 내역 조회 - 단일 심볼만 지원"""
        if isinstance(symbol, list):
            raise ValueError("체결 API는 단일 심볼만 지원합니다.")

        params = {'market': symbol, 'count': min(count, 500)}
        response = await self._make_request('GET', '/trades/ticks', params=params)

        if not response.success:
            raise ApiClientError(f"체결 조회 실패: {response.error_message}")

        return response.data

    # =================================================================
    # 유틸리티 메서드들
    # =================================================================

    async def get_market(self, is_details: bool = False) -> List[Dict[str, Any]]:
        """마켓 정보 조회"""
        params = {'isDetails': 'true' if is_details else 'false'}
        response = await self._make_request('GET', '/market/all', params=params)

        if not response.success:
            raise ApiClientError(f"마켓 조회 실패: {response.error_message}")

        return response.data

    async def get_krw_market_list(self) -> List[str]:
        """KRW 마켓 목록 조회"""
        markets = await self.get_market()
        return [market['market'] for market in markets if market['market'].startswith('KRW-')]

    # =================================================================
    # 고급 기능
    # =================================================================

    async def get_market_snapshot(self, symbol: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """마켓 스냅샷 조회 (티커 + 호가 통합)"""
        symbols_list, is_single_input = self._normalize_input(symbol)

        # 배치 크기 제한 처리
        if len(symbols_list) <= 5:
            # 5개 이하면 병렬 처리
            ticker_task = self.get_ticker(symbols_list)
            orderbook_task = self.get_orderbook(symbols_list)
            ticker_data, orderbook_data = await asyncio.gather(ticker_task, orderbook_task)
        else:
            # 5개 초과면 개별 처리
            ticker_data = await self.get_ticker(symbols_list)
            orderbook_data = []
            for i in range(0, len(symbols_list), 5):
                batch = symbols_list[i:i + 5]
                batch_orderbook = await self.get_orderbook(batch)
                if isinstance(batch_orderbook, list):
                    orderbook_data.extend(batch_orderbook)
                else:
                    orderbook_data.append(batch_orderbook)

        # 응답 구성
        if is_single_input:
            return {
                'symbol': symbols_list[0],
                'ticker': ticker_data,
                'orderbook': orderbook_data,
                'timestamp': datetime.now().isoformat()
            }
        else:
            snapshots = []
            for i, symbol in enumerate(symbols_list):
                ticker = ticker_data[i] if isinstance(ticker_data, list) and i < len(ticker_data) else None
                orderbook = orderbook_data[i] if isinstance(orderbook_data, list) and i < len(orderbook_data) else None
                snapshots.append({
                    'symbol': symbol,
                    'ticker': ticker,
                    'orderbook': orderbook,
                    'timestamp': datetime.now().isoformat()
                })
            return snapshots

    # =================================================================
    # 레거시 호환성 메서드들 (Deprecated)
    # =================================================================

    async def get_tickers(self, markets: List[str]) -> List[Dict[str, Any]]:
        """[DEPRECATED] get_ticker()를 사용하세요"""
        import warnings
        warnings.warn(
            "get_tickers()는 deprecated입니다. get_ticker()를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        result = await self.get_ticker(markets)
        return result if isinstance(result, list) else [result]

    async def get_orderbooks(self, markets: List[str]) -> List[Dict[str, Any]]:
        """[DEPRECATED] get_orderbook()를 사용하세요"""
        import warnings
        warnings.warn(
            "get_orderbooks()는 deprecated입니다. get_orderbook()를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        result = await self.get_orderbook(markets)
        return result if isinstance(result, list) else [result]

    async def get_markets(self, is_details: bool = False) -> List[Dict[str, Any]]:
        """[DEPRECATED] get_market()를 사용하세요"""
        import warnings
        warnings.warn(
            "get_markets()는 deprecated입니다. get_market()를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        return await self.get_market(is_details)
