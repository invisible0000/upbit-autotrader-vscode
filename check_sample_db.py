#!/usr/bin/env python3
"""
샘플 DB 구조 확인
"""

import sqlite3
import pandas as pd
import os

def check_sample_db():
    db_path = "upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/data/sampled_market_data.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"❌ DB 파일이 존재하지 않음: {db_path}")
        return
    
    print(f"✅ DB 파일 발견: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            # 테이블 목록 확인
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📋 테이블 목록: {tables}")
            
            # 각 테이블의 스키마 확인
            for table in tables:
                table_name = table[0]
                print(f"\n📊 테이블: {table_name}")
                
                # 컬럼 정보
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print("컬럼 정보:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
                
                # 샘플 데이터 확인
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_data = cursor.fetchall()
                print(f"샘플 데이터 (5개):")
                for i, row in enumerate(sample_data):
                    print(f"  {i+1}: {row}")
                
                # 총 레코드 수
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"총 레코드 수: {count}")
                
    except Exception as e:
        print(f"❌ DB 접근 실패: {e}")

if __name__ == "__main__":
    check_sample_db()
