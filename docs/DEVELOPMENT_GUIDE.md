# 전략 개발 및 유지보수 가이드

## 📋 개요

이 문서는 **업비트 자동매매 시스템**의 전략 개발, 유지보수, 그리고 협업을 위한 종합적인 가이드라인을 제공합니다. 개발자가 일관성 있고 확장 가능한 전략을 구현할 수 있도록 돕는 것이 목표입니다.

---

## 🏗️ 개발 환경 설정

### 💻 **필수 개발 도구**

#### **1. Python 환경**
```bash
# Python 3.11+ 권장
python --version  # 3.11.0 이상

# 가상환경 생성
python -m venv upbit_trading_env
source upbit_trading_env/bin/activate  # Linux/Mac
# 또는
upbit_trading_env\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

#### **2. 개발 도구 설정**
```bash
# 코드 품질 도구
pip install black isort mypy flake8 pytest

# IDE 설정 (VS Code 권장)
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension ms-python.mypy-type-checker
```

#### **3. 프로젝트 구조**
```
upbit_auto_trading/
├── strategies/              # 전략 구현
│   ├── base/               # 기본 클래스들
│   ├── entry/              # 진입 전략들
│   ├── management/         # 관리 전략들
│   └── combinations/       # 조합 전략들
├── indicators/             # 기술적 지표
├── backtesting/           # 백테스팅 엔진
├── data/                  # 데이터 관리
├── gui/                   # 사용자 인터페이스
├── tests/                 # 테스트 코드
└── docs/                  # 문서
```

---

## 🗄️ 데이터베이스 개발 원칙

### 📊 **DB 파일 관리 표준**

#### **1. 확장자 및 위치 규칙**
```bash
# ✅ 올바른 DB 파일 구조
data/
├── app_settings.sqlite3      # 프로그램 설정 DB
└── market_data.sqlite3       # 백테스팅용 시장 데이터 DB

# ❌ 잘못된 구조 (금지)
- 루트 폴더의 .db 파일들
- 확장자 없는 DB 파일들
- 서로 다른 폴더의 DB 파일들
```

#### **2. DB 파일 목적별 분리**
```python
# 프로그램 설정 DB (app_settings.sqlite3)
TABLES = [
    "trading_conditions",    # 매매 조건
    "component_strategy",    # 전략 정보
    "strategy_components",   # 전략 구성요소
    "strategy_execution",    # 전략 실행 기록
    "system_settings",       # 시스템 설정
    "user_preferences"       # 사용자 설정
]

# 시장 데이터 DB (market_data.sqlite3)
TABLES = [
    "candle_data",          # 캔들 데이터
    "ticker_data",          # 가격 정보
    "orderbook_data",       # 호가 데이터
    "trade_history"         # 거래 이력
]
```

#### **3. DB 연결 표준화**
```python
# ✅ 표준 DB 연결 방식
class DatabaseManager:
    def __init__(self):
        self.app_db = "data/app_settings.sqlite3"
        self.market_db = "data/market_data.sqlite3"
    
    def get_app_connection(self):
        return sqlite3.connect(self.app_db)
    
    def get_market_connection(self):
        return sqlite3.connect(self.market_db)

# ✅ 클래스별 기본 경로 설정
class ConditionStorage:
    def __init__(self, db_path: str = "data/app_settings.sqlite3"):
        self.db_path = db_path

class MarketDataStorage:
    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
```

#### **4. 마이그레이션 가이드라인**
```python
# DB 구조 변경 시 마이그레이션 스크립트 작성
# scripts/migrate_v1_to_v2.py 형태로 버전별 관리

def migrate_database():
    """
    v1.0 → v2.0 마이그레이션
    - .db → .sqlite3 확장자 변경
    - 분산된 DB들을 2개로 통합
    """
    # 1. 백업 생성
    # 2. 스키마 업데이트  
    # 3. 데이터 마이그레이션
    # 4. 검증
    pass
