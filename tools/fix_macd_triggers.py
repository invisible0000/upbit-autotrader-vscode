#!/usr/bin/env python3
"""
MACD 트리거 수정 스크립트
현재 SMA로 잘못 변환된 MACD 트리거들을 올바른 MACD 외부변수로 재변환
"""

import sqlite3
import json
import datetime

def fix_macd_triggers():
    """MACD 트리거들을 올바르게 수정"""
    print("🔧 MACD 트리거 수정 시작")
    print("=" * 50)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        # MACD 관련 트리거 확인
        cursor.execute('''
            SELECT id, name, description, variable_id, external_variable, operator
            FROM trading_conditions 
            WHERE name LIKE '%MACD%'
        ''')
        
        macd_triggers = cursor.fetchall()
        
        print(f"📋 MACD 트리거 {len(macd_triggers)}개 발견:")
        for trigger in macd_triggers:
            id, name, desc, var_id, ext_var, operator = trigger
            print(f"   ID {id}: {name}")
            print(f"      variable_id: {var_id}")
            print(f"      operator: {operator}")
            if ext_var:
                try:
                    ext_var_obj = json.loads(ext_var)
                    print(f"      external_variable: {ext_var_obj.get('variable_id', 'N/A')}")
                except:
                    print(f"      external_variable: [파싱 오류]")
            print()
        
        # 수정 실행
        macd_fixes = []
        
        for trigger in macd_triggers:
            id, name, desc, var_id, ext_var, operator = trigger
            
            if 'golden' in name.lower() or '골든' in name:
                # MACD 골든크로스: MACD > MACD_Signal
                new_data = {
                    'variable_id': 'MACD',
                    'variable_params': {'fast': 12, 'slow': 26, 'signal': 9},
                    'external_variable': {
                        'variable_id': 'MACD_Signal', 
                        'variable_name': '📈 MACD 시그널',
                        'category': 'indicator',
                        'parameters': {'fast': 12, 'slow': 26, 'signal': 9}
                    },
                    'operator': '>',
                    'trend_direction': 'rising'
                }
            elif 'dead' in name.lower() or '데드' in name:
                # MACD 데드크로스: MACD < MACD_Signal
                new_data = {
                    'variable_id': 'MACD',
                    'variable_params': {'fast': 12, 'slow': 26, 'signal': 9},
                    'external_variable': {
                        'variable_id': 'MACD_Signal',
                        'variable_name': '📈 MACD 시그널', 
                        'category': 'indicator',
                        'parameters': {'fast': 12, 'slow': 26, 'signal': 9}
                    },
                    'operator': '<',
                    'trend_direction': 'falling'
                }
            else:
                continue
            
            macd_fixes.append((id, name, new_data))
        
        if not macd_fixes:
            print("✅ 수정할 MACD 트리거가 없습니다.")
            return
        
        print(f"🔄 {len(macd_fixes)}개 MACD 트리거 수정 중...")
        
        for id, name, new_data in macd_fixes:
            print(f"   수정 중: ID {id} - {name}")
            
            cursor.execute('''
                UPDATE trading_conditions 
                SET variable_id = ?,
                    variable_params = ?,
                    operator = ?, 
                    external_variable = ?,
                    trend_direction = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (
                new_data['variable_id'],
                json.dumps(new_data['variable_params']),
                new_data['operator'],
                json.dumps(new_data['external_variable']),
                new_data['trend_direction'],
                datetime.datetime.now().isoformat(),
                id
            ))
            
            print(f"      ✅ {new_data['variable_id']} {new_data['operator']} {new_data['external_variable']['variable_id']}")
        
        conn.commit()
        print(f"\n✅ MACD 트리거 수정 완료!")
        
        # 수정 결과 확인
        cursor.execute('''
            SELECT id, name, variable_id, operator, external_variable
            FROM trading_conditions 
            WHERE name LIKE '%MACD%'
        ''')
        
        updated_triggers = cursor.fetchall()
        
        print(f"\n📋 수정 후 MACD 트리거 상태:")
        for trigger in updated_triggers:
            id, name, var_id, operator, ext_var = trigger
            print(f"   ID {id}: {name}")
            print(f"      {var_id} {operator} ", end="")
            if ext_var:
                try:
                    ext_var_obj = json.loads(ext_var)
                    print(f"{ext_var_obj.get('variable_id', 'N/A')}")
                except:
                    print("[파싱 오류]")
            else:
                print("None")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 수정 실패: {e}")
        raise
    finally:
        conn.close()

def create_example_triggers_reference():
    """예시 트리거 생성을 위한 참고 자료 생성"""
    print(f"\n📚 예시 트리거 참고 자료 생성")
    print("=" * 50)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, description, variable_id, variable_params, 
                   operator, comparison_type, target_value, external_variable, 
                   trend_direction, category
            FROM trading_conditions 
            WHERE comparison_type = 'external' AND name LIKE 't_%'
            ORDER BY id
        ''')
        
        example_triggers = cursor.fetchall()
        
        reference_data = {
            'generated_at': datetime.datetime.now().isoformat(),
            'description': '올바른 외부변수 사용법 예시 - 새로운 트리거 생성 시 참고용',
            'examples': []
        }
        
        for trigger in example_triggers:
            id, name, desc, var_id, var_params, operator, comp_type, target_val, ext_var, trend_dir, category = trigger
            
            example = {
                'id': id,
                'name': name,
                'description': desc,
                'pattern': {
                    'variable_id': var_id,
                    'variable_params': json.loads(var_params) if var_params else {},
                    'operator': operator,
                    'comparison_type': comp_type,
                    'target_value': target_val,
                    'external_variable': json.loads(ext_var) if ext_var else None,
                    'trend_direction': trend_dir,
                    'category': category
                },
                'usage_note': f"이 패턴을 사용하여 {var_id} 변수의 외부변수 비교 트리거 생성 가능"
            }
            
            reference_data['examples'].append(example)
        
        # 파일로 저장
        ref_filename = f"trigger_examples_reference_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(ref_filename, 'w', encoding='utf-8') as f:
            json.dump(reference_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 참고 자료 생성 완료: {ref_filename}")
        print(f"📝 {len(reference_data['examples'])}개 예시 패턴 포함")
        
        # 주요 패턴 요약 출력
        print(f"\n📋 주요 패턴 요약:")
        for example in reference_data['examples']:
            pattern = example['pattern']
            ext_var = pattern['external_variable']
            if ext_var:
                print(f"   {pattern['variable_id']} {pattern['operator']} {ext_var['variable_id']}")
                print(f"      → {example['name']}")
            else:
                print(f"   {pattern['variable_id']} {pattern['operator']} {pattern['target_value']}")
                print(f"      → {example['name']} (고정값)")
            print()
        
        return ref_filename
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 MACD 트리거 수정 및 참고 자료 생성 시작!")
    print("📅 실행 시간:", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)
    
    try:
        # 1. MACD 트리거 수정
        fix_macd_triggers()
        
        # 2. 예시 트리거 참고 자료 생성
        ref_file = create_example_triggers_reference()
        
        print(f"\n🎯 완료!")
        print(f"   참고 자료: {ref_file}")
        print(f"   다음에 새로운 트리거 생성 시 이 파일을 참고하세요.")
        
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        import traceback
        traceback.print_exc()
