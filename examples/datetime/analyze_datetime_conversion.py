#!/usr/bin/env python3
"""
_from_utc_iso() 함수 동작 분석
naive datetime vs timezone-aware datetime 변환 과정 확인
"""

from datetime import datetime, timezone
import sqlite3
import os


def _from_utc_iso(iso_str: str) -> datetime:
    """Repository의 _from_utc_iso 함수 (동일한 로직)"""
    # 업비트 API 'Z' suffix 지원
    if iso_str.endswith('Z'):
        iso_str = iso_str.replace('Z', '')

    # DB는 timezone 정보 없이 저장되므로 naive datetime으로 파싱
    dt_naive = datetime.fromisoformat(iso_str)
    # UTC timezone 명시적 설정
    return dt_naive.replace(tzinfo=timezone.utc)


def analyze_naive_vs_aware():
    """naive datetime vs timezone-aware datetime 분석"""

    print("🔍 naive vs timezone-aware datetime 분석")
    print("=" * 60)

    # 1. DB에서 실제 데이터 가져오기
    db_path = "data/market_data.sqlite3"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'candles_%'")
            table_name = cursor.fetchall()[0][0]

            cursor.execute(f"SELECT candle_date_time_utc FROM {table_name} ORDER BY candle_date_time_utc DESC LIMIT 3")
            db_samples = [row[0] for row in cursor.fetchall()]

            conn.close()

            print(f"📋 DB 테이블: {table_name}")
            print(f"📅 DB 샘플 데이터:")
            for i, sample in enumerate(db_samples, 1):
                print(f"   {i}. '{sample}' (타입: {type(sample).__name__})")

        except Exception as e:
            print(f"❌ DB 읽기 실패: {e}")
            db_samples = ["2025-09-08T14:12:00", "2025-09-08T14:13:00", "2025-09-08T14:14:00"]
            print("📋 샘플 데이터로 테스트:")
            for i, sample in enumerate(db_samples, 1):
                print(f"   {i}. '{sample}'")
    else:
        db_samples = ["2025-09-08T14:12:00", "2025-09-08T14:13:00", "2025-09-08T14:14:00"]
        print("📋 샘플 데이터로 테스트:")
        for i, sample in enumerate(db_samples, 1):
            print(f"   {i}. '{sample}'")

    print("\n" + "=" * 60)

    # 2. 각 단계별 변환 과정 분석
    for i, db_time_str in enumerate(db_samples, 1):
        print(f"\n🔄 {i}번째 데이터 변환 과정: '{db_time_str}'")
        print("-" * 50)

        # Step 1: 원본 DB 문자열
        print(f"📥 Step 1 - DB 원본:")
        print(f"   값: '{db_time_str}'")
        print(f"   타입: {type(db_time_str).__name__}")

        # Step 2: Z suffix 처리 (있다면)
        processed_str = db_time_str
        if db_time_str.endswith('Z'):
            processed_str = db_time_str.replace('Z', '')
            print(f"📝 Step 2 - Z suffix 제거:")
            print(f"   변환 전: '{db_time_str}'")
            print(f"   변환 후: '{processed_str}'")
        else:
            print(f"📝 Step 2 - Z suffix 없음, 그대로 유지:")
            print(f"   값: '{processed_str}'")

        # Step 3: naive datetime 생성
        dt_naive = datetime.fromisoformat(processed_str)
        print(f"🔧 Step 3 - naive datetime 생성:")
        print(f"   값: {dt_naive}")
        print(f"   타입: {type(dt_naive).__name__}")
        print(f"   tzinfo: {dt_naive.tzinfo}")
        print(f"   is naive: {dt_naive.tzinfo is None}")

        # Step 4: UTC timezone 설정
        dt_aware = dt_naive.replace(tzinfo=timezone.utc)
        print(f"🌍 Step 4 - UTC timezone 설정:")
        print(f"   값: {dt_aware}")
        print(f"   타입: {type(dt_aware).__name__}")
        print(f"   tzinfo: {dt_aware.tzinfo}")
        print(f"   is aware: {dt_aware.tzinfo is not None}")

        # Step 5: _from_utc_iso() 함수 결과와 비교
        result = _from_utc_iso(db_time_str)
        print(f"✅ Step 5 - _from_utc_iso() 결과:")
        print(f"   값: {result}")
        print(f"   일치: {result == dt_aware}")

        # 추가 정보
        print(f"📊 추가 정보:")
        print(f"   UTC timestamp: {dt_aware.timestamp()}")
        print(f"   ISO format: '{dt_aware.isoformat()}'")
        print(f"   strftime: '{dt_aware.strftime('%Y-%m-%dT%H:%M:%S')}'")

    # 3. 다양한 입력 형식 테스트
    print(f"\n" + "=" * 60)
    print("🧪 다양한 입력 형식 테스트")
    print("-" * 60)

    test_cases = [
        "2025-09-08T14:12:00",           # DB 형식 (기본)
        "2025-09-08T14:12:00Z",          # 업비트 API 형식 (Z suffix)
        "2025-09-08T14:12:00+00:00",     # ISO 8601 full (timezone 포함)
        "2025-09-08T14:12:00.123456",    # 마이크로초 포함
        "2025-09-08T14:12:00.123456Z",   # 마이크로초 + Z suffix
    ]

    for i, test_input in enumerate(test_cases, 1):
        try:
            print(f"\n테스트 {i}: '{test_input}'")

            # 직접 fromisoformat
            try:
                direct_naive = datetime.fromisoformat(test_input.replace('Z', ''))
                print(f"   직접 파싱 (naive): {direct_naive} (tzinfo: {direct_naive.tzinfo})")
            except Exception as e:
                print(f"   직접 파싱 실패: {e}")

            # _from_utc_iso 함수 사용
            try:
                result = _from_utc_iso(test_input)
                print(f"   _from_utc_iso(): {result} (tzinfo: {result.tzinfo})")
            except Exception as e:
                print(f"   _from_utc_iso() 실패: {e}")

        except Exception as e:
            print(f"   테스트 {i} 전체 실패: {e}")

    # 4. timezone의 실제 의미
    print(f"\n" + "=" * 60)
    print("🌍 timezone의 실제 의미")
    print("-" * 60)

    sample_time = "2025-09-08T14:12:00"

    # naive datetime
    naive_dt = datetime.fromisoformat(sample_time)
    print(f"📅 naive datetime: {naive_dt}")
    print(f"   의미: '2025년 9월 8일 14시 12분' (시간대 불명)")
    print(f"   문제: 이게 UTC인지, KST인지, 다른 시간대인지 알 수 없음")

    # UTC timezone-aware datetime
    utc_dt = naive_dt.replace(tzinfo=timezone.utc)
    print(f"🌍 UTC aware datetime: {utc_dt}")
    print(f"   의미: '2025년 9월 8일 14시 12분 UTC' (명확한 시간대)")
    print(f"   장점: 정확한 시점을 나타냄, 다른 시간대로 변환 가능")

    # 한국 시간으로 변환 예시
    from datetime import timedelta
    kst_offset = timezone(timedelta(hours=9))
    kst_dt = utc_dt.astimezone(kst_offset)
    print(f"🇰🇷 KST 변환: {kst_dt}")
    print(f"   의미: 같은 시점의 한국 시간 표현")


if __name__ == "__main__":
    analyze_naive_vs_aware()
