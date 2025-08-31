"""
업비트 통합 Rate Limiter - GCRA 알고리즘 기반
전문가 제안 2 구현: Asyncio 전역 싱글톤 + GCRA

Design Principles:
1. 표준 라이브러리만 사용 (asyncio, time, threading)
2. 업비트 5개 그룹 + WebSocket 이중 윈도우 지원
3. 전역 공유로 IP 기반 제한 준수
4. GCRA(Generic Cell Rate Algorithm) 정확성
5. DDD Infrastructure 계층 준수
"""
import asyncio
import time
import random
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger


class UpbitRateLimitGroup(Enum):
    """업비트 API Rate Limit 그룹 (공식 문서 기준)"""
    REST_PUBLIC = "rest_public"              # 10 RPS
    REST_PRIVATE_DEFAULT = "rest_private_default"  # 30 RPS
    REST_PRIVATE_ORDER = "rest_private_order"      # 8 RPS
    REST_PRIVATE_CANCEL_ALL = "rest_private_cancel_all"  # 0.5 RPS (2초당 1회)
    WEBSOCKET = "websocket"                  # 5 RPS AND 100 RPM


@dataclass
class GCRAConfig:
    """GCRA(Generic Cell Rate Algorithm) 설정"""
    T_seconds: float  # 토큰 간격 (1/RPS)
    slack_ratio: float = 0.0  # 여유분 비율 (0~1)

    @classmethod
    def from_rps(cls, rps: float, slack_ratio: float = 0.0) -> 'GCRAConfig':
        """RPS로부터 GCRA 설정 생성"""
        return cls(T_seconds=1.0 / rps, slack_ratio=slack_ratio)

    @classmethod
    def from_interval(cls, interval_seconds: float, slack_ratio: float = 0.0) -> 'GCRAConfig':
        """간격(초)으로부터 GCRA 설정 생성"""
        return cls(T_seconds=interval_seconds, slack_ratio=slack_ratio)


class GCRA:
    """
    Generic Cell Rate Algorithm 구현

    상태 1개(TAT)로 간격 제어하는 정확하고 단순한 알고리즘
    Leaky Bucket과 등가하지만 더 효율적임
    """

    def __init__(self, config: GCRAConfig):
        self.T = config.T_seconds
        self.slack = self.T * config.slack_ratio
        self.tat = 0.0  # Theoretical Arrival Time (monotonic time)

    def need_wait(self, now: float) -> float:
        """지금 요청하려면 추가로 기다려야 하는 시간(초). 0 이하면 즉시 가능."""
        allow_at = self.tat - self.slack
        if now >= allow_at:
            return 0.0
        return allow_at - now

    def consume(self, now: float) -> None:
        """토큰 소비 (호출 전 need_wait(now) == 0 이어야 함)"""
        self.tat = max(now, self.tat) + self.T

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        now = time.monotonic()
        return {
            'tat': self.tat,
            'now': now,
            'need_wait': self.need_wait(now),
            'T': self.T,
            'slack': self.slack
        }


