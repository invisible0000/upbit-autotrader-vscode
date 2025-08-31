"""
업비트 Rate Limiter V2 - Legacy 아키텍처 + 웜업 시스템 통합

🎯 핵심 설계 원칙:
- Legacy의 탄탄한 아키텍처 유지 (전역 제한, 멀티 윈도우, 카테고리 관리)
- 새로운 웜업 시스템 추가 (콜드 스타트 보상)
- Rate Limiter는 절대 실패하지 않음 (항상 적절한 대기시간 제공)

핵심 특징:
- 전역 제한: 모든 인스턴스가 동일한 제한 공유
- 멀티 윈도우: WebSocket 5 RPS + 100 RPM 동시 지원
- 체계적 카테고리: UpbitApiCategory Enum + 상세 매핑
- 내장 웜업: 콜드 스타트 시 점진적 성능 향상
"""

import asyncio
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("RateLimiterV2Legacy")


class UpbitApiCategory(Enum):
    """업비트 API 카테고리 - 완전한 지원"""
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
    """Rate Limit 규칙"""
    windows: List[RateWindow]
    category: UpbitApiCategory
    name: str

    def get_strictest_rps(self) -> float:
        """가장 엄격한 RPS 반환"""
        return min(w.requests_per_second for w in self.windows)


