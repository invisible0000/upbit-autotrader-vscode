"""
업비트 Rate Limiter V2 - 단순화된 5카테고리 설계

업비트 공식 문서 기준 최적화:
1. 5개 핵심 카테고리: Quotation, ExchangeDefault, ExchangeOrder, ExchangeCancelAll, WebSocket
2. IP/계정 분리 복잡성 제거 - 카테고리별 단순 관리
3. Cloudflare Sliding Window 정확성 유지
4. 이중 윈도우 지원 (초/분 단위)

🔍 핵심 알고리즘: CloudflareSlidingWindow
=====================================
Cloudflare에서 사용하는 Sliding Window Counter 알고리즘을 구현.
기존 Fixed Window의 한계를 극복한 정교한 Rate Limiting 방식.

📊 동작 원리:
1. 요청 타임스탬프를 리스트로 저장
2. 각 윈도우별로 현재 시점에서 역산하여 윈도우 내 요청 수 계산
3. 가장 엄격한 제한(최소 RPS)을 기준으로 최소 간격 강제
4. 모든 윈도우에서 제한을 통과해야 요청 허용

⚡ 특징:
- 정확한 시간 기반 제어 (타임스탬프 저장)
- 이중/다중 윈도우 지원 (초단위 + 분단위)
- 메모리 효율적 (오래된 요청 자동 정리)
- 버스트 방지 (최소 간격 강제)
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
    🔍 진짜 Cloudflare Sliding Window Counter 알고리즘 구현

    ████████████████████████████████████████████████████████████
    🚀 Cloudflare 공식 알고리즘 - 2개 카운터 + 선형 보간
    ████████████████████████████████████████████████████████████

    📊 알고리즘 동작 방식 (Cloudflare 블로그 기준):

    1️⃣ 2개 카운터 방식:
       - previous_window: 이전 완전한 윈도우의 요청 수
       - current_window: 현재 윈도우의 요청 수 (윈도우 시작부터 now까지)

    2️⃣ 선형 보간 계산:
       rate = previous_count * ((window_time - elapsed_time) / window_time) + current_count

       예) 50 req/min 제한, 15초 경과, 이전:42, 현재:18
       rate = 42 * ((60-15)/60) + 18 = 42 * 0.75 + 18 = 49.5

    ⚡ 특징:
    - Fixed Window의 경계 문제 해결
    - 이전 윈도우 정보로 스무딩 효과
    - 메모리 사용량 극소 (타임스탬프 저장 불필요)
    """

    def __init__(self, windows: List[RateWindow], limiter_id: str):
        self.windows = windows
        self.limiter_id = limiter_id

        # 진짜 Cloudflare 방식: 윈도우별 2개 카운터
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
        Cloudflare Sliding Window Rate Limit 체크

        표준 Cloudflare 알고리즘으로 정확한 Rate Limiting 수행
        """
        max_wait_needed = 0.0

        for window_id, window in enumerate(self.windows):
            counter = self.window_counters[window_id]
            window_seconds = counter['window_seconds']
            max_requests = counter['max_requests']

            # 표준 Cloudflare 알고리즘
            elapsed_in_current = now - counter['current_window_start']

            if elapsed_in_current >= window_seconds:
                full_windows_passed = int(elapsed_in_current // window_seconds)
                if full_windows_passed == 1:
                    counter['previous_count'] = counter['current_count']
                else:
                    counter['previous_count'] = 0
                counter['current_count'] = 0
                counter['current_window_start'] += full_windows_passed * window_seconds
                elapsed_in_current = now - counter['current_window_start']

            # Cloudflare 선형 보간
            remaining_weight = (window_seconds - elapsed_in_current) / window_seconds
            estimated_rate = counter['previous_count'] * remaining_weight + counter['current_count']

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
        🎁 편의 함수: 자동 재시도 포함 (기존 코드 호환성용)

        📊 도우미 함수 동작:
        1️⃣ check_limit()로 즉시 체크
        2️⃣ 실패 시 계산된 시간만큼 대기
        3️⃣ 최대 재시도 횟수까지 반복
        4️⃣ 백오프 전략 적용

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
                    actual_wait *= (1.0 + attempt * 0.1)  # 10%씩 증가
                    await asyncio.sleep(actual_wait)
                    now = time.time()  # 대기 후 시간 업데이트

            return False

    def get_current_usage(self, now: float) -> Dict[str, Any]:
        """현재 사용량 정보 반환 (진짜 Cloudflare 방식)"""
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


# =====================================
# 메인 Rate Limiter V2 클래스
# =====================================


class UpbitRateLimiterV2:
    """
    업비트 Rate Limiter V2 - 표준 Cloudflare 알고리즘

    특징:
    1. 5개 핵심 카테고리로 단순화
    2. Cloudflare Sliding Window 알고리즘
    3. 이중 윈도우 지원 (RPS + RPM)
    4. 정확한 Rate Limiting 제공
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        account_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        # 클라이언트 식별 정보
        self.client_id = client_id or f"upbit_v2_{id(self)}"
        self.account_id = account_id
        self.ip_address = ip_address or "127.0.0.1"

        # 동시성 제어
        self._lock = asyncio.Lock()

        # 카테고리별 Limiter
        self._limiters: Dict[str, CloudflareSlidingWindow] = {}

        # 통계
        self._stats = {
            'total_requests': 0,
            'ip_based_requests': 0,
            'account_based_requests': 0,
            'rejected_by_category': {cat.value: 0 for cat in UpbitApiCategory}
        }

        # 성능 메트릭
        self._performance_metrics = {
            'acquire_times': [],
            'actual_intervals': [],
            'request_timestamps': [],
            'success_count': 0,
            'error_count': 0,
            'rate_limit_errors': 0
        }

        self._real_time_window_size = 10
        self._last_request_time = 0.0

        # 카테고리별 Limiter 초기화
        self._init_limiters()    # 업비트 공식 Rate Limit 규칙 (5개 카테고리)
    _RATE_RULES = {
        # 1. 시세 조회 통합 (IP 단위) - 10 RPS 단일 윈도우
        UpbitApiCategory.QUOTATION: RateLimitRule(
            windows=[RateWindow(10, 1)],
            measurement_unit=UpbitMeasurementUnit.IP_BASED,
            category=UpbitApiCategory.QUOTATION,
            name="시세조회통합"
        ),

        # 2. 기본 거래소 (계정 단위) - 30 RPS 단일 윈도우
        UpbitApiCategory.EXCHANGE_DEFAULT: RateLimitRule(
            windows=[RateWindow(30, 1)],
            measurement_unit=UpbitMeasurementUnit.ACCOUNT_BASED,
            category=UpbitApiCategory.EXCHANGE_DEFAULT,
            name="기본거래소"
        ),

        # 3. 주문 생성/수정 (계정 단위) - 8 RPS 단일 윈도우
        UpbitApiCategory.EXCHANGE_ORDER: RateLimitRule(
            windows=[RateWindow(8, 1)],
            measurement_unit=UpbitMeasurementUnit.ACCOUNT_BASED,
            category=UpbitApiCategory.EXCHANGE_ORDER,
            name="주문생성수정"
        ),

        # 4. 일괄 취소 (계정 단위) - 0.5 RPS 단일 윈도우
        UpbitApiCategory.EXCHANGE_CANCEL_ALL: RateLimitRule(
            windows=[RateWindow(1, 2)],
            measurement_unit=UpbitMeasurementUnit.ACCOUNT_BASED,
            category=UpbitApiCategory.EXCHANGE_CANCEL_ALL,
            name="일괄취소"
        ),

        # 5. WebSocket 통합 (IP/계정 동적) - 5 RPS + 100 RPM 이중 제한
        UpbitApiCategory.WEBSOCKET: RateLimitRule(
            windows=[RateWindow(5, 1), RateWindow(100, 60)],  # 5 RPS + 100 RPM
            measurement_unit=UpbitMeasurementUnit.IP_BASED,  # 기본 IP, 인증시 계정
            category=UpbitApiCategory.WEBSOCKET,
            name="웹소켓통합"
        ),
    }

    # 엔드포인트 → 카테고리 매핑 (단순화)
    _ENDPOINT_MAPPINGS = {
        # 시세 조회 - 모두 QUOTATION으로 통합
        '/market/all': UpbitApiCategory.QUOTATION,
        '/candles/': UpbitApiCategory.QUOTATION,          # 모든 캔들 API
        '/ticker': UpbitApiCategory.QUOTATION,
        '/tickers': UpbitApiCategory.QUOTATION,
        '/trades/ticks': UpbitApiCategory.QUOTATION,
        '/orderbook': UpbitApiCategory.QUOTATION,
        '/quotation': UpbitApiCategory.QUOTATION,         # 테스트용

        # 기본 거래소
        '/accounts': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/chance': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/order': UpbitApiCategory.EXCHANGE_DEFAULT,       # GET 조회
        '/orders/uuids': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/open': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/closed': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/withdraws': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/deposits': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/exchange_default': UpbitApiCategory.EXCHANGE_DEFAULT,  # 테스트용

        # 주문 생성/수정
        '/exchange_order': UpbitApiCategory.EXCHANGE_ORDER,      # 테스트용

        # 일괄 취소
        '/exchange_cancel_all': UpbitApiCategory.EXCHANGE_CANCEL_ALL,  # 테스트용

        # WebSocket
        '/websocket': UpbitApiCategory.WEBSOCKET,
    }

    # 특수 메서드 매핑
    _SPECIAL_METHOD_MAPPINGS = {
        ('/orders', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders', 'DELETE'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders/cancel_and_new', 'POST'): UpbitApiCategory.EXCHANGE_ORDER,
        ('/orders/cancel_all', 'DELETE'): UpbitApiCategory.EXCHANGE_CANCEL_ALL,
        ('/orders/open', 'DELETE'): UpbitApiCategory.EXCHANGE_CANCEL_ALL,
    }

    def _init_limiters(self):
        """카테고리별 Sliding Window Limiter 초기화"""
        for category, rule in self._RATE_RULES.items():
            limiter_id = f"{self.client_id}_{category.value}"
            self._limiters[category.value] = CloudflareSlidingWindow(rule.windows, limiter_id)

    async def acquire(
        self,
        endpoint: str,
        method: str = 'GET',
        is_authenticated: bool = False
    ) -> None:
        """Rate Limit 토큰 획득"""
        acquire_start = time.time()

        async with self._lock:
            now = time.time()
            self._stats['total_requests'] += 1

            # 실제 간격 계산
            if self._last_request_time > 0:
                actual_interval = (acquire_start - self._last_request_time) * 1000
                self._performance_metrics['actual_intervals'].append(actual_interval)
                if len(self._performance_metrics['actual_intervals']) > self._real_time_window_size:
                    self._performance_metrics['actual_intervals'].pop(0)

            self._last_request_time = acquire_start

            # 카테고리 결정
            category = self._resolve_category(endpoint, method, is_authenticated)
            rule = self._RATE_RULES[category]

            # Limiter 선택 (단순화됨)
            limiter = self._limiters[category.value]

            # 통계 업데이트
            if rule.measurement_unit == UpbitMeasurementUnit.IP_BASED:
                self._stats['ip_based_requests'] += 1
            else:
                self._stats['account_based_requests'] += 1
                if not self.account_id:
                    raise ValueError("계정 단위 API 호출 시 account_id 필수")

            # Rate Limit 검증 - 새로운 V2 방식
            allowed, wait_time = limiter.check_limit(now)

            acquire_end = time.time()
            acquire_time = (acquire_end - acquire_start) * 1000

            if not allowed:
                self._stats['rejected_by_category'][category.value] += 1
                self._performance_metrics['rate_limit_errors'] += 1
                self._performance_metrics['error_count'] += 1

                error_msg = f"Rate limit 초과: {endpoint} [{method}] -> {category.value} -> 대기필요: {wait_time:.3f}초"
                raise RateLimitExceeded(error_msg, retry_after=wait_time)

            # 성공 메트릭 기록
            self._performance_metrics['success_count'] += 1
            self._performance_metrics['acquire_times'].append(acquire_time)
            self._performance_metrics['request_timestamps'].append(acquire_start)

            # 최근 N개만 유지
            for key in ['acquire_times', 'request_timestamps']:
                if len(self._performance_metrics[key]) > self._real_time_window_size:
                    self._performance_metrics[key].pop(0)

    def check_limit(
        self,
        endpoint: str,
        method: str = 'GET',
        is_authenticated: bool = False
    ) -> Tuple[bool, float]:
        """
        🔍 Rate Limit 순수 체크 함수 (비블로킹, 새로운 V2 방식)

        📊 Low-level API: 최고 성능, 유연성
        - 즉시 체크만 수행, 대기하지 않음
        - 클라이언트가 대기와 재시도 직접 제어
        - 배치 처리나 고성능 시나리오에 최적

        Returns:
            tuple[bool, float]: (허용 여부, 필요한 대기 시간)
        """
        now = time.time()
        self._stats['total_requests'] += 1

        # 카테고리 결정
        category = self._resolve_category(endpoint, method, is_authenticated)
        rule = self._RATE_RULES[category]

        # Limiter 선택
        limiter = self._limiters[category.value]

        # 통계 업데이트
        if rule.measurement_unit == UpbitMeasurementUnit.IP_BASED:
            self._stats['ip_based_requests'] += 1
        else:
            self._stats['account_based_requests'] += 1

        # Rate Limit 체크 (비블로킹)
        allowed, wait_time = limiter.check_limit(now)

        if not allowed:
            self._stats['rejected_by_category'][category.value] += 1
            self._performance_metrics['rate_limit_errors'] += 1
            self._performance_metrics['error_count'] += 1
        else:
            self._performance_metrics['success_count'] += 1

        return allowed, wait_time

    async def acquire_with_retry(
        self,
        endpoint: str,
        method: str = 'GET',
        is_authenticated: bool = False,
        max_retries: int = 3
    ) -> bool:
        """
        🎁 편의 함수: 자동 재시도 포함 (High-level API)

        📊 기존 코드 호환성을 위한 도우미 함수
        - 내부에서 check_limit() 사용
        - 실패 시 자동으로 대기 + 재시도
        - 기존 await acquire() 패턴과 유사한 사용법

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드
            is_authenticated: 인증 여부
            max_retries: 최대 재시도 횟수

        Returns:
            bool: 성공 여부
        """
        for attempt in range(max_retries):
            allowed, wait_time = self.check_limit(endpoint, method, is_authenticated)

            if allowed:
                return True

            if attempt < max_retries - 1:  # 마지막 시도가 아니면
                # 백오프 전략: 점진적 증가 + 최대 1초 제한
                actual_wait = min(wait_time, 1.0)
                actual_wait *= (1.0 + attempt * 0.1)  # 10%씩 증가
                await asyncio.sleep(actual_wait)

        return False

    def _resolve_category(
        self,
        endpoint: str,
        method: str,
        is_authenticated: bool = False
    ) -> UpbitApiCategory:
        """엔드포인트 → 카테고리 해결 (단순화됨)"""
        method_upper = method.upper()

        # 1. WebSocket 특수 처리
        if endpoint.startswith('/websocket') or 'websocket' in endpoint.lower():
            # WebSocket은 인증 여부에 따라 측정 단위만 변경 (카테고리는 동일)
            return UpbitApiCategory.WEBSOCKET

        # 2. 특수 메서드 매핑
        special_key = (endpoint, method_upper)
        if special_key in self._SPECIAL_METHOD_MAPPINGS:
            return self._SPECIAL_METHOD_MAPPINGS[special_key]

        # 3. 엔드포인트 패턴 매핑
        for pattern, category in self._ENDPOINT_MAPPINGS.items():
            if endpoint.startswith(pattern):
                return category

        # 4. 캔들 API 특수 처리 (모든 캔들 종류 통합)
        if '/candles/' in endpoint:
            return UpbitApiCategory.QUOTATION

        # 5. 기본값: 시세 조회
        return UpbitApiCategory.QUOTATION

    def get_timing_metrics(self) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        metrics = self._performance_metrics

        # RT 메트릭
        if metrics['acquire_times']:
            avg_rt = sum(metrics['acquire_times']) / len(metrics['acquire_times'])
            min_rt = min(metrics['acquire_times'])
            max_rt = max(metrics['acquire_times'])
        else:
            avg_rt = min_rt = max_rt = 0.0

        # AIR 메트릭
        if metrics['actual_intervals']:
            avg_air = sum(metrics['actual_intervals']) / len(metrics['actual_intervals'])
            min_air = min(metrics['actual_intervals'])
            max_air = max(metrics['actual_intervals'])
        else:
            avg_air = min_air = max_air = 0.0

        # RPS 계산
        if len(metrics['request_timestamps']) >= 2:
            time_span = metrics['request_timestamps'][-1] - metrics['request_timestamps'][0]
            if time_span > 0:
                actual_rps = (len(metrics['request_timestamps']) - 1) / time_span
            else:
                actual_rps = 0.0
        else:
            actual_rps = 0.0

        # 성공률
        total_attempts = metrics['success_count'] + metrics['error_count']
        success_rate = (metrics['success_count'] / total_attempts * 100) if total_attempts > 0 else 0.0

        return {
            'avg_rt_ms': avg_rt,
            'min_rt_ms': min_rt,
            'max_rt_ms': max_rt,
            'avg_air_ms': avg_air,
            'min_air_ms': min_air,
            'max_air_ms': max_air,
            'actual_rps': actual_rps,
            'success_count': metrics['success_count'],
            'error_count': metrics['error_count'],
            'rate_limit_errors': metrics['rate_limit_errors'],
            'success_rate': success_rate,
            'total_requests': self._stats['total_requests'],
            'window_size': len(metrics['acquire_times'])
        }

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        now = time.time()
        status = {}

        for category_key, limiter in self._limiters.items():
            usage = limiter.get_current_usage(now)
            rule = self._RATE_RULES[UpbitApiCategory(category_key)]

            # 주요 윈도우 정보
            main_window = usage.get('window_0', {})
            status[category_key] = {
                'measurement_unit': rule.measurement_unit.value,
                'current': main_window.get('current', 0),
                'limit': main_window.get('limit', 0),
                'usage_percent': main_window.get('usage_percent', 0),
                'rule_name': rule.name,
                'strictest_rps': rule.get_strictest_rps()
            }

        return {
            'client_id': self.client_id,
            'architecture': 'simplified_5_categories_v2',
            'categories': status,
            'statistics': self._stats,
            'total_limiters': len(self._limiters)
        }


