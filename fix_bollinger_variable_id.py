#!/usr/bin/env python3
"""
볼린저밴드 variable_id 수정 스크립트
bb_20_2 -> BOLLINGER_BAND 로 변경
"""
import sqlite3
import json

def main():
    """메인 실행 함수"""
    print("🔧 볼린저밴드 variable_id 수정 스크립트 시작")
    print("="*80)
    
    # 데이터베이스 연결
    db_path = 'data/app_settings.sqlite3'
    print(f"📂 데이터베이스 연결: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. bb_20_2 variable_id를 가진 트리거 조회
        print("\n📊 bb_20_2 variable_id 트리거 조회...")
        cursor.execute("""
        SELECT id, name, description, variable_id, variable_params
        FROM trading_conditions 
        WHERE variable_id = 'bb_20_2'
        ORDER BY id
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("❌ bb_20_2 variable_id 트리거를 찾을 수 없습니다.")
            return
        
        print(f"✅ {len(results)}개의 bb_20_2 트리거 발견")
        print("-"*80)
        
        for row in results:
            id_, name, desc, var_id, var_params = row
            print(f"ID: {id_}")
            print(f"이름: {name}")
            print(f"현재 variable_id: {var_id}")
            print(f"현재 파라미터: {var_params}")
            print("-"*60)
        
        # 2. variable_id와 variable_name 업데이트
        print(f"\n🚀 {len(results)}개 트리거의 variable_id 업데이트 시작...")
        
        for row in results:
            id_, name, desc, var_id, var_params = row
            
            # variable_id와 variable_name 업데이트
            cursor.execute("""
            UPDATE trading_conditions 
            SET variable_id = 'BOLLINGER_BAND', 
                variable_name = '볼린저밴드'
            WHERE id = ?
            """, (id_,))
            
            print(f"📝 ID {id_} 업데이트: {var_id} -> BOLLINGER_BAND")
        
        # 변경사항 커밋
        conn.commit()
        print("✅ 모든 변경사항이 저장되었습니다!")
        
        # 업데이트 후 결과 확인
        print("\n📊 업데이트 후 결과 확인...")
        cursor.execute("""
        SELECT id, name, variable_id, variable_name, variable_params
        FROM trading_conditions 
        WHERE variable_id = 'BOLLINGER_BAND'
        ORDER BY id
        """)
        
        updated_results = cursor.fetchall()
        
        for row in updated_results:
            id_, name, var_id, var_name, var_params = row
            print(f"\n✅ ID {id_}: {name}")
            print(f"   변수 ID: {var_id}")
            print(f"   변수 이름: {var_name}")
            print(f"   파라미터: {var_params}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("\n📂 데이터베이스 연결 종료")
    
    print("\n🏁 스크립트 실행 완료!")

if __name__ == "__main__":
    main()
