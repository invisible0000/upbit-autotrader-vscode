#!/usr/bin/env python3
"""
[자동 생성] 트리거 존재 여부 확인 스크립트
"""

import sqlite3
import os
import json

def check_auto_generated_triggers():
    """[자동 생성] 트리거가 실제로 존재하는지 확인"""
    
    # 가능한 데이터베이스 경로들
    db_paths = [
        'strategies.db',
        'upbit_auto_trading/strategies.db', 
        'upbit_auto_trading/ui/desktop/screens/strategy_management/strategies.db',
        'upbit_auto_trading/ui/desktop/screens/strategy_management/components/strategies.db'
    ]
    
    print("🔍 [자동 생성] 트리거 존재 여부 확인 중...")
    print("=" * 60)
    
    found_db = False
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            found_db = True
            print(f"📂 데이터베이스 발견: {db_path}")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # [자동 생성] 트리거 검색
                cursor.execute('SELECT * FROM trading_conditions WHERE name LIKE ?', ('%자동 생성%',))
                auto_generated = cursor.fetchall()
                
                print(f"🎯 [자동 생성] 트리거 개수: {len(auto_generated)}")
                
                if auto_generated:
                    print("\n📋 [자동 생성] 트리거 목록:")
                    for i, trigger in enumerate(auto_generated, 1):
                        print(f"   {i}. ID: {trigger[0]}, 이름: {trigger[2]}")
                        print(f"      변수: {trigger[5]}, 연산자: {trigger[7]}, 대상값: {trigger[9]}")
                        print(f"      생성일: {trigger[14]}")
                        print()
                
                # 전체 트리거 개수 확인
                cursor.execute('SELECT COUNT(*) FROM trading_conditions')
                total_count = cursor.fetchone()[0]
                print(f"📊 전체 트리거 개수: {total_count}")
                
                # 최근 생성된 트리거 5개 확인
                cursor.execute('''
                    SELECT id, name, variable_name, operator, target_value, created_at 
                    FROM trading_conditions 
                    ORDER BY created_at DESC 
                    LIMIT 5
                ''')
                recent_triggers = cursor.fetchall()
                
                print(f"\n🕐 최근 생성된 트리거 5개:")
                for i, trigger in enumerate(recent_triggers, 1):
                    print(f"   {i}. {trigger[1]} ({trigger[2]} {trigger[3]} {trigger[4]}) - {trigger[5]}")
                
                # 빈 이름 또는 문제가 있는 트리거 확인
                cursor.execute('SELECT * FROM trading_conditions WHERE name = "" OR name IS NULL')
                empty_name_triggers = cursor.fetchall()
                
                if empty_name_triggers:
                    print(f"\n⚠️  빈 이름 트리거 개수: {len(empty_name_triggers)}")
                    for trigger in empty_name_triggers:
                        print(f"   ID: {trigger[0]}, 변수: {trigger[5]}")
                
                conn.close()
                print("=" * 60)
                
            except Exception as e:
                print(f"❌ 데이터베이스 접근 오류: {e}")
            
            break
    
    if not found_db:
        print("❌ 데이터베이스 파일을 찾을 수 없습니다.")
        print("다음 경로들을 확인했습니다:")
        for path in db_paths:
            print(f"   - {path}")

if __name__ == "__main__":
    check_auto_generated_triggers()
