"""
거래소 중립적 베이스 클라이언트

어댑터 패턴을 활용한 확장 가능한 API 클라이언트 구조
"""
import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
from datetime import datetime

from .data_models import ApiResponse, UnifiedResponse
from .rate_limiter import UniversalRateLimiter


class BaseExchangeClient(ABC):
    """
    거래소 중립적 베이스 클라이언트

    어댑터 패턴을 통해 거래소별 특화 로직을 분리하고
    통일된 인터페이스를 제공
    """

    def __init__(self, adapter: Any, rate_limiter: UniversalRateLimiter,
                 timeout: int = 30, max_retries: int = 3):
        self.adapter = adapter
        self.rate_limiter = rate_limiter
        self.timeout = timeout
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
        # 세션은 첫 요청 시 자동 초기화

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self) -> None:
        """HTTP 세션 확보"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': f'{self.adapter.exchange_name.title()}AutoTrader/1.0'}
            )

    # ================================================================
    # 핵심 통합 요청 메서드
    # ================================================================

    async def _make_unified_request(
        self,
        endpoint: str,
        symbols: Union[str, List[str]],
        method: str = 'GET',
        **kwargs
    ) -> UnifiedResponse:
        """
        통합 요청 처리기 - 어댑터 기반

        Args:
            endpoint: API 엔드포인트
            symbols: 요청할 심볼(들)
            method: HTTP 메서드
            **kwargs: 추가 파라미터

        Returns:
            UnifiedResponse: 통일된 응답
        """
        try:
            # 1. 입력 정규화
            from ..adapters.base_adapter import InputTypeHandler, ResponseNormalizer
            symbols_list, was_single = InputTypeHandler.normalize_symbol_input(symbols)

            # 2. 배치 vs 개별 처리 결정
            if (self.adapter.supports_batch(endpoint)
                    and len(symbols_list) <= self.adapter.get_max_batch_size(endpoint)):

                # 배치 처리
                response_data = await self._handle_batch_request(
                    endpoint, symbols_list, method, **kwargs
                )
            else:
                # 개별 처리
                response_data = await self._handle_individual_requests(
                    endpoint, symbols_list, method, **kwargs
                )

            # 3. 어댑터를 통한 응답 파싱
            parsed_data = self._parse_response_via_adapter(
                response_data, endpoint, symbols_list, **kwargs
            )

            # 4. 통합 응답 형식으로 변환
            unified_dict = ResponseNormalizer.normalize_to_dict(
                parsed_data, symbols_list, self._get_symbol_key_field(endpoint)
            )

            # print(f"[DEBUG] 정규화된 Dict: {unified_dict}")

            # 5. 최종 응답 생성
            final_data = InputTypeHandler.format_output(
                unified_dict, was_single, symbols_list[0] if symbols_list else None
            )

            # print(f"[DEBUG] 최종 데이터: {final_data}")

            return UnifiedResponse(
                success=True,
                data=final_data,
                metadata={
                    'request_symbols': symbols_list,
                    'response_count': len(unified_dict) if isinstance(unified_dict, dict) else 0,
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': endpoint,
                    'exchange': self.adapter.exchange_name
                },
                exchange=self.adapter.exchange_name
            )

        except Exception as e:
            return UnifiedResponse(
                success=False,
                data={},
                metadata={'error': str(e), 'symbols': symbols},
                error=str(e),
                exchange=self.adapter.exchange_name
            )

    async def _handle_batch_request(
        self, endpoint: str, symbols: List[str], method: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """배치 요청 처리"""
        params = self.adapter.build_batch_params(symbols, endpoint)
        params.update(kwargs.get('params', {}))

        response = await self._make_request(method, endpoint, params=params)
        if response.success and isinstance(response.data, list):
            return response.data
        return []

    async def _handle_individual_requests(
        self, endpoint: str, symbols: List[str], method: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """개별 요청 처리"""
        tasks = []
        for symbol in symbols:
            params = self.adapter.build_single_params(symbol, endpoint, **kwargs)
            # print(f"[DEBUG] 개별 요청 - 심볼: {symbol}, 엔드포인트: {endpoint}, 파라미터: {params}")
            task = self._make_request(method, endpoint, params=params)
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        # print(f"[DEBUG] 개별 응답 개수: {len(responses)}")

        results = []
        for i, response in enumerate(responses):
            # print(f"[DEBUG] 응답 {i}: 타입={type(response)}, 성공={getattr(response, 'success', 'N/A')}")
            if isinstance(response, Exception):
                # print(f"[DEBUG] 예외 발생: {response}")
                continue

            if isinstance(response, ApiResponse) and response.success:
                # print(f"[DEBUG] 성공 응답 데이터: {response.data}")
                if isinstance(response.data, list):
                    results.extend(response.data)
                else:
                    results.append(response.data)
            else:
                # print(f"[DEBUG] 실패 응답: {getattr(response, 'error_message', 'Unknown error')}")
                continue

        # print(f"[DEBUG] 최종 결과 개수: {len(results)}")
        return results

    def _parse_response_via_adapter(
        self, raw_data: List[Dict[str, Any]], endpoint: str,
        symbols: List[str], **kwargs
    ) -> List[Any]:
        """어댑터를 통한 응답 파싱 - 현재는 원본 데이터 반환"""
        # 표준화된 객체 변환은 나중에 필요할 때 사용
        # 현재는 기존 인터페이스와의 호환성을 위해 원본 데이터 반환
        return raw_data

    def _get_symbol_key_field(self, endpoint: str) -> str:
        """엔드포인트별 심볼 키 필드 반환"""
        # 어댑터의 메타데이터를 활용
        return self.adapter.metadata.get_field_mapping('symbol')

    # ================================================================
    # 기본 HTTP 요청 처리
    # ================================================================

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> ApiResponse:
        """기본 HTTP 요청"""
        url = f"{self.adapter.get_base_url()}{endpoint}"

        # Rate limiting
        await self.rate_limiter.acquire()

        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                await self._ensure_session()

                if self._session is None:
                    raise RuntimeError("세션 초기화 실패")

                request_headers = self._prepare_headers(method, endpoint, params, data)
                if headers:
                    request_headers.update(headers)

                async with self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers
                ) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    response_data = await response.json()

                    api_response = ApiResponse(
                        status_code=response.status,
                        data=response_data,
                        headers=dict(response.headers),
                        response_time_ms=response_time_ms,
                        success=200 <= response.status < 300,
                        exchange=self.adapter.exchange_name
                    )

                    if not api_response.success:
                        api_response.error_message = self.adapter.parse_error_response(
                            response_data, response.status
                        )
                    else:
                        self.rate_limiter.update_from_server_headers(api_response.headers)

                    return api_response

            except Exception as e:
                if attempt == self.max_retries:
                    return ApiResponse(
                        status_code=0,
                        data=None,
                        headers={},
                        response_time_ms=0,
                        success=False,
                        error_message=str(e),
                        exchange=self.adapter.exchange_name
                    )
                await asyncio.sleep(2 ** attempt)

        # 모든 재시도 실패 시 기본 응답 반환
        return ApiResponse(
            status_code=0,
            data=None,
            headers={},
            response_time_ms=0,
            success=False,
            error_message="모든 재시도 실패",
            exchange=self.adapter.exchange_name
        )

    @abstractmethod
    def _prepare_headers(self, method: str, endpoint: str,
                         params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """요청 헤더 준비 (서브클래스에서 구현)"""
        pass

    async def close(self):
        """리소스 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


