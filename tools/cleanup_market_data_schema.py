"""
Market Data DB 완전 정리 유틸리티

모든 캔들 테이블을 깨끗하게 삭제하여 스키마 충돌을 원천 방지합니다.
개발/테스트 환경에서 DB를 초기 상태로 리셋할 때 사용합니다.
"""

import asyncio
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DBCleanup")


async def clean_market_data_db():
    """Market Data DB 완전 정리 (모든 캔들 테이블 삭제)"""

    print("🧹 Market Data DB 완전 정리 시작...")
    print("⚠️  이 작업은 모든 캔들 데이터를 영구 삭제합니다!")

    db_paths = {
        "settings": "data/settings.sqlite3",
        "strategies": "data/strategies.sqlite3",
        "market_data": "data/market_data.sqlite3"
    }
    db_manager = DatabaseManager(db_paths)

    try:
        with db_manager.get_connection("market_data") as conn:
            # 1. 모든 캔들 테이블 목록 조회 (백업 테이블 포함)
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND (
                    name LIKE 'candles_%' OR
                    name LIKE '%_backup_%'
                )
                ORDER BY name
            """)
            all_tables = [row[0] for row in cursor.fetchall()]

            if not all_tables:
                print("✅ 삭제할 테이블이 없습니다. DB가 이미 깨끗합니다.")
                return

            print(f"\n📋 삭제 대상 테이블: {len(all_tables)}개")
            for table in all_tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   🗑️ {table} ({count}개 레코드)")

            # 2. 최종 확인
            print("\n⚠️  이 작업은 되돌릴 수 없습니다!")
            response = input("정말로 모든 캔들 데이터를 삭제하시겠습니까? (DELETE 입력): ")

            if response != "DELETE":
                print("❌ 작업 취소됨 (안전장치 활성화)")
                return

            # 3. 모든 테이블 삭제
            deleted_count = 0
            for table_name in all_tables:
                try:
                    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    print(f"   ✅ 삭제 완료: {table_name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"   ❌ 삭제 실패: {table_name}, {e}")

            conn.commit()

            print(f"\n🎉 DB 정리 완료!")
            print(f"   �️ 삭제된 테이블: {deleted_count}개")
            print(f"   ✅ Market Data DB가 깨끗하게 초기화되었습니다.")

    except Exception as e:
        print(f"\n❌ DB 정리 실패: {e}")
        raise


async def show_current_tables():
    """현재 테이블 상태 조회"""

    print("📊 현재 Market Data DB 테이블 상태...")

    db_paths = {
        "settings": "data/settings.sqlite3",
        "strategies": "data/strategies.sqlite3",
        "market_data": "data/market_data.sqlite3"
    }
    db_manager = DatabaseManager(db_paths)

    try:
        with db_manager.get_connection("market_data") as conn:
            # 모든 테이블 조회
            cursor = conn.execute("""
                SELECT name, type FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """)
            all_tables = cursor.fetchall()

            if not all_tables:
                print("✅ 테이블이 없습니다. DB가 비어있습니다.")
                return

            # 캔들 테이블과 기타 테이블 분류
            candle_tables = []
            other_tables = []

            for table_name, table_type in all_tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]

                if table_name.startswith('candles_') or '_backup_' in table_name:
                    candle_tables.append((table_name, count))
                else:
                    other_tables.append((table_name, count))

            # 결과 출력
            print(f"\n📋 전체 테이블: {len(all_tables)}개")

            if candle_tables:
                print(f"\n🕯️ 캔들 관련 테이블: {len(candle_tables)}개")
                for table_name, count in candle_tables:
                    print(f"   � {table_name} ({count}개 레코드)")

            if other_tables:
                print(f"\n📋 기타 테이블: {len(other_tables)}개")
                for table_name, count in other_tables:
                    print(f"   � {table_name} ({count}개 레코드)")

    except Exception as e:
        print(f"❌ 테이블 조회 실패: {e}")


async def vacuum_database():
    """데이터베이스 최적화 (VACUUM)"""

    print("� 데이터베이스 최적화 실행...")

    db_paths = {
        "settings": "data/settings.sqlite3",
        "strategies": "data/strategies.sqlite3",
        "market_data": "data/market_data.sqlite3"
    }
    db_manager = DatabaseManager(db_paths)

    try:
        with db_manager.get_connection("market_data") as conn:
            print("   🗜️ VACUUM 실행 중...")
            conn.execute("VACUUM")
            print("   ✅ 데이터베이스 최적화 완료")

    except Exception as e:
        print(f"❌ 최적화 실패: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "show" or command == "list":
            asyncio.run(show_current_tables())
        elif command == "vacuum":
            asyncio.run(vacuum_database())
        elif command == "clean":
            asyncio.run(clean_market_data_db())
        else:
            print("사용법:")
            print("  python cleanup_market_data_schema.py show   - 현재 테이블 상태 조회")
            print("  python cleanup_market_data_schema.py clean  - 모든 캔들 테이블 삭제")
            print("  python cleanup_market_data_schema.py vacuum - 데이터베이스 최적화")
    else:
        print("🧹 Market Data DB 정리 도구")
        print("\n사용법:")
        print("  python cleanup_market_data_schema.py show   - 현재 테이블 상태 조회")
        print("  python cleanup_market_data_schema.py clean  - 모든 캔들 테이블 삭제 (⚠️ 위험)")
        print("  python cleanup_market_data_schema.py vacuum - 데이터베이스 최적화")
        print("\n예시:")
        print("  python cleanup_market_data_schema.py show")
        print("  python cleanup_market_data_schema.py clean")
