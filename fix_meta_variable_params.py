"""
메타 변수 파라미터를 enum으로 변경하고 한국어 매핑 추가
"""

import sqlite3
from pathlib import Path

def fix_meta_variable_parameters():
    """메타 변수 파라미터를 enum으로 변경"""
    db_path = Path("data/settings.sqlite3")

    if not db_path.exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 현재 메타 변수 파라미터 확인
        print("=== 현재 메타 변수 파라미터 ===")
        cursor.execute("""
            SELECT
                variable_id, parameter_id, parameter_name,
                display_name_ko, parameter_type, default_value, enum_values
            FROM tv_variable_parameters
            WHERE variable_id LIKE 'META_%'
        """)

        current_params = cursor.fetchall()
        for row in current_params:
            print(f"변수: {row[0]}, 파라미터: {row[1]}, 타입: {row[4]}, enum: {row[6]}")

        # META_TRAILING_STOP 파라미터 업데이트
        trailing_stop_updates = [
            {
                'param_id': 'trail_direction',
                'param_name': 'trail_direction',
                'display_name': '추적 방향',
                'type': 'enum',
                'default': 'up',
                'enum_values': 'up:상승추적,down:하락추적',
                'description': '트레일링 스탑 추적 방향 설정'
            }
        ]

        # PYRAMID_TARGET 파라미터 업데이트
        pyramid_updates = [
            {
                'param_id': 'calculation_method',
                'param_name': 'calculation_method',
                'display_name': '계산 방법',
                'type': 'enum',
                'default': 'percentage_of_extreme',
                'enum_values': 'percentage_of_extreme:극값기준비율,entry_price_percent:진입가격비율,fixed_price_difference:고정가격차이',
                'description': '피라미딩 목표가 계산 방법'
            }
        ]

        # META_TRAILING_STOP 파라미터 업데이트
        for update in trailing_stop_updates:
            cursor.execute("""
                UPDATE tv_variable_parameters
                SET
                    display_name_ko = ?,
                    parameter_type = ?,
                    default_value = ?,
                    enum_values = ?,
                    description = ?
                WHERE variable_id = 'META_TRAILING_STOP'
                AND parameter_id = ?
            """, (
                update['display_name'],
                update['type'],
                update['default'],
                update['enum_values'],
                update['description'],
                update['param_id']
            ))

            if cursor.rowcount > 0:
                print(f"✅ META_TRAILING_STOP.{update['param_id']} 업데이트 완료")
            else:
                print(f"⚠️ META_TRAILING_STOP.{update['param_id']} 파라미터가 없어서 업데이트 실패")

        # PYRAMID_TARGET 파라미터 업데이트
        for update in pyramid_updates:
            cursor.execute("""
                UPDATE tv_variable_parameters
                SET
                    display_name_ko = ?,
                    parameter_type = ?,
                    default_value = ?,
                    enum_values = ?,
                    description = ?
                WHERE variable_id = 'PYRAMID_TARGET'
                AND parameter_id = ?
            """, (
                update['display_name'],
                update['type'],
                update['default'],
                update['enum_values'],
                update['description'],
                update['param_id']
            ))

            if cursor.rowcount > 0:
                print(f"✅ PYRAMID_TARGET.{update['param_id']} 업데이트 완료")
            else:
                print(f"⚠️ PYRAMID_TARGET.{update['param_id']} 파라미터가 없어서 업데이트 실패")

        conn.commit()

        # 업데이트 결과 확인
        print("\n=== 업데이트 후 메타 변수 파라미터 ===")
        cursor.execute("""
            SELECT
                variable_id, parameter_id, display_name_ko,
                parameter_type, default_value, enum_values
            FROM tv_variable_parameters
            WHERE variable_id LIKE 'META_%'
        """)

        for row in cursor.fetchall():
            print(f"변수: {row[0]}")
            print(f"  파라미터: {row[1]} ({row[2]})")
            print(f"  타입: {row[3]}, 기본값: {row[4]}")
            print(f"  enum: {row[5]}")
            print("---")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    fix_meta_variable_parameters()
