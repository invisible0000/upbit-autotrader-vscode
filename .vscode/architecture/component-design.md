# 🏗️ 컴포넌트 아키텍처 설계

> **참조**: `.vscode/project-specs.md`의 아키텍처 원칙을 구현하는 상세 설계

## 📊 계층별 컴포넌트 구조

### 1. UI Layer (PyQt6)
```python
# 메인 윈도우 구조
upbit_auto_trading/ui/desktop/
├── main_window.py              # 메인 애플리케이션 윈도우
├── common/
│   ├── components.py           # 공통 스타일 컴포넌트
│   ├── style_manager.py        # 테마 및 스타일 관리
│   └── base_widget.py          # 기본 위젯 클래스
├── dashboard/
│   ├── portfolio_summary.py    # 포트폴리오 요약 위젯
│   ├── active_trades.py        # 활성 거래 목록
│   └── market_overview.py      # 시장 개요 위젯
├── strategy/
│   ├── strategy_manager.py     # 3탭 전략 관리 메인
│   ├── entry_strategy_tab.py   # 진입 전략 탭
│   ├── management_strategy_tab.py # 관리 전략 탭
│   └── combination_tab.py      # 전략 조합 탭
├── charts/
│   ├── candlestick_chart.py    # 캔들스틱 차트
│   ├── indicator_overlay.py    # 기술적 지표 오버레이
│   └── trade_markers.py        # 거래 시점 마커
└── settings/
    ├── api_settings.py         # API 키 관리
    ├── notification_settings.py # 알림 설정
    └── data_settings.py        # 데이터 관리 설정
```

### 2. Business Logic Layer
```python
upbit_auto_trading/business_logic/
├── strategy_engine/
│   ├── base_strategy.py        # 전략 기본 클래스
│   ├── entry_strategies/       # 6개 진입 전략
│   │   ├── moving_average_crossover.py
│   │   ├── rsi_strategy.py
│   │   ├── bollinger_bands.py
│   │   ├── volatility_breakout.py
│   │   ├── macd_strategy.py
│   │   └── stochastic_strategy.py
│   ├── management_strategies/  # 6개 관리 전략
│   │   ├── pyramid_buying.py   # 물타기
│   │   ├── scale_in_buying.py  # 불타기
│   │   ├── trailing_stop.py
│   │   ├── fixed_take_profit_stop_loss.py
│   │   ├── partial_closing.py
│   │   └── time_based_closing.py
│   └── combination_engine.py   # 전략 조합 엔진
├── backtesting/
│   ├── stateful_backtester.py  # 상태 기반 백테스터
│   ├── performance_calculator.py # 성과 지표 계산
│   └── backtest_visualizer.py  # 백테스트 결과 시각화
├── trading/
│   ├── order_manager.py        # 주문 관리
│   ├── position_manager.py     # 포지션 관리
│   └── risk_manager.py         # 리스크 관리
└── portfolio/
    ├── portfolio_manager.py    # 포트폴리오 관리
    └── rebalancer.py          # 리밸런싱 엔진
```

### 3. Data Layer
```python
upbit_auto_trading/data_layer/
├── api/
│   ├── upbit_client.py         # 업비트 API 클라이언트
│   ├── websocket_client.py     # 실시간 데이터 수신
│   └── rate_limiter.py         # API 호출 제한 관리
├── storage/
│   ├── database_manager.py     # 데이터베이스 관리
│   ├── strategy_repository.py  # 전략 저장소
│   ├── backtest_repository.py  # 백테스트 결과 저장소
│   └── market_data_repository.py # 시장 데이터 저장소
└── processing/
    ├── indicator_calculator.py # 기술적 지표 계산
    ├── data_normalizer.py     # 데이터 정규화
    └── data_validator.py      # 데이터 검증
```

## 🔄 상태 관리 아키텍처

### 백테스팅 상태 머신
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

class BacktestState(Enum):
    WAITING_ENTRY = "waiting_entry"
    POSITION_MANAGEMENT = "position_management"

@dataclass
class PositionState:
    """포지션 상태 관리"""
    entry_price: float
    current_price: float
    quantity: float
    side: str  # 'long' or 'short'
    entry_time: datetime
    management_history: List[Dict]  # 관리 전략 실행 이력
    
