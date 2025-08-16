#!/usr/bin/env python3
"""
메타변수 중복 제거 및 정리 스크립트
"""
import sqlite3
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def cleanup_meta_variables():
    """메타변수 중복 제거 및 정리"""
    print("🔧 메타변수 중복 제거 및 정리 시작...")

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    print("\n📊 현재 dynamic_management 카테고리 변수들:")
    cursor.execute('''
        SELECT variable_id, display_name_ko, parameter_required
        FROM tv_trading_variables
        WHERE purpose_category = "dynamic_management"
        ORDER BY variable_id
    ''')

    current_vars = cursor.fetchall()
    for variable_id, display_name_ko, parameter_required in current_vars:
        print(f"  - {variable_id}: '{display_name_ko}' (파라미터:{parameter_required})")

    # 1. META_ 접두사가 있는 변수들 삭제 (파라미터가 없는 더미 변수들)
    print("\n🗑️  META_ 접두사 변수들 삭제 중...")

    # META_PYRAMID_TARGET 삭제
    cursor.execute('DELETE FROM tv_trading_variables WHERE variable_id = "META_PYRAMID_TARGET"')
    print("  ✅ META_PYRAMID_TARGET 삭제")

    # META_TRAILING_STOP 삭제
    cursor.execute('DELETE FROM tv_trading_variables WHERE variable_id = "META_TRAILING_STOP"')
    print("  ✅ META_TRAILING_STOP 삭제")

    # 2. 남은 변수들의 이름을 더 명확하게 수정
    print("\n✏️  변수 이름 정리 중...")

    # PYRAMID_TARGET -> 피라미딩 (목표 제거)
    cursor.execute('''
        UPDATE tv_trading_variables
        SET display_name_ko = "피라미딩", display_name_en = "Pyramiding"
        WHERE variable_id = "PYRAMID_TARGET"
    ''')
    print("  ✅ PYRAMID_TARGET 이름 변경: '피라미딩 목표' -> '피라미딩'")

    # TRAILING_STOP -> 트레일링 스탑 (목표 제거)
    cursor.execute('''
        UPDATE tv_trading_variables
        SET display_name_ko = "트레일링 스탑", display_name_en = "Trailing Stop"
        WHERE variable_id = "TRAILING_STOP"
    ''')
    print("  ✅ TRAILING_STOP 이름 변경: '트레일링 스탑 목표' -> '트레일링 스탑'")

    # 3. parameter_required를 True로 설정 (실제로 파라미터가 있으므로)
    print("\n🔧 parameter_required 설정 중...")

    cursor.execute('''
        UPDATE tv_trading_variables
        SET parameter_required = 1
        WHERE variable_id IN ("PYRAMID_TARGET", "TRAILING_STOP")
    ''')
    print("  ✅ PYRAMID_TARGET, TRAILING_STOP parameter_required = True 설정")

    # 4. 변경 사항 커밋
    conn.commit()

    # 5. 결과 확인
    print("\n📊 정리 후 dynamic_management 카테고리 변수들:")
    cursor.execute('''
        SELECT variable_id, display_name_ko, parameter_required
        FROM tv_trading_variables
        WHERE purpose_category = "dynamic_management"
        ORDER BY variable_id
    ''')

    final_vars = cursor.fetchall()
    for variable_id, display_name_ko, parameter_required in final_vars:
        print(f"  - {variable_id}: '{display_name_ko}' (파라미터:{parameter_required})")

        # 각 변수의 파라미터 확인
        cursor.execute('''
            SELECT parameter_name, display_name_ko
            FROM tv_variable_parameters
            WHERE variable_id = ?
            ORDER BY display_order
        ''', (variable_id,))

        params = cursor.fetchall()
        if params:
            print(f"    📌 파라미터 ({len(params)}개):")
            for param_name, param_display in params:
                print(f"      • {param_name}: {param_display}")

    print("\n🎯 정리 완료!")
    print("이제 UI에서 중복 없이 깔끔하게 표시되고, 파라미터도 정상적으로 보일 것입니다.")

    conn.close()


if __name__ == "__main__":
    cleanup_meta_variables()
