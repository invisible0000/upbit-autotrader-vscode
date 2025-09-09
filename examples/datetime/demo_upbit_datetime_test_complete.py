#!/usr/bin/env python3
"""
업비트 API + SQLite 메모리 DB 교육용 테스트 스크립트

순차적 진행:
1. 업비트 API로 KRW-BTC 1분봉 200개 수집
2. 메모리 DB 저장 및 확인
3. Python datetime 기본 형식 예시
4. 업비트 지원 형식 예시
5. DB 검색 테스트 (다양한 형식)
"""

import sqlite3
import requests
import json
from datetime import datetime, timezone, timedelta
import time


def step1_fetch_upbit_data():
    """1단계: 업비트 API로 KRW-BTC 1분봉 200개 수집"""
    print("🚀 1단계: 업비트 API 데이터 수집")
    print("=" * 60)

    # 업비트 API 엔드포인트
    url = "https://api.upbit.com/v1/candles/minutes/1"
    params = {
        'market': 'KRW-BTC',
        'count': 200
    }

    print(f"📡 API 요청: {url}")
    print(f"📋 파라미터: {params}")

    try:
        # API 요청
        print("⏳ API 요청 중...")
        response = requests.get(url, params=params)
        response.raise_for_status()  # HTTP 에러 체크

        data = response.json()

        print(f"✅ API 응답 성공: {len(data)}개 캔들 수신")
        print("📊 첫 번째 캔들 샘플:")

        # 첫 번째 데이터 샘플 출력
        if data:
            sample = data[0]
            print(f"   market: {sample.get('market')}")
            print(f"   candle_date_time_utc: {sample.get('candle_date_time_utc')}")
            print(f"   candle_date_time_kst: {sample.get('candle_date_time_kst')}")
            print(f"   opening_price: {sample.get('opening_price')}")
            print(f"   high_price: {sample.get('high_price')}")
            print(f"   low_price: {sample.get('low_price')}")
            print(f"   trade_price: {sample.get('trade_price')}")
            print(f"   timestamp: {sample.get('timestamp')}")
            print(f"   candle_acc_trade_price: {sample.get('candle_acc_trade_price')}")
            print(f"   candle_acc_trade_volume: {sample.get('candle_acc_trade_volume')}")

        print("📅 시간 범위:")
        if len(data) >= 2:
            print(f"   최신: {data[0]['candle_date_time_utc']}")
            print(f"   최구: {data[-1]['candle_date_time_utc']}")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        return None


def step2_create_memory_db_and_save(candle_data):
    """2단계: 메모리 DB 생성 및 데이터 저장"""
    print("\n🗄️  2단계: 메모리 DB 생성 및 데이터 저장")
    print("=" * 60)

    # 메모리 DB 생성
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    print("📋 테이블 스키마 생성...")

    # 테이블 생성 (단순한 스키마)
    create_table_sql = """
    CREATE TABLE upbit_candles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market TEXT NOT NULL,
        candle_date_time_utc TEXT NOT NULL,
        candle_date_time_kst TEXT NOT NULL,
        opening_price REAL NOT NULL,
        high_price REAL NOT NULL,
        low_price REAL NOT NULL,
        trade_price REAL NOT NULL,
        timestamp INTEGER NOT NULL,
        candle_acc_trade_price REAL NOT NULL,
        candle_acc_trade_volume REAL NOT NULL
    )
    """

    cursor.execute(create_table_sql)
    print("✅ 테이블 생성 완료")

    # 데이터 삽입
    print(f"💾 {len(candle_data)}개 캔들 데이터 저장 중...")

    insert_sql = """
    INSERT INTO upbit_candles (
        market, candle_date_time_utc, candle_date_time_kst,
        opening_price, high_price, low_price, trade_price,
        timestamp, candle_acc_trade_price, candle_acc_trade_volume
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # 배치 삽입
    rows_to_insert = []
    for candle in candle_data:
        row = (
            candle['market'],
            candle['candle_date_time_utc'],
            candle['candle_date_time_kst'],
            candle['opening_price'],
            candle['high_price'],
            candle['low_price'],
            candle['trade_price'],
            candle['timestamp'],
            candle['candle_acc_trade_price'],
            candle['candle_acc_trade_volume']
        )
        rows_to_insert.append(row)

    cursor.executemany(insert_sql, rows_to_insert)
    conn.commit()

    # 저장 확인
    cursor.execute("SELECT COUNT(*) FROM upbit_candles")
    total_count = cursor.fetchone()[0]
    print(f"✅ 저장 완료: 총 {total_count}개")

    # 저장된 데이터 상위 5개 조회
    print("\n📊 저장된 데이터 상위 5개:")
    print(f"{'id':<3} | {'candle_date_time_utc':<19} | {'candle_date_time_kst':<19} | {'timestamp':<13}")
    print("-" * 70)

    cursor.execute("""
        SELECT id, candle_date_time_utc, candle_date_time_kst, timestamp
        FROM upbit_candles
        ORDER BY id
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(f"{row[0]:03d} | {row[1]:<19} | {row[2]:<19} | {row[3]:<13}")

    print("...")

    # 마지막 5개도 보여주기
    cursor.execute("""
        SELECT id, candle_date_time_utc, candle_date_time_kst, timestamp
        FROM upbit_candles
        ORDER BY id DESC
        LIMIT 5
    """)

    last_rows = cursor.fetchall()
    for row in reversed(last_rows):
        if row[0] > 5:  # 이미 위에서 출력된 것 제외
            print(f"{row[0]:03d} | {row[1]:<19} | {row[2]:<19} | {row[3]:<13}")

    return conn, cursor


