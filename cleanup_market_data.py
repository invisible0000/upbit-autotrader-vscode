"""
마켓 데이터 클린업 도구 - 생성된 테스트 테이블들 정리
"""
import sqlite3
import time


def cleanup_test_tables():
    """테스트로 생성된 캔들 테이블들을 정리"""

    print("🧹 마켓 데이터 클린업 시작\n")

    conn = sqlite3.connect('data/market_data.sqlite3')
    cursor = conn.cursor()

    # 1단계: 현재 테이블 상태 확인
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='table' AND name LIKE 'candles_%'
    """)
    total_tables = cursor.fetchone()[0]
    print(f"📊 정리 전 캔들 테이블 수: {total_tables}개")

    if total_tables == 0:
        print("✅ 정리할 테이블이 없습니다.")
        conn.close()
        return

    # 2단계: 보존할 테이블 정의 (기본 테스트용)
    preserve_tables = {
        'candles_KRW_BTC_1m',
        'candles_KRW_ETH_1m',
        'candles_KRW_DOGE_1m'
    }

    # 3단계: 모든 캔들 테이블 목록 조회
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'candles_%'
        ORDER BY name
    """)
    all_tables = [row[0] for row in cursor.fetchall()]

    # 4단계: 삭제할 테이블 필터링
    tables_to_delete = [table for table in all_tables if table not in preserve_tables]
    tables_to_preserve = [table for table in all_tables if table in preserve_tables]

    print(f"🗑️  삭제 예정: {len(tables_to_delete)}개 테이블")
    print(f"💾 보존 예정: {len(tables_to_preserve)}개 테이블")

    if tables_to_preserve:
        print("\n📋 보존할 테이블:")
        for table in tables_to_preserve:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table} ({count}개 레코드)")

    if not tables_to_delete:
        print("\n✅ 삭제할 테이블이 없습니다.")
        conn.close()
        return

    # 5단계: 사용자 확인
    print(f"\n⚠️  {len(tables_to_delete)}개 테이블을 삭제합니다.")
    print("계속하려면 'y' 또는 'yes'를 입력하세요: ", end="")

    # 자동 승인 (스크립트 실행용)
    auto_confirm = True
    if auto_confirm:
        print("y (자동 승인)")
        confirm = "y"
    else:
        confirm = input().lower().strip()

    if confirm not in ['y', 'yes']:
        print("❌ 작업이 취소되었습니다.")
        conn.close()
        return

    # 6단계: 테이블 삭제 실행
    print(f"\n🗑️  테이블 삭제 시작...")
    start_time = time.time()

    deleted_count = 0
    batch_size = 50  # 배치 단위로 처리

    for i, table in enumerate(tables_to_delete):
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            deleted_count += 1

            # 진행률 표시
            if (i + 1) % batch_size == 0 or i == len(tables_to_delete) - 1:
                progress = ((i + 1) / len(tables_to_delete)) * 100
                print(f"   진행률: {progress:.1f}% ({i + 1}/{len(tables_to_delete)})")

        except Exception as e:
            print(f"   ❌ {table} 삭제 실패: {e}")

    # 변경사항 커밋
    conn.commit()

    elapsed_time = time.time() - start_time
    print(f"\n✅ 삭제 완료: {deleted_count}개 테이블 ({elapsed_time:.2f}초)")

    # 7단계: 정리 후 상태 확인
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master
        WHERE type='table' AND name LIKE 'candles_%'
    """)
    remaining_tables = cursor.fetchone()[0]

    print(f"\n📊 정리 후 캔들 테이블 수: {remaining_tables}개")
    print(f"🗑️  삭제된 테이블: {total_tables - remaining_tables}개")

    # 8단계: VACUUM으로 공간 회수
    print("\n🔧 데이터베이스 최적화 중...")
    vacuum_start = time.time()
    cursor.execute("VACUUM")
    vacuum_time = time.time() - vacuum_start
    print(f"✅ 최적화 완료 ({vacuum_time:.2f}초)")

    conn.close()

    print("\n🎉 마켓 데이터 클린업 완료!")
    print("   - 핵심 테이블은 보존")
    print("   - 테스트 테이블은 정리")
    print("   - 데이터베이스 최적화 완료")


if __name__ == "__main__":
    cleanup_test_tables()
