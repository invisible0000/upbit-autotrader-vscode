"""
업비트 Rate Limiter 보조 매니저들
- 자가치유, 타임아웃, 원자적 TAT 관리
- 검색 키워드: managers, healing, timeout, atomic
"""

import asyncio
import time
import random
from typing import Dict, Any, Optional

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
            'max_lock_wait_time': 0.0
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
            if config.enable_dual_limit and config.requests_per_minute is not None:
                return await self._consume_dual_token_atomic(group, config, stats, now, current_rate_ratio)
            else:
                return await self._consume_single_token_atomic(group, config, stats, now, current_rate_ratio)

    async def _consume_single_token_atomic(
        self, group: UpbitRateLimitGroup, config, stats, now: float, current_rate_ratio: float
    ) -> tuple[bool, float]:
        """🆕 단일 제한 (RPS만) GCRA 로직 + 버스트 지원"""
        # TAT 계산
        current_tat = self.limiter.group_tats.get(group, now)

        # 동적 조정된 emission_interval 계산
        base_interval = config.emission_interval
        adjusted_interval = base_interval / current_rate_ratio

        # 🆕 GCRA 버스트 허용량 계산
        burst_allowance = config.burst_capacity * adjusted_interval

        if current_tat <= now:
            # ✅ 충분히 기다렸음 - 즉시 사용 가능
            new_tat = now + adjusted_interval
            self.limiter.group_tats[group] = new_tat

            self.atomic_stats['successful_acquisitions'] += 1
            return True, new_tat
        else:
            # 🚀 버스트 체크 - TAT가 미래에 있어도 버스트 범위 내면 허용
            potential_new_tat = current_tat + adjusted_interval
            max_tat_with_burst = now + burst_allowance

            if potential_new_tat <= max_tat_with_burst:
                # ✅ 버스트 허용 범위 내 - 사용 가능
                self.limiter.group_tats[group] = potential_new_tat

                self.atomic_stats['successful_acquisitions'] += 1
                self.atomic_stats['burst_used'] = self.atomic_stats.get('burst_used', 0) + 1
                return True, potential_new_tat
            else:
                # ❌ 버스트 초과 - 대기 필요
                self.atomic_stats['rejected_acquisitions'] += 1
                return False, current_tat

    async def _consume_dual_token_atomic(
        self, group: UpbitRateLimitGroup, config, stats, now: float, current_rate_ratio: float
    ) -> tuple[bool, float]:
        """🆕 이중 제한 (RPS + RPM) GCRA 로직 + 독립 버스트 지원"""
        # 초단위 TAT 계산
        short_tat = self.limiter.group_tats.get(group, now)
        short_increment = config.emission_interval / current_rate_ratio  # 동적 조정된 RPS

        # 분단위 TAT 계산
        long_tat = self.limiter.group_tats_minute.get(group, now)
        long_increment = 60.0 / config.requests_per_minute  # 분당 제한은 고정

        # 🆕 버스트 허용량 계산
        short_burst_allowance = config.burst_capacity * short_increment  # RPS 버스트 (예: 5 * 0.2s = 1초)

        # 🔥 RPM 버스트 로직 완전 개선
        long_burst_allowance = 0.0
        rpm_burst_bypass = False  # RPM 제한 완전 우회 플래그

        if config.requests_per_minute_burst:
            # RPM 버스트 윈도우 체크 (1분마다 리셋)
            rpm_burst_used = self.limiter.group_rpm_burst_used.get(group, 0)
            rpm_window_start = self.limiter.group_rpm_burst_window_start.get(group, 0.0)

            # 윈도우 리셋 체크 (1분 경과)
            if now - rpm_window_start >= 60.0:
                self.limiter.group_rpm_burst_used[group] = 0
                self.limiter.group_rpm_burst_window_start[group] = now
                rpm_burst_used = 0

            # RPM 버스트 가능 여부 체크
            if rpm_burst_used < config.requests_per_minute_burst:
                rpm_burst_bypass = True  # RPM 제한 완전 무시

        # RPS 체크 (항상 적용)
        short_result = self._check_single_limit_with_burst(short_tat, short_increment, short_burst_allowance, now)

        # RPM 체크 (버스트 우회 시 무조건 통과)
        if rpm_burst_bypass:
            long_result = (True, now)  # RPM 제한 우회
        else:
            long_result = self._check_single_limit_with_burst(long_tat, long_increment, long_burst_allowance, now)

        # 둘 다 통과해야 성공
        if short_result[0] and long_result[0]:
            # ✅ 모든 제한 통과 - TAT 업데이트
            new_short_tat = short_result[1]

            # RPM TAT 업데이트 (버스트 우회 시에는 실제 RPM TAT 계산)
            if rpm_burst_bypass:
                # RPM 버스트 사용됨 - 카운터 증가, RPM TAT는 실제 계산
                self.limiter.group_rpm_burst_used[group] += 1
                new_long_tat = now + long_increment  # 실제 RPM 간격으로 TAT 설정
            else:
                new_long_tat = long_result[1]

            self.limiter.group_tats[group] = new_short_tat
            self.limiter.group_tats_minute[group] = new_long_tat

            self.atomic_stats['successful_acquisitions'] += 1

            # 🆕 개선된 로그: 버스트 상태 포함
            rps_delay = max(0, new_short_tat - now)
            rpm_delay = max(0, new_long_tat - now)

            burst_info = ""
            if rpm_burst_bypass:
                rpm_used = self.limiter.group_rpm_burst_used[group]
                rpm_total = config.requests_per_minute_burst or 0
                burst_info = f", RPM 버스트: {rpm_used}/{rpm_total}"

            self.logger.debug(f"🔀 이중 TAT 업데이트: {group.value}, "
                              f"RPS 다음: +{rps_delay:.3f}초, "
                              f"RPM 다음: +{rpm_delay:.3f}초{burst_info}")
            return True, max(new_short_tat, new_long_tat)
        else:
            # ❌ 제한 위반 - 더 긴 대기시간 반환
            short_wait = max(0, short_tat - now)
            long_wait = max(0, long_tat - now)
            next_available = now + max(short_wait, long_wait)

            self.atomic_stats['rejected_acquisitions'] += 1
            self.logger.debug(f"⏳ 이중 제한 대기: {group.value}, "
                              f"RPS 대기: {short_wait:.3f}초, RPM 대기: {long_wait:.3f}초")
            return False, next_available

    def _check_single_limit_with_burst(
        self, current_tat: float, increment: float, burst_allowance: float, now: float
    ) -> tuple[bool, float]:
        """🆕 단일 제한에 대한 GCRA + 버스트 체크

        Returns:
            tuple: (사용 가능 여부, 새 TAT)
        """
        if current_tat <= now:
            # ✅ 충분히 기다렸음 - 즉시 사용 가능
            return True, now + increment
        else:
            # 🚀 버스트 체크
            potential_new_tat = current_tat + increment
            max_tat_with_burst = now + burst_allowance

            if potential_new_tat <= max_tat_with_burst:
                # ✅ 버스트 허용 범위 내
                return True, potential_new_tat
            else:
                # ❌ 버스트 초과
                return False, current_tat

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
        """원자적 관리 통계 조회"""
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
            'active_locks': len(self._tat_locks)
        }

    async def cleanup_locks(self):
        """락 정리"""
        self._tat_locks.clear()
        self.logger.info("🔒 TAT 락들 정리 완료")
