# 📈 매매 전략 시스템

## 🎯 전략 시스템 개요

**전략 구조**: 1개 진입 전략(필수) + 0~N개 관리 전략(선택)  
**최대 관리 전략**: 5개까지 조합 허용  
**충돌 해결**: priority/conservative/merge 방식 지원  
**검증 기준**: 기본 7규칙 전략으로 모든 전략 시스템 검증
**아키텍처**: DDD 기반 Domain 엔티티로 구현

## 📊 진입 전략 (Entry Strategies)

### Domain Entity 기반 설계
```python
from upbit_auto_trading.domain.entities import EntryStrategy

class MovingAverageCrossoverStrategy(EntryStrategy):
    """골든크로스/데드크로스 기반 진입 - Domain Entity"""
    
    def __init__(self, strategy_id: StrategyId, short_period=20, long_period=50, ma_type='SMA'):
        super().__init__(strategy_id)
        self.short_period = short_period  # 5~20
        self.long_period = long_period    # 20~60  
        self.ma_type = ma_type           # SMA/EMA
        
    def generate_signal(self, market_data: MarketData) -> TradingSignal:
        short_ma = self.calculate_ma(data['close'], self.short_period)
        long_ma = self.calculate_ma(data['close'], self.long_period)
        
        # 골든 크로스: 단기선이 장기선 상향 돌파
        if short_ma[-1] > long_ma[-1] and short_ma[-2] <= long_ma[-2]:
            return 'BUY'
        # 데드 크로스: 단기선이 장기선 하향 돌파
        elif short_ma[-1] < long_ma[-1] and short_ma[-2] >= long_ma[-2]:
            return 'SELL'
        else:
            return 'HOLD'
```

### 2. RSI 과매수/과매도 전략
```python
class RSIEntryStrategy(EntryStrategy):
    """RSI 기반 진입 전략"""
    
    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        rsi = self.calculate_rsi(data['close'], self.period)
        
        # 과매도 구간에서 상승 반전
        if rsi[-1] > self.oversold and rsi[-2] <= self.oversold:
            return 'BUY'
        # 과매수 구간에서 하락 반전    
        elif rsi[-1] < self.overbought and rsi[-2] >= self.overbought:
            return 'SELL'
        else:
            return 'HOLD'
```

### 3. 볼린저 밴드 전략
```python
class BollingerBandsStrategy(EntryStrategy):
    """볼린저 밴드 돌파/반전 전략"""
    
    def __init__(self, period=20, std_dev=2.0, strategy_type='reversal'):
        self.period = period
        self.std_dev = std_dev
        self.strategy_type = strategy_type  # 'reversal' or 'breakout'
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        middle, upper, lower = self.calculate_bollinger_bands(data['close'])
        current_price = data['close'].iloc[-1]
        
        if self.strategy_type == 'reversal':
            # 하단 터치 후 반등
            if current_price <= lower.iloc[-1]:
                return 'BUY'
            # 상단 터치 후 하락
            elif current_price >= upper.iloc[-1]:
                return 'SELL'
        else:  # breakout
            # 상단 돌파
            if current_price > upper.iloc[-1]:
                return 'BUY'
            # 하단 이탈
            elif current_price < lower.iloc[-1]:
                return 'SELL'
                
        return 'HOLD'
```

### 4. 변동성 돌파 전략
```python
class VolatilityBreakoutStrategy(EntryStrategy):
    """래리 윌리엄스 변동성 돌파"""
    
    def __init__(self, lookback_period=20, breakout_ratio=0.5):
        self.lookback_period = lookback_period
        self.breakout_ratio = breakout_ratio
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.lookback_period + 1:
            return 'HOLD'
            
        # 전일 고가-저가 범위 계산
        prev_high = data['high'].iloc[-2]
        prev_low = data['low'].iloc[-2]
        prev_range = prev_high - prev_low
        
        # 당일 시초가
        today_open = data['open'].iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # 돌파 기준가 계산
        buy_target = today_open + (prev_range * self.breakout_ratio)
        sell_target = today_open - (prev_range * self.breakout_ratio)
        
        if current_price >= buy_target:
            return 'BUY'
        elif current_price <= sell_target:
            return 'SELL'
        else:
            return 'HOLD'
```

