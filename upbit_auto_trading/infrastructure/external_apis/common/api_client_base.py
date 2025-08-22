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
    """API 호출 제한 설정 - 업비트 공식 정책 기반"""
    requests_per_second: int = 10
    requests_per_minute: int = 600
    burst_limit: int = 100

    @classmethod
    def upbit_public_api(cls) -> 'RateLimitConfig':
        """업비트 공개 API 제한 (시세 조회)"""
        return cls(
            requests_per_second=10,
            requests_per_minute=600,
            burst_limit=50
        )

    @classmethod
    def upbit_private_api(cls) -> 'RateLimitConfig':
        """업비트 프라이빗 API 제한 (주문, 계좌)"""
        return cls(
            requests_per_second=8,      # 주문 API 더 엄격
            requests_per_minute=200,
            burst_limit=30
        )

    @classmethod
    def upbit_websocket_connect(cls) -> 'RateLimitConfig':
        """업비트 WebSocket 연결 제한"""
        return cls(
            requests_per_second=5,      # WebSocket 연결
            requests_per_minute=100,
            burst_limit=20
        )

    @classmethod
    def upbit_websocket_message(cls) -> 'RateLimitConfig':
        """업비트 WebSocket 메시지 제한"""
        return cls(
            requests_per_second=50,     # 연결 후 메시지는 관대
            requests_per_minute=1000,
            burst_limit=200
        )


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
    """
    API 호출 제한 관리자
    - Smart Router의 기능을 통합
    - 업비트 공식 정책 준수
    - 적응형 백오프 지원
    - 서버 헤더 기반 동적 조정
    """

    def __init__(self, config: RateLimitConfig, client_id: Optional[str] = None):
        self.config = config
        self.client_id = client_id or f"client_{id(self)}"

        # 기본 Rate Limit 추적
        self._second_requests: List[float] = []
        self._minute_requests: List[float] = []
        self._lock = asyncio.Lock()

        # Smart Router 호환 기능
        self._current_requests = 0
        self._window_start_time = time.time()
        self._throttled_until = 0.0

        # 적응형 백오프
        self._consecutive_limits = 0
        self._backoff_multiplier = 1.0

        # 서버 헤더 기반 조정
        self._server_limit: Optional[int] = None
        self._server_remaining: Optional[int] = None
        self._server_reset_time: Optional[float] = None

        self._logger = logging.getLogger(f"RateLimiter.{self.client_id}")

    async def acquire(self) -> None:
        """API 호출 권한 획득 - 모든 제한 정책 통합 적용"""
        async with self._lock:
            await self._wait_if_throttled()
            await self._enforce_rate_limits()
            self._record_request()

    async def _wait_if_throttled(self) -> None:
        """스로틀링 상태면 대기"""
        if time.time() < self._throttled_until:
            wait_time = self._throttled_until - time.time()
            self._logger.warning(f"Rate limit 스로틀링 대기: {wait_time:.2f}초")
            await asyncio.sleep(wait_time)

    async def _enforce_rate_limits(self) -> None:
        """초당/분당 제한 강제 적용"""
        now = time.time()

        # 서버 기반 제한 우선 적용
        if self._server_remaining is not None and self._server_remaining <= 0:
            if self._server_reset_time and now < self._server_reset_time:
                wait_time = self._server_reset_time - now
                self._logger.warning(f"서버 제한 대기: {wait_time:.2f}초")
                await asyncio.sleep(wait_time)
                return

        # 기본 제한 정책 적용
        await self._enforce_per_minute_limit(now)
        await self._enforce_per_second_limit(now)

    async def _enforce_per_minute_limit(self, now: float) -> None:
        """분당 제한 강제"""
        # 1분 이상 지난 요청 제거
        self._minute_requests = [ts for ts in self._minute_requests if now - ts < 60]

        if len(self._minute_requests) >= self.config.requests_per_minute:
            oldest = self._minute_requests[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                self._apply_backoff()
                adjusted_wait = wait_time * self._backoff_multiplier
                self._logger.warning(f"분당 제한 대기: {adjusted_wait:.2f}초 (백오프: {self._backoff_multiplier:.1f}x)")
                await asyncio.sleep(adjusted_wait)

    async def _enforce_per_second_limit(self, now: float) -> None:
        """초당 제한 강제"""
        # 1초 이상 지난 요청 제거
        self._second_requests = [ts for ts in self._second_requests if now - ts < 1]

        if len(self._second_requests) >= self.config.requests_per_second:
            self._apply_backoff()
            wait_time = 1.0 * self._backoff_multiplier
            self._logger.warning(f"초당 제한 대기: {wait_time:.2f}초")
            await asyncio.sleep(wait_time)

    def _record_request(self) -> None:
        """요청 기록"""
        now = time.time()
        self._second_requests.append(now)
        self._minute_requests.append(now)

        # Smart Router 호환 카운터 업데이트
        if now - self._window_start_time >= 60:
            self._current_requests = 0
            self._window_start_time = now
        self._current_requests += 1

    def _apply_backoff(self) -> None:
        """적응형 백오프 적용"""
        self._consecutive_limits += 1
        self._backoff_multiplier = min(3.0, 1.0 + (self._consecutive_limits * 0.2))

        # 연속 제한 도달 시 스로틀링 시간 설정
        if self._consecutive_limits >= 3:
            self._throttled_until = time.time() + (self._consecutive_limits * 2)

    def update_from_server_headers(self, headers: Dict[str, str]) -> None:
        """서버 응답 헤더로 제한 상태 업데이트 (Smart Router 호환)"""
        # 업비트 'Remaining-Req' 헤더 파싱
        remaining_req = headers.get('Remaining-Req') or headers.get('remaining-req')
        if remaining_req:
            try:
                parts = remaining_req.split(':')
                if len(parts) >= 2:
                    self._server_limit = int(parts[0])
                    self._server_remaining = int(parts[1])

                    # 리셋 시간이 있으면 설정
                    if len(parts) >= 3:
                        reset_seconds = int(parts[2])
                        self._server_reset_time = time.time() + reset_seconds

                    # 성공적인 요청이므로 백오프 리셋
                    self._reset_backoff()

                    self._logger.debug(f"서버 제한 업데이트: {self._server_remaining}/{self._server_limit}")

            except (ValueError, IndexError) as e:
                self._logger.warning(f"서버 헤더 파싱 실패: {remaining_req}, 오류: {e}")

    def _reset_backoff(self) -> None:
        """백오프 상태 리셋"""
        self._consecutive_limits = 0
        self._backoff_multiplier = 1.0
        self._throttled_until = 0.0

    def allow_request(self, cost: int = 1) -> bool:
        """요청 허용 여부 확인 (Smart Router 호환 메서드)"""
        now = time.time()

        # 스로틀링 중이면 거부
        if now < self._throttled_until:
            return False

        # 서버 제한 확인
        if self._server_remaining is not None:
            return self._server_remaining >= cost

        # 기본 제한 확인
        second_count = len([ts for ts in self._second_requests if now - ts < 1])
        minute_count = len([ts for ts in self._minute_requests if now - ts < 60])

        return (second_count + cost <= self.config.requests_per_second and
                minute_count + cost <= self.config.requests_per_minute)

    def get_status(self) -> Dict[str, Any]:
        """현재 Rate Limit 상태 조회"""
        now = time.time()
        second_count = len([ts for ts in self._second_requests if now - ts < 1])
        minute_count = len([ts for ts in self._minute_requests if now - ts < 60])

        return {
            'client_id': self.client_id,
            'config': {
                'requests_per_second': self.config.requests_per_second,
                'requests_per_minute': self.config.requests_per_minute,
                'burst_limit': self.config.burst_limit
            },
            'current_usage': {
                'second': second_count,
                'minute': minute_count,
                'second_percent': (second_count / self.config.requests_per_second) * 100,
                'minute_percent': (minute_count / self.config.requests_per_minute) * 100
            },
            'server_info': {
                'limit': self._server_limit,
                'remaining': self._server_remaining,
                'reset_time': self._server_reset_time
            },
            'backoff': {
                'consecutive_limits': self._consecutive_limits,
                'multiplier': self._backoff_multiplier,
                'throttled_until': self._throttled_until
            }
        }


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
        """HTTP 세션 확보 - 이벤트 루프별 세션 관리"""
        # 현재 이벤트 루프 확인
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            # 실행 중인 루프가 없는 경우
            current_loop = None

        # 세션이 없거나, 닫혔거나, 다른 루프에서 생성된 경우 새로 생성
        session_invalid = (
            self._session is None
            or self._session.closed
            or (current_loop and getattr(self._session, '_loop', None) != current_loop)
        )

        if session_invalid:
            # 기존 세션이 있고 닫히지 않았다면 정리
            if self._session and not self._session.closed:
                try:
                    await self._session.close()
                except Exception:
                    pass  # 정리 중 에러는 무시

            # 새로운 세션 생성
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

                    # 성공 시 서버 헤더로 Rate Limit 상태 업데이트
                    if api_response.success:
                        self._rate_limiter.update_from_server_headers(api_response.headers)
                        return api_response
                    elif response.status in [429, 503, 504]:  # 재시도 가능한 오류
                        # 429 오류 시에도 헤더 정보 활용
                        self._rate_limiter.update_from_server_headers(api_response.headers)
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
