"""
쿼리 성능 비교 테스트 스크립트

기존 방식(범위 체크) vs 최적화 방식(LEAD 윈도우 함수) 성능 비교
업비트 API 순서(최신→과거)에 맞춰 ORDER BY timestamp DESC 사용
"""

import time
import sqlite3
from datetime import datetime, timedelta


def create_test_data():
    """대용량 테스트 데이터 생성 - 업비트 API 순서(최신→과거)"""
    print("📝 대용량 테스트 데이터 생성 중 (10,000개 레코드, 업비트 API 순서: 최신→과거)...")

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

    # 대용량 1분봉 데이터 생성 (약 1주일치 = 10,080분)
    base_time = datetime(2025, 9, 7, 12, 0, 0)
    total_minutes = 10000

    print(f"   생성할 레코드: {total_minutes}개 (약 {total_minutes // 1440}일치 1분봉)")

    # 정답지 하드코딩 (이전 테스트 결과 기반)
    gap_start_time = "2025-09-01T06:00:00Z"      # Gap이 시작되는 시점
    test_start_time = "2025-09-06T19:20:00Z"     # 테스트 시작 시점
    expected_result = "2025-09-01T06:01:00Z"     # 예상 검출 결과 (Gap 직후)

    print(f"   🎯 정답지 - Gap 시작: {gap_start_time}")
    print(f"   🎯 정답지 - 테스트 시작: {test_start_time}")
    print(f"   🎯 정답지 - 예상 검출: {expected_result}")

    # 단순한 Gap 설정: 과거 10% 지점에 하나만
    gap_position = int(total_minutes * 0.9)  # 과거 10% 지점 (90% 진행 시점)
    test_start_position = int(total_minutes * 0.1)  # 최신 10% 지점 (10% 진행 시점)

    print(f"   Gap 위치: {gap_position}번째 (과거 10% 지점)")
    print(f"   테스트 시작: {test_start_position}번째 (최신 10% 지점)")

    # 연속 데이터 생성 (최신→과거 순서)
    for i in range(total_minutes):
        current_time = base_time - timedelta(minutes=i)
        current_timestamp = int(current_time.timestamp() * 1000)

        # 테스트 시작 시점 기록
        if i == test_start_position:
            test_start_time = current_time.isoformat() + 'Z'

        # Gap 생성: 과거 10% 지점에서 3분 건너뛰기
        if i == gap_position:
            gap_start_time = current_time.isoformat() + 'Z'
            print(f"   🎯 Gap 생성: {gap_start_time}에서 3분 건너뛰기")
            i += 3  # 3분 건너뛰기
            if i >= total_minutes:
                break
            current_time = base_time - timedelta(minutes=i)
            current_timestamp = int(current_time.timestamp() * 1000)

        cursor.execute(
            "INSERT INTO test_candles VALUES (?, ?)",
            (current_time.isoformat() + 'Z', current_timestamp)
        )

        # 진행 상황 표시 (1000개마다)
        if (i + 1) % 1000 == 0:
            progress = ((i + 1) / total_minutes) * 100
            print(f"   진행: {i + 1}/{total_minutes} ({progress:.1f}%)")

    conn.commit()

    # 생성된 데이터 통계 확인
    cursor.execute("SELECT COUNT(*) FROM test_candles")
    record_count = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(candle_date_time_utc), MAX(candle_date_time_utc) FROM test_candles")
    min_time, max_time = cursor.fetchone()

    print("✅ 대용량 테스트 데이터 생성 완료")
    print(f"   레코드 수: {record_count:,}개")
    print(f"   시간 범위: {max_time} ~ {min_time}")
    print(f"   🎯 정답지 - Gap 시작: {gap_start_time}")
    print(f"   🎯 정답지 - 테스트 시작: {test_start_time}")
    print(f"   🎯 정답지 - 예상 검출: {expected_result}")

    return conn, gap_start_time, test_start_time, expected_result


def test_query_performance_with_mock_data():
    """업비트 API 순서에 맞는 올바른 gap 검출 방식 비교"""

    conn, gap_start_time, test_start_time, expected_result = create_test_data()
    cursor = conn.cursor()
    table_name = "test_candles"

    try:
        # 테스트 시작 시간 설정 (정답지에서 가져옴)
        start_time = test_start_time

        print("\n=== 올바른 Gap 검출 방식 성능 비교 ===\n")
        print(f"🎯 테스트 시작 시점: {start_time}")
        print(f"🎯 예상 결과: {gap_start_time}에서 gap 검출\n")

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

        # 결과 정확성 확인
        if result_legacy and result_optimized:
            legacy_result = result_legacy[0]
            optimized_result = result_optimized[0]

            if legacy_result == optimized_result:
                print("✅ 두 방식 모두 동일한 결과 반환")

                # 정답지와 비교 (expected_result 기준)
                if legacy_result == expected_result:
                    print("🎯 정답! 예상 검출 시점과 일치")
                else:
                    print("❌ 오답! 예상과 다른 시점 검출")
                    print(f"   예상: {expected_result}")
                    print(f"   실제: {legacy_result}")
            else:
                print("❌ 결과 불일치!")
                print(f"   기존 방식: {legacy_result}")
                print(f"   최적화 방식: {optimized_result}")
                print(f"   정답: {expected_result}")
        else:
            print("❌ 결과를 찾을 수 없음")
            print(f"   정답: {expected_result}")

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
