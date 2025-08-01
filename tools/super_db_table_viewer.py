#!/usr/bin/env python3
"""
🔍 Super DB Table Viewer
데이터베이스 테이블 및 스키마 분석 도구

🤖 LLM 사용 가이드:
===================
이 도구는 DB 상태를 빠르게 파악하기 위한 종합 분석 도구입니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_db_table_viewer.py              # 전체 DB 요약 (가장 많이 사용)
2. python super_db_table_viewer.py settings     # settings DB 상세 분석  
3. python super_db_table_viewer.py compare      # DB vs 스키마 비교
4. python super_db_table_viewer.py table 테이블명  # 특정 테이블 구조 조회

🎯 언제 사용하면 좋은가:
- DB 테이블 개수나 목록이 궁금할 때
- 변수 관련 테이블(tv_*) 상태 확인할 때  
- 스키마 파일과 실제 DB 차이점 분석할 때
- 특정 테이블 구조나 샘플 데이터 확인할 때
- 마이그레이션 전후 DB 상태 비교할 때

💡 출력 해석:
- 📋 총 테이블 수: DB 전체 테이블 개수
- 🎯 변수 관련 테이블: tv_*, *variable* 패턴 테이블들
- ✅ 공통 테이블: DB와 스키마 모두에 있는 테이블
- 🔵 DB에만 있는: 스키마에는 없고 DB에만 있는 테이블
- 🟡 스키마에만 있는: DB에는 없고 스키마에만 있는 테이블

기능:
1. DB 테이블 목록 및 상세 정보 조회
2. 스키마 파일과 DB 비교 분석  
3. 변수 관련 테이블 상태 확인
4. 레코드 수 및 샘플 데이터 조회
5. 테이블 구조 및 인덱스 정보

작성일: 2025-07-31
작성자: Upbit Auto Trading Team
"""

import sqlite3
import os
import re
from typing import List, Dict, Optional, Tuple


