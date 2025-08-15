"""
현재 메타 변수 상태 조사
"""

import sqlite3

def analyze_meta_variables():
    """현재 메타 변수들 상태 분석"""
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    print('=== 현재 메타 변수 목록 ===')
    cursor.execute("""
        SELECT variable_id, display_name_ko, is_active
        FROM tv_trading_variables
        WHERE variable_id LIKE 'META_%' OR variable_id = 'PYRAMID_TARGET'
    """)
    for row in cursor.fetchall():
        print(f'{row[0]} - {row[1]} (활성: {row[2]})')

    print('\n=== 현재 dynamic_management 카테고리 변수들 ===')
    cursor.execute("""
        SELECT variable_id, display_name_ko, purpose_category
        FROM tv_trading_variables
        WHERE purpose_category = 'dynamic_management'
    """)
    for row in cursor.fetchall():
        print(f'{row[0]} - {row[1]} - {row[2]}')

    print('\n=== 메타 변수별 파라미터 개수 ===')
    cursor.execute("""
        SELECT
            p.variable_id,
            COUNT(*) as param_count,
            GROUP_CONCAT(p.parameter_name) as params
        FROM tv_variable_parameters p
        WHERE p.variable_id LIKE 'META_%' OR p.variable_id = 'PYRAMID_TARGET'
        GROUP BY p.variable_id
    """)
    for row in cursor.fetchall():
        print(f'{row[0]}: {row[1]}개 파라미터 ({row[2]})')

    conn.close()

if __name__ == "__main__":
    analyze_meta_variables()
