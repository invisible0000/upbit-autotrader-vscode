#!/usr/bin/env python3
"""
프로젝트 내 데이터베이스 파일 구조 분석 및 마이그레이션 스크립트
"""

import sqlite3
import os
from pathlib import Path
import json

def analyze_database_structure(db_path):
    """데이터베이스 구조 분석"""
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        return {"error": "파일이 없거나 비어있음", "size": 0}
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        structure = {
            "file_size": os.path.getsize(db_path),
            "tables": {}
        }
        
        # 각 테이블의 구조 분석
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            row_count = cursor.fetchone()[0]
            
            structure["tables"][table] = {
                "columns": [{"name": col[1], "type": col[2], "nullable": not col[3], "primary_key": bool(col[5])} for col in columns],
                "row_count": row_count
            }
        
        conn.close()
        return structure
        
    except Exception as e:
        return {"error": str(e)}

def find_all_databases():
    """프로젝트 내 모든 데이터베이스 파일 찾기"""
    base_dir = Path(".")
    db_files = []
    
    # .db 파일들
    for db_file in base_dir.rglob("*.db"):
        if db_file.is_file():
            db_files.append(str(db_file))
    
    # .sqlite3 파일들
    for db_file in base_dir.rglob("*.sqlite3"):
        if db_file.is_file():
            db_files.append(str(db_file))
    
    return db_files

def analyze_all_databases():
    """모든 데이터베이스 분석"""
    print("🔍 프로젝트 내 데이터베이스 파일 분석")
    print("=" * 70)
    
    db_files = find_all_databases()
    
    if not db_files:
        print("❌ 데이터베이스 파일을 찾을 수 없습니다.")
        return {}
    
    results = {}
    
    for db_path in db_files:
        print(f"\n📁 {db_path}")
        structure = analyze_database_structure(db_path)
        results[db_path] = structure
        
        if "error" in structure:
            print(f"   ❌ 오류: {structure['error']} (크기: {structure.get('size', 0)} bytes)")
        else:
            print(f"   📊 크기: {structure['file_size']} bytes")
            print(f"   📋 테이블 수: {len(structure['tables'])}")
            
            for table_name, table_info in structure['tables'].items():
                print(f"      • {table_name}: {table_info['row_count']}개 행, {len(table_info['columns'])}개 열")
    
    return results

def check_trading_conditions_table():
    """trading_conditions 테이블이 있는 DB 찾기"""
    print(f"\n🔍 'trading_conditions' 테이블 검색")
    print("=" * 70)
    
    db_files = find_all_databases()
    found_dbs = []
    
    for db_path in db_files:
        structure = analyze_database_structure(db_path)
        if "tables" in structure and "trading_conditions" in structure["tables"]:
            found_dbs.append(db_path)
            table_info = structure["tables"]["trading_conditions"]
            print(f"✅ {db_path}")
            print(f"   📊 행 수: {table_info['row_count']}")
            print(f"   📋 열 구조:")
            for col in table_info['columns']:
                pk_mark = " (PK)" if col['primary_key'] else ""
                null_mark = " (NULL)" if col['nullable'] else " (NOT NULL)"
                print(f"      • {col['name']}: {col['type']}{pk_mark}{null_mark}")
    
    if not found_dbs:
        print("❌ trading_conditions 테이블을 가진 데이터베이스를 찾을 수 없습니다.")
    
    return found_dbs

def suggest_migration_strategy():
    """마이그레이션 전략 제안"""
    print(f"\n🎯 마이그레이션 전략 분석")
    print("=" * 70)
    
    # 통합 DB 확인
    unified_db_path = "data/app_settings.sqlite3"
    if os.path.exists(unified_db_path):
        unified_structure = analyze_database_structure(unified_db_path)
        print(f"📁 통합 DB 발견: {unified_db_path}")
        
        if "error" in unified_structure:
            print(f"   ❌ 통합 DB 문제: {unified_structure['error']}")
        else:
            print(f"   📊 크기: {unified_structure['file_size']} bytes")
            print(f"   📋 테이블: {list(unified_structure['tables'].keys())}")
    
    # data 폴더 DB들 확인
    data_dir = Path("data")
    if data_dir.exists():
        print(f"\n📁 data/ 폴더 DB들:")
        for db_file in data_dir.glob("*.db"):
            structure = analyze_database_structure(str(db_file))
            if "tables" in structure:
                print(f"   • {db_file.name}: {list(structure['tables'].keys())}")
    
    # 제안
    print(f"\n💡 권장 마이그레이션 방법:")
    
    # trading_conditions 테이블 찾기
    trading_conditions_dbs = check_trading_conditions_table()
    
    if trading_conditions_dbs:
        best_db = max(trading_conditions_dbs, 
                     key=lambda x: analyze_database_structure(x)['tables']['trading_conditions']['row_count'])
        print(f"   1. 기존 데이터 사용: {best_db}")
        print(f"      → 이 DB를 통합 DB로 복사하거나 연결")
    else:
        print(f"   1. 새로운 테이블 생성 필요")
        print(f"      → migration_wizard.py 또는 스키마 초기화 실행")
    
    print(f"   2. 통합 DB 경로 확인")
    print(f"      → data/upbit_trading_unified.db가 올바른 위치에 있는지 확인")

