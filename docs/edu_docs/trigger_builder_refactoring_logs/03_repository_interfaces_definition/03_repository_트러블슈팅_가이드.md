# 🔧 Repository 패턴 트러블슈팅 가이드

> **목적**: Repository 인터페이스 정의 과정에서 발생한 주요 문제들과 실무 해결책 모음  
> **대상**: LLM 에이전트, Python 개발자, DDD 아키텍처 구현자  
> **갱신**: 2025-08-04

## 🎯 트러블슈팅 개요

Repository 패턴을 DDD 아키텍처에 적용하면서 마주한 **실제 문제들과 검증된 해결책**을 정리합니다.

## 🚨 빈발 문제 TOP 10

### 1. 순환 의존성 (Circular Import)

#### ❌ 문제 상황
```python
# domain/repositories/strategy_repository.py
from upbit_auto_trading.domain.entities.strategy import Strategy  # Import Error!

# domain/entities/strategy.py  
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository  # Import Error!
```

#### ✅ 해결책: TYPE_CHECKING 활용
```python
# domain/repositories/strategy_repository.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from upbit_auto_trading.domain.entities.strategy import Strategy
    from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId

# 메서드 시그니처에서 문자열 타입 힌트 사용
def save(self, entity: 'Strategy') -> 'Strategy':
    pass

def find_by_id(self, entity_id: 'StrategyId') -> Optional['Strategy']:
    pass
```

#### 🔍 핵심 포인트
- `TYPE_CHECKING`은 타입 검사 시에만 import 실행
- 런타임에서는 import하지 않아 순환 의존성 방지
- 문자열 타입 힌트로 지연 평가 활용

### 2. Mock 테스트 시 AttributeError

#### ❌ 문제 상황
```python
# 테스트 실행 시 오류 발생
mock_repo = Mock()
mock_repo.save()  # AttributeError: Mock object has no attribute 'save'
```

#### ✅ 해결책: spec 매개변수 활용
```python
from unittest.mock import Mock
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository

# spec으로 인터페이스 계약 강제
mock_repo = Mock(spec=StrategyRepository)

# 이제 존재하지 않는 메서드 호출 시 AttributeError 발생
try:
    mock_repo.nonexistent_method()  # AttributeError 발생
except AttributeError:
    print("올바른 에러 감지!")

# 존재하는 메서드는 정상 동작
mock_repo.save.return_value = Mock()
result = mock_repo.save(Mock())
```

#### 🔍 핵심 포인트
- `Mock(spec=Interface)`로 인터페이스 계약 검증
- 존재하지 않는 메서드 호출 시 즉시 AttributeError
- 타입 안전성과 테스트 신뢰성 동시 확보

### 3. Generic TypeVar 혼란

#### ❌ 문제 상황
```python
# 여러 파일에서 동일 이름의 TypeVar 중복 정의
# file1.py
T = TypeVar('T')

# file2.py  
T = TypeVar('T')  # 혼란 유발

# 잘못된 Generic 사용
class BadRepository(Generic[str, int]):  # 구체 타입 사용
    pass
```

#### ✅ 해결책: 명확한 TypeVar 관리
```python
# domain/repositories/base_repository.py
from typing import TypeVar, Generic

# 명확한 이름의 TypeVar 정의
EntityType = TypeVar('EntityType')
EntityIdType = TypeVar('EntityIdType')

class BaseRepository(Generic[EntityType, EntityIdType], ABC):
    @abstractmethod
    def save(self, entity: EntityType) -> EntityType:
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: EntityIdType) -> Optional[EntityType]:
        pass

# 상속 시 구체 타입 특화
class StrategyRepository(BaseRepository['Strategy', 'StrategyId']):
    pass
```

#### 🔍 핵심 포인트
- 명확한 TypeVar 이름 사용 (`T` 대신 `EntityType`)
- Generic 상속 시 문자열 타입으로 특화
- 프로젝트 전체에서 일관된 TypeVar 관리

### 4. Repository 메서드 폭발 문제

#### ❌ 문제 상황
```python
# 모든 조합을 개별 메서드로 정의하려는 시도
def find_by_name_and_risk_level(self, name: str, risk_level: int): pass
def find_by_name_and_tags(self, name: str, tags: List[str]): pass
def find_by_risk_level_and_tags(self, risk_level: int, tags: List[str]): pass
def find_by_name_and_risk_level_and_tags(self, name: str, risk_level: int, tags: List[str]): pass
# ... 조합이 기하급수적으로 증가
```

