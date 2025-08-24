"""
업비트 공개 API 클라이언트 - 어댑터 패턴 적용

새로운 아키텍처를 적용한 확장 가능한 구현
"""
from typing import List, Dict, Any, Optional, Union

from ..core.base_client import BaseExchangeClient
from ..core.rate_limiter import UniversalRateLimiter, ExchangeRateLimitConfig
from ..adapters.upbit_adapter import UpbitAdapter


class UpbitPublicClient(BaseExchangeClient):
    """
    업비트 공개 API 클라이언트

    특징:
    - 어댑터 패턴 적용으로 업비트 로직 분리
    - 거래소 중립적 베이스 클라이언트 상속
    - Union[str, List[str]] 패턴 완전 지원
    - 기존 클라이언트와 호환 가능한 인터페이스
    """

    def __init__(self, adapter: Optional[UpbitAdapter] = None,
                 rate_limiter: Optional[UniversalRateLimiter] = None):
        """
        업비트 공개 API 클라이언트 초기화

        Args:
            adapter: 업비트 어댑터 (기본값: 자동 생성)
            rate_limiter: Rate Limiter (기본값: 자동 생성)
        """
        if adapter is None:
            adapter = UpbitAdapter()
        if rate_limiter is None:
            config = ExchangeRateLimitConfig.for_upbit_public()
            rate_limiter = UniversalRateLimiter(config)

        super().__init__(adapter, rate_limiter)

    def _prepare_headers(self, method: str, endpoint: str,
                         params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """업비트 공개 API용 헤더 준비 (인증 불필요)"""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    # ================================================================
    # 핵심 API 메서드들 - Union 패턴 지원
    # ================================================================

    async def get_ticker(self, symbol: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        현재가 정보 조회 - Union 패턴 지원

        Args:
            symbol: 마켓 코드 또는 마켓 코드 리스트

        Returns:
            단일 입력 시: Dict[str, Any] (단일 티커 정보)
            리스트 입력 시: List[Dict[str, Any]] (여러 티커 정보 리스트)
        """
        response = await self._make_unified_request('/ticker', symbol)

        if not response.success:
            from ..core.data_models import ExchangeApiError
            raise ExchangeApiError(f"현재가 조회 실패: {response.error}")

        return response.get()

    async def get_orderbook(self, symbol: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        호가 정보 조회 - Union 패턴 지원

        Args:
            symbol: 마켓 코드 또는 마켓 코드 리스트
        """
        response = await self._make_unified_request('/orderbook', symbol)

        if not response.success:
            from ..core.data_models import ExchangeApiError
            raise ExchangeApiError(f"호가 조회 실패: {response.error}")

        return response.get()

    async def get_candle(self, symbol: str, timeframe: str = '1d',
                         count: int = 200, to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        캔들 정보 조회 - 단일 심볼만 지원 (업비트 API 문서 기반)

        Args:
            symbol: 마켓 코드 (단일만 지원)
            timeframe: 시간프레임 ('1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M', '1Y')
            count: 조회할 캔들 개수 (최대 200)
            to: 마지막 캔들 시각 (ISO 8601 형식)
        """
        if isinstance(symbol, list):
            raise ValueError("캔들 API는 단일 심볼만 지원합니다.")

        # 어댑터를 통한 엔드포인트 결정
        if hasattr(self.adapter, 'get_candle_endpoint'):
            endpoint = getattr(self.adapter, 'get_candle_endpoint')(timeframe)
        else:
            # 폴백: 업비트 API 문서 기반 완전한 엔드포인트 매핑
            endpoint_map = {
                # 초 캔들
                '1s': '/candles/seconds',
                # 분(Minute) 캔들
                '1m': '/candles/minutes/1',
                '3m': '/candles/minutes/3',
                '5m': '/candles/minutes/5',
                '10m': '/candles/minutes/10',
                '15m': '/candles/minutes/15',
                '30m': '/candles/minutes/30',
                '1h': '/candles/minutes/60',
                '4h': '/candles/minutes/240',
                # 일/주/월/년 캔들 (표준 표기법)
                '1d': '/candles/days',
                '1w': '/candles/weeks',
                '1M': '/candles/months',  # 월은 대문자 (분과 구분)
                '1y': '/candles/years'    # 년은 소문자 (표준)
            }
            endpoint = endpoint_map.get(timeframe)
            if not endpoint:
                raise ValueError(f"지원하지 않는 시간프레임: {timeframe}")

        response = await self._make_unified_request(
            endpoint, symbol,
            timeframe=timeframe, count=count, to=to
        )

        if not response.success:
            from ..core.data_models import ExchangeApiError
            raise ExchangeApiError(f"캔들 조회 실패: {response.error}")

        return response.get()

    async def get_trade(self, symbol: str, count: int = 200) -> List[Dict[str, Any]]:
        """체결 내역 조회 - 단일 심볼만 지원"""
        if isinstance(symbol, list):
            raise ValueError("체결 API는 단일 심볼만 지원합니다.")

        response = await self._make_unified_request(
            '/trades/ticks', symbol, count=count
        )

        if not response.success:
            from ..core.data_models import ExchangeApiError
            raise ExchangeApiError(f"체결 조회 실패: {response.error}")

        return response.get()

    async def get_candle_minutes(self, symbol: str, unit: int = 1, count: int = 200,
                                 to: Optional[str] = None) -> List[Dict[str, Any]]:
        """분 캔들 조회 (API 문서: /candles/minutes/{unit})"""
        return await self.get_candle(symbol, f'{unit}m', count, to)

    async def get_candle_days(self, symbol: str, count: int = 200,
                              to: Optional[str] = None) -> List[Dict[str, Any]]:
        """일 캔들 조회 (API 문서: /candles/days)"""
        return await self.get_candle(symbol, '1d', count, to)

    async def get_trades(self, symbol: str, count: int = 200) -> List[Dict[str, Any]]:
        """체결 내역 조회 (API 문서: /trades/ticks)"""
        return await self.get_trade(symbol, count)

    async def get_candle_seconds(self, symbol: str, count: int = 200,
                                 to: Optional[str] = None) -> List[Dict[str, Any]]:
        """초 캔들 조회 (API 문서: /candles/seconds)"""
        return await self.get_candle(symbol, '1s', count, to)

    async def get_candle_weeks(self, symbol: str, count: int = 200,
                               to: Optional[str] = None) -> List[Dict[str, Any]]:
        """주 캔들 조회 (API 문서: /candles/weeks)"""
        return await self.get_candle(symbol, '1w', count, to)

    async def get_candle_months(self, symbol: str, count: int = 200,
                                to: Optional[str] = None) -> List[Dict[str, Any]]:
        """월 캔들 조회 (API 문서: /candles/months)"""
        return await self.get_candle(symbol, '1M', count, to)

    async def get_candle_years(self, symbol: str, count: int = 200,
                               to: Optional[str] = None) -> List[Dict[str, Any]]:
        """년 캔들 조회 (API 문서: /candles/years)"""
        return await self.get_candle(symbol, '1y', count, to)

    # ================================================================
    # 유틸리티 메서드들
    # ================================================================

    async def get_market(self, is_details: bool = False) -> List[Dict[str, Any]]:
        """마켓 정보 조회 (API 문서: /market/all)"""
        params = {'isDetails': 'true' if is_details else 'false'}

        # 마켓 목록 API는 심볼이 필요하지 않으므로 직접 호출
        response = await self._make_request('GET', '/market/all', params=params)

        if not response.success:
            from ..core.data_models import ExchangeApiError
            raise ExchangeApiError(f"마켓 조회 실패: {response.error_message}")

        return response.data or []

    async def get_krw_market_list(self) -> List[str]:
        """KRW 마켓 목록 조회"""
        markets = await self.get_market()
        return [market['market'] for market in markets if market['market'].startswith('KRW-')]

    # ================================================================
    # 고급 기능
    # ================================================================

    async def get_market_snapshot(self, symbol: Union[str, List[str]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        마켓 스냅샷 조회 (티커 + 호가 통합)

        어댑터 패턴을 활용한 효율적인 병렬 처리
        """
        # 입력 타입 처리
        from ..adapters.base_adapter import InputTypeHandler
        symbols_list, was_single = InputTypeHandler.normalize_symbol_input(symbol)

        # 효율적인 병렬 처리 (API 문서 기반 최적화)
        import asyncio
        batch_size = 10  # 업비트 권장 배치 크기

        if len(symbols_list) <= batch_size:
            # 배치 크기 이하면 병렬 처리
            ticker_task = self.get_ticker(symbols_list)
            orderbook_task = self.get_orderbook(symbols_list)
            ticker_data, orderbook_data = await asyncio.gather(ticker_task, orderbook_task)
        else:
            # 배치 크기 초과시 순차 처리 (Rate Limit 준수)
            ticker_data = await self.get_ticker(symbols_list)
            orderbook_data = []

            # 배치 단위로 호가 조회
            for i in range(0, len(symbols_list), batch_size):
                batch = symbols_list[i:i + batch_size]
                batch_orderbook = await self.get_orderbook(batch)
                if isinstance(batch_orderbook, list):
                    orderbook_data.extend(batch_orderbook)
                else:
                    orderbook_data.append(batch_orderbook)

        # 응답 구성
        if was_single:
            return {
                'symbol': symbols_list[0],
                'ticker': ticker_data,
                'orderbook': orderbook_data,
                'timestamp': self._get_current_timestamp(),
                'exchange': 'upbit'
            }
        else:
            snapshots = []
            for i, sym in enumerate(symbols_list):
                ticker = ticker_data[i] if isinstance(ticker_data, list) and i < len(ticker_data) else None
                orderbook = orderbook_data[i] if isinstance(orderbook_data, list) and i < len(orderbook_data) else None
                snapshots.append({
                    'symbol': sym,
                    'ticker': ticker,
                    'orderbook': orderbook,
                    'timestamp': self._get_current_timestamp(),
                    'exchange': 'upbit'
                })
            return snapshots

    def _get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        from datetime import datetime
        return datetime.now().isoformat()

    # ================================================================
    # 레거시 호환성 메서드들 (Deprecated)
    # ================================================================

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

    async def cleanup(self) -> None:
        """클라이언트 정리 (세션 닫기)"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()

    async def __aenter__(self):
        """async with 지원"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async with 종료 시 정리"""
        await self.cleanup()


# ================================================================
# 편의 팩토리 함수
# ================================================================

def create_upbit_public_client() -> UpbitPublicClient:
    """업비트 공개 API 클라이언트 생성 (편의 함수)"""
    from ..core.rate_limiter import RateLimiterFactory

    adapter = UpbitAdapter()
    rate_limiter = RateLimiterFactory.create_for_exchange('upbit', 'public')
    return UpbitPublicClient(adapter, rate_limiter)
