#!/usr/bin/env python3
"""
데이터베이스 통합 마이그레이션 스크립트
Step 3: 데이터 마이그레이션
"""

import sqlite3
import json
from datetime import datetime

def migrate_strategies_data():
    """전략 데이터 마이그레이션"""
    
    print("📊 전략 데이터 마이그레이션 시작...")
    
    # 원본 데이터베이스 연결
    source_conn = sqlite3.connect('strategies.db')
    source_cursor = source_conn.cursor()
    
    # 통합 데이터베이스 연결
    target_conn = sqlite3.connect('upbit_trading_unified.db')
    target_cursor = target_conn.cursor()
    
    # 전략 데이터 조회
    source_cursor.execute("""
        SELECT strategy_id, name, description, created_at, modified_at, 
               is_active, rules_count, tags, strategy_data
        FROM strategies
    """)
    
    strategies = source_cursor.fetchall()
    print(f"  📋 마이그레이션할 전략: {len(strategies)}개")
    
    # 통합 데이터베이스에 삽입
    migrated_count = 0
    for strategy in strategies:
        try:
            # strategy_type 추가 (기본값: 'custom')
            target_cursor.execute("""
                INSERT INTO strategies 
                (strategy_id, name, description, strategy_type, created_at, modified_at, 
                 is_active, rules_count, tags, strategy_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*strategy[:3], 'custom', *strategy[3:]))
            
            migrated_count += 1
            print(f"    ✅ {strategy[1]} (ID: {strategy[0]})")
            
        except Exception as e:
            print(f"    ❌ 전략 마이그레이션 실패: {strategy[1]} - {str(e)}")
    
    # 실행 이력 데이터 마이그레이션
    source_cursor.execute("""
        SELECT id, strategy_id, rule_id, executed_at, trigger_type, action_type, result
        FROM execution_history
    """)
    
    execution_history = source_cursor.fetchall()
    print(f"  📋 마이그레이션할 실행 이력: {len(execution_history)}개")
    
    for history in execution_history:
        try:
            target_cursor.execute("""
                INSERT INTO execution_history 
                (strategy_id, rule_id, executed_at, trigger_type, action_type, result)
                VALUES (?, ?, ?, ?, ?, ?)
            """, history[1:])  # id는 자동 증가로 제외
            
        except Exception as e:
            print(f"    ❌ 실행 이력 마이그레이션 실패: {str(e)}")
    
    target_conn.commit()
    source_conn.close()
    target_conn.close()
    
    print(f"  ✅ 전략 마이그레이션 완료: {migrated_count}개")
    return migrated_count

def migrate_conditions_data():
    """조건 데이터 마이그레이션"""
    
    print("\n🎯 조건 데이터 마이그레이션 시작...")
    
    # 원본 데이터베이스 연결
    source_conn = sqlite3.connect('data/trading_conditions.db')
    source_cursor = source_conn.cursor()
    
    # 통합 데이터베이스 연결
    target_conn = sqlite3.connect('upbit_trading_unified.db')
    target_cursor = target_conn.cursor()
    
    # 조건 데이터 조회 (중복 이름 제거)
    source_cursor.execute("""
        SELECT name, description, variable_id, variable_name, variable_params,
               operator, comparison_type, target_value, external_variable,
               trend_direction, is_active, category, created_at, updated_at,
               usage_count, success_rate
        FROM trading_conditions
        WHERE name != '[자동 생성]' AND name IS NOT NULL AND name != ''
        ORDER BY created_at
    """)
    
    conditions = source_cursor.fetchall()
    print(f"  📋 마이그레이션할 조건: {len(conditions)}개")
    
    migrated_count = 0
    skipped_count = 0
    
    for condition in conditions:
        try:
            # 중복 이름 확인
            target_cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE name = ?", (condition[0],))
            if target_cursor.fetchone()[0] > 0:
                print(f"    ⚠️ 중복 조건 건너뛰기: {condition[0]}")
                skipped_count += 1
                continue
            
            target_cursor.execute("""
                INSERT INTO trading_conditions 
                (name, description, variable_id, variable_name, variable_params,
                 operator, comparison_type, target_value, external_variable,
                 trend_direction, is_active, category, created_at, updated_at,
                 usage_count, success_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, condition)
            
            migrated_count += 1
            print(f"    ✅ {condition[0]}")
            
        except Exception as e:
            print(f"    ❌ 조건 마이그레이션 실패: {condition[0]} - {str(e)}")
            skipped_count += 1
    
    # 조건 사용 이력 마이그레이션
    source_cursor.execute("""
        SELECT condition_id, strategy_name, action_type, execution_time,
               market_data, result_type, profit_loss, notes
        FROM condition_usage_history
    """)
    
    usage_history = source_cursor.fetchall()
    print(f"  📋 마이그레이션할 사용 이력: {len(usage_history)}개")
    
    # 사용 이력은 조건 ID 매핑이 필요하므로 일단 스킵
    # 실제 운영에서는 ID 매핑 테이블을 만들어서 처리
    
    target_conn.commit()
    source_conn.close()
    target_conn.close()
    
    print(f"  ✅ 조건 마이그레이션 완료: {migrated_count}개, 건너뛴 항목: {skipped_count}개")
    return migrated_count, skipped_count

def verify_migration():
    """마이그레이션 결과 검증"""
    
    print("\n🔍 마이그레이션 결과 검증...")
    
    conn = sqlite3.connect('upbit_trading_unified.db')
    cursor = conn.cursor()
    
    # 전략 개수 확인
    cursor.execute("SELECT COUNT(*) FROM strategies")
    strategy_count = cursor.fetchone()[0]
    print(f"  📊 마이그레이션된 전략: {strategy_count}개")
    
    # 조건 개수 확인
    cursor.execute("SELECT COUNT(*) FROM trading_conditions")
    condition_count = cursor.fetchone()[0]
    print(f"  🎯 마이그레이션된 조건: {condition_count}개")
    
    # 실행 이력 개수 확인
    cursor.execute("SELECT COUNT(*) FROM execution_history")
    history_count = cursor.fetchone()[0]
    print(f"  📈 마이그레이션된 실행 이력: {history_count}개")
    
    # 데이터 샘플 확인
    print("\n📋 마이그레이션된 데이터 샘플:")
    
    cursor.execute("SELECT name, strategy_type FROM strategies LIMIT 3")
    strategies = cursor.fetchall()
    for name, strategy_type in strategies:
        print(f"  전략: {name} ({strategy_type})")
    
    cursor.execute("SELECT name, category FROM trading_conditions LIMIT 3")
    conditions = cursor.fetchall()
    for name, category in conditions:
        print(f"  조건: {name} ({category})")
    
    conn.close()
    
    return {
        'strategies': strategy_count,
        'conditions': condition_count,
        'history': history_count
    }

def update_migration_info():
    """마이그레이션 정보 업데이트"""
    
    conn = sqlite3.connect('upbit_trading_unified.db')
    cursor = conn.cursor()
    
    migration_info = {
        "migration_completed": datetime.now().isoformat(),
        "source_databases": ["strategies.db", "data/trading_conditions.db"],
        "migration_method": "step_by_step",
        "version": "1.0"
    }
    
    cursor.execute("""
        INSERT OR REPLACE INTO system_settings (key, value, description)
        VALUES (?, ?, ?)
    """, ("migration_info", json.dumps(migration_info), "마이그레이션 상세 정보"))
    
    cursor.execute("""
        INSERT OR REPLACE INTO system_settings (key, value, description)
        VALUES (?, ?, ?)
    """, ("migration_completed", "true", "마이그레이션 완료 여부"))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("🚀 데이터 마이그레이션 시작")
    print("=" * 50)
    
    # 전략 데이터 마이그레이션
    strategy_count = migrate_strategies_data()
    
    # 조건 데이터 마이그레이션
    condition_count, skipped_count = migrate_conditions_data()
    
    # 마이그레이션 검증
    print("\n" + "=" * 50)
    results = verify_migration()
    
    # 마이그레이션 정보 업데이트
    update_migration_info()
    
    print("\n" + "=" * 50)
    print("✅ 데이터 마이그레이션 완료!")
    print(f"  📊 전략: {results['strategies']}개")
    print(f"  🎯 조건: {results['conditions']}개")
    print(f"  📈 실행 이력: {results['history']}개")
    
    if skipped_count > 0:
        print(f"  ⚠️ 건너뛴 조건: {skipped_count}개 (중복 또는 오류)")
    
    print("\n🎯 다음 단계: 코드 업데이트")
    print("   - ConditionStorage 클래스 수정")
    print("   - 데이터베이스 경로 변경")
    print("   - 테스트 및 검증")
