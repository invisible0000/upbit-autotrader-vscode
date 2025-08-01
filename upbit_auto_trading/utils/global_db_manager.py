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

# database_paths 모듈 import
try:
    from upbit_auto_trading.config.database_paths import get_current_config, TableMappings
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    # 백업용 더미 클래스
    class TableMappings:
        SETTINGS_TABLES = {}
        STRATEGIES_TABLES = {}
        MARKET_DATA_TABLES = {}
    
    def get_current_config():
        return {
            'settings_db': 'upbit_auto_trading/data/settings.sqlite3',
            'strategies_db': 'upbit_auto_trading/data/strategies.sqlite3',
            'market_data_db': 'upbit_auto_trading/data/market_data.sqlite3'
        }

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
        """database_paths.py에서 경로 설정 로드"""
        if CONFIG_AVAILABLE:
            self._load_from_database_paths()
        else:
            self._load_fallback_config()
        
    def _load_from_database_paths(self):
        """database_paths.py에서 설정 로드"""
        try:
            config = get_current_config()
            
            self._db_paths = {
                'settings': Path(config['settings_db']),
                'strategies': Path(config['strategies_db']),
                'market_data': Path(config['market_data_db'])
            }
            
            print("✅ [DEBUG] database_paths.py에서 설정 로드 완료")
            print(f"   Settings DB: {self._db_paths['settings']}")
            print(f"   Strategies DB: {self._db_paths['strategies']}")
            print(f"   Market Data DB: {self._db_paths['market_data']}")
            
            # 테이블 매핑도 생성
            self._create_table_mappings()
            
        except Exception as e:
            print(f"❌ [ERROR] database_paths.py 설정 로드 실패: {e}")
            self._load_fallback_config()
    
    def _load_fallback_config(self):
        """백업용 기본 설정"""
        base_dir = Path(__file__).parent.parent
        default_data_dir = base_dir / "data"
        
        self._db_paths = {
            'settings': default_data_dir / "settings.sqlite3",
            'strategies': default_data_dir / "strategies.sqlite3",
            'market_data': default_data_dir / "market_data.sqlite3"
        }
        
        print(f"⚠️ [WARNING] 백업용 기본 설정 사용")
        
        # 테이블 매핑 생성
        self._create_table_mappings()
        
    def reload_configuration(self):
        """설정을 다시 로드하고 연결을 초기화"""
        print("데이터베이스 설정을 다시 로드합니다...")
        
        # 기존 연결 모두 종료
        self.close_all_connections()
        
        # 설정 다시 로드
        self._initialize_paths()
        
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
                except Exception:
                    pass
            self._connections.clear()
            print("모든 데이터베이스 연결이 종료되었습니다.")
            
    def _create_connection(self, db_path: str) -> sqlite3.Connection:
        """개별 데이터베이스 연결 생성 (외부 호출용)"""
        return sqlite3.connect(db_path, check_same_thread=False)
    
    def _create_table_mappings(self):
        """테이블 → DB 매핑 생성"""
        if CONFIG_AVAILABLE:
            # database_paths.py의 TableMappings 사용
            self._table_mappings = {}
            
            # Settings DB 테이블들
            for table, _ in TableMappings.SETTINGS_TABLES.items():
                self._table_mappings[table] = 'settings'
            
            # Strategies DB 테이블들
            for table, _ in TableMappings.STRATEGIES_TABLES.items():
                self._table_mappings[table] = 'strategies'
            
            # Market Data DB 테이블들
            for table, _ in TableMappings.MARKET_DATA_TABLES.items():
                self._table_mappings[table] = 'market_data'
                
            print(f"✅ database_paths.py에서 테이블 매핑 로드 완료 ({len(self._table_mappings)}개 테이블)")
        else:
            # 백업용 기본 매핑
            self._table_mappings = {
                # Settings DB 테이블들 (설정 및 변수 정의)
                'chart_variables': 'settings',
                'component_strategy': 'settings', 
                'tv_trading_variables': 'settings',
                'tv_comparison_groups': 'settings',
                'tv_schema_version': 'settings',
                
                # Strategies DB 테이블들 (사용자 생성 데이터)
                'trading_conditions': 'strategies',  # 🔧 strategies DB로 수정
                'strategies': 'strategies',
                'strategy_execution': 'strategies',
                'migration_info': 'strategies',
                
                # Market Data DB 테이블들
                'market_data': 'market_data',
                'ohlcv_data': 'market_data',
                'backtest_results': 'market_data',
                'portfolios': 'market_data'
            }
            print(f"⚠️ 백업용 테이블 매핑 사용 ({len(self._table_mappings)}개 테이블)")
            print(f"   📊 trading_conditions → strategies DB 매핑 확인")
        
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
        
        # 새 경로로 DB 경로 업데이트
        new_data_dir = Path(new_path)
        self._db_paths = {
            'settings': new_data_dir / "settings.sqlite3",
            'strategies': new_data_dir / "strategies.sqlite3",
            'market_data': new_data_dir / "market_data.sqlite3"
        }
        
        print(f"📂 데이터 디렉토리 변경: {new_data_dir}")
        print(f"   Settings DB: {self._db_paths['settings']}")
        print(f"   Strategies DB: {self._db_paths['strategies']}")
        print(f"   Market Data DB: {self._db_paths['market_data']}")

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