class UpbitGCRARateLimiter:
    """
    업비트 통합 Rate Limiter - GCRA 기반

    Features:
    - 전역 잠금으로 멀티 클라이언트 동기화
    - 업비트 5개 그룹 + WebSocket 이중 윈도우 지원
    - 지터/타임아웃/Retry-After 처리
    - Infrastructure 로깅 통합
    """

    # 업비트 공식 Rate Limit 규칙
    _GROUP_CONFIGS = {
        UpbitRateLimitGroup.REST_PUBLIC: [
            GCRAConfig.from_rps(10.0)  # 10 RPS
        ],
        UpbitRateLimitGroup.REST_PRIVATE_DEFAULT: [
            GCRAConfig.from_rps(30.0)  # 30 RPS
        ],
        UpbitRateLimitGroup.REST_PRIVATE_ORDER: [
            GCRAConfig.from_rps(8.0)   # 8 RPS
        ],
        UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL: [
            GCRAConfig.from_interval(2.0)  # 0.5 RPS = 2초당 1회
        ],
        UpbitRateLimitGroup.WEBSOCKET: [
            GCRAConfig.from_rps(5.0),        # 5 RPS
            GCRAConfig.from_rps(100.0 / 60.0)  # 100 RPM = 1.67 RPS
        ]
    }

    # 엔드포인트 → 그룹 매핑
    _ENDPOINT_MAPPINGS = {
        # Public REST
        '/ticker': UpbitRateLimitGroup.REST_PUBLIC,
        '/tickers': UpbitRateLimitGroup.REST_PUBLIC,
        '/orderbook': UpbitRateLimitGroup.REST_PUBLIC,
        '/trades': UpbitRateLimitGroup.REST_PUBLIC,
        '/candles': UpbitRateLimitGroup.REST_PUBLIC,

        # Private REST - Default
        '/accounts': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/account_info': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/orders': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,

        # Private REST - Order
        '/order': UpbitRateLimitGroup.REST_PRIVATE_ORDER,
        '/order_new': UpbitRateLimitGroup.REST_PRIVATE_ORDER,
        '/order_cancel': UpbitRateLimitGroup.REST_PRIVATE_ORDER,

        # Private REST - Cancel All
        '/order_cancel_all': UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL,

        # WebSocket
        'websocket_connect': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_message': UpbitRateLimitGroup.WEBSOCKET,
    }

    def __init__(self, client_id: Optional[str] = None):
        self.client_id = client_id or f"upbit_gcra_{id(self)}"
        self.logger = create_component_logger("UpbitGCRARateLimiter")

        # 전역 잠금 (asyncio.Lock)
        self._lock = asyncio.Lock()

        # 그룹별 GCRA 컨트롤러 초기화
        self._controllers: Dict[UpbitRateLimitGroup, List[GCRA]] = {}
        for group, configs in self._GROUP_CONFIGS.items():
            self._controllers[group] = [GCRA(config) for config in configs]

        # 통계
        self._stats = {
            'total_requests': 0,
            'total_wait_time': 0.0,
            'immediate_passes': 0,
            'timeout_errors': 0
        }

        self.logger.info(f"업비트 GCRA Rate Limiter 초기화: {self.client_id}")

    async def acquire(self,
                     endpoint: str,
                     method: str = 'GET',
                     max_wait: float = 5.0,
                     jitter_range: tuple = (0.005, 0.02)) -> None:
        """
        Rate Limit 게이트 통과

        Args:
            endpoint: API 엔드포인트 경로
            method: HTTP 메서드
            max_wait: 최대 대기시간(초)
            jitter_range: 지터 범위(초)

        Raises:
            TimeoutError: max_wait 시간 초과
            ValueError: 알 수 없는 엔드포인트
        """
        # 엔드포인트 → 그룹 매핑
        group = self._get_rate_limit_group(endpoint)

        start_time = time.monotonic()
        deadline = start_time + max_wait

        self._stats['total_requests'] += 1

        while True:
            now = time.monotonic()

            async with self._lock:
                # 모든 관련 컨트롤러의 대기시간 계산
                controllers = self._controllers[group]
                wait_times = [controller.need_wait(now) for controller in controllers]
                max_wait_needed = max(wait_times)

                if max_wait_needed <= 0.0:
                    # 모든 제한을 통과 → 동시에 토큰 소비
                    for controller in controllers:
                        controller.consume(now)

                    elapsed = time.monotonic() - start_time
                    if elapsed < 0.001:  # 1ms 미만이면 즉시 통과
                        self._stats['immediate_passes'] += 1

                    self.logger.debug(f"Rate limit 획득: {endpoint} [{method}] -> {group.value} "
                                    f"(소요: {elapsed*1000:.1f}ms)")
                    return

            # 대기 필요 → 지터 추가 후 재시도
            wait_time = max_wait_needed + random.uniform(*jitter_range)

            if now + wait_time > deadline:
                self._stats['timeout_errors'] += 1
                raise TimeoutError(f"Rate limit 대기시간 초과: {endpoint} (max_wait={max_wait}s)")

            self._stats['total_wait_time'] += wait_time
            self.logger.debug(f"Rate limit 대기: {endpoint} -> {group.value} "
                            f"(대기: {wait_time*1000:.1f}ms)")

            await asyncio.sleep(max(0.0, wait_time))

    def _get_rate_limit_group(self, endpoint: str) -> UpbitRateLimitGroup:
        """엔드포인트를 Rate Limit 그룹으로 매핑"""
        # 정확한 매핑 우선 확인
        if endpoint in self._ENDPOINT_MAPPINGS:
            return self._ENDPOINT_MAPPINGS[endpoint]

        # 패턴 매핑 (부분 일치)
        for pattern, group in self._ENDPOINT_MAPPINGS.items():
            if pattern in endpoint:
                return group

        # 기본값: PUBLIC 그룹 (가장 엄격한 제한)
        self.logger.warning(f"알 수 없는 엔드포인트, PUBLIC 그룹 적용: {endpoint}")
        return UpbitRateLimitGroup.REST_PUBLIC

    def handle_429_response(self, retry_after: Optional[float] = None) -> None:
        """
        429 응답 처리 (Rate Limit 초과)

        Args:
            retry_after: 서버에서 제공한 Retry-After 시간(초)
        """
        base_wait = retry_after or 1.0
        jitter_wait = base_wait + random.uniform(0.1, 0.2)  # 100-200ms 지터

        self.logger.warning(f"429 Rate Limit 응답 수신, 대기: {jitter_wait:.2f}초")

        # 모든 컨트롤러에 패널티 적용 (TAT 강제 연장)
        penalty_time = time.monotonic() + jitter_wait
        for controllers in self._controllers.values():
            for controller in controllers:
                controller.tat = max(controller.tat, penalty_time)

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 및 통계 반환"""
        now = time.monotonic()

        group_status = {}
        for group, controllers in self._controllers.items():
            group_status[group.value] = [
                controller.get_status() for controller in controllers
            ]

        return {
            'client_id': self.client_id,
            'groups': group_status,
            'stats': self._stats.copy(),
            'timestamp': now
        }


# =============================================================================
# 전역 싱글톤 관리
# =============================================================================

# 전역 Rate Limiter 인스턴스 (IP 기반 공유)
_GLOBAL_RATE_LIMITER: Optional[UpbitGCRARateLimiter] = None
_GLOBAL_LOCK = asyncio.Lock()


async def get_global_rate_limiter() -> UpbitGCRARateLimiter:
    """전역 공유 Rate Limiter 인스턴스 획득"""
    global _GLOBAL_RATE_LIMITER

    async with _GLOBAL_LOCK:
        if _GLOBAL_RATE_LIMITER is None:
            _GLOBAL_RATE_LIMITER = UpbitGCRARateLimiter("global_shared")

    return _GLOBAL_RATE_LIMITER


# 편의 함수들
async def gate_rest_public(endpoint: str, method: str = 'GET', max_wait: float = 5.0) -> None:
    """REST Public API 게이트"""
    limiter = await get_global_rate_limiter()
    await limiter.acquire(endpoint, method, max_wait)


async def gate_rest_private(endpoint: str, method: str = 'GET', max_wait: float = 5.0) -> None:
    """REST Private API 게이트"""
    limiter = await get_global_rate_limiter()
    await limiter.acquire(endpoint, method, max_wait)


async def gate_websocket(action: str = 'websocket_connect', max_wait: float = 5.0) -> None:
    """WebSocket 게이트 (5 RPS + 100 RPM 이중 윈도우)"""
    limiter = await get_global_rate_limiter()
    await limiter.acquire(action, 'WS', max_wait)


# =============================================================================
# 팩토리 함수들 (기존 호환성)
# =============================================================================

def create_upbit_gcra_limiter(client_id: Optional[str] = None) -> UpbitGCRARateLimiter:
    """업비트 GCRA Rate Limiter 생성"""
    return UpbitGCRARateLimiter(client_id)


async def create_shared_upbit_gcra_limiter() -> UpbitGCRARateLimiter:
    """전역 공유 업비트 GCRA Rate Limiter 생성"""
    return await get_global_rate_limiter()
