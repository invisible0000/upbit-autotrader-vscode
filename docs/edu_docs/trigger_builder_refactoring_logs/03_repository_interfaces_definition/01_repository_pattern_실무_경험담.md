# 🏗️ Repository 패턴 DDD 실무 경험담

> **목적**: Repository 인터페이스 정의 작업에서 얻은 실무 경험과 인사이트 공유  
> **대상**: LLM 에이전트, DDD 학습자, 아키텍처 설계자  
> **갱신**: 2025-08-04

## 🎯 작업 개요

TASK-20250803-03에서 도메인 계층의 Repository 인터페이스를 정의하는 과정에서 얻은 **실무 경험과 교훈**을 정리합니다.

### 📊 작업 성과 요약
- **Repository 인터페이스 7개**: 270+ 추상 메서드 정의
- **Mock 테스트 55개**: 100% 통과로 인터페이스 계약 검증
- **의존성 주입**: 도메인 서비스 2개 연동 완료
- **3-DB 아키텍처**: 완전한 추상화 계층 구축

## 💡 핵심 인사이트

### 1. Repository 인터페이스 설계의 핵심 원칙

#### ✅ 성공 요인
```python
# 도메인 중심적 메서드 네이밍
class StrategyRepository(BaseRepository[Strategy, StrategyId]):
    def find_strategies_by_risk_level(self, risk_level: RiskLevel) -> List[Strategy]:
        """비즈니스 관점의 메서드명 - 기술적 구현 숨김"""
        pass
    
    def get_popular_strategies(self, limit: int = 10) -> List[Strategy]:
        """사용자 경험 중심의 인터페이스"""
        pass
```

**교훈**: 기술적 구현(SQL 쿼리)보다 **비즈니스 의도**를 명확히 드러내는 메서드명을 사용해야 합니다.

#### ❌ 피해야 할 패턴
```python
# 안티패턴: 기술적 구현에 의존적인 네이밍
def select_strategy_by_id_with_join(self, strategy_id: str):
def update_strategy_metadata_direct_sql(self, strategy: Strategy):
```

### 2. Generic 타입 시스템의 실무 적용

#### 🎯 BaseRepository의 Generic 설계
```python
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')  # Entity 타입
ID = TypeVar('ID')  # ID 타입

class BaseRepository(Generic[T, ID], ABC):
    @abstractmethod
    def save(self, entity: T) -> T:
        """Generic을 통한 타입 안전성 확보"""
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: ID) -> Optional[T]:
        """컴파일 타임 타입 검증"""
        pass
```

**핵심 학습**: Generic을 사용하면 컴파일 타임에 타입 오류를 잡을 수 있어 **런타임 에러를 현저히 줄일 수 있습니다**.

### 3. 의존성 주입의 실전 적용

#### 🔄 Before & After 비교

**Before (직접 의존성)**:
```python
class StrategyCompatibilityService:
    def __init__(self):
        self.db = sqlite3.connect("data/settings.sqlite3")  # 하드코딩
    
    def check_compatibility(self, var1, var2):
        cursor = self.db.execute("SELECT ...")  # SQL 직접 실행
```

**After (Repository 추상화)**:
```python
class StrategyCompatibilityService:
    def __init__(self, settings_repository: SettingsRepository):
        self._settings_repository = settings_repository  # 인터페이스 주입
    
    def check_compatibility(self, var1, var2):
        rules = self._settings_repository.get_compatibility_rules()  # 추상화된 메서드
```

**실무 이점**:
- ✅ 테스트 시 Mock 객체로 쉽게 대체 가능
- ✅ 데이터베이스 변경 시 서비스 로직 수정 불필요
- ✅ 단위 테스트가 빠르고 안정적

### 4. 3-DB 아키텍처 매핑의 설계 원칙

#### 📊 DB별 Repository 특성화
```python
# settings.sqlite3 → 읽기 전용 Repository
class SettingsRepository(Protocol):
    def get_trading_variables(self) -> List[TradingVariable]:
        """읽기 전용: save/update/delete 메서드 없음"""
        pass

# strategies.sqlite3 → 완전한 CRUD Repository  
class StrategyRepository(BaseRepository[Strategy, StrategyId]):
    def save(self, strategy: Strategy) -> Strategy:
        """완전한 생명주기 관리"""
        pass

# market_data.sqlite3 → 대용량 특화 Repository
class MarketDataRepository(Protocol):
    def bulk_save_market_data(self, data_list: List[MarketData]) -> bool:
        """대용량 데이터 최적화"""
        pass
```

