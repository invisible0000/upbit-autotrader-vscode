# 📊 업비트 데이터 타입별 분석 및 시스템 설계 방향

## 🔍 **업비트 API 데이터 타입 분석**

### **📈 1. 캔들 데이터 (OHLCV)**
| 특징 | 내용 |
|------|------|
| **성격** | 집약된 과거 데이터 |
| **실시간성** | 낮음 (완성된 캔들만 제공) |
| **데이터 크기** | 심볼당 최대 200개 |
| **업데이트 빈도** | 캔들 간격마다 (1분, 5분, 1일 등) |
| **저장 필요성** | ✅ **높음** - 차트, 백테스팅, 기술적 분석 |
| **활용도** | 🔥 **매우 높음** - 7규칙 전략의 핵심 |

### **🎯 2. 현재가 데이터 (Ticker)**
| 특징 | 내용 |
|------|------|
| **성격** | 스냅샷 형태의 현재 시세 |
| **실시간성** | 높음 (WebSocket 구독 권장) |
| **데이터 크기** | 심볼당 1개 (현재 상태만) |
| **업데이트 빈도** | 체결 발생시마다 |
| **저장 필요성** | ⚠️ **낮음** - 메모리 캐시만으로 충분 |
| **활용도** | 🔥 **높음** - 실시간 모니터링, 주문 결정 |

### **📋 3. 호가 데이터 (Orderbook)**
| 특징 | 내용 |
|------|------|
| **성격** | 매수/매도 주문 현황 |
| **실시간성** | 매우 높음 (WebSocket 필수) |
| **데이터 크기** | 심볼당 15레벨 (업비트 기준) |
| **업데이트 빈도** | 주문 변경시마다 (초당 수십~수백회) |
| **저장 필요성** | ⚠️ **낮음** - 실시간 스냅샷만 필요 |
| **활용도** | 🔥 **중간** - 시장 깊이 분석, 슬리피지 예측 |

### **⚡ 4. 체결 데이터 (Trade)**
| 특징 | 내용 |
|------|------|
| **성격** | 실제 거래 기록 (Tick 데이터) |
| **실시간성** | 매우 높음 (실제 거래 발생시) |
| **데이터 크기** | 최대 500개 (최근 7일간) |
| **업데이트 빈도** | 거래 발생시마다 |
| **저장 필요성** | 🤔 **상황에 따라** - 고급 분석용 |
| **활용도** | 📊 **중간~높음** - 정밀한 시장 분석 |

---

## 🧭 **체결 데이터 상세 분석**

### **📊 체결 데이터가 제공하는 정보**
```json
{
  "market": "KRW-BTC",
  "trade_date_utc": "2025-06-27",
  "trade_time_utc": "23:59:59",
  "timestamp": 1751068799336,
  "trade_price": 147058000,        // 실제 체결 가격
  "trade_volume": 0.00006043,      // 실제 체결 수량
  "prev_closing_price": 146852000,
  "change_price": 206000,
  "ask_bid": "BID",                // 매수/매도 구분 ⭐
  "sequential_id": 17510687993360000
}
```

### **🎯 체결 데이터의 핵심 가치**

#### **1. 매수/매도 압력 분석**
```python
# ask_bid 필드로 시장 심리 파악
def analyze_trade_pressure(trades):
    """체결 데이터로 매수/매도 압력 분석"""
    buy_volume = sum(t['trade_volume'] for t in trades if t['ask_bid'] == 'BID')
    sell_volume = sum(t['trade_volume'] for t in trades if t['ask_bid'] == 'ASK')

    pressure_ratio = buy_volume / (buy_volume + sell_volume)
    return {
        'buy_pressure': pressure_ratio,      # 0.6 = 60% 매수 압력
        'sell_pressure': 1 - pressure_ratio,
        'market_sentiment': 'bullish' if pressure_ratio > 0.55 else 'bearish'
    }
```

