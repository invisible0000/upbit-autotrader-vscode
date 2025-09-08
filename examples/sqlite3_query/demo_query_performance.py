"""
쿼리 성능 비교 테스트 스크립트

기존 방식(범위 체크) vs 최적화 방식(LEAD 윈도우 함수) 성능 비교
업비트 API 순서(최신→과거)에 맞춰 ORDER BY timestamp DESC 사용
"""

import time
import sqlite3
from datetime import datetime, timedelta


def create_test_data():
    """업비트 API 순서에 맞는    print("\n💡 Gap/Data End 검출 베스트 프랙티스:")
    print("   ✅ 업비트 API 데이터 순서: 최신→과거 (DESC)")
    print("   ✅ 윈도우 함수 활용: LEAD()로 성능 최적화")
    print("   ✅ 명확한 임계값: timeframe * 1.5배") 데이터를 생성합니다."""
    print("📝 테스트 데이터 생성 중 (업비트 API 순서: 최신→과거)...")

    # 메모리 DB 사용
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # 간단한 테스트 테이블 생성
    cursor.execute("""
        CREATE TABLE test_candles (
            candle_date_time_utc TEXT,
            timestamp INTEGER
        )
    """)

    # 인덱스 생성 (성능 향상)
    cursor.execute("CREATE INDEX idx_timestamp ON test_candles(timestamp)")
    cursor.execute("CREATE INDEX idx_candle_time ON test_candles(candle_date_time_utc)")

    # 1분봉 테스트 데이터 생성 (12:00 ~ 11:00, 1시간)
    base_time = datetime(2025, 9, 7, 12, 0, 0)

    # 연속 데이터: 12:00 ~ 11:50 (10분)
    for i in range(11):  # 12:00, 11:59, ..., 11:50
        current_time = base_time - timedelta(minutes=i)
        current_timestamp = int(current_time.timestamp() * 1000)

        cursor.execute(
            "INSERT INTO test_candles VALUES (?, ?)",
            (current_time.isoformat() + 'Z', current_timestamp)
        )

    # GAP: 11:50 다음에 11:47 (11:49, 11:48 누락 - 2분 gap)
    gap_time = base_time - timedelta(minutes=13)  # 11:47

    # 연속 데이터: 11:47 ~ 11:00 (47분)
    for i in range(48):  # 11:47, 11:46, ..., 11:00
        current_time = gap_time - timedelta(minutes=i)
        current_timestamp = int(current_time.timestamp() * 1000)

        cursor.execute(
            "INSERT INTO test_candles VALUES (?, ?)",
            (current_time.isoformat() + 'Z', current_timestamp)
        )

    conn.commit()
    print("✅ 테스트 데이터 생성 완료 (gap at 11:50→11:47)")
    return conn


