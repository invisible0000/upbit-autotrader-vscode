# 🏗️ 컴포넌트 아키텍처

## 🎯 아키텍처 개요

**설계 철학**: 계층별 분리와 컴포넌트 기반 모듈화로 확장 가능한 구조 구현

### 핵심 원칙
- **단일 책임**: 각 컴포넌트는 하나의 명확한 역할
- **느슨한 결합**: 인터페이스를 통한 상호작용
- **높은 응집도**: 관련 기능을 하나의 모듈로 그룹화
- **의존성 주입**: 테스트 가능한 설계

## 📊 계층별 구조

### 1. UI Layer (PyQt6)
```
upbit_auto_trading/ui/desktop/
├── main_window.py              # 메인 애플리케이션 윈도우
├── common/
│   ├── components.py           # 공통 스타일 컴포넌트
│   ├── style_manager.py        # 테마 및 스타일 관리
│   └── base_widget.py          # 기본 위젯 클래스
├── screens/                    # 실제 UI 화면들
│   ├── market_analysis/        # 📊 시장 분석 탭
│   ├── strategy_management/    # ⚙️ 전략 관리 탭
│   │   ├── trigger_builder/    # 트리거 빌더
│   │   ├── strategy_maker/     # 전략 메이커
│   │   └── backtesting/        # 백테스팅
│   └── settings/               # 🔧 설정 탭
└── components/                 # 재사용 가능한 UI 컴포넌트
    ├── charts/                 # 차트 컴포넌트
    ├── tables/                 # 테이블 컴포넌트
    └── dialogs/                # 다이얼로그 컴포넌트
```

### 2. Business Logic Layer
```
upbit_auto_trading/core/
├── trading_engine/             # 매매 엔진
│   ├── order_manager.py        # 주문 관리
│   ├── position_manager.py     # 포지션 관리
│   └── risk_manager.py         # 리스크 관리
├── strategy_engine/            # 전략 엔진
│   ├── trigger_system/         # 트리거 시스템
│   │   ├── conditions/         # 조건 정의
│   │   ├── operators/          # 연산자
│   │   └── validators/         # 호환성 검증
│   └── strategy_system/        # 전략 시스템
│       ├── entry_strategies/   # 진입 전략들
│       ├── management_strategies/ # 관리 전략들
│       └── combination_manager.py # 전략 조합 관리
└── data_engine/                # 데이터 엔진
    ├── market_data/            # 시장 데이터
    ├── indicators/             # 기술적 지표
    └── historical_data/        # 과거 데이터
```

### 3. Data Access Layer
```
upbit_auto_trading/storage/
├── database/
│   ├── settings_db.py          # 설정 DB 접근
│   ├── strategies_db.py        # 전략 DB 접근
│   └── market_data_db.py       # 시장 데이터 DB 접근
├── repositories/               # 리포지토리 패턴
│   ├── trading_variable_repo.py
│   ├── strategy_repo.py
│   └── market_data_repo.py
└── models/                     # 데이터 모델
    ├── trading_models.py
    ├── strategy_models.py
    └── market_models.py
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