#### **2. 실시간 거래량 트렌드**
```python
def calculate_volume_trend(trades, window_minutes=5):
    """실시간 거래량 트렌드 계산"""
    recent_trades = filter_recent_trades(trades, window_minutes)

    return {
        'total_volume': sum(t['trade_volume'] for t in recent_trades),
        'trade_count': len(recent_trades),
        'avg_trade_size': total_volume / trade_count,
        'large_trades': [t for t in recent_trades if t['trade_volume'] > threshold]
    }
```

#### **3. 가격 충격 분석**
```python
def analyze_price_impact(trades):
    """큰 거래가 가격에 미치는 영향 분석"""
    large_trades = [t for t in trades if t['trade_volume'] > large_threshold]

    price_movements = []
    for trade in large_trades:
        # 큰 거래 전후 가격 변화 추적
        price_impact = calculate_impact_after_trade(trade)
        price_movements.append(price_impact)

    return {
        'avg_price_impact': np.mean(price_movements),
        'volatility_increase': calculate_volatility_change(trades)
    }
```

### **💡 체결 데이터 활용 시나리오**

#### **🔥 High-Frequency Trading (고빈도 거래)**
- **Scalping 전략**: 초단위 매수/매도 압력 변화 감지
- **Market Making**: 호가와 체결의 괴리 활용
- **Arbitrage**: 거래소 간 체결 시점 차이 활용

#### **📊 Advanced Analytics (고급 분석)**
- **Order Flow 분석**: 큰 주문의 분할 체결 패턴 감지
- **Liquidity 분석**: 시장 유동성 변화 추적
- **Momentum 분석**: 연속 체결의 방향성 분석

#### **⚠️ Risk Management (위험 관리)**
- **Slippage 예측**: 예상 체결가vs실제 체결가 차이
- **Market Impact**: 대량 주문이 시장에 미치는 영향
- **Volatility Burst**: 급격한 거래량 증가 감지

---

## 🏗️ **시스템 설계 방향성**

### **📊 데이터 타입별 시스템 분리 전략**

#### **🥇 1순위: CandleDataProvider (캔들 전용)**
```python
class CandleDataProvider:
    """캔들 데이터 전용 - 안정적이고 예측 가능한 시스템"""

    def get_candles(self, symbol: str, interval: str, count: int) -> List[Candle]
    def sync_candles(self, symbol: str, interval: str) -> bool
    def get_missing_candles(self, symbol: str, start: datetime, end: datetime) -> List[datetime]
```

**✅ 적합한 이유**:
- 데이터 크기 예측 가능 (최대 200개)
- REST API만으로 충분
- 7규칙 전략의 핵심 데이터
- 안정적인 배치 처리 가능

#### **🥈 2순위: RealtimeDataProvider (실시간 전용)**
```python
class RealtimeDataProvider:
    """실시간 데이터 전용 - 티커, 호가 실시간 스트리밍"""

    def subscribe_ticker(self, symbols: List[str], callback: Callable) -> str
    def subscribe_orderbook(self, symbols: List[str], callback: Callable) -> str
    def get_current_price(self, symbol: str) -> float
```

**✅ 적합한 이유**:
- WebSocket 기반 실시간 처리
- 메모리 캐시만으로 충분
- 별도 시스템으로 구성하여 안정성 확보

#### **🥉 3순위: TradeDataProvider (체결 전용) - 선택적**
```python
class TradeDataProvider:
    """체결 데이터 전용 - 고급 분석용"""

    def get_recent_trades(self, symbol: str, count: int) -> List[Trade]
    def subscribe_trades(self, symbols: List[str], callback: Callable) -> str
    def analyze_trade_pressure(self, symbol: str, minutes: int) -> TradePressure
    def detect_large_trades(self, symbol: str, threshold: float) -> List[Trade]
```

**🤔 고려사항**:
- 고급 트레이딩 전략에만 필요
- 데이터 저장이 필요한지 판단 필요
- 초기 단계에서는 생략 가능

