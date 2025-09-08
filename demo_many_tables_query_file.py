"""
순수 DB 성능 테스트 - 실제 파일 DB로 5000+ 테이블 생성 후 직접 쿼리 성능 측정
"""
import time
import sqlite3
import random
import requests
import os
from datetime import datetime, timedelta
from typing import List


def test_db_table_scaling():
    """업비트 모든 마켓에 대해 대량 테이블 생성 후 순수 DB 성능 측정 (실제 파일 DB)"""

    print("🔥 순수 DB 테이블 스케일링 테스트 시작 (실제 파일 DB)\n")

    # 실제 DB 파일 사용
    db_path = "test_scaling_performance.sqlite3"

    # 기존 테스트 DB 파일이 있으면 삭제
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"   🗑️  기존 테스트 DB 파일 삭제: {db_path}")

    try:
        # 1단계: 기준 성능 측정 (빈 DB)
        print("📊 1단계: 기준 성능 측정 (빈 파일 DB)")
        baseline_time = measure_baseline_query_performance(db_path)
        print(f"   기준 쿼리 시간: {baseline_time:.3f}ms")

        # 2단계: 업비트 모든 마켓 조회 (API 직접 호출)
        print("\n📊 2단계: 업비트 마켓 조회 (API 직접 호출)")
        markets = get_all_upbit_markets_direct()
        all_markets = [m['market'] for m in markets]
        krw_markets = [m for m in all_markets if m.startswith('KRW-')]
        btc_markets = [m for m in all_markets if m.startswith('BTC-')]
        usdt_markets = [m for m in all_markets if m.startswith('USDT-')]

        print(f"   총 마켓 수: {len(all_markets)}개")
        print(f"   KRW 마켓: {len(krw_markets)}개")
        print(f"   BTC 마켓: {len(btc_markets)}개")
        print(f"   USDT 마켓: {len(usdt_markets)}개")

        # 3단계: 모든 마켓 × 모든 타임프레임으로 테이블 생성
        print("\n📊 3단계: 대량 테이블 생성")
        timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]

        total_tables_to_create = len(all_markets) * len(timeframes)
        print(f"   생성할 테이블 수: {total_tables_to_create}개 ({len(all_markets)} 마켓 × {len(timeframes)} 타임프레임)")

        # 테이블 생성 실행
        conn = sqlite3.connect(db_path)
        created_count = create_all_market_tables(conn, all_markets, timeframes)
        print(f"   실제 생성된 테이블: {created_count}개")

        # 파일 크기 확인
        file_size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"   DB 파일 크기: {file_size_mb:.2f} MB")

        # 4단계: 메타데이터 쿼리 성능 측정
        print("\n📊 4단계: 메타데이터 쿼리 성능 측정")
        measure_metadata_query_performance(conn)

        # 5단계: 데이터 쿼리 성능 측정
        print("\n📊 5단계: 데이터 쿼리 성능 측정")
        measure_data_query_performance(conn)

        # 6단계: 복잡한 쿼리 성능 측정
        print("\n📊 6단계: 복잡한 쿼리 성능 측정")
        measure_complex_query_performance(conn)

        # 7단계: DB 동기화 성능 측정
        print("\n📊 7단계: DB 동기화 성능 측정")
        measure_sync_performance(conn)

        # 8단계: 확장된 환경에서 기준 쿼리 재측정
        print("\n📊 8단계: 대량 테이블 환경에서 기준 쿼리 재측정")
        scaled_time = measure_baseline_query_performance_on_db(conn)
        print(f"   확장 환경 쿼리 시간: {scaled_time:.3f}ms")

        # 9단계: 성능 분석
        print("\n📊 9단계: 성능 분석")
        analyze_performance_impact(baseline_time, scaled_time, 0, created_count)

        # 연결 종료
        conn.close()

        # 최종 파일 크기 확인
        final_file_size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print("\n📁 최종 DB 파일 정보:")
        print(f"   파일 경로: {os.path.abspath(db_path)}")
        print(f"   파일 크기: {final_file_size_mb:.2f} MB")
        print(f"   테이블 수: {created_count}개")

    finally:
        # 10단계: 테스트 DB 파일 정리
        print("\n📊 10단계: 테스트 DB 파일 정리")
        cleanup_test_db(db_path)


