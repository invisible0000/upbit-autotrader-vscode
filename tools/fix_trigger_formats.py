#!/usr/bin/env python3
"""
트리거 정규화 스크립트 - 비정상적인 트리거를 올바른 외부변수 형식으로 변환

참고: "t_골든크로스 20,60" (ID: 6)이 올바른 외부변수 사용법의 예시
- comparison_type: 'external' 
- external_variable: JSON 형태의 외부변수 정보
- target_value: None (외부변수 사용 시)
"""

import sqlite3
import json
import datetime
from typing import Dict, Any, List, Tuple

def analyze_current_triggers():
    """현재 트리거 상태 분석"""
    print("🔍 현재 트리거 상태 분석")
    print("=" * 60)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, description, variable_id, target_value, 
                   external_variable, comparison_type, operator, category
            FROM trading_conditions 
            ORDER BY id
        ''')
        
        triggers = cursor.fetchall()
        
        print(f"📋 총 {len(triggers)}개 트리거 발견\n")
        
        # 올바른 외부변수 사용 예시 (t_골든크로스)
        correct_examples = []
        # 수정이 필요한 트리거들
        needs_fix = []
        # 정상적인 고정값 트리거들
        normal_fixed = []
        
        for trigger in triggers:
            id, name, desc, var_id, target_val, ext_var, comp_type, operator, category = trigger
            
            if name.startswith("t_"):
                correct_examples.append(trigger)
                print(f"✅ 올바른 예시: ID {id} - {name}")
                print(f"   comparison_type: {comp_type}")
                print(f"   external_variable: {ext_var}")
                print(f"   target_value: {target_val}")
                print()
            elif comp_type in ['cross_up', 'cross_down'] or (target_val and any(c.isalpha() for c in str(target_val))):
                needs_fix.append(trigger)
                print(f"⚠️  수정 필요: ID {id} - {name}")
                print(f"   comparison_type: {comp_type}")
                print(f"   target_value: {target_val} (변수명으로 보임)")
                print()
            elif comp_type in ['fixed', 'value'] and target_val and str(target_val).replace('.', '').replace('-', '').isdigit():
                normal_fixed.append(trigger)
            else:
                print(f"🔍 기타: ID {id} - {name} (comp_type: {comp_type})")
        
        return correct_examples, needs_fix, normal_fixed
        
    finally:
        conn.close()

def create_conversion_plan(correct_examples: List, needs_fix: List) -> List[Dict]:
    """변환 계획 수립"""
    print("\n🎯 변환 계획 수립")
    print("=" * 60)
    
    if not correct_examples:
        print("❌ 올바른 예시 트리거를 찾을 수 없습니다.")
        return []
    
    # 올바른 예시에서 패턴 분석
    example = correct_examples[0]  # t_골든크로스 20,60 사용
    _, _, _, _, _, ext_var_json, _, _, _ = example
    
    if ext_var_json:
        try:
            example_ext_var = json.loads(ext_var_json)
            print(f"📋 올바른 외부변수 구조 (예시):")
            print(f"   {json.dumps(example_ext_var, ensure_ascii=False, indent=2)}")
        except:
            example_ext_var = None
    else:
        example_ext_var = None
    
    conversion_plans = []
    
    print(f"\n📝 수정 대상 트리거들:")
    
    for trigger in needs_fix:
        id, name, desc, var_id, target_val, ext_var, comp_type, operator, category = trigger
        
        plan = {
            'id': id,
            'name': name,
            'description': desc,
            'original': {
                'variable_id': var_id,
                'target_value': target_val,
                'comparison_type': comp_type,
                'external_variable': ext_var
            }
        }
        
        # 변환 로직
        if 'golden' in name.lower() or '골든' in name:
            # 골든크로스 패턴
            plan['action'] = 'convert_to_external'
            plan['new_data'] = {
                'variable_id': 'SMA',  # 20일 SMA
                'variable_params': {'period': 20, 'timeframe': '포지션 설정 따름'},
                'operator': '>',
                'comparison_type': 'external',
                'target_value': None,
                'external_variable': {
                    'variable_id': 'SMA',
                    'variable_name': '📈 단순이동평균',
                    'category': 'indicator',
                    'parameters': {'period': 60, 'timeframe': '포지션 설정 따름'}
                },
                'trend_direction': 'rising'
            }
        elif 'dead' in name.lower() or '데드' in name:
            # 데드크로스 패턴  
            plan['action'] = 'convert_to_external'
            plan['new_data'] = {
                'variable_id': 'SMA',  # 20일 SMA
                'variable_params': {'period': 20, 'timeframe': '포지션 설정 따름'},
                'operator': '<',
                'comparison_type': 'external', 
                'target_value': None,
                'external_variable': {
                    'variable_id': 'SMA',
                    'variable_name': '📈 단순이동평균',
                    'category': 'indicator',
                    'parameters': {'period': 60, 'timeframe': '포지션 설정 따름'}
                },
                'trend_direction': 'falling'
            }
        elif 'macd' in name.lower():
            # MACD 크로스 패턴
            if 'golden' in name.lower() or '골든' in name:
                operator = '>'
                trend = 'rising'
            else:
                operator = '<' 
                trend = 'falling'
                
            plan['action'] = 'convert_to_external'
            plan['new_data'] = {
                'variable_id': 'MACD',  # MACD 라인
                'variable_params': {'fast': 12, 'slow': 26, 'signal': 9},
                'operator': operator,
                'comparison_type': 'external',
                'target_value': None,
                'external_variable': {
                    'variable_id': 'MACD_Signal',
                    'variable_name': '📈 MACD 시그널',
                    'category': 'indicator', 
                    'parameters': {'fast': 12, 'slow': 26, 'signal': 9}
                },
                'trend_direction': trend
            }
        else:
            plan['action'] = 'manual_review'
            plan['reason'] = '자동 변환 패턴을 찾을 수 없음'
        
        conversion_plans.append(plan)
        
        print(f"\n📋 ID {id}: {name}")
        print(f"   현재: {comp_type} / target: {target_val}")
        print(f"   계획: {plan['action']}")
        if plan['action'] == 'convert_to_external':
            print(f"   변환 후: {plan['new_data']['variable_id']} {plan['new_data']['operator']} 외부변수")
    
    return conversion_plans

def execute_conversions(conversion_plans: List[Dict]):
    """변환 실행"""
    print(f"\n🔧 변환 실행")
    print("=" * 60)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        backup_info = []
        conversion_log = []
        
        for plan in conversion_plans:
            if plan['action'] == 'convert_to_external':
                trigger_id = plan['id']
                new_data = plan['new_data']
                
                print(f"🔄 변환 중: ID {trigger_id} - {plan['name']}")
                
                # 백업 정보 저장
                cursor.execute('SELECT * FROM trading_conditions WHERE id = ?', (trigger_id,))
                original_data = cursor.fetchone()
                backup_info.append({
                    'id': trigger_id,
                    'original': original_data,
                    'timestamp': datetime.datetime.now().isoformat()
                })
                
                # 새 데이터로 업데이트
                cursor.execute('''
                    UPDATE trading_conditions 
                    SET variable_id = ?,
                        variable_params = ?,
                        operator = ?,
                        comparison_type = ?,
                        target_value = ?,
                        external_variable = ?,
                        trend_direction = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (
                    new_data['variable_id'],
                    json.dumps(new_data['variable_params']),
                    new_data['operator'],
                    new_data['comparison_type'],
                    new_data['target_value'],
                    json.dumps(new_data['external_variable']),
                    new_data['trend_direction'],
                    datetime.datetime.now().isoformat(),
                    trigger_id
                ))
                
                conversion_log.append({
                    'id': trigger_id,
                    'name': plan['name'],
                    'action': 'converted',
                    'timestamp': datetime.datetime.now().isoformat()
                })
                
                print(f"   ✅ 완료")
                
            elif plan['action'] == 'manual_review':
                print(f"⚠️  수동 검토 필요: ID {plan['id']} - {plan['name']}")
                print(f"   사유: {plan['reason']}")
                
                conversion_log.append({
                    'id': plan['id'],
                    'name': plan['name'],
                    'action': 'manual_review_needed',
                    'reason': plan['reason'],
                    'timestamp': datetime.datetime.now().isoformat()
                })
        
        conn.commit()
        
        # 백업 파일 저장
        backup_filename = f"trigger_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)
        
        # 변환 로그 저장
        log_filename = f"trigger_conversion_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(conversion_log, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 변환 완료!")
        print(f"   백업 파일: {backup_filename}")
        print(f"   로그 파일: {log_filename}")
        
        return backup_filename, log_filename
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 변환 실패: {e}")
        raise
    finally:
        conn.close()

