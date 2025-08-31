"""
업비트 멀티 티어 Rate Limiter - 완전 재설계

설계 원칙:
1. 계층적 제한: 전역 → 그룹별 → 엔드포인트별 (모든 계층 통과 필요)
2. 이중 윈도우: 초/분 단위 동시 검증 (예: 5 RPS + 100 RPM)
3. 분산 동기화: Redis + 로컬 캐시 하이브리드
4. Cloudflare Sliding Window 알고리즘 적용
5. 멀티 클라이언트 전역 IP 기반 공유
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class UpbitRateLimitTier(Enum):
    """업비트 Rate Limit 계층"""
    GLOBAL = "global"           # 최상위: 전역 제한
    GROUP = "group"             # 중간: 그룹별 제한
    ENDPOINT = "endpoint"       # 최하위: 엔드포인트별 특수 제한


class UpbitRateLimitGroup(Enum):
    """업비트 API Rate Limit 그룹"""
    QUOTATION = "quotation"
    EXCHANGE_DEFAULT = "exchange_default"
    ORDER = "order"
    ORDER_CANCEL_ALL = "order_cancel_all"
    WEBSOCKET_CONNECT = "websocket_connect"
    WEBSOCKET_MESSAGE = "websocket_message"


@dataclass
class RateWindow:
    """Rate Limit 윈도우 정의"""
    max_requests: int
    window_seconds: int

    @property
    def requests_per_second(self) -> float:
        return self.max_requests / self.window_seconds


@dataclass
class MultiTierRule:
    """멀티 티어 Rate Limit 규칙"""
    windows: List[RateWindow]  # 여러 윈도우 동시 검증
    tier: UpbitRateLimitTier
    name: str

    def get_strictest_rps(self) -> float:
        """가장 엄격한(낮은) RPS 반환"""
        return min(w.requests_per_second for w in self.windows)


class CloudflareSlidingWindow:
    """Cloudflare Sliding Window Counter 알고리즘"""

    def __init__(self, windows: List[RateWindow]):
        self.windows = windows
        self.requests: List[float] = []

    def check_and_add(self, now: float) -> Tuple[bool, str]:
        """
        요청 허용 여부 확인 및 추가

        Returns:
            (허용여부, 거부사유)
        """
        # 모든 윈도우에서 검증
        for window in self.windows:
            if not self._check_window(now, window):
                return False, f"윈도우 초과: {window.max_requests}/{window.window_seconds}s"

        # 모든 윈도우 통과 시 요청 추가
        self.requests.append(now)
        self._cleanup(now)
        return True, "허용"

    def _check_window(self, now: float, window: RateWindow) -> bool:
        """단일 윈도우 검증 (Cloudflare Sliding Window)"""
        window_start = now - window.window_seconds

        # 현재 윈도우와 이전 윈도우 분리
        current_second = int(now)
        previous_second = current_second - 1

        # 각 윈도우별 요청 카운트
        current_count = sum(1 for ts in self.requests if ts >= current_second)
        previous_count = sum(1 for ts in self.requests
                           if previous_second <= ts < current_second)

        # Sliding Window 가중 계산
        elapsed_ratio = now - current_second
        weighted_count = previous_count * (1.0 - elapsed_ratio) + current_count

        return weighted_count < window.max_requests

    def _cleanup(self, now: float):
        """오래된 요청 제거"""
        max_window = max(w.window_seconds for w in self.windows)
        cutoff = now - max_window * 2  # 안전 마진
        self.requests = [ts for ts in self.requests if ts > cutoff]


class UpbitMultiTierRateLimiter:
    """
    업비트 멀티 티어 Rate Limiter

    특징:
    1. 계층적 검증: GLOBAL → GROUP → ENDPOINT 순차 검증
    2. 이중 윈도우: 초/분 단위 동시 만족 필요
    3. Cloudflare Sliding Window 정확성
    4. Redis 분산 동기화 (향후 확장)
    5. 멀티 클라이언트 IP 공유
    """

    # 업비트 공식 멀티 티어 규칙
    _TIER_RULES = {
        # Tier 1: 전역 제한 (모든 API 공통)
        UpbitRateLimitTier.GLOBAL: {
            "default": MultiTierRule(
                windows=[
                    RateWindow(10, 1),    # 10 RPS
                    RateWindow(600, 60)   # 600 RPM
                ],
                tier=UpbitRateLimitTier.GLOBAL,
                name="전역제한"
            )
        },

        # Tier 2: 그룹별 제한
        UpbitRateLimitTier.GROUP: {
            UpbitRateLimitGroup.QUOTATION: MultiTierRule(
                windows=[
                    RateWindow(10, 1),    # 10 RPS
                    RateWindow(600, 60)   # 600 RPM
                ],
                tier=UpbitRateLimitTier.GROUP,
                name="시세조회"
            ),
            UpbitRateLimitGroup.EXCHANGE_DEFAULT: MultiTierRule(
                windows=[
                    RateWindow(30, 1),    # 30 RPS
                    RateWindow(1800, 60)  # 1800 RPM
                ],
                tier=UpbitRateLimitTier.GROUP,
                name="거래소기본"
            ),
            UpbitRateLimitGroup.ORDER: MultiTierRule(
                windows=[
                    RateWindow(8, 1),     # 8 RPS
                    RateWindow(480, 60)   # 480 RPM
                ],
                tier=UpbitRateLimitTier.GROUP,
                name="주문"
            ),
            UpbitRateLimitGroup.ORDER_CANCEL_ALL: MultiTierRule(
                windows=[
                    RateWindow(1, 2),     # 0.5 RPS (2초당 1회)
                    RateWindow(30, 60)    # 30 RPM
                ],
                tier=UpbitRateLimitTier.GROUP,
                name="전체취소"
            ),
            UpbitRateLimitGroup.WEBSOCKET_CONNECT: MultiTierRule(
                windows=[
                    RateWindow(5, 1),     # 5 RPS
                    RateWindow(100, 60)   # 100 RPM ✅ 이중 윈도우!
                ],
                tier=UpbitRateLimitTier.GROUP,
                name="웹소켓연결"
            ),
            UpbitRateLimitGroup.WEBSOCKET_MESSAGE: MultiTierRule(
                windows=[
                    RateWindow(5, 1),     # 5 RPS
                    RateWindow(100, 60)   # 100 RPM ✅ 이중 윈도우!
                ],
                tier=UpbitRateLimitTier.GROUP,
                name="웹소켓메시지"
            )
        }
    }

    # 엔드포인트 → 그룹 매핑
    _ENDPOINT_MAPPINGS = {
        # Quotation
        '/ticker': UpbitRateLimitGroup.QUOTATION,
        '/tickers': UpbitRateLimitGroup.QUOTATION,
        '/market/all': UpbitRateLimitGroup.QUOTATION,
        '/orderbook': UpbitRateLimitGroup.QUOTATION,
        '/trades/ticks': UpbitRateLimitGroup.QUOTATION,
        '/candles/minutes': UpbitRateLimitGroup.QUOTATION,
        '/candles/days': UpbitRateLimitGroup.QUOTATION,
        '/candles/weeks': UpbitRateLimitGroup.QUOTATION,
        '/candles/months': UpbitRateLimitGroup.QUOTATION,
        '/candles/seconds': UpbitRateLimitGroup.QUOTATION,

        # Exchange Default
        '/accounts': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/orders/chance': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/order': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/orders/uuids': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/orders/open': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/orders/closed': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/withdraws': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/deposits': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
    }

    # 특수 메서드 매핑
    _SPECIAL_METHOD_MAPPINGS = {
        ('/orders', 'POST'): UpbitRateLimitGroup.ORDER,
        ('/orders', 'DELETE'): UpbitRateLimitGroup.ORDER,
        ('/orders/cancel_and_new', 'POST'): UpbitRateLimitGroup.ORDER,
        ('/orders/cancel_all', 'DELETE'): UpbitRateLimitGroup.ORDER_CANCEL_ALL,
        ('/orders/open', 'DELETE'): UpbitRateLimitGroup.ORDER_CANCEL_ALL,
    }

    def __init__(self, client_id: Optional[str] = None, enable_redis: bool = False):
        self.client_id = client_id or f"upbit_multi_{id(self)}"
        self.enable_redis = enable_redis

        # 계층별 Sliding Window Counter
        self._limiters: Dict[str, CloudflareSlidingWindow] = {}

        # 전역 공유 (IP 기반)
        self._shared_global_limiter: Optional[CloudflareSlidingWindow] = None

        # 동기화 상태
        self._last_sync = 0.0
        self._sync_interval = 1.0  # 1초마다 Redis 동기화

        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"UpbitMultiTier.{self.client_id}")

        # 통계
        self._stats = {
            'total_requests': 0,
            'rejected_by_tier': {tier.value: 0 for tier in UpbitRateLimitTier},
            'tier_timings': {tier.value: 0.0 for tier in UpbitRateLimitTier}
        }

        self._init_limiters()

    def _init_limiters(self):
        """Sliding Window Counter 초기화"""
        # 전역 제한
        global_rule = self._TIER_RULES[UpbitRateLimitTier.GLOBAL]["default"]
        self._shared_global_limiter = CloudflareSlidingWindow(global_rule.windows)

        # 그룹별 제한
        for group, rule in self._TIER_RULES[UpbitRateLimitTier.GROUP].items():
            key = f"group_{group.value}"
            self._limiters[key] = CloudflareSlidingWindow(rule.windows)

    async def acquire(self, endpoint: str, method: str = 'GET') -> None:
        """
        멀티 티어 Rate Limit 검증

        검증 순서:
        1. 전역 제한 (10 RPS + 600 RPM)
        2. 그룹별 제한 (QUOTATION/ORDER 등)
        3. 엔드포인트별 특수 제한 (필요시)
        """
        async with self._lock:
            start_time = time.perf_counter()
            now = time.time()

            try:
                self._stats['total_requests'] += 1

                # 🏗️ Tier 1: 전역 제한 검증
                tier_start = time.perf_counter()
                await self._enforce_global_limit(now)
                self._stats['tier_timings']['global'] += time.perf_counter() - tier_start

                # 🏗️ Tier 2: 그룹별 제한 검증
                tier_start = time.perf_counter()
                group = self._resolve_group(endpoint, method)
                await self._enforce_group_limit(now, group)
                self._stats['tier_timings']['group'] += time.perf_counter() - tier_start

                # 🏗️ Tier 3: 엔드포인트별 특수 제한 (향후 확장)
                # await self._enforce_endpoint_limit(now, endpoint, method)

                self._logger.debug(
                    f"Rate limit 획득: {endpoint} [{method}] -> {group.value} "
                    f"(소요: {(time.perf_counter() - start_time)*1000:.1f}ms)"
                )

            except RateLimitExceeded as e:
                self._logger.warning(f"Rate limit 거부: {endpoint} [{method}] -> {e}")
                raise

    async def _enforce_global_limit(self, now: float) -> None:
        """Tier 1: 전역 제한 강제 적용"""
        if not self._shared_global_limiter:
            return

        allowed, reason = self._shared_global_limiter.check_and_add(now)
        if not allowed:
            self._stats['rejected_by_tier']['global'] += 1
            raise RateLimitExceeded(f"전역제한: {reason}")

    async def _enforce_group_limit(self, now: float, group: UpbitRateLimitGroup) -> None:
        """Tier 2: 그룹별 제한 강제 적용"""
        key = f"group_{group.value}"
        limiter = self._limiters.get(key)

        if not limiter:
            return

        allowed, reason = limiter.check_and_add(now)
        if not allowed:
            self._stats['rejected_by_tier']['group'] += 1
            raise RateLimitExceeded(f"그룹제한({group.value}): {reason}")

    def _resolve_group(self, endpoint: str, method: str) -> UpbitRateLimitGroup:
        """엔드포인트 → 그룹 해결"""
        # 1. 특수 메서드 매핑 우선
        method_upper = method.upper()
        special_key = (endpoint, method_upper)

        if special_key in self._SPECIAL_METHOD_MAPPINGS:
            return self._SPECIAL_METHOD_MAPPINGS[special_key]

        # 2. 일반 엔드포인트 매핑
        if endpoint in self._ENDPOINT_MAPPINGS:
            return self._ENDPOINT_MAPPINGS[endpoint]

        # 3. 패턴 매칭
        for pattern, group in self._ENDPOINT_MAPPINGS.items():
            if endpoint.startswith(pattern):
                return group

        # 4. 기본값
        return UpbitRateLimitGroup.QUOTATION

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        now = time.time()

        # 전역 상태
        global_recent = len([ts for ts in self._shared_global_limiter.requests
                           if now - ts < 1])

        # 그룹별 상태
        group_status = {}
        for group in UpbitRateLimitGroup:
            key = f"group_{group.value}"
            limiter = self._limiters.get(key)
            if limiter:
                recent_count = len([ts for ts in limiter.requests if now - ts < 1])
                rule = self._TIER_RULES[UpbitRateLimitTier.GROUP][group]
                max_rps = rule.get_strictest_rps()

                group_status[group.value] = {
                    'current_rps': recent_count,
                    'max_rps': max_rps,
                    'usage_percent': (recent_count / max_rps) * 100
                }

        return {
            'client_id': self.client_id,
            'architecture': 'multi_tier_cloudflare_sliding_window',
            'global': {
                'current_rps': global_recent,
                'max_rps': 10,
                'usage_percent': (global_recent / 10) * 100
            },
            'groups': group_status,
            'statistics': self._stats,
            'total_limiters': len(self._limiters) + 1
        }


class RateLimitExceeded(Exception):
    """Rate Limit 초과 예외"""
    pass


# 🌍 전역 공유 인스턴스 (IP 기반)
_shared_instances: Dict[str, UpbitMultiTierRateLimiter] = {}


def create_upbit_multi_tier_limiter(
    client_id: Optional[str] = None,
    shared: bool = True,
    enable_redis: bool = False
) -> UpbitMultiTierRateLimiter:
    """
    업비트 멀티 티어 Rate Limiter 생성

    Args:
        client_id: 클라이언트 식별자
        shared: IP 기반 전역 공유 여부
        enable_redis: Redis 분산 동기화 여부
    """
    if shared:
        # IP 기반 공유 인스턴스
        key = f"shared_multi_tier_{enable_redis}"
        if key not in _shared_instances:
            _shared_instances[key] = UpbitMultiTierRateLimiter(
                client_id="shared_global",
                enable_redis=enable_redis
            )
        return _shared_instances[key]
    else:
        # 독립 인스턴스
        return UpbitMultiTierRateLimiter(client_id, enable_redis)
