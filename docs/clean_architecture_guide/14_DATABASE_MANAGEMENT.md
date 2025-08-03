# 🗄️ 데이터베이스 관리 가이드

> **목적**: Clean Architecture에서 데이터베이스 구조 변경, 마이그레이션, 성능 최적화 방법  
> **대상**: 개발자, 데이터베이스 관리자  
> **예상 읽기 시간**: 17분

## 🎯 데이터베이스 관리 개요

### 📋 3-DB 아키텍처 관리
1. **settings.sqlite3**: 시스템 구조 및 메타데이터 관리
2. **strategies.sqlite3**: 사용자 전략 및 백테스팅 결과
3. **market_data.sqlite3**: 실시간/과거 시장 데이터

### 🔧 관리 도구
- **스키마 마이그레이션**: 버전 관리와 자동 업그레이드
- **성능 모니터링**: 쿼리 최적화 및 인덱스 관리
- **데이터 정리**: 자동 정리 및 백업 시스템

## 🏗️ 스키마 변경 관리

### 1. 마이그레이션 시스템
```python
# infrastructure/database/migration_manager.py
from typing import List, Dict, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import sqlite3
import json
from datetime import datetime

@dataclass
class MigrationInfo:
    """마이그레이션 정보"""
    version: str
    description: str
    sql_up: str
    sql_down: str
    created_at: datetime

class Migration(ABC):
    """마이그레이션 기본 클래스"""
    
    @abstractmethod
    def get_version(self) -> str:
        """마이그레이션 버전"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """마이그레이션 설명"""
        pass
    
    @abstractmethod
    def up(self, connection: sqlite3.Connection):
        """스키마 업그레이드"""
        pass
    
    @abstractmethod
    def down(self, connection: sqlite3.Connection):
        """스키마 다운그레이드"""
        pass

class DatabaseMigrationManager:
    """데이터베이스 마이그레이션 관리자"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations: List[Migration] = []
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """마이그레이션 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    sql_up TEXT,
                    sql_down TEXT
                )
            """)
    
    def register_migration(self, migration: Migration):
        """마이그레이션 등록"""
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.get_version())
    
    def get_current_version(self) -> Optional[str]:
        """현재 데이터베이스 버전 조회"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_pending_migrations(self) -> List[Migration]:
        """미적용 마이그레이션 목록"""
        current_version = self.get_current_version()
        
        if current_version is None:
            return self.migrations
        
        pending = []
        for migration in self.migrations:
            if migration.get_version() > current_version:
                pending.append(migration)
        
        return pending
    
    def migrate_up(self, target_version: Optional[str] = None) -> List[str]:
        """데이터베이스 업그레이드"""
        pending_migrations = self.get_pending_migrations()
        applied_versions = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN TRANSACTION")
            
            try:
                for migration in pending_migrations:
                    if target_version and migration.get_version() > target_version:
                        break
                    
                    print(f"마이그레이션 적용: {migration.get_version()} - {migration.get_description()}")
                    
                    # 마이그레이션 실행
                    migration.up(conn)
                    
                    # 마이그레이션 기록
                    conn.execute("""
                        INSERT INTO schema_migrations (version, description, sql_up, sql_down)
                        VALUES (?, ?, ?, ?)
                    """, (
                        migration.get_version(),
                        migration.get_description(),
                        self._get_migration_sql_up(migration),
                        self._get_migration_sql_down(migration)
                    ))
                    
                    applied_versions.append(migration.get_version())
                
                conn.execute("COMMIT")
                print(f"마이그레이션 완료: {len(applied_versions)}개 적용")
                
            except Exception as e:
                conn.execute("ROLLBACK")
                print(f"마이그레이션 실패: {str(e)}")
                raise
        
        return applied_versions
    
    def migrate_down(self, target_version: str) -> List[str]:
        """데이터베이스 다운그레이드"""
        current_version = self.get_current_version()
        
        if not current_version or current_version <= target_version:
            print("다운그레이드할 마이그레이션이 없습니다")
            return []
        
        # 롤백할 마이그레이션 찾기
        rollback_migrations = []
        for migration in reversed(self.migrations):
            if migration.get_version() <= current_version and migration.get_version() > target_version:
                rollback_migrations.append(migration)
        
        rolled_back_versions = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN TRANSACTION")
            
            try:
                for migration in rollback_migrations:
                    print(f"마이그레이션 롤백: {migration.get_version()} - {migration.get_description()}")
                    
                    # 롤백 실행
                    migration.down(conn)
                    
                    # 마이그레이션 기록 삭제
                    conn.execute(
                        "DELETE FROM schema_migrations WHERE version = ?",
                        (migration.get_version(),)
                    )
                    
                    rolled_back_versions.append(migration.get_version())
                
                conn.execute("COMMIT")
                print(f"롤백 완료: {len(rolled_back_versions)}개 롤백")
                
            except Exception as e:
                conn.execute("ROLLBACK")
                print(f"롤백 실패: {str(e)}")
                raise
        
        return rolled_back_versions
    
    def _get_migration_sql_up(self, migration: Migration) -> str:
        """마이그레이션 업 SQL 추출"""
        # 실제 구현에서는 migration 객체에서 SQL을 추출
        return "-- Migration SQL UP"
    
    def _get_migration_sql_down(self, migration: Migration) -> str:
        """마이그레이션 다운 SQL 추출"""
        # 실제 구현에서는 migration 객체에서 SQL을 추출
        return "-- Migration SQL DOWN"

# 예시 마이그레이션
class AddTrailingStopToStrategiesMigration(Migration):
    """전략 테이블에 트레일링 스탑 컬럼 추가"""
    
    def get_version(self) -> str:
        return "20240201_001"
    
    def get_description(self) -> str:
        return "전략 테이블에 트레일링 스탑 관련 컬럼 추가"
    
    def up(self, connection: sqlite3.Connection):
        """업그레이드: 컬럼 추가"""
        connection.execute("""
            ALTER TABLE strategies 
            ADD COLUMN trailing_stop_enabled BOOLEAN DEFAULT 0
        """)
        
        connection.execute("""
            ALTER TABLE strategies 
            ADD COLUMN trailing_stop_percentage DECIMAL(5,4) DEFAULT 0.03
        """)
        
        # 인덱스 추가
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_strategies_trailing_stop 
            ON strategies(trailing_stop_enabled) 
            WHERE trailing_stop_enabled = 1
        """)
    
    def down(self, connection: sqlite3.Connection):
        """다운그레이드: 컬럼 제거"""
        # SQLite는 ALTER TABLE DROP COLUMN을 지원하지 않으므로
        # 테이블 재생성이 필요
        connection.execute("""
            CREATE TABLE strategies_backup AS 
            SELECT 
                id, name, description, strategy_type, is_active, 
                created_at, updated_at, last_used_at, use_count, 
                tags, risk_level, expected_return, max_drawdown
            FROM strategies
        """)
        
        connection.execute("DROP TABLE strategies")
        
        connection.execute("""
            CREATE TABLE strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                strategy_type TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                use_count INTEGER DEFAULT 0,
                tags TEXT,
                risk_level INTEGER DEFAULT 3,
                expected_return REAL,
                max_drawdown REAL
            )
        """)
        
        connection.execute("""
            INSERT INTO strategies 
            SELECT * FROM strategies_backup
        """)
        
        connection.execute("DROP TABLE strategies_backup")
```

