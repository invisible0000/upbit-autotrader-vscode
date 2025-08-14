#!/usr/bin/env python3
"""안전한 금융 데이터 타입 마이그레이션 도구"""

import sqlite3
import shutil
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def create_backup(db_path):
    """데이터베이스 백업 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ 백업 생성: {backup_path}")
    return backup_path


def validate_decimal_conversion(value):
    """Decimal 변환 가능성 검증"""
    if value is None:
        return True, None

    try:
        decimal_value = Decimal(str(value))
        return True, decimal_value
    except Exception as e:
        return False, str(e)


def migrate_execution_history():
    """execution_history 테이블의 profit_loss 컬럼 마이그레이션"""
    print("🔄 execution_history.profit_loss 마이그레이션 시작...")

    # 백업 생성
    backup_path = create_backup("data/strategies.sqlite3")

    conn = sqlite3.connect("data/strategies.sqlite3")
    cursor = conn.cursor()

    try:
        # 1. 기존 데이터 검증
        cursor.execute("SELECT id, profit_loss FROM execution_history WHERE profit_loss IS NOT NULL")
        rows = cursor.fetchall()

        conversion_issues = []
        for row_id, profit_loss in rows:
            is_valid, result = validate_decimal_conversion(profit_loss)
            if not is_valid:
                conversion_issues.append((row_id, profit_loss, result))

        if conversion_issues:
            print("❌ Decimal 변환 이슈 발견:")
            for row_id, value, error in conversion_issues:
                print(f"   ID {row_id}: {value} → {error}")
            return False

        # 2. 새 컬럼 추가
        cursor.execute("ALTER TABLE execution_history ADD COLUMN profit_loss_text TEXT")

        # 3. 데이터 변환
        cursor.execute("SELECT id, profit_loss FROM execution_history WHERE profit_loss IS NOT NULL")
        rows = cursor.fetchall()

        for row_id, profit_loss in rows:
            decimal_str = str(Decimal(str(profit_loss)))
            cursor.execute(
                "UPDATE execution_history SET profit_loss_text = ? WHERE id = ?",
                (decimal_str, row_id)
            )

        # 4. 검증
        cursor.execute("""
            SELECT COUNT(*) FROM execution_history
            WHERE profit_loss IS NOT NULL AND profit_loss_text IS NULL
        """)
        missing_count = cursor.fetchone()[0]

        if missing_count > 0:
            print(f"❌ 변환되지 않은 데이터 {missing_count}개 발견")
            conn.rollback()
            return False

        conn.commit()
        print("✅ execution_history.profit_loss 마이그레이션 완료")
        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def migrate_user_strategies():
    """user_strategies 테이블의 position_size_value 컬럼 마이그레이션"""
    print("🔄 user_strategies.position_size_value 마이그레이션 시작...")

    conn = sqlite3.connect("data/strategies.sqlite3")
    cursor = conn.cursor()

    try:
        # 1. 기존 데이터 검증
        cursor.execute("SELECT id, position_size_value FROM user_strategies WHERE position_size_value IS NOT NULL")
        rows = cursor.fetchall()

        conversion_issues = []
        for row_id, position_size in rows:
            is_valid, result = validate_decimal_conversion(position_size)
            if not is_valid:
                conversion_issues.append((row_id, position_size, result))

        if conversion_issues:
            print("❌ Decimal 변환 이슈 발견:")
            for row_id, value, error in conversion_issues:
                print(f"   ID {row_id}: {value} → {error}")
            return False

        # 2. 새 컬럼 추가
        cursor.execute("ALTER TABLE user_strategies ADD COLUMN position_size_value_text TEXT")

        # 3. 데이터 변환
        for row_id, position_size in rows:
            decimal_str = str(Decimal(str(position_size)))
            cursor.execute(
                "UPDATE user_strategies SET position_size_value_text = ? WHERE id = ?",
                (decimal_str, row_id)
            )

        # 4. 검증
        cursor.execute("""
            SELECT COUNT(*) FROM user_strategies
            WHERE position_size_value IS NOT NULL AND position_size_value_text IS NULL
        """)
        missing_count = cursor.fetchone()[0]

        if missing_count > 0:
            print(f"❌ 변환되지 않은 데이터 {missing_count}개 발견")
            conn.rollback()
            return False

        conn.commit()
        print("✅ user_strategies.position_size_value 마이그레이션 완료")
        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def migrate_compatibility_rules():
    """tv_variable_compatibility_rules 테이블 마이그레이션"""
    print("🔄 tv_variable_compatibility_rules 마이그레이션 시작...")

    # 백업 생성
    backup_path = create_backup("data/settings.sqlite3")

    conn = sqlite3.connect("data/settings.sqlite3")
    cursor = conn.cursor()

    try:
        # 1. 기존 데이터 검증
        cursor.execute("""
            SELECT id, min_value_constraint, max_value_constraint
            FROM tv_variable_compatibility_rules
            WHERE min_value_constraint IS NOT NULL OR max_value_constraint IS NOT NULL
        """)
        rows = cursor.fetchall()

        conversion_issues = []
        for row_id, min_val, max_val in rows:
            if min_val is not None:
                is_valid, result = validate_decimal_conversion(min_val)
                if not is_valid:
                    conversion_issues.append((row_id, "min_value_constraint", min_val, result))

            if max_val is not None:
                is_valid, result = validate_decimal_conversion(max_val)
                if not is_valid:
                    conversion_issues.append((row_id, "max_value_constraint", max_val, result))

        if conversion_issues:
            print("❌ Decimal 변환 이슈 발견:")
            for row_id, column, value, error in conversion_issues:
                print(f"   ID {row_id}, {column}: {value} → {error}")
            return False

        # 2. 새 컬럼들 추가
        cursor.execute("ALTER TABLE tv_variable_compatibility_rules ADD COLUMN min_value_constraint_text TEXT")
        cursor.execute("ALTER TABLE tv_variable_compatibility_rules ADD COLUMN max_value_constraint_text TEXT")

        # 3. 데이터 변환
        for row_id, min_val, max_val in rows:
            if min_val is not None:
                min_decimal_str = str(Decimal(str(min_val)))
                cursor.execute(
                    "UPDATE tv_variable_compatibility_rules SET min_value_constraint_text = ? WHERE id = ?",
                    (min_decimal_str, row_id)
                )

            if max_val is not None:
                max_decimal_str = str(Decimal(str(max_val)))
                cursor.execute(
                    "UPDATE tv_variable_compatibility_rules SET max_value_constraint_text = ? WHERE id = ?",
                    (max_decimal_str, row_id)
                )

        conn.commit()
        print("✅ tv_variable_compatibility_rules 마이그레이션 완료")
        return True

    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def run_migration_analysis():
    """마이그레이션 분석 실행"""
    print("🔍 === 금융 데이터 타입 마이그레이션 분석 ===")
    print()

    # 현재 상태 분석
    print("📊 현재 REAL 타입 사용 현황:")

    # Strategies DB
    conn = sqlite3.connect("data/strategies.sqlite3")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM execution_history WHERE profit_loss IS NOT NULL")
    profit_loss_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_strategies WHERE position_size_value IS NOT NULL")
    position_size_count = cursor.fetchone()[0]

    print(f"   • execution_history.profit_loss: {profit_loss_count}개 레코드")
    print(f"   • user_strategies.position_size_value: {position_size_count}개 레코드")

    conn.close()

    # Settings DB
    conn = sqlite3.connect("data/settings.sqlite3")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tv_variable_compatibility_rules WHERE min_value_constraint IS NOT NULL OR max_value_constraint IS NOT NULL")
    constraint_count = cursor.fetchone()[0]

    print(f"   • tv_variable_compatibility_rules 제약값: {constraint_count}개 레코드")

    conn.close()

    print()
    print("💡 마이그레이션 권장사항:")
    if profit_loss_count > 0 or position_size_count > 0 or constraint_count > 0:
        print("   ⚠️  금융 정밀도가 중요한 데이터가 REAL 타입으로 저장되어 있습니다")
        print("   🔧 TEXT 타입으로 마이그레이션을 권장합니다")
        print("   📋 마이그레이션 전 반드시 데이터를 백업하세요")
    else:
        print("   ✅ 현재 금융 데이터가 없거나 이미 안전한 상태입니다")


def main():
    """메인 실행 함수"""
    print("🛡️  안전한 금융 데이터 타입 마이그레이션 도구")
    print("=" * 60)

    # 분석 먼저 실행
    run_migration_analysis()

    print()
    print("🚀 마이그레이션 실행 옵션:")
    print("1. 분석만 실행 (현재 완료)")
    print("2. Strategies DB 마이그레이션")
    print("3. Settings DB 마이그레이션")
    print("4. 전체 마이그레이션")
    print()
    print("⚠️  주의: 실제 마이그레이션은 데이터 백업 후 신중하게 진행하세요")


if __name__ == "__main__":
    main()
