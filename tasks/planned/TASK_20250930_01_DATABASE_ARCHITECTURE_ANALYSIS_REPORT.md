# 📋 TASK_20250930_01: 데이터베이스 아키텍처 종합 분석 보고서

## 🎯 분석 개요

**API 키 저장 실패 문제 (44bytes → 34bytes) 조사 결과 시스템 전반의 구조적 문제 발견**

현재 API 키 설정에서 DB 암호화키 저장 실패는 단순한 구조적 문제가 아니라 **데이터베이스 아키텍처 전반의 근본적 설계 문제**임이 확인되었습니다.

### 🎯 우선순위 개선 방향

1. **Path 관리 서비스 완전 구성** (Priority: P0) - Database Manager 개선의 필수 선행 작업
2. **Database Manager 구조적 개선** (Priority: P1) - 핵심 인프라 안정화
3. **실시간 검증 시스템** - `candle_data_provider.py` + `candle_test_07_comprehensive.py` 연동 테스트

### 🧪 검증 전략

**CandleDataProvider 기반 실시간 검증**: Database Manager 개선 과정에서 `candle_data_provider.py`는 시스템에서 가장 활발하게 DB를 사용하는 컴포넌트로, `candle_test_07_comprehensive.py`를 통해 개선 사항이 실제 운영 환경에서 정상 작동하는지 지속적으로 검증 가능합니다.

---

## 🗂️ Path 관리 서비스 우선 개선 (Phase 0)

### 🚨 현재 Path 관리의 구조적 문제

DatabaseManager 개선 전에 **Path 관리 서비스의 완전한 구성**이 선행되어야 합니다. 현재 시스템의 파일 경로 관리가 일관성 없이 분산되어 있어, Database Manager 개선 시 경로 충돌과 설정 불일치 문제가 발생할 수 있습니다.

#### 🔍 발견된 Path 관리 문제점

```python
# 문제 1: 하드코딩된 경로들
"data/settings.sqlite3"           # 직접 하드코딩
"data/strategies.sqlite3"         # 직접 하드코딩
"data/market_data.sqlite3"        # 직접 하드코딩
"config/paths_config.yaml"        # 설정 파일 경로도 하드코딩

# 문제 2: 중복된 Path 서비스들
PathConfigurationService          # Domain Layer
get_path_service()               # Factory 함수
config/paths_config.yaml         # YAML 기반 설정
config/database_config.yaml      # 별도 DB 경로 설정

# 문제 3: 환경별 경로 관리 부재
# 개발/테스트/프로덕션 환경별 경로 분리 없음
```

#### 💡 Path 관리 서비스 완전 구성 방안

**1. 통합 Path Configuration 서비스**

```yaml
# config/unified_paths_config.yaml
path_management:
  version: "2.0"
  environment: "${UPBIT_ENV:development}"  # development/testing/production

  base_directories:
    project_root: "${PROJECT_ROOT:.}"
    data_root: "${DATA_ROOT:./data}"
    config_root: "${CONFIG_ROOT:./config}"
    logs_root: "${LOGS_ROOT:./logs}"
    cache_root: "${CACHE_ROOT:./temp/cache}"

  databases:
    settings:
      path: "${data_root}/settings.sqlite3"
      backup_dir: "${data_root}/backups/settings"
      test_path: "${data_root}/test_settings.sqlite3"  # 테스트 전용

    strategies:
      path: "${data_root}/strategies.sqlite3"
      backup_dir: "${data_root}/backups/strategies"
      test_path: "${data_root}/test_strategies.sqlite3"

    market_data:
      path: "${data_root}/market_data.sqlite3"
      backup_dir: "${data_root}/backups/market_data"
      test_path: "${data_root}/test_market_data.sqlite3"

  security:
    secure_config_dir: "${config_root}/secure"
    api_credentials_path: "${config_root}/secure/api_credentials.json"
    encryption_key_path: "${config_root}/secure/encryption_key.key"

  # 환경별 오버라이드
  environment_overrides:
    testing:
      databases:
        settings:
          path: "${data_root}/test/test_settings.sqlite3"
        strategies:
          path: "${data_root}/test/test_strategies.sqlite3"
        market_data:
          path: "${data_root}/test/test_market_data.sqlite3"

    production:
      base_directories:
        data_root: "/var/lib/upbit-autotrader/data"
        logs_root: "/var/log/upbit-autotrader"
        config_root: "/etc/upbit-autotrader"
```

**2. Universal Path Service 구현**

```python
class UniversalPathService:
    """
    통합 경로 관리 서비스 - 모든 파일 경로의 단일 진실의 원천

    특징:
    - 환경별 경로 자동 전환 (development/testing/production)
    - 환경변수 기반 동적 경로 구성
    - Path 검증 및 자동 생성
    - Database Manager와 완전 통합
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
        if not hasattr(self, '_initialized'):
            self.config = self._load_unified_config()
            self.environment = self._detect_environment()
            self._validate_and_create_paths()
            self._initialized = True

    def get_database_path(self, db_name: str) -> Path:
        """DB 이름으로 환경별 경로 반환"""
        if self.environment == "testing":
            return Path(self.config['databases'][db_name]['test_path'])
        else:
            return Path(self.config['databases'][db_name]['path'])

    def get_database_backup_dir(self, db_name: str) -> Path:
        """DB 백업 디렉토리 반환"""
        return Path(self.config['databases'][db_name]['backup_dir'])

    def get_secure_path(self, file_type: str) -> Path:
        """보안 파일 경로 반환"""
        return Path(self.config['security'][f'{file_type}_path'])

    def switch_to_testing_mode(self):
        """테스트 모드로 경로 전환"""
        self.environment = "testing"
        self._validate_and_create_paths()

    def _detect_environment(self) -> str:
        """현재 실행 환경 자동 감지"""
        if os.getenv('PYTEST_CURRENT_TEST'):
            return "testing"
        elif os.getenv('UPBIT_ENV') == 'production':
            return "production"
        else:
            return "development"
```