---

## 🎯 **체결 데이터 활용 결정 가이드**

### **✅ 체결 데이터가 필요한 경우**

#### **고빈도 트레이딩 (HFT)**
```python
# 예시: 체결 흐름 기반 스캘핑
if recent_trades_show_buying_pressure() and price_momentum_positive():
    place_buy_order_with_tight_stop_loss()
```

#### **정밀한 시장 분석**
```python
# 예시: 시장 충격 예측
large_trade_detected = any(trade.volume > 1.0 for trade in recent_trades)
if large_trade_detected:
    increase_volatility_buffer()
    adjust_position_size()
```

#### **실시간 리스크 관리**
```python
# 예시: 비정상적 거래량 감지
current_volume = get_recent_trade_volume(minutes=5)
if current_volume > historical_average * 3:
    trigger_risk_management_protocol()
```

### **⛔ 체결 데이터가 불필요한 경우**

#### **기본적인 7규칙 전략**
- RSI 과매도/과매수
- 이동평균선 교차
- 볼린저 밴드 돌파
- 단순 추세 추종

→ **캔들 데이터만으로 충분**

#### **장기 투자 전략**
- DCA (Dollar Cost Averaging)
- Rebalancing
- Hold & Accumulate

→ **현재가 데이터만으로 충분**

---

## 🏆 **최종 권장사항**

### **🎯 단계적 접근법**

#### **Phase 1: CandleDataProvider (최우선)**
- 7규칙 전략의 기반 구축
- 안정적이고 예측 가능한 시스템
- 복잡도 최소화로 빠른 구현

#### **Phase 2: RealtimeDataProvider (필요시)**
- 실시간 모니터링 요구사항 발생시
- WebSocket 기반 별도 시스템
- 메모리 캐시 중심

#### **Phase 3: TradeDataProvider (고급 기능)**
- 고빈도 거래 전략 도입시
- 정밀한 시장 분석 요구시
- 충분한 인프라 구축 후

### **💡 체결 데이터 저장 여부 결정**

#### **저장하는 경우**
```python
class TradeRepository:
    """체결 데이터 저장 - 고급 분석용"""

    def save_trades(self, trades: List[Trade]) -> None
    def get_historical_trades(self, symbol: str, days: int) -> List[Trade]
    def analyze_historical_patterns(self, symbol: str) -> TradePattern
```

#### **저장하지 않는 경우**
```python
class RealtimeTradeStream:
    """체결 데이터 스트리밍 - 실시간 분석용"""

    def process_trade_realtime(self, trade: Trade) -> None
    def calculate_rolling_metrics(self, trade: Trade) -> Metrics
    def trigger_alerts_if_needed(self, trade: Trade) -> None
```

### **🎯 명명 규칙 최종 제안**

#### **데이터 타입별 전용 시스템**
- `CandleDataProvider` - 캔들 데이터 전용 ✅
- `RealtimeDataProvider` - 티커/호가 실시간 전용
- `TradeDataProvider` - 체결 데이터 전용 (선택적)

#### **통합 시스템 (복잡도 증가)**
- `MarketDataProvider` - 모든 데이터 타입 통합 ❌

---

## 📌 **결론**

**체결 데이터는 강력하지만 복잡한 도구**입니다.

✅ **캔들 데이터 우선**: 7규칙 전략에는 캔들 데이터가 핵심
✅ **단계적 접근**: CandleDataProvider → RealtimeDataProvider → TradeDataProvider
✅ **명확한 분리**: 각 데이터 타입별 전용 시스템으로 복잡도 관리
✅ **필요성 검증**: 체결 데이터는 실제 고급 전략 도입시에만 추가

**🎯 현재 시점 권장**: **CandleDataProvider 단독 구현**으로 시작하여 안정성과 단순성을 확보한 후, 필요에 따라 다른 데이터 타입 시스템을 추가하는 것이 최적의 전략입니다.
