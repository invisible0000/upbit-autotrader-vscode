
# 비활성화된 트리거 정리 스크립트
import sqlite3

def cleanup_inactive_triggers():
    """비활성화된 트리거들을 완전히 삭제"""
    try:
        conn = sqlite3.connect('upbit_trading_unified.db')
        cursor = conn.cursor()
        
        # 삭제할 비활성화 트리거 확인
        cursor.execute("SELECT id, name FROM trading_conditions WHERE is_active = 0")
        inactive_triggers = cursor.fetchall()
        
        if inactive_triggers:
            print(f"삭제할 비활성화 트리거 {len(inactive_triggers)}개:")
            for trigger_id, name in inactive_triggers:
                print(f"  - ID {trigger_id}: {name}")
            
            # 사용자 확인
            confirm = input("\n이 트리거들을 완전히 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == 'yes':
                # 완전 삭제 실행
                cursor.execute("DELETE FROM trading_conditions WHERE is_active = 0")
                deleted_count = cursor.rowcount
                conn.commit()
                print(f"✅ {deleted_count}개 트리거 완전 삭제 완료")
            else:
                print("❌ 삭제 취소됨")
        else:
            print("✅ 삭제할 비활성화 트리거가 없습니다")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 정리 실패: {e}")

if __name__ == "__main__":
    cleanup_inactive_triggers()
