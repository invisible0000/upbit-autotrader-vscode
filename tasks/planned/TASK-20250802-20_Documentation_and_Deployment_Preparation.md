# 📋 TASK-20250802-20: 문서화 및 배포 준비

## 🎯 **작업 개요**
리팩토링된 트리거 빌더 시스템의 완전한 문서화와 운영 환경 배포 준비를 완료합니다.

## 📊 **현재 상황**

### **문서화 대상**
```python
# 완성된 시스템 구조
├── business_logic/triggers/          # 비즈니스 로직 레이어
│   ├── engines/                     # 계산 엔진들
│   ├── models/                      # 데이터 모델들
│   └── services/                    # 서비스 레이어
├── business_logic/visualization/     # 시각화 레이어
├── business_logic/optimization/      # 성능 최적화
├── ui/desktop/adapters/triggers/     # UI 어댑터
└── tests/                           # 테스트 코드

# 문서화 필요 영역
├── API 문서 (모든 public 메서드)
├── 아키텍처 가이드 (시스템 구조 설명)
├── 사용자 가이드 (기존 사용자용)
├── 개발자 가이드 (확장 개발용)
├── 마이그레이션 가이드 (기존 코드 대체)
├── 성능 가이드 (최적화 활용법)
└── 배포 가이드 (운영 환경 설정)
```

### **배포 준비 사항**
```python
# 배포 환경 설정
├── 환경 변수 설정
├── 의존성 관리 (requirements.txt 업데이트)
├── 설정 파일 마이그레이션
├── 데이터베이스 스키마 업데이트
├── 로깅 설정 최적화
├── 모니터링 설정
└── 백업 및 롤백 계획
```

## 🏗️ **구현 목표**

### **문서화 구조**
```
docs/trigger_builder_refactoring/
├── README.md                                   # 전체 개요
├── architecture/
│   ├── system_overview.md                     # 시스템 전체 구조
│   ├── business_logic_architecture.md         # 비즈니스 로직 구조
│   ├── ui_adapter_pattern.md                  # UI 어댑터 패턴
│   └── performance_optimization.md            # 성능 최적화 구조
├── api_reference/
│   ├── trigger_orchestration_service.md       # 트리거 오케스트레이션 API
│   ├── technical_indicator_calculator.md      # 기술 지표 계산 API
│   ├── trigger_point_detector.md              # 트리거 탐지 API
│   ├── cross_signal_analyzer.md               # 크로스 신호 분석 API
│   ├── condition_management_service.md        # 조건 관리 API
│   ├── minichart_orchestration_service.md     # 차트 서비스 API
│   └── ui_adapter_api.md                      # UI 어댑터 API
├── user_guides/
│   ├── migration_guide.md                     # 기존 코드 마이그레이션
│   ├── usage_examples.md                      # 사용법 예제
│   ├── troubleshooting.md                     # 문제 해결 가이드
│   └── performance_tips.md                    # 성능 최적화 팁
├── developer_guides/
│   ├── extending_indicators.md                # 지표 확장 개발
│   ├── custom_triggers.md                     # 커스텀 트리거 개발
│   ├── ui_customization.md                    # UI 커스터마이징
│   └── testing_guidelines.md                  # 테스트 가이드라인
└── deployment/
    ├── production_setup.md                    # 운영 환경 설정
    ├── monitoring_setup.md                    # 모니터링 설정
    ├── backup_strategy.md                     # 백업 전략
    └── rollback_procedures.md                 # 롤백 절차
```

## 📋 **상세 작업 내용**

### **1. 시스템 아키텍처 문서화 (3시간)**
```markdown
# docs/trigger_builder_refactoring/architecture/system_overview.md

# 트리거 빌더 시스템 아키텍처 개요

## 🏗️ 전체 시스템 구조

### 아키텍처 원칙
- **관심사 분리**: UI와 비즈니스 로직 완전 분리
- **어댑터 패턴**: 기존 호환성 100% 보장
- **성능 최적화**: 벡터화, 병렬 처리, 메모리 최적화
- **확장성**: 새로운 지표 및 트리거 쉽게 추가 가능
- **테스트 가능성**: 모든 컴포넌트 독립적 테스트 지원

### 레이어 구조

```
┌─────────────────────────────────────────┐
│           UI Layer (PyQt6)              │
│  ┌─────────────────────────────────┐    │
│  │    trigger_builder_screen.py    │    │  ← 기존 파일 (UI만 남김)
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │ 어댑터 패턴
┌─────────────────▼───────────────────────┐
│          Adapter Layer                  │
│  ┌─────────────────────────────────┐    │
│  │   trigger_builder_adapter.py    │    │  ← 새로운 어댑터
│  └─────────────────────────────────┘    │
└─────────────────┬───────────────────────┘
                  │ 서비스 호출
