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
    업비트 최적화 Cloudflare Sliding Window + 내장 PRG(PreemptiveRateGuard)

    🎯 올바른 아키텍처:
    - Rate Limiter는 절대 실패하지 않음 (항상 적절한 대기시간 제공)
    - PRG는 Cloudflare 내부 웜업/콜드스타트 메커니즘
    - 429 에러는 클라이언트(테스트)에서 별도 감지

    공식 Cloudflare 블로그 기반:
    https://blog.cloudflare.com/counting-things-a-lot-of-different-things/

    핵심 공식:
    rate = previous_count * ((window_seconds - elapsed) / window_seconds) + current_count

    특징:
    - 메모리 효율적: 윈도우당 2개 카운터만 사용
    - 정확도 99.997% (Cloudflare 검증)
    - 간단하고 빠른 계산
    - 내장 PRG: 콜드스타트 시 점진적 웜업
    """

    def __init__(self, windows: List[RateWindow], limiter_id: str):
        self.windows = windows
        self.limiter_id = limiter_id

        # Cloudflare 2-카운터 시스템
        self.window_data = {}
        for i, window in enumerate(windows):
            self.window_data[i] = {
                'current_count': 0,
                'previous_count': 0,
                'window_start_time': time.time(),
                'window_seconds': window.window_seconds,
                'max_requests': window.max_requests
            }

        # 내장 PRG: Cloudflare 웜업 시스템
        self.warmup_history = {}  # {window_id: [request_times...]}
        self.is_cold_start = True  # 콜드 스타트 상태
        self.warmup_factor = 1.0   # 1.0 = 완전 웜업, 0.5 = 50% 성능

        # 통계
        self.total_requests = 0
        self.warmup_requests = 0

        self._lock = asyncio.Lock()

    def _update_window_if_needed(self, window_id: int, now: float) -> None:
        """윈도우가 경과되었다면 previous/current 카운터 업데이트"""
        data = self.window_data[window_id]
        elapsed = now - data['window_start_time']
        window_seconds = data['window_seconds']

        if elapsed >= window_seconds:
            # 완전히 지난 윈도우 수 계산
            windows_passed = int(elapsed // window_seconds)

            if windows_passed == 1:
                # 정확히 1개 윈도우가 지남: current → previous
                data['previous_count'] = data['current_count']
            else:
                # 2개 이상 윈도우가 지남: previous는 0
                data['previous_count'] = 0

            # current 리셋 및 시작 시간 업데이트
            data['current_count'] = 0
            data['window_start_time'] += windows_passed * window_seconds

    def _update_warmup_status(self, window_id: int, now: float) -> float:
        """
        내장 PRG: Cloudflare 웜업 상태 업데이트

        콜드 스타트 시 점진적 성능 향상
        초기 30개 요청 동안 50% → 100% 성능으로 웜업

        Args:
            window_id: 윈도우 인덱스
            now: 현재 시간

        Returns:
            float: 웜업 팩터 (0.5~1.0)
        """
        if window_id not in self.warmup_history:
            self.warmup_history[window_id] = []

        history = self.warmup_history[window_id]
        window_seconds = self.windows[window_id].window_seconds

        # 윈도우 범위 내 요청만 유지
        cutoff_time = now - window_seconds * 2  # 2윈도우 범위로 확장
        history[:] = [req_time for req_time in history if req_time > cutoff_time]

        # 웜업 팩터 계산 (30개 요청까지 점진적 증가)
        warmup_requests = len(history)
        if warmup_requests < 30:
            # 0.5에서 1.0까지 선형 증가
            self.warmup_factor = 0.5 + (warmup_requests / 30) * 0.5
            self.is_cold_start = True
        else:
            self.warmup_factor = 1.0
            self.is_cold_start = False

        return self.warmup_factor

    def calculate_optimal_wait_time(self, now: float) -> Tuple[bool, float, Dict]:
        """
        🎯 새로운 접근: 항상 성공, 최적 대기시간만 계산

        Rate Limiter는 절대 실패하지 않음
        적절한 대기시간을 계산해서 클라이언트가 요청 타이밍 조절

        Returns:
            Tuple[bool, float, Dict]: (항상 True, 대기시간, 상태정보)
        """
        max_wait_needed = 0.0
        status_info = {
            'warmup_factor': 1.0,
            'is_cold_start': False,
            'window_states': [],
            'total_requests': self.total_requests
        }

        for window_id, window in enumerate(self.windows):
            # 1. 웜업 상태 업데이트
            warmup_factor = self._update_warmup_status(window_id, now)
            status_info['warmup_factor'] = warmup_factor
            status_info['is_cold_start'] = self.is_cold_start

            # 2. 윈도우 업데이트
            self._update_window_if_needed(window_id, now)

            data = self.window_data[window_id]
            elapsed = now - data['window_start_time']
            window_seconds = data['window_seconds']
            max_requests = data['max_requests']

            # 3. 웜업 적용 (콜드 스타트 시 성능 제한)
            effective_max_requests = max_requests * warmup_factor

            # 4. Cloudflare 공식 sliding window 계산
            remaining_ratio = (window_seconds - elapsed) / window_seconds
            estimated_rate = data['previous_count'] * remaining_ratio + data['current_count']

            # 5. 대기시간 계산 (실패 아님, 조절만)
            if estimated_rate + 1 > effective_max_requests:
                # 웜업 중에는 더 보수적으로
                safety_factor = 1.2 if self.is_cold_start else 1.0

                remaining_time = window_seconds - elapsed
                slots_per_second = effective_max_requests / window_seconds
                wait_for_next_slot = (1.0 / slots_per_second) * safety_factor

                # 최대 대기 시간 제한
                max_allowed_wait = window_seconds * 0.5
                wait_time = min(wait_for_next_slot, max_allowed_wait)

                max_wait_needed = max(max_wait_needed, wait_time)

            # 윈도우 상태 저장
            status_info['window_states'].append({
                'window_id': window_id,
                'current': data['current_count'],
                'previous': data['previous_count'],
                'estimated_rate': estimated_rate,
                'effective_limit': effective_max_requests,
                'usage_percent': (estimated_rate / effective_max_requests) * 100 if effective_max_requests > 0 else 0
            })

        return True, max_wait_needed, status_info

    async def acquire(self, max_retries: int = 3) -> bool:
        """
        Rate Limit 토큰 획득 (항상 성공)

        웜업 기반 대기시간 적용 후 항상 성공 반환
        """
        async with self._lock:
            now = time.time()
            allowed, wait_time, status_info = self.calculate_optimal_wait_time(now)

            # 대기시간이 있다면 적용
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # 요청 카운트 업데이트 및 웜업 히스토리 추가
            for window_id in range(len(self.windows)):
                self.window_data[window_id]['current_count'] += 1

                # 웜업 히스토리에 추가
                if window_id in self.warmup_history:
                    self.warmup_history[window_id].append(time.time())

            self.total_requests += 1
            if self.is_cold_start:
                self.warmup_requests += 1

            return True  # 항상 성공

    def check_limit(self, now: float) -> Tuple[bool, float, Optional[Dict]]:
        """
        통합된 Rate Limiting 체크 (PRG + Cloudflare 병렬 동작)

        ✨ 핵심: PRG와 Cloudflare 대기시간을 합산하여 강한 지연 제공

        Returns:
            Tuple[bool, float, Optional[Dict]]: (허용 여부, PRG+Cloudflare 합산 대기시간, PRG 상태)
        """
        max_prg_wait = 0.0
        max_cloudflare_wait = 0.0
        prg_status = None
        cloudflare_blocked = False

        for window_id, window in enumerate(self.windows):
            # 1. PreemptiveRateGuard 보상 대기시간 계산 (항상 성공, 히스토리 업데이트)
            preemptive_allowed, preemptive_wait, current_prg_status = self._preemptive_rate_guard(window_id, now)

            # PRG 상태 저장 (첫 번째 윈도우 또는 백오프가 있는 경우)
            if prg_status is None or current_prg_status.get('backoff_ms', 0) > 0:
                prg_status = current_prg_status
                prg_status['window_id'] = window_id

            # PRG 보상 대기시간 누적
            max_prg_wait = max(max_prg_wait, preemptive_wait)

            # 2. Cloudflare 알고리즘 병렬 확인 (독립적으로 계산)
            # 윈도우 업데이트
            self._update_window_if_needed(window_id, now)

            data = self.window_data[window_id]
            elapsed = now - data['window_start_time']
            window_seconds = data['window_seconds']
            max_requests = data['max_requests']

            # Cloudflare 공식 sliding window 계산
            remaining_ratio = (window_seconds - elapsed) / window_seconds
            estimated_rate = data['previous_count'] * remaining_ratio + data['current_count']

            # Cloudflare 제한 확인 (새 요청 1개 추가 시)
            if estimated_rate + 1 > max_requests:
                cloudflare_blocked = True
                # Cloudflare 대기 시간 계산
                remaining_time = window_seconds - elapsed

                # 방법 1: 균등 분배 방식 (더 안정적)
                slots_per_second = max_requests / window_seconds
                wait_for_next_slot = 1.0 / slots_per_second

                # 방법 2: 여유 공간 기반 (더 정확)
                available_slots = max_requests - estimated_rate
                if available_slots > 0:
                    slot_wait = remaining_time / available_slots
                else:
                    slot_wait = remaining_time

                # 두 방법 중 더 적은 대기 시간 선택
                cloudflare_wait = min(wait_for_next_slot, slot_wait)

                # 최대 대기 시간 제한 (윈도우 크기의 50%)
                max_allowed_wait = window_seconds * 0.5
                cloudflare_wait = min(cloudflare_wait, max_allowed_wait)

                max_cloudflare_wait = max(max_cloudflare_wait, cloudflare_wait)

        # ✨ 핵심 변경: PRG + Cloudflare 대기시간 합산
        total_wait_time = max_prg_wait + max_cloudflare_wait

        # PRG 상태에 Cloudflare 정보 추가
        if prg_status:
            prg_status['cloudflare_wait'] = max_cloudflare_wait
            prg_status['prg_wait'] = max_prg_wait
            prg_status['total_wait'] = total_wait_time
            prg_status['cloudflare_blocked'] = cloudflare_blocked

        if total_wait_time > 0:
            return False, total_wait_time, prg_status

        # 허용: 모든 윈도우의 current_count 증가 (히스토리는 PRG에서 이미 업데이트됨)
        for window_id in range(len(self.windows)):
            self.window_data[window_id]['current_count'] += 1

        return True, 0.0, prg_status

    async def acquire(self, max_retries: int = 3) -> bool:
        """
        Rate Limit 토큰 획득 (자동 재시도)

        Args:
            max_retries: 최대 재시도 횟수

        Returns:
            bool: 성공 여부
        """
        async with self._lock:
            for attempt in range(max_retries):
                now = time.time()
                allowed, wait_time, _ = self.check_limit(now)

                if allowed:
                    return True

                if attempt < max_retries - 1:
                    # 백오프 대기: 계산된 대기시간 + 약간의 여유
                    actual_wait = min(wait_time * 1.1, 2.0)  # 최대 2초 제한
                    await asyncio.sleep(actual_wait)

            return False

    async def acquire_with_prg_status(self, max_retries: int = 3) -> Tuple[bool, Dict]:
        """
        PRG 상태 추적을 포함한 Rate Limit 토큰 획득

        Returns:
            Tuple[bool, Dict]: (성공 여부, PRG 상태 정보)
        """
        prg_status = {
            'prg_attempts': 0,
            'total_backoff_time': 0.0,
            'max_backoff': 0.0,
            'backoff_details': [],
            'final_prg_info': None
        }

        async with self._lock:
            for attempt in range(max_retries):
                now = time.time()
                allowed, wait_time, current_prg_info = self.check_limit(now)

                # PRG 정보 업데이트
                if current_prg_info:
                    prg_status['final_prg_info'] = current_prg_info

                if allowed:
                    return True, prg_status

                # PRG 백오프 추적
                if current_prg_info and current_prg_info.get('backoff_ms', 0) > 0:
                    prg_status['prg_attempts'] = current_prg_info.get('attempts', 0)

                actual_wait = min(wait_time * 1.1, 2.0)
                prg_status['total_backoff_time'] += actual_wait
                prg_status['max_backoff'] = max(prg_status['max_backoff'], actual_wait)
                prg_status['backoff_details'].append({
                    'attempt': attempt + 1,
                    'calculated_wait': wait_time * 1000,  # ms
                    'actual_wait': actual_wait * 1000,     # ms
                    'prg_backoff': current_prg_info.get('backoff_ms', 0) if current_prg_info else 0
                })

                if attempt < max_retries - 1:
                    await asyncio.sleep(actual_wait)

            return False, prg_status

    def get_usage_info(self, now: float) -> Dict[str, Any]:
        """현재 사용량 정보 반환"""
        usage_info = {}

        for i, window in enumerate(self.windows):
            # 윈도우 업데이트
            self._update_window_if_needed(i, now)

            data = self.window_data[i]
            elapsed = now - data['window_start_time']

            # 현재 예상 사용률 계산
            remaining_ratio = (data['window_seconds'] - elapsed) / data['window_seconds']
            estimated_rate = data['previous_count'] * remaining_ratio + data['current_count']
            usage_percent = (estimated_rate / window.max_requests) * 100

            usage_info[f'window_{i}'] = {
                'window_seconds': window.window_seconds,
                'limit': window.max_requests,
                'current': data['current_count'],
                'previous': data['previous_count'],
                'estimated_rate': estimated_rate,
                'usage_percent': usage_percent,
                'rps': window.requests_per_second,
                'elapsed_in_window': elapsed
            }

        return usage_info

    def get_debug_info(self) -> List[str]:
        """디버그 정보 반환"""
        debug_info = []
        now = time.time()

        for i, window in enumerate(self.windows):
            data = self.window_data[i]
            elapsed = now - data['window_start_time']
            remaining_ratio = (data['window_seconds'] - elapsed) / data['window_seconds']
            estimated_rate = data['previous_count'] * remaining_ratio + data['current_count']

            debug_info.append(
                f"윈도우 {i}: current={data['current_count']}, "
                f"previous={data['previous_count']}, "
                f"elapsed={elapsed:.3f}s, "
                f"ratio={remaining_ratio:.3f}, "
                f"estimated={estimated_rate:.2f}/{data['max_requests']}"
            )

        return debug_info


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

        # Rate Limit 획득 (더 관대한 재시도)
        limiter = self.limiters[category]
        success = await limiter.acquire(max_retries=5)  # 3→5 증가

        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
            # 계산된 대기 시간으로 더 정확한 retry_after 제공
            now = time.time()
            _, wait_time, _ = limiter.check_limit(now)
            raise RateLimitExceededException(
                f"Rate limit exceeded for {category.value}",
                retry_after=wait_time
            )

    async def acquire_with_prg_status(self, endpoint: str, method: str = 'GET') -> Tuple[bool, Dict]:
        """
        PRG 상태 추적을 포함한 Rate Limit 토큰 획득

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드

        Returns:
            Tuple[bool, Dict]: (성공 여부, PRG 상태 정보)
        """
        # 카테고리 결정
        category = self.resolve_category(endpoint, method)

        # 통계 업데이트
        self.stats['total_requests'] += 1
        self.stats['category_counts'][category.value] += 1

        # Rate Limit 획득 (PRG 상태 포함)
        limiter = self.limiters[category]
        success, prg_status = await limiter.acquire_with_prg_status(max_retries=5)

        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1

        return success, prg_status

    def check_limit(self, endpoint: str, method: str = 'GET') -> Tuple[bool, float]:
        """
        Rate Limit 순수 체크 (비블로킹) - 호환성 유지

        Args:
            endpoint: API 엔드포인트
            method: HTTP 메서드

        Returns:
            Tuple[bool, float]: (허용 여부, 대기 시간)
        """
        category = self.resolve_category(endpoint, method)
        limiter = self.limiters[category]

        now = time.time()
        allowed, wait_time, _ = limiter.check_limit(now)
        return allowed, wait_time

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