**설계 철학**: 각 데이터베이스의 **특성과 사용 패턴을 반영**한 맞춤형 인터페이스 설계

## 🧪 테스트 주도 개발의 실무 적용

### Mock 기반 Repository 테스트 전략

#### 🎯 인터페이스 계약 검증
```python
def test_strategy_repository_interface_contract():
    """Repository 인터페이스 계약 테스트"""
    mock_repo = Mock(spec=StrategyRepository)
    
    # 모든 필수 메서드 존재 여부 검증
    required_methods = ['save', 'find_by_id', 'find_all', 'delete', 'exists']
    for method in required_methods:
        assert hasattr(mock_repo, method)
        assert callable(getattr(mock_repo, method))
```

**핵심 학습**: Mock 테스트로 **인터페이스 설계 오류를 조기 발견**할 수 있습니다.

### 의존성 주입 검증 패턴
```python
def test_dependency_injection_works():
    """실제 의존성 주입 동작 검증"""
    mock_settings_repo = Mock(spec=SettingsRepository)
    mock_settings_repo.get_compatibility_rules.return_value = []
    
    # 서비스에 Mock Repository 주입
    service = StrategyCompatibilityService(mock_settings_repo)
    
    # 정상 동작 검증
    assert service is not None
    mock_settings_repo.get_compatibility_rules.assert_called_once()
```

## 🚧 마주한 도전과 해결책

### 1. Repository 메서드 폭발 문제

#### ❌ 문제 상황
초기에는 모든 가능한 조회 패턴을 개별 메서드로 정의하려 했습니다:
```python
def find_strategies_by_name_and_risk_level(self, name: str, risk: RiskLevel)
def find_strategies_by_name_and_tags(self, name: str, tags: List[str])
def find_strategies_by_risk_level_and_tags(self, risk: RiskLevel, tags: List[str])
# ... 무한 조합
```

#### ✅ 해결책: 복합 조건과 범용 검색
```python
def search_strategies(self, criteria: StrategySearchCriteria) -> List[Strategy]:
    """범용 검색 메서드로 조합 폭발 해결"""
    pass

def find_strategies_by_performance_range(
    self, min_return: float, max_return: float
) -> List[Strategy]:
    """비즈니스적으로 의미 있는 조건만 개별 메서드화"""
    pass
```

### 2. 타입 힌트 복잡성 관리

#### ❌ 초기 접근법
```python
def find_by_complex_criteria(
    self, 
    name: Optional[str], 
    tags: Optional[List[str]], 
    risk_level: Optional[RiskLevel],
    date_range: Optional[Tuple[datetime, datetime]]
) -> Union[List[Strategy], None]:
    """타입이 너무 복잡함"""
    pass
```

#### ✅ 개선된 접근법
```python
@dataclass
class StrategySearchCriteria:
    name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    risk_level: Optional[RiskLevel] = None
    date_range: Optional[DateRange] = None

def search_strategies(self, criteria: StrategySearchCriteria) -> List[Strategy]:
    """명확한 데이터 클래스로 타입 단순화"""
    pass
```

### 3. 순환 의존성 해결

#### ❌ 문제 상황
```python
# domain/repositories/strategy_repository.py
from upbit_auto_trading.domain.entities.strategy import Strategy  # ❌

# domain/entities/strategy.py  
from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository  # ❌
```

#### ✅ 해결책: Protocol과 TYPE_CHECKING
```python
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from upbit_auto_trading.domain.entities.strategy import Strategy

class StrategyRepository(Protocol):
    def save(self, strategy: 'Strategy') -> 'Strategy':  # 문자열 타입 힌트
        pass
```

## 📚 실무에서 얻은 설계 가이드라인

### 1. Repository 인터페이스 네이밍 규칙

