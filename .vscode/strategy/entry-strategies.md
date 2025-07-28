# 📈 진입 전략 상세 명세

> **참조**: `.vscode/project-specs.md`의 전략 시스템 핵심 섹션

## 🎯 진입 전략 개요

**역할**: 포지션이 없는 상태에서 최초 진입 신호 생성  
**활성화 조건**: `position_state == "waiting_entry"`  
**출력 신호**: `BUY`, `SELL`, `HOLD`  
**구현 목표**: 6개 진입 전략 완전 구현

## 1️⃣ 이동평균 교차 전략 (Moving Average Crossover)

### 전략 로직
```python
class MovingAverageCrossoverStrategy(EntryStrategy):
    """이동평균 교차 진입 전략"""
    
    def __init__(self, short_period=20, long_period=50, ma_type='SMA'):
        self.short_period = short_period  # 단기 이평선 (5~20)
        self.long_period = long_period    # 장기 이평선 (20~60)
        self.ma_type = ma_type           # SMA/EMA
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """이동평균 교차 신호 생성"""
        if len(data) < max(self.short_period, self.long_period):
            return 'HOLD'
            
        if self.ma_type == 'SMA':
            short_ma = data['close'].rolling(self.short_period).mean()
            long_ma = data['close'].rolling(self.long_period).mean()
        else:  # EMA
            short_ma = data['close'].ewm(span=self.short_period).mean()
            long_ma = data['close'].ewm(span=self.long_period).mean()
            
        # 골든 크로스: 단기 이평선이 장기 이평선을 상향 돌파
        if short_ma.iloc[-1] > long_ma.iloc[-1] and short_ma.iloc[-2] <= long_ma.iloc[-2]:
            return 'BUY'
        # 데드 크로스: 단기 이평선이 장기 이평선을 하향 돌파    
        elif short_ma.iloc[-1] < long_ma.iloc[-1] and short_ma.iloc[-2] >= long_ma.iloc[-2]:
            return 'SELL'
        else:
            return 'HOLD'
```

### UI 파라미터 설정
```python
def setup_ma_crossover_ui(self):
    """이동평균 교차 전략 UI"""
    layout = QVBoxLayout()
    
    # 단기 이평선 설정
    short_group = QGroupBox("단기 이동평균")
    short_layout = QVBoxLayout(short_group)
    self.short_period_spin = QSpinBox()
    self.short_period_spin.setRange(5, 20)
    self.short_period_spin.setValue(20)
    short_layout.addWidget(QLabel("기간:"))
    short_layout.addWidget(self.short_period_spin)
    
    # 장기 이평선 설정
    long_group = QGroupBox("장기 이동평균")
    long_layout = QVBoxLayout(long_group)
    self.long_period_spin = QSpinBox()
    self.long_period_spin.setRange(20, 60)
    self.long_period_spin.setValue(50)
    long_layout.addWidget(QLabel("기간:"))
    long_layout.addWidget(self.long_period_spin)
    
    # 이평선 타입
    type_group = QGroupBox("이동평균 종류")
    type_layout = QVBoxLayout(type_group)
    self.ma_type_combo = StyledComboBox()
    self.ma_type_combo.addItems(['SMA (단순)', 'EMA (지수)'])
    type_layout.addWidget(self.ma_type_combo)
    
    layout.addWidget(short_group)
    layout.addWidget(long_group)
    layout.addWidget(type_group)
```

## 2️⃣ RSI 전략 (Relative Strength Index)

### 전략 로직
```python
class RSIEntryStrategy(EntryStrategy):
    """RSI 기반 진입 전략"""
    
    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period        # RSI 계산 기간 (기본 14)
        self.oversold = oversold    # 과매도 기준 (기본 30)
        self.overbought = overbought # 과매수 기준 (기본 70)
        
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """RSI 계산"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """RSI 기반 신호 생성"""
        if len(data) < self.period + 1:
            return 'HOLD'
            
        rsi = self.calculate_rsi(data)
        current_rsi = rsi.iloc[-1]
        previous_rsi = rsi.iloc[-2]
        
        # 과매도 구간에서 상승 반전
        if previous_rsi <= self.oversold and current_rsi > self.oversold:
            return 'BUY'
        # 과매수 구간에서 하락 반전
        elif previous_rsi >= self.overbought and current_rsi < self.overbought:
            return 'SELL'
        else:
            return 'HOLD'
```

