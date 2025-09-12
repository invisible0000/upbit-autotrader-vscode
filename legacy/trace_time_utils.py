"""
🔍 TimeUtils.calculate_expected_count 단계별 추적 디버깅
"""

from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

def trace_calculate_expected_count():
    """calculate_expected_count 메서드 단계별 추적"""
    print("🔍 TimeUtils.calculate_expected_count 단계별 추적")

    # 테스트 데이터
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=2)  # 과거 (더 작은 값)
    end_time = now  # 최신 (더 큰 값)
    timeframe = "1m"

    print(f"입력 매개변수:")
    print(f"  start_time (과거): {start_time}")
    print(f"  end_time (최신): {end_time}")
    print(f"  timeframe: {timeframe}")
    print(f"  start_time < end_time: {start_time < end_time}")

    # 1단계: 초기 조건 검사
    print(f"\n1️⃣ 초기 조건 검사:")
    condition1 = start_time >= end_time
    print(f"  if start_time >= end_time: {condition1}")
    if condition1:
        print(f"  ➡️ return 0 (조기 종료)")
        return

    # 2단계: 시간 정렬
    print(f"\n2️⃣ 시간 정렬:")
    aligned_start = TimeUtils._align_to_candle_boundary(start_time, timeframe)
    print(f"  aligned_start = {aligned_start}")

    # 3단계: 타임프레임별 분기
    print(f"\n3️⃣ 타임프레임별 분기:")
    print(f"  timeframe == '1M': {timeframe == '1M'}")
    print(f"  timeframe == '1y': {timeframe == '1y'}")

    if timeframe not in ['1M', '1y']:
        print(f"  ➡️ 분/시/일/주봉 로직 사용")

        # 4단계: timedelta 계산
        print(f"\n4️⃣ timedelta 계산:")
        dt = TimeUtils.get_timeframe_delta(timeframe)
        print(f"  dt = {dt}")

        # 5단계: time_diff 계산 (수정된 로직)
        print(f"\n5️⃣ time_diff 계산:")
        time_diff = aligned_start - end_time  # 사용자가 수정한 부분
        print(f"  time_diff = aligned_start - end_time = {time_diff}")
        print(f"  time_diff.total_seconds() = {time_diff.total_seconds()}")

        # 6단계: count 계산
        print(f"\n6️⃣ count 계산:")
        count = int(time_diff.total_seconds() / dt.total_seconds())
        print(f"  count = int({time_diff.total_seconds()} / {dt.total_seconds()}) = {count}")
        final_count = max(0, count)
        print(f"  max(0, count) = {final_count}")

        print(f"\n✅ 예상 결과: {final_count}")

    # 실제 메서드 호출 비교
    print(f"\n🧪 실제 메서드 호출:")
    actual_result = TimeUtils.calculate_expected_count(start_time, end_time, timeframe)
    print(f"  actual_result = {actual_result}")

if __name__ == "__main__":
    trace_calculate_expected_count()