def create_migration_script():
    """간단한 마이그레이션 스크립트 생성"""
    print(f"\n🔧 마이그레이션 스크립트 생성")
    print("=" * 70)
    
    # trading_conditions 테이블이 있는 DB 찾기
    trading_conditions_dbs = []
    for db_path in find_all_databases():
        structure = analyze_database_structure(db_path)
        if "tables" in structure and "trading_conditions" in structure["tables"]:
            trading_conditions_dbs.append(db_path)
    
    if trading_conditions_dbs:
        # 데이터가 가장 많은 DB 선택
        best_db = max(trading_conditions_dbs, 
                     key=lambda x: analyze_database_structure(x)['tables']['trading_conditions']['row_count'])
        
        print(f"🎯 최적 DB 발견: {best_db}")
        
        migration_script = f'''
# 간단한 데이터 마이그레이션
import sqlite3
import shutil

def migrate_trading_conditions():
    """trading_conditions 데이터 마이그레이션"""
    source_db = "{best_db}"
    target_db = "data/upbit_trading_unified.db"
    
    print(f"{{source_db}} → {{target_db}} 마이그레이션 시작...")
    
    # 소스 DB에서 데이터 읽기
    source_conn = sqlite3.connect(source_db)
    source_cursor = source_conn.cursor()
    
    # 타겟 DB 연결
    target_conn = sqlite3.connect(target_db)
    target_cursor = target_conn.cursor()
    
    try:
        # trading_conditions 테이블 생성 (이미 있으면 무시)
        source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trading_conditions';")
        create_sql = source_cursor.fetchone()
        
        if create_sql:
            target_cursor.execute(create_sql[0])
            print("✅ trading_conditions 테이블 생성 완료")
        
        # 데이터 복사
        source_cursor.execute("SELECT * FROM trading_conditions;")
        rows = source_cursor.fetchall()
        
        if rows:
            # 열 정보 가져오기
            source_cursor.execute("PRAGMA table_info(trading_conditions);")
            columns = [col[1] for col in source_cursor.fetchall()]
            
            placeholders = "?" + ",?" * (len(columns) - 1)
            insert_sql = f"INSERT OR REPLACE INTO trading_conditions VALUES ({{placeholders}})"
            
            target_cursor.executemany(insert_sql, rows)
            target_conn.commit()
            
            print(f"✅ {{len(rows)}}개 데이터 마이그레이션 완료")
        else:
            print("⚠️ 복사할 데이터가 없습니다")
    
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {{e}}")
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    migrate_trading_conditions()
        '''
        
        # 마이그레이션 스크립트 파일로 저장
        with open("scripts/migrate_trading_conditions.py", "w", encoding="utf-8") as f:
            f.write(migration_script)
        
        print(f"✅ 마이그레이션 스크립트 생성: scripts/migrate_trading_conditions.py")
        return True
    else:
        print(f"❌ trading_conditions 테이블을 찾을 수 없어 마이그레이션 스크립트를 생성할 수 없습니다.")
        return False

def main():
    print("🔍 데이터베이스 구조 분석 및 마이그레이션 도구")
    print("=" * 70)
    
    # 1. 모든 DB 분석
    db_analysis = analyze_all_databases()
    
    # 2. trading_conditions 테이블 검색
    trading_conditions_dbs = check_trading_conditions_table()
    
    # 3. 마이그레이션 전략 제안
    suggest_migration_strategy()
    
    # 4. 마이그레이션 스크립트 생성
    script_created = create_migration_script()
    
    print(f"\n{'='*70}")
    print("📊 분석 요약:")
    print(f"   • 총 DB 파일: {len(db_analysis)}개")
    print(f"   • trading_conditions 보유 DB: {len(trading_conditions_dbs)}개")
    print(f"   • 마이그레이션 스크립트: {'생성됨' if script_created else '생성 실패'}")

if __name__ == "__main__":
    main()