### 2. 스키마 버전 관리
```python
# infrastructure/database/schema_manager.py
class DatabaseSchemaManager:
    """데이터베이스 스키마 관리자"""
    
    def __init__(self, db_configs: Dict[str, str]):
        """
        Args:
            db_configs: 데이터베이스 설정 딕셔너리
                예: {
                    'settings': 'data/settings.sqlite3',
                    'strategies': 'data/strategies.sqlite3',
                    'market_data': 'data/market_data.sqlite3'
                }
        """
        self.db_configs = db_configs
        self.migration_managers = {}
        
        for db_name, db_path in db_configs.items():
            self.migration_managers[db_name] = DatabaseMigrationManager(db_path)
            self._register_migrations_for_db(db_name)
    
    def _register_migrations_for_db(self, db_name: str):
        """데이터베이스별 마이그레이션 등록"""
        manager = self.migration_managers[db_name]
        
        if db_name == 'strategies':
            manager.register_migration(AddTrailingStopToStrategiesMigration())
            manager.register_migration(AddBacktestResultsTableMigration())
        elif db_name == 'settings':
            manager.register_migration(AddIndicatorCategoriesMigration())
        elif db_name == 'market_data':
            manager.register_migration(AddMarketDataIndexesMigration())
    
    def migrate_all_databases(self) -> Dict[str, List[str]]:
        """모든 데이터베이스 마이그레이션"""
        results = {}
        
        for db_name, manager in self.migration_managers.items():
            print(f"\n=== {db_name} 데이터베이스 마이그레이션 ===")
            try:
                applied_versions = manager.migrate_up()
                results[db_name] = applied_versions
                print(f"✅ {db_name}: {len(applied_versions)}개 마이그레이션 적용")
            except Exception as e:
                print(f"❌ {db_name}: 마이그레이션 실패 - {str(e)}")
                results[db_name] = []
        
        return results
    
    def get_all_database_versions(self) -> Dict[str, Optional[str]]:
        """모든 데이터베이스 버전 조회"""
        versions = {}
        
        for db_name, manager in self.migration_managers.items():
            versions[db_name] = manager.get_current_version()
        
        return versions
    
    def check_schema_health(self) -> Dict[str, Dict]:
        """스키마 건강성 검사"""
        health_report = {}
        
        for db_name, db_path in self.db_configs.items():
            health_report[db_name] = self._check_single_db_health(db_name, db_path)
        
        return health_report
    
    def _check_single_db_health(self, db_name: str, db_path: str) -> Dict:
        """단일 데이터베이스 건강성 검사"""
        health_info = {
            'accessible': False,
            'current_version': None,
            'pending_migrations': 0,
            'table_count': 0,
            'integrity_check': False,
            'file_size_mb': 0
        }
        
        try:
            # 파일 크기 확인
            import os
            if os.path.exists(db_path):
                health_info['file_size_mb'] = round(os.path.getsize(db_path) / 1024 / 1024, 2)
            
            # 데이터베이스 접근 테스트
            with sqlite3.connect(db_path) as conn:
                health_info['accessible'] = True
                
                # 현재 버전
                manager = self.migration_managers[db_name]
                health_info['current_version'] = manager.get_current_version()
                
                # 미적용 마이그레이션
                pending = manager.get_pending_migrations()
                health_info['pending_migrations'] = len(pending)
                
                # 테이블 수
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                )
                health_info['table_count'] = cursor.fetchone()[0]
                
                # 무결성 검사
                cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                health_info['integrity_check'] = integrity_result == 'ok'
                
        except Exception as e:
            health_info['error'] = str(e)
        
        return health_info
```

