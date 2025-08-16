#!/usr/bin/env python3
"""
데이터베이스 테이블 구조 확인 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_db_structure():
    """데이터베이스 테이블 구조 확인"""
    print("🔍 데이터베이스 테이블 구조 확인 시작...")

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # 1. 테이블 목록 확인
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
    tables = cursor.fetchall()

    print("\n📊 Settings DB 테이블 목록:")
    for table in tables:
        print(f"  - {table[0]}")

    # 2. 파라미터 관련 테이블 찾기
    param_tables = [t[0] for t in tables if "param" in t[0].lower()]
    print(f"\n🔧 파라미터 관련 테이블: {param_tables}")

    # 3. tv_trading_variables 테이블 스키마 확인
    print("\n📋 tv_trading_variables 테이블 스키마:")
    cursor.execute('PRAGMA table_info(tv_trading_variables)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]}: {col[2]} (NULL허용: {col[3] == 0})")

    # 4. 메타변수들의 상세 정보
    print("\n🎯 메타변수 상세 정보:")
    cursor.execute('''
        SELECT variable_id, display_name_ko, parameter_required
        FROM tv_trading_variables
        WHERE purpose_category = "dynamic_management"
        ORDER BY variable_id
    ''')

    meta_vars = cursor.fetchall()
    for variable_id, display_name_ko, parameter_required in meta_vars:
        print(f"\n📌 {variable_id} ({display_name_ko}):")
        print(f"  - 파라미터 필요: {parameter_required}")

        # tv_variable_parameters 테이블에서 파라미터 확인
        cursor.execute('''
            SELECT parameter_name, data_type, is_required, default_value
            FROM tv_variable_parameters
            WHERE variable_id = ?
            ORDER BY parameter_name
        ''', (variable_id,))

        params = cursor.fetchall()
        if params:
            print(f"  - 파라미터 ({len(params)}개):")
            for param_name, data_type, is_required, default_value in params:
                print(f"    • {param_name}: {data_type} (필수:{is_required}, 기본값:{default_value})")
        else:
            print("  - ❌ 파라미터 없음")

    # 5. 중복 문제 분석
    print("\n🔍 중복 문제 분석:")
    print("META_ 접두사가 있는 변수들과 없는 변수들이 동시에 존재합니다.")
    print("이로 인해 UI에서 중복으로 표시되고 있습니다.")

    # 6. 해결 방안 제시
    print("\n💡 해결 방안:")
    print("1. META_ 접두사 없는 변수들(PYRAMID_TARGET, TRAILING_STOP)을 삭제")
    print("2. 또는 META_ 접두사 있는 변수들의 display_name_ko에서 '목표' 제거")
    print("3. 파라미터가 없는 변수들에 필요한 파라미터 추가")

    conn.close()


if __name__ == "__main__":
    check_db_structure()
