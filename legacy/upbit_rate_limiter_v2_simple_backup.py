"""
업비트 Rate Limiter V2 - 단일 사용자 최적화 버전

특징:
- 단일 사용자 환경 최적화 (IP = 계정 = 동일인)
- UpbitMeasurementUnit 제거로 복잡성 대폭 감소
- 순수 Cloudflare Sliding Window 알고리즘
- 5개 카테고리 단순 관리
- 엔드포인트 자동 매핑
- access_key 없어도 public 완전 동작
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class UpbitApiCategory(Enum):
    """업비트 API 카테고리 - 5개 단순화"""
    QUOTATION = "quotation"                    # 시세 조회: 10 RPS
    EXCHANGE_DEFAULT = "exchange_default"      # 기본 거래소: 30 RPS
    EXCHANGE_ORDER = "exchange_order"          # 주문 생성/수정: 8 RPS
    EXCHANGE_CANCEL_ALL = "exchange_cancel_all"  # 일괄 취소: 0.5 RPS
    WEBSOCKET = "websocket"                    # WebSocket: 5 RPS + 100 RPM


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
    """Rate Limit 규칙 - 단순화"""
    windows: List[RateWindow]
    category: UpbitApiCategory
    name: str

    def get_strictest_rps(self) -> float:
        """가장 엄격한 RPS 반환"""
        return min(w.requests_per_second for w in self.windows)


class CloudflareSlidingWindow:
    """
    순수한 Cloudflare Sliding Window Counter 알고리즘 구현

    단일 사용자 환경 최적화:
    - 복잡한 IP/계정 분기 제거
    - 2-Counter 방식으로 메모리 효율성
    - 정확한 수학적 계산
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

        Returns:
            Tuple[bool, float]: (허용 여부, 대기 시간)
        """
        max_wait_needed = 0.0
        debug_info = []

        for window_id, window in enumerate(self.windows):
            counter = self.window_counters[window_id]
            window_seconds = counter['window_seconds']
            max_requests = counter['max_requests']

            # 현재 윈도우에서 경과된 시간 계산
            elapsed_in_current = now - counter['current_window_start']

            # 윈도우가 완전히 지났는지 확인하고 업데이트
            if elapsed_in_current >= window_seconds:
                full_windows_passed = int(elapsed_in_current // window_seconds)
                old_current = counter['current_count']

                if full_windows_passed == 1:
                    counter['previous_count'] = counter['current_count']
                else:
                    counter['previous_count'] = 0
                counter['current_count'] = 0
                counter['current_window_start'] += full_windows_passed * window_seconds
                elapsed_in_current = now - counter['current_window_start']

                debug_info.append(f"윈도우 {window_id} 리셋: {old_current}->{counter['current_count']}")

            # Cloudflare 선형 보간 계산
            remaining_weight = (window_seconds - elapsed_in_current) / window_seconds
            estimated_rate = counter['previous_count'] * remaining_weight + counter['current_count']

            debug_info.append(f"윈도우 {window_id}: 예상률={estimated_rate:.2f}/{max_requests}")

            # 제한 확인
            if estimated_rate + 1 > max_requests:
                time_to_allow = (estimated_rate + 1 - max_requests) / max_requests * window_seconds
                max_wait_needed = max(max_wait_needed, time_to_allow)
                debug_info.append(f"윈도우 {window_id} 제한 초과: 대기={time_to_allow:.3f}s")
                continue

        # 디버그 정보를 limiter 객체에 저장 (추후 조회 가능)
        self.last_debug_info = debug_info

        if max_wait_needed > 0:
            return False, max_wait_needed

        # 요청 허용: 모든 카운터 업데이트
        for window_id in range(len(self.windows)):
            counter = self.window_counters[window_id]
            counter['current_count'] += 1

        return True, 0.0

    async def acquire(self, max_retries: int = 3) -> bool:
        """
        Rate Limit 토큰 획득 (자동 재시도 포함)

        Args:
            max_retries: 최대 재시도 횟수

        Returns:
            bool: 성공 여부
        """
        async with self._lock:
            for attempt in range(max_retries):
                now = time.time()
                allowed, wait_time = self.check_limit(now)

                if allowed:
                    return True

                if attempt < max_retries - 1:  # 마지막 시도가 아니면
                    # 백오프 전략: 점진적 증가 + 최대 1초 제한
                    actual_wait = min(wait_time, 1.0)
                    backoff_factor = 1.1 ** attempt  # 점진적 증가
                    total_wait = actual_wait * backoff_factor

                    await asyncio.sleep(total_wait)

            return False

    def get_usage_info(self, now: float) -> Dict[str, Any]:
        """현재 사용량 정보 반환"""
        usage_info = {}

        for i, window in enumerate(self.windows):
            counter = self.window_counters[i]
            current_count = counter['current_count']
            usage_percent = (current_count / window.max_requests) * 100

            usage_info[f'window_{i}'] = {
                'window_seconds': window.window_seconds,
                'limit': window.max_requests,
                'current': current_count,
                'previous': counter['previous_count'],
                'usage_percent': usage_percent,
                'rps': window.requests_per_second
            }

        return usage_info

    def get_debug_info(self) -> List[str]:
        """마지막 check_limit 호출의 디버그 정보 반환"""
        return getattr(self, 'last_debug_info', [])


class UpbitRateLimiterV2Simple:
    """
    업비트 Rate Limiter V2 - 단일 사용자 최적화 버전

    핵심 특징:
    1. UpbitMeasurementUnit 완전 제거 (단일 사용자 = IP = 계정)
    2. 5개 카테고리 직접 관리
    3. 엔드포인트 자동 매핑
    4. access_key 없어도 public 완전 동작
    """

    # 업비트 공식 Rate Limit 규칙 (단순화)
    UPBIT_RULES = {
        UpbitApiCategory.QUOTATION: RateLimitRule(
            windows=[RateWindow(10, 1)],  # 10 RPS
            category=UpbitApiCategory.QUOTATION,
            name="시세 조회"
        ),
        UpbitApiCategory.EXCHANGE_DEFAULT: RateLimitRule(
            windows=[RateWindow(30, 1)],  # 30 RPS
            category=UpbitApiCategory.EXCHANGE_DEFAULT,
            name="기본 거래소"
        ),
        UpbitApiCategory.EXCHANGE_ORDER: RateLimitRule(
            windows=[RateWindow(8, 1)],  # 8 RPS
            category=UpbitApiCategory.EXCHANGE_ORDER,
            name="주문 생성/수정"
        ),
        UpbitApiCategory.EXCHANGE_CANCEL_ALL: RateLimitRule(
            windows=[RateWindow(1, 2)],  # 0.5 RPS (1 per 2 seconds)
            category=UpbitApiCategory.EXCHANGE_CANCEL_ALL,
            name="일괄 취소"
        ),
        UpbitApiCategory.WEBSOCKET: RateLimitRule(
            windows=[RateWindow(5, 1), RateWindow(100, 60)],  # 5 RPS + 100 RPM
            category=UpbitApiCategory.WEBSOCKET,
            name="WebSocket"
        ),
    }

    # 엔드포인트 → 카테고리 매핑
    ENDPOINT_MAPPINGS = {
        # 시세 조회 - 모두 QUOTATION으로 통합
        '/market/all': UpbitApiCategory.QUOTATION,
        '/candles/': UpbitApiCategory.QUOTATION,          # prefix 매칭
        '/ticker': UpbitApiCategory.QUOTATION,
        '/tickers': UpbitApiCategory.QUOTATION,
        '/trades/ticks': UpbitApiCategory.QUOTATION,
        '/orderbook': UpbitApiCategory.QUOTATION,

        # 기본 거래소
        '/accounts': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/chance': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/order': UpbitApiCategory.EXCHANGE_DEFAULT,       # GET 조회
        '/orders/uuids': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/open': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/closed': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/withdraws': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/deposits': UpbitApiCategory.EXCHANGE_DEFAULT,

        # WebSocket
        '/websocket': UpbitApiCategory.WEBSOCKET,
    }

    # 특수 메서드 매핑 (endpoint, method) → category
    SPECIAL_METHOD_MAPPINGS = {
        ('/orders', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders', 'DELETE'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders/cancel_and_new', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders/cancel_all', 'DELETE'): UpbitApiCategory.EXCHANGE_CANCEL_ALL,
        ('/orders/open', 'DELETE'): UpbitApiCategory.EXCHANGE_CANCEL_ALL,
    }

    def __init__(self, user_type: str = "anonymous"):
        """
        Rate Limiter 초기화

        Args:
            user_type: 사용자 타입 ("anonymous" 또는 "authenticated")
        """
        self.user_type = user_type
        self.client_id = f"upbit_simple_{user_type}_{id(self)}"

        # 카테고리별 Limiter 생성 (단순 직접 관리)
        self.limiters: Dict[UpbitApiCategory, CloudflareSlidingWindow] = {}
        for category, rule in self.UPBIT_RULES.items():
            limiter_id = f"{self.client_id}_{category.value}"
            self.limiters[category] = CloudflareSlidingWindow(
                windows=rule.windows,
                limiter_id=limiter_id
            )

        # 통계
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'category_counts': {cat.value: 0 for cat in UpbitApiCategory}
        }

    def resolve_category(self, endpoint: str, method: str = 'GET') -> UpbitApiCategory:
        """
        엔드포인트 → 카테고리 해결 (단순화됨)

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드

        Returns:
            UpbitApiCategory: 해당 카테고리
        """
        method_upper = method.upper()

        # 1. 특수 메서드 매핑 우선 확인
        special_key = (endpoint, method_upper)
        if special_key in self.SPECIAL_METHOD_MAPPINGS:
            return self.SPECIAL_METHOD_MAPPINGS[special_key]

        # 2. 정확한 엔드포인트 매핑
        if endpoint in self.ENDPOINT_MAPPINGS:
            return self.ENDPOINT_MAPPINGS[endpoint]

        # 3. 패턴 매칭 (prefix)
        for pattern, category in self.ENDPOINT_MAPPINGS.items():
            if endpoint.startswith(pattern):
                return category

        # 4. 기본값: 시세 조회 (가장 안전한 선택)
        return UpbitApiCategory.QUOTATION

    async def acquire(self, endpoint: str, method: str = 'GET') -> None:
        """
        Rate Limit 토큰 획득 (클라이언트 호환 인터페이스)

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드

        Raises:
            RateLimitExceededException: Rate Limit 초과 시
        """
        # 카테고리 결정
        category = self.resolve_category(endpoint, method)

        # 통계 업데이트
        self.stats['total_requests'] += 1
        self.stats['category_counts'][category.value] += 1

        # Rate Limit 획득
        limiter = self.limiters[category]
        success = await limiter.acquire(max_retries=3)

        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
            raise RateLimitExceededException(
                f"Rate limit exceeded for {endpoint} [{method}] -> {category.value}",
                retry_after=1.0
            )

    def check_limit(self, endpoint: str, method: str = 'GET') -> Tuple[bool, float]:
        """
        Rate Limit 순수 체크 (비블로킹)

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드

        Returns:
            Tuple[bool, float]: (허용 여부, 대기 시간)
        """
        category = self.resolve_category(endpoint, method)
        limiter = self.limiters[category]

        now = time.time()
        return limiter.check_limit(now)

    def get_status(self) -> Dict[str, Any]:
        """현재 Rate Limiter 상태 조회"""
        now = time.time()
        status = {}

        for category, limiter in self.limiters.items():
            rule = self.UPBIT_RULES[category]
            usage = limiter.get_usage_info(now)

            # 주요 윈도우 정보
            main_window = usage.get('window_0', {})
            strictest_rps = rule.get_strictest_rps()

            status[category.value] = {
                'current': main_window.get('current', 0),
                'limit': main_window.get('limit', 0),
                'usage_percent': main_window.get('usage_percent', 0),
                'rule_name': rule.name,
                'strictest_rps': f"{strictest_rps:.2f}"  # 소수점 2자리 표시
            }

        return {
            'client_id': self.client_id,
            'user_type': self.user_type,
            'architecture': 'single_user_optimized',
            'categories': status,
            'statistics': self.stats,
            'total_limiters': len(self.limiters)
        }

    def update_from_upbit_headers(self, headers: Dict[str, str]) -> None:
        """
        업비트 응답 헤더에서 Rate Limit 정보 업데이트

        Args:
            headers: HTTP 응답 헤더
        """
        # Remaining-Req 헤더 파싱
        remaining_req = headers.get('Remaining-Req', '')
        if remaining_req:
            try:
                # 예: "group=default; min=1800; sec=29"
                parts = remaining_req.split(';')
                for part in parts:
                    if 'sec=' in part:
                        # 서버 잔여 요청 수 파싱 (향후 확장용)
                        # sec_remaining = int(part.split('=')[1].strip())
                        break
            except (ValueError, IndexError):
                pass

    def update_response_timing(self, response_end_time: float, status_code: int) -> None:
        """
        응답 타이밍 정보 업데이트

        Args:
            response_end_time: 응답 완료 시간
            status_code: HTTP 상태 코드
        """
        # 429 에러 등 특수 처리 가능
        if status_code == 429:
            # 429 에러 시 추가 보수적 제어 가능
            pass


class RateLimitExceededException(Exception):
    """Rate Limit 초과 예외"""

    def __init__(self, message: str, retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


# ================================================================
# 팩토리 함수들 - 단일 사용자 최적화
# ================================================================

def create_upbit_public_limiter(use_shared: bool = True) -> UpbitRateLimiterV2Simple:
    """
    업비트 공개 API 전용 Rate Limiter 생성

    Args:
        use_shared: 공유 사용 여부 (단일 사용자에서는 의미 없음)

    Returns:
        UpbitRateLimiterV2Simple: Public 전용 Rate Limiter
    """
    return UpbitRateLimiterV2Simple(user_type="anonymous")


def create_upbit_private_limiter(client_id: str) -> UpbitRateLimiterV2Simple:
    """
    업비트 프라이빗 API 전용 Rate Limiter 생성

    Args:
        client_id: 클라이언트 식별자

    Returns:
        UpbitRateLimiterV2Simple: Private 전용 Rate Limiter
    """
    return UpbitRateLimiterV2Simple(user_type="authenticated")


def create_upbit_unified_limiter(
    access_key: Optional[str] = None
) -> UpbitRateLimiterV2Simple:
    """
    업비트 통합 Rate Limiter 생성 (권장)

    Args:
        access_key: 업비트 액세스 키 (없어도 됨)

    Returns:
        UpbitRateLimiterV2Simple: 통합 Rate Limiter
    """
    user_type = "authenticated" if access_key else "anonymous"
    return UpbitRateLimiterV2Simple(user_type=user_type)