def get_all_upbit_markets_direct() -> List:
    """업비트 API 직접 호출하여 모든 마켓 조회"""
    try:
        response = requests.get("https://api.upbit.com/v1/market/all", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"   ❌ API 호출 실패: {e}")
        # 실패 시 더미 데이터 반환
        return [
            {"market": "KRW-BTC"}, {"market": "KRW-ETH"}, {"market": "KRW-XRP"},
            {"market": "BTC-ETH"}, {"market": "USDT-BTC"}
        ]


def create_all_market_tables(conn: sqlite3.Connection, markets: List[str], timeframes: List[str]) -> int:
    """모든 마켓과 타임프레임 조합으로 테이블 생성"""
    created_count = 0
    cursor = conn.cursor()

    print(f"   시작: {len(markets)} 마켓 × {len(timeframes)} 타임프레임")

    for i, market in enumerate(markets):
        if i % 50 == 0:
            print(f"   진행률: {i + 1}/{len(markets)} - {market}")

        for timeframe in timeframes:
            try:
                table_name = f"candles_{market.replace('-', '_')}_{timeframe}"

                # 표준화된 캔들 테이블 생성
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        candle_date_time_utc TEXT NOT NULL PRIMARY KEY,
                        market TEXT NOT NULL,
                        candle_date_time_kst TEXT NOT NULL,
                        opening_price REAL NOT NULL,
                        high_price REAL NOT NULL,
                        low_price REAL NOT NULL,
                        trade_price REAL NOT NULL,
                        timestamp INTEGER NOT NULL,
                        candle_acc_trade_price REAL NOT NULL,
                        candle_acc_trade_volume REAL NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 샘플 데이터 삽입 (3개만)
                insert_sample_candle_data(cursor, table_name, market)
                created_count += 1

            except Exception as e:
                print(f"      ⚠️  {market} {timeframe} 실패: {e}")

    conn.commit()
    print(f"   ✅ 총 {created_count}개 테이블 생성 완료")
    return created_count


