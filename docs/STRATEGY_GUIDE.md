# 📈 전략 시스템 완전 가이드

## 🎯 전략 시스템 개요

**핵심 구조**: DDD 기반 전략 엔티티 + 호환성 검증 시스템
**검증 기준**: 기본 7규칙 전략으로 모든 전략 시스템 검증
**조합 규칙**: 1개 진입 전략(필수) + 0~N개 관리 전략(선택)
**최대 관리 전략**: 5개까지 조합 허용

## 📊 진입 전략 (Entry Strategies)

### 1. RSI 과매수/과매도 전략 ⭐
```python
class RSIEntryStrategy(EntryStrategy):
    """RSI 기반 진입 전략 - 기본 7규칙 검증 기준"""

    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period
        self.oversold = oversold      # 과매도 기준
        self.overbought = overbought  # 과매수 기준

    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        rsi = self.calculate_rsi(data['close'], self.period)

        # 과매도 구간에서 상승 반전 (매수 신호)
        if rsi[-1] > self.oversold and rsi[-2] <= self.oversold:
            return TradingSignal.BUY
        # 과매수 구간에서 하락 반전 (매도 신호)
        elif rsi[-1] < self.overbought and rsi[-2] >= self.overbought:
            return TradingSignal.SELL
        else:
            return TradingSignal.HOLD
```

### 2. 이동평균 크로스오버 전략
```python
class MovingAverageCrossoverStrategy(EntryStrategy):
    """골든크로스/데드크로스 기반 진입"""

    def __init__(self, short_period=20, long_period=50, ma_type='SMA'):
        self.short_period = short_period  # 5~20
        self.long_period = long_period    # 20~60
        self.ma_type = ma_type           # SMA/EMA

    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        short_ma = self.calculate_ma(data['close'], self.short_period)
        long_ma = self.calculate_ma(data['close'], self.long_period)

        # 골든 크로스: 단기선이 장기선 상향 돌파
        if short_ma[-1] > long_ma[-1] and short_ma[-2] <= long_ma[-2]:
            return TradingSignal.BUY
        # 데드 크로스: 단기선이 장기선 하향 돌파
        elif short_ma[-1] < long_ma[-1] and short_ma[-2] >= long_ma[-2]:
            return TradingSignal.SELL
        else:
            return TradingSignal.HOLD
```

### 3. 볼린저 밴드 전략
```python
class BollingerBandsStrategy(EntryStrategy):
    """볼린저 밴드 돌파/반전 전략"""

    def __init__(self, period=20, std_dev=2.0, strategy_type='reversal'):
        self.period = period
        self.std_dev = std_dev
        self.strategy_type = strategy_type  # 'reversal' or 'breakout'

    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        middle, upper, lower = self.calculate_bollinger_bands(data['close'])
        current_price = data['close'].iloc[-1]

        if self.strategy_type == 'reversal':
            # 하단 터치 후 반등
            if current_price <= lower.iloc[-1]:
                return TradingSignal.BUY
            # 상단 터치 후 하락
            elif current_price >= upper.iloc[-1]:
                return TradingSignal.SELL
        else:  # breakout
            # 상단 돌파
            if current_price > upper.iloc[-1]:
                return TradingSignal.BUY
            # 하단 이탈
            elif current_price < lower.iloc[-1]:
                return TradingSignal.SELL

        return TradingSignal.HOLD
```

### 4. MACD 전략
```python
class MACDStrategy(EntryStrategy):
    """MACD 신호선 교차 전략"""

    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signal(self, data: pd.DataFrame) -> TradingSignal:
        macd_line, signal_line, histogram = self.calculate_macd(data['close'])

        # MACD가 신호선을 상향 돌파
        if (macd_line[-1] > signal_line[-1] and
            macd_line[-2] <= signal_line[-2]):
            return TradingSignal.BUY
        # MACD가 신호선을 하향 돌파
        elif (macd_line[-1] < signal_line[-1] and
              macd_line[-2] >= signal_line[-2]):
            return TradingSignal.SELL
        else:
            return TradingSignal.HOLD
```

