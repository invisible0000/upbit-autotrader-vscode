"""
🚨 Rate Limiter Cold Start 보호 방안

사용자의 생명이 걸린 문제 해결을 위한 3가지 해결책 제시
"""

import time
import asyncio
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

@dataclass
class RateWindow:
    window_seconds: float
    max_requests: int
    requests_per_second: float

class ColdStartProtectedRateLimiter:
    """
    🛡️ Cold Start 보호가 적용된 Rate Limiter

    ████████████████████████████████████████████████████████████
    🚀 3가지 Cold Start 보호 전략
    ████████████████████████████████████████████████████████████

    1️⃣ CONSERVATIVE_WARMUP: 처음 N개 요청은 더 엄격한 제한
    2️⃣ MIN_INTERVAL_ENFORCEMENT: 최소 간격 강제 (기존 방식 개선)
    3️⃣ HYBRID_PROTECTION: 두 방식 결합으로 최대 안전성
    """

    def __init__(self, windows: List[RateWindow], protection_mode: str = "HYBRID"):
        self.windows = windows
        self.protection_mode = protection_mode

        # Cloudflare 기본 구조
        self.window_counters = {}
        for i, window in enumerate(windows):
            self.window_counters[i] = {
                'current_count': 0,
                'previous_count': 0,
                'current_window_start': time.time(),
                'window_seconds': window.window_seconds,
                'max_requests': window.max_requests,
                # 🛡️ Cold Start 보호 추가 필드
                'first_request_time': None,
                'warmup_requests': 0,
                'last_request_time': None
            }

        self._lock = asyncio.Lock()

    def check_limit_with_cold_start_protection(self, now: float) -> Tuple[bool, float]:
        """
        🛡️ Cold Start 보호가 적용된 제한 검사
        """
        max_wait_needed = 0.0

        for window_id, window in enumerate(self.windows):
            counter = self.window_counters[window_id]
            window_seconds = counter['window_seconds']
            max_requests = counter['max_requests']

            # 🛡️ STRATEGY 1: CONSERVATIVE_WARMUP
            if self.protection_mode in ["CONSERVATIVE_WARMUP", "HYBRID"]:
                if counter['first_request_time'] is None:
                    # 첫 번째 요청 - 즉시 기록하고 허용
                    counter['first_request_time'] = now
                    counter['warmup_requests'] = 1
                    counter['last_request_time'] = now
                    continue

                # 워밍업 기간 (첫 윈도우 동안)
                time_since_first = now - counter['first_request_time']
                if time_since_first < window_seconds:
                    # 워밍업 기간 동안 더 엄격한 제한 (50% 제한)
                    warmup_max = max(1, max_requests // 2)
                    if counter['warmup_requests'] >= warmup_max:
                        warmup_wait = (warmup_max / max_requests) * window_seconds
                        max_wait_needed = max(max_wait_needed, warmup_wait)
                        return False, max_wait_needed

            # 🛡️ STRATEGY 2: MIN_INTERVAL_ENFORCEMENT
            if self.protection_mode in ["MIN_INTERVAL_ENFORCEMENT", "HYBRID"]:
                if counter['last_request_time'] is not None:
                    min_interval = window_seconds / max_requests
                    time_since_last = now - counter['last_request_time']
                    if time_since_last < min_interval:
                        interval_wait = min_interval - time_since_last
                        max_wait_needed = max(max_wait_needed, interval_wait)
                        return False, max_wait_needed

            # 기본 Cloudflare 알고리즘 적용
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

        if max_wait_needed > 0:
            return False, max_wait_needed

        # 요청 허용: 모든 카운터 업데이트
        for window_id in range(len(self.windows)):
            counter = self.window_counters[window_id]
            counter['current_count'] += 1
            counter['last_request_time'] = now
            if counter['first_request_time'] is not None:
                time_since_first = now - counter['first_request_time']
                if time_since_first < counter['window_seconds']:
                    counter['warmup_requests'] += 1

        return True, 0.0


class RedisStyleSlidingWindow:
    """
    🏆 Redis Sorted Set 스타일 - Cold Start 자연 보호

    ClassDojo 방식 참조: 타임스탬프 기반으로 자연스러운 Cold Start 보호
    """

    def __init__(self, windows: List[RateWindow]):
        self.windows = windows
        # 각 윈도우별 타임스탬프 저장 (메모리 사용량 증가)
        self.request_timestamps = {i: [] for i in range(len(windows))}
        self._lock = asyncio.Lock()

    def check_limit_redis_style(self, now: float) -> Tuple[bool, float]:
        """
        🏆 Redis Sorted Set 방식 - 자연적 Cold Start 보호
        """
        max_wait_needed = 0.0

        for window_id, window in enumerate(self.windows):
            timestamps = self.request_timestamps[window_id]
            window_seconds = window.window_seconds
            max_requests = window.max_requests

            # 1️⃣ 윈도우 범위 밖 요청 제거
            cutoff_time = now - window_seconds
            self.request_timestamps[window_id] = [
                ts for ts in timestamps if ts > cutoff_time
            ]

            # 2️⃣ 현재 윈도우 내 요청 수 확인
            current_count = len(self.request_timestamps[window_id])

            # 3️⃣ 제한 검사
            if current_count >= max_requests:
                # 가장 오래된 요청이 윈도우를 벗어날 때까지 대기
                oldest_request = min(self.request_timestamps[window_id])
                wait_time = oldest_request + window_seconds - now
                max_wait_needed = max(max_wait_needed, wait_time)

        if max_wait_needed > 0:
            return False, max_wait_needed

        # 요청 허용: 현재 타임스탬프 추가
        for window_id in range(len(self.windows)):
            self.request_timestamps[window_id].append(now)

        return True, 0.0


class GCRAStyleRateLimiter:
    """
    🎯 GCRA/Leaky Bucket 스타일 - max_burst로 Cold Start 제어

    redis-cell 방식 참조: burst 허용량으로 초기 처리량 제어
    """

    def __init__(self, windows: List[RateWindow]):
        self.windows = windows
        # GCRA 상태: 다음 허용 시간
        self.next_allowed_time = {i: time.time() for i in range(len(windows))}
        self._lock = asyncio.Lock()

    def check_limit_gcra_style(self, now: float) -> Tuple[bool, float]:
        """
        🎯 GCRA 방식 - burst 제어로 Cold Start 보호
        """
        max_wait_needed = 0.0

        for window_id, window in enumerate(self.windows):
            requests_per_second = window.requests_per_second
            interval = 1.0 / requests_per_second if requests_per_second > 0 else float('inf')

            # burst 허용량 (초기 보호): 최대 3개 요청까지만 즉시 허용
            max_burst = min(3, window.max_requests // 2)

            next_allowed = self.next_allowed_time[window_id]

            if now >= next_allowed:
                # 요청 허용 가능
                # 다음 허용 시간 업데이트 (burst 고려)
                increment = interval
                if now - next_allowed > max_burst * interval:
                    # burst 윈도우 초과 시 정상 간격
                    self.next_allowed_time[window_id] = now + increment
                else:
                    # burst 윈도우 내에서는 누적
                    self.next_allowed_time[window_id] = max(next_allowed, now) + increment
            else:
                # 대기 필요
                wait_time = next_allowed - now
                max_wait_needed = max(max_wait_needed, wait_time)

        return max_wait_needed == 0, max_wait_needed


def demonstrate_cold_start_protection():
    """
    🧪 Cold Start 보호 방식 비교 테스트
    """
    print("🚨 Cold Start 보호 방식 비교")
    print("=" * 60)

    # 테스트 설정: QUOTATION 카테고리 (10 RPS)
    windows = [RateWindow(window_seconds=1.0, max_requests=10, requests_per_second=10.0)]

    # 3가지 방식 테스트
    limiters = {
        "HYBRID 보호": ColdStartProtectedRateLimiter(windows, "HYBRID"),
        "Redis 스타일": RedisStyleSlidingWindow(windows),
        "GCRA 스타일": GCRAStyleRateLimiter(windows)
    }

    results = {}

    for name, limiter in limiters.items():
        print(f"\n🧪 {name} 테스트:")

        now = time.time()
        allowed_count = 0
        blocked_count = 0

        # 15개 요청을 즉시 연속 시도 (Cold Start 상황)
        for i in range(15):
            if hasattr(limiter, 'check_limit_with_cold_start_protection'):
                allowed, wait_time = limiter.check_limit_with_cold_start_protection(now)
            elif hasattr(limiter, 'check_limit_redis_style'):
                allowed, wait_time = limiter.check_limit_redis_style(now)
            else:
                allowed, wait_time = limiter.check_limit_gcra_style(now)

            if allowed:
                allowed_count += 1
                print(f"   ✅ 요청 {i+1}: 허용")
            else:
                blocked_count += 1
                print(f"   ❌ 요청 {i+1}: 차단 (대기: {wait_time:.3f}초)")

            now += 0.01  # 10ms 간격

        actual_rps = allowed_count / 0.15  # 150ms 동안의 RPS
        results[name] = {
            'allowed': allowed_count,
            'blocked': blocked_count,
            'rps': actual_rps,
            'protection_level': 'HIGH' if actual_rps <= 12 else 'LOW'
        }

        print(f"   📊 결과: {allowed_count}개 허용, {blocked_count}개 차단")
        print(f"   📈 실제 RPS: {actual_rps:.1f} (제한: 10.0)")
        print(f"   🛡️ 보호 수준: {results[name]['protection_level']}")

    print("\n🏆 최종 권장사항:")
    print("=" * 60)

    best_protection = min(results.items(), key=lambda x: x[1]['rps'])
    print(f"✅ 권장: {best_protection[0]}")
    print(f"   - RPS: {best_protection[1]['rps']:.1f}")
    print(f"   - 초기 보호: {best_protection[1]['allowed']}개 허용")
    print(f"   - 429 에러 위험: {'낮음' if best_protection[1]['rps'] <= 12 else '높음'}")


if __name__ == "__main__":
    demonstrate_cold_start_protection()
