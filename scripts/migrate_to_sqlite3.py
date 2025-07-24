#!/usr/bin/env python3
"""
DB 파일 확장자 및 구조 정리 마이그레이션
- 확장자를 .sqlite3으로 통일
- 2개 DB로 통합: app_settings.sqlite3, market_data.sqlite3
"""

import os
import sqlite3
import shutil
from datetime import datetime


def create_app_settings_db():
    """프로그램 설정용 DB 생성"""
    db_path = "data/app_settings.sqlite3"
    
    print(f"📊 {db_path} 생성 중...")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. trading_conditions 테이블 (기존)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                condition_type TEXT NOT NULL,
                parameters TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                category TEXT DEFAULT 'manual',
                description TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0
            );
        """)
        
        # 2. component_strategy 테이블 (기존)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS component_strategy (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                triggers TEXT NOT NULL,
                conditions TEXT,
                actions TEXT NOT NULL,
                tags TEXT,
                category TEXT DEFAULT 'user_created',
                difficulty TEXT DEFAULT 'intermediate',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                is_template BOOLEAN NOT NULL DEFAULT 0,
                performance_metrics TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 3. strategy_components 테이블 (기존)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_components (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                component_type TEXT NOT NULL,
                component_data TEXT NOT NULL,
                order_index INTEGER NOT NULL DEFAULT 0,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
            );
        """)
        
        # 4. strategy_execution 테이블 (기존)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_execution (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                action_type TEXT NOT NULL,
                market_data TEXT,
                result TEXT NOT NULL,
                result_details TEXT,
                position_tag TEXT,
                executed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
            );
        """)
        
        # 5. system_settings 테이블 (새로 추가)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string',
                description TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 6. user_preferences 테이블 (새로 추가)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT NOT NULL,
                user_id TEXT DEFAULT 'default',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print(f"✅ {db_path} 스키마 생성 완료")


def migrate_data_from_unified_db():
    """기존 통합 DB에서 데이터 마이그레이션"""
    source_db = "data/upbit_trading_unified.db"
    target_db = "data/app_settings.sqlite3"
    
    if not os.path.exists(source_db):
        print(f"⚠️ 소스 DB 없음: {source_db}")
        return
    
    print(f"🔄 데이터 마이그레이션: {source_db} → {target_db}")
    
    # 소스에서 데이터 읽기
    source_conn = sqlite3.connect(source_db)
    target_conn = sqlite3.connect(target_db)
    
    try:
        # trading_conditions 마이그레이션
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # 1. trading_conditions 테이블 확인 및 복사
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trading_conditions'")
        if source_cursor.fetchone():
            source_cursor.execute("SELECT * FROM trading_conditions")
            rows = source_cursor.fetchall()
            
            # 컬럼 정보 가져오기
            source_cursor.execute("PRAGMA table_info(trading_conditions)")
            columns = [col[1] for col in source_cursor.fetchall()]
            
            if rows:
                placeholders = ','.join(['?' for _ in columns])
                target_cursor.execute(f"DELETE FROM trading_conditions")  # 기존 데이터 삭제
                target_cursor.executemany(
                    f"INSERT INTO trading_conditions ({','.join(columns)}) VALUES ({placeholders})", 
                    rows
                )
                print(f"✅ trading_conditions 마이그레이션 완료: {len(rows)}건")
        
        # 2. component_strategy 마이그레이션
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='component_strategy'")
        if source_cursor.fetchone():
            source_cursor.execute("SELECT * FROM component_strategy")
            rows = source_cursor.fetchall()
            
            if rows:
                # 컬럼 정보 가져오기
                source_cursor.execute("PRAGMA table_info(component_strategy)")
                columns = [col[1] for col in source_cursor.fetchall()]
                
                placeholders = ','.join(['?' for _ in columns])
                target_cursor.execute(f"DELETE FROM component_strategy")
                target_cursor.executemany(
                    f"INSERT INTO component_strategy ({','.join(columns)}) VALUES ({placeholders})", 
                    rows
                )
                print(f"✅ component_strategy 마이그레이션 완료: {len(rows)}건")
        
        # 3. strategy_components 마이그레이션
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_components'")
        if source_cursor.fetchone():
            source_cursor.execute("SELECT * FROM strategy_components")
            rows = source_cursor.fetchall()
            
            if rows:
                source_cursor.execute("PRAGMA table_info(strategy_components)")
                columns = [col[1] for col in source_cursor.fetchall()]
                
                placeholders = ','.join(['?' for _ in columns])
                target_cursor.execute(f"DELETE FROM strategy_components")
                target_cursor.executemany(
                    f"INSERT INTO strategy_components ({','.join(columns)}) VALUES ({placeholders})", 
                    rows
                )
                print(f"✅ strategy_components 마이그레이션 완료: {len(rows)}건")
        
        # 4. strategy_execution 마이그레이션
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_execution'")
        if source_cursor.fetchone():
            source_cursor.execute("SELECT * FROM strategy_execution")
            rows = source_cursor.fetchall()
            
            if rows:
                source_cursor.execute("PRAGMA table_info(strategy_execution)")
                columns = [col[1] for col in source_cursor.fetchall()]
                
                placeholders = ','.join(['?' for _ in columns])
                target_cursor.execute(f"DELETE FROM strategy_execution")
                target_cursor.executemany(
                    f"INSERT INTO strategy_execution ({','.join(columns)}) VALUES ({placeholders})", 
                    rows
                )
                print(f"✅ strategy_execution 마이그레이션 완료: {len(rows)}건")
        
        target_conn.commit()
        
    except Exception as e:
        print(f"❌ 마이그레이션 오류: {e}")
        target_conn.rollback()
    finally:
        source_conn.close()
        target_conn.close()


def rename_market_data_db():
    """시장 데이터 DB 이름 변경"""
    old_path = "data/upbit_auto_trading.sqlite3"
    new_path = "data/market_data.sqlite3"
    
    if os.path.exists(old_path):
        if os.path.exists(new_path):
            # 백업 생성
            backup_path = f"data/market_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
            shutil.move(new_path, backup_path)
            print(f"📦 기존 파일 백업: {backup_path}")
        
        shutil.move(old_path, new_path)
        print(f"✅ 시장 데이터 DB 이름 변경: {old_path} → {new_path}")
    else:
        print(f"⚠️ 시장 데이터 DB 파일 없음: {old_path}")


def cleanup_old_db_files():
    """기존 .db 파일들 정리"""
    old_files = [
        "data/strategies.db",
        "data/trading_conditions.db", 
        "data/upbit_auto_trading.db",
        "data/upbit_trading_unified_backup.db"
    ]
    
    # 백업 폴더 생성
    backup_dir = f"data/old_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for old_file in old_files:
        if os.path.exists(old_file):
            backup_file = os.path.join(backup_dir, os.path.basename(old_file))
            shutil.move(old_file, backup_file)
            print(f"📦 백업 이동: {old_file} → {backup_file}")
    
    print(f"✅ 기존 DB 파일들 백업 완료: {backup_dir}")


def update_code_references():
    """코드에서 DB 경로 참조 업데이트 가이드"""
    print("\n🔧 코드 업데이트 가이드:")
    print("=" * 60)
    print("다음 파일들의 DB 경로를 수정해야 합니다:")
    print("")
    print("1. strategy_storage.py:")
    print('   - "data/upbit_trading_unified.db" → "data/app_settings.sqlite3"')
    print("")
    print("2. condition_storage.py:")
    print('   - "data/upbit_trading_unified.db" → "data/app_settings.sqlite3"')
    print("")
    print("3. enhanced_real_data_simulation_engine.py:")
    print('   - unified_db_path → "data/app_settings.sqlite3"')
    print('   - data_db_path → "data/market_data.sqlite3"')
    print("")
    print("4. database_backtest_engine.py:")
    print('   - db_path → "data/market_data.sqlite3"')


def main():
    """메인 마이그레이션 실행"""
    print("🚀 DB 구조 정리 마이그레이션 시작")
    print("=" * 60)
    
    # 1. 새 app_settings.sqlite3 생성
    create_app_settings_db()
    
    # 2. 기존 통합 DB에서 데이터 마이그레이션
    migrate_data_from_unified_db()
    
    # 3. 시장 데이터 DB 이름 변경
    rename_market_data_db()
    
    # 4. 기존 .db 파일들 백업 정리
    cleanup_old_db_files()
    
    # 5. 코드 업데이트 가이드
    update_code_references()
    
    print("\n✅ DB 구조 정리 마이그레이션 완료!")
    print("📊 최종 DB 구조:")
    print("   - data/app_settings.sqlite3 (프로그램 설정)")
    print("   - data/market_data.sqlite3 (백테스팅 데이터)")


if __name__ == "__main__":
    main()
