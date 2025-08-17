#!/usr/bin/env python3
"""
단계별 DB 업데이터 - 보수적 접근법
하나의 변수, 하나의 컬럼씩 안전하게 업데이트
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "settings.sqlite3"


def log_action(action, details):
    """작업 로그 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {action}: {details}")

def verify_before_action(variable_id, table_name, description):
    """작업 전 현재 상태 확인"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE variable_id = ?", (variable_id,))
    count = cursor.fetchone()[0]

    conn.close()

    log_action("BEFORE", f"{description} - {table_name}: {count} rows for {variable_id}")
    return count


def verify_after_action(variable_id, table_name, description, expected_count):
    """작업 후 결과 확인"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE variable_id = ?", (variable_id,))
    count = cursor.fetchone()[0]

    conn.close()

    log_action("AFTER", f"{description} - {table_name}: {count} rows for {variable_id}")

    if count == expected_count:
        log_action("SUCCESS", f"Expected {expected_count}, got {count}")
        return True
    else:
        log_action("ERROR", f"Expected {expected_count}, got {count}")
        return False


def add_help_text_single(variable_id, parameter_name, help_text_ko, help_text_en, tooltip_ko, tooltip_en):
    """단일 help_text 추가"""
    description = f"Adding help text for {variable_id}.{parameter_name}"

    # 사전 확인
    before_count = verify_before_action(variable_id, "tv_help_texts", description)

    # 사용자 확인
    print(f"\n🔄 {description}")
    print(f"   Variable: {variable_id}")
    print(f"   Parameter: {parameter_name}")
    print(f"   Help Text (KO): {help_text_ko[:50]}...")
    print(f"   Tooltip (KO): {tooltip_ko[:30]}...")

    response = input("계속 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        log_action("CANCELLED", "User cancelled operation")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # INSERT 실행
        cursor.execute("""
            INSERT INTO tv_help_texts
            (variable_id, parameter_name, help_text_ko, help_text_en, tooltip_ko, tooltip_en,
             language, context_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'ko', 'tooltip', datetime('now'), datetime('now'))
        """, (variable_id, parameter_name, help_text_ko, help_text_en, tooltip_ko, tooltip_en))

        conn.commit()
        conn.close()

        # 사후 확인
        success = verify_after_action(variable_id, "tv_help_texts", description, before_count + 1)
        return success

    except Exception as e:
        log_action("ERROR", f"Database operation failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def delete_null_help_text_single(variable_id, row_id, preview_text):
    """단일 NULL help_text 삭제"""
    description = f"Deleting NULL help text for {variable_id} (ID: {row_id})"

    # 사전 확인
    before_count = verify_before_action(variable_id, "tv_help_texts", description)

    # 사용자 확인
    print(f"\n🗑️ {description}")
    print(f"   Variable: {variable_id}")
    print(f"   Row ID: {row_id}")
    print(f"   Content: {preview_text[:50]}...")
    print("   Reason: 변수 전체 설명은 tv_trading_variables.description에서 관리")

    response = input("정말로 삭제하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        log_action("CANCELLED", "User cancelled deletion")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # DELETE 실행
        cursor.execute("DELETE FROM tv_help_texts WHERE id = ? AND variable_id = ? AND parameter_name IS NULL",
                       (row_id, variable_id))

        if cursor.rowcount == 0:
            log_action("WARNING", "No rows were deleted - row may not exist")
            conn.close()
            return False

        conn.commit()
        conn.close()

        # 사후 확인
        success = verify_after_action(variable_id, "tv_help_texts", description, before_count - 1)
        return success

    except Exception as e:
        log_action("ERROR", f"Database deletion failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def add_placeholder_text_single(variable_id, parameter_name, placeholder_ko, placeholder_en, example_value):
    """단일 placeholder_text 추가"""
    description = f"Adding placeholder text for {variable_id}.{parameter_name}"

    # 사전 확인
    before_count = verify_before_action(variable_id, "tv_placeholder_texts", description)

    # 사용자 확인
    print(f"\n🔄 {description}")
    print(f"   Variable: {variable_id}")
    print(f"   Parameter: {parameter_name}")
    print(f"   Placeholder (KO): {placeholder_ko}")
    print(f"   Example: {example_value}")

    response = input("계속 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        log_action("CANCELLED", "User cancelled operation")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # INSERT 실행
        cursor.execute("""
            INSERT INTO tv_placeholder_texts
            (variable_id, parameter_name, placeholder_text_ko, placeholder_text_en,
             example_value, validation_pattern, input_type, language, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, '', 'text', 'ko', datetime('now'), datetime('now'))
        """, (variable_id, parameter_name, placeholder_ko, placeholder_en, example_value))

        conn.commit()
        conn.close()

        # 사후 확인
        success = verify_after_action(variable_id, "tv_placeholder_texts", description, before_count + 1)
        return success

    except Exception as e:
        log_action("ERROR", f"Database operation failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def main():
    print("🛠️  단계별 DB 업데이터 - 보수적 접근법")
    print("=" * 60)
    print(f"📁 DB Path: {DB_PATH}")

    if len(sys.argv) < 2:
        print("사용법: python step_by_step_db_updater.py <command> [args...]")
        print("Commands:")
        print("  add_help_text VARIABLE_ID PARAMETER_NAME 'HELP_TEXT_KO' 'HELP_TEXT_EN' 'TOOLTIP_KO' 'TOOLTIP_EN'")
        print("  add_placeholder VARIABLE_ID PARAMETER_NAME 'PLACEHOLDER_KO' 'PLACEHOLDER_EN' 'EXAMPLE'")
        print("  delete_null_help ROW_ID VARIABLE_ID 'PREVIEW_TEXT'")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add_help_text" and len(sys.argv) >= 8:
        variable_id = sys.argv[2]
        parameter_name = sys.argv[3] if sys.argv[3] != 'null' else None
        help_text_ko = sys.argv[4]
        help_text_en = sys.argv[5]
        tooltip_ko = sys.argv[6]
        tooltip_en = sys.argv[7]

        success = add_help_text_single(variable_id, parameter_name, help_text_ko, help_text_en, tooltip_ko, tooltip_en)
        sys.exit(0 if success else 1)

    elif command == "add_placeholder" and len(sys.argv) >= 7:
        variable_id = sys.argv[2]
        parameter_name = sys.argv[3]
        placeholder_ko = sys.argv[4]
        placeholder_en = sys.argv[5]
        example_value = sys.argv[6]

        success = add_placeholder_text_single(variable_id, parameter_name, placeholder_ko, placeholder_en, example_value)
        sys.exit(0 if success else 1)

    elif command == "delete_null_help" and len(sys.argv) >= 5:
        row_id = int(sys.argv[2])
        variable_id = sys.argv[3]
        preview_text = sys.argv[4]

        success = delete_null_help_text_single(variable_id, row_id, preview_text)
        sys.exit(0 if success else 1)

    else:
        print("❌ 잘못된 명령어 또는 인수입니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
