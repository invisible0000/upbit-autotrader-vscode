import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RateLimitConfig:
    """API 호출 제한 설정"""
    requests_per_second: int = 10
    requests_per_minute: int = 600
    burst_limit: int = 100

@dataclass
class ApiResponse:
    """API 응답 래퍼"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    request_time: datetime
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None

class RateLimiter:
    """API 호출 제한 관리 - 기존 UpbitAPI 로직 기반"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._second_requests: List[float] = []
        self._minute_requests: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """API 호출 권한 획득 - 기존 _check_rate_limit 로직 기반"""
        async with self._lock:
            now = time.time()

            # 1분 이상 지난 타임스탬프 제거 (기존 로직 보존)
            self._minute_requests = [ts for ts in self._minute_requests if now - ts < 60]

            # 분당 요청 제한 확인 (기존 로직 보존)
            if len(self._minute_requests) >= self.config.requests_per_minute:
                oldest = self._minute_requests[0]
                sleep_time = 60 - (now - oldest)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    # 대기 후 타임스탬프 갱신
                    self._minute_requests = [ts for ts in self._minute_requests if time.time() - ts < 60]
                    self._minute_requests.append(time.time())
                    return

            # 초당 요청 제한 확인 (기존 로직 보존)
            self._second_requests = [ts for ts in self._second_requests if now - ts < 1]
            if len(self._second_requests) >= self.config.requests_per_second:
                sleep_time = 1.0
                await asyncio.sleep(sleep_time)

            # 현재 요청 타임스탬프 추가 (기존 로직 보존)
            self._minute_requests.append(time.time())

class BaseApiClient(ABC):
    """API 클라이언트 기본 클래스"""

    def __init__(self, base_url: str, rate_limit_config: RateLimitConfig,
                 timeout: int = 30, max_retries: int = 3):
        self._base_url = base_url.rstrip('/')
        self._rate_limiter = RateLimiter(rate_limit_config)
        self._timeout = timeout
        self._max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
        self._logger = logging.getLogger(self.__class__.__name__)

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self._session:
            await self._session.close()
            self._session = None

    async def _ensure_session(self) -> None:
        """HTTP 세션 확보 - 기존 _create_session 로직 기반"""
        if self._session is None or self._session.closed:
            # 기존 재시도 전략을 aiohttp에 맞게 적용
            connector = aiohttp.TCPConnector(
                limit=100,  # 최대 연결 수
                limit_per_host=30,  # 호스트당 최대 연결 수
                ttl_dns_cache=300,  # DNS 캐시 시간
                use_dns_cache=True
            )

            timeout = aiohttp.ClientTimeout(
                total=self._timeout,
                connect=5  # 기존 연결 타임아웃 5초 보존
            )

            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'UpbitAutoTrader/1.0'}
            )

    async def _make_request(self, method: str, endpoint: str,
                            params: Optional[Dict] = None,
                            data: Optional[Dict] = None,
                            headers: Optional[Dict] = None) -> ApiResponse:
        """HTTP 요청 실행 - 기존 _request 로직 기반"""
        url = f"{self._base_url}{endpoint}"

        # Rate limiting 적용 (기존 로직 보존)
        await self._rate_limiter.acquire()

        # 재시도 로직 (기존 로직 기반)
        last_exception = None
        for attempt in range(self._max_retries + 1):
            try:
                start_time = time.time()
                request_time = datetime.now()

                await self._ensure_session()

                # 요청 헤더 준비
                request_headers = self._prepare_headers(method, endpoint, params, data)
                if headers:
                    request_headers.update(headers)

                # HTTP 요청 실행
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
                        request_time=request_time,
                        response_time_ms=response_time_ms,
                        success=200 <= response.status < 300
                    )

                    if not api_response.success:
                        api_response.error_message = self._extract_error_message(response_data)

                    self._log_request(method, url, api_response, attempt)

                    if api_response.success:
                        return api_response
                    elif response.status in [429, 503, 504]:  # 재시도 가능한 오류
                        if attempt < self._max_retries:
                            await self._handle_retryable_error(response.status, attempt)
                            continue

                    return api_response

            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self._max_retries:
                    # 기존 점진적 대기 시간 증가 로직 보존
                    retry_delay = (self._max_retries - attempt) * 2
                    await asyncio.sleep(retry_delay)
                    continue

            except aiohttp.ClientError as e:
                last_exception = e
                if attempt < self._max_retries:
                    retry_delay = (self._max_retries - attempt) * 2
                    await asyncio.sleep(retry_delay)
                    continue

        # 모든 재시도 실패
        return ApiResponse(
            status_code=0,
            data=None,
            headers={},
            request_time=datetime.now(),
            response_time_ms=0,
            success=False,
            error_message=f"요청 실패 (재시도 {self._max_retries}회): {str(last_exception)}"
        )

    @abstractmethod
    def _prepare_headers(self, method: str, endpoint: str,
                        params: Optional[Dict], data: Optional[Dict]) -> Dict[str, str]:
        """요청 헤더 준비 (인증 등)"""
        pass

    def _extract_error_message(self, response_data: Any) -> str:
        """API 응답에서 에러 메시지 추출"""
        if isinstance(response_data, dict):
            return response_data.get('error', {}).get('message', 'Unknown error')
        return str(response_data)

    async def _handle_retryable_error(self, status_code: int, attempt: int) -> None:
        """재시도 가능한 오류 처리 - 기존 429 처리 로직 기반"""
        if status_code == 429:  # Rate limit exceeded
            sleep_time = min(60, (2 ** attempt) * 5)  # 최대 60초
        else:  # 503, 504 등 서버 오류
            sleep_time = 2 ** attempt

        self._logger.warning(f"재시도 가능한 오류 {status_code}, {sleep_time}초 대기")
        await asyncio.sleep(sleep_time)

    def _log_request(self, method: str, url: str, response: ApiResponse, attempt: int) -> None:
        """요청 로깅"""
        log_msg = (
            f"{method} {url} -> {response.status_code} "
            f"({response.response_time_ms:.1f}ms, 시도 {attempt + 1})"
        )

        if response.success:
            self._logger.debug(log_msg)
        else:
            self._logger.warning(f"{log_msg} - {response.error_message}")

    async def close(self):
        """리소스 정리"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        if hasattr(self, '_rate_limiter') and self._rate_limiter:
            # rate limiter에 정리할 리소스가 있다면 정리
            pass

class ApiClientError(Exception):
    """API 클라이언트 예외"""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_data: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class AuthenticationError(ApiClientError):
    """인증 오류"""
    pass

class RateLimitError(ApiClientError):
    """API 호출 제한 오류"""
    pass

class NetworkError(ApiClientError):
    """네트워크 오류"""
    pass