### 5. MACD 전략
```python
class MACDStrategy(EntryStrategy):
    """MACD 신호선 교차 전략"""
    
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        macd_line, signal_line, histogram = self.calculate_macd(data['close'])
        
        # MACD가 신호선을 상향 돌파
        if (macd_line[-1] > signal_line[-1] and 
            macd_line[-2] <= signal_line[-2]):
            return 'BUY'
        # MACD가 신호선을 하향 돌파
        elif (macd_line[-1] < signal_line[-1] and 
              macd_line[-2] >= signal_line[-2]):
            return 'SELL'
        else:
            return 'HOLD'
```

### 6. 스토캐스틱 전략
```python
class StochasticStrategy(EntryStrategy):
    """스토캐스틱 %K, %D 교차 전략"""
    
    def __init__(self, k_period=14, d_period=3, oversold=20, overbought=80):
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        k_percent, d_percent = self.calculate_stochastic(data)
        
        # 과매도 구간에서 %K가 %D를 상향 돌파
        if (k_percent[-1] > d_percent[-1] and 
            k_percent[-2] <= d_percent[-2] and
            k_percent[-1] < self.oversold):
            return 'BUY'
        # 과매수 구간에서 %K가 %D를 하향 돌파
        elif (k_percent[-1] < d_percent[-1] and 
              k_percent[-2] >= d_percent[-2] and
              k_percent[-1] > self.overbought):
            return 'SELL'
        else:
            return 'HOLD'
```

## 🛡️ 관리 전략 (Management Strategies)

### 1. 물타기 전략 (Pyramid Buying)
```python
class PyramidBuyingStrategy(ManagementStrategy):
    """하락 시 추가 매수로 평단가 낮추기"""
    
    def __init__(self, trigger_drop_rate=0.05, max_additions=5, 
                 addition_ratio=1.0, absolute_stop_loss=0.15):
        self.trigger_drop_rate = trigger_drop_rate
        self.max_additions = max_additions
        self.addition_ratio = addition_ratio
        self.absolute_stop_loss = absolute_stop_loss
        self.addition_count = 0
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        current_price = data['close'].iloc[-1]
        loss_rate = (position.avg_price - current_price) / position.avg_price
        
        # 절대 손절선 체크
        if loss_rate >= self.absolute_stop_loss:
            return 'CLOSE_POSITION'
            
        # 추가 매수 조건 체크
        required_drop = self.trigger_drop_rate * (self.addition_count + 1)
        if (self.addition_count < self.max_additions and loss_rate >= required_drop):
            self.addition_count += 1
            return 'ADD_BUY'
            
        return 'HOLD'
```

### 2. 불타기 전략 (Scale-in Buying)
```python
class ScaleInBuyingStrategy(ManagementStrategy):
    """상승 시 추가 매수로 수익 극대화"""
    
    def __init__(self, trigger_profit_rate=0.03, max_additions=3,
                 addition_ratio=0.5, profit_target=0.20):
        self.trigger_profit_rate = trigger_profit_rate
        self.max_additions = max_additions
        self.addition_ratio = addition_ratio
        self.profit_target = profit_target
        self.addition_count = 0
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        current_price = data['close'].iloc[-1]
        profit_rate = (current_price - position.avg_price) / position.avg_price
        
        # 목표 수익률 달성
        if profit_rate >= self.profit_target:
            return 'CLOSE_POSITION'
            
        # 추가 매수 조건 체크
        required_profit = self.trigger_profit_rate * (self.addition_count + 1)
        if (self.addition_count < self.max_additions and profit_rate >= required_profit):
            self.addition_count += 1
            return 'ADD_BUY'
            
        return 'HOLD'
```

### 3. 트레일링 스탑 전략
```python
class TrailingStopStrategy(ManagementStrategy):
    """수익 보호를 위한 후행 손절"""
    
    def __init__(self, trail_distance=0.05, activation_profit=0.02):
        self.trail_distance = trail_distance
        self.activation_profit = activation_profit
        self.highest_price = 0
        self.stop_price = 0
        self.activated = False
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        current_price = data['close'].iloc[-1]
        profit_rate = (current_price - position.avg_price) / position.avg_price
        
        # 트레일링 스탑 활성화
        if not self.activated and profit_rate >= self.activation_profit:
            self.activated = True
            self.highest_price = current_price
            self.stop_price = current_price * (1 - self.trail_distance)
            
        if self.activated:
            # 최고가 갱신 시 스탑 가격 상향 조정
            if current_price > self.highest_price:
                self.highest_price = current_price
                new_stop = current_price * (1 - self.trail_distance)
                self.stop_price = max(self.stop_price, new_stop)
                
            # 스탑 가격 터치 시 청산
            if current_price <= self.stop_price:
                return 'CLOSE_POSITION'
                
        return 'HOLD'
```

