#!/usr/bin/env python3
"""
DB 상태 확인 스크립트
"""

import sqlite3
import os

def check_db_status():
    # settings.sqlite3만 확인
    db_path = 'upbit_auto_trading/data/settings.sqlite3'
    
    print(f'\n=== {db_path} 확인 ===')
    
    if not os.path.exists(db_path):
        print(f'❌ DB 파일이 없습니다')
        return
    
    print(f'✅ DB 파일 발견')
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%variable%'")
            tables = cursor.fetchall()
            print(f'변수 관련 테이블: {[t[0] for t in tables]}')
            
            # tv_variable_parameters 테이블 확인
            try:
                cursor.execute('SELECT COUNT(*) FROM tv_variable_parameters')
                count = cursor.fetchone()[0]
                print(f'tv_variable_parameters 레코드 수: {count}')
                
                if count > 0:
                    cursor.execute('SELECT DISTINCT variable_id FROM tv_variable_parameters LIMIT 5')
                    var_ids = cursor.fetchall()
                    print(f'파라미터가 있는 variable_id들: {[v[0] for v in var_ids]}')
                
            except Exception as e:
                print(f'tv_variable_parameters 테이블 오류: {e}')
            
            # tv_trading_variables 테이블 확인
            try:
                cursor.execute('SELECT COUNT(*) FROM tv_trading_variables')
                count = cursor.fetchone()[0]
                print(f'tv_trading_variables 레코드 수: {count}')
                
            except Exception as e:
                print(f'tv_trading_variables 테이블 오류: {e}')
                
    except Exception as e:
        print(f'DB 연결 오류: {e}')

if __name__ == "__main__":
    check_db_status()
