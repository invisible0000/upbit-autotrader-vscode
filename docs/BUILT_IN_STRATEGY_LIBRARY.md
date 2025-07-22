# 내장 전략 라이브러리 목록 및 관리 가이드

## 📋 개요

업비트 자동매매 시스템에 내장된 모든 전략들의 종합 목록과 관리 정보를 제공합니다. 새로운 전략 추가 시 이 문서를 업데이트하여 전략 생태계를 체계적으로 관리합니다.

---

## 🎯 전략 분류 체계

### 📈 **진입 전략 (Entry Strategies)**
포지션이 없을 때 매수/매도 신호를 생성하는 전략들

### � **증액 전략 (Scale-In Strategies)**
포지션이 있을 때 추가 매수로 포지션을 늘리는 전략들 (피라미딩, 물타기)

### 📉 **감액 전략 (Scale-Out Strategies)**
포지션이 있을 때 부분 매도로 포지션을 줄이는 전략들

### �🛡️ **관리 전략 (Management Strategies)**  
포지션이 있을 때 청산/조정 신호를 생성하는 전략들

### 🔍 **필터 전략 (Filter Strategies)**
다른 전략의 신호를 검증/필터링하는 보조 전략들

---

## 📊 진입 전략 목록

### 🔵 **추세 추종형 (Trend Following)**

#### **1. 이동평균 교차 (Moving Average Cross)**
```python
strategy_id: "moving_average_cross"
class: MovingAverageCrossStrategy
role: ENTRY
signal_type: BUY, SELL
market_phase: TRENDING
risk_level: MEDIUM
```

**파라미터**:
- `fast_period` (int): 단기 이동평균 기간 (기본값: 5)
- `slow_period` (int): 장기 이동평균 기간 (기본값: 20)  
- `ma_type` (str): 이동평균 타입 ["SMA", "EMA", "WMA"] (기본값: "SMA")

**신호 로직**:
- 골든크로스: 단기 MA > 장기 MA → BUY
- 데드크로스: 단기 MA < 장기 MA → SELL

**적용 시장**: 트렌드가 명확한 시장 환경

---

#### **2. MACD 교차 (MACD Cross)**
```python
strategy_id: "macd_cross"
class: MACDCrossStrategy  
role: ENTRY
signal_type: BUY, SELL
market_phase: TRENDING
risk_level: MEDIUM
```

**파라미터**:
- `fast_period` (int): 빠른 EMA 기간 (기본값: 12)
- `slow_period` (int): 느린 EMA 기간 (기본값: 26)
- `signal_period` (int): 시그널 라인 기간 (기본값: 9)
- `histogram_threshold` (float): 히스토그램 임계값 (기본값: 0.0)

**신호 로직**:
- MACD Line > Signal Line → BUY
- MACD Line < Signal Line → SELL

---

### 🔄 **평균 회귀형 (Mean Reversion)**

#### **3. RSI 과매수/과매도 (RSI Reversal)**
```python
strategy_id: "rsi_reversal"
class: RSIReversalStrategy
role: ENTRY  
signal_type: BUY, SELL
market_phase: SIDEWAYS
risk_level: HIGH
```

**파라미터**:
- `rsi_period` (int): RSI 계산 기간 (기본값: 14)
- `oversold_threshold` (float): 과매도 임계값 (기본값: 30.0)
- `overbought_threshold` (float): 과매수 임계값 (기본값: 70.0)
- `min_confidence` (float): 최소 신뢰도 (기본값: 0.6)

**신호 로직**:
- RSI < 30 → BUY (과매도 반전)
- RSI > 70 → SELL (과매수 반전)

---

#### **4. 볼린저 밴드 (Bollinger Bands)**
```python
strategy_id: "bollinger_bands"
class: BollingerBandsStrategy
role: ENTRY
signal_type: BUY, SELL  
market_phase: SIDEWAYS
risk_level: HIGH
```

**파라미터**:
- `period` (int): 이동평균 기간 (기본값: 20)
- `std_dev` (float): 표준편차 배수 (기본값: 2.0)
- `band_touch_threshold` (float): 밴드 터치 임계값 (기본값: 0.98)

**신호 로직**:
- 가격이 하단 밴드 터치 후 반등 → BUY
- 가격이 상단 밴드 터치 후 하락 → SELL

---

#### **5. 스토캐스틱 (Stochastic)**
```python
strategy_id: "stochastic"
class: StochasticStrategy
role: ENTRY
signal_type: BUY, SELL
market_phase: SIDEWAYS  
risk_level: HIGH
```

