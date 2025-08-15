#!/usr/bin/env python3
"""
나머지 6개 파라미터 일괄 분석:
2. META_TRAILING_STOP.calculation_method
3. META_TRAILING_STOP.reset_trigger
4. META_TRAILING_STOP.trail_direction
5. PYRAMID_TARGET.calculation_method
6. PYRAMID_TARGET.direction
7. PYRAMID_TARGET.reset_trigger
"""

import sqlite3
import yaml
import json

def analyze_remaining_parameters():
    """나머지 6개 파라미터 일괄 분석"""

    print("=== 나머지 6개 파라미터 일괄 분석 ===\n")

    # 분석 대상 목록
    target_params = [
        ("META_TRAILING_STOP", "calculation_method", 2),
        ("META_TRAILING_STOP", "reset_trigger", 3),
        ("META_TRAILING_STOP", "trail_direction", 4),
        ("PYRAMID_TARGET", "calculation_method", 5),
        ("PYRAMID_TARGET", "direction", 6),
        ("PYRAMID_TARGET", "reset_trigger", 7)
    ]

    # 데이터베이스에서 현재 상태 확인
    conn = sqlite3.connect('data/settings.sqlite3')

    for variable_id, param_name, number in target_params:
        print(f"📋 {number}번 분석: {variable_id}.{param_name}")
        analyze_single_parameter(conn, variable_id, param_name, number)
        print()

    conn.close()

    # 최종 권장사항
    print("🎯 최종 권장사항:")
    print("   모든 6개 파라미터를 enum으로 변경 권장")
    print("   이유: enum_values가 정의되어 있고, 고정된 선택지가 있음")

def analyze_single_parameter(conn, variable_id, param_name, number):
    """개별 파라미터 분석"""

    cursor = conn.cursor()

    # DB에서 파라미터 정보 조회
    cursor.execute("""
        SELECT parameter_type, default_value, enum_values, description
        FROM tv_variable_parameters
        WHERE variable_id = ? AND parameter_name = ?
    """, (variable_id, param_name))

    result = cursor.fetchone()

    if not result:
        print(f"   ❌ DB에서 찾을 수 없음")
        return

    param_type, default_value, enum_values, description = result

    print(f"   📊 현재 상태:")
    print(f"     - parameter_type: {param_type}")
    print(f"     - default_value: {default_value}")
    print(f"     - description: {description}")

    # enum_values 분석
    if enum_values:
        try:
            parsed_values = json.loads(enum_values)
            print(f"     - enum_values ({len(parsed_values)}개):")
            for i, value in enumerate(parsed_values, 1):
                print(f"       {i}. {value}")

            # enum 변경 필요성 판단
            if len(parsed_values) > 1:
                print(f"   ✅ ENUM 변경 필요: {len(parsed_values)}개 고정 선택지")
                analyze_why_enum_needed(variable_id, param_name, parsed_values)
            else:
                print(f"   ⚠️  선택지 1개: enum 불필요할 수 있음")

        except Exception as e:
            print(f"   ❌ enum_values 파싱 오류: {e}")
    else:
        print(f"   ❌ enum_values 없음")

def analyze_why_enum_needed(variable_id, param_name, enum_values):
    """각 파라미터별로 enum이 필요한 이유 분석"""

    print(f"   🎯 ENUM 필요 이유:")

    if param_name == "calculation_method":
        print(f"     💡 계산 방법은 알고리즘으로 미리 정의됨:")
        for value in enum_values:
            print(f"       - {value}")
        print(f"     🚫 사용자가 임의로 만들 수 없음 → ENUM 필수")

    elif param_name == "reset_trigger":
        print(f"     💡 리셋 트리거는 시스템 이벤트로 제한됨:")
        for value in enum_values:
            print(f"       - {value}")
        print(f"     🚫 존재하지 않는 이벤트 입력 방지 → ENUM 필수")

    elif param_name in ["trail_direction", "direction"]:
        print(f"     💡 방향은 up/down 등으로 제한됨:")
        for value in enum_values:
            print(f"       - {value}")
        print(f"     🚫 'left', 'right' 같은 잘못된 방향 방지 → ENUM 필수")

    else:
        print(f"     💡 고정된 선택지가 있어 사용자 실수 방지 필요")

def generate_batch_fix_script():
    """일괄 수정 스크립트 생성"""

    print("\n📝 일괄 수정 스크립트:")

    script_content = '''
# 나머지 6개 파라미터를 enum으로 일괄 변경
UPDATE tv_variable_parameters SET parameter_type = 'enum'
WHERE (variable_id = 'META_TRAILING_STOP' AND parameter_name = 'calculation_method')
   OR (variable_id = 'META_TRAILING_STOP' AND parameter_name = 'reset_trigger')
   OR (variable_id = 'META_TRAILING_STOP' AND parameter_name = 'trail_direction')
   OR (variable_id = 'PYRAMID_TARGET' AND parameter_name = 'calculation_method')
   OR (variable_id = 'PYRAMID_TARGET' AND parameter_name = 'direction')
   OR (variable_id = 'PYRAMID_TARGET' AND parameter_name = 'reset_trigger');
'''

    print(script_content)

    # 실제 SQL 실행 여부 확인
    response = input("위 SQL을 실행하시겠습니까? (y/N): ")
    if response.lower() == 'y':
        execute_batch_fix()

def execute_batch_fix():
    """일괄 수정 실행"""

    print("\n🔧 일괄 수정 실행 중...")

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # 각각 개별적으로 수정하여 개수 확인
    updates = [
        ("META_TRAILING_STOP", "calculation_method", 2),
        ("META_TRAILING_STOP", "reset_trigger", 3),
        ("META_TRAILING_STOP", "trail_direction", 4),
        ("PYRAMID_TARGET", "calculation_method", 5),
        ("PYRAMID_TARGET", "direction", 6),
        ("PYRAMID_TARGET", "reset_trigger", 7)
    ]

    total_updated = 0

    for variable_id, param_name, number in updates:
        cursor.execute("""
            UPDATE tv_variable_parameters
            SET parameter_type = 'enum'
            WHERE variable_id = ? AND parameter_name = ?
        """, (variable_id, param_name))

        if cursor.rowcount > 0:
            print(f"   ✅ {number}번 {variable_id}.{param_name}: → enum")
            total_updated += cursor.rowcount
        else:
            print(f"   ⚠️  {number}번 {variable_id}.{param_name}: 변경 없음")

    conn.commit()
    conn.close()

    print(f"\n✅ 총 {total_updated}개 파라미터가 enum으로 변경되었습니다!")

if __name__ == "__main__":
    analyze_remaining_parameters()
    generate_batch_fix_script()
