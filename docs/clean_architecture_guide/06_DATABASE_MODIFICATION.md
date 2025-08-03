# 💾 데이터베이스 수정 및 관리 가이드

> **목적**: Clean Architecture에서 데이터베이스 스키마 변경, 테이블 추가/삭제 관리  
> **대상**: 개발자, 데이터베이스 관리자  
> **예상 읽기 시간**: 20분

## 🏗️ Clean Architecture의 DB 관리 변화

### ❌ 기존 방식 (Legacy)
```python
# 직접 SQL 실행
db.execute("ALTER TABLE strategies ADD COLUMN new_field TEXT")

# 하드코딩된 테이블 구조
class Strategy:
    def save(self):
        query = "INSERT INTO strategies (name, config) VALUES (?, ?)"
        db.execute(query, (self.name, self.config))
```

### ✅ Clean Architecture 방식
```python
# 1. Domain에서 비즈니스 요구사항 정의
class Strategy:
    def __init__(self, strategy_id, name, risk_level):  # 새 필드 추가
        self.risk_level = risk_level  # 비즈니스 규칙

# 2. Migration Script로 체계적 변경
class AddRiskLevelToStrategies(Migration):
    def up(self):
        self.execute("ALTER TABLE strategies ADD COLUMN risk_level INTEGER DEFAULT 3")
    
    def down(self):
        self.execute("ALTER TABLE strategies DROP COLUMN risk_level")

# 3. Repository에서 구현 분리
class StrategyRepository:
    def save(self, strategy: Strategy):
        # Domain 객체 → DB 스키마 변환
        data = self._to_database_format(strategy)
        self.db.execute(query, data)
```

## 📊 3-DB 아키텍처 관리

### 데이터베이스 분리 구조
```
📁 data/
├── 🔧 settings.sqlite3      # 시스템 구조 정의 (거의 변경 없음)
│   ├── tv_trading_variables  # 매매 변수 정의
│   ├── tv_variable_parameters # 파라미터 스키마
│   └── tv_indicator_categories # 카테고리 분류
│
├── 📈 strategies.sqlite3     # 사용자 전략 (자주 변경)
│   ├── strategies           # 전략 메인 테이블
│   ├── strategy_conditions  # 조건 저장
│   ├── backtest_results     # 백테스트 결과
│   └── execution_logs       # 실행 기록
│
└── 📊 market_data.sqlite3   # 시장 데이터 (대용량, 휘발성)
    ├── price_data          # 가격 데이터
    ├── indicator_cache     # 지표 캐시
    └── market_info         # 마켓 정보
```

### DB별 변경 빈도 및 관리 전략
```python
DATABASE_MANAGEMENT_STRATEGY = {
    "settings.sqlite3": {
        "변경_빈도": "월 1-2회 (기능 추가시)",
        "백업_주기": "변경 전 필수",
        "마이그레이션": "수동 승인 필요",
        "롤백_가능": True,
        "영향_범위": "전체 시스템"
    },
    "strategies.sqlite3": {
        "변경_빈도": "주 1-3회 (기능 개선시)",
        "백업_주기": "일일 자동",
        "마이그레이션": "자동 적용",
        "롤백_가능": True,
        "영향_범위": "사용자 데이터"
    },
    "market_data.sqlite3": {
        "변경_빈도": "월 1회 (성능 최적화)",
        "백업_주기": "불필요 (재생성 가능)",
        "마이그레이션": "자동 적용",
        "롤백_가능": False,
        "영향_범위": "성능만"
    }
}
```

## 🔄 데이터베이스 마이그레이션 시스템

### Migration 클래스 구조
```python
# infrastructure/database/migrations/base_migration.py
from abc import ABC, abstractmethod
from datetime import datetime

class Migration(ABC):
    """마이그레이션 기본 클래스"""
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        self.version = self._get_version()
        self.description = self._get_description()
    
    @abstractmethod
    def up(self):
        """변경사항 적용"""
        pass
    
    @abstractmethod
    def down(self):
        """변경사항 롤백"""
        pass
    
    @abstractmethod
    def _get_version(self) -> str:
        """마이그레이션 버전 (YYYYMMDD_HHMMSS 형식)"""
        pass
    
    @abstractmethod
    def _get_description(self) -> str:
        """마이그레이션 설명"""
        pass
    
    def execute(self, query: str, params=None):
        """SQL 실행 (트랜잭션 관리 포함)"""
        connection = self._get_connection()
        try:
            connection.execute(query, params or ())
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise MigrationError(f"마이그레이션 실패: {e}")
    
    def _get_connection(self):
        """DB 연결 획득"""
        return DatabaseConnectionManager.get_connection(self.database_name)
```

