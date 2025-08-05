# 🔧 Infrastructure Repository 구현 문제해결 가이드

> **목적**: Infrastructure Repository 구현 시 발생할 수 있는 문제들과 해결 방법 제시
> **대상**: 주니어 개발자, 문제 해결이 필요한 개발자
> **갱신**: 2025-08-05

## 🚨 주요 문제 상황 및 해결 방법

### **Problem 1: Domain Entity 없이 Infrastructure 구현하기**

#### 🎯 **문제 상황**
```
❌ 상황: Domain Layer가 아직 완성되지 않았는데 Infrastructure를 구현해야 함
❌ 오류: "Strategy 클래스를 import할 수 없습니다"
❌ 딜레마: Infrastructure 구현을 미룰 수 없고, Domain Entity도 없음
```

#### ✅ **해결 방법: Mock 패턴 적용**

**1단계: Mock Entity 클래스 생성**
```python
# infrastructure/mappers/strategy_mapper.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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

**2단계: Repository에서 Mock Entity 사용**
```python
# infrastructure/repositories/sqlite_strategy_repository.py
from ..mappers.strategy_mapper import MockStrategy  # 실제 Strategy 대신

class SqliteStrategyRepository:
    def save(self, strategy: MockStrategy) -> str:  # type: ignore
        # MockStrategy를 사용하되 type: ignore로 타입 체커 우회
        pass
```

**3단계: 향후 마이그레이션 준비**
```python
# Domain Entity 완성 후 교체 방법
# 1. MockStrategy → Strategy import 변경
# 2. type: ignore 주석 제거
# 3. 인터페이스 호환성 검증
```

### **Problem 2: SQLite 동시성 및 성능 문제**

#### 🎯 **문제 상황**
```
❌ 증상: "database is locked" 오류 발생
❌ 증상: 동시 요청 시 성능 저하
❌ 증상: 트랜잭션 데드락 발생
```

#### ✅ **해결 방법: SQLite 최적화 설정**

**1단계: WAL 모드 활성화**
```python
def _optimize_connection(self, conn: sqlite3.Connection) -> None:
    """SQLite 연결 최적화 - 동시성 문제 해결"""

    # 🚨 핵심: Write-Ahead Logging 모드
    conn.execute("PRAGMA journal_mode=WAL")      # 읽기/쓰기 동시성 대폭 향상

    # 성능 최적화
    conn.execute("PRAGMA synchronous=NORMAL")    # 완전 동기화 → 일반 동기화
    conn.execute("PRAGMA cache_size=10000")      # 캐시 크기 증가 (기본 2000)
    conn.execute("PRAGMA temp_store=memory")     # 임시 데이터 메모리 저장
    conn.execute("PRAGMA mmap_size=268435456")   # 메모리 맵 크기 (256MB)

    # Row 접근 최적화
    conn.row_factory = sqlite3.Row               # dict-like 접근 지원
```

**2단계: Thread-Local 연결 관리**
```python
import threading

class DatabaseManager:
    def __init__(self):
        self._connections = threading.local()  # 스레드별 독립 연결

    def get_connection(self, db_name: str) -> sqlite3.Connection:
        """스레드 안전 연결 획득"""
        if not hasattr(self._connections, db_name):
            conn = sqlite3.connect(self._db_paths[db_name])
            self._optimize_connection(conn)
            setattr(self._connections, db_name, conn)

        return getattr(self._connections, db_name)
```

**3단계: 안전한 트랜잭션 패턴**
```python
from contextlib import contextmanager

@contextmanager
def transaction(self, db_name: str):
    """데드락 방지 트랜잭션"""
    conn = self.get_connection(db_name)
    try:
        # 트랜잭션 시작
        conn.execute("BEGIN IMMEDIATE")  # 즉시 배타적 락 획득
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        # 🚨 중요: 원본 예외를 다시 발생시켜 호출자가 처리
        raise DatabaseTransactionError(f"트랜잭션 실패: {e}") from e
```

### **Problem 3: Mock과 실제 Entity 간 인터페이스 불일치**

#### 🎯 **문제 상황**
```
❌ 증상: Domain Entity 완성 후 Repository가 동작하지 않음
❌ 증상: 메서드 시그니처 불일치로 런타임 오류
❌ 증상: 타입 체커에서 지속적인 경고
```

#### ✅ **해결 방법: 인터페이스 호환성 보장**

**1단계: Domain Interface 사전 정의**
```python
# domain/entities/strategy_interface.py
from abc import ABC, abstractmethod
from typing import Protocol

class StrategyProtocol(Protocol):
    """Strategy Entity가 구현해야 할 최소 인터페이스"""
    strategy_id: str
    name: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

**2단계: Mock Entity에서 Protocol 구현**
```python
@dataclass
class MockStrategy:
    """StrategyProtocol 완전 구현"""
    strategy_id: str = "mock_strategy"
    name: str = "Mock Strategy"
    description: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        # Protocol에서 요구하는 모든 속성 초기화
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    # Protocol 검증
    def _verify_protocol_compliance(self):
        """컴파일 타임에 Protocol 준수 확인"""
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            # 타입 체커만 확인, 런타임에는 실행되지 않음
            _: StrategyProtocol = self
```

