# 🛠️ Repository 인터페이스 구현 가이드

> **목적**: DDD 기반 Repository 패턴 인터페이스 구현의 단계별 실용 가이드  
> **대상**: LLM 에이전트, 백엔드 개발자, 아키텍처 설계자  
> **갱신**: 2025-08-04

## 🎯 가이드 개요

Repository 패턴을 DDD 아키텍처에 적용하여 **도메인 계층과 데이터 접근 계층을 완전히 분리**하는 실무 구현 방법을 제시합니다.

## 📋 구현 로드맵

### Phase 1: 기반 구조 설계 (1일)
- **BaseRepository**: Generic 기반 추상 인터페이스
- **폴더 구조**: `domain/repositories/` 패키지 구성
- **타입 시스템**: TypeVar와 Protocol 활용

### Phase 2: 도메인별 특화 (2일)  
- **StrategyRepository**: 전략 도메인 특화 인터페이스
- **TriggerRepository**: 트리거 관리 인터페이스
- **SettingsRepository**: 읽기 전용 설정 인터페이스

### Phase 3: 고급 기능 (1일)
- **MarketDataRepository**: 대용량 데이터 처리
- **BacktestRepository**: 백테스팅 결과 관리
- **RepositoryFactory**: Abstract Factory 패턴

### Phase 4: 통합 및 검증 (1일)
- **의존성 주입**: 도메인 서비스 연동
- **Mock 테스트**: 인터페이스 계약 검증
- **순환 의존성**: 방지 및 해결

## 🏗️ Phase 1: 기반 구조 설계

### 1. 폴더 구조 생성

```powershell
# Repository 패키지 기반 구조 생성
mkdir upbit_auto_trading/domain/repositories
New-Item upbit_auto_trading/domain/repositories/__init__.py
```

#### 📂 권장 폴더 구조
```
upbit_auto_trading/domain/repositories/
├── __init__.py                    # 패키지 초기화
├── base_repository.py             # Generic 기반 클래스
├── strategy_repository.py         # 전략 특화 인터페이스
├── trigger_repository.py          # 트리거 특화 인터페이스
├── settings_repository.py         # 설정 읽기 전용
├── market_data_repository.py      # 시장 데이터 특화
├── backtest_repository.py         # 백테스팅 결과
└── repository_factory.py          # Abstract Factory
```

### 2. BaseRepository 구현

#### 🎯 Generic 기반 설계
```python
# upbit_auto_trading/domain/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

# Generic 타입 변수 정의
T = TypeVar('T')  # Entity 타입
ID = TypeVar('ID')  # ID 타입

class BaseRepository(Generic[T, ID], ABC):
    """
    모든 Repository의 기본 인터페이스
    Generic을 사용하여 타입 안전성 확보
    """
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """
        엔티티 저장 또는 업데이트
        
        Args:
            entity: 저장할 도메인 엔티티
            
        Returns:
            저장된 엔티티 (ID가 할당될 수 있음)
            
        Raises:
            RepositoryError: 저장 실패 시
        """
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: ID) -> Optional[T]:
        """
        ID로 엔티티 조회
        
        Args:
            entity_id: 조회할 엔티티의 ID
            
        Returns:
            찾은 엔티티 또는 None
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[T]:
        """
        모든 엔티티 조회
        
        Returns:
            모든 엔티티 리스트
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: ID) -> bool:
        """
        엔티티 삭제
        
        Args:
            entity_id: 삭제할 엔티티의 ID
            
        Returns:
            삭제 성공 여부
        """
        pass
    
    @abstractmethod
    def exists(self, entity_id: ID) -> bool:
        """
        엔티티 존재 여부 확인
        
        Args:
            entity_id: 확인할 엔티티의 ID
            
        Returns:
            존재 여부
        """
        pass
```

#### 💡 Generic 활용 이점
- **컴파일 타임 타입 검증**: IDE에서 타입 오류 즉시 감지
- **코드 재사용성**: 모든 도메인 엔티티에 동일 패턴 적용
- **IntelliSense 지원**: 자동 완성과 타입 추론 향상