class BacktestStateMachine:
    """상태 기반 백테스팅 상태 머신"""
    
    def __init__(self):
        self.state = BacktestState.WAITING_ENTRY
        self.position: Optional[PositionState] = None
        self.entry_strategy = None
        self.management_strategies = []
        
    def transition_to_position_management(self, position: PositionState):
        """진입 대기 → 포지션 관리 전환"""
        self.state = BacktestState.POSITION_MANAGEMENT
        self.position = position
        
    def transition_to_waiting_entry(self):
        """포지션 관리 → 진입 대기 전환"""
        self.state = BacktestState.WAITING_ENTRY
        self.position = None
```

## 🔧 의존성 주입 패턴

### 인터페이스 기반 설계
```python
from abc import ABC, abstractmethod
from typing import Protocol

class DataProvider(Protocol):
    """데이터 제공자 인터페이스"""
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        ...

class StrategyEngine(Protocol):
    """전략 엔진 인터페이스"""
    def generate_signal(self, data: pd.DataFrame) -> str:
        ...

class BacktestEngine:
    """의존성 주입을 통한 백테스트 엔진"""
    
    def __init__(
        self,
        data_provider: DataProvider,
        entry_strategy: StrategyEngine,
        management_strategies: List[StrategyEngine]
    ):
        self.data_provider = data_provider
        self.entry_strategy = entry_strategy
        self.management_strategies = management_strategies
```

## 📡 이벤트 기반 아키텍처

### 시그널/슬롯 패턴 확장
```python
from PyQt6.QtCore import QObject, pyqtSignal

class TradingEventBus(QObject):
    """거래 이벤트 버스"""
    
    # 전략 관련 시그널
    entry_signal_generated = pyqtSignal(str, str)  # strategy_id, signal
    management_signal_generated = pyqtSignal(str, str)  # strategy_id, signal
    position_opened = pyqtSignal(dict)  # position_data
    position_closed = pyqtSignal(dict)  # position_data
    
    # 백테스팅 관련 시그널
    backtest_started = pyqtSignal(str)  # backtest_id
    backtest_progress = pyqtSignal(str, int)  # backtest_id, progress
    backtest_completed = pyqtSignal(str, dict)  # backtest_id, results
    
    # 시장 데이터 관련 시그널
    market_data_updated = pyqtSignal(str, dict)  # symbol, data
    price_alert_triggered = pyqtSignal(str, float)  # symbol, price

class StrategyComponent(QObject):
    """전략 컴포넌트 기본 클래스"""
    
    def __init__(self, event_bus: TradingEventBus):
        super().__init__()
        self.event_bus = event_bus
        self._connect_signals()
        
    def _connect_signals(self):
        """이벤트 버스와 연결"""
        self.event_bus.market_data_updated.connect(self.on_market_data_updated)
        
    def on_market_data_updated(self, symbol: str, data: dict):
        """시장 데이터 업데이트 처리"""
        pass
```

## 🎯 컴포넌트 라이프사이클

### UI 컴포넌트 생명주기
```python
class BaseWidget(QWidget):
    """모든 UI 컴포넌트의 기본 클래스"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_initialized = False
        
    def initialize(self):
        """컴포넌트 초기화"""
        if self.is_initialized:
            return
            
        self.setup_ui()
        self.connect_signals()
        self.load_initial_data()
        self.is_initialized = True
        
    def setup_ui(self):
        """UI 구성 - 서브클래스에서 구현"""
        raise NotImplementedError
        
    def connect_signals(self):
        """시그널 연결 - 서브클래스에서 구현"""
        pass
        
    def load_initial_data(self):
        """초기 데이터 로드 - 서브클래스에서 구현"""
        pass
        
    def cleanup(self):
        """리소스 정리"""
        # 타이머 정리
        for timer in self.findChildren(QTimer):
            timer.stop()
            timer.deleteLater()
            
        # 시그널 연결 해제
        self.disconnect()
```

## 🔒 에러 경계 패턴

### 컴포넌트별 에러 처리
```python
import logging
from functools import wraps

def error_boundary(component_name: str):
    """컴포넌트 에러 경계 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"{component_name} 에러: {e}", exc_info=True)
                # 사용자에게 친화적인 에러 메시지 표시
                if hasattr(args[0], 'show_error_message'):
                    args[0].show_error_message(f"{component_name}에서 오류가 발생했습니다.")
                return None
        return wrapper
    return decorator

