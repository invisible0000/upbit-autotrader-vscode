#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
기존 SQLite 데이터베이스 구조 분석
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

def analyze_database(db_path):
    """데이터베이스 구조 분석"""
    if not os.path.exists(db_path):
        print(f"❌ {db_path} 파일이 존재하지 않습니다.")
        return None
    
    file_size = os.path.getsize(db_path)
    print(f"🔍 {db_path} 분석 (크기: {file_size:,} bytes)")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"   📊 테이블 수: {len(tables)}개")
        
        for table in tables:
            table_name = table[0]
            print(f"\n   📋 테이블: {table_name}")
            
            # 테이블 구조 확인
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"      컬럼 수: {len(columns)}개")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, is_pk = col
                pk_mark = " (PK)" if is_pk else ""
                null_mark = " NOT NULL" if not_null else ""
                print(f"      └ {col_name}: {col_type}{pk_mark}{null_mark}")
            
            # 데이터 개수 확인
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"      📈 데이터: {count:,}개")
                
                # 최근 데이터 확인 (timestamp 컬럼이 있는 경우)
                if any(col[1] == 'timestamp' for col in columns):
                    cursor.execute(f"SELECT timestamp FROM {table_name} ORDER BY timestamp DESC LIMIT 1")
                    latest = cursor.fetchone()
                    if latest:
                        print(f"      ⏰ 최신 데이터: {latest[0]}")
                        
            except Exception as e:
                print(f"      ❌ 데이터 조회 실패: {e}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ 데이터베이스 분석 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🔍 기존 SQLite 데이터베이스 구조 분석")
    print("=" * 60)
    
    # 확인할 데이터베이스 파일들
    db_files = [
        'data/upbit_auto_trading.db',
        'data/upbit_auto_trading.sqlite3',
        'upbit_auto_trading.db',
        'upbit_auto_trading.sqlite3'
    ]
    
    found_dbs = []
    
    for db_file in db_files:
        if os.path.exists(db_file):
            found_dbs.append(db_file)
            analyze_database(db_file)
            print()
    
    if not found_dbs:
        print("❌ 기존 SQLite 데이터베이스 파일을 찾을 수 없습니다.")
        print("📁 현재 디렉토리의 파일들:")
        for item in os.listdir('.'):
            if item.endswith('.db') or item.endswith('.sqlite3') or item.endswith('.sqlite'):
                print(f"   - {item}")
    else:
        print(f"✅ 총 {len(found_dbs)}개의 데이터베이스 발견:")
        for db in found_dbs:
            print(f"   - {db}")
    
    print("\n" + "=" * 60)
    print("📋 분석 완료!")

if __name__ == "__main__":
    main()
