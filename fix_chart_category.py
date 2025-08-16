#!/usr/bin/env python3
"""
ChartCategory 검증 오류 디버깅 및 수정 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_and_fix_chart_category():
    """ChartCategory 검증 오류 확인 및 수정"""
    print("🔍 ChartCategory 검증 오류 디버깅 시작...")

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # chart_category가 빈 문자열이거나 NULL인 변수들 확인
    cursor.execute('''
        SELECT variable_id, display_name_ko, chart_category, purpose_category
        FROM tv_trading_variables
        WHERE chart_category = "" OR chart_category IS NULL
        ORDER BY variable_id
    ''')

    rows = cursor.fetchall()
    print(f"\n📊 chart_category가 빈 문자열인 변수: {len(rows)}개")

    if rows:
        print("\n❌ 문제가 있는 변수들:")
        for variable_id, display_name_ko, chart_category, purpose_category in rows:
            print(f"  - {variable_id}: '{display_name_ko}' -> '{chart_category}' ({purpose_category})")

        # chart_category 매핑 정의
        chart_category_mapping = {
            # 가격 관련 변수들은 overlay (차트 위에 표시)
            'CURRENT_PRICE': 'overlay',
            'HIGH_PRICE': 'overlay',
            'LOW_PRICE': 'overlay',
            'OPEN_PRICE': 'overlay',
            'AVG_BUY_PRICE': 'overlay',

            # 지표들은 subplot (별도 창)
            'RSI': 'subplot',
            'MACD': 'subplot',
            'STOCHASTIC': 'subplot',

            # 이동평균들은 overlay
            'SMA': 'overlay',
            'EMA': 'overlay',
            'VOLUME_SMA': 'subplot',

            # 볼린저밴드, ATR은 overlay
            'BOLLINGER_BAND': 'overlay',
            'ATR': 'subplot',

            # 거래량은 subplot
            'VOLUME': 'subplot',

            # 잔고/상태 변수들은 표시하지 않음 (none)
            'CASH_BALANCE': 'none',
            'COIN_BALANCE': 'none',
            'TOTAL_BALANCE': 'none',
            'POSITION_SIZE': 'none',
            'PROFIT_AMOUNT': 'none',
            'PROFIT_PERCENT': 'none',

            # 메타변수들과 동적 변수들은 none
            'META_PYRAMID_TARGET': 'none',
            'META_TRAILING_STOP': 'none',
            'PYRAMID_TARGET': 'none',
            'TRAILING_STOP': 'none'
        }

        print("\n🔧 차트 카테고리 수정 중...")
        for variable_id, _, _, purpose_category in rows:
            if variable_id in chart_category_mapping:
                new_category = chart_category_mapping[variable_id]
                cursor.execute('''
                    UPDATE tv_trading_variables
                    SET chart_category = ?
                    WHERE variable_id = ?
                ''', (new_category, variable_id))
                print(f"✅ {variable_id} -> '{new_category}'")
            else:
                # 기본 차트 카테고리 추정
                if purpose_category in ['capital', 'state', 'dynamic_management']:
                    default_category = 'none'  # 차트에 표시하지 않음
                elif purpose_category in ['price']:
                    default_category = 'overlay'  # 가격 차트 위에 표시
                elif purpose_category in ['momentum', 'volatility']:
                    default_category = 'subplot'  # 별도 창에 표시
                elif purpose_category in ['volume']:
                    default_category = 'subplot'  # 거래량 창에 표시
                else:
                    default_category = 'overlay'  # 기본값

                cursor.execute('''
                    UPDATE tv_trading_variables
                    SET chart_category = ?
                    WHERE variable_id = ?
                ''', (default_category, variable_id))
                print(f"✅ {variable_id} -> '{default_category}' (추정: {purpose_category})")

        conn.commit()
        print("\n🎯 데이터베이스 수정 완료!")

    else:
        print("✅ chart_category 문제 없음")

    # 수정 후 재확인
    print("\n🔍 수정 후 재확인...")
    cursor.execute('''
        SELECT variable_id, chart_category
        FROM tv_trading_variables
        WHERE chart_category = "" OR chart_category IS NULL
        ORDER BY variable_id
    ''')

    remaining_rows = cursor.fetchall()
    if remaining_rows:
        print(f"❌ 여전히 문제가 있는 변수: {len(remaining_rows)}개")
        for variable_id, chart_category in remaining_rows:
            print(f"  - {variable_id}: '{chart_category}'")
    else:
        print("✅ 모든 chart_category 문제 해결됨")

    # 차트 카테고리 분포 확인
    print("\n📊 차트 카테고리 분포:")
    cursor.execute('''
        SELECT chart_category, COUNT(*) as count
        FROM tv_trading_variables
        GROUP BY chart_category
        ORDER BY chart_category
    ''')

    category_rows = cursor.fetchall()
    for category, count in category_rows:
        print(f"  - {category}: {count}개")

    conn.close()


if __name__ == "__main__":
    debug_and_fix_chart_category()