### 3. __init__.py 설정

```python
# upbit_auto_trading/domain/repositories/__init__.py
"""
Repository 인터페이스 패키지

DDD 아키텍처의 도메인 계층에서 데이터 접근을 추상화하는
Repository 패턴 인터페이스들을 제공합니다.
"""

from .base_repository import BaseRepository

# 향후 Repository 인터페이스들을 여기에 추가
__all__ = [
    'BaseRepository',
    # 'StrategyRepository',
    # 'TriggerRepository',
    # 'SettingsRepository',
    # 'MarketDataRepository',
    # 'BacktestRepository',
    # 'RepositoryFactory',
]

__version__ = '1.0.0'
```

## 🎨 Phase 2: 도메인별 특화 Repository

### 1. StrategyRepository 구현

#### 🎯 전략 도메인 특화 설계
```python
# upbit_auto_trading/domain/repositories/strategy_repository.py
from typing import TYPE_CHECKING, List, Optional, Dict, Any
from datetime import datetime, date

if TYPE_CHECKING:
    from upbit_auto_trading.domain.entities.strategy import Strategy
    from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId

from .base_repository import BaseRepository

class StrategyRepository(BaseRepository['Strategy', 'StrategyId']):
    """
    전략 도메인 엔티티 전용 Repository 인터페이스
    strategies.sqlite3 데이터베이스에 매핑
    """
    
    # === 전략 특화 검색 메서드 ===
    def find_by_name(self, name: str) -> Optional['Strategy']:
        """전략명으로 조회"""
        pass
    
    def find_by_tags(self, tags: List[str]) -> List['Strategy']:
        """태그로 전략 검색"""
        pass
    
    def find_active_strategies(self) -> List['Strategy']:
        """활성 상태 전략만 조회"""
        pass
    
    def search_strategies(self, keyword: str) -> List['Strategy']:
        """키워드 기반 전략 검색 (이름, 설명, 태그 포함)"""
        pass
    
    # === 성능 기반 조회 ===
    def find_strategies_by_risk_level(self, risk_level: int) -> List['Strategy']:
        """리스크 레벨별 전략 조회 (1: 낮음 ~ 5: 높음)"""
        pass
    
    def find_strategies_by_performance_range(
        self, min_return: float, max_return: float
    ) -> List['Strategy']:
        """수익률 범위별 전략 조회"""
        pass
    
    def get_popular_strategies(self, limit: int = 10) -> List['Strategy']:
        """인기 전략 조회 (사용 횟수 기준)"""
        pass
    
    # === 메타데이터 관리 ===
    def update_strategy_metadata(
        self, strategy_id: 'StrategyId', metadata: Dict[str, Any]
    ) -> bool:
        """전략 메타데이터 업데이트"""
        pass
    
    def increment_use_count(self, strategy_id: 'StrategyId') -> bool:
        """전략 사용 횟수 증가"""
        pass
    
    def update_last_used_at(self, strategy_id: 'StrategyId') -> bool:
        """마지막 사용 시간 업데이트"""
        pass
```

#### 🔍 설계 포인트
1. **BaseRepository 상속**: Generic 타입으로 Strategy와 StrategyId 특화
2. **비즈니스 중심 메서드**: SQL이 아닌 도메인 관점의 메서드명
3. **TYPE_CHECKING**: 순환 의존성 방지를 위한 조건부 import

### 2. SettingsRepository 구현 (읽기 전용)