**3. Database Manager 통합 설계**

```python
class UniversalDatabaseManager:
    """
    Path Service와 완전 통합된 Database Manager
    """

    def __init__(self, path_service: UniversalPathService):
        self.path_service = path_service
        self.connections = {}

        # Path Service 기반으로 DB 설정 구성
        self.db_configs = {
            'settings': {
                'path': path_service.get_database_path('settings'),
                'backup_dir': path_service.get_database_backup_dir('settings')
            },
            'strategies': {
                'path': path_service.get_database_path('strategies'),
                'backup_dir': path_service.get_database_backup_dir('strategies')
            },
            'market_data': {
                'path': path_service.get_database_path('market_data'),
                'backup_dir': path_service.get_database_backup_dir('market_data')
            }
        }

    def get_connection(self, db_name: str):
        """Path Service 기반 동적 연결 관리"""
        db_path = self.path_service.get_database_path(db_name)

        # 환경 전환 시 자동으로 새 경로 적용
        if db_name in self.connections:
            current_path = self.connections[db_name].path
            if current_path != str(db_path):
                # 경로가 변경되었으면 연결 재생성
                self._recreate_connection(db_name, db_path)

        return self._get_or_create_connection(db_name, db_path)
```

### 🎯 Path 서비스 개선 효과

1. **Database Manager 개선 준비**: 일관된 경로 관리로 DB Manager 리팩터링 시 경로 충돌 방지
2. **환경별 자동 전환**: 개발/테스트/프로덕션 환경 간 투명한 경로 전환
3. **테스트 격리**: `candle_test_07_comprehensive.py` 실행 시 자동으로 테스트 전용 DB 사용
4. **PostgreSQL 전환 준비**: 경로 추상화로 DB 엔진 전환 시에도 Path 관리 일관성 유지

---

## 🚨 발견된 핵심 문제들

### 1. **API 키 저장 실패의 정확한 원인**

#### 🔍 문제 상황

```bash
# 실제 테스트 결과
테스트 키 크기: 32 bytes  # 입력된 키
저장 결과: True          # 저장 성공으로 보고됨
로드된 키: None          # 실제로는 로드 실패
로드된 키 크기: 0 bytes  # 데이터 손실

# DB 상태 확인
secure_keys 테이블:
- ID: 350, 타입: encryption, 크기: 34bytes ← 문제! (32bytes가 34bytes로 저장됨)
- 생성: 2025-09-30 03:49:46

# 오류 메시지
ERROR: Fernet key must be 32 url-safe base64-encoded bytes.
```

#### 🎯 근본 원인 분석

**1. Fernet 암호화 키 형식 문제**

- **요구사항**: Fernet는 32바이트 URL-safe base64 인코딩된 키 필요
- **현재 상태**: DB에 34바이트 키가 저장됨 (잘못된 형식)
- **결과**: 초기화 시 Fernet 객체 생성 실패 → self.fernet = None

**2. 데이터 불일치 및 검증 부족**

- 저장 시 `save_key()` 성공 리포트하지만 실제 데이터 형식 문제
- 로드 시 형식 검증 실패로 None 반환
- Repository와 Service 간 데이터 일관성 검증 누락

**3. 예외 처리의 문제점**

```python
# ApiKeyService._try_load_existing_encryption_key()
try:
    self.fernet = Fernet(self.encryption_key)  # 34bytes 키로 실패
except Exception as e:
    self.logger.error(f"암호화 키 로드 중 오류: {e}")
    self.encryption_key = None  # 오류를 숨기고 None으로 설정
    self.fernet = None
```

### 2. **DatabaseManager 설계의 구조적 한계**

#### 🏗️ 현재 아키텍처의 문제점

**1. SQLite 과도한 의존성 (50+ 코드 위치)**

```python
# 발견된 SQLite 하드코딩 예시들
- "SQLite format 3\x00" (파일 헤더 체크)
- sqlite3.connect() 직접 호출
- ".sqlite3" 확장자 하드코딩
- SQLite 특화 PRAGMA 명령어 사용
- SQLite 전용 SQL 문법 (INSERT OR REPLACE)
```

**2. DB 엔진 독립성 부재**

- Connection Factory 패턴 미적용
- 추상화 레이어 없이 sqlite3 직접 사용
- SQL 방언 차이 고려 없음
- 트랜잭션 격리 수준 하드코딩

**3. 설계 패턴 혼재**

```
현재 혼재된 패턴들:
- DatabaseManager (Connection Pooling)
- DatabaseConnectionProvider (Singleton)
- DatabaseConnectionService (Health Check)
- Repository 직접 DB 접근
```

#### 🔧 Connection 관리 문제점

**1. 인스턴스 생성 패턴 혼재**

