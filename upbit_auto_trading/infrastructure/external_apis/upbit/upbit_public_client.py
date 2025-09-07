"""
업비트 공개 API 클라이언트 - 동적 GCRA Rate Limiter 기반

DDD Infrastructure 계층 컴포넌트
- 업비트 전용 최적화 구현
- 동적 조정 GCRA Rate Limiter 통합
- 429 오류 자동 처리 및 재시도
- Infrastructure 로깅 시스템 준수
- 인증이 불필요한 공개 API 전담
- gzip 압축 지원으로 대역폭 최적화
"""
import asyncio
import aiohttp
import time
import gzip
import json
from typing import List, Dict, Any, Optional, Union

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .upbit_rate_limiter import get_global_rate_limiter, UpbitGCRARateLimiter
from .dynamic_rate_limiter_wrapper import (
    get_dynamic_rate_limiter,
    DynamicUpbitRateLimiter,
    DynamicConfig,
    AdaptiveStrategy
)


class UpbitPublicClient:
    """
    업비트 공개 API 클라이언트 - 동적 GCRA Rate Limiter 기반

    주요 특징:
    - 동적 조정 GCRA Rate Limiter 기본 사용
    - 429 오류 자동 감지 및 Rate Limit 조정
    - Infrastructure 로깅 시스템 준수
    - 전역 공유 Rate Limiter 지원
    - 상세한 응답 시간 추적
    - 버스트 처리 지원
    - 인증 불필요 (공개 API 전용)

    DDD 원칙:
    - Infrastructure 계층 컴포넌트
    - 외부 API 통신 책임
    - 도메인 로직 포함 금지
    """

    BASE_URL = "https://api.upbit.com/v1"

    def __init__(self,
                 use_dynamic_limiter: bool = True,
                 dynamic_config: Optional[DynamicConfig] = None,
                 legacy_rate_limiter: Optional[UpbitGCRARateLimiter] = None,
                 enable_gzip: bool = True):
        """
        업비트 공개 API 클라이언트 초기화

        Args:
            use_dynamic_limiter: 동적 Rate Limiter 사용 여부 (기본값: True)
            dynamic_config: 동적 조정 설정 (기본값: 균형 전략)
            legacy_rate_limiter: 기존 GCRA Rate Limiter (동적 비활성화 시)
            enable_gzip: gzip 압축 사용 여부 (기본값: True, 대역폭 83% 절약 가능)

        Note:
            공개 API 클라이언트는 인증이 불필요하며,
            모든 업비트 공개 데이터 조회 기능을 제공합니다.
            gzip 압축을 통해 대역폭 사용량을 크게 줄일 수 있습니다.
        """
        # Infrastructure 로깅 초기화
        self._logger = create_component_logger("UpbitPublicClient")

        # Rate Limiter 설정
        self._use_dynamic_limiter = use_dynamic_limiter
        self._dynamic_limiter: Optional[DynamicUpbitRateLimiter] = None
        self._legacy_rate_limiter = legacy_rate_limiter
        self._dynamic_config = dynamic_config or DynamicConfig(strategy=AdaptiveStrategy.BALANCED)

        # gzip 압축 설정
        self._enable_gzip = enable_gzip

        # HTTP 세션 관리
        self._session: Optional[aiohttp.ClientSession] = None

        # 성능 통계 추적
        self._stats = {
            'total_requests': 0,
            'total_429_retries': 0,
            'last_request_429_retries': 0,
            'average_response_time_ms': 0.0,
            'last_http_response_time_ms': 0.0,
            'gzip_enabled': enable_gzip,
            'total_bytes_received': 0,
            'total_compressed_bytes': 0
        }

        self._logger.info(f"✅ UpbitPublicClient 초기화 완료 (동적 Rate Limiter: {use_dynamic_limiter}, "
                         f"gzip: {enable_gzip})")

    def __repr__(self):
        return (f"UpbitPublicClient("
                f"dynamic_limiter={self._use_dynamic_limiter}, "
                f"total_requests={self._stats['total_requests']})")

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ================================================================
    # 세션 및 리소스 관리
    # ================================================================

    async def _ensure_session(self) -> None:
        """HTTP 세션 확보 - 연결 풀링, 타임아웃 및 gzip 압축 최적화"""
        if not self._session or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,           # 전체 연결 제한
                limit_per_host=30,   # 호스트당 연결 제한
                keepalive_timeout=30,  # Keep-alive 타임아웃
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(
                total=30,      # 전체 요청 타임아웃
                connect=10,    # 연결 타임아웃
                sock_read=20   # 소켓 읽기 타임아웃
            )

            # 기본 헤더 설정 (gzip 압축 지원 포함)
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'upbit-autotrader-vscode/1.0'
            }

            # gzip 압축 요청 (대역폭 83% 절약 가능)
            if self._enable_gzip:
                headers['Accept-Encoding'] = 'gzip, deflate'

            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
            self._logger.debug(f"🌐 HTTP 세션 초기화 완료 (gzip: {self._enable_gzip})")

    async def _ensure_rate_limiter(self) -> Union[DynamicUpbitRateLimiter, UpbitGCRARateLimiter]:
        """Rate Limiter 확보 (동적 우선, 전역 공유 대체)"""
        if self._use_dynamic_limiter:
            if self._dynamic_limiter is None:
                self._dynamic_limiter = await get_dynamic_rate_limiter(self._dynamic_config)
                self._logger.debug("🔄 동적 Rate Limiter 초기화 완료")
            return self._dynamic_limiter
        else:
            if self._legacy_rate_limiter is None:
                self._legacy_rate_limiter = await get_global_rate_limiter()
                self._logger.debug("⚙️ 레거시 Rate Limiter 초기화 완료")
            return self._legacy_rate_limiter

    async def close(self) -> None:
        """리소스 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            self._logger.debug("🗑️ HTTP 세션 정리 완료")

        # 동적 Rate Limiter 모니터링 중지
        if self._dynamic_limiter:
            await self._dynamic_limiter.stop_monitoring()

    # ================================================================
    # 상태 조회 및 통계
    # ================================================================

    def get_stats(self) -> Dict[str, Any]:
        """클라이언트 통계 정보 조회"""
        stats = self._stats.copy()

        # 동적 Rate Limiter 통계 추가
        if self._dynamic_limiter:
            stats['dynamic_limiter'] = self._dynamic_limiter.get_dynamic_status()

        return stats

    def get_last_http_response_time(self) -> float:
        """
        마지막 HTTP 요청의 순수 서버 응답 시간 조회 (Rate Limiter 대기 시간 제외)

        Returns:
            float: 응답 시간 (밀리초)
        """
        return self._stats['last_http_response_time_ms']

    # ================================================================
    # 핵심 HTTP 요청 처리
    # ================================================================

    async def _make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        업비트 공개 API 요청 실행 - 429 자동 처리 및 재시도

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드 (기본값: GET)
            params: 쿼리 파라미터
            **kwargs: 추가 aiohttp 옵션

        Returns:
            Any: API 응답 데이터

        Raises:
            Exception: API 오류 또는 네트워크 오류
        """
        await self._ensure_session()

        if not self._session:
            raise RuntimeError("HTTP 세션이 초기화되지 않았습니다")

        url = f"{self.BASE_URL}{endpoint}"
        max_retries = 3

        # 요청별 429 재시도 카운터 초기화
        self._stats['last_request_429_retries'] = 0
        self._stats['total_requests'] += 1

        for attempt in range(max_retries):
            try:
                # Rate Limit 적용
                rate_limiter = await self._ensure_rate_limiter()
                await rate_limiter.acquire(endpoint, method)

                # 순수 HTTP 요청 시간 측정 시작
                http_start_time = time.perf_counter()

                async with self._session.request(method, url, params=params, **kwargs) as response:
                    http_end_time = time.perf_counter()

                    # 순수 HTTP 응답 시간 저장 (Rate Limiter 대기 시간 제외)
                    response_time_ms = (http_end_time - http_start_time) * 1000
                    self._stats['last_http_response_time_ms'] = response_time_ms

                    # 평균 응답 시간 업데이트
                    if self._stats['average_response_time_ms'] == 0.0:
                        self._stats['average_response_time_ms'] = response_time_ms
                    else:
                        # 지수 이동 평균 (α=0.1)
                        self._stats['average_response_time_ms'] = (
                            0.9 * self._stats['average_response_time_ms']
                            + 0.1 * response_time_ms
                        )

                    if response.status == 200:
                        # gzip 압축 통계 업데이트
                        content_encoding = response.headers.get('Content-Encoding', '')
                        content_length = response.headers.get('Content-Length')

                        # 응답 데이터 읽기
                        response_data = await response.json()

                        # 압축 통계 추적 (가능한 경우)
                        if content_length:
                            compressed_size = int(content_length)
                            self._stats['total_compressed_bytes'] += compressed_size

                            # 압축 효율 로깅
                            if 'gzip' in content_encoding.lower() and self._enable_gzip:
                                self._logger.debug(f"✅ gzip 압축 응답: {endpoint} "
                                                 f"({compressed_size} bytes, {response_time_ms:.1f}ms)")
                            else:
                                self._logger.debug(f"✅ 일반 응답: {endpoint} "
                                                 f"({compressed_size} bytes, {response_time_ms:.1f}ms)")
                        else:
                            self._logger.debug(f"✅ API 요청 성공: {method} {endpoint} ({response_time_ms:.1f}ms)")

                        return response_data

                    elif response.status == 429:
                        # 429 응답 처리 - 동적/레거시 Rate Limiter별 처리
                        retry_after = response.headers.get('Retry-After')
                        retry_after_float = float(retry_after) if retry_after else None

                        if isinstance(rate_limiter, DynamicUpbitRateLimiter):
                            # 동적 Rate Limiter는 자동으로 429 처리됨 (acquire 단계에서)
                            pass
                        else:
                            # 레거시 Rate Limiter 수동 처리
                            rate_limiter.handle_429_response(retry_after=retry_after_float)

                        # 429 재시도 카운터 업데이트
                        self._stats['last_request_429_retries'] += 1
                        self._stats['total_429_retries'] += 1

                        self._logger.warning(f"⚠️ Rate Limit 초과 (429): {endpoint}, 재시도 {attempt + 1}/{max_retries}")

                        # 429 오류 시 지수 백오프로 재시도
                        if attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 0.5  # 0.5, 1.0, 2.0초
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            raise Exception(f"429 Rate Limit 오류로 {max_retries}회 재시도 후에도 실패: {error_text}")

                    else:
                        error_text = await response.text()
                        self._logger.error(f"❌ API 오류 (상태: {response.status}): {error_text}")
                        raise Exception(f"API 오류 (상태: {response.status}): {error_text}")

            except asyncio.TimeoutError:
                self._logger.warning(f"⏰ 타임아웃 발생: {endpoint}, 재시도 {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.3  # 타임아웃 재시도
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"타임아웃으로 {max_retries}회 재시도 후에도 실패")

            except Exception as e:
                self._logger.error(f"❌ HTTP 요청 중 오류 발생: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5)
                    continue
                else:
                    raise e

        raise Exception("모든 재시도 실패")

    # ================================================================
    # 시세 정보 API - 현재가, 호가, 체결
    # ================================================================

    async def get_ticker(self, markets: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        현재가 정보 조회

        특정 마켓의 현재가 정보를 조회합니다.

        Args:
            markets: 마켓 코드 또는 마켓 코드 리스트
                - 단일 마켓: 'KRW-BTC'
                - 여러 마켓: ['KRW-BTC', 'KRW-ETH']
                - 최대 100개까지 조회 가능

        Returns:
            List[Dict[str, Any]]: 현재가 정보 리스트
                [
                    {
                        'market': 'KRW-BTC',           # 마켓 코드
                        'trade_date': '20230101',      # 최근 거래 일자
                        'trade_time': '120000',        # 최근 거래 시각
                        'trade_date_kst': '20230101',  # 최근 거래 일자 (KST)
                        'trade_time_kst': '210000',    # 최근 거래 시각 (KST)
                        'trade_timestamp': 1672574400000,  # 최근 거래 일시 (timestamp)
                        'opening_price': 19000000.0,   # 시가
                        'high_price': 19500000.0,      # 고가
                        'low_price': 18500000.0,       # 저가
                        'trade_price': 19200000.0,     # 종가 (현재가)
                        'prev_closing_price': 19100000.0,  # 전일 종가
                        'change': 'RISE',              # 전일 대비 ('RISE', 'FALL', 'EVEN')
                        'change_price': 100000.0,      # 전일 대비 가격
                        'change_rate': 0.00523560209,  # 전일 대비 등락률
                        'signed_change_price': 100000.0,    # 부호가 있는 변화 가격
                        'signed_change_rate': 0.00523560209,  # 부호가 있는 변화율
                        'trade_volume': 0.12345678,    # 가장 최근 거래량
                        'acc_trade_price': 15432109876.0,   # 누적 거래대금 (UTC 0시 기준)
                        'acc_trade_price_24h': 15432109876.0,  # 24시간 누적 거래대금
                        'acc_trade_volume': 1234.56789012,     # 누적 거래량 (UTC 0시 기준)
                        'acc_trade_volume_24h': 1234.56789012,  # 24시간 누적 거래량
                        'highest_52_week_price': 25000000.0,   # 52주 신고가
                        'highest_52_week_date': '2022-11-15',  # 52주 신고가 달성일
                        'lowest_52_week_price': 15000000.0,    # 52주 신저가
                        'lowest_52_week_date': '2022-06-18',   # 52주 신저가 달성일
                        'timestamp': 1672574400000      # 타임스탬프
                    }
                ]

        Examples:
            # 단일 마켓 조회
            ticker = await client.get_ticker('KRW-BTC')

            # 여러 마켓 조회
            tickers = await client.get_ticker(['KRW-BTC', 'KRW-ETH', 'KRW-XRP'])

        Raises:
            ValueError: 마켓 코드가 비어있거나 100개를 초과하는 경우
            Exception: API 오류
        """
        if isinstance(markets, str):
            markets = [markets]

        if not markets:
            raise ValueError("마켓 코드는 필수입니다")

        if len(markets) > 100:
            raise ValueError("한 번에 조회할 수 있는 마켓은 최대 100개입니다")

        params = {'markets': ','.join(markets)}
        response = await self._make_request('/ticker', params=params)

        self._logger.debug(f"📊 현재가 정보 조회 완료: {len(markets)}개 마켓")
        return response

    async def get_tickers(self, quote_currency: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        전체 마켓 현재가 정보 조회

        업비트에서 제공하는 모든 마켓의 현재가 정보를 조회합니다.

        Args:
            quote_currency: 기준 통화 필터링 (옵션)
                - None: 모든 마켓
                - 'KRW': 원화 마켓만
                - 'BTC': 비트코인 마켓만
                - 'USDT': USDT 마켓만

        Returns:
            List[Dict[str, Any]]: 전체 마켓 현재가 정보 리스트
                (응답 형식은 get_ticker()와 동일)

        Examples:
            # 모든 마켓 조회
            all_tickers = await client.get_tickers()

            # 원화 마켓만 조회
            krw_tickers = await client.get_tickers('KRW')

            # 비트코인 마켓만 조회
            btc_tickers = await client.get_tickers('BTC')

        Raises:
            Exception: API 오류
        """
        params = {}
        if quote_currency:
            params['quote_currency'] = quote_currency

        response = await self._make_request('/ticker', params=params)

        currency_info = f" ({quote_currency} 마켓)" if quote_currency else ""
        self._logger.debug(f"📊 전체 마켓 현재가 조회 완료: {len(response)}개 마켓{currency_info}")
        return response

    async def get_orderbook(self, markets: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        호가 정보 조회

        특정 마켓의 호가 정보를 조회합니다.

        Args:
            markets: 마켓 코드 또는 마켓 코드 리스트
                - 단일 마켓: 'KRW-BTC'
                - 여러 마켓: ['KRW-BTC', 'KRW-ETH']
                - 최대 5개까지 조회 가능

        Returns:
            List[Dict[str, Any]]: 호가 정보 리스트
                [
                    {
                        'market': 'KRW-BTC',           # 마켓 코드
                        'timestamp': 1672574400000,    # 호가 생성 시각
                        'total_ask_size': 12.34567890,     # 호가 매도 총 잔량
                        'total_bid_size': 23.45678901,     # 호가 매수 총 잔량
                        'orderbook_units': [           # 호가 리스트 (15단계)
                            {
                                'ask_price': 19200000.0,    # 매도 호가
                                'bid_price': 19190000.0,    # 매수 호가
                                'ask_size': 0.12345678,     # 매도 잔량
                                'bid_size': 0.23456789      # 매수 잔량
                            },
                            ...
                        ]
                    }
                ]

        Examples:
            # 단일 마켓 호가 조회
            orderbook = await client.get_orderbook('KRW-BTC')

            # 여러 마켓 호가 조회
            orderbooks = await client.get_orderbook(['KRW-BTC', 'KRW-ETH'])

        Raises:
            ValueError: 마켓 코드가 비어있거나 5개를 초과하는 경우
            Exception: API 오류
        """
        if isinstance(markets, str):
            markets = [markets]

        if not markets:
            raise ValueError("마켓 코드는 필수입니다")

        if len(markets) > 5:
            raise ValueError("한 번에 조회할 수 있는 마켓은 최대 5개입니다")

        params = {'markets': ','.join(markets)}
        response = await self._make_request('/orderbook', params=params)

        self._logger.debug(f"📋 호가 정보 조회 완료: {len(markets)}개 마켓")
        return response

    async def get_orderbook_instruments(self, markets: Union[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """
        호가 단위 정보 조회

        지정한 마켓들의 호가 단위(tick_size)와 호가 모아보기 단위(supported_levels) 정보를 조회합니다.

        Args:
            markets: 마켓 코드 또는 마켓 코드 리스트
                    (예: 'KRW-BTC' 또는 ['KRW-BTC', 'KRW-ETH'])

        Returns:
            Dict[str, Dict[str, Any]]: 마켓별 호가 단위 정보
                {
                    'KRW-BTC': {
                        'market': 'KRW-BTC',
                        'quote_currency': 'KRW',
                        'tick_size': 1000,                # 호가 단위
                        'supported_levels': [0, 10000, 100000, ...]  # 호가 모아보기 단위
                    },
                    'KRW-ETH': {
                        'market': 'KRW-ETH',
                        'quote_currency': 'KRW',
                        'tick_size': 1000,
                        'supported_levels': [0, 10000, 100000, ...]
                    }
                }

        Examples:
            # 단일 마켓 호가 단위 조회
            instruments = await client.get_orderbook_instruments('KRW-BTC')
            btc_tick_size = instruments['KRW-BTC']['tick_size']

            # 여러 마켓 호가 단위 조회
            instruments = await client.get_orderbook_instruments(['KRW-BTC', 'KRW-ETH'])

        Raises:
            ValueError: 마켓 코드가 비어있는 경우
            Exception: API 오류

        Note:
            이 API는 호가 그룹 내에서 초당 최대 10회 호출 제한이 있습니다.
        """
        if isinstance(markets, str):
            markets = [markets]

        if not markets:
            raise ValueError("마켓 코드는 필수입니다")

        params = {'markets': ','.join(markets)}
        response = await self._make_request('/orderbook/instruments', params=params)

        # List를 Dict으로 변환 (마켓별 빠른 접근을 위해)
        instruments_dict = {}
        for item in response:
            market = item.get('market')
            if market:
                instruments_dict[market] = item

        self._logger.debug(f"📏 호가 단위 정보 조회 완료: {len(instruments_dict)}개 마켓")
        return instruments_dict

    async def get_trades(self, market: str, count: int = 100) -> List[Dict[str, Any]]:
        """
        최근 체결 내역 조회

        특정 마켓의 최근 체결 내역을 조회합니다.

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            count: 조회할 체결 개수 (기본값: 100, 최대: 500)

        Returns:
            List[Dict[str, Any]]: 체결 내역 리스트 (최신 순)
                [
                    {
                        'market': 'KRW-BTC',           # 마켓 코드
                        'trade_date_utc': '2023-01-01',    # 체결 일자 (UTC)
                        'trade_time_utc': '12:00:00',      # 체결 시각 (UTC)
                        'timestamp': 1672574400000,        # 체결 타임스탬프
                        'trade_price': 19200000.0,         # 체결 가격
                        'trade_volume': 0.12345678,        # 체결 량
                        'prev_closing_price': 19100000.0,  # 전일 종가
                        'change_price': 100000.0,          # 변화 가격
                        'ask_bid': 'BID',                  # 매수/매도 구분 ('ASK', 'BID')
                        'sequential_id': 1672574400000123   # 체결 번호 (Unique)
                    },
                    ...
                ]

        Examples:
            # 최근 100개 체결 내역
            trades = await client.get_trades('KRW-BTC')

            # 최근 50개 체결 내역
            trades = await client.get_trades('KRW-BTC', count=50)

        Raises:
            ValueError: 마켓 코드가 비어있거나 count가 500을 초과하는 경우
            Exception: API 오류
        """
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        if count > 500:
            raise ValueError("한 번에 조회할 수 있는 체결 내역은 최대 500개입니다")

        params = {'market': market, 'count': str(count)}
        response = await self._make_request('/trades/ticks', params=params)

        self._logger.debug(f"📈 체결 내역 조회 완료: {market}, {len(response)}개 체결")
        return response

    # ================================================================
    # 캔들 정보 API - 초봉, 분봉, 일봉, 주봉, 월봉, 연봉
    # ================================================================

    async def get_candles_seconds(self, market: str, count: int = 200, to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        초봉 정보 조회

        특정 마켓의 초봉 데이터를 조회합니다.

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            count: 조회할 캔들 개수 (기본값: 200, 최대: 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: '2023-01-01T00:00:00Z')
                None이면 가장 최근 캔들부터 조회

        Returns:
            List[Dict[str, Any]]: 초봉 데이터 리스트 (과거순 → 최신순)
                [
                    {
                        'market': 'KRW-BTC',              # 마켓 코드
                        'candle_date_time_utc': '2023-01-01T12:00:00',  # 캔들 기준 시각 (UTC)
                        'candle_date_time_kst': '2023-01-01T21:00:00',  # 캔들 기준 시각 (KST)
                        'opening_price': 19000000.0,       # 시가
                        'high_price': 19200000.0,          # 고가
                        'low_price': 18900000.0,           # 저가
                        'trade_price': 19100000.0,         # 종가
                        'timestamp': 1672574400000,        # 타임스탬프
                        'candle_acc_trade_price': 123456789.0,  # 누적 거래 금액
                        'candle_acc_trade_volume': 6.78901234   # 누적 거래량
                    },
                    ...
                ]

        Examples:
            # 초봉 200개 조회
            candles = await client.get_candles_seconds('KRW-BTC')

            # 초봉 100개 조회
            candles = await client.get_candles_seconds('KRW-BTC', count=100)

            # 특정 시각부터 초봉 조회
            candles = await client.get_candles_seconds(
                'KRW-BTC',
                count=50,
                to='2023-01-01T00:00:00Z'
            )

        Raises:
            ValueError: 마켓 코드가 비어있거나 count가 200을 초과하는 경우
            Exception: API 오류

        Note:
            초 캔들 조회는 최대 3개월 이내 데이터만 제공됩니다.
            조회 가능 기간을 초과한 경우 빈 리스트가 반환될 수 있습니다.
        """
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        if count > 200:
            raise ValueError("조회 가능한 최대 캔들 개수는 200개입니다")

        params = {'market': market, 'count': str(count)}
        if to:
            params['to'] = to

        response = await self._make_request('/candles/seconds', params=params)

        self._logger.debug(f"⚡ 초봉 조회 완료: {market}, {len(response)}개 캔들")
        return response

    async def get_candles_minutes(
        self,
        unit: int,
        market: str,
        count: int = 200,
        to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        분봉 정보 조회

        특정 마켓의 분봉 데이터를 조회합니다.

        Args:
            unit: 분봉 단위 (1, 3, 5, 15, 10, 30, 60, 240)
            market: 마켓 코드 (예: 'KRW-BTC')
            count: 조회할 캔들 개수 (기본값: 200, 최대: 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: '2023-01-01T00:00:00Z')
                None이면 가장 최근 캔들부터 조회

        Returns:
            List[Dict[str, Any]]: 분봉 데이터 리스트 (과거순 → 최신순)
                [
                    {
                        'market': 'KRW-BTC',              # 마켓 코드
                        'candle_date_time_utc': '2023-01-01T12:00:00',  # 캔들 기준 시각 (UTC)
                        'candle_date_time_kst': '2023-01-01T21:00:00',  # 캔들 기준 시각 (KST)
                        'opening_price': 19000000.0,       # 시가
                        'high_price': 19200000.0,          # 고가
                        'low_price': 18900000.0,           # 저가
                        'trade_price': 19100000.0,         # 종가
                        'timestamp': 1672574400000,        # 타임스탬프
                        'candle_acc_trade_price': 123456789.0,  # 누적 거래 금액
                        'candle_acc_trade_volume': 6.78901234,  # 누적 거래량
                        'unit': 1                          # 분봉 단위
                    },
                    ...
                ]

        Examples:
            # 1분봉 200개 조회
            candles = await client.get_candles_minutes(1, 'KRW-BTC')

            # 5분봉 100개 조회
            candles = await client.get_candles_minutes(5, 'KRW-BTC', count=100)

            # 특정 시각부터 15분봉 조회
            candles = await client.get_candles_minutes(
                15, 'KRW-BTC',
                count=50,
                to='2023-01-01T00:00:00Z'
            )

        Raises:
            ValueError: 잘못된 unit, 마켓 코드, count 값
            Exception: API 오류
        """
        valid_units = [1, 3, 5, 15, 10, 30, 60, 240]
        if unit not in valid_units:
            raise ValueError(f"지원하지 않는 분봉 단위입니다. 지원 단위: {valid_units}")

        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        if count > 200:
            raise ValueError("한 번에 조회할 수 있는 캔들은 최대 200개입니다")

        endpoint = f'/candles/minutes/{unit}'
        params = {'market': market, 'count': str(count)}
        if to:
            params['to'] = to

        response = await self._make_request(endpoint, params=params)

        self._logger.debug(f"🕐 {unit}분봉 조회 완료: {market}, {len(response)}개 캔들")
        return response

    async def get_candles_days(
        self,
        market: str,
        count: int = 200,
        to: Optional[str] = None,
        converting_price_unit: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        일봉 정보 조회

        특정 마켓의 일봉 데이터를 조회합니다.

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            count: 조회할 캔들 개수 (기본값: 200, 최대: 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: '2023-01-01T00:00:00Z')
            converting_price_unit: 종가 환산 통화 단위 (예: 'KRW')

        Returns:
            List[Dict[str, Any]]: 일봉 데이터 리스트 (과거순 → 최신순)
                [
                    {
                        'market': 'KRW-BTC',              # 마켓 코드
                        'candle_date_time_utc': '2023-01-01T00:00:00',  # 캔들 기준 시각 (UTC)
                        'candle_date_time_kst': '2023-01-01T09:00:00',  # 캔들 기준 시각 (KST)
                        'opening_price': 19000000.0,       # 시가
                        'high_price': 19500000.0,          # 고가
                        'low_price': 18500000.0,           # 저가
                        'trade_price': 19200000.0,         # 종가
                        'timestamp': 1672531200000,        # 타임스탬프
                        'candle_acc_trade_price': 15432109876.0,  # 누적 거래 금액
                        'candle_acc_trade_volume': 1234.56789012,  # 누적 거래량
                        'prev_closing_price': 19100000.0,  # 전일 종가
                        'change_price': 100000.0,          # 전일 대비 가격
                        'change_rate': 0.00523560209,      # 전일 대비 등락률
                        'converted_trade_price': 19200000.0  # 종가 환산 가격 (converting_price_unit 설정 시)
                    },
                    ...
                ]

        Examples:
            # 일봉 200개 조회
            candles = await client.get_candles_days('KRW-BTC')

            # 일봉 100개 조회
            candles = await client.get_candles_days('KRW-BTC', count=100)

            # 특정 날짜부터 일봉 조회
            candles = await client.get_candles_days(
                'KRW-BTC',
                count=30,
                to='2023-01-01T00:00:00Z'
            )

        Raises:
            ValueError: 마켓 코드가 비어있거나 count가 200을 초과하는 경우
            Exception: API 오류
        """
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        if count > 200:
            raise ValueError("한 번에 조회할 수 있는 캔들은 최대 200개입니다")

        params = {'market': market, 'count': str(count)}
        if to:
            params['to'] = to
        if converting_price_unit:
            params['convertingPriceUnit'] = converting_price_unit

        response = await self._make_request('/candles/days', params=params)

        self._logger.debug(f"📅 일봉 조회 완료: {market}, {len(response)}개 캔들")
        return response

    async def get_candles_weeks(self, market: str, count: int = 200, to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        주봉 정보 조회

        특정 마켓의 주봉 데이터를 조회합니다.

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            count: 조회할 캔들 개수 (기본값: 200, 최대: 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: '2023-01-01T00:00:00Z')

        Returns:
            List[Dict[str, Any]]: 주봉 데이터 리스트 (과거순 → 최신순)
                (응답 형식은 일봉과 유사하지만 주 단위 데이터)

        Examples:
            # 주봉 200개 조회
            candles = await client.get_candles_weeks('KRW-BTC')

            # 주봉 52개 조회 (1년)
            candles = await client.get_candles_weeks('KRW-BTC', count=52)

        Raises:
            ValueError: 마켓 코드가 비어있거나 count가 200을 초과하는 경우
            Exception: API 오류
        """
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        if count > 200:
            raise ValueError("한 번에 조회할 수 있는 캔들은 최대 200개입니다")

        params = {'market': market, 'count': str(count)}
        if to:
            params['to'] = to

        response = await self._make_request('/candles/weeks', params=params)

        self._logger.debug(f"📊 주봉 조회 완료: {market}, {len(response)}개 캔들")
        return response

    async def get_candles_months(self, market: str, count: int = 200, to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        월봉 정보 조회

        특정 마켓의 월봉 데이터를 조회합니다.

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            count: 조회할 캔들 개수 (기본값: 200, 최대: 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: '2023-01-01T00:00:00Z')

        Returns:
            List[Dict[str, Any]]: 월봉 데이터 리스트 (과거순 → 최신순)
                (응답 형식은 일봉과 유사하지만 월 단위 데이터)

        Examples:
            # 월봉 200개 조회
            candles = await client.get_candles_months('KRW-BTC')

            # 월봉 24개 조회 (2년)
            candles = await client.get_candles_months('KRW-BTC', count=24)

        Raises:
            ValueError: 마켓 코드가 비어있거나 count가 200을 초과하는 경우
            Exception: API 오류
        """
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        if count > 200:
            raise ValueError("한 번에 조회할 수 있는 캔들은 최대 200개입니다")

        params = {'market': market, 'count': str(count)}
        if to:
            params['to'] = to

        response = await self._make_request('/candles/months', params=params)

        self._logger.debug(f"📆 월봉 조회 완료: {market}, {len(response)}개 캔들")
        return response

    async def get_candles_years(self, market: str, count: int = 200, to: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        연봉 정보 조회

        특정 마켓의 연봉 데이터를 조회합니다.

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')
            count: 조회할 캔들 개수 (기본값: 200, 최대: 200)
            to: 마지막 캔들 시각 (ISO 8601 형식, 예: '2023-01-01T00:00:00Z')

        Returns:
            List[Dict[str, Any]]: 연봉 데이터 리스트 (과거순 → 최신순)
                [
                    {
                        'market': 'KRW-BTC',              # 마켓 코드
                        'candle_date_time_utc': '2023-01-01T00:00:00',  # 캔들 기준 시각 (UTC)
                        'candle_date_time_kst': '2023-01-01T09:00:00',  # 캔들 기준 시각 (KST)
                        'opening_price': 19000000.0,       # 시가
                        'high_price': 19500000.0,          # 고가
                        'low_price': 18500000.0,           # 저가
                        'trade_price': 19200000.0,         # 종가
                        'timestamp': 1672531200000,        # 타임스탬프
                        'candle_acc_trade_price': 15432109876.0,  # 누적 거래 금액
                        'candle_acc_trade_volume': 1234.56789012,  # 누적 거래량
                        'prev_closing_price': 19100000.0,  # 전년 종가
                        'change_price': 100000.0,          # 전년 대비 가격
                        'change_rate': 0.00523560209,      # 전년 대비 등락률
                        'first_day_of_period': '2023-01-01'  # 캔들 집계 시작일자
                    },
                    ...
                ]

        Examples:
            # 연봉 200개 조회
            candles = await client.get_candles_years('KRW-BTC')

            # 연봉 10개 조회 (10년)
            candles = await client.get_candles_years('KRW-BTC', count=10)

        Raises:
            ValueError: 마켓 코드가 비어있거나 count가 200을 초과하는 경우
            Exception: API 오류
        """
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        if count > 200:
            raise ValueError("한 번에 조회할 수 있는 캔들은 최대 200개입니다")

        params = {'market': market, 'count': str(count)}
        if to:
            params['to'] = to

        response = await self._make_request('/candles/years', params=params)

        self._logger.debug(f"📊 연봉 조회 완료: {market}, {len(response)}개 캔들")
        return response

    # ================================================================
    # 마켓 정보 API - 마켓 코드, 거래 가능 정보
    # ================================================================

    async def get_markets(self) -> List[Dict[str, Any]]:
        """
        마켓 코드 목록 조회

        업비트에서 거래 가능한 모든 마켓의 정보를 조회합니다.

        Returns:
            List[Dict[str, Any]]: 마켓 정보 리스트
                [
                    {
                        'market': 'KRW-BTC',              # 마켓 코드
                        'korean_name': '비트코인',         # 거래 대상 암호화폐 한글명
                        'english_name': 'Bitcoin',        # 거래 대상 암호화폐 영문명
                        'market_warning': 'NONE'          # 유의 종목 여부 ('NONE', 'CAUTION')
                    },
                    {
                        'market': 'KRW-ETH',
                        'korean_name': '이더리움',
                        'english_name': 'Ethereum',
                        'market_warning': 'NONE'
                    },
                    ...
                ]

        Examples:
            # 전체 마켓 목록 조회
            markets = await client.get_markets()

            # 원화 마켓만 필터링
            krw_markets = [m for m in markets if m['market'].startswith('KRW-')]

            # 비트코인 마켓만 필터링
            btc_markets = [m for m in markets if m['market'].startswith('BTC-')]

        Raises:
            Exception: API 오류
        """
        response = await self._make_request('/market/all')

        self._logger.debug(f"🏪 마켓 목록 조회 완료: {len(response)}개 마켓")
        return response

    # ================================================================
    # 편의 메서드 - 자주 사용되는 조합 기능
    # ================================================================

    async def get_krw_markets(self) -> List[Dict[str, Any]]:
        """
        원화 마켓 목록 조회 (편의 메서드)

        Returns:
            List[Dict[str, Any]]: 원화 마켓 정보 리스트
        """
        all_markets = await self.get_markets()
        krw_markets = [market for market in all_markets if market['market'].startswith('KRW-')]

        self._logger.debug(f"💰 원화 마켓 조회 완료: {len(krw_markets)}개 마켓")
        return krw_markets

    async def get_btc_markets(self) -> List[Dict[str, Any]]:
        """
        비트코인 마켓 목록 조회 (편의 메서드)

        Returns:
            List[Dict[str, Any]]: 비트코인 마켓 정보 리스트
        """
        all_markets = await self.get_markets()
        btc_markets = [market for market in all_markets if market['market'].startswith('BTC-')]

        self._logger.debug(f"₿ 비트코인 마켓 조회 완료: {len(btc_markets)}개 마켓")
        return btc_markets

    async def get_market_summary(self, market: str) -> Dict[str, Any]:
        """
        마켓 종합 정보 조회 (편의 메서드)

        현재가, 호가, 최근 체결 정보를 한 번에 조회합니다.

        Args:
            market: 마켓 코드 (예: 'KRW-BTC')

        Returns:
            Dict[str, Any]: 마켓 종합 정보
                {
                    'market': 'KRW-BTC',
                    'ticker': {...},       # 현재가 정보
                    'orderbook': {...},    # 호가 정보
                    'recent_trades': [...] # 최근 체결 내역 (10개)
                }

        Raises:
            ValueError: 마켓 코드가 비어있는 경우
            Exception: API 오류
        """
        if not market:
            raise ValueError("마켓 코드는 필수입니다")

        # 병렬로 데이터 조회
        ticker_task = self.get_ticker(market)
        orderbook_task = self.get_orderbook(market)
        trades_task = self.get_trades(market, count=10)

        ticker_data, orderbook_data, trades_data = await asyncio.gather(
            ticker_task, orderbook_task, trades_task
        )

        summary = {
            'market': market,
            'ticker': ticker_data[0] if ticker_data else None,
            'orderbook': orderbook_data[0] if orderbook_data else None,
            'recent_trades': trades_data
        }

        self._logger.debug(f"📋 마켓 종합 정보 조회 완료: {market}")
        return summary


# ================================================================
# 편의 팩토리 함수
# ================================================================

def create_upbit_public_client(
    use_dynamic_limiter: bool = True,
    dynamic_config: Optional[DynamicConfig] = None,
    enable_gzip: bool = True
) -> UpbitPublicClient:
    """
    업비트 공개 API 클라이언트 생성 (편의 함수)

    Args:
        use_dynamic_limiter: 동적 Rate Limiter 사용 여부 (기본값: True)
        dynamic_config: 동적 조정 설정 (기본값: 균형 전략)
        enable_gzip: gzip 압축 사용 여부 (기본값: True, 대역폭 83% 절약)

    Returns:
        UpbitPublicClient: 설정된 클라이언트 인스턴스

    Examples:
        # 기본 설정으로 생성 (gzip 압축 포함)
        client = create_upbit_public_client()

        # 보수적 전략으로 생성
        config = DynamicConfig(strategy=AdaptiveStrategy.CONSERVATIVE)
        client = create_upbit_public_client(dynamic_config=config)

        # 레거시 Rate Limiter + gzip 비활성화
        client = create_upbit_public_client(use_dynamic_limiter=False, enable_gzip=False)
    """
    return UpbitPublicClient(
        use_dynamic_limiter=use_dynamic_limiter,
        dynamic_config=dynamic_config,
        enable_gzip=enable_gzip
    )


async def create_upbit_public_client_async(
    use_dynamic_limiter: bool = True,
    dynamic_config: Optional[DynamicConfig] = None,
    enable_gzip: bool = True
) -> UpbitPublicClient:
    """
    업비트 공개 API 클라이언트 비동기 생성 (편의 함수)

    Args:
        use_dynamic_limiter: 동적 Rate Limiter 사용 여부 (기본값: True)
        dynamic_config: 동적 조정 설정 (기본값: 균형 전략)
        enable_gzip: gzip 압축 사용 여부 (기본값: True, 대역폭 83% 절약)

    Returns:
        UpbitPublicClient: 초기화된 클라이언트 인스턴스

    Note:
        세션을 미리 초기화하여 첫 번째 요청 시 지연을 줄입니다.
        gzip 압축을 통해 데이터 전송량을 83% 절약할 수 있습니다.
    """
    client = UpbitPublicClient(
        use_dynamic_limiter=use_dynamic_limiter,
        dynamic_config=dynamic_config,
        enable_gzip=enable_gzip
    )

    # 세션 미리 초기화
    await client._ensure_session()

    return client