### 실제 마이그레이션 예시
```python
# infrastructure/database/migrations/20250803_140000_add_trailing_stop_strategy.py
class AddTrailingStopStrategy(Migration):
    """트레일링 스탑 전략 지원을 위한 테이블 추가"""
    
    def _get_version(self) -> str:
        return "20250803_140000"
    
    def _get_description(self) -> str:
        return "트레일링 스탑 전략 테이블 추가 및 기존 strategies 테이블 확장"
    
    def up(self):
        """변경사항 적용"""
        # 1. 새 테이블 생성
        self.execute("""
            CREATE TABLE trailing_stop_strategies (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                activation_profit_rate REAL NOT NULL CHECK(activation_profit_rate >= 0.02),
                trail_distance_rate REAL NOT NULL CHECK(trail_distance_rate BETWEEN 0.01 AND 0.20),
                max_loss_rate REAL CHECK(max_loss_rate < activation_profit_rate),
                is_activated BOOLEAN DEFAULT 0,
                highest_price REAL,
                stop_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
            )
        """)
        
        # 2. 기존 테이블에 컬럼 추가
        self.execute("""
            ALTER TABLE strategies 
            ADD COLUMN strategy_type TEXT DEFAULT 'basic' 
            CHECK(strategy_type IN ('basic', 'trailing_stop', 'pyramid', 'grid'))
        """)
        
        # 3. 인덱스 추가
        self.execute("""
            CREATE INDEX idx_trailing_stop_strategy_id 
            ON trailing_stop_strategies(strategy_id)
        """)
        
        self.execute("""
            CREATE INDEX idx_trailing_stop_activated 
            ON trailing_stop_strategies(is_activated, strategy_id)
        """)
        
        # 4. 트리거 추가 (updated_at 자동 갱신)
        self.execute("""
            CREATE TRIGGER update_trailing_stop_timestamp 
            AFTER UPDATE ON trailing_stop_strategies
            BEGIN
                UPDATE trailing_stop_strategies 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)
        
        print("✅ 트레일링 스탑 전략 테이블 생성 완료")
    
    def down(self):
        """변경사항 롤백"""
        # 역순으로 제거
        self.execute("DROP TRIGGER IF EXISTS update_trailing_stop_timestamp")
        self.execute("DROP INDEX IF EXISTS idx_trailing_stop_activated")
        self.execute("DROP INDEX IF EXISTS idx_trailing_stop_strategy_id")
        self.execute("DROP TABLE IF EXISTS trailing_stop_strategies")
        
        # 컬럼 제거 (SQLite 제한으로 인해 테이블 재생성 필요)
        self._remove_column_from_strategies()
        
        print("✅ 트레일링 스탑 전략 관련 변경사항 롤백 완료")
    
    def _remove_column_from_strategies(self):
        """SQLite에서 컬럼 제거 (테이블 재생성 방식)"""
        # 임시 테이블 생성
        self.execute("""
            CREATE TABLE strategies_temp AS 
            SELECT id, name, description, is_active, created_at, updated_at 
            FROM strategies
        """)
        
        # 기존 테이블 삭제
        self.execute("DROP TABLE strategies")
        
        # 원래 구조로 테이블 재생성
        self.execute("""
            CREATE TABLE strategies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 데이터 복원
        self.execute("""
            INSERT INTO strategies 
            SELECT * FROM strategies_temp
        """)
        
        # 임시 테이블 삭제
        self.execute("DROP TABLE strategies_temp")
```

## 🚀 마이그레이션 관리자