```python
# Pattern 1: Container DI (권장)
secure_keys_repository = providers.Singleton(SqliteSecureKeysRepository, db_manager=database_manager)

# Pattern 2: 직접 생성 (문제)
repo = SqliteSecureKeysRepository(database_connection_service)
service = ApiKeyService(repo)
```

**2. 트랜잭션 경계 불명확**

```python
# DatabaseManager.get_connection() - auto commit
@contextmanager
def get_connection(self, db_name: str):
    try:
        with self._lock:
            yield conn
    except Exception as e:
        conn.rollback()  # 실패 시 롤백
        raise
    else:
        conn.commit()    # 성공 시 자동 커밋 ← 문제!
```

**3. 동시성 제어 한계**

- 단일 Lock으로 모든 DB 접근 직렬화
- DB별 세분화된 Lock 없음
- Connection Pool 크기 제어 없음

### 3. **PostgreSQL 전환 시 예상 장애물**

#### 🚧 호환성 문제 (High Impact)

**1. SQL 문법 차이**

```sql
-- SQLite (현재)
INSERT OR REPLACE INTO secure_keys ...
SELECT last_insert_rowid()
PRAGMA table_info(table_name)

-- PostgreSQL (필요)
INSERT ... ON CONFLICT ... DO UPDATE
SELECT lastval()
SELECT column_name, data_type FROM information_schema.columns
```

**2. 데이터 타입 매핑**

```python
# SQLite → PostgreSQL 변환 필요
BLOB → BYTEA
TEXT → VARCHAR/TEXT
INTEGER → SERIAL/BIGSERIAL
TIMESTAMP → TIMESTAMP WITH TIME ZONE
```

**3. Connection String & 설정**

```python
# SQLite (현재)
sqlite3.connect("data/settings.sqlite3", check_same_thread=False)

# PostgreSQL (필요)
psycopg2.connect(
    host="localhost",
    database="upbit_trading",
    user="username",
    password="password",
    port=5432
)
```

#### 🔧 마이그레이션 복잡성

**1. 스키마 마이그레이션**

- 37개 테이블 스키마 변환 필요
- UNIQUE 제약조건 재정의
- 인덱스 재구성
- 시퀀스 설정

**2. 데이터 이전**

- BLOB 데이터 형식 변환
- 문자 인코딩 처리 (UTF-8)
- 대용량 market_data 테이블 마이그레이션

**3. 애플리케이션 레이어 변경**

- 50+ 개 파일에서 SQLite 의존성 제거
- Repository 패턴 전면 적용
- Connection Factory 구현

---

## 🏗️ 현재 시스템 아키텍처 상세 분석

### Database Layer 구조도

```
┌─────────────────────────────────────────┐
│           Application Layer             │
├─────────────────────────────────────────┤
│  ApiKeyService  │  Various Services     │
│        │        │         │             │
│        └────────┼─────────┘             │
├─────────────────┼─────────────────────────┤
│           Repository Layer              │
├─────────────────┼─────────────────────────┤
│ SqliteSecureKeys│  Other Repositories   │
│ Repository      │                       │
│        │        │                       │
├────────┼────────┼─────────────────────────┤
│        Infrastructure Layer            │
├────────┼────────┼─────────────────────────┤
│        │        │                       │
│ ┌──────▼──┐ ┌───▼───────┐ ┌─────────────┐ │
│ │Database │ │Database   │ │Database     │ │
│ │Manager  │ │Connection │ │Connection   │ │
│ │         │ │Provider   │ │Service      │ │
│ └─────────┘ └───────────┘ └─────────────┘ │
│        │                                 │
├────────┼─────────────────────────────────┤
│        │        Database Files          │
├────────┼─────────────────────────────────┤
│ ┌──────▼───┐ ┌──────────┐ ┌─────────────┐ │
│ │settings  │ │strategies│ │market_data  │ │
│ │.sqlite3  │ │.sqlite3  │ │.sqlite3     │ │
│ └──────────┘ └──────────┘ └─────────────┘ │
└─────────────────────────────────────────┘
```

### 🔍 Connection Flow 분석

**현재 문제있는 흐름:**

```
ApiKeyService 초기화
└→ SecureKeysRepository(DatabaseConnectionService) ← 직접 생성!
   └→ DatabaseConnectionService.get_connection()
      └→ sqlite3.connect() 직접 호출
         └→ 개별 Connection (Pool 없음)

VS

Container 기반 (올바른) 흐름:
ApplicationContainer
└→ secure_keys_repository (Singleton)
   └→ database_manager (Singleton)
      └→ DatabaseManager.get_connection()
         └→ Connection Pool 관리
```

### 🚧 설계 원칙 위반 사례

**1. DDD 계층 위반**

```python
# Infrastructure에서 Domain 직접 참조 (위반!)
from upbit_auto_trading.domain.repositories.secure_keys_repository import SecureKeysRepository

# UI에서 SQLite 직접 접근 (위반!)
if header.startswith(b'SQLite format 3\x00'):
```

**2. 의존성 역전 원칙 위반**

```python
# 고수준 모듈(Service)이 저수준 모듈(SQLite)에 직접 의존
class ApiKeyService:
    def __init__(self, secure_keys_repository):
        # Repository가 SQLite에 강결합됨
```

**3. 단일 책임 원칙 위반**

```python
# DatabaseManager가 너무 많은 책임을 가짐
- Connection Pool 관리
- 트랜잭션 처리
- SQL 실행
- 최적화 설정
- 에러 처리
```

---

