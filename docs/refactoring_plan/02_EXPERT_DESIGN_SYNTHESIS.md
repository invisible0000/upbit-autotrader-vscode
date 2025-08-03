# 🎯 전문가 설계 문서 종합 분석

## 📋 분석 개요

본 문서는 `docs/upbit_trading_system_design` 폴더의 전문가 설계 문서들을 종합 분석하여 리팩토링의 목표 아키텍처를 정의합니다.

**분석 범위**: upbit_trading_system_design 폴더 내 6개 문서  
**목표**: 전문가가 제시한 이상적 아키텍처 추출  
**활용**: 리팩토링 방향성 및 우선순위 결정

## 🏗️ 전문가 제시 이상적 아키텍처

### 1. 5-Layer 시스템 아키텍처

#### 최상위 구조
```
+----------------------------------------------------------------+
|                        UI Layer (PyQt6)                        |
| [Trigger Builder] [Strategy Maker] [Dashboard] [Mini-Chart]    |
+--------------------------------+-------------------------------+
|      Application Layer         |     Strategy Engine Layer     |
| (Service 계층)                  |     (Strategy Management)     |
+--------------------------------+-------------------------------+
|                    Domain Layer                                |
|           (Business Logic & Domain Models)                    |
+----------------------------------------------------------------+
|                  Infrastructure Layer                         |
| [Data Handler] [API Wrapper] [Trading Engine]                |
+----------------------------------------------------------------+
```

### 2. 계층별 역할 정의 (전문가 권장)

#### UI Layer (Presentation)
- **책임**: 사용자 입력 수신 및 시각적 표시만 담당
- **금지사항**: 직접적인 계산, 매매 로직, DB 접근 금지
- **핵심 원칙**: "UI는 바보여야 한다" (Passive View 패턴)

```python
# ✅ 올바른 UI 패턴
class TriggerBuilderWidget(QWidget):
    def on_create_trigger_clicked(self):
        # UI는 입력만 수집하고 Service에 위임
        trigger_data = self.collect_user_input()
        result = self.trigger_service.create_trigger(trigger_data)
        self.display_result(result)
```

#### Application Layer (Service)
- **책임**: Use Case 구현, 트랜잭션 관리, 보안
- **핵심 서비스**: StrategyService, TriggerService, TradingService
- **패턴**: Command Pattern, Transaction Script

```python
# ✅ Service Layer 예시
class StrategyService:
    def create_strategy(self, strategy_dto: StrategyDto) -> Result:
        # 1. 입력 검증
        # 2. 비즈니스 규칙 적용
        # 3. Domain 객체 생성
        # 4. Repository 통한 저장
        # 5. 이벤트 발행
```

#### Domain Layer (Business Logic)
- **책임**: 핵심 비즈니스 규칙, 도메인 모델, 비즈니스 로직
- **핵심 모델**: Strategy, Trigger, Position, Trade
- **패턴**: Domain Model, Specification Pattern

```python
# ✅ Domain Model 예시
class Strategy:
    def __init__(self, entry_triggers, exit_triggers):
        self.entry_triggers = entry_triggers
        self.exit_triggers = exit_triggers
        
    def evaluate_entry_signal(self, market_data) -> Signal:
        # 순수한 비즈니스 로직만 포함
        pass
        
    def can_add_trigger(self, trigger) -> bool:
        # 도메인 규칙 검증
        pass
```

#### Infrastructure Layer
- **책임**: 외부 시스템과의 통신, 데이터 영속성
- **구성요소**: Repository, API Client, Database Manager
- **패턴**: Repository Pattern, Adapter Pattern

## 🎯 전문가 권장 핵심 컴포넌트

### 1. Strategy Management Engine (두뇌)

#### 핵심 클래스 구조
```python
class IndicatorCalculator:
    """지표 계산 전문 서비스"""
    def calculate_sma(self, data, period): pass
    def calculate_rsi(self, data, period): pass
    def calculate_macd(self, data, fast, slow, signal): pass

class TriggerEvaluator:
    """트리거 조건 평가 엔진"""
    def evaluate_condition(self, trigger, market_data): pass
    def combine_conditions(self, triggers, logic): pass

class StrategyEvaluator:
    """전략 종합 판단 엔진"""
    def evaluate_entry_signals(self, strategy, data): pass
    def evaluate_exit_signals(self, strategy, position, data): pass
```

