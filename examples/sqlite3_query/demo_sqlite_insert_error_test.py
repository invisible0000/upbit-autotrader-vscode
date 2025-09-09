#!/usr/bin/env python3
"""
SQLite INSERT 에러 테스트

테이블이 없을 때 INSERT 문에서 발생하는 에러를 확인합니다.
"""

import sqlite3
import tempfile
import os


def test_insert_without_table():
    """존재하지 않는 테이블에 INSERT 시 에러 확인"""
    print("🧪 SQLite INSERT 에러 테스트")
    print("=" * 50)

    # 임시 SQLite 파일 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3') as temp_file:
        temp_db_path = temp_file.name

    try:
        conn = sqlite3.connect(temp_db_path)

        # 1. 존재하지 않는 테이블에 INSERT 시도
        print("\n1. 존재하지 않는 테이블에 INSERT 시도:")
        print("   INSERT INTO nonexistent_table (id, name) VALUES (1, 'test')")

        try:
            conn.execute("INSERT INTO nonexistent_table (id, name) VALUES (?, ?)", (1, 'test'))
            print("   결과: 성공 (예상치 못함)")
        except sqlite3.OperationalError as e:
            print(f"   결과: OperationalError 발생")
            print(f"   에러 메시지: {e}")
            print(f"   에러 타입: {type(e).__name__}")

        # 2. 잘못된 컬럼에 INSERT 시도 (테이블은 존재)
        print("\n2. 테이블 생성 후 잘못된 컬럼에 INSERT:")
        conn.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")

        try:
            conn.execute("INSERT INTO test_table (id, wrong_column) VALUES (?, ?)", (1, 'test'))
            print("   결과: 성공 (예상치 못함)")
        except sqlite3.OperationalError as e:
            print(f"   결과: OperationalError 발생")
            print(f"   에러 메시지: {e}")

        # 3. 복잡한 INSERT 에러 (여러 컬럼)
        print("\n3. 복잡한 INSERT 에러 테스트:")
        table_name = "candles_KRW_BTC_1m"

        insert_sql = f"""
        INSERT OR IGNORE INTO {table_name} (
            candle_date_time_utc, market, candle_date_time_kst,
            opening_price, high_price, low_price, trade_price,
            timestamp, candle_acc_trade_price, candle_acc_trade_volume
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:
            conn.execute(insert_sql, (
                "2025-09-09T10:00:00", "KRW-BTC", "2025-09-09T19:00:00",
                100000000, 100100000, 99900000, 100050000,
                1725879600, 1000000000, 10.5
            ))
            print("   결과: 성공 (예상치 못함)")
        except sqlite3.OperationalError as e:
            print(f"   결과: OperationalError 발생")
            print(f"   에러 메시지: {e}")
            print(f"   에러 길이: {len(str(e))}자")

        # 4. 에러 메시지 패턴 분석
        print("\n4. 에러 메시지 패턴 분석:")

        error_patterns = [
            "nonexistent_table_1",
            "VERY_LONG_TABLE_NAME_WITH_MANY_CHARACTERS_candles_KRW_BTC_1m",
            "candles_KRW_BTC_1m"
        ]

        for table in error_patterns:
            try:
                conn.execute(f"INSERT INTO {table} (col) VALUES (?)", ('test',))
            except sqlite3.OperationalError as e:
                print(f"   {table}: {e}")

        conn.close()

    finally:
        # 임시 파일 정리
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_error_detection():
    """에러 감지 및 처리 방법 테스트"""
    print("\n🔧 에러 감지 및 처리 방법")
    print("=" * 50)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3') as temp_file:
        temp_db_path = temp_file.name

    try:
        conn = sqlite3.connect(temp_db_path)

        # 1. 에러 메시지로 테이블 부재 감지
        print("\n1. 에러 메시지 패턴 감지:")

        def is_table_not_found_error(error_msg: str) -> bool:
            """테이블 부재 에러인지 판단"""
            patterns = [
                "no such table",
                "table",
                "does not exist"
            ]
            error_lower = str(error_msg).lower()
            return any(pattern in error_lower for pattern in patterns)

        try:
            conn.execute("INSERT INTO missing_table (id) VALUES (1)")
        except sqlite3.OperationalError as e:
            print(f"   에러 메시지: {e}")
            print(f"   테이블 부재 에러 감지: {is_table_not_found_error(str(e))}")

        # 2. 자동 복구 시뮬레이션
        print("\n2. 자동 복구 시뮬레이션:")

        def safe_insert_with_auto_create(conn, table_name, data):
            """INSERT 실패 시 자동으로 테이블 생성 후 재시도"""
            insert_sql = f"INSERT INTO {table_name} (id, name) VALUES (?, ?)"

            try:
                # 첫 번째 시도
                conn.execute(insert_sql, data)
                print(f"   ✅ INSERT 성공: {table_name}")
                return True

            except sqlite3.OperationalError as e:
                if is_table_not_found_error(str(e)):
                    print(f"   ⚠️ 테이블 없음 감지: {table_name}")

                    # 테이블 생성
                    create_sql = f"""
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY,
                        name TEXT
                    )
                    """
                    conn.execute(create_sql)
                    print(f"   🔧 테이블 생성 완료: {table_name}")

                    # 재시도
                    conn.execute(insert_sql, data)
                    print(f"   ✅ INSERT 재시도 성공: {table_name}")
                    return True
                else:
                    print(f"   ❌ 다른 에러: {e}")
                    return False

        # 테스트 실행
        success = safe_insert_with_auto_create(conn, "auto_created_table", (1, "test"))
        print(f"   자동 복구 결과: {success}")

        conn.close()

    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


def test_performance_comparison():
    """성능 비교: 사전 확인 vs 에러 기반 처리"""
    print("\n⚡ 성능 비교 테스트")
    print("=" * 50)

    import time

    with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3') as temp_file:
        temp_db_path = temp_file.name

    try:
        conn = sqlite3.connect(temp_db_path)

        # 테이블 생성
        conn.execute("""
            CREATE TABLE perf_test (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        """)

        iterations = 1000

        # 1. 매번 table_exists 확인 방식
        print(f"\n1. 매번 table_exists 확인 ({iterations}회):")

        start_time = time.time()
        for i in range(iterations):
            # table_exists 확인
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, ("perf_test",))
            exists = cursor.fetchone() is not None

            if exists:
                conn.execute("INSERT INTO perf_test (data) VALUES (?)", (f"data_{i}",))

        table_check_time = (time.time() - start_time) * 1000
        print(f"   소요 시간: {table_check_time:.2f}ms")

        # 데이터 정리
        conn.execute("DELETE FROM perf_test")

        # 2. 직접 INSERT 방식
        print(f"\n2. 직접 INSERT ({iterations}회):")

        start_time = time.time()
        for i in range(iterations):
            try:
                conn.execute("INSERT INTO perf_test (data) VALUES (?)", (f"data_{i}",))
            except sqlite3.OperationalError:
                # 실제로는 여기서 테이블 생성하겠지만, 테스트에서는 건너뜀
                pass

        direct_insert_time = (time.time() - start_time) * 1000
        print(f"   소요 시간: {direct_insert_time:.2f}ms")

        # 성능 비교
        improvement = ((table_check_time - direct_insert_time) / table_check_time) * 100
        print(f"\n📊 성능 비교:")
        print(f"   table_exists 확인: {table_check_time:.2f}ms")
        print(f"   직접 INSERT:       {direct_insert_time:.2f}ms")
        print(f"   성능 향상:          {improvement:.1f}%")

        conn.close()

    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


if __name__ == "__main__":
    test_insert_without_table()
    test_error_detection()
    test_performance_comparison()