## 💡 개선된 DB 엔진 독립적 아키텍처 설계안

### 1. **다중 DB 엔진 지원 아키텍처**

#### 🏗️ 제안하는 새로운 구조

```
┌─────────────────────────────────────────┐
│           Application Layer             │
├─────────────────────────────────────────┤
│  Services (DB Engine Independent)      │
├─────────────────────────────────────────┤
│           Repository Layer              │
│  (Abstract Interfaces)                 │
├─────────────────────────────────────────┤
│        Database Abstraction Layer      │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │     Database Engine Factory         │ │
│ │                                     │ │
│ │ ┌─────────┐ ┌──────────┐ ┌─────────┐ │ │
│ │ │SQLite   │ │PostgreSQL│ │MySQL    │ │ │
│ │ │Engine   │ │Engine    │ │Engine   │ │ │
│ │ └─────────┘ └──────────┘ └─────────┘ │ │
│ └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│        Query Builder & Migration        │
│                                         │
│ ┌─────────────┐ ┌─────────────────────┐ │
│ │Query Builder│ │Migration Framework  │ │
│ │(SQL Dialect)│ │(Schema Versioning)  │ │
│ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────┘
```

#### 🔧 핵심 컴포넌트 설계

**1. Database Engine Factory**

```python
class DatabaseEngine(ABC):
    """데이터베이스 엔진 추상화 인터페이스"""

    @abstractmethod
    def create_connection(self, config: DatabaseConfig) -> Connection:
        pass

    @abstractmethod
    def get_query_builder(self) -> QueryBuilder:
        pass

    @abstractmethod
    def get_migration_runner(self) -> MigrationRunner:
        pass

class SQLiteEngine(DatabaseEngine):
    def create_connection(self, config: DatabaseConfig) -> sqlite3.Connection:
        return sqlite3.connect(config.path, **config.options)

class PostgreSQLEngine(DatabaseEngine):
    def create_connection(self, config: DatabaseConfig) -> psycopg2.Connection:
        return psycopg2.connect(**config.postgres_params)
```

**2. Universal Query Builder**

```python
class QueryBuilder(ABC):
    """SQL 방언별 쿼리 빌더"""

    @abstractmethod
    def insert_or_replace(self, table: str, data: Dict) -> str:
        """INSERT OR REPLACE 등가 쿼리 생성"""
        pass

    @abstractmethod
    def last_insert_id(self) -> str:
        """마지막 삽입 ID 조회 쿼리"""
        pass

class SQLiteQueryBuilder(QueryBuilder):
    def insert_or_replace(self, table: str, data: Dict) -> str:
        return f"INSERT OR REPLACE INTO {table} ..."

    def last_insert_id(self) -> str:
        return "SELECT last_insert_rowid()"

class PostgreSQLQueryBuilder(QueryBuilder):
    def insert_or_replace(self, table: str, data: Dict) -> str:
        return f"INSERT INTO {table} ... ON CONFLICT ... DO UPDATE"

    def last_insert_id(self) -> str:
        return "SELECT lastval()"
```

**3. Configuration-Driven Engine Selection**

```yaml
# config/database_config.yaml
database:
  engine: "sqlite"  # sqlite | postgresql | mysql

  sqlite:
    settings_path: "data/settings.sqlite3"
    strategies_path: "data/strategies.sqlite3"
    market_data_path: "data/market_data.sqlite3"
    options:
      check_same_thread: false
      timeout: 30.0

  postgresql:
    host: "localhost"
    port: 5432
    database: "upbit_trading"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"
    connection_pool:
      min_connections: 5
      max_connections: 20
```

### 2. **통합 Connection Manager 재설계**

#### 🔄 새로운 Connection 관리 방식

**1. Engine-Agnostic Connection Pool**

```python
class UniversalConnectionManager:
    """DB 엔진에 독립적인 연결 관리자"""

    def __init__(self, config: DatabaseConfig):
        self.engine = DatabaseEngineFactory.create(config.engine)
        self.pools = {}  # {db_name: ConnectionPool}

    @contextmanager
    def get_connection(self, db_name: str):
        """Universal connection context manager"""
        pool = self._get_or_create_pool(db_name)
        connection = pool.get_connection()

        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
        finally:
            pool.return_connection(connection)
```

**2. Repository 패턴 강화**

```python
class SecureKeysRepository(ABC):
    """DB 엔진 독립적 Repository 인터페이스"""

    @abstractmethod
    def save_key(self, key_type: str, key_data: bytes) -> bool:
        pass

class UniversalSecureKeysRepository(SecureKeysRepository):
    """DB 엔진 독립적 구현체"""

    def __init__(self, connection_manager: UniversalConnectionManager):
        self.conn_mgr = connection_manager
        self.query_builder = connection_manager.engine.get_query_builder()

    def save_key(self, key_type: str, key_data: bytes) -> bool:
        # 엔진별 쿼리 빌더 사용으로 호환성 보장
        query = self.query_builder.insert_or_replace(
            "secure_keys",
            {"key_type": key_type, "key_value": key_data}
        )

        with self.conn_mgr.get_connection('settings') as conn:
            cursor = conn.execute(query, (key_type, key_data))
            return cursor.rowcount > 0
```

### 3. **Migration Framework**

#### 🚀 점진적 전환 지원

**1. Schema Version Management**

