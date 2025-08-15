#!/usr/bin/env python3
"""
메타 변수 단순화 스크립트
- 불필요한 메타 변수 제거
- 트레일링 스탑, 피라미딩만 유지
- display_name 정리
"""

import sqlite3
import os


def simplify_meta_variables():
    """메타 변수 단순화"""
    print("🔧 === 메타 변수 단순화 작업 ===\n")

    db_path = "data/settings.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스가 없습니다: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. 기존 메타 변수 확인
        print("📋 기존 메타 변수 확인:")
        cursor.execute("""
            SELECT variable_id, display_name_ko
            FROM tv_trading_variables
            WHERE variable_id LIKE 'META_%' OR variable_id = 'PYRAMID_TARGET'
            ORDER BY variable_id
        """)
        existing_meta_vars = cursor.fetchall()

        for var_id, display_name in existing_meta_vars:
            print(f"  • {var_id:20s} | {display_name}")

        # 2. 불필요한 메타 변수 비활성화
        print(f"\n🗑️  불필요한 메타 변수 비활성화:")
        vars_to_deactivate = [
            'META_RSI_CHANGE',
            'META_PRICE_BREAKOUT',
            'META_VOLUME_SPIKE'
        ]

        for var_id in vars_to_deactivate:
            cursor.execute("""
                UPDATE tv_trading_variables
                SET is_active = 0
                WHERE variable_id = ?
            """, (var_id,))
            print(f"  ❌ {var_id} 비활성화")

        # 3. 남은 메타 변수 이름 정리
        print(f"\n✏️  메타 변수 이름 정리:")

        # META_TRAILING_STOP -> 트레일링 스탑
        cursor.execute("""
            UPDATE tv_trading_variables
            SET display_name_ko = '트레일링 스탑',
                display_name_en = 'Trailing Stop',
                description = '추적 대상의 고점/저점을 기록하고 설정된 차이만큼 벗어나면 신호 발생'
            WHERE variable_id = 'META_TRAILING_STOP'
        """)
        print(f"  ✅ META_TRAILING_STOP → '트레일링 스탑'")

        # PYRAMID_TARGET -> 피라미딩
        cursor.execute("""
            UPDATE tv_trading_variables
            SET display_name_ko = '피라미딩',
                display_name_en = 'Pyramiding',
                description = '불타기(상향추적)/물타기(하향추적) 기능. 추적 변수가 설정 조건을 만족하면 신호 발생'
            WHERE variable_id = 'PYRAMID_TARGET'
        """)
        print(f"  ✅ PYRAMID_TARGET → '피라미딩'")

        # 4. 변경사항 확인
        print(f"\n📋 최종 활성 메타 변수:")
        cursor.execute("""
            SELECT variable_id, display_name_ko, is_active
            FROM tv_trading_variables
            WHERE (variable_id LIKE 'META_%' OR variable_id = 'PYRAMID_TARGET')
            ORDER BY is_active DESC, variable_id
        """)
        final_meta_vars = cursor.fetchall()

        for var_id, display_name, is_active in final_meta_vars:
            status = "✅ 활성" if is_active else "❌ 비활성"
            print(f"  • {var_id:20s} | {display_name:15s} | {status}")

        conn.commit()
        print(f"\n✅ 메타 변수 단순화 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    simplify_meta_variables()