```

---

## 📝 코딩 스타일 가이드

### 🎨 **Python 스타일 규칙**

#### **1. 명명 규칙 (Naming Conventions)**
```python
# 클래스명: PascalCase
class RSIReversalStrategy:
    pass

class MovingAverageCrossover:
    pass

# 함수/변수명: snake_case
def calculate_rsi(prices, period=14):
    pass

strategy_name = "rsi_reversal"
signal_strength = 0.75

# 상수: UPPER_SNAKE_CASE
DEFAULT_RSI_PERIOD = 14
MAX_POSITION_SIZE = 0.1

# 전략 타입 식별자: snake_case
STRATEGY_TYPES = {
    "rsi_reversal": RSIReversalStrategy,
    "ma_crossover": MovingAverageCrossover
}
```

#### **2. 문서화 스타일**
```python
def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, List[float]]:
    """
    볼린저 밴드를 계산합니다.
    
    Args:
        prices: 가격 데이터 리스트
        period: 이동평균 계산 기간 (기본값: 20)
        std_dev: 표준편차 배수 (기본값: 2.0)
    
    Returns:
        Dict containing:
            - 'upper': 상단 밴드
            - 'middle': 중간 밴드 (이동평균)
            - 'lower': 하단 밴드
    
    Example:
        >>> prices = [100, 101, 99, 102, 98]
        >>> bands = calculate_bollinger_bands(prices, period=3)
        >>> print(bands['middle'])
        [100.0, 100.67, 100.67]
    
    Note:
        최소 period 개수만큼의 데이터가 필요합니다.
    """
    pass
```

#### **3. 타입 힌팅**
```python
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Signal:
    """트레이딩 신호를 나타내는 데이터 클래스"""
    action: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0.0 ~ 1.0
    timestamp: datetime
    strategy_id: str
    metadata: Optional[Dict[str, Union[str, float, int]]] = None

class StrategyBase:
    """모든 전략의 기본 클래스"""
    
    def __init__(self, config: Dict[str, Union[str, int, float]]) -> None:
        self.config = config
        self.is_initialized = False
    
    def generate_signal(self, market_data: Dict[str, List[float]]) -> Optional[Signal]:
        """시장 데이터로부터 트레이딩 신호를 생성합니다."""
        pass
```

---

## 🧪 테스트 주도 개발 (TDD)

### ✅ **테스트 구조**

#### **1. 단위 테스트 (Unit Tests)**
```python
# tests/strategies/test_rsi_reversal.py
import pytest
from unittest.mock import Mock, patch
from upbit_auto_trading.strategies.entry.rsi_reversal import RSIReversalStrategy

class TestRSIReversalStrategy:
    """RSI 반전 전략 단위 테스트"""
    
    @pytest.fixture
    def strategy_config(self):
        return {
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70,
            "min_confidence": 0.6
        }
    
    @pytest.fixture
    def strategy(self, strategy_config):
        return RSIReversalStrategy(strategy_config)
    
    def test_initialization(self, strategy, strategy_config):
        """전략 초기화 테스트"""
        assert strategy.config == strategy_config
        assert strategy.rsi_period == 14
        assert strategy.oversold_threshold == 30
    
    def test_oversold_buy_signal(self, strategy):
        """과매도 구간에서 매수 신호 테스트"""
        # Given: RSI가 30 이하인 상황
        market_data = {
            "close": [100, 95, 90, 85, 88],  # 하락 후 반등
            "rsi": [50, 40, 28, 25, 32]      # 과매도 후 회복
        }
        
        # When: 신호 생성
        signal = strategy.generate_signal(market_data)
        
        # Then: 매수 신호 확인
        assert signal is not None
        assert signal.action == "BUY"
        assert signal.confidence >= 0.6
        assert signal.strategy_id == "rsi_reversal"
    
    def test_no_signal_in_normal_range(self, strategy):
        """정상 범위에서는 신호 없음 테스트"""
        # Given: RSI가 정상 범위인 상황
        market_data = {
            "close": [100, 101, 102, 101, 100],
            "rsi": [50, 52, 55, 53, 50]
        }
        
        # When: 신호 생성
        signal = strategy.generate_signal(market_data)
        
        # Then: 신호 없음 확인
        assert signal is None
