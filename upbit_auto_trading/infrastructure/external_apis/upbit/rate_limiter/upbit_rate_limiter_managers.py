"""
업비트 Rate Limiter 보조 매니저들
- 자가치유, 타임아웃, 원자적 TAT 관리
- 검색 키워드: managers, healing, timeout, atomic
"""

import asyncio
import time
import random
import collections
from typing import Dict, Optional, Any

from .upbit_rate_limiter_types import UpbitRateLimitGroup, TaskHealth, WaiterState, WaiterInfo


class SelfHealingTaskManager:
    """
    자가치유 백그라운드 태스크 매니저

    백그라운드 태스크 장애 시 자동 감지/재시작 기능:
    - 태스크 생존 상태 모니터링
    - 연속 실패 감지 및 지수 백오프
    - 긴급 대기자 알림 메커니즘
    - 자동 복구 및 상태 추적
    """

    def __init__(self, limiter_instance, max_consecutive_errors: int = 10):
        self.limiter = limiter_instance
        self.max_consecutive_errors = max_consecutive_errors
        self.logger = None  # 나중에 설정됨

        # 태스크 건강 상태 추적
        self.task_health: Dict[UpbitRateLimitGroup, TaskHealth] = {}
        self.consecutive_errors: Dict[UpbitRateLimitGroup, int] = {}
        self.last_restart_time: Dict[UpbitRateLimitGroup, float] = {}

        # 헬스체크 태스크
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_check_interval = 5.0  # 5초마다 체크

    async def start_health_monitoring(self):
        """헬스체크 모니터링 시작"""
        if self._health_check_task is None:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            self.logger.info("🏥 태스크 헬스체크 모니터링 시작")

    async def stop_health_monitoring(self):
        """헬스체크 모니터링 중지"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await asyncio.wait_for(self._health_check_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            finally:
                self._health_check_task = None
                self.logger.info("🏥 태스크 헬스체크 모니터링 중지")

    async def _health_check_loop(self):
        """주기적 헬스체크 루프"""
        while self.limiter._running:
            try:
                await self._check_and_heal_tasks()
                await asyncio.sleep(self._health_check_interval)
            except Exception as e:
                self.logger.error(f"❌ 헬스체크 루프 오류: {e}")
                await asyncio.sleep(1.0)

    async def _check_and_heal_tasks(self):
        """태스크 헬스체크 및 자가치유"""
        for group, task in list(self.limiter._notifier_tasks.items()):
            current_health = self._assess_task_health(group, task)
            self.task_health[group] = current_health

            if current_health in [TaskHealth.FAILED, TaskHealth.DEGRADED]:
                await self._heal_failed_task(group, task)

    def _assess_task_health(self, group: UpbitRateLimitGroup, task: asyncio.Task) -> TaskHealth:
        """태스크 건강 상태 평가"""
        if task.done():
            if task.cancelled():
                return TaskHealth.FAILED
            elif task.exception():
                return TaskHealth.FAILED
            else:
                # 정상 완료는 있을 수 없음 (무한 루프여야 함)
                return TaskHealth.FAILED

        # 연속 에러 카운트 기반 평가
        error_count = self.consecutive_errors.get(group, 0)
        if error_count >= self.max_consecutive_errors // 2:
            return TaskHealth.DEGRADED

        return TaskHealth.HEALTHY

    async def _heal_failed_task(self, group: UpbitRateLimitGroup, failed_task: asyncio.Task):
        """실패한 태스크 치유"""
        now = time.monotonic()
        last_restart = self.last_restart_time.get(group, 0)

        # 너무 자주 재시작 방지 (최소 30초 간격)
        if now - last_restart < 30.0:
            return

        self.logger.error(f"🚨 태스크 실패 감지, 치유 시작: {group.value}")
        self.task_health[group] = TaskHealth.RESTARTING

        # 기존 태스크 정리
        await self._cleanup_failed_task(group, failed_task)

        # 긴급 대기자 알림
        await self._emergency_wake_all_waiters(group)

        # 새 태스크 생성
        new_task = asyncio.create_task(
            self._background_notifier_with_recovery(group)
        )
        self.limiter._notifier_tasks[group] = new_task

        # 재시작 시간 기록
        self.last_restart_time[group] = now
        self.consecutive_errors[group] = 0  # 에러 카운트 리셋

        self.logger.info(f"✅ 태스크 재시작 완료: {group.value}")

    async def _cleanup_failed_task(self, group: UpbitRateLimitGroup, task: asyncio.Task):
        """실패한 태스크 정리"""
        try:
            if not task.done():
                task.cancel()
        except Exception as e:
            self.logger.warning(f"⚠️ 태스크 취소 실패: {group.value}, {e}")

        # 실패 원인 로그
        if task.done():
            if task.exception():
                self.logger.error(f"💀 태스크 실패 원인: {group.value}, {task.exception()}")
            elif task.cancelled():
                self.logger.info(f"🚫 태스크 취소됨: {group.value}")

    async def _emergency_wake_all_waiters(self, group: UpbitRateLimitGroup):
        """긴급 상황 시 모든 대기자 깨우기"""
        waiters_to_wake = list(self.limiter.waiters[group].values())
        woken_count = 0

        for waiter_info in waiters_to_wake:
            if waiter_info.state == WaiterState.WAITING:
                waiter_info.state = WaiterState.READY
                if not waiter_info.future.done():
                    waiter_info.future.set_result(None)
                    woken_count += 1

        if woken_count > 0:
            self.logger.warning(f"🚨 긴급 대기자 알림: {group.value}, {woken_count}명 깨움")

    async def _background_notifier_with_recovery(self, group: UpbitRateLimitGroup):
        """복구 메커니즘 내장 백그라운드 알림기"""
        consecutive_errors = 0

        while self.limiter._running:
            try:
                await self._background_notifier_core(group)
                consecutive_errors = 0  # 성공 시 리셋
                self.consecutive_errors[group] = 0

            except Exception as e:
                consecutive_errors += 1
                self.consecutive_errors[group] = consecutive_errors

                self.logger.error(f"❌ 백그라운드 알림 오류: {group.value}, {e} (연속: {consecutive_errors}회)")

                if consecutive_errors >= self.max_consecutive_errors:
                    self.logger.critical(f"💀 최대 연속 오류 도달: {group.value}, 태스크 종료")
                    break

                # 지수 백오프
                backoff_delay = min(30.0, 0.1 * (2 ** consecutive_errors) + random.uniform(0, 0.1))
                await asyncio.sleep(backoff_delay)

    async def _background_notifier_core(self, group: UpbitRateLimitGroup):
        """백그라운드 알림기 핵심 로직"""
        if not self.limiter.waiters[group]:
            await asyncio.sleep(0.1)
            return

        now = time.monotonic()

        # 시간이 된 대기자 찾아 깨우기
        for waiter_id, waiter_info in list(self.limiter.waiters[group].items()):
            if waiter_info.state == WaiterState.WAITING and now >= waiter_info.ready_at:
                waiter_info.state = WaiterState.READY
                if not waiter_info.future.done():
                    waiter_info.future.set_result(None)
                del self.limiter.waiters[group][waiter_id]

        # 다음 확인 시점
        next_check = min(
            (info.ready_at for info in self.limiter.waiters[group].values()
             if info.state == WaiterState.WAITING),
            default=now + 0.1
        )

        sleep_time = max(0.001, next_check - now)
        await asyncio.sleep(sleep_time)

    def get_health_status(self) -> Dict[str, Any]:
        """태스크 건강 상태 조회"""
        return {
            'overall_health': all(
                health == TaskHealth.HEALTHY
                for health in self.task_health.values()
            ),
            'groups': {
                group.value: {
                    'health': health.value,
                    'consecutive_errors': self.consecutive_errors.get(group, 0),
                    'last_restart': self.last_restart_time.get(group)
                }
                for group, health in self.task_health.items()
            }
        }


class TimeoutAwareRateLimiter:
    """
    타임아웃 보장 Rate Limiter 유틸리티

    WaiterInfo 객체들의 무한 대기 방지 및 확실한 정리 보장:
    - Future 과 timeout 간의 race condition 해결
    - 모든 타임아웃 태스크 추적 및 자동 정리
    - 메모리 누수 방지 및 통계 처리
    """

    def __init__(self, limiter_instance, waiter_timeout: float = 30.0):
        self.limiter = limiter_instance
        self.waiter_timeout = waiter_timeout
        self.logger = None  # 나중에 설정됨

        # 타임아웃 태스크 추적
        self.active_timeout_tasks: Dict[str, asyncio.Task] = {}

        # 주기적 정리 태스크
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 60.0  # 1분마다 정리

        # 통계
        self.timeout_stats = {
            'total_timeouts': 0,
            'successful_acquisitions': 0,
            'cancelled_by_timeout': 0,
            'avg_wait_time': 0.0,
            'max_wait_time': 0.0
        }

    async def start_timeout_management(self):
        """타임아웃 관리 시작"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup_loop())
            self.logger.info("⏰ 타임아웃 관리 시작")

    async def stop_timeout_management(self):
        """타임아웃 관리 중지"""
        # 정리 태스크 중지
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await asyncio.wait_for(self._cleanup_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            finally:
                self._cleanup_task = None

        # 모든 활성 타임아웃 태스크 정리
        await self._cleanup_all_timeout_tasks()
        self.logger.info("⏰ 타임아웃 관리 중지")

    async def _periodic_cleanup_loop(self):
        """주기적 정리 루프"""
        while self.limiter._running:
            try:
                await self._cleanup_completed_timeout_tasks()
                await asyncio.sleep(self._cleanup_interval)
            except Exception as e:
                self.logger.error(f"❌ 타임아웃 정리 오류: {e}")
                await asyncio.sleep(5.0)

    async def acquire_token_with_guaranteed_cleanup(self,
                                                    group: UpbitRateLimitGroup,
                                                    endpoint: str,
                                                    waiter_info: WaiterInfo) -> None:
        """🚀 CRITICAL FIX: 기존 WaiterInfo 재사용으로 중복 생성 방지"""
        waiter_id = waiter_info.waiter_id
        future = waiter_info.future

        # 타임아웃 태스크 생성
        timeout_task = asyncio.create_task(
            self._timeout_waiter(waiter_id, waiter_info)
        )
        waiter_info.timeout_task = timeout_task
        self.active_timeout_tasks[waiter_id] = timeout_task

        # ✅ 대기자는 이미 등록되어 있음 (메인 rate limiter에서 처리)

        # Race condition 방지를 위한 보장된 정리
        pending_tasks = {timeout_task, future}

        try:
            # Future 또는 timeout 중 하나가 완료될 때까지 대기
            done, pending = await asyncio.wait(
                pending_tasks,
                return_when=asyncio.FIRST_COMPLETED
            )

            # 완료되지 않은 태스크들 취소
            for task in pending:
                if not task.done():
                    task.cancel()

        finally:
            # 확실한 정리 수행
            await self._guaranteed_cleanup(waiter_id, waiter_info, pending_tasks)

    async def _timeout_waiter(self, waiter_id: str, waiter_info: WaiterInfo) -> str:
        """대기자 타임아웃 처리"""
        try:
            await asyncio.sleep(self.waiter_timeout)

            # 타임아웃 발생
            if waiter_info.state == WaiterState.WAITING:
                waiter_info.state = WaiterState.CANCELLED

                # Future가 아직 완료되지 않았다면 타임아웃으로 완료
                if not waiter_info.future.done():
                    waiter_info.future.cancel()

                self.timeout_stats['cancelled_by_timeout'] += 1
                self.logger.warning(f"⏰ 대기자 타임아웃: {waiter_info.group.value}/{waiter_info.endpoint}")

        except asyncio.CancelledError:
            # 정상적인 취소 (토큰 획득 완료)
            pass

        return waiter_id

    async def _guaranteed_cleanup(self,
                                  waiter_id: str,
                                  waiter_info: WaiterInfo,
                                  pending_tasks: set):
        """보장된 정리 작업"""
        try:
            # 대기자 목록에서 제거
            if waiter_id in self.limiter.waiters[waiter_info.group]:
                del self.limiter.waiters[waiter_info.group][waiter_id]

            # 활성 타임아웃 태스크 목록에서 제거
            if waiter_id in self.active_timeout_tasks:
                del self.active_timeout_tasks[waiter_id]

            # 통계 업데이트
            request_time = time.monotonic()
            self._record_timeout_stats(waiter_info.group, request_time, waiter_info.created_at)

        except Exception as e:
            self.logger.error(f"❌ 대기자 정리 실패: {waiter_id}, {e}")

    async def _cleanup_completed_timeout_tasks(self):
        """완료된 타임아웃 태스크 정리"""
        completed_tasks = []

        for waiter_id, task in self.active_timeout_tasks.items():
            if task.done():
                completed_tasks.append(waiter_id)

        for waiter_id in completed_tasks:
            del self.active_timeout_tasks[waiter_id]

        if completed_tasks:
            self.logger.debug(f"🧹 완료된 타임아웃 태스크 정리: {len(completed_tasks)}개")

    async def _cleanup_all_timeout_tasks(self):
        """모든 타임아웃 태스크 정리"""
        tasks_to_cancel = list(self.active_timeout_tasks.values())

        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()

        # 모든 태스크가 완료될 때까지 대기
        if tasks_to_cancel:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks_to_cancel, return_exceptions=True),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("⚠️ 일부 타임아웃 태스크 강제 종료 실패")

        self.active_timeout_tasks.clear()

    def _record_timeout_stats(self, group: UpbitRateLimitGroup, request_time: float, create_time: float):
        """타임아웃 통계 기록"""
        wait_time = request_time - create_time

        # 통계 업데이트
        if self.timeout_stats['avg_wait_time'] == 0:
            self.timeout_stats['avg_wait_time'] = wait_time
        else:
            # 지수 이동 평균
            self.timeout_stats['avg_wait_time'] = (
                0.9 * self.timeout_stats['avg_wait_time'] + 0.1 * wait_time
            )

        self.timeout_stats['max_wait_time'] = max(
            self.timeout_stats['max_wait_time'],
            wait_time
        )

        if wait_time < self.waiter_timeout:
            self.timeout_stats['successful_acquisitions'] += 1
        else:
            self.timeout_stats['total_timeouts'] += 1

    def get_timeout_status(self) -> Dict[str, Any]:
        """타임아웃 상태 조회"""
        return {
            'active_timeout_tasks': len(self.active_timeout_tasks),
            'waiter_timeout_seconds': self.waiter_timeout,
            'cleanup_interval_seconds': self._cleanup_interval,
            'stats': self.timeout_stats.copy()
        }