**3단계: Repository에서 Protocol 활용**
```python
from typing import Union
from ..domain.entities.strategy_interface import StrategyProtocol

class SqliteStrategyRepository:
    def save(self, strategy: StrategyProtocol) -> str:
        """Protocol 기반으로 Mock과 실제 Entity 모두 지원"""
        # strategy.strategy_id, strategy.name 등 Protocol 정의 속성만 사용
        pass
```

### **Problem 4: 복잡한 쿼리 동적 생성 문제**

#### 🎯 **문제 상황**
```
❌ 증상: WHERE 절이 조건에 따라 달라져야 함
❌ 증상: SQL Injection 취약점 위험
❌ 증상: 쿼리 문자열 조합이 복잡하고 오류 발생
```

#### ✅ **해결 방법: 안전한 동적 쿼리 빌더**

**1단계: QueryBuilder 클래스 생성**
```python
class QueryBuilder:
    """안전한 동적 쿼리 생성기"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self.conditions = []
        self.params = []
        self.order_by = []
        self.limit_count = None

    def where(self, column: str, operator: str, value: Any) -> 'QueryBuilder':
        """WHERE 조건 추가 (SQL Injection 방지)"""
        allowed_operators = ['=', '!=', '>', '>=', '<', '<=', 'LIKE', 'IN']
        if operator not in allowed_operators:
            raise ValueError(f"허용되지 않는 연산자: {operator}")

        self.conditions.append(f"{column} {operator} ?")
        self.params.append(value)
        return self

    def where_in(self, column: str, values: List[Any]) -> 'QueryBuilder':
        """WHERE IN 절 추가"""
        placeholders = ','.join(['?'] * len(values))
        self.conditions.append(f"{column} IN ({placeholders})")
        self.params.extend(values)
        return self

    def order_by_desc(self, column: str) -> 'QueryBuilder':
        """정렬 조건 추가"""
        self.order_by.append(f"{column} DESC")
        return self

    def limit(self, count: int) -> 'QueryBuilder':
        """제한 조건 추가"""
        self.limit_count = count
        return self

    def build_select(self, columns: str = "*") -> Tuple[str, List[Any]]:
        """SELECT 쿼리 생성"""
        query_parts = [f"SELECT {columns} FROM {self.table_name}"]

        if self.conditions:
            query_parts.append("WHERE " + " AND ".join(self.conditions))

        if self.order_by:
            query_parts.append("ORDER BY " + ", ".join(self.order_by))

        if self.limit_count:
            query_parts.append(f"LIMIT {self.limit_count}")

        return " ".join(query_parts), self.params
```

**2단계: Repository에서 QueryBuilder 활용**
```python
def find_strategies_by_criteria(self, criteria: Dict[str, Any]) -> List[MockStrategy]:
    """동적 조건 검색 - 안전하고 유연함"""

    builder = QueryBuilder("strategies")

    # 조건별 쿼리 구성
    if criteria.get('is_active') is not None:
        builder.where('is_active', '=', criteria['is_active'])

    if criteria.get('name_pattern'):
        builder.where('strategy_name', 'LIKE', f"%{criteria['name_pattern']}%")

    if criteria.get('risk_level_max'):
        builder.where('risk_level', '<=', criteria['risk_level_max'])

    if criteria.get('tags'):
        # JSON 태그 검색
        for tag in criteria['tags']:
            builder.where('tags', 'LIKE', f'%"{tag}"%')

    # 쿼리 생성 및 실행
    query, params = builder.order_by_desc('created_at').limit(100).build_select()

    try:
        conn = self._db_manager.get_connection('strategies')
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        return [self._mapper.to_entity(row) for row in rows]

    except Exception as e:
        logger.error(f"❌ 전략 검색 실패: {e}")
        raise RepositoryError(f"검색 실패: {e}") from e
```

### **Problem 5: 테스트에서 Mock과 실제 DB 의존성 격리**

#### 🎯 **문제 상황**
```
❌ 증상: 테스트가 실제 데이터베이스를 수정함
❌ 증상: 테스트 간 데이터 오염 발생
❌ 증상: CI/CD에서 데이터베이스 설정 복잡성
```

#### ✅ **해결 방법: Mock을 활용한 완전한 격리**

**1단계: pytest fixture로 Mock 환경 구성**
```python
# tests/infrastructure/conftest.py
import pytest
from unittest.mock import Mock, MagicMock

@pytest.fixture
def mock_db_manager():
    """완전히 격리된 DatabaseManager Mock"""
    mock = Mock()

    # transaction context manager 설정
    mock_conn = Mock()
    mock.transaction.return_value.__enter__ = Mock(return_value=mock_conn)
    mock.transaction.return_value.__exit__ = Mock(return_value=None)

    # get_connection 설정
    mock.get_connection.return_value = mock_conn

    return mock

@pytest.fixture
def repository(mock_db_manager):
    """테스트용 Repository 인스턴스"""
    from upbit_auto_trading.infrastructure.repositories import SqliteStrategyRepository
    return SqliteStrategyRepository(mock_db_manager)
```

