"""
업비트 통합 Rate Limiter v2.0 - Lock-Free + Dynamic + Zero-429
- aiohttp BaseConnector 패턴 기반 Lock-Free 구현
- 동적 조정 기능 내장 (429 자동 대응)
- 예방적 스로틀링 내장
- 통합된 모니터링 시스템
- 전역 공유 구조 지원

기존 5개 파일의 기능을 단일 파일로 통합:
- upbit_rate_limiter.py (기본 GCRA)
- dynamic_rate_limiter_wrapper.py (동적 조정)
- lock_free_gcra.py (Lock-Free 패턴)
- rate_limit_monitor.py (모니터링)
- precision_timing.py (정밀 타이밍)
"""

import asyncio
import time
import collections
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import random

from upbit_auto_trading.infrastructure.logging import create_component_logger


class UpbitRateLimitGroup(Enum):
    """업비트 API Rate Limit 그룹 (공식 문서 기준)"""
    REST_PUBLIC = "rest_public"              # 10 RPS
    REST_PRIVATE_DEFAULT = "rest_private_default"  # 30 RPS
    REST_PRIVATE_ORDER = "rest_private_order"      # 8 RPS
    REST_PRIVATE_CANCEL_ALL = "rest_private_cancel_all"  # 0.5 RPS (2초당 1회)
    WEBSOCKET = "websocket"                  # 5 RPS AND 100 RPM


class AdaptiveStrategy(Enum):
    """적응형 전략"""
    CONSERVATIVE = "conservative"  # Zero-429 우선
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class WaiterState(Enum):
    """대기자 상태"""
    WAITING = "waiting"
    READY = "ready"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class UnifiedRateLimiterConfig:
    """통합 Rate Limiter 설정"""
    # 기본 GCRA 설정
    rps: float
    burst_capacity: int

    # 동적 조정 설정
    enable_dynamic_adjustment: bool = True
    error_429_threshold: int = 1  # Zero-429 정책
    error_429_window: float = 60.0
    reduction_ratio: float = 0.8
    min_ratio: float = 0.5
    recovery_delay: float = 300.0  # 5분 보수적 복구
    recovery_step: float = 0.05
    recovery_interval: float = 30.0

    # 예방적 스로틀링 설정
    enable_preventive_throttling: bool = True
    preventive_window: float = 30.0
    max_preventive_delay: float = 0.5

    # 전략
    strategy: AdaptiveStrategy = AdaptiveStrategy.CONSERVATIVE

    @classmethod
    def from_rps(cls, rps: float, burst_capacity: int = None, **kwargs):
        """RPS 기반 설정 생성"""
        if burst_capacity is None:
            burst_capacity = max(1, int(rps))

        return cls(rps=rps, burst_capacity=burst_capacity, **kwargs)

    @property
    def emission_interval(self) -> float:
        """토큰 배출 간격"""
        return 1.0 / self.rps

    @property
    def increment(self) -> float:
        """TAT 증가량"""
        return self.emission_interval


@dataclass
class WaiterInfo:
    """대기자 정보"""
    future: asyncio.Future
    requested_at: float
    ready_at: float
    group: UpbitRateLimitGroup
    endpoint: str
    state: WaiterState = WaiterState.WAITING
    waiter_id: str = ""


@dataclass
class GroupStats:
    """그룹별 통계 및 동적 상태"""
    # 기본 통계
    total_requests: int = 0
    total_waits: int = 0
    total_wait_time: float = 0.0
    concurrent_waiters: int = 0
    max_concurrent_waiters: int = 0
    race_conditions_prevented: int = 0

    # 429 관련
    error_429_count: int = 0
    error_429_history: List[float] = field(default_factory=list)

    # 동적 조정
    current_rate_ratio: float = 1.0
    last_reduction_time: Optional[float] = None
    last_recovery_time: Optional[float] = None
    original_config: Optional[UnifiedRateLimiterConfig] = None

    def add_429_error(self, timestamp: float):
        """429 에러 기록"""
        self.error_429_count += 1
        self.error_429_history.append(timestamp)

        # 1시간 이상 된 기록 정리
        cutoff = timestamp - 3600.0
        self.error_429_history = [t for t in self.error_429_history if t > cutoff]