#### ✅ 해결책: 검색 기준 객체 활용
```python
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class StrategySearchCriteria:
    """전략 검색 기준 통합 객체"""
    name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    risk_level: Optional[int] = None
    min_return: Optional[float] = None
    max_return: Optional[float] = None
    created_after: Optional[datetime] = None
    is_active: Optional[bool] = None

class StrategyRepository(BaseRepository['Strategy', 'StrategyId']):
    def search_strategies(self, criteria: StrategySearchCriteria) -> List['Strategy']:
        """범용 검색 메서드"""
        pass
    
    # 자주 사용되는 조합만 개별 메서드로 제공
    def find_active_strategies(self) -> List['Strategy']:
        """활성 전략만 조회 (자주 사용)"""
        return self.search_strategies(StrategySearchCriteria(is_active=True))
    
    def get_popular_strategies(self, limit: int = 10) -> List['Strategy']:
        """인기 전략 조회 (비즈니스 가치)"""
        pass
```

#### 🔍 핵심 포인트
- 검색 기준 객체로 조합 폭발 방지
- 자주 사용되는 패턴만 개별 메서드로 제공
- 비즈니스 가치가 있는 조합은 명시적 메서드 생성

### 5. Protocol vs ABC 선택 혼란

#### ❌ 문제 상황
```python
# 언제 Protocol을 쓰고 언제 ABC를 써야 할지 모호

# 모든 Repository에 ABC 사용
class SettingsRepository(ABC):  # 읽기 전용인데 ABC?
    pass

# 모든 Repository에 Protocol 사용
class StrategyRepository(Protocol):  # 상속이 필요한데 Protocol?
    pass
```

#### ✅ 해결책: 목적에 따른 구분
```python
# ABC: 상속 관계와 공통 기능이 있을 때
from abc import ABC, abstractmethod

class BaseRepository(Generic[T, ID], ABC):
    """공통 CRUD 기능을 제공하는 기본 클래스"""
    @abstractmethod
    def save(self, entity: T) -> T: pass

# Protocol: 덕 타이핑과 유연한 계약이 필요할 때
from typing_extensions import Protocol

class SettingsRepository(Protocol):
    """읽기 전용, 상속 불필요한 계약 정의"""
    def get_trading_variables(self) -> List['TradingVariable']: pass

# BaseRepository 상속: 공통 기능 + 특화 기능
class StrategyRepository(BaseRepository['Strategy', 'StrategyId']):
    """기본 CRUD + 전략 특화 메서드"""
    def find_by_name(self, name: str) -> Optional['Strategy']: pass
```

#### 🔍 선택 기준
- **ABC**: 공통 기능과 상속 관계가 필요할 때
- **Protocol**: 덕 타이핑과 유연한 계약이 필요할 때
- **상속 Repository**: ABC 기반으로 특화 기능 추가

### 6. Repository 생성자 의존성 주입 실패

#### ❌ 문제 상황
```python
# 도메인 서비스에서 Repository를 직접 생성
class StrategyCompatibilityService:
    def __init__(self):
        # 하드코딩된 Repository 생성
        self.db = sqlite3.connect("data/settings.sqlite3")
        self.settings_repo = SQLiteSettingsRepository(self.db)  # 구체 클래스 의존
```

#### ✅ 해결책: 인터페이스 기반 의존성 주입
```python
# 도메인 서비스는 인터페이스에만 의존
class StrategyCompatibilityService:
    def __init__(self, settings_repository: 'SettingsRepository'):
        """Repository 인터페이스를 주입받음"""
        self._settings_repository = settings_repository
    
    def check_compatibility(self, var1_id: str, var2_id: str) -> bool:
        """Repository를 통한 데이터 접근"""
        try:
            rules = self._settings_repository.get_compatibility_rules()
            return self._validate_rules(var1_id, var2_id, rules)
        except Exception as e:
            self._logger.error(f"호환성 검증 실패: {e}")
            return False

# 실제 사용 시 (Infrastructure Layer에서)
def create_compatibility_service() -> StrategyCompatibilityService:
    """팩토리 함수에서 의존성 조립"""
    db_connection = create_database_connection()
    settings_repo = SQLiteSettingsRepository(db_connection)
    return StrategyCompatibilityService(settings_repo)
```

#### 🔍 핵심 포인트
- 도메인 서비스는 Repository 인터페이스에만 의존
- 구체적인 Repository 구현은 Infrastructure Layer에서 주입
- 팩토리 함수나 DI 컨테이너로 의존성 조립

### 7. Repository 메서드 파라미터 과다

