#!/usr/bin/env python3
"""
메타변수 관련 상황 정리 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def summarize_current_situation():
    """현재 상황 정리"""
    print("🔍 메타변수 관련 현재 상황 정리")
    print("=" * 60)

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # 1. 현재 dynamic_management 카테고리 변수들
    print("\n📊 1. 현재 DB - dynamic_management 카테고리:")
    cursor.execute('''
        SELECT variable_id, display_name_ko, parameter_required
        FROM tv_trading_variables
        WHERE purpose_category = "dynamic_management"
        ORDER BY variable_id
    ''')

    current_vars = cursor.fetchall()
    for variable_id, display_name_ko, parameter_required in current_vars:
        print(f"  ✅ {variable_id}: '{display_name_ko}' (파라미터 필요: {parameter_required})")

    # 2. tv_variable_help_documents 스키마와 데이터
    print("\n📋 2. tv_variable_help_documents 테이블:")
    cursor.execute('PRAGMA table_info(tv_variable_help_documents)')
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    print(f"  컬럼: {col_names}")

    # 메타변수 관련 도움말 확인
    cursor.execute('''
        SELECT variable_id, COUNT(*) as count
        FROM tv_variable_help_documents
        WHERE variable_id LIKE "%PYRAMID%" OR variable_id LIKE "%TRAILING%"
        GROUP BY variable_id
        ORDER BY variable_id
    ''')

    help_vars = cursor.fetchall()
    if help_vars:
        print("  📖 메타변수 관련 도움말:")
        for variable_id, count in help_vars:
            print(f"    • {variable_id}: {count}개 문서")
    else:
        print("  ❌ 메타변수 관련 도움말 없음")

    # 3. 파라미터 상태 확인
    print("\n🔧 3. 메타변수 파라미터 상태:")
    for variable_id, _, _ in current_vars:
        cursor.execute('''
            SELECT parameter_name, parameter_type, enum_values, display_name_ko
            FROM tv_variable_parameters
            WHERE variable_id = ?
            ORDER BY display_order
        ''', (variable_id,))

        params = cursor.fetchall()
        print(f"\n  📌 {variable_id} 파라미터 ({len(params)}개):")
        for param_name, param_type, enum_values, display_name_ko in params:
            enum_status = "JSON 오류" if enum_values and enum_values.strip() and param_type == "enum" else "정상"
            print(f"    • {param_name} ({param_type}): '{display_name_ko}' - {enum_status}")
            if enum_values and param_type == "enum":
                print(f"      enum_values: {enum_values[:50]}...")

    # 4. YAML 파일 구조 확인
    print("\n📁 4. YAML 파일 구조:")
    yaml_base = Path("data_info/trading_variables")
    if yaml_base.exists():
        meta_folder = yaml_base / "meta"
        if meta_folder.exists():
            print(f"  ✅ meta 폴더 존재: {meta_folder}")
            meta_vars = list(meta_folder.iterdir())
            print(f"  📂 메타변수 폴더들: {[v.name for v in meta_vars if v.is_dir()]}")
        else:
            print("  ❌ meta 폴더 없음")

        # 다른 카테고리들도 확인
        categories = [d.name for d in yaml_base.iterdir() if d.is_dir()]
        print(f"  📁 전체 카테고리: {categories}")
    else:
        print("  ❌ data_info/trading_variables 폴더 없음")

    conn.close()


def identify_core_problems():
    """핵심 문제점 식별"""
    print("\n\n🚨 핵심 문제점 식별")
    print("=" * 60)

    print("\n1. 🔄 메타변수 정의 혼재:")
    print("   - 이전: META_PYRAMID_TARGET, META_TRAILING_STOP (삭제됨)")
    print("   - 현재: PYRAMID_TARGET, TRAILING_STOP (파라미터 있음)")
    print("   - 혼란: META_ 접두사 있는 것이 '진짜'인지 없는 것이 '진짜'인지 불분명")

    print("\n2. 🔧 파라미터 표시 문제:")
    print("   - enum_values JSON 파싱 실패로 드롭다운 표시 안됨")
    print("   - 'calculation_method', 'trail_direction' 같은 중요 파라미터 선택 불가")

    print("\n3. 📚 도움말 시스템 불일치:")
    print("   - TV_variable_help_documents에 삭제된 변수 데이터 잔존 가능성")
    print("   - YAML 파일과 DB 도움말 내용 불일치")

    print("\n4. 🏗️ 아키텍처 설계 문제:")
    print("   - DB-first vs YAML-first 정책 불분명")
    print("   - 스키마 파일과 실제 DB 구조 동기화 미흡")


def propose_solution_phases():
    """해결 방안 단계별 제시"""
    print("\n\n💡 해결 방안 (3단계)")
    print("=" * 60)

    print("\n🎯 Phase 1: 긴급 수정 (현재 UI 문제 해결)")
    print("   1-1. enum_values JSON 형식 수정")
    print("   1-2. 파라미터 드롭다운 정상 작동 확인")
    print("   1-3. 메타변수명 최종 결정 (META_ 접두사 사용 여부)")

    print("\n🔧 Phase 2: 데이터 정리 (기술 부채 해결)")
    print("   2-1. 모든 tv_ 테이블 일관성 검증")
    print("   2-2. 불필요한 도움말 문서 정리")
    print("   2-3. DB에서 정확한 YAML 재추출")

    print("\n🏗️ Phase 3: 시스템 표준화 (미래 확장성)")
    print("   3-1. 메타변수 추가 프로세스 표준화")
    print("   3-2. DB-YAML 동기화 자동화")
    print("   3-3. 스키마 파일 자동 생성")

    print("\n❓ 우선순위 질문:")
    print("   Q1: 현재 UI에서 파라미터 선택이 가장 급한 문제인가요?")
    print("   Q2: META_ 접두사를 사용하는 것이 맞나요? (data_info 기준)")
    print("   Q3: DB를 기준으로 YAML을 재생성하는 것이 맞나요?")


def show_immediate_next_steps():
    """즉시 실행 가능한 다음 단계"""
    print("\n\n⚡ 즉시 실행 가능한 다음 단계")
    print("=" * 60)

    print("\nA. 🚀 빠른 수정 (UI 파라미터 문제 해결):")
    print("   1. enum_values JSON 형식 수정")
    print("   2. calculation_method, trail_direction 드롭다운 작동 확인")
    print("   3. 7규칙 전략 테스트 가능한 상태로 만들기")

    print("\nB. 🧹 철저한 정리 (기술 부채 완전 해결):")
    print("   1. 전체 데이터 일관성 분석")
    print("   2. META_ 접두사 통일 정책 결정")
    print("   3. DB-YAML-스키마 완전 동기화")

    print("\n💬 권장사항:")
    print("   첫 번째로 A(빠른 수정)를 통해 현재 문제를 해결하고,")
    print("   7규칙 전략이 정상 작동하는 것을 확인한 후")
    print("   B(철저한 정리)를 단계적으로 진행하는 것을 권장합니다.")


if __name__ == "__main__":
    summarize_current_situation()
    identify_core_problems()
    propose_solution_phases()
    show_immediate_next_steps()
