#!/usr/bin/env python3
"""
볼린저밴드 트리거 누락 파라미터 수정 스크립트
ID:17의 timeframe 파라미터 추가
"""
import sqlite3
import json

def main():
    """메인 실행 함수"""
    print("🔧 볼린저밴드 누락 파라미터 수정 스크립트 시작")
    print("="*80)
    
    # 데이터베이스 연결
    db_path = 'data/app_settings.sqlite3'
    print(f"📂 데이터베이스 연결: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 볼린저밴드 트리거들 조회
        print("\n📊 볼린저밴드 트리거 조회...")
        cursor.execute("""
        SELECT id, name, variable_params
        FROM trading_conditions 
        WHERE variable_id = 'BOLLINGER_BAND'
        ORDER BY id
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("❌ 볼린저밴드 트리거를 찾을 수 없습니다.")
            return
        
        print(f"✅ {len(results)}개의 볼린저밴드 트리거 발견")
        print("-"*80)
        
        # Variable definitions에서 기본값 가져오기
        from upbit_auto_trading.ui.desktop.screens.strategy_management.components.variable_definitions import VariableDefinitions
        var_def = VariableDefinitions()
        bollinger_params = var_def.get_variable_parameters("BOLLINGER_BAND")
        
        print("📋 BOLLINGER_BAND 기본 파라미터:")
        for param_name, param_config in bollinger_params.items():
            default_val = param_config.get('default', 'N/A')
            print(f"  • {param_name}: {default_val}")
        print()
        
        updates_needed = []
        
        for row in results:
            id_, name, var_params_str = row
            
            print(f"🔍 ID {id_}: {name}")
            
            # 현재 파라미터 파싱
            try:
                if var_params_str:
                    current_params = json.loads(var_params_str)
                else:
                    current_params = {}
            except json.JSONDecodeError:
                current_params = {}
            
            print(f"   현재 파라미터: {current_params}")
            
            # 누락된 파라미터 찾기
            missing_params = []
            updated_params = current_params.copy()
            
            for param_name, param_config in bollinger_params.items():
                if param_name not in current_params:
                    default_value = param_config.get('default')
                    if default_value is not None:
                        updated_params[param_name] = default_value
                        missing_params.append(f"{param_name}={default_value}")
            
            if missing_params:
                print(f"   ⚠️  누락된 파라미터: {', '.join(missing_params)}")
                print(f"   ✅ 수정 후 파라미터: {updated_params}")
                updates_needed.append((id_, updated_params))
            else:
                print(f"   ✅ 모든 파라미터 완료")
            
            print("-"*60)
        
        # 업데이트 실행
        if updates_needed:
            print(f"\n🚀 {len(updates_needed)}개 트리거 파라미터 업데이트 시작...")
            
            for trigger_id, updated_params in updates_needed:
                updated_params_str = json.dumps(updated_params, ensure_ascii=False)
                
                cursor.execute("""
                UPDATE trading_conditions 
                SET variable_params = ?
                WHERE id = ?
                """, (updated_params_str, trigger_id))
                
                print(f"📝 ID {trigger_id} 파라미터 업데이트 완료")
            
            # 변경사항 커밋
            conn.commit()
            print("✅ 모든 변경사항이 저장되었습니다!")
            
            # 업데이트 후 결과 확인
            print("\n📊 업데이트 후 결과 확인...")
            trigger_ids = [str(uid) for uid, _ in updates_needed]
            cursor.execute(f"""
            SELECT id, name, variable_params
            FROM trading_conditions 
            WHERE id IN ({','.join(trigger_ids)})
            ORDER BY id
            """)
            
            updated_results = cursor.fetchall()
            
            for row in updated_results:
                id_, name, var_params = row
                print(f"\n✅ ID {id_}: {name}")
                try:
                    params = json.loads(var_params)
                    print(f"   📋 파라미터: {params}")
                except:
                    print(f"   📋 파라미터 (raw): {var_params}")
        else:
            print("\n✅ 모든 트리거가 완전한 파라미터를 가지고 있습니다.")
        
        # 실행 시 기본값 처리 로직 확인
        print("\n🔍 실행 시 파라미터 처리 방식:")
        print("1. UI에서 편집 시: 모든 파라미터가 명시적으로 저장됨")
        print("2. DB 직접 삽입 시: 누락된 파라미터는 실행 시 기본값 사용")
        print("3. 권장사항: 모든 파라미터를 명시적으로 저장하여 일관성 유지")
        
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
