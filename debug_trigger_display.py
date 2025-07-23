#!/usr/bin/env python3
"""
트리거 표시 문제 디버깅 스크립트
1. DB에 있는 모든 트리거 확인
2. UI 트리거 로딩 로직 분석
"""

import sqlite3
import os

def check_all_triggers_in_db():
    """DB의 모든 트리거 확인"""
    print("=" * 60)
    print("🔍 DB 전체 트리거 조회")
    print("=" * 60)
    
    db_path = "upbit_trading_unified.db"
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일 없음: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 모든 트리거 조회
        cursor.execute("""
            SELECT id, name, description, variable_id, operator, target_value, created_at
            FROM trading_conditions 
            ORDER BY created_at DESC
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"📊 총 {len(results)}개의 트리거 발견:")
            for i, row in enumerate(results, 1):
                id_, name, desc, var_id, operator, target, created = row
                is_t_prefix = name.startswith('t_')
                prefix_mark = "🔶" if is_t_prefix else "🔸"
                
                print(f"  {prefix_mark} #{i} - ID: {id_}")
                print(f"     이름: '{name}' {'(t_ 접두사)' if is_t_prefix else ''}")
                print(f"     설명: '{desc}'")
                print(f"     변수: {var_id}")
                print(f"     연산자: {operator}")
                print(f"     대상값: {target}")
                print(f"     생성일: {created}")
                print(f"     {'-' * 50}")
        else:
            print("❌ 트리거가 없습니다.")
        
        # t_ 접두사별 분류
        cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE name LIKE 't_%'")
        t_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE name NOT LIKE 't_%'")
        non_t_count = cursor.fetchone()[0]
        
        print(f"\n📈 트리거 분류:")
        print(f"  🔶 t_ 접두사 트리거: {t_count}개")
        print(f"  🔸 일반 트리거: {non_t_count}개")
        print(f"  📊 총합: {t_count + non_t_count}개")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ DB 조회 오류: {e}")

def analyze_ui_loading_logic():
    """UI 트리거 로딩 로직 분석"""
    print("\n" + "=" * 60)
    print("🔍 UI 트리거 로딩 로직 분석")
    print("=" * 60)
    
    # 트리거 로딩 관련 파일들 확인
    files_to_check = [
        "integrated_condition_manager.py",
        "upbit_auto_trading/ui/desktop/screens/strategy_management/integrated_condition_manager.py"
    ]
    
    loading_methods = [
        "load_triggers",
        "refresh_trigger_list", 
        "load_conditions",
        "refresh_conditions",
        "update_trigger_list",
        "populate_trigger_list"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"📁 분석 중: {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 로딩 메서드 찾기
                found_methods = []
                for method in loading_methods:
                    if f"def {method}" in content:
                        found_methods.append(method)
                
                if found_methods:
                    print(f"  ✅ 발견된 로딩 메서드: {', '.join(found_methods)}")
                    
                    # 각 메서드의 SQL 쿼리 확인
                    for method in found_methods:
                        method_start = content.find(f"def {method}")
                        if method_start != -1:
                            # 메서드 시작부터 다음 메서드까지 또는 파일 끝까지
                            next_method = content.find("\n    def ", method_start + 1)
                            if next_method == -1:
                                method_content = content[method_start:]
                            else:
                                method_content = content[method_start:next_method]
                            
                            # SQL 쿼리 찾기
                            if "SELECT" in method_content and "trading_conditions" in method_content:
                                print(f"    🔍 {method}에서 SQL 쿼리 발견")
                                
                                # WHERE 절 확인
                                if "WHERE" in method_content:
                                    print(f"      📋 필터링 조건 사용 중")
                                    if "LIKE 't_%'" in method_content:
                                        print(f"        ⚠️ t_ 접두사 필터링 적용됨!")
                                else:
                                    print(f"      ✅ 전체 트리거 로딩")
                else:
                    print(f"  ❌ 로딩 메서드를 찾을 수 없습니다.")
                
                # 특정 필터 패턴 검색
                if "LIKE 't_%'" in content:
                    print(f"  ⚠️ 경고: t_ 필터링 코드 발견!")
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if "LIKE 't_%'" in line:
                            print(f"    라인 {i}: {line.strip()}")
                
                if "WHERE name LIKE" in content:
                    print(f"  ⚠️ 경고: 이름 필터링 코드 발견!")
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if "WHERE name LIKE" in line:
                            print(f"    라인 {i}: {line.strip()}")
                            
            except Exception as e:
                print(f"  ❌ 파일 분석 오류: {e}")
        else:
            print(f"❌ 파일 없음: {file_path}")

def suggest_solutions():
    """해결책 제안"""
    print("\n" + "=" * 60)
    print("🛠️ 트리거 표시 문제 해결책")
    print("=" * 60)
    
    print("💡 가능한 원인들:")
    print("  1. UI 로딩 쿼리에 WHERE name LIKE 't_%' 필터가 있음")
    print("  2. 트리거 목록 새로고침이 제대로 안됨")
    print("  3. UI와 DB 연결 문제")
    print("  4. 캐싱된 데이터 사용 중")
    
    print("\n🔧 해결 방법:")
    print("  1. 트리거 로딩 쿼리에서 WHERE 조건 제거")
    print("  2. refresh_trigger_list() 메서드 호출")
    print("  3. UI 새로고침 버튼 추가")
    print("  4. 전체 트리거 로딩으로 변경")

if __name__ == "__main__":
    print("🔍 트리거 표시 문제 디버깅 시작")
    print("=" * 60)
    
    # 1. DB 전체 트리거 확인
    check_all_triggers_in_db()
    
    # 2. UI 로딩 로직 분석
    analyze_ui_loading_logic()
    
    # 3. 해결책 제안
    suggest_solutions()
    
    print("\n✅ 디버깅 완료!")
