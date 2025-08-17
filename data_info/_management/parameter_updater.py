#!/usr/bin/env python3
"""
Parameter Field Updater - Surgical DB Updates
안전한 파라미터 필드 업데이트 도구
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def get_db_path():
    """데이터베이스 경로 반환"""
    current_dir = Path(__file__).parent
    db_path = current_dir.parent.parent / "data" / "settings.sqlite3"
    return str(db_path)


def log_action(level: str, message: str):
    """작업 로그 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def update_parameter_field(variable_id: str, parameter_name: str, field_name: str, new_value: str):
    """파라미터 필드 업데이트"""
    log_action("INFO", f"Updating {variable_id}.{parameter_name}.{field_name} → '{new_value}'")

    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 현재 값 확인
        cursor.execute(f"""
            SELECT parameter_id, {field_name}
            FROM tv_variable_parameters
            WHERE variable_id = ? AND parameter_name = ?
        """, (variable_id, parameter_name))

        current = cursor.fetchone()
        if not current:
            print(f"❌ 찾을 수 없음: {variable_id}.{parameter_name}")
            return False

        param_id, old_value = current

        print("\n🔍 수정 대상:")
        print(f"  Variable: {variable_id}")
        print(f"  Parameter: {parameter_name}")
        print(f"  Field: {field_name}")
        print(f"  Current: {old_value}")
        print(f"  New: {new_value}")

        user_input = input("\n계속하시겠습니까? (y/N): ").strip().lower()
        if user_input != 'y':
            print("❌ 취소됨")
            return False

        # 백업 생성
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table = f"backup_param_{param_id}_{backup_id}"
        cursor.execute(f"""
            CREATE TABLE {backup_table} AS
            SELECT * FROM tv_variable_parameters
            WHERE parameter_id = ?
        """, (param_id,))
        log_action("INFO", f"백업 생성: {backup_table}")

        # 업데이트 실행
        update_sql = f"UPDATE tv_variable_parameters SET {field_name} = ? WHERE parameter_id = ?"
        cursor.execute(update_sql, (new_value, param_id))

        # 검증
        cursor.execute(f"SELECT {field_name} FROM tv_variable_parameters WHERE parameter_id = ?", (param_id,))
        updated_value = cursor.fetchone()[0]

        if updated_value == new_value:
            conn.commit()
            print("✅ 업데이트 성공!")
            log_action("SUCCESS", f"'{old_value}' → '{new_value}'")
            return True
        else:
            conn.rollback()
            print(f"❌ 업데이트 실패: 예상값({new_value}) != 실제값({updated_value})")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        log_action("ERROR", f"Update failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    print("🛠️  Parameter Field Updater")
    print("=" * 50)

    if len(sys.argv) != 5:
        print("사용법: python parameter_updater.py VARIABLE_ID PARAMETER_NAME FIELD_NAME 'NEW_VALUE'")
        print("예시: python parameter_updater.py MACD macd_type enum_values_ko '[\"MACD선\", \"시그널선\", \"히스토그램\"]'")
        print("가능한 필드: default_value, enum_values, enum_values_ko, min_value, max_value")
        sys.exit(1)

    variable_id = sys.argv[1]
    parameter_name = sys.argv[2]
    field_name = sys.argv[3]
    new_value = sys.argv[4]

    # 유효한 필드인지 확인
    valid_fields = ['default_value', 'enum_values', 'enum_values_ko', 'min_value', 'max_value']
    if field_name not in valid_fields:
        print(f"❌ 유효하지 않은 필드: {field_name}")
        print(f"사용 가능한 필드: {', '.join(valid_fields)}")
        sys.exit(1)

    success = update_parameter_field(variable_id, parameter_name, field_name, new_value)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