**파라미터**:
- `k_period` (int): %K 기간 (기본값: 14)
- `d_period` (int): %D 기간 (기본값: 3)
- `oversold_level` (float): 과매도 레벨 (기본값: 20.0)
- `overbought_level` (float): 과매수 레벨 (기본값: 80.0)

---

### 🚀 **돌파형 (Breakout)**

#### **6. 변동성 돌파 (Volatility Breakout)**
```python
strategy_id: "volatility_breakout"  
class: VolatilityBreakoutStrategy
role: ENTRY
signal_type: BUY, SELL
market_phase: VOLATILE
risk_level: HIGH
```

**파라미터**:
- `atr_period` (int): ATR 계산 기간 (기본값: 14)
- `breakout_multiplier` (float): 돌파 배수 (기본값: 2.0)
- `volume_threshold` (float): 거래량 임계값 (기본값: 1.5)

---

## 🛡️ 관리 전략 목록

### 🚨 **손절 전략 (Stop Loss)**

#### **7. 고정 손절 (Fixed Stop Loss)**
```python
strategy_id: "fixed_stop_loss"
class: FixedStopLossStrategy  
role: EXIT
signal_type: STOP_LOSS
market_phase: ALL
risk_level: LOW
```

**파라미터**:
- `stop_loss_percent` (float): 손절 비율 (기본값: 0.05) # 5%
- `immediate_execution` (bool): 즉시 실행 여부 (기본값: True)

**신호 로직**:
- 현재가 < 진입가 × (1 - stop_loss_percent) → STOP_LOSS

---

#### **8. 트레일링 스탑 (Trailing Stop)**
```python
strategy_id: "trailing_stop"
class: TrailingStopStrategy
role: EXIT  
signal_type: TRAILING
market_phase: ALL
risk_level: MEDIUM
```

**파라미터**:
- `trail_percent` (float): 트레일링 비율 (기본값: 0.03) # 3%
- `activation_percent` (float): 활성화 수익률 (기본값: 0.02) # 2%

**신호 로직**:
- 수익률이 activation_percent 도달 시 트레일링 시작
- 최고가 대비 trail_percent 하락 시 → TRAILING

---

### 💰 **익절 전략 (Take Profit)**

#### **9. 목표 익절 (Target Take Profit)**
```python
strategy_id: "target_take_profit"
class: TargetTakeProfitStrategy
role: EXIT
signal_type: TAKE_PROFIT  
market_phase: ALL
risk_level: LOW
```

**파라미터**:
- `target_percent` (float): 목표 수익률 (기본값: 0.10) # 10%
- `partial_exit` (bool): 부분 익절 여부 (기본값: False)

---

#### **10. 부분 익절 (Partial Take Profit)**
```python
strategy_id: "partial_take_profit"
class: PartialTakeProfitStrategy
role: SCALE_OUT
signal_type: PARTIAL_EXIT
market_phase: ALL  
risk_level: MEDIUM
```

**파라미터**:
- `profit_levels` (list): 익절 단계 [0.05, 0.10, 0.15] # 5%, 10%, 15%
- `exit_ratios` (list): 단계별 매도 비율 [0.3, 0.3, 0.4] # 30%, 30%, 40%

---

### ⏰ **시간 기반 전략 (Time-Based)**

#### **11. 시간 기반 청산 (Time-Based Exit)**
```python
strategy_id: "time_based_exit"
class: TimeBasedExitStrategy
role: EXIT
signal_type: TIME_EXIT
market_phase: ALL
risk_level: MEDIUM  
```

**파라미터**:
- `max_hold_hours` (int): 최대 보유 시간 (기본값: 24)
- `force_exit` (bool): 강제 청산 여부 (기본값: True)

---

## � 증액 전략 목록 (Scale-In Strategies)

### 🔺 **피라미딩 전략 (Pyramiding)**

#### **12. 상승 피라미딩 (Upward Pyramiding)**
```python
strategy_id: "upward_pyramiding"
class: UpwardPyramidingStrategy
role: SCALE_IN
signal_type: ADD_BUY
market_phase: TRENDING
risk_level: HIGH
```

**파라미터**:
- `add_trigger_percent` (float): 추가 매수 트리거 상승률 (기본값: 0.05) # 5%
- `add_amount` (int): 추가 매수 금액 (기본값: 100000) # 10만원
- `max_add_count` (int): 최대 추가 매수 횟수 (기본값: 3)
- `profit_exit_percent` (float): 수익 청산 비율 (기본값: 0.05) # 5%
- `loss_exit_percent` (float): 손실 청산 비율 (기본값: 0.03) # 3%