```

#### **2. 통합 테스트 (Integration Tests)**
```python
# tests/integration/test_strategy_combination.py
import pytest
from upbit_auto_trading.strategies.combinations.trend_following import TrendFollowingCombination
from upbit_auto_trading.data.market_data_provider import MarketDataProvider

class TestTrendFollowingCombination:
    """트렌드 추종 조합 통합 테스트"""
    
    @pytest.fixture
    def market_data_provider(self):
        return MarketDataProvider(api_key="test_key")
    
    @pytest.fixture
    def combination(self):
        config = {
            "strategies": [
                {"type": "ma_crossover", "weight": 0.6},
                {"type": "macd_trend", "weight": 0.4}
            ],
            "combination_rule": "weighted_average"
        }
        return TrendFollowingCombination(config)
    
    @pytest.mark.integration
    def test_real_data_signal_generation(self, combination, market_data_provider):
        """실제 데이터로 신호 생성 테스트"""
        # Given: 실제 시장 데이터
        market_data = market_data_provider.get_candles("KRW-BTC", "1h", 100)
        
        # When: 조합 신호 생성
        signal = combination.generate_signal(market_data)
        
        # Then: 신호 검증
        if signal:
            assert signal.action in ["BUY", "SELL", "HOLD"]
            assert 0.0 <= signal.confidence <= 1.0
            assert signal.timestamp is not None
```

#### **3. 백테스트 테스트**
```python
# tests/backtesting/test_strategy_backtest.py
import pytest
from datetime import datetime, timedelta
from upbit_auto_trading.backtesting.backtest_engine import BacktestEngine

class TestStrategyBacktest:
    """전략 백테스트 테스트"""
    
    @pytest.fixture
    def backtest_config(self):
        return {
            "initial_capital": 1000000,  # 100만원
            "start_date": datetime(2024, 1, 1),
            "end_date": datetime(2024, 3, 31),
            "commission_rate": 0.0005,
            "slippage_rate": 0.0001
        }
    
    @pytest.fixture
    def backtest_engine(self, backtest_config):
        return BacktestEngine(backtest_config)
    
    def test_backtest_performance_metrics(self, backtest_engine):
        """백테스트 성능 지표 계산 테스트"""
        # Given: 전략과 데이터
        strategy_config = {"type": "rsi_reversal", "rsi_period": 14}
        
        # When: 백테스트 실행
        results = backtest_engine.run_backtest(strategy_config)
        
        # Then: 성능 지표 검증
        assert "total_return" in results
        assert "sharpe_ratio" in results
        assert "max_drawdown" in results
        assert "win_rate" in results
        
        # 합리적인 범위 검증
        assert -1.0 <= results["total_return"] <= 10.0  # -100% ~ +1000%
        assert results["max_drawdown"] <= 0  # 항상 음수 또는 0
        assert 0.0 <= results["win_rate"] <= 1.0  # 0% ~ 100%
```

---

## 🔄 버전 관리 및 배포

### 📦 **Git 워크플로우**

#### **1. 브랜치 전략**
```bash
# 메인 브랜치들
main        # 프로덕션 배포용
develop     # 개발 통합용

# 기능 브랜치들
feature/rsi-strategy-enhancement    # 새 기능 개발
bugfix/signal-timing-issue         # 버그 수정
hotfix/critical-stop-loss-fix      # 긴급 수정
```

#### **2. 커밋 메시지 규칙**
```bash
# 기본 형식
<type>(<scope>): <subject>

<body>

<footer>

