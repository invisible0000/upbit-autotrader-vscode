"""
최적화된 마켓 데이터 스키마 생성기
"""
import sqlite3
from pathlib import Path

def create_optimized_schema():
    """최적화된 스키마로 DB 생성"""
    db_path = Path("data/market_data.sqlite3")
    schema_path = Path("data_info/optimized_market_data_schema.sql")

    # 스키마 파일 읽기
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # DB 생성 및 스키마 적용
    with sqlite3.connect(db_path) as conn:
        # 스키마 실행
        conn.executescript(schema_sql)
        print("✅ 최적화된 마켓 데이터 스키마 생성 완료")

        # 테이블 목록 확인
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()

        print(f"📋 생성된 테이블 수: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")

if __name__ == "__main__":
    create_optimized_schema()
