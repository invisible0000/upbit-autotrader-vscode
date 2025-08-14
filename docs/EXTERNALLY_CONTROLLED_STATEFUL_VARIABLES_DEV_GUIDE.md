# 🔄 외부 제어형 상태 변수 시스템 개발 가이드

## 📋 개요

**목적**: 기존 하드코딩된 관리 전략을 대체하여, 사용자가 트리거 빌더에서 동적으로 조립할 수 있는 재사용 가능한 컴포넌트 시스템

**핵심 아키텍처**: 외부 제어형 상태 변수 패턴 + 통합 파라미터 구조

**지원 전략**: 불타기(Pyramid Buying), 물타기(Cost-Averaging), 트레일링 스탑(Trailing Stop)

## 🏗️ 아키텍처 설계

### 핵심 패턴

#### 1. 수동적 상태 변수 (Passive Stateful Variable)
- 상태 변수는 자신의 상태 관리/계산에만 집중
- 초기화 시점과 정책을 스스로 결정하지 않음
- 외부 명령에 수동적으로 반응하는 `initialize(context)` 메서드 제공

#### 2. 시스템 주도 초기화 (System-Driven Reset)
- Application Layer의 `StrategyExecutionService`가 초기화 제어
- 포지션 생애주기 기반 + 전략 설정 기반 초기화 지원

### DDD 계층 구조
```
📁 upbit_auto_trading/domain/trigger_builder/
├── 📄 enums.py                    # 확장된 enum 정의
├── 📁 entities/
│   └── 📄 trading_variable.py     # 통합 파라미터 지원 확장
├── 📁 value_objects/
│   ├── 📄 variable_parameter.py   # 기존 파라미터 (유지)
│   └── 📄 unified_parameter.py    # 새로운 통합 파라미터
└── 📁 tests/
    └── 📁 value_objects/
        └── 📄 test_unified_parameter.py  # 테스트 스위트
```

## 🎯 핵심 컴포넌트

### 1. 확장된 Enum 정의

```python
# upbit_auto_trading/domain/trigger_builder/enums.py

class VariableCategory(Enum):
    # 기존 카테고리들...
    DYNAMIC_MANAGEMENT = "dynamic_management"  # 동적 관리 (불타기, 물타기, 트레일링 스탑)

class ComparisonGroup(Enum):
    # 기존 그룹들...
    DYNAMIC_TARGET = "dynamic_target"  # 동적 목표값 (불타기/물타기 목표가)

class CalculationMethod(Enum):
    """통합 파라미터 계산 방식"""
    STATIC_VALUE_OFFSET = "static_value_offset"         # 정적 값 차이
    PERCENTAGE_OF_TRACKED = "percentage_of_tracked"     # 추적값 대비 비율
    ENTRY_PRICE_PERCENT = "entry_price_percent"         # 진입가 대비 퍼센트
    AVERAGE_PRICE_PERCENT = "average_price_percent"     # 평단가 대비 퍼센트

class BaseVariable(Enum):
    """기준값 타입"""
    ENTRY_PRICE = "entry_price"         # 최초 진입가
    AVERAGE_PRICE = "average_price"     # 현재 평단가
    CURRENT_PRICE = "current_price"     # 현재가
    HIGH_PRICE = "high_price"           # 고가
    LOW_PRICE = "low_price"             # 저가

class TrailDirection(Enum):
    """트레일링 방향"""
    UP = "up"       # 상향 추적 (고점 추적)
    DOWN = "down"   # 하향 추적 (저점 추적)
```

### 2. UnifiedParameter Value Object

```python
# upbit_auto_trading/domain/trigger_builder/value_objects/unified_parameter.py

@dataclass(frozen=True)
class UnifiedParameter:
    """
    외부 제어형 상태 변수용 통합 파라미터

    동적 관리 전략에서 사용되는 파라미터의 통합 구조:
    - 불타기: 목표가 계산을 위한 base_variable + calculation_method
    - 물타기: 추가 매수 기준을 위한 base_variable + calculation_method
    - 트레일링 스탑: 추적 방향과 계산 방식 조합
    """
    name: str                                    # 파라미터 이름
    calculation_method: CalculationMethod        # 계산 방식
    base_variable: BaseVariable                  # 기준값 타입
    value: Decimal                              # 계산에 사용될 값 (퍼센트, 원화 등)
    trail_direction: Optional[TrailDirection] = None  # 트레일링 방향 (트레일링 스탑용)

    def calculate_target_value(self, context: dict[str, Any]) -> Decimal:
        """컨텍스트를 기반으로 목표값 계산"""
        # 구현 세부사항...

    def get_description(self) -> str:
        """파라미터 설명 텍스트 생성"""
        # 구현 세부사항...
```