# 예시들
feat(strategies): add MACD crossover strategy
- Implement MACD line and signal line crossover detection
- Add configurable parameters for fast/slow periods
- Include signal strength calculation based on histogram

fix(backtesting): correct commission calculation
- Fix double commission charging bug
- Update test cases to verify correct calculation

docs(api): update strategy combination examples
- Add weighted combination examples
- Include performance comparison charts

test(rsi): add edge case tests for RSI calculation
- Test with insufficient data
- Test with all identical prices
- Test boundary conditions (0, 100)
```

#### **3. 코드 리뷰 체크리스트**
```markdown
## 코드 리뷰 체크리스트

### 📋 기능성
- [ ] 요구사항을 올바르게 구현했는가?
- [ ] 엣지 케이스를 처리했는가?
- [ ] 에러 핸들링이 적절한가?

### 🎨 코드 품질
- [ ] 코드가 읽기 쉽고 이해하기 쉬운가?
- [ ] 네이밍이 명확하고 일관성이 있는가?
- [ ] 중복 코드가 있는가?
- [ ] 함수/클래스 크기가 적절한가?

### 🧪 테스트
- [ ] 단위 테스트가 작성되었는가?
- [ ] 테스트 커버리지가 충분한가?
- [ ] 모든 테스트가 통과하는가?

### 📚 문서화
- [ ] 함수/클래스 문서화가 충분한가?
- [ ] README가 업데이트되었는가?
- [ ] API 문서가 정확한가?

### ⚡ 성능
- [ ] 성능상 병목이 있는가?
- [ ] 메모리 사용량이 적절한가?
- [ ] 알고리즘 복잡도가 최적인가?

### 🛡️ 보안
- [ ] API 키가 하드코딩되지 않았는가?
- [ ] 입력 값 검증이 충분한가?
- [ ] 로깅에 민감한 정보가 포함되지 않았는가?
```

---

## 🚀 배포 및 모니터링

### 📊 **성능 모니터링**

#### **1. 메트릭 수집**
```python
# monitoring/performance_tracker.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import logging

