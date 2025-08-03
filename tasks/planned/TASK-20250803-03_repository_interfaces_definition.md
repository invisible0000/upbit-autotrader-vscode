# TASK-20250803-03

## Title
Repository 인터페이스 정의 (도메인 데이터 접근 추상화)

## Objective (목표)
도메인 계층과 데이터 접근 계층 간의 완전한 분리를 위해 Repository 패턴의 추상 인터페이스를 정의합니다. 기존 3-DB 아키텍처(settings.sqlite3, strategies.sqlite3, market_data.sqlite3)를 유지하면서도 도메인 로직이 구체적인 데이터베이스 구현에 의존하지 않도록 합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 1: Domain Layer 구축 (2주)" > "1.3 Repository 인터페이스 정의 (3일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-01`: 도메인 엔티티 설계 및 구현이 완료되어야 함
- `TASK-20250803-02`: 도메인 서비스 구현이 완료되어야 함

## Detailed Steps (상세 실행 절차 - 체크리스트)

### 1. **[분석]** 기존 데이터 접근 패턴 및 3-DB 아키텍처 분석
- [ ] `upbit_auto_trading/storage/database/` 폴더의 기존 DB 접근 코드 분석
- [ ] `data/settings.sqlite3`, `data/strategies.sqlite3`, `data/market_data.sqlite3`의 스키마 구조 확인
- [ ] `docs/DB_SCHEMA.md` 문서에서 3-DB 아키텍처 설계 원칙 재확인
- [ ] `data_info/*.sql` 파일들에서 실제 테이블 구조 분석
- [ ] 기존 전략 저장/조회 로직이 있는 파일들 식별 및 분석

### 2. **[폴더 구조 생성]** Repository 인터페이스 폴더 구조 생성
- [ ] `upbit_auto_trading/domain/repositories/` 폴더 생성
- [ ] `upbit_auto_trading/domain/repositories/__init__.py` 파일 생성

### 3. **[새 코드 작성]** 기본 Repository 인터페이스 정의
- [ ] `upbit_auto_trading/domain/repositories/base_repository.py` 파일 생성:
  ```python
  from abc import ABC, abstractmethod
  from typing import TypeVar, Generic, Optional, List
  
  T = TypeVar('T')
  ID = TypeVar('ID')
  
  class BaseRepository(ABC, Generic[T, ID]):
      """모든 Repository의 기본 인터페이스"""
      
      @abstractmethod
      def save(self, entity: T) -> None:
          """엔티티 저장"""
          pass
      
      @abstractmethod
      def find_by_id(self, entity_id: ID) -> Optional[T]:
          """ID로 엔티티 조회"""
          pass
      
      @abstractmethod
      def find_all(self) -> List[T]:
          """모든 엔티티 조회"""
          pass
      
      @abstractmethod
      def delete(self, entity_id: ID) -> bool:
          """엔티티 삭제"""
          pass
      
      @abstractmethod
      def exists(self, entity_id: ID) -> bool:
          """엔티티 존재 여부 확인"""
          pass
  ```

### 4. **[새 코드 작성]** 전략 Repository 인터페이스 구현
- [ ] `upbit_auto_trading/domain/repositories/strategy_repository.py` 파일 생성:
  ```python
  from abc import abstractmethod
  from typing import List, Optional, Dict, Any
  from datetime import datetime
  
  from upbit_auto_trading.domain.entities.strategy import Strategy
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  from upbit_auto_trading.domain.repositories.base_repository import BaseRepository
  
  class StrategyRepository(BaseRepository[Strategy, StrategyId]):
      """전략 데이터 접근을 위한 Repository 인터페이스"""
      
      @abstractmethod
      def save(self, strategy: Strategy) -> None:
          """전략을 strategies.sqlite3에 저장"""
          pass
      
      @abstractmethod
      def find_by_id(self, strategy_id: StrategyId) -> Optional[Strategy]:
          """전략 ID로 전략 조회"""
          pass
      
      @abstractmethod
      def find_all(self) -> List[Strategy]:
          """모든 전략 조회"""
          pass
      
      @abstractmethod
      def delete(self, strategy_id: StrategyId) -> bool:
          """전략 삭제"""
          pass
      
      @abstractmethod
      def exists(self, strategy_id: StrategyId) -> bool:
          """전략 존재 여부 확인"""
          pass
      
      # 전략 특화 메서드들
      @abstractmethod
      def find_by_name(self, name: str) -> Optional[Strategy]:
          """전략 이름으로 조회"""
          pass
      
      @abstractmethod
      def find_by_tags(self, tags: List[str]) -> List[Strategy]:
          """태그로 전략 검색"""
          pass
      
      @abstractmethod
      def find_active_strategies(self) -> List[Strategy]:
          """활성화된 전략들만 조회"""
          pass
      
      @abstractmethod
      def find_strategies_created_after(self, date: datetime) -> List[Strategy]:
          """특정 날짜 이후 생성된 전략들 조회"""
          pass
      
      @abstractmethod
      def update_strategy_metadata(self, strategy_id: StrategyId, metadata: Dict[str, Any]) -> bool:
          """전략 메타데이터 업데이트 (이름, 설명, 태그 등)"""
          pass
      
      @abstractmethod
      def increment_use_count(self, strategy_id: StrategyId) -> None:
          """전략 사용 횟수 증가"""
          pass
      
      @abstractmethod
      def update_last_used_at(self, strategy_id: StrategyId, timestamp: datetime) -> None:
          """마지막 사용 시간 업데이트"""
          pass
  ```

### 5. **[새 코드 작성]** 트리거 Repository 인터페이스 구현
- [ ] `upbit_auto_trading/domain/repositories/trigger_repository.py` 파일 생성:
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional, Dict
  
  from upbit_auto_trading.domain.entities.trigger import Trigger, TriggerType
  from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  from upbit_auto_trading.domain.repositories.base_repository import BaseRepository
  
  class TriggerRepository(BaseRepository[Trigger, TriggerId]):
      """트리거 데이터 접근을 위한 Repository 인터페이스"""
      
      @abstractmethod
      def save(self, trigger: Trigger) -> None:
          """트리거 저장"""
          pass
      
      @abstractmethod
      def find_by_id(self, trigger_id: TriggerId) -> Optional[Trigger]:
          """트리거 ID로 조회"""
          pass
      
      @abstractmethod
      def find_all(self) -> List[Trigger]:
          """모든 트리거 조회"""
          pass
      
      @abstractmethod
      def delete(self, trigger_id: TriggerId) -> bool:
          """트리거 삭제"""
          pass
      
      @abstractmethod
      def exists(self, trigger_id: TriggerId) -> bool:
          """트리거 존재 여부 확인"""
          pass
      
      # 트리거 특화 메서드들
      @abstractmethod
      def find_by_strategy_id(self, strategy_id: StrategyId) -> List[Trigger]:
          """특정 전략의 모든 트리거 조회"""
          pass
      
      @abstractmethod
      def find_by_trigger_type(self, trigger_type: TriggerType) -> List[Trigger]:
          """트리거 타입별 조회 (ENTRY, EXIT, MANAGEMENT)"""
          pass
      
      @abstractmethod
      def find_by_variable_id(self, variable_id: str) -> List[Trigger]:
          """특정 변수를 사용하는 트리거들 조회"""
          pass
      
      @abstractmethod
      def save_strategy_triggers(self, strategy_id: StrategyId, triggers: List[Trigger]) -> None:
          """전략에 속한 모든 트리거를 일괄 저장"""
          pass
      
      @abstractmethod
      def delete_strategy_triggers(self, strategy_id: StrategyId) -> int:
          """전략의 모든 트리거 삭제 (삭제된 개수 반환)"""
          pass
      
      @abstractmethod
      def count_triggers_by_strategy(self, strategy_id: StrategyId) -> Dict[TriggerType, int]:
          """전략별 트리거 타입별 개수 조회"""
          pass
  ```

### 6. **[새 코드 작성]** 설정 Repository 인터페이스 구현 (읽기 전용)
- [ ] `upbit_auto_trading/domain/repositories/settings_repository.py` 파일 생성:
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional, Dict, Any
  
  from upbit_auto_trading.domain.entities.trigger import TradingVariable
  from upbit_auto_trading.domain.value_objects.compatibility_rules import ComparisonGroupRules
  
  class SettingsRepository(ABC):
      """설정 데이터 접근을 위한 Repository 인터페이스 (읽기 전용)"""
      
      @abstractmethod
      def get_trading_variables(self) -> List[TradingVariable]:
          """settings.sqlite3에서 모든 매매 변수 정의 조회"""
          pass
      
      @abstractmethod
      def find_trading_variable_by_id(self, variable_id: str) -> Optional[TradingVariable]:
          """변수 ID로 매매 변수 조회"""
          pass
      
      @abstractmethod
      def get_trading_variables_by_category(self, purpose_category: str) -> List[TradingVariable]:
          """목적 카테고리별 매매 변수 조회"""
          pass
      
      @abstractmethod
      def get_trading_variables_by_comparison_group(self, comparison_group: str) -> List[TradingVariable]:
          """비교 그룹별 매매 변수 조회"""
          pass
      
      @abstractmethod
      def get_variable_parameters(self, variable_id: str) -> Dict[str, Any]:
          """변수의 파라미터 정의 조회"""
          pass
      
      @abstractmethod
      def get_compatibility_rules(self) -> ComparisonGroupRules:
          """3중 카테고리 호환성 규칙 조회"""
          pass
      
      @abstractmethod
      def get_indicator_categories(self) -> Dict[str, List[str]]:
          """지표 카테고리 정보 조회"""
          pass
      
      @abstractmethod
      def is_variable_active(self, variable_id: str) -> bool:
          """변수 활성화 상태 확인"""
          pass
      
      @abstractmethod
      def get_variable_help_text(self, variable_id: str) -> Optional[str]:
          """변수 도움말 텍스트 조회"""
          pass
      
      @abstractmethod
      def get_app_settings(self) -> Dict[str, Any]:
          """애플리케이션 설정 조회"""
          pass
  ```

### 7. **[새 코드 작성]** 시장 데이터 Repository 인터페이스 구현
- [ ] `upbit_auto_trading/domain/repositories/market_data_repository.py` 파일 생성:
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional, Dict, Any
  from datetime import datetime
  
  from upbit_auto_trading.domain.services.trigger_evaluation_service import MarketData
  
  class MarketDataRepository(ABC):
      """시장 데이터 접근을 위한 Repository 인터페이스"""
      
      @abstractmethod
      def get_latest_market_data(self, symbol: str) -> Optional[MarketData]:
          """최신 시장 데이터 조회"""
          pass
      
      @abstractmethod
      def get_historical_data(self, symbol: str, timeframe: str, 
                            start_date: datetime, end_date: datetime) -> List[MarketData]:
          """과거 시장 데이터 조회"""
          pass
      
      @abstractmethod
      def save_market_data(self, market_data: MarketData) -> None:
          """시장 데이터 저장"""
          pass
      
      @abstractmethod
      def get_indicator_data(self, symbol: str, indicator_name: str, 
                           timeframe: str, period: int) -> List[float]:
          """기술적 지표 데이터 조회"""
          pass
      
      @abstractmethod
      def save_indicator_data(self, symbol: str, indicator_name: str, 
                            timeframe: str, values: List[float], 
                            timestamps: List[datetime]) -> None:
          """기술적 지표 데이터 저장"""
          pass
      
      @abstractmethod
      def get_available_symbols(self) -> List[str]:
          """사용 가능한 심볼 목록 조회"""
          pass
      
      @abstractmethod
      def get_available_timeframes(self) -> List[str]:
          """사용 가능한 시간프레임 목록 조회"""
          pass
      
      @abstractmethod
      def cleanup_old_data(self, cutoff_date: datetime) -> int:
          """오래된 데이터 정리 (삭제된 레코드 수 반환)"""
          pass
      
      @abstractmethod
      def get_data_range(self, symbol: str, timeframe: str) -> Optional[tuple[datetime, datetime]]:
          """특정 심볼/시간프레임의 데이터 범위 조회 (시작일, 종료일)"""
          pass
  ```

### 8. **[새 코드 작성]** 백테스팅 결과 Repository 인터페이스 구현
- [ ] `upbit_auto_trading/domain/repositories/backtest_repository.py` 파일 생성:
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional, Dict, Any
  from datetime import datetime
  
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  
  # 임시 백테스팅 결과 모델 (추후 도메인 엔티티로 이동)
  from dataclasses import dataclass
  
  @dataclass
  class BacktestResult:
      backtest_id: str
      strategy_id: StrategyId
      symbol: str
      start_date: datetime
      end_date: datetime
      total_return: float
      annual_return: float
      max_drawdown: float
      sharpe_ratio: float
      win_rate: float
      total_trades: int
      avg_holding_time: float
      profit_factor: float
      created_at: datetime
  
  class BacktestRepository(ABC):
      """백테스팅 결과 데이터 접근을 위한 Repository 인터페이스"""
      
      @abstractmethod
      def save_backtest_result(self, result: BacktestResult) -> None:
          """백테스팅 결과 저장"""
          pass
      
      @abstractmethod
      def find_backtest_by_id(self, backtest_id: str) -> Optional[BacktestResult]:
          """백테스팅 결과 조회"""
          pass
      
      @abstractmethod
      def find_backtests_by_strategy_id(self, strategy_id: StrategyId) -> List[BacktestResult]:
          """전략별 백테스팅 결과 조회"""
          pass
      
      @abstractmethod
      def find_recent_backtests(self, limit: int = 10) -> List[BacktestResult]:
          """최근 백테스팅 결과 조회"""
          pass
      
      @abstractmethod
      def find_best_performing_strategies(self, metric: str = "total_return", 
                                        limit: int = 10) -> List[BacktestResult]:
          """성과별 최고 전략 조회"""
          pass
      
      @abstractmethod
      def delete_backtest_result(self, backtest_id: str) -> bool:
          """백테스팅 결과 삭제"""
          pass
      
      @abstractmethod
      def get_backtest_statistics(self, strategy_id: StrategyId) -> Dict[str, Any]:
          """전략의 백테스팅 통계 정보"""
          pass
  ```

### 9. **[새 코드 작성]** Repository 팩토리 인터페이스 구현
- [ ] `upbit_auto_trading/domain/repositories/repository_factory.py` 파일 생성:
  ```python
  from abc import ABC, abstractmethod
  
  from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
  from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
  from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
  from upbit_auto_trading.domain.repositories.market_data_repository import MarketDataRepository
  from upbit_auto_trading.domain.repositories.backtest_repository import BacktestRepository
  
  class RepositoryFactory(ABC):
      """Repository 생성을 위한 추상 팩토리"""
      
      @abstractmethod
      def create_strategy_repository(self) -> StrategyRepository:
          """전략 Repository 생성"""
          pass
      
      @abstractmethod
      def create_trigger_repository(self) -> TriggerRepository:
          """트리거 Repository 생성"""
          pass
      
      @abstractmethod
      def create_settings_repository(self) -> SettingsRepository:
          """설정 Repository 생성 (읽기 전용)"""
          pass
      
      @abstractmethod
      def create_market_data_repository(self) -> MarketDataRepository:
          """시장 데이터 Repository 생성"""
          pass
      
      @abstractmethod
      def create_backtest_repository(self) -> BacktestRepository:
          """백테스팅 Repository 생성"""
          pass
  ```

### 10. **[테스트 코드 작성]** Repository 인터페이스 테스트 구현
- [ ] `tests/domain/repositories/` 폴더 생성
- [ ] `tests/domain/repositories/test_strategy_repository_interface.py` 파일 생성:
  ```python
  import pytest
  from unittest.mock import Mock
  
  from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
  from upbit_auto_trading.domain.entities.strategy import Strategy
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  
  class TestStrategyRepositoryInterface:
      """Repository 인터페이스 테스트 (Mock 사용)"""
      
      def setup_method(self):
          # Mock Repository 생성
          self.mock_repo = Mock(spec=StrategyRepository)
      
      def test_save_strategy_interface(self):
          # Given
          strategy = self.create_test_strategy()
          
          # When
          self.mock_repo.save(strategy)
          
          # Then
          self.mock_repo.save.assert_called_once_with(strategy)
      
      def test_find_by_id_interface(self):
          # Given
          strategy_id = StrategyId("TEST_001")
          expected_strategy = self.create_test_strategy()
          self.mock_repo.find_by_id.return_value = expected_strategy
          
          # When
          result = self.mock_repo.find_by_id(strategy_id)
          
          # Then
          assert result == expected_strategy
          self.mock_repo.find_by_id.assert_called_once_with(strategy_id)
      
      def test_find_active_strategies_interface(self):
          # Given
          active_strategies = [self.create_test_strategy(), self.create_test_strategy()]
          self.mock_repo.find_active_strategies.return_value = active_strategies
          
          # When
          result = self.mock_repo.find_active_strategies()
          
          # Then
          assert len(result) == 2
          self.mock_repo.find_active_strategies.assert_called_once()
      
      def test_exists_interface(self):
          # Given
          strategy_id = StrategyId("TEST_001")
          self.mock_repo.exists.return_value = True
          
          # When
          result = self.mock_repo.exists(strategy_id)
          
          # Then
          assert result == True
          self.mock_repo.exists.assert_called_once_with(strategy_id)
      
      def create_test_strategy(self):
          return Strategy(StrategyId("TEST_001"), "테스트 전략")
  ```

- [ ] `tests/domain/repositories/test_trigger_repository_interface.py` 파일 생성
- [ ] `tests/domain/repositories/test_settings_repository_interface.py` 파일 생성

### 11. **[통합]** 도메인 서비스와 Repository 인터페이스 연동
- [ ] `upbit_auto_trading/domain/services/strategy_compatibility_service.py` 파일 수정하여 SettingsRepository 사용:
  ```python
  class StrategyCompatibilityService:
      def __init__(self, settings_repository: SettingsRepository):
          self._settings_repository = settings_repository
          self._comparison_group_rules = self._load_comparison_group_rules()
      
      def _load_comparison_group_rules(self) -> ComparisonGroupRules:
          """설정 Repository에서 호환성 규칙 로드"""
          return self._settings_repository.get_compatibility_rules()
      
      def get_trading_variables(self) -> List[TradingVariable]:
          """설정 Repository에서 매매 변수 조회"""
          return self._settings_repository.get_trading_variables()
  ```

- [ ] `upbit_auto_trading/domain/services/trigger_evaluation_service.py` 파일 수정하여 MarketDataRepository 사용:
  ```python
  class TriggerEvaluationService:
      def __init__(self, market_data_repository: MarketDataRepository):
          self._market_data_repository = market_data_repository
      
      def get_latest_market_data(self, symbol: str) -> Optional[MarketData]:
          """시장 데이터 Repository에서 최신 데이터 조회"""
          return self._market_data_repository.get_latest_market_data(symbol)
      
      def get_indicator_value(self, symbol: str, indicator_name: str) -> Optional[float]:
          """지표 데이터 Repository에서 조회"""
          values = self._market_data_repository.get_indicator_data(
              symbol, indicator_name, "1h", 1
          )
          return values[-1] if values else None
  ```

## Verification Criteria (완료 검증 조건)

### **[인터페이스 검증]** Repository 인터페이스 정의 완성도 확인
- [ ] 모든 Repository 인터페이스 파일이 올바른 위치에 생성되었는지 확인
- [ ] 각 Repository가 적절한 추상 메서드들을 정의하고 있는지 확인
- [ ] `from abc import ABC, abstractmethod`가 올바르게 사용되었는지 확인

### **[타입 검증]** Python 타입 힌트 정확성 확인
- [ ] `mypy upbit_auto_trading/domain/repositories/ --strict` 실행하여 타입 오류가 없는지 확인
- [ ] 모든 메서드가 적절한 반환 타입을 가지고 있는지 확인
- [ ] Generic 타입이 올바르게 사용되었는지 확인

### **[Mock 테스트 검증]** Repository 인터페이스 테스트 통과
- [ ] `pytest tests/domain/repositories/ -v` 실행하여 모든 인터페이스 테스트가 통과하는지 확인
- [ ] Mock Repository가 실제 인터페이스 명세를 올바르게 구현하는지 확인

### **[의존성 주입 검증]** 도메인 서비스와 Repository 연동 확인
- [ ] Python REPL에서 의존성 주입이 올바르게 동작하는지 확인:
  ```python
  from unittest.mock import Mock
  from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
  from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
  
  # Mock Repository 생성
  mock_settings_repo = Mock(spec=SettingsRepository)
  mock_settings_repo.get_compatibility_rules.return_value = Mock()
  
  # 서비스에 주입
  compatibility_service = StrategyCompatibilityService(mock_settings_repo)
  
  # 정상 동작 확인
  assert compatibility_service is not None
  mock_settings_repo.get_compatibility_rules.assert_called_once()
  
  print("✅ 의존성 주입 검증 완료")
  ```

### **[아키텍처 검증]** 3-DB 아키텍처 매핑 확인
- [ ] 각 Repository가 올바른 데이터베이스에 매핑되는지 확인:
  ```python
  # settings.sqlite3 매핑 확인
  from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
  assert hasattr(SettingsRepository, 'get_trading_variables')
  assert hasattr(SettingsRepository, 'get_compatibility_rules')
  
  # strategies.sqlite3 매핑 확인
  from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
  assert hasattr(StrategyRepository, 'save')
  assert hasattr(StrategyRepository, 'find_by_id')
  
  # market_data.sqlite3 매핑 확인
  from upbit_auto_trading.domain.repositories.market_data_repository import MarketDataRepository
  assert hasattr(MarketDataRepository, 'get_latest_market_data')
  assert hasattr(MarketDataRepository, 'save_market_data')
  
  print("✅ 3-DB 아키텍처 매핑 검증 완료")
  ```

### **[순환 의존성 검증]** 모듈 import 안전성 확인
- [ ] 모든 Repository 인터페이스가 순환 참조 없이 import되는지 확인:
  ```bash
  python -c "from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository; print('✅ StrategyRepository import 성공')"
  python -c "from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository; print('✅ TriggerRepository import 성공')"
  python -c "from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository; print('✅ SettingsRepository import 성공')"
  ```

### **[Repository 팩토리 검증]** 팩토리 패턴 동작 확인
- [ ] Repository 팩토리가 올바르게 정의되었는지 확인:
  ```python
  from unittest.mock import Mock
  from upbit_auto_trading.domain.repositories.repository_factory import RepositoryFactory
  
  # Mock 팩토리 생성
  mock_factory = Mock(spec=RepositoryFactory)
  
  # 모든 Repository 생성 메서드가 있는지 확인
  assert hasattr(mock_factory, 'create_strategy_repository')
  assert hasattr(mock_factory, 'create_trigger_repository')
  assert hasattr(mock_factory, 'create_settings_repository')
  assert hasattr(mock_factory, 'create_market_data_repository')
  assert hasattr(mock_factory, 'create_backtest_repository')
  
  print("✅ Repository 팩토리 검증 완료")
  ```

## Notes (주의사항)
- 이 단계에서는 구체적인 Repository 구현은 하지 않습니다. 추상 인터페이스만 정의합니다.
- 실제 SQLite 구현은 Phase 3: Infrastructure Layer에서 진행할 예정입니다.
- 기존 데이터베이스 파일이나 스키마는 수정하지 않습니다. 인터페이스만 정의하여 향후 마이그레이션을 준비합니다.
- 모든 Repository 메서드는 비즈니스 도메인 관점에서 정의되어야 하며, 데이터베이스 구현 세부사항을 포함하지 않아야 합니다.
- BacktestResult는 임시로 dataclass로 정의했으며, 추후 완전한 도메인 엔티티로 리팩토링할 예정입니다.