def verify_conversions():
    """변환 결과 검증"""
    print(f"\n🔍 변환 결과 검증")
    print("=" * 60)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, comparison_type, target_value, external_variable
            FROM trading_conditions 
            WHERE comparison_type = 'external'
            ORDER BY id
        ''')
        
        external_triggers = cursor.fetchall()
        
        print(f"📋 외부변수 사용 트리거: {len(external_triggers)}개")
        
        for trigger in external_triggers:
            id, name, comp_type, target_val, ext_var = trigger
            print(f"   ID {id}: {name}")
            print(f"      comparison_type: {comp_type}")
            print(f"      target_value: {target_val}")
            if ext_var:
                try:
                    ext_var_obj = json.loads(ext_var)
                    print(f"      external_variable: {ext_var_obj.get('variable_id', 'N/A')}")
                except:
                    print(f"      external_variable: [파싱 오류]")
            print()
        
        # 문제가 있는 트리거 확인
        cursor.execute('''
            SELECT id, name, comparison_type, target_value
            FROM trading_conditions 
            WHERE (comparison_type NOT IN ('external', 'fixed', 'value') 
                   OR (comparison_type IN ('fixed', 'value') AND target_value LIKE '%ma_%'))
            ORDER BY id
        ''')
        
        problem_triggers = cursor.fetchall()
        
        if problem_triggers:
            print(f"⚠️  여전히 문제가 있는 트리거: {len(problem_triggers)}개")
            for trigger in problem_triggers:
                id, name, comp_type, target_val = trigger
                print(f"   ID {id}: {name} ({comp_type}, {target_val})")
        else:
            print("✅ 모든 트리거가 정상적으로 변환되었습니다!")
            
    finally:
        conn.close()

def main():
    """메인 실행 함수"""
    print("🚀 트리거 정규화 스크립트 시작!")
    print("📅 실행 시간:", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 80)
    
    try:
        # 1. 현재 상태 분석
        correct_examples, needs_fix, normal_fixed = analyze_current_triggers()
        
        if not needs_fix:
            print("✅ 수정이 필요한 트리거가 없습니다!")
            return
        
        # 2. 변환 계획 수립
        conversion_plans = create_conversion_plan(correct_examples, needs_fix)
        
        if not conversion_plans:
            print("❌ 변환 계획을 수립할 수 없습니다.")
            return
        
        # 3. 사용자 확인
        print(f"\n🤔 {len([p for p in conversion_plans if p['action'] == 'convert_to_external'])}개 트리거를 변환하시겠습니까?")
        response = input("계속하려면 'yes'를 입력하세요: ").lower().strip()
        
        if response != 'yes':
            print("❌ 변환이 취소되었습니다.")
            return
        
        # 4. 변환 실행
        backup_file, log_file = execute_conversions(conversion_plans)
        
        # 5. 결과 검증
        verify_conversions()
        
        print(f"\n🎯 완료 요약:")
        print(f"   백업: {backup_file}")
        print(f"   로그: {log_file}")
        print(f"   다음에 이 스크립트를 참고하여 예시 트리거 생성 가능")
        
    except Exception as e:
        print(f"❌ 스크립트 실행 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
