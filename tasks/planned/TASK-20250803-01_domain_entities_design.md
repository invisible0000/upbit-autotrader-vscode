# TASK-20250803-01

## Title
도메인 엔티티 설계 및 구현 (Strategy, Trigger, Value Objects)

## Objective (목표)
매매 전략의 핵심 비즈니스 로직을 순수한 도메인 모델로 구현하여, UI와 완전히 분리된 도메인 엔티티를 구축합니다. 기존 UI에 혼재된 전략 관련 로직을 추출하여 새로운 도메인 계층으로 이동시킵니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 1: Domain Layer 구축 (2주)" > "1.1 도메인 엔티티 설계 (3일)"

## Pre-requisites (선행 조건)
- 없음 (첫 번째 태스크)

## Detailed Steps (상세 실행 절차 - 체크리스트)

### 1. **[분석]** 기존 코드베이스에서 전략 관련 로직 식별
- [ ] `upbit_auto_trading/ui/desktop/screens/strategy_management/` 폴더의 모든 파일을 분석하여 전략 생성, 관리 로직 파악
- [ ] `upbit_auto_trading/data_layer/strategy_models.py` 파일에서 기존 전략 데이터 모델 구조 분석
- [ ] `upbit_auto_trading/business_logic/strategy/` 폴더에서 전략 실행 관련 로직 식별
- [ ] 트리거 관련 코드가 있는 `trigger_builder` 관련 파일들에서 조건 생성 로직 분석

### 2. **[폴더 구조 생성]** 새로운 도메인 계층 폴더 구조 생성
- [ ] `upbit_auto_trading/domain/` 폴더 생성
- [ ] `upbit_auto_trading/domain/entities/` 폴더 생성
- [ ] `upbit_auto_trading/domain/value_objects/` 폴더 생성
- [ ] `upbit_auto_trading/domain/exceptions/` 폴더 생성
- [ ] 각 폴더에 `__init__.py` 파일 생성

### 3. **[새 코드 작성]** 값 객체(Value Objects) 구현
- [ ] `upbit_auto_trading/domain/value_objects/strategy_id.py` 파일 생성:
  ```python
  @dataclass(frozen=True)
  class StrategyId:
      value: str
      
      def __post_init__(self):
          if not self.value or len(self.value) < 3:
              raise InvalidStrategyIdError("전략 ID는 최소 3자 이상이어야 합니다")
  ```
- [ ] `upbit_auto_trading/domain/value_objects/trigger_id.py` 파일 생성:
  ```python
  @dataclass(frozen=True)
  class TriggerId:
      value: str
      
      def __post_init__(self):
          if not self.value:
              raise InvalidTriggerIdError("트리거 ID는 필수입니다")
  ```
- [ ] `upbit_auto_trading/domain/value_objects/comparison_operator.py` 파일 생성:
  ```python
  from enum import Enum
  
  class ComparisonOperator(Enum):
      GREATER_THAN = ">"
      LESS_THAN = "<"
      GREATER_EQUAL = ">="
      LESS_EQUAL = "<="
      EQUAL = "=="
      NOT_EQUAL = "!="
      APPROXIMATELY_EQUAL = "~="
  ```

### 4. **[새 코드 작성]** 도메인 예외 클래스 구현
- [ ] `upbit_auto_trading/domain/exceptions/domain_exceptions.py` 파일 생성:
  ```python
  class DomainException(Exception):
      """도메인 계층 기본 예외"""
      pass
  
  class InvalidStrategyIdError(DomainException):
      """잘못된 전략 ID 예외"""
      pass
  
  class InvalidTriggerIdError(DomainException):
      """잘못된 트리거 ID 예외"""
      pass
  
  class IncompatibleTriggerError(DomainException):
      """호환되지 않는 트리거 예외"""
      pass
  ```

