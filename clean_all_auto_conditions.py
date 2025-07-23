import sqlite3
import os

# 모든 trading_conditions.db 파일 확인
db_files = [
    'data/trading_conditions.db',
    'upbit_auto_trading/ui/desktop/data/trading_conditions.db'
]

for db_path in db_files:
    if os.path.exists(db_path):
        print(f"\n=== {db_path} ===")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 존재 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trading_conditions'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # 전체 조건 개수
            cursor.execute("SELECT COUNT(*) FROM trading_conditions")
            total_count = cursor.fetchone()[0]
            print(f"전체 조건 개수: {total_count}")
            
            # [자동 생성] 조건 확인
            cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE name LIKE '%자동 생성%'")
            auto_count = cursor.fetchone()[0]
            print(f"[자동 생성] 조건 개수: {auto_count}")
            
            if auto_count > 0:
                cursor.execute("SELECT id, name FROM trading_conditions WHERE name LIKE '%자동 생성%'")
                auto_conditions = cursor.fetchall()
                print("발견된 [자동 생성] 조건:")
                for condition in auto_conditions:
                    print(f"  ID: {condition[0]}, 이름: {condition[1]}")
                    
                # 이 데이터베이스에서도 삭제
                cursor.execute("DELETE FROM trading_conditions WHERE name LIKE '%자동 생성%'")
                deleted_count = cursor.rowcount
                conn.commit()
                if deleted_count > 0:
                    print(f"✓ {deleted_count}개의 [자동 생성] 조건을 삭제했습니다.")
            else:
                print("✓ [자동 생성] 조건이 없습니다.")
        else:
            print("trading_conditions 테이블이 없습니다.")
        
        conn.close()
    else:
        print(f"파일 없음: {db_path}")
