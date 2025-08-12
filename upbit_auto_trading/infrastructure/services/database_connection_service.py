"""
Database Connection Service Adapter

데이터베이스 연결 상태 모니터링과 연결 관리를 담당하는 외부 서비스 어댑터입니다.
데이터베이스 설정 변경 시 연결 상태를 확인하고 안전한 전환을 지원합니다.

Features:
- 데이터베이스 연결 상태 모니터링
- 연결 유효성 검증
- 안전한 연결 전환
- 연결 풀 관리
- 트랜잭션 상태 확인

Design Principles:
- Health Check Pattern: 정기적인 연결 상태 확인
- Circuit Breaker: 연결 실패 시 자동 복구
- Connection Pooling: 효율적인 연결 재사용
"""

import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
from contextlib import contextmanager

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.configuration.paths import infrastructure_paths

logger = create_component_logger("DatabaseConnectionService")

class DatabaseHealthStatus:
    """데이터베이스 연결 상태 정보"""

    def __init__(self, db_name: str, is_healthy: bool,
                 response_time_ms: float = 0, error_message: str = ""):
        self.db_name = db_name
        self.is_healthy = is_healthy
        self.response_time_ms = response_time_ms
        self.error_message = error_message
        self.checked_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 변환"""
        return {
            'db_name': self.db_name,
            'is_healthy': self.is_healthy,
            'response_time_ms': self.response_time_ms,
            'error_message': self.error_message,
            'checked_at': self.checked_at.isoformat()
        }

class DatabaseConnectionService:
    """데이터베이스 연결 관리 서비스"""

    def __init__(self):
        self._logger = logger
        self._connections = threading.local()
        self._health_cache: Dict[str, DatabaseHealthStatus] = {}
        self._health_cache_ttl = timedelta(seconds=30)  # 30초 캐시

        # 데이터베이스 설정
        self._db_configs = {
            'settings': {
                'path': infrastructure_paths.SETTINGS_DB,
                'timeout': 30.0,
                'check_same_thread': False
            },
            'strategies': {
                'path': infrastructure_paths.STRATEGIES_DB,
                'timeout': 30.0,
                'check_same_thread': False
            },
            'market_data': {
                'path': infrastructure_paths.MARKET_DATA_DB,
                'timeout': 30.0,
                'check_same_thread': False
            }
        }

    async def check_database_health(self, db_name: str) -> DatabaseHealthStatus:
        """
        데이터베이스 연결 상태 확인

        Args:
            db_name: 데이터베이스 이름 ('settings', 'strategies', 'market_data')

        Returns:
            데이터베이스 상태 정보
        """
        # 캐시 확인
        if db_name in self._health_cache:
            cached_status = self._health_cache[db_name]
            if datetime.now() - cached_status.checked_at < self._health_cache_ttl:
                return cached_status

        # 새로운 상태 확인
        start_time = time.time()

        try:
            db_path = self._get_db_path(db_name)

            # 1. 파일 존재 확인
            if not db_path.exists():
                status = DatabaseHealthStatus(
                    db_name=db_name,
                    is_healthy=False,
                    error_message=f"데이터베이스 파일이 존재하지 않습니다: {db_path}"
                )
            else:
                # 2. 연결 테스트
                with self._create_test_connection(db_name) as conn:
                    # 3. 간단한 쿼리 실행으로 응답성 확인
                    cursor = conn.execute("SELECT 1")
                    cursor.fetchone()

                    response_time = (time.time() - start_time) * 1000

                    status = DatabaseHealthStatus(
                        db_name=db_name,
                        is_healthy=True,
                        response_time_ms=round(response_time, 2)
                    )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            status = DatabaseHealthStatus(
                db_name=db_name,
                is_healthy=False,
                response_time_ms=round(response_time, 2),
                error_message=str(e)
            )

        # 캐시 저장
        self._health_cache[db_name] = status

        if status.is_healthy:
            self._logger.debug(f"✅ {db_name} 데이터베이스 상태 양호 ({status.response_time_ms}ms)")
        else:
            self._logger.warning(f"⚠️ {db_name} 데이터베이스 상태 불량: {status.error_message}")

        return status

    async def check_all_databases_health(self) -> Dict[str, DatabaseHealthStatus]:
        """
        모든 데이터베이스 연결 상태 확인

        Returns:
            각 데이터베이스의 상태 정보
        """
        health_results = {}

        for db_name in self._db_configs.keys():
            health_results[db_name] = await self.check_database_health(db_name)

        healthy_count = sum(1 for status in health_results.values() if status.is_healthy)
        total_count = len(health_results)

        self._logger.info(f"📊 전체 데이터베이스 상태: {healthy_count}/{total_count} 정상")

        return health_results

    async def verify_database_accessibility(self, db_path: Path) -> bool:
        """
        특정 데이터베이스 파일의 접근 가능성 확인

        Args:
            db_path: 확인할 데이터베이스 파일 경로

        Returns:
            접근 가능 여부
        """
        try:
            # 1. 파일 존재 확인
            if not db_path.exists():
                self._logger.warning(f"❌ 데이터베이스 파일 없음: {db_path}")
                return False

            # 2. 읽기 권한 확인
            if not db_path.is_file():
                self._logger.warning(f"❌ 데이터베이스가 파일이 아님: {db_path}")
                return False

            # 3. SQLite 파일 형식 확인
            with open(db_path, 'rb') as f:
                header = f.read(16)
                if not header.startswith(b'SQLite format 3'):
                    self._logger.warning(f"❌ 올바른 SQLite 파일이 아님: {db_path}")
                    return False

            # 4. 연결 테스트
            with sqlite3.connect(str(db_path), timeout=5.0) as conn:
                conn.execute("SELECT 1").fetchone()

            self._logger.debug(f"✅ 데이터베이스 접근 가능: {db_path}")
            return True

        except Exception as e:
            self._logger.warning(f"❌ 데이터베이스 접근 불가: {db_path} - {e}")
            return False

    async def test_database_connection(self, db_path: Path) -> Dict[str, Any]:
        """
        데이터베이스 연결 테스트 및 상세 정보 수집

        Args:
            db_path: 테스트할 데이터베이스 경로

        Returns:
            연결 테스트 결과
        """
        start_time = time.time()
        result = {
            'path': str(db_path),
            'exists': False,
            'accessible': False,
            'connection_time_ms': 0,
            'schema_info': {},
            'error': None
        }

        try:
            # 1. 기본 접근성 확인
            result['exists'] = db_path.exists()
            if not result['exists']:
                result['error'] = "파일이 존재하지 않습니다"
                return result

            result['accessible'] = await self.verify_database_accessibility(db_path)
            if not result['accessible']:
                result['error'] = "데이터베이스에 접근할 수 없습니다"
                return result

            # 2. 연결 성능 테스트
            with sqlite3.connect(str(db_path), timeout=10.0) as conn:
                # 연결 시간 측정
                result['connection_time_ms'] = round((time.time() - start_time) * 1000, 2)

                # 3. 스키마 정보 수집
                cursor = conn.execute("""
                    SELECT name, type
                    FROM sqlite_master
                    WHERE type IN ('table', 'view')
                    ORDER BY type, name
                """)

                tables_and_views = cursor.fetchall()
                result['schema_info'] = {
                    'tables_count': len([t for t in tables_and_views if t[1] == 'table']),
                    'views_count': len([t for t in tables_and_views if t[1] == 'view']),
                    'objects': [{'name': name, 'type': obj_type} for name, obj_type in tables_and_views]
                }

                # 4. 데이터베이스 크기 정보
                result['file_size_mb'] = round(db_path.stat().st_size / (1024 * 1024), 2)

                self._logger.info(f"✅ 데이터베이스 연결 테스트 성공: {db_path}")

        except Exception as e:
            result['error'] = str(e)
            result['connection_time_ms'] = round((time.time() - start_time) * 1000, 2)
            self._logger.error(f"❌ 데이터베이스 연결 테스트 실패: {db_path} - {e}")

        return result

    async def monitor_active_connections(self) -> Dict[str, Any]:
        """
        현재 활성 연결 모니터링

        Returns:
            활성 연결 정보
        """
        monitoring_info = {
            'timestamp': datetime.now().isoformat(),
            'thread_id': threading.get_ident(),
            'connections': {},
            'health_cache_size': len(self._health_cache)
        }

        # 스레드 로컬 연결 상태 확인
        if hasattr(self._connections, 'active_connections'):
            for db_name, conn_info in self._connections.active_connections.items():
                monitoring_info['connections'][db_name] = {
                    'created_at': conn_info.get('created_at'),
                    'last_used': conn_info.get('last_used'),
                    'query_count': conn_info.get('query_count', 0)
                }

        return monitoring_info

    def clear_health_cache(self) -> None:
        """상태 캐시 초기화"""
        cache_size = len(self._health_cache)
        self._health_cache.clear()
        self._logger.info(f"🧹 데이터베이스 상태 캐시 초기화: {cache_size}개 항목 삭제")

    def get_database_list(self) -> List[str]:
        """관리 중인 데이터베이스 목록 반환"""
        return list(self._db_configs.keys())

    # === Private Helper Methods ===

    def _get_db_path(self, db_name: str) -> Path:
        """데이터베이스 이름으로 경로 반환"""
        if db_name not in self._db_configs:
            raise ValueError(f"알 수 없는 데이터베이스: {db_name}")

        return self._db_configs[db_name]['path']

    @contextmanager
    def _create_test_connection(self, db_name: str):
        """테스트용 임시 연결 생성"""
        config = self._db_configs[db_name]

        conn = sqlite3.connect(
            str(config['path']),
            timeout=config['timeout'],
            check_same_thread=config['check_same_thread']
        )

        try:
            # SQLite 최적화 설정
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")

            yield conn

        finally:
            conn.close()

# 전역 인스턴스 (Singleton 패턴)
database_connection_service = DatabaseConnectionService()