class SuperDBTableViewer:
    """
    🔍 종합 DB 테이블 분석 도구
    
    🤖 LLM 사용 패턴:
    viewer = SuperDBTableViewer()
    viewer.check_all_databases()        # 📊 전체 DB 요약 - 가장 많이 사용
    viewer.check_database('settings')   # 🔍 특정 DB 상세 분석
    viewer.compare_with_schema()        # ⚖️ DB vs 스키마 비교
    viewer.show_table_structure('tv_trading_variables')  # 🏗️ 테이블 구조 조회
    
    💡 지원 DB: settings, market_data, strategies
    💡 지원 스키마: gui_unified (GUI 마이그레이션 도구용)
    """
    
    def __init__(self):
        self.db_paths = {
            'settings': 'upbit_auto_trading/data/settings.sqlite3',
            'market_data': 'upbit_auto_trading/data/market_data.sqlite3',
            'strategies': 'upbit_auto_trading/data/strategies.sqlite3'
        }
        self.schema_paths = {
            'gui_unified': 'upbit_auto_trading/utils/trading_variables/gui_variables_DB_migration_util/data_info/upbit_autotrading_unified_schema.sql'
        }
    
    def check_all_databases(self) -> None:
        """
        🤖 LLM 추천: 가장 많이 사용하는 메서드
        모든 데이터베이스 상태 확인 - DB 테이블 개수와 변수 관련 테이블 현황 파악
        
        출력 예시:
        📊 === SETTINGS DB 분석 ===
        📋 총 테이블 수: 28
        🎯 변수 관련 테이블 분석 (5개):
          • tv_trading_variables: 42개 레코드
          • tv_variable_parameters: 37개 레코드
        """
        print("🔍 === Super DB Table Viewer ===\n")
        
        for db_name, db_path in self.db_paths.items():
            print(f"📊 === {db_name.upper()} DB 분석 ===")
            if os.path.exists(db_path):
                self._analyze_database(db_path)
            else:
                print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
            print()
    
    def check_database(self, db_name: str = 'settings') -> None:
        """특정 데이터베이스 상세 분석"""
        if db_name not in self.db_paths:
            print(f"❌ 알 수 없는 DB: {db_name}")
            print(f"📋 사용 가능한 DB: {list(self.db_paths.keys())}")
            return
            
        db_path = self.db_paths[db_name]
        if not os.path.exists(db_path):
            print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
            return
            
        print(f"🔍 === {db_name.upper()} DB 상세 분석 ===")
        self._analyze_database(db_path, detailed=True)
    
    def _analyze_database(self, db_path: str, detailed: bool = False) -> None:
        """데이터베이스 분석 실행"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # 기본 테이블 정보
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cursor.fetchall()]
                
                print(f"📋 총 테이블 수: {len(tables)}")
                
                if detailed:
                    self._show_detailed_table_info(cursor, tables)
                else:
                    self._show_basic_table_info(tables)
                
                # 변수 관련 테이블 특별 분석
                self._analyze_variable_tables(cursor, tables)
                
        except Exception as e:
            print(f"❌ DB 분석 중 오류: {e}")
    
    def _show_basic_table_info(self, tables: List[str]) -> None:
        """기본 테이블 목록 표시"""
        for i, table in enumerate(tables, 1):
            print(f"  {i:2d}. {table}")
    
    def _show_detailed_table_info(self, cursor: sqlite3.Cursor, tables: List[str]) -> None:
        """상세 테이블 정보 표시"""
        print("\n📊 테이블 상세 정보:")
        print("-" * 80)
        print(f"{'No.':<4} {'테이블명':<25} {'레코드수':<10} {'주요 컬럼'}")
        print("-" * 80)
        
        for i, table in enumerate(tables, 1):
            try:
                # 레코드 수 조회
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]
                
                # 주요 컬럼 조회 (처음 3개)
                cursor.execute(f"PRAGMA table_info(`{table}`)")
                columns = cursor.fetchall()
                main_columns = [col[1] for col in columns[:3]]
                column_str = ", ".join(main_columns)
                if len(columns) > 3:
                    column_str += f" (+{len(columns)-3}개)"
                
                print(f"{i:<4} {table:<25} {count:<10} {column_str}")
                
            except Exception as e:
                print(f"{i:<4} {table:<25} {'오류':<10} {str(e)[:30]}")
    
    def _analyze_variable_tables(self, cursor: sqlite3.Cursor, tables: List[str]) -> None:
        """변수 관련 테이블 특별 분석"""
        var_tables = [t for t in tables if 'variable' in t.lower()]
        
        if not var_tables:
            return
            
        print(f"\n🎯 변수 관련 테이블 분석 ({len(var_tables)}개):")
        
        for table in var_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                count = cursor.fetchone()[0]
                print(f"  • {table}: {count}개 레코드")
                
                # tv_variable_parameters 특별 분석
                if table == 'tv_variable_parameters' and count > 0:
                    cursor.execute("SELECT DISTINCT variable_id FROM tv_variable_parameters LIMIT 5")
                    var_ids = [row[0] for row in cursor.fetchall()]
                    print(f"    └─ 파라미터가 있는 변수: {', '.join(var_ids)}")
                
                # tv_trading_variables 특별 분석  
                elif table == 'tv_trading_variables' and count > 0:
                    cursor.execute("SELECT COUNT(DISTINCT purpose_category) FROM tv_trading_variables")
                    cat_count = cursor.fetchone()[0]
                    print(f"    └─ 목적 카테고리 수: {cat_count}개")
                    
            except Exception as e:
                print(f"  • {table}: 분석 오류 - {e}")
    
    def compare_with_schema(self, schema_name: str = 'gui_unified') -> None:
        """
        🤖 LLM 추천: 마이그레이션 전후 DB 상태 비교 시 사용
        스키마 파일과 DB 비교 - 차이점 분석으로 마이그레이션 계획 수립
        
        출력 예시:
        🔍 === DB vs 스키마 비교 (gui_unified) ===
        📊 DB 테이블: 28개
        📋 스키마 테이블: 27개
        ✅ 공통 테이블 (27개): ...
        🔵 DB에만 있는 테이블 (1개): sqlite_sequence
        📋 비교 요약: • 일치: 27개 • DB 추가: 1개 • 스키마 추가: 0개
        """
        if schema_name not in self.schema_paths:
            print(f"❌ 알 수 없는 스키마: {schema_name}")
            return
            
        schema_path = self.schema_paths[schema_name]
        if not os.path.exists(schema_path):
            print(f"❌ 스키마 파일이 존재하지 않습니다: {schema_path}")
            return
            
        # DB 테이블 조회
        db_path = self.db_paths['settings']  # 기본적으로 settings DB 사용
        if not os.path.exists(db_path):
            print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
            return
            
        try:
            # DB 테이블 목록
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
                db_tables = set(row[0] for row in cursor.fetchall())
            
            # 스키마 파일 테이블 목록
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_content = f.read()
            
            create_patterns = re.findall(
                r'CREATE TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+(\w+)\s*\(',
                schema_content,
                re.IGNORECASE
            )
            schema_tables = set(create_patterns)
            
            # 비교 결과
            print(f"🔍 === DB vs 스키마 비교 ({schema_name}) ===")
            print(f"📊 DB 테이블: {len(db_tables)}개")
            print(f"📋 스키마 테이블: {len(schema_tables)}개")
            print()
            
            # 공통 테이블
            common = db_tables & schema_tables
            print(f"✅ 공통 테이블 ({len(common)}개):")
            for table in sorted(common):
                print(f"    {table}")
            print()
            
            # DB에만 있는 테이블
            db_only = db_tables - schema_tables
            if db_only:
                print(f"🔵 DB에만 있는 테이블 ({len(db_only)}개):")
                for table in sorted(db_only):
                    print(f"    {table}")
                print()
            
            # 스키마에만 있는 테이블
            schema_only = schema_tables - db_tables
            if schema_only:
                print(f"🟡 스키마에만 있는 테이블 ({len(schema_only)}개):")
                for table in sorted(schema_only):
                    print(f"    {table}")
                print()
            
            # 요약
            print("📋 비교 요약:")
            print(f"  • 일치: {len(common)}개")
            print(f"  • DB 추가: {len(db_only)}개") 
            print(f"  • 스키마 추가: {len(schema_only)}개")
            
        except Exception as e:
            print(f"❌ 비교 중 오류: {e}")
    
    def show_table_structure(self, table_name: str, db_name: str = 'settings') -> None:
        """
        🤖 LLM 추천: 특정 테이블 상세 정보 필요 시 사용
        특정 테이블 구조 상세 조회 - 컬럼 정보, 타입, 샘플 데이터
        
        사용 예시:
        viewer.show_table_structure('tv_trading_variables')  # 거래 변수 테이블 구조
        viewer.show_table_structure('strategies')            # 전략 테이블 구조
        
        출력 예시:
        🔍 === tv_trading_variables 테이블 구조 ===
        📊 컬럼 정보: variable_id, display_name_ko, purpose_category...
        📋 총 레코드 수: 42개
        📄 샘플 데이터 (최대 3개): 실제 데이터 예시 표시
        """
        if db_name not in self.db_paths:
            print(f"❌ 알 수 없는 DB: {db_name}")
            return
            
        db_path = self.db_paths[db_name]
        if not os.path.exists(db_path):
            print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
            return
            
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # 테이블 존재 확인
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    print(f"❌ 테이블을 찾을 수 없습니다: {table_name}")
                    return
                
                print(f"🔍 === {table_name} 테이블 구조 ===")
                
                # 컬럼 정보
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = cursor.fetchall()
                
                print("\n📊 컬럼 정보:")
                print("-" * 80)
                print(f"{'No.':<4} {'컬럼명':<20} {'타입':<15} {'Null':<6} {'기본값':<15} {'PK'}")
                print("-" * 80)
                
                for col in columns:
                    cid, name, type_, notnull, default, pk = col
                    null_str = "NO" if notnull else "YES"
                    default_str = str(default) if default else ""
                    pk_str = "YES" if pk else ""
                    print(f"{cid+1:<4} {name:<20} {type_:<15} {null_str:<6} {default_str:<15} {pk_str}")
                
                # 레코드 수
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                print(f"\n📋 총 레코드 수: {count}개")
                
                # 샘플 데이터 (최대 3개)
                if count > 0:
                    cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 3")
                    samples = cursor.fetchall()
                    
                    print(f"\n📄 샘플 데이터 (최대 3개):")
                    col_names = [col[1] for col in columns]
                    
                    for i, sample in enumerate(samples, 1):
                        print(f"\n  레코드 {i}:")
                        for j, (col_name, value) in enumerate(zip(col_names, sample)):
                            print(f"    {col_name}: {value}")
                
        except Exception as e:
            print(f"❌ 테이블 구조 조회 중 오류: {e}")


def main():
    """
    🤖 LLM 사용 가이드: 메인 실행 함수
    
    명령행 인수에 따라 다른 기능 실행:
    - 인수 없음 또는 'all': 전체 DB 요약 (기본값, 가장 유용)
    - 'settings'/'market_data'/'strategies': 특정 DB 상세 분석
    - 'compare': DB vs 스키마 비교  
    - 'table 테이블명': 특정 테이블 구조 조회
    
    🎯 LLM이 자주 사용할 패턴:
    1. python super_db_table_viewer.py              # 전체 현황 파악
    2. python super_db_table_viewer.py compare      # 마이그레이션 검증
    3. python super_db_table_viewer.py table tv_trading_variables  # 특정 테이블 확인
    """
    import sys
    
    viewer = SuperDBTableViewer()
    
    if len(sys.argv) == 1:
        # 인수 없음 - 전체 DB 요약
        viewer.check_all_databases()
    elif len(sys.argv) == 2:
        cmd = sys.argv[1]
        if cmd == "all":
            viewer.check_all_databases()
        elif cmd == "compare":
            viewer.compare_with_schema()
        elif cmd in viewer.db_paths:
            viewer.check_database(cmd)
        else:
            print(f"❌ 알 수 없는 명령어: {cmd}")
            print_usage()
    elif len(sys.argv) == 3:
        cmd, arg = sys.argv[1], sys.argv[2]
        if cmd == "table":
            viewer.show_table_structure(arg)
        elif cmd == "compare":
            viewer.compare_with_schema(arg)
        else:
            print(f"❌ 알 수 없는 명령어: {cmd}")
            print_usage()
    else:
        print_usage()


def print_usage():
    """
    🤖 LLM을 위한 상세 사용법 가이드
    사용자가 도구 사용법을 물어볼 때 이 내용을 참조하세요
    """
    print("""