┌─────────────────▼───────────────────────┐
│        Business Logic Layer            │
│                                         │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │    Services     │ │ Visualization   ││
│  │                 │ │                 ││
│  │ • Orchestration │ │ • Chart Engine  ││
│  │ • Condition Mgmt│ │ • Data Models   ││
│  └─────────────────┘ └─────────────────┘│
│                                         │
│  ┌─────────────────┐ ┌─────────────────┐│
│  │     Engines     │ │     Models      ││
│  │                 │ │                 ││
│  │ • Indicator Calc│ │ • Trigger Models││
│  │ • Trigger Detect│ │ • Chart Models  ││
│  │ • Cross Analysis│ │ • Config Models ││
│  └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────┘
```

### 주요 컴포넌트

#### 1. 트리거 오케스트레이션 서비스
- **역할**: 전체 트리거 워크플로우 관리
- **핵심 기능**: 
  - 지표 계산 → 트리거 탐지 → 결과 반환
  - 복잡한 조건 조합 처리
  - 성능 최적화 적용

#### 2. 기술 지표 계산 엔진
- **역할**: 모든 기술 지표 계산
- **최적화**: NumPy 벡터화, Numba JIT 컴파일
- **지원 지표**: SMA, EMA, RSI, MACD, Bollinger Bands 등

#### 3. 트리거 포인트 탐지기
- **역할**: 조건 기반 트리거 포인트 탐지
- **알고리즘**: 효율적인 순회 및 조건 매칭
- **지원 연산자**: crosses_above, crosses_below, greater_than 등

#### 4. 크로스 신호 분석기
- **역할**: 두 지표간 교차점 분석
- **최적화**: O(n) 복잡도 알고리즘
- **신호 타입**: Golden Cross, Death Cross 등

#### 5. 미니차트 시각화 서비스
- **역할**: UI 독립적 차트 데이터 생성
- **호환성**: 기존 shared_simulation과 100% 호환
- **기능**: 지표 오버레이, 신호 마킹, 테마 지원

### 데이터 흐름

```
가격 데이터 입력
      ↓
기술 지표 계산 (병렬)
      ↓
트리거 조건 검사
      ↓
크로스 신호 분석
      ↓
결과 데이터 생성
      ↓
차트 시각화 데이터
      ↓
