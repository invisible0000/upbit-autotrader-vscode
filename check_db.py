#!/usr/bin/env python3
"""
데이터베이스 확인 스크립트
"""

import sqlite3
import os

# 통합 데이터베이스 경로들
db_paths = [
    r"d:\projects\upbit-autotrader-vscode\data\upbit_auto_trading.sqlite3",
    r"d:\projects\upbit-autotrader-vscode\data\app_settings.sqlite3"
]

print("=== 데이터베이스 확인 ===")

for db_path in db_paths:
    print(f"\nDB 경로: {db_path}")
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            print("\n=== 테이블 목록 ===")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                print(f"- {table[0]}")
            
            # 트리거 관련 테이블 확인
            trigger_tables = [name[0] for name in tables if 'trigger' in name[0].lower() or 'condition' in name[0].lower()]
            
            print("\n=== 트리거/조건 관련 테이블 ===")
            for table_name in trigger_tables:
                print(f"\n--- {table_name} 테이블 ---")
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"레코드 수: {count}")
                
                if count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()
                    
                    # 컬럼명 가져오기
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    print(f"컬럼: {', '.join(columns)}")
                    
                    print("샘플 데이터:")
                    for row in rows:
                        print(f"  {row}")
            
            conn.close()
            
        except Exception as e:
            print(f"오류: {e}")
    else:
        print(f"{db_path} 파일이 존재하지 않습니다.")

print("\n=== 완료 ===")