## 🛡️ 관리 전략 (Management Strategies)

### 1. 물타기 전략 (Pyramid Buying) ⭐
```python
class PyramidBuyingStrategy(ManagementStrategy):
    """하락 시 추가 매수로 평단가 낮추기 - 기본 7규칙 중 하나"""

    def __init__(self, trigger_drop_rate=0.05, max_additions=5,
                 addition_ratio=1.0, absolute_stop_loss=0.15):
        self.trigger_drop_rate = trigger_drop_rate  # 5% 하락마다 추가 매수
        self.max_additions = max_additions          # 최대 5회 추가
        self.addition_ratio = addition_ratio        # 추가 매수 비율
        self.absolute_stop_loss = absolute_stop_loss # 절대 손절선 15%
        self.addition_count = 0

    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> ManagementSignal:
        current_price = data['close'].iloc[-1]
        loss_rate = (position.avg_price - current_price) / position.avg_price

        # 절대 손절선 체크 (급락 감지)
        if loss_rate >= self.absolute_stop_loss:
            return ManagementSignal.CLOSE_POSITION

        # 추가 매수 조건 체크
        required_drop = self.trigger_drop_rate * (self.addition_count + 1)
        if (self.addition_count < self.max_additions and loss_rate >= required_drop):
            self.addition_count += 1
            return ManagementSignal.ADD_BUY

        return ManagementSignal.HOLD
```

### 2. 불타기 전략 (Scale-in Buying) ⭐
```python
class ScaleInBuyingStrategy(ManagementStrategy):
    """수익시 추가 매수로 수익 극대화 - 기본 7규칙 중 하나"""

    def __init__(self, trigger_profit_rate=0.03, max_additions=3,
                 addition_ratio=0.5, profit_target=0.20):
        self.trigger_profit_rate = trigger_profit_rate # 3% 상승마다 추가 매수
        self.max_additions = max_additions             # 최대 3회 추가
        self.addition_ratio = addition_ratio           # 추가 매수 비율 50%
        self.profit_target = profit_target             # 목표 수익률 20%
        self.addition_count = 0

    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> ManagementSignal:
        current_price = data['close'].iloc[-1]
        profit_rate = (current_price - position.avg_price) / position.avg_price

        # 목표 수익률 달성 (계획된 익절)
        if profit_rate >= self.profit_target:
            return ManagementSignal.CLOSE_POSITION

        # 추가 매수 조건 체크 (급등 감지)
        required_profit = self.trigger_profit_rate * (self.addition_count + 1)
        if (self.addition_count < self.max_additions and profit_rate >= required_profit):
            self.addition_count += 1
            return ManagementSignal.ADD_BUY

        return ManagementSignal.HOLD
```

### 3. 트레일링 스탑 전략 ⭐
```python
class TrailingStopStrategy(ManagementStrategy):
    """수익 보호를 위한 후행 손절 - 기본 7규칙 중 하나"""

    def __init__(self, trail_distance=0.05, activation_profit=0.02):
        self.trail_distance = trail_distance      # 5% 거리 유지
        self.activation_profit = activation_profit # 2% 수익 후 활성화
        self.highest_price = 0
        self.stop_price = 0
        self.activated = False

    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> ManagementSignal:
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
                return ManagementSignal.CLOSE_POSITION

        return ManagementSignal.HOLD
```