## 🚀 성능 최적화

### 1. 인덱스 관리
```python
# infrastructure/database/index_manager.py
class DatabaseIndexManager:
    """데이터베이스 인덱스 관리자"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def create_optimal_indexes(self):
        """최적화된 인덱스 생성"""
        with sqlite3.connect(self.db_path) as conn:
            
            # 전략 테이블 인덱스
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_strategies_type_active 
                ON strategies(strategy_type, is_active)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_strategies_last_used 
                ON strategies(last_used_at DESC) 
                WHERE is_active = 1
            """)
            
            # 백테스트 결과 인덱스
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backtest_strategy_date 
                ON backtest_results(strategy_id, start_date, end_date)
            """)
            
            # 시장 데이터 인덱스 (market_data.sqlite3용)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_data_symbol_timestamp 
                ON price_data(symbol, timestamp DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_data_timeframe 
                ON price_data(timeframe, timestamp DESC)
            """)
            
            # 지표 캐시 인덱스
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_indicator_cache_lookup 
                ON indicator_cache(symbol, indicator_name, timestamp DESC)
            """)
    
    def analyze_query_performance(self, query: str) -> Dict:
        """쿼리 성능 분석"""
        with sqlite3.connect(self.db_path) as conn:
            # 쿼리 플랜 분석
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            cursor = conn.execute(explain_query)
            query_plan = cursor.fetchall()
            
            # 실행 시간 측정
            import time
            start_time = time.time()
            conn.execute(query)
            execution_time = time.time() - start_time
            
            return {
                'query': query,
                'execution_time_ms': round(execution_time * 1000, 2),
                'query_plan': query_plan,
                'uses_index': any('USING INDEX' in str(step) for step in query_plan)
            }
    
    def get_index_usage_stats(self) -> List[Dict]:
        """인덱스 사용 통계"""
        with sqlite3.connect(self.db_path) as conn:
            # SQLite는 인덱스 사용 통계를 직접 제공하지 않으므로
            # 시뮬레이션을 통해 확인
            
            cursor = conn.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
            """)
            
            indexes = cursor.fetchall()
            index_stats = []
            
            for index_name, index_sql in indexes:
                # 테이블 추출
                table_name = self._extract_table_name(index_sql)
                
                # 테이블 크기
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                index_stats.append({
                    'index_name': index_name,
                    'table_name': table_name,
                    'table_rows': row_count,
                    'index_sql': index_sql
                })
            
            return index_stats
    
    def _extract_table_name(self, index_sql: str) -> str:
        """인덱스 SQL에서 테이블 이름 추출"""
        if "ON " in index_sql:
            table_part = index_sql.split("ON ")[1]
            table_name = table_part.split("(")[0].strip()
            return table_name
        return "unknown"

# 성능 모니터링
class DatabasePerformanceMonitor:
    """데이터베이스 성능 모니터링"""
    
    def __init__(self, db_configs: Dict[str, str]):
        self.db_configs = db_configs
    
    def generate_performance_report(self) -> Dict:
        """성능 리포트 생성"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'databases': {}
        }
        
        for db_name, db_path in self.db_configs.items():
            report['databases'][db_name] = self._analyze_db_performance(db_path)
        
        return report
    
    def _analyze_db_performance(self, db_path: str) -> Dict:
        """단일 데이터베이스 성능 분석"""
        performance_info = {}
        
        with sqlite3.connect(db_path) as conn:
            # WAL 모드 확인
            cursor = conn.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            performance_info['journal_mode'] = journal_mode
            
            # 캐시 크기
            cursor = conn.execute("PRAGMA cache_size")
            cache_size = cursor.fetchone()[0]
            performance_info['cache_size'] = cache_size
            
            # 페이지 크기
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            performance_info['page_size'] = page_size
            
            # 데이터베이스 크기
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            db_size_mb = (page_count * page_size) / 1024 / 1024
            performance_info['db_size_mb'] = round(db_size_mb, 2)
            
            # 느린 쿼리 테스트
            slow_queries = self._test_common_queries(conn)
            performance_info['query_performance'] = slow_queries
        
        return performance_info
    
    def _test_common_queries(self, connection: sqlite3.Connection) -> List[Dict]:
        """일반적인 쿼리 성능 테스트"""
        test_queries = [
            "SELECT COUNT(*) FROM strategies WHERE is_active = 1",
            "SELECT * FROM strategies ORDER BY last_used_at DESC LIMIT 10",
            "SELECT COUNT(*) FROM backtest_results",
        ]
        
        results = []
        
        for query in test_queries:
            try:
                start_time = time.time()
                cursor = connection.execute(query)
                cursor.fetchall()
                execution_time = time.time() - start_time
                
                results.append({
                    'query': query,
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'status': 'success'
                })
            except Exception as e:
                results.append({
                    'query': query,
                    'execution_time_ms': 0,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
```