### 3. 확장된 TradingVariable Entity

```python
# upbit_auto_trading/domain/trigger_builder/entities/trading_variable.py

@dataclass
class TradingVariable:
    # 기존 필드들...
    parameters: List[VariableParameter] = field(default_factory=list)
    unified_parameters: List[UnifiedParameter] = field(default_factory=list)  # 신규 추가

    def add_unified_parameter(self, parameter: UnifiedParameter) -> None:
        """통합 파라미터 추가 (동적 관리 전략용)"""

    def get_unified_parameter(self, parameter_name: str) -> Optional[UnifiedParameter]:
        """통합 파라미터 조회"""

    def is_dynamic_management_variable(self) -> bool:
        """동적 관리 변수인지 확인"""
        return self.purpose_category == VariableCategory.DYNAMIC_MANAGEMENT
```

## 🎮 사용 시나리오

### 1. 불타기 (Pyramid Buying) 전략

```python
# 진입가 대비 5% 수익 시 추가 매수
pyramid_parameter = UnifiedParameter(
    name="profit_threshold",
    calculation_method=CalculationMethod.ENTRY_PRICE_PERCENT,
    base_variable=BaseVariable.ENTRY_PRICE,
    value=Decimal("5")  # 5% 수익
)

# 실행 컨텍스트
context = {
    "entry_price": 50000,
    "current_price": 52500,
    "average_price": 50000
}

target_price = pyramid_parameter.calculate_target_value(context)
# 결과: 52500 (50000 * 1.05)
```

### 2. 물타기 (Cost-Averaging) 전략

```python
# 평단가 대비 -3% 손실 시 추가 매수
martingale_parameter = UnifiedParameter(
    name="loss_threshold",
    calculation_method=CalculationMethod.AVERAGE_PRICE_PERCENT,
    base_variable=BaseVariable.AVERAGE_PRICE,
    value=Decimal("-3")  # -3% 손실
)

context = {
    "entry_price": 50000,
    "current_price": 47530,
    "average_price": 49000
}

target_price = martingale_parameter.calculate_target_value(context)
# 결과: 47530 (49000 * 0.97)
```

### 3. 트레일링 스탑 전략

```python
# 고점 대비 -2% 하락 시 매도
trailing_parameter = UnifiedParameter(
    name="trailing_stop",
    calculation_method=CalculationMethod.PERCENTAGE_OF_TRACKED,
    base_variable=BaseVariable.HIGH_PRICE,
    value=Decimal("-2"),  # -2% 하락
    trail_direction=TrailDirection.DOWN
)

context = {
    "tracked_value": 55000,  # 추적 중인 고점
    "high_price": 55000,
    "current_price": 52000
}

stop_price = trailing_parameter.calculate_target_value(context)
# 결과: 53900 (55000 * 0.98)
```

## 🔄 초기화 제어 시스템

### Application Layer 초기화 로직

```python
class StrategyExecutionService:
    """전략 실행 서비스 - 상태 변수 초기화 제어"""

    def process_trade_cycle(self, strategy_id: str) -> None:
        strategy = self.strategy_repo.get_by_id(strategy_id)
        position = self.position_repo.get_by_strategy(strategy_id)

        # 1. EXIT 시그널 확인
        exit_signal_fired = strategy.evaluate_for_exit_signal(market_data)

        # 2. 전략 설정 기반 초기화
        if strategy.reset_variables_on_exit and exit_signal_fired:
            for var in strategy.get_dynamic_management_variables():
                var.initialize(position_context)
            self.close_position(position)

        # 3. 포지션 생애주기 기반 초기화
        if position.is_closed() and strategy.is_continuous():
            for var in strategy.get_dynamic_management_variables():
                var.initialize(context=None)  # 신규 포지션 전 리셋
```

