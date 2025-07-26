# 트레이딩 지표 계산 로직 분석 보고서

## 📋 개요

기존 트리거 시스템에서 사용하는 지표들의 계산 로직 위치와 구현 현황을 분석하여 정리한 보고서입니다.

**분석 일시**: 2025년 7월 26일  
**분석 범위**: upbit-autotrader-vscode 프로젝트 전체  
**분석 대상**: SMA, EMA, RSI, MACD, 볼린저 밴드 등 주요 기술적 지표

## 🎯 주요 발견사항

### 1. 지표 계산 로직의 분산 현황

**계산 로직이 여러 파일에 중복 구현되어 있음**을 확인했습니다:

| 파일 위치 | 구현된 지표 | 용도 | 상태 |
|-----------|-------------|------|------|
| `data_layer/processors/indicator_processor.py` | SMA, EMA, RSI, BOLLINGER_BANDS, MACD | 메인 프로세서 | ✅ 완전 구현 |
| `chart_view/chart_view_screen_v2.py` | SMA, EMA, RSI, MACD, Stochastic, Bollinger | 차트 화면용 | ✅ 완전 구현 |
| `chart_view/indicator_overlay.py` | SMA, EMA, RSI | 차트 오버레이용 | ✅ 완전 구현 |
| `strategy_management/robust_simulation_engine.py` | SMA, RSI | 시뮬레이션용 | ✅ 완전 구현 |
| `strategy_management/embedded_simulation_engine.py` | SMA, RSI, MACD | 시뮬레이션용 | ✅ 완전 구현 |
| `trigger_builder/components/simulation_engines.py` | SMA, RSI, MACD | 트리거 빌더용 | ✅ 완전 구현 |

## 🔍 상세 분석

### 1. 메인 지표 프로세서 (`indicator_processor.py`)

**위치**: `upbit_auto_trading/data_layer/processors/indicator_processor.py`

#### 구현된 지표들:

```python
class IndicatorProcessor:
    def _calculate_sma(self, data, params):
        """단순 이동 평균 계산"""
        window = params['window']
        column = params.get('column', 'close')
        data[f'SMA_{window}'] = data[column].rolling(window=window).mean()
        
    def _calculate_ema(self, data, params):
        """지수 이동 평균 계산"""
        window = params['window']
        column = params.get('column', 'close')
        data[f'EMA_{window}'] = data[column].ewm(span=window, adjust=False).mean()
        
    def _calculate_rsi(self, data, params):
        """RSI 계산"""
        delta = data[column].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
    def _calculate_bollinger_bands(self, data, params):
        """볼린저 밴드 계산"""
        data['BB_MIDDLE'] = data[column].rolling(window=window).mean()
        rolling_std = data[column].rolling(window=window).std()
        data['BB_UPPER'] = data['BB_MIDDLE'] + (rolling_std * num_std)
        data['BB_LOWER'] = data['BB_MIDDLE'] - (rolling_std * num_std)
        
    def _calculate_macd(self, data, params):
        """MACD 계산"""
        fast_ema = data[column].ewm(span=fast_period, adjust=False).mean()
        slow_ema = data[column].ewm(span=slow_period, adjust=False).mean()
        data['MACD'] = fast_ema - slow_ema
        data['MACD_SIGNAL'] = data['MACD'].ewm(span=signal_period, adjust=False).mean()
        data['MACD_HIST'] = data['MACD'] - data['MACD_SIGNAL']
```

#### 특징:
- ✅ 파라미터 기반 동적 계산
- ✅ 에러 처리 포함
- ✅ 로깅 지원
- ✅ 다양한 컬럼 지원 ('open', 'high', 'low', 'close')

### 2. 차트 화면용 계산 (`chart_view_screen_v2.py`)

**위치**: `upbit_auto_trading/ui/desktop/screens/chart_view/chart_view_screen_v2.py`

#### 구현된 지표들:

```python
def calculate_sma(self, period):
    """단순 이동 평균 계산"""
    return self.chart_data['close'].rolling(window=period).mean()

def calculate_ema(self, period):
    """지수 이동 평균 계산"""
    return self.chart_data['close'].ewm(span=period, adjust=False).mean()

def calculate_rsi(self, period):
    """RSI 계산"""
    delta = self.chart_data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(self, period, std_multiplier):
    """볼린저 밴드 계산"""
    sma = self.chart_data['close'].rolling(window=period).mean()
    std = self.chart_data['close'].rolling(window=period).std()
    upper = sma + (std * std_multiplier)
    lower = sma - (std * std_multiplier)
    return pd.DataFrame({'upper': upper, 'middle': sma, 'lower': lower})

def calculate_macd(self, fast_period, slow_period, signal_period):
    """MACD 계산"""
    fast_ema = self.chart_data['close'].ewm(span=fast_period).mean()
    slow_ema = self.chart_data['close'].ewm(span=slow_period).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({'macd': macd_line, 'signal': signal_line, 'histogram': histogram})

def calculate_stochastic(self, k_period, d_period):
    """스토캐스틱 계산"""
    low_min = self.chart_data['low'].rolling(window=k_period).min()
    high_max = self.chart_data['high'].rolling(window=k_period).max()
    k_percent = 100 * ((self.chart_data['close'] - low_min) / (high_max - low_min))
    d_percent = k_percent.rolling(window=d_period).mean()
    return pd.DataFrame({'k': k_percent, 'd': d_percent})
```