```python
class MigrationRunner:
    """스키마 마이그레이션 실행기"""

    def migrate_to_postgresql(self, sqlite_path: str, postgres_config: Dict):
        """SQLite → PostgreSQL 마이그레이션"""

        # 1. 스키마 마이그레이션
        self._migrate_schema(sqlite_path, postgres_config)

        # 2. 데이터 마이그레이션
        self._migrate_data(sqlite_path, postgres_config)

        # 3. 인덱스 재구성
        self._rebuild_indexes(postgres_config)

        # 4. 검증
        self._validate_migration(sqlite_path, postgres_config)
```

**2. 호환성 레이어**

```python
class DatabaseCompatibilityLayer:
    """기존 코드 호환성 보장"""

    def __init__(self, new_engine: DatabaseEngine):
        self.engine = new_engine

    # 기존 sqlite3 인터페이스 에뮬레이션
    def connect(self, path: str, **kwargs) -> Connection:
        """sqlite3.connect() 호환 인터페이스"""
        if self.engine.type == "sqlite":
            return self.engine.create_connection(DatabaseConfig(path=path, **kwargs))
        else:
            # PostgreSQL 등 다른 엔진으로 투명하게 라우팅
            return self.engine.create_connection(self._convert_config(path, kwargs))
```

---

## 🧪 CandleDataProvider 기반 실시간 검증 전략

### 🎯 검증 도구 개요

**CandleDataProvider + candle_test_07_comprehensive.py**: Database Manager 개선 과정에서 실제 운영 부하를 시뮬레이션하여 시스템 안정성을 실시간으로 검증할 수 있는 최적의 도구 조합입니다.

#### 📊 CandleDataProvider의 DB 사용 특성

```python
# CandleDataProvider v9.0 - 데이터베이스 집약적 사용 패턴
class CandleDataProvider:
    """
    시스템에서 가장 DB를 활발하게 사용하는 컴포넌트

    DB 사용 특성:
    - ChunkProcessor를 통한 대량 INSERT/UPDATE 연산
    - OverlapAnalyzer를 통한 복잡한 SELECT 쿼리
    - Repository 패턴을 통한 트랜잭션 처리
    - 실시간 Market Data 수집으로 인한 높은 동시성
    """

    async def get_candles(self, symbol, timeframe, count=None, to=None, end=None):
        # ChunkProcessor에 완전 위임 → 내부적으로 다음 작업들 수행:
        # 1. Repository를 통한 기존 데이터 조회 (복잡한 SELECT)
        # 2. OverlapAnalyzer를 통한 중복 분석 (JOIN 쿼리)
        # 3. 업비트 API 호출 후 대량 INSERT
        # 4. 트랜잭션 커밋/롤백 처리
        # 5. Connection Pool 사용 패턴 검증
        collection_result = await self.chunk_processor.process_collection(
            symbol=symbol, timeframe=timeframe, count=count, to=to, end=end
        )
```

#### 🔧 candle_test_07_comprehensive.py 검증 시나리오

```python
# TEST_CONFIG 예시 - Database Manager 스트레스 테스트
TEST_CONFIG = {
    "symbol": "KRW-BTC",
    "timeframe": "1s",                    # 고빈도 데이터로 DB 부하 테스트
    "start_time": "2025-09-25 06:02:05",
    "end_time": "2025-09-25 06:01:30",
    "count": 500,                         # 대량 데이터 수집으로 Connection Pool 테스트
    "chunk_size": 5,                      # 작은 청크로 빈번한 트랜잭션 테스트

    # Database Manager 검증을 위한 파편화 시나리오
    "partial_records": [
        {"start_time": "2025-09-25 06:00:00", "count": 50},   # 기존 데이터 시뮬레이션
        {"start_time": "2025-09-25 06:01:00", "count": 30},   # 오버랩 시나리오
        {"start_time": "2025-09-25 06:02:00", "count": 20}    # 복잡한 병합 시나리오
    ],

    "enable_db_clean": True,              # 각 테스트 전 DB 정리로 일관성 보장
    "pause_for_verification": True,       # 단계별 DB 상태 수동 검증
    "complete_db_table_view": True        # 상세한 DB 상태 확인
}
```

### 📋 Database Manager 개선 단계별 검증 계획

#### **Phase 0: Path 서비스 검증**

```bash
# 1. Path 서비스 개선 후 CandleDataProvider 동작 확인
python tests/candle_data_logic/candle_test_07_comprehensive.py

# 검증 포인트:
# - UniversalPathService를 통한 정확한 DB 경로 사용
# - 환경별 경로 자동 전환 (개발/테스트 모드)
# - DB 파일 자동 생성 및 권한 확인
```

#### **Phase 1: Connection Pool 통합 검증**

```bash
# 2. DatabaseManager 리팩터링 후 연결 안정성 확인
# TEST_CONFIG에서 chunk_size=5, count=1000 설정으로 높은 연결 빈도 테스트
python tests/candle_data_logic/candle_test_07_comprehensive.py

# 검증 포인트:
# - MasterDatabaseManager Singleton 동작
# - Connection Pool 재사용률
# - 트랜잭션 경계 명확성 (자동 커밋/롤백)
# - 동시성 제어 (여러 청크 동시 처리)
```

#### **Phase 2: DB 엔진 추상화 검증**

```bash
# 3. UniversalConnectionManager 적용 후 호환성 확인
python tests/candle_data_logic/candle_test_07_comprehensive.py

# 검증 포인트:
# - Query Builder를 통한 SQL 쿼리 정상 생성
# - Repository 패턴 DB 엔진 독립성
# - 기존 CandleDataProvider API 완전 호환
```

