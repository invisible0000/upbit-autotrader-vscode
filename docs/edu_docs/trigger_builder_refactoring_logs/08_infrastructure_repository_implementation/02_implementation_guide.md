# 🛠️ Infrastructure Repository 구현 가이드

> **목적**: DDD 기반 Infrastructure Layer Repository 구현을 위한 단계별 실행 가이드
> **대상**: 주니어 개발자, Infrastructure Layer 구현 담당자
> **갱신**: 2025-08-05

## 📋 구현 준비사항

### 🔧 **필수 선행 조건**
- [X] Domain Layer Repository 인터페이스 정의 완료
- [X] 기존 데이터베이스 스키마 분석 완료
- [X] DDD 아키텍처 이해 (Aggregate, Entity, Value Object)
- [X] Python 타입 힌트 및 Abstract Base Class 숙지

### 📦 **필요한 도구 및 라이브러리**
```python
# requirements.txt
sqlite3      # 내장 모듈 (데이터베이스)
pytest       # 테스트 프레임워크
unittest.mock # Mock 객체 생성
typing       # 타입 힌트
abc          # 추상 기본 클래스
dataclasses  # 데이터 클래스 (Mock Entity용)
```

## 🎯 Step-by-Step 구현 가이드

### **Step 1: 프로젝트 구조 설정**

#### 1.1 폴더 구조 생성
```bash
mkdir -p upbit_auto_trading/infrastructure/repositories
mkdir -p upbit_auto_trading/infrastructure/database
mkdir -p upbit_auto_trading/infrastructure/mappers
mkdir -p tests/infrastructure/repositories
```

#### 1.2 패키지 초기화 파일 작성
```python
# upbit_auto_trading/infrastructure/__init__.py
"""
Infrastructure Layer - 외부 시스템과의 연동을 담당

주요 구성요소:
- repositories/: Domain Repository 인터페이스 구현체
- database/: 데이터베이스 연결 및 트랜잭션 관리
- mappers/: Entity ↔ Database Record 변환
"""

from .repositories.repository_container import RepositoryContainer
from .database.database_manager import DatabaseManager

__all__ = ['RepositoryContainer', 'DatabaseManager']
```

### **Step 2: 데이터베이스 연결 관리자 구현**

#### 2.1 DatabaseManager 클래스 기본 구조
```python
# upbit_auto_trading/infrastructure/database/database_manager.py
import sqlite3
import threading
from contextlib import contextmanager
from typing import List, Tuple, Any, Optional
from pathlib import Path

class DatabaseManager:
    """멀티 SQLite 데이터베이스 연결 관리자"""

    def __init__(self):
        self._connections = threading.local()
        self._db_paths = {
            'settings': Path('data/settings.sqlite3'),
            'strategies': Path('data/strategies.sqlite3'),
            'market_data': Path('data/market_data.sqlite3')
        }

    def get_connection(self, db_name: str) -> sqlite3.Connection:
        """데이터베이스 연결 획득 (스레드 로컬)"""
        # 구현 세부사항...
```

#### 2.2 핵심 구현 포인트
```python
# 🚨 필수: SQLite 성능 최적화 설정
def _optimize_connection(self, conn: sqlite3.Connection) -> None:
    """SQLite 연결 최적화"""
    conn.execute("PRAGMA journal_mode=WAL")      # 동시성 향상
    conn.execute("PRAGMA synchronous=NORMAL")    # 성능 향상
    conn.execute("PRAGMA cache_size=10000")      # 메모리 캐시
    conn.execute("PRAGMA temp_store=memory")     # 임시 저장소
    conn.row_factory = sqlite3.Row               # dict-like 접근

# 🚨 필수: 트랜잭션 Context Manager
@contextmanager
def transaction(self, db_name: str):
    """안전한 트랜잭션 처리"""
    conn = self.get_connection(db_name)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

### **Step 3: Entity-Database 매퍼 구현**

#### 3.1 Mock Entity 클래스 작성
```python
# upbit_auto_trading/infrastructure/mappers/strategy_mapper.py
@dataclass
class MockStrategy:
    """Domain Strategy Entity 완성 전까지 호환성 보장"""
    strategy_id: str = "mock_strategy"
    name: str = "Mock Strategy"
    description: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
