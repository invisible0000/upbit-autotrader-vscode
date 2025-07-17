#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터베이스 마이그레이션 관리자

데이터베이스 스키마 변경 및 마이그레이션을 관리합니다.
"""

import os
import logging
import importlib
import pkgutil
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, MetaData, Table, text

from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager

logger = logging.getLogger(__name__)

class MigrationManager:
    """데이터베이스 마이그레이션을 관리하는 클래스"""
    
    MIGRATION_TABLE = 'schema_migrations'
    
    def __init__(self, migrations_path: str = 'upbit_auto_trading/data_layer/storage/migrations'):
        """MigrationManager 초기화
        
        Args:
            migrations_path: 마이그레이션 스크립트 디렉토리 경로
        """
        self.migrations_path = migrations_path
        self.db_manager = get_database_manager()
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """마이그레이션 테이블이 존재하는지 확인하고, 없으면 생성합니다."""
        engine = self.db_manager.get_engine()
        metadata = MetaData()
        
        # 마이그레이션 테이블 정의
        migrations_table = Table(
            self.MIGRATION_TABLE,
            metadata,
            Column('id', Integer, primary_key=True),
            Column('version', String(50), nullable=False, unique=True),
            Column('applied_at', DateTime, nullable=False, default=datetime.utcnow)
        )
        
        # 테이블이 존재하지 않으면 생성
        if not engine.dialect.has_table(engine.connect(), self.MIGRATION_TABLE):
            metadata.create_all(engine)
            logger.info(f"마이그레이션 테이블 '{self.MIGRATION_TABLE}'이 생성되었습니다.")
    
    def get_applied_migrations(self) -> List[str]:
        """적용된 마이그레이션 버전 목록을 반환합니다.
        
        Returns:
            List[str]: 적용된 마이그레이션 버전 목록
        """
        engine = self.db_manager.get_engine()
        query = f"SELECT version FROM {self.MIGRATION_TABLE} ORDER BY version"
        
        with engine.connect() as conn:
            result = conn.execute(text(query))
            return [row[0] for row in result]
    
    def get_available_migrations(self) -> List[str]:
        """사용 가능한 마이그레이션 스크립트 목록을 반환합니다.
        
        Returns:
            List[str]: 사용 가능한 마이그레이션 스크립트 버전 목록
        """
        migrations = []
        
        if not os.path.exists(self.migrations_path):
            logger.warning(f"마이그레이션 디렉토리가 존재하지 않습니다: {self.migrations_path}")
            return migrations
        
        # 마이그레이션 디렉토리에서 모든 Python 파일 검색
        for _, name, is_pkg in pkgutil.iter_modules([self.migrations_path]):
            if not is_pkg and name.startswith('v'):
                migrations.append(name)
        
        return sorted(migrations)
    
    def get_pending_migrations(self) -> List[str]:
        """적용되지 않은 마이그레이션 스크립트 목록을 반환합니다.
        
        Returns:
            List[str]: 적용되지 않은 마이그레이션 스크립트 버전 목록
        """
        applied = set(self.get_applied_migrations())
        available = self.get_available_migrations()
        
        return [m for m in available if m not in applied]
    
    def apply_migration(self, version: str) -> bool:
        """지정된 버전의 마이그레이션을 적용합니다.
        
        Args:
            version: 마이그레이션 버전
            
        Returns:
            bool: 마이그레이션 적용 성공 여부
        """
        try:
            # 마이그레이션 모듈 로드
            module_path = f"{self.migrations_path.replace('/', '.')}.{version}"
            module = importlib.import_module(module_path)
            
            # 마이그레이션 실행
            if hasattr(module, 'upgrade') and callable(module.upgrade):
                session = self.db_manager.get_session()
                try:
                    # 마이그레이션 함수 실행
                    module.upgrade(session)
                    
                    # 마이그레이션 기록 추가
                    engine = self.db_manager.get_engine()
                    query = f"INSERT INTO {self.MIGRATION_TABLE} (version, applied_at) VALUES (:version, :applied_at)"
                    with engine.connect() as conn:
                        conn.execute(
                            text(query),
                            {"version": version, "applied_at": datetime.utcnow()}
                        )
                        conn.commit()
                    
                    logger.info(f"마이그레이션 '{version}'이 성공적으로 적용되었습니다.")
                    return True
                except Exception as e:
                    session.rollback()
                    logger.exception(f"마이그레이션 '{version}' 적용 중 오류가 발생했습니다: {e}")
                    return False
                finally:
                    session.close()
            else:
                logger.error(f"마이그레이션 '{version}'에 'upgrade' 함수가 없습니다.")
                return False
        except ImportError as e:
            logger.error(f"마이그레이션 '{version}' 모듈을 로드할 수 없습니다: {e}")
            return False
    
    def migrate(self) -> bool:
        """모든 보류 중인 마이그레이션을 적용합니다.
        
        Returns:
            bool: 모든 마이그레이션 적용 성공 여부
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("적용할 마이그레이션이 없습니다.")
            return True
        
        success = True
        for version in pending:
            if not self.apply_migration(version):
                success = False
                break
        
        return success
    
    def create_migration(self, name: str) -> str:
        """새 마이그레이션 스크립트를 생성합니다.
        
        Args:
            name: 마이그레이션 이름
            
        Returns:
            str: 생성된 마이그레이션 파일 경로
        """
        # 마이그레이션 디렉토리 생성
        os.makedirs(self.migrations_path, exist_ok=True)
        
        # 버전 생성 (현재 시간 기반)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version = f"v{timestamp}_{name}"
        
        # 마이그레이션 파일 경로
        file_path = os.path.join(self.migrations_path, f"{version}.py")
        
        # 마이그레이션 템플릿
        template = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
마이그레이션: {name}

생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from sqlalchemy.orm import Session
from sqlalchemy import text

def upgrade(session: Session):
    """마이그레이션을 적용합니다."""
    # 여기에 마이그레이션 코드를 작성하세요
    pass

def downgrade(session: Session):
    """마이그레이션을 롤백합니다."""
    # 여기에 롤백 코드를 작성하세요
    pass
'''
        
        # 파일 작성
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        logger.info(f"마이그레이션 '{version}'이 생성되었습니다: {file_path}")
        return file_path