## 3️⃣ 볼린저 밴드 전략 (Bollinger Bands)

### 전략 로직
```python
class BollingerBandsStrategy(EntryStrategy):
    """볼린저 밴드 진입 전략"""
    
    def __init__(self, period=20, std_dev=2.0, strategy_type='reversal'):
        self.period = period          # 중심선 기간 (기본 20)
        self.std_dev = std_dev       # 표준편차 승수 (기본 2.0)
        self.strategy_type = strategy_type  # 'reversal' or 'breakout'
        
    def calculate_bollinger_bands(self, data: pd.DataFrame):
        """볼린저 밴드 계산"""
        sma = data['close'].rolling(self.period).mean()
        std = data['close'].rolling(self.period).std()
        
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        
        return upper_band, sma, lower_band
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """볼린저 밴드 신호 생성"""
        if len(data) < self.period:
            return 'HOLD'
            
        upper, middle, lower = self.calculate_bollinger_bands(data)
        current_price = data['close'].iloc[-1]
        previous_price = data['close'].iloc[-2]
        
        if self.strategy_type == 'reversal':
            # 반전 전략: 밴드 터치 후 반전
            if previous_price <= lower.iloc[-2] and current_price > lower.iloc[-1]:
                return 'BUY'  # 하단 밴드에서 반등
            elif previous_price >= upper.iloc[-2] and current_price < upper.iloc[-1]:
                return 'SELL'  # 상단 밴드에서 반락
        else:  # breakout
            # 돌파 전략: 밴드 돌파
            if current_price > upper.iloc[-1] and previous_price <= upper.iloc[-2]:
                return 'BUY'  # 상단 밴드 돌파
            elif current_price < lower.iloc[-1] and previous_price >= lower.iloc[-2]:
                return 'SELL'  # 하단 밴드 이탈
                
        return 'HOLD'
```

## 4️⃣ 변동성 돌파 전략 (Volatility Breakout)

### 전략 로직
```python
class VolatilityBreakoutStrategy(EntryStrategy):
    """변동성 돌파 진입 전략"""
    
    def __init__(self, lookback_period=1, k_value=0.5, close_at_end=True):
        self.lookback_period = lookback_period  # 변동폭 계산 기간 (일)
        self.k_value = k_value                  # K값 (0.1~0.9)
        self.close_at_end = close_at_end        # 당일 종가 청산 여부
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """변동성 돌파 신호 생성"""
        if len(data) < self.lookback_period + 1:
            return 'HOLD'
            
        # 전일 변동폭 계산
        prev_high = data['high'].iloc[-(self.lookback_period+1)]
        prev_low = data['low'].iloc[-(self.lookback_period+1)]
        prev_range = prev_high - prev_low
        
        # 당일 시가
        today_open = data['open'].iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # 돌파 기준가격
        breakout_price = today_open + (prev_range * self.k_value)
        breakdown_price = today_open - (prev_range * self.k_value)
        
        # 돌파 신호
        if current_price > breakout_price:
            return 'BUY'
        elif current_price < breakdown_price:
            return 'SELL'
        else:
            return 'HOLD'
```

## 5️⃣ MACD 전략 (Moving Average Convergence Divergence)