### 초기화 트리거 조건

#### 1. 포지션 생애주기 기반 (필수)
- **시점**: 포지션 완전 청산 후 → 신규 포지션 생성 직전
- **목적**: 거래 사이클 간 독립성 보장
- **제어**: 시스템 레벨에서 강제 실행

#### 2. 전략 설정 기반 (선택적)
- **시점**: EXIT 타입 시그널 발생 직후
- **조건**: `user_strategies.reset_variables_on_exit = true`
- **목적**: 부분 익절 후 관리 로직 기준점 리셋

## 🧪 테스트 아키텍처

### 테스트 커버리지 (44개 테스트 통과)

```python
# tests/domain/trigger_builder/value_objects/test_unified_parameter.py

class TestUnifiedParameter:
    """UnifiedParameter 통합 테스트 스위트"""

    def test_static_value_offset_calculation(self):
        """정적 값 차이 계산 테스트"""

    def test_entry_price_percent_calculation(self):
        """진입가 대비 퍼센트 계산 테스트"""

    def test_average_price_percent_calculation(self):
        """평단가 대비 퍼센트 계산 테스트"""

    def test_percentage_of_tracked_calculation(self):
        """추적값 대비 비율 계산 테스트"""

    def test_trailing_description_generation(self):
        """트레일링 설명 텍스트 생성 테스트"""

    # ... 추가 테스트들
```

### TDD 검증 시나리오
```bash
# 전체 도메인 테스트 실행
python -m pytest tests/domain/trigger_builder/ -v

# 44 passed, 0 failed
# ✅ 기존 27개 + 신규 17개 = 총 44개 테스트 통과
```

## 🔗 기존 시스템과의 호환성

### 하위 호환성 보장

```python
class TradingVariable:
    # 기존 VariableParameter 지원 (유지)
    parameters: List[VariableParameter] = field(default_factory=list)

    # 새로운 UnifiedParameter 지원 (추가)
    unified_parameters: List[UnifiedParameter] = field(default_factory=list)

    def validate_required_parameters(self) -> None:
        """기존 파라미터와 통합 파라미터 모두 검증"""
        if self.parameter_required and not self.parameters and not self.unified_parameters:
            raise ValidationError(f"변수 '{self.variable_id}'는 파라미터가 필요합니다")
```

### 기본 7규칙 전략 지원

현재 구현된 시스템은 **BASIC_7_RULE_STRATEGY_GUIDE.md**에 명시된 7규칙을 완벽하게 지원:

1. **RSI 과매도 진입**: 기존 TradingVariable 지원
2. **수익시 불타기**: UnifiedParameter로 구현 ✅
3. **계획된 익절**: 기존 고정 익절 + UnifiedParameter 조합
4. **트레일링 스탑**: UnifiedParameter로 구현 ✅
5. **하락시 물타기**: UnifiedParameter로 구현 ✅
6. **급락 감지**: 모니터링 시스템 (별도)
7. **급등 감지**: 모니터링 시스템 (별도)

## 🎯 확장 포인트

### 새로운 계산 방식 추가
```python
class CalculationMethod(Enum):
    # 기존 방식들...
    FIBONACCI_RETRACEMENT = "fibonacci_retracement"  # 피보나치 되돌림
    VOLUME_WEIGHTED_PERCENT = "volume_weighted_percent"  # 거래량 가중 비율
```

### 새로운 기준값 추가
```python
class BaseVariable(Enum):
    # 기존 기준값들...
    VWAP = "vwap"                    # 거래량 가중 평균가
    YESTERDAY_CLOSE = "yesterday_close"  # 전일 종가
```

### 복합 전략 지원
```python
# 여러 UnifiedParameter 조합으로 복잡한 전략 구성
complex_strategy_variable = TradingVariable(
    variable_id="complex_martingale",
    purpose_category=VariableCategory.DYNAMIC_MANAGEMENT,
    unified_parameters=[
        pyramid_parameter,    # 불타기
        martingale_parameter, # 물타기
        trailing_parameter    # 트레일링 스탑
    ]
)
```