class StrategyManagerWidget(BaseWidget):
    """전략 관리 위젯"""
    
    @error_boundary("전략 관리")
    def create_new_strategy(self):
        """새 전략 생성"""
        # 전략 생성 로직
        pass
        
    @error_boundary("전략 관리")
    def save_strategy(self, strategy_data):
        """전략 저장"""
        # 전략 저장 로직
        pass
```

## 🔄 플러그인 아키텍처

### 전략 플러그인 시스템
```python
class StrategyPlugin(ABC):
    """전략 플러그인 인터페이스"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """전략 이름"""
        pass
        
    @property
    @abstractmethod
    def strategy_type(self) -> str:
        """전략 타입: 'entry' or 'management'"""
        pass
        
    @abstractmethod
    def get_parameter_schema(self) -> Dict:
        """파라미터 스키마 반환"""
        pass
        
    @abstractmethod
    def create_instance(self, parameters: Dict):
        """전략 인스턴스 생성"""
        pass

class StrategyRegistry:
    """전략 등록 시스템"""
    
    def __init__(self):
        self._entry_strategies = {}
        self._management_strategies = {}
        
    def register_entry_strategy(self, plugin: StrategyPlugin):
        """진입 전략 등록"""
        if plugin.strategy_type != 'entry':
            raise ValueError("진입 전략만 등록 가능합니다")
        self._entry_strategies[plugin.name] = plugin
        
    def register_management_strategy(self, plugin: StrategyPlugin):
        """관리 전략 등록"""
        if plugin.strategy_type != 'management':
            raise ValueError("관리 전략만 등록 가능합니다")
        self._management_strategies[plugin.name] = plugin
        
    def get_entry_strategies(self) -> Dict[str, StrategyPlugin]:
        """등록된 진입 전략 목록 반환"""
        return self._entry_strategies.copy()
        
    def get_management_strategies(self) -> Dict[str, StrategyPlugin]:
        """등록된 관리 전략 목록 반환"""
        return self._management_strategies.copy()
```

## 📊 성능 최적화 패턴

### 지연 로딩 및 캐싱
```python
from functools import lru_cache
import weakref

class LazyLoadingManager:
    """지연 로딩 관리자"""
    
    def __init__(self):
        self._loaded_components = weakref.WeakValueDictionary()
        
    def get_component(self, component_id: str, factory_func):
        """컴포넌트 지연 로딩"""
        if component_id in self._loaded_components:
            return self._loaded_components[component_id]
            
        component = factory_func()
        self._loaded_components[component_id] = component
        return component

class CachedDataProvider:
    """캐시된 데이터 제공자"""
    
    @lru_cache(maxsize=100)
    def get_indicator_data(self, symbol: str, indicator: str, period: int):
        """기술적 지표 데이터 캐시"""
        # 계산 비용이 높은 지표 계산
        pass
        
    def invalidate_cache(self, symbol: str = None):
        """캐시 무효화"""
        if symbol:
            # 특정 심볼 관련 캐시만 무효화
            pass
        else:
            self.get_indicator_data.cache_clear()
```

## 🧪 테스트 가능한 아키텍처

### 테스트 친화적 설계
```python
class TestableBacktester:
    """테스트 가능한 백테스터"""
    
    def __init__(
        self,
        data_provider: DataProvider,
        time_provider: Optional[TimeProvider] = None  # 시간 의존성 주입
    ):
        self.data_provider = data_provider
        self.time_provider = time_provider or RealTimeProvider()
        
    def get_current_time(self):
        """현재 시간 (테스트시 고정 시간 사용 가능)"""
        return self.time_provider.now()

class MockDataProvider:
    """테스트용 모의 데이터 제공자"""
    
    def __init__(self, test_data: pd.DataFrame):
        self.test_data = test_data
        
    def get_market_data(self, symbol: str, timeframe: str) -> pd.DataFrame:
        return self.test_data.copy()
```

이 아키텍처 설계는 확장 가능하고 테스트 가능하며 유지보수가 용이한 시스템을 구축하기 위한 기반을 제공합니다.
