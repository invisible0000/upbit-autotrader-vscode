#!/usr/bin/env python3
"""
최종 트리거 상태 검증 스크립트
"""

import sqlite3
import json

def final_verification():
    """최종 트리거 상태 검증"""
    print("🔍 최종 트리거 상태 검증")
    print("=" * 60)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        # 전체 트리거 상태 확인
        cursor.execute('''
            SELECT id, name, variable_id, operator, comparison_type, 
                   target_value, external_variable, trend_direction
            FROM trading_conditions 
            ORDER BY id
        ''')
        
        all_triggers = cursor.fetchall()
        
        # 카테고리별 분류
        external_triggers = []
        fixed_triggers = []
        problem_triggers = []
        
        print(f"📋 전체 트리거: {len(all_triggers)}개\n")
        
        for trigger in all_triggers:
            id, name, var_id, operator, comp_type, target_val, ext_var, trend_dir = trigger
            
            if comp_type == 'external':
                external_triggers.append(trigger)
            elif comp_type in ['fixed', 'value'] and target_val and str(target_val).replace('.', '').replace('-', '').isdigit():
                fixed_triggers.append(trigger)
            else:
                problem_triggers.append(trigger)
        
        # 외부변수 사용 트리거들
        print(f"✅ 외부변수 사용 트리거: {len(external_triggers)}개")
        for trigger in external_triggers:
            id, name, var_id, operator, comp_type, target_val, ext_var, trend_dir = trigger
            ext_var_name = "None"
            if ext_var:
                try:
                    ext_var_obj = json.loads(ext_var)
                    ext_var_name = ext_var_obj.get('variable_id', 'Unknown')
                except:
                    ext_var_name = "[파싱오류]"
            
            print(f"   ID {id:2d}: {name}")
            print(f"         {var_id} {operator} {ext_var_name} ({trend_dir})")
        
        print()
        
        # 고정값 사용 트리거들
        print(f"✅ 고정값 사용 트리거: {len(fixed_triggers)}개")
        for trigger in fixed_triggers:
            id, name, var_id, operator, comp_type, target_val, ext_var, trend_dir = trigger
            print(f"   ID {id:2d}: {name}")
            print(f"         {var_id} {operator} {target_val}")
        
        print()
        
        # 문제가 있는 트리거들
        if problem_triggers:
            print(f"⚠️  문제가 있는 트리거: {len(problem_triggers)}개")
            for trigger in problem_triggers:
                id, name, var_id, operator, comp_type, target_val, ext_var, trend_dir = trigger
                print(f"   ID {id:2d}: {name}")
                print(f"         타입: {comp_type}, 비교값: {target_val}")
                
                # 문제 원인 분석
                if target_val and any(c.isalpha() for c in str(target_val)):
                    print(f"         ❌ 비교값에 문자가 포함됨 (변수명 가능성)")
                if comp_type not in ['external', 'fixed', 'value']:
                    print(f"         ❌ 지원하지 않는 비교 타입")
        else:
            print("✅ 모든 트리거가 정상 상태입니다!")
        
        print(f"\n📊 요약:")
        print(f"   외부변수 사용: {len(external_triggers)}개")
        print(f"   고정값 사용: {len(fixed_triggers)}개")  
        print(f"   문제 있음: {len(problem_triggers)}개")
        print(f"   총계: {len(all_triggers)}개")
        
        # 외부변수 패턴 분석
        print(f"\n📈 외부변수 패턴 분석:")
        patterns = {}
        for trigger in external_triggers:
            id, name, var_id, operator, comp_type, target_val, ext_var, trend_dir = trigger
            if ext_var:
                try:
                    ext_var_obj = json.loads(ext_var)
                    ext_var_id = ext_var_obj.get('variable_id', 'Unknown')
                    pattern = f"{var_id} {operator} {ext_var_id}"
                    if pattern not in patterns:
                        patterns[pattern] = []
                    patterns[pattern].append(name)
                except:
                    pass
        
        for pattern, names in patterns.items():
            print(f"   {pattern}: {len(names)}개")
            for name in names:
                print(f"      - {name}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    final_verification()