### 전략 로직
```python
class MACDStrategy(EntryStrategy):
    """MACD 진입 전략"""
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        self.fast_period = fast_period      # 빠른 EMA (기본 12)
        self.slow_period = slow_period      # 느린 EMA (기본 26)
        self.signal_period = signal_period  # 시그널 라인 (기본 9)
        
    def calculate_macd(self, data: pd.DataFrame):
        """MACD 계산"""
        ema_fast = data['close'].ewm(span=self.fast_period).mean()
        ema_slow = data['close'].ewm(span=self.slow_period).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """MACD 신호 생성"""
        if len(data) < max(self.slow_period, self.signal_period) + 1:
            return 'HOLD'
            
        macd, signal, histogram = self.calculate_macd(data)
        
        # MACD 라인이 시그널 라인을 상향 돌파
        if (macd.iloc[-1] > signal.iloc[-1] and 
            macd.iloc[-2] <= signal.iloc[-2]):
            return 'BUY'
        # MACD 라인이 시그널 라인을 하향 돌파
        elif (macd.iloc[-1] < signal.iloc[-1] and 
              macd.iloc[-2] >= signal.iloc[-2]):
            return 'SELL'
        else:
            return 'HOLD'
```

## 6️⃣ 스토캐스틱 전략 (Stochastic Oscillator)

### 전략 로직
```python
class StochasticStrategy(EntryStrategy):
    """스토캐스틱 진입 전략"""
    
    def __init__(self, k_period=14, d_period=3, oversold=20, overbought=80):
        self.k_period = k_period        # %K 기간 (기본 14)
        self.d_period = d_period        # %D 기간 (기본 3)
        self.oversold = oversold        # 과매도 기준 (기본 20)
        self.overbought = overbought    # 과매수 기준 (기본 80)
        
    def calculate_stochastic(self, data: pd.DataFrame):
        """스토캐스틱 계산"""
        lowest_low = data['low'].rolling(self.k_period).min()
        highest_high = data['high'].rolling(self.k_period).max()
        
        k_percent = 100 * ((data['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(self.d_period).mean()
        
        return k_percent, d_percent
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """스토캐스틱 신호 생성"""
        if len(data) < self.k_period + self.d_period:
            return 'HOLD'
            
        k_percent, d_percent = self.calculate_stochastic(data)
        
        current_k = k_percent.iloc[-1]
        current_d = d_percent.iloc[-1]
        prev_k = k_percent.iloc[-2]
        prev_d = d_percent.iloc[-2]
        
        # 과매도 구간에서 %K가 %D를 상향 돌파
        if (current_d < self.oversold and 
            current_k > current_d and prev_k <= prev_d):
            return 'BUY'
        # 과매수 구간에서 %K가 %D를 하향 돌파
        elif (current_d > self.overbought and 
              current_k < current_d and prev_k >= prev_d):
            return 'SELL'
        else:
            return 'HOLD'
```

## 🎨 진입 전략 탭 UI 구현

### 전략 선택 및 설정 인터페이스
```python
class EntryStrategyTab(QWidget):
    """진입 전략 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.strategies = {
            'moving_average': MovingAverageCrossoverStrategy,
            'rsi': RSIEntryStrategy,
            'bollinger_bands': BollingerBandsStrategy,
            'volatility_breakout': VolatilityBreakoutStrategy,
            'macd': MACDStrategy,
            'stochastic': StochasticStrategy
        }
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QHBoxLayout(self)
        
        # 왼쪽: 전략 목록 (25%)
        strategy_list_group = QGroupBox("진입 전략 목록")
        strategy_list_layout = QVBoxLayout(strategy_list_group)
        
        self.strategy_list = QListWidget()
        strategy_items = [
            "📊 이동평균 교차",
            "📈 RSI 신호",
            "📉 볼린저 밴드",
            "⚡ 변동성 돌파",
            "🌊 MACD",
            "🎯 스토캐스틱"
        ]
        self.strategy_list.addItems(strategy_items)
        strategy_list_layout.addWidget(self.strategy_list)
        
        # 가운데: 파라미터 설정 (50%)
        parameter_group = QGroupBox("파라미터 설정")
        self.parameter_layout = QVBoxLayout(parameter_group)
        self.parameter_stack = QStackedWidget()
        self.parameter_layout.addWidget(self.parameter_stack)
        
        # 오른쪽: 미리보기 (25%)
        preview_group = QGroupBox("신호 미리보기")
        preview_layout = QVBoxLayout(preview_group)
        self.preview_chart = QLabel("차트 영역")  # 실제로는 차트 위젯
        preview_layout.addWidget(self.preview_chart)
        
        # 레이아웃 비율 설정
        layout.addWidget(strategy_list_group, 25)
        layout.addWidget(parameter_group, 50)
        layout.addWidget(preview_group, 25)
        
        # 시그널 연결
        self.strategy_list.currentRowChanged.connect(self.on_strategy_selected)
        
    def on_strategy_selected(self, index):
        """전략 선택 시 파라미터 UI 변경"""
        self.parameter_stack.setCurrentIndex(index)
        self.update_preview()
```

