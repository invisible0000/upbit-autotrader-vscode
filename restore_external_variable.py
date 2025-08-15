#!/usr/bin/env python3
"""
external_variable 복구 스크립트
- 도메인 모델에 external_variable 타입 복원
- 데이터베이스에서 external_variable 타입 복원
- YAML에서 external_variable 타입 복원
"""

import sqlite3
import yaml
from pathlib import Path

def restore_external_variable():
    """external_variable 타입 복구"""

    print("=== EXTERNAL_VARIABLE 복구 작업 ===\n")

    # 1. 데이터베이스 복구
    restore_db_external_variable()

    # 2. YAML 복구
    restore_yaml_external_variable()

    print("\n✅ 모든 복구 작업 완료!")

def restore_db_external_variable():
    """데이터베이스에서 external_variable 복구"""

    print("1. 데이터베이스 복구")

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # 변수 참조 파라미터들을 external_variable로 복구
    variable_reference_params = [
        ("PYRAMID_TARGET", "tracking_variable"),
        ("META_TRAILING_STOP", "tracking_variable"),
        ("META_RSI_CHANGE", "source_variable"),
        ("META_PRICE_BREAKOUT", "source_variable"),
        ("META_PRICE_BREAKOUT", "reference_value"),
        ("META_VOLUME_SPIKE", "source_variable")
    ]

    restored_count = 0

    for variable_id, param_name in variable_reference_params:
        cursor.execute("""
            UPDATE tv_variable_parameters
            SET parameter_type = 'external_variable'
            WHERE variable_id = ? AND parameter_name = ?
        """, (variable_id, param_name))

        if cursor.rowcount > 0:
            print(f"  ✅ {variable_id}.{param_name}: string → external_variable")
            restored_count += 1

    conn.commit()
    conn.close()

    print(f"  📊 DB에서 {restored_count}개 파라미터 복구됨")

def restore_yaml_external_variable():
    """YAML에서 external_variable 복구"""

    print("\n2. YAML 파일 복구")

    yaml_file = Path("data_info/tv_variable_parameters.yaml")

    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    parameters = data.get('variable_parameters', {})

    # 변수 참조 파라미터 키들
    reference_param_keys = [
        "PYRAMID_TARGET_tracking_variable",
        "META_TRAILING_STOP_tracking_variable",
        "META_RSI_CHANGE_source_variable",
        "META_PRICE_BREAKOUT_source_variable",
        "META_PRICE_BREAKOUT_reference_value",
        "META_VOLUME_SPIKE_source_variable"
    ]

    restored_count = 0

    for key in reference_param_keys:
        if key in parameters:
            old_type = parameters[key].get('parameter_type', '')
            if old_type != 'external_variable':
                parameters[key]['parameter_type'] = 'external_variable'
                print(f"  ✅ {key}: {old_type} → external_variable")
                restored_count += 1

    if restored_count > 0:
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                     sort_keys=False, indent=2)
        print(f"  📄 YAML 파일 저장됨 ({restored_count}개 복구)")
    else:
        print("  ℹ️  복구할 항목이 없습니다")

def verify_restoration():
    """복구 결과 검증"""

    print("\n3. 복구 결과 검증")

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT variable_id, parameter_name, parameter_type
        FROM tv_variable_parameters
        WHERE parameter_type = 'external_variable'
        ORDER BY variable_id, parameter_name
    """)

    results = cursor.fetchall()

    if results:
        print(f"  ✅ external_variable 타입 파라미터: {len(results)}개")
        for var_id, param_name, param_type in results:
            print(f"    - {var_id}.{param_name}")
    else:
        print("  ❌ external_variable 타입 파라미터가 없습니다")

    conn.close()

if __name__ == "__main__":
    restore_external_variable()
    verify_restoration()
