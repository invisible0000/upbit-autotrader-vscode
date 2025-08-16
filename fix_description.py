#!/usr/bin/env python3
"""
Description 검증 오류 디버깅 및 수정 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_and_fix_description():
    """Description 검증 오류 확인 및 수정"""
    print("🔍 Description 검증 오류 디버깅 시작...")

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # description이 빈 문자열이거나 NULL인 변수들 확인
    cursor.execute('''
        SELECT variable_id, display_name_ko, description
        FROM tv_trading_variables
        WHERE description = "" OR description IS NULL
        ORDER BY variable_id
    ''')

    rows = cursor.fetchall()
    print(f"\n📊 description이 빈 문자열인 변수: {len(rows)}개")

    if rows:
        print("\n❌ 문제가 있는 변수들:")
        for variable_id, display_name_ko, description in rows:
            print(f"  - {variable_id}: '{display_name_ko}' -> '{description}'")

        # 기본 설명 추가
        print("\n🔧 설명 추가 중...")
        cursor.execute('''
            UPDATE tv_trading_variables
            SET description = '동적 관리 변수'
            WHERE description = "" OR description IS NULL
        ''')

        affected_rows = cursor.rowcount
        conn.commit()
        print(f"✅ {affected_rows}개 변수의 description을 '동적 관리 변수'로 설정")

    else:
        print("✅ description 문제 없음")

    # 수정 후 재확인
    print("\n🔍 수정 후 재확인...")
    cursor.execute('''
        SELECT variable_id, description
        FROM tv_trading_variables
        WHERE description = "" OR description IS NULL
        ORDER BY variable_id
    ''')

    remaining_rows = cursor.fetchall()
    if remaining_rows:
        print(f"❌ 여전히 문제가 있는 변수: {len(remaining_rows)}개")
        for variable_id, description in remaining_rows:
            print(f"  - {variable_id}: '{description}'")
    else:
        print("✅ 모든 description 문제 해결됨")

    conn.close()


if __name__ == "__main__":
    debug_and_fix_description()
