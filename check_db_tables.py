#!/usr/bin/env python3
import sqlite3
import os

# 현재 DB 테이블 확인
db_path = "upbit_auto_trading/data/settings.sqlite3"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"DB 테이블 수: {len(tables)}")
    print("DB 테이블 목록:")
    for table in sorted(tables):
        print(f"  - {table}")
    conn.close()
else:
    print(f"DB 파일을 찾을 수 없습니다: {db_path}")

# 현재 GUI 스키마 파일의 테이블 확인
import re
schema_path = "upbit_auto_trading/utils/trading_variables/gui_variables_DB_migration_util/data_info/upbit_autotrading_unified_schema.sql"
if os.path.exists(schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_content = f.read()
    
    # CREATE TABLE 문 추출
    create_patterns = re.findall(
        r'CREATE TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(\w+)\s*\(',
        schema_content,
        re.IGNORECASE
    )
    print(f"\n스키마 파일 테이블 수: {len(create_patterns)}")
    print("스키마 파일 테이블 목록:")
    for table in sorted(create_patterns):
        print(f"  - {table}")
else:
    print(f"스키마 파일을 찾을 수 없습니다: {schema_path}")