def step3_python_datetime_examples():
    """3단계: Python datetime 기본 형식 예시"""
    print("\n🐍 3단계: Python datetime 기본 형식 예시")
    print("=" * 60)

    # 현재 시간 기준으로 다양한 형식 생성
    now_utc = datetime.now(timezone.utc)
    now_naive = datetime.now()
    specific_time = datetime(2025, 9, 8, 14, 30, 45)
    specific_time_utc = datetime(2025, 9, 8, 14, 30, 45, tzinfo=timezone.utc)

    print("📅 Python datetime 객체 생성 방법들:")
    print(f"   1. datetime.now(timezone.utc): {now_utc}")
    print(f"   2. datetime.now(): {now_naive}")
    print(f"   3. datetime(2025, 9, 8, 14, 30, 45): {specific_time}")
    print(f"   4. datetime(..., tzinfo=timezone.utc): {specific_time_utc}")

    print("\n🔄 Python datetime → 문자열 변환 방법들:")

    conversion_methods = [
        ("isoformat()", now_utc.isoformat()),
        ("isoformat() [naive]", now_naive.isoformat()),
        ("strftime('%Y-%m-%dT%H:%M:%S')", now_utc.strftime('%Y-%m-%dT%H:%M:%S')),
        ("strftime('%Y-%m-%d %H:%M:%S')", now_utc.strftime('%Y-%m-%d %H:%M:%S')),
        ("str(datetime)", str(now_utc)),
        ("repr(datetime)", repr(now_utc)),
    ]

    for desc, result in conversion_methods:
        print(f"   {desc:<30}: '{result}'")

    print("\n🔄 문자열 → Python datetime 변환:")

    test_strings = [
        "2025-09-08T14:30:45",
        "2025-09-08T14:30:45Z",
        "2025-09-08T14:30:45+00:00",
        "2025-09-08 14:30:45",
    ]

    for test_str in test_strings:
        try:
            if test_str.endswith('Z'):
                # Z는 직접 fromisoformat 불가, 변환 필요
                dt = datetime.fromisoformat(test_str.replace('Z', '+00:00'))
            elif ' ' in test_str:
                # 공백 포함은 strptime 사용
                dt = datetime.strptime(test_str, '%Y-%m-%d %H:%M:%S')
            else:
                dt = datetime.fromisoformat(test_str)

            print(f"   '{test_str}' → {dt} (tzinfo: {dt.tzinfo})")
        except Exception as e:
            print(f"   '{test_str}' → ❌ {e}")