def insert_sample_candle_data(cursor: sqlite3.Cursor, table_name: str, market: str):
    """가상의 캔들 데이터 삽입"""
    base_time = datetime.now()
    base_price = random.uniform(1000, 100000)

    for i in range(3):  # 3개만 삽입
        candle_time = base_time - timedelta(minutes=i)

        # 간단한 가격 변동
        price_variation = random.uniform(0.98, 1.02)
        opening_price = base_price * price_variation
        high_price = opening_price * random.uniform(1.0, 1.01)
        low_price = opening_price * random.uniform(0.99, 1.0)
        trade_price = random.uniform(low_price, high_price)

        cursor.execute(f"""
            INSERT OR IGNORE INTO {table_name}
            (candle_date_time_utc, market, candle_date_time_kst, opening_price,
             high_price, low_price, trade_price, timestamp,
             candle_acc_trade_price, candle_acc_trade_volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            candle_time.strftime('%Y-%m-%dT%H:%M:%S'),
            market,
            candle_time.strftime('%Y-%m-%dT%H:%M:%S'),
            opening_price,
            high_price,
            low_price,
            trade_price,
            int(candle_time.timestamp() * 1000),
            trade_price * random.uniform(100, 1000),  # 거래대금
            random.uniform(1, 100)  # 거래량
        ))


def measure_baseline_query_performance(db_path: str) -> float:
    """기준 쿼리 성능 측정 (빈 DB)"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 간단한 메타데이터 쿼리
    start_time = time.perf_counter()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    cursor.fetchall()
    query_time = (time.perf_counter() - start_time) * 1000

    conn.close()
    return query_time


def measure_baseline_query_performance_on_db(conn: sqlite3.Connection) -> float:
    """기존 DB에서 기준 쿼리 성능 측정"""
    cursor = conn.cursor()

    start_time = time.perf_counter()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 10")
    cursor.fetchall()
    query_time = (time.perf_counter() - start_time) * 1000

    return query_time


def measure_metadata_query_performance(conn: sqlite3.Connection):
    """메타데이터 쿼리 성능 측정"""
    cursor = conn.cursor()

    # 1. 전체 테이블 목록 조회
    times = []
    tables_count = 0
    for i in range(10):
        start_time = time.perf_counter()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        tables_count = len(tables)
        query_time = (time.perf_counter() - start_time) * 1000
        times.append(query_time)

    avg_time = sum(times) / len(times)
    print(f"   전체 테이블 목록 조회 ({tables_count}개 테이블):")
    print(f"      평균: {avg_time:.2f}ms, 범위: {min(times):.2f}-{max(times):.2f}ms")

    # 2. 캔들 테이블만 조회
    times = []
    candle_tables_count = 0
    for i in range(10):
        start_time = time.perf_counter()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'candles_%'")
        candle_tables = cursor.fetchall()
        candle_tables_count = len(candle_tables)
        query_time = (time.perf_counter() - start_time) * 1000
        times.append(query_time)

    avg_time = sum(times) / len(times)
    print(f"   캔들 테이블만 조회 ({candle_tables_count}개 테이블):")
    print(f"      평균: {avg_time:.2f}ms, 범위: {min(times):.2f}-{max(times):.2f}ms")

    # 3. 특정 테이블 존재 확인
    times = []
    test_table = "candles_KRW_BTC_1m"
    for i in range(100):
        start_time = time.perf_counter()
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (test_table,))
        cursor.fetchone()
        query_time = (time.perf_counter() - start_time) * 1000
        times.append(query_time)

    avg_time = sum(times) / len(times)
    print("   테이블 존재 확인 (100회):")
    print(f"      평균: {avg_time:.3f}ms")


def measure_data_query_performance(conn: sqlite3.Connection):
    """데이터 쿼리 성능 측정"""
    cursor = conn.cursor()

    # 1. 단일 테이블 데이터 조회
    table_name = "candles_KRW_BTC_1m"
    times = []
    rows_count = 0
    for i in range(20):
        start_time = time.perf_counter()
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY candle_date_time_utc DESC LIMIT 5")
        rows = cursor.fetchall()
        rows_count = len(rows)
        query_time = (time.perf_counter() - start_time) * 1000
        times.append(query_time)

    avg_time = sum(times) / len(times)
    print(f"   단일 테이블 데이터 조회 ({rows_count}개 레코드):")
    print(f"      평균: {avg_time:.3f}ms")

    # 2. COUNT 쿼리
    times = []
    record_count = 0
    for i in range(10):
        start_time = time.perf_counter()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        record_count = cursor.fetchone()[0]
        query_time = (time.perf_counter() - start_time) * 1000
        times.append(query_time)

    avg_time = sum(times) / len(times)
    print(f"   COUNT 쿼리 ({record_count}개 레코드):")
    print(f"      평균: {avg_time:.3f}ms")