### Migration Manager 구현
```python
# infrastructure/database/migration_manager.py
class MigrationManager:
    """데이터베이스 마이그레이션 관리자"""
    
    def __init__(self):
        self.migrations = self._discover_migrations()
        self._ensure_migration_table_exists()
    
    def migrate(self, target_version: str = None, database: str = None):
        """마이그레이션 실행"""
        pending_migrations = self._get_pending_migrations(target_version, database)
        
        if not pending_migrations:
            print("✅ 실행할 마이그레이션이 없습니다")
            return
        
        print(f"🚀 {len(pending_migrations)}개의 마이그레이션을 실행합니다")
        
        for migration in pending_migrations:
            try:
                print(f"📝 실행 중: {migration.version} - {migration.description}")
                
                # 백업 생성 (중요한 DB의 경우)
                if migration.database_name in ['settings.sqlite3', 'strategies.sqlite3']:
                    self._create_backup(migration.database_name, migration.version)
                
                # 마이그레이션 실행
                migration.up()
                
                # 실행 기록 저장
                self._record_migration(migration)
                
                print(f"✅ 완료: {migration.version}")
                
            except Exception as e:
                print(f"❌ 실패: {migration.version} - {str(e)}")
                raise MigrationError(f"마이그레이션 실패: {migration.version}")
        
        print("🎉 모든 마이그레이션이 완료되었습니다")
    
    def rollback(self, target_version: str, database: str):
        """마이그레이션 롤백"""
        migrations_to_rollback = self._get_migrations_to_rollback(target_version, database)
        
        if not migrations_to_rollback:
            print("✅ 롤백할 마이그레이션이 없습니다")
            return
        
        print(f"🔄 {len(migrations_to_rollback)}개의 마이그레이션을 롤백합니다")
        
        # 역순으로 롤백
        for migration in reversed(migrations_to_rollback):
            try:
                print(f"📝 롤백 중: {migration.version} - {migration.description}")
                
                # 백업 생성
                self._create_backup(migration.database_name, f"rollback_{migration.version}")
                
                # 롤백 실행
                migration.down()
                
                # 실행 기록 제거
                self._remove_migration_record(migration)
                
                print(f"✅ 롤백 완료: {migration.version}")
                
            except Exception as e:
                print(f"❌ 롤백 실패: {migration.version} - {str(e)}")
                raise MigrationError(f"롤백 실패: {migration.version}")
    
    def status(self, database: str = None):
        """마이그레이션 상태 확인"""
        applied_versions = self._get_applied_versions(database)
        
        print("\n📊 마이그레이션 상태")
        print("=" * 60)
        
        for migration in self.migrations:
            if database and migration.database_name != database:
                continue
                
            status = "✅ 적용됨" if migration.version in applied_versions else "⏳ 대기 중"
            print(f"{status} {migration.version} - {migration.description} ({migration.database_name})")
    
    def _discover_migrations(self) -> List[Migration]:
        """마이그레이션 파일 자동 발견"""
        migrations = []
        migration_dir = Path(__file__).parent / "migrations"
        
        for migration_file in migration_dir.glob("*.py"):
            if migration_file.name.startswith("__"):
                continue
                
            module_name = f"infrastructure.database.migrations.{migration_file.stem}"
            module = importlib.import_module(module_name)
            
            # Migration 클래스 찾기
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (inspect.isclass(attr) and 
                    issubclass(attr, Migration) and 
                    attr != Migration):
                    migrations.append(attr())
        
        # 버전순 정렬
        migrations.sort(key=lambda m: m.version)
        return migrations
    
    def _get_pending_migrations(self, target_version: str, database: str) -> List[Migration]:
        """대기 중인 마이그레이션 목록"""
        applied_versions = self._get_applied_versions(database)
        
        pending = []
        for migration in self.migrations:
            if database and migration.database_name != database:
                continue
                
            if migration.version not in applied_versions:
                pending.append(migration)
                
                if target_version and migration.version == target_version:
                    break
        
        return pending
    
    def _create_backup(self, database_name: str, version: str):
        """데이터베이스 백업 생성"""
        source_path = Path(f"data/{database_name}")
        backup_path = Path(f"data/backups/{database_name}_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, backup_path)
        
        print(f"💾 백업 생성: {backup_path}")
```

## 🔧 Repository 패턴의 DB 스키마 변경 대응

