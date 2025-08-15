"""
데이터베이스 최적화 도구 - 시스템 테이블 정리 및 성능 향상
"""

import sqlite3
from pathlib import Path
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DatabaseOptimizer")


def optimize_settings_database():
    """settings 데이터베이스 최적화"""
    db_path = Path("data/settings.sqlite3")

    if not db_path.exists():
        logger.error(f"데이터베이스 파일이 없습니다: {db_path}")
        return

    logger.info("settings 데이터베이스 최적화 시작")

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()

        # 1. VACUUM으로 공간 회수
        logger.info("VACUUM 실행 중...")
        cursor.execute("VACUUM")

        # 2. ANALYZE로 통계 갱신
        logger.info("ANALYZE 실행 중...")
        cursor.execute("ANALYZE")

        # 3. 인덱스 최적화 확인
        cursor.execute("""
            SELECT name, sql FROM sqlite_master
            WHERE type = 'index' AND sql IS NOT NULL
        """)
        indexes = cursor.fetchall()

        logger.info(f"현재 인덱스 수: {len(indexes)}")
        for name, sql in indexes:
            logger.info(f"  - {name}")

        # 4. 중요한 인덱스들이 있는지 확인하고 없으면 생성
        important_indexes = [
            ("idx_tv_trading_variables_id",
             "CREATE INDEX IF NOT EXISTS idx_tv_trading_variables_id ON tv_trading_variables(variable_id)"),
            ("idx_tv_help_docs_variable",
             "CREATE INDEX IF NOT EXISTS idx_tv_help_docs_variable ON tv_variable_help_documents(variable_id, help_category)"),
            ("idx_tv_parameters_variable",
             "CREATE INDEX IF NOT EXISTS idx_tv_parameters_variable ON tv_variable_parameters(variable_id, parameter_name)"),
            ("idx_tv_help_texts_lookup",
             "CREATE INDEX IF NOT EXISTS idx_tv_help_texts_lookup ON tv_help_texts(variable_id, parameter_name)"),
            ("idx_tv_placeholder_lookup",
             "CREATE INDEX IF NOT EXISTS idx_tv_placeholder_lookup ON tv_placeholder_texts(variable_id, parameter_name)")
        ]

        for index_name, create_sql in important_indexes:
            try:
                cursor.execute(create_sql)
                logger.info(f"인덱스 생성/확인: {index_name}")
            except sqlite3.Error as e:
                logger.warning(f"인덱스 생성 실패 {index_name}: {e}")

        # 5. 데이터 무결성 검사
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]

        if integrity_result == "ok":
            logger.info("✅ 데이터 무결성 검사 통과")
        else:
            logger.error(f"❌ 데이터 무결성 문제: {integrity_result}")

        # 6. 통계 정보 표시
        cursor.execute("SELECT COUNT(*) FROM tv_trading_variables")
        vars_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tv_variable_help_documents")
        help_docs_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters")
        params_count = cursor.fetchone()[0]

        logger.info(f"📊 최적화 완료 통계:")
        logger.info(f"  - 거래 변수: {vars_count}개")
        logger.info(f"  - 도움말 문서: {help_docs_count}개")
        logger.info(f"  - 변수 파라미터: {params_count}개")

        conn.commit()

def check_database_sizes():
    """데이터베이스 파일 크기 확인"""
    db_files = [
        "data/settings.sqlite3",
        "data/strategies.sqlite3",
        "data/market_data.sqlite3"
    ]

    logger.info("📁 데이터베이스 파일 크기:")
    total_size = 0

    for db_file in db_files:
        path = Path(db_file)
        if path.exists():
            size = path.stat().st_size
            size_mb = size / (1024 * 1024)
            logger.info(f"  - {db_file}: {size_mb:.2f} MB")
            total_size += size
        else:
            logger.info(f"  - {db_file}: 파일 없음")

    total_mb = total_size / (1024 * 1024)
    logger.info(f"🔢 전체 DB 크기: {total_mb:.2f} MB")

def create_backup():
    """중요 데이터베이스 백업"""
    backup_dir = Path("data/backups")
    backup_dir.mkdir(exist_ok=True)

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    settings_path = Path("data/settings.sqlite3")
    if settings_path.exists():
        backup_path = backup_dir / f"settings_backup_{timestamp}.sqlite3"

        import shutil
        shutil.copy2(settings_path, backup_path)
        logger.info(f"✅ 백업 생성: {backup_path}")
        return backup_path

    return None

def main():
    """메인 실행"""
    logger.info("🚀 데이터베이스 최적화 시작")

    # 1. 백업 생성
    backup_path = create_backup()
    if backup_path:
        logger.info(f"📦 백업 완료: {backup_path}")

    # 2. 파일 크기 확인 (최적화 전)
    logger.info("📊 최적화 전 상태:")
    check_database_sizes()

    # 3. 최적화 실행
    optimize_settings_database()

    # 4. 파일 크기 확인 (최적화 후)
    logger.info("📊 최적화 후 상태:")
    check_database_sizes()

    logger.info("✅ 데이터베이스 최적화 완료")

if __name__ == "__main__":
    main()
