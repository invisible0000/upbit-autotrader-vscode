#!/usr/bin/env python3
"""
Phase 4.2 - condition_storage.py 경로 업데이트 검증
"""

import sqlite3
import os

def test_condition_storage_update():
    """condition_storage.py 업데이트 검증"""
    print("🔍 Phase 4.2 - condition_storage.py 업데이트 검증")
    print("=" * 60)
    
    # 1. 새로운 통합 DB 파일 존재 확인
    settings_db = "data/settings.sqlite3"
    if os.path.exists(settings_db):
        print(f"✅ 통합 DB 존재: {settings_db}")
        
        # 2. trading_conditions 테이블 확인
        try:
            conn = sqlite3.connect(settings_db)
            cursor = conn.cursor()
            
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="trading_conditions"')
            table_exists = cursor.fetchone()
            
            if table_exists:
                cursor.execute('SELECT COUNT(*) FROM trading_conditions')
                count = cursor.fetchone()[0]
                print(f"✅ trading_conditions 테이블: {count}개 레코드")
                
                # 3. 샘플 데이터 확인
                cursor.execute('SELECT id, name FROM trading_conditions LIMIT 3')
                samples = cursor.fetchall()
                print("📊 샘플 조건들:")
                for sample in samples:
                    print(f"  - ID {sample[0]}: {sample[1]}")
                    
            else:
                print("❌ trading_conditions 테이블 없음")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ DB 연결 오류: {e}")
    else:
        print(f"❌ 통합 DB 파일 없음: {settings_db}")
    
    # 4. condition_storage.py 모듈 import 테스트
    print("\n🔗 condition_storage.py 모듈 테스트:")
    try:
        import sys
        sys.path.append('upbit_auto_trading/ui/desktop/screens/strategy_management/components')
        
        from condition_storage import ConditionStorage
        print("✅ ConditionStorage 모듈 import 성공")
        
        # 기본 생성자 테스트 (새 통합 DB 사용해야 함)
        storage = ConditionStorage()
        expected_path = os.path.abspath("data/settings.sqlite3")
        actual_path = os.path.abspath(storage.db_path)
        
        if actual_path == expected_path:
            print(f"✅ 새로운 통합 DB 경로 사용: {storage.db_path}")
        else:
            print(f"⚠️ 예상과 다른 DB 경로:")
            print(f"  예상: {expected_path}")
            print(f"  실제: {actual_path}")
        
    except Exception as e:
        print(f"❌ 모듈 테스트 실패: {e}")
    
    print("\n🎯 Phase 4.2 검증 완료!")

if __name__ == "__main__":
    test_condition_storage_update()