**2단계: Mock 동작 상세 설정**
```python
def test_save_strategy_success(repository, mock_db_manager):
    """전략 저장 성공 테스트 - 완전 격리"""

    # Given: Mock 동작 설정
    mock_conn = Mock()
    mock_db_manager.transaction.return_value.__enter__.return_value = mock_conn
    mock_conn.execute.return_value = None  # INSERT 성공

    strategy = MockStrategy(
        strategy_id="test_strategy",
        name="Test Strategy",
        description="Test Description"
    )

    # When: Repository 메서드 호출
    result = repository.save(strategy)

    # Then: Mock 호출 검증
    assert result == "test_strategy"
    mock_db_manager.transaction.assert_called_once_with('strategies')
    mock_conn.execute.assert_called_once()

    # SQL 쿼리 검증
    call_args = mock_conn.execute.call_args
    sql_query = call_args[0][0]
    sql_params = call_args[0][1]

    assert "INSERT OR REPLACE INTO strategies" in sql_query
    assert "test_strategy" in sql_params
```

**3단계: 에러 시나리오 테스트**
```python
def test_save_strategy_database_error(repository, mock_db_manager):
    """데이터베이스 오류 시나리오 테스트"""

    # Given: Mock에서 예외 발생 설정
    mock_conn = Mock()
    mock_conn.execute.side_effect = sqlite3.Error("DB connection failed")
    mock_db_manager.transaction.return_value.__enter__.return_value = mock_conn

    strategy = MockStrategy()

    # When & Then: 예외 발생 확인
    with pytest.raises(RepositoryError) as exc_info:
        repository.save(strategy)

    assert "전략 저장 실패" in str(exc_info.value)
    assert "DB connection failed" in str(exc_info.value)
```

## 🔍 문제 예방을 위한 Best Practices

### ✅ **개발 초기 단계**

1. **Domain Interface 먼저 설계**: 구현 전에 인터페이스 명확히 정의
2. **Mock 패턴 일관성**: 실제 Entity와 동일한 메서드 시그니처 유지
3. **트랜잭션 패턴 표준화**: 모든 쓰기 연산은 트랜잭션 Context Manager 사용

### ✅ **구현 단계**

1. **점진적 개발**: 한 번에 모든 메서드를 구현하지 말고 단계별 접근
2. **테스트 주도 개발**: 구현 전에 테스트 케이스 먼저 작성
3. **에러 처리 일관성**: 모든 Repository 메서드에서 동일한 예외 처리 패턴

### ✅ **테스트 단계**

1. **완전한 격리**: Mock을 활용해 실제 데이터베이스와 완전 분리
2. **에지 케이스 포함**: 정상 케이스뿐만 아니라 예외 상황도 반드시 테스트
3. **성능 테스트**: 동시성 안전성과 메모리 누수 확인

## 🛠️ 디버깅 도구 및 방법

### 🔍 **로깅 시스템 활용**

```python
import logging

# Repository 전용 로거 설정
logger = logging.getLogger('infrastructure.repository')

class SqliteStrategyRepository:
    def save(self, strategy: MockStrategy) -> str:
        logger.info(f"✅ 전략 저장 시작: {strategy.strategy_id}")

        try:
            # 구현 로직...
            logger.info(f"✅ 전략 저장 성공: {strategy.strategy_id}")
            return strategy.strategy_id

        except Exception as e:
            logger.error(f"❌ 전략 저장 실패: {strategy.strategy_id}, 오류: {e}")
            raise
```

### 🔍 **SQL 쿼리 디버깅**

```python
def _execute_query_with_debug(self, conn, query: str, params: Tuple):
    """쿼리 실행 전 디버그 로깅"""
    logger.debug(f"🔍 SQL Query: {query}")
    logger.debug(f"🔍 Parameters: {params}")

    try:
        result = conn.execute(query, params)
        logger.debug(f"✅ Query 실행 성공")
        return result
    except Exception as e:
        logger.error(f"❌ Query 실행 실패: {e}")
        raise
```

### 🔍 **성능 모니터링**

```python
import time
from functools import wraps

def monitor_performance(func):
    """Repository 메서드 성능 모니터링 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"⚡ {func.__name__} 실행 시간: {execution_time:.4f}초")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {func.__name__} 실패 ({execution_time:.4f}초): {e}")
            raise
    return wrapper

class SqliteStrategyRepository:
    @monitor_performance
    def save(self, strategy: MockStrategy) -> str:
        # 구현...
```

## 📚 추가 참고 자료

- [SQLite 최적화 가이드](https://www.sqlite.org/optoverview.html)
- [Python threading 모듈 문서](https://docs.python.org/3/library/threading.html)
- [pytest Mock 사용법](https://docs.python.org/3/library/unittest.mock.html)
- [DDD Repository 패턴](../../../COMPONENT_ARCHITECTURE.md)

---

**💡 핵심 메시지**: 문제를 **예방**하는 것이 해결하는 것보다 효율적이다. 초기 설계와 테스트가 핵심!
