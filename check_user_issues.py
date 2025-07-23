#!/usr/bin/env python3
"""
사용자 문제 해결 스크립트
1. 조건명 특수문자 제한 완화
2. t_ 시작 트리거 DB 확인
3. 편집 기능 디버깅
4. condition/trigger 용어 통일 제안
"""

import sqlite3
import os
import re
from typing import List, Tuple

def check_condition_name_restrictions():
    """1. 조건명 특수문자 제한 확인 및 완화"""
    print("=" * 60)
    print("1️⃣ 조건명 특수문자 제한 확인")
    print("=" * 60)
    
    # 현재 제한사항 확인
    validator_file = "components/condition_validator.py"
    if os.path.exists(validator_file):
        with open(validator_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 현재 제한 패턴 찾기
        pattern_match = re.search(r"re\.search\(r'([^']+)', name\)", content)
        if pattern_match:
            current_pattern = pattern_match.group(1)
            print(f"📋 현재 제한 패턴: {current_pattern}")
            print(f"   제한 문자: < > \" | \\")
            
            # 완화된 패턴 제안
            new_pattern = r'["|\\]'  # < > | 제거, " \ 만 유지
            print(f"🔄 제안 패턴: {new_pattern}")
            print(f"   제한 문자: \" \\ (SQL 인젝션 방지용)")
            print("✅ < > | 기호는 수학적 표현에 유용하므로 허용 가능")
        else:
            print("❌ 패턴을 찾을 수 없습니다.")
    else:
        print(f"❌ {validator_file} 파일을 찾을 수 없습니다.")

def check_t_triggers_in_db():
    """2. t_ 시작 트리거 DB 확인"""
    print("\n" + "=" * 60)
    print("2️⃣ t_ 시작 트리거 DB 확인")
    print("=" * 60)
    
    db_path = "upbit_trading_unified.db"
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일 없음: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # t_ 시작하는 트리거 조회
        cursor.execute("""
            SELECT id, name, description, variable_id, operator, target_value, created_at
            FROM trading_conditions 
            WHERE name LIKE 't_%'
            ORDER BY created_at DESC
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"✅ {len(results)}개의 t_ 트리거 발견:")
            for row in results:
                id_, name, desc, var_id, operator, target, created = row
                print(f"  📋 ID: {id_}")
                print(f"     이름: {name}")
                print(f"     설명: {desc}")
                print(f"     변수: {var_id}")
                print(f"     연산자: {operator}")
                print(f"     대상값: {target}")
                print(f"     생성일: {created}")
                print(f"     {'-' * 40}")
        else:
            print("❌ t_ 시작하는 트리거가 없습니다.")
            
        # 전체 트리거 수 확인
        cursor.execute("SELECT COUNT(*) FROM trading_conditions")
        total_count = cursor.fetchone()[0]
        print(f"📊 전체 트리거 수: {total_count}개")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ DB 조회 오류: {e}")

def check_edit_functionality():
    """3. 편집 기능 문제 확인"""
    print("\n" + "=" * 60)
    print("3️⃣ 편집 기능 문제 분석")
    print("=" * 60)
    
    # 편집 관련 파일들 확인
    files_to_check = [
        "integrated_condition_manager.py",
        "upbit_auto_trading/ui/desktop/screens/strategy_management/integrated_condition_manager.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"📁 분석 중: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 편집 관련 메서드 찾기
            edit_methods = [
                "edit_selected_trigger",
                "load_condition_for_edit",
                "populate_dialog_from_condition",
                "edit_condition"
            ]
            
            found_methods = []
            for method in edit_methods:
                if f"def {method}" in content:
                    found_methods.append(method)
            
            if found_methods:
                print(f"  ✅ 발견된 편집 메서드: {', '.join(found_methods)}")
            else:
                print(f"  ❌ 편집 메서드를 찾을 수 없습니다.")
            
            # 편집 버튼 연결 확인
            if "edit_btn.clicked.connect" in content:
                print(f"  ✅ 편집 버튼 연결 발견")
            else:
                print(f"  ❌ 편집 버튼 연결 없음")
        else:
            print(f"❌ 파일 없음: {file_path}")

def analyze_terminology_issue():
    """4. condition/trigger 용어 통일 분석"""
    print("\n" + "=" * 60)
    print("4️⃣ condition/trigger 용어 통일 분석")
    print("=" * 60)
    
    # 용어 사용 현황 분석
    terminology_analysis = {
        "코드": {"condition": 0, "trigger": 0},
        "DB": {"condition": 0, "trigger": 0},
        "UI": {"condition": 0, "trigger": 0}
    }
    
    # DB 테이블명 확인
    db_path = "upbit_trading_unified.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print("📊 DB 테이블 분석:")
            for table in tables:
                if "condition" in table.lower():
                    terminology_analysis["DB"]["condition"] += 1
                    print(f"  🔵 condition 계열: {table}")
                elif "trigger" in table.lower():
                    terminology_analysis["DB"]["trigger"] += 1
                    print(f"  🟠 trigger 계열: {table}")
            
            conn.close()
        except Exception as e:
            print(f"❌ DB 분석 오류: {e}")
    
    # 파일 용어 사용 빈도 분석
    python_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    condition_files = 0
    trigger_files = 0
    
    for file_path in python_files[:10]:  # 샘플로 10개만 확인
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "condition" in content.lower():
                    condition_files += 1
                if "trigger" in content.lower():
                    trigger_files += 1
        except:
            continue
    
    print(f"\n📈 코드 용어 사용 빈도 (샘플 10개 파일):")
    print(f"  🔵 condition 포함 파일: {condition_files}개")
    print(f"  🟠 trigger 포함 파일: {trigger_files}개")
    
    # 권장사항 제시
    print(f"\n💡 용어 통일 권장사항:")
    print(f"  현재 상황:")
    print(f"    - DB: trading_conditions 테이블 (condition 기반)")
    print(f"    - 코드: ConditionDialog, ConditionBuilder 등 (condition 기반)")
    print(f"    - UI 표시: '트리거' 용어 사용 (사용자 친화적)")
    print(f"")
    print(f"  🎯 권장 해결방안:")
    print(f"    1. 내부 코드/DB: condition 용어 유지 (기술적 일관성)")
    print(f"    2. 사용자 UI: '트리거' 용어 사용 (직관성)")
    print(f"    3. 주석/문서: condition → trigger 매핑 명시")
    print(f"    4. 변수명: 혼동 방지를 위해 명확한 네이밍")
    print(f"")
    print(f"  📋 구체적 적용:")
    print(f"    - DB 테이블: trading_conditions (유지)")
    print(f"    - 클래스명: ConditionDialog (유지)")
    print(f"    - UI 라벨: '트리거 목록', '트리거 편집' 등")
    print(f"    - 변수명: selected_trigger_condition, trigger_data 등")

def suggest_solutions():
    """해결책 제안"""
    print("\n" + "=" * 60)
    print("🛠️ 종합 해결책 제안")
    print("=" * 60)
    
    solutions = [
        {
            "문제": "조건명 특수문자 제한",
            "해결책": "condition_validator.py에서 < > | 허용, \" \\ 만 제한",
            "파일": "components/condition_validator.py",
            "변경": "re.search(r'[\"|\\\\]', name)"
        },
        {
            "문제": "편집 기능 미작동",
            "해결책": "load_condition_for_edit 메서드 구현 및 UI 데이터 로딩",
            "파일": "integrated_condition_manager.py",
            "변경": "edit_selected_trigger → load_condition_data → populate_ui"
        },
        {
            "문제": "용어 혼용",
            "해결책": "내부는 condition, UI는 trigger 용어 사용",
            "파일": "UI 라벨 텍스트",
            "변경": "'조건' → '트리거' 표시명 변경"
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"{i}. {solution['문제']}")
        print(f"   해결책: {solution['해결책']}")
        print(f"   파일: {solution['파일']}")
        print(f"   변경: {solution['변경']}")
        print()

if __name__ == "__main__":
    print("🔍 사용자 문제 종합 분석 시작")
    print("=" * 60)
    
    # 1. 조건명 특수문자 제한 확인
    check_condition_name_restrictions()
    
    # 2. t_ 트리거 DB 확인
    check_t_triggers_in_db()
    
    # 3. 편집 기능 분석
    check_edit_functionality()
    
    # 4. 용어 통일 분석
    analyze_terminology_issue()
    
    # 5. 해결책 제안
    suggest_solutions()
    
    print("\n✅ 분석 완료!")
