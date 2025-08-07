#!/usr/bin/env python3
"""
API 키 보안 시스템 - secure_keys 테이블 생성 스크립트
Task 1.1.2: 기본 스키마 구현
"""

import sqlite3
from config.simple_paths import paths
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("SecureKeysTableCreation")


def main():
    """secure_keys 테이블 및 인덱스 생성"""
    try:
        # DB 연결
        db_path = paths.get_db_path('settings')
        logger.info(f"🔗 DB 경로: {db_path}")

        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()

            # 1. secure_keys 테이블 생성
            logger.info("📋 secure_keys 테이블 생성 시작...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS secure_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_type TEXT NOT NULL UNIQUE,
                    key_value BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("✅ secure_keys 테이블 생성 완료")

            # 2. 인덱스 생성
            logger.info("📊 인덱스 생성 시작...")
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_secure_keys_type ON secure_keys(key_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_secure_keys_created_at ON secure_keys(created_at)')
            logger.info("✅ 인덱스 생성 완료")

            # 3. 변경사항 저장
            conn.commit()
            logger.info("💾 변경사항 저장 완료")

            # 4. 테이블 존재 확인 (수정된 방식)
            logger.info("🔍 테이블 존재 확인...")
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='secure_keys'
            """)
            result = cursor.fetchone()

            if result:
                logger.info(f"✅ 테이블 확인 성공: {result[0]}")

                # 5. 테이블 구조 확인
                cursor.execute("PRAGMA table_info(secure_keys)")
                columns = cursor.fetchall()
                logger.info("📋 테이블 구조:")
                for col in columns:
                    logger.info(f"  - {col[1]} ({col[2]})")

                # 6. 인덱스 확인
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND tbl_name='secure_keys'
                """)
                indexes = cursor.fetchall()
                logger.info("📊 인덱스 목록:")
                for idx in indexes:
                    logger.info(f"  - {idx[0]}")

            else:
                logger.error("❌ 테이블이 생성되지 않았습니다!")
                return False

    except sqlite3.Error as e:
        logger.error(f"❌ SQLite 오류: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {e}")
        return False

    logger.info("🎯 secure_keys 테이블 생성 작업 완료!")
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 성공: secure_keys 테이블이 성공적으로 생성되었습니다!")
        print("📋 다음 단계: pytest로 테이블 존재 확인 테스트 실행")
        print("   pytest tests/infrastructure/services/test_secure_keys_schema_basic.py::test_secure_keys_table_exists -v")
    else:
        print("\n❌ 실패: 테이블 생성 중 오류가 발생했습니다.")
        print("📋 로그를 확인하여 문제를 해결해주세요.")
