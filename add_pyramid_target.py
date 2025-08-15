"""
PYRAMID_TARGET 메타 변수 추가
"""

import sqlite3
from pathlib import Path

def add_pyramid_target():
    """PYRAMID_TARGET 메타 변수 추가"""
    db_path = Path("data/settings.sqlite3")

    if not db_path.exists():
        print(f"❌ 데이터베이스 파일이 없습니다: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # PYRAMID_TARGET 변수가 있는지 확인
        cursor.execute("SELECT COUNT(*) FROM tv_trading_variables WHERE variable_id = 'PYRAMID_TARGET'")
        if cursor.fetchone()[0] == 0:
            # PYRAMID_TARGET 변수 추가
            cursor.execute("""
                INSERT INTO tv_trading_variables (
                    variable_id, display_name_ko, display_name_en,
                    category_name, purpose_category, description,
                    data_type, chart_category, comparison_group, is_active
                ) VALUES (
                    'PYRAMID_TARGET', '피라미딩 목표', 'Pyramid Target',
                    'dynamic_management', 'trend', '분할 매수/매도를 위한 목표 가격 추적',
                    'decimal', 'overlay', 'price_comparable', 1
                )
            """)
            print("✅ PYRAMID_TARGET 변수 추가 완료")

        # PYRAMID_TARGET 파라미터들 추가
        pyramid_params = [
            {
                'param_name': 'calculation_method',
                'display_name': '계산 방법',
                'type': 'enum',
                'default': 'percentage_of_extreme',
                'enum_values': '["percentage_of_extreme", "entry_price_percent", "fixed_price_difference"]',
                'description': '피라미딩 목표가 계산 방법'
            },
            {
                'param_name': 'percentage_value',
                'display_name': '비율 값',
                'type': 'decimal',
                'default': '2.0',
                'enum_values': None,
                'description': '목표가 계산에 사용할 비율(%)'
            }
        ]

        # 기존 파라미터 확인
        cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters WHERE variable_id = 'PYRAMID_TARGET'")
        existing_count = cursor.fetchone()[0]

        if existing_count == 0:
            for param in pyramid_params:
                cursor.execute("""
                    INSERT INTO tv_variable_parameters (
                        variable_id, parameter_name, display_name_ko,
                        parameter_type, default_value, enum_values,
                        description, is_required, min_value, max_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, NULL, NULL)
                """, (
                    'PYRAMID_TARGET',
                    param['param_name'],
                    param['display_name'],
                    param['type'],
                    param['default'],
                    param['enum_values'],
                    param['description']
                ))
                print(f"✅ PYRAMID_TARGET.{param['param_name']} 파라미터 추가 완료")
        else:
            print(f"⚠️ PYRAMID_TARGET 파라미터가 이미 {existing_count}개 존재합니다")

        conn.commit()

        # 결과 확인
        print("\n=== PYRAMID_TARGET 메타 변수 확인 ===")
        cursor.execute("""
            SELECT
                p.parameter_name, p.display_name_ko, p.parameter_type,
                p.default_value, p.enum_values
            FROM tv_variable_parameters p
            WHERE p.variable_id = 'PYRAMID_TARGET'
        """)

        for row in cursor.fetchall():
            print(f"파라미터: {row[0]} ({row[1]})")
            print(f"  타입: {row[2]}, 기본값: {row[3]}")
            print(f"  enum: {row[4]}")
            print("---")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    add_pyramid_target()
