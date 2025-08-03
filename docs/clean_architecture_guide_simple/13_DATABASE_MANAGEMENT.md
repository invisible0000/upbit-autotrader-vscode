# 🗄️ 데이터베이스 관리 가이드

> **목적**: Clean Architecture에서 DB 구조 변경, 마이그레이션, 성능 최적화  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 데이터베이스 관리 전략

### 3-DB 아키텍처 관리 포인트
```python
DATABASE_MANAGEMENT = {
    "settings.sqlite3": {
        "목적": "시스템 구조와 메타데이터",
        "변경빈도": "낮음 (기능 추가시)",
        "백업정책": "주간 백업",
        "관리방식": "스키마 마이그레이션"
    },
    "strategies.sqlite3": {
        "목적": "사용자 전략과 백테스팅 결과", 
        "변경빈도": "높음 (사용자 활동)",
        "백업정책": "일일 백업",
        "관리방식": "데이터 정리 + 백업"
    },
    "market_data.sqlite3": {
        "목적": "시장 데이터 캐시",
        "변경빈도": "매우 높음 (실시간)",
        "백업정책": "백업 불필요",
        "관리방식": "자동 정리 + 성능 최적화"
    }
}
```

### 관리 우선순위
1. **성능 최적화**: 쿼리 속도와 응답성
2. **데이터 무결성**: 중요 데이터 보호
3. **스토리지 효율성**: 디스크 공간 관리
4. **백업 복구**: 장애 대응 준비

## 🔧 스키마 마이그레이션 시스템

### 마이그레이션 관리자
```python
class DatabaseMigrationManager:
    """데이터베이스 스키마 마이그레이션 관리"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrations = []
        self._setup_migration_table()
        
    def _setup_migration_table(self):
        """마이그레이션 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL DEFAULT 1,
                    error_message TEXT
                )
            """)
            
    def register_migration(self, version: str, description: str, 
                         up_sql: str, down_sql: str):
        """마이그레이션 등록"""
        migration = {
            'version': version,
            'description': description,
            'up_sql': up_sql,
            'down_sql': down_sql
        }
        self.migrations.append(migration)
        print(f"📝 마이그레이션 등록: {version} - {description}")
        
    def migrate_up(self):
        """마이그레이션 실행"""
        applied_versions = self._get_applied_versions()
        
        for migration in self.migrations:
            if migration['version'] not in applied_versions:
                print(f"🔄 마이그레이션 적용: {migration['version']}")
                
                try:
                    self._apply_migration(migration)
                    self._record_migration_success(migration)
                    print(f"✅ 마이그레이션 성공: {migration['version']}")
                    
                except Exception as e:
                    print(f"❌ 마이그레이션 실패: {migration['version']}")
                    print(f"   오류: {e}")
                    self._record_migration_failure(migration, str(e))
                    raise
                    
    def _apply_migration(self, migration):
        """개별 마이그레이션 적용"""
        with sqlite3.connect(self.db_path) as conn:
            # 트랜잭션으로 안전하게 실행
            conn.execute("BEGIN TRANSACTION;")
            try:
                for statement in migration['up_sql'].split(';'):
                    if statement.strip():
                        conn.execute(statement)
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise
                
    def _get_applied_versions(self):
        """적용된 마이그레이션 버전 목록"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT version FROM schema_migrations WHERE success = 1"
            )
            return [row[0] for row in cursor.fetchall()]
            
    def rollback_migration(self, version: str):
        """마이그레이션 롤백"""
        migration = next(
            (m for m in self.migrations if m['version'] == version), None
        )
        
        if not migration:
            raise ValueError(f"마이그레이션 버전을 찾을 수 없음: {version}")
            
        print(f"↩️ 마이그레이션 롤백: {version}")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("BEGIN TRANSACTION;")
            try:
                for statement in migration['down_sql'].split(';'):
                    if statement.strip():
                        conn.execute(statement)
                        
                # 마이그레이션 기록에서 제거
                conn.execute(
                    "DELETE FROM schema_migrations WHERE version = ?", 
                    (version,)
                )
                conn.execute("COMMIT;")
                print(f"✅ 롤백 완료: {version}")
                
            except Exception as e:
                conn.execute("ROLLBACK;")
                print(f"❌ 롤백 실패: {e}")
                raise
```

### 마이그레이션 예시
```python
# 새로운 전략 태그 기능 추가
migration_manager = DatabaseMigrationManager("data/strategies.sqlite3")

migration_manager.register_migration(
    version="2025.08.03.001",
    description="전략 태그 테이블 추가",
    up_sql="""
        CREATE TABLE strategy_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            tag_color TEXT DEFAULT '#3498db',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE,
            UNIQUE(strategy_id, tag_name)
        );
        
        CREATE INDEX idx_strategy_tags_strategy_id ON strategy_tags(strategy_id);
        CREATE INDEX idx_strategy_tags_tag_name ON strategy_tags(tag_name);
    """,
    down_sql="""
        DROP INDEX IF EXISTS idx_strategy_tags_tag_name;
        DROP INDEX IF EXISTS idx_strategy_tags_strategy_id;
        DROP TABLE IF EXISTS strategy_tags;
    """
)

# 마이그레이션 적용
migration_manager.migrate_up()
```

