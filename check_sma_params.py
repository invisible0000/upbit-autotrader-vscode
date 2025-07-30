#!/usr/bin/env python3
"""
SMA 파라미터 확인 스크립트
"""

import sqlite3

def check_sma_parameters():
    db_path = 'upbit_auto_trading/data/settings.sqlite3'
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # SMA 파라미터 상세 정보
        cursor.execute("""
            SELECT parameter_id, variable_id, parameter_name, parameter_type, 
                   default_value, display_name_ko, description, display_order
            FROM tv_variable_parameters 
            WHERE variable_id = 'SMA'
            ORDER BY display_order
        """)
        
        sma_params = cursor.fetchall()
        print('SMA 파라미터 상세:')
        for param in sma_params:
            print(f'  ID: {param[0]}')
            print(f'  변수: {param[1]}')
            print(f'  파라미터명: {param[2]}')
            print(f'  타입: {param[3]}')
            print(f'  기본값: {param[4]}')
            print(f'  한국어명: {param[5]}')
            print(f'  설명: {param[6]}')
            print(f'  순서: {param[7]}')
            print('  ---')

if __name__ == "__main__":
    check_sma_parameters()
