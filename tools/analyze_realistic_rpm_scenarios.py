"""
실제 업비트 사용 패턴에서의 RPM vs RPS 제한 분석
장기간 사용 시나리오와 실제 의미 있는 차이점 분석
"""

import time
from dataclasses import dataclass
from typing import List


@dataclass
class RequestEvent:
    time: float
    allowed: bool
    reason: str
    rps_tat: float
    rpm_tat: float


class RealisticWebSocketRateLimiter:
    """실제 웹소켓 사용 패턴 시뮬레이터"""

    def __init__(self):
        # 5 RPS, 100 RPM 설정
        self.rps_increment = 1.0 / 5    # 0.2초
        self.rpm_increment = 60.0 / 100 # 0.6초

        # 버스트 설정
        self.rps_burst_allowance = 5 * self.rps_increment  # 1초
        self.rpm_burst_allowance = 10 * self.rpm_increment # 6초 (순수 GCRA인 경우)

        # TAT 상태
        self.rps_tat = 0.0
        self.rpm_tat = 0.0

        # Fixed Window RPM Burst (현재 구현 비교용)
        self.fixed_rpm_burst_used = 0
        self.fixed_rpm_window_start = 0.0

    def check_pure_gcra(self, now: float) -> RequestEvent:
        """순수 GCRA 방식 (RPM도 GCRA 버스트)"""
        # RPS 체크
        rps_ok = False
        if self.rps_tat <= now:
            rps_ok = True
            new_rps_tat = now + self.rps_increment
        else:
            potential_rps_tat = self.rps_tat + self.rps_increment
            if potential_rps_tat <= now + self.rps_burst_allowance:
                rps_ok = True
                new_rps_tat = potential_rps_tat
            else:
                new_rps_tat = self.rps_tat

        # RPM 체크
        rpm_ok = False
        if self.rpm_tat <= now:
            rpm_ok = True
            new_rpm_tat = now + self.rpm_increment
        else:
            potential_rpm_tat = self.rpm_tat + self.rpm_increment
            if potential_rpm_tat <= now + self.rpm_burst_allowance:
                rpm_ok = True
                new_rpm_tat = potential_rpm_tat
            else:
                new_rpm_tat = self.rpm_tat

        if rps_ok and rpm_ok:
            self.rps_tat = new_rps_tat
            self.rpm_tat = new_rpm_tat
            reason = "PURE_GCRA_OK"
            return RequestEvent(now, True, reason, self.rps_tat, self.rpm_tat)

        rps_wait = max(0, self.rps_tat - now)
        rpm_wait = max(0, self.rpm_tat - now)

        if not rps_ok and not rpm_ok:
            reason = f"BOTH_BLOCK(RPS:{rps_wait:.1f}s,RPM:{rpm_wait:.1f}s)"
        elif not rps_ok:
            reason = f"RPS_BLOCK({rps_wait:.1f}s)"
        else:
            reason = f"RPM_BLOCK({rpm_wait:.1f}s)"

        return RequestEvent(now, False, reason, self.rps_tat, self.rpm_tat)

    def check_current_impl(self, now: float) -> RequestEvent:
        """현재 구현 방식 (Fixed Window RPM Burst)"""
        # Fixed Window RPM Burst 체크
        rpm_burst_bypass = False

        # 윈도우 리셋 (1분마다)
        if now - self.fixed_rpm_window_start >= 60.0:
            self.fixed_rpm_burst_used = 0
            self.fixed_rpm_window_start = now

        # RPM 버스트 가능 여부
        if self.fixed_rpm_burst_used < 10:  # 10개 고정 버스트
            rpm_burst_bypass = True

        # RPS GCRA 체크
        rps_ok = False
        if self.rps_tat <= now:
            rps_ok = True
            new_rps_tat = now + self.rps_increment
        else:
            potential_rps_tat = self.rps_tat + self.rps_increment
            if potential_rps_tat <= now + self.rps_burst_allowance:
                rps_ok = True
                new_rps_tat = potential_rps_tat
            else:
                new_rps_tat = self.rps_tat

        # RPM 체크
        if rpm_burst_bypass:
            rpm_ok = True
            new_rpm_tat = now + self.rpm_increment
        else:
            # 일반 RPM GCRA (버스트 없음)
            if self.rpm_tat <= now:
                rpm_ok = True
                new_rpm_tat = now + self.rpm_increment
            else:
                rpm_ok = False
                new_rpm_tat = self.rpm_tat

        if rps_ok and rpm_ok:
            self.rps_tat = new_rps_tat
            self.rpm_tat = new_rpm_tat

            if rpm_burst_bypass:
                self.fixed_rpm_burst_used += 1
                reason = f"FIXED_BURST({self.fixed_rpm_burst_used}/10)"
            else:
                reason = "FIXED_NORMAL"

            return RequestEvent(now, True, reason, self.rps_tat, self.rpm_tat)

        # 실패
        rps_wait = max(0, self.rps_tat - now)
        rpm_wait = max(0, self.rpm_tat - now)

        reason = f"BLOCKED(RPS:{rps_wait:.1f}s,RPM:{rpm_wait:.1f}s)"
        return RequestEvent(now, False, reason, self.rps_tat, self.rpm_tat)


