#!/usr/bin/env python3
"""
현재 DB 상태 확인 및 사용자 지적 문제점 진단
"""

import sqlite3
import json

def check_current_db_state():
    """현재 DB 상태 확인"""
    print("🔍 현재 데이터베이스 상태 확인")
    
    conn = sqlite3.connect("data/app_settings.sqlite3")
    cursor = conn.cursor()
    
    try:
        # 골든크로스 트리거 확인
        cursor.execute("""
            SELECT id, name, variable_params, external_variable 
            FROM trading_conditions 
            WHERE name LIKE '%골든크로스%'
        """)
        
        results = cursor.fetchall()
        
        for r in results:
            trigger_id, name, variable_params, external_variable_str = r
            print(f"ID:{trigger_id} {name}")
            print(f"  주변수: {variable_params}")
            
            if external_variable_str:
                try:
                    external_variable = json.loads(external_variable_str)
                    print(f"  외부변수: {external_variable}")
                except json.JSONDecodeError:
                    print(f"  외부변수: JSON 파싱 실패 - {external_variable_str}")
            else:
                print(f"  외부변수: None")
            print()
            
    except Exception as e:
        print(f"❌ 오류: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_current_db_state()
