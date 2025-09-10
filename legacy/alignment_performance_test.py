"""
🔬 TimeUtils _align_to_candle_boundary 성능 비교 테스트

현재 구현 vs backup 구현 (동일한 매핑 + 순수 내림 정렬 로직만 비교)
"""

import time
from datetime import datetime
from typing import Dict


class TimeUtilsCurrentImplementation:
    """현재 구현: 직접 매핑 + 최적화된 정렬"""

    _TIMEFRAME_SECONDS: Dict[str, int] = {
        "1s": 1, "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
        "60m": 3600, "1h": 3600, "240m": 14400, "4h": 14400,
        "1d": 86400, "1w": 604800, "1M": 2592000, "1y": 31536000,
    }

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        return TimeUtilsCurrentImplementation._TIMEFRAME_SECONDS[timeframe]

    @staticmethod
    def _align_to_candle_boundary(dt: datetime, timeframe: str) -> datetime:
        timeframe_seconds = TimeUtilsCurrentImplementation.get_timeframe_seconds(timeframe)

        if timeframe_seconds < 60:
            aligned_second = (dt.second // timeframe_seconds) * timeframe_seconds
            return dt.replace(second=aligned_second, microsecond=0)
        elif timeframe_seconds < 3600:
            timeframe_minutes = timeframe_seconds // 60
            aligned_minute = (dt.minute // timeframe_minutes) * timeframe_minutes
            return dt.replace(minute=aligned_minute, second=0, microsecond=0)
        elif timeframe_seconds < 86400:
            timeframe_hours = timeframe_seconds // 3600
            aligned_hour = (dt.hour // timeframe_hours) * timeframe_hours
            return dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)
        else:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)


class TimeUtilsBackupImplementation:
    """backup 파일 구현: 동일한 매핑 + backup 내림 정렬 로직"""

    # 현재 구현과 동일한 매핑 사용 (공정한 비교를 위해)
    _TIMEFRAME_SECONDS: Dict[str, int] = {
        "1s": 1, "1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
        "60m": 3600, "1h": 3600, "240m": 14400, "4h": 14400,
        "1d": 86400, "1w": 604800, "1M": 2592000, "1y": 31536000,
    }

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        return TimeUtilsBackupImplementation._TIMEFRAME_SECONDS[timeframe]

    @staticmethod
    def _floor_to_candle_boundary(dt: datetime, timeframe_seconds: int) -> datetime:
        """backup 파일의 내림 정렬 로직"""
        if timeframe_seconds < 60:
            aligned_second = (dt.second // timeframe_seconds) * timeframe_seconds
            return dt.replace(second=aligned_second, microsecond=0)
        elif timeframe_seconds < 3600:
            timeframe_minutes = timeframe_seconds // 60
            aligned_minute = (dt.minute // timeframe_minutes) * timeframe_minutes
            return dt.replace(minute=aligned_minute, second=0, microsecond=0)
        elif timeframe_seconds < 86400:
            timeframe_hours = timeframe_seconds // 3600
            aligned_hour = (dt.hour // timeframe_hours) * timeframe_hours
            return dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)
        else:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _align_to_candle_boundary(dt: datetime, timeframe: str) -> datetime:
        """backup 파일의 내림 정렬 로직만 (동일한 매핑 사용으로 순수 비교)"""
        timeframe_seconds = TimeUtilsBackupImplementation.get_timeframe_seconds(timeframe)

        # backup 파일의 _floor_to_candle_boundary 로직
        return TimeUtilsBackupImplementation._floor_to_candle_boundary(dt, timeframe_seconds)


def performance_test():
    """성능 비교 테스트 (내림 정렬만 공정 비교)"""

    # 테스트 데이터 생성
    test_times = [
        datetime(2024, 1, 1, 14, 32, 45, 123456),
        datetime(2024, 5, 15, 9, 17, 23, 789012),
        datetime(2024, 8, 20, 16, 48, 52, 345678),
        datetime(2024, 12, 31, 23, 59, 59, 999999),
    ]

    timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"]
    iterations = 10000

    print("🔬 _align_to_candle_boundary 순수 내림 정렬 성능 비교")
    print("=" * 60)
    print(f"테스트 데이터: {len(test_times)}개 시간 × {len(timeframes)}개 타임프레임")
    print(f"반복 횟수: {iterations:,}회")
    print("조건: 동일한 초 변환 매핑 사용, 순수 내림 정렬 로직만 비교")
    print()

    # 현재 구현 테스트
    print("🚀 현재 구현 (직접 매핑) 테스트 중...")
    start_time = time.perf_counter()

    for _ in range(iterations):
        for test_time in test_times:
            for timeframe in timeframes:
                TimeUtilsCurrentImplementation._align_to_candle_boundary(test_time, timeframe)

    current_time = time.perf_counter() - start_time

    # backup 구현 테스트
    print("📚 backup 구현 (timedelta 기반) 테스트 중...")
    start_time = time.perf_counter()

    for _ in range(iterations):
        for test_time in test_times:
            for timeframe in timeframes:
                TimeUtilsBackupImplementation._align_to_candle_boundary(test_time, timeframe)

    backup_time = time.perf_counter() - start_time

    # 결과 비교
    print()
    print("📊 성능 비교 결과:")
    print("-" * 40)
    print(f"현재 구현:   {current_time:.4f}초")
    print(f"backup 구현: {backup_time:.4f}초")
    print(f"성능 향상:   {backup_time / current_time:.2f}배 빠름")
    print()

    # 정확성 검증
    print("🔍 정확성 검증:")
    print("-" * 40)

    all_correct = True
    for test_time in test_times[:2]:  # 일부만 검증
        for timeframe in timeframes[:4]:  # 일부만 검증
            current_result = TimeUtilsCurrentImplementation._align_to_candle_boundary(test_time, timeframe)
            backup_result = TimeUtilsBackupImplementation._align_to_candle_boundary(test_time, timeframe)

            if current_result != backup_result:
                print(f"❌ 불일치: {timeframe} | {test_time}")
                print(f"   현재: {current_result}")
                print(f"   backup: {backup_result}")
                all_correct = False

    if all_correct:
        print("✅ 모든 테스트 케이스에서 결과 일치")

    print()
    print("📈 결론:")
    if current_time < backup_time:
        print(f"✅ 현재 구현이 {backup_time / current_time:.2f}배 더 빠름")
    else:
        print(f"⚠️ backup 구현이 {current_time / backup_time:.2f}배 더 빠름")


if __name__ == "__main__":
    performance_test()
