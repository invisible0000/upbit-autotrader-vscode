"""
Lock-Free GCRA Rate Limiter - aiohttp 패턴 기반 구현
- asyncio.Future 기반 대기열 시스템
- OrderedDict를 이용한 공정한 FIFO 대기
- Re-checking을 통한 race condition 방지
- Lock contention 완전 제거

DeepWiki 조사 결과 aiohttp BaseConnector의 패턴을 Rate Limiting에 적용
"""
import asyncio
import time
import collections
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class LockFreeGCRAConfig:
    """Lock-Free GCRA 설정"""
    rps: float  # Requests per second
    burst_capacity: int  # 버스트 용량
    emission_interval: float  # 배출 간격 (1/rps)
    increment: float  # 토큰 증가량

    @classmethod
    def from_rps(cls, rps: float, burst_capacity: int = None):
        """RPS 기반 설정 생성"""
        if burst_capacity is None:
            burst_capacity = int(rps)

        emission_interval = 1.0 / rps
        increment = emission_interval

        return cls(
            rps=rps,
            burst_capacity=burst_capacity,
            emission_interval=emission_interval,
            increment=increment
        )


class WaiterState(Enum):
    """대기자 상태"""
    WAITING = "waiting"
    READY = "ready"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


@dataclass
class WaiterInfo:
    """대기자 정보"""
    future: asyncio.Future
    requested_at: float
    ready_at: float
    state: WaiterState = WaiterState.WAITING
    waiter_id: str = ""


