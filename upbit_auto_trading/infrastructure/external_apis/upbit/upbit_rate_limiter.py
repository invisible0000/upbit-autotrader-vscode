"""
업비트 전용 통합 Rate Limiter

업비트 공식 문서의 복잡한 Rate Limit 규칙을 완벽 지원:
- 전역 제한: 초당 10회 (모든 REST API)
- 그룹별 제한: Quotation(30회/초), Order(8회/초), Order-cancel-all(1회/2초) 등
- 엔드포인트별 자동 그룹 매핑
- Remaining-Req 헤더 기반 서버 상태 추적
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class UpbitRateLimitGroup(Enum):
    """업비트 API Rate Limit 그룹 (공식 문서 기준)"""
    GLOBAL = "global"                # 전역 제한: 초당 10회
    QUOTATION = "quotation"          # 시세 조회: 초당 30회
    EXCHANGE_DEFAULT = "exchange_default"  # 거래소 기본: 초당 30회
    ORDER = "order"                  # 주문: 초당 8회
    ORDER_CANCEL_ALL = "order_cancel_all"  # 전체 취소: 2초당 1회
    WEBSOCKET_CONNECT = "websocket_connect"  # WebSocket 연결: 초당 5회
    WEBSOCKET_MESSAGE = "websocket_message"  # WebSocket 메시지: 초당 5회


class RateLimitStrategy(Enum):
    """Rate Limiting 알고리즘 전략"""
    CLOUDFLARE_SLIDING_WINDOW = "cloudflare_sliding_window"     # Cloudflare 방식 (정확성 중시)
    AIOLIMITER_OPTIMIZED = "aiolimiter_optimized"              # aiolimiter 최적화 (성능 중시)
    HYBRID_FAST = "hybrid_fast"                                # 하이브리드 (속도+정확성)
    LEGACY_CONSERVATIVE = "legacy_conservative"                # Legacy 방식 (최고 안전성)
    RESPONSE_INTERVAL_SIMPLE = "response_interval_simple"      # 단순 응답 기반 간격 제어
    SMART_RESPONSE_ADAPTIVE = "smart_response_adaptive"        # 스마트 응답 적응형 제어


@dataclass
class UpbitRateLimitRule:
    """업비트 Rate Limit 규칙"""
    requests_per_second: int
    requests_per_minute: int
    window_seconds: int = 1  # 시간 윈도우 (order-cancel-all은 2초)
    max_requests_per_window: int = 0  # 윈도우당 최대 요청

    def __post_init__(self):
        if self.max_requests_per_window == 0:
            self.max_requests_per_window = self.requests_per_second * self.window_seconds


class UpbitRateLimiter:
    """
    업비트 전용 통합 Rate Limiter

    특징:
    - 업비트 공식 Rate Limit 규칙 완벽 지원
    - 엔드포인트별 자동 그룹 매핑
    - Remaining-Req 헤더 기반 서버 상태 추적
    - 적응형 백오프 및 스로틀링
    - 1초 내 통신 완료 규칙 준수
    """

    # 업비트 공식 Rate Limit 규칙 (정적 설정)
    _RATE_RULES = {
        UpbitRateLimitGroup.GLOBAL: UpbitRateLimitRule(
            requests_per_second=10,
            requests_per_minute=600
        ),
        UpbitRateLimitGroup.QUOTATION: UpbitRateLimitRule(
            requests_per_second=30,
            requests_per_minute=1800
        ),
        UpbitRateLimitGroup.EXCHANGE_DEFAULT: UpbitRateLimitRule(
            requests_per_second=30,
            requests_per_minute=1800
        ),
        UpbitRateLimitGroup.ORDER: UpbitRateLimitRule(
            requests_per_second=8,
            requests_per_minute=480
        ),
        UpbitRateLimitGroup.ORDER_CANCEL_ALL: UpbitRateLimitRule(
            requests_per_second=1,  # 0.5 RPS = 2초당 1회 = requests_per_second=1, window_seconds=2
            requests_per_minute=30,
            window_seconds=2,
            max_requests_per_window=1
        ),
        UpbitRateLimitGroup.WEBSOCKET_CONNECT: UpbitRateLimitRule(
            requests_per_second=5,
            requests_per_minute=100
        ),
        UpbitRateLimitGroup.WEBSOCKET_MESSAGE: UpbitRateLimitRule(
            requests_per_second=5,
            requests_per_minute=100
        )
    }

    # 엔드포인트별 그룹 매핑 (업비트 공식 문서 기준)
    _ENDPOINT_MAPPINGS = {
        # Quotation 그룹 (시세 조회) - 30 RPS
        '/ticker': UpbitRateLimitGroup.QUOTATION,
        '/tickers': UpbitRateLimitGroup.QUOTATION,
        '/orderbook': UpbitRateLimitGroup.QUOTATION,
        '/trades': UpbitRateLimitGroup.QUOTATION,
        '/candles/minutes': UpbitRateLimitGroup.QUOTATION,
        '/candles/days': UpbitRateLimitGroup.QUOTATION,
        '/candles/weeks': UpbitRateLimitGroup.QUOTATION,
        '/candles/months': UpbitRateLimitGroup.QUOTATION,
        '/market/all': UpbitRateLimitGroup.QUOTATION,

        # Exchange Default 그룹 (계좌/자산 조회) - 30 RPS
        '/accounts': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/orders/chance': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/withdraws': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/deposits': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/deposits/coin_addresses': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/deposits/generate_coin_address': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/deposits/coin_address': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/withdraws/chance': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/withdraws/coin': UpbitRateLimitGroup.EXCHANGE_DEFAULT,
        '/withdraws/krw': UpbitRateLimitGroup.EXCHANGE_DEFAULT,

        # Order Cancel All 그룹 (전체 주문 취소) - 0.5 RPS (2초당 1회)
        '/orders/cancel_all': UpbitRateLimitGroup.ORDER_CANCEL_ALL,
    }

    def __init__(self, client_id: Optional[str] = None,
                 strategy: RateLimitStrategy = RateLimitStrategy.HYBRID_FAST):
        self.client_id = client_id or f"upbit_limiter_{id(self)}"
        self.strategy = strategy

        # 전역 제한 추적
        self._global_requests: List[float] = []

        # 그룹별 제한 추적
        self._group_requests: Dict[UpbitRateLimitGroup, List[float]] = {
            group: [] for group in UpbitRateLimitGroup
        }

        # 업비트 서버 제한 추적 (Remaining-Req 헤더 기반)
        self._server_limit: Optional[int] = None
        self._server_remaining: Optional[int] = None
        self._server_reset_time: Optional[float] = None

        # 적응형 백오프
        self._consecutive_limits = 0
        self._backoff_multiplier = 1.0
        self._throttled_until = 0.0

        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(f"UpbitRateLimiter.{self.client_id}")

        # 전략별 성능 통계
        self._strategy_stats = {
            'total_requests': 0,
            'total_wait_time': 0.0,
            'immediate_passes': 0,
            'calculations_needed': 0
        }

        # 🚀 응답 기반 간격 제어를 위한 추가 상태
        self._response_timing_enabled = strategy in [
            RateLimitStrategy.RESPONSE_INTERVAL_SIMPLE,
            RateLimitStrategy.SMART_RESPONSE_ADAPTIVE
        ]

        if self._response_timing_enabled:
            self._init_response_timing_state()

    def _init_response_timing_state(self) -> None:
        """응답 기반 간격 제어를 위한 상태 초기화"""
        # 📊 핵심 추적 메트릭
        self._request_start_times: List[float] = []     # 요청 시작 시점
        self._response_end_times: List[float] = []      # 응답 완료 시점
        self._interval_history: List[float] = []        # 요청간 간격 히스토리 (최근 10개)
        self._rrt_history: List[float] = []             # Request-Response Time 히스토리 (최근 5개)

        # 🎯 전략별 파라미터
        self._target_interval = 0.1                     # TIR: 목표 간격 (100ms)
        self._base_wait_margin = 0.1                    # BWM: 기본 대기 마진 (100ms)
        self._adaptive_ratio = 1.05                     # ARR: 적응형 비율 조정

        # 📈 동적 상태
        self._current_mode = "warmup"                   # warmup -> adaptive -> optimized
        self._consecutive_success = 0                   # 연속 성공 카운트
        self._last_response_end_time = 0.0             # 마지막 응답 완료 시점
        self._estimated_rtt = 0.05                     # 추정 RTT (기본 50ms)

    async def acquire(self, endpoint: str, method: str = 'GET') -> None:
        """
        업비트 API 호출 권한 획득

        Args:
            endpoint: API 엔드포인트 (예: '/ticker', '/orders')
            method: HTTP 메서드 (GET, POST, DELETE)
        """
        async with self._lock:
            # 1. 스로틀링 상태 확인
            await self._wait_if_throttled()

            # 2. 서버 기반 제한 확인
            await self._enforce_server_limits()

            # 3. 엔드포인트별 그룹 결정
            group = self._get_endpoint_group(endpoint, method)

            # 4. 제한 확인 먼저 (레거시 방식)
            if group != UpbitRateLimitGroup.GLOBAL:
                await self._enforce_group_limit(group)
            await self._enforce_global_limit()

            # 5. 제한 통과 후 요청 기록 (레거시 방식)
            self._record_request(group)

            # 6. 성공적인 acquire - 백오프 상태 리셋
            self._consecutive_limits = 0
            self._backoff_multiplier = 1.0

            self._logger.debug(f"Rate limit 획득: {endpoint} [{method}] -> {group.value}")

    def _get_endpoint_group(self, endpoint: str, method: str) -> UpbitRateLimitGroup:
        """엔드포인트와 메서드를 기반으로 Rate Limit 그룹 결정"""
        # 특별 케이스: /orders는 메서드에 따라 다른 그룹
        if endpoint == '/orders':
            if method.upper() in ['POST', 'DELETE']:
                return UpbitRateLimitGroup.ORDER
            else:  # GET
                return UpbitRateLimitGroup.EXCHANGE_DEFAULT

        # 일반적인 매핑
        for pattern, group in self._ENDPOINT_MAPPINGS.items():
            if endpoint.startswith(pattern):
                return group

        # 기본값: 전역 제한
        return UpbitRateLimitGroup.GLOBAL

    async def _wait_if_throttled(self) -> None:
        """스로틀링 상태면 대기"""
        if time.time() < self._throttled_until:
            wait_time = self._throttled_until - time.time()
            self._logger.warning(f"업비트 Rate limit 스로틀링 대기: {wait_time:.2f}초")
            await asyncio.sleep(wait_time)

    async def _enforce_server_limits(self) -> None:
        """업비트 서버 기반 제한 강제 적용 (Remaining-Req 헤더 기준)"""
        now = time.time()

        if self._server_remaining is not None and self._server_remaining <= 0:
            if self._server_reset_time and now < self._server_reset_time:
                wait_time = min(self._server_reset_time - now, 0.9)  # 최대 0.9초
                self._logger.warning(f"업비트 서버 제한 대기: {wait_time:.2f}초")
                await asyncio.sleep(wait_time)

    async def _enforce_global_limit(self) -> None:
        """전역 Rate Limit 강제 적용 - 선택된 전략에 따라 실행"""
        start_time = time.perf_counter()
        self._strategy_stats['total_requests'] += 1

        try:
            if self.strategy == RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW:
                await self._enforce_global_limit_cloudflare()
            elif self.strategy == RateLimitStrategy.AIOLIMITER_OPTIMIZED:
                await self._enforce_global_limit_aiolimiter()
            elif self.strategy == RateLimitStrategy.HYBRID_FAST:
                await self._enforce_global_limit_hybrid()
            elif self.strategy == RateLimitStrategy.LEGACY_CONSERVATIVE:
                await self._enforce_global_limit_legacy()
            elif self.strategy == RateLimitStrategy.RESPONSE_INTERVAL_SIMPLE:
                await self._enforce_global_limit_response_simple()
            elif self.strategy == RateLimitStrategy.SMART_RESPONSE_ADAPTIVE:
                await self._enforce_global_limit_smart_adaptive()
            else:
                # 기본값: Hybrid
                await self._enforce_global_limit_hybrid()
        finally:
            wait_time = time.perf_counter() - start_time
            self._strategy_stats['total_wait_time'] += wait_time

    async def _enforce_global_limit_cloudflare(self) -> None:
        """Cloudflare Sliding Window Counter 방식 (정확성 중시)"""
        # ==========================================
        # 🔧 CLOUDFLARE 전략 조정 가능한 파라미터들
        # ==========================================
        CLEANUP_WINDOW_SECONDS = 2.0        # 오래된 요청 정리 윈도우 (기본: 2.0초)
        MAX_WAIT_TIME_MS = 120               # 최대 대기시간 (기본: 120ms)
        EXCESS_MULTIPLIER = 0.1              # 초과량 대기시간 계수 (기본: 0.1)
        SAFETY_BUFFER = 1                    # 안전 버퍼 (기본: 1)
        # ==========================================

        now = time.time()
        rule = self._RATE_RULES[UpbitRateLimitGroup.GLOBAL]

        # Sliding Window Counter: 현재 1초와 이전 1초 구간 분리
        current_window_start = int(now)  # 현재 1초 구간 시작
        previous_window_start = current_window_start - 1  # 이전 1초 구간

        # 현재 1초 구간 내 요청 수
        current_requests = [ts for ts in self._global_requests if ts >= current_window_start]
        current_count = len(current_requests)

        # 이전 1초 구간 내 요청 수
        previous_requests = [ts for ts in self._global_requests
                             if previous_window_start <= ts < current_window_start]
        previous_count = len(previous_requests)

        # Sliding Window 계산
        elapsed_in_current = now - current_window_start
        weight = (1.0 - elapsed_in_current)  # 이전 구간 가중치
        estimated_rate = previous_count * weight + current_count

        # 정리: 설정된 윈도우 이상 지난 요청 제거
        self._global_requests = [ts for ts in self._global_requests
                                 if now - ts < CLEANUP_WINDOW_SECONDS]

        # 🚀 엄격한 시간 간격 제어 - 모든 요청 필수 적용
        min_interval = 1.0 / rule.requests_per_second  # 0.1초 (100ms)

        if self._global_requests:
            time_since_last = now - self._global_requests[-1]
            if time_since_last < min_interval:
                # 최소 간격 미충족 시 강제 대기
                wait_time = min_interval - time_since_last
                self._strategy_stats['calculations_needed'] += 1

                self._logger.debug(
                    f"업비트 전역 제한 (Cloudflare 시간간격): 마지막 요청 {time_since_last * 1000:.1f}ms 전, "
                    f"최소간격 {min_interval * 1000:.1f}ms → 대기 {wait_time * 1000:.1f}ms"
                )
                await asyncio.sleep(wait_time)

        # 추가 안전장치: Sliding Window 기반 제한 확인
        if estimated_rate >= rule.requests_per_second - SAFETY_BUFFER:
            self._strategy_stats['calculations_needed'] += 1
            # 정밀한 대기시간 계산
            excess = estimated_rate - rule.requests_per_second + SAFETY_BUFFER
            additional_wait = min(excess * EXCESS_MULTIPLIER, MAX_WAIT_TIME_MS / 1000.0)

            if additional_wait > 0:
                self._logger.debug(
                    f"업비트 전역 제한 (Cloudflare 추가): {estimated_rate:.1f}/10, 추가 대기 {additional_wait * 1000:.1f}ms"
                )
                await asyncio.sleep(additional_wait)

    async def _enforce_global_limit_aiolimiter(self) -> None:
        """aiolimiter 라이브러리 정확한 구현 (Leaky Bucket 알고리즘)"""
        # ==========================================
        # 🔧 AIOLIMITER 전략 조정 가능한 파라미터들
        # ==========================================
        RATE_LIMIT = 10.0                   # 초당 최대 요청 (15.0 → 10.0으로 업비트 규칙 준수!)
        TIME_PERIOD = 1.0                   # 시간 윈도우 (기본: 1.0초)
        CAPACITY_THRESHOLD = 0.8            # 용량 임계값 (0.9 → 0.8로 감소)
        PRECISION_MODE = True               # 정밀 모드 활성화 (기본: True)
        # ==========================================

        now = time.time()

        # 🚀 엄격한 시간 간격 제어 - 용량 확인과 별도로 적용
        min_interval = 1.0 / RATE_LIMIT  # 0.1초 (100ms)

        if self._global_requests:
            time_since_last = now - self._global_requests[-1]
            if time_since_last < min_interval:
                # 최소 간격 미충족 시 강제 대기
                wait_time = min_interval - time_since_last
                self._strategy_stats['calculations_needed'] += 1

                self._logger.debug(
                    f"업비트 전역 제한 (aiolimiter 시간간격): 마지막 요청 {time_since_last * 1000:.1f}ms 전, "
                    f"최소간격 {min_interval * 1000:.1f}ms → 대기 {wait_time * 1000:.1f}ms"
                )
                await asyncio.sleep(wait_time)

        # Leaky Bucket 핵심: 시간 경과에 따른 용량 복구
        rate_per_sec = RATE_LIMIT / TIME_PERIOD

        if hasattr(self, '_aiolimiter_level'):
            elapsed = now - self._aiolimiter_last_check
            # 시간 비례 용량 복구 (핵심 알고리즘!)
            decrement = elapsed * rate_per_sec
            self._aiolimiter_level = max(self._aiolimiter_level - decrement, 0.0)
        else:
            # 초기화
            self._aiolimiter_level = 0.0

        self._aiolimiter_last_check = now

        # 용량 확인 (Leaky Bucket 방식) - 시간 간격 제어 후 추가 안전장치
        current_capacity = self._aiolimiter_level + 1.0  # 현재 요청 추가

        if current_capacity > RATE_LIMIT * CAPACITY_THRESHOLD:
            # 용량 초과 시 추가 대기
            self._strategy_stats['calculations_needed'] += 1

            if PRECISION_MODE:
                # 정밀한 대기시간 계산 (실제 aiolimiter 방식)
                excess = current_capacity - RATE_LIMIT
                if excess > 0:
                    # 초과 용량이 복구되는 시간 계산
                    additional_wait = excess / rate_per_sec

                    # 최대 대기시간 제한 (안전장치)
                    max_wait = 0.15  # 150ms
                    actual_wait = min(additional_wait, max_wait)

                    self._logger.debug(
                        f"업비트 전역 제한 (aiolimiter Leaky Bucket 추가): "
                        f"용량 {current_capacity:.2f}/{RATE_LIMIT}, "
                        f"추가 대기 {actual_wait * 1000:.1f}ms"
                    )

                    await asyncio.sleep(actual_wait)

                    # 대기 후 용량 업데이트
                    post_wait_now = time.time()
                    post_elapsed = post_wait_now - self._aiolimiter_last_check
                    post_decrement = post_elapsed * rate_per_sec
                    self._aiolimiter_level = max(self._aiolimiter_level - post_decrement, 0.0)
                    self._aiolimiter_last_check = post_wait_now

        # 최종 용량 추가
        self._aiolimiter_level = min(self._aiolimiter_level + 1.0, RATE_LIMIT)

    async def _enforce_global_limit_hybrid(self) -> None:
        """하이브리드 방식 (속도+정확성 균형) - 웜업 모드 포함"""
        # ==========================================
        # 🔧 HYBRID 전략 조정 가능한 파라미터들
        # ==========================================
        SAFETY_BUFFER = 1                    # 안전 버퍼 (기본: 1)
        HEAVY_OVERLOAD_THRESHOLD = 1.5       # 심한 초과 임계값 (기본: 1.5배)
        HEAVY_WAIT_MULTIPLIER = 0.08         # 심한 초과 대기시간 계수 (기본: 0.08)
        LIGHT_WAIT_MULTIPLIER = 0.04         # 가벼운 초과 대기시간 계수 (기본: 0.04)
        MAX_HEAVY_WAIT_MS = 100              # 심한 초과 최대 대기시간 (기본: 100ms)
        MAX_LIGHT_WAIT_MS = 60               # 가벼운 초과 최대 대기시간 (기본: 60ms)

        # 🚀 웜업 모드 파라미터들 (초반 429 오류 방지)
        WARMUP_REQUEST_COUNT = 15            # 웜업 모드 요청 수 (기본: 15회)
        WARMUP_SAFETY_BUFFER = 2            # 웜업 시 추가 안전 버퍼 (기본: 2)
        WARMUP_EXTRA_WAIT_MS = 20            # 웜업 시 추가 대기시간 (기본: 20ms)
        # ==========================================

        now = time.time()
        rule = self._RATE_RULES[UpbitRateLimitGroup.GLOBAL]

        # 🚀 웜업 모드 확인: 초기 요청들은 더 보수적으로 처리
        total_requests = self._strategy_stats['total_requests']
        is_warmup_mode = total_requests <= WARMUP_REQUEST_COUNT

        if is_warmup_mode:
            # 웜업 모드: 더 보수적인 처리
            effective_safety_buffer = SAFETY_BUFFER + WARMUP_SAFETY_BUFFER
            self._logger.debug(f"Hybrid 웜업 모드: {total_requests}/{WARMUP_REQUEST_COUNT}, 안전 버퍼 {effective_safety_buffer}")
        else:
            # 정상 모드: 기본 처리
            effective_safety_buffer = SAFETY_BUFFER

        # 🚀 엄격한 시간 간격 제어 - 모든 요청 필수 적용 (Phase 0)
        min_interval = 1.0 / rule.requests_per_second  # 0.1초 (100ms)

        if self._global_requests:
            time_since_last = now - self._global_requests[-1]
            if time_since_last < min_interval:
                # 최소 간격 미충족 시 강제 대기
                base_wait = min_interval - time_since_last

                # 웜업 모드에서는 추가 안전 마진
                if is_warmup_mode:
                    total_wait = base_wait + (WARMUP_EXTRA_WAIT_MS / 1000.0)
                    self._logger.debug(
                        f"Hybrid 시간간격 웜업: 마지막 {time_since_last * 1000:.1f}ms 전 → "
                        f"대기 {total_wait * 1000:.1f}ms (기본 {base_wait * 1000:.1f}ms + 웜업 {WARMUP_EXTRA_WAIT_MS}ms)"
                    )
                else:
                    total_wait = base_wait
                    self._logger.debug(
                        f"Hybrid 시간간격 정상: 마지막 {time_since_last * 1000:.1f}ms 전 → 대기 {total_wait * 1000:.1f}ms"
                    )

                self._strategy_stats['calculations_needed'] += 1
                await asyncio.sleep(total_wait)

        # Phase 1: 빠른 요청 목록 정리 (성능 최적화)
        cutoff_time = now - 1.0
        recent_requests = [ts for ts in self._global_requests if ts > cutoff_time]

        # Phase 2: 추가 안전장치 - Sliding Window 기반 제한 확인
        if len(recent_requests) >= rule.requests_per_second - effective_safety_buffer:
            self._strategy_stats['calculations_needed'] += 1

            # 정밀 계산 (Cloudflare 방식 간소화)
            current_second = int(now)
            previous_second = current_second - 1

            # 빠른 카운팅
            current_count = sum(1 for ts in recent_requests if ts >= current_second)
            previous_count = sum(1 for ts in recent_requests if previous_second <= ts < current_second)

            # 간소화된 Sliding Window
            elapsed = now - current_second
            estimated_rate = previous_count * (1.0 - elapsed) + current_count

            # 메모리 정리
            self._global_requests = recent_requests

            # Phase 3: 적응형 추가 대기시간 (필요한 경우에만)
            if estimated_rate >= rule.requests_per_second - effective_safety_buffer:
                # 동적 대기: 현재 상황에 최적화
                if estimated_rate > rule.requests_per_second * HEAVY_OVERLOAD_THRESHOLD:
                    # 심한 초과: 정확한 대기
                    base_wait_time = min(
                        (estimated_rate - rule.requests_per_second) * HEAVY_WAIT_MULTIPLIER,
                        MAX_HEAVY_WAIT_MS / 1000.0
                    )
                else:
                    # 가벼운 초과: 최소 대기
                    base_wait_time = min(
                        (estimated_rate - rule.requests_per_second) * LIGHT_WAIT_MULTIPLIER,
                        MAX_LIGHT_WAIT_MS / 1000.0
                    )

                # 웜업 모드에서는 추가 대기시간 적용
                if is_warmup_mode:
                    total_wait_time = base_wait_time + (WARMUP_EXTRA_WAIT_MS / 1000.0)
                    self._logger.debug(
                        f"업비트 전역 제한 (Hybrid 웜업 추가): {estimated_rate:.2f}/10 → "
                        f"{total_wait_time * 1000:.1f}ms 추가 대기"
                    )
                else:
                    total_wait_time = base_wait_time
                    self._logger.debug(
                        f"업비트 전역 제한 (Hybrid 정상 추가): {estimated_rate:.2f}/10 → {total_wait_time * 1000:.1f}ms 추가 대기"
                    )

                await asyncio.sleep(total_wait_time)
        else:
            # 메모리 정리만 수행
            self._global_requests = recent_requests

    async def _enforce_global_limit_legacy(self) -> None:
        """Legacy 방식 (최고 안전성) - rate_limiter_legacy.py 기반"""
        # ==========================================
        # 🔧 LEGACY 전략 조정 가능한 파라미터들
        # ==========================================
        REQUESTS_PER_SECOND = 10             # 초당 요청 제한 (8 → 10, 업비트 규칙 준수)
        REQUESTS_PER_MINUTE = 400            # 분당 요청 제한 (기본: 400 < 600, 안전 마진)
        MAX_WAIT_TIME_MS = 150               # 최대 대기시간 (기본: 150ms)
        BACKOFF_MULTIPLIER = 1.5             # 백오프 계수 (기본: 1.5)
        SAFETY_MARGIN = 0.01                 # 안전 마진 (0.1 → 0.01초로 단축)
        # ==========================================

        now = time.time()

        # 🚀 엄격한 시간 간격 제어 - 모든 요청 필수 적용
        min_interval = 1.0 / REQUESTS_PER_SECOND  # 0.1초 (100ms)

        if self._global_requests:
            time_since_last = now - self._global_requests[-1]
            if time_since_last < min_interval:
                # Legacy는 가장 보수적이므로 추가 안전 마진
                safe_wait = min_interval - time_since_last + SAFETY_MARGIN  # +10ms
                self._strategy_stats['calculations_needed'] += 1

                self._logger.debug(
                    f"업비트 전역 제한 (Legacy 시간간격): 마지막 요청 {time_since_last * 1000:.1f}ms 전, "
                    f"최소간격 {min_interval * 1000:.1f}ms → 안전 대기 {safe_wait * 1000:.1f}ms"
                )
                await asyncio.sleep(safe_wait)

        # Legacy 방식: 1분 및 1초 윈도우 모두 엄격하게 관리
        # 1분 윈도우 정리
        minute_cutoff = now - 60.0
        self._global_requests = [ts for ts in self._global_requests if ts > minute_cutoff]

        # 1초 윈도우 정리
        second_cutoff = now - 1.0
        recent_requests = [ts for ts in self._global_requests if ts > second_cutoff]

        # 분당 제한 확인 (추가 안전장치로만 활용)
        if len(self._global_requests) >= REQUESTS_PER_MINUTE:
            oldest_request = min(self._global_requests)
            wait_time = min(60.0 - (now - oldest_request) + SAFETY_MARGIN, 0.9)
            if wait_time > 0:
                self._logger.debug(
                    f"업비트 전역 제한 (Legacy 분당 추가): {len(self._global_requests)}/{REQUESTS_PER_MINUTE}, "
                    f"추가 대기 {wait_time * 1000:.1f}ms"
                )
                await asyncio.sleep(wait_time)
                return

        # 초당 제한 확인 (추가 안전장치로만 활용)
        if len(recent_requests) >= REQUESTS_PER_SECOND:
            # Legacy 백오프: 연속 제한 시 대기시간 증가
            backoff_wait = min(
                (1.0 / REQUESTS_PER_SECOND) * BACKOFF_MULTIPLIER * self._backoff_multiplier,
                MAX_WAIT_TIME_MS / 1000.0
            )

            self._strategy_stats['calculations_needed'] += 1
            self._apply_backoff()  # 백오프 상태 업데이트

            self._logger.debug(
                f"업비트 전역 제한 (Legacy 초당 추가): {len(recent_requests)}/{REQUESTS_PER_SECOND}, "
                f"백오프 추가 대기 {backoff_wait * 1000:.1f}ms"
            )
            await asyncio.sleep(backoff_wait)

    async def _enforce_global_limit_response_simple(self) -> None:
        """단순 응답 기반 간격 제어 - 강력한 버스트 억제"""
        # ==========================================
        # 🔧 RESPONSE_SIMPLE 전략 조정 가능한 파라미터들
        # ==========================================
        TARGET_INTERVAL_MS = 100                # 목표 간격 (기본: 100ms)
        TARGET_10_WINDOW_MS = 950               # 🎯 10개 윈도우 목표 시간 (950ms)
        BURST_PREVENTION_THRESHOLD = 10        # 버스트 방지 임계값 (10개)
        MAX_SINGLE_WAIT_MS = 500               # 단일 대기 최대시간 (500ms)
        MIN_WAIT_MS = 10                       # 최소 대기시간 (10ms)
        SAFETY_MARGIN_MS = 50                  # 안전 마진 (50ms)
        # ==========================================

        now = time.time()
        current_request_count = len(self._request_start_times)

        # 🚀 Phase 1: 기본 시간 간격 제어 (모든 요청 필수)
        min_interval = TARGET_INTERVAL_MS / 1000.0  # 100ms

        if self._request_start_times:
            time_since_last = now - self._request_start_times[-1]
            if time_since_last < min_interval:
                basic_wait = min_interval - time_since_last
                basic_wait = min(basic_wait, MAX_SINGLE_WAIT_MS / 1000.0)

                self._strategy_stats['calculations_needed'] += 1
                self._logger.debug(
                    f"응답간격(단순) 기본간격: 마지막 {time_since_last * 1000:.1f}ms 전 → 대기 {basic_wait * 1000:.1f}ms"
                )
                await asyncio.sleep(basic_wait)

        # 요청 시작 시점 기록
        self._request_start_times.append(now)

        # 🎯 Phase 2: 강력한 버스트 억제 - 10개 윈도우 시간 검증
        if current_request_count >= BURST_PREVENTION_THRESHOLD - 1:  # 10번째 요청부터
            # 최근 10개 요청의 시간 윈도우 계산
            recent_10_requests = self._request_start_times[-10:]
            window_duration = now - recent_10_requests[0]  # 첫 번째부터 현재까지의 시간

            target_window = TARGET_10_WINDOW_MS / 1000.0  # 950ms

            self._logger.debug(
                f"응답간격(단순) 10개윈도우: 현재 {window_duration * 1000:.1f}ms, 목표 {target_window * 1000:.1f}ms"
            )

            if window_duration < target_window:
                # 🚨 윈도우가 너무 짧음 - 강력한 억제 필요
                required_wait = target_window - window_duration + (SAFETY_MARGIN_MS / 1000.0)
                required_wait = min(required_wait, MAX_SINGLE_WAIT_MS / 1000.0)

                if required_wait > MIN_WAIT_MS / 1000.0:
                    self._strategy_stats['calculations_needed'] += 1
                    self._logger.warning(
                        f"🚨 응답간격(단순) 버스트억제: 윈도우 {window_duration * 1000:.1f}ms < 목표 {target_window * 1000:.1f}ms → "
                        f"강제 대기 {required_wait * 1000:.1f}ms"
                    )
                    await asyncio.sleep(required_wait)

        # 🔧 Phase 3: 429 이후 복구를 위한 적응형 조정
        if current_request_count >= BURST_PREVENTION_THRESHOLD:
            # 429 오류 감지 및 복구 로직
            if hasattr(self, '_consecutive_limits') and self._consecutive_limits > 0:
                # 429 이후 상태 - 점진적 복구
                recovery_requests = current_request_count - BURST_PREVENTION_THRESHOLD

                if recovery_requests < 10:  # 처음 10개 요청은 보수적
                    recovery_wait = (TARGET_INTERVAL_MS / 1000.0) * (1.5 - (recovery_requests * 0.05))
                    recovery_wait = max(recovery_wait, TARGET_INTERVAL_MS / 1000.0)
                    recovery_wait = min(recovery_wait, MAX_SINGLE_WAIT_MS / 1000.0)

                    if recovery_wait > MIN_WAIT_MS / 1000.0:
                        self._strategy_stats['calculations_needed'] += 1
                        self._logger.debug(
                            f"응답간격(단순) 429복구: 복구요청 {recovery_requests}/10 → 추가 대기 {recovery_wait * 1000:.1f}ms"
                        )
                        await asyncio.sleep(recovery_wait)
                else:
                    # 10개 이후는 정상 모드
                    self._logger.debug(f"응답간격(단순) 429복구: 복구 완료 ({recovery_requests}개), 정상 모드")

        # 🧹 메모리 정리: 오래된 요청 제거 (최근 20개만 유지)
        if len(self._request_start_times) > 20:
            self._request_start_times = self._request_start_times[-20:]

    async def _enforce_global_limit_smart_adaptive(self) -> None:
        """스마트 응답 적응형 제어 - 예측적 조정 포함"""
        # ==========================================
        # 🔧 SMART_ADAPTIVE 전략 조정 가능한 파라미터들
        # ==========================================
        TARGET_INTERVAL_MS = 100                # 목표 간격 (기본: 100ms)
        WARMUP_COUNT = 10                       # 웜업 모드 요청 수 (기본: 10회)
        ADAPTIVE_COUNT = 50                     # 적응형 모드 요청 수 (기본: 50회)
        RTT_TREND_WINDOW = 5                    # RTT 트렌드 분석 윈도우 (기본: 5개)
        PREDICTION_MULTIPLIER = 1.1             # 예측 기반 여유 계수 (기본: 1.1)
        MIN_WAIT_MS = 15                        # 최소 대기시간 (기본: 15ms)
        # ==========================================

        now = time.time()
        request_count = len(self._request_start_times) + 1

        # 🚀 엄격한 시간 간격 제어 - 모든 요청 필수 적용 (모든 모드 공통)
        await self._enforce_strict_interval(now)

        # 요청 시작 시점 기록
        self._request_start_times.append(now)

        # 모드 결정
        if request_count <= WARMUP_COUNT:
            mode = "warmup"
        elif request_count <= WARMUP_COUNT + ADAPTIVE_COUNT:
            mode = "adaptive"
        else:
            mode = "optimized"

        self._current_mode = mode

        if mode == "warmup":
            # 🚀 웜업 모드: 보수적 처리
            await self._smart_warmup_mode(request_count, TARGET_INTERVAL_MS, MIN_WAIT_MS)

        elif mode == "adaptive":
            # 📊 적응형 모드: 실시간 조정
            await self._smart_adaptive_mode(request_count, TARGET_INTERVAL_MS, MIN_WAIT_MS)

        else:
            # ⚡ 최적화 모드: 예측적 조정
            await self._smart_optimized_mode(request_count, TARGET_INTERVAL_MS,
                                             RTT_TREND_WINDOW, PREDICTION_MULTIPLIER, MIN_WAIT_MS)

    async def _enforce_strict_interval(self, now: float) -> None:
        """엄격한 시간 간격 검증 - 모든 응답 기반 전략 공통"""
        min_interval = 0.1  # 100ms 고정
        max_wait = 0.2  # 🚨 최대 대기시간 200ms

        if self._request_start_times:
            time_since_last = now - self._request_start_times[-1]
            if time_since_last < min_interval:
                wait_time = min(min_interval - time_since_last, max_wait)  # 🚨 최대값 제한
                self._strategy_stats['calculations_needed'] += 1

                self._logger.debug(
                    f"스마트적응 시간간격: 마지막 {time_since_last * 1000:.1f}ms 전 → 대기 {wait_time * 1000:.1f}ms"
                )
                await asyncio.sleep(wait_time)

    async def _smart_warmup_mode(self, request_count: int, target_interval_ms: int, min_wait_ms: int) -> None:
        """스마트 웜업 모드 - 초기 안정성 중시 (안전장치 강화)"""
        max_wait_ms = 200  # 🚨 최대 대기시간 200ms

        if request_count == 1:
            wait_time = min(target_interval_ms / 1000.0, max_wait_ms / 1000.0)
            self._logger.debug(f"스마트적응(웜업) 첫 요청: {wait_time * 1000:.1f}ms")
        else:
            # 이전 RRT 기반 보정 (안전장치 추가)
            if len(self._response_end_times) > 0 and len(self._request_start_times) >= 2:
                try:
                    last_rrt = self._response_end_times[-1] - self._request_start_times[-2]

                    # 🚨 비정상적인 RRT 값 필터링
                    if last_rrt > 0 and last_rrt < 2.0:  # 0~2초 사이만 유효
                        self._rrt_history.append(last_rrt)

                        # 웜업에서는 보수적 계산 (최대값 제한)
                        base_interval = target_interval_ms / 1000.0
                        rrt_compensation = min(last_rrt * 0.3, 0.05)  # 50% → 30%로 감소, 최대 50ms
                        safety_margin = 0.01  # 20ms → 10ms로 단축

                        wait_time = max(
                            base_interval - rrt_compensation + safety_margin,
                            min_wait_ms / 1000.0
                        )

                        # 🚨 최대 대기시간 제한
                        wait_time = min(wait_time, max_wait_ms / 1000.0)

                        self._logger.debug(
                            f"스마트적응(웜업) {request_count}/10: RRT {last_rrt * 1000:.1f}ms → {wait_time * 1000:.1f}ms"
                        )
                    else:
                        # 비정상적인 RRT인 경우 기본값 사용
                        wait_time = min(target_interval_ms / 1000.0, max_wait_ms / 1000.0)
                        self._logger.debug(
                            f"스마트적응(웜업) {request_count}/10: 비정상 RRT {last_rrt * 1000:.1f}ms, 기본 {wait_time * 1000:.1f}ms"
                        )
                except (IndexError, ValueError) as e:
                    # 예외 발생 시 기본값 사용
                    wait_time = min(target_interval_ms / 1000.0, max_wait_ms / 1000.0)
                    self._logger.warning(f"스마트적응(웜업) {request_count}/10: 오류 {e}, 기본 {wait_time * 1000:.1f}ms")
            else:
                # 데이터 부족 시 기본값
                wait_time = min(target_interval_ms / 1000.0, max_wait_ms / 1000.0)
                self._logger.debug(f"스마트적응(웜업) {request_count}/10: 데이터 부족, 기본 {wait_time * 1000:.1f}ms")

        self._strategy_stats['calculations_needed'] += 1
        await asyncio.sleep(wait_time)

    async def _smart_adaptive_mode(self, request_count: int, target_interval_ms: int, min_wait_ms: int) -> None:
        """스마트 적응형 모드 - 실시간 성능 조정 (안전장치 강화)"""
        max_wait_ms = 300  # 🚨 최대 대기시간 300ms

        if len(self._interval_history) >= 3:
            try:
                # 실제 간격 추적 (안전한 계산)
                recent_intervals = self._interval_history[-10:]
                if not recent_intervals or any(interval <= 0 for interval in recent_intervals):
                    # 비정상적인 데이터 발견 시 기본값 사용
                    wait_time = min(target_interval_ms / 1000.0, max_wait_ms / 1000.0)
                    self._logger.warning(f"스마트적응(적응형) 비정상 간격 데이터, 기본값 {wait_time * 1000:.1f}ms")
                else:
                    current_avg_interval = sum(recent_intervals) / len(recent_intervals)
                    target_interval = target_interval_ms / 1000.0

                    # 성능 피드백 기반 조정 (안전 범위 제한)
                    performance_ratio = max(0.1, min(current_avg_interval / target_interval, 10.0))  # 🚨 범위 제한

                    if performance_ratio < 0.8:  # 너무 빠름 (0.9 → 0.8로 더 엄격하게)
                        adjustment_factor = 1.3  # 1.2 → 1.3으로 더 보수적
                        self._logger.debug(f"스마트적응(적응형) 속도 조정: {performance_ratio:.2f} → 감속")
                    elif performance_ratio > 1.2:  # 너무 느림 (1.1 → 1.2로 더 관대하게)
                        adjustment_factor = 0.9  # 0.8 → 0.9로 더 보수적
                        self._logger.debug(f"스마트적응(적응형) 속도 조정: {performance_ratio:.2f} → 가속")
                    else:  # 적정 범위
                        adjustment_factor = 1.0

                    # RTT 기반 보정 (안전장치 강화)
                    if len(self._rrt_history) >= 3:
                        valid_rtts = [rtt for rtt in self._rrt_history[-3:] if 0 < rtt < 2.0]  # 🚨 유효한 RTT만
                        if valid_rtts:
                            estimated_rtt = sum(valid_rtts) / len(valid_rtts)
                            rtt_compensation = min(estimated_rtt * 0.2, 0.05)  # 0.4 → 0.2로 감소, 최대 50ms
                        else:
                            rtt_compensation = 0.02  # 기본 20ms
                    else:
                        rtt_compensation = 0.02  # 기본 20ms

                    # 안전한 대기시간 계산
                    calculated_wait = (target_interval * adjustment_factor) - rtt_compensation
                    wait_time = max(
                        min(calculated_wait, max_wait_ms / 1000.0),  # 🚨 최대값 제한
                        min_wait_ms / 1000.0  # 최소값 보장
                    )

                    self._logger.debug(
                        f"스마트적응(적응형) 요청 {request_count}: 성능비 {performance_ratio:.2f}, "
                        f"조정계수 {adjustment_factor:.2f}, 대기 {wait_time * 1000:.1f}ms"
                    )

            except (ValueError, ZeroDivisionError, TypeError) as e:
                # 예외 발생 시 안전한 기본값
                wait_time = min(target_interval_ms / 1000.0, max_wait_ms / 1000.0)
                self._logger.warning(f"스마트적응(적응형) 계산 오류: {e}, 기본값 {wait_time * 1000:.1f}ms")
        else:
            # 데이터 부족 시 기본값
            wait_time = min(target_interval_ms / 1000.0, max_wait_ms / 1000.0)
            self._logger.debug(f"스마트적응(적응형) 데이터 부족 ({len(self._interval_history)}개), 기본값 {wait_time * 1000:.1f}ms")

        self._strategy_stats['calculations_needed'] += 1
        await asyncio.sleep(wait_time)

    async def _smart_optimized_mode(self, request_count: int, target_interval_ms: int,
                                    rtt_trend_window: int, prediction_multiplier: float, min_wait_ms: int) -> None:
        """스마트 최적화 모드 - 예측적 성능 최적화 (안전장치 강화)"""
        target_interval = target_interval_ms / 1000.0
        max_wait_ms = 400  # 🚨 최대 대기시간 400ms

        # RTT 트렌드 분석
        if len(self._rrt_history) >= rtt_trend_window:
            try:
                recent_rtts = self._rrt_history[-rtt_trend_window:]

                # 🚨 유효한 RTT 값만 필터링
                valid_rtts = [rtt for rtt in recent_rtts if 0 < rtt < 2.0]

                if len(valid_rtts) >= 3:
                    rtt_trend = self._analyze_rtt_trend(valid_rtts)

                    # 예측 기반 조정 (안전 범위 제한)
                    if rtt_trend == "increasing":
                        interval_multiplier = min(prediction_multiplier, 2.0)  # 🚨 최대 2배 제한
                        self._logger.debug("스마트적응(최적화) RTT 증가 감지 → 여유 확대")
                    elif rtt_trend == "decreasing":
                        interval_multiplier = max(1.0 / prediction_multiplier, 0.5)  # 🚨 최소 0.5배 제한
                        self._logger.debug("스마트적응(최적화) RTT 감소 감지 → 공격적 최적화")
                    else:
                        interval_multiplier = 1.0  # 유지

                    # 네트워크 상태 예측 보정 (안전장치)
                    avg_rtt = sum(valid_rtts) / len(valid_rtts)
                    rtt_compensation = min(avg_rtt * 0.2, 0.06)  # 0.3 → 0.2로 감소, 최대 60ms

                    # 안전한 대기시간 계산
                    calculated_wait = (target_interval * interval_multiplier) - rtt_compensation
                    wait_time = max(
                        min(calculated_wait, max_wait_ms / 1000.0),  # 🚨 최대값 제한
                        min_wait_ms / 1000.0  # 최소값 보장
                    )

                    self._logger.debug(
                        f"스마트적응(최적화) 요청 {request_count}: RTT 트렌드 {rtt_trend}, "
                        f"승수 {interval_multiplier:.2f}, 대기 {wait_time * 1000:.1f}ms"
                    )
                else:
                    # 유효한 RTT 데이터 부족 시 적응형 모드로 폴백
                    self._logger.debug("스마트적응(최적화) 유효한 RTT 부족, 적응형 모드로 폴백")
                    await self._smart_adaptive_mode(request_count, target_interval_ms, min_wait_ms)
                    return

            except (ValueError, ZeroDivisionError, TypeError) as e:
                # 예외 발생 시 적응형 모드로 폴백
                self._logger.warning(f"스마트적응(최적화) 계산 오류: {e}, 적응형 모드로 폴백")
                await self._smart_adaptive_mode(request_count, target_interval_ms, min_wait_ms)
                return
        else:
            # 충분한 데이터가 없으면 적응형 모드와 동일
            self._logger.debug(f"스마트적응(최적화) RTT 데이터 부족 ({len(self._rrt_history)}개), 적응형 모드로 폴백")
            await self._smart_adaptive_mode(request_count, target_interval_ms, min_wait_ms)
            return

        self._strategy_stats['calculations_needed'] += 1
        await asyncio.sleep(wait_time)

    def _analyze_rtt_trend(self, rtt_samples: List[float]) -> str:
        """RTT 트렌드 분석 - 단순 선형 추세"""
        if len(rtt_samples) < 3:
            return "stable"

        # 간단한 선형 회귀 근사
        n = len(rtt_samples)
        x_vals = list(range(n))

        # 기울기 계산 (최소제곱법 간소화)
        sum_x = sum(x_vals)
        sum_y = sum(rtt_samples)
        sum_xy = sum(x * y for x, y in zip(x_vals, rtt_samples))
        sum_x2 = sum(x * x for x in x_vals)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return "stable"

        slope = (n * sum_xy - sum_x * sum_y) / denominator

        # 트렌드 판정 (임계값 기반)
        if slope > 0.01:  # 10ms/요청 이상 증가
            return "increasing"
        elif slope < -0.01:  # 10ms/요청 이상 감소
            return "decreasing"
        else:
            return "stable"

    def update_response_timing(self, response_end_time: float, status_code: int = 200) -> None:
        """
        응답 완료 시점에서 호출 - 다음 간격 계산을 위한 메트릭 업데이트

        Args:
            response_end_time: 응답 완료 시점
            status_code: HTTP 상태 코드 (429 감지용)
        """
        if not self._response_timing_enabled:
            return

        # 응답 완료 시점 기록
        self._response_end_times.append(response_end_time)
        self._last_response_end_time = response_end_time

        # 요청-응답 간격 계산 (최근 요청이 있는 경우)
        if len(self._request_start_times) > 0:
            request_start = self._request_start_times[-1]
            rrt = response_end_time - request_start

            # RRT 히스토리 업데이트 (최근 5개만 유지)
            self._rrt_history.append(rrt)
            if len(self._rrt_history) > 5:
                self._rrt_history.pop(0)

        # 요청간 간격 계산 (이전 응답이 있는 경우)
        if len(self._response_end_times) >= 2:
            interval = response_end_time - self._response_end_times[-2]

            # 간격 히스토리 업데이트 (최근 10개만 유지)
            self._interval_history.append(interval)
            if len(self._interval_history) > 10:
                self._interval_history.pop(0)

        # 429 오류 처리
        if status_code == 429:
            self._handle_429_response()
        else:
            # 성공 응답 시 연속 성공 카운트 증가
            self._consecutive_success += 1
            if self._consecutive_success >= 10:
                # 10회 연속 성공 시 백오프 리셋
                self._reset_backoff()

        self._logger.debug(
            f"응답 타이밍 업데이트: "
            f"RRT {(response_end_time - self._request_start_times[-1]) * 1000:.1f}ms, "
            f"간격 {(response_end_time - self._response_end_times[-2]) * 1000:.1f}ms, "
            f"모드: {getattr(self, '_current_mode', 'N/A')}"
            if len(self._request_start_times) > 0 and len(self._response_end_times) >= 2
            else f"응답 타이밍 업데이트: 초기 상태, 모드: {getattr(self, '_current_mode', 'N/A')}"
        )

    def _handle_429_response(self) -> None:
        """429 응답 처리 - 적응형 백오프"""
        self._consecutive_success = 0
        self._apply_backoff()

        # 응답 기반 전략에서는 추가 조정
        if hasattr(self, '_current_mode'):
            # 웜업/적응형 모드로 되돌리기
            if self._current_mode == "optimized":
                self._current_mode = "adaptive"
                self._logger.warning("429 오류로 인해 최적화 모드에서 적응형 모드로 전환")

        self._logger.warning(f"429 응답 감지 - 백오프 적용 (승수: {self._backoff_multiplier:.2f})")

    def get_response_timing_status(self) -> Dict[str, Any]:
        """응답 기반 타이밍 상태 조회"""
        if not self._response_timing_enabled:
            return {"enabled": False}

        # 최근 성능 메트릭 계산
        current_avg_interval = 0.0
        current_avg_rrt = 0.0

        if len(self._interval_history) > 0:
            current_avg_interval = sum(self._interval_history) / len(self._interval_history)

        if len(self._rrt_history) > 0:
            current_avg_rrt = sum(self._rrt_history) / len(self._rrt_history)

        return {
            "enabled": True,
            "current_mode": getattr(self, '_current_mode', 'unknown'),
            "target_interval_ms": self._target_interval * 1000,
            "current_avg_interval_ms": current_avg_interval * 1000,
            "current_avg_rrt_ms": current_avg_rrt * 1000,
            "estimated_rtt_ms": self._estimated_rtt * 1000,
            "consecutive_success": self._consecutive_success,
            "request_count": len(self._request_start_times),
            "response_count": len(self._response_end_times),
            "interval_history_size": len(self._interval_history),
            "rrt_history_size": len(self._rrt_history)
        }

    async def _enforce_group_limit(self, group: UpbitRateLimitGroup) -> None:
        """그룹별 Rate Limit 강제 적용 - 업비트 공식 규칙 완벽 준수"""
        if group not in self._RATE_RULES:
            return

        now = time.time()
        rule = self._RATE_RULES[group]

        # 윈도우 시간에 따른 요청 정리
        window = rule.window_seconds
        self._group_requests[group] = [
            ts for ts in self._group_requests[group] if now - ts < window
        ]

        current_requests_in_window = len(self._group_requests[group])

        # 🎯 특별 처리: ORDER_CANCEL_ALL (0.5 RPS = 2초당 1회)
        if group == UpbitRateLimitGroup.ORDER_CANCEL_ALL:
            if current_requests_in_window >= rule.max_requests_per_window:
                # 2초 윈도우에서 이미 1회 요청됨 - 2초 대기 필요
                oldest_request = min(self._group_requests[group])
                wait_time = window - (now - oldest_request)

                if wait_time > 0:
                    # 0.5 RPS를 위한 정확한 대기 (최소 2초 간격)
                    safe_wait = max(wait_time + 0.05, 0.1)  # 최소 100ms, 안전 마진 50ms
                    self._logger.debug(
                        f"업비트 {group.value} 제한 (0.5 RPS): {current_requests_in_window}/{rule.max_requests_per_window} in {window}s → 대기 {safe_wait * 1000:.1f}ms"
                    )
                    await asyncio.sleep(safe_wait)
            return

        # 🚀 일반 그룹 처리: 윈도우 기반 제한 확인
        if current_requests_in_window >= rule.max_requests_per_window:
            # 윈도우가 꽉 참 - 가장 오래된 요청이 윈도우를 벗어날 때까지 대기
            oldest_request = min(self._group_requests[group])
            wait_time = window - (now - oldest_request)

            if wait_time > 0:
                # 일반 그룹 안전 마진 (짧게)
                safe_wait = min(wait_time + 0.01, 0.1)  # 최대 100ms
                self._logger.debug(
                    f"업비트 {group.value} 제한: {current_requests_in_window}/{rule.max_requests_per_window} in {window}s → 대기 {safe_wait * 1000:.1f}ms"
                )
                await asyncio.sleep(safe_wait)

        # 🔍 추가 안전장치: 초당 요청 수 확인 (1초 윈도우가 아닌 경우만)
        if window != 1:
            # 최근 1초간 요청 수 확인
            recent_1s_requests = [ts for ts in self._group_requests[group] if now - ts < 1.0]
            if len(recent_1s_requests) >= rule.requests_per_second:
                # 1초 안에 너무 많은 요청 - 추가 대기
                oldest_in_1s = min(recent_1s_requests)
                additional_wait = 1.0 - (now - oldest_in_1s)

                if additional_wait > 0:
                    safe_additional_wait = min(additional_wait + 0.01, 0.05)  # 최대 50ms
                    self._logger.debug(
                        f"업비트 {group.value} 1초 추가 제한: {len(recent_1s_requests)}/{rule.requests_per_second} in 1s → 추가 대기 {safe_additional_wait * 1000:.1f}ms"
                    )
                    await asyncio.sleep(safe_additional_wait)

    def _record_request(self, group: UpbitRateLimitGroup) -> None:
        """요청 기록"""
        now = time.time()

        # 전역 요청 기록
        self._global_requests.append(now)

        # 그룹별 요청 기록
        if group in self._group_requests:
            self._group_requests[group].append(now)

    def _apply_backoff(self) -> None:
        """적응형 백오프 적용 - 실용적 버전"""
        self._consecutive_limits += 1
        self._backoff_multiplier = min(2.0, 1.0 + (self._consecutive_limits * 0.1))

        # 연속 제한 도달 시 짧은 스로틀링 (테스트 환경 고려)
        if self._consecutive_limits >= 5:  # 더 관대한 기준
            throttle_time = min(self._consecutive_limits * 0.5, 2.0)  # 최대 2초
            self._throttled_until = time.time() + throttle_time
            self._logger.warning(
                f"업비트 연속 제한 {self._consecutive_limits}회, "
                f"짧은 스로틀링 적용: {throttle_time:.1f}초"
            )

    def update_from_upbit_headers(self, headers: Dict[str, str]) -> None:
        """업비트 Remaining-Req 헤더로 제한 상태 업데이트"""
        remaining_req = headers.get('Remaining-Req') or headers.get('remaining-req')
        if remaining_req:
            try:
                parts = remaining_req.split(':')
                if len(parts) >= 2:
                    self._server_limit = int(parts[0])
                    self._server_remaining = int(parts[1])
                    if len(parts) >= 3:
                        self._server_reset_time = time.time() + int(parts[2])

                    # 성공적인 요청이므로 백오프 리셋
                    self._reset_backoff()

                    self._logger.debug(
                        f"업비트 서버 제한 업데이트: {self._server_remaining}/{self._server_limit}"
                    )
            except (ValueError, IndexError):
                self._logger.warning(f"업비트 Remaining-Req 헤더 파싱 실패: {remaining_req}")

    def _reset_backoff(self) -> None:
        """백오프 상태 리셋"""
        self._consecutive_limits = 0
        self._backoff_multiplier = 1.0
        self._throttled_until = 0.0

    def allow_request(self, endpoint: str, method: str = 'GET') -> bool:
        """요청 허용 여부 확인"""
        now = time.time()

        # 스로틀링 중이면 거부
        if now < self._throttled_until:
            return False

        # 서버 제한 확인
        if self._server_remaining is not None and self._server_remaining <= 0:
            return False

        # 전역 제한 확인
        global_count = len([ts for ts in self._global_requests if now - ts < 1])
        if global_count >= self._RATE_RULES[UpbitRateLimitGroup.GLOBAL].requests_per_second:
            return False

        # 그룹별 제한 확인
        group = self._get_endpoint_group(endpoint, method)
        if group in self._RATE_RULES:
            rule = self._RATE_RULES[group]
            group_count = len([
                ts for ts in self._group_requests[group]
                if now - ts < rule.window_seconds
            ])
            if group_count >= rule.max_requests_per_window:
                return False

        return True

    def get_status(self) -> Dict[str, Any]:
        """현재 Rate Limit 상태 조회"""
        now = time.time()

        # 전역 상태
        global_count = len([ts for ts in self._global_requests if now - ts < 1])

        # 그룹별 상태
        group_status = {}
        for group, requests in self._group_requests.items():
            if group in self._RATE_RULES:
                rule = self._RATE_RULES[group]
                window_count = len([ts for ts in requests if now - ts < rule.window_seconds])
                group_status[group.value] = {
                    'current': window_count,
                    'limit': rule.max_requests_per_window,
                    'window_seconds': rule.window_seconds,
                    'usage_percent': (window_count / rule.max_requests_per_window) * 100
                }

        # 전략 성능 통계
        total_requests = self._strategy_stats['total_requests']
        total_wait_time = self._strategy_stats['total_wait_time']
        immediate_passes = self._strategy_stats['immediate_passes']
        calculations_needed = self._strategy_stats['calculations_needed']

        strategy_performance = {
            'current_strategy': self.strategy.value,
            'total_requests': total_requests,
            'immediate_pass_rate': (immediate_passes / max(total_requests, 1)) * 100,
            'calculation_rate': (calculations_needed / max(total_requests, 1)) * 100,
            'average_wait_time_ms': (total_wait_time / max(total_requests, 1)) * 1000,
            'total_wait_time_ms': total_wait_time * 1000
        }

        return {
            'client_id': self.client_id,
            'exchange': 'upbit',
            'strategy': strategy_performance,
            'global': {
                'current': global_count,
                'limit': self._RATE_RULES[UpbitRateLimitGroup.GLOBAL].requests_per_second,
                'usage_percent': (global_count / self._RATE_RULES[UpbitRateLimitGroup.GLOBAL].requests_per_second) * 100
            },
            'groups': group_status,
            'server_info': {
                'limit': self._server_limit,
                'remaining': self._server_remaining,
                'reset_time': self._server_reset_time
            },
            'backoff': {
                'consecutive_limits': self._consecutive_limits,
                'multiplier': self._backoff_multiplier,
                'throttled_until': self._throttled_until
            },
            'endpoint_mappings': {k: v.value for k, v in self._ENDPOINT_MAPPINGS.items()}
        }


# 편의 팩토리 함수들
def create_upbit_rate_limiter(client_id: Optional[str] = None,
                              strategy: RateLimitStrategy = RateLimitStrategy.HYBRID_FAST) -> UpbitRateLimiter:
    """업비트 Rate Limiter 생성"""
    return UpbitRateLimiter(client_id, strategy)


# 🌍 글로벌 공유 Rate Limiter - IP 기반 10 RPS 제한 공유
_global_shared_limiters: Dict[str, "UpbitRateLimiter"] = {}
_global_rate_limiters: Dict[str, "UpbitRateLimiter"] = {}  # 기존 호환성


def create_shared_upbit_limiter(api_type: str = "public",
                                strategy: RateLimitStrategy = RateLimitStrategy.HYBRID_FAST) -> UpbitRateLimiter:
    """업비트 공유 Rate Limiter - 모든 클라이언트가 IP 기반 10 RPS 제한 공유"""
    key = f"shared_{api_type}_{strategy.value}"
    if key not in _global_shared_limiters:
        _global_shared_limiters[key] = UpbitRateLimiter(f"shared_{api_type}", strategy)
    return _global_shared_limiters[key]


def create_upbit_public_limiter(client_id: Optional[str] = None,
                                strategy: RateLimitStrategy = RateLimitStrategy.HYBRID_FAST,
                                use_shared: bool = True) -> UpbitRateLimiter:
    """업비트 공개 API용 Rate Limiter"""
    if use_shared:
        # 🎯 IP 기반 공유 제한 - 모든 클라이언트가 동일한 인스턴스 사용
        return create_shared_upbit_limiter("public", strategy)
    else:
        # 기존 방식 - 클라이언트별 독립 (테스트 전용)
        key = f"{client_id or 'upbit_public'}_{strategy.value}"
        if key not in _global_rate_limiters:
            _global_rate_limiters[key] = UpbitRateLimiter(client_id or "upbit_public", strategy)
        return _global_rate_limiters[key]


def create_upbit_private_limiter(client_id: Optional[str] = None,
                                 strategy: RateLimitStrategy = RateLimitStrategy.AIOLIMITER_OPTIMIZED,
                                 use_shared: bool = True) -> UpbitRateLimiter:
    """업비트 프라이빗 API용 Rate Limiter"""
    if use_shared:
        # 🎯 IP 기반 공유 제한 - 모든 클라이언트가 동일한 인스턴스 사용
        return create_shared_upbit_limiter("private", strategy)
    else:
        # 기존 방식 - 클라이언트별 독립 (테스트 전용)
        key = f"{client_id or 'upbit_private'}_{strategy.value}"
        if key not in _global_rate_limiters:
            _global_rate_limiters[key] = UpbitRateLimiter(client_id or "upbit_private", strategy)
        return _global_rate_limiters[key]


def create_upbit_websocket_limiter(client_id: Optional[str] = None,
                                   strategy: RateLimitStrategy = RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW,
                                   use_shared: bool = True) -> UpbitRateLimiter:
    """업비트 WebSocket용 Rate Limiter"""
    if use_shared:
        # 🎯 IP 기반 공유 제한 - 모든 클라이언트가 동일한 인스턴스 사용
        return create_shared_upbit_limiter("websocket", strategy)
    else:
        # 기존 방식 - 클라이언트별 독립 (테스트 전용)
        key = f"{client_id or 'upbit_websocket'}_{strategy.value}"
        if key not in _global_rate_limiters:
            _global_rate_limiters[key] = UpbitRateLimiter(client_id or "upbit_websocket", strategy)
        return _global_rate_limiters[key]


def get_available_strategies() -> Dict[str, str]:
    """사용 가능한 Rate Limiting 전략 목록"""
    return {
        strategy.value: {
            RateLimitStrategy.CLOUDFLARE_SLIDING_WINDOW.value: "Cloudflare 방식 - 정확성 중시, 업계 표준",
            RateLimitStrategy.AIOLIMITER_OPTIMIZED.value: "aiolimiter 최적화 - 성능 중시, 빠른 응답",
            RateLimitStrategy.HYBRID_FAST.value: "하이브리드 - 속도와 정확성 균형 (권장)",
            RateLimitStrategy.LEGACY_CONSERVATIVE.value: "Legacy 방식 - 최고 안전성, 429 오류 거의 없음",
            RateLimitStrategy.RESPONSE_INTERVAL_SIMPLE.value: "단순 응답간격 - 응답 완료 시점 기반 간격 제어",
            RateLimitStrategy.SMART_RESPONSE_ADAPTIVE.value: "스마트 응답적응 - 예측적 성능 최적화 (실험적)"
        }[strategy.value] for strategy in RateLimitStrategy
    }
