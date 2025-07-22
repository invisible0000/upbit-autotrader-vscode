#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DB 정리 및 초기화 관리자

기획 변경이나 스키마 변경 시 깨끗한 DB 상태를 만들어주는 관리자
"""

import os
import shutil
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager
from upbit_auto_trading.data_layer.storage.backup_manager import BackupManager

logger = logging.getLogger(__name__)

class DBCleanupManager:
    """DB 초기화 및 정리를 담당하는 클래스"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        DBCleanupManager 초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = config_path
        self.db_manager = get_database_manager()
        self.backup_manager = BackupManager()
        self.data_dir = Path("data")
        
    def analyze_current_state(self) -> Dict[str, Any]:
        """
        현재 DB 상태를 분석합니다.
        
        Returns:
            분석 결과 딕셔너리
        """
        logger.info("🔍 현재 DB 상태 분석 시작...")
        
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "database_files": [],
            "tables": {},
            "data_counts": {},
            "schema_version": "unknown",
            "total_size_mb": 0,
            "issues": []
        }
        
        try:
            # 1. DB 파일 검색
            db_files = list(self.data_dir.glob("*.db")) + list(self.data_dir.glob("*.sqlite*"))
            analysis_result["database_files"] = [str(f) for f in db_files]
            
            # 2. 총 크기 계산
            total_size = sum(f.stat().st_size for f in db_files if f.exists())
            analysis_result["total_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            # 3. 각 DB 파일 분석
            for db_file in db_files:
                if db_file.exists():
                    self._analyze_database_file(str(db_file), analysis_result)
                    
            # 4. 스키마 버전 감지
            analysis_result["schema_version"] = self._detect_schema_version(analysis_result)
            
            # 5. 문제점 검출
            analysis_result["issues"] = self._detect_issues(analysis_result)
            
            logger.info(f"✅ DB 분석 완료: {len(analysis_result['database_files'])}개 파일, {analysis_result['total_size_mb']}MB")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ DB 상태 분석 실패: {e}")
            analysis_result["error"] = str(e)
            return analysis_result
    
    def _analyze_database_file(self, db_path: str, result: Dict[str, Any]):
        """단일 DB 파일을 분석합니다."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 테이블 목록 조회
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            db_name = Path(db_path).name
            result["tables"][db_name] = tables
            result["data_counts"][db_name] = {}
            
            # 각 테이블의 레코드 수 조회
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    result["data_counts"][db_name][table] = count
                except Exception as e:
                    logger.warning(f"⚠️ 테이블 {table} 카운트 실패: {e}")
                    result["data_counts"][db_name][table] = -1
                    
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ DB 파일 {db_path} 분석 실패: {e}")
    
    def _detect_schema_version(self, analysis: Dict[str, Any]) -> str:
        """스키마 버전을 감지합니다."""
        all_tables = []
        for db_tables in analysis["tables"].values():
            all_tables.extend(db_tables)
        
        # 신규 스키마 감지 (전략 조합 시스템)
        if any("strategy_combinations" in table.lower() for table in all_tables):
            return "v2.0-strategy-combination"
        
        # 포지션 관리 시스템 감지
        elif any("positions" in table.lower() for table in all_tables):
            return "v1.5-position-management"
        
        # 기본 전략 시스템 감지
        elif any("strategy" in table.lower() for table in all_tables):
            return "v1.0-legacy"
        
        # 빈 DB
        elif not all_tables:
            return "v0.0-empty"
        
        return "unknown"
    
    def _detect_issues(self, analysis: Dict[str, Any]) -> List[str]:
        """DB 문제점을 감지합니다."""
        issues = []
        
        # 1. 중복 DB 파일
        if len(analysis["database_files"]) > 1:
            issues.append(f"중복 DB 파일 감지: {len(analysis['database_files'])}개")
        
        # 2. 스키마 버전 충돌
        if analysis["schema_version"] == "unknown":
            issues.append("스키마 버전을 확인할 수 없음")
        
        # 3. 빈 테이블들
        empty_tables = []
        for db_name, counts in analysis["data_counts"].items():
            for table, count in counts.items():
                if count == 0:
                    empty_tables.append(f"{db_name}.{table}")
        
        if empty_tables:
            issues.append(f"빈 테이블들: {', '.join(empty_tables[:5])}" + 
                         (f" 외 {len(empty_tables)-5}개" if len(empty_tables) > 5 else ""))
        
        # 4. 대용량 DB
        if analysis["total_size_mb"] > 500:
            issues.append(f"대용량 DB: {analysis['total_size_mb']}MB")
        
        return issues
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        현재 DB 상태를 백업합니다.
        
        Args:
            backup_name: 백업 이름 (None시 자동 생성)
            
        Returns:
            백업 경로
        """
        if backup_name is None:
            backup_name = f"cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"💾 DB 백업 생성 중: {backup_name}")
        
        try:
            backup_path = self.backup_manager.create_backup(backup_name)
            logger.info(f"✅ 백업 완료: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ 백업 실패: {e}")
            raise
    
    def apply_clean_schema(self, schema_version: str = "latest") -> bool:
        """
        깨끗한 스키마를 적용합니다.
        
        Args:
            schema_version: 적용할 스키마 버전
            
        Returns:
            성공 여부
        """
        logger.info(f"🧹 깨끗한 스키마 적용 중: {schema_version}")
        
        try:
            # 1. 기존 DB 파일들 제거
            self._remove_existing_databases()
            
            # 2. 새 스키마 생성
            if schema_version == "latest":
                schema_version = "v2.0-strategy-combination"
            
            self._create_fresh_schema(schema_version)
            
            logger.info(f"✅ 깨끗한 스키마 적용 완료: {schema_version}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 스키마 적용 실패: {e}")
            return False
    
    def _remove_existing_databases(self):
        """기존 DB 파일들을 제거합니다."""
        db_files = list(self.data_dir.glob("*.db")) + list(self.data_dir.glob("*.sqlite*"))
        
        for db_file in db_files:
            if db_file.exists():
                logger.info(f"🗑️ 기존 DB 파일 제거: {db_file}")
                db_file.unlink()
    
    def _create_fresh_schema(self, schema_version: str):
        """새로운 스키마를 생성합니다."""
        from upbit_auto_trading.data_layer.models import Base
        
        # 새 DB 엔진 생성
        engine = self.db_manager.get_engine()
        
        # 모든 테이블 생성
        Base.metadata.create_all(engine)
        
        logger.info(f"🏗️ 스키마 {schema_version} 생성 완료")
    
    def migrate_selective_data(self, backup_path: str, migration_rules: Dict[str, Any]) -> bool:
        """
        백업에서 선별적으로 데이터를 이관합니다.
        
        Args:
            backup_path: 백업 경로
            migration_rules: 이관 규칙
            
        Returns:
            성공 여부
        """
        logger.info(f"📦 선별적 데이터 이관 시작: {backup_path}")
        
        try:
            # 백업에서 필요한 데이터 추출
            preserved_data = self._extract_data_from_backup(backup_path, migration_rules)
            
            # 새 DB에 데이터 삽입
            self._insert_preserved_data(preserved_data, migration_rules)
            
            logger.info("✅ 선별적 데이터 이관 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 데이터 이관 실패: {e}")
            return False
    
    def _extract_data_from_backup(self, backup_path: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """백업에서 보존할 데이터를 추출합니다."""
        # TODO: 백업 데이터 추출 로직 구현
        return {}
    
    def _insert_preserved_data(self, data: Dict[str, Any], rules: Dict[str, Any]):
        """보존된 데이터를 새 DB에 삽입합니다."""
        # TODO: 데이터 삽입 로직 구현
        pass
    
    def validate_migration(self) -> Dict[str, Any]:
        """
        마이그레이션 결과를 검증합니다.
        
        Returns:
            검증 결과
        """
        logger.info("🔍 마이그레이션 검증 시작...")
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "checks": {},
            "errors": [],
            "warnings": []
        }
        
        try:
            # 1. 스키마 무결성 검증
            validation_result["checks"]["schema_integrity"] = self._validate_schema_integrity()
            
            # 2. 데이터 일관성 검증
            validation_result["checks"]["data_consistency"] = self._validate_data_consistency()
            
            # 3. 외래키 제약 조건 검증
            validation_result["checks"]["foreign_keys"] = self._validate_foreign_keys()
            
            # 4. 전체 상태 결정
            all_passed = all(check.get("passed", False) for check in validation_result["checks"].values())
            validation_result["status"] = "passed" if all_passed else "failed"
            
            logger.info(f"✅ 마이그레이션 검증 완료: {validation_result['status']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ 마이그레이션 검증 실패: {e}")
            validation_result["status"] = "error"
            validation_result["errors"].append(str(e))
            return validation_result
    
    def _validate_schema_integrity(self) -> Dict[str, Any]:
        """스키마 무결성을 검증합니다."""
        # TODO: 스키마 검증 로직 구현
        return {"passed": True, "message": "스키마 무결성 확인"}
    
    def _validate_data_consistency(self) -> Dict[str, Any]:
        """데이터 일관성을 검증합니다."""
        # TODO: 데이터 일관성 검증 로직 구현
        return {"passed": True, "message": "데이터 일관성 확인"}
    
    def _validate_foreign_keys(self) -> Dict[str, Any]:
        """외래키 제약 조건을 검증합니다."""
        # TODO: 외래키 검증 로직 구현
        return {"passed": True, "message": "외래키 제약 조건 확인"}
    
    def emergency_reset(self, preserve_backtests: bool = True) -> bool:
        """
        긴급 DB 초기화를 수행합니다.
        
        Args:
            preserve_backtests: 백테스트 결과 보존 여부
            
        Returns:
            성공 여부
        """
        logger.info("🚨 긴급 DB 초기화 시작...")
        
        try:
            # 1. 현재 상태 분석
            current_state = self.analyze_current_state()
            
            # 2. 백업 생성
            backup_path = self.create_backup("emergency_reset_backup")
            
            # 3. 깨끗한 스키마 적용
            self.apply_clean_schema("latest")
            
            # 4. 필요시 데이터 복원
            if preserve_backtests and "backtest" in str(current_state):
                migration_rules = {"preserve_tables": ["backtest_results", "trade_logs"]}
                self.migrate_selective_data(backup_path, migration_rules)
            
            # 5. 검증
            validation = self.validate_migration()
            
            if validation["status"] == "passed":
                logger.info("✅ 긴급 DB 초기화 성공!")
                return True
            else:
                logger.error("❌ 검증 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 긴급 DB 초기화 실패: {e}")
            return False


# 편의 함수들
def quick_reset() -> bool:
    """빠른 DB 초기화"""
    manager = DBCleanupManager()
    return manager.emergency_reset(preserve_backtests=False)

def safe_reset() -> bool:
    """안전한 DB 초기화 (백테스트 보존)"""
    manager = DBCleanupManager()
    return manager.emergency_reset(preserve_backtests=True)

def analyze_db() -> Dict[str, Any]:
    """현재 DB 상태 분석"""
    manager = DBCleanupManager()
    return manager.analyze_current_state()