#### **Phase 3: PostgreSQL 전환 검증**

```bash
# 4. PostgreSQL 엔진으로 전환 후 기능 검증
UPBIT_DB_ENGINE=postgresql python tests/candle_data_logic/candle_test_07_comprehensive.py

# 검증 포인트:
# - PostgreSQL Connection 정상 동작
# - 데이터 타입 매핑 정확성 (BLOB → BYTEA)
# - SQL 방언 변환 정확성 (INSERT OR REPLACE → ON CONFLICT)
# - 성능 비교 (SQLite 대비 응답시간)
```

### 🔍 실시간 모니터링 대시보드

```python
# 개선 과정 모니터링을 위한 확장된 테스트 설정
MONITORING_CONFIG = {
    "performance_tracking": True,        # 각 단계별 성능 측정
    "connection_monitoring": True,       # Connection Pool 사용률 추적
    "transaction_logging": True,         # 트랜잭션 성공/실패 로그
    "memory_profiling": True,           # 메모리 사용량 프로파일링

    # 자동화된 검증 기준
    "performance_thresholds": {
        "max_response_time_ms": 100,     # 캔들 1개당 최대 응답시간
        "max_memory_usage_mb": 500,      # 최대 메모리 사용량
        "min_connection_reuse_rate": 0.8  # Connection Pool 재사용률 최소값
    }
}

# 예상 출력 - Database Manager 개선 효과 측정
"""
🧪 === Database Manager 개선 효과 측정 ===

Phase 0 (Path Service) 결과:
✅ 경로 관리: UniversalPathService 통합 완료
✅ 환경 전환: development → testing 자동 전환
✅ DB 생성: 테스트 전용 DB 자동 생성 확인

Phase 1 (Connection Pool) 결과:
📊 Connection 재사용률: 85% (개선 전: 45%)
📊 평균 응답시간: 23ms/candle (개선 전: 67ms/candle)
📊 동시성 오류: 0건 (개선 전: 12건/테스트)

Phase 2 (DB Engine Abstraction) 결과:
🔧 SQL 쿼리 변환: 100% 성공 (SQLite → Universal)
🔧 Repository 호환성: 기존 API 100% 유지
🔧 추상화 오버헤드: +2ms/query (허용 범위)

Phase 3 (PostgreSQL) 결과:
🚀 PostgreSQL 연결: 정상 동작
🚀 데이터 일관성: 100% (SQLite와 동일 결과)
🚀 성능 비교: SQLite 대비 15% 향상

결론: ✅ Database Manager 개선 성공
"""
```

### 🎯 검증 도구 활용 가이드

#### **1. 일일 회귀 테스트**

```bash
# Database Manager 개선 중 매일 실행할 검증 스크립트
./scripts/daily_db_regression_test.sh

# 내부적으로 다음 실행:
# 1. candle_test_07_comprehensive.py (기본 기능 확인)
# 2. 성능 벤치마크 (응답시간, 메모리 사용량)
# 3. Connection Pool 사용률 리포트
# 4. 트랜잭션 로그 분석
```

#### **2. 스트레스 테스트**

```python
# 높은 부하 상황에서 Database Manager 안정성 확인
STRESS_TEST_CONFIG = {
    "concurrent_tests": 5,               # 동시 실행 테스트 수
    "large_dataset_size": 10000,         # 대용량 데이터셋
    "connection_pool_stress": True,      # Connection Pool 한계 테스트
    "transaction_rollback_test": True    # 강제 롤백 시나리오
}
```

#### **3. PostgreSQL 마이그레이션 시뮬레이션**

```bash
# SQLite → PostgreSQL 전환 과정 시뮬레이션
python tests/migration_simulation.py

# 1. SQLite 기준 데이터 생성 (candle_test_07)
# 2. PostgreSQL로 마이그레이션 실행
# 3. 동일한 테스트로 결과 일치성 확인
# 4. 성능 비교 리포트 생성
```

이러한 검증 체계를 통해 Database Manager 개선 과정에서 발생할 수 있는 문제를 사전에 감지하고, 실제 운영 환경에서의 안정성을 보장할 수 있습니다.

---

## 🚀 단계별 개선 로드맵 (업데이트)

### Phase 0: Path 관리 서비스 완전 구성 (4-6시간) 🔥 최우선

#### 🗂️ UniversalPathService 구현 및 적용

```python
# 1. 기존 PathConfigurationService 확장
class UniversalPathService(PathConfigurationService):
    """기존 Path 서비스 확장 - 하위 호환성 보장"""

    def __init__(self):
        super().__init__()
        self.unified_config = self._load_unified_config()
        self.environment = self._detect_environment()

    def _load_unified_config(self) -> Dict:
        """통합 경로 설정 로드 (기존 설정과 병합)"""
        # 기존 paths_config.yaml과 새로운 unified_paths_config.yaml 병합
        base_config = self._load_base_config()  # 기존 설정 로드
        unified_config = self._load_new_unified_config()  # 새 설정 로드
        return {**base_config, **unified_config}  # 새 설정이 우선

    def get_database_path(self, db_name: str) -> Path:
        """환경별 DB 경로 반환 (테스트 환경 자동 전환)"""
        if self.environment == "testing" and hasattr(self, '_test_mode_paths'):
            return self._test_mode_paths.get(db_name, self._get_default_db_path(db_name))
        return self._get_default_db_path(db_name)

# 2. 기존 코드 최소 변경으로 적용
# get_path_service() 팩토리 함수 업데이트만으로 전체 시스템 적용
def get_path_service() -> UniversalPathService:
    """기존 팩토리 함수 - 내부 구현만 변경"""
    return UniversalPathService()  # 기존 PathConfigurationService → UniversalPathService
```

