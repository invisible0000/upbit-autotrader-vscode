#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터베이스 백업 관리자

데이터베이스 백업 및 복원을 관리합니다.
"""

import os
import logging
import shutil
import sqlite3
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager
from upbit_auto_trading.utils import ensure_directory

logger = logging.getLogger(__name__)

class BackupManager:
    """데이터베이스 백업 및 복원을 관리하는 클래스"""
    
    def __init__(self, backup_dir: str = 'data/backups'):
        """BackupManager 초기화
        
        Args:
            backup_dir: 백업 파일 저장 디렉토리
        """
        self.backup_dir = backup_dir
        self.db_manager = get_database_manager()
        
        # 백업 디렉토리 생성
        ensure_directory(self.backup_dir)
    
    def backup_sqlite(self, backup_name: Optional[str] = None) -> str:
        """SQLite 데이터베이스를 백업합니다.
        
        Args:
            backup_name: 백업 파일 이름 (없으면 타임스탬프 사용)
            
        Returns:
            str: 백업 파일 경로
        """
        db_config = self.db_manager.config['database']
        
        if db_config['type'].lower() != 'sqlite':
            raise ValueError("이 메서드는 SQLite 데이터베이스만 지원합니다.")
        
        # 데이터베이스 파일 경로
        db_path = db_config.get('path', 'data/upbit_auto_trading.db')
        
        # 백업 파일 이름 생성
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.db"
        
        # 백업 파일 경로
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # 데이터베이스 연결
            source_conn = sqlite3.connect(db_path)
            
            # 백업 수행
            with source_conn:
                source_conn.execute("BEGIN IMMEDIATE")
                shutil.copy2(db_path, backup_path)
            
            logger.info(f"SQLite 데이터베이스가 성공적으로 백업되었습니다: {backup_path}")
            return backup_path
        except Exception as e:
            logger.exception(f"SQLite 데이터베이스 백업 중 오류가 발생했습니다: {e}")
            raise
        finally:
            if 'source_conn' in locals():
                source_conn.close()
    
    def backup_mysql(self, backup_name: Optional[str] = None) -> str:
        """MySQL 데이터베이스를 백업합니다.
        
        Args:
            backup_name: 백업 파일 이름 (없으면 타임스탬프 사용)
            
        Returns:
            str: 백업 파일 경로
        """
        db_config = self.db_manager.config['database']
        
        if db_config['type'].lower() != 'mysql':
            raise ValueError("이 메서드는 MySQL 데이터베이스만 지원합니다.")
        
        # 데이터베이스 연결 정보
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', 3306)
        username = db_config.get('username', 'root')
        password = db_config.get('password', '')
        database_name = db_config.get('database_name', 'upbit_auto_trading')
        
        # 백업 파일 이름 생성
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.sql"
        
        # 백업 파일 경로
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # mysqldump 명령 실행
            cmd = [
                'mysqldump',
                f'--host={host}',
                f'--port={port}',
                f'--user={username}',
                f'--password={password}',
                '--single-transaction',
                '--routines',
                '--triggers',
                '--events',
                database_name
            ]
            
            with open(backup_path, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)
            
            logger.info(f"MySQL 데이터베이스가 성공적으로 백업되었습니다: {backup_path}")
            return backup_path
        except Exception as e:
            logger.exception(f"MySQL 데이터베이스 백업 중 오류가 발생했습니다: {e}")
            raise
    
    def backup_postgresql(self, backup_name: Optional[str] = None) -> str:
        """PostgreSQL 데이터베이스를 백업합니다.
        
        Args:
            backup_name: 백업 파일 이름 (없으면 타임스탬프 사용)
            
        Returns:
            str: 백업 파일 경로
        """
        db_config = self.db_manager.config['database']
        
        if db_config['type'].lower() != 'postgresql':
            raise ValueError("이 메서드는 PostgreSQL 데이터베이스만 지원합니다.")
        
        # 데이터베이스 연결 정보
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', 5432)
        username = db_config.get('username', 'postgres')
        password = db_config.get('password', '')
        database_name = db_config.get('database_name', 'upbit_auto_trading')
        
        # 백업 파일 이름 생성
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.sql"
        
        # 백업 파일 경로
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # 환경 변수 설정
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
            
            # pg_dump 명령 실행
            cmd = [
                'pg_dump',
                f'--host={host}',
                f'--port={port}',
                f'--username={username}',
                '--format=plain',
                '--create',
                '--clean',
                database_name
            ]
            
            with open(backup_path, 'w') as f:
                subprocess.run(cmd, stdout=f, env=env, check=True)
            
            logger.info(f"PostgreSQL 데이터베이스가 성공적으로 백업되었습니다: {backup_path}")
            return backup_path
        except Exception as e:
            logger.exception(f"PostgreSQL 데이터베이스 백업 중 오류가 발생했습니다: {e}")
            raise
    
    def backup(self, backup_name: Optional[str] = None) -> str:
        """데이터베이스 유형에 따라 적절한 백업 메서드를 호출합니다.
        
        Args:
            backup_name: 백업 파일 이름 (없으면 타임스탬프 사용)
            
        Returns:
            str: 백업 파일 경로
        """
        db_type = self.db_manager.config['database']['type'].lower()
        
        if db_type == 'sqlite':
            return self.backup_sqlite(backup_name)
        elif db_type == 'mysql':
            return self.backup_mysql(backup_name)
        elif db_type == 'postgresql':
            return self.backup_postgresql(backup_name)
        else:
            raise ValueError(f"지원하지 않는 데이터베이스 유형입니다: {db_type}")
    
    def restore_sqlite(self, backup_path: str) -> bool:
        """SQLite 데이터베이스를 복원합니다.
        
        Args:
            backup_path: 백업 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        db_config = self.db_manager.config['database']
        
        if db_config['type'].lower() != 'sqlite':
            raise ValueError("이 메서드는 SQLite 데이터베이스만 지원합니다.")
        
        # 데이터베이스 파일 경로
        db_path = db_config.get('path', 'data/upbit_auto_trading.db')
        
        try:
            # 데이터베이스 연결 종료
            self.db_manager.cleanup_database()
            
            # 백업 파일 복사
            shutil.copy2(backup_path, db_path)
            
            # 데이터베이스 재연결
            self.db_manager._setup_connection()
            
            logger.info(f"SQLite 데이터베이스가 성공적으로 복원되었습니다: {backup_path}")
            return True
        except Exception as e:
            logger.exception(f"SQLite 데이터베이스 복원 중 오류가 발생했습니다: {e}")
            
            # 오류 발생 시 재연결 시도
            try:
                self.db_manager._setup_connection()
            except:
                pass
            
            return False
    
    def restore_mysql(self, backup_path: str) -> bool:
        """MySQL 데이터베이스를 복원합니다.
        
        Args:
            backup_path: 백업 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        db_config = self.db_manager.config['database']
        
        if db_config['type'].lower() != 'mysql':
            raise ValueError("이 메서드는 MySQL 데이터베이스만 지원합니다.")
        
        # 데이터베이스 연결 정보
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', 3306)
        username = db_config.get('username', 'root')
        password = db_config.get('password', '')
        database_name = db_config.get('database_name', 'upbit_auto_trading')
        
        try:
            # 데이터베이스 연결 종료
            self.db_manager.cleanup_database()
            
            # mysql 명령 실행
            cmd = [
                'mysql',
                f'--host={host}',
                f'--port={port}',
                f'--user={username}',
                f'--password={password}',
                database_name
            ]
            
            with open(backup_path, 'r') as f:
                subprocess.run(cmd, stdin=f, check=True)
            
            # 데이터베이스 재연결
            self.db_manager._setup_connection()
            
            logger.info(f"MySQL 데이터베이스가 성공적으로 복원되었습니다: {backup_path}")
            return True
        except Exception as e:
            logger.exception(f"MySQL 데이터베이스 복원 중 오류가 발생했습니다: {e}")
            
            # 오류 발생 시 재연결 시도
            try:
                self.db_manager._setup_connection()
            except:
                pass
            
            return False
    
    def restore_postgresql(self, backup_path: str) -> bool:
        """PostgreSQL 데이터베이스를 복원합니다.
        
        Args:
            backup_path: 백업 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        db_config = self.db_manager.config['database']
        
        if db_config['type'].lower() != 'postgresql':
            raise ValueError("이 메서드는 PostgreSQL 데이터베이스만 지원합니다.")
        
        # 데이터베이스 연결 정보
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', 5432)
        username = db_config.get('username', 'postgres')
        password = db_config.get('password', '')
        database_name = db_config.get('database_name', 'upbit_auto_trading')
        
        try:
            # 데이터베이스 연결 종료
            self.db_manager.cleanup_database()
            
            # 환경 변수 설정
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password
            
            # psql 명령 실행
            cmd = [
                'psql',
                f'--host={host}',
                f'--port={port}',
                f'--username={username}',
                '--set', 'ON_ERROR_STOP=on',
                database_name
            ]
            
            with open(backup_path, 'r') as f:
                subprocess.run(cmd, stdin=f, env=env, check=True)
            
            # 데이터베이스 재연결
            self.db_manager._setup_connection()
            
            logger.info(f"PostgreSQL 데이터베이스가 성공적으로 복원되었습니다: {backup_path}")
            return True
        except Exception as e:
            logger.exception(f"PostgreSQL 데이터베이스 복원 중 오류가 발생했습니다: {e}")
            
            # 오류 발생 시 재연결 시도
            try:
                self.db_manager._setup_connection()
            except:
                pass
            
            return False
    
    def restore(self, backup_path: str) -> bool:
        """데이터베이스 유형에 따라 적절한 복원 메서드를 호출합니다.
        
        Args:
            backup_path: 백업 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        db_type = self.db_manager.config['database']['type'].lower()
        
        if db_type == 'sqlite':
            return self.restore_sqlite(backup_path)
        elif db_type == 'mysql':
            return self.restore_mysql(backup_path)
        elif db_type == 'postgresql':
            return self.restore_postgresql(backup_path)
        else:
            raise ValueError(f"지원하지 않는 데이터베이스 유형입니다: {db_type}")
    
    def list_backups(self) -> List[Dict]:
        """사용 가능한 백업 파일 목록을 반환합니다.
        
        Returns:
            List[Dict]: 백업 파일 정보 목록
        """
        backups = []
        
        try:
            # 백업 디렉토리의 모든 파일 검색
            for file_name in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, file_name)
                
                # 파일인 경우만 처리
                if os.path.isfile(file_path):
                    # 파일 정보 수집
                    stat = os.stat(file_path)
                    created_at = datetime.fromtimestamp(stat.st_ctime)
                    size = stat.st_size
                    
                    backups.append({
                        'name': file_name,
                        'path': file_path,
                        'size': size,
                        'created_at': created_at
                    })
            
            # 생성 시간 기준으로 정렬 (최신순)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
        except Exception as e:
            logger.exception(f"백업 목록 조회 중 오류가 발생했습니다: {e}")
            return []