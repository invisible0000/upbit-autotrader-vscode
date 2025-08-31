"""
Rate Limiter V2 정확도 검증 테스트 - 최소 오버헤드

측정 정확도 개선을 위한 단순화된 테스트
"""

import time
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_rate_limiter_v2 import (
    UpbitRateLimiterV2, UpbitApiCategory
)


def test_rate_limiter_accuracy():
    """Rate Limiter 정확도 직접 검증"""

    print("🎯 Rate Limiter V2 정확도 검증 테스트")
    print("=" * 60)

    limiter = UpbitRateLimiterV2()

    # 테스트 설정
    test_configs = [
        ("QUOTATION", "/quotation", "GET", 10.0, 5),
        ("EXCHANGE_DEFAULT", "/accounts", "GET", 30.0, 5),
        ("EXCHANGE_ORDER", "/orders", "POST", 8.0, 3),
        ("EXCHANGE_CANCEL_ALL", "/orders/cancel_all", "DELETE", 0.5, 2),
    ]

    for name, endpoint, method, rps, count in test_configs:
        print(f"\n🧪 {name} 테스트")
        print(f"설정: {rps} RPS → {1000/rps:.1f}ms 간격")

        times = []
        allowed_times = []

        for i in range(count):
            start = time.perf_counter()
            allowed, wait_time = limiter.check_limit(endpoint, method)

            if allowed:
                allowed_times.append(start)
                print(f"  요청 {i+1}: 허용 (시간: {start:.6f})")
            else:
                print(f"  요청 {i+1}: 차단, {wait_time:.3f}초 대기")
                if wait_time > 0:
                    time.sleep(wait_time)

        # 간격 계산
        if len(allowed_times) >= 2:
            intervals = []
            for j in range(1, len(allowed_times)):
                interval = (allowed_times[j] - allowed_times[j-1]) * 1000
                intervals.append(interval)
                print(f"    간격 {j}: {interval:.1f}ms")

            avg_interval = sum(intervals) / len(intervals)
            expected = 1000 / rps
            accuracy = max(0, 100 - abs(avg_interval - expected) / expected * 100)

            print(f"  📊 평균간격: {avg_interval:.1f}ms, 예상: {expected:.1f}ms")
            print(f"  🎯 정확도: {accuracy:.1f}%")
        else:
            print(f"  ⚠️ 허용된 요청 부족 ({len(allowed_times)}개)")


if __name__ == "__main__":
    test_rate_limiter_accuracy()
