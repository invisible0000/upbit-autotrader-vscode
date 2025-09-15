"""
업비트 Rate Limiter 메인 코어
- UnifiedUpbitRateLimiter 클래스와 유틸리티 함수들
- 검색 키워드: core, limiter, gcra, main
"""

import asyncio
import time
import collections
from typing import Dict, Any, Optional, Callable, List
import uuid

from upbit_auto_trading.infrastructure.logging import create_component_logger
from .upbit_rate_limiter_types import (
    UpbitRateLimitGroup, UnifiedRateLimiterConfig, GroupStats, WaiterInfo,
    AdaptiveStrategy
)
from .upbit_rate_limiter_managers import SelfHealingTaskManager, TimeoutAwareRateLimiter, AtomicTATManager


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
        self.group_tats: Dict[UpbitRateLimitGroup, float] = {}  # Theoretical Arrival Time (초단위)

        # 🆕 웹소켓 복합 제한용 분단위 TAT
        self.group_tats_minute: Dict[UpbitRateLimitGroup, float] = {}  # Theoretical Arrival Time (분단위)

        # � 순수 GCRA: Fixed Window 제거, TAT만으로 모든 제어

        # Lock-Free 대기열 (aiohttp 패턴)
        self.waiters: Dict[UpbitRateLimitGroup, collections.OrderedDict[str, WaiterInfo]] = {}

        # 제어
        self._running = True
        self._adjustment_lock = asyncio.Lock()
        self._recovery_task: Optional[asyncio.Task] = None
        self._notifier_tasks: Dict[UpbitRateLimitGroup, asyncio.Task] = {}

        # 로깅
        self.logger = create_component_logger("UnifiedUpbitRateLimiter")

        # 백그라운드 태스크 시작 여부 추적
        self._background_tasks_started = False

        # 자가치유 태스크 매니저
        self._task_manager = SelfHealingTaskManager(self)
        self._task_manager.logger = self.logger

        # 타임아웃 보장 매니저
        self._timeout_manager = TimeoutAwareRateLimiter(self)
        self._timeout_manager.logger = self.logger

        # 원자적 TAT 매니저
        self._atomic_tat_manager = AtomicTATManager(self)

        # 🔍 슬라이딩 윈도우 관찰 모드 (Phase 1: 기존 시스템에 영향 없음)
        self.sliding_window_config = {
            'enabled': True,  # 관찰 모드 활성화
            'window_size': 60.0,  # 1분 윈도우
            'max_log_size': 1000,  # 메모리 제한
            'cleanup_interval': 30.0  # 정리 주기 (초)
        }

        # 그룹별 요청 로그 저장소 (timestamp, weight)
        self.sliding_window_logs: Dict[UpbitRateLimitGroup, List[tuple[float, int]]] = {
            group: [] for group in UpbitRateLimitGroup
        }

        # 🆕 Phase 1: 하이브리드 알고리즘용 타임스탬프 윈도우
        # 그룹별 타임스탬프 FIFO 윈도우 (deque로 고정 크기 관리)
        self._timestamp_windows: Dict[UpbitRateLimitGroup, collections.deque] = {}

        # 하이브리드 알고리즘 설정
        self.hybrid_config = {
            'enabled': False,  # 기본값 비활성화 (단계별 활성화 예정)
            'window_cleanup_interval': 1.0,  # 1초마다 오래된 타임스탬프 정리
            'detailed_logging': True  # 상세 로깅 활성화
        }

        # 알고리즘 비교 통계
        self.algorithm_comparison_stats = {
            'total_requests': 0,
            'gcra_allowed': 0,
            'sw_allowed': 0,
            'both_allowed': 0,
            'both_denied': 0,
            'gcra_only_allowed': 0,
            'sw_only_allowed': 0,
            'last_cleanup': time.monotonic()
        }

        # 콜백
        self.on_429_detected: Optional[Callable] = None
        self.on_rate_reduced: Optional[Callable] = None
        self.on_rate_recovered: Optional[Callable] = None

        self._initialize_groups()
        self.logger.info("🚀 통합 Rate Limiter v2.0 초기화 완료 (슬라이딩 윈도우 관찰 모드 포함)")

    def _create_default_configs(self) -> Dict[UpbitRateLimitGroup, UnifiedRateLimiterConfig]:
        """기본 설정 생성 - 업비트 공식 Rate Limit 규칙"""
        return {
            UpbitRateLimitGroup.REST_PUBLIC: UnifiedRateLimiterConfig.from_rps(
                rps=9.5, burst_capacity=10,
                strategy=AdaptiveStrategy.CONSERVATIVE
            ),
            UpbitRateLimitGroup.REST_PRIVATE_DEFAULT: UnifiedRateLimiterConfig.from_rps(
                rps=30.0, burst_capacity=30,
                strategy=AdaptiveStrategy.CONSERVATIVE
            ),
            UpbitRateLimitGroup.REST_PRIVATE_ORDER: UnifiedRateLimiterConfig.from_rps(
                rps=8.0, burst_capacity=8,
                strategy=AdaptiveStrategy.CONSERVATIVE
            ),
            UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL: UnifiedRateLimiterConfig(
                rps=0.5, burst_capacity=0.5,
                strategy=AdaptiveStrategy.CONSERVATIVE
            ),
            UpbitRateLimitGroup.WEBSOCKET: UnifiedRateLimiterConfig.from_rps(
                rps=5.0, burst_capacity=1,
                requests_per_minute=100,         # � 순수 GCRA: 분당 100 요청 (0.6초 간격)
                requests_per_minute_burst=10,    # � 순수 GCRA: RPM 버스트 6초 허용 (10 * 0.6초)
                enable_dual_limit=True,          # � 이중 GCRA: 5 RPS + 100 RPM 자연스러운 제어
                enable_dynamic_adjustment=False  # 웹소켓은 고정 제한
            )
        }

    def _initialize_groups(self):
        """그룹 초기화"""
        for group, config in self.group_configs.items():
            # 통계 초기화
            stats = GroupStats()
            stats.original_config = config
            self.group_stats[group] = stats

            # 🎯 순수 GCRA TAT 초기화
            self.group_tats[group] = 0.0

            # 분단위 TAT는 이중 제한 그룹에만 초기화
            if config.enable_dual_limit and config.requests_per_minute is not None:
                self.group_tats_minute[group] = 0.0

            # 대기열 초기화
            self.waiters[group] = collections.OrderedDict()

            # 🆕 Phase 1: 타임스탬프 윈도우 초기화 (burst_capacity 크기)
            window_size = int(config.burst_capacity)
            self._timestamp_windows[group] = collections.deque(maxlen=window_size)

            self.logger.debug(f"📊 그룹 초기화: {group.value} ({config.rps} RPS, 윈도우: {window_size}슬롯)")

    # 엔드포인트 → 그룹 매핑 (클라이언트 실제 사용 경로 기준)
    _ENDPOINT_MAPPINGS = {
        # ============================================
        # PUBLIC API (REST_PUBLIC) - 10 RPS
        # ============================================
        '/market/all': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 페어 목록 조회
        '/ticker': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 페어 단위 현재가 조회
        '/ticker/all': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 마켓 단위 현재가 조회
        '/orderbook': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 호가 조회
        '/orderbook/instruments': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 호가 정책 조회
        '/trades/ticks': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 페어 체결 이력 조회
        '/candles/seconds': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 초(Second) 캔들 조회
        '/candles/minutes': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 분(Minute) 캔들 조회
        '/candles/days': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 일(Day) 캔들 조회
        '/candles/weeks': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 주(Week) 캔들 조회
        '/candles/months': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 월(Month) 캔들 조회
        '/candles/years': UpbitRateLimitGroup.REST_PUBLIC,  # GET, 년(Year) 캔들 조회

        # ============================================
        # PRIVATE API - DEFAULT (REST_PRIVATE_DEFAULT) - 30 RPS
        # ============================================
        '/accounts': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,       # GET, 계정 잔고 조회
        '/order': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,          # GET, DEL, 개별 주문 조회, 개별 주문 취소 접수
        '/orders/chance': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,  # GET, 페어별 주문 가능 정보 조회
        '/orders/open': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,    # GET만, 체결 대기 주문 목록 조회
        '/orders/closed': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,  # GET, 종료 주문 목록 조회
        '/orders/uuids': UpbitRateLimitGroup.REST_PRIVATE_DEFAULT,   # GET, DEL, id로 주문 목록 조회, id로 주문 목록 취소 접수

        # ============================================
        # WEBSOCKET (WEBSOCKET) - 5 RPS + 100 RPM
        # ============================================
        'websocket_connect': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_message': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_subscription': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_ticker': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_trade': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_orderbook': UpbitRateLimitGroup.WEBSOCKET,
        'websocket_candle': UpbitRateLimitGroup.WEBSOCKET,
    }

    # 메서드별 특별 매핑 (엔드포인트 + HTTP 메서드 조합)
    _METHOD_SPECIFIC_MAPPINGS = {
        # ============================================
        # PRIVATE API - ORDER (REST_PRIVATE_ORDER) - 8 RPS
        # ============================================
        ('/orders/cancel_and_new', 'POST'): UpbitRateLimitGroup.REST_PRIVATE_ORDER,  # 취소 후 재주문
        ('/orders', 'POST'): UpbitRateLimitGroup.REST_PRIVATE_ORDER,  # 주문 생성

        # ============================================
        # PRIVATE API - CANCEL ALL (REST_PRIVATE_CANCEL_ALL) - 0.5 RPS
        # ============================================
        ('/orders/open', 'DELETE'): UpbitRateLimitGroup.REST_PRIVATE_CANCEL_ALL,  # 주문 일괄 취소 접수
    }

    def _get_rate_limit_group(self, endpoint: str, method: str = 'GET') -> UpbitRateLimitGroup:
        """엔드포인트와 메서드를 기반으로 Rate Limit 그룹 결정"""
        # 🛡️ 방어적 타입 검증 (startswith 에러 방지)
        if not isinstance(endpoint, str):
            self.logger.error(f"❌ endpoint는 문자열이어야 함: {type(endpoint).__name__} = {endpoint}")
            raise TypeError(f"endpoint must be str, got {type(endpoint).__name__}: {endpoint}")

        if not isinstance(method, str):
            self.logger.error(f"❌ method는 문자열이어야 함: {type(method).__name__} = {method}")
            raise TypeError(f"method must be str, got {type(method).__name__}: {method}")

        # 메서드별 특별 매핑 우선 확인
        method_key = (endpoint, method.upper())
        if method_key in self._METHOD_SPECIFIC_MAPPINGS:
            return self._METHOD_SPECIFIC_MAPPINGS[method_key]

        # 일반 엔드포인트 매핑
        for pattern, group in self._ENDPOINT_MAPPINGS.items():
            if endpoint.startswith(pattern):
                return group

        # 기본값: Private Default
        return UpbitRateLimitGroup.REST_PRIVATE_DEFAULT

    async def acquire(self, endpoint: str, method: str = 'GET', **kwargs) -> None:
        """Rate Limit 토큰 획득 (메인 API)"""
        group = self._get_rate_limit_group(endpoint, method)
        config = self.group_configs[group]
        stats = self.group_stats[group]
        now = time.monotonic()

        # 통계 업데이트
        stats.total_requests += 1

        # 예방적 스로틀링 체크
        if config.enable_preventive_throttling:
            await self._apply_preventive_throttling(group, stats, now)

        # Lock-Free 토큰 획득
        await self._acquire_token_lock_free(group, endpoint, now)

        self.logger.debug(f"✅ 토큰 획득: {group.value}/{endpoint}")

    async def gate(self, group: UpbitRateLimitGroup, endpoint: str) -> None:
        """Rate Limiter 게이트 통과 (호환성 메소드)

        Args:
            group: Rate Limit 그룹
            endpoint: API 엔드포인트
        """
        await self.acquire(endpoint, method='GET')

    async def _apply_preventive_throttling(self, group: UpbitRateLimitGroup, stats: GroupStats, now: float):
        """예방적 스로틀링 적용 (개선된 시간 감쇠 로직)"""
        config = self.group_configs[group]

        # 최근 윈도우 내 429 에러 체크
        recent_errors = [
            t for t in stats.error_429_history
            if now - t <= config.preventive_window
        ]

        if recent_errors:
            # 가장 최근 에러로부터의 경과 시간
            most_recent_error = max(recent_errors)
            time_since_error = now - most_recent_error

            # 시간 경과에 따른 지연 감쇠 (기본: 30초 후 0으로 감소)
            decay_factor = max(0.0, 1.0 - (time_since_error / config.preventive_window))

            # 기본 지연 계산
            base_delay = min(config.max_preventive_delay, len(recent_errors) * 0.1)

            # 감쇠 적용된 최종 지연
            final_delay = base_delay * decay_factor

            if final_delay > 0.001:  # 1ms 이상일 때만 지연 적용
                await asyncio.sleep(final_delay)
                self.logger.debug(f"🛡️ 예방적 스로틀링: {group.value}, {final_delay:.3f}초 지연 (감쇠율: {decay_factor:.2f})")

    async def _acquire_token_lock_free(self, group: UpbitRateLimitGroup, endpoint: str, now: float):
        """Lock-Free 토큰 획득"""
        # 🚀 CRITICAL FIX: 첫 번째 사용 시 자동으로 백그라운드 태스크 시작
        if not self._background_tasks_started:
            await self._ensure_background_tasks_started()

        stats = self.group_stats[group]

        # 원자적 토큰 소모 시도
        can_proceed, next_available = await self._atomic_tat_manager.consume_token_atomic(group, now)

        if can_proceed:
            # 즉시 진행 가능
            return

        # 대기 필요
        waiter_id = str(uuid.uuid4())
        future = asyncio.Future()

        waiter_info = WaiterInfo(
            future=future,
            requested_at=now,
            ready_at=next_available,
            group=group,
            endpoint=endpoint,
            waiter_id=waiter_id,
            created_at=now
        )

        # 통계 업데이트
        stats.total_waits += 1
        stats.concurrent_waiters += 1
        stats.max_concurrent_waiters = max(stats.max_concurrent_waiters, stats.concurrent_waiters)

        # 대기자 등록
        self.waiters[group][waiter_id] = waiter_info

        # 🚀 CRITICAL FIX: 기존 WaiterInfo를 재사용하여 중복 생성 방지
        await self._timeout_manager.acquire_token_with_guaranteed_cleanup(group, endpoint, waiter_info)

        # 대기 완료 후 통계 업데이트
        wait_time = time.monotonic() - now
        stats.total_wait_time += wait_time
        stats.concurrent_waiters -= 1

    async def notify_429_error(self, endpoint: str, method: str = 'GET', **kwargs):
        """429 에러 알림 및 동적 조정"""
        group = self._get_rate_limit_group(endpoint, method)
        stats = self.group_stats[group]
        config = self.group_configs[group]
        now = time.monotonic()

        # 429 에러 기록
        stats.add_429_error(now)

        self.logger.error(f"🚨 429 에러 감지: {group.value}/{endpoint}")

        # 동적 조정이 활성화된 경우
        if config.enable_dynamic_adjustment:
            async with self._adjustment_lock:
                # 임계값 체크
                recent_window = config.error_429_window
                recent_errors = [
                    t for t in stats.error_429_history
                    if now - t <= recent_window
                ]

                if len(recent_errors) >= config.error_429_threshold:
                    await self._reduce_rate_limit(group, stats, now)

        # 콜백 호출
        if self.on_429_detected:
            await self.on_429_detected(group, endpoint, method, **kwargs)

    async def _reduce_rate_limit(self, group: UpbitRateLimitGroup, stats: GroupStats, timestamp: float):
        """Rate Limit 감소"""
        config = self.group_configs[group]

        old_ratio = stats.current_rate_ratio
        new_ratio = max(config.min_ratio, old_ratio * config.reduction_ratio)

        stats.current_rate_ratio = new_ratio
        stats.last_reduction_time = timestamp

        self.logger.warning(f"📉 Rate Limit 감소: {group.value}, {old_ratio:.1%} → {new_ratio:.1%}")

        # 콜백 호출
        if self.on_rate_reduced:
            await self.on_rate_reduced(group, old_ratio, new_ratio)

    async def start_background_tasks(self):
        """백그라운드 태스크 시작"""
        if self._recovery_task is None:
            self._recovery_task = asyncio.create_task(self._recovery_loop())

        # 🚀 CRITICAL FIX: Background Notifier Tasks 시작
        for group in UpbitRateLimitGroup:
            if group not in self._notifier_tasks:
                self._notifier_tasks[group] = asyncio.create_task(
                    self._task_manager._background_notifier_with_recovery(group)
                )
                self.logger.info(f"📢 Notifier Task 시작: {group.value}")

        # 자가치유 매니저 시작
        await self._task_manager.start_health_monitoring()

        # 타임아웃 매니저 시작
        await self._timeout_manager.start_timeout_management()

        # 🔍 Phase 4: 슬라이딩 윈도우 정리 태스크 시작
        if self.sliding_window_config['enabled'] and not hasattr(self, '_sliding_window_cleanup_task'):
            self._sliding_window_cleanup_task = asyncio.create_task(self._sliding_window_cleanup_task())
            self.logger.info("🧹 슬라이딩 윈도우 메모리 정리 태스크 시작")

        self.logger.info("🔄 백그라운드 태스크 시작 완료 (Notifier Tasks + 슬라이딩 윈도우 정리 포함)")

    async def _ensure_background_tasks_started(self):
        """백그라운드 태스크 자동 시작 (중복 방지)"""
        if not self._background_tasks_started:
            self._background_tasks_started = True
            await self.start_background_tasks()
            self.logger.info("🚀 백그라운드 태스크 자동 시작 완료")

    async def stop_background_tasks(self):
        """백그라운드 태스크 중지"""
        self._running = False

        # 🚀 CRITICAL FIX: Notifier Tasks 중지
        for group, task in list(self._notifier_tasks.items()):
            if task and not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                self.logger.info(f"📢 Notifier Task 중지: {group.value}")
        self._notifier_tasks.clear()

        # Recovery 태스크 중지
        if self._recovery_task and not self._recovery_task.done():
            self._recovery_task.cancel()

        # 자가치유 매니저 중지
        await self._task_manager.stop_health_monitoring()

        # 타임아웃 매니저 중지
        await self._timeout_manager.stop_timeout_management()

        # 원자적 TAT 매니저 정리
        await self._atomic_tat_manager.cleanup_locks()

        self.logger.info("🛑 백그라운드 태스크 중지 완료 (Notifier Tasks 포함)")

    async def _recovery_loop(self):
        """복구 루프"""
        while self._running:
            try:
                await self._check_recovery()
                await asyncio.sleep(30.0)  # 30초마다 체크
            except Exception as e:
                self.logger.error(f"❌ 복구 루프 오류: {e}")
                await asyncio.sleep(5.0)

    async def _check_recovery(self):
        """복구 체크"""
        for group, stats in self.group_stats.items():
            config = self.group_configs[group]

            if not config.enable_dynamic_adjustment:
                continue

            if stats.current_rate_ratio < 1.0 and stats.last_reduction_time:
                now = time.monotonic()
                time_since_reduction = now - stats.last_reduction_time

                if time_since_reduction >= config.recovery_delay:
                    await self._recover_rate_limit(group, stats, now)

    async def _recover_rate_limit(self, group: UpbitRateLimitGroup, stats: GroupStats, timestamp: float):
        """Rate Limit 복구"""
        config = self.group_configs[group]

        old_ratio = stats.current_rate_ratio
        new_ratio = min(1.0, old_ratio + config.recovery_step)

        stats.current_rate_ratio = new_ratio
        stats.last_recovery_time = timestamp

        self.logger.info(f"📈 Rate Limit 복구: {group.value}, {old_ratio:.1%} → {new_ratio:.1%}")

        # 콜백 호출
        if self.on_rate_recovered:
            await self.on_rate_recovered(group, old_ratio, new_ratio)

    def get_comprehensive_status(self) -> Dict[str, Any]:
        """종합 상태 조회"""
        groups_status = {}

        for group, config in self.group_configs.items():
            stats = self.group_stats[group]

            # 기본 설정 정보
            config_info = {
                'rps': config.rps,
                'current_ratio': stats.current_rate_ratio,
                'effective_rps': config.rps * stats.current_rate_ratio
            }

            # 🆕 이중 제한 및 버스트 정보 추가
            if config.enable_dual_limit and config.requests_per_minute:
                config_info['requests_per_minute'] = config.requests_per_minute
                config_info['requests_per_minute_burst'] = config.requests_per_minute_burst or 0
                config_info['dual_limit_enabled'] = True
                config_info['burst_capacity'] = config.burst_capacity
                config_info['tat_second'] = self.group_tats.get(group, 0.0)
                config_info['tat_minute'] = self.group_tats_minute.get(group, 0.0)
            else:
                config_info['dual_limit_enabled'] = False
                config_info['burst_capacity'] = config.burst_capacity
                config_info['tat'] = self.group_tats.get(group, 0.0)

            groups_status[group.value] = {
                'config': config_info,
                'stats': {
                    'total_requests': stats.total_requests,
                    'total_waits': stats.total_waits,
                    'error_429_count': stats.error_429_count,
                    'concurrent_waiters': stats.concurrent_waiters
                }
            }

        return {
            'groups': groups_status,
            'task_health': self._task_manager.get_health_status(),
            'timeout_status': self._timeout_manager.get_timeout_status(),
            'atomic_stats': self._atomic_tat_manager.get_atomic_stats(),
            'sliding_window_stats': self.get_sliding_window_stats()
        }

    # 🔍 슬라이딩 윈도우 관찰 메서드들 (Phase 1)

    def _log_sliding_window_request(self, group: UpbitRateLimitGroup, weight: int = 1) -> None:
        """슬라이딩 윈도우용 요청 로그 추가 (기존 시스템에 영향 없음)"""
        if not self.sliding_window_config['enabled']:
            return

        current_time = time.monotonic()
        log_entry = (current_time, weight)

        # 그룹별 로그에 추가
        self.sliding_window_logs[group].append(log_entry)

        # 메모리 제한 확인 및 정리
        max_size = self.sliding_window_config['max_log_size']
        if len(self.sliding_window_logs[group]) > max_size:
            self.sliding_window_logs[group] = self.sliding_window_logs[group][-max_size:]

    def _cleanup_sliding_window_logs(self, group: UpbitRateLimitGroup) -> None:
        """오래된 슬라이딩 윈도우 로그 정리"""
        if not self.sliding_window_config['enabled']:
            return

        current_time = time.monotonic()
        window_size = self.sliding_window_config['window_size']
        cutoff_time = current_time - window_size

        # 윈도우 밖의 오래된 로그 제거
        logs = self.sliding_window_logs[group]
        self.sliding_window_logs[group] = [
            (timestamp, weight) for timestamp, weight in logs
            if timestamp >= cutoff_time
        ]

    def _calculate_sliding_window_usage(self, group: UpbitRateLimitGroup) -> tuple[int, float]:
        """슬라이딩 윈도우 기반 현재 사용량 계산

        Returns:
            tuple[int, float]: (현재 윈도우 내 요청 수, 사용률 %)
        """
        if not self.sliding_window_config['enabled']:
            return 0, 0.0

        # 로그 정리
        self._cleanup_sliding_window_logs(group)

        # 현재 윈도우 내 요청 수 계산
        logs = self.sliding_window_logs[group]
        request_count = sum(weight for _, weight in logs)

        # 그룹별 한도 확인
        group_config = self.group_configs[group]
        max_requests = group_config.rps * self.sliding_window_config['window_size']

        usage_rate = (request_count / max_requests * 100) if max_requests > 0 else 0.0

        return request_count, usage_rate

    def _would_sliding_window_allow(self, group: UpbitRateLimitGroup, weight: int = 1) -> bool:
        """슬라이딩 윈도우 알고리즘이 요청을 허용할지 시뮬레이션

        Returns:
            bool: 허용 여부 (실제로는 허용하지 않고 시뮬레이션만)
        """
        if not self.sliding_window_config['enabled']:
            return True

        request_count, _ = self._calculate_sliding_window_usage(group)
        group_config = self.group_configs[group]
        max_requests = group_config.rps * self.sliding_window_config['window_size']

        # 새 요청을 추가했을 때 한도를 초과하는지 확인
        return (request_count + weight) <= max_requests

    def get_sliding_window_stats(self) -> Dict[str, Any]:
        """슬라이딩 윈도우 관찰 통계 반환"""
        if not self.sliding_window_config['enabled']:
            return {'enabled': False}

        stats = {
            'enabled': True,
            'config': self.sliding_window_config,
            'comparison_stats': self.algorithm_comparison_stats.copy(),
            'groups': {}
        }

        for group in UpbitRateLimitGroup:
            request_count, usage_rate = self._calculate_sliding_window_usage(group)
            stats['groups'][group.name] = {
                'current_requests': request_count,
                'usage_rate_percent': round(usage_rate, 2),
                'log_size': len(self.sliding_window_logs[group]),
                'window_size': self.sliding_window_config['window_size']
            }

        return stats

    def _update_algorithm_comparison_stats(self, gcra_allowed: bool, sw_allowed: bool) -> None:
        """알고리즘 비교 통계 업데이트"""
        stats = self.algorithm_comparison_stats
        stats['total_requests'] += 1

        if gcra_allowed:
            stats['gcra_allowed'] += 1
        if sw_allowed:
            stats['sw_allowed'] += 1

        if gcra_allowed and sw_allowed:
            stats['both_allowed'] += 1
        elif not gcra_allowed and not sw_allowed:
            stats['both_denied'] += 1
        elif gcra_allowed and not sw_allowed:
            stats['gcra_only_allowed'] += 1
        elif not gcra_allowed and sw_allowed:
            stats['sw_only_allowed'] += 1

    # 🆕 Phase 1: 타임스탬프 윈도우 관리 메서드들

    def _get_timestamp_window(self, group: UpbitRateLimitGroup) -> collections.deque:
        """그룹별 타임스탬프 윈도우 반환"""
        return self._timestamp_windows[group]

    def _add_timestamp_to_window(self, group: UpbitRateLimitGroup, timestamp: float) -> None:
        """타임스탬프 윈도우에 새 요청 시간 추가"""
        window = self._get_timestamp_window(group)
        window.append(timestamp)

        # 디버그 로깅 (상세 모드일 때만)
        if self.hybrid_config.get('detailed_logging', False):
            window_list = list(window)
            self.logger.debug(f"📊 타임스탬프 추가: {group.value} | 윈도우: {window_list}")

    def _has_empty_slots(self, group: UpbitRateLimitGroup) -> bool:
        """타임스탬프 윈도우에 빈슬롯이 있는지 확인"""
        window = self._get_timestamp_window(group)
        config = self.group_configs[group]
        window_capacity = int(config.burst_capacity)

        return len(window) < window_capacity

    def _cleanup_old_timestamps(self, group: UpbitRateLimitGroup, current_time: float) -> None:
        """감시 인터벌을 초과한 오래된 타임스탬프 제거"""
        window = self._get_timestamp_window(group)

        # 감시 인터벌 = 1/RPS (초 단위)
        monitoring_interval = 1.0  # 1초 (업비트 기본 감시 인터벌)
        cutoff_time = current_time - monitoring_interval

        # deque의 왼쪽부터(오래된 것부터) 제거
        original_size = len(window)
        while window and window[0] < cutoff_time:
            window.popleft()

        removed_count = original_size - len(window)
        if removed_count > 0 and self.hybrid_config.get('detailed_logging', False):
            self.logger.debug(f"🧹 타임스탬프 정리: {group.value} | 제거: {removed_count}개")

    def get_timestamp_window_stats(self) -> Dict[str, Any]:
        """타임스탬프 윈도우 통계 반환"""
        stats = {
            'hybrid_enabled': self.hybrid_config['enabled'],
            'groups': {}
        }

        for group in UpbitRateLimitGroup:
            window = self._get_timestamp_window(group)
            config = self.group_configs[group]
            window_capacity = int(config.burst_capacity)

            stats['groups'][group.name] = {
                'current_slots_used': len(window),
                'max_capacity': window_capacity,
                'empty_slots': window_capacity - len(window),
                'usage_percent': (len(window) / window_capacity) * 100 if window_capacity > 0 else 0,
                'timestamps': list(window) if self.hybrid_config.get('detailed_logging', False) else []
            }

        return stats

    # 🆕 Phase 2: 윈도우 지연 계산 로직 (문서의 시차 계산 알고리즘)

    def _calculate_window_delay(self, group: UpbitRateLimitGroup, current_time: float) -> float:
        """
        타임스탬프 윈도우 기반 지연 계산

        문서 알고리즘:
        1. 빈슬롯 있으면 → 0 지연 (즉시 허용)
        2. 윈도우 가득참 → 시차 계산하여 지연 시간 산출

        Returns:
            float: 지연 시간 (초). 0이면 즉시 허용
        """
        # 빈슬롯 체크 - 있으면 즉시 허용
        if self._has_empty_slots(group):
            if self.hybrid_config.get('detailed_logging', False):
                self.logger.debug(f"🟢 빈슬롯 허용: {group.value}")
            return 0.0

        # 윈도우가 가득 찬 경우 시차 계산
        window = self._get_timestamp_window(group)
        if not window:
            return 0.0

        return self._calculate_timestamp_gap_delay(window, current_time)

    def _calculate_timestamp_gap_delay(self, window: collections.deque, current_time: float) -> float:
        """
        타임스탬프 시차 기반 지연 계산 (문서 알고리즘 구현)

        알고리즘:
        1. 첫 슬롯에서 현재시간을 빼서 시차 계산
        2. 만약 첫슬롯 시차가 감시 인터벌보다 크면 계산 중지 (이미 지연 불필요)
        3. 2번 슬롯부터는 다음-이전 슬롯 간 시차 계산
        4. 시차 합을 감시 인터벌에서 뺀 값이 지연 시간

        Args:
            window: 타임스탬프 deque ([newest, ..., oldest] 순서)
            current_time: 현재 시간

        Returns:
            float: 지연 시간 (초)
        """
        if not window:
            return 0.0

        monitoring_interval = 1.0  # 1초 (업비트 감시 인터벌)
        window_list = list(window)  # [newest, ..., oldest]

        # 문서 명세: 첫 슬롯에서 현재시간을 빼서 시차 계산
        first_slot_time = window_list[0]  # 가장 최신 타임스탬프
        first_gap = current_time - first_slot_time

        # 첫슬롯 시차가 감시 인터벌보다 크면 계산 중지 (이미 충분한 시간 경과)
        if first_gap >= monitoring_interval:
            if self.hybrid_config.get('detailed_logging', False):
                self.logger.debug(f"⏰ 첫슬롯 시차 충분: {first_gap:.3f}s >= {monitoring_interval}s")
            return 0.0

        # 시차 합 계산
        total_gap = first_gap

        # 2번째 슬롯부터 슬롯간 시차 계산
        for i in range(1, len(window_list)):
            current_slot = window_list[i - 1]  # 더 최신
            previous_slot = window_list[i]     # 더 오래됨
            slot_gap = current_slot - previous_slot
            total_gap += slot_gap

            # 조기 종료: 시차합이 감시 인터벌을 초과하면 더 이상 계산 불필요
            if total_gap >= monitoring_interval:
                if self.hybrid_config.get('detailed_logging', False):
                    self.logger.debug(f"⏰ 시차합 충분: {total_gap:.3f}s >= {monitoring_interval}s")
                return 0.0

        # 최종 지연 계산: 감시 인터벌 - 시차 합
        delay = max(0.0, monitoring_interval - total_gap)

        if self.hybrid_config.get('detailed_logging', False):
            self.logger.debug(
                f"🕒 윈도우 지연 계산: 시차합={total_gap:.3f}s, "
                f"감시인터벌={monitoring_interval}s → 지연={delay:.3f}s"
            )

        return delay

    def _simulate_window_request(self, group: UpbitRateLimitGroup, current_time: float) -> tuple[bool, float]:
        """
        윈도우 알고리즘으로 요청 처리 시뮬레이션

        Returns:
            tuple: (즉시 허용 여부, 지연 시간)
        """
        # 오래된 타임스탬프 정리
        self._cleanup_old_timestamps(group, current_time)

        # 지연 계산
        delay = self._calculate_window_delay(group, current_time)
        immediate_allow = (delay == 0.0)

        return immediate_allow, delay

    # 🔍 Phase 3: 상세한 로깅 및 성능 지표 수집

    def log_algorithm_comparison(self, group: UpbitRateLimitGroup, gcra_result: bool, sw_result: bool,
                                 burst_remaining: int = 0, sw_usage: float = 0.0) -> None:
        """알고리즘 비교 결과 상세 로깅"""
        if not self.sliding_window_config['enabled']:
            return

        # 알고리즘 불일치 시 경고 로그
        if gcra_result != sw_result:
            self.logger.warning(
                f"🔍 알고리즘 불일치 감지: {group.value} | "
                f"GCRA: {'허용' if gcra_result else '거부'} | "
                f"SW: {'허용' if sw_result else '거부'} | "
                f"버스트잔여: {burst_remaining} | SW사용률: {sw_usage:.1f}%"
            )
        else:
            # 일치하는 경우는 디버그 레벨로
            self.logger.debug(
                f"🔍 알고리즘 일치: {group.value} | "
                f"결과: {'허용' if gcra_result else '거부'} | "
                f"버스트잔여: {burst_remaining} | SW사용률: {sw_usage:.1f}%"
            )

    def get_algorithm_agreement_rate(self) -> Dict[str, float]:
        """알고리즘 일치율 계산"""
        stats = self.algorithm_comparison_stats
        total = stats['total_requests']

        if total == 0:
            return {'agreement_rate': 100.0, 'total_samples': 0}

        agreement_count = stats['both_allowed'] + stats['both_denied']
        agreement_rate = (agreement_count / total) * 100

        return {
            'agreement_rate': round(agreement_rate, 2),
            'total_samples': total,
            'both_allowed': stats['both_allowed'],
            'both_denied': stats['both_denied'],
            'gcra_only_allowed': stats['gcra_only_allowed'],
            'sw_only_allowed': stats['sw_only_allowed'],
            'gcra_strictness': round((stats['gcra_only_allowed'] / total) * 100, 2) if total > 0 else 0.0,
            'sw_strictness': round((stats['sw_only_allowed'] / total) * 100, 2) if total > 0 else 0.0
        }

    def reset_algorithm_comparison_stats(self) -> None:
        """알고리즘 비교 통계 초기화"""
        self.algorithm_comparison_stats = {
            'total_requests': 0,
            'gcra_allowed': 0,
            'sw_allowed': 0,
            'both_allowed': 0,
            'both_denied': 0,
            'gcra_only_allowed': 0,
            'sw_only_allowed': 0,
            'last_cleanup': time.monotonic()
        }
        self.logger.info("🔍 알고리즘 비교 통계가 초기화되었습니다")

    async def log_periodic_comparison_summary(self) -> None:
        """주기적 비교 요약 로그 (백그라운드 태스크용)"""
        if not self.sliding_window_config['enabled']:
            return

        agreement_data = self.get_algorithm_agreement_rate()

        if agreement_data['total_samples'] > 0:
            self.logger.info(
                f"📊 알고리즘 비교 요약 (샘플: {agreement_data['total_samples']}개) | "
                f"일치율: {agreement_data['agreement_rate']}% | "
                f"GCRA더엄격: {agreement_data['gcra_strictness']}% | "
                f"SW더엄격: {agreement_data['sw_strictness']}%"
            )

    # 🔍 Phase 4: 메모리 관리 및 최적화

    async def _sliding_window_cleanup_task(self) -> None:
        """슬라이딩 윈도우 로그 정리 백그라운드 태스크"""
        while True:
            try:
                if self.sliding_window_config['enabled']:
                    current_time = time.monotonic()
                    cleanup_interval = self.sliding_window_config['cleanup_interval']

                    # 마지막 정리 시간 체크
                    if current_time - self.algorithm_comparison_stats['last_cleanup'] >= cleanup_interval:
                        await self._perform_memory_cleanup()
                        self.algorithm_comparison_stats['last_cleanup'] = current_time

                        # 주기적 요약 로그
                        await self.log_periodic_comparison_summary()

                # 다음 정리까지 대기
                await asyncio.sleep(self.sliding_window_config['cleanup_interval'])

            except asyncio.CancelledError:
                self.logger.info("🧹 슬라이딩 윈도우 정리 태스크가 중지되었습니다")
                break
            except Exception as e:
                self.logger.error(f"🧹 슬라이딩 윈도우 정리 태스크 오류: {e}")
                await asyncio.sleep(5.0)  # 오류 시 5초 대기

    async def _perform_memory_cleanup(self) -> None:
        """메모리 정리 수행"""
        if not self.sliding_window_config['enabled']:
            return

        total_cleaned = 0
        memory_usage_before = self._get_memory_usage_info()

        for group in UpbitRateLimitGroup:
            before_count = len(self.sliding_window_logs[group])
            self._cleanup_sliding_window_logs(group)
            after_count = len(self.sliding_window_logs[group])
            cleaned_count = before_count - after_count
            total_cleaned += cleaned_count

        memory_usage_after = self._get_memory_usage_info()

        self.logger.debug(
            f"🧹 메모리 정리 완료: {total_cleaned}개 로그 제거 | "
            f"메모리: {memory_usage_before['total_logs']} → {memory_usage_after['total_logs']}개"
        )

    def _get_memory_usage_info(self) -> Dict[str, int]:
        """메모리 사용량 정보 조회"""
        total_logs = sum(len(logs) for logs in self.sliding_window_logs.values())
        max_allowed = self.sliding_window_config['max_log_size'] * len(UpbitRateLimitGroup)

        group_usage = {}
        for group in UpbitRateLimitGroup:
            group_usage[group.name] = len(self.sliding_window_logs[group])

        return {
            'total_logs': total_logs,
            'max_allowed': max_allowed,
            'usage_percent': round((total_logs / max_allowed * 100), 2) if max_allowed > 0 else 0,
            'groups': group_usage
        }

    def get_memory_usage_status(self) -> Dict[str, Any]:
        """메모리 사용량 상태 조회 (외부 접근용)"""
        if not self.sliding_window_config['enabled']:
            return {'enabled': False}

        usage_info = self._get_memory_usage_info()
        config = self.sliding_window_config

        # 다음 정리까지 남은 시간 계산
        last_cleanup = self.algorithm_comparison_stats['last_cleanup']
        next_cleanup = max(0, config['cleanup_interval'] - (time.monotonic() - last_cleanup))

        return {
            'enabled': True,
            'usage': usage_info,
            'config': {
                'window_size': config['window_size'],
                'max_log_size': config['max_log_size'],
                'cleanup_interval': config['cleanup_interval']
            },
            'next_cleanup_in': next_cleanup
        }

    def force_cleanup_sliding_window_logs(self) -> Dict[str, int]:
        """강제 메모리 정리 (수동 호출용)"""
        if not self.sliding_window_config['enabled']:
            return {'status': 'disabled'}

        before_usage = self._get_memory_usage_info()

        # 모든 그룹의 로그 정리
        for group in UpbitRateLimitGroup:
            self._cleanup_sliding_window_logs(group)

        after_usage = self._get_memory_usage_info()

        self.logger.info(f"🧹 강제 메모리 정리: {before_usage['total_logs']} → {after_usage['total_logs']}개 로그")

        return {
            'before': before_usage['total_logs'],
            'after': after_usage['total_logs'],
            'cleaned': before_usage['total_logs'] - after_usage['total_logs']
        }


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