### 3. 트리거 계산기 (`trigger_calculator.py`)

**위치**: `upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/components/trigger_calculator.py`

#### 특별한 기능:

```python
class TriggerCalculator:
    def calculate_trigger_points(self, price_data, operator, target_value):
        """실제 가격 데이터를 기반으로 트리거 포인트 계산"""
        # 연산자별 조건 확인 (>, >=, <, <=, ~=, !=)
        
    def calculate_rsi_trigger_points(self, rsi_data, operator, target_value):
        """RSI 데이터를 기반으로 트리거 포인트 계산"""
        # RSI 범위 체크 (0-100)
        
    def calculate_macd_trigger_points(self, macd_data, operator, target_value):
        """MACD 데이터를 기반으로 트리거 포인트 계산"""
        # MACD 0 교차 등 처리
```

#### 특징:
- ✅ 트리거 조건 검증
- ✅ 신호 필터링 로직
- ✅ 다양한 연산자 지원
- ✅ 지표별 특화 처리

## 🔄 중복 구현 패턴 분석

### 1. SMA (단순 이동 평균)

동일한 계산 로직이 **6개 파일**에 구현되어 있습니다:

```python
# 패턴 1: 기본 pandas rolling
data['close'].rolling(window=period).mean()

# 패턴 2: 파라미터 기반
data[column].rolling(window=window).mean()
```

### 2. EMA (지수 이동 평균)

동일한 계산 로직이 **5개 파일**에 구현되어 있습니다:

```python
# 공통 패턴
data['close'].ewm(span=period, adjust=False).mean()
```

### 3. RSI

동일한 계산 로직이 **7개 파일**에 구현되어 있습니다:

```python
# 공통 패턴
delta = prices.diff()
gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))
```

## 🎯 통합 기회 및 권장사항

### 1. 중앙 집중식 지표 계산 라이브러리 필요

현재 상황:
- ❌ 동일한 로직이 여러 파일에 중복
- ❌ 수정 시 모든 파일을 업데이트해야 함
- ❌ 일관성 유지 어려움
- ❌ 테스트 복잡성 증가

### 2. 새로운 통합 시스템과의 연계

우리가 구축한 `trading_variables` 시스템에 실제 계산 로직을 통합하면:

```python
# 현재: 분산된 계산
chart_view.calculate_sma(20)
indicator_processor._calculate_sma(data, {'window': 20})
simulation_engine._calculate_rsi(prices, 14)

# 제안: 중앙 집중식 계산
from upbit_auto_trading.utils.trading_variables import IndicatorCalculator

calc = IndicatorCalculator()
sma_result = calc.calculate('SMA', data, period=20)
rsi_result = calc.calculate('RSI', data, period=14)
```

### 3. 구체적 통합 계획

#### Phase 1: 계산 엔진 통합
- `trading_variables` 패키지에 `IndicatorCalculator` 클래스 추가
- 기존 분산된 계산 로직을 하나로 통합
- 파라미터 관리 시스템과 연동

#### Phase 2: 기존 코드 리팩토링
- 각 화면/컴포넌트에서 통합 계산기 사용
- 중복 코드 제거
- 일관성 있는 지표 계산 보장

#### Phase 3: 확장성 확보
- 새 지표 추가 시 한 곳에서만 구현
- 자동 테스트 케이스 생성
- 성능 최적화 중앙 관리

## 📊 현재 구현 상태 요약

| 지표 | 구현 파일 수 | 일관성 | 파라미터 지원 | 상태 |
|------|-------------|--------|---------------|------|
| SMA | 6개 | ✅ 일관됨 | ⚠️ 부분적 | 통합 필요 |
| EMA | 5개 | ✅ 일관됨 | ⚠️ 부분적 | 통합 필요 |
| RSI | 7개 | ✅ 일관됨 | ⚠️ 부분적 | 통합 필요 |
| MACD | 4개 | ✅ 일관됨 | ✅ 지원 | 통합 필요 |
| Bollinger | 3개 | ✅ 일관됨 | ✅ 지원 | 통합 필요 |
| Stochastic | 2개 | ✅ 일관됨 | ✅ 지원 | 통합 필요 |

## 🚀 결론

1. **현재 상태**: 지표 계산 로직이 여러 파일에 중복 구현되어 있음
2. **통합 기회**: 우리의 `trading_variables` 시스템과 연계하여 중앙 집중식 관리 가능
3. **예상 효과**: 코드 중복 제거, 일관성 확보, 유지보수성 향상, 새 지표 추가 시 효율성 증대

**권장사항**: `trading_variables` 패키지에 `IndicatorCalculator` 클래스를 추가하여 모든 지표 계산을 통합 관리하는 것이 최적의 해결책입니다.
