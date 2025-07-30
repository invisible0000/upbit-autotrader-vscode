#!/usr/bin/env python3
"""
마이그레이션 결과 검증 스크립트
현재 DB와 백업 DB 비교
"""

import sqlite3
from pathlib import Path
import sys

# 프로젝트 루트 경로 추가  
project_root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(project_root))

try:
    from upbit_auto_trading.utils.global_db_manager import get_database_path
except ImportError:
    def get_database_path(db_name):
        return project_root / "upbit_auto_trading" / "data" / f"{db_name}.sqlite3"

def compare_table_structures(current_cursor, backup_cursor, table_name):
    """테이블 구조 비교"""
    try:
        # 현재 DB 테이블 구조
        current_cursor.execute(f"PRAGMA table_info({table_name})")
        current_structure = current_cursor.fetchall()
        
        # 백업 DB 테이블 구조 (존재하는 경우)
        backup_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        backup_exists = backup_cursor.fetchone()
        
        if backup_exists:
            backup_cursor.execute(f"PRAGMA table_info({table_name})")
            backup_structure = backup_cursor.fetchall()
            
            if current_structure == backup_structure:
                print(f"  ✅ {table_name}: 구조 동일")
            else:
                print(f"  📋 {table_name}: 구조 변경됨")
                print(f"    📊 현재: {len(current_structure)}개 컬럼")
                print(f"    📊 백업: {len(backup_structure)}개 컬럼")
        else:
            print(f"  🆕 {table_name}: 새로 생성된 테이블 ({len(current_structure)}개 컬럼)")
            
    except Exception as e:
        print(f"  ❌ {table_name}: 비교 실패 - {e}")

def compare_data_counts(current_cursor, backup_cursor, table_name):
    """데이터 개수 비교"""
    try:
        # 현재 DB 데이터 개수
        current_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        current_count = current_cursor.fetchone()[0]
        
        # 백업 DB 데이터 개수 (테이블이 존재하는 경우)
        backup_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        backup_exists = backup_cursor.fetchone()
        
        if backup_exists:
            backup_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            backup_count = backup_cursor.fetchone()[0]
            
            if current_count == backup_count:
                print(f"  ✅ {table_name}: {current_count}개 레코드 (변화 없음)")
            else:
                diff = current_count - backup_count
                print(f"  📈 {table_name}: {current_count}개 레코드 (+{diff})")
        else:
            print(f"  🆕 {table_name}: {current_count}개 레코드 (새 테이블)")
            
    except Exception as e:
        print(f"  ❌ {table_name}: 개수 비교 실패 - {e}")

def main():
    """메인 검증 함수"""
    print("🔍 마이그레이션 결과 검증")
    print("=" * 50)
    
    # DB 경로 설정
    current_db = get_database_path("settings")
    data_dir = current_db.parent
    
    # settings 백업 파일 찾기 (settings로 시작하는 파일만)
    backup_files = list(data_dir.glob("settings_migration_backup_*.sqlite3"))
    if not backup_files:
        # settings_bck로 시작하는 기존 백업 파일도 확인
        backup_files = list(data_dir.glob("settings_bck_*.sqlite3"))
        if not backup_files:
            print("❌ settings 백업 파일을 찾을 수 없습니다")
            print(f"📁 검색 경로: {data_dir}")
            print("🔍 찾는 패턴: settings_migration_backup_*.sqlite3 또는 settings_bck_*.sqlite3")
            return
    
    # 가장 최근 settings 백업 파일 선택
    backup_db = max(backup_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 현재 DB: {current_db.name}")
    print(f"📁 백업 DB: {backup_db.name}")
    
    try:
        with sqlite3.connect(current_db) as current_conn, \
             sqlite3.connect(backup_db) as backup_conn:
            
            current_cursor = current_conn.cursor()
            backup_cursor = backup_conn.cursor()
            
            # 현재 DB의 모든 테이블 목록
            current_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            current_tables = [row[0] for row in current_cursor.fetchall()]
            
            print(f"\n📊 총 테이블 수: {len(current_tables)}개")
            
            # 1. 테이블 구조 비교
            print("\n🏗️ 테이블 구조 비교")
            print("-" * 30)
            for table in current_tables:
                compare_table_structures(current_cursor, backup_cursor, table)
            
            # 2. 데이터 개수 비교  
            print("\n📈 데이터 개수 비교")
            print("-" * 30)
            for table in current_tables:
                compare_data_counts(current_cursor, backup_cursor, table)
                
            # 3. 확장 테이블 상세 검증
            print("\n🔍 확장 테이블 상세 검증")
            print("-" * 30)
            extension_tables = [
                'tv_help_texts',
                'tv_placeholder_texts', 
                'tv_indicator_categories',
                'tv_parameter_types',
                'tv_workflow_guides',
                'tv_indicator_library'
            ]
            
            for table in extension_tables:
                if table in current_tables:
                    current_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = current_cursor.fetchone()[0]
                    
                    if count > 0:
                        # 샘플 데이터 확인
                        current_cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                        samples = current_cursor.fetchall()
                        print(f"  ✅ {table}: {count}개 레코드")
                        if samples:
                            current_cursor.execute(f"PRAGMA table_info({table})")
                            columns = [col[1] for col in current_cursor.fetchall()]
                            print(f"    📋 컬럼: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                    else:
                        print(f"  ⚠️ {table}: 레코드 없음")
                else:
                    print(f"  ❌ {table}: 테이블 없음")
            
            print("\n✅ 검증 완료!")
            
    except Exception as e:
        print(f"❌ 검증 실패: {e}")

if __name__ == "__main__":
    main()