class CloudflareSlidingWindowWithWarmup:
    """
    Cloudflare Sliding Window + 웜업 시스템

    🎯 Legacy 기능 + 새로운 웜업:
    - 멀티 윈도우 지원 (WebSocket 5 RPS + 100 RPM)
    - 전역 공유 상태
    - 웜업 기반 콜드 스타트 보상
    - Rate Limiter는 절대 실패하지 않음
    """

    # 전역 공유 상태 (Legacy 호환)
    _global_limiters: Dict[str, 'CloudflareSlidingWindowWithWarmup'] = {}
    _global_lock = threading.Lock()

    def __init__(self, windows: List[RateWindow], limiter_id: str):
        self.windows = windows
        self.limiter_id = limiter_id

        # Cloudflare 멀티 윈도우 시스템
        self.window_data = {}
        for i, window in enumerate(windows):
            self.window_data[i] = {
                'current_count': 0,
                'previous_count': 0,
                'window_start_time': time.time(),
                'window_seconds': window.window_seconds,
                'max_requests': window.max_requests
            }

        # 웜업 시스템 (새로운 기능)
        self.warmup_history: Dict[int, List[float]] = {}  # 윈도우별 요청 히스토리
        self.warmup_factor = 0.5  # 초기 50% 성능
        self.is_cold_start = True
        self.warmup_requests = 0

        # 통계
        self.total_requests = 0
        self._lock = asyncio.Lock()

        # 전역 등록 (Legacy 호환)
        with self._global_lock:
            self._global_limiters[limiter_id] = self

    @classmethod
    def get_global_limiter(cls, limiter_id: str) -> Optional['CloudflareSlidingWindowWithWarmup']:
        """전역 Limiter 조회 (Legacy 호환)"""
        with cls._global_lock:
            return cls._global_limiters.get(limiter_id)

    @classmethod
    def get_all_global_usage(cls) -> Dict[str, Dict]:
        """모든 전역 Limiter 사용량 조회"""
        with cls._global_lock:
            usage = {}
            now = time.time()
            for limiter_id, limiter in cls._global_limiters.items():
                usage[limiter_id] = limiter.get_usage_info(now)
            return usage

    def _update_window_if_needed(self, window_id: int, now: float) -> None:
        """윈도우 갱신 (Cloudflare 공식 로직)"""
        data = self.window_data[window_id]
        window_seconds = data['window_seconds']
        elapsed = now - data['window_start_time']

        if elapsed >= window_seconds:
            periods_passed = int(elapsed // window_seconds)
            if periods_passed == 1:
                data['previous_count'] = data['current_count']
            else:
                data['previous_count'] = 0

            data['current_count'] = 0
            data['window_start_time'] = now

    def _update_warmup_status(self, window_id: int, now: float) -> float:
        """
        웜업 상태 업데이트 (새로운 기능)

        콜드 스타트 시 점진적 성능 향상
        초기 20개 요청 동안 50% → 100% 성능으로 웜업
        """
        if window_id not in self.warmup_history:
            self.warmup_history[window_id] = []

        history = self.warmup_history[window_id]
        window_seconds = self.windows[window_id].window_seconds

        # 윈도우 범위 내 요청만 유지
        cutoff_time = now - window_seconds * 2
        history[:] = [req_time for req_time in history if req_time > cutoff_time]

        # 웜업 팩터 계산 (20개 요청까지 점진적 증가)
        warmup_requests = len(history)
        if warmup_requests < 20:
            self.warmup_factor = 0.5 + (warmup_requests / 20) * 0.5
            self.is_cold_start = True
        else:
            self.warmup_factor = 1.0
            self.is_cold_start = False

        return self.warmup_factor

    def calculate_optimal_wait_time(self, now: float) -> Tuple[bool, float, Dict]:
        """
        🎯 새로운 접근: 항상 성공, 최적 대기시간만 계산

        모든 윈도우를 체크하여 가장 긴 대기시간 적용
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
                # 웜업 중에는 더 보수적으로 (완료 후에는 최적화)
                safety_factor = 1.1 if self.is_cold_start else 0.9

                slots_per_second = effective_max_requests / window_seconds
                wait_for_next_slot = (1.0 / slots_per_second) * safety_factor

                # 최대 대기 시간 제한
                max_allowed_wait = window_seconds * 0.4
                wait_time = min(wait_for_next_slot, max_allowed_wait)

                max_wait_needed = max(max_wait_needed, wait_time)

            # 윈도우 상태 저장
            status_info['window_states'].append({
                'window_id': window_id,
                'window_seconds': window_seconds,
                'max_requests': max_requests,
                'current': data['current_count'],
                'previous': data['previous_count'],
                'estimated_rate': estimated_rate,
                'effective_limit': effective_max_requests,
                'usage_percent': (estimated_rate / effective_max_requests) * 100 if effective_max_requests > 0 else 0
            })

        return True, max_wait_needed, status_info

    async def acquire(self, max_retries: int = 3) -> bool:
        """Rate Limit 토큰 획득 (항상 성공)"""
        async with self._lock:
            now = time.time()
            allowed, wait_time, status_info = self.calculate_optimal_wait_time(now)

            # 대기시간이 있다면 적용
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # 모든 윈도우의 카운트 업데이트 및 웜업 히스토리 추가
            for window_id in range(len(self.windows)):
                self.window_data[window_id]['current_count'] += 1

                # 웜업 히스토리에 추가
                if window_id in self.warmup_history:
                    self.warmup_history[window_id].append(time.time())

            self.total_requests += 1
            if self.is_cold_start:
                self.warmup_requests += 1

            return True  # 항상 성공

    async def acquire_with_status(self) -> Tuple[bool, Dict]:
        """상세 상태 정보와 함께 토큰 획득"""
        async with self._lock:
            now = time.time()
            allowed, wait_time, status_info = self.calculate_optimal_wait_time(now)

            # 대기시간이 있다면 적용
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # 모든 윈도우의 카운트 업데이트
            for window_id in range(len(self.windows)):
                self.window_data[window_id]['current_count'] += 1

                # 웜업 히스토리에 추가
                if window_id in self.warmup_history:
                    self.warmup_history[window_id].append(time.time())

            self.total_requests += 1
            if self.is_cold_start:
                self.warmup_requests += 1

            # 최종 상태 정보 업데이트
            status_info['wait_time_applied'] = wait_time
            status_info['total_requests'] = self.total_requests
            status_info['warmup_requests'] = self.warmup_requests

            return True, status_info

    def get_usage_info(self, now: float) -> Dict[str, Any]:
        """현재 사용량 정보 반환 (Legacy 호환)"""
        usage_info = {}

        for i, window in enumerate(self.windows):
            self._update_window_if_needed(i, now)

            data = self.window_data[i]
            elapsed = now - data['window_start_time']

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


class UpbitRateLimiterV2:
    """
    업비트 Rate Limiter V2 - Legacy 아키텍처 + 웜업 시스템

    🎯 핵심 특징:
    - Legacy의 탄탄한 아키텍처 유지
    - 전역 제한 지원 (모든 인스턴스 영향)
    - 멀티 윈도우 지원 (WebSocket 등)
    - 체계적 카테고리 관리
    - 새로운 웜업 시스템
    """

    # 업비트 공식 Rate Limit 규칙 (Legacy 호환)
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

    # 엔드포인트 → 카테고리 매핑 (Legacy 호환)
    ENDPOINT_MAPPINGS = {
        # 시세 조회
        '/market/all': UpbitApiCategory.QUOTATION,
        '/candles/': UpbitApiCategory.QUOTATION,
        '/ticker': UpbitApiCategory.QUOTATION,
        '/tickers': UpbitApiCategory.QUOTATION,
        '/trades/ticks': UpbitApiCategory.QUOTATION,
        '/orderbook': UpbitApiCategory.QUOTATION,

        # 기본 거래소
        '/accounts': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/orders/chance': UpbitApiCategory.EXCHANGE_DEFAULT,
        '/order': UpbitApiCategory.EXCHANGE_DEFAULT,
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
        """Rate Limiter 초기화"""
        self.user_type = user_type
        self.client_id = f"upbit_v2_{user_type}_{id(self)}"

        # 카테고리별 Limiter 생성 (전역 공유)
        self.limiters: Dict[UpbitApiCategory, CloudflareSlidingWindowWithWarmup] = {}
        for category, rule in self.UPBIT_RULES.items():
            limiter_id = f"global_{category.value}"

            # 전역에서 기존 Limiter 확인
            existing_limiter = CloudflareSlidingWindowWithWarmup.get_global_limiter(limiter_id)
            if existing_limiter:
                self.limiters[category] = existing_limiter
                logger.debug(f"재사용 전역 Limiter: {limiter_id}")
            else:
                self.limiters[category] = CloudflareSlidingWindowWithWarmup(
                    windows=rule.windows,
                    limiter_id=limiter_id
                )
                logger.debug(f"새 전역 Limiter 생성: {limiter_id}")

        # 통계
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'category_counts': {cat.value: 0 for cat in UpbitApiCategory}
        }

    def resolve_category(self, endpoint: str, method: str = 'GET') -> UpbitApiCategory:
        """엔드포인트 → 카테고리 해결 (Legacy 호환)"""
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
        """Rate Limit 토큰 획득 (항상 성공)"""
        # 카테고리 결정
        category = self.resolve_category(endpoint, method)

        # 통계 업데이트
        self.stats['total_requests'] += 1
        self.stats['category_counts'][category.value] += 1

        # Rate Limit 획득 (항상 성공)
        limiter = self.limiters[category]
        success = await limiter.acquire()

        if success:
            self.stats['successful_requests'] += 1
        else:
            # 이론적으로는 발생하지 않음 (항상 성공)
            self.stats['failed_requests'] += 1
            logger.warning(f"Rate limiter returned failure (unexpected): {category.value}")

        logger.debug(f"Rate limit acquired: {endpoint} → {category.value}")

    async def acquire_with_status(self, endpoint: str, method: str = 'GET') -> Tuple[bool, Dict]:
        """상세 상태 정보와 함께 토큰 획득"""
        # 카테고리 결정
        category = self.resolve_category(endpoint, method)

        # 통계 업데이트
        self.stats['total_requests'] += 1
        self.stats['category_counts'][category.value] += 1

        # Rate Limit 획득 (상태 포함)
        limiter = self.limiters[category]
        success, status = await limiter.acquire_with_status()

        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1

        # 상태에 카테고리 정보 추가
        status['category'] = category.value
        status['endpoint'] = endpoint

        return success, status

    def get_status(self) -> Dict[str, Any]:
        """현재 Rate Limiter 상태 조회 (Legacy 호환)"""
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
                'strictest_rps': f"{strictest_rps:.2f}",
                'windows_count': len(rule.windows)  # 멀티 윈도우 정보
            }

        return {
            'client_id': self.client_id,
            'user_type': self.user_type,
            'architecture': 'legacy_with_warmup',
            'global_sharing': True,  # 전역 공유 지원
            'categories': status,
            'statistics': self.stats,
            'total_limiters': len(self.limiters)
        }

    @classmethod
    def get_global_status(cls) -> Dict[str, Any]:
        """모든 전역 Limiter 상태 조회"""
        return CloudflareSlidingWindowWithWarmup.get_all_global_usage()


class RateLimitExceededException(Exception):
    """Rate Limit 초과 예외 (Legacy 호환)"""

    def __init__(self, message: str, retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


# ================================================================
# 팩토리 함수들 (Legacy 호환)
# ================================================================

def create_upbit_public_limiter() -> UpbitRateLimiterV2:
    """업비트 공개 API 전용 Rate Limiter 생성"""
    return UpbitRateLimiterV2(user_type="anonymous")


def create_upbit_private_limiter(client_id: str) -> UpbitRateLimiterV2:
    """업비트 프라이빗 API 전용 Rate Limiter 생성"""
    return UpbitRateLimiterV2(user_type="authenticated")


def create_upbit_unified_limiter(access_key: Optional[str] = None) -> UpbitRateLimiterV2:
    """업비트 통합 Rate Limiter 생성 (권장)"""
    user_type = "authenticated" if access_key else "anonymous"
    return UpbitRateLimiterV2(user_type=user_type)
