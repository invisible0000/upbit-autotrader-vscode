#!/usr/bin/env python3
"""
외부변수 파라미터 긴급 수정 스크립트
골든크로스/데드크로스 트리거들의 외부변수 파라미터를 올바르게 수정
"""

import sqlite3
import json
import datetime

def fix_external_variable_parameters():
    """외부변수 파라미터 수정"""
    print("🔧 외부변수 파라미터 긴급 수정")
    print("=" * 50)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        # 수정이 필요한 트리거들 확인
        cursor.execute('''
            SELECT id, name, variable_id, external_variable
            FROM trading_conditions 
            WHERE comparison_type = 'external' 
            AND (name LIKE '%골든%' OR name LIKE '%데드%')
            ORDER BY id
        ''')
        
        triggers = cursor.fetchall()
        
        fixes_applied = []
        
        for trigger in triggers:
            id, name, var_id, ext_var_json = trigger
            
            if not ext_var_json:
                continue
                
            try:
                ext_var = json.loads(ext_var_json)
                current_params = ext_var.get('parameters') or ext_var.get('variable_params')
                
                print(f"🔍 검사 중: ID {id} - {name}")
                print(f"   외부변수: {ext_var.get('variable_id')}")
                print(f"   현재 파라미터: {current_params}")
                
                needs_fix = False
                new_ext_var = ext_var.copy()
                
                # SMA 골든크로스/데드크로스 수정
                if ext_var.get('variable_id') == 'SMA':
                    if not current_params or current_params.get('period') != 60:
                        # 60일 SMA로 설정
                        new_ext_var['parameters'] = {
                            'period': 60,
                            'timeframe': '포지션 설정 따름'
                        }
                        # 중복 필드 제거
                        if 'variable_params' in new_ext_var:
                            del new_ext_var['variable_params']
                        needs_fix = True
                        print(f"   → 수정: 60일 SMA로 설정")
                
                if needs_fix:
                    # DB 업데이트
                    cursor.execute('''
                        UPDATE trading_conditions 
                        SET external_variable = ?, updated_at = ?
                        WHERE id = ?
                    ''', (
                        json.dumps(new_ext_var, ensure_ascii=False),
                        datetime.datetime.now().isoformat(),
                        id
                    ))
                    
                    fixes_applied.append({
                        'id': id,
                        'name': name,
                        'old_params': current_params,
                        'new_params': new_ext_var.get('parameters')
                    })
                    
                    print(f"   ✅ 수정 완료")
                else:
                    print(f"   ✅ 이미 올바름")
                    
            except json.JSONDecodeError:
                print(f"   ❌ JSON 파싱 오류")
            
            print()
        
        if fixes_applied:
            conn.commit()
            print(f"🎯 수정 완료: {len(fixes_applied)}개 트리거")
            
            for fix in fixes_applied:
                print(f"   ID {fix['id']}: {fix['name']}")
                print(f"      {fix['old_params']} → {fix['new_params']}")
        else:
            print("✅ 수정할 트리거가 없습니다.")
        
        return fixes_applied
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 수정 실패: {e}")
        raise
    finally:
        conn.close()

def verify_fixes():
    """수정 결과 검증"""
    print(f"\n🔍 수정 결과 검증")
    print("=" * 50)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, variable_id, variable_params, external_variable
            FROM trading_conditions 
            WHERE comparison_type = 'external' 
            AND (name LIKE '%골든%' OR name LIKE '%데드%')
            ORDER BY id
        ''')
        
        triggers = cursor.fetchall()
        
        all_correct = True
        
        for trigger in triggers:
            id, name, var_id, var_params, ext_var_json = trigger
            
            print(f"📋 ID {id}: {name}")
            
            # 주 변수 파라미터
            if var_params:
                main_params = json.loads(var_params)
                main_period = main_params.get('period')
                print(f"   주 변수: {var_id} (기간: {main_period}일)")
            
            # 외부변수 파라미터
            if ext_var_json:
                ext_var = json.loads(ext_var_json)
                ext_params = ext_var.get('parameters') or ext_var.get('variable_params')
                ext_var_id = ext_var.get('variable_id')
                
                if ext_params:
                    ext_period = ext_params.get('period')
                    print(f"   외부변수: {ext_var_id} (기간: {ext_period}일)")
                    
                    # 골든크로스/데드크로스 검증
                    if ext_var_id == 'SMA':
                        if main_params.get('period') == 20 and ext_period == 60:
                            print(f"   ✅ 올바른 골든크로스/데드크로스 설정")
                        else:
                            print(f"   ❌ 기간 설정 오류: {main_params.get('period')}일 vs {ext_period}일")
                            all_correct = False
                else:
                    print(f"   ❌ 외부변수 파라미터 없음")
                    all_correct = False
            
            print()
        
        if all_correct:
            print("🎉 모든 트리거가 올바르게 설정되었습니다!")
        else:
            print("⚠️  일부 트리거에 여전히 문제가 있습니다.")
        
        return all_correct
        
    finally:
        conn.close()

def fix_ui_loading_logic():
    """UI 로딩 로직 수정 제안"""
    print(f"\n🔧 UI 로딩 로직 수정 필요 사항")
    print("=" * 50)
    
    print("""
📋 condition_dialog.py 수정이 필요한 부분:

1. load_condition() 메서드의 파라미터 복원 기능:
   현재: "TODO: 파라미터 값 복원 기능 구현 필요" 주석만 있음
   
   수정 필요:
   - 주 변수 파라미터 복원
   - 외부변수 파라미터 복원
   - parameter_factory를 통한 위젯 값 설정

2. 외부변수 파라미터 저장 위치 통일:
   현재: 'parameters'와 'variable_params' 혼재
   목표: 'parameters'로 통일

3. 파라미터 검증 로직 추가:
   - 골든크로스: 주변수 < 외부변수 기간 확인
   - 중복 기간 방지
   - 유효성 검사 강화

🎯 다음 단계:
1. 현재 DB 수정 완료 후
2. UI 로딩 로직 개선 작업 진행
3. 파라미터 복원 기능 완성
    """)

if __name__ == "__main__":
    print("🚀 외부변수 파라미터 긴급 수정 시작!")
    print("📅 실행 시간:", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)
    
    try:
        # 1. DB 데이터 수정
        fixes = fix_external_variable_parameters()
        
        # 2. 수정 결과 검증
        is_correct = verify_fixes()
        
        # 3. UI 로딩 로직 수정 가이드
        fix_ui_loading_logic()
        
        if fixes:
            print(f"\n🎯 완료 요약:")
            print(f"   수정된 트리거: {len(fixes)}개")
            print(f"   검증 결과: {'✅ 성공' if is_correct else '⚠️ 추가 작업 필요'}")
        
        print(f"\n📝 다음 작업: condition_dialog.py UI 로딩 로직 개선")
        
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        import traceback
        traceback.print_exc()