## 📊 성능 지표 및 검증

### 진입 전략 성과 측정
```python
class EntryStrategyEvaluator:
    """진입 전략 평가기"""
    
    def evaluate_strategy(self, strategy: EntryStrategy, data: pd.DataFrame):
        """전략 성과 평가"""
        signals = []
        for i in range(len(data)):
            window_data = data.iloc[:i+1]
            signal = strategy.generate_signal(window_data)
            signals.append(signal)
            
        signal_series = pd.Series(signals, index=data.index)
        
        return {
            'total_signals': len(signal_series[signal_series != 'HOLD']),
            'buy_signals': len(signal_series[signal_series == 'BUY']),
            'sell_signals': len(signal_series[signal_series == 'SELL']),
            'signal_frequency': self._calculate_signal_frequency(signal_series),
            'signal_accuracy': self._calculate_signal_accuracy(signal_series, data)
        }
        
    def _calculate_signal_frequency(self, signals: pd.Series) -> float:
        """신호 발생 빈도 계산"""
        total_periods = len(signals)
        signal_periods = len(signals[signals != 'HOLD'])
        return signal_periods / total_periods if total_periods > 0 else 0
        
    def _calculate_signal_accuracy(self, signals: pd.Series, data: pd.DataFrame) -> float:
        """신호 정확도 계산 (간단한 다음 기간 수익률 기준)"""
        # 실제 구현에서는 더 정교한 정확도 측정 필요
        pass
```

## 🧪 테스트 케이스

### 진입 전략 단위 테스트
```python
import unittest
import pandas as pd
import numpy as np

class TestEntryStrategies(unittest.TestCase):
    
    def setUp(self):
        """테스트 데이터 설정"""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='1H')
        
        # 모의 OHLCV 데이터 생성
        close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        high_prices = close_prices + np.random.uniform(0, 2, 100)
        low_prices = close_prices - np.random.uniform(0, 2, 100)
        open_prices = np.roll(close_prices, 1)
        volumes = np.random.randint(1000, 10000, 100)
        
        self.test_data = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        }, index=dates)
        
    def test_moving_average_crossover(self):
        """이동평균 교차 전략 테스트"""
        strategy = MovingAverageCrossoverStrategy(short_period=5, long_period=10)
        
        # 충분한 데이터가 있을 때만 신호 생성
        signal = strategy.generate_signal(self.test_data[:20])
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
        
        # 데이터가 부족할 때는 HOLD
        signal = strategy.generate_signal(self.test_data[:5])
        self.assertEqual(signal, 'HOLD')
        
    def test_rsi_strategy(self):
        """RSI 전략 테스트"""
        strategy = RSIEntryStrategy(period=14)
        
        signal = strategy.generate_signal(self.test_data[:30])
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
        
        # RSI 계산 검증
        rsi = strategy.calculate_rsi(self.test_data[:30])
        self.assertTrue(0 <= rsi.iloc[-1] <= 100)
```

이 진입 전략 명세는 6개 전략의 완전한 구현 가이드라인을 제공하며, 각 전략의 핵심 로직과 파라미터를 명확히 정의합니다.
