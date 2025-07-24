#!/usr/bin/env python3
"""
데이터베이스 통합 계획 및 마이그레이션 스크립트
"""

import sqlite3
import json
import os
from datetime import datetime

def analyze_current_databases():
    """현재 데이터베이스 구조 분석"""
    
    databases = {
        'strategies.db': [],
        'data/trading_conditions.db': [],
        'data/upbit_auto_trading.db': []
    }
    
    print("=== 현재 데이터베이스 구조 분석 ===")
    
    for db_path, tables in databases.items():
        if os.path.exists(db_path):
            print(f"\n📂 {db_path}:")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 테이블 목록 조회
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            table_list = cursor.fetchall()
            
            for table in table_list:
                table_name = table[0]
                if table_name != 'sqlite_sequence':
                    # 테이블 구조 확인
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    # 데이터 개수 확인
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    
                    print(f"  📋 {table_name} ({count} rows)")
                    for col in columns:
                        print(f"    - {col[1]} ({col[2]})")
                    
                    tables.append({
                        'name': table_name,
                        'columns': columns,
                        'count': count
                    })
            
            conn.close()
        else:
            print(f"❌ {db_path}: 파일 없음")
    
    return databases

def propose_unified_schema():
    """통합 데이터베이스 스키마 제안"""
    
    unified_schema = """
    -- 통합 데이터베이스 스키마 (upbit_trading.db)
    
    -- 1. 전략 테이블 (기존 strategies 테이블 확장)
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
    );
    
    -- 2. 조건/트리거 테이블 (기존 trading_conditions 개선)
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
    );
    
    -- 3. 전략-조건 연결 테이블 (새로 추가)
    CREATE TABLE IF NOT EXISTS strategy_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_id TEXT NOT NULL,
        condition_id INTEGER NOT NULL,
        condition_order INTEGER DEFAULT 0,
        condition_logic TEXT DEFAULT 'AND', -- AND, OR, NOT
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id),
        FOREIGN KEY (condition_id) REFERENCES trading_conditions (id)
    );
    
    -- 4. 실행 이력 테이블 (통합 및 확장)
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
    );
    
    -- 5. 시스템 설정 테이블 (새로 추가)
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    
    -- 6. 백업 정보 테이블 (새로 추가)
    CREATE TABLE IF NOT EXISTS backup_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_name TEXT NOT NULL,
        backup_path TEXT NOT NULL,
        backup_size INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        description TEXT
    );
    """
    
    return unified_schema

def create_migration_plan():
    """마이그레이션 계획 수립"""
    
    migration_steps = [
        {
            "step": 1,
            "title": "백업 생성",
            "description": "현재 모든 데이터베이스 백업",
            "risk": "낮음"
        },
        {
            "step": 2,
            "title": "통합 데이터베이스 생성",
            "description": "새로운 upbit_trading.db 파일에 통합 스키마 생성",
            "risk": "낮음"
        },
        {
            "step": 3,
            "title": "전략 데이터 마이그레이션",
            "description": "strategies.db에서 데이터 복사",
            "risk": "중간"
        },
        {
            "step": 4,
            "title": "조건 데이터 마이그레이션",
            "description": "trading_conditions.db에서 데이터 복사 (중복 제거)",
            "risk": "중간"
        },
        {
            "step": 5,
            "title": "코드 업데이트",
            "description": "모든 DB 접근 코드를 통합 DB로 변경",
            "risk": "높음"
        },
        {
            "step": 6,
            "title": "테스트 및 검증",
            "description": "기능 테스트 및 데이터 무결성 확인",
            "risk": "중간"
        }
    ]
    
    return migration_steps

def estimate_migration_effort():
    """마이그레이션 작업량 예상"""
    
    affected_files = [
        "components/condition_storage.py",
        "components/strategy_storage.py", 
        "integrated_condition_manager.py",
        "upbit_auto_trading/ui/desktop/screens/strategy_management/*",
        "upbit_auto_trading/data_layer/storage/*",
        "database_backtest_engine.py",
        "trading_manager.py"
    ]
    
    return {
        "estimated_hours": 8-12,
        "complexity": "중간",
        "affected_files": len(affected_files),
        "risk_factors": [
            "기존 데이터 손실 위험",
            "참조 무결성 오류 가능성",
            "UI 코드 대량 수정 필요"
        ],
        "benefits": [
            "데이터 일관성 향상",
            "백업/복원 단순화",
            "성능 향상 (조인 쿼리)",
            "유지보수성 향상"
        ]
    }

if __name__ == "__main__":
    print("🔍 데이터베이스 통합 분석 시작")
    print("=" * 60)
    
    # 1. 현재 상태 분석
    databases = analyze_current_databases()
    
    # 2. 통합 스키마 제안
    print("\n\n=== 통합 데이터베이스 스키마 제안 ===")
    schema = propose_unified_schema()
    print(schema)
    
    # 3. 마이그레이션 계획
    print("\n=== 마이그레이션 계획 ===")
    steps = create_migration_plan()
    for step in steps:
        print(f"Step {step['step']}: {step['title']}")
        print(f"  설명: {step['description']}")
        print(f"  위험도: {step['risk']}")
        print()
    
    # 4. 작업량 예상
    print("=== 작업량 예상 ===")
    effort = estimate_migration_effort()
    print(f"예상 작업 시간: {effort['estimated_hours']}시간")
    print(f"복잡도: {effort['complexity']}")
    print(f"영향받는 파일 수: {effort['affected_files']}개")
    
    print("\n위험 요소:")
    for risk in effort['risk_factors']:
        print(f"  ⚠️ {risk}")
    
    print("\n기대 효과:")
    for benefit in effort['benefits']:
        print(f"  ✅ {benefit}")
    
    print("\n" + "=" * 60)
    print("💡 권장사항: 단계적 마이그레이션 진행")
    print("   1. 먼저 백업 생성")
    print("   2. 테스트 환경에서 마이그레이션 검증")
    print("   3. 운영 환경 적용")