### 5. **[리팩토링/마이그레이션]** 기존 전략 모델을 도메인 엔티티로 변환
- [ ] 기존 `data_layer/strategy_models.py`에서 전략 관련 클래스 구조 분석
- [ ] `upbit_auto_trading/domain/entities/strategy.py` 파일 생성하고, 기존 모델을 브리핑 문서의 설계에 맞게 변환:
  ```python
  from dataclasses import dataclass, field
  from typing import List, Optional
  from datetime import datetime
  
  @dataclass
  class Strategy:
      strategy_id: StrategyId
      name: str
      entry_triggers: List['Trigger'] = field(default_factory=list)
      exit_triggers: List['Trigger'] = field(default_factory=list)
      management_rules: List['ManagementRule'] = field(default_factory=list)
      created_at: datetime = field(default_factory=datetime.now)
      _domain_events: List['DomainEvent'] = field(default_factory=list, init=False)
      
      def add_trigger(self, trigger: 'Trigger') -> None:
          """트리거 추가 시 호환성 검증"""
          if not self._is_compatible_trigger(trigger):
              raise IncompatibleTriggerError(f"트리거 {trigger.trigger_id}는 현재 전략과 호환되지 않습니다")
          
          if trigger.trigger_type == TriggerType.ENTRY:
              self.entry_triggers.append(trigger)
          elif trigger.trigger_type == TriggerType.EXIT:
              self.exit_triggers.append(trigger)
      
      def _is_compatible_trigger(self, trigger: 'Trigger') -> bool:
          # 호환성 검증 로직 (추후 CompatibilityService로 위임)
          return True  # 임시 구현
      
      def get_all_triggers(self) -> List['Trigger']:
          """모든 트리거 반환"""
          return self.entry_triggers + self.exit_triggers
      
      def get_domain_events(self) -> List['DomainEvent']:
          """도메인 이벤트 반환"""
          return self._domain_events.copy()
  ```

### 6. **[새 코드 작성]** 트리거 도메인 엔티티 구현
- [ ] 기존 트리거 빌더 코드에서 조건 생성 로직 분석
- [ ] `upbit_auto_trading/domain/entities/trigger.py` 파일 생성:
  ```python
  from dataclasses import dataclass
  from typing import Union
  from enum import Enum
  
  class TriggerType(Enum):
      ENTRY = "entry"
      EXIT = "exit"
      MANAGEMENT = "management"
  
  @dataclass
  class TradingVariable:
      variable_id: str
      display_name: str
      purpose_category: str  # trend, momentum, volatility, volume, price
      chart_category: str    # overlay, subplot
      comparison_group: str  # price_comparable, percentage_comparable, zero_centered
  
  @dataclass
  class Trigger:
      trigger_id: TriggerId
      trigger_type: TriggerType
      variable: TradingVariable
      operator: ComparisonOperator
      target_value: Union[float, TradingVariable]
      parameters: dict = field(default_factory=dict)
      
      def evaluate(self, market_data: 'MarketData') -> bool:
          """조건 평가 로직 (추후 TriggerEvaluationService로 위임)"""
          # 임시 구현
          return True
      
      def to_human_readable(self) -> str:
          """사람이 읽기 쉬운 형태로 조건 표현"""
          return f"{self.variable.display_name} {self.operator.value} {self.target_value}"
  ```

### 7. **[새 코드 작성]** 관리 규칙 도메인 엔티티 구현
- [ ] `upbit_auto_trading/domain/entities/management_rule.py` 파일 생성:
  ```python
  from dataclasses import dataclass
  from enum import Enum
  
  class ManagementType(Enum):
      PYRAMID_BUYING = "pyramid_buying"    # 물타기
      SCALE_IN_BUYING = "scale_in_buying"  # 불타기
      TRAILING_STOP = "trailing_stop"      # 트레일링 스탑
      FIXED_STOP = "fixed_stop"           # 고정 손절/익절
      TIME_BASED_EXIT = "time_based_exit" # 시간 기반 청산
  
  @dataclass
  class ManagementRule:
      rule_id: str
      rule_type: ManagementType
      parameters: dict
      priority: int = 1
      is_active: bool = True
      
      def should_execute(self, position_state: 'PositionState', market_data: 'MarketData') -> bool:
          """관리 규칙 실행 조건 확인"""
          # 임시 구현
          return False
  ```

### 8. **[새 코드 작성]** 팩토리 클래스 구현
- [ ] `upbit_auto_trading/domain/entities/strategy_factory.py` 파일 생성:
  ```python
  class StrategyFactory:
      """전략 생성을 위한 팩토리 클래스"""
      
      @staticmethod
      def create_basic_7_rule_strategy() -> Strategy:
          """기본 7규칙 전략 생성"""
          strategy_id = StrategyId("BASIC_7_RULE_001")
          strategy = Strategy(strategy_id, "기본 7규칙 전략")
          
          # RSI 과매도 진입 트리거
          rsi_variable = TradingVariable(
              variable_id="RSI",
              display_name="RSI 지표",
              purpose_category="momentum",
              chart_category="subplot",
              comparison_group="percentage_comparable"
          )
          
          entry_trigger = Trigger(
              trigger_id=TriggerId("RSI_OVERSOLD_ENTRY"),
              trigger_type=TriggerType.ENTRY,
              variable=rsi_variable,
              operator=ComparisonOperator.LESS_THAN,
              target_value=30,
              parameters={"period": 14}
          )
          
          strategy.add_trigger(entry_trigger)
          
          # 추가 규칙들 (불타기, 물타기, 트레일링 스탑 등)
          # ... (구체적 구현은 다음 태스크에서)
          
          return strategy
  ```

