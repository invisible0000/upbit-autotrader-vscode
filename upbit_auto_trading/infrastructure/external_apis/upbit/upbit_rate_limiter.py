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
import logging
import math
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

# 표준 로깅 폴백 (외부 의존성 제거)
try:
    from upbit_auto_trading.infrastructure.logging import create_component_logger
    def _create_logger(name: str):
        return create_component_logger(name)
except Exception:
    def _create_logger(name: str):
        return logging.getLogger(name)


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
    burst_capacity: int = 1  # 버스트 용량 (토큰 수)
    slack_ratio: float = 0.0  # 여유분 비율 (0~1) - deprecated, burst_capacity 사용 권장

    @classmethod
    def from_rps(cls, rps: float, burst_capacity: int = 1, slack_ratio: float = 0.0) -> 'GCRAConfig':
        """RPS로부터 GCRA 설정 생성 (버스트 지원)"""
        return cls(T_seconds=1.0 / rps, burst_capacity=burst_capacity, slack_ratio=slack_ratio)

    @classmethod
    def from_interval(cls, interval_seconds: float, burst_capacity: int = 1, slack_ratio: float = 0.0) -> 'GCRAConfig':
        """간격(초)으로부터 GCRA 설정 생성 (버스트 지원)"""
        return cls(T_seconds=interval_seconds, burst_capacity=burst_capacity, slack_ratio=slack_ratio)

    @classmethod
    def from_rpm(cls, requests_per_minute: int, burst_capacity: Optional[int] = None) -> 'GCRAConfig':
        """RPM(분당 요청수)으로부터 GCRA 설정 생성 - 진정한 분 단위 제한"""
        if burst_capacity is None:
            # 기본 버스트: 분당 제한의 10% 또는 최소 5개
            burst_capacity = max(5, requests_per_minute // 10)

        # 분당 제한을 초 단위로 변환하되, 버스트를 고려한 간격 설정
        T_seconds = 60.0 / requests_per_minute
        return cls(T_seconds=T_seconds, burst_capacity=burst_capacity)


class GCRA:
    """
    Generic Cell Rate Algorithm 구현 - 버스트 지원

    상태 1개(TAT)로 간격 제어하는 정확하고 단순한 알고리즘
    Leaky Bucket과 등가하지만 더 효율적이며, 버스트 용량 지원
    """

    def __init__(self, config: GCRAConfig):
        self.T = config.T_seconds
        self.burst_capacity = config.burst_capacity
        self.slack = self.T * config.slack_ratio  # 하위 호환성

        # 버스트 용량이 설정된 경우 이를 우선 사용
        if self.burst_capacity > 1:
            # 버스트 토큰만큼의 여유 시간 제공
            self.burst_slack = self.T * (self.burst_capacity - 1)
        else:
            self.burst_slack = self.slack

        self.tat = 0.0  # Theoretical Arrival Time (monotonic time)

    def need_wait(self, now: float) -> float:
        """지금 요청하려면 추가로 기다려야 하는 시간(초). 0 이하면 즉시 가능."""
        allow_at = self.tat - self.burst_slack
        if now >= allow_at:
            return 0.0
        return allow_at - now

    def consume(self, now: float) -> None:
        """토큰 소비 (호출 전 need_wait(now) == 0 이어야 함)"""
        self.tat = max(now, self.tat) + self.T

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환 - 개선된 버스트 토큰 계산"""
        now = time.monotonic()

        # 선점된 시간과 사용된 토큰 수 계산 (전문가 제안)
        ahead = max(0.0, self.tat - now)  # 선점된 시간
        used_tokens = math.ceil(ahead / self.T) if ahead > 0 else 0  # 선점으로 간주할 토큰 수
        available_burst_tokens = max(0, self.burst_capacity - used_tokens)  # 남은 버스트 추정

        return {
            'tat': self.tat,
            'now': now,
            'need_wait': self.need_wait(now),
            'T': self.T,
            'burst_capacity': self.burst_capacity,
            'burst_slack': self.burst_slack,
            'available_burst_tokens': available_burst_tokens
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

    # 업비트 공식 Rate Limit 규칙 - Zero-429 정책 적용 (2025-09-12)
    # 측정 결과: 95ms(10.53 RPS)까지 100% 안전, Zero-429를 위한 버스트 증가
    _GROUP_CONFIGS = {
        UpbitRateLimitGroup.REST_PUBLIC: [
            GCRAConfig.from_rps(10.0, burst_capacity=10)  # 10 RPS, Zero-429를 위한 최대 버스트 (10개)
        ],
        UpbitRateLimitGroup.REST_PRIVATE_DEFAULT: [
            GCRAConfig.from_rps(30.0, burst_capacity=30)  # 30 RPS, 최대 버스트
        ],
        UpbitRateLimitGroup.REST_PRIVATE_ORDER: [
            GCRAConfig.from_rps(8.0, burst_capacity=8)   # 8 RPS, 최대 버스트
        ],
        UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL: [
            GCRAConfig.from_interval(2.0, burst_capacity=1)  # 0.5 RPS, 버스트 없음 (안전성)
        ],
        UpbitRateLimitGroup.WEBSOCKET: [
            # 5 RPS 제한 (최대 버스트 허용)
            GCRAConfig.from_rps(5.0, burst_capacity=5),
            # 100 RPM 제한 (WebSocket 특성 고려 대용량 버스트 허용)
            GCRAConfig.from_rpm(100, burst_capacity=50)  # 분당 100요청, 50개 버스트로 즉시성 확보
        ]
    }

    # 엔드포인트 → 그룹 매핑 (업비트 공식 문서 기준)
    _ENDPOINT_MAPPINGS = {
        # ============================================
        # PUBLIC API (REST_PUBLIC) - 10 RPS
        # ============================================
        # 현재가 정보
        '/ticker': UpbitRateLimitGroup.REST_PUBLIC,
        '/tickers': UpbitRateLimitGroup.REST_PUBLIC,

        # 호가 정보
        '/orderbook': UpbitRateLimitGroup.REST_PUBLIC,

        # 체결 정보
        '/trades': UpbitRateLimitGroup.REST_PUBLIC,
        '/trades/ticks': UpbitRateLimitGroup.REST_PUBLIC,

        # 캔들 정보 (모든 종류)
        '/candles': UpbitRateLimitGroup.REST_PUBLIC,
        '/candles/minutes': UpbitRateLimitGroup.REST_PUBLIC,
        '/candles/days': UpbitRateLimitGroup.REST_PUBLIC,
        '/candles/weeks': UpbitRateLimitGroup.REST_PUBLIC,
        '/candles/months': UpbitRateLimitGroup.REST_PUBLIC,
        '/candles/seconds': UpbitRateLimitGroup.REST_PUBLIC,

        # 마켓 코드
        '/market/all': UpbitRateLimitGroup.REST_PUBLIC,

        # ============================================
        # PRIVATE API - DEFAULT (REST_PRIVATE_DEFAULT) - 30 RPS
        # ============================================
        # 계좌 정보
        '/accounts': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/account_info': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,

        # 주문 조회 (GET 요청들)
        '/orders': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,  # GET만 (POST/DELETE는 별도)
        '/order': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,   # GET만 (DELETE는 별도)
        '/orders/chance': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/orders/uuids': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,  # GET만
        '/orders/open': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,   # GET만
        '/orders/closed': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,

        # 입출금 관련
        '/withdraws': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/deposits': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/deposits/coin_addresses': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/deposits/generate_coin_address': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/deposits/coin_address': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/withdraws/chance': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/withdraws/coin': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        '/withdraws/krw': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,

        # ============================================
        # PRIVATE API - ORDER (REST_PRIVATE_ORDER) - 8 RPS
        # ============================================
        # 주문 생성/취소는 메서드별 매핑에서 처리
        # ('/orders', 'POST'): ORDER 그룹
        # ('/orders', 'DELETE'): ORDER 그룹
        # ('/order', 'DELETE'): ORDER 그룹

        # ============================================
        # PRIVATE API - CANCEL ALL (REST_PRIVATE_CANCEL_ALL) - 0.5 RPS
        # ============================================
        '/orders/cancel_all': UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL,

        # ============================================
        # WEBSOCKET (WEBSOCKET) - 5 RPS + 100 RPM
        # ============================================
        'websocket_connect': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_message': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_availability_check': UpbitRateLimitGroup.WEBSOCKET,  # 구 디바운스 최적화용 (deprecated)
        'websocket_delay_check': UpbitRateLimitGroup.WEBSOCKET,         # 새 실제 지연 측정용
        'websocket_subscription': UpbitRateLimitGroup.WEBSOCKET,        # 구독 요청용
        'test_message': UpbitRateLimitGroup.WEBSOCKET,  # 테스트용
    }

    # 메서드별 특별 매핑 (엔드포인트 + HTTP 메서드 조합)
    _METHOD_SPECIFIC_MAPPINGS = {
        # 주문 생성/취소 - ORDER 그룹 (8 RPS)
        ('/orders', 'POST'): UpbitRateLimitGroup.REST_PRIVATE_ORDER,     # 주문 생성
        ('/orders', 'DELETE'): UpbitRateLimitGroup.REST_PRIVATE_ORDER,   # 주문 취소
        ('/order', 'DELETE'): UpbitRateLimitGroup.REST_PRIVATE_ORDER,    # 단일 주문 취소
        ('/orders/uuids', 'DELETE'): UpbitRateLimitGroup.REST_PRIVATE_ORDER,  # UUID 기반 취소

        # 전체 주문 취소 - CANCEL_ALL 그룹 (0.5 RPS)
        ('/orders/open', 'DELETE'): UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL,

        # 주문 조회는 DEFAULT 그룹 (30 RPS) - 이미 기본 매핑에 있음
        ('/orders', 'GET'): UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        ('/order', 'GET'): UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        ('/orders/uuids', 'GET'): UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
        ('/orders/open', 'GET'): UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,
    }

    def __init__(self, client_id: Optional[str] = None):
        self.client_id = client_id or f"upbit_gcra_{id(self)}"
        self.logger = _create_logger("UpbitGCRARateLimiter")

        # 전역 잠금 (asyncio.Lock)
        self._lock = asyncio.Lock()

        # 배치 로깅을 위한 큐
        self._log_queue = []
        self._last_batch_log = time.monotonic()
        self._batch_interval = 2.0  # 2초마다 배치 로그 출력

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
        Rate Limit 게이트 통과 - WebSocket 그룹 개선된 대기시간

        Args:
            endpoint: API 엔드포인트 경로
            method: HTTP 메서드
            max_wait: 최대 대기시간(초)
            jitter_range: 지터 범위(초)

        Raises:
            TimeoutError: max_wait 시간 초과
            ValueError: 알 수 없는 엔드포인트
        """
        # 엔드포인트 → 그룹 매핑 (메서드 포함)
        group = self._get_rate_limit_group(endpoint, method)

        # 🔍 디버깅: Rate Limiter 호출 추적 (성능 최적화 - 필요시에만)
        instance_id = f"{self.client_id}_{id(self)}"
        if self.logger.isEnabledFor(logging.INFO):
            self.logger.info(f"🚀 Rate Limiter 호출: {endpoint} [{method}] -> {group.value} (인스턴스: {instance_id})")

        # WebSocket 그룹의 경우 더 넉넉한 max_wait 적용 (전문가 제안)
        if group == UpbitRateLimitGroup.WEBSOCKET and max_wait < 15.0:
            max_wait = 15.0

        start_time = time.monotonic()
        deadline = start_time + max_wait

        self._stats['total_requests'] += 1

        while True:
            now = time.monotonic()

            async with self._lock:
                # 모든 관련 컨트롤러의 대기시간을 원자적으로 계산하고 소비
                controllers = self._controllers[group]

                # 현재 시점을 다시 확인 (락 획득 동안 시간이 흐름)
                now = time.monotonic()
                wait_times = [controller.need_wait(now) for controller in controllers]
                max_wait_needed = max(wait_times)

                # 🔍 디버깅: 토큰 상태 출력 (성능 최적화 - 대기시에만)
                if max_wait_needed > 0.0:
                    self.logger.debug(f"🔍 토큰 상태: {group.value}, 대기시간: {max_wait_needed:.3f}s")

                if max_wait_needed <= 0.0:
                    # 원자적 토큰 소비: 다시 한번 체크 후 소비
                    final_wait_times = [controller.need_wait(now) for controller in controllers]
                    final_max_wait = max(final_wait_times)

                    if final_max_wait <= 0.0:
                        # 모든 제한을 통과 → 동시에 토큰 소비
                        for controller in controllers:
                            controller.consume(now)

                        elapsed = time.monotonic() - start_time
                        if elapsed < 0.001:  # 1ms 미만이면 즉시 통과
                            self._stats['immediate_passes'] += 1

                        # 성공 로깅 (성능 최적화)
                        self.logger.info(f"✅ Rate Limiter 획득: {endpoint} -> {group.value} ({elapsed * 1000:.1f}ms)")
                        return
                    else:
                        # 체크와 소비 사이에 상태가 변경됨 - 다시 대기 필요
                        max_wait_needed = final_max_wait

            # 대기 필요 → 지터 추가 후 재시도
            wait_time = max_wait_needed + random.uniform(*jitter_range)

            if now + wait_time > deadline:
                self._stats['timeout_errors'] += 1
                self.logger.error(f"❌ Rate Limit 대기시간 초과: {endpoint} (max_wait={max_wait}s)")
                raise TimeoutError(f"Rate limit 대기시간 초과: {endpoint} (max_wait={max_wait}s)")

            self._stats['total_wait_time'] += wait_time

            # 즉시 로깅 (디버깅용)
            self.logger.info(f"⏳ Rate Limiter 대기: {endpoint} -> {group.value} ({wait_time * 1000:.1f}ms)")

            await asyncio.sleep(max(0.0, wait_time))

    def _add_to_log_batch(self, message: str):
        """로그 메시지를 배치에 추가"""
        now = time.monotonic()
        self._log_queue.append(message)

        # 배치 간격이 지났거나 큐가 너무 많이 쌓인 경우 출력
        if (now - self._last_batch_log >= self._batch_interval or
            len(self._log_queue) >= 10):
            self._flush_log_batch()
            self._last_batch_log = now

    def _flush_log_batch(self):
        """배치된 로그 메시지들을 출력"""
        if not self._log_queue:
            return

        # 메시지 종류별 집계
        wait_count = sum(1 for msg in self._log_queue if "대기:" in msg)
        acquire_count = sum(1 for msg in self._log_queue if "획득:" in msg)

        if wait_count > 0 and acquire_count > 0:
            self.logger.info(f"Rate Limiter 활동: 대기 {wait_count}회, 획득 {acquire_count}회")
        elif wait_count > 0:
            self.logger.info(f"Rate Limiter 대기: {wait_count}회")
        elif acquire_count > 0:
            self.logger.info(f"Rate Limiter 획득: {acquire_count}회")

        # 큐 초기화
        self._log_queue.clear()

    def _get_rate_limit_group(self, endpoint: str, method: str = 'GET') -> UpbitRateLimitGroup:
        """엔드포인트와 메서드를 기반으로 Rate Limit 그룹 매핑"""
        # 1. 메서드별 특별 매핑 우선 확인
        method_key = (endpoint, method.upper())
        if method_key in self._METHOD_SPECIFIC_MAPPINGS:
            return self._METHOD_SPECIFIC_MAPPINGS[method_key]

        # 2. 정확한 엔드포인트 매핑 확인
        if endpoint in self._ENDPOINT_MAPPINGS:
            return self._ENDPOINT_MAPPINGS[endpoint]

        # 3. 패턴 매핑 (부분 일치)
        for pattern, group in self._ENDPOINT_MAPPINGS.items():
            if pattern in endpoint:
                return group

        # 4. 기본값: PUBLIC 그룹 (가장 엄격한 제한)
        self.logger.warning(f"알 수 없는 엔드포인트, PUBLIC 그룹 적용: {endpoint} [{method}]")
        return UpbitRateLimitGroup.REST_PUBLIC

    def handle_429_response(self,
                            group: Optional[UpbitRateLimitGroup] = None,
                            retry_after: Optional[float] = None) -> None:
        """
        429 응답 처리 (Rate Limit 초과) - 그룹 한정 패널티

        Args:
            group: 패널티를 적용할 특정 그룹 (None이면 모든 그룹)
            retry_after: 서버에서 제공한 Retry-After 시간(초)
        """
        base_wait = retry_after or 1.0
        jitter_wait = base_wait + random.uniform(0.1, 0.2)  # 100-200ms 지터

        penalty_time = time.monotonic() + jitter_wait

        if group is None:
            # 호환성: 모든 그룹에 패널티 적용
            target_groups = self._controllers.values()
            self.logger.warning(f"429 Rate Limit 응답 수신 (전체 그룹), 대기: {jitter_wait:.2f}초")
        else:
            # 개선: 특정 그룹만 패널티 적용
            target_groups = [self._controllers[group]]
            self.logger.warning(f"429 Rate Limit 응답 수신 ({group.value} 그룹), 대기: {jitter_wait:.2f}초")

        # 타겟 그룹들에만 패널티 적용 (TAT 강제 연장)
        for controllers in target_groups:
            for controller in controllers:
                # TAT를 penalty_time + T로 설정하여 확실한 대기시간 보장
                controller.tat = max(controller.tat, penalty_time + controller.T)

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


async def gate_websocket(action: str = 'websocket_connect', max_wait: float = 15.0) -> None:
    """WebSocket 게이트 (5 RPS + 100 RPM 이중 윈도우) - 넉넉한 대기시간"""
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