#### ❌ 문제 상황
```python
# 메서드 파라미터가 너무 많음
def update_strategy_metadata(
    self, 
    strategy_id: str,
    name: str,
    description: str,
    risk_level: int,
    expected_return: float,
    max_drawdown: float,
    tags: List[str],
    is_active: bool,
    last_modified: datetime
) -> bool:
    pass  # 파라미터 관리 불가
```

#### ✅ 해결책: 커맨드 객체 패턴
```python
@dataclass
class UpdateStrategyMetadataCommand:
    """전략 메타데이터 업데이트 명령"""
    strategy_id: 'StrategyId'
    name: Optional[str] = None
    description: Optional[str] = None
    risk_level: Optional[int] = None
    expected_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class StrategyRepository(BaseRepository['Strategy', 'StrategyId']):
    def update_strategy_metadata(self, command: UpdateStrategyMetadataCommand) -> bool:
        """커맨드 객체로 파라미터 단순화"""
        pass
    
    # 자주 사용하는 단순 업데이트는 개별 메서드
    def update_last_used_at(self, strategy_id: 'StrategyId') -> bool:
        """자주 사용되는 단순 업데이트"""
        pass
```

#### 🔍 핵심 포인트
- 복잡한 업데이트는 커맨드 객체 사용
- 선택적 파라미터는 Optional로 처리
- 자주 사용하는 단순 연산은 개별 메서드 유지

### 8. Repository 반환 타입 일관성 부족

#### ❌ 문제 상황
```python
# 반환 타입이 일관되지 않음
def find_by_id(self, strategy_id: str) -> Strategy:  # None 가능성 무시
def find_by_name(self, name: str) -> Optional[Strategy]:  # 일관성 없음
def find_all(self) -> List[Strategy]:  # 빈 리스트일 수 있음
def get_popular_strategies(self) -> Strategy:  # 복수인데 단수 반환?
```

#### ✅ 해결책: 일관된 반환 타입 규칙
```python
class StrategyRepository(BaseRepository['Strategy', 'StrategyId']):
    # 단일 조회: Optional[T] (없을 수 있음)
    def find_by_id(self, strategy_id: 'StrategyId') -> Optional['Strategy']:
        pass
    
    def find_by_name(self, name: str) -> Optional['Strategy']:
        pass
    
    # 복수 조회: List[T] (빈 리스트 가능)
    def find_all(self) -> List['Strategy']:
        pass
    
    def find_by_tags(self, tags: List[str]) -> List['Strategy']:
        pass
    
    def get_popular_strategies(self, limit: int = 10) -> List['Strategy']:
        pass
    
    # 존재 여부: bool
    def exists(self, strategy_id: 'StrategyId') -> bool:
        pass
    
    # 개수: int
    def count_all(self) -> int:
        pass
    
    # 저장/업데이트: 성공한 객체 반환 (실패 시 예외)
    def save(self, strategy: 'Strategy') -> 'Strategy':
        pass
    
    # 삭제: bool (성공 여부)
    def delete(self, strategy_id: 'StrategyId') -> bool:
        pass
```

#### 🔍 반환 타입 규칙
- **단일 조회**: `Optional[T]` (없을 수 있음)
- **복수 조회**: `List[T]` (빈 리스트 가능)
- **존재 여부**: `bool`
- **개수**: `int`
- **저장/업데이트**: 성공한 객체 반환
- **삭제**: `bool` (성공 여부)

### 9. Repository 테스트 데이터 관리

#### ❌ 문제 상황
```python
# 테스트마다 하드코딩된 테스트 데이터
def test_find_by_name():
    mock_repo = Mock(spec=StrategyRepository)
    # 하드코딩된 반환값
    mock_repo.find_by_name.return_value = Strategy(
        id="test-id",
        name="test-strategy",
        # ... 모든 속성 하드코딩
    )
```

#### ✅ 해결책: 테스트 데이터 팩토리
```python
# tests/factories/strategy_factory.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class StrategyTestDataFactory:
    """전략 테스트 데이터 팩토리"""
    
    @staticmethod
    def create_basic_strategy(
        name: str = "test-strategy",
        risk_level: int = 3,
        is_active: bool = True
    ) -> 'Strategy':
        """기본 테스트 전략 생성"""
        return Strategy(
            id=StrategyId.generate(),
            name=name,
            description=f"Test strategy: {name}",
            risk_level=risk_level,
            is_active=is_active,
            created_at=datetime.now(),
            tags=["test"],
            expected_return=0.1,
            max_drawdown=0.05
        )
    
    @staticmethod
    def create_multiple_strategies(count: int = 3) -> List['Strategy']:
        """여러 테스트 전략 생성"""
        return [
            StrategyTestDataFactory.create_basic_strategy(
                name=f"strategy-{i}",
                risk_level=(i % 5) + 1
            )
            for i in range(count)
        ]

# 테스트 코드에서 사용
class TestStrategyRepository(unittest.TestCase):
    def test_find_by_name(self):
        mock_repo = Mock(spec=StrategyRepository)
        test_strategy = StrategyTestDataFactory.create_basic_strategy()
        
        mock_repo.find_by_name.return_value = test_strategy
        
        result = mock_repo.find_by_name("test-strategy")
        self.assertEqual(result.name, "test-strategy")
```

