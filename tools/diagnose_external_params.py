#!/usr/bin/env python3
"""
외부변수 파라미터 문제 진단 스크립트
골든크로스 트리거들의 외부변수 파라미터가 올바르게 저장/로드되는지 확인
"""

import sqlite3
import json
from typing import Dict, Any

def diagnose_external_variable_parameters():
    """외부변수 파라미터 문제 진단"""
    print("🔍 외부변수 파라미터 문제 진단")
    print("=" * 60)
    
    conn = sqlite3.connect('data/app_settings.sqlite3')
    cursor = conn.cursor()
    
    try:
        # 골든크로스/데드크로스 관련 외부변수 트리거들 조회
        cursor.execute('''
            SELECT id, name, description, variable_id, variable_params, 
                   operator, external_variable, trend_direction
            FROM trading_conditions 
            WHERE comparison_type = 'external' 
            AND (name LIKE '%골든%' OR name LIKE '%데드%' OR name LIKE '%golden%' OR name LIKE '%dead%')
            ORDER BY id
        ''')
        
        triggers = cursor.fetchall()
        
        print(f"📋 골든크로스/데드크로스 외부변수 트리거: {len(triggers)}개\n")
        
        for trigger in triggers:
            id, name, desc, var_id, var_params, operator, ext_var, trend_dir = trigger
            
            print(f"🎯 ID {id}: {name}")
            print(f"   설명: {desc}")
            print(f"   주 변수: {var_id}")
            
            # 주 변수 파라미터 분석
            if var_params:
                try:
                    main_params = json.loads(var_params)
                    print(f"   주 변수 파라미터: {main_params}")
                    main_period = main_params.get('period', 'N/A')
                    print(f"      → 주 변수 기간: {main_period}일")
                except json.JSONDecodeError:
                    print(f"   주 변수 파라미터: [파싱 오류] {var_params}")
            else:
                print(f"   주 변수 파라미터: None")
            
            # 외부변수 파라미터 분석
            if ext_var:
                try:
                    ext_var_obj = json.loads(ext_var)
                    print(f"   외부변수: {ext_var_obj.get('variable_id', 'N/A')}")
                    
                    # parameters vs variable_params 확인
                    ext_params = ext_var_obj.get('parameters')
                    ext_var_params = ext_var_obj.get('variable_params')
                    
                    if ext_params:
                        print(f"   외부변수 파라미터 (parameters): {ext_params}")
                        ext_period = ext_params.get('period', 'N/A')
                        print(f"      → 외부변수 기간: {ext_period}일")
                    elif ext_var_params:
                        print(f"   외부변수 파라미터 (variable_params): {ext_var_params}")
                        ext_period = ext_var_params.get('period', 'N/A')
                        print(f"      → 외부변수 기간: {ext_period}일")
                    else:
                        print(f"   외부변수 파라미터: 없음")
                        print(f"      ❌ 외부변수에 파라미터가 없습니다!")
                    
                    # 골든크로스/데드크로스 검증
                    if '골든' in name or 'golden' in name.lower():
                        expected_main = 20
                        expected_ext = 60
                    elif '데드' in name or 'dead' in name.lower():
                        expected_main = 20
                        expected_ext = 60
                    else:
                        expected_main = None
                        expected_ext = None
                    
                    if expected_main and expected_ext:
                        # 실제 파라미터와 기대값 비교
                        actual_main = main_params.get('period') if var_params else None
                        actual_ext = (ext_params or ext_var_params or {}).get('period') if (ext_params or ext_var_params) else None
                        
                        print(f"   📊 검증:")
                        print(f"      기대값: {expected_main}일 > {expected_ext}일")
                        print(f"      실제값: {actual_main}일 > {actual_ext}일")
                        
                        if actual_main == expected_main and actual_ext == expected_ext:
                            print(f"      ✅ 올바름")
                        else:
                            print(f"      ❌ 문제 발견!")
                            if actual_main != expected_main:
                                print(f"         주 변수 기간 불일치: {actual_main} ≠ {expected_main}")
                            if actual_ext != expected_ext:
                                print(f"         외부변수 기간 불일치: {actual_ext} ≠ {expected_ext}")
                    
                except json.JSONDecodeError:
                    print(f"   외부변수: [파싱 오류] {ext_var}")
            else:
                print(f"   외부변수: None")
            
            print(f"   연산자: {operator}")
            print(f"   추세방향: {trend_dir}")
            print("-" * 50)
        
        return triggers
        
    finally:
        conn.close()