class AtomicTATManager:
    """
    원자적 TAT(Theoretical Arrival Time) 관리자

    TAT 읽기/쓰기 간 race condition 해결:
    - asyncio.Lock 기반 완전 원자적 토큰 소모
    - rate_ratio 스냅샷을 통한 일관성 보장
    - 멀티쓰레드 환경에서 안전한 동시 업데이트
    """

    def __init__(self, limiter_instance):
        self.limiter = limiter_instance
        self.logger = limiter_instance.logger

        # 그룹별 TAT 락
        self._tat_locks: Dict[UpbitRateLimitGroup, asyncio.Lock] = {}

        # 원자적 업데이트 통계
        self.atomic_stats = {
            'total_atomic_operations': 0,
            'successful_acquisitions': 0,
            'rejected_acquisitions': 0,
            'lock_contentions': 0,
            'avg_lock_wait_time': 0.0,
            'max_lock_wait_time': 0.0,
            # 🆕 하이브리드 결정 통계
            'burst_decisions': 0,      # 버스트(타임스탬프 윈도우)가 결정한 횟수
            'gcra_decisions': 0,       # GCRA가 결정한 횟수
            'burst_allowed': 0,        # 버스트로 허용된 횟수
            'gcra_allowed': 0          # GCRA 기본속도로 허용된 횟수
        }

    def _get_or_create_lock(self, group: UpbitRateLimitGroup) -> asyncio.Lock:
        """그룹별 TAT 락 획득 또는 생성"""
        if group not in self._tat_locks:
            self._tat_locks[group] = asyncio.Lock()
        return self._tat_locks[group]

    async def consume_token_atomic(self, group: UpbitRateLimitGroup, now: float) -> tuple[bool, float]:
        """
        원자적 토큰 소모 시도

        Returns:
            tuple: (성공 여부, 다음 사용 가능 시간)
        """
        lock = self._get_or_create_lock(group)
        lock_start_time = time.monotonic()

        async with lock:
            lock_end_time = time.monotonic()
            lock_wait_time = lock_end_time - lock_start_time

            # 락 대기 통계 기록
            self._record_lock_wait_time(lock_wait_time)

            # 통계 업데이트
            self.atomic_stats['total_atomic_operations'] += 1

            if lock_wait_time > 0.001:  # 1ms 이상 대기했다면 경합 발생
                self.atomic_stats['lock_contentions'] += 1

            # 현재 설정 스냅샷 (일관성 보장)
            config = self.limiter.group_configs[group]
            stats = self.limiter.group_stats[group]
            current_rate_ratio = stats.current_rate_ratio

            # 🆕 이중 제한 지원 (RPS + RPM)
            if config.enable_dual_limit and config.rpm is not None:
                return await self._consume_dual_token_atomic(group, config, stats, now, current_rate_ratio)
            else:
                return await self._consume_single_token_atomic(group, config, stats, now, current_rate_ratio)

    def _check_burst_slots(self, group: UpbitRateLimitGroup, now: float) -> tuple[bool, float]:
        """
        타임스탬프 윈도우 기반 버스트 슬롯 체크

        개선된 설계:
        - 빈슬롯 여부와 관계없이 항상 윈도우 딜레이 계산
        - 빈슬롯 있으면 버스트 허용하지만 계산된 딜레이도 반환 (로깅용)
        - 로깅에서 GCRA vs 윈도우 딜레이 비교 분석 가능

        Returns:
            tuple: (버스트 허용 여부, 윈도우 계산 딜레이)
        """
        # 항상 윈도우 딜레이 계산 (빈슬롯 여부와 무관)
        window_delay = self.limiter._calculate_window_delay(group, now)

        # 빈슬롯 체크 (클린업 전 원본 상태로 판단)
        has_empty_slots = self.limiter._has_empty_slots(group)

        if has_empty_slots:
            # 빈슬롯 있음 → 버스트 허용 (하지만 계산된 딜레이도 반환)
            return True, window_delay
        else:
            # 윈도우 가득참 → 버스트 불허용, 시차 기반 딜레이 사용
            return False, window_delay

    def _check_basic_gcra(
        self, group: UpbitRateLimitGroup, config, now: float, rate_ratio: float
    ) -> tuple[bool, float, float]:
        """
        순수 표준 GCRA 체크 (버스트 로직 완전 제거)

        사용자 승인 설계:
        - 표준 GCRA는 기본 간격(RPS)만 계산
        - 버스트는 관여하지 않음 (타임스탬프 윈도우가 담당)

        Returns:
            tuple: (기본속도 허용 여부, 딜레이 시간, 새로운 TAT)
        """
        # 표준 GCRA 파라미터
        increment = 1.0 / (config.rps * rate_ratio)  # I = 1/RPS (표준 공식)
        current_tat = self.limiter.group_tats.get(group, now)

        if now >= current_tat:
            # 기본 속도 OK - 즉시 사용 가능
            new_tat = now + increment
            return True, 0.0, new_tat
        else:
            # 기본 속도 위반 - 대기 필요
            delay = current_tat - now
            future_tat = current_tat + increment  # 미래 TAT 예상
            return False, delay, future_tat

    async def _consume_single_token_atomic(
        self, group: UpbitRateLimitGroup, config, stats, now: float, current_rate_ratio: float
    ) -> tuple[bool, float]:
        """
        ✅ 올바른 하이브리드 GCRA+윈도우 알고리즘 (사용자 승인 설계)

        역할 분담:
        0) 버스트 허용량: 타임스탬프 윈도우 빈슬롯이 결정
        1) 표준 GCRA: 기본 간격에 대해서만 계산 (버스트 관여 안함)
        2) 딜레이: max(GCRA딜레이, 윈도우딜레이) - 보수적 선택
        3) 자연스러운 전환: 빈슬롯 없으면 GCRA 주도, 두 값 수렴
        """

        # 1단계: 버스트 슬롯 체크 (타임스탬프 윈도우 전담)
        burst_available, burst_delay = self._check_burst_slots(group, now)

        # 2단계: 기본 속도 체크 (순수 GCRA, 버스트 제외)
        rate_ok, rate_delay, new_tat = self._check_basic_gcra(group, config, now, current_rate_ratio)

        # 3단계: 버스트 우선 하이브리드 결정
        if burst_available:
            # 버스트 가능하면 무조건 즉시 허용 (GCRA 딜레이 무시)
            final_delay = 0.0
            can_proceed = True
        else:
            # 버스트 불가하면 기존 보수적 로직 적용
            final_delay = max(burst_delay, rate_delay)
            can_proceed = (final_delay == 0.0)

        # 🆕 개선된 하이브리드 결정 로깅 (항상 양쪽 딜레이 표시)
        decision_reason = "버스트허용" if burst_available else ("GCRA주도" if rate_delay >= burst_delay else "윈도우주도")
        self.logger.debug(
            f"🧠 하이브리드분석: {group.value} | "
            f"윈도우딜레이:{burst_delay:.3f}s | "
            f"GCRA딜레이:{rate_delay:.3f}s | "
            f"버스트슬롯:{burst_available} | "
            f"GCRA속도OK:{rate_ok} | "
            f"결정:{decision_reason} → 최종:{final_delay:.3f}s({can_proceed})"
        )

        if can_proceed:
            # ✅ 허용: GCRA TAT만 업데이트 (타임스탬프는 API 성공 후 커밋)
            self.limiter.group_tats[group] = new_tat

            # 🔍 디버그: 지연된 커밋 전 윈도우 상태 추적
            if self.limiter.hybrid_config.get('detailed_logging', False):
                window = self.limiter._get_timestamp_window(group)
                window_capacity = self.limiter._get_window_size(group)
                current_usage = len(window)
                self.logger.debug(
                    f"🕐 지연된 커밋 예정: {group.value} | "
                    f"현재 윈도우: {current_usage}/{window_capacity}슬롯 | "
                    f"커밋 후 예상: {current_usage + 1}/{window_capacity}슬롯 | "
                    f"타임스탬프: {now:.3f} (API 성공 시 추가 예정)"
                )

            # ⚠️ 타임스탬프 추가는 API 성공 후에 별도로 수행
            # self.limiter._add_timestamp_to_window(group, now)  # 지연된 커밋으로 이동

            # ⚠️ 클린업도 API 성공 후에 별도로 수행 (실패 시 롤백 위해 원본 상태 유지)
            # self.limiter._cleanup_old_timestamps(group, now)  # 지연된 커밋으로 이동

            self.atomic_stats['successful_acquisitions'] += 1

            # 결정 근거 로깅 및 통계 기록
            if burst_available:
                decisive_algo = "버스트"
                self.atomic_stats['burst_decisions'] += 1
                self.atomic_stats['burst_allowed'] += 1
            else:
                decisive_algo = "GCRA"
                self.atomic_stats['gcra_decisions'] += 1
                if can_proceed:
                    self.atomic_stats['gcra_allowed'] += 1

            self.logger.debug(f"✅ 허용: {group.value} (결정: {decisive_algo})")
            return True, new_tat
        else:
            # ❌ 거부: 대기 시간 반환
            # 거부 시에도 오래된 타임스탬프 정리 (일관성 유지) <-- 거부시 시차합 일관성 때문에 지우면 안됨
            # self.limiter._cleanup_old_timestamps(group, now)

            self.atomic_stats['rejected_acquisitions'] += 1

            # 결정 근거 로깅 및 통계 기록
            if not burst_available:
                decisive_algo = "GCRA"  # 버스트 불가 시에는 항상 GCRA 결정
                self.atomic_stats['gcra_decisions'] += 1
            else:
                # 이 케이스는 발생하지 않음 (버스트 가능하면 위에서 허용됨)
                decisive_algo = "버스트"
                self.atomic_stats['burst_decisions'] += 1

            self.logger.debug(f"❌ 거부: {group.value} 대기:{final_delay:.3f}s (결정: {decisive_algo})")
            return False, now + final_delay

    async def _consume_dual_token_atomic(
        self, group: UpbitRateLimitGroup, config, stats, now: float, current_rate_ratio: float
    ) -> tuple[bool, float]:
        """
        ✅ 이중 제한 하이브리드 GCRA+윈도우 알고리즘 (웹소켓 전용)
        웹소켓은 RPS+RPM 이중 제한을 사용하므로 각각을 하이브리드 방식으로 처리:
        1) RPS: 버스트(윈도우) + 기본속도(GCRA) 하이브리드
        2) RPM: 버스트(윈도우) + 기본속도(GCRA) 하이브리드
        3) 최종: max(RPS딜레이, RPM딜레이) - 보수적 선택
        """

        # 1단계: RPS 제한 하이브리드 체크
        rps_burst_ok, rps_burst_delay = self._check_burst_slots(group, now)
        rps_rate_ok, rps_rate_delay, rps_new_tat = self._check_basic_gcra(
            group, config, now, current_rate_ratio
        )
        rps_final_delay = max(rps_burst_delay, rps_rate_delay)

        # 2단계: RPM 제한 하이브리드 체크 (분당 제한용 별도 윈도우/TAT)
        # RPM 기본 설정 (변수명 스타일 통일)
        rpm_limit = config.rpm or 100  # 기본 100/분
        rpm_burst_capacity = config.rpm_burst_capacity or 0  # 버스트 용량 명시
        # 동적 RPM 모니터링 간격 계산: rpm_burst_capacity * 60 / rpm
        rpm_monitoring_interval = (rpm_burst_capacity * 60.0 / rpm_limit) if rpm_burst_capacity > 0 else 60.0

        # RPM용 가상 그룹 설정 (분당 윈도우 사용)
        rpm_window_key = f"{group.value}_rpm"
        if rpm_window_key not in self.limiter.timestamp_windows:
            # RPM용 분당 윈도우 초기화
            self.limiter.timestamp_windows[rpm_window_key] = collections.deque()

        # RPM 윈도우 정리 (동적 모니터링 간격 사용)
        rpm_window = self.limiter.timestamp_windows[rpm_window_key]
        while rpm_window and (now - rpm_window[0]) > rpm_monitoring_interval:
            rpm_window.popleft()

        # RPM 버스트 체크 (동적 버스트 용량 사용)
        effective_rpm_burst = rpm_burst_capacity if rpm_burst_capacity > 0 else rpm_limit
        rpm_burst_ok = len(rpm_window) < effective_rpm_burst
        rpm_burst_delay = 0.0 if rpm_burst_ok else (
            rpm_monitoring_interval - (now - rpm_window[0]) if rpm_window else 0.0
        )        # RPM GCRA 체크
        rpm_tat = self.limiter.group_tats_minute.get(group, now)
        rpm_increment = rpm_monitoring_interval / rpm_limit  # 60.0 / 100 = 0.6초
        if rpm_tat <= now:
            rpm_rate_delay, rpm_new_tat = 0.0, now + rpm_increment
        else:
            rpm_rate_delay, rpm_new_tat = rpm_tat - now, rpm_tat + rpm_increment

        rpm_final_delay = max(rpm_burst_delay, rpm_rate_delay)

        # 3단계: 하이브리드 보수적 결정
        total_delay = max(rps_final_delay, rpm_final_delay)
        can_proceed = (total_delay == 0.0)

        if can_proceed:
            # ✅ 즉시 허용 - TAT만 업데이트 (윈도우는 API 성공 후 커밋)

            # 🔍 디버그: 이중 제한 지연된 커밋 전 상태 추적
            if self.limiter.hybrid_config.get('detailed_logging', False):
                rps_window = self.limiter._get_timestamp_window(group)
                rps_capacity = self.limiter._get_window_size(group)
                rps_usage = len(rps_window)
                rpm_usage = len(rpm_window)
                rpm_capacity = effective_rpm_burst

                self.logger.debug(
                    f"🕐 이중제한 지연된 커밋 예정: {group.value} | "
                    f"RPS 윈도우: {rps_usage}/{rps_capacity}슬롯 → {rps_usage + 1}/{rps_capacity}슬롯 | "
                    f"RPM 윈도우: {rpm_usage}/{rpm_capacity}슬롯 → {rpm_usage + 1}/{rpm_capacity}슬롯 | "
                    f"타임스탬프: {now:.3f} (API 성공 시 양쪽 추가 예정)"
                )

            # ⚠️ 타임스탬프 추가는 API 성공 후에 별도로 수행
            # self.limiter._add_timestamp_to_window(group, now)  # 지연된 커밋으로 이동
            # rpm_window.append(now)  # RPM 윈도우도 지연된 커밋으로 이동
            self.limiter.group_tats[group] = rps_new_tat
            self.limiter.group_tats_minute[group] = rpm_new_tat

            self.atomic_stats['successful_acquisitions'] += 1
            self.logger.debug(f"웹소켓 이중제한 허용: {group.value}")
            return True, now
        else:
            # ❌ 대기 필요
            controlling_factor = "RPS" if rps_final_delay >= rpm_final_delay else "RPM"
            if abs(rps_final_delay - rpm_final_delay) < 0.001:
                controlling_factor = "RPS+RPM"

            self.atomic_stats['rejected_acquisitions'] += 1
            self.logger.debug(f"웹소켓 이중제한 대기: {group.value} -> {total_delay:.3f}초 ({controlling_factor})")
            return False, now + total_delay

    async def update_tat_atomic(self, group: UpbitRateLimitGroup, new_tat: float):
        """원자적 TAT 업데이트"""
        lock = self._get_or_create_lock(group)

        async with lock:
            old_tat = self.limiter.group_tats.get(group, 0.0)
            self.limiter.group_tats[group] = new_tat

            self.logger.debug(f"🔒 TAT 원자적 업데이트: {group.value}, {old_tat:.3f} → {new_tat:.3f}")

    async def get_tat_atomic(self, group: UpbitRateLimitGroup) -> float:
        """원자적 TAT 조회"""
        lock = self._get_or_create_lock(group)

        async with lock:
            return self.limiter.group_tats.get(group, time.monotonic())

    def _record_lock_wait_time(self, wait_time: float):
        """락 대기 시간 통계 기록"""
        # 평균 대기 시간 (지수 이동 평균)
        if self.atomic_stats['avg_lock_wait_time'] == 0:
            self.atomic_stats['avg_lock_wait_time'] = wait_time
        else:
            self.atomic_stats['avg_lock_wait_time'] = (
                0.9 * self.atomic_stats['avg_lock_wait_time'] + 0.1 * wait_time
            )

        # 최대 대기 시간
        self.atomic_stats['max_lock_wait_time'] = max(
            self.atomic_stats['max_lock_wait_time'],
            wait_time
        )

    def get_atomic_stats(self) -> Dict[str, Any]:
        """원자적 관리 통계 조회 (하이브리드 결정 통계 포함)"""
        total_decisions = self.atomic_stats['burst_decisions'] + self.atomic_stats['gcra_decisions']

        return {
            'total_operations': self.atomic_stats['total_atomic_operations'],
            'successful_rate': (
                self.atomic_stats['successful_acquisitions']
                / max(1, self.atomic_stats['total_atomic_operations'])
            ),
            'contention_rate': (
                self.atomic_stats['lock_contentions']
                / max(1, self.atomic_stats['total_atomic_operations'])
            ),
            'avg_lock_wait_ms': self.atomic_stats['avg_lock_wait_time'] * 1000,
            'max_lock_wait_ms': self.atomic_stats['max_lock_wait_time'] * 1000,
            'active_locks': len(self._tat_locks),
            # 🆕 하이브리드 알고리즘 통계
            'hybrid_decisions': {
                'total_decisions': total_decisions,
                'burst_decision_rate': (
                    self.atomic_stats['burst_decisions'] / max(1, total_decisions)
                ),
                'gcra_decision_rate': (
                    self.atomic_stats['gcra_decisions'] / max(1, total_decisions)
                ),
                'burst_success_rate': (
                    self.atomic_stats['burst_allowed'] / max(1, self.atomic_stats['burst_decisions'])
                ),
                'gcra_success_rate': (
                    self.atomic_stats['gcra_allowed'] / max(1, self.atomic_stats['gcra_decisions'])
                )
            }
        }

    async def commit_timestamp_window(self, group: UpbitRateLimitGroup, timestamp: float) -> None:
        """
        🚀 지연된 커밋: API 성공 후 타임스탬프 윈도우에 커밋 + 클린업

        Args:
            group: Rate Limit 그룹
            timestamp: 커밋할 타임스탬프
        """
        # 단일 제한의 경우
        config = self.limiter.group_configs[group]
        if not config.enable_dual_limit:
            # 1단계: 타임스탬프 윈도우에 커밋
            self.limiter._add_timestamp_to_window(group, timestamp)

            # 2단계: API 성공 후 오래된 타임스탬프 정리 (안전한 시점)
            self.limiter._cleanup_old_timestamps(group, timestamp)

            self.logger.debug(f"📊 타임스탬프 커밋+정리: {group.value} at {timestamp:.3f}")
        else:
            # 이중 제한의 경우 (웹소켓)
            # 1단계: RPS 윈도우에 커밋
            self.limiter._add_timestamp_to_window(group, timestamp)

            # 2단계: RPM 윈도우에도 커밋
            rpm_window_key = f"{group.value}_rpm"
            if rpm_window_key in self.limiter.timestamp_windows:
                rpm_window = self.limiter.timestamp_windows[rpm_window_key]
                rpm_window.append(timestamp)

            # 3단계: 양쪽 윈도우 모두 정리
            self.limiter._cleanup_old_timestamps(group, timestamp)
            # RPM 윈도우도 정리 (필요시)

            self.logger.debug(f"📊 이중제한 타임스탬프 커밋+정리: {group.value} at {timestamp:.3f}")

    async def cleanup_locks(self):
        """락 정리"""
        self._tat_locks.clear()
        self.logger.info("🔒 TAT 락들 정리 완료")
