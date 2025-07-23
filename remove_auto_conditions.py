import sqlite3

def remove_auto_generated_conditions():
    """[자동 생성] 조건들을 데이터베이스에서 삭제"""
    db_path = 'data/trading_conditions.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 삭제 전 확인
        cursor.execute("SELECT id, name, description FROM trading_conditions WHERE name LIKE '%자동 생성%'")
        auto_conditions = cursor.fetchall()
        
        if not auto_conditions:
            print("삭제할 [자동 생성] 조건이 없습니다.")
            return
        
        print("삭제될 조건들:")
        for condition in auto_conditions:
            print(f"  ID: {condition[0]}, 이름: {condition[1]}, 설명: {condition[2]}")
        
        # 확인 후 삭제
        response = input("\n이 조건들을 삭제하시겠습니까? (y/N): ")
        if response.lower() in ['y', 'yes']:
            cursor.execute("DELETE FROM trading_conditions WHERE name LIKE '%자동 생성%'")
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"\n✓ {deleted_count}개의 [자동 생성] 조건이 삭제되었습니다.")
        else:
            print("삭제가 취소되었습니다.")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    remove_auto_generated_conditions()
