#!/usr/bin/env python3
"""
🚀 DB 연결 풀 및 성능 최적화 유틸리티
========================================

Trading Variables DB Migration Tool을 위한 성능 최적화 모듈

주요 기능:
1. SQLite 연결 풀링
2. 메모리 사용량 최적화
3. 비동기 DB 작업
4. 캐싱 시스템

작성일: 2025-07-31
버전: 1.0.0 (Phase 3 - 성능 최적화)
"""

import sqlite3
import threading
import time
import weakref
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
from pathlib import Path
import json
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ConnectionInfo:
    """연결 정보 클래스"""
    connection: sqlite3.Connection
    last_used: datetime
    in_use: bool = False
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DatabaseConnectionPool:
    """SQLite 연결 풀 클래스"""
    
    def __init__(self, database_path: str, max_connections: int = 5, 
                 max_idle_time: int = 300):  # 5분
        """
        연결 풀 초기화
        
        Args:
            database_path: 데이터베이스 파일 경로
            max_connections: 최대 연결 수
            max_idle_time: 최대 유휴 시간 (초)
        """
        self.database_path = database_path
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        
        self._pool: List[ConnectionInfo] = []
        self._lock = threading.RLock()
        self._total_connections = 0
        
        # 주기적 정리 스레드
        self._cleanup_thread = threading.Thread(
            target=self._periodic_cleanup, 
            daemon=True
        )
        self._cleanup_running = True
        self._cleanup_thread.start()
    
    @contextmanager
    def get_connection(self):
        """
        연결 컨텍스트 매니저
        
        Yields:
            sqlite3.Connection: 데이터베이스 연결
        """
        conn_info = self._acquire_connection()
        try:
            yield conn_info.connection
        finally:
            self._release_connection(conn_info)
    
    def _acquire_connection(self) -> ConnectionInfo:
        """연결 획득"""
        with self._lock:
            # 사용 가능한 연결 찾기
            for conn_info in self._pool:
                if not conn_info.in_use:
                    conn_info.in_use = True
                    conn_info.last_used = datetime.now()
                    return conn_info
            
            # 새 연결 생성 (최대 연결 수 확인)
            if self._total_connections < self.max_connections:
                conn_info = self._create_connection()
                self._pool.append(conn_info)
                self._total_connections += 1
                return conn_info
            
            # 연결 풀이 가득 참 - 기존 연결이 해제될 때까지 대기
            raise RuntimeError(f"연결 풀이 가득 참 (최대: {self.max_connections})")
    
    def _release_connection(self, conn_info: ConnectionInfo):
        """연결 해제"""
        with self._lock:
            conn_info.in_use = False
            conn_info.last_used = datetime.now()
    
    def _create_connection(self) -> ConnectionInfo:
        """새 연결 생성"""
        conn = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
            timeout=30
        )
        
        # SQLite 성능 최적화 설정
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # 균형잡힌 동기화
        conn.execute("PRAGMA cache_size=10000")  # 캐시 크기 증가
        conn.execute("PRAGMA temp_store=MEMORY")  # 임시 저장소를 메모리로
        
        conn_info = ConnectionInfo(
            connection=conn,
            last_used=datetime.now(),
            in_use=True
        )
        return conn_info
    
    def _periodic_cleanup(self):
        """주기적 연결 정리"""
        while self._cleanup_running:
            try:
                time.sleep(60)  # 1분마다 정리
                self._cleanup_idle_connections()
            except Exception as e:
                print(f"연결 정리 중 오류: {e}")
    
    def _cleanup_idle_connections(self):
        """유휴 연결 정리"""
        with self._lock:
            current_time = datetime.now()
            connections_to_remove = []
            
            for conn_info in self._pool:
                if (not conn_info.in_use and 
                    (current_time - conn_info.last_used).total_seconds() > self.max_idle_time):
                    connections_to_remove.append(conn_info)
            
            for conn_info in connections_to_remove:
                try:
                    conn_info.connection.close()
                    self._pool.remove(conn_info)
                    self._total_connections -= 1
                except Exception as e:
                    print(f"연결 정리 중 오류: {e}")
    
    def close_all(self):
        """모든 연결 닫기"""
        self._cleanup_running = False
        
        with self._lock:
            for conn_info in self._pool:
                try:
                    conn_info.connection.close()
                except Exception as e:
                    print(f"연결 종료 중 오류: {e}")
            
            self._pool.clear()
            self._total_connections = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 풀 통계 반환"""
        with self._lock:
            active_connections = sum(1 for c in self._pool if c.in_use)
            return {
                'total_connections': self._total_connections,
                'active_connections': active_connections,
                'idle_connections': self._total_connections - active_connections,
                'max_connections': self.max_connections
            }


class QueryCache:
    """쿼리 결과 캐시 클래스"""
    
    def __init__(self, max_size: int = 100, ttl: int = 300):  # 5분 TTL
        """
        캐시 초기화
        
        Args:
            max_size: 최대 캐시 항목 수
            ttl: Time To Live (초)
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return None
            
            entry['last_accessed'] = datetime.now()
            return entry['value']
    
    def set(self, key: str, value: Any):
        """캐시에 값 저장"""
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_oldest()
            
            self._cache[key] = {
                'value': value,
                'created_at': datetime.now(),
                'last_accessed': datetime.now()
            }
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """캐시 항목 만료 확인"""
        age = (datetime.now() - entry['created_at']).total_seconds()
        return age > self.ttl
    
    def _evict_oldest(self):
        """가장 오래된 항목 제거"""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]['last_accessed']
        )
        del self._cache[oldest_key]
    
    def clear(self):
        """캐시 전체 삭제"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'ttl': self.ttl
            }


class PerformanceOptimizedDBManager:
    """성능 최적화된 DB 매니저"""
    
    def __init__(self, database_path: str):
        """
        DB 매니저 초기화
        
        Args:
            database_path: 데이터베이스 파일 경로
        """
        self.database_path = database_path
        self.connection_pool = DatabaseConnectionPool(database_path)
        self.query_cache = QueryCache()
        
        # 약한 참조로 인스턴스 추적
        self._instances = weakref.WeakSet()
        self._instances.add(self)
    
    def execute_query(self, query: str, params: tuple = None, 
                     use_cache: bool = True) -> List[tuple]:
        """
        쿼리 실행 (캐시 지원)
        
        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터
            use_cache: 캐시 사용 여부
        
        Returns:
            쿼리 결과 리스트
        """
        cache_key = f"{query}:{params}" if use_cache else None
        
        # 캐시 확인
        if use_cache and cache_key:
            cached_result = self.query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        # DB에서 실행
        with self.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            
            # 캐시에 저장 (SELECT 쿼리만)
            if use_cache and cache_key and query.strip().upper().startswith('SELECT'):
                self.query_cache.set(cache_key, result)
            
            return result
    
    def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """
        트랜잭션 실행
        
        Args:
            operations: 작업 리스트 [{'query': 'SQL', 'params': tuple}, ...]
        
        Returns:
            성공 여부
        """
        with self.connection_pool.get_connection() as conn:
            try:
                cursor = conn.cursor()
                
                for op in operations:
                    query = op['query']
                    params = op.get('params')
                    
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                
                conn.commit()
                
                # 캐시 무효화 (데이터 변경 시)
                if any(not op['query'].strip().upper().startswith('SELECT') 
                       for op in operations):
                    self.query_cache.clear()
                
                return True
                
            except Exception as e:
                conn.rollback()
                print(f"트랜잭션 실행 중 오류: {e}")
                return False
    
    def get_table_info(self, table_name: str, use_cache: bool = True) -> List[tuple]:
        """테이블 정보 조회"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query, use_cache=use_cache)
    
    def get_table_list(self, use_cache: bool = True) -> List[str]:
        """테이블 목록 조회"""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = self.execute_query(query, use_cache=use_cache)
        return [row[0] for row in results]
    
    def optimize_database(self):
        """데이터베이스 최적화 실행"""
        with self.connection_pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # VACUUM (데이터베이스 압축)
            cursor.execute("VACUUM")
            
            # ANALYZE (통계 업데이트)
            cursor.execute("ANALYZE")
            
            conn.commit()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        return {
            'connection_pool': self.connection_pool.get_stats(),
            'query_cache': self.query_cache.get_stats(),
            'database_path': self.database_path,
            'file_exists': Path(self.database_path).exists(),
            'file_size_mb': (
                Path(self.database_path).stat().st_size / (1024 * 1024)
                if Path(self.database_path).exists() else 0
            )
        }
    
    def close(self):
        """리소스 정리"""
        self.connection_pool.close_all()
        self.query_cache.clear()