### 2. Trading Engine (손과 발)

#### 포지션 생명주기 관리
```python
class PositionManager:
    """포지션 생명주기 전담 관리"""
    def create_position(self, strategy, market, capital): pass
    def monitor_position(self, position_id): pass
    def close_position(self, position_id, reason): pass

class OrderExecutor:
    """실제 주문 실행 전담"""
    def execute_market_order(self, market, side, amount): pass
    def execute_limit_order(self, market, side, amount, price): pass
    def cancel_order(self, order_id): pass
```

### 3. Data Handler (기록 보관소)

#### Repository 패턴 적용
```python
class StrategyRepository:
    """전략 데이터 접근 전담"""
    def save_strategy(self, strategy): pass
    def find_by_id(self, strategy_id): pass
    def find_active_strategies(self): pass

class TriggerRepository:
    """트리거 데이터 접근 전담"""
    def save_trigger(self, trigger): pass
    def find_by_strategy_id(self, strategy_id): pass
```

## 📊 3-Database 아키텍처 (전문가 설계)

### 1. settings.sqlite3 (시스템 메타데이터)
```sql
-- 지표 정의 테이블
CREATE TABLE indicator_definitions (
    indicator_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    params_schema TEXT, -- JSON
    plot_category TEXT, -- "Price Overlay" / "Subplot"
    scale_category TEXT, -- "Price" / "0-100" / "Volume"
    compat_group TEXT,  -- 호환성 그룹
    calculation_func TEXT -- 계산 함수 식별자
);

-- 앱 설정 테이블
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    category TEXT
);
```

### 2. strategies.sqlite3 (사용자 자산)
```sql
-- 트리거 테이블
CREATE TABLE triggers (
    trigger_id TEXT PRIMARY KEY,
    trigger_name TEXT NOT NULL,
    base_variable TEXT, -- JSON
    comparison_operator TEXT,
    target_value TEXT, -- JSON
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 전략 테이블
CREATE TABLE strategies (
    strategy_id TEXT PRIMARY KEY,
    strategy_name TEXT NOT NULL,
    entry_triggers TEXT, -- JSON Array
    entry_logic TEXT, -- "AND" / "OR"
    exit_triggers TEXT, -- JSON Array
    exit_logic TEXT,
    version INTEGER,
    status TEXT -- "draft" / "active" / "archived"
);

-- 포지션 테이블
CREATE TABLE positions (
    position_id TEXT PRIMARY KEY,
    strategy_snapshot TEXT, -- 실행 시점 Strategy 전체 JSON
    market TEXT,
    status TEXT,
    initial_capital REAL,
    created_at TIMESTAMP,
    closed_at TIMESTAMP
);

-- 거래 기록 테이블 (진실의 원천)
CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    position_id TEXT,
    order_type TEXT, -- "buy" / "sell"
    quantity REAL,
    price REAL,
    fee REAL,
    executed_at TIMESTAMP,
    upbit_order_id TEXT
);
```

### 3. market_data.sqlite3 (시장 데이터)
```sql
-- OHLCV 데이터
CREATE TABLE ohlcv_data (
    market TEXT,
    interval TEXT, -- "1m", "5m", "1h", "1d"
    timestamp INTEGER,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume REAL,
    PRIMARY KEY (market, interval, timestamp)
);

-- 성능 최적화 인덱스
CREATE INDEX idx_ohlcv_lookup ON ohlcv_data(market, interval, timestamp);
```

## 🔧 전문가 권장 핵심 패턴

### 1. 통합 지표 관리 시스템