### 4. 고정 손절/익절 전략 ⭐
```python
class FixedStopLossStrategy(ManagementStrategy):
    """고정 손절선/익절선 설정 - 기본 7규칙 중 하나"""

    def __init__(self, stop_loss_rate=0.05, take_profit_rate=0.10):
        self.stop_loss_rate = stop_loss_rate      # 5% 손절
        self.take_profit_rate = take_profit_rate  # 10% 익절

    def generate_signal(self, position: PositionState, data: pd.DataFrame) -> ManagementSignal:
        current_price = data['close'].iloc[-1]
        profit_rate = (current_price - position.avg_price) / position.avg_price

        # 손절선 터치
        if profit_rate <= -self.stop_loss_rate:
            return ManagementSignal.CLOSE_POSITION
        # 익절선 터치 (계획된 익절)
        elif profit_rate >= self.take_profit_rate:
            return ManagementSignal.CLOSE_POSITION
        else:
            return ManagementSignal.HOLD
```

## 🔗 호환성 검증 시스템

### 변수 호환성 규칙
```python
COMPARISON_GROUPS = {
    "price_comparable": {
        "variables": ["Close", "Open", "High", "Low", "SMA", "EMA", "BB_Upper", "BB_Lower"],
        "unit": "KRW",
        "직접_비교": True
    },
    "percentage_comparable": {
        "variables": ["RSI", "Stochastic_K", "Stochastic_D", "Williams_R"],
        "unit": "%",
        "range": "0-100",
        "직접_비교": True
    },
    "zero_centered": {
        "variables": ["MACD", "MACD_Signal", "MACD_Histogram", "ROC", "CCI"],
        "unit": "없음",
        "range": "0 중심 양수/음수",
        "직접_비교": True
    },
    "volume_based": {
        "variables": ["Volume", "Volume_SMA", "VWAP"],
        "unit": "개수/KRW",
        "직접_비교": True
    }
}
```

### Domain Service 기반 검증
```python
class VariableCompatibilityDomainService:
    """변수 호환성 검증 도메인 서비스"""

    def check_compatibility(self, var1: Variable, var2: Variable) -> CompatibilityResult:
        """두 변수 간 호환성 검증"""

        # 같은 comparison_group = 직접 비교 가능
        if var1.comparison_group == var2.comparison_group:
            return CompatibilityResult.COMPATIBLE

        # price vs percentage = 정규화 후 비교 (경고)
        if self._is_normalizable_pair(var1, var2):
            return CompatibilityResult.WARNING_NORMALIZATION_NEEDED

        # 완전 비호환
        return CompatibilityResult.INCOMPATIBLE

    def filter_compatible_variables(self, base_variable: Variable) -> List[Variable]:
        """기본 변수와 호환 가능한 변수들만 반환"""
        all_variables = self.variable_repository.find_all_active()
        compatible_variables = []

        for var in all_variables:
            if self.check_compatibility(base_variable, var).is_valid():
                compatible_variables.append(var)

        return compatible_variables
```

### 호환성 매트릭스
```
            | Price | Percentage | Zero-Center | Volume
------------|-------|------------|-------------|--------
Price       |   ✅   |     ⚠️     |      ❌     |   ❌
Percentage  |   ⚠️   |     ✅     |      ❌     |   ❌
Zero-Center |   ❌   |     ❌     |      ✅     |   ❌
Volume      |   ❌   |     ❌     |      ❌     |   ✅

✅ 직접 비교 가능
⚠️ 정규화 후 비교 가능 (경고 표시)
❌ 비교 불가능 (UI에서 차단)
```

## 🎯 기본 7규칙 전략 (검증 기준)

### 완전한 7규칙 구성 예시
```python
class Basic7RuleStrategy:
    """시스템 검증을 위한 기본 7규칙 전략"""

    def __init__(self):
        # 진입 전략: RSI 과매도 진입
        self.entry_strategy = RSIEntryStrategy(
            period=14,
            oversold=30,
            overbought=70
        )

        # 관리 전략들
        self.management_strategies = [
            # 1. 수익시 불타기
            ScaleInBuyingStrategy(
                trigger_profit_rate=0.03,
                max_additions=3,
                priority=1
            ),

            # 2. 계획된 익절
            FixedStopLossStrategy(
                stop_loss_rate=0.05,
                take_profit_rate=0.15,
                priority=2
            ),

            # 3. 트레일링 스탑
            TrailingStopStrategy(
                trail_distance=0.05,
                activation_profit=0.02,
                priority=3
            ),

            # 4. 하락시 물타기
            PyramidBuyingStrategy(
                trigger_drop_rate=0.05,
                max_additions=5,
                priority=4
            ),

            # 5-7. 급락/급등 감지는 별도 모니터링 시스템으로 구현
        ]

        self.conflict_resolution = "priority"
```

