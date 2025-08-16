#!/usr/bin/env python3
"""
display_name_en 검증 오류 디버깅 및 수정 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_and_fix_display_name_en():
    """display_name_en 검증 오류 확인 및 수정"""
    print("🔍 display_name_en 검증 오류 디버깅 시작...")

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # display_name_en이 빈 문자열이거나 NULL인 변수들 확인
    cursor.execute('''
        SELECT variable_id, display_name_ko, display_name_en, purpose_category
        FROM tv_trading_variables
        WHERE display_name_en = "" OR display_name_en IS NULL
        ORDER BY variable_id
    ''')

    rows = cursor.fetchall()
    print(f"\n📊 display_name_en이 빈 문자열인 변수: {len(rows)}개")

    if rows:
        print("\n❌ 문제가 있는 변수들:")
        for variable_id, display_name_ko, display_name_en, purpose_category in rows:
            print(f"  - {variable_id}: '{display_name_ko}' -> '{display_name_en}' ({purpose_category})")

        # 영어 이름 매핑 정의
        english_names = {
            'CASH_BALANCE': 'Cash Balance',
            'COIN_BALANCE': 'Coin Balance',
            'PYRAMID_TARGET': 'Pyramid Target',
            'TOTAL_BALANCE': 'Total Balance',
            'TRAILING_STOP': 'Trailing Stop Target',
            'AVG_BUY_PRICE': 'Average Buy Price',
            'POSITION_SIZE': 'Position Size',
            'PROFIT_AMOUNT': 'Profit Amount',
            'PROFIT_PERCENT': 'Profit Percent'
        }

        print("\n🔧 영어 이름 수정 중...")
        for variable_id, _, _, _ in rows:
            if variable_id in english_names:
                new_name = english_names[variable_id]
                cursor.execute('''
                    UPDATE tv_trading_variables
                    SET display_name_en = ?
                    WHERE variable_id = ?
                ''', (new_name, variable_id))
                print(f"✅ {variable_id} -> '{new_name}'")
            else:
                # 기본 영어 이름 생성 (한국어 이름 기반)
                cursor.execute('''
                    SELECT display_name_ko FROM tv_trading_variables
                    WHERE variable_id = ?
                ''', (variable_id,))
                korean_name = cursor.fetchone()[0]

                # 간단한 영어 이름 생성
                english_name = variable_id.replace('_', ' ').title()

                cursor.execute('''
                    UPDATE tv_trading_variables
                    SET display_name_en = ?
                    WHERE variable_id = ?
                ''', (english_name, variable_id))
                print(f"✅ {variable_id} -> '{english_name}' (자동 생성)")

        conn.commit()
        print("\n🎯 데이터베이스 수정 완료!")

    else:
        print("✅ display_name_en 문제 없음")

    # 수정 후 재확인
    print("\n🔍 수정 후 재확인...")
    cursor.execute('''
        SELECT variable_id, display_name_ko, display_name_en, purpose_category
        FROM tv_trading_variables
        WHERE display_name_en = "" OR display_name_en IS NULL
        ORDER BY variable_id
    ''')

    remaining_rows = cursor.fetchall()
    if remaining_rows:
        print(f"❌ 여전히 문제가 있는 변수: {len(remaining_rows)}개")
        for variable_id, display_name_ko, display_name_en, purpose_category in remaining_rows:
            print(f"  - {variable_id}: '{display_name_en}' ({purpose_category})")
    else:
        print("✅ 모든 display_name_en 문제 해결됨")

    conn.close()


if __name__ == "__main__":
    debug_and_fix_display_name_en()