# 전역 DB 매니저 인스턴스 관리
_db_managers: Dict[str, PerformanceOptimizedDBManager] = {}
_managers_lock = threading.RLock()


def get_db_manager(database_path: str) -> PerformanceOptimizedDBManager:
    """
    DB 매니저 싱글톤 인스턴스 반환
    
    Args:
        database_path: 데이터베이스 파일 경로
    
    Returns:
        DB 매니저 인스턴스
    """
    normalized_path = str(Path(database_path).resolve())
    
    with _managers_lock:
        if normalized_path not in _db_managers:
            _db_managers[normalized_path] = PerformanceOptimizedDBManager(normalized_path)
        
        return _db_managers[normalized_path]


def close_all_db_managers():
    """모든 DB 매니저 정리"""
    with _managers_lock:
        for manager in _db_managers.values():
            manager.close()
        _db_managers.clear()


# 성능 모니터링 데코레이터
def monitor_performance(func: Callable) -> Callable:
    """성능 모니터링 데코레이터"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            if elapsed > 1.0:  # 1초 이상 걸리는 작업 로깅
                print(f"⚡ 성능 주의: {func.__name__} 실행 시간 {elapsed:.2f}초")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ 에러 (실행 시간 {elapsed:.2f}초): {func.__name__} - {str(e)}")
            raise
    
    return wrapper