**신호 로직**:
- 매수가 대비 5% 상승 시 → ADD_BUY (최대 3회)
- 3회 추가 매수 후 5% 상승 시 → TAKE_PROFIT (전량 매도)
- 언제든 3% 하락 시 → STOP_LOSS (전량 매도)

**적용 시장**: 강한 상승 트렌드가 예상되는 환경

---

#### **13. 하락 물타기 (Downward Averaging)**
```python
strategy_id: "downward_averaging"
class: DownwardAveragingStrategy
role: SCALE_IN
signal_type: ADD_BUY
market_phase: VOLATILE
risk_level: VERY_HIGH
```

**파라미터**:
- `dip_trigger_percent` (float): 추가 매수 트리거 하락률 (기본값: 0.05) # 5%
- `add_amount` (int): 추가 매수 금액 (기본값: 100000) # 10만원
- `max_add_count` (int): 최대 추가 매수 횟수 (기본값: 3)
- `break_even_exit` (bool): 손익분기점 청산 여부 (기본값: True)
- `stop_loss_percent` (float): 최대 손실 한도 (기본값: 0.15) # 15%

**신호 로직**:
- 매수가 대비 5% 하락 시 → ADD_BUY (최대 3회)
- 평균 매수가 도달 시 → BREAK_EVEN (전량 매도)
- 총 손실 15% 도달 시 → STOP_LOSS (전량 매도)

**적용 시장**: 변동성이 큰 횡보장 또는 약한 하락장

---

## �🔍 필터 전략 목록

### 📊 **거래량 필터 (Volume Filter)**

#### **12. 거래량 확인 (Volume Confirmation)**
```python
strategy_id: "volume_confirmation"
class: VolumeConfirmationStrategy
role: FILTER
signal_type: VOLUME_FILTER
market_phase: ALL
risk_level: LOW
```

**파라미터**:
- `volume_ma_period` (int): 거래량 이동평균 기간 (기본값: 20)
- `volume_threshold` (float): 거래량 임계값 배수 (기본값: 1.5)

---

### 🌊 **변동성 필터 (Volatility Filter)**

#### **13. 변동성 필터 (Volatility Filter)**
```python
strategy_id: "volatility_filter"  
class: VolatilityFilterStrategy
role: FILTER
signal_type: VOLATILITY_FILTER
market_phase: ALL
risk_level: MEDIUM
```

**파라미터**:
- `atr_period` (int): ATR 기간 (기본값: 14)
- `min_volatility` (float): 최소 변동성 (기본값: 0.01) # 1%
- `max_volatility` (float): 최대 변동성 (기본값: 0.10) # 10%

---

## 📁 파일 구조 매핑

```
upbit_auto_trading/strategies/
├── base/
│   ├── strategy_base.py           # 모든 전략의 기본 클래스
│   ├── signal.py                  # Signal 데이터 클래스
│   └── enums.py                   # 전략 관련 열거형
├── entry/
│   ├── moving_average_cross.py    # 이동평균 교차
│   ├── macd_cross.py             # MACD 교차  
│   ├── rsi_reversal.py           # RSI 과매수/과매도
│   ├── bollinger_bands.py        # 볼린저 밴드
│   ├── stochastic.py             # 스토캐스틱
│   └── volatility_breakout.py    # 변동성 돌파
├── management/
│   ├── fixed_stop_loss.py        # 고정 손절
│   ├── trailing_stop.py          # 트레일링 스탑
│   ├── target_take_profit.py     # 목표 익절
│   ├── partial_take_profit.py    # 부분 익절
│   └── time_based_exit.py        # 시간 기반 청산
├── filters/
│   ├── volume_confirmation.py    # 거래량 확인
│   └── volatility_filter.py      # 변동성 필터
└── combinations/
    ├── base_combination.py       # 조합 전략 기본 클래스
    └── predefined_combinations.py # 사전 정의된 조합들
```

---

## 🏭 전략 팩토리 등록

### 📝 **전략 레지스트리 (Strategy Registry)**