#### 🎯 읽기 전용 특화 설계
```python
# upbit_auto_trading/domain/repositories/settings_repository.py
from typing import TYPE_CHECKING, List, Optional, Dict, Any
from typing_extensions import Protocol

if TYPE_CHECKING:
    from upbit_auto_trading.domain.entities.trading_variable import TradingVariable
    from upbit_auto_trading.domain.value_objects.parameter_definition import ParameterDefinition

class SettingsRepository(Protocol):
    """
    설정 데이터 읽기 전용 Repository 인터페이스
    settings.sqlite3 데이터베이스에 매핑 (읽기 전용)
    """
    
    # === TradingVariable 관리 ===
    def get_trading_variables(self) -> List['TradingVariable']:
        """모든 매매 변수 조회"""
        pass
    
    def find_trading_variable_by_id(self, variable_id: str) -> Optional['TradingVariable']:
        """변수 ID로 조회"""
        pass
    
    def get_variables_by_purpose_category(self, category: str) -> List['TradingVariable']:
        """목적 카테고리별 변수 조회"""
        pass
    
    def get_variables_by_comparison_group(self, group: str) -> List['TradingVariable']:
        """비교 그룹별 변수 조회 (호환성 검증용)"""
        pass
    
    # === 파라미터 시스템 ===
    def get_variable_parameters(self, variable_id: str) -> List['ParameterDefinition']:
        """변수별 파라미터 정의 조회"""
        pass
    
    def get_required_parameters(self, variable_id: str) -> List['ParameterDefinition']:
        """필수 파라미터만 조회"""
        pass
    
    # === 호환성 검증 ===
    def get_compatibility_rules(self) -> Dict[str, Any]:
        """변수 호환성 규칙 조회"""
        pass
    
    def is_variable_compatible_with(self, var1_id: str, var2_id: str) -> bool:
        """두 변수의 호환성 검증"""
        pass
```

#### 🔍 설계 포인트
1. **Protocol 사용**: BaseRepository 상속 대신 Protocol로 읽기 전용 특성 강조
2. **save/update/delete 없음**: settings.sqlite3의 불변성 반영
3. **호환성 시스템**: 3중 카테고리 호환성 검증 지원

### 3. TriggerRepository 구현

#### 🎯 트리거 관리 특화
```python
# upbit_auto_trading/domain/repositories/trigger_repository.py
from typing import TYPE_CHECKING, List, Optional, Dict, Any
from enum import Enum

if TYPE_CHECKING:
    from upbit_auto_trading.domain.entities.trigger import Trigger
    from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
    from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId

from .base_repository import BaseRepository

class TriggerType(Enum):
    """트리거 타입 열거형"""
    ENTRY = "entry"
    EXIT = "exit"
    MANAGEMENT = "management"

class TriggerRepository(BaseRepository['Trigger', 'TriggerId']):
    """
    트리거 도메인 엔티티 전용 Repository 인터페이스
    strategy_conditions 테이블에 매핑
    """
    
    # === 전략별 관리 ===
    def find_by_strategy_id(self, strategy_id: 'StrategyId') -> List['Trigger']:
        """전략별 모든 트리거 조회"""
        pass
    
    def save_strategy_triggers(
        self, strategy_id: 'StrategyId', triggers: List['Trigger']
    ) -> bool:
        """전략의 모든 트리거 일괄 저장"""
        pass
    
    def delete_strategy_triggers(self, strategy_id: 'StrategyId') -> bool:
        """전략의 모든 트리거 삭제"""
        pass
    
    # === 타입별 조회 ===
    def find_by_trigger_type(self, trigger_type: TriggerType) -> List['Trigger']:
        """트리거 타입별 조회"""
        pass
    
    def find_by_strategy_and_type(
        self, strategy_id: 'StrategyId', trigger_type: TriggerType
    ) -> List['Trigger']:
        """전략별 + 타입별 트리거 조회"""
        pass
    
    # === 변수별 검색 ===
    def find_by_variable_id(self, variable_id: str) -> List['Trigger']:
        """특정 매매 변수를 사용하는 트리거 검색"""
        pass
    
    def get_most_used_variables(self, limit: int = 10) -> List[str]:
        """가장 많이 사용되는 변수 ID 목록"""
        pass
    
    # === 통계 및 분석 ===
    def count_triggers_by_strategy(self, strategy_id: 'StrategyId') -> int:
        """전략별 트리거 개수"""
        pass
    
    def get_trigger_statistics(self) -> Dict[str, Any]:
        """트리거 사용 통계"""
        pass
```