def step4_upbit_supported_formats():
    """4단계: 업비트 지원 형식 예시"""
    print("\n🏢 4단계: 업비트 API 지원 datetime 형식 예시")
    print("=" * 60)

    print("📋 업비트 공식 문서에서 지원하는 형식들:")
    print("   (ISO 8601 형식의 datetime)")
    print()

    # 업비트 지원 형식들
    upbit_formats = [
        ("Z suffix (UTC)", "2025-06-24T04:56:53Z"),
        ("공백 구분 (시간대 없음)", "2025-06-24 04:56:53"),
        ("KST 시간대", "2025-06-24T13:56:53+09:00"),
        ("UTC 시간대", "2025-06-24T04:56:53+00:00"),
        ("다른 시간대 예시", "2025-06-24T12:56:53+08:00"),
    ]

    print("✅ 업비트 API에서 '뜨' 매개변수로 사용 가능한 형식들:")
    for desc, fmt in upbit_formats:
        print(f"   {desc:<25}: {fmt}")

    print("\n💡 주요 특징:")
    print("   - ISO 8601 표준 준수")
    print("   - 다양한 시간대 지원")
    print("   - URL 인코딩 필요 (실제 요청 시)")
    print("   - 미지정시 요청 시각 기준")

    # Python에서 업비트 형식 생성하는 방법
    print("\n🐍 Python에서 업비트 형식 생성:")

    now_utc = datetime.now(timezone.utc)
    kst = timezone(timedelta(hours=9))
    now_kst = now_utc.astimezone(kst)

    python_to_upbit = [
        ("UTC Z suffix", now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')),
        ("UTC +00:00", now_utc.isoformat()),
        ("KST +09:00", now_kst.isoformat()),
        ("공백 형식", now_utc.strftime('%Y-%m-%d %H:%M:%S')),
    ]

    for desc, fmt in python_to_upbit:
        print(f"   {desc:<15}: {fmt}")


def step5_db_search_tests(cursor):
    """5단계: DB 검색 테스트 (다양한 형식)"""
    print("\n🔍 5단계: DB 검색 테스트 (다양한 datetime 형식)")
    print("=" * 60)

    # DB에서 실제 데이터 범위 확인
    cursor.execute("""
        SELECT
            MIN(candle_date_time_utc) as min_time,
            MAX(candle_date_time_utc) as max_time,
            COUNT(*) as total_count
        FROM upbit_candles
    """)
    min_time, max_time, total_count = cursor.fetchone()

    print("📊 DB 데이터 현황:")
    print(f"   총 개수: {total_count}개")
    print(f"   시간 범위: {min_time} ~ {max_time}")

    # 테스트용 시간 범위 설정 (중간 구간)
    cursor.execute("""
        SELECT candle_date_time_utc
        FROM upbit_candles
        ORDER BY id
        LIMIT 5 OFFSET 10
    """)
    middle_times = [row[0] for row in cursor.fetchall()]

    test_start = middle_times[0]  # 11번째 데이터
    test_end = middle_times[4]    # 15번째 데이터

    print("\n🎯 테스트 범위 설정:")
    print(f"   시작: {test_start}")
    print(f"   종료: {test_end}")

    # 기준 쿼리 (문자열 직접 사용)
    cursor.execute("""
        SELECT COUNT(*) FROM upbit_candles
        WHERE candle_date_time_utc BETWEEN ? AND ?
    """, (test_start, test_end))
    baseline_count = cursor.fetchone()[0]

    print(f"   기준 결과: {baseline_count}개")

    print("\n⚡ 다양한 형식으로 검색 테스트:")

    # 1. 문자열 형식들
    print("\n   📝 1. 문자열 형식 테스트:")

    string_formats = [
        ("DB 원본 형식", test_start, test_end),
        ("Z suffix 추가", test_start + "Z", test_end + "Z"),
        ("공백으로 변경", test_start.replace('T', ' '), test_end.replace('T', ' ')),
        ("+00:00 추가", test_start + "+00:00", test_end + "+00:00"),
    ]

    for desc, start_fmt, end_fmt in string_formats:
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM upbit_candles
                WHERE candle_date_time_utc BETWEEN ? AND ?
            """, (start_fmt, end_fmt))
            count = cursor.fetchone()[0]
            match = "✅" if count == baseline_count else f"❌ ({count}개)"
            print(f"      {desc:<15}: {match}")
            if count != baseline_count:
                print(f"         사용된 형식: '{start_fmt}' ~ '{end_fmt}'")
        except Exception as e:
            print(f"      {desc:<15}: ❌ 에러 - {e}")

    # 2. Python datetime 객체들
    print("\n   🐍 2. Python datetime 객체 테스트:")

    # datetime 객체 생성
    dt_start_naive = datetime.fromisoformat(test_start)
    dt_end_naive = datetime.fromisoformat(test_end)
    dt_start_utc = dt_start_naive.replace(tzinfo=timezone.utc)
    dt_end_utc = dt_end_naive.replace(tzinfo=timezone.utc)

    datetime_tests = [
        ("naive datetime", dt_start_naive, dt_end_naive),
        ("UTC datetime", dt_start_utc, dt_end_utc),
        ("str(datetime)", str(dt_start_naive), str(dt_end_naive)),
    ]

    for desc, start_dt, end_dt in datetime_tests:
        try:
            # ⚠️  DeprecationWarning 발생 지점:
            # Python 3.12부터 SQLite의 기본 datetime adapter가 deprecated됨
            # datetime 객체를 직접 SQL 파라미터로 사용할 때 경고 발생
            # 권장: datetime 객체 대신 문자열 사용 (str(datetime_obj) 또는 strftime())
            cursor.execute("""
                SELECT COUNT(*) FROM upbit_candles
                WHERE candle_date_time_utc BETWEEN ? AND ?
            """, (start_dt, end_dt))
            count = cursor.fetchone()[0]
            match = "✅" if count == baseline_count else f"❌ ({count}개)"
            print(f"      {desc:<15}: {match}")
            if count != baseline_count:
                print(f"         SQLite 변환값: '{start_dt}' ~ '{end_dt}'")
        except Exception as e:
            print(f"      {desc:<15}: ❌ 에러 - {e}")

    # 3. 변환 함수 테스트
    print("\n   🔧 3. 변환 함수 테스트:")

    def to_db_format(dt_str):
        """업비트 형식 → DB 형식 변환"""
        if dt_str.endswith('Z'):
            return dt_str.replace('Z', '')
        elif '+' in dt_str:
            return dt_str.split('+')[0]
        elif ' ' in dt_str:
            return dt_str.replace(' ', 'T')
        return dt_str

    def from_db_format(db_str):
        """DB 형식 → datetime 객체"""
        return datetime.fromisoformat(db_str)

    # 업비트 다양한 형식으로 테스트
    upbit_test_formats = [
        test_start + "Z",
        test_start + "+00:00",
        test_start.replace('T', ' '),
        test_start + "+09:00",
    ]

    for upbit_fmt in upbit_test_formats:
        try:
            converted = to_db_format(upbit_fmt)
            cursor.execute("""
                SELECT COUNT(*) FROM upbit_candles
                WHERE candle_date_time_utc = ?
            """, (converted,))
            count = cursor.fetchone()[0]
            match = "✅" if count > 0 else "❌"
            print(f"      '{upbit_fmt}' → '{converted}': {match} ({count}개)")
        except Exception as e:
            print(f"      '{upbit_fmt}': ❌ {e}")

    # 4. 성능 비교
    print("\n   ⏱️  4. 성능 비교 (1000회 반복):")

    performance_tests = [
        ("문자열 직접", test_start, test_end),
        ("변환 함수 사용", to_db_format(test_start + "Z"), to_db_format(test_end + "Z")),
        ("datetime 객체", dt_start_naive, dt_end_naive),
    ]

    for desc, start_param, end_param in performance_tests:
        try:
            start_time = time.time()
            for _ in range(1000):
                # ⚠️  DeprecationWarning 발생 지점 (datetime 객체 사용시):
                # 해결책: datetime 객체 대신 문자열 변환하여 사용
                # 예) str(datetime_obj) 또는 datetime_obj.strftime('%Y-%m-%dT%H:%M:%S')
                cursor.execute("""
                    SELECT COUNT(*) FROM upbit_candles
                    WHERE candle_date_time_utc BETWEEN ? AND ?
                """, (start_param, end_param))
                cursor.fetchone()

            elapsed = (time.time() - start_time) * 1000
            print(f"      {desc:<15}: {elapsed:.2f}ms")
        except Exception as e:
            print(f"      {desc:<15}: ❌ {e}")


def step6_deprecation_warning_solution():
    """6단계: DeprecationWarning 해결 방법 및 권장 패턴"""
    print("\n⚠️  6단계: DeprecationWarning 해결 방법")
    print("=" * 60)

    print("📋 Python 3.12 DeprecationWarning 설명:")
    print("   - SQLite의 기본 datetime adapter가 deprecated됨")
    print("   - datetime 객체를 SQL 파라미터로 직접 사용하면 경고 발생")
    print("   - 이유: 암묵적 변환이 예측하기 어려워 버그 유발 가능")
    print("   - 해결: 명시적으로 문자열 변환 후 사용")

    # 메모리 DB 생성 (테스트용)
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # 간단한 테스트 테이블
    cursor.execute("""
        CREATE TABLE test_times (
            id INTEGER PRIMARY KEY,
            time_str TEXT,
            created_at TEXT
        )
    """)

    # 테스트 데이터 삽입
    test_data = [
        (1, "2025-09-09T10:00:00", "2025-09-09T10:00:00"),
        (2, "2025-09-09T10:01:00", "2025-09-09T10:01:00"),
        (3, "2025-09-09T10:02:00", "2025-09-09T10:02:00"),
    ]

    cursor.executemany("INSERT INTO test_times VALUES (?, ?, ?)", test_data)

    print("\n❌ 문제가 되는 방식 (DeprecationWarning 발생):")

    # 문제가 되는 방식: datetime 객체 직접 사용
    dt_start = datetime(2025, 9, 9, 10, 0, 0)
    dt_end = datetime(2025, 9, 9, 10, 2, 0)

    print(f"   datetime 객체: {dt_start} ~ {dt_end}")
    print("   cursor.execute('SELECT * WHERE time BETWEEN ? AND ?', (datetime_obj, datetime_obj))")
    print("   → DeprecationWarning 발생!")

    print("\n✅ 권장하는 방식들:")    # 방법 1: strftime 사용
    start_str1 = dt_start.strftime('%Y-%m-%dT%H:%M:%S')
    end_str1 = dt_end.strftime('%Y-%m-%dT%H:%M:%S')

    cursor.execute("""
        SELECT COUNT(*) FROM test_times
        WHERE created_at BETWEEN ? AND ?
    """, (start_str1, end_str1))
    count1 = cursor.fetchone()[0]

    print("   방법 1 - strftime() 사용:")
    print("      start_str = dt.strftime('%Y-%m-%dT%H:%M:%S')")
    print(f"      결과: '{start_str1}' ~ '{end_str1}' → {count1}개")

    # 방법 2: str() 사용
    start_str2 = str(dt_start).replace(' ', 'T')
    end_str2 = str(dt_end).replace(' ', 'T')

    cursor.execute("""
        SELECT COUNT(*) FROM test_times
        WHERE created_at BETWEEN ? AND ?
    """, (start_str2, end_str2))
    count2 = cursor.fetchone()[0]

    print("   방법 2 - str() + replace 사용:")
    print("      start_str = str(dt).replace(' ', 'T')")
    print(f"      결과: '{start_str2}' ~ '{end_str2}' → {count2}개")

    # 방법 3: isoformat() 사용 (권장)
    start_str3 = dt_start.isoformat()
    end_str3 = dt_end.isoformat()

    cursor.execute("""
        SELECT COUNT(*) FROM test_times
        WHERE created_at BETWEEN ? AND ?
    """, (start_str3, end_str3))
    count3 = cursor.fetchone()[0]

    print("   방법 3 - isoformat() 사용 (가장 권장):")
    print("      start_str = dt.isoformat()")
    print(f"      결과: '{start_str3}' ~ '{end_str3}' → {count3}개")

    # 방법 4: 처음부터 문자열 사용 (최고 권장)
    print("   방법 4 - 처음부터 문자열 사용 (최고 성능):")
    print("      time_str = '2025-09-09T10:00:00'  # datetime 객체 생성 안함")
    print("      → 변환 비용 없음, 경고 없음, 최고 성능")

    conn.close()

    print("\n💡 권장 패턴:")
    print("   1. DB 저장/검색: 문자열 직접 사용")
    print("   2. 시간 연산 필요시: datetime 변환 → 계산 → isoformat()")
    print("   3. API 통신: 문자열 형식 변환만")
    print("   4. SQLite 파라미터: 항상 문자열만 전달")


def main():
    """메인 실행 함수"""
    print("🎓 업비트 API + SQLite DateTime 교육용 테스트")
    print("=" * 70)
    print("📚 학습 목표:")
    print("   - 업비트 API 실제 데이터 수집")
    print("   - SQLite 메모리 DB 활용")
    print("   - Python datetime 다양한 형식 이해")
    print("   - 업비트 API datetime 형식 지원 범위")
    print("   - DB 검색에서 작동하는 형식 확인")
    print("   - DeprecationWarning 해결 방법")
    print()

    # 1단계: API 데이터 수집
    candle_data = step1_fetch_upbit_data()
    if not candle_data:
        print("❌ API 데이터 수집 실패. 테스트 중단.")
        return

    # 2단계: DB 저장
    conn, cursor = step2_create_memory_db_and_save(candle_data)

    # 3단계: Python datetime 예시
    step3_python_datetime_examples()

    # 4단계: 업비트 형식 예시
    step4_upbit_supported_formats()

    # 5단계: DB 검색 테스트
    step5_db_search_tests(cursor)

    # 6단계: DeprecationWarning 해결 방법
    step6_deprecation_warning_solution()

    # 정리
    print("\n🎯 최종 결론:")
    print("   ✅ 업비트 API: 다양한 datetime 형식 지원")
    print("   ✅ SQLite DB: 문자열 형식이 가장 안정적")
    print("   ✅ 성능: 문자열 직접 사용이 가장 빠름")
    print("   ✅ Python 3.12: datetime 객체 대신 문자열 사용")
    print("   💡 권장: 내부적으로 문자열 사용, 필요시에만 datetime 변환")

    conn.close()
    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()