### 4. 고정 손절/익절 전략
```python
class FixedStopLossStrategy(ManagementStrategy):
    """고정 손절선/익절선 설정"""
    
    def __init__(self, stop_loss_rate=0.05, take_profit_rate=0.10):
        self.stop_loss_rate = stop_loss_rate
        self.take_profit_rate = take_profit_rate
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        current_price = data['close'].iloc[-1]
        profit_rate = (current_price - position.avg_price) / position.avg_price
        
        # 손절선 터치
        if profit_rate <= -self.stop_loss_rate:
            return 'CLOSE_POSITION'
        # 익절선 터치
        elif profit_rate >= self.take_profit_rate:
            return 'CLOSE_POSITION'
        else:
            return 'HOLD'
```

### 5. 부분 익절 전략
```python
class PartialTakeProfitStrategy(ManagementStrategy):
    """단계별 부분 익절"""
    
    def __init__(self, profit_levels=[0.05, 0.10, 0.20], 
                 sell_ratios=[0.3, 0.3, 0.4]):
        self.profit_levels = profit_levels
        self.sell_ratios = sell_ratios
        self.executed_levels = set()
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        current_price = data['close'].iloc[-1]
        profit_rate = (current_price - position.avg_price) / position.avg_price
        
        for i, level in enumerate(self.profit_levels):
            if profit_rate >= level and i not in self.executed_levels:
                self.executed_levels.add(i)
                if i == len(self.profit_levels) - 1:  # 마지막 레벨
                    return 'CLOSE_POSITION'
                else:
                    return f'PARTIAL_SELL_{self.sell_ratios[i]}'
                    
        return 'HOLD'
```

### 6. 시간 기반 청산 전략
```python
class TimeBasedExitStrategy(ManagementStrategy):
    """시간 기반 강제 청산"""
    
    def __init__(self, max_holding_hours=168):  # 1주일
        self.max_holding_hours = max_holding_hours
        
    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> str:
        holding_time = datetime.now() - position.entry_time
        holding_hours = holding_time.total_seconds() / 3600
        
        if holding_hours >= self.max_holding_hours:
            return 'CLOSE_POSITION'
        else:
            return 'HOLD'
```

## 🔗 전략 조합 규칙

### 유효한 조합 패턴
```python
# 1. 기본 조합 (진입 + 1개 관리)
basic_combination = {
    "entry_strategy": RSIEntryStrategy(period=14),
    "management_strategies": [
        TrailingStopStrategy(trail_distance=0.05)
    ]
}

# 2. 복합 리스크 관리
complex_combination = {
    "entry_strategy": MovingAverageCrossoverStrategy(),
    "management_strategies": [
        PyramidBuyingStrategy(max_additions=3, priority=3),
        FixedStopLossStrategy(stop_loss_rate=0.10, priority=2),
        PartialTakeProfitStrategy(priority=1)
    ],
    "conflict_resolution": "priority"
}
```

### 충돌 해결 방식
1. **priority**: 우선순위 높은 신호 채택
2. **conservative**: 보수적 신호 채택 (HOLD > CLOSE > ADD)
3. **merge**: 신호들을 병합하여 처리

## 🧪 전략 검증 기준

### 기본 7규칙 전략으로 검증
```python
def validate_strategy_system():
    """모든 전략 시스템이 기본 7규칙을 지원하는지 검증"""
    
    # 기본 7규칙 전략 구성
    basic_strategy = {
        "entry": RSIEntryStrategy(period=14, oversold=30, overbought=70),
        "management": [
            FixedStopLossStrategy(stop_loss_rate=0.05, take_profit_rate=0.10)
        ]
    }
    
    # 백테스팅으로 동작 검증
    backtest_result = run_backtest(basic_strategy, test_data)
    
    assert backtest_result.total_trades > 0
    assert backtest_result.win_rate is not None
    assert backtest_result.total_return is not None
```

## 📚 관련 문서

- [기본 7규칙 전략](BASIC_7_RULE_STRATEGY_GUIDE.md): 전략 검증 기준
- [트리거 빌더](TRIGGER_BUILDER_GUIDE.md): 조건 기반 전략 구성
- [백테스팅](BACKTESTING_GUIDE.md): 전략 성능 검증
- [개발 체크리스트](DEV_CHECKLIST.md): 전략 구현 검증

---
**💡 핵심**: "모든 전략 시스템은 기본 7규칙 전략으로 검증되어야 한다!"
