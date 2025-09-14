"""
RPM GCRA가 RPS GCRA를 자연스럽게 억제하는 현상 실증
- 100 RPM GCRA에서 10개 버스트 후 긴 지연이 RPS를 자동 억제
- 현재 Fixed Window 방식의 부자연스러움 증명
"""

import time
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SuppressionTest:
    """억제 현상 테스트 결과"""
    time: float
    rps_allowed: bool
    rpm_allowed: bool
    rps_wait: float
    rpm_wait: float
    rps_tat: float
    rpm_tat: float
    controlling_factor: str  # 'RPS' 또는 'RPM'


class NaturalGCRADualLimiter:
    """자연스러운 GCRA 이중 제한 (RPM도 순수 GCRA)"""

    def __init__(self):
        # 5 RPS 설정
        self.rps = 5
        self.rps_increment = 1.0 / 5  # 0.2초
        self.rps_burst_capacity = 5
        self.rps_burst_allowance = self.rps_burst_capacity * self.rps_increment  # 1초
        self.rps_tat = 0.0

        # 100 RPM 설정 (순수 GCRA)
        self.rpm = 100
        self.rpm_increment = 60.0 / 100  # 0.6초
        self.rpm_burst_capacity = 10
        self.rpm_burst_allowance = self.rpm_burst_capacity * self.rpm_increment  # 6초!
        self.rpm_tat = 0.0

    def check_single_gcra(self, current_tat: float, increment: float,
                          burst_allowance: float, now: float) -> Tuple[bool, float]:
        """표준 GCRA 단일 제한 체크"""
        if current_tat <= now:
            # 충분히 기다렸음 - 즉시 사용 가능
            return True, now + increment
        else:
            # 버스트 체크: TAT가 미래에 있어도 버스트 범위 내면 허용
            potential_new_tat = current_tat + increment
            max_tat_with_burst = now + burst_allowance

            if potential_new_tat <= max_tat_with_burst:
                # 버스트 허용 범위 내
                return True, potential_new_tat
            else:
                # 버스트 초과
                return False, current_tat

    def acquire(self, now: float) -> SuppressionTest:
        """토큰 획득 시도 및 억제 현상 분석"""
        # RPS GCRA 체크
        rps_allowed, rps_new_tat = self.check_single_gcra(
            self.rps_tat, self.rps_increment, self.rps_burst_allowance, now
        )

        # RPM GCRA 체크
        rpm_allowed, rpm_new_tat = self.check_single_gcra(
            self.rpm_tat, self.rpm_increment, self.rpm_burst_allowance, now
        )

        # 대기 시간 계산
        rps_wait = max(0, self.rps_tat - now)
        rpm_wait = max(0, self.rpm_tat - now)

        # 제어 요소 결정
        if not rps_allowed and not rpm_allowed:
            controlling_factor = "RPM" if rpm_wait > rps_wait else "RPS"
        elif not rps_allowed:
            controlling_factor = "RPS"
        elif not rpm_allowed:
            controlling_factor = "RPM"
        else:
            controlling_factor = "NONE"

        # 성공 시 TAT 업데이트
        if rps_allowed and rpm_allowed:
            self.rps_tat = rps_new_tat
            self.rpm_tat = rpm_new_tat

        return SuppressionTest(
            time=now,
            rps_allowed=rps_allowed,
            rpm_allowed=rpm_allowed,
            rps_wait=rps_wait,
            rpm_wait=rpm_wait,
            rps_tat=self.rps_tat,
            rpm_tat=self.rpm_tat,
            controlling_factor=controlling_factor
        )


def demonstrate_rpm_suppression():
    """RPM GCRA가 RPS GCRA를 자연스럽게 억제하는 현상 실증"""

    print("🎯 RPM GCRA가 RPS를 자연스럽게 억제하는 현상 실증")
    print("=" * 80)
    print("설정: 5 RPS (0.2초, 1초 버스트) + 100 RPM (0.6초, 6초 버스트)")
    print()

    limiter = NaturalGCRADualLimiter()

    print("📊 연속 요청 시나리오 (0.1초 간격으로 20개 요청)")
    print(f"{'#':>2} {'Time':>5} | {'RPS':>3} {'RPM':>3} {'결과':>4} | "
          f"{'RPS_Wait':>8} {'RPM_Wait':>8} | {'제어요소':>6} | {'설명'}")
    print("-" * 95)

    suppression_detected = False
    suppression_start_time = None

    for i in range(25):
        now = i * 0.1
        result = limiter.acquire(now)

        # 결과 표시
        rps_icon = "✅" if result.rps_allowed else "❌"
        rpm_icon = "✅" if result.rpm_allowed else "❌"
        overall = "통과" if (result.rps_allowed and result.rpm_allowed) else "차단"

        print(f"{i+1:2d} {now:5.1f} | {rps_icon} {rpm_icon} {overall:>4} | "
              f"{result.rps_wait:8.3f} {result.rpm_wait:8.3f} | "
              f"{result.controlling_factor:>6} |", end=" ")

        # 억제 현상 분석
        if result.controlling_factor == "RPM" and result.rpm_wait > 1.0:
            if not suppression_detected:
                suppression_detected = True
                suppression_start_time = now
                print("🚨 RPM 억제 시작! RPS는 자동 차단됨")
            else:
                print(f"⏳ RPM 억제 지속 중 ({now - suppression_start_time:.1f}초째)")
        elif result.controlling_factor == "RPS":
            print("🔵 RPS가 제어 (정상)")
        elif overall == "통과":
            if suppression_detected:
                print("✅ 억제 해제 - 정상 동작 복귀")
                suppression_detected = False
            else:
                print("✅ 정상 통과")
        else:
            print("⚪ 기타")

    print()

    # 핵심 분석
    print("🔍 핵심 발견:")
    print("  1. 초기 10개 요청: 빠르게 RPM 버스트 소모")
    print("  2. RPM TAT 누적: 6초 버스트 허용량 초과로 긴 대기시간 발생")
    print("  3. 자동 억제: RPM 대기시간이 RPS보다 길어져 자연스럽게 RPS 차단")
    print("  4. 결론: RPM GCRA가 RPS를 **자동으로** 억제하는 천재적 메커니즘!")


