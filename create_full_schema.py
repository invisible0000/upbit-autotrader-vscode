#!/usr/bin/env python3
import sqlite3
import os

def extract_full_schema():
    """현재 DB에서 완전한 스키마 추출"""
    db_path = "upbit_auto_trading/data/settings.sqlite3"
    output_path = "upbit_auto_trading/utils/trading_variables/gui_variables_DB_migration_util/data_info/upbit_autotrading_unified_schema.sql"
    
    if not os.path.exists(db_path):
        print(f"DB 파일을 찾을 수 없습니다: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 스키마 추출
    schema_lines = []
    schema_lines.append("-- Upbit Auto Trading Unified Schema")
    schema_lines.append("-- 완전한 통합 스키마 (모든 테이블 포함)")
    schema_lines.append("-- 생성일: Auto-generated from current DB")
    schema_lines.append("PRAGMA foreign_keys = ON;")
    schema_lines.append("")
    
    # 모든 테이블의 CREATE TABLE 문 추출
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table_name in tables:
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        create_sql = cursor.fetchone()
        if create_sql and create_sql[0]:
            schema_lines.append(f"-- Table: {table_name}")
            schema_lines.append(create_sql[0] + ";")
            schema_lines.append("")
    
    # 인덱스 추출
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name")
    indexes = cursor.fetchall()
    
    if indexes:
        schema_lines.append("-- Indexes")
        for index in indexes:
            if index[0]:
                schema_lines.append(index[0] + ";")
        schema_lines.append("")
    
    conn.close()
    
    # 파일 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(schema_lines))
    
    print(f"완전한 스키마가 생성되었습니다: {output_path}")
    print(f"총 {len(tables)}개 테이블 포함")
    
    # 검증
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import re
    create_patterns = re.findall(
        r'CREATE TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(\w+)\s*\(',
        content,
        re.IGNORECASE
    )
    print(f"검증: 스키마 파일에서 {len(create_patterns)}개 테이블 감지")

if __name__ == "__main__":
    extract_full_schema()
