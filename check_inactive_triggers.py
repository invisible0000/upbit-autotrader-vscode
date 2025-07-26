#!/usr/bin/env python3
"""
데이터베이스에서 소프트 삭제된 비활성 트리거들을 검색하는 스크립트
"""

import sqlite3
import json
from pathlib import Path

def check_database(db_path):
    """데이터베이스 확인"""
    if not Path(db_path).exists():
        print(f'❌ 데이터베이스 없음: {db_path}')
        return
    
    print(f'\n📊 데이터베이스: {db_path}')
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 테이블 목록 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f'테이블 목록: {tables}')
            
            if 'trading_conditions' in tables:
                # 전체 조건 수 확인
                cursor.execute('SELECT COUNT(*) FROM trading_conditions')
                total = cursor.fetchone()[0]
                print(f'전체 조건 수: {total}')
                
                # 활성 조건 수
                cursor.execute('SELECT COUNT(*) FROM trading_conditions WHERE is_active = 1')
                active = cursor.fetchone()[0]
                print(f'활성 조건 수: {active}')
                
                # 비활성 조건 수
                cursor.execute('SELECT COUNT(*) FROM trading_conditions WHERE is_active = 0')
                inactive = cursor.fetchone()[0]
                print(f'비활성(소프트 삭제) 조건 수: {inactive}')
                
                if inactive > 0:
                    print(f'\n🗑️ 비활성 조건들:')
                    cursor.execute('''
                        SELECT id, name, created_at, updated_at 
                        FROM trading_conditions 
                        WHERE is_active = 0 
                        ORDER BY updated_at DESC
                    ''')
                    for row in cursor.fetchall():
                        print(f'  ID: {row[0]}, Name: {row[1]}, Created: {row[2]}, Updated: {row[3]}')
                
                # 최근 조건들 (활성/비활성 모두)
                print(f'\n📋 최근 조건들 (활성/비활성):')
                cursor.execute('''
                    SELECT id, name, is_active, created_at, updated_at 
                    FROM trading_conditions 
                    ORDER BY updated_at DESC 
                    LIMIT 10
                ''')
                for row in cursor.fetchall():
                    status = '활성' if row[2] else '비활성'
                    print(f'  ID: {row[0]}, Name: {row[1]}, Status: {status}, Created: {row[3]}, Updated: {row[4]}')
                    
    except Exception as e:
        print(f'❌ 오류: {e}')

def main():
    """메인 함수"""
    print("🔍 소프트 삭제된 비활성 트리거 검색")
    
    # 데이터베이스 경로들 확인
    db_paths = [
        'data/app_settings.sqlite3',
        'upbit_auto_trading/ui/desktop/data/trading_conditions.db',
        'data/upbit_auto_trading.db',
        'data/trading_conditions.db', 
        'upbit_auto_trading.db',
        'trading_conditions.db'
    ]
    
    for db_path in db_paths:
        check_database(db_path)

if __name__ == "__main__":
    main()