### 스키마 변경에 유연한 Repository 구현
```python
# infrastructure/repositories/strategy_repository.py
class SQLiteStrategyRepository(StrategyRepository):
    """전략 리포지토리 - 스키마 변경에 유연하게 대응"""
    
    def save(self, strategy: Strategy):
        """도메인 객체를 DB에 저장 (스키마 변화 대응)"""
        
        # 1. Domain 객체 → DB 데이터 변환
        strategy_data = self._to_database_format(strategy)
        
        # 2. 동적 SQL 생성 (존재하는 컬럼만 사용)
        available_columns = self._get_available_columns("strategies")
        insert_columns = [col for col in strategy_data.keys() if col in available_columns]
        
        placeholders = ", ".join([f":{col}" for col in insert_columns])
        columns_str = ", ".join(insert_columns)
        
        query = f"""
            INSERT OR REPLACE INTO strategies ({columns_str})
            VALUES ({placeholders})
        """
        
        # 3. 사용 가능한 데이터만 추출
        filtered_data = {col: strategy_data[col] for col in insert_columns}
        
        try:
            self.db.execute(query, filtered_data)
            
            # 4. 관련 데이터 저장 (트레일링 스탑 등)
            self._save_related_data(strategy)
            
        except sqlite3.Error as e:
            raise RepositoryError(f"전략 저장 실패: {str(e)}")
    
    def _to_database_format(self, strategy: Strategy) -> dict:
        """Domain 객체 → DB 형식 변환 (버전 호환성 고려)"""
        base_data = {
            'id': strategy.id.value,
            'name': strategy.name,
            'description': strategy.description,
            'is_active': strategy.is_active,
            'created_at': strategy.created_at.isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # 새로운 필드들 (스키마 버전에 따라 선택적 추가)
        if hasattr(strategy, 'strategy_type'):
            base_data['strategy_type'] = strategy.strategy_type
        
        if hasattr(strategy, 'risk_level'):
            base_data['risk_level'] = strategy.risk_level
        
        if hasattr(strategy, 'tags'):
            base_data['tags'] = json.dumps(strategy.tags)
        
        return base_data
    
    def _get_available_columns(self, table_name: str) -> set:
        """테이블의 사용 가능한 컬럼 목록 조회"""
        query = f"PRAGMA table_info({table_name})"
        result = self.db.fetchall(query)
        return {row['name'] for row in result}
    
    def _save_related_data(self, strategy: Strategy):
        """관련 데이터 저장 (확장 전략들)"""
        # 트레일링 스탑 전략인 경우
        if isinstance(strategy, TrailingStopStrategy):
            self._save_trailing_stop_data(strategy)
        
        # 피라미드 전략인 경우
        if hasattr(strategy, 'pyramid_config'):
            self._save_pyramid_data(strategy)
    
    def find_by_id(self, strategy_id: StrategyId) -> Strategy:
        """ID로 전략 조회 (스키마 변화 대응)"""
        query = "SELECT * FROM strategies WHERE id = ?"
        row = self.db.fetchone(query, (strategy_id.value,))
        
        if not row:
            raise StrategyNotFoundError(strategy_id)
        
        # DB → Domain 객체 변환 (버전 호환성 고려)
        return self._from_database_format(row)
    
    def _from_database_format(self, row: dict) -> Strategy:
        """DB 형식 → Domain 객체 변환"""
        # 기본 필드
        strategy_data = {
            'strategy_id': StrategyId(row['id']),
            'name': row['name'],
            'description': row.get('description'),
            'is_active': bool(row.get('is_active', True)),
            'created_at': datetime.fromisoformat(row['created_at'])
        }
        
        # 선택적 필드들 (존재하는 경우에만 추가)
        if 'strategy_type' in row and row['strategy_type']:
            strategy_data['strategy_type'] = row['strategy_type']
        
        if 'risk_level' in row and row['risk_level'] is not None:
            strategy_data['risk_level'] = row['risk_level']
        
        if 'tags' in row and row['tags']:
            strategy_data['tags'] = json.loads(row['tags'])
        
        # 전략 타입에 따른 구체적 객체 생성
        strategy_type = row.get('strategy_type', 'basic')
        
        if strategy_type == 'trailing_stop':
            return self._create_trailing_stop_strategy(strategy_data, row['id'])
        elif strategy_type == 'pyramid':
            return self._create_pyramid_strategy(strategy_data, row['id'])
        else:
            return Strategy(**strategy_data)
```

## 📋 데이터베이스 변경 체크리스트

### 새 테이블 추가 시
- [ ] **Migration Script 작성**: `up()`, `down()` 메서드 구현
- [ ] **Domain Entity 정의**: 비즈니스 규칙과 제약 조건
- [ ] **Repository 구현**: 도메인 객체 ↔ DB 변환
- [ ] **DTO 정의**: Application Layer와의 데이터 교환
- [ ] **테스트 작성**: Repository 통합 테스트
- [ ] **백업 생성**: 중요한 DB는 마이그레이션 전 백업

### 기존 테이블 수정 시
- [ ] **호환성 검토**: 기존 데이터와의 호환성 확인
- [ ] **기본값 설정**: 새 컬럼의 적절한 기본값
- [ ] **제약 조건 추가**: 비즈니스 규칙을 DB 레벨에서 강제
- [ ] **Repository 업데이트**: 새 필드 처리 로직 추가
- [ ] **Migration 테스트**: 실제 데이터로 마이그레이션 테스트
- [ ] **롤백 계획**: 문제 발생 시 롤백 방법 준비

### 테이블 삭제 시
- [ ] **의존성 확인**: 다른 테이블과의 외래키 관계
- [ ] **데이터 백업**: 삭제 전 중요 데이터 백업
- [ ] **Repository 제거**: 관련 Repository 코드 정리
- [ ] **Application Layer 정리**: Service, DTO 정리
- [ ] **테스트 업데이트**: 관련 테스트 수정/삭제

## 🔍 다음 단계

- **[기능 추가 가이드](04_FEATURE_DEVELOPMENT.md)**: DB 변경을 포함한 기능 개발
- **[API 통합](07_API_INTEGRATION.md)**: 외부 시스템과의 데이터 연동
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: DB 관련 문제 해결

---
**💡 핵심**: "Clean Architecture에서는 Domain이 변경 기준이고, Infrastructure(DB)는 Domain을 지원하는 구현 세부사항입니다!"
