"""
데이터 끝 감지 논리 테스트
"""

import sqlite3


def test_end_detection_logic():
    """CTE + LAG로 데이터 끝을 감지할 수 있는지 테스트"""
    print("🚀 데이터 끝 감지 논리 테스트")

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE test_candles (
            time_str TEXT,
            ts INTEGER
        )
    """)

    # 시나리오: 중간 Gap + 데이터 끝
    test_data = [
        ("10:00", 1000),
        ("10:01", 1060),  # 정상
        ("10:02", 1120),  # 정상
        ("10:03", 1180),  # 정상
        ("10:09", 1540),  # 6분 GAP!
        ("10:10", 1600),  # 정상 (마지막 데이터)
        # 여기서 끝! 10:11 데이터 없음
    ]

    for time_str, ts in test_data:
        cursor.execute("INSERT INTO test_candles VALUES (?, ?)", (time_str, ts))

    conn.commit()

    print("\n📋 테스트 데이터:")
    cursor.execute("SELECT * FROM test_candles ORDER BY ts")
    for row in cursor.fetchall():
        print(f"  {row}")

    print("\n🔍 핵심 질문: LAG로 '데이터 끝'을 감지할 수 있나?")

    # 모든 행의 LAG 상태 확인
    print("\n📊 모든 행의 LAG/LEAD 분석:")
    cursor.execute("""
    SELECT
        time_str,
        ts,
        LAG(time_str) OVER (ORDER BY ts) as prev_time,
        LAG(ts) OVER (ORDER BY ts) as prev_ts,
        LEAD(time_str) OVER (ORDER BY ts) as next_time,
        LEAD(ts) OVER (ORDER BY ts) as next_ts,
        ts - LAG(ts) OVER (ORDER BY ts) as gap_from_prev,
        LEAD(ts) OVER (ORDER BY ts) - ts as gap_to_next
    FROM test_candles
    ORDER BY ts
    """)

    results = cursor.fetchall()
    for row in results:
        time_str, ts, prev_time, prev_ts, next_time, next_ts, gap_from_prev, gap_to_next = row

        print(f"\n  📍 {time_str} (ts={ts}):")
        print(f"    이전: {prev_time} (gap: {gap_from_prev})")
        print(f"    다음: {next_time} (gap: {gap_to_next})")

        # 데이터 끝 판단 로직
        if next_time is None:
            print(f"    🎯 데이터 끝 감지! LEAD = NULL")
        elif gap_from_prev and gap_from_prev > 90:
            print(f"    🚨 Gap 감지! 이전과 {gap_from_prev}초 차이")

    print("\n" + "="*60)
    print("💡 데이터 끝 감지 전략")
    print("="*60)

    # 전략 1: LEAD NULL 체크
    print("\n1️⃣ LEAD NULL 체크로 마지막 데이터 찾기:")
    cursor.execute("""
    WITH lead_check AS (
        SELECT
            time_str,
            LEAD(time_str) OVER (ORDER BY ts) as next_time
        FROM test_candles
    )
    SELECT time_str as last_data_time
    FROM lead_check
    WHERE next_time IS NULL
    """)

    last_data = cursor.fetchone()
    if last_data:
        print(f"  마지막 데이터: {last_data[0]}")

    # 전략 2: 현재 시간과 마지막 데이터 비교
    print("\n2️⃣ 현재 시간과 마지막 데이터 비교:")
    current_time_ts = 1720  # 10:12 가정 (현재 시간)
    current_time_str = "10:12"

    cursor.execute("SELECT MAX(time_str), MAX(ts) FROM test_candles")
    last_time, last_ts = cursor.fetchone()

    data_delay = current_time_ts - last_ts
    print(f"  현재 시간: {current_time_str} (ts={current_time_ts})")
    print(f"  마지막 데이터: {last_time} (ts={last_ts})")
    print(f"  데이터 지연: {data_delay}초")

    if data_delay > 90:
        print(f"  🚨 실시간 데이터 지연 감지!")
        print(f"  실제 마지막 연속 시간: {last_time}")

    # 전략 3: 통합 Gap 감지 (과거 + 현재)
    print("\n3️⃣ 통합 Gap 감지 (과거 Gap + 실시간 지연):")

    # 과거 Gap 찾기
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

    past_gap_result = cursor.fetchone()

    if past_gap_result:
        past_gap_time = past_gap_result[0]
        print(f"  과거 Gap 감지: {past_gap_time} 이후 끊어짐")

        # 현재 시간 기준 지연도 확인
        if data_delay > 90:
            print(f"  실시간 지연도 감지: {last_time} 이후 지연")
            print(f"  🎯 최종 결과: {past_gap_time} (과거 Gap이 더 이른 시점)")
        else:
            print(f"  실시간 지연 없음")
            print(f"  🎯 최종 결과: {past_gap_time}")
    else:
        if data_delay > 90:
            print(f"  과거 Gap 없음, 실시간 지연 감지")
            print(f"  🎯 최종 결과: {last_time} (실시간 지연)")
        else:
            print(f"  Gap 없음, 데이터 정상")
            print(f"  🎯 최종 결과: None (연속 데이터)")

    print("\n" + "="*60)
    print("🎯 결론: 데이터 끝 감지 가능!")
    print("="*60)

    print("✅ LEAD IS NULL로 마지막 데이터 확인 가능")
    print("✅ 현재 시간과 비교로 실시간 지연 감지 가능")
    print("✅ LAG + 현재시간 조합으로 완벽한 Gap 감지 가능")
    print("� 핵심: LAG(과거 Gap) + 현재시간 비교(실시간 지연)")

    conn.close()


if __name__ == "__main__":
    test_end_detection_logic()
