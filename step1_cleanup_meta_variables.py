"""
메타 변수 DB 정리 및 통일성 확보
1. 명명 통일: PYRAMID_TARGET → META_PYRAMID_TARGET
2. 미사용 메타 변수 비활성화
3. enum 값들 한국어 매핑 완료
"""

import sqlite3
from pathlib import Path


def step1_cleanup_meta_variables():
    """1단계: 메타 변수 정리 및 통일성 확보"""
    db_path = Path("data/settings.sqlite3")

    if not db_path.exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("🔧 1단계: 메타 변수 DB 정리 시작...")

        # 1. PYRAMID_TARGET → META_PYRAMID_TARGET 이름 변경
        print("\n📝 1-1. PYRAMID_TARGET → META_PYRAMID_TARGET 변경...")

        # 변수 이름 변경
        cursor.execute("""
            UPDATE tv_trading_variables
            SET variable_id = 'META_PYRAMID_TARGET'
            WHERE variable_id = 'PYRAMID_TARGET'
        """)

        # 파라미터 변수 ID 변경
        cursor.execute("""
            UPDATE tv_variable_parameters
            SET variable_id = 'META_PYRAMID_TARGET'
            WHERE variable_id = 'PYRAMID_TARGET'
        """)

        print(f"✅ PYRAMID_TARGET → META_PYRAMID_TARGET 변경 완료")

        # 2. 미사용 메타 변수들 비활성화 (완전 삭제는 위험하므로 비활성화)
        print("\n📝 1-2. 미사용 메타 변수 비활성화...")
        unused_meta_vars = [
            'META_RSI_CHANGE',
            'META_PRICE_BREAKOUT',
            'META_VOLUME_SPIKE',
            'MARTINGALE_TARGET',
            'DYNAMIC_PROFIT_TARGET',
            'DYNAMIC_LOSS_THRESHOLD'
        ]

        for var_id in unused_meta_vars:
            cursor.execute("""
                UPDATE tv_trading_variables
                SET is_active = 0
                WHERE variable_id = ?
            """, (var_id,))

            affected = cursor.rowcount
            if affected > 0:
                print(f"✅ {var_id} 비활성화 완료")
            else:
                print(f"⚠️ {var_id} 변수를 찾을 수 없음")

        # 3. 사용할 메타 변수들 한국어 표시명 개선
        print("\n📝 1-3. 메타 변수 한국어 표시명 개선...")

        meta_var_updates = {
            'META_TRAILING_STOP': '트레일링 스탑',
            'META_PYRAMID_TARGET': '피라미딩'
        }

        for var_id, display_name in meta_var_updates.items():
            cursor.execute("""
                UPDATE tv_trading_variables
                SET display_name_ko = ?, is_active = 1
                WHERE variable_id = ?
            """, (display_name, var_id))
            print(f"✅ {var_id} → {display_name}")

        # 4. enum 값들 한국어 매핑 개선
        print("\n📝 1-4. enum 파라미터 한국어 매핑 개선...")

        # META_TRAILING_STOP enum 개선
        enum_updates = [
            {
                'variable_id': 'META_TRAILING_STOP',
                'parameter_name': 'trail_direction',
                'enum_values': '["up:상승추적", "down:하락추적", "bidirectional:양방향추적"]',
                'display_name_ko': '추적 방향'
            },
            {
                'variable_id': 'META_TRAILING_STOP',
                'parameter_name': 'calculation_method',
                'enum_values': '["static_value:고정값", "percentage_of_extreme:극값비율", "entry_price_percent:진입가비율", "average_price_percent:평단가비율"]',
                'display_name_ko': '계산 방식'
            },
            {
                'variable_id': 'META_TRAILING_STOP',
                'parameter_name': 'reset_trigger',
                'enum_values': '["never:초기화안함", "position_entry:포지션진입시", "position_exit:포지션청산시", "manual_reset:수동리셋", "condition_met:조건충족시"]',
                'display_name_ko': '초기화 트리거'
            },
            # META_PYRAMID_TARGET enum 개선
            {
                'variable_id': 'META_PYRAMID_TARGET',
                'parameter_name': 'direction',
                'enum_values': '["up:상승방향", "down:하락방향", "bidirectional:양방향"]',
                'display_name_ko': '방향'
            },
            {
                'variable_id': 'META_PYRAMID_TARGET',
                'parameter_name': 'calculation_method',
                'enum_values': '["static_value:고정값", "percentage_of_extreme:극값비율", "entry_price_percent:진입가비율", "average_price_percent:평단가비율"]',
                'display_name_ko': '계산 방식'
            },
            {
                'variable_id': 'META_PYRAMID_TARGET',
                'parameter_name': 'reset_trigger',
                'enum_values': '["never:초기화안함", "position_entry:포지션진입시", "position_exit:포지션청산시", "manual_reset:수동리셋", "condition_met:조건충족시"]',
                'display_name_ko': '초기화 트리거'
            }
        ]

        for update in enum_updates:
            cursor.execute("""
                UPDATE tv_variable_parameters
                SET enum_values = ?, display_name_ko = ?
                WHERE variable_id = ? AND parameter_name = ?
            """, (
                update['enum_values'],
                update['display_name_ko'],
                update['variable_id'],
                update['parameter_name']
            ))

            if cursor.rowcount > 0:
                print(f"✅ {update['variable_id']}.{update['parameter_name']} enum 한국어 매핑 완료")
            else:
                print(f"⚠️ {update['variable_id']}.{update['parameter_name']} 파라미터를 찾을 수 없음")

        conn.commit()

        # 5. 정리 결과 확인
        print("\n📋 정리 결과 확인...")
        cursor.execute("""
            SELECT variable_id, display_name_ko, is_active
            FROM tv_trading_variables
            WHERE variable_id LIKE 'META_%'
            ORDER BY is_active DESC, variable_id
        """)

        print("\n=== 메타 변수 정리 완료 ===")
        for row in cursor.fetchall():
            status = "✅ 활성" if row[2] else "❌ 비활성"
            print(f"{row[0]} - {row[1]} ({status})")

        print("\n🎉 1단계 메타 변수 정리 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    step1_cleanup_meta_variables()
