"""
순수 GCRA 이중 제한 vs 현재 구현 비교 분석
RPM Fixed Window Burst 제거 후 차이점 분석
"""

import time
from typing import Tuple, List
from dataclasses import dataclass


@dataclass
class GCRAResult:
    allowed: bool
    next_available_time: float
    wait_time: float
    reason: str


class PureGCRADualLimiter:
    """순수 GCRA 이중 제한 (Fixed Window Burst 제거)"""

    def __init__(self, rps: float, rpm: float, rps_burst: int = 0, rpm_burst: int = 0):
        # RPS 설정
        self.rps = rps
        self.rps_increment = 1.0 / rps
        self.rps_burst_allowance = rps_burst * self.rps_increment
        self.rps_tat = 0.0

        # RPM 설정
        self.rpm = rpm
        self.rpm_increment = 60.0 / rpm
        self.rpm_burst_allowance = rpm_burst * self.rpm_increment
        self.rpm_tat = 0.0

    def check_single_limit_with_burst(self, current_tat: float, increment: float,
                                     burst_allowance: float, now: float) -> Tuple[bool, float]:
        """GCRA 단일 제한 체크"""
        if current_tat <= now:
            # 충분히 기다렸음 - 즉시 사용 가능
            return True, now + increment
        else:
            # 버스트 체크
            potential_new_tat = current_tat + increment
            max_tat_with_burst = now + burst_allowance

            if potential_new_tat <= max_tat_with_burst:
                # 버스트 허용 범위 내
                return True, potential_new_tat
            else:
                # 버스트 초과
                return False, current_tat

    def acquire(self, now: float) -> GCRAResult:
        """토큰 획득 시도"""
        # RPS 체크
        rps_ok, rps_new_tat = self.check_single_limit_with_burst(
            self.rps_tat, self.rps_increment, self.rps_burst_allowance, now
        )

        # RPM 체크
        rpm_ok, rpm_new_tat = self.check_single_limit_with_burst(
            self.rpm_tat, self.rpm_increment, self.rpm_burst_allowance, now
        )

        if rps_ok and rpm_ok:
            # 둘 다 통과
            self.rps_tat = rps_new_tat
            self.rpm_tat = rpm_new_tat
            return GCRAResult(True, max(rps_new_tat, rpm_new_tat), 0.0, "BOTH_OK")

        # 실패한 경우 대기 시간 계산
        rps_wait = max(0, self.rps_tat - now)
        rpm_wait = max(0, self.rpm_tat - now)

        if not rps_ok and not rpm_ok:
            wait_time = max(rps_wait, rpm_wait)
            reason = f"BOTH_BLOCK (RPS:{rps_wait:.3f}s, RPM:{rpm_wait:.3f}s)"
        elif not rps_ok:
            wait_time = rps_wait
            reason = f"RPS_BLOCK ({rps_wait:.3f}s)"
        else:
            wait_time = rpm_wait
            reason = f"RPM_BLOCK ({rpm_wait:.3f}s)"

        return GCRAResult(False, now + wait_time, wait_time, reason)


class CurrentImplementationSimulator:
    """현재 구현 시뮬레이터 (Fixed Window Burst 포함)"""

    def __init__(self, rps: float, rpm: float, rps_burst: int = 0, rpm_burst_fixed: int = 0):
        # RPS GCRA
        self.rps = rps
        self.rps_increment = 1.0 / rps
        self.rps_burst_allowance = rps_burst * self.rps_increment
        self.rps_tat = 0.0

        # RPM GCRA (버스트 없음)
        self.rpm = rpm
        self.rpm_increment = 60.0 / rpm
        self.rpm_tat = 0.0

        # Fixed Window RPM Burst
        self.rpm_burst_fixed = rpm_burst_fixed
        self.rpm_burst_used = 0
        self.rpm_window_start = 0.0

    def acquire(self, now: float) -> GCRAResult:
        """토큰 획득 시도"""
        # Fixed Window RPM Burst 체크
        rpm_burst_bypass = False

        if self.rpm_burst_fixed > 0:
            # 윈도우 리셋 체크 (1분마다)
            if now - self.rpm_window_start >= 60.0:
                self.rpm_burst_used = 0
                self.rpm_window_start = now

            # 버스트 가능 여부
            if self.rpm_burst_used < self.rpm_burst_fixed:
                rpm_burst_bypass = True

        # RPS GCRA 체크
        rps_ok, rps_new_tat = self.check_single_limit_with_burst(
            self.rps_tat, self.rps_increment, self.rps_burst_allowance, now
        )

        # RPM 체크
        if rpm_burst_bypass:
            rpm_ok, rpm_new_tat = True, now + self.rpm_increment
        else:
            rpm_ok, rpm_new_tat = self.check_single_limit_with_burst(
                self.rpm_tat, self.rpm_increment, 0.0, now  # RPM 버스트 없음
            )

        if rps_ok and rpm_ok:
            # 성공
            self.rps_tat = rps_new_tat
            self.rpm_tat = rpm_new_tat

            if rpm_burst_bypass:
                self.rpm_burst_used += 1
                reason = f"SUCCESS_BURST ({self.rpm_burst_used}/{self.rpm_burst_fixed})"
            else:
                reason = "SUCCESS_NORMAL"

            return GCRAResult(True, max(rps_new_tat, rpm_new_tat), 0.0, reason)

        # 실패
        rps_wait = max(0, self.rps_tat - now)
        rpm_wait = max(0, self.rpm_tat - now)
        wait_time = max(rps_wait, rpm_wait)

        reason = f"BLOCKED (RPS:{rps_wait:.3f}s, RPM:{rpm_wait:.3f}s)"
        return GCRAResult(False, now + wait_time, wait_time, reason)

    def check_single_limit_with_burst(self, current_tat: float, increment: float,
                                     burst_allowance: float, now: float) -> Tuple[bool, float]:
        """GCRA 단일 제한 체크"""
        if current_tat <= now:
            return True, now + increment
        else:
            potential_new_tat = current_tat + increment
            max_tat_with_burst = now + burst_allowance

            if potential_new_tat <= max_tat_with_burst:
                return True, potential_new_tat
            else:
                return False, current_tat