### 2. 자동 정리 시스템
```python
# infrastructure/database/cleanup_manager.py
class DatabaseCleanupManager:
    """데이터베이스 정리 관리자"""
    
    def __init__(self, db_configs: Dict[str, str]):
        self.db_configs = db_configs
    
    def run_daily_cleanup(self):
        """일일 정리 작업"""
        print("=== 데이터베이스 일일 정리 시작 ===")
        
        for db_name, db_path in self.db_configs.items():
            print(f"\n{db_name} 정리 중...")
            
            if db_name == 'market_data':
                self._cleanup_market_data(db_path)
            elif db_name == 'strategies':
                self._cleanup_strategy_data(db_path)
            
            # 공통 정리 작업
            self._vacuum_database(db_path)
            self._update_statistics(db_path)
        
        print("\n✅ 데이터베이스 정리 완료")
    
    def _cleanup_market_data(self, db_path: str):
        """시장 데이터 정리"""
        with sqlite3.connect(db_path) as conn:
            # 30일 이상된 분봉 데이터 삭제
            deleted_count = conn.execute("""
                DELETE FROM price_data 
                WHERE timeframe = '1m' 
                AND timestamp < datetime('now', '-30 days')
            """).rowcount
            
            print(f"  - 오래된 분봉 데이터 {deleted_count}개 삭제")
            
            # 7일 이상된 지표 캐시 삭제
            deleted_cache = conn.execute("""
                DELETE FROM indicator_cache 
                WHERE created_at < datetime('now', '-7 days')
            """).rowcount
            
            print(f"  - 오래된 지표 캐시 {deleted_cache}개 삭제")
    
    def _cleanup_strategy_data(self, db_path: str):
        """전략 데이터 정리"""
        with sqlite3.connect(db_path) as conn:
            # 90일 이상 사용되지 않은 비활성 전략의 백테스트 결과 삭제
            deleted_backtests = conn.execute("""
                DELETE FROM backtest_results 
                WHERE strategy_id IN (
                    SELECT id FROM strategies 
                    WHERE is_active = 0 
                    AND (last_used_at IS NULL OR last_used_at < datetime('now', '-90 days'))
                )
            """).rowcount
            
            print(f"  - 오래된 백테스트 결과 {deleted_backtests}개 삭제")
            
            # 실행 로그 정리 (30일 이상)
            deleted_logs = conn.execute("""
                DELETE FROM execution_logs 
                WHERE timestamp < datetime('now', '-30 days')
            """).rowcount
            
            print(f"  - 오래된 실행 로그 {deleted_logs}개 삭제")
    
    def _vacuum_database(self, db_path: str):
        """데이터베이스 압축 및 최적화"""
        with sqlite3.connect(db_path) as conn:
            # 빈 공간 정리
            conn.execute("VACUUM")
            
            # 통계 정보 업데이트
            conn.execute("ANALYZE")
        
        print(f"  - 데이터베이스 VACUUM 완료")
    
    def _update_statistics(self, db_path: str):
        """통계 정보 업데이트"""
        with sqlite3.connect(db_path) as conn:
            conn.execute("ANALYZE")
        
        print(f"  - 통계 정보 업데이트 완료")
    
    def create_backup(self, backup_dir: str = "data/backups") -> Dict[str, str]:
        """데이터베이스 백업 생성"""
        import os
        import shutil
        from datetime import datetime
        
        os.makedirs(backup_dir, exist_ok=True)
        backup_info = {}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for db_name, db_path in self.db_configs.items():
            if os.path.exists(db_path):
                backup_filename = f"{db_name}_{timestamp}.sqlite3"
                backup_path = os.path.join(backup_dir, backup_filename)
                
                shutil.copy2(db_path, backup_path)
                backup_info[db_name] = backup_path
                print(f"✅ {db_name} 백업 완료: {backup_path}")
        
        return backup_info
```

