#!/usr/bin/env python3
"""
트리거 파라미터 복원 테스트 스크립트
데이터베이스에서 골든크로스 트리거를 읽어와서 UI에서 파라미터가 제대로 복원되는지 확인
"""

import sqlite3
import json
from pathlib import Path

# 데이터베이스 경로
DB_PATH = "data/app_settings.sqlite3"

def test_parameter_restoration():
    """파라미터 복원 테스트"""
    print("🔍 파라미터 복원 시스템 테스트 시작")
    
    # 데이터베이스 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 골든크로스 트리거 조회
        cursor.execute("""
            SELECT id, name, variable_id, variable_params, operator, 
                   comparison_type, target_value, external_variable, 
                   trend_direction
            FROM trading_conditions 
            WHERE name LIKE '%골든크로스%' 
            ORDER BY id
        """)
        
        golden_triggers = cursor.fetchall()
        
        print(f"📊 발견된 골든크로스 트리거: {len(golden_triggers)}개")
        
        for row in golden_triggers:
            (trigger_id, name, variable_id, variable_params, operator, 
             comparison_type, target_value, external_variable_str, trend_direction) = row
            print(f"\n🔧 트리거 분석: {name} (ID: {trigger_id})")
            
            try:
                # 외부 변수 파싱
                external_variable = None
                if external_variable_str:
                    external_variable = json.loads(external_variable_str)
                
                # 주 변수 파라미터 분석
                print(f"  - 주 변수 ID: {variable_id}")
                print(f"  - 주 변수 파라미터: {variable_params}")
                
                if variable_params:
                    try:
                        parsed_params = json.loads(variable_params)
                        print(f"  - 파싱된 파라미터: {parsed_params}")
                        
                        # SMA 기간 확인
                        if 'period' in parsed_params:
                            print(f"  ✅ SMA 기간: {parsed_params['period']}일")
                        else:
                            print("  ❌ SMA 기간 정보 없음")
                            
                    except json.JSONDecodeError as e:
                        print(f"  ❌ 파라미터 파싱 실패: {e}")
                
                # 외부 변수 파라미터 분석
                if external_variable:
                    ext_var_id = external_variable.get('variable_id')
                    ext_var_params = external_variable.get('variable_params') or external_variable.get('parameters')
                    
                    print(f"  - 외부 변수 ID: {ext_var_id}")
                    print(f"  - 외부 변수 파라미터: {ext_var_params}")
                    
                    if ext_var_params:
                        if isinstance(ext_var_params, str):
                            try:
                                parsed_ext_params = json.loads(ext_var_params)
                                print(f"  - 파싱된 외부 파라미터: {parsed_ext_params}")
                                
                                # SMA 기간 확인
                                if 'period' in parsed_ext_params:
                                    print(f"  ✅ 외부 SMA 기간: {parsed_ext_params['period']}일")
                                else:
                                    print("  ❌ 외부 SMA 기간 정보 없음")
                                    
                            except json.JSONDecodeError as e:
                                print(f"  ❌ 외부 파라미터 파싱 실패: {e}")
                        elif isinstance(ext_var_params, dict):
                            print(f"  - 외부 파라미터 (dict): {ext_var_params}")
                            if 'period' in ext_var_params:
                                print(f"  ✅ 외부 SMA 기간: {ext_var_params['period']}일")
                
                print(f"  - 연산자: {operator}")
                print(f"  - 비교 타입: {comparison_type}")
                print(f"  - 추세방향: {trend_direction}")
                
            except json.JSONDecodeError as e:
                print(f"  ❌ 외부 변수 파싱 실패: {e}")
        
        # 20일 vs 60일 SMA 조합 확인
        print("\n📈 골든크로스 파라미터 조합 분석:")
        for row in golden_triggers:
            (trigger_id, name, variable_id, variable_params, operator, 
             comparison_type, target_value, external_variable_str, trend_direction) = row
            
            try:
                # 주 변수 파라미터
                main_period = None
                if variable_params:
                    try:
                        parsed = json.loads(variable_params)
                        main_period = parsed.get('period')
                    except json.JSONDecodeError:
                        pass
                
                # 외부 변수 파라미터
                ext_period = None
                if external_variable_str:
                    external_variable = json.loads(external_variable_str)
                    ext_params = external_variable.get('variable_params') or external_variable.get('parameters')
                    if ext_params:
                        if isinstance(ext_params, str):
                            try:
                                parsed = json.loads(ext_params)
                                ext_period = parsed.get('period')
                            except json.JSONDecodeError:
                                pass
                        elif isinstance(ext_params, dict):
                            ext_period = ext_params.get('period')
                
                if main_period and ext_period:
                    print(f"  {name}: SMA{main_period} vs SMA{ext_period}")
                    if main_period == 20 and ext_period == 60:
                        print("    ✅ 올바른 골든크로스 조합 (20일 > 60일)")
                    elif main_period == 60 and ext_period == 20:
                        print("    ⚠️  반대 조합 (60일 > 20일)")
                    else:
                        print(f"    ❓ 기타 조합 ({main_period}일 vs {ext_period}일)")
                else:
                    print(f"  {name}: 파라미터 정보 불완전 (main:{main_period}, ext:{ext_period})")
                    
            except json.JSONDecodeError:
                print(f"  {name}: 데이터 파싱 실패")
        
        print("\n✅ 파라미터 복원 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_parameter_restoration()
