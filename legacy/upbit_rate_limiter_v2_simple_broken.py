"""
업비트 Rate Limiter v2 - 웜업 시스템 (2025.01.15)

🎯 새로운 접근: Rate Limiter는 절대 실패하지 않음
- 적절한 대기시간만 계산하여 클라이언트가 요청 타이밍 조절
- PRG는 Cloudflare 내부 웜업 메커니즘으로 작동 (콜드 스타트 보상)
- 429 에러는 클라이언트 측에서 감지, Rate Limiter는 예방만 담당

Cloudflare + Internal Warmup Architecture:
┌─────────────────────────────────────────┐
│ CloudflareSlidingWindow                 │
│  ├── Sliding Window Counter (정확성)   │
│  ├── Internal Warmup (콜드 스타트 보상) │
│  └── Optimal Wait Time (실패 없음)     │
└─────────────────────────────────────────┘
"""

import asyncio
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Tuple
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("RateLimiterV2Clean")


@dataclass(frozen=True)
class WindowConfig:
    """Rate Limit 윈도우 설정"""
    max_requests: int
    window_seconds: float


class CloudflareSlidingWindow:
    """
    Cloudflare Sliding Window + Internal Warmup System

    🎯 핵심 변경:
    - Rate Limiter는 절대 실패하지 않음 (항상 대기시간만 반환)
    - PRG는 내부 웜업 메커니즘으로 작동 (콜드 스타트 시 성능 점진적 증가)
    - 초기 30개 요청 동안 50% → 100% 성능으로 웜업
    """

    def __init__(self, windows: List[WindowConfig]):
        self.windows = windows
        self._lock = asyncio.Lock()
        self.total_requests = 0

        # 각 윈도우별 카운터 (Cloudflare 공식 알고리즘)
        self.window_data = []
        for window in windows:
            self.window_data.append({
                'window_seconds': window.window_seconds,
                'max_requests': window.max_requests,
                'window_start_time': time.time(),
                'current_count': 0,
                'previous_count': 0
            })

        # 내부 웜업 시스템 (기존 PRG 대체)
        self.warmup_history: Dict[int, List[float]] = {}  # 윈도우별 요청 시간 히스토리
        self.warmup_factor = 0.5  # 초기 50% 성능
        self.is_cold_start = True
        self.warmup_requests = 0

    def _update_window_if_needed(self, window_id: int, now: float) -> None:
        """윈도우 갱신 (Cloudflare 공식 로직)"""
        data = self.window_data[window_id]
        window_seconds = data['window_seconds']
        elapsed = now - data['window_start_time']

        if elapsed >= window_seconds:
            # 윈도우 완전히 넘어감 → 이전 카운트로 이동
            periods_passed = int(elapsed // window_seconds)
            if periods_passed == 1:
                data['previous_count'] = data['current_count']
            else:
                data['previous_count'] = 0

            data['current_count'] = 0
            data['window_start_time'] = now

    def _update_warmup_status(self, window_id: int, now: float) -> float:
        """
        내장 PRG: Cloudflare 웜업 상태 업데이트

        콜드 스타트 시 점진적 성능 향상
        초기 20개 요청 동안 50% → 100% 성능으로 웜업

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

        # 웜업 팩터 계산 (20개 요청까지 점진적 증가)
        warmup_requests = len(history)
        if warmup_requests < 20:
            # 0.5에서 1.0까지 선형 증가
            self.warmup_factor = 0.5 + (warmup_requests / 20) * 0.5
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
                # 웜업 중에는 더 보수적으로 (완료 후에는 최적화)
                safety_factor = 1.1 if self.is_cold_start else 0.9
                
                slots_per_second = effective_max_requests / window_seconds
                wait_for_next_slot = (1.0 / slots_per_second) * safety_factor

                # 최대 대기 시간 제한
                max_allowed_wait = window_seconds * 0.4  # 50% → 40%로 단축
                wait_time = min(wait_for_next_slot, max_allowed_wait)
                
                max_wait_needed = max(max_wait_needed, wait_time)            # 윈도우 상태 저장
            status_info['window_states'].append({
                'window_id': window_id,
                'current': data['current_count'],
                'previous': data['previous_count'],
                'estimated_rate': estimated_rate,
                'effective_limit': effective_max_requests,
                'usage_percent': (estimated_rate / effective_max_requests) * 100 if effective_max_requests > 0 else 0
            })

        return True, max_wait_needed, status_info

    async def acquire(self) -> bool:
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

    async def acquire_with_status(self) -> Tuple[bool, Dict]:
        """상세 상태 정보와 함께 토큰 획득"""
        async with self._lock:
            now = time.time()
            allowed, wait_time, status_info = self.calculate_optimal_wait_time(now)

            # 대기시간이 있다면 적용
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                # 대기 후 상태 재계산
                allowed, wait_time, status_info = self.calculate_optimal_wait_time(now)

            # 요청 카운트 업데이트 및 웜업 히스토리 추가
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


class UpbitRateLimiterV2:
    """
    업비트 API Rate Limiter v2 - 웜업 시스템

    5개 단순화된 카테고리로 관리
    """

    # 6개 카테고리 (일괄 취소 추가)
    RATE_LIMITS = {
        'QUOTATION': WindowConfig(max_requests=10, window_seconds=1.0),       # 시세 조회: 10 RPS
        'ACCOUNT': WindowConfig(max_requests=5, window_seconds=1.0),          # 계좌 조회: 5 RPS
        'ORDER': WindowConfig(max_requests=8, window_seconds=1.0),            # 주문: 8 RPS
        'CANDLE': WindowConfig(max_requests=10, window_seconds=1.0),          # 캔들: 10 RPS
        'BULK_CANCEL': WindowConfig(max_requests=1, window_seconds=2.0),      # 일괄 취소: 0.5 RPS (매우 엄격)
        'EXCHANGE_DEFAULT': WindowConfig(max_requests=30, window_seconds=1.0)  # 기타: 30 RPS
    }

    # 엔드포인트 → 카테고리 매핑 (간소화, 중복 제거)
    ENDPOINT_MAPPING = {
        # 시세 (실시간 데이터)
        '/v1/ticker': 'QUOTATION',
        '/v1/orderbook': 'QUOTATION',
        '/v1/trades/ticks': 'QUOTATION',

        # 계좌 (조회만)
        '/v1/accounts': 'ACCOUNT',

        # 일괄 취소 (매우 엄격한 제한)
        '/v1/orders/cancel': 'BULK_CANCEL',  # 일괄 취소: 0.5 RPS

        # 캔들
        '/v1/candles/minutes/1': 'CANDLE',
        '/v1/candles/minutes/5': 'CANDLE',
        '/v1/candles/minutes/15': 'CANDLE',
        '/v1/candles/days': 'CANDLE',
    }

    def __init__(self):
        self._limiters = {}
        self._lock = threading.Lock()

    def _get_category(self, endpoint: str, method: str = 'GET') -> str:
        """엔드포인트 → 카테고리 결정"""
        # 정확한 매핑 확인
        if endpoint in self.ENDPOINT_MAPPING:
            return self.ENDPOINT_MAPPING[endpoint]

        # 패턴 매칭
        if '/candles/' in endpoint:
            return 'CANDLE'
        elif endpoint in ['/v1/accounts', '/v1/orders']:
            return 'ACCOUNT'
        elif endpoint == '/v1/order' and method in ['POST', 'DELETE']:
            return 'ORDER'
        elif endpoint.startswith('/v1/'):
            return 'EXCHANGE_DEFAULT'

        return 'QUOTATION'  # 기본값

    def _get_limiter(self, category: str) -> CloudflareSlidingWindow:
        """카테고리별 Rate Limiter 인스턴스 반환"""
        with self._lock:
            if category not in self._limiters:
                if category in self.RATE_LIMITS:
                    config = self.RATE_LIMITS[category]
                    self._limiters[category] = CloudflareSlidingWindow([config])
                else:
                    # 알 수 없는 카테고리 → 기본값 사용
                    config = self.RATE_LIMITS['EXCHANGE_DEFAULT']
                    self._limiters[category] = CloudflareSlidingWindow([config])

            return self._limiters[category]

    async def acquire(self, endpoint: str, method: str = 'GET') -> None:
        """
        Rate Limit 토큰 획득 (항상 성공)

        새로운 웜업 시스템 기반으로 적절한 대기시간 적용
        """
        category = self._get_category(endpoint, method)
        limiter = self._get_limiter(category)

        success = await limiter.acquire()
        if not success:
            logger.warning(f"Rate limiter returned failure (unexpected): {category}")

        logger.debug(f"Rate limit acquired: {endpoint} → {category}")

    async def acquire_with_status(self, endpoint: str, method: str = 'GET') -> Tuple[bool, Dict]:
        """상세 상태 정보와 함께 토큰 획득"""
        category = self._get_category(endpoint, method)
        limiter = self._get_limiter(category)

        success, status = await limiter.acquire_with_status()
        status['category'] = category
        status['endpoint'] = endpoint

        return success, status
