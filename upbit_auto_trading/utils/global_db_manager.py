#!/usr/bin/env python3
"""
글로벌 데이터베이스 매니저 - 싱글톤 패턴
모든 DB 연결을 중앙에서 관리하는 전역 매니저
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, Dict
import threading

class DatabaseManager:
    """
    싱글톤 패턴으로 구현된 전역 데이터베이스 매니저
    
    사용법:
        from global_db_manager import db_manager
        
        # 자동으로 올바른 DB에 연결됨
        conn = db_manager.get_connection('trading_conditions')
        conn = db_manager.get_connection('chart_variables') 
        conn = db_manager.get_connection('market_data')
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._connections: Dict[str, sqlite3.Connection] = {}
        self._db_paths = {}
        self._table_mappings = {}
        self._initialize_paths()
        
    def _initialize_paths(self):
        """환경 변수나 설정 파일로부터 DB 경로 초기화"""
        self._load_database_config()
        
    def _load_database_config(self):
        """설정 파일에서 데이터베이스 설정 로드"""
        config_path = "config/database_config.yaml"
        
        # 기본 설정
        base_dir = Path(__file__).parent
        default_data_dir = base_dir / "upbit_auto_trading" / "data"
        
        self._db_paths = {
            'settings': default_data_dir / "settings.sqlite3",
            'strategies': default_data_dir / "strategies.sqlite3", 
            'market_data': default_data_dir / "market_data.sqlite3"
        }
        
        try:
            if os.path.exists(config_path):
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                # 사용자 정의 설정이 활성화된 경우
                if config.get('user_defined', {}).get('active', False):
                    user_config = config['user_defined']
                    if user_config.get('settings_db'):
                        self._db_paths['settings'] = Path(user_config['settings_db'])
                    if user_config.get('strategies_db'):
                        self._db_paths['strategies'] = Path(user_config['strategies_db'])
                    if user_config.get('market_data_db'):
                        self._db_paths['market_data'] = Path(user_config['market_data_db'])
                        
                # 환경별 설정 확인
                env = os.environ.get('UPBIT_ENV', 'development')
                if env in config:
                    env_config = config[env]
                    if not config.get('user_defined', {}).get('active', False):  # 사용자 정의가 비활성화된 경우만
                        for db_type in ['settings', 'strategies', 'market_data']:
                            db_key = f"{db_type}_db"
                            if db_key in env_config:
                                self._db_paths[db_type] = Path(env_config[db_key])
                                
        except Exception as e:
            print(f"데이터베이스 설정 로드 오류 (기본값 사용): {e}")
            
        # 테이블 매핑 생성
        self._create_table_mappings()
        
    def reload_configuration(self):
        """설정 파일을 다시 로드하고 연결을 초기화"""
        print("데이터베이스 설정을 다시 로드합니다...")
        
        # 기존 연결 모두 종료
        self.close_all_connections()
        
        # 설정 다시 로드
        self._load_database_config()
        
        print("데이터베이스 설정이 업데이트되었습니다.")
        print(f"설정 DB: {self._db_paths['settings']}")
        print(f"전략 DB: {self._db_paths['strategies']}")
        print(f"시장데이터 DB: {self._db_paths['market_data']}")
        
    def close_all_connections(self):
        """모든 데이터베이스 연결 종료"""
        with self._lock:
            for conn in self._connections.values():
                try:
                    conn.close()
                except:
                    pass
            self._connections.clear()
            print("모든 데이터베이스 연결이 종료되었습니다.")
            
    def _create_connection(self, db_path: str) -> sqlite3.Connection:
        """개별 데이터베이스 연결 생성 (외부 호출용)"""
        return sqlite3.connect(db_path, check_same_thread=False)
    
    def _create_table_mappings(self):
        """테이블 → DB 매핑 생성"""
        # 테이블 → DB 매핑 (이것만 수정하면 모든 곳에서 자동 적용)
        self._table_mappings = {
            # Settings DB 테이블들
            'trading_conditions': 'settings',
            'chart_variables': 'settings',
            'component_strategy': 'settings',
            'strategies': 'settings',
            'tv_trading_variables': 'settings',
            'tv_comparison_groups': 'settings',
            'tv_schema_version': 'settings',
            
            # Strategies DB 테이블들  
            'strategy_execution': 'strategies',
            'migration_info': 'strategies',
            
            # Market Data DB 테이블들
            'market_data': 'market_data',
            'ohlcv_data': 'market_data',
            'backtest_results': 'market_data',
            'portfolios': 'market_data'
        }
        
    def get_connection(self, table_name: str) -> sqlite3.Connection:
        """
        테이블명을 받아서 적절한 DB 연결을 반환
        
        Args:
            table_name: 접근하려는 테이블명
            
        Returns:
            sqlite3.Connection: 해당 테이블이 있는 DB 연결
        """
        db_name = self._table_mappings.get(table_name)
        
        if not db_name:
            raise ValueError(f"테이블 '{table_name}'에 대한 DB 매핑을 찾을 수 없습니다.")
            
        db_path = self._db_paths[db_name]
        
        # 연결 풀링 - 기존 연결이 있으면 재사용
        connection_key = f"{db_name}_{threading.current_thread().ident}"
        
        if connection_key not in self._connections:
            if not db_path.exists():
                # DB 파일이 없으면 생성
                db_path.parent.mkdir(parents=True, exist_ok=True)
                
            self._connections[connection_key] = sqlite3.connect(
                str(db_path), 
                check_same_thread=False
            )
            
        return self._connections[connection_key]
    
    def get_db_path(self, table_name: str) -> Path:
        """테이블명으로 DB 파일 경로 반환"""
        db_name = self._table_mappings.get(table_name)
        if not db_name:
            raise ValueError(f"테이블 '{table_name}'에 대한 DB 매핑을 찾을 수 없습니다.")
        return self._db_paths[db_name]
        
    def set_data_directory(self, new_path: str):
        """
        데이터 디렉토리 변경 (런타임에 경로 변경 가능)
        
        Args:
            new_path: 새로운 데이터 디렉토리 경로
        """
        self.close_all_connections()
        self.data_dir = Path(new_path)
        self._initialize_paths()
        print(f"📂 데이터 디렉토리 변경: {self.data_dir}")

# 전역 싱글톤 인스턴스
db_manager = DatabaseManager()

# 편의 함수들
def get_db_connection(table_name: str) -> sqlite3.Connection:
    """편의 함수: 테이블명으로 DB 연결 가져오기"""
    return db_manager.get_connection(table_name)

def get_db_path(table_name: str) -> Path:
    """편의 함수: 테이블명으로 DB 경로 가져오기"""
    return db_manager.get_db_path(table_name)

def set_data_dir(new_path: str):
    """편의 함수: 데이터 디렉토리 변경"""
    db_manager.set_data_directory(new_path)
