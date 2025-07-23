#!/usr/bin/env python3
"""
삭제 기능 분석 스크립트
1. 삭제 버튼의 실제 동작 확인
2. 소프트 삭제 vs 하드 삭제 문제점 분석
3. 해결책 제안
"""

import sqlite3
import os

def analyze_delete_functionality():
    """삭제 기능 분석"""
    print("=" * 60)
    print("🔍 삭제 기능 동작 분석")
    print("=" * 60)
    
    # 삭제 관련 파일들 확인
    files_to_check = [
        "integrated_condition_manager.py",
        "upbit_auto_trading/ui/desktop/screens/strategy_management/integrated_condition_manager.py",
        "components/condition_storage.py"
    ]
    
    delete_methods = [
        "delete_selected_trigger",
        "delete_condition", 
        "remove_condition",
        "delete_trigger",
        "soft_delete",
        "hard_delete"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"📁 분석 중: {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 삭제 메서드 찾기
                found_methods = []
                for method in delete_methods:
                    if f"def {method}" in content:
                        found_methods.append(method)
                
                if found_methods:
                    print(f"  ✅ 발견된 삭제 메서드: {', '.join(found_methods)}")
                    
                    # 각 메서드의 SQL 동작 확인
                    for method in found_methods:
                        method_start = content.find(f"def {method}")
                        if method_start != -1:
                            # 메서드 시작부터 다음 메서드까지
                            next_method = content.find("\n    def ", method_start + 1)
                            if next_method == -1:
                                method_content = content[method_start:]
                            else:
                                method_content = content[method_start:next_method]
                            
                            # SQL 동작 확인
                            if "DELETE FROM" in method_content:
                                print(f"    🗑️ {method}: 하드 삭제 (DELETE FROM)")
                            elif "UPDATE" in method_content and "is_active" in method_content:
                                print(f"    🔄 {method}: 소프트 삭제 (is_active = 0)")
                            elif "UPDATE" in method_content:
                                print(f"    🔄 {method}: 업데이트 기반 삭제")
                            else:
                                print(f"    ❓ {method}: 삭제 방식 불명확")
                else:
                    print(f"  ❌ 삭제 메서드를 찾을 수 없습니다.")
                
                # 특정 패턴 검색
                if "is_active = 0" in content or "is_active=0" in content:
                    print(f"  ⚠️ 소프트 삭제 코드 발견!")
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if "is_active = 0" in line or "is_active=0" in line:
                            print(f"    라인 {i}: {line.strip()}")
                
                if "DELETE FROM trading_conditions" in content:
                    print(f"  ✅ 하드 삭제 코드 발견!")
                    
            except Exception as e:
                print(f"  ❌ 파일 분석 오류: {e}")
        else:
            print(f"❌ 파일 없음: {file_path}")

def check_db_schema():
    """DB 스키마 확인"""
    print("\n" + "=" * 60)
    print("🔍 DB 스키마 분석")
    print("=" * 60)
    
    db_path = "upbit_trading_unified.db"
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일 없음: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # trading_conditions 테이블 스키마 확인
        cursor.execute("PRAGMA table_info(trading_conditions)")
        columns = cursor.fetchall()
        
        print("📊 trading_conditions 테이블 구조:")
        has_is_active = False
        for col in columns:
            col_id, name, type_, not_null, default, pk = col
            print(f"  📋 {name}: {type_} {'(PK)' if pk else ''} {'NOT NULL' if not_null else ''} {'DEFAULT: ' + str(default) if default else ''}")
            if name == "is_active":
                has_is_active = True
        
        if has_is_active:
            print("\n⚠️ is_active 컬럼 존재 - 소프트 삭제 지원")
            
            # 비활성화된 레코드 확인
            cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE is_active = 0")
            inactive_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE is_active = 1")
            active_count = cursor.fetchone()[0]
            
            print(f"  📈 활성화된 트리거: {active_count}개")
            print(f"  📉 비활성화된 트리거: {inactive_count}개")
            
            if inactive_count > 0:
                print(f"\n⚠️ 경고: {inactive_count}개의 비활성화된 트리거가 DB에 남아있음!")
        else:
            print("\n✅ is_active 컬럼 없음 - 하드 삭제만 지원")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ DB 스키마 조회 오류: {e}")

def analyze_problems():
    """소프트 삭제 문제점 분석"""
    print("\n" + "=" * 60)
    print("⚠️ 소프트 삭제 방식의 문제점")
    print("=" * 60)
    
    problems = [
        {
            "문제": "데이터베이스 크기 증가",
            "설명": "삭제된 데이터가 계속 누적되어 DB 크기가 불필요하게 커짐",
            "영향": "성능 저하, 스토리지 낭비"
        },
        {
            "문제": "중복 이름 문제",
            "설명": "비활성화된 트리거와 같은 이름의 새 트리거 생성 시 충돌",
            "영향": "이름 중복 오류, 사용자 혼란"
        },
        {
            "문제": "쿼리 복잡성 증가",
            "설명": "모든 조회 쿼리에 WHERE is_active = 1 조건 필요",
            "영향": "코드 복잡성, 실수 가능성"
        },
        {
            "문제": "일관성 문제",
            "설명": "일부 코드에서 is_active 조건을 빼먹을 수 있음",
            "영향": "예상치 못한 비활성화 데이터 노출"
        },
        {
            "문제": "백업/복원 복잡성",
            "설명": "비활성화된 데이터 포함 여부 결정 필요",
            "영향": "데이터 관리 복잡성"
        }
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"{i}. 🚨 {problem['문제']}")
        print(f"   📝 설명: {problem['설명']}")
        print(f"   💥 영향: {problem['영향']}")
        print()

def suggest_solutions():
    """해결책 제안"""
    print("=" * 60)
    print("🛠️ 권장 해결책")
    print("=" * 60)
    
    solutions = [
        {
            "방법": "하드 삭제로 변경 (권장)",
            "장점": "데이터 일관성, 단순성, 성능",
            "단점": "실수로 삭제 시 복구 어려움",
            "구현": "DELETE FROM trading_conditions WHERE id = ?"
        },
        {
            "방법": "삭제 확인 다이얼로그 강화",
            "장점": "실수 방지, 사용자 안전성",
            "단점": "사용자 경험 약간 저하",
            "구현": "2단계 확인, 되돌리기 불가 경고"
        },
        {
            "방법": "휴지통 기능 (임시 보관)",
            "장점": "복구 가능, 안전성",
            "단점": "별도 관리 필요",
            "구현": "deleted_at 컬럼, 자동 정리 작업"
        },
        {
            "방법": "백업 후 하드 삭제",
            "장점": "안전성 + 성능",
            "단점": "복잡성 증가",
            "구현": "삭제 전 백업 테이블에 저장"
        }
    ]
    
    print("💡 추천 순서:")
    for i, solution in enumerate(solutions, 1):
        print(f"{i}. {solution['방법']}")
        print(f"   ✅ 장점: {solution['장점']}")
        print(f"   ❌ 단점: {solution['단점']}")
        print(f"   🔧 구현: {solution['구현']}")
        print()
    
    print("🎯 최종 권장사항:")
    print("  1. 현재 is_active = 0인 비활성화 데이터 정리")
    print("  2. 삭제 기능을 하드 삭제로 변경")
    print("  3. 강화된 삭제 확인 다이얼로그 구현")
    print("  4. 중요한 삭제는 자동 백업 후 삭제")

def create_cleanup_script():
    """정리 스크립트 생성"""
    print("\n" + "=" * 60)
    print("🧹 비활성화 데이터 정리 스크립트")
    print("=" * 60)
    
    cleanup_script = '''
# 비활성화된 트리거 정리 스크립트
import sqlite3

def cleanup_inactive_triggers():
    """비활성화된 트리거들을 완전히 삭제"""
    try:
        conn = sqlite3.connect('upbit_trading_unified.db')
        cursor = conn.cursor()
        
        # 삭제할 비활성화 트리거 확인
        cursor.execute("SELECT id, name FROM trading_conditions WHERE is_active = 0")
        inactive_triggers = cursor.fetchall()
        
        if inactive_triggers:
            print(f"삭제할 비활성화 트리거 {len(inactive_triggers)}개:")
            for trigger_id, name in inactive_triggers:
                print(f"  - ID {trigger_id}: {name}")
            
            # 사용자 확인
            confirm = input("\\n이 트리거들을 완전히 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() == 'yes':
                # 완전 삭제 실행
                cursor.execute("DELETE FROM trading_conditions WHERE is_active = 0")
                deleted_count = cursor.rowcount
                conn.commit()
                print(f"✅ {deleted_count}개 트리거 완전 삭제 완료")
            else:
                print("❌ 삭제 취소됨")
        else:
            print("✅ 삭제할 비활성화 트리거가 없습니다")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 정리 실패: {e}")

if __name__ == "__main__":
    cleanup_inactive_triggers()
'''
    
    with open("cleanup_inactive_triggers.py", "w", encoding="utf-8") as f:
        f.write(cleanup_script)
    
    print("✅ cleanup_inactive_triggers.py 파일 생성됨")
    print("   실행: python cleanup_inactive_triggers.py")

if __name__ == "__main__":
    print("🔍 삭제 기능 문제 분석 시작")
    print("=" * 60)
    
    # 1. 삭제 기능 분석
    analyze_delete_functionality()
    
    # 2. DB 스키마 확인
    check_db_schema()
    
    # 3. 문제점 분석
    analyze_problems()
    
    # 4. 해결책 제안
    suggest_solutions()
    
    # 5. 정리 스크립트 생성
    create_cleanup_script()
    
    print("\n✅ 분석 완료!")