## 🚀 Phase 3: 고급 기능 구현

### 1. MarketDataRepository 설계

#### 🎯 대용량 데이터 최적화
```python
# upbit_auto_trading/domain/repositories/market_data_repository.py
from typing import TYPE_CHECKING, List, Optional, Dict, Any
from datetime import datetime
from typing_extensions import Protocol

if TYPE_CHECKING:
    from upbit_auto_trading.domain.value_objects.market_data import MarketData

class Timeframe(Enum):
    """시간 프레임 열거형"""
    MIN_1 = "1m"
    MIN_5 = "5m"
    HOUR_1 = "1h"
    DAY_1 = "1d"

class MarketDataRepository(Protocol):
    """
    시장 데이터 전용 Repository 인터페이스
    market_data.sqlite3에 매핑
    """
    
    # === 기본 OHLCV 데이터 ===
    def get_latest_market_data(self, symbol: str, timeframe: Timeframe) -> Optional['MarketData']:
        """최신 시장 데이터 조회"""
        pass
    
    def get_historical_data(
        self, symbol: str, timeframe: Timeframe, 
        start_date: datetime, end_date: datetime
    ) -> List['MarketData']:
        """기간별 히스토리 데이터 조회"""
        pass
    
    def save_market_data(self, data: 'MarketData') -> bool:
        """시장 데이터 저장"""
        pass
    
    def bulk_save_market_data(self, data_list: List['MarketData']) -> bool:
        """대량 시장 데이터 일괄 저장"""
        pass
    
    # === 기술적 지표 캐싱 ===
    def get_indicator_value(
        self, symbol: str, indicator_name: str, timestamp: datetime
    ) -> Optional[float]:
        """특정 시점의 지표 값 조회"""
        pass
    
    def cache_indicator(
        self, symbol: str, indicator_name: str, 
        timestamp: datetime, value: float
    ) -> bool:
        """지표 값 캐싱"""
        pass
    
    def bulk_cache_indicators(self, indicator_data: List[Dict[str, Any]]) -> bool:
        """지표 값 일괄 캐싱"""
        pass
    
    # === 성능 최적화 ===
    def preload_data_for_backtest(
        self, symbol: str, timeframe: Timeframe, 
        start_date: datetime, end_date: datetime
    ) -> bool:
        """백테스팅용 데이터 미리 로드"""
        pass
    
    def cleanup_old_data(self, cutoff_date: datetime) -> int:
        """오래된 데이터 정리 (반환: 삭제된 레코드 수)"""
        pass
```

#### 🔍 성능 최적화 포인트
1. **Bulk Operations**: 대량 데이터 일괄 처리
2. **Indicator Caching**: 계산 비용이 높은 지표 캐싱
3. **Data Preloading**: 백테스팅 성능 향상을 위한 사전 로드
4. **Cleanup Strategy**: 스토리지 효율성을 위한 데이터 정리

### 2. RepositoryFactory 구현

