#!/usr/bin/env python3
"""
🔄 GUI용 Trading Variables DB 마이그레이션 모듈
GUI 컴포넌트에서 사용하는 마이그레이션 클래스

주요 기능:
1. GUI 환경에 최적화된 진행 상황 보고
2. 기존 schema_new02.sql을 사용한 마이그레이션
3. 안전한 백업 및 복원 기능
4. 실시간 로그 및 진행 상황 업데이트

작성일: 2025-07-30
버전: 2.0.0 (GUI 최적화)
"""

import os
import sqlite3
import shutil
from datetime import datetime
from typing import Dict, Any, Callable, Optional


class TradingVariablesDBMigration:
    """GUI용 Trading Variables DB 마이그레이션 클래스"""
    
    def __init__(self, db_path: str, progress_callback: Optional[Callable] = None, log_callback: Optional[Callable] = None):
        """
        초기화
        
        Args:
            db_path: DB 파일 경로
            progress_callback: 진행 상황 콜백 함수 (message, percentage)
            log_callback: 로그 메시지 콜백 함수 (message, level)
        """
        self.db_path = db_path
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.backup_path = None
        
        # 스키마 파일 경로 설정 (GUI 컴포넌트 기준)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        gui_util_dir = os.path.dirname(current_dir)  # gui_variables_DB_migration_util
        trading_vars_dir = os.path.dirname(gui_util_dir)  # trading_variables
        self.schema_file = os.path.join(trading_vars_dir, "schema_new02.sql")
        
        self._log(f"🎯 DB 경로: {self.db_path}", "INFO")
        self._log(f"📄 스키마 파일: {self.schema_file}", "INFO")
    
    def _log(self, message: str, level: str = "INFO"):
        """로그 메시지 출력"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        if self.log_callback:
            self.log_callback(message, level)
    
    def _update_progress(self, message: str, percentage: int):
        """진행 상황 업데이트"""
        self._log(message, "INFO")
        if self.progress_callback:
            self.progress_callback(message, percentage)
    
    def create_backup(self) -> str:
        """
        기존 DB 백업 생성
        
        Returns:
            백업 파일 경로
        """
        # 백업 파일명 수정 (settings.sqlite3 기준)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"settings_backup_{timestamp}.sqlite3"
        backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
        
        # 백업 디렉토리 생성
        os.makedirs(backup_dir, exist_ok=True)
        
        self.backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            shutil.copy2(self.db_path, self.backup_path)
            self._log(f"✅ 백업 완료: {backup_filename}", "SUCCESS")
            return self.backup_path
        except Exception as e:
            self._log(f"❌ 백업 실패: {e}", "ERROR")
            raise
    
    def analyze_existing_db(self) -> Dict[str, Any]:
        """
        기존 DB 구조 분석
        
        Returns:
            DB 분석 결과
        """
        if not os.path.exists(self.db_path):
            self._log("ℹ️ 기존 DB 파일이 없습니다. 새로 생성됩니다.", "INFO")
            return {"tables": [], "has_legacy": False, "needs_migration": True}
        
        analysis = {
            "tables": [],
            "legacy_tables": [],
            "new_tables": [],
            "has_legacy": False,
            "has_new_schema": False,
            "needs_migration": False,
            "data_count": {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 테이블 목록 조회
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                analysis["tables"] = tables
                
                # 스키마 파일에서 정의된 테이블 목록 가져오기
                schema_tables = self._get_schema_tables()
                
                # 새 스키마 테이블 확인 (tv_ 접두사)
                for table in tables:
                    if table.startswith('tv_') and table in schema_tables:
                        analysis["new_tables"].append(table)
                        analysis["has_new_schema"] = True
                
                # 레거시 테이블 식별 (스키마 기반)
                # 하드코딩 제거: 이전 방식 (주석)
                # legacy_patterns = [
                #     "trading_variables",    # 접두사 없는 구버전
                #     "variable_parameters",  # 접두사 없는 구버전
                # ]
                
                for table in tables:
                    # tv_ 접두사가 없고 스키마에 정의되지 않은 테이블을 레거시로 간주
                    if not table.startswith('tv_') and table not in schema_tables:
                        # sqlite 시스템 테이블 제외
                        if not table.startswith('sqlite_'):
                            analysis["legacy_tables"].append(table)
                            analysis["has_legacy"] = True
                            
                            # 데이터 개수 확인
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                count = cursor.fetchone()[0]
                                analysis["data_count"][table] = count
                            except sqlite3.Error:
                                analysis["data_count"][table] = 0
                
                # 마이그레이션 필요 여부 판단
                if not analysis["has_new_schema"]:
                    analysis["needs_migration"] = True
                    self._log("🔄 새 스키마가 없어 마이그레이션이 필요합니다.", "INFO")
                elif analysis["has_legacy"]:
                    analysis["needs_migration"] = True
                    self._log("🔄 레거시 테이블 정리를 위한 마이그레이션이 필요합니다.", "INFO")
                else:
                    self._log("✅ 이미 최신 스키마가 적용되어 있습니다.", "SUCCESS")
                
                self._log("🔍 기존 DB 분석 완료:", "INFO")
                self._log(f"  - 전체 테이블: {len(tables)}개", "INFO")
                self._log(f"  - 새 스키마 테이블: {len(analysis['new_tables'])}개", "INFO")
                self._log(f"  - 레거시 테이블: {len(analysis['legacy_tables'])}개", "INFO")
                
        except Exception as e:
            self._log(f"⚠️ DB 분석 중 오류: {e}", "ERROR")
            analysis["error"] = str(e)
            analysis["needs_migration"] = True
        
        return analysis
    
    def remove_legacy_tables(self, conn: sqlite3.Connection) -> bool:
        """
        레거시 테이블 완전 제거 (스키마 파일 기반)
        
        스키마 파일에서 정의된 테이블과 현재 DB의 테이블을 비교하여
        스키마에 없는 테이블을 레거시로 간주하고 제거합니다.
        
        Args:
            conn: DB 연결 객체
            
        Returns:
            성공 여부
        """
        # 하드코딩 제거: 이전 방식 (주석)
        # legacy_tables = [
        #     "trading_variables",      # → tv_trading_variables로 대체됨
        #     "variable_parameters",    # → tv_variable_parameters로 대체됨  
        #     "comparison_groups",      # → tv_comparison_groups로 대체됨
        #     "schema_version"          # → tv_schema_version으로 대체됨
        # ]
        
        # 새로운 방식: 스키마 파일에서 정의된 테이블 목록 가져오기
        schema_tables = self._get_schema_tables()
        current_tables = self._get_current_tables(conn)
        
        # 스키마에 없는 테이블을 레거시로 간주
        legacy_tables = []
        for table in current_tables:
            # tv_ 접두사가 없고 스키마에 정의되지 않은 테이블
            if not table.startswith('tv_') and table not in schema_tables:
                # sqlite 시스템 테이블 제외
                if not table.startswith('sqlite_'):
                    legacy_tables.append(table)
        
        if not legacy_tables:
            self._log("ℹ️ 제거할 레거시 테이블이 없습니다.", "INFO")
            return True
            
        self._log(f"🔍 발견된 레거시 테이블: {', '.join(legacy_tables)}", "INFO")
        
        cursor = conn.cursor()
        removed_count = 0
        
        for table in legacy_tables:
            try:
                # 테이블 존재 확인
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                    (table,)
                )
                if cursor.fetchone():
                    # 데이터 개수 확인 후 삭제
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    self._log(f"🗑️ 레거시 테이블 제거: {table} ({count}개 레코드)", "INFO")
                    removed_count += 1
            except Exception as e:
                self._log(f"⚠️ 테이블 {table} 제거 중 오류: {e}", "WARNING")
        
        if removed_count > 0:
            self._log(f"✅ 총 {removed_count}개 레거시 테이블 제거 완료", "SUCCESS")
        else:
            self._log("ℹ️ 제거할 레거시 테이블이 없습니다.", "INFO")
        
        return True
    
    def _get_schema_tables(self) -> set:
        """스키마 파일에서 정의된 테이블 목록 가져오기"""
        schema_tables = set()
        
        try:
            if os.path.exists(self.schema_file):
                with open(self.schema_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # CREATE TABLE 구문에서 테이블명 추출
                import re
                table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)'
                matches = re.findall(table_pattern, content, re.IGNORECASE)
                
                for match in matches:
                    schema_tables.add(match)
                    
                self._log(f"📋 스키마 파일에서 {len(schema_tables)}개 테이블 발견", "INFO")
                
        except Exception as e:
            self._log(f"⚠️ 스키마 파일 읽기 실패: {e}", "WARNING")
            
        return schema_tables
    
    def _get_current_tables(self, conn: sqlite3.Connection) -> list:
        """현재 DB의 테이블 목록 가져오기"""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self._log(f"📊 현재 DB에 {len(tables)}개 테이블 존재", "INFO")
            return tables
            
        except Exception as e:
            self._log(f"⚠️ 현재 테이블 목록 조회 실패: {e}", "ERROR")
            return []
    
    def apply_new_schema(self, conn: sqlite3.Connection) -> bool:
        """
        새로운 스키마 적용 (schema_new02.sql 사용)
        
        Args:
            conn: DB 연결 객체
            
        Returns:
            성공 여부
        """
        if not os.path.exists(self.schema_file):
            self._log(f"❌ 스키마 파일을 찾을 수 없습니다: {self.schema_file}", "ERROR")
            return False
        
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # SQL 스크립트를 문장별로 분할하여 실행
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            cursor = conn.cursor()
            success_count = 0
            total_statements = len([s for s in statements if not s.startswith('--') and s])
            
            # SQL 문장을 종류별로 분류하여 순서대로 실행
            create_table_statements = []
            create_index_statements = []
            insert_statements = []
            other_statements = []
            
            for statement in statements:
                if statement.startswith('--') or not statement:
                    continue
                
                statement_upper = statement.upper().strip()
                if statement_upper.startswith('CREATE TABLE'):
                    create_table_statements.append(statement)
                elif statement_upper.startswith('CREATE INDEX'):
                    create_index_statements.append(statement)
                elif statement_upper.startswith('INSERT'):
                    insert_statements.append(statement)
                else:
                    other_statements.append(statement)
            
            # 순서대로 실행: 테이블 생성 → 인덱스 생성 → 데이터 삽입 → 기타
            all_ordered_statements = create_table_statements + create_index_statements + insert_statements + other_statements
            
            self._log(f"스키마 적용 계획: 테이블 {len(create_table_statements)}개, 인덱스 {len(create_index_statements)}개, 데이터 {len(insert_statements)}개", "INFO")
            
            for i, statement in enumerate(all_ordered_statements):
                try:
                    cursor.execute(statement)
                    success_count += 1
                    
                    # 중요한 테이블 생성 로깅
                    if "CREATE TABLE" in statement.upper() and "tv_" in statement:
                        table_name = statement.split()[5] if len(statement.split()) > 5 else "Unknown"
                        self._log(f"✅ 테이블 생성: {table_name}", "SUCCESS")
                    
                    # 진행 상황 업데이트 (스키마 적용은 50-80% 구간)
                    progress = 50 + int((success_count / len(all_ordered_statements)) * 30)
                    if i % 10 == 0:  # 10개 문장마다 업데이트
                        self._update_progress(f"스키마 적용 중... ({success_count}/{len(all_ordered_statements)})", progress)
                        
                except Exception as e:
                    self._log(f"⚠️ SQL 문장 {i + 1} 실행 오류: {e}", "WARNING")
                    self._log(f"   문장: {statement[:100]}...", "WARNING")
                    # 중요한 테이블 생성 오류는 실패로 처리
                    if "CREATE TABLE" in statement.upper() and "tv_" in statement:
                        self._log(f"❌ 중요한 테이블 생성 실패: {statement[:50]}...", "ERROR")
                        conn.rollback()
                        return False
            
            conn.commit()
            self._log(f"✅ 새 스키마 적용 완료: {success_count}개 문장 실행", "SUCCESS")
            return True
            
        except Exception as e:
            self._log(f"❌ 스키마 적용 실패: {e}", "ERROR")
            conn.rollback()
            return False
    
    def verify_migration(self, conn: sqlite3.Connection) -> bool:
        """
        마이그레이션 결과 검증
        
        Args:
            conn: DB 연결 객체
            
        Returns:
            검증 성공 여부
        """
        cursor = conn.cursor()
        verification_results = {}
        
        # 1. 새 테이블 존재 확인
        expected_tables = [
            'tv_trading_variables',
            'tv_variable_parameters', 
            'tv_comparison_groups',
            'tv_schema_version'
        ]
        
        self._log("🔍 마이그레이션 결과 검증 중...", "INFO")
        
        for table in expected_tables:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                (table,)
            )
            exists = cursor.fetchone() is not None
            verification_results[table] = exists
            
            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                self._log(f"  ✅ {table}: {count}개 레코드", "SUCCESS")
            else:
                self._log(f"  ❌ {table}: 테이블 없음", "ERROR")
        
        # 2. 데이터 무결성 확인
        try:
            # 지표 개수 확인
            cursor.execute("SELECT COUNT(*) FROM tv_trading_variables WHERE is_active = 1")
            active_indicators = cursor.fetchone()[0]
            
            # 파라미터 개수 확인
            cursor.execute("SELECT COUNT(*) FROM tv_variable_parameters")
            total_parameters = cursor.fetchone()[0]
            
            # 카테고리별 분포 확인
            cursor.execute("SELECT purpose_category, COUNT(*) FROM tv_trading_variables GROUP BY purpose_category")
            category_distribution = dict(cursor.fetchall())
            
            self._log(f"📊 데이터 요약:", "INFO")
            self._log(f"  - 활성 지표: {active_indicators}개", "INFO")
            self._log(f"  - 총 파라미터: {total_parameters}개", "INFO")
            self._log(f"  - 카테고리 분포: {category_distribution}", "INFO")
            
            # 기대값과 비교 (schema_new02.sql 기준)
            expected_indicators = 18  # schema_new02.sql의 지표 개수
            expected_parameters = 37  # schema_new02.sql의 파라미터 개수
            
            if active_indicators >= expected_indicators and total_parameters >= expected_parameters:
                self._log("✅ 데이터 무결성 검증 통과", "SUCCESS")
                return True
            else:
                self._log(f"⚠️ 데이터 개수 부족: 지표 {active_indicators}/{expected_indicators}, 파라미터 {total_parameters}/{expected_parameters}", "WARNING")
                return False
                
        except Exception as e:
            self._log(f"❌ 검증 중 오류: {e}", "ERROR")
            return False
    
    def run_migration(self, force: bool = False) -> bool:
        """
        전체 마이그레이션 실행 (GUI 환경 최적화)
        
        Args:
            force: 강제 실행 여부
            
        Returns:
            성공 여부
        """
        self._log("🚀 Trading Variables DB 마이그레이션 시작", "INFO")
        
        try:
            # 1. 기존 DB 분석 (0-10%)
            self._update_progress("기존 DB 분석 중...", 5)
            analysis = self.analyze_existing_db()
            
            # 마이그레이션이 필요하지 않은 경우
            if not analysis.get("needs_migration", True):
                self._log("ℹ️ 마이그레이션이 필요하지 않습니다.", "INFO")
                self._update_progress("마이그레이션 완료 (이미 최신 상태)", 100)
                return True
            
            # 2. 백업 생성 (10-30%)
            self._update_progress("백업 파일 생성 중...", 15)
            if os.path.exists(self.db_path):
                self.create_backup()
            self._update_progress("백업 완료", 30)
            
            # 3. 마이그레이션 실행 (30-90%)
            with sqlite3.connect(self.db_path) as conn:
                # 외래키 제약조건 활성화
                conn.execute("PRAGMA foreign_keys = ON")
                
                # 3-1. 레거시 테이블 제거 (30-50%)
                self._update_progress("레거시 테이블 제거 중...", 35)
                self.remove_legacy_tables(conn)
                self._update_progress("레거시 테이블 제거 완료", 50)
                
                # 3-2. 새 스키마 적용 (50-80%)
                self._update_progress("새 스키마 적용 중...", 55)
                if not self.apply_new_schema(conn):
                    self._log("❌ 스키마 적용 실패", "ERROR")
                    return False
                self._update_progress("스키마 적용 완료", 80)
                
                # 3-3. 결과 검증 (80-90%)
                self._update_progress("마이그레이션 결과 검증 중...", 85)
                if not self.verify_migration(conn):
                    self._log("❌ 마이그레이션 검증 실패", "ERROR")
                    return False
                self._update_progress("검증 완료", 90)
            
            # 4. 완료 (90-100%)
            self._update_progress("마이그레이션 완료!", 100)
            self._log("🎉 마이그레이션 완료!", "SUCCESS")
            self._log(f"📁 백업 파일: {os.path.basename(self.backup_path) if self.backup_path else 'N/A'}", "INFO")
            self._log("✨ 이제 새로운 DB 스키마를 사용할 수 있습니다!", "SUCCESS")
            
            return True
            
        except Exception as e:
            self._log(f"💥 마이그레이션 중 오류 발생: {e}", "ERROR")
            if self.backup_path and os.path.exists(self.backup_path):
                self._log(f"🔄 백업에서 복원 가능: {os.path.basename(self.backup_path)}", "INFO")
            return False
    
    def rollback_from_backup(self, backup_file: str = None) -> bool:
        """
        백업에서 DB 복원
        
        Args:
            backup_file: 백업 파일 경로 (기본값: 가장 최근 백업)
            
        Returns:
            성공 여부
        """
        if backup_file is None:
            backup_file = self.backup_path
        
        if not backup_file or not os.path.exists(backup_file):
            self._log(f"❌ 백업 파일을 찾을 수 없습니다: {backup_file}", "ERROR")
            return False
        
        try:
            shutil.copy2(backup_file, self.db_path)
            self._log(f"✅ 백업에서 복원 완료: {os.path.basename(backup_file)}", "SUCCESS")
            return True
        except Exception as e:
            self._log(f"❌ 복원 실패: {e}", "ERROR")
            return False
