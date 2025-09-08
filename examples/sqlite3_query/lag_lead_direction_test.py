"""
LAG 함수 방향성 정확히 이해하기

ORDER BY timestamp DESC 에서:
- LAG(timestamp): 현재 행보다 이전 행 (리스트상 위쪽, 시간상 더 최신)
- LEAD(timestamp): 현재 행보다 다음 행 (리스트상 아래쪽, 시간상 더 과거)
"""

import sqlite3
from datetime import datetime, timedelta

def create_simple_test_data():
    """간단한 테스트 데이터로 LAG/LEAD 방향 확인"""
    conn = sqlite3.connect(":memory:")

    conn.execute("""
        CREATE TABLE test_candles (
            time_str TEXT,
            timestamp INTEGER
        )
    """)

    # 5개 시점: 12:00, 11:59, 11:57, 11:56, 11:55 (11:58 누락)
    times = [
        ("12:00", 1735700400000),  # 최신
        ("11:59", 1735700340000),
        # 11:58 누락 (GAP)
        ("11:57", 1735700220000),
        ("11:56", 1735700160000),
        ("11:55", 1735700100000)   # 가장 과거
    ]

    for time_str, timestamp in times:
        conn.execute("INSERT INTO test_candles VALUES (?, ?)", (time_str, timestamp))

    return conn

def test_lag_lead_directions():
    """LAG/LEAD 방향성 테스트"""
    conn = create_simple_test_data()

    print("📊 원본 데이터 (ORDER BY timestamp DESC):")
    cursor = conn.execute("""
        SELECT time_str, timestamp FROM test_candles ORDER BY timestamp DESC
    """)
    for i, (time_str, timestamp) in enumerate(cursor.fetchall()):
        print(f"   [{i+1}] {time_str} (timestamp: {timestamp})")

    print("\n🔍 LAG/LEAD 함수 테스트 (ORDER BY timestamp DESC):")
    cursor = conn.execute("""
        SELECT
            time_str,
            timestamp,
            LAG(timestamp) OVER (ORDER BY timestamp DESC) as lag_timestamp,
            LEAD(timestamp) OVER (ORDER BY timestamp DESC) as lead_timestamp,
            timestamp - LAG(timestamp) OVER (ORDER BY timestamp DESC) as lag_diff,
            timestamp - LEAD(timestamp) OVER (ORDER BY timestamp DESC) as lead_diff
        FROM test_candles
        ORDER BY timestamp DESC
    """)

    print("   시간  | timestamp  | LAG(이전)  | LEAD(다음) | LAG차이    | LEAD차이")
    print("   " + "-" * 70)

    for time_str, ts, lag_ts, lead_ts, lag_diff, lead_diff in cursor.fetchall():
        lag_str = f"{lag_ts}" if lag_ts else "NULL"
        lead_str = f"{lead_ts}" if lead_ts else "NULL"
        lag_diff_str = f"{lag_diff}" if lag_diff else "NULL"
        lead_diff_str = f"{lead_diff}" if lead_diff else "NULL"

        print(f"   {time_str} | {ts} | {lag_str:>10} | {lead_str:>10} | {lag_diff_str:>8} | {lead_diff_str:>8}")

def test_gap_detection_methods():
    """다양한 gap 검출 방법 테스트"""
    conn = create_simple_test_data()

    print("\n🎯 Gap 검출 방법 비교:")
    print("   목표: 11:58 누락 감지")

    # 방법 1: LEAD 사용 (현재 → 다음 간격 확인)
    print("\n1️⃣ LEAD 방식 (현재 → 다음 간격):")
    cursor = conn.execute("""
        SELECT
            time_str,
            timestamp,
            LEAD(timestamp) OVER (ORDER BY timestamp DESC) as next_timestamp,
            CASE
                WHEN LEAD(timestamp) OVER (ORDER BY timestamp DESC) IS NULL THEN 'LAST'
                WHEN timestamp - LEAD(timestamp) OVER (ORDER BY timestamp DESC) > 70000 THEN 'GAP_AFTER'
                ELSE 'OK'
            END as status
        FROM test_candles
        ORDER BY timestamp DESC
    """)

    for time_str, ts, next_ts, status in cursor.fetchall():
        next_str = f"{next_ts}" if next_ts else "NULL"
        print(f"   {time_str}: {status} (다음: {next_str})")

    # 방법 2: LAG 사용 (이전 → 현재 간격 확인)
    print("\n2️⃣ LAG 방식 (이전 → 현재 간격):")
    cursor = conn.execute("""
        SELECT
            time_str,
            timestamp,
            LAG(timestamp) OVER (ORDER BY timestamp DESC) as prev_timestamp,
            CASE
                WHEN LAG(timestamp) OVER (ORDER BY timestamp DESC) IS NULL THEN 'FIRST'
                WHEN LAG(timestamp) OVER (ORDER BY timestamp DESC) - timestamp > 70000 THEN 'GAP_BEFORE'
                ELSE 'OK'
            END as status
        FROM test_candles
        ORDER BY timestamp DESC
    """)

    for time_str, ts, prev_ts, status in cursor.fetchall():
        prev_str = f"{prev_ts}" if prev_ts else "NULL"
        print(f"   {time_str}: {status} (이전: {prev_str})")

def find_last_continuous_correct():
    """올바른 연속 데이터 끝점 찾기"""
    conn = create_simple_test_data()

    print("\n🎯 올바른 'find_last_continuous_time' 구현:")
    print("   목표: 11:59 시점에서 역방향으로 연속성 확인 → 11:59가 끝점")

    start_time_ts = 1735700280000  # 11:58 시점 (누락된 시점부터)

    # LEAD 방식: 현재 시점에서 다음 시점 간격 확인
    cursor = conn.execute("""
        WITH gap_check AS (
            SELECT
                time_str,
                timestamp,
                LEAD(timestamp) OVER (ORDER BY timestamp DESC) as next_timestamp,
                CASE
                    WHEN LEAD(timestamp) OVER (ORDER BY timestamp DESC) IS NULL THEN 0
                    WHEN timestamp - LEAD(timestamp) OVER (ORDER BY timestamp DESC) > 70000 THEN 1
                    ELSE 0
                END as has_gap_after
            FROM test_candles
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        )
        SELECT time_str, timestamp
        FROM gap_check
        WHERE has_gap_after = 1
        ORDER BY timestamp DESC
        LIMIT 1
    """, (start_time_ts,))

    result = cursor.fetchone()
    if result:
        print(f"   결과: {result[0]} 이후에 끊어짐 발견")
    else:
        print("   결과: 끊어짐 없음")

    conn.close()

if __name__ == "__main__":
    print("🚀 LAG/LEAD 방향성 정확한 이해")
    print("=" * 60)

    test_lag_lead_directions()
    test_gap_detection_methods()
    find_last_continuous_correct()

    print("\n✅ 테스트 완료")
