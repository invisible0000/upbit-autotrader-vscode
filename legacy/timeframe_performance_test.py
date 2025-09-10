"""
🔬 TimeUtils get_timeframe_seconds 성능 비교 테스트

현재 구현 (timedelta 기반) vs 단순 매핑 방법 성능 비교
"""

import time
from typing import Dict
from datetime import timedelta


class TimeUtilsCurrentImplementation:
    """현재 구현: timedelta 기반"""

    _TIMEFRAME_MAP: Dict[str, timedelta] = {
        "1s": timedelta(seconds=1),
        "1m": timedelta(minutes=1),
        "3m": timedelta(minutes=3),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "60m": timedelta(minutes=60),
        "1h": timedelta(minutes=60),
        "240m": timedelta(minutes=240),
        "4h": timedelta(minutes=240),
        "1d": timedelta(days=1),
        "1w": timedelta(weeks=1),
        "1M": timedelta(days=30),
        "1y": timedelta(days=365),
    }

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        """현재 구현: timedelta → total_seconds()"""
        if timeframe not in TimeUtilsCurrentImplementation._TIMEFRAME_MAP:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")
        dt = TimeUtilsCurrentImplementation._TIMEFRAME_MAP[timeframe]
        return int(dt.total_seconds())


class TimeUtilsDirectMapping:
    """대안 구현: 직접 초 단위 매핑"""

    _TIMEFRAME_SECONDS: Dict[str, int] = {
        "1s": 1,
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "60m": 3600,
        "1h": 3600,
        "240m": 14400,
        "4h": 14400,
        "1d": 86400,
        "1w": 604800,
        "1M": 2592000,  # 30일 기준
        "1y": 31536000,  # 365일 기준
    }

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        """대안 구현: 직접 초 값 반환"""
        if timeframe not in TimeUtilsDirectMapping._TIMEFRAME_SECONDS:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")
        return TimeUtilsDirectMapping._TIMEFRAME_SECONDS[timeframe]


def run_performance_test():
    """성능 비교 테스트 실행"""

    # 테스트 타임프레임들 (자주 사용되는 것들)
    timeframes = ["1m", "5m", "15m", "1h", "1d"]
    iterations = 100000  # 10만 번 호출 테스트

    print("🔬 get_timeframe_seconds 성능 비교 테스트")
    print(f"⚡ 반복 횟수: {iterations:,}회")
    print(f"📊 테스트 타임프레임: {timeframes}")
    print()

    # === 현재 구현 (timedelta 기반) 테스트 ===
    print("1️⃣ 현재 구현 (timedelta 기반) 테스트...")
    start_time = time.perf_counter()

    for _ in range(iterations):
        for tf in timeframes:
            _ = TimeUtilsCurrentImplementation.get_timeframe_seconds(tf)

    current_time = time.perf_counter() - start_time

    # === 대안 구현 (직접 매핑) 테스트 ===
    print("2️⃣ 대안 구현 (직접 매핑) 테스트...")
    start_time = time.perf_counter()

    for _ in range(iterations):
        for tf in timeframes:
            _ = TimeUtilsDirectMapping.get_timeframe_seconds(tf)

    direct_time = time.perf_counter() - start_time

    # === 결과 출력 ===
    print()
    print("📊 성능 비교 결과:")
    print(f"   🔹 현재 구현 (timedelta): {current_time:.4f}초")
    print(f"   🔹 직접 매핑: {direct_time:.4f}초")
    print()

    if direct_time < current_time:
        speedup = current_time / direct_time
        print(f"🚀 직접 매핑이 {speedup:.2f}배 더 빠름")
    else:
        slowdown = direct_time / current_time
        print(f"🐌 직접 매핑이 {slowdown:.2f}배 더 느림")

    print()

    # === 정확성 검증 ===
    print("✅ 정확성 검증:")
    for tf in timeframes:
        current_result = TimeUtilsCurrentImplementation.get_timeframe_seconds(tf)
        direct_result = TimeUtilsDirectMapping.get_timeframe_seconds(tf)
        match = "✅" if current_result == direct_result else "❌"
        print(f"   {match} {tf}: {current_result} == {direct_result}")


def run_memory_test():
    """메모리 사용량 비교"""
    import sys

    print()
    print("💾 메모리 사용량 비교:")

    # timedelta 객체 크기
    td_obj = timedelta(minutes=5)
    td_size = sys.getsizeof(td_obj)

    # int 객체 크기
    int_obj = 300
    int_size = sys.getsizeof(int_obj)

    print(f"   🔹 timedelta 객체: {td_size} bytes")
    print(f"   🔹 int 객체: {int_size} bytes")
    print(f"   🔹 차이: {td_size - int_size} bytes/객체")

    # 전체 딕셔너리 크기 비교
    current_dict_size = sys.getsizeof(TimeUtilsCurrentImplementation._TIMEFRAME_MAP)
    direct_dict_size = sys.getsizeof(TimeUtilsDirectMapping._TIMEFRAME_SECONDS)

    print(f"   🔹 현재 딕셔너리: {current_dict_size} bytes")
    print(f"   🔹 직접 매핑 딕셔너리: {direct_dict_size} bytes")


if __name__ == "__main__":
    print("🎯 TimeUtils 성능 최적화 분석")
    print("=" * 50)

    run_performance_test()
    run_memory_test()

    print()
    print("💡 결론 및 권장사항:")
    print("   - CandleDataProvider에서 매우 자주 호출되는 메서드")
    print("   - 성능이 중요한 경우 직접 매핑 고려")
    print("   - 유지보수성과 성능 사이의 트레이드오프 고려")
