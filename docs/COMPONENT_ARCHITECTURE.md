# 🏗️ 컴포넌트 아키텍처

## 🎯 아키텍처 개요

**설계 철학**: DDD(Domain-Driven Design) 계층별 분리와 도메인 중심 모듈화로 확장 가능한 구조 구현

### 핵심 원칙
- **도메인 중심**: 비즈니스 로직이 시스템의 핵심
- **단일 책임**: 각 컴포넌트는 하나의 명확한 역할
- **느슨한 결합**: 인터페이스를 통한 상호작용
- **의존성 역전**: 상위 계층이 하위 계층에 의존하지 않음

## 📊 DDD 계층별 구조

### 1. Presentation Layer (PyQt6)
```
upbit_auto_trading/presentation/desktop/
├── main_window.py              # 메인 애플리케이션 윈도우
├── presenters/                 # MVP 패턴 프레젠터
│   ├── strategy_presenter.py   # 전략 관리 프레젠터
│   ├── trigger_presenter.py    # 트리거 빌더 프레젠터
│   └── backtest_presenter.py   # 백테스팅 프레젠터
├── views/                      # Passive View 구현
│   ├── strategy_view.py        # 전략 관리 뷰
│   ├── trigger_view.py         # 트리거 빌더 뷰
│   └── backtest_view.py        # 백테스팅 뷰
└── components/                 # 재사용 가능한 UI 컴포넌트
    ├── charts/                 # 차트 컴포넌트
    ├── tables/                 # 테이블 컴포넌트
    └── dialogs/                # 다이얼로그 컴포넌트
```

### 2. Application Layer (Use Cases)
```
upbit_auto_trading/application/
├── services/                   # Application Services
│   ├── strategy_service.py     # 전략 관리 서비스
│   ├── trigger_service.py      # 트리거 관리 서비스
│   └── backtest_service.py     # 백테스팅 서비스
├── dto/                        # Data Transfer Objects
│   ├── strategy_dto.py         # 전략 DTO
│   ├── trigger_dto.py          # 트리거 DTO
│   └── backtest_dto.py         # 백테스팅 DTO
└── commands/                   # Command Objects
    ├── create_strategy_command.py
    ├── create_trigger_command.py
    └── run_backtest_command.py
```

### 3. Domain Layer (핵심 비즈니스)
```
upbit_auto_trading/domain/
├── entities/                   # 도메인 엔티티
│   ├── strategy.py             # 전략 엔티티
│   ├── trigger.py              # 트리거 엔티티
│   ├── position.py             # 포지션 엔티티
│   └── trade.py                # 거래 엔티티
├── value_objects/              # 값 객체
│   ├── strategy_id.py          # 전략 ID
│   ├── trigger_id.py           # 트리거 ID
│   └── trading_signal.py       # 거래 신호
├── services/                   # 도메인 서비스
│   ├── compatibility_checker.py # 호환성 검증
│   ├── signal_evaluator.py     # 신호 평가
│   └── position_manager.py     # 포지션 관리
├── repositories/               # Repository 인터페이스
│   ├── strategy_repository.py  # 전략 저장소 인터페이스
│   ├── trigger_repository.py   # 트리거 저장소 인터페이스
│   └── market_data_repository.py # 시장 데이터 저장소 인터페이스
└── events/                     # 도메인 이벤트
    ├── strategy_created.py     # 전략 생성 이벤트
    ├── position_opened.py      # 포지션 개설 이벤트
    └── trade_executed.py       # 거래 실행 이벤트
```

### 4. Infrastructure Layer
│       └── combination_manager.py # 전략 조합 관리
└── data_engine/                # 데이터 엔진
    ├── market_data/            # 시장 데이터
```
upbit_auto_trading/infrastructure/
├── repositories/               # Repository 구현체
│   ├── sqlite_strategy_repository.py    # SQLite 전략 저장소
│   ├── sqlite_trigger_repository.py     # SQLite 트리거 저장소
│   └── sqlite_market_data_repository.py # SQLite 시장 데이터 저장소
├── external_apis/              # 외부 API 클라이언트
│   ├── upbit_api_client.py     # 업비트 API 클라이언트
│   └── market_data_provider.py # 시장 데이터 제공자
├── database/                   # 데이터베이스 접근
│   ├── database_manager.py     # 데이터베이스 관리자
│   └── migration_manager.py    # 마이그레이션 관리자
└── messaging/                  # 이벤트 메시징
    └── domain_event_bus.py     # 도메인 이벤트 버스
```

## 🔧 핵심 컴포넌트 설계

### 트리거 시스템 컴포넌트
```python
class TriggerCondition:
    """개별 조건 (예: RSI > 30)"""
    def __init__(self, variable, operator, value, parameters):
        self.variable = variable        # 매매 변수
        self.operator = operator        # 비교 연산자
        self.value = value             # 대상값
        self.parameters = parameters    # 파라미터
        
    def evaluate(self, market_data) -> bool:
        """조건 평가"""
        pass

class TriggerRule:
    """규칙 (조건들의 논리 조합)"""
    def __init__(self, conditions, logic_operator='AND'):
        self.conditions = conditions
        self.logic_operator = logic_operator
        
    def evaluate(self, market_data) -> bool:
        """규칙 평가"""
        pass

class TriggerBuilder:
    """트리거 빌더 메인 컴포넌트"""
    def __init__(self):
        self.rules = []
        self.validator = CompatibilityValidator()
        
    def add_rule(self, rule: TriggerRule):
        """규칙 추가 (호환성 검증 포함)"""
        if self.validator.validate_rule(rule):
            self.rules.append(rule)
```