def analyze_differences():
    """두 구현 방식의 차이점 분석"""

    print("🔍 순수 GCRA vs 현재 구현 (Fixed Window Burst) 비교 분석")
    print("=" * 80)

    # 설정: 5 RPS, 100 RPM, RPS 버스트 5개, RPM 버스트 10개
    pure_gcra = PureGCRADualLimiter(rps=5, rpm=100, rps_burst=5, rpm_burst=10)  # RPM 버스트도 GCRA
    current_impl = CurrentImplementationSimulator(rps=5, rpm=100, rps_burst=5, rpm_burst_fixed=10)  # RPM 버스트는 Fixed Window

    start_time = 0.0
    results_pure = []
    results_current = []

    print(f"설정: 5 RPS (0.2s), 100 RPM (0.6s), RPS 버스트: 5개, RPM 버스트: 10개")
    print()

    # 시나리오 1: 연속 요청 (버스트 테스트)
    print("📊 시나리오 1: 연속 요청 20개 (0.1초 간격)")
    print(f"{'Req#':>4} {'Time':>6} | {'Pure GCRA':<25} | {'Current Impl':<25}")
    print("-" * 80)

    for i in range(20):
        now = start_time + i * 0.1

        pure_result = pure_gcra.acquire(now)
        current_result = current_impl.acquire(now)

        results_pure.append(pure_result)
        results_current.append(current_result)

        print(f"{i+1:>4} {now:>6.1f} | "
              f"{'✅' if pure_result.allowed else '❌'} {pure_result.reason:<22} | "
              f"{'✅' if current_result.allowed else '❌'} {current_result.reason}")

    # 통계 분석
    pure_success = sum(1 for r in results_pure if r.allowed)
    current_success = sum(1 for r in results_current if r.allowed)

    print()
    print("📈 시나리오 1 결과:")
    print(f"  순수 GCRA:     {pure_success:2d}/20 요청 허용")
    print(f"  현재 구현:     {current_success:2d}/20 요청 허용")
    print(f"  차이:          {abs(pure_success - current_success):2d} 요청")

    # 시나리오 2: 1분 후 재테스트
    print(f"\n📊 시나리오 2: 61초 후 연속 요청 10개")
    minute_later = start_time + 61.0

    print(f"{'Req#':>4} {'Time':>7} | {'Pure GCRA':<25} | {'Current Impl':<25}")
    print("-" * 80)

    for i in range(10):
        now = minute_later + i * 0.1

        pure_result = pure_gcra.acquire(now)
        current_result = current_impl.acquire(now)

        print(f"{i+1:>4} {now:>7.1f} | "
              f"{'✅' if pure_result.allowed else '❌'} {pure_result.reason:<22} | "
              f"{'✅' if current_result.allowed else '❌'} {current_result.reason}")


def analyze_rate_differences():
    """속도 차이 분석"""
    print(f"\n🎯 속도 및 버스트 허용량 차이 분석")
    print("=" * 60)

    # 기본 간격
    rps_interval = 1.0 / 5    # 0.2초
    rpm_interval = 60.0 / 100 # 0.6초

    print(f"RPS 간격: {rps_interval:.3f}초")
    print(f"RPM 간격: {rpm_interval:.3f}초")
    print(f"속도 비교: RPM이 RPS보다 {rpm_interval/rps_interval:.1f}배 느림")

    # 버스트 허용량
    rps_burst_time = 5 * rps_interval  # 5 * 0.2 = 1.0초
    rpm_burst_time_gcra = 10 * rpm_interval  # 10 * 0.6 = 6.0초

    print(f"\nGCRA 버스트 허용 시간:")
    print(f"  RPS: {rps_burst_time:.1f}초 (5개 * 0.2초)")
    print(f"  RPM: {rpm_burst_time_gcra:.1f}초 (10개 * 0.6초)")

    # 핵심 발견
    print(f"\n🔍 핵심 발견:")
    print(f"  1. RPM 간격(0.6s)이 RPS 간격(0.2s)보다 3배 느림")
    print(f"  2. 단순 연속 요청에서는 RPS가 더 엄격한 제한")
    print(f"  3. RPM GCRA 버스트(6초)가 RPS GCRA 버스트(1초)보다 6배 관대")
    print(f"  4. 하지만 실제로는 RPS가 먼저 차단하므로 RPM 버스트가 큰 의미 없음")


if __name__ == "__main__":
    analyze_differences()
    analyze_rate_differences()