#### 🎯 Abstract Factory 패턴
```python
# upbit_auto_trading/domain/repositories/repository_factory.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .strategy_repository import StrategyRepository
    from .trigger_repository import TriggerRepository
    from .settings_repository import SettingsRepository
    from .market_data_repository import MarketDataRepository
    from .backtest_repository import BacktestRepository

class RepositoryFactory(ABC):
    """
    Repository 생성을 위한 Abstract Factory 인터페이스
    의존성 주입 컨테이너와 연동하여 사용
    """
    
    @abstractmethod
    def create_strategy_repository(self) -> 'StrategyRepository':
        """전략 Repository 생성"""
        pass
    
    @abstractmethod
    def create_trigger_repository(self) -> 'TriggerRepository':
        """트리거 Repository 생성"""
        pass
    
    @abstractmethod
    def create_settings_repository(self) -> 'SettingsRepository':
        """설정 Repository 생성"""
        pass
    
    @abstractmethod
    def create_market_data_repository(self) -> 'MarketDataRepository':
        """시장 데이터 Repository 생성"""
        pass
    
    @abstractmethod
    def create_backtest_repository(self) -> 'BacktestRepository':
        """백테스팅 Repository 생성"""
        pass
    
    # === 팩토리 관리 ===
    @abstractmethod
    def configure_database_connections(self, config: dict) -> bool:
        """데이터베이스 연결 설정"""
        pass
    
    @abstractmethod
    def validate_database_schema(self) -> bool:
        """데이터베이스 스키마 검증"""
        pass
    
    @abstractmethod
    def cleanup_resources(self) -> bool:
        """리소스 정리"""
        pass
```

## 🧪 Phase 4: 통합 및 검증

### 1. 의존성 주입 구현

#### 🔄 도메인 서비스 연동
```python
# upbit_auto_trading/domain/services/strategy_compatibility_service.py 수정
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository

class StrategyCompatibilityService:
    """전략 호환성 검증 서비스"""
    
    def __init__(self, settings_repository: 'SettingsRepository'):
        """Repository 의존성 주입"""
        self._settings_repository = settings_repository
    
    def check_variable_compatibility(self, var1_id: str, var2_id: str) -> bool:
        """변수 호환성 검증"""
        try:
            # Repository를 통한 데이터 접근
            compatibility_rules = self._settings_repository.get_compatibility_rules()
            
            # 비즈니스 로직은 그대로 유지
            return self._validate_compatibility(var1_id, var2_id, compatibility_rules)
        except Exception as e:
            # 에러 처리
            self._logger.error(f"호환성 검증 실패: {e}")
            return False
    
    def _validate_compatibility(self, var1_id: str, var2_id: str, rules: dict) -> bool:
        """실제 호환성 검증 로직"""
        # 기존 비즈니스 로직 유지
        pass
```

### 2. Mock 기반 테스트 구현

#### 🧪 인터페이스 계약 검증
```python
# tests/domain/repositories/test_strategy_repository_interface.py
import unittest
from unittest.mock import Mock

class TestStrategyRepositoryInterface(unittest.TestCase):
    """StrategyRepository 인터페이스 계약 테스트"""
    
    def setUp(self):
        """테스트용 Mock Repository 생성"""
        from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
        self.mock_repo = Mock(spec=StrategyRepository)
    
    def test_base_repository_methods_exist(self):
        """BaseRepository 기본 메서드 존재 확인"""
        required_methods = ['save', 'find_by_id', 'find_all', 'delete', 'exists']
        
        for method in required_methods:
            self.assertTrue(hasattr(self.mock_repo, method))
            self.assertTrue(callable(getattr(self.mock_repo, method)))
    
    def test_strategy_specific_methods_exist(self):
        """전략 특화 메서드 존재 확인"""
        strategy_methods = [
            'find_by_name', 'find_by_tags', 'find_active_strategies',
            'find_strategies_by_risk_level', 'get_popular_strategies'
        ]
        
        for method in strategy_methods:
            self.assertTrue(hasattr(self.mock_repo, method))
            self.assertTrue(callable(getattr(self.mock_repo, method)))
    
    def test_mock_repository_behavior(self):
        """Mock Repository 동작 테스트"""
        # Mock 동작 설정
        self.mock_repo.find_by_name.return_value = None
        self.mock_repo.exists.return_value = False
        
        # 테스트 실행
        result = self.mock_repo.find_by_name("test_strategy")
        exists = self.mock_repo.exists("test_id")
        
        # 검증
        self.assertIsNone(result)
        self.assertFalse(exists)
        
        # 메서드 호출 확인
        self.mock_repo.find_by_name.assert_called_once_with("test_strategy")
        self.mock_repo.exists.assert_called_once_with("test_id")

if __name__ == '__main__':
    unittest.main()
```

