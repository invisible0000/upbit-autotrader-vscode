#!/usr/bin/env python3
"""
새로운 문제점 조사 스크립트
사용자가 지적한 6가지 새로운 문제점에 대한 상세 조사
"""

import sqlite3
import json
from pathlib import Path

def investigate_new_issues():
    """새로운 문제점들 조사"""
    print("🔍 새로운 문제점 조사")
    print("=" * 50)
    
    # 1. 데드크로스 트리거 상태 확인
    print("\n1️⃣ 데드크로스 트리거 상태 확인")
    check_deadcross_triggers()
    
    # 2. 모든 외부변수 트리거 파라미터 확인
    print("\n2️⃣ 모든 외부변수 트리거 파라미터 확인")
    check_all_external_triggers()
    
    # 3. Parameter Factory 50봉 제한 확인
    print("\n6️⃣ Parameter Factory 50봉 제한 확인")
    check_parameter_factory_limits()

def check_deadcross_triggers():
    """데드크로스 트리거 상태 확인"""
    try:
        conn = sqlite3.connect("data/app_settings.sqlite3")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, variable_id, variable_params, external_variable 
            FROM trading_conditions 
            WHERE name LIKE '%데드크로스%'
        """)
        
        results = cursor.fetchall()
        
        print(f"📊 발견된 데드크로스 트리거: {len(results)}개")
        
        for trigger_id, name, variable_id, variable_params, external_variable_str in results:
            print(f"\n🔧 트리거: {name} (ID: {trigger_id})")
            print(f"  - 주 변수 ID: {variable_id}")
            print(f"  - 주 변수 파라미터: {variable_params}")
            
            if external_variable_str:
                try:
                    external_var = json.loads(external_variable_str)
                    print(f"  - 외부 변수 ID: {external_var.get('variable_id')}")
                    
                    # parameters 또는 variable_params 확인
                    ext_params = external_var.get('parameters') or external_var.get('variable_params')
                    print(f"  - 외부 변수 파라미터: {ext_params}")
                    
                    # 기간 정보 추출
                    if ext_params and isinstance(ext_params, dict) and 'period' in ext_params:
                        period = ext_params['period']
                        print(f"  - 외부 변수 기간: {period}일")
                        if period != 50 and "120, 50" in name:
                            print(f"    ⚠️  예상 기간(50일)과 다름!")
                    
                except json.JSONDecodeError as e:
                    print(f"  - ❌ 외부 변수 JSON 파싱 실패: {e}")
            else:
                print(f"  - 외부 변수: 없음")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류: {e}")

def check_all_external_triggers():
    """모든 외부변수 트리거 확인"""
    try:
        conn = sqlite3.connect("data/app_settings.sqlite3")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, variable_id, variable_params, external_variable, comparison_type
            FROM trading_conditions 
            WHERE comparison_type = 'external'
            ORDER BY id
        """)
        
        results = cursor.fetchall()
        
        print(f"📊 외부변수 트리거: {len(results)}개")
        
        for trigger_id, name, variable_id, variable_params, external_variable_str, comparison_type in results:
            print(f"\n🔧 {name} (ID: {trigger_id})")
            
            # 주 변수 파라미터 확인
            if variable_params:
                try:
                    main_params = json.loads(variable_params)
                    main_period = main_params.get('period', 'N/A')
                    print(f"  주변수: {variable_id} (기간: {main_period})")
                except json.JSONDecodeError:
                    print(f"  주변수: {variable_id} (파라미터 파싱 실패)")
            
            # 외부 변수 파라미터 확인  
            if external_variable_str:
                try:
                    external_var = json.loads(external_variable_str)
                    ext_var_id = external_var.get('variable_id')
                    ext_params = external_var.get('parameters') or external_var.get('variable_params')
                    
                    if ext_params and isinstance(ext_params, dict):
                        ext_period = ext_params.get('period', 'N/A')
                        print(f"  외부변수: {ext_var_id} (기간: {ext_period})")
                    else:
                        print(f"  외부변수: {ext_var_id} (파라미터 없음)")
                        
                except json.JSONDecodeError:
                    print(f"  외부변수: JSON 파싱 실패")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류: {e}")

def check_parameter_factory_limits():
    """Parameter Factory에서 50봉 제한 확인"""
    parameter_factory_file = "upbit_auto_trading/ui/desktop/screens/strategy_management/components/parameter_widgets.py"
    
    if Path(parameter_factory_file).exists():
        with open(parameter_factory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔧 Parameter Factory 파일 분석:")
        
        # SpinBox 최대값 설정 찾기
        import re
        spinbox_patterns = [
            r'setMaximum\((\d+)\)',
            r'setRange\([^,]+,\s*(\d+)\)',
            r'maximum.*=.*(\d+)',
            r'range.*50'
        ]
        
        found_limits = []
        for pattern in spinbox_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_limits.extend(matches)
        
        if found_limits:
            print(f"  📊 발견된 제한값들: {found_limits}")
            if '50' in found_limits:
                print("  ⚠️  50 제한값 발견!")
            if any(int(limit) > 50 for limit in found_limits if limit.isdigit()):
                print("  ✅ 50 초과 제한값도 존재")
        else:
            print("  📝 명시적인 제한값을 찾을 수 없음")
        
        # period 관련 설정 찾기
        if 'period' in content.lower():
            print("  📝 'period' 관련 설정 발견됨")
            
        # SMA 관련 설정 찾기  
        if 'sma' in content.lower():
            print("  📝 'SMA' 관련 설정 발견됨")
    else:
        print("❌ Parameter Factory 파일을 찾을 수 없음")

if __name__ == "__main__":
    investigate_new_issues()
