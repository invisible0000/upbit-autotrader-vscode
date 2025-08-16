#!/usr/bin/env python3
"""
VariableCategory 검증 오류 디버깅 및 수정 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_and_fix_variable_category():
    """VariableCategory 검증 오류 확인 및 수정"""
    print("🔍 VariableCategory 검증 오류 디버깅 시작...")

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # purpose_category가 빈 문자열이거나 NULL인 변수들 확인
    cursor.execute('''
        SELECT variable_id, display_name_ko, purpose_category, description
        FROM tv_trading_variables
        WHERE purpose_category = "" OR purpose_category IS NULL
        ORDER BY variable_id
    ''')

    rows = cursor.fetchall()
    print(f"\n📊 purpose_category가 빈 문자열인 변수: {len(rows)}개")

    if rows:
        print("\n❌ 문제가 있는 변수들:")
        for variable_id, display_name_ko, purpose_category, description in rows:
            print(f"  - {variable_id}: '{display_name_ko}' -> '{purpose_category}'")
            print(f"    설명: {description}")

        # 카테고리 매핑 정의 (변수 이름과 설명을 기반으로)
        category_mapping = {
            'PYRAMID_TARGET': 'dynamic_management',  # 피라미딩 목표
            'TRAILING_STOP': 'dynamic_management'   # 트레일링 스탑 목표
        }

        print("\n🔧 카테고리 수정 중...")
        for variable_id, _, _, _ in rows:
            if variable_id in category_mapping:
                new_category = category_mapping[variable_id]
                cursor.execute('''
                    UPDATE tv_trading_variables
                    SET purpose_category = ?
                    WHERE variable_id = ?
                ''', (new_category, variable_id))
                print(f"✅ {variable_id} -> '{new_category}'")
            else:
                # 기본 카테고리 추정
                if 'balance' in variable_id.lower() or 'cash' in variable_id.lower():
                    default_category = 'capital'
                elif 'price' in variable_id.lower():
                    default_category = 'price'
                elif 'volume' in variable_id.lower():
                    default_category = 'volume'
                elif 'profit' in variable_id.lower() or 'position' in variable_id.lower():
                    default_category = 'state'
                else:
                    default_category = 'other'

                cursor.execute('''
                    UPDATE tv_trading_variables
                    SET purpose_category = ?
                    WHERE variable_id = ?
                ''', (default_category, variable_id))
                print(f"✅ {variable_id} -> '{default_category}' (추정)")

        conn.commit()
        print("\n🎯 데이터베이스 수정 완료!")

    else:
        print("✅ purpose_category 문제 없음")

    # 수정 후 재확인
    print("\n🔍 수정 후 재확인...")
    cursor.execute('''
        SELECT variable_id, purpose_category
        FROM tv_trading_variables
        WHERE purpose_category = "" OR purpose_category IS NULL
        ORDER BY variable_id
    ''')

    remaining_rows = cursor.fetchall()
    if remaining_rows:
        print(f"❌ 여전히 문제가 있는 변수: {len(remaining_rows)}개")
        for variable_id, purpose_category in remaining_rows:
            print(f"  - {variable_id}: '{purpose_category}'")
    else:
        print("✅ 모든 purpose_category 문제 해결됨")

    # 모든 카테고리 확인
    print("\n📊 전체 카테고리 분포:")
    cursor.execute('''
        SELECT purpose_category, COUNT(*) as count
        FROM tv_trading_variables
        GROUP BY purpose_category
        ORDER BY purpose_category
    ''')

    category_rows = cursor.fetchall()
    for category, count in category_rows:
        print(f"  - {category}: {count}개")

    conn.close()


if __name__ == "__main__":
    debug_and_fix_variable_category()