#### 🔧 즉시 적용 가능한 개선사항

```yaml
# config/unified_paths_config.yaml (새 파일 추가)
path_management:
  version: "2.0"

  # 기존 설정 확장
  databases:
    settings:
      path: "${DATA_ROOT:./data}/settings.sqlite3"
      test_path: "${DATA_ROOT:./data}/test_settings.sqlite3"
    strategies:
      path: "${DATA_ROOT:./data}/strategies.sqlite3"
      test_path: "${DATA_ROOT:./data}/test_strategies.sqlite3"
    market_data:
      path: "${DATA_ROOT:./data}/market_data.sqlite3"
      test_path: "${DATA_ROOT:./data}/test_market_data.sqlite3"

  # CandleDataProvider 테스트 지원
  testing:
    auto_switch_on_pytest: true
    cleanup_test_dbs: true
    test_data_isolation: true
```

#### 🧪 candle_test_07_comprehensive.py 연동 검증

```python
# 개선된 Path 서비스 즉시 검증
python tests/candle_data_logic/candle_test_07_comprehensive.py

# 검증 포인트:
# 1. 테스트 실행 시 자동으로 test_market_data.sqlite3 사용
# 2. 테스트 완료 후 자동 정리
# 3. 기존 운영 데이터와 완전 분리
# 4. Path 충돌 없이 정상 동작
```

### Phase 1: 긴급 문제 해결 (1-2일)

#### 🔧 API 키 저장 문제 즉시 수정

```python
# 1. Fernet 키 형식 수정
def _create_new_encryption_key(self):
    # 올바른 32바이트 URL-safe base64 키 생성
    key = Fernet.generate_key()  # 이미 올바른 형식
    assert len(key) == 44, f"Fernet 키는 44바이트여야 함: {len(key)}"

    # 검증 후 저장
    success = self._save_encryption_key_to_db(key)
    if success:
        # 즉시 검증
        loaded = self._load_encryption_key_from_db()
        assert loaded == key, "저장/로드 검증 실패"

# 2. Repository 검증 강화
def save_key(self, key_type: str, key_data: bytes) -> bool:
    # 입력 검증
    if key_type == "encryption":
        if len(key_data) != 44:
            raise ValueError(f"암호화 키는 44바이트여야 함: {len(key_data)}")
        # Fernet 형식 검증
        try:
            Fernet(key_data)
        except ValueError as e:
            raise ValueError(f"올바르지 않은 Fernet 키: {e}")

    # 저장 후 즉시 검증
    result = self._execute_save(key_type, key_data)
    if result:
        loaded = self.load_key(key_type)
        if loaded != key_data:
            raise RuntimeError(f"저장/로드 불일치: 저장{len(key_data)} != 로드{len(loaded or b'')}")

    return result
```

### Phase 2: Connection 관리 통합 (3-5일)

#### 🔄 DatabaseManager 리팩터링

```python
# 1. 단일 진실의 원천 (Single Source of Truth)
class MasterDatabaseManager:
    """모든 DB 연결의 중앙 집중 관리"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

# 2. Container 통합
class ApplicationContainer(containers.DeclarativeContainer):
    # 단일 DB 관리자
    master_db_manager = providers.Singleton(MasterDatabaseManager)

    # 모든 Repository가 동일한 관리자 사용
    secure_keys_repository = providers.Singleton(
        SqliteSecureKeysRepository,
        db_manager=master_db_manager
    )
```

### Phase 3: DB 엔진 추상화 (1-2주)

#### 🏗️ Engine Factory 구현

```python
# 1. 점진적 마이그레이션 지원
class HybridDatabaseEngine:
    """SQLite → PostgreSQL 점진적 전환 지원"""

    def __init__(self, primary_engine: str = "sqlite", fallback_engine: str = None):
        self.primary = DatabaseEngineFactory.create(primary_engine)
        self.fallback = DatabaseEngineFactory.create(fallback_engine) if fallback_engine else None

    def execute_query(self, query: str, params: tuple = ()):
        try:
            return self.primary.execute(query, params)
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary engine failed, falling back: {e}")
                return self.fallback.execute(query, params)
            raise

# 2. 설정 기반 전환
# config/database_config.yaml
migration:
  enabled: true
  source_engine: "sqlite"
  target_engine: "postgresql"
  rollback_enabled: true
```

### Phase 4: PostgreSQL 전체 마이그레이션 (2-3주)

#### 🚀 Production 전환 준비

```python
# 1. 데이터 마이그레이션 도구
class ProductionMigrationTool:
    def migrate_live_system(self):
        # 1. 백업 생성
        self._create_full_backup()

        # 2. PostgreSQL 환경 준비
        self._setup_postgresql()

        # 3. 스키마 마이그레이션
        self._migrate_schema()

        # 4. 데이터 이전 (배치 처리)
        self._migrate_data_in_batches()

        # 5. 검증 및 성능 테스트
        self._validate_and_benchmark()

        # 6. 애플리케이션 설정 전환
        self._switch_application_config()

# 2. 롤백 계획
class MigrationRollbackManager:
    def rollback_to_sqlite(self):
        # 안전한 롤백 프로세스
        pass
```

