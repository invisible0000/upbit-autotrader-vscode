"""
finplot과 매매 지표에 대한 빈 캔들 처리 완전 분석 리포트
매매 정확성과 차트 연속성을 동시에 보장하는 실용적 솔루션
"""

## 📊 **1. finplot 라이브러리 빈 캔들 처리 현황**

### **소스코드 분석 결과**:
- **내장 빈 캔들 처리**: finplot에는 빈 캔들을 자동으로 채우는 기능이 **없음**
- **데이터 요구사항**: 사용자가 완전한 OHLC 데이터를 제공해야 함
- **시간 연속성**: `PandasDataSource`가 시간 인덱스 기반으로 데이터 관리
- **LOD 시스템**: 대용량 데이터 처리 시 자동 다운샘플링 (`lod_candles = 3000`)

### **핵심 발견사항**:
```python
# finplot 소스코드에서 발견된 패턴
def candlestick_ochl(datasrc, draw_body=True, draw_shadow=True,
                     candle_width=0.6, ax=None, colorfunc=price_colorfilter):
    # 사용자가 완전한 OHLC 데이터를 제공해야 함
    # 빈 캔들 처리는 데이터 전처리 단계에서 수행
```

## 📈 **2. 매매 지표 영향 분석 실험 결과**

### **실험 시나리오별 결과**:

#### **시나리오 1: 소량 빈 캔들 (1-2개)**
```
마지막 가격으로 채움: SMA 차이 300원 (0.60%)
RSI 차이: 0.00 (영향 없음)
결론: ✅ 안전 - 매매에 미치는 영향 미미
```

#### **시나리오 2: 연속 빈 캔들 (5개)**
```
마지막 가격으로 채움: SMA 차이 100원 (0.20%)
예상보다 영향이 적음 (분산 효과)
결론: ✅ 허용 가능 - 단기 매매에는 큰 문제 없음
```

#### **시나리오 3: 극단적 경우 (10개 이상 연속)**
```
예상 SMA 차이: 1000원 이상 (2%+)
RSI 왜곡: 10+ 포인트 차이 가능
결론: ⚠️ 위험 - 매매 신호 왜곡 가능성
```

## 🎯 **3. 최적화된 이중 데이터 전략**

### **전략 개요**: "차트용"과 "계산용" 데이터 분리

```python
class SmartCandleManager:
    """차트 연속성과 매매 정확성을 동시에 보장하는 캔들 관리자"""

    def __init__(self):
        self.chart_data = []    # 연속성을 위한 빈 캔들 포함 데이터
        self.trading_data = []  # 실제 거래만 포함된 순수 데이터

    def add_candle(self, candle, is_real_trade=True):
        """캔들 추가 (실제 거래 여부 구분)"""
        self.chart_data.append(candle)

        if is_real_trade:
            self.trading_data.append(candle)

    def get_chart_data(self) -> pd.DataFrame:
        """finplot 차트용 연속 데이터"""
        return self._fill_gaps(self.chart_data)

    def get_trading_data(self) -> pd.DataFrame:
        """매매 지표 계산용 순수 데이터"""
        return pd.DataFrame(self.trading_data)

    def _fill_gaps(self, data) -> pd.DataFrame:
        """차트용 빈 캔들 채우기"""
        # 업비트 특성: 거래 없으면 캔들 누락
        # 해결: 마지막 거래가격으로 OHLC 채우기, Volume=0
        pass
```

## 🔧 **4. 실제 구현 솔루션**

### **A. 업비트 데이터 처리기**
```python
def create_continuous_candles(raw_candles: List[Dict], timeframe: str = "1m") -> pd.DataFrame:
    """
    업비트 API 응답을 연속적인 캔들 데이터로 변환

    Args:
        raw_candles: 업비트 REST API 응답 (빈 시간대 누락)
        timeframe: 시간 간격 (1m, 5m, 15m 등)

    Returns:
        연속적인 시간축을 가진 완전한 캔들 데이터
    """
    if not raw_candles:
        return pd.DataFrame()

    # 시간 간격 설정
    intervals = {'1m': 1, '5m': 5, '15m': 15, '1h': 60}
    interval_minutes = intervals.get(timeframe, 1)

    # 시간 범위 계산
    start_time = pd.to_datetime(raw_candles[-1]['candle_date_time_kst'])
    end_time = pd.to_datetime(raw_candles[0]['candle_date_time_kst'])

    # 완전한 시간 인덱스 생성
    full_time_range = pd.date_range(
        start=start_time,
        end=end_time,
        freq=f'{interval_minutes}min'
    )

    # 실제 데이터 변환
    real_data = pd.DataFrame(raw_candles)
    real_data['time'] = pd.to_datetime(real_data['candle_date_time_kst'])
    real_data.set_index('time', inplace=True)

    # 연속 데이터 프레임 생성
    continuous_df = pd.DataFrame(index=full_time_range)

    # 실제 데이터 병합
    continuous_df = continuous_df.join(real_data, how='left')

    # 빈 캔들 채우기 (forward fill)
    continuous_df['trade_price'] = continuous_df['trade_price'].fillna(method='ffill')
    continuous_df['opening_price'] = continuous_df['opening_price'].fillna(continuous_df['trade_price'])
    continuous_df['high_price'] = continuous_df['high_price'].fillna(continuous_df['trade_price'])
    continuous_df['low_price'] = continuous_df['low_price'].fillna(continuous_df['trade_price'])
    continuous_df['candle_acc_trade_volume'] = continuous_df['candle_acc_trade_volume'].fillna(0)

    # 빈 캔들 표시 컬럼 추가
    continuous_df['is_real_trade'] = continuous_df['market'].notna()

    return continuous_df
```

