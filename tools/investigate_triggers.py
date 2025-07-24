#!/usr/bin/env python3
"""
골든크로스/데드크로스 트리거 조사 스크립트
비교값에 ma_60이 있는 트리거들을 분석
"""

import sqlite3
import json
import sys
import os

def investigate_triggers():
    """골든크로스/데드크로스 트리거 조사"""
    db_path = "data/app_settings.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 골든크로스/데드크로스 트리거 조사 시작")
        print("=" * 60)
        
        # 1. 골든크로스/데드크로스 관련 트리거 검색
        search_patterns = ["%골든%", "%데드%", "%golden%", "%dead%", "%ma_%"]
        all_triggers = []
        
        for pattern in search_patterns:
            cursor.execute('''
                SELECT id, name, description, variable_id, target_value, 
                       external_variable, comparison_type, operator, trend_direction,
                       variable_params, created_at
                FROM trading_conditions 
                WHERE name LIKE ? OR description LIKE ? OR target_value LIKE ?
            ''', (pattern, pattern, pattern))
            
            triggers = cursor.fetchall()
            for trigger in triggers:
                if trigger not in all_triggers:
                    all_triggers.append(trigger)
        
        print(f"📋 발견된 관련 트리거: {len(all_triggers)}개")
        print()
        
        # 2. 각 트리거 상세 분석
        for i, trigger in enumerate(all_triggers, 1):
            print(f"🎯 트리거 #{i}")
            print(f"   ID: {trigger[0]}")
            print(f"   이름: {trigger[1]}")
            print(f"   설명: {trigger[2]}")
            print(f"   변수 ID: {trigger[3]}")
            print(f"   비교값: {trigger[4]}")
            print(f"   외부변수: {trigger[5]}")
            print(f"   비교타입: {trigger[6]}")
            print(f"   연산자: {trigger[7]}")
            print(f"   추세방향: {trigger[8]}")
            print(f"   변수파라미터: {trigger[9]}")
            print(f"   생성일시: {trigger[10]}")
            
            # 외부변수 정보 파싱
            if trigger[5]:  # external_variable이 있는 경우
                try:
                    external_var = json.loads(trigger[5])
                    print(f"   🔗 외부변수 상세:")
                    print(f"      - 변수 ID: {external_var.get('variable_id', 'N/A')}")
                    print(f"      - 변수명: {external_var.get('variable_name', 'N/A')}")
                    print(f"      - 카테고리: {external_var.get('category', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"   🔗 외부변수 (파싱 실패): {trigger[5]}")
            
            # 변수 파라미터 파싱
            if trigger[9]:  # variable_params가 있는 경우
                try:
                    var_params = json.loads(trigger[9])
                    print(f"   📊 변수 파라미터:")
                    for key, value in var_params.items():
                        print(f"      - {key}: {value}")
                except json.JSONDecodeError:
                    print(f"   📊 변수 파라미터 (파싱 실패): {trigger[9]}")
            
            print("-" * 40)
        
        # 3. 특별히 ma_60이 비교값에 있는 트리거들 검색
        print("\n🔍 비교값에 'ma_60'이 포함된 트리거들:")
        print("=" * 50)
        
        cursor.execute('''
            SELECT id, name, description, variable_id, target_value, 
                   external_variable, comparison_type
            FROM trading_conditions 
            WHERE target_value LIKE '%ma_60%'
        ''')
        
        ma60_triggers = cursor.fetchall()
        
        if ma60_triggers:
            for trigger in ma60_triggers:
                print(f"🎯 ID: {trigger[0]}")
                print(f"   이름: {trigger[1]}")
                print(f"   설명: {trigger[2]}")
                print(f"   변수 ID: {trigger[3]}")
                print(f"   비교값: '{trigger[4]}'")
                print(f"   외부변수: {trigger[5]}")
                print(f"   비교타입: {trigger[6]}")
                print()
                
                # 이것이 실제 동작 방식인지 분석
                print("   💡 분석:")
                if trigger[6] == 'fixed' and 'ma_60' in str(trigger[4]):
                    print("   ⚠️  이 트리거는 'fixed' 비교 타입이지만 비교값에 'ma_60'이 있습니다!")
                    print("   ⚠️  이는 비정상적인 상태로 보입니다.")
                    print("   ✅ 정상적인 외부변수 사용은 comparison_type='external'이어야 합니다.")
                elif trigger[6] == 'external':
                    print("   ✅ 외부변수를 올바르게 사용하는 트리거입니다.")
                
                print("-" * 30)
        else:
            print("📝 비교값에 'ma_60'이 포함된 트리거를 찾지 못했습니다.")
        
        # 4. 모든 트리거의 비교타입 통계
        print("\n📊 전체 트리거 비교타입 통계:")
        print("=" * 40)
        
        cursor.execute('''
            SELECT comparison_type, COUNT(*) as count
            FROM trading_conditions 
            GROUP BY comparison_type
        ''')
        
        stats = cursor.fetchall()
        total = sum(stat[1] for stat in stats)
        
        for stat in stats:
            comp_type = stat[0] if stat[0] else "NULL"
            count = stat[1]
            percentage = (count / total * 100) if total > 0 else 0
            print(f"   {comp_type}: {count}개 ({percentage:.1f}%)")
        
        print(f"\n총 트리거 수: {total}개")
        
    except Exception as e:
        print(f"❌ 조사 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

def analyze_condition_loading():
    """조건 로딩 로직 분석"""
    print("\n" + "=" * 60)
    print("🔍 조건 로딩 로직 분석")
    print("=" * 60)
    
    print("""
📋 현재 condition_dialog.py의 load_condition 메서드 분석:

1. 비교 타입 판단 로직:
   - comparison_type이 'external'이고 external_variable이 있으면 → 외부변수 모드
   - 그렇지 않으면 → 고정값 모드에서 target_value를 비교값 입력창에 설정

2. 문제 상황:
   - DB에 comparison_type='fixed'이지만 target_value='ma_60'인 트리거가 있다면?
   - → 외부변수 모드가 아니므로 'ma_60'이 비교값 입력창에 그대로 표시됨
   - → 이는 의도된 동작이 아닐 가능성이 높음

3. 예상 원인:
   - 에이전트가 DB에 직접 등록할 때 comparison_type을 잘못 설정
   - 또는 target_value에 변수명을 직접 입력
   - 정상적인 외부변수 사용은 external_variable 필드에 JSON으로 저장되어야 함

4. 검증 방법:
   - 해당 트리거들이 실제로 동작하는지 확인
   - 전략 실행 엔진에서 'ma_60'을 어떻게 해석하는지 확인
    """)

if __name__ == "__main__":
    print("🚀 골든크로스/데드크로스 트리거 조사 시작!")
    investigate_triggers()
    analyze_condition_loading()
    print("\n✅ 조사 완료!")
