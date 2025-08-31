"""
업비트 Rate Limiter V2 - 순수한 Cloudflare 알고리즘

콜드 스타트 보호 없이 순수한 Cloudflare Sliding Window 알고리즘만 사용
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class UpbitMeasurementUnit(Enum):
    """업비트 측정 단위"""
    IP_BASED = "ip_based"           # IP 단위 (시세 조회)
    ACCOUNT_BASED = "account_based"  # 계정 단위 (거래/자산)


class UpbitApiCategory(Enum):
    """업비트 API 카테고리 - 5개 단순화"""
    QUOTATION = "quotation"                    # 시세 조회 통합: 10 RPS (IP 단위)
    EXCHANGE_DEFAULT = "exchange_default"      # 기본 거래소: 30 RPS (계정 단위)
    EXCHANGE_ORDER = "exchange_order"          # 주문 생성/수정: 8 RPS (계정 단위)
    EXCHANGE_CANCEL_ALL = "exchange_cancel_all"  # 일괄 취소: 0.5 RPS (계정 단위)
    WEBSOCKET = "websocket"                    # WebSocket 통합: 5 RPS + 100 RPM (IP/계정 동적)


@dataclass
class RateWindow:
    """Rate Limit 윈도우"""
    max_requests: int
    window_seconds: int

    @property
    def requests_per_second(self) -> float:
        return self.max_requests / self.window_seconds


@dataclass
class RateLimitRule:
    """Rate Limit 규칙"""
    windows: List[RateWindow]
    measurement_unit: UpbitMeasurementUnit
    category: UpbitApiCategory
    name: str

    def get_strictest_rps(self) -> float:
        """가장 엄격한 RPS 반환"""
        return min(w.requests_per_second for w in self.windows)


class CloudflareSlidingWindow:
    """
    순수한 Cloudflare Sliding Window Counter 알고리즘 구현

    콜드 스타트 보호 없이 정확한 수학적 계산만 사용
    """

    def __init__(self, windows: List[RateWindow], limiter_id: str):
        self.windows = windows
        self.limiter_id = limiter_id

        # Cloudflare 방식: 윈도우별 2개 카운터
        self.window_counters = {}
        for i, window in enumerate(windows):
            self.window_counters[i] = {
                'current_count': 0,
                'previous_count': 0,
                'current_window_start': time.time(),
                'window_seconds': window.window_seconds,
                'max_requests': window.max_requests
            }

        self._lock = asyncio.Lock()

    def check_limit(self, now: float) -> Tuple[bool, float]:
        """
        순수한 Cloudflare Sliding Window 알고리즘

        복잡한 보호 로직 없이 정확한 수학적 계산만 사용
        """
        max_wait_needed = 0.0

        for window_id, window in enumerate(self.windows):
            counter = self.window_counters[window_id]
            window_seconds = counter['window_seconds']
            max_requests = counter['max_requests']

            # 현재 윈도우에서 경과된 시간 계산
            elapsed_in_current = now - counter['current_window_start']

            # 윈도우가 완전히 지났는지 확인하고 업데이트
            if elapsed_in_current >= window_seconds:
                full_windows_passed = int(elapsed_in_current // window_seconds)
                if full_windows_passed == 1:
                    counter['previous_count'] = counter['current_count']
                else:
                    counter['previous_count'] = 0
                counter['current_count'] = 0
                counter['current_window_start'] += full_windows_passed * window_seconds
                elapsed_in_current = now - counter['current_window_start']

            # Cloudflare 선형 보간 계산
            remaining_weight = (window_seconds - elapsed_in_current) / window_seconds
            estimated_rate = counter['previous_count'] * remaining_weight + counter['current_count']

            # 제한 확인
            if estimated_rate + 1 > max_requests:
                time_to_allow = (estimated_rate + 1 - max_requests) / max_requests * window_seconds
                max_wait_needed = max(max_wait_needed, time_to_allow)
                continue

        if max_wait_needed > 0:
            return False, max_wait_needed

        # 요청 허용: 모든 카운터 업데이트
        for window_id in range(len(self.windows)):
            counter = self.window_counters[window_id]
            counter['current_count'] += 1

        return True, 0.0

    async def acquire_with_retry(self, now: float, max_retries: int = 3) -> bool:
        """
        편의 함수: 자동 재시도 포함

        Args:
            now: 현재 시간
            max_retries: 최대 재시도 횟수

        Returns:
            bool: 성공 여부
        """
        async with self._lock:
            for attempt in range(max_retries):
                allowed, wait_time = self.check_limit(now)

                if allowed:
                    return True

                if attempt < max_retries - 1:  # 마지막 시도가 아니면
                    # 백오프 전략: 점진적 증가 + 최대 1초 제한
                    actual_wait = min(wait_time, 1.0)
                    backoff_factor = 1.1 ** attempt  # 점진적 증가
                    total_wait = actual_wait * backoff_factor

                    await asyncio.sleep(total_wait)
                    now = time.time()  # 대기 후 시간 업데이트

            return False


class UpbitRateLimiterV2:
    """
    업비트 Rate Limiter V2 - 순수한 5카테고리 구현

    콜드 스타트 보호 없이 순수한 Cloudflare 알고리즘만 사용
    """

    # 업비트 공식 Rate Limit 규칙
    UPBIT_RULES = {
        UpbitApiCategory.QUOTATION: RateLimitRule(
            windows=[RateWindow(10, 1)],  # 10 RPS
            measurement_unit=UpbitMeasurementUnit.IP_BASED,
            category=UpbitApiCategory.QUOTATION,
            name="시세 조회"
        ),
        UpbitApiCategory.EXCHANGE_DEFAULT: RateLimitRule(
            windows=[RateWindow(30, 1)],  # 30 RPS
            measurement_unit=UpbitMeasurementUnit.ACCOUNT_BASED,
            category=UpbitApiCategory.EXCHANGE_DEFAULT,
            name="기본 거래소"
        ),
        UpbitApiCategory.EXCHANGE_ORDER: RateLimitRule(
            windows=[RateWindow(8, 1)],  # 8 RPS
            measurement_unit=UpbitMeasurementUnit.ACCOUNT_BASED,
            category=UpbitApiCategory.EXCHANGE_ORDER,
            name="주문 생성/수정"
        ),
        UpbitApiCategory.EXCHANGE_CANCEL_ALL: RateLimitRule(
            windows=[RateWindow(1, 2)],  # 0.5 RPS (1 per 2 seconds)
            measurement_unit=UpbitMeasurementUnit.ACCOUNT_BASED,
            category=UpbitApiCategory.EXCHANGE_CANCEL_ALL,
            name="일괄 취소"
        ),
        UpbitApiCategory.WEBSOCKET: RateLimitRule(
            windows=[RateWindow(5, 1), RateWindow(100, 60)],  # 5 RPS + 100 RPM
            measurement_unit=UpbitMeasurementUnit.IP_BASED,
            category=UpbitApiCategory.WEBSOCKET,
            name="WebSocket"
        ),
    }

    def __init__(
        self,
        upbit_access_key: Optional[str] = None,
        upbit_secret_key: Optional[str] = None,
        use_account_based: bool = True,
    ):
        """
        Rate Limiter 초기화

        Args:
            upbit_access_key: 업비트 액세스 키 (계정 기반 제한용)
            upbit_secret_key: 업비트 시크릿 키 (계정 기반 제한용)
            use_account_based: 계정 기반 제한 사용 여부
        """
        self.upbit_access_key = upbit_access_key
        self.upbit_secret_key = upbit_secret_key
        self.use_account_based = use_account_based

        # 카테고리별 Limiter 생성
        self.limiters: Dict[UpbitApiCategory, CloudflareSlidingWindow] = {}
        for category, rule in self.UPBIT_RULES.items():
            limiter_id = f"{category.value}_{rule.measurement_unit.value}"
            self.limiters[category] = CloudflareSlidingWindow(
                windows=rule.windows,
                limiter_id=limiter_id
            )

    def check_limit(
        self,
        category: UpbitApiCategory,
        now: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        순수한 Rate Limit 체크

        Args:
            category: API 카테고리
            now: 현재 시간 (None이면 자동 계산)

        Returns:
            Tuple[bool, float]: (허용 여부, 대기 시간)
        """
        if now is None:
            now = time.time()

        limiter = self.limiters.get(category)
        if limiter is None:
            return True, 0.0

        return limiter.check_limit(now)

    async def acquire_with_retry(
        self,
        category: UpbitApiCategory,
        max_retries: int = 3,
        now: Optional[float] = None
    ) -> bool:
        """
        자동 재시도 포함 Rate Limit 획득

        Args:
            category: API 카테고리
            max_retries: 최대 재시도 횟수
            now: 현재 시간

        Returns:
            bool: 성공 여부
        """
        if now is None:
            now = time.time()

        limiter = self.limiters.get(category)
        if limiter is None:
            return True

        return await limiter.acquire_with_retry(now, max_retries)

    def get_status(self) -> Dict[str, Any]:
        """
        현재 Rate Limiter 상태 조회

        Returns:
            Dict: 카테고리별 상태 정보
        """
        status = {}
        now = time.time()

        for category, limiter in self.limiters.items():
            rule = self.UPBIT_RULES[category]

            # 각 윈도우별 상태 수집
            window_status = []
            for window_id, window in enumerate(limiter.windows):
                counter = limiter.window_counters[window_id]
                elapsed = now - counter['current_window_start']

                window_status.append({
                    'window_seconds': counter['window_seconds'],
                    'max_requests': counter['max_requests'],
                    'current_count': counter['current_count'],
                    'previous_count': counter['previous_count'],
                    'elapsed_seconds': round(elapsed, 3),
                    'rps_limit': window.requests_per_second
                })

            status[category.value] = {
                'name': rule.name,
                'measurement_unit': rule.measurement_unit.value,
                'strictest_rps': rule.get_strictest_rps(),
                'windows': window_status
            }

        return status


class RateLimitExceededException(Exception):
    """Rate Limit 초과 예외"""

    def __init__(self, message: str, retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after