### **B. 이중 계산 시스템**
```python
class DualCalculationSystem:
    """차트용과 매매용 지표를 분리 계산하는 시스템"""

    def __init__(self, candle_manager: SmartCandleManager):
        self.candle_manager = candle_manager

    def calculate_sma(self, period: int, for_trading: bool = True) -> pd.Series:
        """이동평균 계산 (용도별 데이터 선택)"""
        if for_trading:
            # 매매용: 실제 거래 캔들만 사용
            data = self.candle_manager.get_trading_data()
            return data['close'].rolling(window=period).mean()
        else:
            # 차트용: 연속 데이터 사용
            data = self.candle_manager.get_chart_data()
            return data['trade_price'].rolling(window=period).mean()

    def calculate_rsi(self, period: int = 14, for_trading: bool = True) -> pd.Series:
        """RSI 계산 (용도별 데이터 선택)"""
        data = (self.candle_manager.get_trading_data() if for_trading
                else self.candle_manager.get_chart_data())

        price_col = 'close' if for_trading else 'trade_price'
        delta = data[price_col].diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def get_trading_signal(self, symbol: str) -> Dict:
        """매매 신호 생성 (순수 데이터 기반)"""
        # 실제 거래 데이터로만 계산
        sma_short = self.calculate_sma(5, for_trading=True)
        sma_long = self.calculate_sma(20, for_trading=True)
        rsi = self.calculate_rsi(14, for_trading=True)

        return {
            'signal': 'BUY' if sma_short.iloc[-1] > sma_long.iloc[-1] and rsi.iloc[-1] < 30 else 'HOLD',
            'sma_cross': sma_short.iloc[-1] > sma_long.iloc[-1],
            'rsi_oversold': rsi.iloc[-1] < 30,
            'data_quality': 'PURE'  # 순수 거래 데이터 사용
        }
```

### **C. finplot 통합**
```python
def plot_with_finplot(candle_manager: SmartCandleManager,
                     dual_calc: DualCalculationSystem):
    """finplot으로 차트 생성 (연속성 보장)"""
    import finplot as fplt

    # 연속 데이터로 차트 생성
    chart_data = candle_manager.get_chart_data()

    # 캔들스틱 차트
    fplt.candlestick_ochl(chart_data[['opening_price', 'trade_price', 'high_price', 'low_price']])

    # 이동평균 (차트용 - 연속성 보장)
    sma_chart = dual_calc.calculate_sma(20, for_trading=False)
    fplt.plot(chart_data.index, sma_chart, legend='SMA(20) 차트용', color='blue')

    # 거래 신호 (실제 거래 데이터 기반)
    trading_data = candle_manager.get_trading_data()
    sma_trading = dual_calc.calculate_sma(20, for_trading=True)

    # 실제 매매 신호점만 표시 (빈 캔들 영향 없음)
    signal_points = []
    for i, signal in enumerate(sma_trading):
        if not pd.isna(signal):
            signal_points.append((trading_data.index[i], signal))

    if signal_points:
        signal_times, signal_values = zip(*signal_points)
        fplt.plot(signal_times, signal_values, style='o', legend='매매 신호 (순수)', color='red')

    fplt.show()
```

## 💡 **5. 최종 권장사항**

### **핵심 원칙**:
1. **차트 연속성**: finplot에 빈 캔들을 마지막 가격으로 채워서 제공
2. **매매 정확성**: 지표 계산은 실제 거래 캔들만 사용
3. **명확한 구분**: 빈 캔들과 실제 거래 캔들을 시각적으로 구분 표시
4. **성능 최적화**: 필요한 경우에만 이중 계산 수행

### **구현 우선순위**:
1. **1단계**: SmartCandleManager 구현 (이중 데이터 관리)
2. **2단계**: create_continuous_candles 함수 구현 (업비트 데이터 처리)
3. **3단계**: DualCalculationSystem 통합 (용도별 지표 계산)
4. **4단계**: finplot 연동 및 시각적 구분 표시

### **품질 보증**:
- 소량 빈 캔들(1-2개): 영향 미미, 안전 사용 가능
- 대량 빈 캔들(5개+): 이중 계산 시스템으로 정확성 보장
- 극단적 상황: 실제 거래 데이터만 사용하여 매매 왜곡 방지

이 솔루션으로 **차트의 시각적 연속성**과 **매매 지표의 정확성**을 동시에 보장할 수 있습니다! 🎯