# ================================================================
# 거래소별 클라이언트 팩토리
# ================================================================

class ExchangeClientFactory:
    """거래소별 클라이언트 생성 팩토리"""

    @staticmethod
    def create_public_client(exchange: str) -> 'BaseExchangeClient':
        """거래소별 공개 API 클라이언트 생성"""
        from .rate_limiter import RateLimiterFactory

        exchange_lower = exchange.lower()

        if exchange_lower == 'upbit':
            from ..adapters.upbit_adapter import UpbitAdapter
            from ..upbit.upbit_public_client_v2 import UpbitPublicClientV2

            adapter = UpbitAdapter()
            rate_limiter = RateLimiterFactory.create_for_exchange('upbit', 'public')
            return UpbitPublicClientV2(adapter, rate_limiter)

        # elif exchange_lower == 'binance':
        #     from ..adapters.binance_adapter import BinanceAdapter
        #     from ..binance.binance_public_client import BinancePublicClient
        #     adapter = BinanceAdapter()
        #     rate_limiter = RateLimiterFactory.create_for_exchange('binance', 'public')
        #     return BinancePublicClient(adapter, rate_limiter)

        else:
            raise ValueError(f"지원하지 않는 거래소: {exchange}")

    @staticmethod
    def get_supported_exchanges() -> List[str]:
        """지원하는 거래소 목록"""
        return ['upbit']  # 향후 확장: ['upbit', 'binance', 'okx']