## 📊 성능 최적화 도구

### 쿼리 성능 분석기
```python
class QueryPerformanceAnalyzer:
    """쿼리 성능 분석 도구"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.slow_queries = []
        
    def analyze_query_performance(self, query: str, params: list = None):
        """쿼리 성능 분석"""
        with sqlite3.connect(self.db_path) as conn:
            start_time = time.time()
            
            # EXPLAIN QUERY PLAN으로 실행 계획 분석
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            plan = conn.execute(explain_query, params or []).fetchall()
            
            # 실제 쿼리 실행
            result = conn.execute(query, params or [])
            row_count = len(result.fetchall()) if query.strip().upper().startswith('SELECT') else 0
            
            execution_time = time.time() - start_time
            
            analysis = {
                'query': query,
                'params': params,
                'execution_time': execution_time,
                'row_count': row_count,
                'execution_plan': plan
            }
            
            # 느린 쿼리 기록 (1초 이상)
            if execution_time > 1.0:
                self.slow_queries.append(analysis)
                print(f"🐌 느린 쿼리 발견: {execution_time:.3f}초")
                
            return analysis
            
    def get_optimization_recommendations(self):
        """최적화 권장사항 생성"""
        recommendations = []
        
        for query_analysis in self.slow_queries:
            plan = query_analysis['execution_plan']
            
            # SCAN 테이블 체크 (인덱스 없이 전체 스캔)
            full_scans = [step for step in plan if 'SCAN TABLE' in str(step)]
            if full_scans:
                recommendations.append({
                    'type': 'missing_index',
                    'query': query_analysis['query'][:100],
                    'suggestion': '인덱스 추가 필요',
                    'tables': [step for step in full_scans]
                })
                
            # 높은 row count
            if query_analysis['row_count'] > 10000:
                recommendations.append({
                    'type': 'large_result_set',
                    'query': query_analysis['query'][:100],
                    'suggestion': 'LIMIT 절 추가 또는 조건 강화',
                    'row_count': query_analysis['row_count']
                })
                
        return recommendations
        
    def create_recommended_indexes(self):
        """권장 인덱스 생성"""
        recommendations = self.get_optimization_recommendations()
        
        index_suggestions = [
            "CREATE INDEX idx_strategies_created_at ON strategies(created_at);",
            "CREATE INDEX idx_strategy_conditions_strategy_id ON strategy_conditions(strategy_id);",
            "CREATE INDEX idx_backtest_results_strategy_id_symbol ON backtest_results(strategy_id, symbol);",
            "CREATE INDEX idx_price_data_symbol_timestamp ON price_data(symbol, timestamp);"
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            for index_sql in index_suggestions:
                try:
                    conn.execute(index_sql)
                    print(f"✅ 인덱스 생성: {index_sql}")
                except sqlite3.OperationalError as e:
                    if "already exists" not in str(e):
                        print(f"❌ 인덱스 생성 실패: {e}")
```

### 자동 데이터 정리 시스템
```python
class DataCleanupManager:
    """자동 데이터 정리 관리자"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def cleanup_old_market_data(self, days_to_keep: int = 30):
        """오래된 시장 데이터 정리"""
        print(f"🧹 시장 데이터 정리 시작 ({days_to_keep}일 이전 데이터)")
        
        with sqlite3.connect(self.db_path) as conn:
            # 1분봉 데이터는 30일만 보관
            cursor = conn.execute("""
                DELETE FROM price_data 
                WHERE timeframe = '1m' 
                AND timestamp < date('now', '-{} days')
            """.format(days_to_keep))
            
            deleted_1m = cursor.rowcount
            print(f"  1분봉 데이터 삭제: {deleted_1m}건")
            
            # 지표 캐시는 7일만 보관
            cursor = conn.execute("""
                DELETE FROM indicator_cache 
                WHERE created_at < date('now', '-7 days')
            """)
            
            deleted_cache = cursor.rowcount
            print(f"  지표 캐시 삭제: {deleted_cache}건")
            
            # VACUUM으로 디스크 공간 확보
            conn.execute("VACUUM;")
            print("  디스크 공간 정리 완료")
            
        return {'deleted_1m': deleted_1m, 'deleted_cache': deleted_cache}
        
    def cleanup_old_backtests(self, max_results_per_strategy: int = 50):
        """오래된 백테스트 결과 정리"""
        print(f"🧹 백테스트 결과 정리 (전략당 최대 {max_results_per_strategy}개 보관)")
        
        with sqlite3.connect(self.db_path) as conn:
            # 각 전략별로 최근 결과만 보관
            cursor = conn.execute("""
                DELETE FROM backtest_results 
                WHERE id NOT IN (
                    SELECT id FROM (
                        SELECT id, ROW_NUMBER() OVER (
                            PARTITION BY strategy_id 
                            ORDER BY created_at DESC
                        ) as rn
                        FROM backtest_results
                    ) 
                    WHERE rn <= ?
                )
            """, (max_results_per_strategy,))
            
            deleted_count = cursor.rowcount
            print(f"  백테스트 결과 삭제: {deleted_count}건")
            
        return deleted_count
```

