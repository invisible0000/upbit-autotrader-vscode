#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터베이스 관리자

데이터베이스 연결 및 관리를 담당합니다.
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from upbit_auto_trading.data_layer.models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """데이터베이스 연결 및 관리를 담당하는 클래스"""
    
    def __init__(self, config_path: str = None, config: Dict = None):
        """DatabaseManager 초기화
        
        Args:
            config_path: 설정 파일 경로 (config가 None인 경우 사용)
            config: 설정 정보 (직접 전달 시 config_path 무시)
        """
        self.engine = None
        self.session_factory = None
        
        if config:
            self.config = config
        elif config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            # 기본 설정
            self.config = {
                'database': {
                    'type': 'sqlite',
                    'path': 'data/upbit_auto_trading.sqlite3'
                }
            }
            logger.warning("설정 파일을 찾을 수 없어 기본 설정을 사용합니다.")
        
        # 데이터 디렉토리 생성
        Path('data').mkdir(exist_ok=True)
        
        # 데이터베이스 연결 설정
        self._setup_connection()
    
    def _setup_connection(self):
        """데이터베이스 연결을 설정합니다."""
        db_config = self.config['database']
        db_type = db_config['type'].lower()
        
        try:
            if db_type == 'sqlite':
                db_path = db_config.get('path', 'data/upbit_auto_trading.db')
                connection_string = f"sqlite:///{db_path}"
                
                # SQLite 연결 설정
                self.engine = create_engine(
                    connection_string,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30  # 연결 타임아웃 (초)
                    },
                    # SQLite는 풀링이 필요 없음
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=3600
                )
            elif db_type == 'mysql':
                host = db_config.get('host', 'localhost')
                port = db_config.get('port', 3306)
                username = db_config.get('username', 'root')
                password = db_config.get('password', '')
                database_name = db_config.get('database_name', 'upbit_auto_trading')
                
                # 연결 옵션 설정
                connect_args = {
                    'charset': 'utf8mb4',
                    'connect_timeout': 30,  # 연결 타임아웃 (초)
                    'read_timeout': 30,     # 읽기 타임아웃 (초)
                    'write_timeout': 30     # 쓰기 타임아웃 (초)
                }
                
                # MySQL 연결 문자열 생성
                connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_name}"
                
                # MySQL 연결 설정
                self.engine = create_engine(
                    connection_string,
                    connect_args=connect_args,
                    pool_size=10,           # 풀 크기
                    max_overflow=20,        # 최대 초과 연결 수
                    pool_timeout=30,        # 풀 타임아웃 (초)
                    pool_recycle=3600,      # 연결 재활용 시간 (초)
                    pool_pre_ping=True      # 연결 유효성 검사
                )
            elif db_type == 'postgresql':
                host = db_config.get('host', 'localhost')
                port = db_config.get('port', 5432)
                username = db_config.get('username', 'postgres')
                password = db_config.get('password', '')
                database_name = db_config.get('database_name', 'upbit_auto_trading')
                
                # 연결 옵션 설정
                connect_args = {
                    'connect_timeout': 30,  # 연결 타임아웃 (초)
                    'application_name': 'upbit_auto_trading'
                }
                
                # PostgreSQL 연결 문자열 생성
                connection_string = f"postgresql://{username}:{password}@{host}:{port}/{database_name}"
                
                # PostgreSQL 연결 설정
                self.engine = create_engine(
                    connection_string,
                    connect_args=connect_args,
                    pool_size=10,           # 풀 크기
                    max_overflow=20,        # 최대 초과 연결 수
                    pool_timeout=30,        # 풀 타임아웃 (초)
                    pool_recycle=3600,      # 연결 재활용 시간 (초)
                    pool_pre_ping=True      # 연결 유효성 검사
                )
            else:
                raise ValueError(f"지원하지 않는 데이터베이스 유형입니다: {db_type}")
            
            # 세션 팩토리 생성
            self.session_factory = sessionmaker(bind=self.engine)
            
            logger.info(f"데이터베이스 연결이 설정되었습니다. (유형: {db_type})")
        
        except Exception as e:
            logger.exception(f"데이터베이스 연결 설정 중 오류가 발생했습니다: {e}")
            raise
    
    def get_engine(self) -> Engine:
        """SQLAlchemy 엔진을 반환합니다.
        
        Returns:
            Engine: SQLAlchemy 엔진
        """
        return self.engine
    
    def get_session(self) -> Session:
        """새 SQLAlchemy 세션을 생성하여 반환합니다.
        
        Returns:
            Session: SQLAlchemy 세션
        """
        if not self.session_factory:
            raise RuntimeError("세션 팩토리가 초기화되지 않았습니다.")
        return self.session_factory()
    
    def initialize_database(self):
        """데이터베이스 스키마를 초기화합니다."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("데이터베이스 스키마가 초기화되었습니다.")
        except Exception as e:
            logger.exception(f"데이터베이스 스키마 초기화 중 오류가 발생했습니다: {e}")
            raise
    
    def cleanup_database(self):
        """데이터베이스 연결을 정리합니다."""
        if self.engine:
            self.engine.dispose()
            logger.info("데이터베이스 연결이 정리되었습니다.")

# 싱글톤 인스턴스
_instance = None

def get_database_manager(config_path: str = None, config: Dict = None) -> DatabaseManager:
    """DatabaseManager의 싱글톤 인스턴스를 반환합니다.
    
    Args:
        config_path: 설정 파일 경로 (config가 None인 경우 사용)
        config: 설정 정보 (직접 전달 시 config_path 무시)
        
    Returns:
        DatabaseManager: DatabaseManager 인스턴스
    """
    global _instance
    if _instance is None:
        _instance = DatabaseManager(config_path, config)
    return _instance