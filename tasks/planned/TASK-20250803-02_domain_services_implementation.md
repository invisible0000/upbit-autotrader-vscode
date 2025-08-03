# TASK-20250803-02

## Title
도메인 서비스 구현 (전략 호환성 검증 및 트리거 평가)

## Objective (목표)
매매 전략의 핵심 비즈니스 규칙인 3중 카테고리 호환성 검증과 트리거 조건 평가 로직을 순수한 도메인 서비스로 구현합니다. 기존 UI에 분산된 호환성 검증 로직을 도메인 계층으로 이동시켜 비즈니스 규칙의 중앙화를 달성합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 1: Domain Layer 구축 (2주)" > "1.2 도메인 서비스 구현 (4일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-01`: 도메인 엔티티 설계 및 구현이 완료되어야 함

## Detailed Steps (상세 실행 절차 - 체크리스트)

### 1. **[분석]** 기존 호환성 검증 로직 식별 및 분석
- [ ] `upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/` 폴더에서 변수 호환성 검증 관련 코드 분석
- [ ] `docs/VARIABLE_COMPATIBILITY.md` 문서에서 3중 카테고리 호환성 시스템 규칙 숙지
- [ ] `data_info/tv_trading_variables.yaml` 파일에서 기존 변수 분류 체계 분석
- [ ] `data_info/tv_comparison_groups.yaml` 파일에서 comparison_group 정의 확인
- [ ] 기존 트리거 평가 로직이 있는 파일들 식별 (business_logic 폴더 내)

### 2. **[폴더 구조 생성]** 도메인 서비스 폴더 구조 생성
- [ ] `upbit_auto_trading/domain/services/` 폴더 생성
- [ ] `upbit_auto_trading/domain/services/__init__.py` 파일 생성

### 3. **[새 코드 작성]** 호환성 검증을 위한 데이터 구조 구현
- [ ] `upbit_auto_trading/domain/value_objects/compatibility_rules.py` 파일 생성:
  ```python
  from dataclasses import dataclass
  from typing import Dict, List, Set
  from enum import Enum
  
  class CompatibilityLevel(Enum):
      COMPATIBLE = "compatible"
      WARNING = "warning"  
      INCOMPATIBLE = "incompatible"
  
  @dataclass(frozen=True)
  class CompatibilityResult:
      level: CompatibilityLevel
      message: str
      warnings: List[str] = field(default_factory=list)
      
      @property
      def is_compatible(self) -> bool:
          return self.level in [CompatibilityLevel.COMPATIBLE, CompatibilityLevel.WARNING]
  
  @dataclass
  class ComparisonGroupRules:
      """comparison_group별 호환성 규칙"""
      same_group_compatible: Set[str] = field(default_factory=set)
      cross_group_rules: Dict[str, Dict[str, CompatibilityLevel]] = field(default_factory=dict)
      
      def check_compatibility(self, group1: str, group2: str) -> CompatibilityLevel:
          if group1 == group2:
              return CompatibilityLevel.COMPATIBLE
              
          if group1 in self.cross_group_rules:
              return self.cross_group_rules[group1].get(group2, CompatibilityLevel.INCOMPATIBLE)
              
          return CompatibilityLevel.INCOMPATIBLE
  ```

### 4. **[리팩토링/마이그레이션]** 전략 호환성 서비스 구현
- [ ] 기존 호환성 검증 로직을 분석하여 핵심 규칙 추출
- [ ] `upbit_auto_trading/domain/services/strategy_compatibility_service.py` 파일 생성:
  ```python
  from typing import List, Dict
  from upbit_auto_trading.domain.entities.strategy import Strategy
  from upbit_auto_trading.domain.entities.trigger import Trigger, TradingVariable
  from upbit_auto_trading.domain.value_objects.compatibility_rules import (
      CompatibilityResult, CompatibilityLevel, ComparisonGroupRules
  )
  
  class StrategyCompatibilityService:
      """전략 호환성 검증을 담당하는 도메인 서비스"""
      
      def __init__(self):
          # 3중 카테고리 호환성 규칙 초기화
          self._comparison_group_rules = self._load_comparison_group_rules()
          self._purpose_category_rules = self._load_purpose_category_rules()
          self._chart_category_rules = self._load_chart_category_rules()
      
      def check_trigger_compatibility(self, strategy: Strategy, new_trigger: Trigger) -> CompatibilityResult:
          """전략에 새 트리거 추가 시 호환성 검증"""
          existing_variables = [t.variable for t in strategy.get_all_triggers()]
          return self.check_variable_compatibility(existing_variables, new_trigger.variable)
      
      def check_variable_compatibility(self, existing_variables: List[TradingVariable], 
                                     new_variable: TradingVariable) -> CompatibilityResult:
          """변수 간 호환성 검증 (3중 카테고리 시스템)"""
          if not existing_variables:
              return CompatibilityResult(CompatibilityLevel.COMPATIBLE, "첫 번째 변수입니다")
          
          # 1. comparison_group 호환성 검증 (가장 중요)
          comparison_result = self._check_comparison_group_compatibility(existing_variables, new_variable)
          if comparison_result.level == CompatibilityLevel.INCOMPATIBLE:
              return comparison_result
          
          # 2. purpose_category 호환성 검증
          purpose_result = self._check_purpose_category_compatibility(existing_variables, new_variable)
          
          # 3. chart_category 호환성 검증  
          chart_result = self._check_chart_category_compatibility(existing_variables, new_variable)
          
          # 결과 통합
          return self._combine_compatibility_results([comparison_result, purpose_result, chart_result])
      
      def validate_strategy(self, strategy: Strategy) -> bool:
          """전체 전략의 호환성 검증"""
          all_variables = [t.variable for t in strategy.get_all_triggers()]
          
          for i, var1 in enumerate(all_variables):
              for var2 in all_variables[i+1:]:
                  result = self.check_variable_compatibility([var1], var2)
                  if not result.is_compatible:
                      return False
          
          return True
      
      def _check_comparison_group_compatibility(self, existing_variables: List[TradingVariable], 
                                              new_variable: TradingVariable) -> CompatibilityResult:
          """comparison_group 기반 호환성 검증"""
          existing_groups = {var.comparison_group for var in existing_variables}
          new_group = new_variable.comparison_group
          
          for existing_group in existing_groups:
              compatibility_level = self._comparison_group_rules.check_compatibility(existing_group, new_group)
              
              if compatibility_level == CompatibilityLevel.INCOMPATIBLE:
                  return CompatibilityResult(
                      CompatibilityLevel.INCOMPATIBLE,
                      f"'{existing_group}'과 '{new_group}' 그룹은 비교할 수 없습니다"
                  )
              elif compatibility_level == CompatibilityLevel.WARNING:
                  return CompatibilityResult(
                      CompatibilityLevel.WARNING,
                      f"'{existing_group}'과 '{new_group}' 그룹 비교 시 정규화가 필요합니다",
                      [f"정규화를 통한 비교입니다. 결과 해석에 주의하세요."]
                  )
          
          return CompatibilityResult(CompatibilityLevel.COMPATIBLE, "호환 가능한 그룹입니다")
      
      def _check_purpose_category_compatibility(self, existing_variables: List[TradingVariable], 
                                              new_variable: TradingVariable) -> CompatibilityResult:
          """purpose_category 기반 호환성 검증"""
          existing_purposes = {var.purpose_category for var in existing_variables}
          new_purpose = new_variable.purpose_category
          
          # purpose_category 조합에 대한 경고나 권장사항
          if "trend" in existing_purposes and new_purpose == "momentum":
              return CompatibilityResult(
                  CompatibilityLevel.WARNING,
                  "추세 지표와 모멘텀 지표 조합입니다",
                  ["서로 다른 신호를 제공할 수 있습니다"]
              )
          
          return CompatibilityResult(CompatibilityLevel.COMPATIBLE, "목적 카테고리 호환")
      
      def _check_chart_category_compatibility(self, existing_variables: List[TradingVariable], 
                                            new_variable: TradingVariable) -> CompatibilityResult:
          """chart_category 기반 호환성 검증"""
          # chart_category는 시각적 표시용이므로 호환성에 영향 없음
          return CompatibilityResult(CompatibilityLevel.COMPATIBLE, "차트 카테고리 호환")
      
      def _load_comparison_group_rules(self) -> ComparisonGroupRules:
          """comparison_group 호환성 규칙 로드"""
          rules = ComparisonGroupRules()
          
          # 같은 그룹끼리는 항상 호환
          rules.same_group_compatible = {
              "price_comparable", "percentage_comparable", "zero_centered", "volume_based"
          }
          
          # 서로 다른 그룹 간 호환성 규칙
          rules.cross_group_rules = {
              "price_comparable": {
                  "percentage_comparable": CompatibilityLevel.WARNING,  # 정규화 필요
                  "zero_centered": CompatibilityLevel.INCOMPATIBLE,
                  "volume_based": CompatibilityLevel.INCOMPATIBLE
              },
              "percentage_comparable": {
                  "price_comparable": CompatibilityLevel.WARNING,
                  "zero_centered": CompatibilityLevel.INCOMPATIBLE,
                  "volume_based": CompatibilityLevel.INCOMPATIBLE
              },
              "zero_centered": {
                  "price_comparable": CompatibilityLevel.INCOMPATIBLE,
                  "percentage_comparable": CompatibilityLevel.INCOMPATIBLE,
                  "volume_based": CompatibilityLevel.INCOMPATIBLE
              },
              "volume_based": {
                  "price_comparable": CompatibilityLevel.INCOMPATIBLE,
                  "percentage_comparable": CompatibilityLevel.INCOMPATIBLE,
                  "zero_centered": CompatibilityLevel.INCOMPATIBLE
              }
          }
          
          return rules
      
      def _load_purpose_category_rules(self) -> Dict:
          """purpose_category 호환성 규칙 로드"""
          # 추후 확장 가능
          return {}
      
      def _load_chart_category_rules(self) -> Dict:
          """chart_category 호환성 규칙 로드"""
          # 추후 확장 가능
          return {}
      
      def _combine_compatibility_results(self, results: List[CompatibilityResult]) -> CompatibilityResult:
          """여러 호환성 검증 결과를 통합"""
          # 가장 제한적인 결과를 채택
          if any(r.level == CompatibilityLevel.INCOMPATIBLE for r in results):
              incompatible = next(r for r in results if r.level == CompatibilityLevel.INCOMPATIBLE)
              return incompatible
          
          if any(r.level == CompatibilityLevel.WARNING for r in results):
              warnings = []
              messages = []
              for r in results:
                  if r.level == CompatibilityLevel.WARNING:
                      warnings.extend(r.warnings)
                      messages.append(r.message)
              
              return CompatibilityResult(
                  CompatibilityLevel.WARNING,
                  "; ".join(messages),
                  warnings
              )
          
          return CompatibilityResult(CompatibilityLevel.COMPATIBLE, "모든 호환성 검증 통과")
  ```

### 5. **[새 코드 작성]** 트리거 평가 서비스 구현
- [ ] 기존 트리거 평가 로직 분석 (business_logic 폴더에서)
- [ ] `upbit_auto_trading/domain/services/trigger_evaluation_service.py` 파일 생성:
  ```python
  from typing import List, Dict, Any
  from dataclasses import dataclass
  from datetime import datetime
  
  from upbit_auto_trading.domain.entities.trigger import Trigger
  from upbit_auto_trading.domain.value_objects.comparison_operator import ComparisonOperator
  
  @dataclass
  class MarketData:
      """시장 데이터 표현 (임시 구현)"""
      symbol: str
      timestamp: datetime
      close: float
      volume: float
      indicators: Dict[str, Any] = field(default_factory=dict)
  
  @dataclass
  class EvaluationResult:
      """트리거 평가 결과"""
      trigger_id: str
      result: bool
      value: float
      target_value: float
      operator: str
      message: str
      timestamp: datetime
  
  class TriggerEvaluationService:
      """트리거 조건 평가를 담당하는 도메인 서비스"""
      
      def evaluate_trigger(self, trigger: Trigger, market_data: MarketData) -> EvaluationResult:
          """단일 트리거 조건 평가"""
          # 1. 변수값 계산
          current_value = self._calculate_variable_value(trigger.variable, market_data)
          
          # 2. 대상값 계산 (고정값 또는 다른 변수값)
          target_value = self._calculate_target_value(trigger.target_value, market_data)
          
          # 3. 비교 연산 수행
          comparison_result = self._perform_comparison(
              current_value, trigger.operator, target_value
          )
          
          # 4. 결과 반환
          return EvaluationResult(
              trigger_id=trigger.trigger_id.value,
              result=comparison_result,
              value=current_value,
              target_value=target_value,
              operator=trigger.operator.value,
              message=f"{trigger.variable.display_name}: {current_value} {trigger.operator.value} {target_value}",
              timestamp=market_data.timestamp
          )
      
      def evaluate_all_triggers(self, triggers: List[Trigger], 
                               market_data: MarketData) -> List[EvaluationResult]:
          """모든 트리거 조건 평가"""
          results = []
          for trigger in triggers:
              try:
                  result = self.evaluate_trigger(trigger, market_data)
                  results.append(result)
              except Exception as e:
                  # 개별 트리거 평가 실패 시 False 결과 생성
                  error_result = EvaluationResult(
                      trigger_id=trigger.trigger_id.value,
                      result=False,
                      value=0.0,
                      target_value=0.0,
                      operator=trigger.operator.value,
                      message=f"평가 오류: {str(e)}",
                      timestamp=market_data.timestamp
                  )
                  results.append(error_result)
          
          return results
      
      def evaluate_strategy_triggers(self, strategy: 'Strategy', 
                                   market_data: MarketData) -> Dict[str, List[EvaluationResult]]:
          """전략의 모든 트리거 그룹별 평가"""
          return {
              "entry": self.evaluate_all_triggers(strategy.entry_triggers, market_data),
              "exit": self.evaluate_all_triggers(strategy.exit_triggers, market_data)
          }
      
      def _calculate_variable_value(self, variable: 'TradingVariable', market_data: MarketData) -> float:
          """변수값 계산 (지표 계산 포함)"""
          variable_id = variable.variable_id
          
          # 기본 가격 데이터
          if variable_id == "Close":
              return market_data.close
          elif variable_id == "Volume":
              return market_data.volume
          
          # 기술적 지표 (indicators에서 조회)
          if variable_id in market_data.indicators:
              return market_data.indicators[variable_id]
          
          # 임시 구현: 실제로는 지표 계산 로직 필요
          if variable_id == "RSI":
              return 45.0  # 임시값
          elif variable_id == "MACD":
              return 0.1   # 임시값
          
          raise ValueError(f"알 수 없는 변수: {variable_id}")
      
      def _calculate_target_value(self, target, market_data: MarketData) -> float:
          """대상값 계산 (고정값 또는 변수값)"""
          if isinstance(target, (int, float)):
              return float(target)
          elif hasattr(target, 'variable_id'):  # TradingVariable인 경우
              return self._calculate_variable_value(target, market_data)
          else:
              return float(target)
      
      def _perform_comparison(self, value1: float, operator: ComparisonOperator, value2: float) -> bool:
          """비교 연산 수행"""
          if operator == ComparisonOperator.GREATER_THAN:
              return value1 > value2
          elif operator == ComparisonOperator.LESS_THAN:
              return value1 < value2
          elif operator == ComparisonOperator.GREATER_EQUAL:
              return value1 >= value2
          elif operator == ComparisonOperator.LESS_EQUAL:
              return value1 <= value2
          elif operator == ComparisonOperator.EQUAL:
              return abs(value1 - value2) < 1e-6  # 부동소수점 비교
          elif operator == ComparisonOperator.NOT_EQUAL:
              return abs(value1 - value2) >= 1e-6
          elif operator == ComparisonOperator.APPROXIMATELY_EQUAL:
              # 대략적 동일 (5% 오차 허용)
              tolerance = max(abs(value1), abs(value2)) * 0.05
              return abs(value1 - value2) <= tolerance
          else:
              raise ValueError(f"지원하지 않는 연산자: {operator}")
  ```

### 6. **[새 코드 작성]** 정규화 서비스 구현
- [ ] `upbit_auto_trading/domain/services/normalization_service.py` 파일 생성:
  ```python
  from typing import Tuple, Dict, Any
  from enum import Enum
  
  class NormalizationMethod(Enum):
      MINMAX = "minmax"
      ZSCORE = "zscore"
      PERCENTAGE = "percentage"
  
  class NormalizationService:
      """서로 다른 comparison_group 간 정규화를 담당하는 서비스"""
      
      def normalize_for_comparison(self, value1: float, group1: str, 
                                 value2: float, group2: str,
                                 method: NormalizationMethod = NormalizationMethod.MINMAX) -> Tuple[float, float]:
          """두 값을 같은 스케일로 정규화"""
          
          if group1 == group2:
              # 같은 그룹이면 정규화 불필요
              return value1, value2
          
          if {group1, group2} == {"price_comparable", "percentage_comparable"}:
              return self._normalize_price_vs_percentage(value1, group1, value2, group2, method)
          else:
              raise ValueError(f"지원하지 않는 그룹 조합: {group1} vs {group2}")
      
      def _normalize_price_vs_percentage(self, value1: float, group1: str, 
                                       value2: float, group2: str,
                                       method: NormalizationMethod) -> Tuple[float, float]:
          """가격 지표와 백분율 지표 간 정규화"""
          
          if group1 == "price_comparable" and group2 == "percentage_comparable":
              price_value, percentage_value = value1, value2
          elif group1 == "percentage_comparable" and group2 == "price_comparable":
              price_value, percentage_value = value2, value1
          else:
              raise ValueError("price_comparable와 percentage_comparable 조합이 아닙니다")
          
          if method == NormalizationMethod.MINMAX:
              # 0-100 스케일로 정규화 (임시 구현)
              # 실제로는 과거 데이터 기반으로 min/max 계산 필요
              normalized_price = min(100, max(0, (price_value / 100000) * 100))  # 임시 스케일링
              normalized_percentage = percentage_value
              
              if group1 == "price_comparable":
                  return normalized_price, normalized_percentage
              else:
                  return normalized_percentage, normalized_price
          
          elif method == NormalizationMethod.ZSCORE:
              # Z-스코어 정규화 (임시 구현)
              price_zscore = (price_value - 50000) / 20000  # 임시 평균/표준편차
              percentage_zscore = (percentage_value - 50) / 28.87
              
              if group1 == "price_comparable":
                  return price_zscore, percentage_zscore
              else:
                  return percentage_zscore, price_zscore
          
          else:
              raise ValueError(f"지원하지 않는 정규화 방법: {method}")
  ```

### 7. **[테스트 코드 작성]** 도메인 서비스 단위 테스트 구현
- [ ] `tests/domain/services/` 폴더 생성
- [ ] `tests/domain/services/test_strategy_compatibility_service.py` 파일 생성:
  ```python
  import pytest
  from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
  from upbit_auto_trading.domain.entities.trigger import TradingVariable
  from upbit_auto_trading.domain.value_objects.compatibility_rules import CompatibilityLevel
  
  class TestStrategyCompatibilityService:
      def setup_method(self):
          self.compatibility_service = StrategyCompatibilityService()
      
      def test_same_comparison_group_compatible(self):
          # Given
          rsi_variable = TradingVariable(
              variable_id="RSI",
              display_name="RSI 지표",
              purpose_category="momentum",
              chart_category="subplot", 
              comparison_group="percentage_comparable"
          )
          stochastic_variable = TradingVariable(
              variable_id="Stochastic",
              display_name="스토캐스틱",
              purpose_category="momentum",
              chart_category="subplot",
              comparison_group="percentage_comparable"
          )
          
          # When
          result = self.compatibility_service.check_variable_compatibility([rsi_variable], stochastic_variable)
          
          # Then
          assert result.is_compatible
          assert result.level == CompatibilityLevel.COMPATIBLE
      
      def test_different_comparison_group_incompatible(self):
          # Given
          rsi_variable = TradingVariable(
              variable_id="RSI",
              display_name="RSI 지표",
              purpose_category="momentum",
              chart_category="subplot",
              comparison_group="percentage_comparable"
          )
          macd_variable = TradingVariable(
              variable_id="MACD",
              display_name="MACD",
              purpose_category="momentum", 
              chart_category="subplot",
              comparison_group="zero_centered"
          )
          
          # When
          result = self.compatibility_service.check_variable_compatibility([rsi_variable], macd_variable)
          
          # Then
          assert not result.is_compatible
          assert result.level == CompatibilityLevel.INCOMPATIBLE
      
      def test_price_vs_percentage_warning(self):
          # Given
          close_variable = TradingVariable(
              variable_id="Close",
              display_name="종가",
              purpose_category="price",
              chart_category="overlay",
              comparison_group="price_comparable"
          )
          rsi_variable = TradingVariable(
              variable_id="RSI",
              display_name="RSI 지표", 
              purpose_category="momentum",
              chart_category="subplot",
              comparison_group="percentage_comparable"
          )
          
          # When
          result = self.compatibility_service.check_variable_compatibility([close_variable], rsi_variable)
          
          # Then
          assert result.is_compatible  # 경고지만 호환 가능
          assert result.level == CompatibilityLevel.WARNING
          assert "정규화" in result.message
      
      def test_7_rule_strategy_compatibility(self):
          # Given: 기본 7규칙 전략 구성 요소
          from upbit_auto_trading.domain.entities.strategy_factory import StrategyFactory
          strategy = StrategyFactory.create_basic_7_rule_strategy()
          
          # When: 전체 전략 호환성 검증
          result = self.compatibility_service.validate_strategy(strategy)
          
          # Then: 모든 조합이 호환되어야 함
          assert result == True
  ```

- [ ] `tests/domain/services/test_trigger_evaluation_service.py` 파일 생성:
  ```python
  import pytest
  from datetime import datetime
  from upbit_auto_trading.domain.services.trigger_evaluation_service import (
      TriggerEvaluationService, MarketData
  )
  from upbit_auto_trading.domain.entities.trigger import Trigger, TradingVariable
  from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
  from upbit_auto_trading.domain.value_objects.comparison_operator import ComparisonOperator
  
  class TestTriggerEvaluationService:
      def setup_method(self):
          self.evaluation_service = TriggerEvaluationService()
      
      def test_simple_comparison_trigger(self):
          # Given
          trigger = self.create_rsi_trigger()
          market_data = MarketData(
              symbol="KRW-BTC",
              timestamp=datetime.now(),
              close=50000,
              volume=1000,
              indicators={"RSI": 25.0}  # RSI < 30 조건 만족
          )
          
          # When
          result = self.evaluation_service.evaluate_trigger(trigger, market_data)
          
          # Then
          assert result.result == True
          assert result.value == 25.0
          assert result.target_value == 30.0
          assert result.operator == "<"
      
      def test_multiple_triggers_evaluation(self):
          # Given
          triggers = [
              self.create_rsi_trigger(),
              self.create_volume_trigger()
          ]
          market_data = MarketData(
              symbol="KRW-BTC",
              timestamp=datetime.now(),
              close=50000,
              volume=1500,  # Volume > 1000 조건 만족
              indicators={"RSI": 35.0}  # RSI < 30 조건 불만족
          )
          
          # When
          results = self.evaluation_service.evaluate_all_triggers(triggers, market_data)
          
          # Then
          assert len(results) == 2
          assert results[0].result == False  # RSI 조건 불만족
          assert results[1].result == True   # Volume 조건 만족
      
      def create_rsi_trigger(self):
          rsi_variable = TradingVariable(
              variable_id="RSI",
              display_name="RSI 지표",
              purpose_category="momentum",
              chart_category="subplot",
              comparison_group="percentage_comparable"
          )
          return Trigger(
              trigger_id=TriggerId("RSI_OVERSOLD"),
              trigger_type=TriggerType.ENTRY,
              variable=rsi_variable,
              operator=ComparisonOperator.LESS_THAN,
              target_value=30.0
          )
      
      def create_volume_trigger(self):
          volume_variable = TradingVariable(
              variable_id="Volume",
              display_name="거래량",
              purpose_category="volume",
              chart_category="subplot", 
              comparison_group="volume_based"
          )
          return Trigger(
              trigger_id=TriggerId("VOLUME_THRESHOLD"),
              trigger_type=TriggerType.ENTRY,
              variable=volume_variable,
              operator=ComparisonOperator.GREATER_THAN,
              target_value=1000.0
          )
  ```

### 8. **[통합]** 기존 도메인 엔티티와 서비스 연동
- [ ] `upbit_auto_trading/domain/entities/strategy.py` 파일 수정하여 호환성 서비스 사용:
  ```python
  # Strategy 클래스의 _is_compatible_trigger 메서드 실제 구현
  def _is_compatible_trigger(self, trigger: 'Trigger') -> bool:
      """트리거 호환성 검증 (CompatibilityService 위임)"""
      from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
      
      compatibility_service = StrategyCompatibilityService()
      result = compatibility_service.check_trigger_compatibility(self, trigger)
      return result.is_compatible
  ```

- [ ] `upbit_auto_trading/domain/entities/trigger.py` 파일 수정하여 평가 서비스 사용:
  ```python
  # Trigger 클래스의 evaluate 메서드 실제 구현
  def evaluate(self, market_data: 'MarketData') -> bool:
      """조건 평가 로직 (EvaluationService 위임)"""
      from upbit_auto_trading.domain.services.trigger_evaluation_service import TriggerEvaluationService
      
      evaluation_service = TriggerEvaluationService()
      result = evaluation_service.evaluate_trigger(self, market_data)
      return result.result
  ```

## Verification Criteria (완료 검증 조건)

### **[기능 검증]** 단위 테스트 통과
- [ ] `pytest tests/domain/services/test_strategy_compatibility_service.py -v` 실행하여 모든 호환성 테스트가 성공적으로 통과하는 것을 확인
- [ ] `pytest tests/domain/services/test_trigger_evaluation_service.py -v` 실행하여 모든 평가 테스트가 통과하는 것을 확인
- [ ] 코드 커버리지: `pytest tests/domain/services/ --cov=upbit_auto_trading/domain/services --cov-report=html` 실행하여 85% 이상 커버리지 확인

### **[비즈니스 규칙 검증]** 기본 7규칙 전략 호환성 검증
- [ ] Python REPL에서 다음 코드 실행 시 모든 조합이 호환되는지 확인:
  ```python
  from upbit_auto_trading.domain.entities.strategy_factory import StrategyFactory
  from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
  
  # 기본 7규칙 전략 생성
  strategy = StrategyFactory.create_basic_7_rule_strategy()
  
  # 호환성 검증
  compatibility_service = StrategyCompatibilityService()
  result = compatibility_service.validate_strategy(strategy)
  
  print(f"7규칙 전략 호환성: {result}")
  assert result == True, "기본 7규칙 전략의 모든 조합이 호환되어야 합니다"
  ```

### **[실시간 호환성 검증]** 개별 변수 조합 테스트
- [ ] Python REPL에서 다음 호환성 시나리오 검증:
  ```python
  from upbit_auto_trading.domain.services.strategy_compatibility_service import StrategyCompatibilityService
  from upbit_auto_trading.domain.entities.trigger import TradingVariable
  from upbit_auto_trading.domain.value_objects.compatibility_rules import CompatibilityLevel
  
  service = StrategyCompatibilityService()
  
  # 시나리오 1: 같은 그룹 (호환 가능)
  rsi = TradingVariable("RSI", "RSI", "momentum", "subplot", "percentage_comparable")
  stochastic = TradingVariable("Stochastic", "스토캐스틱", "momentum", "subplot", "percentage_comparable")
  result1 = service.check_variable_compatibility([rsi], stochastic)
  assert result1.level == CompatibilityLevel.COMPATIBLE
  
  # 시나리오 2: 다른 그룹, 비호환 (차단)
  macd = TradingVariable("MACD", "MACD", "momentum", "subplot", "zero_centered")
  result2 = service.check_variable_compatibility([rsi], macd)
  assert result2.level == CompatibilityLevel.INCOMPATIBLE
  
  # 시나리오 3: 정규화 가능 (경고)
  close = TradingVariable("Close", "종가", "price", "overlay", "price_comparable")
  result3 = service.check_variable_compatibility([close], rsi)
  assert result3.level == CompatibilityLevel.WARNING
  
  print("✅ 모든 호환성 시나리오 검증 완료")
  ```

### **[트리거 평가 검증]** 조건 평가 로직 테스트
- [ ] Python REPL에서 트리거 평가 시나리오 검증:
  ```python
  from upbit_auto_trading.domain.services.trigger_evaluation_service import TriggerEvaluationService, MarketData
  from datetime import datetime
  
  # 평가 서비스 생성
  service = TriggerEvaluationService()
  
  # 테스트 시장 데이터
  market_data = MarketData(
      symbol="KRW-BTC",
      timestamp=datetime.now(),
      close=50000,
      volume=1000,
      indicators={"RSI": 25.0, "MACD": 0.1}
  )
  
  # 기본 7규칙 전략의 트리거들 평가
  strategy = StrategyFactory.create_basic_7_rule_strategy()
  results = service.evaluate_strategy_triggers(strategy, market_data)
  
  print(f"진입 트리거 평가 결과: {len(results['entry'])}개")
  print(f"청산 트리거 평가 결과: {len(results['exit'])}개")
  
  # 각 결과에 result, value, target_value가 포함되어 있는지 확인
  for result in results['entry']:
      assert hasattr(result, 'result')
      assert hasattr(result, 'value')
      assert hasattr(result, 'target_value')
  
  print("✅ 트리거 평가 로직 검증 완료")
  ```

### **[통합 검증]** 엔티티-서비스 연동 확인
- [ ] 도메인 엔티티에서 서비스 메서드 호출이 정상 동작하는지 확인:
  ```python
  # Strategy.add_trigger에서 호환성 검증이 동작하는지 확인
  strategy = Strategy(StrategyId("TEST"), "테스트 전략")
  compatible_trigger = create_compatible_trigger()  
  incompatible_trigger = create_incompatible_trigger()
  
  # 호환 가능한 트리거는 추가되어야 함
  strategy.add_trigger(compatible_trigger)
  assert len(strategy.get_all_triggers()) == 1
  
  # 비호환 트리거는 예외 발생해야 함
  with pytest.raises(IncompatibleTriggerError):
      strategy.add_trigger(incompatible_trigger)
  
  print("✅ 엔티티-서비스 연동 검증 완료")
  ```

## Notes (주의사항)
- 이 단계에서도 아직 UI나 데이터베이스와 연동하지 않습니다. 순수한 도메인 서비스만 구현합니다.
- 정규화 서비스는 기본적인 구현만 하고, 실제 과거 데이터 기반 정규화는 추후 Infrastructure Layer에서 구현할 예정입니다.
- TriggerEvaluationService의 지표 계산 부분은 임시 구현이며, 실제 ta-lib 연동은 다음 단계에서 진행합니다.
- 모든 호환성 규칙은 docs/VARIABLE_COMPATIBILITY.md 문서의 명세를 정확히 따라야 합니다.