## 🔧 실제 사용 예시

### 1. 마이그레이션 실행
```python
# scripts/run_migration.py
def main():
    """마이그레이션 실행 스크립트"""
    
    # 데이터베이스 설정
    db_configs = {
        'settings': 'data/settings.sqlite3',
        'strategies': 'data/strategies.sqlite3', 
        'market_data': 'data/market_data.sqlite3'
    }
    
    # 스키마 관리자 초기화
    schema_manager = DatabaseSchemaManager(db_configs)
    
    # 현재 버전 확인
    print("=== 현재 데이터베이스 버전 ===")
    versions = schema_manager.get_all_database_versions()
    for db_name, version in versions.items():
        print(f"{db_name}: {version or 'No migrations'}")
    
    # 건강성 검사
    print("\n=== 스키마 건강성 검사 ===")
    health_report = schema_manager.check_schema_health()
    for db_name, health in health_report.items():
        status = "✅" if health['accessible'] and health['integrity_check'] else "❌"
        print(f"{status} {db_name}: {health['table_count']}개 테이블, {health['file_size_mb']}MB")
    
    # 마이그레이션 실행
    print("\n=== 마이그레이션 실행 ===")
    migration_results = schema_manager.migrate_all_databases()
    
    # 결과 요약
    total_applied = sum(len(versions) for versions in migration_results.values())
    print(f"\n🎉 총 {total_applied}개 마이그레이션 완료!")

if __name__ == "__main__":
    main()
```

