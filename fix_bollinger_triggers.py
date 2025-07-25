#!/usr/bin/env python3
"""
볼린저밴드 트리거 DB 수정 스크립트
"""
import sqlite3
import json
from datetime import datetime

def main():
    """메인 실행 함수"""
    print("🔧 볼린저밴드 트리거 DB 수정 스크립트 시작")
    print("="*80)
    
    # 데이터베이스 연결
    db_path = 'data/app_settings.sqlite3'
    print(f"📂 데이터베이스 연결: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 현재 볼린저밴드 관련 트리거 조회
        print("\n📊 현재 볼린저밴드 관련 트리거 조회...")
        cursor.execute("""
        SELECT id, name, description, variable_id, variable_params, operator, target_value, 
               comparison_type, external_variable, trend_direction, created_at
        FROM trading_conditions 
        WHERE name LIKE '%볼린%' OR variable_id = 'bollinger_bands' OR variable_id = 'BOLLINGER_BAND'
        ORDER BY id
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("❌ 볼린저밴드 관련 트리거를 찾을 수 없습니다.")
            return
        
        print(f"✅ {len(results)}개의 볼린저밴드 관련 트리거 발견")
        print("-"*80)
        
        # 수정할 트리거들
        updates = []
        
        for row in results:
            id_, name, desc, var_id, var_params, operator, target_val, comp_type, ext_var, trend, created = row
            
            print(f"ID: {id_}")
            print(f"이름: {name}")
            print(f"설명: {desc}")
            print(f"변수 ID: {var_id}")
            print(f"변수 파라미터: {var_params}")
            print(f"연산자: {operator}")
            print(f"대상값: {target_val}")
            print(f"비교 타입: {comp_type}")
            print(f"외부 변수: {ext_var}")
            print(f"추세 방향: {trend}")
            print(f"생성일: {created}")
            print("-"*60)
            
            # 수정이 필요한 항목들 체크
            needs_update = False
            update_data = {}
            
            # 1. variable_id 수정 (bollinger_bands -> BOLLINGER_BAND)
            if var_id == 'bollinger_bands':
                update_data['variable_id'] = 'BOLLINGER_BAND'
                needs_update = True
                print(f"🔧 variable_id 수정: {var_id} -> BOLLINGER_BAND")
            
            # 2. target_value 수정 (bb_lower, bb_upper -> 현재가와 비교)
            if target_val in ['bb_lower', 'bb_upper']:
                if target_val == 'bb_lower':
                    # 하한선 터치는 현재가가 하단밴드보다 작거나 같을 때
                    update_data['comparison_type'] = 'external'
                    update_data['target_value'] = None
                    
                    # 외부변수로 현재가 설정
                    external_var_data = {
                        'variable_id': 'CURRENT_PRICE',
                        'variable_name': '현재가',
                        'category': 'price',
                        'variable_params': {
                            'price_type': '현재가',
                            'backtest_mode': '종가기준'
                        }
                    }
                    update_data['external_variable'] = json.dumps(external_var_data)
                    
                    # 볼린저밴드 파라미터에 하단 밴드 설정
                    if var_params:
                        try:
                            params = json.loads(var_params) if isinstance(var_params, str) else var_params
                        except:
                            params = {}
                    else:
                        params = {}
                    
                    params['band_position'] = '하단'
                    update_data['variable_params'] = json.dumps(params)
                    
                    print(f"🔧 하한선 터치 설정: 현재가 <= 볼린저밴드 하단")
                    
                elif target_val == 'bb_upper':
                    # 상한선 터치는 현재가가 상단밴드보다 크거나 같을 때  
                    update_data['comparison_type'] = 'external'
                    update_data['target_value'] = None
                    
                    # 외부변수로 현재가 설정
                    external_var_data = {
                        'variable_id': 'CURRENT_PRICE',
                        'variable_name': '현재가',
                        'category': 'price',
                        'variable_params': {
                            'price_type': '현재가',
                            'backtest_mode': '종가기준'
                        }
                    }
                    update_data['external_variable'] = json.dumps(external_var_data)
                    
                    # 볼린저밴드 파라미터에 상단 밴드 설정
                    if var_params:
                        try:
                            params = json.loads(var_params) if isinstance(var_params, str) else var_params
                        except:
                            params = {}
                    else:
                        params = {}
                    
                    params['band_position'] = '상단'
                    update_data['variable_params'] = json.dumps(params)
                    
                    print(f"🔧 상한선 터치 설정: 현재가 >= 볼린저밴드 상단")
                
                needs_update = True
            
            # 3. 추세 방향 기본값 설정
            if not trend or trend == 'static':
                update_data['trend_direction'] = 'both'
                needs_update = True
                print(f"🔧 추세 방향 수정: {trend} -> both")
            
            if needs_update:
                updates.append((id_, update_data))
        
        # 업데이트 실행
        if updates:
            print(f"\n🚀 {len(updates)}개 트리거 업데이트 시작...")
            
            for trigger_id, update_data in updates:
                # UPDATE 쿼리 생성
                set_clauses = []
                values = []
                
                for field, value in update_data.items():
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
                
                values.append(trigger_id)  # WHERE 조건용
                
                query = f"UPDATE trading_conditions SET {', '.join(set_clauses)} WHERE id = ?"
                
                print(f"📝 ID {trigger_id} 업데이트 실행...")
                cursor.execute(query, values)
            
            # 변경사항 커밋
            conn.commit()
            print("✅ 모든 변경사항이 저장되었습니다!")
            
            # 업데이트 후 결과 확인
            print("\n📊 업데이트 후 결과 확인...")
            cursor.execute("""
            SELECT id, name, variable_id, variable_params, operator, target_value, 
                   comparison_type, external_variable, trend_direction
            FROM trading_conditions 
            WHERE id IN ({})
            ORDER BY id
            """.format(','.join(str(uid) for uid, _ in updates)))
            
            updated_results = cursor.fetchall()
            
            for row in updated_results:
                id_, name, var_id, var_params, operator, target_val, comp_type, ext_var, trend = row
                print(f"\n✅ ID {id_}: {name}")
                print(f"   변수: {var_id}")
                print(f"   파라미터: {var_params}")
                print(f"   연산자: {operator}")
                print(f"   대상값: {target_val}")
                print(f"   비교 타입: {comp_type}")
                print(f"   외부 변수: {ext_var}")
                print(f"   추세 방향: {trend}")
        else:
            print("❌ 수정이 필요한 트리거가 없습니다.")
        
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