### 3. 의존성 주입 검증

#### 🔍 실제 연동 테스트
```python
# 의존성 주입 동작 검증 스크립트
def test_dependency_injection():
    """Repository 의존성 주입 테스트"""
    from unittest.mock import Mock
    
    # Mock Repository 생성
    mock_settings_repo = Mock()
    mock_settings_repo.get_compatibility_rules.return_value = {}
    
    # 서비스에 주입
    from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
    service = StrategyCompatibilityService(mock_settings_repo)
    
    # 정상 동작 확인
    assert service is not None
    
    # Repository 메서드 호출 확인
    result = service.check_variable_compatibility("var1", "var2")
    mock_settings_repo.get_compatibility_rules.assert_called()
    
    print("✅ 의존성 주입 검증 완료")

if __name__ == "__main__":
    test_dependency_injection()
```

## 📚 구현 체크리스트

### Phase 1 완료 기준
- [ ] `domain/repositories/` 폴더 구조 생성
- [ ] `BaseRepository` Generic 인터페이스 구현
- [ ] 타입 힌트와 docstring 완성
- [ ] `__init__.py` 패키지 설정

### Phase 2 완료 기준
- [ ] `StrategyRepository` 전략 특화 메서드 정의
- [ ] `SettingsRepository` 읽기 전용 인터페이스 구현
- [ ] `TriggerRepository` 트리거 관리 메서드 정의
- [ ] TYPE_CHECKING으로 순환 의존성 방지

### Phase 3 완료 기준
- [ ] `MarketDataRepository` 대용량 데이터 처리 메서드
- [ ] `BacktestRepository` 백테스팅 결과 관리
- [ ] `RepositoryFactory` Abstract Factory 패턴
- [ ] 성능 최적화 메서드 (bulk operations, caching)

### Phase 4 완료 기준
- [ ] 도메인 서비스 의존성 주입 연동
- [ ] Mock 기반 인터페이스 테스트 구현
- [ ] 실제 의존성 주입 동작 검증
- [ ] 순환 의존성 해결 확인

## 🚀 성공 요인

### 기술적 성공 요인
1. **Generic 타입 시스템**: 컴파일 타임 타입 안전성 확보
2. **Protocol 활용**: 순환 의존성 방지와 인터페이스 분리
3. **Mock 테스트**: 인터페이스 계약 검증으로 설계 품질 향상
4. **의존성 주입**: 도메인 서비스와 깨끗한 연동

### 설계적 성공 요인
1. **도메인 중심 네이밍**: 비즈니스 의도를 명확히 반영
2. **3-DB 특성화**: 각 데이터베이스에 최적화된 인터페이스
3. **인터페이스 분리**: 읽기 전용 vs 읽기/쓰기 구분
4. **성능 고려**: 대용량 데이터 처리를 위한 bulk operations

## 📝 다음 단계

이 가이드로 구현한 Repository 인터페이스는 **Infrastructure Layer**에서 SQLite 기반 구체 클래스로 구현됩니다.

### Infrastructure Layer 구현 시 고려사항
1. **성능 최적화**: 인덱스, 쿼리 최적화, 연결 풀링
2. **트랜잭션 관리**: 원자적 연산과 일관성 보장
3. **에러 처리**: Repository 예외를 도메인 예외로 변환
4. **테스트**: 실제 데이터베이스 연동 테스트

## 📚 관련 문서

- [Repository 실무 경험담](01_repository_pattern_실무_경험담.md): 설계 인사이트와 교훈
- [Repository 문제 해결](03_repository_트러블슈팅_가이드.md): 주요 문제와 해결책
- [TASK-20250803-03](../../../tasks/active/TASK-20250803-03_repository_interfaces_definition.md): 원본 작업 문서

---

**💡 핵심**: "Repository 인터페이스는 Infrastructure에 의존하지 않는 순수한 도메인 추상화여야 한다!"
