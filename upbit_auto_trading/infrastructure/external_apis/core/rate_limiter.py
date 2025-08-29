"""
거래소 중립적 범용 Rate Limiter

각 거래소별 설정과 헤더 파싱을 지원하는 확장 가능한 구조
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class ExchangeRateLimitConfig:
    """거래소별 Rate Limit 설정"""
    requests_per_second: int
    requests_per_minute: int
    exchange_name: str
    header_parser: Optional[Callable[[Dict[str, str]], Dict[str, Any]]] = None

    @classmethod
    def for_upbit_public(cls) -> 'ExchangeRateLimitConfig':
        """업비트 공개 API 설정 (업비트 공식 문서 기준)"""
        return cls(
            requests_per_second=10,  # Quotation 그룹: 초당 10회
            requests_per_minute=600,  # 분당 600회 (안전 마진)
            exchange_name='upbit_public',
            header_parser=cls._parse_upbit_headers
        )

    @classmethod
    def for_upbit_private(cls) -> 'ExchangeRateLimitConfig':
        """업비트 프라이빗 API 설정 (업비트 공식 문서 기준)"""
        return cls(
            requests_per_second=8,   # Exchange order 그룹: 초당 8회 (주문 생성)
            requests_per_minute=200,  # 분당 200회 (안전 마진)
            exchange_name='upbit_private',
            header_parser=cls._parse_upbit_headers
        )

    @classmethod
    def for_upbit_exchange_default(cls) -> 'ExchangeRateLimitConfig':
        """업비트 Exchange Default 그룹 (조회 API)"""
        return cls(
            requests_per_second=30,  # Exchange default 그룹: 초당 30회
            requests_per_minute=1800,  # 분당 1800회
            exchange_name='upbit_exchange_default',
            header_parser=cls._parse_upbit_headers
        )

    @classmethod
    def for_upbit_websocket_connect(cls) -> 'ExchangeRateLimitConfig':
        """업비트 WebSocket 연결 (업비트 공식 문서 기준)"""
        return cls(
            requests_per_second=5,   # WebSocket 연결: 초당 5회
            requests_per_minute=100,  # 분당 100회 (안전 마진)
            exchange_name='upbit_websocket_connect',
            header_parser=cls._parse_upbit_headers
        )

    @classmethod
    def for_upbit_websocket_message(cls) -> 'ExchangeRateLimitConfig':
        """업비트 WebSocket 메시지 (업비트 공식 문서 기준)"""
        return cls(
            requests_per_second=5,   # WebSocket 메시지: 초당 5회
            requests_per_minute=100,  # WebSocket 메시지: 분당 100회
            exchange_name='upbit_websocket_message',
            header_parser=cls._parse_upbit_headers
        )

    @classmethod
    def for_binance_public(cls) -> 'ExchangeRateLimitConfig':
        """바이낸스 공개 API 설정 (예시)"""
        return cls(
            requests_per_second=20,
            requests_per_minute=1200,
            exchange_name='binance',
            header_parser=cls._parse_binance_headers
        )

    @staticmethod
    def _parse_upbit_headers(headers: Dict[str, str]) -> Dict[str, Any]:
        """업비트 헤더 파싱"""
        remaining_req = headers.get('Remaining-Req') or headers.get('remaining-req')
        if remaining_req:
            try:
                parts = remaining_req.split(':')
                if len(parts) >= 2:
                    return {
                        'limit': int(parts[0]),
                        'remaining': int(parts[1]),
                        'reset_time': int(parts[2]) if len(parts) >= 3 else None
                    }
            except (ValueError, IndexError):
                pass
        return {}

    @staticmethod
    def _parse_binance_headers(headers: Dict[str, str]) -> Dict[str, Any]:
        """바이낸스 헤더 파싱 (예시)"""
        # 바이낸스는 X-MBX-USED-WEIGHT 등 사용
        used_weight = headers.get('X-MBX-USED-WEIGHT')
        if used_weight:
            try:
                return {
                    'used_weight': int(used_weight),
                    'remaining': 1200 - int(used_weight)  # 기본 제한에서 차감
                }
            except ValueError:
                pass
        return {}


class UniversalRateLimiter:
    """
    거래소 중립적 범용 Rate Limiter

    특징:
    - 거래소별 설정 지원
    - 거래소별 헤더 파싱 로직
    - 적응형 백오프
    - 서버 제한 자동 조정
    """

    def __init__(self, config: ExchangeRateLimitConfig, client_id: Optional[str] = None):
        self.config = config
        self.client_id = client_id or f"{config.exchange_name}_client_{id(self)}"

        # 기본 Rate Limit 추적
        self._second_requests: List[float] = []
        self._minute_requests: List[float] = []
        self._lock = asyncio.Lock()

        # 거래소별 서버 제한 추적
        self._server_limit: Optional[int] = None
        self._server_remaining: Optional[int] = None
        self._server_reset_time: Optional[float] = None

        # 적응형 백오프
        self._consecutive_limits = 0
        self._backoff_multiplier = 1.0
        self._throttled_until = 0.0

        self._logger = logging.getLogger(f"RateLimiter.{self.client_id}")

    async def acquire(self) -> None:
        """API 호출 권한 획득"""
        async with self._lock:
            await self._wait_if_throttled()
            await self._enforce_rate_limits()
            self._record_request()

    async def _wait_if_throttled(self) -> None:
        """스로틀링 상태면 대기"""
        if time.time() < self._throttled_until:
            wait_time = self._throttled_until - time.time()
            self._logger.warning(
                f"[{self.config.exchange_name}] Rate limit 스로틀링 대기: {wait_time:.2f}초"
            )
            await asyncio.sleep(wait_time)

    async def _enforce_rate_limits(self) -> None:
        """초당/분당 제한 강제 적용"""
        now = time.time()

        # 서버 기반 제한 우선 적용
        if self._server_remaining is not None and self._server_remaining <= 0:
            if self._server_reset_time and now < self._server_reset_time:
                wait_time = self._server_reset_time - now
                self._logger.warning(
                    f"[{self.config.exchange_name}] 서버 제한 대기: {wait_time:.2f}초"
                )
                await asyncio.sleep(wait_time)
                return

        # 기본 제한 정책 적용
        await self._enforce_per_minute_limit(now)
        await self._enforce_per_second_limit(now)

    async def _enforce_per_minute_limit(self, now: float) -> None:
        """분당 제한 강제 (1초 내 통신 완료 규칙 준수)"""
        # 1분 이상 지난 요청 제거
        self._minute_requests = [ts for ts in self._minute_requests if now - ts < 60]

        if len(self._minute_requests) >= self.config.requests_per_minute:
            oldest = self._minute_requests[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                self._apply_backoff()

                # 1초 내 통신 완료 규칙: 분당 제한 시에도 최대 0.9초로 제한
                adjusted_wait = wait_time * self._backoff_multiplier
                max_wait = min(adjusted_wait, 0.9)  # 최대 0.9초로 제한

                self._logger.warning(
                    f"[{self.config.exchange_name}] 분당 제한 대기: {max_wait:.2f}초 "
                    f"(1초 규칙 준수, 원래: {adjusted_wait:.2f}초)"
                )
                await asyncio.sleep(max_wait)

    async def _enforce_per_second_limit(self, now: float) -> None:
        """초당 제한 강제 (1초 내 통신 완료 규칙 준수)"""
        # 1초 이상 지난 요청 제거
        self._second_requests = [ts for ts in self._second_requests if now - ts < 1]

        if len(self._second_requests) >= self.config.requests_per_second:
            self._apply_backoff()

            # 1초 내 통신 완료 규칙: 최대 대기시간 0.8초로 제한
            base_wait = 1.0 / self.config.requests_per_second  # 기본 간격
            backoff_wait = base_wait * self._backoff_multiplier
            wait_time = min(backoff_wait, 0.8)  # 최대 0.8초로 제한

            self._logger.warning(
                f"[{self.config.exchange_name}] 초당 제한 대기: {wait_time:.2f}초 "
                f"(1초 규칙 준수)"
            )
            await asyncio.sleep(wait_time)

    def _record_request(self) -> None:
        """요청 기록"""
        now = time.time()
        self._second_requests.append(now)
        self._minute_requests.append(now)

    def _apply_backoff(self) -> None:
        """적응형 백오프 적용"""
        self._consecutive_limits += 1
        self._backoff_multiplier = min(3.0, 1.0 + (self._consecutive_limits * 0.2))

        # 연속 제한 도달 시 스로틀링 시간 설정
        if self._consecutive_limits >= 3:
            self._throttled_until = time.time() + (self._consecutive_limits * 2)
            self._logger.warning(
                f"[{self.config.exchange_name}] 연속 제한 {self._consecutive_limits}회, "
                f"스로틀링 적용: {self._consecutive_limits * 2}초"
            )

    def update_from_server_headers(self, headers: Dict[str, str]) -> None:
        """서버 응답 헤더로 제한 상태 업데이트"""
        if self.config.header_parser:
            parsed_data = self.config.header_parser(headers)

            if parsed_data:
                if 'limit' in parsed_data:
                    self._server_limit = parsed_data['limit']
                if 'remaining' in parsed_data:
                    self._server_remaining = parsed_data['remaining']
                if 'reset_time' in parsed_data and parsed_data['reset_time']:
                    self._server_reset_time = time.time() + parsed_data['reset_time']

                # 성공적인 요청이므로 백오프 리셋
                self._reset_backoff()

                self._logger.debug(
                    f"[{self.config.exchange_name}] 서버 제한 업데이트: "
                    f"{self._server_remaining}/{self._server_limit}"
                )

    def _reset_backoff(self) -> None:
        """백오프 상태 리셋"""
        self._consecutive_limits = 0
        self._backoff_multiplier = 1.0
        self._throttled_until = 0.0

    def allow_request(self, cost: int = 1) -> bool:
        """요청 허용 여부 확인"""
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

        return (second_count + cost <= self.config.requests_per_second
                and minute_count + cost <= self.config.requests_per_minute)

    def get_status(self) -> Dict[str, Any]:
        """현재 Rate Limit 상태 조회"""
        now = time.time()
        second_count = len([ts for ts in self._second_requests if now - ts < 1])
        minute_count = len([ts for ts in self._minute_requests if now - ts < 60])

        return {
            'client_id': self.client_id,
            'exchange': self.config.exchange_name,
            'config': {
                'requests_per_second': self.config.requests_per_second,
                'requests_per_minute': self.config.requests_per_minute
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


class RateLimiterFactory:
    """Rate Limiter 팩토리"""

    @staticmethod
    def create_for_exchange(exchange: str, api_type: str, client_id: Optional[str] = None) -> UniversalRateLimiter:
        """거래소별 Rate Limiter 생성 (업비트 공식 규격 반영)"""
        config_map = {
            'upbit': {
                'public': ExchangeRateLimitConfig.for_upbit_public(),
                'private': ExchangeRateLimitConfig.for_upbit_private(),
                'exchange_default': ExchangeRateLimitConfig.for_upbit_exchange_default(),
                'websocket_connect': ExchangeRateLimitConfig.for_upbit_websocket_connect(),
                'websocket_message': ExchangeRateLimitConfig.for_upbit_websocket_message()
            },
            'binance': {
                'public': ExchangeRateLimitConfig.for_binance_public(),
                'private': ExchangeRateLimitConfig.for_binance_public()  # 임시로 같은 설정 사용
            }
        }

        exchange_lower = exchange.lower()
        if exchange_lower not in config_map:
            raise ValueError(f"지원하지 않는 거래소: {exchange}")

        if api_type not in config_map[exchange_lower]:
            raise ValueError(f"{exchange}에서 지원하지 않는 API 타입: {api_type}")

        config = config_map[exchange_lower][api_type]
        return UniversalRateLimiter(config, client_id)