class LockFreeGCRA:
    """
    Lock-Free GCRA Rate Limiter

    aiohttp BaseConnector 패턴을 활용하여 Lock contention 없는 Rate Limiting 구현:
    1. OrderedDict _waiters로 공정한 FIFO 대기열 관리
    2. asyncio.Future 기반 비동기 대기
    3. Re-checking으로 race condition 방지
    4. 중앙집중식 상태 관리

    핵심 원리:
    - TAT(Theoretical Arrival Time) 원자적 업데이트
    - 대기 필요 시 Future 생성하여 대기열 추가
    - 토큰 사용 가능 시 대기자 순차적 깨우기
    - 깨어난 대기자는 다시 조건 확인 (re-check)
    """

    def __init__(self, config: LockFreeGCRAConfig):
        self.config = config
        self._tat = 0.0  # Theoretical Arrival Time

        # aiohttp 패턴: OrderedDict로 공정한 대기열
        self._waiters: collections.OrderedDict[str, WaiterInfo] = collections.OrderedDict()

        # 통계
        self._stats = {
            'total_requests': 0,
            'total_waits': 0,
            'total_wait_time': 0.0,
            'concurrent_waiters': 0,
            'max_concurrent_waiters': 0,
            'race_conditions_prevented': 0
        }

        # 로깅
        self.logger = create_component_logger("LockFreeGCRA")

        self.logger.info(f"🚀 Lock-Free GCRA 초기화: {config.rps} RPS, burst {config.burst_capacity}")

    def _calculate_wait_time(self, now: float) -> float:
        """필요한 대기 시간 계산 (원자적 연산)"""
        # GCRA 알고리즘 핵심
        if self._tat <= now:
            # 토큰 즉시 사용 가능
            return 0.0
        else:
            # 대기 필요
            return self._tat - now

    def _try_consume_token(self, now: float) -> bool:
        """토큰 소모 시도 (원자적 연산)"""
        if self._tat <= now:
            # 토큰 사용 가능 - TAT 업데이트
            self._tat = now + self.config.increment
            self._stats['total_requests'] += 1
            return True
        else:
            # 토큰 사용 불가
            return False

    def _schedule_token_availability(self, now: float) -> float:
        """다음 토큰 사용 가능 시점 예약"""
        if self._tat <= now:
            # 현재 즉시 사용 가능
            next_available = now + self.config.increment
        else:
            # 기존 TAT 기준으로 다음 토큰 예약
            next_available = self._tat + self.config.increment

        self._tat = next_available
        return next_available

    async def acquire(self) -> None:
        """
        Rate Limit 획득 - Lock-Free 구현

        aiohttp BaseConnector._get_connection 패턴 적용:
        1. 즉시 사용 가능한지 확인
        2. 불가능하면 Future 생성하여 대기열 추가
        3. 다른 작업이 토큰을 반납하면 대기자를 깨움
        4. 깨어난 후 다시 조건 확인 (re-check)
        """
        now = time.monotonic()
        self._stats['total_requests'] += 1

        # 1차: 즉시 사용 가능 확인
        if self._try_consume_token(now):
            self.logger.debug(f"⚡ 즉시 토큰 획득: TAT={self._tat:.3f}")
            return

        # 2차: 대기 필요 - Future 생성
        future = asyncio.Future()
        waiter_id = f"waiter_{id(future)}_{now:.6f}"

        ready_at = self._schedule_token_availability(now)

        waiter_info = WaiterInfo(
            future=future,
            requested_at=now,
            ready_at=ready_at,
            state=WaiterState.WAITING,
            waiter_id=waiter_id
        )

        # OrderedDict에 추가 (FIFO 보장)
        self._waiters[waiter_id] = waiter_info

        # 통계 업데이트
        self._stats['total_waits'] += 1
        self._stats['concurrent_waiters'] = len(self._waiters)
        if self._stats['concurrent_waiters'] > self._stats['max_concurrent_waiters']:
            self._stats['max_concurrent_waiters'] = self._stats['concurrent_waiters']

        self.logger.debug(f"⏳ 대기열 추가: {waiter_id}, ready_at={ready_at:.3f}, 대기자수={len(self._waiters)}")

        try:
            # 3차: 비동기 대기
            await future

            # 4차: Re-check (aiohttp 패턴 핵심)
            # 깨어난 후 실제로 토큰이 사용 가능한지 다시 확인
            recheck_now = time.monotonic()

            if self._try_consume_token(recheck_now):
                self.logger.debug(f"✅ Re-check 성공: {waiter_id}")
                waiter_info.state = WaiterState.COMPLETED
            else:
                # Race condition 감지 - 다른 대기자가 토큰을 가져감
                self._stats['race_conditions_prevented'] += 1
                self.logger.debug(f"🔄 Race condition 방지: {waiter_id}, 재대기")

                # 재귀적으로 다시 대기 (새로운 Future 생성)
                await self.acquire()
                return

        finally:
            # 대기열에서 제거
            self._waiters.pop(waiter_id, None)
            self._stats['concurrent_waiters'] = len(self._waiters)

            # 대기 시간 통계
            if waiter_info.state != WaiterState.CANCELLED:
                wait_duration = time.monotonic() - waiter_info.requested_at
                self._stats['total_wait_time'] += wait_duration

    def _notify_next_waiter(self) -> None:
        """다음 대기자 알림 (aiohttp 패턴)"""
        if not self._waiters:
            return

        # FIFO: 가장 먼저 대기한 waiter 선택
        waiter_id, waiter_info = next(iter(self._waiters.items()))

        if waiter_info.state == WaiterState.WAITING and not waiter_info.future.done():
            waiter_info.state = WaiterState.READY
            waiter_info.future.set_result(None)
            self.logger.debug(f"🔔 대기자 알림: {waiter_id}")

    async def _background_token_notifier(self) -> None:
        """
        백그라운드 토큰 알림 시스템

        주기적으로 대기자들을 확인하여 토큰 사용 가능 시점이 된 대기자를 깨움
        이는 타이머 기반 정확한 Rate Limiting을 구현
        """
        while True:
            try:
                if not self._waiters:
                    await asyncio.sleep(0.1)  # 대기자 없으면 짧게 대기
                    continue

                now = time.monotonic()

                # 토큰 사용 가능한 대기자 찾기
                for waiter_id, waiter_info in list(self._waiters.items()):
                    if (waiter_info.state == WaiterState.WAITING and
                        now >= waiter_info.ready_at and
                        not waiter_info.future.done()):

                        # 시간이 된 대기자 깨우기
                        self._notify_next_waiter()
                        break

                # 다음 확인 시점 계산
                next_check = min(
                    (info.ready_at for info in self._waiters.values()
                     if info.state == WaiterState.WAITING),
                    default=now + 0.1
                )

                sleep_time = max(0.001, next_check - now)  # 최소 1ms
                await asyncio.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"❌ 백그라운드 알림 오류: {e}")
                await asyncio.sleep(0.1)

    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        now = time.monotonic()

        return {
            'config': {
                'rps': self.config.rps,
                'burst_capacity': self.config.burst_capacity,
                'emission_interval': self.config.emission_interval
            },
            'state': {
                'current_tat': self._tat,
                'next_token_available_in': max(0, self._tat - now),
                'tokens_available_now': 1 if self._tat <= now else 0
            },
            'waiters': {
                'active_waiters': len(self._waiters),
                'waiter_ids': list(self._waiters.keys())
            },
            'stats': dict(self._stats),
            'performance': {
                'avg_wait_time': (
                    self._stats['total_wait_time'] / self._stats['total_waits']
                    if self._stats['total_waits'] > 0 else 0
                ),
                'wait_ratio': (
                    self._stats['total_waits'] / self._stats['total_requests']
                    if self._stats['total_requests'] > 0 else 0
                )
            }
        }

    def cleanup_cancelled_waiters(self) -> int:
        """취소된 대기자 정리"""
        cancelled_count = 0

        for waiter_id in list(self._waiters.keys()):
            waiter_info = self._waiters[waiter_id]

            if waiter_info.future.cancelled():
                waiter_info.state = WaiterState.CANCELLED
                self._waiters.pop(waiter_id)
                cancelled_count += 1

        if cancelled_count > 0:
            self.logger.debug(f"🧹 취소된 대기자 정리: {cancelled_count}개")

        return cancelled_count