```python
# upbit_auto_trading/strategies/strategy_registry.py

STRATEGY_REGISTRY = {
    # 진입 전략
    "moving_average_cross": {
        "class": MovingAverageCrossStrategy,
        "category": "entry",
        "subcategory": "trend_following"
    },
    "macd_cross": {
        "class": MACDCrossStrategy, 
        "category": "entry",
        "subcategory": "trend_following"
    },
    "rsi_reversal": {
        "class": RSIReversalStrategy,
        "category": "entry", 
        "subcategory": "mean_reversion"
    },
    "bollinger_bands": {
        "class": BollingerBandsStrategy,
        "category": "entry",
        "subcategory": "mean_reversion"  
    },
    "stochastic": {
        "class": StochasticStrategy,
        "category": "entry",
        "subcategory": "mean_reversion"
    },
    "volatility_breakout": {
        "class": VolatilityBreakoutStrategy,
        "category": "entry",
        "subcategory": "breakout"
    },
    
    # 관리 전략
    "fixed_stop_loss": {
        "class": FixedStopLossStrategy,
        "category": "management", 
        "subcategory": "stop_loss"
    },
    "trailing_stop": {
        "class": TrailingStopStrategy,
        "category": "management",
        "subcategory": "stop_loss"
    },
    "target_take_profit": {
        "class": TargetTakeProfitStrategy,
        "category": "management",
        "subcategory": "take_profit"
    },
    "partial_take_profit": {
        "class": PartialTakeProfitStrategy, 
        "category": "management",
        "subcategory": "take_profit"
    },
    "time_based_exit": {
        "class": TimeBasedExitStrategy,
        "category": "management",
        "subcategory": "time_based"
    },
    
    # 필터 전략
    "volume_confirmation": {
        "class": VolumeConfirmationStrategy,
        "category": "filter",
        "subcategory": "volume"
    },
    "volatility_filter": {
        "class": VolatilityFilterStrategy,
        "category": "filter", 
        "subcategory": "volatility"
    }
}
```

---

## 🎨 UI 표시 정보

### 🏷️ **전략 배지 매핑**

```python
# GUI에서 사용할 전략 시각화 정보
STRATEGY_UI_INFO = {
    "moving_average_cross": {
        "display_name": "이동평균 교차",
        "badges": ["🔵", "📈", "📊", "🟡"],
        "color": "#2196F3",
        "icon": "📈"
    },
    "rsi_reversal": {
        "display_name": "RSI 과매수/과매도", 
        "badges": ["🔵", "📈", "〰️", "🔴"],
        "color": "#FF5722",
        "icon": "📊"
    },
    "trailing_stop": {
        "display_name": "트레일링 스탑",
        "badges": ["🔴", "🛑", "🔄", "🟡"], 
        "color": "#FF9800",
        "icon": "🛡️"
    }
    # ... 나머지 전략들
}
```

---

## ➕ 새 전략 추가 가이드

### 📋 **체크리스트**

새로운 전략을 추가할 때 다음 단계를 따르세요:

1. **[ ]** 전략 클래스 구현 (`StrategyBase` 상속)
2. **[ ]** 파라미터 스키마 정의
3. **[ ]** 단위 테스트 작성
4. **[ ]** `STRATEGY_REGISTRY`에 등록
5. **[ ]** `STRATEGY_UI_INFO`에 UI 정보 추가
6. **[ ]** 이 문서에 전략 정보 추가
7. **[ ]** 예제 설정 파일 작성

### 🔧 **구현 템플릿**

```python
# upbit_auto_trading/strategies/entry/new_strategy.py
from typing import Dict, Any, Optional
from upbit_auto_trading.strategies.base.strategy_base import StrategyBase
from upbit_auto_trading.strategies.base.signal import Signal

class NewStrategy(StrategyBase):
    """새로운 전략 설명"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.strategy_id = "new_strategy"
        self.strategy_name = "새 전략"
        self.role = "ENTRY"  # or EXIT, FILTER
        self.signal_type = "BUY"  # or SELL, STOP_LOSS, etc.
        
        # 파라미터 초기화
        self.param1 = config.get("param1", default_value)
        
    def generate_signal(self, market_data: Dict[str, Any]) -> Optional[Signal]:
        """신호 생성 로직"""
        # 구현 필요
        pass
        
    def validate_parameters(self) -> bool:
        """파라미터 유효성 검증"""
        # 구현 필요
        pass
```

---

## 📊 전략 통계 현황

| 카테고리 | 전략 수 | 완성도 | 테스트 커버리지 |
|----------|---------|--------|-----------------|
| 진입 전략 | 6개 | 95% | 85% |
| 관리 전략 | 5개 | 90% | 80% |
| 필터 전략 | 2개 | 85% | 75% |
| **총계** | **13개** | **92%** | **82%** |

---

> **💡 전략 추가 원칙**: "각 전략은 독립적이고 테스트 가능해야 하며, 명확한 목적과 책임을 가져야 합니다."

마지막 업데이트: 2024년 1월 20일