def measure_complex_query_performance(conn: sqlite3.Connection):
    """복잡한 쿼리 성능 측정"""
    cursor = conn.cursor()

    # 1. 여러 테이블 존재 확인
    test_tables = [
        "candles_KRW_BTC_1m", "candles_KRW_ETH_1m", "candles_KRW_XRP_1m",
        "candles_BTC_ETH_1h", "candles_USDT_BTC_1d"
    ]

    times = []
    existing_count = 0
    for i in range(10):
        start_time = time.perf_counter()
        placeholders = ','.join(['?' for _ in test_tables])
        cursor.execute(f"""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ({placeholders})
        """, test_tables)
        existing_tables = cursor.fetchall()
        existing_count = len(existing_tables)
        query_time = (time.perf_counter() - start_time) * 1000
        times.append(query_time)

    avg_time = sum(times) / len(times)
    print(f"   복수 테이블 존재 확인 ({existing_count}/{len(test_tables)}개):")
    print(f"      평균: {avg_time:.3f}ms")

    # 2. 테이블별 레코드 수 집계
    start_time = time.perf_counter()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'candles_KRW_%_1m'
        LIMIT 10
    """)
    krw_1m_tables = cursor.fetchall()

    total_records = 0
    for table_row in krw_1m_tables:
        table_name = table_row[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        total_records += count

    query_time = (time.perf_counter() - start_time) * 1000
    print(f"   KRW 1분봉 테이블 집계 ({len(krw_1m_tables)}개 테이블, {total_records}개 레코드):")
    print(f"      총 시간: {query_time:.2f}ms")


def measure_sync_performance(conn: sqlite3.Connection):
    """DB 동기화 성능 측정 (파일 DB 전용)"""
    cursor = conn.cursor()

    # 1. 수동 COMMIT 성능
    start_time = time.perf_counter()
    cursor.execute("BEGIN TRANSACTION")
    cursor.execute("CREATE TEMP TABLE test_sync_table (id INTEGER, data TEXT)")
    cursor.execute("INSERT INTO test_sync_table VALUES (1, 'test')")
    cursor.execute("COMMIT")
    sync_time = (time.perf_counter() - start_time) * 1000

    print(f"   수동 트랜잭션 COMMIT: {sync_time:.3f}ms")

    # 2. PRAGMA synchronous 설정 확인
    cursor.execute("PRAGMA synchronous")
    sync_mode = cursor.fetchone()[0]
    sync_modes = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}
    print(f"   동기화 모드: {sync_modes.get(sync_mode, sync_mode)}")

    # 3. VACUUM 성능 (소규모)
    start_time = time.perf_counter()
    cursor.execute("VACUUM")
    vacuum_time = (time.perf_counter() - start_time) * 1000
    print(f"   VACUUM 실행: {vacuum_time:.2f}ms")

    # 4. 페이지 캐시 정보
    cursor.execute("PRAGMA cache_size")
    cache_size = cursor.fetchone()[0]
    print(f"   페이지 캐시 크기: {cache_size}개 페이지")


def cleanup_test_db(db_path: str):
    """테스트 DB 파일 정리"""
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"   ✅ 테스트 DB 파일 삭제 완료: {db_path}")
        else:
            print(f"   ⚠️  테스트 DB 파일이 존재하지 않음: {db_path}")
    except Exception as e:
        print(f"   ❌ 테스트 DB 파일 삭제 실패: {e}")


def analyze_performance_impact(baseline: float, scaled: float, initial_tables: int, final_tables: int):
    """성능 영향 분석"""
    if baseline > 0:
        percent_change = ((scaled - baseline) / baseline) * 100
    else:
        percent_change = 0

    print(f"   기준 시간: {baseline:.3f}ms ({initial_tables}개 테이블)")
    print(f"   확장 시간: {scaled:.3f}ms ({final_tables}개 테이블)")
    print(f"   성능 변화: {scaled - baseline:+.3f}ms ({percent_change:+.1f}%)")
    print(f"   테이블 증가: +{final_tables - initial_tables}개")

    if abs(percent_change) < 10:
        print("   ✅ 성능 영향 미미 (10% 이하)")
        scale_rating = "우수"
    elif abs(percent_change) < 25:
        print("   ⚠️  경미한 성능 변화 (10-25%)")
        scale_rating = "양호"
    elif abs(percent_change) < 50:
        print("   ⚠️  중간 성능 변화 (25-50%)")
        scale_rating = "보통"
    else:
        print("   ❌ 유의미한 성능 변화 (50% 이상)")
        scale_rating = "개선 필요"

    print(f"   대량 테이블 확장성: {scale_rating}")

    # 예상 성능 추정
    if final_tables > 0:
        per_table_impact = percent_change / final_tables
        projected_10k = baseline * (1 + (per_table_impact * 10000 / 100))
        print(f"   10,000개 테이블 예상: {projected_10k:.3f}ms")


if __name__ == "__main__":
    test_db_table_scaling()
