#!/usr/bin/env python3
"""
스키마 직접 적용 스크립트
"""

import sqlite3
import os

def apply_schema():
    # 스키마 파일과 DB 파일 경로
    schema_path = 'upbit_auto_trading/utils/trading_variables/schema_new02.sql'
    db_path = 'upbit_auto_trading/data/settings.sqlite3'
    
    print(f'스키마 파일 존재: {os.path.exists(schema_path)}')
    print(f'DB 파일 존재: {os.path.exists(db_path)}')
    
    if not os.path.exists(schema_path):
        print('❌ 스키마 파일을 찾을 수 없습니다')
        return
        
    if not os.path.exists(db_path):
        print('❌ DB 파일을 찾을 수 없습니다')
        return
    
    # 스키마 파일 읽기
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        print(f'스키마 SQL 크기: {len(schema_sql)} 바이트')
    except Exception as e:
        print(f'❌ 스키마 파일 읽기 실패: {e}')
        return
    
    # 스키마 적용
    try:
        with sqlite3.connect(db_path) as conn:
            conn.executescript(schema_sql)
            print('✅ 스키마 적용 완료')
            
            # 확인
            cursor = conn.cursor()
            
            # tv_variable_parameters 테이블 확인
            cursor.execute('SELECT COUNT(*) FROM tv_variable_parameters')
            param_count = cursor.fetchone()[0]
            print(f'tv_variable_parameters 레코드 수: {param_count}')
            
            # SMA 파라미터 확인
            cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters WHERE variable_id = 'SMA'")
            sma_count = cursor.fetchone()[0]
            print(f'SMA 파라미터 수: {sma_count}')
            
            # 모든 파라미터 확인
            cursor.execute('SELECT DISTINCT variable_id FROM tv_variable_parameters ORDER BY variable_id')
            var_ids = cursor.fetchall()
            print(f'파라미터가 있는 변수들: {[v[0] for v in var_ids]}')
            
    except Exception as e:
        print(f'❌ 스키마 적용 실패: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    apply_schema()