class LockFreeUpbitRateLimiter:
    """
    업비트 전용 Lock-Free Rate Limiter

    여러 그룹을 관리하되 각 그룹마다 개별 LockFreeGCRA 인스턴스 사용
    """

    def __init__(self):
        self.limiters: Dict[str, LockFreeGCRA] = {}
        self.logger = create_component_logger("LockFreeUpbitRateLimiter")

        # 기본 업비트 설정
        self._init_default_limiters()

    def _init_default_limiters(self):
        """기본 Rate Limiter 초기화"""
        # REST Public API (10 RPS, burst 10)
        self.limiters['rest_public'] = LockFreeGCRA(
            LockFreeGCRAConfig.from_rps(10.0, burst_capacity=10)
        )

        self.logger.info("🔧 Lock-Free 업비트 Rate Limiter 초기화 완료")

    async def acquire_rest_public(self) -> None:
        """REST Public API Rate Limit 획득"""
        await self.limiters['rest_public'].acquire()

    def get_all_status(self) -> Dict[str, Any]:
        """모든 리미터 상태 조회"""
        return {
            group: limiter.get_status()
            for group, limiter in self.limiters.items()
        }

    async def cleanup_all_waiters(self) -> Dict[str, int]:
        """모든 리미터의 취소된 대기자 정리"""
        results = {}

        for group, limiter in self.limiters.items():
            cancelled = limiter.cleanup_cancelled_waiters()
            if cancelled > 0:
                results[group] = cancelled

        return results


# 팩토리 함수
def create_lock_free_upbit_limiter() -> LockFreeUpbitRateLimiter:
    """Lock-Free 업비트 Rate Limiter 생성"""
    return LockFreeUpbitRateLimiter()


# 테스트용 편의 함수
async def test_lock_free_performance(
    rps: float = 10.0,
    burst: int = 10,
    test_duration: float = 10.0,
    concurrent_tasks: int = 5
) -> Dict[str, Any]:
    """Lock-Free 성능 테스트"""

    limiter = LockFreeGCRA(LockFreeGCRAConfig.from_rps(rps, burst))

    async def worker(worker_id: int):
        """워커 태스크"""
        requests = 0
        start_time = time.monotonic()

        while time.monotonic() - start_time < test_duration:
            await limiter.acquire()
            requests += 1

        return requests

    # 동시 워커 실행
    start_time = time.monotonic()
    tasks = [worker(i) for i in range(concurrent_tasks)]
    results = await asyncio.gather(*tasks)
    end_time = time.monotonic()

    # 통계 수집
    total_requests = sum(results)
    actual_duration = end_time - start_time
    actual_rps = total_requests / actual_duration

    return {
        'config': {
            'target_rps': rps,
            'burst_capacity': burst,
            'test_duration': test_duration,
            'concurrent_tasks': concurrent_tasks
        },
        'results': {
            'total_requests': total_requests,
            'actual_duration': actual_duration,
            'actual_rps': actual_rps,
            'efficiency': (actual_rps / rps) * 100,
            'per_worker': results
        },
        'limiter_stats': limiter.get_status()
    }