### 전략 시스템 컴포넌트
```python
class BaseStrategy(ABC):
    """전략 기본 클래스"""
    @abstractmethod
    def generate_signal(self, data) -> TradingSignal:
        pass
        
    @abstractmethod
    def get_parameters(self) -> Dict:
        pass

class EntryStrategy(BaseStrategy):
    """진입 전략 기본 클래스"""
    def generate_signal(self, data) -> str:
        # 반환값: 'BUY', 'SELL', 'HOLD'
        pass

class ManagementStrategy(BaseStrategy):
    """관리 전략 기본 클래스"""  
    def generate_signal(self, position, data) -> str:
        # 반환값: 'ADD_BUY', 'ADD_SELL', 'CLOSE_POSITION', 'UPDATE_STOP', 'HOLD'
        pass

class StrategyCombiner:
    """전략 조합 관리자"""
    def __init__(self):
        self.entry_strategy = None
        self.management_strategies = []
        
    def add_management_strategy(self, strategy, priority=1):
        """관리 전략 추가"""
        pass
        
    def resolve_conflicts(self, signals) -> TradingSignal:
        """신호 충돌 해결"""
        pass
```

### UI 컴포넌트 설계
```python
class BaseWidget(QWidget):
    """모든 UI 위젯의 기본 클래스"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
        self.setup_events()
        
    @abstractmethod
    def setup_ui(self):
        pass
        
    def setup_style(self):
        """QSS 스타일 적용"""
        pass
        
    def setup_events(self):
        """이벤트 연결"""
        pass

class ConditionCard(BaseWidget):
    """조건 카드 위젯"""
    def __init__(self, condition: TriggerCondition):
        self.condition = condition
        super().__init__()
        
    def setup_ui(self):
        """조건 카드 UI 구성"""
        pass

class RuleBuilder(BaseWidget):
    """규칙 빌더 위젯"""
    def __init__(self):
        self.conditions = []
        super().__init__()
        
    def add_condition(self, condition):
        """조건 추가"""
        pass
        
    def validate_compatibility(self):
        """호환성 검증"""
        pass
```

## 🔄 데이터 흐름

### 1. 트리거 생성 흐름
```
사용자 입력 → UI 컴포넌트 → 조건 생성 → 호환성 검증 → 규칙 조합 → DB 저장
```

### 2. 매매 신호 생성 흐름
```
시장 데이터 → 지표 계산 → 조건 평가 → 규칙 평가 → 전략 실행 → 매매 신호
```

### 3. 전략 실행 흐름
```
진입 신호 → 포지션 생성 → 관리 전략 활성화 → 리스크 관리 → 포지션 종료
```

## 🔗 의존성 관리

### 의존성 주입 컨테이너
```python
class DIContainer:
    """의존성 주입 컨테이너"""
    def __init__(self):
        self.services = {}
        
    def register(self, interface, implementation):
        """서비스 등록"""
        self.services[interface] = implementation
        
    def resolve(self, interface):
        """서비스 해결"""
        return self.services.get(interface)

# 사용 예시
container = DIContainer()
container.register(IMarketDataService, UpbitMarketDataService)
container.register(IDatabaseService, SQLiteDatabaseService)
```

### 인터페이스 정의
```python
class IMarketDataService(ABC):
    @abstractmethod
    def get_candle_data(self, symbol, timeframe) -> pd.DataFrame:
        pass

class IDatabaseService(ABC):
    @abstractmethod
    def save_strategy(self, strategy) -> bool:
        pass
        
    @abstractmethod
    def load_strategy(self, strategy_id) -> Strategy:
        pass
```

## 🧪 테스트 가능한 설계

### 모킹 가능한 구조
```python
class TradingEngine:
    def __init__(self, market_data_service: IMarketDataService):
        self.market_data_service = market_data_service
        
    def execute_strategy(self, strategy):
        # 실제 구현에서 의존성을 주입받아 사용
        data = self.market_data_service.get_candle_data("BTC", "1h")
        return strategy.generate_signal(data)

# 테스트에서는 모킹된 서비스 주입
def test_trading_engine():
    mock_service = Mock(spec=IMarketDataService)
    mock_service.get_candle_data.return_value = create_test_data()
    
    engine = TradingEngine(mock_service)
    result = engine.execute_strategy(test_strategy)
    
    assert result == expected_signal
```

## 📚 관련 문서

- [UI 디자인 시스템](UI_DESIGN_SYSTEM.md): UI 컴포넌트 설계 가이드
- [DB 스키마](DB_SCHEMA.md): 데이터 모델 정의
- [개발 체크리스트](DEV_CHECKLIST.md): 아키텍처 준수 검증
- [트리거 빌더](TRIGGER_BUILDER_GUIDE.md): 트리거 시스템 상세

---
**💡 핵심**: "각 컴포넌트가 독립적으로 테스트 가능하고 교체 가능한 구조가 좋은 아키텍처다!"
