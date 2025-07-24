import os
import sqlite3

# trading_conditions.db 파일 찾기
possible_paths = [
    'data/trading_conditions.db',
    'upbit_auto_trading/data/trading_conditions.db',
    'trading_conditions.db'
]

print("trading_conditions.db 파일 검색:")
for path in possible_paths:
    if os.path.exists(path):
        print(f"✓ 발견: {path}")
        
        # 데이터베이스 내용 확인
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        
        # trading_conditions 테이블 확인
        cursor.execute("SELECT COUNT(*) FROM trading_conditions")
        total_count = cursor.fetchone()[0]
        print(f"  전체 조건 개수: {total_count}")
        
        # [자동 생성] 조건 확인
        cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE name LIKE '%자동 생성%'")
        auto_count = cursor.fetchone()[0]
        print(f"  [자동 생성] 조건 개수: {auto_count}")
        
        if auto_count > 0:
            cursor.execute("SELECT id, name, description FROM trading_conditions WHERE name LIKE '%자동 생성%'")
            auto_conditions = cursor.fetchall()
            print(f"  [자동 생성] 조건 목록:")
            for condition in auto_conditions:
                print(f"    ID: {condition[0]}, 이름: {condition[1]}, 설명: {condition[2]}")
        
        conn.close()
    else:
        print(f"✗ 없음: {path}")

print("\n모든 .db 파일 검색:")
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.db'):
            full_path = os.path.join(root, file)
            print(f"  {full_path}")
