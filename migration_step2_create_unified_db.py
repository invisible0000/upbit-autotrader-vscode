#!/usr/bin/env python3
"""
데이터베이스 통합 마이그레이션 스크립트
Step 2: 통합 데이터베이스 생성
"""

import sqlite3
import os
import json
from datetime import datetime

def create_unified_database():
    """통합 데이터베이스 생성"""
    
    unified_db_path = "upbit_trading_unified.db"
    
    # 기존 파일이 있으면 백업
    if os.path.exists(unified_db_path):
        backup_name = f"{unified_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(unified_db_path, backup_name)
        print(f"⚠️ 기존 파일 백업: {backup_name}")
    
    print(f"🗃️ 통합 데이터베이스 생성: {unified_db_path}")
    
    conn = sqlite3.connect(unified_db_path)
    cursor = conn.cursor()
    
    # 1. 전략 테이블 (기존 strategies 테이블 확장)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            strategy_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            strategy_type TEXT DEFAULT 'custom',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            rules_count INTEGER DEFAULT 0,
            tags TEXT, -- JSON array
            strategy_data TEXT, -- JSON
            backtest_results TEXT, -- JSON
            performance_metrics TEXT -- JSON
        )
    """)
    print("✅ strategies 테이블 생성")
    
    # 2. 조건/트리거 테이블 (기존 trading_conditions 개선)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            variable_id TEXT NOT NULL,
            variable_name TEXT NOT NULL,
            variable_params TEXT, -- JSON
            operator TEXT NOT NULL,
            comparison_type TEXT DEFAULT 'fixed',
            target_value TEXT,
            external_variable TEXT, -- JSON
            trend_direction TEXT DEFAULT 'static',
            is_active INTEGER DEFAULT 1,
            category TEXT DEFAULT 'custom',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            UNIQUE(name) -- 중복 이름 방지
        )
    """)
    print("✅ trading_conditions 테이블 생성")
    
    # 3. 전략-조건 연결 테이블 (새로 추가)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            condition_id INTEGER NOT NULL,
            condition_order INTEGER DEFAULT 0,
            condition_logic TEXT DEFAULT 'AND', -- AND, OR, NOT
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id),
            FOREIGN KEY (condition_id) REFERENCES trading_conditions (id)
        )
    """)
    print("✅ strategy_conditions 테이블 생성")
    
    # 4. 실행 이력 테이블 (통합 및 확장)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS execution_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT,
            condition_id INTEGER,
            rule_id TEXT,
            executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            trigger_type TEXT,
            action_type TEXT,
            market_data TEXT, -- JSON
            result TEXT,
            profit_loss REAL,
            notes TEXT,
            FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id),
            FOREIGN KEY (condition_id) REFERENCES trading_conditions (id)
        )
    """)
    print("✅ execution_history 테이블 생성")
    
    # 5. 시스템 설정 테이블 (새로 추가)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✅ system_settings 테이블 생성")
    
    # 6. 백업 정보 테이블 (새로 추가)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backup_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_name TEXT NOT NULL,
            backup_path TEXT NOT NULL,
            backup_size INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """)
    print("✅ backup_info 테이블 생성")
    
    # 인덱스 생성
    indexes = [
        ("idx_strategies_active", "CREATE INDEX IF NOT EXISTS idx_strategies_active ON strategies (is_active)"),
        ("idx_conditions_active", "CREATE INDEX IF NOT EXISTS idx_conditions_active ON trading_conditions (is_active)"),
        ("idx_conditions_category", "CREATE INDEX IF NOT EXISTS idx_conditions_category ON trading_conditions (category)"),
        ("idx_strategy_conditions_strategy", "CREATE INDEX IF NOT EXISTS idx_strategy_conditions_strategy ON strategy_conditions (strategy_id)"),
        ("idx_execution_history_strategy", "CREATE INDEX IF NOT EXISTS idx_execution_history_strategy ON execution_history (strategy_id)"),
        ("idx_execution_history_date", "CREATE INDEX IF NOT EXISTS idx_execution_history_date ON execution_history (executed_at)")
    ]
    
    print("\n📊 인덱스 생성...")
    for idx_name, idx_sql in indexes:
        cursor.execute(idx_sql)
        print(f"  ✅ {idx_name}")
    
    # 기본 시스템 설정 추가
    default_settings = [
        ("db_version", "1.0", "데이터베이스 스키마 버전"),
        ("migration_date", datetime.now().isoformat(), "통합 마이그레이션 날짜"),
        ("unified_db", "true", "통합 데이터베이스 사용 여부")
    ]
    
    print("\n⚙️ 기본 설정 추가...")
    for key, value, description in default_settings:
        cursor.execute(
            "INSERT OR REPLACE INTO system_settings (key, value, description) VALUES (?, ?, ?)",
            (key, value, description)
        )
        print(f"  ✅ {key}: {value}")
    
    conn.commit()
    conn.close()
    
    return unified_db_path

def verify_unified_database(db_path):
    """통합 데이터베이스 구조 검증"""
    
    print(f"\n🔍 통합 데이터베이스 검증: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 테이블 목록 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'strategies', 'trading_conditions', 'strategy_conditions',
        'execution_history', 'system_settings', 'backup_info'
    ]
    
    print(f"📋 생성된 테이블: {len(tables)}개")
    for table in tables:
        if table in expected_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ⚠️ {table} (예상하지 못한 테이블)")
    
    # 누락된 테이블 확인
    missing_tables = set(expected_tables) - set(tables)
    if missing_tables:
        print(f"❌ 누락된 테이블: {missing_tables}")
        return False
    
    # 인덱스 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"📊 생성된 인덱스: {len(indexes)}개")
    
    # 시스템 설정 확인
    cursor.execute("SELECT key, value FROM system_settings")
    settings = cursor.fetchall()
    print(f"⚙️ 시스템 설정: {len(settings)}개")
    for key, value in settings:
        print(f"  {key}: {value}")
    
    conn.close()
    return True

if __name__ == "__main__":
    print("🚀 통합 데이터베이스 생성 시작")
    print("=" * 50)
    
    unified_db_path = create_unified_database()
    
    print("\n" + "=" * 50)
    verified = verify_unified_database(unified_db_path)
    
    if verified:
        print("✅ 통합 데이터베이스가 성공적으로 생성되었습니다!")
        print(f"📂 데이터베이스 위치: {unified_db_path}")
    else:
        print("❌ 통합 데이터베이스 생성에 실패했습니다.")
        exit(1)
    
    print("\n🎯 다음 단계: 데이터 마이그레이션")
    print("   python migration_step3_migrate_data.py")
