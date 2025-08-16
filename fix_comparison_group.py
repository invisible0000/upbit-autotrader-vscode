#!/usr/bin/env python3
"""
ComparisonGroup 검증 오류 디버깅 및 수정 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_and_fix_comparison_group():
    """ComparisonGroup 검증 오류 확인 및 수정"""
    print("🔍 ComparisonGroup 검증 오류 디버깅 시작...")

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # comparison_group이 빈 문자열이거나 NULL인 변수들 확인
    cursor.execute('''
        SELECT variable_id, display_name_ko, comparison_group, purpose_category
        FROM tv_trading_variables
        WHERE comparison_group = "" OR comparison_group IS NULL
        ORDER BY variable_id
    ''')

    rows = cursor.fetchall()
    print(f"\n📊 comparison_group이 빈 문자열인 변수: {len(rows)}개")

    if rows:
        print("\n❌ 문제가 있는 변수들:")
        for variable_id, display_name_ko, comparison_group, purpose_category in rows:
            print(f"  - {variable_id}: '{display_name_ko}' -> '{comparison_group}' ({purpose_category})")

        # comparison_group 매핑 정의
        comparison_group_mapping = {
            # 가격 관련
            'CURRENT_PRICE': 'price_comparable',
            'HIGH_PRICE': 'price_comparable',
            'LOW_PRICE': 'price_comparable',
            'OPEN_PRICE': 'price_comparable',
            'AVG_BUY_PRICE': 'price_comparable',

            # 백분율 지표
            'RSI': 'percentage_comparable',
            'STOCHASTIC': 'percentage_comparable',
            'PROFIT_PERCENT': 'percentage_comparable',

            # 0 중심 지표
            'MACD': 'zero_centered',

            # 거래량
            'VOLUME': 'volume_comparable',
            'VOLUME_SMA': 'volume_comparable',

            # 변동성
            'ATR': 'volatility_comparable',
            'BOLLINGER_BAND': 'volatility_comparable',

            # 자본/잔고
            'CASH_BALANCE': 'capital_comparable',
            'COIN_BALANCE': 'capital_comparable',
            'TOTAL_BALANCE': 'capital_comparable',

            # 수량
            'POSITION_SIZE': 'quantity_comparable',
            'PROFIT_AMOUNT': 'capital_comparable',

            # 이동평균 (가격 기반)
            'SMA': 'price_comparable',
            'EMA': 'price_comparable',

            # 동적 목표값
            'META_PYRAMID_TARGET': 'dynamic_target',
            'META_TRAILING_STOP': 'dynamic_target',
            'PYRAMID_TARGET': 'dynamic_target',
            'TRAILING_STOP': 'dynamic_target'
        }

        print("\n🔧 비교 그룹 수정 중...")
        for variable_id, _, _, purpose_category in rows:
            if variable_id in comparison_group_mapping:
                new_group = comparison_group_mapping[variable_id]
                cursor.execute('''
                    UPDATE tv_trading_variables
                    SET comparison_group = ?
                    WHERE variable_id = ?
                ''', (new_group, variable_id))
                print(f"✅ {variable_id} -> '{new_group}'")
            else:
                # 기본 비교 그룹 추정
                if purpose_category == 'price':
                    default_group = 'price_comparable'
                elif purpose_category == 'momentum':
                    default_group = 'percentage_comparable'
                elif purpose_category == 'volatility':
                    default_group = 'volatility_comparable'
                elif purpose_category == 'volume':
                    default_group = 'volume_comparable'
                elif purpose_category == 'capital':
                    default_group = 'capital_comparable'
                elif purpose_category == 'state':
                    default_group = 'quantity_comparable'
                elif purpose_category == 'dynamic_management':
                    default_group = 'dynamic_target'
                else:
                    default_group = 'price_comparable'  # 기본값

                cursor.execute('''
                    UPDATE tv_trading_variables
                    SET comparison_group = ?
                    WHERE variable_id = ?
                ''', (default_group, variable_id))
                print(f"✅ {variable_id} -> '{default_group}' (추정: {purpose_category})")

        conn.commit()
        print("\n🎯 데이터베이스 수정 완료!")

    else:
        print("✅ comparison_group 문제 없음")

    # 수정 후 재확인
    print("\n🔍 수정 후 재확인...")
    cursor.execute('''
        SELECT variable_id, comparison_group
        FROM tv_trading_variables
        WHERE comparison_group = "" OR comparison_group IS NULL
        ORDER BY variable_id
    ''')

    remaining_rows = cursor.fetchall()
    if remaining_rows:
        print(f"❌ 여전히 문제가 있는 변수: {len(remaining_rows)}개")
        for variable_id, comparison_group in remaining_rows:
            print(f"  - {variable_id}: '{comparison_group}'")
    else:
        print("✅ 모든 comparison_group 문제 해결됨")

    # 비교 그룹 분포 확인
    print("\n📊 비교 그룹 분포:")
    cursor.execute('''
        SELECT comparison_group, COUNT(*) as count
        FROM tv_trading_variables
        GROUP BY comparison_group
        ORDER BY comparison_group
    ''')

    group_rows = cursor.fetchall()
    for group, count in group_rows:
        print(f"  - {group}: {count}개")

    conn.close()


if __name__ == "__main__":
    debug_and_fix_comparison_group()