#### 🎯 권장 패턴
- **조회**: `find_*`, `get_*`, `search_*`
- **저장**: `save`, `save_all`
- **삭제**: `delete`, `delete_all`
- **존재 확인**: `exists`, `count`
- **메타데이터**: `get_*_statistics`, `get_*_count`

#### 💡 비즈니스 도메인 반영
```python
# ✅ 도메인 용어 사용
def get_popular_strategies(self) -> List[Strategy]
def find_active_strategies(self) -> List[Strategy]

# ❌ 기술적 용어 지양  
def select_from_strategies_where_active_true(self) -> List[Strategy]
```

### 2. 인터페이스 분리 원칙 (ISP) 적용

#### 🔄 기능별 인터페이스 분리
```python
class StrategyReadRepository(Protocol):
    """읽기 전용 연산"""
    def find_by_id(self, strategy_id: StrategyId) -> Optional[Strategy]: pass

class StrategyWriteRepository(Protocol):
    """쓰기 전용 연산"""
    def save(self, strategy: Strategy) -> Strategy: pass

class StrategyRepository(StrategyReadRepository, StrategyWriteRepository):
    """완전한 Repository 인터페이스"""
    pass
```

### 3. 에러 처리 전략

#### 🚨 Repository 예외 설계
```python
class RepositoryError(Exception):
    """Repository 계층 기본 예외"""
    pass

class EntityNotFoundError(RepositoryError):
    """엔티티 미발견 예외"""
    pass

class DuplicateEntityError(RepositoryError):
    """중복 엔티티 예외"""
    pass
```

## 🎯 다음 단계 준비사항

### Infrastructure Layer 구현 시 고려사항

1. **SQLite 성능 최적화**
   - 인덱스 전략: 자주 조회되는 컬럼
   - 배치 작업: `save_all`, `delete_all` 구현
   - 연결 풀링: 동시성 처리

2. **Repository 팩토리 구현**
   - 의존성 주입 컨테이너 연동
   - 트랜잭션 경계 관리
   - 리소스 생명주기 관리

3. **마이그레이션 전략**
   - 기존 코드의 점진적 전환
   - Repository 구현체 교체 방안
   - 데이터 일관성 보장

## 🏆 성공 요인 정리

### 기술적 성공 요인
- ✅ **Generic 타입 시스템**: 컴파일 타임 타입 안전성
- ✅ **Mock 기반 테스트**: 인터페이스 계약 검증
- ✅ **의존성 주입**: 느슨한 결합 달성
- ✅ **Protocol 활용**: 순환 의존성 방지

### 설계적 성공 요인  
- ✅ **도메인 중심 네이밍**: 비즈니스 의도 명확화
- ✅ **인터페이스 분리**: 단일 책임 원칙 준수
- ✅ **3-DB 특성화**: 각 데이터베이스에 최적화된 인터페이스
- ✅ **범용 검색 메서드**: 메서드 폭발 방지

### 프로세스적 성공 요인
- ✅ **TDD 적용**: 테스트로 설계 검증
- ✅ **점진적 구현**: 단계별 검증과 피드백
- ✅ **문서화**: 실시간 작업 로그 기록
- ✅ **코드 리뷰**: Mock 테스트로 인터페이스 품질 검증

## 📝 결론

Repository 인터페이스 정의 작업을 통해 **DDD의 핵심 가치**인 도메인 중심 설계와 계층 분리를 실무에 성공적으로 적용할 수 있었습니다.

특히 **Mock 기반 테스트**와 **의존성 주입**의 조합이 인터페이스 설계의 품질을 크게 향상시켰으며, **Generic 타입 시스템**으로 타입 안전성까지 확보할 수 있었습니다.

이 경험은 Infrastructure Layer 구현과 향후 다른 프로젝트의 Repository 패턴 적용에 귀중한 자산이 될 것입니다.

## 📚 관련 문서

- [Repository 구현 가이드](02_repository_인터페이스_구현_가이드.md): 단계별 구현 방법
- [Repository 문제 해결](03_repository_트러블슈팅_가이드.md): 주요 문제와 해결책
- [TASK-20250803-03](../../../tasks/active/TASK-20250803-03_repository_interfaces_definition.md): 원본 작업 문서

---

**💡 핵심**: "Repository 인터페이스는 기술이 아닌 비즈니스 도메인을 표현해야 한다!"
