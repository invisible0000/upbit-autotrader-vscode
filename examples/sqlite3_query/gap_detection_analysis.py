"""
데이터 끝에서의 Gap 감지 테스트 - 간단 버전
"""

import sqlite3


def test_data_end_scenarios():
    """데이터 끝에서 LAG가 어떻게 동작하는지 테스트"""
    print("🚀 데이터 끝에서의 LAG 동작 테스트")

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE test_candles (
            time_str TEXT,
            ts INTEGER
        )
    """)

    # 시나리오: 중간에 Gap이 있고 데이터가 끝남
    test_data = [
        ("10:00", 1000),
        ("10:01", 1060),  # 60초 차이 (정상)
        ("10:02", 1120),  # 60초 차이 (정상)
        ("10:03", 1180),  # 60초 차이 (정상)
        ("10:09", 1540),  # 360초 차이 (6분 GAP!)
        ("10:10", 1600),  # 60초 차이 (정상, 마지막 데이터)
        # 여기서 데이터 끝!
    ]

    for time_str, ts in test_data:
        cursor.execute("INSERT INTO test_candles VALUES (?, ?)", (time_str, ts))

    conn.commit()

    print("\n📋 테스트 데이터:")
    cursor.execute("SELECT * FROM test_candles ORDER BY ts")
    for row in cursor.fetchall():
        print(f"  {row}")

    # LAG 동작 확인
    print("\n📊 LAG 동작 분석:")
    cursor.execute("""
    SELECT
        time_str,
        ts,
        LAG(time_str) OVER (ORDER BY ts) as prev_time,
        LAG(ts) OVER (ORDER BY ts) as prev_ts,
        ts - LAG(ts) OVER (ORDER BY ts) as gap
    FROM test_candles
    ORDER BY ts
    """)

    results = cursor.fetchall()
    for row in results:
        time_str, ts, prev_time, prev_ts, gap = row
        if gap is None:
            print(f"  {time_str}: 첫 번째 데이터 (LAG = NULL)")
        else:
            status = "🚨 GAP!" if gap > 90 else "✅ 정상"
            print(f"  {prev_time} → {time_str}: {gap}초 차이 ({status})")

    # Gap 감지 쿼리
    print("\n🎯 Gap 감지 결과:")
    cursor.execute("""
    WITH gap_detect AS (
        SELECT
            LAG(time_str) OVER (ORDER BY ts) as prev_time,
            ts - LAG(ts) OVER (ORDER BY ts) as gap
        FROM test_candles
        ORDER BY ts
    )
    SELECT prev_time
    FROM gap_detect
    WHERE gap > 90
    LIMIT 1
    """)

    gap_result = cursor.fetchone()
    if gap_result:
        print(f"  첫 번째 Gap 직전 시간: {gap_result[0]}")
    else:
        print("  Gap이 감지되지 않음")

    print("\n" + "="*60)
    print("🔍 중요한 발견들")
    print("="*60)

    print("1. ✅ LAG는 중간 Gap을 잘 감지함")
    print("   - 10:03 → 10:09의 6분 Gap을 정확히 탐지")

    print("\n2. ❌ 데이터 끝에서는 Gap을 감지할 수 없음")
    print("   - 10:10 이후에 데이터가 없어도 LAG로는 알 수 없음")
    print("   - 현재 시간(예: 10:12)과 마지막 데이터(10:10) 비교 필요")

    print("\n3. 💡 실시간 시스템에서 필요한 추가 로직:")
    print("   - find_last_continuous_time: 과거 Gap 감지 (LAG 방식)")
    print("   - check_data_freshness: 현재 시간과 마지막 데이터 비교")

    # 데이터 신선도 체크 시뮬레이션
    print("\n📈 데이터 신선도 체크 예시:")

    cursor.execute("SELECT MAX(time_str), MAX(ts) FROM test_candles")
    last_time, last_ts = cursor.fetchone()

    current_time = "10:12"  # 현재 시간 가정
    current_ts = 1720       # 현재 timestamp 가정

    data_delay = current_ts - last_ts

    print(f"  마지막 데이터: {last_time} (ts={last_ts})")
    print(f"  현재 시간: {current_time} (ts={current_ts})")
    print(f"  데이터 지연: {data_delay}초")

    if data_delay > 90:  # 90초 이상 지연
        print(f"  🚨 데이터 지연 감지! 마지막 신뢰 시간: {last_time}")
    else:
        print(f"  ✅ 데이터가 최신 상태")

    conn.close()


if __name__ == "__main__":
    test_data_end_scenarios()
