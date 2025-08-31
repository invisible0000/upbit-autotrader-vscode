"""
🚨 PRODUCTION-READY Cold Start 보호 구현

실제 운영 환경을 위한 더 강력한 보호 방식
"""

import time
import asyncio
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class RateWindow:
    window_seconds: float
    max_requests: int
    requests_per_second: float


class ProductionColdStartProtection:
    """
    🏭 PRODUCTION 급 Cold Start 보호

    ████████████████████████████████████████████████████████████
    🛡️ 3단계 보호 전략 (생명이 걸린 시스템용)
    ████████████████████████████████████████████████████████████

    1️⃣ COLD_START_GATE: 첫 N초 동안 극도로 제한적 허용
    2️⃣ WARMUP_PHASE: 점진적 제한 완화
    3️⃣ NORMAL_OPERATION: 일반 Cloudflare 알고리즘
    """

    def __init__(self, windows: List[RateWindow]):
        self.windows = windows
        self.startup_time = time.time()

        # 상태 관리
        self.window_counters = {}
        for i, window in enumerate(windows):
            self.window_counters[i] = {
                'current_count': 0,
                'previous_count': 0,
                'current_window_start': time.time(),
                'window_seconds': window.window_seconds,
                'max_requests': window.max_requests,
                'last_request_time': None,
                'total_requests': 0  # 전체 요청 카운트
            }

        self._lock = asyncio.Lock()

    def check_production_limit(self, now: float) -> Tuple[bool, float]:
        """
        🏭 PRODUCTION 등급 Cold Start 보호
        """
        time_since_startup = now - self.startup_time
        max_wait_needed = 0.0

        for window_id, window in enumerate(self.windows):
            counter = self.window_counters[window_id]
            window_seconds = counter['window_seconds']
            max_requests = counter['max_requests']
            total_requests = counter['total_requests']

            # 🚨 PHASE 1: COLD START GATE (첫 5초)
            if time_since_startup < 5.0:
                # 극도로 제한적: 전체 한도의 10%만 허용
                cold_start_limit = max(1, max_requests // 10)
                if total_requests >= cold_start_limit:
                    # 남은 cold start 시간만큼 대기
                    wait_time = 5.0 - time_since_startup
                    max_wait_needed = max(max_wait_needed, wait_time)
                    continue

            # 🔥 PHASE 2: WARMUP PHASE (5-30초)
            elif time_since_startup < 30.0:
                # 점진적 증가: 시간에 따라 한도 상승
                warmup_progress = (time_since_startup - 5.0) / 25.0  # 0~1
                warmup_limit = int(max_requests * (0.3 + 0.7 * warmup_progress))

                # 최소 간격 강제 (warmup 중에는 더 엄격)
                min_interval = (window_seconds / warmup_limit) * 1.5  # 50% 더 엄격
                if counter['last_request_time'] is not None:
                    time_since_last = now - counter['last_request_time']
                    if time_since_last < min_interval:
                        wait_time = min_interval - time_since_last
                        max_wait_needed = max(max_wait_needed, wait_time)
                        continue

            # ⚡ PHASE 3: NORMAL OPERATION (30초 이후)
            else:
                # 표준 Cloudflare 알고리즘 + 최소 간격
                elapsed_in_current = now - counter['current_window_start']

                if elapsed_in_current >= window_seconds:
                    full_windows_passed = int(elapsed_in_current // window_seconds)
                    if full_windows_passed == 1:
                        counter['previous_count'] = counter['current_count']
                    else:
                        counter['previous_count'] = 0
                    counter['current_count'] = 0
                    counter['current_window_start'] += full_windows_passed * window_seconds
                    elapsed_in_current = now - counter['current_window_start']

                # Cloudflare 선형 보간
                remaining_weight = (window_seconds - elapsed_in_current) / window_seconds
                estimated_rate = counter['previous_count'] * remaining_weight + counter['current_count']

                if estimated_rate + 1 > max_requests:
                    time_to_allow = (estimated_rate + 1 - max_requests) / max_requests * window_seconds
                    max_wait_needed = max(max_wait_needed, time_to_allow)
                    continue

                # 최소 간격 검사 (정상 운영 중에도)
                min_interval = window_seconds / max_requests
                if counter['last_request_time'] is not None:
                    time_since_last = now - counter['last_request_time']
                    if time_since_last < min_interval:
                        wait_time = min_interval - time_since_last
                        max_wait_needed = max(max_wait_needed, wait_time)
                        continue

        if max_wait_needed > 0:
            return False, max_wait_needed

        # 요청 허용: 모든 카운터 업데이트
        for window_id in range(len(self.windows)):
            counter = self.window_counters[window_id]
            counter['current_count'] += 1
            counter['last_request_time'] = now
            counter['total_requests'] += 1

        return True, 0.0

    def get_protection_status(self, now: float) -> dict:
        """현재 보호 상태 반환"""
        time_since_startup = now - self.startup_time

        if time_since_startup < 5.0:
            phase = "COLD_START_GATE"
            progress = time_since_startup / 5.0
        elif time_since_startup < 30.0:
            phase = "WARMUP_PHASE"
            progress = (time_since_startup - 5.0) / 25.0
        else:
            phase = "NORMAL_OPERATION"
            progress = 1.0

        return {
            'phase': phase,
            'progress': progress,
            'time_since_startup': time_since_startup,
            'protection_level': 'HIGH' if time_since_startup < 30 else 'NORMAL'
        }


def test_production_protection():
    """🧪 운영급 보호 테스트"""
    print("🏭 PRODUCTION Cold Start 보호 테스트")
    print("=" * 60)

    # QUOTATION 카테고리 (10 RPS)
    windows = [RateWindow(window_seconds=1.0, max_requests=10, requests_per_second=10.0)]
    limiter = ProductionColdStartProtection(windows)

    # 다양한 시점에서 테스트
    test_scenarios = [
        ("🚨 Cold Start (0초)", 0.0),
        ("🔥 Early Warmup (10초)", 10.0),
        ("⚡ Late Warmup (25초)", 25.0),
        ("✅ Normal Operation (35초)", 35.0)
    ]

    for scenario_name, time_offset in test_scenarios:
        print(f"\n{scenario_name}:")

        # 시간 시뮬레이션
        simulated_now = limiter.startup_time + time_offset

        # 상태 확인
        status = limiter.get_protection_status(simulated_now)
        print(f"   📊 Phase: {status['phase']}")
        print(f"   📈 Progress: {status['progress']:.1%}")
        print(f"   🛡️ Protection: {status['protection_level']}")

        # 연속 요청 테스트 (10개)
        allowed_count = 0
        blocked_count = 0

        for i in range(10):
            allowed, wait_time = limiter.check_production_limit(simulated_now)
            if allowed:
                allowed_count += 1
            else:
                blocked_count += 1
                if i == 0:  # 첫 번째 차단 시만 출력
                    print(f"   ❌ 첫 번째 차단: {wait_time:.3f}초 대기")

            simulated_now += 0.01  # 10ms 간격

        rps = allowed_count / 0.1  # 100ms 동안의 RPS
        print(f"   📊 결과: {allowed_count}개 허용, {blocked_count}개 차단")
        print(f"   📈 실제 RPS: {rps:.1f} (제한: 10.0)")

        safety_level = "매우 안전" if rps <= 5 else "안전" if rps <= 10 else "위험"
        print(f"   🔒 Safety Level: {safety_level}")


def demonstrate_vs_original():
    """🆚 기존 방식과 비교"""
    print("\n🆚 기존 Rate Limiter vs Production 보호")
    print("=" * 60)

    windows = [RateWindow(window_seconds=1.0, max_requests=10, requests_per_second=10.0)]

    # 기존 방식 (Cold Start 보호 없음)
    class OriginalLimiter:
        def __init__(self, windows):
            self.current_count = 0
            self.window_start = time.time()
            self.max_requests = windows[0].max_requests

        def check_limit(self, now):
            if now - self.window_start >= 1.0:
                self.current_count = 0
                self.window_start = now

            if self.current_count >= self.max_requests:
                return False, 0.1

            self.current_count += 1
            return True, 0.0

    original = OriginalLimiter(windows)
    production = ProductionColdStartProtection(windows)

    now = time.time()

    print("\n📊 초기 10개 요청 결과:")
    print(f"{'방식':<20} {'허용':<6} {'RPS':<8} {'안전성'}")
    print("-" * 40)

    # 기존 방식 테스트
    original_allowed = 0
    for i in range(10):
        allowed, _ = original.check_limit(now + i * 0.01)
        if allowed:
            original_allowed += 1
    original_rps = original_allowed / 0.1
    original_safety = "위험" if original_rps > 15 else "보통" if original_rps > 10 else "안전"

    # Production 방식 테스트
    prod_allowed = 0
    for i in range(10):
        allowed, _ = production.check_production_limit(now + i * 0.01)
        if allowed:
            prod_allowed += 1
    prod_rps = prod_allowed / 0.1
    prod_safety = "위험" if prod_rps > 15 else "보통" if prod_rps > 10 else "안전"

    print(f"{'기존 방식':<20} {original_allowed:<6} {original_rps:<8.1f} {original_safety}")
    print(f"{'Production 보호':<20} {prod_allowed:<6} {prod_rps:<8.1f} {prod_safety}")

    print(f"\n🎯 결론:")
    print(f"   - Production 보호가 {original_rps - prod_rps:.1f} RPS 더 안전")
    print(f"   - 429 에러 위험: {(prod_rps / original_rps * 100):.1f}%로 감소")


if __name__ == "__main__":
    test_production_protection()
    demonstrate_vs_original()