## 📈 성능 최적화

### 계산 캐싱
```python
@lru_cache(maxsize=128)
def calculate_target_value_cached(self, context_hash: str) -> Decimal:
    """컨텍스트 해시 기반 계산 결과 캐싱"""
```

### 배치 계산 지원
```python
def calculate_batch_targets(self, contexts: List[dict]) -> List[Decimal]:
    """여러 컨텍스트에 대한 배치 계산"""
```

## 🔍 모니터링 및 디버깅

### 로깅 전략
```python
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("UnifiedParameter")

def calculate_target_value(self, context: dict[str, Any]) -> Decimal:
    logger.info(f"목표값 계산 시작: {self.name}")
    logger.debug(f"컨텍스트: {context}")

    result = self._perform_calculation(context)

    logger.info(f"목표값 계산 완료: {result}")
    return result
```

### 실시간 상태 추적
```python
class StatefulVariableMonitor:
    """상태 변수 실시간 모니터링"""

    def track_initialization(self, variable_name: str, context: dict):
        """초기화 이벤트 추적"""

    def track_calculation(self, variable_name: str, input_context: dict, output_value: Decimal):
        """계산 이벤트 추적"""
```

## 🚀 배포 가이드

### Phase 2 Infrastructure Layer 준비사항

1. **Repository 구현**: UnifiedParameter 영속화
2. **DTO 계층**: API 통신용 데이터 변환
3. **Service 계층**: 비즈니스 로직 조율
4. **UI 계층**: 트리거 빌더 통합

### 마이그레이션 전략

```sql
-- 기존 테이블 확장
ALTER TABLE trading_variables ADD COLUMN unified_parameters TEXT;

-- 새로운 계산 방식 지원
INSERT INTO enum_values (enum_type, value, display_name_ko) VALUES
('calculation_method', 'static_value_offset', '정적 값 차이'),
('calculation_method', 'percentage_of_tracked', '추적값 대비 비율'),
('calculation_method', 'entry_price_percent', '진입가 대비 퍼센트'),
('calculation_method', 'average_price_percent', '평단가 대비 퍼센트');
```

## 📚 관련 문서

- **[외부 제어형 상태 변수 시스템 기술사양서](외부 제어형 상태 변수 시스템.md)**: 상세 기술 사양
- **[기본 7규칙 전략 가이드](BASIC_7_RULE_STRATEGY_GUIDE.md)**: 시스템 검증 기준
- **[전략 시스템 가이드](STRATEGY_GUIDE.md)**: 전체 전략 아키텍처
- **[트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)**: UI 통합 방법
- **[DDD 아키텍처 가이드](ARCHITECTURE_GUIDE.md)**: 도메인 주도 설계 원칙

---

## 🎉 구현 완료 현황

### ✅ Phase 1 완료 (Domain Layer)
- 🏗️ **아키텍처**: DDD 4계층 구조 + MVP 패턴
- 🎯 **도메인 모델**: TradingVariable + UnifiedParameter
- 🔧 **Value Objects**: 통합 파라미터 구조 완성
- 🧪 **테스트**: 44개 테스트 통과 (100% 성공률)

### 🎯 핵심 성과
- **확장성 확보**: 새로운 계산 방식/기준값 쉽게 추가 가능
- **하위 호환성**: 기존 VariableParameter와 동시 지원
- **타입 안전성**: 강타입 시스템으로 런타임 오류 방지
- **도메인 순수성**: 외부 의존성 없는 순수 도메인 로직

### 📈 다음 단계
**Phase 2**: Infrastructure Layer 구현
- Database Repository 패턴
- REST API DTO 계층
- Service 계층 비즈니스 로직
- PyQt6 UI 통합

**최종 검증**: `python run_desktop_ui.py` → 전략 관리 → 트리거 빌더에서 7규칙 전략 구성 테스트

---

**💡 핵심 아키텍처 가치**: "외부 제어형 상태 변수"라는 단일 패턴으로 복잡한 동적 관리 전략을 통합하여 **유연성, 일관성, 확장성**을 동시에 확보!