### 2. 성능 최적화 실행
```python
# scripts/optimize_database.py
def main():
    """데이터베이스 최적화 스크립트"""
    
    db_configs = {
        'settings': 'data/settings.sqlite3',
        'strategies': 'data/strategies.sqlite3',
        'market_data': 'data/market_data.sqlite3'
    }
    
    # 성능 모니터링
    monitor = DatabasePerformanceMonitor(db_configs)
    print("=== 성능 분석 시작 ===")
    
    performance_report = monitor.generate_performance_report()
    
    for db_name, metrics in performance_report['databases'].items():
        print(f"\n📊 {db_name}:")
        print(f"  - 크기: {metrics['db_size_mb']}MB")
        print(f"  - WAL 모드: {metrics['journal_mode']}")
        print(f"  - 캐시 크기: {metrics['cache_size']}")
        
        # 느린 쿼리 확인
        slow_queries = [q for q in metrics['query_performance'] 
                       if q['execution_time_ms'] > 100]
        if slow_queries:
            print(f"  ⚠️ 느린 쿼리 {len(slow_queries)}개 발견")
    
    # 인덱스 최적화
    print("\n=== 인덱스 최적화 ===")
    for db_name, db_path in db_configs.items():
        index_manager = DatabaseIndexManager(db_path)
        index_manager.create_optimal_indexes()
        print(f"✅ {db_name} 인덱스 최적화 완료")
    
    # 정리 작업
    print("\n=== 데이터 정리 ===")
    cleanup_manager = DatabaseCleanupManager(db_configs)
    cleanup_manager.run_daily_cleanup()
    
    print("\n🎉 데이터베이스 최적화 완료!")

if __name__ == "__main__":
    main()
```

## 🔍 다음 단계

- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 데이터베이스 관련 문제 해결
- **[테스팅 전략](16_TESTING_STRATEGY.md)**: 데이터베이스 테스트 방법
- **[모니터링 전략](17_MONITORING_STRATEGY.md)**: 데이터베이스 모니터링

---
**💡 핵심**: "Clean Architecture에서 데이터베이스는 Infrastructure 계층의 책임이며, 체계적인 마이그레이션과 성능 관리로 시스템 안정성을 보장합니다!"