def test_query_performance_with_mock_data():
    """업비트 API 순서에 맞는 올바른 gap 검출 방식 비교"""

    conn = create_test_data()
    cursor = conn.cursor()
    table_name = "test_candles"

    try:
        # 테스트 시작 시간 설정 (gap 발생 전 시점)
        start_time = "2025-09-07T11:55:00Z"

        print("\n=== 올바른 Gap 검출 방식 성능 비교 ===\n")

        # 데이터 구조 확인
        print("📊 테스트 데이터 구조 확인:")
        cursor.execute(f"""
            SELECT candle_date_time_utc, timestamp,
                   LEAD(timestamp) OVER (ORDER BY timestamp DESC) as next_timestamp,
                   timestamp - LEAD(timestamp) OVER (ORDER BY timestamp DESC) as gap_ms
            FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT 15
        """)

        print("   시간                    | timestamp      | 다음 시간      | Gap(ms)")
        print("   " + "-" * 75)

        for time_str, ts, next_ts, gap_ms in cursor.fetchall():
            next_str = f"{next_ts}" if next_ts else "NULL"
            gap_str = f"{gap_ms}" if gap_ms else "NULL"
            gap_status = "🔴 GAP" if gap_ms and gap_ms > 90000 else "✅ OK"

            print(f"   {time_str} | {ts} | {next_str:>13} | {gap_str:>8} {gap_status}")

        print(f"\n🎯 테스트 시작 시점: {start_time}")
        print("   예상 결과: 11:50:00Z에서 gap 검출\n")

        # 1. 기존 방식 (범위 체크 + EXISTS) - 올바른 방향으로 수정
        print("1️⃣ 기존 방식 (범위 체크 + EXISTS) - 올바른 방향으로 수정")
        legacy_query = f"""
        WITH range_check AS (
            SELECT
                candle_date_time_utc,
                timestamp,
                CASE WHEN NOT EXISTS (
                    SELECT 1 FROM {table_name} t2
                    WHERE t2.timestamp BETWEEN {table_name}.timestamp - 90000
                    AND {table_name}.timestamp - 60000
                    -- AND t2.candle_date_time_utc <= ?
                ) THEN 1 ELSE 0 END as has_gap
            FROM {table_name}
            WHERE candle_date_time_utc <= ?
            ORDER BY timestamp DESC  -- ✅ 올바른 방향
        )
        SELECT candle_date_time_utc as last_continuous_time
        FROM range_check
        WHERE has_gap = 1
        ORDER BY timestamp DESC
        LIMIT 1
        """

        # 성능 측정
        times_legacy = []
        result_legacy = None
        for i in range(10):  # 10회 반복
            start = time.perf_counter()
            cursor.execute(legacy_query, (start_time,))
            result_legacy = cursor.fetchone()
            end = time.perf_counter()
            times_legacy.append(end - start)

        avg_legacy = sum(times_legacy) / len(times_legacy)
        print(f"   평균 실행시간: {avg_legacy:.6f}초")
        print(f"   결과: {result_legacy}")
        print()

        # 2. 최적화 방식 (LEAD 윈도우 함수) - 데이터 끝 감지 포함
        print("2️⃣ 최적화 방식 (LEAD 윈도우 함수) - 데이터 끝 감지 포함")
        optimized_query = f"""
        SELECT candle_date_time_utc as last_continuous_time
        FROM (
            SELECT
                candle_date_time_utc,
                timestamp,
                LEAD(timestamp) OVER (ORDER BY timestamp DESC) as next_timestamp
            FROM {table_name}
            WHERE candle_date_time_utc <= ?  -- 과거 방향으로 검색
            ORDER BY timestamp DESC  -- 업비트 API 순서: 최신→과거
        )
        WHERE (
            -- 중간 Gap 검출
            (next_timestamp IS NOT NULL AND timestamp - next_timestamp > 90000)
            OR
            -- 데이터 끝 검출 (LEAD = NULL)
            (next_timestamp IS NULL)
        )
        ORDER BY timestamp DESC
        LIMIT 1
        """

        # 성능 측정
        times_optimized = []
        result_optimized = None
        for i in range(10):  # 10회 반복
            start = time.perf_counter()
            cursor.execute(optimized_query, (start_time,))
            result_optimized = cursor.fetchone()
            end = time.perf_counter()
            times_optimized.append(end - start)

        avg_optimized = sum(times_optimized) / len(times_optimized)
        print(f"   평균 실행시간: {avg_optimized:.6f}초")
        print(f"   결과: {result_optimized}")
        print()

        # 3. 성능 비교 결과
        print("🏁 성능 비교 결과")
        print("-" * 50)

        # 결과 일치성 확인
        if result_legacy and result_optimized:
            if result_legacy[0] == result_optimized[0]:
                print("✅ 두 방식 모두 동일한 결과 반환")
            else:
                print("❌ 결과 불일치!")
                print(f"   기존 방식: {result_legacy[0]}")
                print(f"   최적화 방식: {result_optimized[0]}")

        # 성능 비교
        if avg_legacy > 0:
            improvement = ((avg_legacy - avg_optimized) / avg_legacy) * 100
            speed_ratio = avg_legacy / avg_optimized

            if avg_optimized < avg_legacy:
                print(f"🚀 최적화 방식이 {improvement:.1f}% 더 빠름 ({speed_ratio:.1f}x)")
            else:
                print(f"⚠️  기존 방식이 {-improvement:.1f}% 더 빠름")

        print(f"기존 방식:   {avg_legacy:.6f}초")
        print(f"최적화 방식: {avg_optimized:.6f}초")

        # 4. EXPLAIN QUERY PLAN 분석
        print("\n📊 쿼리 실행 계획 분석")
        print("-" * 50)

        print("기존 방식 (범위 체크):")
        cursor.execute(f"EXPLAIN QUERY PLAN {legacy_query}", (start_time,))
        for row in cursor.fetchall():
            print(f"  {row}")

        print("\n최적화 방식 (LEAD 윈도우):")
        cursor.execute(f"EXPLAIN QUERY PLAN {optimized_query}", (start_time,))
        for row in cursor.fetchall():
            print(f"  {row}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 Gap 검출 및 데이터 엔드 검출 방법론 가이드")
    print("=" * 60)
    print("� 목적: 업비트 API 순서(최신→과거)에 맞는 올바른 gap 검출 방법 비교")
    print()

    print("📊 테스트 DB 구조:")
    print("   - 메모리 DB (sqlite3 ':memory:')")
    print("   - 테이블: test_candles")
    print("   - 데이터: 12:00~11:50 (연속) + GAP(11:49,11:48 누락) + 11:47~11:00 (연속)")
    print("   - 목표: 11:50:00Z에서 gap 검출 확인")
    print()

    print("� 비교 방법:")
    print("   1️⃣ 기존 방식: CTE + EXISTS 서브쿼리 (범위 체크)")
    print("   2️⃣ 최적화 방식: LEAD 윈도우 함수 (직접 간격 계산)")
    print()

    print("✅ 핵심 포인트:")
    print("   - ORDER BY timestamp DESC (업비트 API 순서 반영)")
    print("   - LEAD()로 다음 시점과의 간격 확인")
    print("   - 90000ms (1.5분) 임계값 초과시 gap 감지")
    print()

    # 테스트 실행
    test_query_performance_with_mock_data()

    print("\n� Gap/Data End 검출 베스트 프랙티스:")
    print("   ✅ 업비트 API 데이터 순서: 최신→과거 (DESC)")
    print("   ✅ 윈도우 함수 활용: LEAD()로 성능 최적화")
    print("   ✅ 명확한 임계값: timeframe * 1.5배")
    print("   ✅ 단일 패스 쿼리: CTE 오버헤드 최소화")
    print()
    print("🎯 이 방법론을 find_last_continuous_time 함수 최적화에 적용!")
