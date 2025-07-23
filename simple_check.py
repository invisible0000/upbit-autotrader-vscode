import sqlite3
import os

# 데이터베이스 파일 찾기
db_file = None
possible_paths = ['strategies.db', 'upbit_auto_trading/strategies.db']

for path in possible_paths:
    if os.path.exists(path):
        db_file = path
        break

if db_file:
    print(f"DB 파일 발견: {db_file}")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 테이블 목록 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"데이터베이스 테이블 목록: {tables}")
    
    # 각 테이블의 구조 확인
    for table in tables:
        table_name = table[0]
        print(f"\n테이블: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 데이터 개수 확인
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  데이터 개수: {count}")
        
        # trading_conditions 테이블이 있으면 [자동 생성] 확인
        if table_name == 'trading_conditions':
            cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE name LIKE '%자동 생성%'")
            auto_count = cursor.fetchone()[0]
            print(f"  [자동 생성] 트리거 개수: {auto_count}")
            
            if auto_count > 0:
                cursor.execute("SELECT id, name FROM trading_conditions WHERE name LIKE '%자동 생성%'")
                auto_triggers = cursor.fetchall()
                print("  [자동 생성] 트리거 목록:")
                for trigger in auto_triggers:
                    print(f"    ID: {trigger[0]}, 이름: {trigger[1]}")
    
    conn.close()
else:
    print("데이터베이스 파일을 찾을 수 없습니다.")
