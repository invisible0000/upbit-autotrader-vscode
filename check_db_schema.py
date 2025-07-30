#!/usr/bin/env python3
"""
DB 스키마 확인 스크립트
"""

import sqlite3
import os

# DB 파일 경로
db_path = "upbit_auto_trading/data/settings.sqlite3"

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print("📋 테이블 목록:")
        for table in tables:
            print(f"  - {table}")
        
        print("\n" + "="*50)
        
        # trading_variables 테이블 구조
        if "trading_variables" in tables:
            print("\n📊 trading_variables 테이블 구조:")
            cursor.execute("PRAGMA table_info(trading_variables)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 샘플 데이터
            print("\n📄 샘플 데이터:")
            cursor.execute("SELECT * FROM trading_variables LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")
        
        # variable_parameters 테이블 구조
        if "variable_parameters" in tables:
            print("\n⚙️ variable_parameters 테이블 구조:")
            cursor.execute("PRAGMA table_info(variable_parameters)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 샘플 데이터
            print("\n📄 샘플 데이터:")
            cursor.execute("SELECT * FROM variable_parameters LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류: {e}")
else:
    print(f"❌ DB 파일을 찾을 수 없습니다: {db_path}")