```

#### 3.2 매퍼 클래스 구현 패턴
```python
class StrategyMapper:
    """Strategy Entity ↔ Database Record 변환"""

    @staticmethod
    def to_database_record(strategy: MockStrategy) -> Tuple:
        """Entity → Database 튜플 변환"""
        return (
            strategy.strategy_id,
            strategy.name,
            strategy.description,
            strategy.is_active,
            strategy.created_at.isoformat(),
            strategy.updated_at.isoformat()
        )

    @staticmethod
    def to_entity(row: sqlite3.Row) -> MockStrategy:
        """Database Row → Entity 변환"""
        return MockStrategy(
            strategy_id=row['id'],
            name=row['strategy_name'],
            description=row['description'] or "",
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
```

### **Step 4: Repository 구현**

#### 4.1 Strategy Repository 기본 구조
```python
# upbit_auto_trading/infrastructure/repositories/sqlite_strategy_repository.py
from typing import List, Optional
from ...domain.repositories.strategy_repository import StrategyRepository
from ..database.database_manager import DatabaseManager
from ..mappers.strategy_mapper import MockStrategy, StrategyMapper

class SqliteStrategyRepository(StrategyRepository):
    """SQLite 기반 Strategy Repository 구현"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self._db_manager = db_manager or DatabaseManager()
        self._mapper = StrategyMapper()

    def save(self, strategy: MockStrategy) -> str:
        """전략 저장 (Upsert 패턴)"""
        # 구현 세부사항...

    def find_by_id(self, strategy_id: str) -> Optional[MockStrategy]:
        """ID로 전략 조회"""
        # 구현 세부사항...
```

#### 4.2 핵심 구현 패턴들

**🎯 Upsert 패턴 (INSERT OR REPLACE)**
```python
def save(self, strategy: MockStrategy) -> str:
    try:
        strategy_data = self._mapper.to_database_record(strategy)
        query = """
        INSERT OR REPLACE INTO strategies
        (id, strategy_name, description, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        with self._db_manager.transaction('strategies') as conn:
            conn.execute(query, strategy_data)

        return strategy.strategy_id

    except Exception as e:
        # 상세한 에러 로깅
        raise RepositoryError(f"전략 저장 실패: {e}") from e
```

**🎯 동적 쿼리 생성 패턴**
```python
def find_strategies_by_criteria(self, criteria: Dict[str, Any]) -> List[MockStrategy]:
    """조건별 전략 검색"""
    conditions = []
    params = []

    # 동적 WHERE 절 생성
    if criteria.get('is_active') is not None:
        conditions.append("is_active = ?")
        params.append(criteria['is_active'])

    if criteria.get('name_pattern'):
        conditions.append("strategy_name LIKE ?")
        params.append(f"%{criteria['name_pattern']}%")

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = f"""
    SELECT * FROM strategies
    {where_clause}
    ORDER BY created_at DESC
    """

    # 실행 및 변환...
```

### **Step 5: Repository Container 구현**

#### 5.1 의존성 주입 컨테이너 패턴
```python
# upbit_auto_trading/infrastructure/repositories/repository_container.py
class RepositoryContainer:
    """Repository 의존성 주입 컨테이너"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # 싱글톤 패턴 구현
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._db_manager = DatabaseManager()
            self._repositories = {}
            self._initialized = True

    def get_strategy_repository(self) -> SqliteStrategyRepository:
        """Strategy Repository 획득 (Lazy Loading)"""
        if 'strategy' not in self._repositories:
            self._repositories['strategy'] = SqliteStrategyRepository(self._db_manager)
        return self._repositories['strategy']
```

### **Step 6: 테스트 구현**

#### 6.1 pytest 기반 단위 테스트 구조
```python
# tests/infrastructure/repositories/test_strategy_repository.py
import pytest
from unittest.mock import Mock, MagicMock
from upbit_auto_trading.infrastructure.repositories import SqliteStrategyRepository

class TestSqliteStrategyRepository:

    @pytest.fixture
    def mock_db_manager(self):
        """DatabaseManager Mock 픽스처"""
        mock = Mock()
        mock.transaction.return_value.__enter__ = Mock()
        mock.transaction.return_value.__exit__ = Mock(return_value=None)
        return mock

    @pytest.fixture
    def repository(self, mock_db_manager):
        """테스트용 Repository 인스턴스"""
        return SqliteStrategyRepository(mock_db_manager)

    def test_save_strategy_success(self, repository, mock_db_manager):
        """전략 저장 성공 테스트"""
        # Given
        strategy = create_mock_strategy()
        mock_conn = Mock()
        mock_db_manager.transaction.return_value.__enter__.return_value = mock_conn

        # When
        result = repository.save(strategy)

        # Then
        assert result == strategy.strategy_id
        mock_conn.execute.assert_called_once()
```

#### 6.2 주요 테스트 케이스들
```python
# 🚨 필수 테스트 케이스들
def test_save_strategy_success():           # 정상 저장
def test_save_strategy_database_error():   # DB 오류 처리
def test_find_by_id_exists():             # 존재하는 데이터 조회
def test_find_by_id_not_exists():         # 존재하지 않는 데이터
def test_find_all_empty_database():       # 빈 데이터베이스 조회
def test_delete_strategy_success():       # 정상 삭제
def test_concurrent_access_safety():      # 동시성 안전성
```

## 🎯 구현 시 주의사항

### 🚨 **반드시 지켜야 할 원칙들**

1. **Domain 의존성 역전**: Infrastructure → Domain 의존 (반대 X)
2. **Mock 패턴 일관성**: 실제 Entity와 동일한 인터페이스 유지
3. **트랜잭션 안전성**: 모든 쓰기 연산은 트랜잭션 내에서 실행
4. **에러 처리 명확성**: 구체적인 예외 메시지와 로깅

### ⚠️ **자주 하는 실수들**

```python
# ❌ 잘못된 방식: Domain Entity에 Infrastructure 의존성
class Strategy:
    def save_to_database(self):  # Domain에 Infrastructure 로직
        pass

# ✅ 올바른 방식: Infrastructure에서 Domain 호출
class SqliteStrategyRepository:
    def save(self, strategy: Strategy):  # Infrastructure에서 처리
        pass

# ❌ 잘못된 방식: 트랜잭션 없는 쓰기 연산
def save(self, strategy):
    conn = self._db_manager.get_connection('strategies')
    conn.execute(query, params)  # 롤백 불가능

# ✅ 올바른 방식: 트랜잭션 Context Manager 사용
def save(self, strategy):
    with self._db_manager.transaction('strategies') as conn:
        conn.execute(query, params)  # 자동 롤백 지원
```

### 💡 **성능 최적화 팁**

1. **Connection Pooling**: 스레드별 연결 재사용
2. **Lazy Loading**: Repository 인스턴스 필요 시점 생성
3. **쿼리 최적화**: 인덱스 활용, WHERE 절 순서 최적화
4. **배치 처리**: 대량 데이터는 배치 INSERT 사용

## 🔍 검증 및 테스트 방법

### ✅ **구현 완료 체크리스트**

- [ ] DatabaseManager 클래스 구현 완료
- [ ] 3-DB 연결 설정 (settings, strategies, market_data)
- [ ] SQLite 성능 최적화 적용 (WAL, cache_size 등)
- [ ] Entity ↔ Database 매퍼 구현
- [ ] Mock Pattern으로 Domain 호환성 보장
- [ ] Repository 클래스 모든 메서드 구현
- [ ] RepositoryContainer 의존성 주입 구현
- [ ] 포괄적인 단위 테스트 작성 (pytest)
- [ ] 에러 처리 및 로깅 구현
- [ ] 동시성 안전성 검증

### 🧪 **테스트 실행 방법**

```bash
# 전체 테스트 실행
python -m pytest tests/infrastructure/ -v

# 특정 Repository 테스트
python -m pytest tests/infrastructure/repositories/test_strategy_repository.py -v

# 커버리지 포함 테스트
python -m pytest tests/infrastructure/ --cov=upbit_auto_trading.infrastructure --cov-report=html
```

### 📊 **성능 벤치마크**

```python
# 성능 측정 예시
import time

def benchmark_repository_operations():
    repo = get_strategy_repository()

    # 저장 성능 측정
    start_time = time.time()
    for i in range(1000):
        strategy = create_test_strategy(f"strategy_{i}")
        repo.save(strategy)
    save_time = time.time() - start_time

    print(f"1000개 전략 저장 시간: {save_time:.2f}초")
```

## 📚 관련 문서 및 참고 자료

- [Domain Repository 인터페이스](../../../domain/repositories/)
- [DDD 아키텍처 가이드](../../../COMPONENT_ARCHITECTURE.md)
- [데이터베이스 스키마](../../../DB_SCHEMA.md)
- [pytest 테스트 가이드](../../../VSCODE_PYTEST_ENVIRONMENT_TROUBLESHOOTING.md)

---

**💡 핵심 메시지**: Infrastructure Repository 구현은 **점진적 개발**과 **철저한 테스트**가 성공의 핵심이다!