class UnifiedUpbitRateLimiter:
    """
    업비트 통합 Rate Limiter v2.0

    주요 특징:
    1. Lock-Free GCRA (aiohttp 패턴)
    2. 동적 조정 (429 자동 대응)
    3. 예방적 스로틀링
    4. 통합 모니터링
    5. Zero-429 정책

    기존 5개 파일 기능을 단일 클래스로 통합
    """

    def __init__(self, group_configs: Optional[Dict[UpbitRateLimitGroup, UnifiedRateLimiterConfig]] = None):
        # 기본 설정
        self.group_configs = group_configs or self._create_default_configs()

        # 그룹별 상태
        self.group_stats: Dict[UpbitRateLimitGroup, GroupStats] = {}
        self.group_tats: Dict[UpbitRateLimitGroup, float] = {}  # Theoretical Arrival Time

        # Lock-Free 대기열 (aiohttp 패턴)
        self.waiters: Dict[UpbitRateLimitGroup, collections.OrderedDict[str, WaiterInfo]] = {}

        # 제어
        self._running = True
        self._adjustment_lock = asyncio.Lock()
        self._recovery_task: Optional[asyncio.Task] = None
        self._notifier_tasks: Dict[UpbitRateLimitGroup, asyncio.Task] = {}

        # 로깅
        self.logger = create_component_logger("UnifiedUpbitRateLimiter")

        # 콜백
        self.on_429_detected: Optional[Callable] = None
        self.on_rate_reduced: Optional[Callable] = None
        self.on_rate_recovered: Optional[Callable] = None

        self._initialize_groups()
        self.logger.info("🚀 통합 Rate Limiter v2.0 초기화 완료")

    def _create_default_configs(self) -> Dict[UpbitRateLimitGroup, UnifiedRateLimiterConfig]:
        """기본 설정 생성 - 업비트 공식 Rate Limit 규칙"""
        return {
            UpbitRateLimitGroup.REST_PUBLIC: UnifiedRateLimiterConfig.from_rps(
                rps=10.0, burst_capacity=10,  # 10 RPS, Zero-429를 위한 최대 버스트
                strategy=AdaptiveStrategy.CONSERVATIVE
            ),
            UpbitRateLimitGroup.REST_PRIVATE_DEFAULT: UnifiedRateLimiterConfig.from_rps(
                rps=30.0, burst_capacity=30,  # 30 RPS, 최대 버스트
                strategy=AdaptiveStrategy.CONSERVATIVE
            ),
            UpbitRateLimitGroup.REST_PRIVATE_ORDER: UnifiedRateLimiterConfig.from_rps(
                rps=8.0, burst_capacity=8,   # 8 RPS, 최대 버스트
                strategy=AdaptiveStrategy.CONSERVATIVE
            ),
            UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL: UnifiedRateLimiterConfig(
                rps=0.5, burst_capacity=1,  # 0.5 RPS (2초당 1회), 버스트 없음
                strategy=AdaptiveStrategy.CONSERVATIVE
            ),
            UpbitRateLimitGroup.WEBSOCKET: UnifiedRateLimiterConfig.from_rps(
                rps=5.0, burst_capacity=5,  # 5 RPS + 100 RPM 이중 윈도우는 별도 처리
                enable_dynamic_adjustment=False  # WebSocket은 동적 조정 비활성화
            )
        }

    def _initialize_groups(self):
        """그룹 초기화"""
        for group, config in self.group_configs.items():
            # 통계 초기화
            stats = GroupStats()
            stats.original_config = config
            self.group_stats[group] = stats

            # TAT 초기화
            self.group_tats[group] = 0.0

            # 대기열 초기화
            self.waiters[group] = collections.OrderedDict()

            self.logger.debug(f"📊 그룹 초기화: {group.value} ({config.rps} RPS)")

    async def start_background_tasks(self):
        """백그라운드 태스크 시작"""
        if self._recovery_task is None:
            self._recovery_task = asyncio.create_task(self._recovery_loop())

        # 각 그룹별 알림 태스크
        for group in self.group_configs.keys():
            if group not in self._notifier_tasks:
                self._notifier_tasks[group] = asyncio.create_task(
                    self._background_notifier(group)
                )

        self.logger.info("🔄 백그라운드 태스크 시작 완료")

    async def stop_background_tasks(self):
        """백그라운드 태스크 정지"""
        self._running = False

        # 복구 태스크 정지
        if self._recovery_task and not self._recovery_task.done():
            try:
                self._recovery_task.cancel()
                await asyncio.wait_for(self._recovery_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            finally:
                self._recovery_task = None

        # 알림 태스크들 정지
        for group, task in self._notifier_tasks.items():
            if not task.done():
                try:
                    task.cancel()
                    await asyncio.wait_for(task, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

        self._notifier_tasks.clear()
        self.logger.info("⏹️ 백그라운드 태스크 정지 완료")

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
        # PRIVATE API - CANCEL ALL (REST_PRIVATE_CANCEL_ALL) - 0.5 RPS
        # ============================================
        '/orders/cancel_all': UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL,

        # ============================================
        # WEBSOCKET (WEBSOCKET) - 5 RPS + 100 RPM
        # ============================================
        'websocket_connect': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_message': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_availability_check': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_delay_check': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_subscription': UpbitRateLimitGroup.WEBSOCKET,
        'test_message': UpbitRateLimitGroup.WEBSOCKET,
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

    async def acquire(self, endpoint: str, method: str = 'GET', **kwargs) -> None:
        """
        Rate Limit 획득 - 통합 구현

        1. 그룹 결정
        2. 예방적 스로틀링 적용
        3. Lock-Free 토큰 획득
        4. 429 처리 및 동적 조정
        """
        group = self._get_rate_limit_group(endpoint, method)
        config = self.group_configs[group]
        stats = self.group_stats[group]

        now = time.monotonic()
        stats.total_requests += 1

        # 1단계: 예방적 스로틀링
        if config.enable_preventive_throttling:
            await self._apply_preventive_throttling(group, stats, now)

        # 2단계: Lock-Free 토큰 획득
        await self._acquire_token_lock_free(group, endpoint, now)

        self.logger.debug(f"✅ Rate Limit 획득: {endpoint} -> {group.value}")

    async def _apply_preventive_throttling(self, group: UpbitRateLimitGroup, stats: GroupStats, now: float):
        """예방적 스로틀링"""
        config = self.group_configs[group]

        if not stats.error_429_history:
            return

        # 최근 429 확인
        recent_429s = [t for t in stats.error_429_history
                      if now - t <= config.preventive_window]

        if recent_429s:
            time_since_last = now - max(recent_429s)

            if time_since_last < 10.0:  # 10초 이내
                # Rate 비율에 따른 추가 대기
                safety_delay = (1.0 - stats.current_rate_ratio) * config.max_preventive_delay

                if safety_delay > 0.05:  # 50ms 이상만
                    # 미세 지터 추가 (race condition 방지)
                    jitter = random.uniform(0.9, 1.1)
                    final_delay = safety_delay * jitter

                    self.logger.debug(f"🛡️ 예방적 대기: {group.value} (+{final_delay*1000:.0f}ms)")
                    await asyncio.sleep(final_delay)

    async def _acquire_token_lock_free(self, group: UpbitRateLimitGroup, endpoint: str, now: float):
        """Lock-Free 토큰 획득 (aiohttp 패턴)"""
        config = self.group_configs[group]
        stats = self.group_stats[group]

        # 1차: 즉시 사용 가능 확인
        if self._try_consume_token(group, now):
            return

        # 2차: 대기 필요 - Future 생성
        future = asyncio.Future()
        waiter_id = f"waiter_{group.value}_{id(future)}_{now:.6f}"

        ready_at = self._schedule_token_availability(group, now)

        waiter_info = WaiterInfo(
            future=future,
            requested_at=now,
            ready_at=ready_at,
            group=group,
            endpoint=endpoint,
            state=WaiterState.WAITING,
            waiter_id=waiter_id
        )

        # OrderedDict에 추가 (FIFO 보장)
        self.waiters[group][waiter_id] = waiter_info

        # 통계 업데이트
        stats.total_waits += 1
        stats.concurrent_waiters = len(self.waiters[group])
        if stats.concurrent_waiters > stats.max_concurrent_waiters:
            stats.max_concurrent_waiters = stats.concurrent_waiters

        self.logger.debug(f"⏳ 대기열 추가: {waiter_id} (ready_at={ready_at:.3f})")

        try:
            # 3차: 비동기 대기
            await future

            # 4차: Re-check (aiohttp 핵심)
            recheck_now = time.monotonic()

            if self._try_consume_token(group, recheck_now):
                waiter_info.state = WaiterState.COMPLETED
            else:
                # Race condition 방지 - 재귀 호출
                stats.race_conditions_prevented += 1
                self.logger.debug(f"🔄 Race condition 방지: {waiter_id}")
                await self._acquire_token_lock_free(group, endpoint, recheck_now)
                return

        finally:
            # 대기열에서 제거
            self.waiters[group].pop(waiter_id, None)
            stats.concurrent_waiters = len(self.waiters[group])

            # 대기 시간 통계
            if waiter_info.state != WaiterState.CANCELLED:
                wait_duration = time.monotonic() - waiter_info.requested_at
                stats.total_wait_time += wait_duration

    def _try_consume_token(self, group: UpbitRateLimitGroup, now: float) -> bool:
        """토큰 소모 시도 (원자적)"""
        config = self.group_configs[group]
        current_tat = self.group_tats[group]

        if current_tat <= now:
            # 토큰 사용 가능
            effective_increment = config.increment / self.group_stats[group].current_rate_ratio
            self.group_tats[group] = now + effective_increment
            return True
        else:
            return False

    def _schedule_token_availability(self, group: UpbitRateLimitGroup, now: float) -> float:
        """다음 토큰 사용 가능 시점 예약"""
        config = self.group_configs[group]
        current_tat = self.group_tats[group]

        effective_increment = config.increment / self.group_stats[group].current_rate_ratio

        if current_tat <= now:
            next_available = now + effective_increment
        else:
            next_available = current_tat + effective_increment

        self.group_tats[group] = next_available
        return next_available

    async def notify_429_error(self, endpoint: str, method: str = 'GET', **kwargs):
        """429 에러 알림 및 동적 조정"""
        group = self._get_rate_limit_group(endpoint, method)
        config = self.group_configs[group]

        if not config.enable_dynamic_adjustment:
            return

        stats = self.group_stats[group]
        now = time.monotonic()

        stats.add_429_error(now)

        self.logger.warning(f"🚨 429 에러 감지: {group.value} - {endpoint} (총 {stats.error_429_count}회)")

        # 콜백 호출
        if self.on_429_detected:
            self.on_429_detected(group, endpoint, stats.error_429_count)

        async with self._adjustment_lock:
            # 즉시 토큰 고갈
            await self._emergency_token_depletion(group, now)

            # 최근 429 확인
            recent_errors = [t for t in stats.error_429_history
                           if now - t <= config.error_429_window]

            # 임계치 초과 시 Rate 감소
            if len(recent_errors) >= config.error_429_threshold:
                await self._reduce_rate_limit(group, stats, now)

    async def _emergency_token_depletion(self, group: UpbitRateLimitGroup, now: float):
        """긴급 토큰 고갈"""
        config = self.group_configs[group]

        # 강력한 토큰 고갈 (T * 10)
        depletion_time = config.increment * 10.0
        self.group_tats[group] = now + depletion_time

        self.logger.warning(f"🔥 긴급 토큰 고갈: {group.value} (대기시간 {depletion_time:.1f}초)")

    async def _reduce_rate_limit(self, group: UpbitRateLimitGroup, stats: GroupStats, timestamp: float):
        """Rate Limit 감소"""
        config = self.group_configs[group]

        if stats.current_rate_ratio <= config.min_ratio:
            self.logger.warning(f"⚠️ {group.value} 이미 최소 비율 도달")
            return

        old_ratio = stats.current_rate_ratio
        stats.current_rate_ratio *= config.reduction_ratio
        stats.current_rate_ratio = max(stats.current_rate_ratio, config.min_ratio)
        stats.last_reduction_time = timestamp

        if self.on_rate_reduced:
            self.on_rate_reduced(group, old_ratio, stats.current_rate_ratio)

        self.logger.warning(f"🔻 Rate 감소: {group.value} {old_ratio:.1%} → {stats.current_rate_ratio:.1%}")

    async def _recovery_loop(self):
        """백그라운드 복구 루프"""
        while self._running:
            try:
                await asyncio.sleep(30.0)  # 30초마다 체크
                await self._check_recovery()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ 복구 루프 오류: {e}")

    async def _check_recovery(self):
        """복구 가능한 그룹 확인"""
        now = time.monotonic()

        async with self._adjustment_lock:
            for group, stats in self.group_stats.items():
                config = self.group_configs[group]

                if (config.enable_dynamic_adjustment and
                    stats.current_rate_ratio < 1.0 and
                    stats.last_reduction_time and
                    now - stats.last_reduction_time >= config.recovery_delay):

                    # 최근 429 없는지 확인
                    recent_errors = [t for t in stats.error_429_history
                                   if now - t <= config.recovery_delay]

                    if len(recent_errors) == 0:
                        await self._recover_rate_limit(group, stats, now)

    async def _recover_rate_limit(self, group: UpbitRateLimitGroup, stats: GroupStats, timestamp: float):
        """Rate Limit 점진적 복구"""
        config = self.group_configs[group]

        old_ratio = stats.current_rate_ratio
        stats.current_rate_ratio = min(1.0, stats.current_rate_ratio + config.recovery_step)
        stats.last_recovery_time = timestamp

        if self.on_rate_recovered:
            self.on_rate_recovered(group, old_ratio, stats.current_rate_ratio)

        self.logger.info(f"🔺 Rate 복구: {group.value} {old_ratio:.1%} → {stats.current_rate_ratio:.1%}")

    async def _background_notifier(self, group: UpbitRateLimitGroup):
        """백그라운드 대기자 알림 (그룹별)"""
        while self._running:
            try:
                if not self.waiters[group]:
                    await asyncio.sleep(0.1)
                    continue

                now = time.monotonic()

                # 시간이 된 대기자 찾아 깨우기
                for waiter_id, waiter_info in list(self.waiters[group].items()):
                    if (waiter_info.state == WaiterState.WAITING and
                        now >= waiter_info.ready_at and
                        not waiter_info.future.done()):

                        waiter_info.state = WaiterState.READY
                        waiter_info.future.set_result(None)
                        break

                # 다음 확인 시점
                next_check = min(
                    (info.ready_at for info in self.waiters[group].values()
                     if info.state == WaiterState.WAITING),
                    default=now + 0.1
                )

                sleep_time = max(0.001, next_check - now)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"❌ 알림 태스크 오류 ({group.value}): {e}")
                await asyncio.sleep(0.1)

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """종합 상태 조회"""
        now = time.monotonic()

        result = {
            'overall': {
                'total_groups': len(self.group_configs),
                'running': self._running,
                'background_tasks_active': len(self._notifier_tasks)
            },
            'groups': {}
        }

        for group, config in self.group_configs.items():
            stats = self.group_stats[group]
            current_tat = self.group_tats[group]

            result['groups'][group.value] = {
                'config': {
                    'rps': config.rps,
                    'effective_rps': config.rps * stats.current_rate_ratio,
                    'burst_capacity': config.burst_capacity,
                    'dynamic_adjustment': config.enable_dynamic_adjustment,
                    'preventive_throttling': config.enable_preventive_throttling
                },
                'state': {
                    'current_tat': current_tat,
                    'next_token_available_in': max(0, current_tat - now),
                    'current_rate_ratio': stats.current_rate_ratio,
                    'active_waiters': len(self.waiters[group])
                },
                'stats': {
                    'total_requests': stats.total_requests,
                    'total_waits': stats.total_waits,
                    'error_429_count': stats.error_429_count,
                    'race_conditions_prevented': stats.race_conditions_prevented,
                    'max_concurrent_waiters': stats.max_concurrent_waiters
                },
                'performance': {
                    'avg_wait_time': (
                        stats.total_wait_time / stats.total_waits
                        if stats.total_waits > 0 else 0
                    ),
                    'wait_ratio': (
                        stats.total_waits / stats.total_requests
                        if stats.total_requests > 0 else 0
                    ),
                    'recent_429_count': len([
                        t for t in stats.error_429_history
                        if now - t <= 60.0
                    ])
                }
            }

        return result


# 전역 인스턴스
_GLOBAL_UNIFIED_LIMITER: Optional[UnifiedUpbitRateLimiter] = None


async def get_unified_rate_limiter(
    group_configs: Optional[Dict[UpbitRateLimitGroup, UnifiedRateLimiterConfig]] = None
) -> UnifiedUpbitRateLimiter:
    """전역 통합 Rate Limiter 획득"""
    global _GLOBAL_UNIFIED_LIMITER

    if _GLOBAL_UNIFIED_LIMITER is None:
        _GLOBAL_UNIFIED_LIMITER = UnifiedUpbitRateLimiter(group_configs)
        await _GLOBAL_UNIFIED_LIMITER.start_background_tasks()

    return _GLOBAL_UNIFIED_LIMITER


# 편의 함수들
async def unified_gate_rest_public(endpoint: str, method: str = 'GET') -> None:
    """REST Public API 게이트"""
    limiter = await get_unified_rate_limiter()
    await limiter.acquire(endpoint, method)


async def unified_gate_rest_private(endpoint: str, method: str = 'GET') -> None:
    """REST Private API 게이트"""
    limiter = await get_unified_rate_limiter()
    await limiter.acquire(endpoint, method)


async def notify_unified_429_error(endpoint: str, method: str = 'GET') -> None:
    """통합 429 에러 알림"""
    limiter = await get_unified_rate_limiter()
    await limiter.notify_429_error(endpoint, method)


# 레거시 호환성
async def get_global_rate_limiter():
    """레거시 호환성 - 기존 코드와의 호환"""
    return await get_unified_rate_limiter()