#### 🔍 핵심 포인트
- 테스트 데이터 팩토리로 중복 제거
- 매개변수로 다양한 테스트 케이스 생성
- 일관된 테스트 데이터 구조 유지

### 10. Repository 예외 처리 불일치

#### ❌ 문제 상황
```python
# Repository마다 다른 예외 처리 방식
class StrategyRepository:
    def find_by_id(self, strategy_id: str) -> Optional[Strategy]:
        try:
            # DB 접근
            pass
        except Exception:
            return None  # 모든 예외를 None으로 처리

class TriggerRepository:
    def find_by_id(self, trigger_id: str) -> Optional[Trigger]:
        try:
            # DB 접근
            pass
        except DatabaseError as e:
            raise RepositoryError(f"DB 접근 실패: {e}")  # 예외 재발생
        except Exception:
            return None  # 일관성 없음
```

#### ✅ 해결책: 일관된 예외 처리 전략
```python
# domain/repositories/exceptions.py
class RepositoryError(Exception):
    """Repository 계층 기본 예외"""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error

class EntityNotFoundError(RepositoryError):
    """엔티티 미발견 예외"""
    pass

class DuplicateEntityError(RepositoryError):
    """중복 엔티티 예외"""
    pass

class DatabaseConnectionError(RepositoryError):
    """데이터베이스 연결 예외"""
    pass

# Repository 인터페이스에서 예외 명시
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .exceptions import RepositoryError, EntityNotFoundError

class BaseRepository(Generic[T, ID], ABC):
    @abstractmethod
    def find_by_id(self, entity_id: ID) -> Optional[T]:
        """
        ID로 엔티티 조회
        
        Args:
            entity_id: 조회할 엔티티의 ID
            
        Returns:
            찾은 엔티티 또는 None
            
        Raises:
            DatabaseConnectionError: DB 연결 실패
            RepositoryError: 기타 Repository 오류
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """
        엔티티 저장
        
        Raises:
            DuplicateEntityError: 중복 엔티티
            DatabaseConnectionError: DB 연결 실패
            RepositoryError: 기타 저장 오류
        """
        pass
```

#### 🔍 예외 처리 원칙
- **일관된 예외 계층**: 모든 Repository에서 동일한 예외 사용
- **명시적 예외 문서화**: docstring에 발생 가능한 예외 명시
- **원본 예외 보존**: `original_error`로 디버깅 정보 유지
- **적절한 추상화**: 기술적 오류를 도메인 예외로 변환

## 🔧 문제 해결 도구

### 1. 순환 의존성 검사 스크립트

```python
# tools/check_circular_imports.py
def check_circular_imports():
    """순환 의존성 검사"""
    import importlib
    
    modules_to_check = [
        'upbit_auto_trading.domain.repositories.strategy_repository',
        'upbit_auto_trading.domain.repositories.trigger_repository',
        'upbit_auto_trading.domain.repositories.settings_repository',
        'upbit_auto_trading.domain.entities.strategy',
        'upbit_auto_trading.domain.entities.trigger',
    ]
    
    for module_name in modules_to_check:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name} import 성공")
        except ImportError as e:
            print(f"❌ {module_name} import 실패: {e}")
            return False
    
    print("🎯 모든 모듈 import 성공 - 순환 의존성 없음")
    return True

if __name__ == "__main__":
    check_circular_imports()
```

### 2. Repository 인터페이스 계약 검증

```python
# tools/validate_repository_contracts.py
def validate_repository_contracts():
    """Repository 인터페이스 계약 검증"""
    from unittest.mock import Mock
    
    repositories = {
        'StrategyRepository': 'upbit_auto_trading.domain.repositories.strategy_repository.StrategyRepository',
        'TriggerRepository': 'upbit_auto_trading.domain.repositories.trigger_repository.TriggerRepository',
        'SettingsRepository': 'upbit_auto_trading.domain.repositories.settings_repository.SettingsRepository',
    }
    
    for repo_name, repo_path in repositories.items():
        try:
            module_path, class_name = repo_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            repo_class = getattr(module, class_name)
            
            # Mock으로 인터페이스 계약 검증
            mock_repo = Mock(spec=repo_class)
            
            # BaseRepository 기본 메서드 확인
            base_methods = ['save', 'find_by_id', 'find_all', 'delete', 'exists']
            for method in base_methods:
                if hasattr(mock_repo, method):
                    print(f"✅ {repo_name}.{method} 존재")
                else:
                    print(f"❌ {repo_name}.{method} 누락")
            
        except Exception as e:
            print(f"❌ {repo_name} 검증 실패: {e}")

if __name__ == "__main__":
    validate_repository_contracts()
```

