"""
SQLite 데이터베이스 연결 관리자

다중 SQLite 데이터베이스 연결을 효율적으로 관리하고,
성능 최적화된 쿼리 실행 및 트랜잭션 처리를 제공합니다.

주요 기능:
- Connection Pooling: 데이터베이스별 연결 풀 관리
- 트랜잭션 관리: 원자적 작업 보장
- 동시성 제어: 멀티스레드 환경에서 안전한 접근
- 성능 최적화: WAL 모드, 캐시 설정 등
"""

import sqlite3
from typing import Dict, Optional, List
from contextlib import contextmanager
import logging
from pathlib import Path
import threading


class DatabaseManager:
    """SQLite 데이터베이스 연결 관리"""

    def __init__(self, db_paths: Dict[str, str]):
        """
        Args:
            db_paths: 데이터베이스 이름과 경로 매핑
            예: {
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3',
                'market_data': 'data/market_data.sqlite3'
                # 주의: 미니차트 샘플 DB는 전용 엔진에서 독립 관리
                # 'mini_chart_samples': 'ui/desktop/screens/.../engines/data/sampled_market_data.sqlite3'
            }
        """
        self._db_paths = db_paths
        self._connections: Dict[str, sqlite3.Connection] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)

        # 데이터베이스 연결 풀 초기화
        self._initialize_connections()

    def _initialize_connections(self) -> None:
        """데이터베이스 연결 초기화"""
        for db_name, db_path in self._db_paths.items():
            if not Path(db_path).exists():
                self._logger.warning(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
                continue

            try:
                conn = sqlite3.connect(db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환

                # SQLite 최적화 설정
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA cache_size = 10000")
                conn.execute("PRAGMA temp_store = MEMORY")

                self._connections[db_name] = conn
                self._logger.info(f"데이터베이스 연결 완료: {db_name}")

            except sqlite3.Error as e:
                self._logger.error(f"데이터베이스 연결 실패 {db_name}: {e}")
                raise

    @contextmanager
    def get_connection(self, db_name: str):
        """데이터베이스 연결 반환 (컨텍스트 매니저)"""
        if db_name not in self._connections:
            raise ValueError(f"존재하지 않는 데이터베이스: {db_name}")

        conn = self._connections[db_name]

        try:
            with self._lock:
                yield conn
        except Exception as e:
            self._logger.error(f"데이터베이스 작업 실패 {db_name}: {e}")
            conn.rollback()
            raise
        else:
            conn.commit()

    def execute_query(self, db_name: str, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """SELECT 쿼리 실행"""
        with self.get_connection(db_name) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def execute_command(self, db_name: str, query: str, params: tuple = ()) -> int:
        """INSERT/UPDATE/DELETE 쿼리 실행"""
        with self.get_connection(db_name) as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount

    def execute_many(self, db_name: str, query: str, params_list: List[tuple]) -> int:
        """배치 INSERT/UPDATE 실행"""
        with self.get_connection(db_name) as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount

    def get_last_insert_id(self, db_name: str) -> int:
        """마지막 삽입된 행의 ID 반환"""
        with self.get_connection(db_name) as conn:
            cursor = conn.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]

    def close_all(self) -> None:
        """모든 데이터베이스 연결 종료"""
        for db_name, conn in self._connections.items():
            try:
                conn.close()
                self._logger.info(f"데이터베이스 연결 종료: {db_name}")
            except Exception as e:
                self._logger.error(f"데이터베이스 연결 종료 실패 {db_name}: {e}")

        self._connections.clear()


class DatabaseConnectionProvider:
    """데이터베이스 연결 제공자 (Singleton)"""

    _instance: Optional['DatabaseConnectionProvider'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'DatabaseConnectionProvider':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._db_manager: Optional[DatabaseManager] = None
            self._initialized = True

    def initialize(self, db_paths: Dict[str, str]) -> None:
        """데이터베이스 연결 초기화"""
        if self._db_manager is None:
            self._db_manager = DatabaseManager(db_paths)

    def get_manager(self) -> DatabaseManager:
        """데이터베이스 매니저 반환"""
        if self._db_manager is None:
            raise RuntimeError("데이터베이스가 초기화되지 않았습니다")
        return self._db_manager