def analyze_db_structure_issues():
    """DB 구조 문제점 분석"""
    print(f"\n🔍 DB 구조 문제점 분석")
    print("=" * 60)
    
    print("""
📋 발견된 문제점들:

1. 외부변수 파라미터 저장 방식 불일치:
   - 일부는 'parameters' 필드에 저장
   - 일부는 'variable_params' 필드에 저장
   - 표준화되지 않은 구조

2. 골든크로스/데드크로스 파라미터 누락:
   - 20일 vs 60일 이동평균 비교가 목적
   - 외부변수에 60일 파라미터가 누락되거나 잘못됨
   - 주 변수와 외부변수 모두 기본값(20일) 사용 가능성

3. UI 로딩 로직 문제:
   - condition_dialog.py의 load_condition()에서
   - 외부변수 파라미터 복원 기능이 미완성
   - "TODO: 파라미터 값 복원 기능 구현 필요" 주석 존재

4. 백테스팅/실시간 거래 영향:
   - 잘못된 파라미터로 인한 전략 오작동 가능성
   - 20일 vs 20일 비교 = 골든크로스 의미 없음
   - 실제 의도: 20일 vs 60일 비교
    """)

def suggest_fixes():
    """수정 방안 제안"""
    print(f"\n🔧 수정 방안 제안")
    print("=" * 60)
    
    print("""
🎯 단기 수정 (즉시 적용 가능):

1. DB 데이터 직접 수정:
   - 골든크로스/데드크로스 트리거들의 외부변수 파라미터 수정
   - 외부변수 period를 60으로 설정
   - parameters와 variable_params 필드 표준화

2. UI 로딩 로직 수정:
   - condition_dialog.py의 load_condition() 개선
   - 외부변수 파라미터 복원 기능 완성
   - 파라미터 위젯에 저장된 값 올바르게 설정

🎯 중기 수정 (구조적 개선):

3. DB 스키마 개선:
   - 외부변수 파라미터 저장 방식 표준화
   - JSON 구조 일관성 확보
   - 버전 마이그레이션 스크립트 작성

4. 검증 로직 추가:
   - 트리거 저장 시 파라미터 유효성 검증
   - 골든크로스/데드크로스 파라미터 자동 검증
   - 중복 기간 방지 (예: 20일 vs 20일)

🎯 장기 수정 (아키텍처 개선):

5. 크로스 전용 트리거 타입 추가:
   - golden_cross, dead_cross 전용 comparison_type
   - 자동 파라미터 생성 및 검증
   - UI에서 크로스 전용 설정 모드 제공
    """)

if __name__ == "__main__":
    print("🚀 외부변수 파라미터 문제 진단 시작!")
    print("📅 실행 시간:", __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 80)
    
    try:
        # 1. 현재 상태 진단
        triggers = diagnose_external_variable_parameters()
        
        # 2. 문제점 분석
        analyze_db_structure_issues()
        
        # 3. 수정 방안 제안
        suggest_fixes()
        
        print(f"\n🎯 다음 단계:")
        print(f"   1. DB 데이터 직접 수정 스크립트 실행")
        print(f"   2. UI 로딩 로직 개선")
        print(f"   3. 수정 후 백테스팅으로 검증")
        
    except Exception as e:
        print(f"❌ 진단 실패: {e}")
        import traceback
        traceback.print_exc()
