"""
간단한 Gap 감지 테스트
"""

import time
import sqlite3
from datetime import datetime


def create_simple_test_data():
    """간단한 Gap이 있는 테스트 데이터 생성"""
    print("📝 간단한 테스트 데이터 생성 중...")

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE test_candles (
            candle_date_time_utc TEXT,
            timestamp INTEGER
        )
    """)

    # 10분간의 1분봉 데이터 + 중간에 5분 Gap
    test_data = [
        ("2025-09-07T10:00:00", 1725696000000),  # 10:00
        ("2025-09-07T10:01:00", 1725696060000),  # 10:01
        ("2025-09-07T10:02:00", 1725696120000),  # 10:02
        ("2025-09-07T10:03:00", 1725696180000),  # 10:03
        # 여기서 5분 Gap 발생
        ("2025-09-07T10:09:00", 1725696540000),  # 10:09 (Gap 후)
        ("2025-09-07T10:10:00", 1725696600000),  # 10:10
    ]

    for time_str, timestamp in test_data:
        cursor.execute(
            "INSERT INTO test_candles VALUES (?, ?)",
            (time_str, timestamp)
        )

    conn.commit()
    print("✅ 테스트 데이터 6개 생성 완료")

    # 데이터 확인
    print("\n📋 생성된 데이터:")
    cursor.execute("SELECT * FROM test_candles ORDER BY timestamp")
    for row in cursor.fetchall():
        print(f"  {row}")

    return conn


def test_gap_detection():
    """Gap 감지 쿼리 테스트"""
    conn = create_simple_test_data()
    cursor = conn.cursor()

    print("\n=== Gap 감지 쿼리 테스트 ===")

    start_time = "2025-09-07T10:00:00"

    # 1. 현재 방식
    print("\n1️⃣ 현재 방식 (LAG + 차이계산)")
    query1 = """
    WITH consecutive_check AS (
        SELECT
            candle_date_time_utc,
            `timestamp`,
            (`timestamp` - LAG(`timestamp`) OVER (ORDER BY `timestamp`)) / 1000.0 as time_diff_seconds,
            LAG(candle_date_time_utc) OVER (ORDER BY `timestamp`) as prev_time
        FROM test_candles
        WHERE candle_date_time_utc >= ?
        ORDER BY `timestamp`
    ),
    gap_detection AS (
        SELECT
            candle_date_time_utc,
            prev_time,
            time_diff_seconds,
            CASE WHEN time_diff_seconds > 90 THEN 1 ELSE 0 END as has_gap
        FROM consecutive_check
        WHERE prev_time IS NOT NULL
    )
    SELECT prev_time as last_continuous_time
    FROM gap_detection
    WHERE has_gap = 1
    ORDER BY candle_date_time_utc
    LIMIT 1
    """

    cursor.execute(query1, (start_time,))
    result1 = cursor.fetchone()
    print(f"결과: {result1}")

    # 2. 단일 CTE 방식
    print("\n2️⃣ 단일 CTE 방식")
    query2 = """
    WITH gap_detect AS (
        SELECT
            LAG(candle_date_time_utc) OVER (ORDER BY `timestamp`) as prev_time,
            `timestamp` - LAG(`timestamp`) OVER (ORDER BY `timestamp`) as gap_ms
        FROM test_candles
        WHERE candle_date_time_utc >= ?
        ORDER BY `timestamp`
    )
    SELECT prev_time
    FROM gap_detect
    WHERE gap_ms > 90000
    LIMIT 1
    """

    cursor.execute(query2, (start_time,))
    result2 = cursor.fetchone()
    print(f"결과: {result2}")

    # 3. 최적화 방식 (상수 기반)
    print("\n3️⃣ 최적화 방식 (상수 기반)")
    timeframe_ms = 60 * 1000  # 1분
    tolerance_ms = 30 * 1000  # 30초 허용 오차

    query3 = f"""
    WITH gap_check AS (
        SELECT
            candle_date_time_utc,
            LAG(candle_date_time_utc) OVER (ORDER BY `timestamp`) as prev_time,
            (`timestamp` - LAG(`timestamp`) OVER (ORDER BY `timestamp`)) as time_diff_ms
        FROM test_candles
        WHERE candle_date_time_utc >= ?
        ORDER BY `timestamp`
    )
    SELECT prev_time
    FROM gap_check
    WHERE prev_time IS NOT NULL
      AND time_diff_ms > {timeframe_ms + tolerance_ms}
    ORDER BY candle_date_time_utc
    LIMIT 1
    """

    cursor.execute(query3, (start_time,))
    result3 = cursor.fetchone()
    print(f"결과: {result3}")

    # 성능 측정
    print("\n⏱️ 성능 측정 (100회 반복)")

    queries = [
        ("현재 방식", query1),
        ("단일 CTE", query2),
        ("최적화 방식", query3)
    ]

    for name, query in queries:
        times = []
        for _ in range(100):
            start = time.perf_counter()
            cursor.execute(query, (start_time,))
            cursor.fetchone()
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)
        print(f"{name}: {avg_time:.6f}초")

    conn.close()


if __name__ == "__main__":
    print("🚀 Gap 감지 쿼리 테스트")
    test_gap_detection()
