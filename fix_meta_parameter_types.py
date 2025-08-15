#!/usr/bin/env python3
"""
META 변수들의 잘못된 parameter_type을 수정하는 스크립트
"""

import sqlite3
from pathlib import Path

def fix_parameter_types():
    """잘못된 parameter_type을 올바른 값으로 수정"""

    settings_db = Path("data/settings.sqlite3")

    if not settings_db.exists():
        print("settings.sqlite3 파일이 없습니다.")
        return

    # 파라미터 타입 매핑 정의
    type_mappings = {
        'external_variable': 'string',  # 외부 변수 참조는 문자열로
        'trail_direction': 'string',    # 방향은 문자열로 (up/down)
        'calculation_method': 'string', # 계산 방법은 문자열로
        'reset_trigger': 'string'       # 리셋 트리거는 문자열로
    }

    conn = sqlite3.connect(settings_db)
    cursor = conn.cursor()

    print("=== META 변수 파라미터 타입 수정 ===\n")

    try:
        # 잘못된 파라미터 타입들을 수정
        for wrong_type, correct_type in type_mappings.items():
            print(f"'{wrong_type}' → '{correct_type}' 수정 중...")

            cursor.execute("""
                UPDATE tv_variable_parameters
                SET parameter_type = ?
                WHERE parameter_type = ?
            """, (correct_type, wrong_type))

            affected_rows = cursor.rowcount
            print(f"  → {affected_rows}개 레코드 수정됨")

        # 변경사항 커밋
        conn.commit()
        print("\n✅ 모든 파라미터 타입이 수정되었습니다.")

        # 검증
        print("\n=== 수정 후 검증 ===")
        cursor.execute("""
            SELECT variable_id, parameter_name, parameter_type
            FROM tv_variable_parameters
            WHERE parameter_type NOT IN ('boolean', 'integer', 'string', 'decimal')
        """)

        invalid_params = cursor.fetchall()
        if invalid_params:
            print("⚠️  여전히 잘못된 parameter_type이 있습니다:")
            for row in invalid_params:
                print(f"  - {row[0]}.{row[1]}: {row[2]}")
        else:
            print("✅ 모든 parameter_type이 유효합니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        conn.rollback()
    finally:
        conn.close()

def verify_meta_variables():
    """META 변수들이 올바르게 로드되는지 확인"""

    print("\n=== META 변수 로딩 테스트 ===")

    try:
        # 실제 리포지토리 클래스를 사용해서 테스트
        import sys
        sys.path.append('.')

        from upbit_auto_trading.infrastructure.repositories.sqlite_trading_variable_repository import SqliteTradingVariableRepository
        from upbit_auto_trading.infrastructure.logging import create_component_logger

        logger = create_component_logger("MetaTest")
        repo = SqliteTradingVariableRepository(
            database_path="data/settings.sqlite3",
            logger=logger
        )

        # META 변수들 로딩 테스트
        meta_variables = [
            "PYRAMID_TARGET",
            "META_TRAILING_STOP",
            "META_RSI_CHANGE",
            "META_PRICE_BREAKOUT",
            "META_VOLUME_SPIKE"
        ]

        for var_id in meta_variables:
            print(f"  {var_id} 로딩 테스트...")
            try:
                detail = repo.get_trading_variable_detail(var_id)
                if detail:
                    param_count = len(detail.parameters)
                    print(f"    ✅ 성공 (파라미터 {param_count}개)")
                else:
                    print(f"    ❌ 변수를 찾을 수 없음")
            except Exception as e:
                print(f"    ❌ 오류: {e}")

    except ImportError as e:
        print(f"모듈 import 실패: {e}")
    except Exception as e:
        print(f"테스트 오류: {e}")

if __name__ == "__main__":
    fix_parameter_types()
    verify_meta_variables()