UI 표시
```

## 🔧 성능 최적화

### 벡터화 최적화
- **NumPy 활용**: 모든 계산을 NumPy 배열 기반으로 수행
- **Numba JIT**: 핫스팟 함수에 JIT 컴파일 적용
- **메모리 효율성**: 불필요한 복사 최소화

### 병렬 처리
- **지표 계산**: ThreadPoolExecutor를 통한 병렬 계산
- **배치 처리**: 대용량 데이터를 배치로 분할하여 처리
- **캐싱**: 계산 결과 캐싱으로 중복 계산 방지

### 메모리 관리
- **자동 GC**: 메모리 임계값 초과 시 자동 가비지 컬렉션
- **약한 참조**: 대용량 객체의 자동 정리
- **메모리 모니터링**: 실시간 메모리 사용량 추적

## 🧪 테스트 전략

### 단위 테스트
- 모든 엔진과 서비스의 독립적 테스트
- 90% 이상 코드 커버리지 목표

### 통합 테스트
- 전체 워크플로우 엔드투엔드 테스트
- 기존 시스템과의 호환성 검증

### 성능 테스트
- 벤치마크 기반 성능 회귀 방지
- 메모리 누수 및 병목 지점 모니터링

## 🚀 확장성

### 새로운 지표 추가
```python
# 새로운 지표는 기존 인터페이스를 구현하여 쉽게 추가
class CustomIndicatorCalculator(BaseIndicatorCalculator):
    def calculate(self, prices: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        # 커스텀 지표 계산 로직
        pass
```

### 새로운 트리거 조건 추가
```python
# 새로운 연산자는 조건 검사기에 메서드 추가로 구현
class TriggerConditionChecker:
    def check_custom_condition(self, data: np.ndarray, params: Dict[str, Any]) -> List[int]:
        # 커스텀 조건 검사 로직
        pass
```

---

이 아키텍처는 기존 시스템의 완전한 호환성을 보장하면서도, 성능과 확장성을 크게 개선한 현대적인 구조를 제공합니다.
```

### **2. API 레퍼런스 문서 생성 (3시간)**
```markdown
# docs/trigger_builder_refactoring/api_reference/trigger_orchestration_service.md

# TriggerOrchestrationService API 레퍼런스

## 개요
`TriggerOrchestrationService`는 트리거 빌더의 핵심 서비스로, 전체 트리거 탐지 워크플로우를 관리합니다.

## 클래스 정의

```python
class TriggerOrchestrationService:
    """트리거 오케스트레이션 서비스 - 전체 트리거 워크플로우 관리"""
    
    def __init__(self):
        """서비스 초기화"""
```

## 주요 메서드

### calculate_indicators()
지정된 지표들을 계산합니다.

```python
def calculate_indicators(self, price_data: List[float], 
                        indicators: Dict[str, Dict[str, Any]]) -> IndicatorCalculationResult:
    """
    기술 지표 계산
    
    Args:
        price_data: 가격 데이터 리스트
        indicators: 계산할 지표 설정
                   예: {"SMA": {"period": 20}, "RSI": {"period": 14}}
    
    Returns:
        IndicatorCalculationResult: 계산 결과
        
    Example:
        >>> service = TriggerOrchestrationService()
        >>> price_data = [100, 101, 102, 103, 104]
        >>> indicators = {"SMA": {"period": 3}}
        >>> result = service.calculate_indicators(price_data, indicators)
        >>> print(result.success)  # True
        >>> print(result.indicators["SMA"])  # [nan, nan, 101.0, 102.0, 103.0]
    """
```

**매개변수:**
- `price_data` (List[float]): 가격 데이터 리스트
- `indicators` (Dict[str, Dict[str, Any]]): 계산할 지표와 매개변수

**반환값:**
- `IndicatorCalculationResult`: 계산 결과 객체

**예외:**
- `ValueError`: 잘못된 지표 이름 또는 매개변수
- `RuntimeError`: 계산 중 오류 발생

### detect_triggers()
조건에 따라 트리거 포인트를 탐지합니다.

```python
def detect_triggers(self, price_data: List[float], 
                   conditions: List[Dict[str, Any]]) -> TriggerDetectionResult:
    """
    트리거 포인트 탐지
    
    Args:
        price_data: 가격 데이터 리스트
        conditions: 탐지 조건 리스트
    
    Returns:
        TriggerDetectionResult: 탐지 결과
        
    Example:
        >>> conditions = [{
        ...     "variable": "SMA_20",
        ...     "operator": "crosses_above", 
        ...     "target": "price"
        ... }]
        >>> result = service.detect_triggers(price_data, conditions)
        >>> print(result.trigger_points)  # [15, 28, 45]
    """
```

### analyze_cross_signals()
크로스 신호를 분석합니다.

```python
def analyze_cross_signals(self, data1: List[float], data2: List[float], 
                         signal_type: str = "golden_cross") -> CrossSignalResult:
    """
    크로스 신호 분석
    
    Args:
        data1: 첫 번째 데이터 시리즈 (예: 단기 이동평균)
        data2: 두 번째 데이터 시리즈 (예: 장기 이동평균)
        signal_type: 신호 타입 ("golden_cross", "death_cross", "any_cross")
    
    Returns:
        CrossSignalResult: 크로스 신호 분석 결과
        
    Example:
        >>> sma_short = service.calculate_indicators(prices, {"SMA": {"period": 10}})
        >>> sma_long = service.calculate_indicators(prices, {"SMA": {"period": 20}})
        >>> result = service.analyze_cross_signals(
        ...     sma_short.indicators["SMA"], 
        ...     sma_long.indicators["SMA"], 
        ...     "golden_cross"
        ... )
        >>> print(result.cross_points)  # [25, 67]
    """
```

### run_complete_simulation()
전체 시뮬레이션을 실행합니다.

```python
def run_complete_simulation(self, price_data: List[float], 
                           simulation_config: Dict[str, Any]) -> SimulationResult:
    """
    완전한 트리거 시뮬레이션 실행
    
    Args:
        price_data: 가격 데이터
        simulation_config: 시뮬레이션 설정
            - conditions: 트리거 조건 리스트
            - indicators: 계산할 지표들
            - analysis_options: 분석 옵션
    
    Returns:
        SimulationResult: 시뮬레이션 전체 결과
        
    Example:
        >>> config = {
        ...     "conditions": [{"variable": "RSI_14", "operator": "less_than", "threshold": 30}],
        ...     "indicators": {"RSI": {"period": 14}, "SMA": {"period": 20}},
        ...     "analysis_options": {"include_cross_signals": True}
        ... }
        >>> result = service.run_complete_simulation(price_data, config)
        >>> print(f"트리거: {len(result.trigger_points)}개")
        >>> print(f"지표: {list(result.indicators.keys())}")
    """
```

## 결과 클래스

### IndicatorCalculationResult
```python
@dataclass
class IndicatorCalculationResult:
    success: bool
    indicators: Dict[str, List[float]]
    calculation_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### TriggerDetectionResult
```python
@dataclass  
class TriggerDetectionResult:
    success: bool
    trigger_points: List[int]
    conditions_met: List[Dict[str, Any]]
    detection_time: float
    error_message: Optional[str] = None
```

### SimulationResult
```python
@dataclass
class SimulationResult:
    success: bool
    trigger_points: List[int]
    indicators: Dict[str, List[float]]
    cross_signals: List[Dict[str, Any]]
    chart_data: Optional[Any]
    simulation_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## 사용 예제

### 기본 사용법
```python
from business_logic.triggers.services.trigger_orchestration_service import TriggerOrchestrationService

# 서비스 초기화
service = TriggerOrchestrationService()

# 가격 데이터 준비
price_data = [100, 101, 99, 102, 104, 103, 105, 107, 106, 108]

# 1. 지표 계산
indicators = {
    "SMA": {"period": 5},
    "RSI": {"period": 14}
}
indicator_result = service.calculate_indicators(price_data, indicators)

if indicator_result.success:
    print(f"SMA 계산 완료: {len(indicator_result.indicators['SMA'])}개 값")

# 2. 트리거 탐지
conditions = [
    {
        "variable": "SMA_5",
        "operator": "crosses_above",
        "target": "price"
    }
]
trigger_result = service.detect_triggers(price_data, conditions)

if trigger_result.success:
    print(f"트리거 포인트: {trigger_result.trigger_points}")

# 3. 완전한 시뮬레이션
simulation_config = {
    "conditions": conditions,
    "indicators": indicators,
    "analysis_options": {
        "include_cross_signals": True,
        "generate_chart_data": True
    }
}
simulation_result = service.run_complete_simulation(price_data, simulation_config)

if simulation_result.success:
    print(f"시뮬레이션 완료:")
    print(f"  - 트리거: {len(simulation_result.trigger_points)}개")
    print(f"  - 지표: {list(simulation_result.indicators.keys())}")
    print(f"  - 실행 시간: {simulation_result.simulation_time:.3f}초")
```

### 고급 사용법
```python
# 복잡한 조건 조합
complex_conditions = [
    {
        "variable": "RSI_14",
        "operator": "less_than",
        "threshold": 30
    },
    {
        "variable": "SMA_20",
        "operator": "greater_than",
        "target": "SMA_50"
    }
]

# 다중 지표 계산
multiple_indicators = {
    "SMA": {"period": 20},
    "EMA": {"period": 20}, 
    "RSI": {"period": 14},
    "MACD": {"fast": 12, "slow": 26, "signal": 9}
}

# 성능 최적화 옵션 포함
optimized_config = {
    "conditions": complex_conditions,
    "indicators": multiple_indicators,
    "performance_options": {
        "use_parallel_processing": True,
        "enable_caching": True,
        "memory_optimization": True
    }
}

result = service.run_complete_simulation(price_data, optimized_config)
```

## 성능 가이드

### 최적 사용법
1. **대용량 데이터**: 10,000개 이상의 포인트에서는 병렬 처리 활성화
2. **반복 계산**: 동일한 지표를 여러 번 계산할 때는 캐싱 활용
3. **메모리 관리**: 메모리 제약이 있는 환경에서는 배치 처리 사용

### 성능 팁
```python
# 좋은 예: 지표들을 한 번에 계산
indicators = {"SMA": {"period": 20}, "RSI": {"period": 14}}
result = service.calculate_indicators(price_data, indicators)

# 나쁜 예: 지표를 하나씩 계산
sma_result = service.calculate_indicators(price_data, {"SMA": {"period": 20}})
rsi_result = service.calculate_indicators(price_data, {"RSI": {"period": 14}})
```

## 오류 처리

### 일반적인 오류
```python
try:
    result = service.calculate_indicators(price_data, indicators)
    if not result.success:
        print(f"계산 실패: {result.error_message}")
except ValueError as e:
    print(f"잘못된 매개변수: {str(e)}")
except RuntimeError as e:
    print(f"런타임 오류: {str(e)}")
```

### 디버깅 정보
```python
# 상세 로깅 활성화
import logging
logging.getLogger('business_logic.triggers').setLevel(logging.DEBUG)

# 결과 메타데이터 확인
if result.success:
    print(f"실행 메타데이터: {result.metadata}")
```
```

### **3. 사용자 마이그레이션 가이드 (2시간)**
```markdown
# docs/trigger_builder_refactoring/user_guides/migration_guide.md

# 기존 코드 마이그레이션 가이드

## 🎯 개요
이 가이드는 기존 `trigger_builder_screen.py`를 사용하던 코드를 새로운 아키텍처로 마이그레이션하는 방법을 설명합니다.

## 🔄 주요 변경사항

### 기존 vs 새로운 구조

| 항목 | 기존 방식 | 새로운 방식 |
|------|-----------|-------------|
| 지표 계산 | `trigger_builder_screen._calculate_sma()` | `TriggerOrchestrationService.calculate_indicators()` |
| 트리거 탐지 | `trigger_builder_screen.calculate_trigger_points()` | `TriggerOrchestrationService.detect_triggers()` |
| 시뮬레이션 | `trigger_simulation_service.run_simulation()` | `TriggerOrchestrationService.run_complete_simulation()` |
| UI 상호작용 | 직접 PyQt6 위젯 조작 | `TriggerBuilderAdapter` 사용 |

## 📋 단계별 마이그레이션

### 1단계: 의존성 업데이트

기존 import 문을 새로운 구조로 변경:

```python
# 기존 방식 ❌
from ui.desktop.screens.strategy_management.components.triggers.trigger_builder_screen import TriggerBuilderScreen

# 새로운 방식 ✅
from business_logic.triggers.services.trigger_orchestration_service import TriggerOrchestrationService
from ui.desktop.adapters.triggers.trigger_builder_adapter import TriggerBuilderAdapter
```

### 2단계: 지표 계산 마이그레이션

#### 기존 코드
```python
# 기존 방식 ❌
trigger_builder = TriggerBuilderScreen(parent)
price_data = [100, 101, 102, 103, 104]

# SMA 계산
sma_result = trigger_builder._calculate_sma(price_data, 20)

# RSI 계산
rsi_result = trigger_builder._calculate_rsi(price_data, 14)

# MACD 계산
macd_result = trigger_builder._calculate_macd(price_data, 12, 26, 9)
```

#### 새로운 코드
```python
# 새로운 방식 ✅
service = TriggerOrchestrationService()
price_data = [100, 101, 102, 103, 104]

# 모든 지표를 한 번에 계산 (성능 최적화)
indicators = {
    "SMA": {"period": 20},
    "RSI": {"period": 14},
    "MACD": {"fast": 12, "slow": 26, "signal": 9}
}

result = service.calculate_indicators(price_data, indicators)

if result.success:
    sma_result = result.indicators["SMA"]
    rsi_result = result.indicators["RSI"]
    macd_result = result.indicators["MACD"]  # [macd_line, signal_line, histogram]
else:
    print(f"계산 실패: {result.error_message}")
```

### 3단계: 트리거 탐지 마이그레이션

#### 기존 코드
```python
# 기존 방식 ❌
variable_name = "SMA_20"
operator = "crosses_above"
threshold = 105

# 트리거 포인트 계산
trigger_points = trigger_builder.calculate_trigger_points(
    variable_name, operator, threshold
)
```

#### 새로운 코드
```python
# 새로운 방식 ✅
conditions = [
    {
        "variable": "SMA_20",
        "operator": "crosses_above",
        "threshold": 105
    }
]

result = service.detect_triggers(price_data, conditions)

if result.success:
    trigger_points = result.trigger_points
    print(f"트리거 포인트: {trigger_points}")
else:
    print(f"탐지 실패: {result.error_message}")
```

### 4단계: 복잡한 조건 처리

#### 기존 코드
```python
# 기존 방식 ❌ - 여러 조건을 개별적으로 처리
rsi_triggers = trigger_builder.calculate_trigger_points("RSI_14", "less_than", 30)
sma_triggers = trigger_builder.calculate_trigger_points("SMA_20", "greater_than", "SMA_50")

# 수동으로 조건 결합
combined_triggers = []
for point in rsi_triggers:
    if point in sma_triggers:
        combined_triggers.append(point)
```

#### 새로운 코드
```python
# 새로운 방식 ✅ - 다중 조건을 자동으로 처리
conditions = [
    {
        "variable": "RSI_14",
        "operator": "less_than",
        "threshold": 30
    },
    {
        "variable": "SMA_20", 
        "operator": "greater_than",
        "target": "SMA_50"
    }
]

result = service.detect_triggers(price_data, conditions)

if result.success:
    # 모든 조건을 만족하는 포인트가 자동으로 반환됨
    combined_triggers = result.trigger_points
```

### 5단계: 시뮬레이션 마이그레이션

#### 기존 코드
```python
# 기존 방식 ❌ - 단계별 수동 처리
# 1. 지표 계산
sma_data = trigger_builder._calculate_sma(price_data, 20)
rsi_data = trigger_builder._calculate_rsi(price_data, 14)

# 2. 트리거 탐지
triggers = trigger_builder.calculate_trigger_points("RSI_14", "less_than", 30)

# 3. 차트 데이터 준비
chart_data = trigger_builder.create_chart_data(price_data, triggers)

# 4. 시뮬레이션 서비스 호출
sim_service = trigger_builder.trigger_simulation_service
sim_result = sim_service.run_simulation(chart_data)
```

#### 새로운 코드
```python
# 새로운 방식 ✅ - 통합 워크플로우
simulation_config = {
    "conditions": [
        {
            "variable": "RSI_14",
            "operator": "less_than", 
            "threshold": 30
        }
    ],
    "indicators": {
        "SMA": {"period": 20},
        "RSI": {"period": 14}
    },
    "analysis_options": {
        "include_cross_signals": True,
        "generate_chart_data": True
    }
}

result = service.run_complete_simulation(price_data, simulation_config)

if result.success:
    print(f"시뮬레이션 결과:")
    print(f"  - 트리거: {len(result.trigger_points)}개")
    print(f"  - 지표: {list(result.indicators.keys())}")
    print(f"  - 차트 데이터: {'있음' if result.chart_data else '없음'}")
    print(f"  - 실행 시간: {result.simulation_time:.3f}초")
```

### 6단계: UI 연동 마이그레이션

#### 기존 코드
```python
# 기존 방식 ❌ - 직접 UI 조작
class CustomTriggerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.trigger_builder = TriggerBuilderScreen(self)
        
    def on_calculate_clicked(self):
        # UI에서 값 직접 추출
        price_data = self.get_price_data()
        variable = self.variable_combo.currentText()
        operator = self.operator_combo.currentText()
        threshold = self.threshold_spin.value()
        
        # 직접 계산 호출
        result = self.trigger_builder.calculate_trigger_points(
            variable, operator, threshold
        )
        
        # UI 직접 업데이트
        self.update_result_display(result)
```

#### 새로운 코드
```python
# 새로운 방식 ✅ - 어댑터 패턴 사용
class CustomTriggerWidget(QWidget):
    def __init__(self):
        super().__init__()
        # 어댑터를 통한 비즈니스 로직 접근
        self.adapter = TriggerBuilderAdapter()
        
    def on_calculate_clicked(self):
        # UI에서 값 추출
        price_data = self.get_price_data()
        
        # 어댑터를 통한 계산
        conditions = [{
            "variable": self.variable_combo.currentText(),
            "operator": self.operator_combo.currentText(),
            "threshold": self.threshold_spin.value()
        }]
        
        result = self.adapter.detect_triggers(price_data, conditions)
        
        # 결과 처리
        if result.success:
            self.update_result_display(result.trigger_points)
        else:
            self.show_error_message(result.error_message)
```

## 🔧 일반적인 마이그레이션 패턴

### 패턴 1: 단순 메서드 교체

```python
# 기존: 개별 메서드 호출
old_result = trigger_builder._calculate_sma(prices, 20)

# 새로운: 통합 서비스 사용
new_result = service.calculate_indicators(prices, {"SMA": {"period": 20}})
sma_values = new_result.indicators["SMA"] if new_result.success else []
```

### 패턴 2: 오류 처리 개선

```python
# 기존: 예외 기반 오류 처리
try:
    result = trigger_builder.some_calculation()
except Exception as e:
    handle_error(str(e))

# 새로운: 결과 객체 기반 오류 처리
result = service.some_calculation()
if result.success:
    process_result(result.data)
else:
    handle_error(result.error_message)
```

### 패턴 3: 성능 최적화

```python
# 기존: 순차적 계산
sma_result = calculate_sma(prices, 20)
ema_result = calculate_ema(prices, 20)
rsi_result = calculate_rsi(prices, 14)

# 새로운: 배치 계산
indicators = {
    "SMA": {"period": 20},
    "EMA": {"period": 20},
    "RSI": {"period": 14}
}
result = service.calculate_indicators(prices, indicators)
```

## ⚠️ 주의사항

### 호환성 이슈
1. **반환값 형식**: 기존 리스트 → 새로운 결과 객체
2. **오류 처리**: 예외 발생 → 결과 객체의 success 플래그
3. **매개변수**: 개별 매개변수 → 딕셔너리 설정

### 성능 고려사항
1. **배치 처리**: 가능한 한 여러 지표를 한 번에 계산
2. **캐싱**: 동일한 계산의 반복 방지
3. **메모리**: 대용량 데이터 처리 시 메모리 최적화 활용

### 테스트 업데이트
```python
# 기존 테스트
def test_sma_calculation():
    trigger_builder = TriggerBuilderScreen(None)
    result = trigger_builder._calculate_sma([1, 2, 3, 4, 5], 3)
    assert result == [None, None, 2.0, 3.0, 4.0]

# 새로운 테스트
def test_sma_calculation():
    service = TriggerOrchestrationService()
    result = service.calculate_indicators([1, 2, 3, 4, 5], {"SMA": {"period": 3}})
    assert result.success
    assert result.indicators["SMA"] == [None, None, 2.0, 3.0, 4.0]
```

## 🚀 마이그레이션 체크리스트

- [ ] Import 문 업데이트
- [ ] 지표 계산 코드 변경
- [ ] 트리거 탐지 코드 변경
- [ ] 오류 처리 로직 업데이트
- [ ] UI 연동 코드 어댑터 패턴으로 변경
- [ ] 테스트 코드 업데이트
- [ ] 성능 최적화 옵션 활용
- [ ] 기존 기능 동작 검증

## 🆘 문제 해결

### 자주 발생하는 문제

1. **"None" 값 처리**
   ```python
   # 문제: 새로운 시스템은 np.nan 사용
   # 해결: None → np.nan 변환 또는 isnan() 체크
   ```

2. **반환값 형식 차이**
   ```python
   # 문제: 기존 List[float] → 새로운 결과 객체
   # 해결: result.indicators[indicator_name] 접근
   ```

3. **성능 저하**
   ```python
   # 문제: 개별 호출로 인한 성능 저하
   # 해결: 배치 계산 사용
   ```

마이그레이션 과정에서 문제가 발생하면 `docs/trigger_builder_refactoring/user_guides/troubleshooting.md`를 참조하세요.
```

### **4. 배포 환경 설정 (2시간)**
```python
# deployment/production_setup.py
"""
운영 환경 배포 설정 스크립트
"""

import os
import sys
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

class ProductionDeployment:
    """운영 환경 배포 관리자"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.logger = self._setup_logging()
        
        # 배포 설정
        self.deployment_config = {
            "version": "1.0.0",
            "environment": "production",
            "backup_enabled": True,
            "rollback_enabled": True,
            "monitoring_enabled": True
        }
    
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger("deployment")
        logger.setLevel(logging.INFO)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 파일 핸들러
        log_file = self.base_path / "logs" / "deployment.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # 포매터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def backup_existing_system(self) -> str:
        """기존 시스템 백업"""
        self.logger.info("기존 시스템 백업 시작")
        
        import datetime
        backup_name = f"trigger_builder_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.base_path / "backups" / backup_name
        
        # 백업 대상 파일들
        backup_targets = [
            "upbit_auto_trading/ui/desktop/screens/strategy_management/components/triggers/trigger_builder_screen.py",
            "upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/",
            "config/",
            "requirements.txt"
        ]
        
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for target in backup_targets:
            source = self.base_path / target
            if source.exists():
                if source.is_file():
                    dest = backup_path / target
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                else:
                    dest = backup_path / target
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                
                self.logger.info(f"백업 완료: {target}")
        
        # 백업 메타데이터 저장
        backup_metadata = {
            "backup_name": backup_name,
            "backup_time": datetime.datetime.now().isoformat(),
            "version": self.deployment_config["version"],
            "files_backed_up": backup_targets
        }
        
        metadata_file = backup_path / "backup_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(backup_metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"백업 완료: {backup_path}")
        return str(backup_path)
    
    def update_requirements(self):
        """의존성 업데이트"""
        self.logger.info("의존성 업데이트")
        
        # 새로운 의존성 추가
        new_requirements = [
            "numpy>=1.21.0",
            "pandas>=1.3.0", 
            "numba>=0.58.0",
            "psutil>=5.8.0"
        ]
        
        requirements_file = self.base_path / "requirements.txt"
        
        # 기존 requirements.txt 읽기
        existing_requirements = []
        if requirements_file.exists():
            with open(requirements_file, 'r', encoding='utf-8') as f:
                existing_requirements = [line.strip() for line in f if line.strip()]
        
        # 중복 제거하고 새로운 의존성 추가
        all_requirements = list(set(existing_requirements + new_requirements))
        all_requirements.sort()
        
        # 업데이트된 requirements.txt 저장
        with open(requirements_file, 'w', encoding='utf-8') as f:
            for req in all_requirements:
                f.write(f"{req}\n")
        
        self.logger.info(f"의존성 업데이트 완료: {len(new_requirements)}개 추가")
    
    def update_config_files(self):
        """설정 파일 업데이트"""
        self.logger.info("설정 파일 업데이트")
        
        # 새로운 설정 추가
        new_config = {
            "trigger_builder": {
                "performance_optimization": {
                    "enable_numba": True,
                    "max_workers": 4,
                    "memory_threshold_mb": 500,
                    "enable_caching": True
                },
                "logging": {
                    "level": "INFO",
                    "enable_performance_logging": True,
                    "log_file": "logs/trigger_builder.log"
                }
            }
        }
        
        config_file = self.base_path / "config" / "trigger_builder_config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        import yaml
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)
        
        self.logger.info(f"설정 파일 생성: {config_file}")
    
    def setup_monitoring(self):
        """모니터링 설정"""
        self.logger.info("모니터링 시스템 설정")
        
        # 성능 모니터링 설정
        monitoring_config = {
            "performance_monitoring": {
                "enabled": True,
                "metrics_collection_interval": 60,  # 초
                "alert_thresholds": {
                    "memory_usage_mb": 1000,
                    "execution_time_seconds": 10,
                    "error_rate_percent": 5
                }
            },
            "logging": {
                "performance_logs": "logs/performance.log",
                "error_logs": "logs/errors.log",
                "system_logs": "logs/system.log"
            }
        }
        
        monitoring_file = self.base_path / "config" / "monitoring_config.yaml"
        
        import yaml
        with open(monitoring_file, 'w', encoding='utf-8') as f:
            yaml.dump(monitoring_config, f, default_flow_style=False, allow_unicode=True)
        
        # 로그 디렉토리 생성
        logs_dir = self.base_path / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("모니터링 설정 완료")
    
    def validate_deployment(self) -> bool:
        """배포 유효성 검증"""
        self.logger.info("배포 유효성 검증")
        
        # 필수 파일들 검증
        required_files = [
            "business_logic/triggers/services/trigger_orchestration_service.py",
            "business_logic/triggers/engines/technical_indicator_calculator.py",
            "business_logic/triggers/engines/trigger_point_detector.py",
            "ui/desktop/adapters/triggers/trigger_builder_adapter.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.logger.error(f"필수 파일 누락: {missing_files}")
            return False
        
        # 의존성 검증
        try:
            import numpy
            import pandas
            import numba
            import psutil
            self.logger.info("의존성 검증 완료")
        except ImportError as e:
            self.logger.error(f"의존성 누락: {str(e)}")
            return False
        
        # 기본 기능 테스트
        try:
            sys.path.append(str(self.base_path))
            from business_logic.triggers.services.trigger_orchestration_service import TriggerOrchestrationService
            
            service = TriggerOrchestrationService()
            test_data = [100, 101, 102, 103, 104]
            test_indicators = {"SMA": {"period": 3}}
            
            result = service.calculate_indicators(test_data, test_indicators)
            if not result.success:
                self.logger.error(f"기능 테스트 실패: {result.error_message}")
                return False
            
            self.logger.info("기능 테스트 통과")
            
        except Exception as e:
            self.logger.error(f"기능 테스트 오류: {str(e)}")
            return False
        
        self.logger.info("배포 유효성 검증 완료")
        return True
    
    def create_rollback_script(self, backup_path: str):
        """롤백 스크립트 생성"""
        rollback_script = f"""#!/usr/bin/env python3
'''
트리거 빌더 리팩토링 롤백 스크립트
백업: {backup_path}
'''

import os
import sys
import shutil
from pathlib import Path

def rollback():
    print("🔄 트리거 빌더 롤백 시작")
    
    base_path = Path(__file__).parent
    backup_path = Path("{backup_path}")
    
    if not backup_path.exists():
        print(f"❌ 백업을 찾을 수 없습니다: {{backup_path}}")
        return False
    
    # 백업 복원
    rollback_targets = [
        "upbit_auto_trading/ui/desktop/screens/strategy_management/components/triggers/trigger_builder_screen.py",
        "upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/",
        "config/",
        "requirements.txt"
    ]
    
    for target in rollback_targets:
        backup_source = backup_path / target
        restore_dest = base_path / target
        
        if backup_source.exists():
            if restore_dest.exists():
                if restore_dest.is_file():
                    restore_dest.unlink()
                else:
                    shutil.rmtree(restore_dest)
            
            if backup_source.is_file():
                restore_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_source, restore_dest)
            else:
                shutil.copytree(backup_source, restore_dest)
            
            print(f"✅ 복원 완료: {{target}}")
    
    print("✅ 롤백 완료")
    return True

if __name__ == "__main__":
    success = rollback()
    sys.exit(0 if success else 1)
"""
        
        rollback_file = self.base_path / "rollback_trigger_builder.py"
        with open(rollback_file, 'w', encoding='utf-8') as f:
            f.write(rollback_script)
        
        # 실행 권한 부여 (Unix 계열)
        if os.name != 'nt':
            os.chmod(rollback_file, 0o755)
        
        self.logger.info(f"롤백 스크립트 생성: {rollback_file}")
    
    def deploy(self) -> bool:
        """전체 배포 실행"""
        self.logger.info("🚀 트리거 빌더 리팩토링 배포 시작")
        
        try:
            # 1. 백업
            backup_path = self.backup_existing_system()
            
            # 2. 의존성 업데이트
            self.update_requirements()
            
            # 3. 설정 파일 업데이트  
            self.update_config_files()
            
            # 4. 모니터링 설정
            self.setup_monitoring()
            
            # 5. 유효성 검증
            if not self.validate_deployment():
                self.logger.error("❌ 배포 유효성 검증 실패")
                return False
            
            # 6. 롤백 스크립트 생성
            self.create_rollback_script(backup_path)
            
            self.logger.info("✅ 트리거 빌더 리팩토링 배포 완료")
            self.logger.info(f"📁 백업 위치: {backup_path}")
            self.logger.info(f"🔄 롤백 스크립트: {self.base_path}/rollback_trigger_builder.py")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 배포 실패: {str(e)}")
            return False

def main():
    """메인 배포 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="트리거 빌더 리팩토링 배포")
    parser.add_argument("--base-path", default=".", help="프로젝트 기본 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 배포 없이 검증만 수행")
    
    args = parser.parse_args()
    
    deployment = ProductionDeployment(args.base_path)
    
    if args.dry_run:
        print("🔍 배포 사전 검증 모드")
        success = deployment.validate_deployment()
        print(f"✅ 검증 {'성공' if success else '실패'}")
    else:
        success = deployment.deploy()
        print(f"🚀 배포 {'성공' if success else '실패'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
```

## ✅ **완료 기준**

### **문서화 체크리스트**
- [ ] 시스템 아키텍처 문서 완성
- [ ] 모든 API 레퍼런스 문서 작성
- [ ] 마이그레이션 가이드 완성
- [ ] 사용자 가이드 및 예제 작성
- [ ] 개발자 확장 가이드 작성

### **배포 준비 체크리스트**
- [ ] 운영 환경 설정 스크립트 완성
- [ ] 의존성 및 요구사항 정의
- [ ] 모니터링 시스템 설정
- [ ] 백업 및 롤백 절차 수립
- [ ] 배포 유효성 검증 완료

### **품질 기준**
- [ ] 모든 public API 문서화 100%
- [ ] 코드 예제 동작 검증 완료
- [ ] 배포 스크립트 테스트 완료
- [ ] 롤백 절차 검증 완료

### **검증 명령어**
```powershell
# 문서 생성 확인
Get-ChildItem docs/trigger_builder_refactoring/ -Recurse -Name "*.md"

# 배포 사전 검증
python deployment/production_setup.py --dry-run

# 실제 배포 실행
python deployment/production_setup.py --base-path .
```

## 🔗 **연관 작업**
- **이전**: TASK-20250802-19 (성능 최적화 및 벤치마킹)
- **다음**: TASK-20250802-21 (최종 검증 및 완료)
- **관련**: 모든 이전 TASK (문서화 대상)

## 📊 **예상 소요 시간**
- **총 소요 시간**: 10시간
- **우선순위**: HIGH
- **복잡도**: MEDIUM (문서 작성 위주)
- **리스크**: LOW (문서화 작업)

---
**작성일**: 2025년 8월 2일  
**담당자**: GitHub Copilot  
**문서 타입**: 문서화 및 배포 준비