🔍 Super DB Table Viewer 사용법:

🤖 === LLM을 위한 핵심 가이드 ===
가장 많이 사용할 명령어들:

1️⃣ 전체 DB 현황 파악 (가장 기본, 자주 사용):
   python super_db_table_viewer.py

2️⃣ 마이그레이션 전후 비교 (중요):
   python super_db_table_viewer.py compare

3️⃣ 특정 테이블 상세 조회:
   python super_db_table_viewer.py table tv_trading_variables
   python super_db_table_viewer.py table strategies

📋 === 전체 명령어 목록 ===
기본 사용:
  python super_db_table_viewer.py              # 전체 DB 요약 ⭐ 가장 유용
  python super_db_table_viewer.py all          # 전체 DB 요약 (위와 동일)
  python super_db_table_viewer.py settings     # settings DB 상세 분석
  python super_db_table_viewer.py market_data  # market_data DB 상세 분석

비교 분석:
  python super_db_table_viewer.py compare      # DB vs 스키마 비교 ⭐ 마이그레이션 시 필수
  
테이블 구조:
  python super_db_table_viewer.py table 테이블명    # 특정 테이블 구조 조회

💡 === 활용 시나리오 ===
• DB 문제 진단: 전체 요약으로 시작 → 특정 테이블 상세 조회
• 마이그레이션 검증: compare로 스키마 차이점 확인
• 데이터 분석: 테이블 구조로 컬럼 정보와 샘플 데이터 확인
• 변수 시스템 디버깅: tv_* 테이블들의 레코드 수와 상태 확인
""")


if __name__ == "__main__":
    main()
