#!/usr/bin/env python3
"""
잘못된 데드크로스 트리거 수정 스크립트
"""

import sqlite3
import json
from datetime import datetime

def fix_deadcross_triggers():
    """잘못된 데드크로스 트리거들 수정"""
    print("🔧 잘못된 데드크로스 트리거 수정")
    
    conn = sqlite3.connect("data/app_settings.sqlite3")
    cursor = conn.cursor()
    
    try:
        # t_데드크로스 120, 50 트리거 수정 (ID: 22)
        print("\n1️⃣ t_데드크로스 120, 50 트리거 수정")
        
        external_variable_data = {
            "variable_id": "SMA",
            "variable_name": "📈 단순이동평균",
            "category": "indicator",
            "parameters": {
                "period": 50,
                "timeframe": "포지션 설정 따름"
            }
        }
        
        cursor.execute("""
            UPDATE trading_conditions 
            SET external_variable = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 22
        """, (json.dumps(external_variable_data, ensure_ascii=False),))
        
        print("  ✅ ID 22: 외부변수를 RSI → SMA(50)로 수정")
        
        # t_데드크로스 60 트리거도 확인하고 수정 (ID: 21)
        print("\n2️⃣ t_데드크로스 60 트리거 수정") 
        
        # 이름에서 기간 정보 추출 (60은 외부변수 기간으로 추정)
        external_variable_data_60 = {
            "variable_id": "SMA",
            "variable_name": "📈 단순이동평균", 
            "category": "indicator",
            "parameters": {
                "period": 60,
                "timeframe": "포지션 설정 따름"
            }
        }
        
        cursor.execute("""
            UPDATE trading_conditions 
            SET external_variable = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 21
        """, (json.dumps(external_variable_data_60, ensure_ascii=False),))
        
        print("  ✅ ID 21: 외부변수를 RSI → SMA(60)로 수정")
        
        # 변경사항 커밋
        conn.commit()
        
        # 수정 결과 확인
        print("\n📊 수정 결과 확인:")
        cursor.execute("""
            SELECT id, name, variable_id, variable_params, external_variable
            FROM trading_conditions 
            WHERE id IN (21, 22)
        """)
        
        for trigger_id, name, variable_id, variable_params, external_variable_str in cursor.fetchall():
            print(f"\n🔧 {name} (ID: {trigger_id})")
            
            # 주 변수 파라미터
            if variable_params:
                try:
                    main_params = json.loads(variable_params)
                    main_period = main_params.get('period', 'N/A')
                    print(f"  주변수: {variable_id} (기간: {main_period})")
                except json.JSONDecodeError:
                    print(f"  주변수: {variable_id} (파라미터 파싱 실패)")
            
            # 외부 변수 파라미터
            if external_variable_str:
                try:
                    external_var = json.loads(external_variable_str)
                    ext_var_id = external_var.get('variable_id')
                    ext_params = external_var.get('parameters', {})
                    ext_period = ext_params.get('period', 'N/A')
                    print(f"  외부변수: {ext_var_id} (기간: {ext_period})")
                except json.JSONDecodeError:
                    print(f"  외부변수: JSON 파싱 실패")
        
        print("\n✅ 데드크로스 트리거 수정 완료")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 오류: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_deadcross_triggers()