## 🔄 전략 조합 및 충돌 해결

### 유효한 조합 패턴
```python
# 기본 조합 (진입 + 1개 관리)
basic_combination = {
    "entry_strategy": RSIEntryStrategy(period=14),
    "management_strategies": [
        TrailingStopStrategy(trail_distance=0.05)
    ]
}

# 복합 리스크 관리 (진입 + 여러 관리)
complex_combination = {
    "entry_strategy": MovingAverageCrossoverStrategy(),
    "management_strategies": [
        PyramidBuyingStrategy(max_additions=3, priority=3),
        FixedStopLossStrategy(stop_loss_rate=0.10, priority=2),
        TrailingStopStrategy(trail_distance=0.05, priority=1)
    ],
    "conflict_resolution": "priority"
}
```

### 충돌 해결 방식
1. **priority**: 우선순위 높은 신호 채택
2. **conservative**: 보수적 신호 채택 (HOLD > CLOSE > ADD)
3. **merge**: 신호들을 병합하여 처리

## 🧪 전략 검증 테스트

### 기본 7규칙 동작 검증
```python
def test_basic_7_rule_strategy():
    """기본 7규칙 전략이 모든 시나리오에서 동작하는지 검증"""

    strategy = Basic7RuleStrategy()
    test_scenarios = [
        "bull_market_data.csv",     # 상승장
        "bear_market_data.csv",     # 하락장
        "sideways_market_data.csv", # 횡보장
        "volatile_market_data.csv"  # 변동장
    ]

    for scenario in test_scenarios:
        backtest_result = run_backtest(strategy, scenario)

        # 기본 검증 조건
        assert backtest_result.total_trades > 0, f"{scenario}: 거래 신호 생성 실패"
        assert backtest_result.win_rate is not None, f"{scenario}: 승률 계산 실패"
        assert backtest_result.max_drawdown < 0.30, f"{scenario}: 과도한 손실"

        # 7규칙 특정 검증
        assert backtest_result.has_entry_signals, "진입 신호 부재"
        assert backtest_result.has_management_signals, "관리 신호 부재"
```

### 호환성 검증 테스트
```python
def test_variable_compatibility():
    """변수 호환성 시스템 검증"""

    checker = VariableCompatibilityDomainService()

    # 호환 가능한 조합
    assert checker.check_compatibility("SMA", "EMA").is_compatible()
    assert checker.check_compatibility("RSI", "Stochastic_K").is_compatible()

    # 정규화 필요한 조합 (경고)
    result = checker.check_compatibility("Close", "RSI")
    assert result.needs_normalization()
    assert result.has_warning()

    # 비호환 조합 (차단)
    assert checker.check_compatibility("RSI", "MACD").is_incompatible()
    assert checker.check_compatibility("Volume", "RSI").is_incompatible()
```

## 📚 관련 문서

- **[기본 7규칙 전략 가이드](BASIC_7_RULE_STRATEGY_GUIDE.md)**: 시스템 검증 기준
- **[트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)**: 조건 기반 전략 구성
- **[아키텍처 가이드](ARCHITECTURE_GUIDE.md)**: DDD 기반 설계
- **[통합 설정 관리 가이드](UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md)**: 설정 시스템

---

**🎯 핵심 목표**: 기본 7규칙 전략이 트리거 빌더에서 완벽하게 구성되고 실행되는 시스템!

**💡 검증 방법**: `python run_desktop_ui.py` → 전략 관리 → 트리거 빌더에서 7규칙 구성 테스트
