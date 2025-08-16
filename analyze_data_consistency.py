#!/usr/bin/env python3
"""
메타변수 관련 데이터 일관성 분석 스크립트
DB, YAML, 스키마 간의 불일치 문제 파악
"""
import sqlite3
import sys
import os
import yaml
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def analyze_data_consistency():
    """데이터 일관성 분석"""
    print("🔍 메타변수 관련 데이터 일관성 분석 시작...")

    # 1. 현재 DB 상태 확인
    print("\n📊 1. 현재 DB 상태 (dynamic_management 카테고리)")
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT variable_id, display_name_ko, parameter_required
        FROM tv_trading_variables
        WHERE purpose_category = "dynamic_management"
        ORDER BY variable_id
    ''')

    current_vars = cursor.fetchall()
    for variable_id, display_name_ko, parameter_required in current_vars:
        print(f"  - {variable_id}: '{display_name_ko}' (파라미터:{parameter_required})")

    # 2. tv_variable_help_documents 확인
    print("\n📋 2. tv_variable_help_documents 테이블 - 메타변수 관련")
    cursor.execute('''
        SELECT variable_id, help_type, content
        FROM tv_variable_help_documents
        WHERE variable_id LIKE "%PYRAMID%" OR variable_id LIKE "%TRAILING%"
        ORDER BY variable_id, help_type
    ''')

    help_docs = cursor.fetchall()
    if help_docs:
        current_help_var = None
        for variable_id, help_type, content in help_docs:
            if variable_id != current_help_var:
                print(f"\n  📌 {variable_id}:")
                current_help_var = variable_id
            print(f"    - {help_type}: {content[:50]}..." if len(content) > 50 else f"    - {help_type}: {content}")
    else:
        print("  ❌ 메타변수 관련 도움말 문서 없음")

    # 3. 모든 tv_ 테이블 확인
    print("\n📊 3. 모든 tv_ 테이블 목록과 메타변수 관련 데이터")
    cursor.execute('''
        SELECT name FROM sqlite_master
        WHERE type="table" AND name LIKE "tv_%"
        ORDER BY name
    ''')

    tv_tables = [row[0] for row in cursor.fetchall()]
    print(f"TV 테이블들: {tv_tables}")

    for table in tv_tables:
        print(f"\n  📋 {table} 테이블:")
        try:
            # 테이블 스키마 확인
            cursor.execute(f'PRAGMA table_info({table})')
            columns = [col[1] for col in cursor.fetchall()]

            # variable_id 컬럼이 있는 테이블만 메타변수 데이터 확인
            if 'variable_id' in columns:
                cursor.execute(f'''
                    SELECT variable_id, COUNT(*) as count
                    FROM {table}
                    WHERE variable_id LIKE "%PYRAMID%" OR variable_id LIKE "%TRAILING%"
                    GROUP BY variable_id
                    ORDER BY variable_id
                ''')

                meta_data = cursor.fetchall()
                if meta_data:
                    for variable_id, count in meta_data:
                        print(f"    • {variable_id}: {count}개 레코드")
                else:
                    print("    • 메타변수 관련 데이터 없음")
            else:
                print(f"    • 컬럼: {columns}")
        except Exception as e:
            print(f"    • 오류: {e}")

    conn.close()

    # 4. YAML 파일 구조 확인
    print("\n📁 4. data_info/trading_variables YAML 구조 분석")
    yaml_base_path = Path("data_info/trading_variables")

    if yaml_base_path.exists():
        # 모든 카테고리 폴더 확인
        categories = [d for d in yaml_base_path.iterdir() if d.is_dir()]
        print(f"  카테고리 폴더: {[c.name for c in categories]}")

        # 각 카테고리의 변수들 확인
        for category in categories:
            print(f"\n  📂 {category.name} 카테고리:")
            variables = [d for d in category.iterdir() if d.is_dir()]

            for var_dir in variables:
                definition_file = var_dir / "definition.yaml"
                if definition_file.exists():
                    try:
                        with open(definition_file, 'r', encoding='utf-8') as f:
                            var_data = yaml.safe_load(f)

                        variable_id = var_data.get('variable_id', '없음')
                        display_name_ko = var_data.get('display_name_ko', '없음')
                        print(f"    • {var_dir.name}: {variable_id} - {display_name_ko}")
                    except Exception as e:
                        print(f"    • {var_dir.name}: YAML 파싱 오류 - {e}")
                else:
                    print(f"    • {var_dir.name}: definition.yaml 없음")
    else:
        print("  ❌ data_info/trading_variables 폴더 없음")

    # 5. 스키마 파일 확인
    print("\n📄 5. 스키마 파일 상태")
    schema_file = Path("data_info/upbit_autotrading_schema_settings.sql")
    if schema_file.exists():
        print(f"  ✅ 스키마 파일 존재: {schema_file}")
        # 파일 크기와 수정 시간 확인
        stat = schema_file.stat()
        print(f"  📊 크기: {stat.st_size} bytes")
        print(f"  📅 수정일: {stat.st_mtime}")
    else:
        print("  ❌ 스키마 파일 없음")


def analyze_specific_meta_vars():
    """특정 메타변수 상세 분석"""
    print("\n\n🔬 메타변수 상세 분석")

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # META_ 접두사 유무 모든 변수 확인
    meta_patterns = ['PYRAMID', 'TRAILING']

    for pattern in meta_patterns:
        print(f"\n📌 {pattern} 관련 모든 변수:")

        # tv_trading_variables에서 확인
        cursor.execute('''
            SELECT variable_id, display_name_ko, parameter_required
            FROM tv_trading_variables
            WHERE variable_id LIKE ?
            ORDER BY variable_id
        ''', (f'%{pattern}%',))

        vars_in_main = cursor.fetchall()
        for variable_id, display_name_ko, parameter_required in vars_in_main:
            print(f"  📊 Main Table: {variable_id} - '{display_name_ko}' (파라미터:{parameter_required})")

        # tv_variable_parameters에서 확인
        cursor.execute('''
            SELECT DISTINCT variable_id
            FROM tv_variable_parameters
            WHERE variable_id LIKE ?
            ORDER BY variable_id
        ''', (f'%{pattern}%',))

        vars_with_params = [row[0] for row in cursor.fetchall()]
        print(f"  🔧 Parameters: {vars_with_params}")

        # tv_variable_help_documents에서 확인
        cursor.execute('''
            SELECT DISTINCT variable_id
            FROM tv_variable_help_documents
            WHERE variable_id LIKE ?
            ORDER BY variable_id
        ''', (f'%{pattern}%',))

        vars_with_help = [row[0] for row in cursor.fetchall()]
        print(f"  📖 Help Docs: {vars_with_help}")

    conn.close()


def recommend_solution():
    """해결 방안 제시"""
    print("\n\n💡 문제 진단 및 해결 방안")

    print("\n🔍 문제 진단:")
    print("1. DB-YAML 불일치: DB에는 display_name_ko가 있지만 YAML에는 없음")
    print("2. 메타변수 정의 혼재: META_ 접두사 유무로 혼란")
    print("3. 파라미터 연결 부실: enum_values JSON 파싱 실패")
    print("4. 도움말 문서 불일치: 삭제된 변수의 도움말이 남아있음")
    print("5. 스키마 동기화 미흡: 실제 DB와 스키마 파일 불일치")

    print("\n🛠️ 해결 방안 (단계별):")
    print("Phase 1: 현재 상태 정리")
    print("  1-1. DB에서 올바른 메타변수 데이터 추출")
    print("  1-2. 불필요한 도움말 문서 정리")
    print("  1-3. 파라미터 enum_values JSON 형식 수정")

    print("\nPhase 2: YAML 재생성")
    print("  2-1. DB에서 정확한 YAML 추출 스크립트 작성")
    print("  2-2. data_info/trading_variables 폴더 재구성")
    print("  2-3. META_ 접두사 통일 (새 메타변수는 META_ 사용)")

    print("\nPhase 3: 스키마 동기화")
    print("  3-1. 현재 DB에서 정확한 스키마 추출")
    print("  3-2. upbit_autotrading_schema_settings.sql 업데이트")

    print("\n❓ 진행 방향 선택:")
    print("A. 현재 DB 기준으로 모든 것을 정리 (권장)")
    print("B. YAML 기준으로 DB 재구성")
    print("C. 처음부터 메타변수 시스템 재설계")


if __name__ == "__main__":
    analyze_data_consistency()
    analyze_specific_meta_vars()
    recommend_solution()