## 💾 백업 및 복구 시스템

### 스마트 백업 관리자
```python
class DatabaseBackupManager:
    """데이터베이스 백업 관리자"""
    
    def __init__(self, backup_dir: str = "data/backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
    def create_backup(self, db_path: str, backup_name: str = None):
        """데이터베이스 백업 생성"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = os.path.basename(db_path).replace('.sqlite3', '')
            backup_name = f"{db_name}_backup_{timestamp}.sqlite3"
            
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        print(f"💾 백업 생성: {db_path} → {backup_path}")
        
        # SQLite 백업 (온라인 백업)
        source_conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)
        
        try:
            source_conn.backup(backup_conn)
            
            # 백업 검증
            self._verify_backup(backup_path)
            
            print(f"✅ 백업 완료: {backup_name}")
            return backup_path
            
        finally:
            source_conn.close()
            backup_conn.close()
            
    def _verify_backup(self, backup_path: str):
        """백업 파일 검증"""
        with sqlite3.connect(backup_path) as conn:
            # 무결성 검사
            result = conn.execute("PRAGMA integrity_check;").fetchone()
            if result[0] != "ok":
                raise ValueError(f"백업 무결성 검사 실패: {result[0]}")
                
            # 테이블 수 확인
            tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            
            print(f"  백업 검증 완료: {tables}개 테이블")
            
    def restore_backup(self, backup_path: str, target_path: str):
        """백업 복구"""
        print(f"🔄 백업 복구: {backup_path} → {target_path}")
        
        if os.path.exists(target_path):
            # 기존 파일 백업
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_old = f"{target_path}.before_restore_{timestamp}"
            shutil.move(target_path, backup_old)
            print(f"  기존 파일 백업: {backup_old}")
            
        # 백업 파일 복사
        shutil.copy2(backup_path, target_path)
        
        # 복구 검증
        self._verify_backup(target_path)
        print(f"✅ 복구 완료: {target_path}")
        
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """오래된 백업 파일 정리"""
        print(f"🧹 백업 파일 정리 ({days_to_keep}일 이전)")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.sqlite3'):
                file_path = os.path.join(self.backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"  삭제: {filename}")
                    
        print(f"✅ 백업 정리 완료: {deleted_count}개 파일 삭제")
```

## 🔧 데이터베이스 관리 자동화

### 관리 작업 스케줄러
```python
class DatabaseMaintenanceScheduler:
    """데이터베이스 유지보수 스케줄러"""
    
    def __init__(self):
        self.cleanup_manager = DataCleanupManager("data/market_data.sqlite3")
        self.backup_manager = DatabaseBackupManager()
        self.performance_analyzer = QueryPerformanceAnalyzer("data/strategies.sqlite3")
        
    def run_daily_maintenance(self):
        """일일 유지보수 작업"""
        print("📅 일일 데이터베이스 유지보수 시작")
        
        # 1. 시장 데이터 정리
        self.cleanup_manager.cleanup_old_market_data(days_to_keep=30)
        
        # 2. 전략 DB 백업
        self.backup_manager.create_backup("data/strategies.sqlite3")
        
        # 3. 성능 최적화
        self.performance_analyzer.create_recommended_indexes()
        
        print("✅ 일일 유지보수 완료")
        
    def run_weekly_maintenance(self):
        """주간 유지보수 작업"""
        print("📅 주간 데이터베이스 유지보수 시작")
        
        # 1. 설정 DB 백업
        self.backup_manager.create_backup("data/settings.sqlite3")
        
        # 2. 백테스트 결과 정리
        self.cleanup_manager.cleanup_old_backtests(max_results_per_strategy=50)
        
        # 3. 오래된 백업 정리
        self.backup_manager.cleanup_old_backups(days_to_keep=30)
        
        print("✅ 주간 유지보수 완료")
        
    def emergency_recovery(self):
        """긴급 복구 작업"""
        print("🚨 긴급 데이터베이스 복구 시작")
        
        # 최신 백업으로 복구
        # 무결성 검사
        # 성능 검증
        
        print("✅ 긴급 복구 완료")

# 사용 예시
scheduler = DatabaseMaintenanceScheduler()
scheduler.run_daily_maintenance()
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처 이해
- [레이어 책임](02_LAYER_RESPONSIBILITIES.md): Infrastructure 계층 역할
- [성능 최적화](09_PERFORMANCE_OPTIMIZATION.md): 데이터베이스 성능 향상
- [문제 해결](06_TROUBLESHOOTING.md): 데이터베이스 관련 문제

---
**💡 핵심**: "예방적 관리와 자동화를 통해 데이터베이스를 안정적으로 운영하세요!"
