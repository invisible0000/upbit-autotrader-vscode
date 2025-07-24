
# 간단한 데이터 마이그레이션
import sqlite3
import shutil

def migrate_trading_conditions():
    """trading_conditions 데이터 마이그레이션"""
    source_db = "data/upbit_trading_unified.db"
    target_db = "data/upbit_trading_unified.db"
    
    print(f"{source_db} → {target_db} 마이그레이션 시작...")
    
    # 소스 DB에서 데이터 읽기
    source_conn = sqlite3.connect(source_db)
    source_cursor = source_conn.cursor()
    
    # 타겟 DB 연결
    target_conn = sqlite3.connect(target_db)
    target_cursor = target_conn.cursor()
    
    try:
        # trading_conditions 테이블 생성 (이미 있으면 무시)
        source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trading_conditions';")
        create_sql = source_cursor.fetchone()
        
        if create_sql:
            target_cursor.execute(create_sql[0])
            print("✅ trading_conditions 테이블 생성 완료")
        
        # 데이터 복사
        source_cursor.execute("SELECT * FROM trading_conditions;")
        rows = source_cursor.fetchall()
        
        if rows:
            # 열 정보 가져오기
            source_cursor.execute("PRAGMA table_info(trading_conditions);")
            columns = [col[1] for col in source_cursor.fetchall()]
            
            placeholders = "?" + ",?" * (len(columns) - 1)
            insert_sql = f"INSERT OR REPLACE INTO trading_conditions VALUES ({placeholders})"
            
            target_cursor.executemany(insert_sql, rows)
            target_conn.commit()
            
            print(f"✅ {len(rows)}개 데이터 마이그레이션 완료")
        else:
            print("⚠️ 복사할 데이터가 없습니다")
    
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    migrate_trading_conditions()
        