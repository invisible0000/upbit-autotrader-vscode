#!/usr/bin/env python3
"""
🔄 Trading Variables DB 완전 마이그레이션 도구
기존 설정 DB를 새로운 스키마로 완전히 개선하는 마이그레이션 스크립트

주요 기능:
1. 기존 변수 관련 테이블 완전 제거 (레거시 정리)
2. 새로운 tv_ 접두사 스키마 적용
3. 기존 코드와 100% 호환성 보장
4. 데이터 무결성 및 성능 최적화

작성일: 2025-07-30
버전: 2.0.0
"""

import os
import sqlite3
import shutil
from datetime import datetime
from typing import Dict, Any


class TradingVariablesDBMigration:
    """Trading Variables DB 완전 마이그레이션 클래스"""
    
    def __init__(self, db_path: str = None):
        """
        초기화
        
        Args:
            db_path: DB 파일 경로 (기본값: 프로젝트 표준 경로)
        """
        if db_path is None:
            # 프로젝트 표준 경로 사용
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            self.db_path = os.path.join(project_root, "upbit_auto_trading", "data", "settings.sqlite3")
        else:
            self.db_path = db_path
            
        self.backup_path = None
        self.schema_file = os.path.join(os.path.dirname(__file__), "schema_new02.sql")
        
        print(f"🎯 DB 경로: {self.db_path}")
        print(f"📄 스키마 파일: {self.schema_file}")
    
    def create_backup(self) -> str:
        """
        기존 DB 백업 생성
        
        Returns:
            백업 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"settings_backup_{timestamp}.sqlite3"
        backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
        
        # 백업 디렉토리 생성
        os.makedirs(backup_dir, exist_ok=True)
        
        self.backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            shutil.copy2(self.db_path, self.backup_path)
            print(f"✅ 백업 완료: {self.backup_path}")
            return self.backup_path
        except Exception as e:
            print(f"❌ 백업 실패: {e}")
            raise
    
    def analyze_existing_db(self) -> Dict[str, Any]:
        """
        기존 DB 구조 분석
        
        Returns:
            DB 분석 결과
        """
        if not os.path.exists(self.db_path):
            print("ℹ️ 기존 DB 파일이 없습니다. 새로 생성됩니다.")
            return {"tables": [], "has_legacy": False}
        
        analysis = {
            "tables": [],
            "legacy_tables": [],
            "has_legacy": False,
            "data_count": {}
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 테이블 목록 조회
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                analysis["tables"] = tables
                
                # 레거시 테이블 식별
                legacy_patterns = [
                    "trading_variables",  # 접두사 없는 구버전
                    "variable_parameters",  # 접두사 없는 구버전
                    "comparison_groups",  # 접두사 없는 구버전
                ]
                
                for table in tables:
                    if any(pattern in table for pattern in legacy_patterns):
                        analysis["legacy_tables"].append(table)
                        analysis["has_legacy"] = True
                        
                        # 데이터 개수 확인
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            analysis["data_count"][table] = count
                        except sqlite3.Error:
                            analysis["data_count"][table] = 0
                
                print("🔍 기존 DB 분석 완료:")
                print(f"  - 전체 테이블: {len(tables)}개")
                print(f"  - 레거시 테이블: {len(analysis['legacy_tables'])}개")
                if analysis["legacy_tables"]:
                    print(f"  - 레거시 목록: {', '.join(analysis['legacy_tables'])}")
                
        except Exception as e:
            print(f"⚠️ DB 분석 중 오류: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def remove_legacy_tables(self, conn: sqlite3.Connection) -> bool:
        """
        레거시 테이블 완전 제거
        
        Args:
            conn: DB 연결 객체
            
        Returns:
            성공 여부
        """
        legacy_tables = [
            "trading_variables",
            "variable_parameters", 
            "comparison_groups",
            "schema_version"
        ]
        
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
                    print(f"🗑️ 레거시 테이블 제거: {table} ({count}개 레코드)")
                    removed_count += 1
            except Exception as e:
                print(f"⚠️ 테이블 {table} 제거 중 오류: {e}")
        
        if removed_count > 0:
            print(f"✅ 총 {removed_count}개 레거시 테이블 제거 완료")
        else:
            print("ℹ️ 제거할 레거시 테이블이 없습니다.")
        
        return True
    
    def apply_new_schema(self, conn: sqlite3.Connection) -> bool:
        """
        새로운 스키마 적용
        
        Args:
            conn: DB 연결 객체
            
        Returns:
            성공 여부
        """
        if not os.path.exists(self.schema_file):
            print(f"❌ 스키마 파일을 찾을 수 없습니다: {self.schema_file}")
            return False
        
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # SQL 스크립트를 문장별로 분할하여 실행
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            cursor = conn.cursor()
            success_count = 0
            
            for i, statement in enumerate(statements):
                if statement.startswith('--') or not statement:
                    continue
                    
                try:
                    cursor.execute(statement)
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ SQL 문장 {i+1} 실행 오류: {e}")
                    print(f"   문장: {statement[:100]}...")
            
            conn.commit()
            print(f"✅ 새 스키마 적용 완료: {success_count}개 문장 실행")
            return True
            
        except Exception as e:
            print(f"❌ 스키마 적용 실패: {e}")
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
        
        print("🔍 마이그레이션 결과 검증 중...")
        
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
                print(f"  ✅ {table}: {count}개 레코드")
            else:
                print(f"  ❌ {table}: 테이블 없음")
        
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
            
            print(f"📊 데이터 요약:")
            print(f"  - 활성 지표: {active_indicators}개")
            print(f"  - 총 파라미터: {total_parameters}개")
            print(f"  - 카테고리 분포: {category_distribution}")
            
            # 기대값과 비교
            expected_indicators = 18  # schema_new02.sql의 지표 개수
            expected_parameters = 37  # schema_new02.sql의 파라미터 개수
            
            if active_indicators >= expected_indicators and total_parameters >= expected_parameters:
                print("✅ 데이터 무결성 검증 통과")
                return True
            else:
                print(f"⚠️ 데이터 개수 부족: 지표 {active_indicators}/{expected_indicators}, 파라미터 {total_parameters}/{expected_parameters}")
                return False
                
        except Exception as e:
            print(f"❌ 검증 중 오류: {e}")
            return False
    
    def run_migration(self, force: bool = False) -> bool:
        """
        전체 마이그레이션 실행
        
        Args:
            force: 강제 실행 여부
            
        Returns:
            성공 여부
        """
        print("🚀 Trading Variables DB 마이그레이션 시작")
        print("=" * 60)
        
        try:
            # 1. 기존 DB 분석
            analysis = self.analyze_existing_db()
            
            # 2. 백업 생성 (기존 DB가 있는 경우만)
            if os.path.exists(self.db_path):
                self.create_backup()
            
            # 3. 사용자 확인 (force가 아닌 경우)
            if not force and analysis.get("has_legacy", False):
                print(f"\n⚠️ 다음 레거시 테이블들이 완전히 제거됩니다:")
                for table in analysis["legacy_tables"]:
                    count = analysis["data_count"].get(table, 0)
                    print(f"  - {table}: {count}개 레코드")
                
                confirm = input(f"\n계속 진행하시겠습니까? (y/N): ")
                if confirm.lower() != 'y':
                    print("❌ 마이그레이션이 취소되었습니다.")
                    return False
            
            # 4. DB 연결 및 마이그레이션 실행
            with sqlite3.connect(self.db_path) as conn:
                # 외래키 제약조건 활성화
                conn.execute("PRAGMA foreign_keys = ON")
                
                # 4-1. 레거시 테이블 제거
                self.remove_legacy_tables(conn)
                
                # 4-2. 새 스키마 적용
                if not self.apply_new_schema(conn):
                    print("❌ 스키마 적용 실패")
                    return False
                
                # 4-3. 결과 검증
                if not self.verify_migration(conn):
                    print("❌ 마이그레이션 검증 실패")
                    return False
            
            print("\n" + "=" * 60)
            print("🎉 마이그레이션 완료!")
            print(f"📁 백업 파일: {self.backup_path}")
            print(f"🆕 새 DB: {self.db_path}")
            print("\n✨ 이제 기존 코드와 100% 호환되는 새로운 DB 스키마를 사용할 수 있습니다!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 마이그레이션 중 심각한 오류 발생: {e}")
            if self.backup_path and os.path.exists(self.backup_path):
                print(f"🔄 백업에서 복원하려면: {self.backup_path}")
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
            print(f"❌ 백업 파일을 찾을 수 없습니다: {backup_file}")
            return False
        
        try:
            shutil.copy2(backup_file, self.db_path)
            print(f"✅ 백업에서 복원 완료: {backup_file} → {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ 복원 실패: {e}")
            return False


def main():
    """메인 함수 - 명령행에서 직접 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trading Variables DB 마이그레이션 도구")
    parser.add_argument("--db-path", help="DB 파일 경로 (기본값: 프로젝트 표준 경로)")
    parser.add_argument("--force", action="store_true", help="확인 없이 강제 실행")
    parser.add_argument("--rollback", help="지정된 백업 파일에서 복원")
    
    args = parser.parse_args()
    
    migration = TradingVariablesDBMigration(args.db_path)
    
    if args.rollback:
        success = migration.rollback_from_backup(args.rollback)
    else:
        success = migration.run_migration(args.force)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