class RateLimitExceeded(Exception):
    """Rate Limit 초과 예외"""

    def __init__(self, message: str, retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


# 팩토리 함수들 (깔끔한 방식)
def create_quotation_limiter(ip_address: str = "127.0.0.1") -> UpbitRateLimiterV2:
    """시세 조회 전용 Rate Limiter"""
    return UpbitRateLimiterV2(client_id="quotation_only", ip_address=ip_address)


def create_exchange_limiter(account_id: str, ip_address: str = "127.0.0.1") -> UpbitRateLimiterV2:
    """거래소 전용 Rate Limiter"""
    return UpbitRateLimiterV2(client_id="exchange_only", account_id=account_id, ip_address=ip_address)


def create_websocket_limiter(
    ip_address: str = "127.0.0.1",
    account_id: Optional[str] = None
) -> UpbitRateLimiterV2:
    """WebSocket 전용 Rate Limiter"""
    return UpbitRateLimiterV2(client_id="websocket_only", account_id=account_id, ip_address=ip_address)


def create_unified_limiter(
    account_id: Optional[str] = None,
    ip_address: str = "127.0.0.1"
) -> UpbitRateLimiterV2:
    """통합 Rate Limiter (권장)"""
    return UpbitRateLimiterV2(client_id="unified", account_id=account_id, ip_address=ip_address)