#### IndicatorRegistry 패턴
```python
@dataclass
class IndicatorDefinition:
    name: str  # "RSI", "SMA", "MACD"
    params_schema: List[IndicatorParam]
    plot_category: str  # "Price Overlay" / "Subplot"
    scale_category: str # "Price" / "0-100" / "Volume"
    compat_group: str   # 호환성 그룹
    output_names: List[str] # ['value'] 또는 ['macd', 'signal', 'histogram']
    calculation_func: Callable

class IndicatorRegistry:
    """모든 지표 정의의 중앙 관리소"""
    def load_definitions_from_db(self): pass
    def get_definition(self, indicator_name): pass
    def get_compatible_indicators(self, base_indicator): pass
```

### 2. 트리거-전략 조합 시스템

#### 유연한 조건 조합
```python
class TriggerCombination:
    """트리거들의 논리적 조합 관리"""
    def __init__(self, triggers: List[Trigger], logic: str):
        self.triggers = triggers
        self.logic = logic  # "AND", "OR", "(A AND B) OR C"
        
    def evaluate(self, market_data) -> bool:
        # 복잡한 논리 조합 평가
        pass

class Strategy:
    """전략 = 진입 조합 + 청산 조합"""
    def __init__(self, entry_combination, exit_combination):
        self.entry_combination = entry_combination
        self.exit_combination = exit_combination
```

### 3. 이벤트 기반 아키텍처

#### 도메인 이벤트 시스템
```python
class DomainEvent:
    """도메인 이벤트 기본 클래스"""
    def __init__(self, timestamp=None):
        self.timestamp = timestamp or datetime.utcnow()

class PositionOpened(DomainEvent):
    def __init__(self, position_id, strategy_id, market):
        super().__init__()
        self.position_id = position_id
        self.strategy_id = strategy_id
        self.market = market

class EventBus:
    """이벤트 발행/구독 관리"""
    def publish(self, event: DomainEvent): pass
    def subscribe(self, event_type, handler): pass
```

## 🚀 전문가 권장 개발 우선순위

### Phase 1: 핵심 Domain 구축 (2주)
1. **Domain Models 구현**
   - Strategy, Trigger, Position, Trade 엔티티
   - 비즈니스 규칙 및 검증 로직

2. **Service Layer 구축**
   - StrategyService, TriggerService 구현
   - 기본 CRUD 기능

### Phase 2: Infrastructure 구축 (2주)
1. **Repository Pattern 구현**
   - 각 도메인별 Repository 구현
   - Unit of Work 패턴 적용

2. **Database Migration**
   - 새로운 스키마로 점진적 마이그레이션
   - 기존 데이터 보존 전략

### Phase 3: UI Refactoring (3주)
1. **Passive View 패턴 적용**
   - UI에서 비즈니스 로직 분리
   - Service 계층과의 연동

2. **Event-Driven UI**
   - 도메인 이벤트 기반 UI 갱신
   - 느슨한 결합 구현

## 💡 전문가 강조 핵심 원칙

### 1. 단일 책임 원칙 (SRP)
- **UI**: 표시만 담당
- **Service**: Use Case만 담당  
- **Domain**: 비즈니스 규칙만 담당
- **Repository**: 데이터 접근만 담당

### 2. 의존성 역전 원칙 (DIP)
- 상위 계층이 하위 계층에 의존하지 않음
- 인터페이스를 통한 추상화 의존

### 3. 도메인 주도 설계 (DDD)
- 비즈니스 도메인이 설계의 중심
- 유비쿼터스 언어 사용
- 도메인 전문가와의 지속적 소통

## 📊 전문가 설계 vs 현재 상태 비교

| 영역 | 전문가 설계 | 현재 상태 | 갭 분석 |
|------|-------------|-----------|---------|
| 아키텍처 | 5-Layer 분리 | UI 중심 구조 | 4개 계층 누락 |
| 서비스 계층 | 명확한 Service 클래스 | 부분적 구현 | Service 패턴 미완성 |
| Repository | 모든 도메인별 구현 | 일부만 구현 | Repository 패턴 확장 필요 |
| 도메인 모델 | Rich Domain Model | Anemic Model | 비즈니스 로직 집중화 필요 |
| 이벤트 시스템 | Event-Driven | 직접 호출 | 이벤트 시스템 구축 필요 |

---

**다음 문서**: [전문가 리팩토링 계획 종합](03_EXPERT_REFACTORING_SYNTHESIS.md)