---

## 📊 예상 효과 및 리스크

### 🎯 기대 효과

#### 1. **즉시 해결되는 문제들**

- ✅ API 키 저장/로드 문제 완전 해결
- ✅ 44bytes → 34bytes 데이터 불일치 제거
- ✅ Fernet 암호화 오류 해결
- ✅ Repository 데이터 일관성 보장

#### 2. **아키텍처 개선 효과**

- 🏗️ DB 엔진 독립성 확보 (SQLite ↔ PostgreSQL 자유 전환)
- 🔧 Connection Pool 성능 향상 (20-30% 쿼리 응답 개선)
- 🛡️ 트랜잭션 격리 수준 보장 (데이터 정합성)
- 📈 확장성 확보 (MySQL, Oracle 등 추가 지원 가능)

#### 3. **운영 효율성**

- 🔄 무중단 DB 엔진 전환 가능
- 📊 성능 모니터링 및 튜닝 기반 구축
- 🛠️ 마이그레이션 도구로 운영 리스크 최소화

### ⚠️ 리스크 및 완화 방안

#### 1. **기술적 리스크**

| 리스크 | 확률 | 영향도 | 완화 방안 |
|--------|------|--------|-----------|
| 기존 코드 호환성 문제 | 중간 | 높음 | 호환성 레이어 + 단계적 전환 |
| 데이터 마이그레이션 실패 | 낮음 | 높음 | 전체 백업 + 롤백 계획 |
| 성능 저하 | 중간 | 중간 | 벤치마킹 + 점진적 최적화 |

#### 2. **일정 리스크**

- **Phase 1 (긴급)**: 리스크 낮음 - 기존 코드 최소 변경
- **Phase 2-3**: 리스크 중간 - 충분한 테스트 기간 확보
- **Phase 4**: 리스크 높음 - 단계별 전환으로 완화

#### 3. **완화 전략**

```python
# 1. 안전한 전환을 위한 Feature Flag
class DatabaseEngineSelector:
    def get_engine(self):
        if os.getenv("FORCE_SQLITE") == "true":
            return "sqlite"  # 긴급시 SQLite로 강제 전환
        return config.database.engine

# 2. 실시간 모니터링
class DatabaseHealthMonitor:
    def monitor_migration(self):
        # 마이그레이션 중 실시간 상태 모니터링
        # 문제 감지 시 자동 롤백 트리거
        pass
```

---

## 🎯 결론 및 권장사항

### 🚨 즉시 조치 필요사항 (우선순위 재조정)

1. **Path 관리 서비스 완전 구성** (Priority: P0) 🔥 최우선
   - UniversalPathService 구현 및 기존 시스템 통합
   - 환경별 DB 경로 자동 전환 (개발/테스트/프로덕션)
   - candle_test_07_comprehensive.py 연동 검증
   - 예상 소요: 4-6시간

2. **API 키 저장 문제 긴급 수정** (Priority: P1)
   - Fernet 키 형식 검증 강화
   - Repository 저장/로드 일관성 검증 추가
   - Path 서비스 통합 후 안정된 경로 기반 수정
   - 예상 소요: 4-6시간

3. **DatabaseManager 인스턴스 통합** (Priority: P2)
   - Path 서비스 기반 단일 인스턴스 관리
   - Container DI를 통한 의존성 주입 통일
   - CandleDataProvider 연동 검증 병행
   - 예상 소요: 1-2일

### 🏗️ 중장기 아키텍처 로드맵

1. **DB 엔진 추상화 레이어 구축** (Priority: P2)
   - 다중 DB 엔진 지원 아키텍처
   - Query Builder & Migration Framework
   - 예상 소요: 2-3주

2. **PostgreSQL 전환 준비** (Priority: P3)
   - Production 마이그레이션 도구 개발
   - 성능 벤치마킹 & 튜닝
   - 예상 소요: 3-4주

### 💡 핵심 설계 원칙

#### 1. **점진적 전환 (Gradual Migration)**

- 기존 시스템 무중단 운영 보장
- 각 단계별 롤백 계획 수립
- Feature Flag 기반 안전한 전환

#### 2. **DB 엔진 독립성 (Database Agnostic)**

- Repository 패턴 강화
- Query Builder로 SQL 방언 추상화
- Configuration-Driven Engine Selection

#### 3. **운영 안정성 우선 (Operations First)**

- 충분한 테스트 & 검증 절차
- 실시간 모니터링 & 알람 시스템
- 자동화된 백업 & 복구 프로세스

---

**다음 단계**:

1. **Path 관리 서비스 완전 구성** (4-6시간) - Database Manager 개선의 필수 기반
2. **candle_test_07_comprehensive.py 검증** - 실시간 동작 확인
3. **API 키 저장 문제 수정** - 안정된 Path 기반 수정
4. **단계별 Database Manager 아키텍처 개선** - CandleDataProvider 연동 검증 병행

---

**문서 유형**: 🏗️ 시스템 아키텍처 분석 보고서
**우선순위**: 🔥 최우선 (운영 안정성 + 확장성 확보)
**예상 완료**: Phase 1 (2일) + Phase 2-4 (6-8주)
**핵심 가치**: 안정적 운영 + DB 엔진 독립성 + 확장 가능한 아키텍처
