#!/usr/bin/env python3
"""
tv_variable_parameters 테이블 스키마 확인 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_parameters_table():
    """tv_variable_parameters 테이블 확인"""
    print("🔍 tv_variable_parameters 테이블 확인 시작...")

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # 1. tv_variable_parameters 테이블 스키마 확인
    print("\n📋 tv_variable_parameters 테이블 스키마:")
    cursor.execute('PRAGMA table_info(tv_variable_parameters)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]}: {col[2]} (NULL허용: {col[3] == 0})")

    # 2. 메타변수 관련 파라미터들 확인
    print("\n🎯 메타변수 파라미터들:")
    cursor.execute('''
        SELECT variable_id, parameter_name
        FROM tv_variable_parameters
        WHERE variable_id LIKE "META_%" OR variable_id LIKE "%PYRAMID%" OR variable_id LIKE "%TRAILING%"
        ORDER BY variable_id, parameter_name
    ''')

    params = cursor.fetchall()
    if params:
        current_var = None
        for variable_id, parameter_name in params:
            if variable_id != current_var:
                print(f"\n📌 {variable_id}:")
                current_var = variable_id
            print(f"  - {parameter_name}")
    else:
        print("❌ 메타변수 관련 파라미터 없음")

    # 3. 전체 파라미터 데이터 확인 (처음 10개만)
    print("\n📊 전체 파라미터 데이터 샘플 (처음 10개):")
    cursor.execute('SELECT * FROM tv_variable_parameters LIMIT 10')
    sample_params = cursor.fetchall()

    # 컬럼명 가져오기
    col_names = [desc[0] for desc in cursor.description]
    print(f"컬럼: {col_names}")

    for i, row in enumerate(sample_params):
        print(f"  {i+1}: {row}")

    conn.close()


if __name__ == "__main__":
    check_parameters_table()