### 9. **[테스트 코드 작성]** 도메인 엔티티 단위 테스트 구현
- [ ] `tests/domain/` 폴더 생성
- [ ] `tests/domain/entities/` 폴더 생성
- [ ] `tests/domain/entities/test_strategy.py` 파일 생성:
  ```python
  import pytest
  from datetime import datetime
  from upbit_auto_trading.domain.entities.strategy import Strategy
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  from upbit_auto_trading.domain.exceptions.domain_exceptions import IncompatibleTriggerError
  
  def test_strategy_creation():
      # Given
      strategy_id = StrategyId("RSI_STRATEGY_001")
      
      # When
      strategy = Strategy(strategy_id, "RSI 전략")
      
      # Then
      assert strategy.strategy_id.value == "RSI_STRATEGY_001"
      assert strategy.name == "RSI 전략"
      assert len(strategy.entry_triggers) == 0
      assert len(strategy.exit_triggers) == 0
      assert isinstance(strategy.created_at, datetime)
  
  def test_strategy_add_trigger():
      # Given
      strategy = Strategy(StrategyId("TEST_001"), "테스트 전략")
      trigger = create_test_trigger()  # 헬퍼 함수
      
      # When
      strategy.add_trigger(trigger)
      
      # Then
      assert len(strategy.get_all_triggers()) == 1
      
  def create_test_trigger():
      # 테스트용 트리거 생성 헬퍼 함수
      pass
  ```
- [ ] `tests/domain/entities/test_trigger.py` 파일 생성
- [ ] `tests/domain/value_objects/test_strategy_id.py` 파일 생성

## Verification Criteria (완료 검증 조건)

### **[기능 검증]** 단위 테스트 통과
- [ ] `pytest tests/domain/entities/test_strategy.py -v` 실행하여 모든 테스트가 성공적으로 통과하는 것을 확인
- [ ] `pytest tests/domain/value_objects/ -v` 실행하여 값 객체 테스트가 통과하는 것을 확인
- [ ] 코드 커버리지: `pytest tests/domain/ --cov=upbit_auto_trading/domain --cov-report=html` 실행하여 80% 이상 커버리지 확인

### **[구조 검증]** 폴더 구조 및 파일 존재 확인
- [ ] `upbit_auto_trading/domain/entities/strategy.py` 파일이 존재하고 Strategy 클래스가 브리핑 문서 설계대로 구현되어 있는지 확인
- [ ] `upbit_auto_trading/domain/entities/trigger.py` 파일이 존재하고 Trigger 클래스가 구현되어 있는지 확인
- [ ] 모든 값 객체 파일들이 올바른 위치에 존재하는지 확인

### **[비즈니스 규칙 검증]** 기본 7규칙 전략 생성 확인
- [ ] Python REPL에서 다음 코드 실행 시 오류 없이 동작하는지 확인:
  ```python
  from upbit_auto_trading.domain.entities.strategy_factory import StrategyFactory
  
  strategy = StrategyFactory.create_basic_7_rule_strategy()
  print(f"전략 ID: {strategy.strategy_id.value}")
  print(f"전략 이름: {strategy.name}")
  print(f"진입 트리거 수: {len(strategy.entry_triggers)}")
  assert strategy.strategy_id.value == "BASIC_7_RULE_001"
  assert strategy.name == "기본 7규칙 전략"
  assert len(strategy.entry_triggers) >= 1
  ```

### **[Import 검증]** 모듈 import 및 의존성 확인
- [ ] 모든 새로 생성된 도메인 모듈이 올바르게 import되는지 확인
- [ ] 순환 참조가 없는지 확인: `python -c "import upbit_auto_trading.domain.entities.strategy"` 실행
- [ ] 기존 코드와 새 도메인 계층 간의 임시 연결이 정상 동작하는지 확인

## Notes (주의사항)
- 이 단계에서는 아직 UI와 연동하지 않습니다. 순수한 도메인 로직만 구현합니다.
- 기존 데이터베이스 연동 코드는 수정하지 않습니다. 다음 태스크에서 Repository 패턴으로 분리할 예정입니다.
- 호환성 검증 로직은 임시로 `True`를 반환하도록 구현하고, 다음 태스크에서 CompatibilityService로 구현할 예정입니다.