def test_long_term_usage():
    """장기간 사용 시나리오 테스트"""
    print("🕒 장기간 사용 시나리오: RPM 제한의 실제 의미 분석")
    print("=" * 80)

    limiter = RealisticWebSocketRateLimiter()

    # 시나리오: 5분 동안 0.5초마다 요청 (분당 120개 시도 = 100개 초과)
    print("패턴: 5분간 0.5초마다 요청 (분당 120개 시도, 100 RPM 초과)")
    print()

    duration = 300.0  # 5분
    interval = 0.5    # 0.5초마다
    requests = int(duration / interval)

    pure_success = 0
    fixed_success = 0

    # 매분별 통계
    minute_stats = {}

    for i in range(requests):
        now = i * interval
        minute = int(now // 60)

        if minute not in minute_stats:
            minute_stats[minute] = {'pure': 0, 'fixed': 0, 'attempts': 0}

        minute_stats[minute]['attempts'] += 1

        # 순수 GCRA 테스트
        limiter_pure = RealisticWebSocketRateLimiter()
        limiter_pure.rps_tat = limiter.rps_tat
        limiter_pure.rpm_tat = limiter.rpm_tat

        pure_result = limiter_pure.check_pure_gcra(now)
        if pure_result.allowed:
            pure_success += 1
            minute_stats[minute]['pure'] += 1
            limiter.rps_tat = limiter_pure.rps_tat
            limiter.rpm_tat = limiter_pure.rpm_tat

        # 현재 구현 테스트
        limiter_fixed = RealisticWebSocketRateLimiter()
        limiter_fixed.rps_tat = limiter.rps_tat
        limiter_fixed.rpm_tat = limiter.rpm_tat
        limiter_fixed.fixed_rpm_burst_used = limiter.fixed_rpm_burst_used
        limiter_fixed.fixed_rpm_window_start = limiter.fixed_rpm_window_start

        fixed_result = limiter_fixed.check_current_impl(now)
        if fixed_result.allowed:
            fixed_success += 1
            minute_stats[minute]['fixed'] += 1
            limiter.fixed_rpm_burst_used = limiter_fixed.fixed_rpm_burst_used
            limiter.fixed_rpm_window_start = limiter_fixed.fixed_rpm_window_start

    # 결과 출력
    print(f"📊 5분간 총 결과 ({requests}회 시도):")
    print(f"  순수 GCRA:  {pure_success:3d}회 성공 ({pure_success/requests*100:.1f}%)")
    print(f"  현재 구현:  {fixed_success:3d}회 성공 ({fixed_success/requests*100:.1f}%)")
    print(f"  차이:       {abs(pure_success - fixed_success):3d}회")

    print(f"\n📈 분별 상세 분석:")
    print(f"{'분':>2} | {'시도':>3} | {'순수GCRA':>8} | {'현재구현':>8} | {'차이':>4}")
    print("-" * 45)

    for minute in sorted(minute_stats.keys()):
        stats = minute_stats[minute]
        diff = stats['pure'] - stats['fixed']
        print(f"{minute:2d} | {stats['attempts']:3d} | "
              f"{stats['pure']:8d} | {stats['fixed']:8d} | {diff:+4d}")


def test_critical_rpm_scenario():
    """RPM 제한이 실제로 작동하는 시나리오"""
    print(f"\n🎯 RPM 제한이 실제 의미를 갖는 시나리오")
    print("=" * 60)

    print("패턴: 30분간 휴지 후 1분간 집중 사용")

    limiter = RealisticWebSocketRateLimiter()

    # 30분 휴지 (TAT 완전 초기화됨)
    rest_time = 30 * 60  # 30분
    limiter.rps_tat = 0.0
    limiter.rpm_tat = 0.0

    # 1분간 0.1초마다 요청 (600개 시도)
    burst_start = rest_time
    attempts = 0
    pure_success = 0
    fixed_success = 0

    print(f"\n📊 1분간 집중 사용 (0.1초마다, 600회 시도):")
    print(f"{'시간':>6} | {'순수GCRA':>12} | {'현재구현':>12}")
    print("-" * 40)

    for i in range(600):  # 1분간 0.1초마다
        now = burst_start + i * 0.1
        attempts += 1

        # 매 10초마다 상태 출력
        if i % 100 == 0:
            pure_limiter = RealisticWebSocketRateLimiter()
            pure_limiter.rps_tat = limiter.rps_tat
            pure_limiter.rpm_tat = limiter.rpm_tat

            pure_result = pure_limiter.check_pure_gcra(now)

            fixed_limiter = RealisticWebSocketRateLimiter()
            fixed_limiter.rps_tat = limiter.rps_tat
            fixed_limiter.rpm_tat = limiter.rpm_tat

            fixed_result = fixed_limiter.check_current_impl(now)

            print(f"{i*0.1:6.1f} | {'✅' if pure_result.allowed else '❌'} {pure_result.reason:<10} | "
                  f"{'✅' if fixed_result.allowed else '❌'} {fixed_result.reason}")

            if pure_result.allowed:
                limiter.rps_tat = pure_limiter.rps_tat
                limiter.rpm_tat = pure_limiter.rpm_tat
                pure_success += 1

            if fixed_result.allowed:
                fixed_success += 1

    expected_rps_limit = 5 * 60  # 5 RPS * 60초 = 300개
    expected_rpm_limit = 100     # 100 RPM

    print(f"\n📈 집중 사용 결과:")
    print(f"  이론적 RPS 한계: {expected_rps_limit:3d}개 (5 RPS × 60초)")
    print(f"  이론적 RPM 한계: {expected_rpm_limit:3d}개 (100 RPM)")
    print(f"  실제 순수 GCRA: {pure_success:3d}개")
    print(f"  실제 현재 구현: {fixed_success:3d}개")
    print(f"\n🔍 핵심 발견:")
    print(f"  - RPS 제한이 더 엄격하므로 최대 300개까지만 가능")
    print(f"  - RPM 제한(100개)은 RPS 제한보다 더 엄격함")
    print(f"  - 따라서 실제로는 RPM이 주요 제한 요소가 됨!")


if __name__ == "__main__":
    test_long_term_usage()
    test_critical_rpm_scenario()