@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터 클래스"""
    strategy_id: str
    timestamp: datetime
    metric_name: str
    value: float
    metadata: Dict[str, str] = None

class PerformanceTracker:
    """전략 성능 추적 클래스"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.logger = logging.getLogger(__name__)
    
    def track_signal_accuracy(self, strategy_id: str, predicted: str, actual: str):
        """신호 정확도 추적"""
        accuracy = 1.0 if predicted == actual else 0.0
        
        metric = PerformanceMetric(
            strategy_id=strategy_id,
            timestamp=datetime.now(),
            metric_name="signal_accuracy",
            value=accuracy,
            metadata={"predicted": predicted, "actual": actual}
        )
        
        self.metrics.append(metric)
        self.logger.info(f"Signal accuracy tracked: {strategy_id} - {accuracy}")
    
    def track_execution_time(self, strategy_id: str, execution_time: float):
        """실행 시간 추적"""
        metric = PerformanceMetric(
            strategy_id=strategy_id,
            timestamp=datetime.now(),
            metric_name="execution_time",
            value=execution_time
        )
        
        self.metrics.append(metric)
        
        # 성능 임계값 경고
        if execution_time > 5.0:  # 5초 초과
            self.logger.warning(f"Slow execution detected: {strategy_id} - {execution_time}s")
    
    def get_performance_summary(self, strategy_id: str, hours: int = 24) -> Dict:
        """성능 요약 보고서 생성"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics 
            if m.strategy_id == strategy_id and m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # 메트릭별 집계
        accuracy_metrics = [m for m in recent_metrics if m.metric_name == "signal_accuracy"]
        time_metrics = [m for m in recent_metrics if m.metric_name == "execution_time"]
        
        summary = {
            "strategy_id": strategy_id,
            "period_hours": hours,
            "total_signals": len(accuracy_metrics),
            "avg_accuracy": sum(m.value for m in accuracy_metrics) / len(accuracy_metrics) if accuracy_metrics else 0,
            "avg_execution_time": sum(m.value for m in time_metrics) / len(time_metrics) if time_metrics else 0,
            "max_execution_time": max(m.value for m in time_metrics) if time_metrics else 0
        }
        
        return summary
```

#### **2. 알림 시스템**
```python
# monitoring/alert_system.py
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict
import smtplib
from email.mime.text import MIMEText

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(ABC):
    """알림 채널 추상 클래스"""
    
    @abstractmethod
    def send_alert(self, level: AlertLevel, message: str, metadata: Dict = None):
        pass

class EmailAlertChannel(AlertChannel):
    """이메일 알림 채널"""
    
    def __init__(self, smtp_server: str, port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
    
    def send_alert(self, level: AlertLevel, message: str, metadata: Dict = None):
        subject = f"[{level.value.upper()}] 업비트 자동매매 알림"
        
        body = f"""
        알림 레벨: {level.value}
        메시지: {message}
        시간: {datetime.now()}
        
        추가 정보:
        {self._format_metadata(metadata)}
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = "admin@example.com"
        
        with smtplib.SMTP(self.smtp_server, self.port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
    
    def _format_metadata(self, metadata: Dict) -> str:
        if not metadata:
            return "없음"
        
        return "\n".join(f"- {k}: {v}" for k, v in metadata.items())

class AlertManager:
    """알림 관리자"""
    
    def __init__(self):
        self.channels: List[AlertChannel] = []
        self.alert_rules = {
            "low_accuracy": {"threshold": 0.5, "level": AlertLevel.WARNING},
            "slow_execution": {"threshold": 5.0, "level": AlertLevel.WARNING},
            "strategy_error": {"level": AlertLevel.ERROR},
            "system_failure": {"level": AlertLevel.CRITICAL}
        }
    
    def add_channel(self, channel: AlertChannel):
        """알림 채널 추가"""
        self.channels.append(channel)
    
    def check_performance_alerts(self, performance_summary: Dict):
        """성능 기반 알림 체크"""
        strategy_id = performance_summary.get("strategy_id")
        
        # 정확도 체크
        accuracy = performance_summary.get("avg_accuracy", 1.0)
        if accuracy < self.alert_rules["low_accuracy"]["threshold"]:
            self._send_alert(
                self.alert_rules["low_accuracy"]["level"],
                f"전략 {strategy_id}의 정확도가 낮습니다: {accuracy:.2%}",
                performance_summary
            )
        
        # 실행 시간 체크
        exec_time = performance_summary.get("avg_execution_time", 0)
        if exec_time > self.alert_rules["slow_execution"]["threshold"]:
            self._send_alert(
                self.alert_rules["slow_execution"]["level"],
                f"전략 {strategy_id}의 실행이 느립니다: {exec_time:.2f}초",
                performance_summary
            )
    
    def _send_alert(self, level: AlertLevel, message: str, metadata: Dict = None):
        """모든 채널로 알림 발송"""
        for channel in self.channels:
            try:
                channel.send_alert(level, message, metadata)
            except Exception as e:
                print(f"Alert sending failed: {e}")
```

---

## 📈 성능 최적화 가이드

### ⚡ **코드 최적화**

#### **1. 프로파일링**
```python
# tools/profiler.py
import cProfile
import pstats
from functools import wraps
import time

def profile_function(func):
    """함수 실행 프로파일링 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        
        result = func(*args, **kwargs)
        
        pr.disable()
        
        # 결과 출력
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # 상위 10개 함수
        
        return result
    
    return wrapper

def time_function(func):
    """함수 실행 시간 측정 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        print(f"{func.__name__} 실행시간: {end_time - start_time:.4f}초")
        
        return result
    
    return wrapper

# 사용 예시
@profile_function
@time_function
def calculate_complex_indicator(prices, period=20):
    """복잡한 지표 계산 (최적화 대상)"""
    pass
```

#### **2. 메모이제이션 (Caching)**
```python
# utils/caching.py
from functools import lru_cache
from typing import Tuple, List
import hashlib
import json

class IndicatorCache:
    """지표 계산 결과 캐싱"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
    
    def _generate_key(self, prices: List[float], params: dict) -> str:
        """캐시 키 생성"""
        # 가격 데이터와 파라미터로 해시 생성
        prices_hash = hashlib.md5(str(prices).encode()).hexdigest()
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        return f"{prices_hash}_{params_hash}"
    
    def get_or_calculate(self, prices: List[float], params: dict, calculator_func):
        """캐시된 결과 반환 또는 계산"""
        cache_key = self._generate_key(prices, params)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 계산 실행
        result = calculator_func(prices, **params)
        
        # 캐시 저장 (크기 제한)
        if len(self.cache) >= self.max_size:
            # LRU 방식으로 오래된 항목 제거
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[cache_key] = result
        return result

# 전역 캐시 인스턴스
indicator_cache = IndicatorCache()

# 사용 예시
def calculate_sma_cached(prices: List[float], period: int = 20) -> List[float]:
    """캐시된 단순이동평균 계산"""
    return indicator_cache.get_or_calculate(
        prices, 
        {"period": period}, 
        lambda p, period: calculate_sma(p, period)
    )
```

#### **3. 벡터화 연산**
```python
# utils/vectorized_calculations.py
import numpy as np
import pandas as pd
from typing import List, Dict, Union

class VectorizedIndicators:
    """NumPy/Pandas를 활용한 벡터화 지표 계산"""
    
    @staticmethod
    def calculate_sma(prices: Union[List[float], np.ndarray], period: int) -> np.ndarray:
        """벡터화된 단순이동평균"""
        prices_array = np.array(prices)
        return pd.Series(prices_array).rolling(window=period).mean().values
    
    @staticmethod
    def calculate_rsi(prices: Union[List[float], np.ndarray], period: int = 14) -> np.ndarray:
        """벡터화된 RSI 계산"""
        prices_series = pd.Series(prices)
        
        # 가격 변화 계산
        delta = prices_series.diff()
        
        # 상승/하락 분리
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # 지수이동평균으로 평균 상승/하락 계산
        avg_gains = gains.ewm(span=period).mean()
        avg_losses = losses.ewm(span=period).mean()
        
        # RSI 계산
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.values
    
    @staticmethod
    def calculate_bollinger_bands(prices: Union[List[float], np.ndarray], 
                                period: int = 20, 
                                std_dev: float = 2.0) -> Dict[str, np.ndarray]:
        """벡터화된 볼린저 밴드 계산"""
        prices_series = pd.Series(prices)
        
        # 중간선 (이동평균)
        middle = prices_series.rolling(window=period).mean()
        
        # 표준편차
        std = prices_series.rolling(window=period).std()
        
        # 상단/하단 밴드
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            'upper': upper.values,
            'middle': middle.values,
            'lower': lower.values
        }

# 성능 비교 테스트
def performance_comparison():
    """벡터화 vs 루프 성능 비교"""
    import time
    
    # 테스트 데이터
    prices = np.random.randn(10000).cumsum() + 100
    
    # 루프 방식 (느림)
    start_time = time.time()
    rsi_loop = calculate_rsi_loop(prices.tolist(), 14)
    loop_time = time.time() - start_time
    
    # 벡터화 방식 (빠름)
    start_time = time.time()
    rsi_vectorized = VectorizedIndicators.calculate_rsi(prices, 14)
    vectorized_time = time.time() - start_time
    
    print(f"루프 방식: {loop_time:.4f}초")
    print(f"벡터화 방식: {vectorized_time:.4f}초")
    print(f"성능 향상: {loop_time / vectorized_time:.1f}배")
```

---

## 🤝 협업 및 커뮤니케이션

### 📢 **개발 프로세스**

#### **1. 이슈 트래킹**
```markdown
## 이슈 템플릿

### 🐛 버그 리포트
**버그 설명:**
간단하고 명확한 버그 설명

**재현 방법:**
1. 단계 1
2. 단계 2
3. 단계 3

**예상 결과:**
예상했던 동작

**실제 결과:**
실제로 발생한 동작

**환경 정보:**
- OS: Windows 10
- Python: 3.11.0
- 브랜치: feature/rsi-strategy

**추가 정보:**
스크린샷, 로그 등

---

### ✨ 기능 요청
**기능 설명:**
새로운 기능에 대한 명확한 설명

**동기:**
이 기능이 왜 필요한지

**구현 아이디어:**
구현 방법에 대한 아이디어

**대안:**
고려해본 다른 방법들
```

#### **2. 코드 리뷰 프로세스**
```markdown
## 코드 리뷰 가이드라인

### 📝 리뷰어 가이드
1. **건설적인 피드백:** 문제점과 함께 해결책 제시
2. **명확한 의사소통:** 애매한 표현 지양
3. **우선순위 표시:** MUST/SHOULD/COULD로 구분
4. **학습 기회:** 더 나은 방법이 있다면 설명과 함께 제안

### 📋 리뷰 체크포인트
- [ ] 비즈니스 로직이 올바른가?
- [ ] 코드가 일관성 있는 스타일을 따르는가?
- [ ] 테스트가 충분한가?
- [ ] 성능에 영향을 주는 부분이 있는가?
- [ ] 보안 취약점이 있는가?

### 💬 리뷰 댓글 예시
```
MUST: 이 부분에서 예외 처리가 필요합니다.
Division by zero 에러가 발생할 수 있습니다.

SHOULD: `calculate_rsi` 함수를 별도 유틸리티로 분리하는 것이 좋겠습니다.
재사용성과 테스트 용이성이 향상됩니다.

COULD: 변수명을 더 명확하게 하면 좋겠습니다.
`x` -> `signal_strength`
```

#### **3. 문서화 표준**
```python
# 모듈 수준 문서화
"""
업비트 자동매매 전략 모듈

이 모듈은 다양한 기술적 분석 기반 트레이딩 전략을 구현합니다.
모든 전략은 StrategyBase 클래스를 상속받아 구현되며,
일관된 인터페이스를 통해 신호를 생성합니다.

주요 기능:
- 진입 전략: 매수/매도 타이밍 결정
- 관리 전략: 포지션 관리 및 리스크 컨트롤
- 조합 전략: 여러 전략의 조합을 통한 신호 생성

사용 예시:
    >>> from upbit_auto_trading.strategies import RSIReversalStrategy
    >>> strategy = RSIReversalStrategy({"rsi_period": 14})
    >>> signal = strategy.generate_signal(market_data)

Author: Trading Team
Version: 1.0.0
Last Updated: 2024-01-20
"""

class StrategyBase:
    """
    모든 트레이딩 전략의 기본 클래스
    
    이 클래스는 전략 구현을 위한 공통 인터페이스를 정의합니다.
    모든 하위 전략 클래스는 이 클래스를 상속받아 구현해야 합니다.
    
    Attributes:
        config (Dict): 전략 설정 딕셔너리
        strategy_id (str): 전략 고유 식별자
        is_initialized (bool): 초기화 상태
    
    Example:
        >>> class MyStrategy(StrategyBase):
        ...     def generate_signal(self, market_data):
        ...         return Signal("BUY", 0.8, datetime.now())
        
    Note:
        이 클래스는 직접 인스턴스화하지 말고 상속받아 사용하세요.
    """
    pass
```

---

## 🔐 보안 및 모범 사례

### 🛡️ **보안 가이드라인**

#### **1. API 키 관리**
```python
# config/security.py
import os
from cryptography.fernet import Fernet
from typing import Optional

class SecureConfig:
    """보안 설정 관리 클래스"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            self.cipher = None
    
    def get_api_key(self, key_name: str) -> Optional[str]:
        """환경변수에서 API 키 조회"""
        # 환경변수에서 먼저 찾기
        api_key = os.getenv(key_name)
        
        if not api_key:
            # 암호화된 설정 파일에서 찾기
            api_key = self._load_encrypted_key(key_name)
        
        return api_key
    
    def _load_encrypted_key(self, key_name: str) -> Optional[str]:
        """암호화된 키 파일에서 로드"""
        try:
            with open(f"secrets/{key_name}.enc", "rb") as f:
                encrypted_key = f.read()
            
            if self.cipher:
                decrypted_key = self.cipher.decrypt(encrypted_key)
                return decrypted_key.decode()
        except FileNotFoundError:
            return None
    
    def store_encrypted_key(self, key_name: str, api_key: str):
        """API 키를 암호화하여 저장"""
        if not self.cipher:
            raise ValueError("Encryption key not provided")
        
        encrypted_key = self.cipher.encrypt(api_key.encode())
        
        os.makedirs("secrets", exist_ok=True)
        with open(f"secrets/{key_name}.enc", "wb") as f:
            f.write(encrypted_key)

# 사용 예시
secure_config = SecureConfig(os.getenv("ENCRYPTION_KEY"))
upbit_api_key = secure_config.get_api_key("UPBIT_API_KEY")
upbit_secret_key = secure_config.get_api_key("UPBIT_SECRET_KEY")
```

#### **2. 입력 검증**
```python
# utils/validation.py
from typing import Any, Dict, List, Union
import re

class InputValidator:
    """입력 값 검증 유틸리티"""
    
    @staticmethod
    def validate_strategy_config(config: Dict[str, Any]) -> Dict[str, List[str]]:
        """전략 설정 검증"""
        errors = {}
        
        # 필수 필드 검증
        required_fields = ["strategy_type", "parameters"]
        for field in required_fields:
            if field not in config:
                errors.setdefault("missing_fields", []).append(field)
        
        # 전략 타입 검증
        valid_types = ["rsi_reversal", "ma_crossover", "bollinger_bounce"]
        if config.get("strategy_type") not in valid_types:
            errors.setdefault("invalid_values", []).append(
                f"Invalid strategy_type: {config.get('strategy_type')}"
            )
        
        # 파라미터 검증
        if "parameters" in config:
            param_errors = InputValidator._validate_parameters(
                config["parameters"], 
                config.get("strategy_type")
            )
            if param_errors:
                errors["parameter_errors"] = param_errors
        
        return errors
    
    @staticmethod
    def _validate_parameters(params: Dict, strategy_type: str) -> List[str]:
        """전략별 파라미터 검증"""
        errors = []
        
        if strategy_type == "rsi_reversal":
            # RSI 파라미터 검증
            rsi_period = params.get("rsi_period", 14)
            if not isinstance(rsi_period, int) or rsi_period < 2 or rsi_period > 100:
                errors.append("rsi_period must be integer between 2 and 100")
            
            thresholds = ["oversold_threshold", "overbought_threshold"]
            for threshold in thresholds:
                value = params.get(threshold)
                if value is not None and (not isinstance(value, (int, float)) or 
                                        value < 0 or value > 100):
                    errors.append(f"{threshold} must be number between 0 and 100")
        
        return errors
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """문자열 입력 정화"""
        # SQL 인젝션 방지를 위한 특수문자 제거
        sanitized = re.sub(r"[;'\"\\]", "", value)
        
        # 길이 제한
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized.strip()
```

---

> **🎯 핵심 원칙**: "코드는 작성할 때보다 읽을 때를 고려하여 작성하고, 항상 보안과 성능을 염두에 두어야 합니다."

이 문서는 지속적으로 업데이트되며, 새로운 모범 사례와 도구가 발견되면 추가될 예정입니다.
