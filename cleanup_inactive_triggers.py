#!/usr/bin/env python3
"""
비활성(소프트 삭제된) 트리거들을 완전히 삭제하는 스크립트
"""

import sqlite3
from pathlib import Path

def cleanup_inactive_triggers():
    """비활성 트리거들을 완전히 삭제"""
    db_path = 'data/app_settings.sqlite3'
    
    if not Path(db_path).exists():
        print(f'❌ 데이터베이스 없음: {db_path}')
        return
    
    print(f'🧹 비활성 트리거 정리 시작: {db_path}')
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 삭제 전 현재 상태 확인
            cursor.execute('SELECT COUNT(*) FROM trading_conditions WHERE is_active = 0')
            inactive_count = cursor.fetchone()[0]
            
            if inactive_count == 0:
                print('✅ 비활성 트리거가 없습니다.')
                return
            
            print(f'🗑️ 삭제할 비활성 트리거 수: {inactive_count}')
            
            # 삭제할 트리거들의 정보 표시
            cursor.execute('''
                SELECT id, name, created_at, updated_at 
                FROM trading_conditions 
                WHERE is_active = 0 
                ORDER BY updated_at DESC
            ''')
            
            for row in cursor.fetchall():
                print(f'  삭제 예정: ID={row[0]}, Name={row[1]}, Updated={row[3]}')
            
            # 확인 메시지
            print(f'\n⚠️ {inactive_count}개의 비활성 트리거를 완전히 삭제하시겠습니까? (y/N): ', end='')
            confirm = input().strip().lower()
            
            if confirm == 'y':
                # 하드 삭제 실행
                cursor.execute('DELETE FROM trading_conditions WHERE is_active = 0')
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f'✅ {deleted_count}개의 비활성 트리거가 완전히 삭제되었습니다.')
                
                # 삭제 후 상태 확인
                cursor.execute('SELECT COUNT(*) FROM trading_conditions')
                total_remaining = cursor.fetchone()[0]
                print(f'📊 남은 총 트리거 수: {total_remaining}')
                
            else:
                print('❌ 삭제가 취소되었습니다.')
                
    except Exception as e:
        print(f'❌ 오류: {e}')

def main():
    """메인 함수"""
    print("🧹 비활성 트리거 정리 도구")
    cleanup_inactive_triggers()

if __name__ == "__main__":
    main()