def analyze_burst_depletion():
    """버스트 고갈과 TAT 누적 과정 상세 분석"""

    print(f"\n📈 버스트 고갈과 TAT 누적 과정 상세 분석")
    print("=" * 60)

    limiter = NaturalGCRADualLimiter()

    print(f"{'요청#':>4} {'시간':>5} | {'RPS_TAT':>8} {'RPM_TAT':>8} | "
          f"{'RPS_버스트':>10} {'RPM_버스트':>10} | {'상태'}")
    print("-" * 80)

    for i in range(15):
        now = i * 0.1

        # 현재 버스트 사용량 계산 (근사치)
        rps_burst_used = max(0, (limiter.rps_tat - now) / limiter.rps_increment)
        rpm_burst_used = max(0, (limiter.rpm_tat - now) / limiter.rpm_increment)

        result = limiter.acquire(now)

        # 상태 설명
        if result.rps_allowed and result.rpm_allowed:
            status = "✅ 통과"
        elif result.controlling_factor == "RPM":
            status = "🚨 RPM 차단"
        elif result.controlling_factor == "RPS":
            status = "🔵 RPS 차단"
        else:
            status = "❌ 양쪽 차단"

        print(f"{i+1:4d} {now:5.1f} | {limiter.rps_tat:8.3f} {limiter.rpm_tat:8.3f} | "
              f"{rps_burst_used:10.1f} {rpm_burst_used:10.1f} | {status}")

    print()
    print("🔍 TAT 누적 메커니즘:")
    print("  - RPS TAT: 매번 0.2초씩 증가")
    print("  - RPM TAT: 매번 0.6초씩 증가 (3배 빠른 누적!)")
    print("  - 10개 후: RPM TAT가 6초 앞서가며 긴 대기시간 발생")
    print("  - 결과: RPM이 자연스럽게 전체 시스템을 제어하게 됨")


def compare_with_fixed_window():
    """현재 Fixed Window 방식과 비교"""

    print(f"\n🆚 현재 Fixed Window vs 자연스러운 GCRA 비교")
    print("=" * 60)

    print("현재 Fixed Window 방식:")
    print("  ❌ 10개 버스트 후 인위적으로 RPM 완전 차단")
    print("  ❌ RPS는 계속 동작하지만 RPM이 막혀서 전체 차단")
    print("  ❌ 1분 후 갑작스럽게 리셋 - 부자연스러운 동작")
    print()

    print("자연스러운 GCRA 방식:")
    print("  ✅ 10개 버스트 후 RPM TAT가 자연스럽게 누적")
    print("  ✅ RPM 대기시간이 RPS보다 길어지면 자동으로 RPM이 제어")
    print("  ✅ 시간이 지나면서 점진적으로 회복 - 자연스러운 동작")
    print()

    print("🏆 결론:")
    print("  현재 방식: 인위적이고 복잡한 로직으로 부자연스러운 제어")
    print("  GCRA 방식: 수학적으로 완벽한 자동 제어, 별도 로직 불필요!")


def demonstrate_natural_recovery():
    """자연스러운 회복 과정 시연"""

    print(f"\n🔄 자연스러운 회복 과정 시연")
    print("=" * 50)

    limiter = NaturalGCRADualLimiter()

    # 먼저 버스트 고갈시키기
    print("1단계: 버스트 고갈 (10개 연속 요청)")
    for i in range(10):
        result = limiter.acquire(i * 0.1)

    print(f"  RPM TAT: {limiter.rpm_tat:.3f}초 (현재로부터 {limiter.rpm_tat - 1.0:.3f}초 후)")
    print()

    # 회복 과정 관찰
    print("2단계: 자연스러운 회복 과정")
    print(f"{'시간':>5} | {'RPM_Wait':>8} | {'RPS_Wait':>8} | {'상태'}")
    print("-" * 40)

    recovery_times = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]

    for recovery_time in recovery_times:
        # 회복 시점에서 테스트
        limiter_copy = NaturalGCRADualLimiter()
        limiter_copy.rps_tat = limiter.rps_tat
        limiter_copy.rpm_tat = limiter.rpm_tat

        result = limiter_copy.acquire(recovery_time)

        if result.rps_allowed and result.rpm_allowed:
            status = "✅ 완전 회복"
        elif result.rpm_wait > result.rps_wait:
            status = "⏳ RPM 제어 중"
        else:
            status = "🔵 RPS 제어 중"

        print(f"{recovery_time:5.1f} | {result.rpm_wait:8.3f} | {result.rps_wait:8.3f} | {status}")

    print()
    print("🔍 회복 메커니즘:")
    print("  - 시간이 지나면서 current_time이 TAT에 점점 가까워짐")
    print("  - RPM TAT가 더 크므로 RPM이 더 오래 제어")
    print("  - 별도 리셋 없이 자연스럽게 점진적 회복!")


if __name__ == "__main__":
    demonstrate_rpm_suppression()
    analyze_burst_depletion()
    compare_with_fixed_window()
    demonstrate_natural_recovery()