### 3. 의존성 주입 검증 스크립트

```python
# tools/test_dependency_injection.py
def test_dependency_injection():
    """의존성 주입 동작 검증"""
    from unittest.mock import Mock
    
    try:
        # Mock Repository 생성
        mock_settings_repo = Mock()
        mock_settings_repo.get_compatibility_rules.return_value = {}
        
        # 도메인 서비스에 주입
        from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
        service = StrategyCompatibilityService(mock_settings_repo)
        
        # 정상 동작 확인
        assert service is not None
        print("✅ 의존성 주입 성공")
        
        # Repository 메서드 호출 확인
        result = service.check_variable_compatibility("var1", "var2")
        mock_settings_repo.get_compatibility_rules.assert_called()
        print("✅ Repository 메서드 호출 확인")
        
        return True
        
    except Exception as e:
        print(f"❌ 의존성 주입 실패: {e}")
        return False

if __name__ == "__main__":
    test_dependency_injection()
```

## 📚 문제 예방 체크리스트

### 설계 단계 (Design Phase)
- [ ] Repository 인터페이스는 도메인 관점의 메서드명 사용
- [ ] Generic TypeVar 이름을 명확하게 정의
- [ ] Protocol vs ABC 선택 기준 명확화
- [ ] 반환 타입 일관성 규칙 정의
- [ ] 예외 처리 전략 수립

### 구현 단계 (Implementation Phase)
- [ ] TYPE_CHECKING으로 순환 의존성 방지
- [ ] Mock(spec=Interface)로 테스트 작성
- [ ] 커맨드 객체로 복잡한 파라미터 단순화
- [ ] 검색 기준 객체로 메서드 폭발 방지
- [ ] 테스트 데이터 팩토리 활용

### 검증 단계 (Validation Phase)
- [ ] 순환 의존성 검사 스크립트 실행
- [ ] Repository 인터페이스 계약 검증
- [ ] 의존성 주입 동작 확인
- [ ] Mock 테스트 전체 통과
- [ ] 실제 도메인 서비스 연동 테스트

## 🎯 성공 패턴 요약

### 1. 점진적 구현 전략
1. **BaseRepository 먼저**: 공통 기능 안정화
2. **핵심 Repository 다음**: Strategy, Settings 우선
3. **특화 Repository 마지막**: MarketData, Backtest
4. **통합 테스트 최종**: 전체 연동 검증

### 2. 테스트 주도 설계
1. **Mock 테스트 먼저**: 인터페이스 계약 정의
2. **의존성 주입 검증**: 도메인 서비스 연동
3. **순환 의존성 확인**: import 오류 방지
4. **통합 테스트**: 전체 시스템 동작 검증

### 3. 문제 조기 발견
1. **자동화된 검증**: 스크립트로 문제 조기 감지
2. **일관성 체크**: 명명 규칙과 반환 타입 검증
3. **예외 처리 검토**: 모든 Repository 예외 전략 통일
4. **문서화**: 문제와 해결책 실시간 기록

## 📝 결론

Repository 패턴 구현에서 발생하는 문제들은 대부분 **설계 단계의 명확한 규칙 정의**와 **체계적인 검증 과정**으로 예방할 수 있습니다.

특히 **TYPE_CHECKING을 통한 순환 의존성 방지**와 **Mock(spec=Interface)을 통한 계약 검증**이 가장 효과적인 해결책이었습니다.

이 가이드의 해결책들을 적용하면 **Infrastructure Layer 구현 시에도 동일한 품질**을 유지할 수 있을 것입니다.

## 📚 관련 문서

- [Repository 실무 경험담](01_repository_pattern_실무_경험담.md): 설계 인사이트와 교훈
- [Repository 구현 가이드](02_repository_인터페이스_구현_가이드.md): 단계별 구현 방법
- [TASK-20250803-03](../../../tasks/active/TASK-20250803-03_repository_interfaces_definition.md): 원본 작업 문서

---

**💡 핵심**: "문제는 발생하기 전에 예방하는 것이 가장 효율적이다!"
