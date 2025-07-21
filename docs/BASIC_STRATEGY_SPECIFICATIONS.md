# 기본 매매 전략 상세 명세서

## 📋 개요

현재 시스템에서 지원하는 4가지 기본 매매 전략의 정확한 정의와 구현 명세입니다.

## 🔧 기본 전략 상세 명세

### 1. 이동평균 교차 (Moving Average Cross)

#### 개념 및 목표
- **개념**: 단기 이동평균선이 장기 이동평균선을 돌파하는 시점을 이용한 추세 추종 전략
- **목표**: 상승 추세 시작점에서 매수, 하락 추세 시작점에서 매도하여 추세 수익 달성

#### 주요 파라미터
```python
parameters = {
    "short_period": 5,          # 단기 이동평균 기간 (기본값: 5일)
    "long_period": 20,          # 장기 이동평균 기간 (기본값: 20일)
    "ma_type": "SMA",           # 이동평균 종류: "SMA" | "EMA"
    "min_cross_strength": 0.1   # 최소 교차 강도 (%) - 가짜 신호 필터링
}
```

#### 신호 생성 로직
```python
def generate_signals(self, data):
    """
    골든크로스/데드크로스 신호 생성
    """
    short_ma = calculate_ma(data, self.short_period, self.ma_type)
    long_ma = calculate_ma(data, self.long_period, self.ma_type)
    
    signals = []
    for i in range(1, len(data)):
        # 골든 크로스 (매수 신호)
        if (short_ma[i] > long_ma[i] and 
            short_ma[i-1] <= long_ma[i-1] and
            abs(short_ma[i] - long_ma[i]) / long_ma[i] >= self.min_cross_strength):
            signals.append('BUY')
        
        # 데드 크로스 (매도 신호)
        elif (short_ma[i] < long_ma[i] and 
              short_ma[i-1] >= long_ma[i-1] and
              abs(short_ma[i] - long_ma[i]) / long_ma[i] >= self.min_cross_strength):
            signals.append('SELL')
        
        else:
            signals.append('HOLD')
    
    return signals
```

### 2. RSI (Relative Strength Index)

#### 개념 및 목표
- **개념**: 가격의 상대적 강도를 측정하여 과매수/과매도 상태를 판단하는 모멘텀 지표
- **목표**: 과매도 구간에서 매수, 과매수 구간에서 매도하여 역추세 매매 수익 달성

#### 주요 파라미터
```python
parameters = {
    "rsi_period": 14,           # RSI 계산 기간 (기본값: 14일)
    "overbought_level": 70,     # 과매수 기준선 (기본값: 70)
    "oversold_level": 30,       # 과매도 기준선 (기본값: 30)
    "signal_confirmation": 2    # 신호 확정 대기 기간 (봉 수)
}
```

#### 신호 생성 로직
```python
def generate_signals(self, data):
    """
    RSI 과매수/과매도 신호 생성
    """
    rsi = calculate_rsi(data, self.rsi_period)
    
    signals = []
    for i in range(self.signal_confirmation, len(data)):
        # 과매도에서 상향 돌파 (매수 신호)
        if (rsi[i] > self.oversold_level and 
            rsi[i-1] <= self.oversold_level and
            all(rsi[j] <= self.oversold_level for j in range(i-self.signal_confirmation, i))):
            signals.append('BUY')
        
        # 과매수에서 하향 돌파 (매도 신호)
        elif (rsi[i] < self.overbought_level and 
              rsi[i-1] >= self.overbought_level and
              all(rsi[j] >= self.overbought_level for j in range(i-self.signal_confirmation, i))):
            signals.append('SELL')
        
        else:
            signals.append('HOLD')
    
    return signals
```

### 3. 볼린저 밴드 (Bollinger Bands)

#### 개념 및 목표
- **개념**: 이동평균선 중심으로 표준편차 범위의 밴드를 설정하여 가격 극단 지점 포착
- **목표**: 가격의 평균 회귀 성질을 이용하여 하단 터치시 매수, 상단 터치시 매도

#### 주요 파라미터
```python
parameters = {
    "bb_period": 20,            # 중심선(이동평균) 기간 (기본값: 20일)
    "bb_stddev": 2.0,           # 표준편차 승수 (기본값: 2.0)
    "touch_threshold": 0.01,    # 밴드 터치 인정 임계값 (1%)
    "trading_mode": "reversal"  # 매매 방식: "reversal" | "breakout"
}
```

#### 신호 생성 로직
```python
def generate_signals(self, data):
    """
    볼린저 밴드 터치/돌파 신호 생성
    """
    middle_band = calculate_sma(data, self.bb_period)
    std_dev = calculate_std(data, self.bb_period)
    upper_band = middle_band + (std_dev * self.bb_stddev)
    lower_band = middle_band - (std_dev * self.bb_stddev)
    
    signals = []
    for i in range(len(data)):
        close_price = data[i]['close']
        
        if self.trading_mode == "reversal":
            # 하단 밴드 터치 (매수 신호)
            if close_price <= lower_band[i] * (1 + self.touch_threshold):
                signals.append('BUY')
            
            # 상단 밴드 터치 (매도 신호)  
            elif close_price >= upper_band[i] * (1 - self.touch_threshold):
                signals.append('SELL')
            
            else:
                signals.append('HOLD')
        
        elif self.trading_mode == "breakout":
            # 상단 밴드 돌파 (매수 신호)
            if close_price > upper_band[i]:
                signals.append('BUY')
            
            # 하단 밴드 돌파 (매도 신호)
            elif close_price < lower_band[i]:
                signals.append('SELL')
            
            else:
                signals.append('HOLD')
    
    return signals
```

### 4. 변동성 돌파 (Volatility Breakout)

#### 개념 및 목표
- **개념**: 래리 윌리엄스의 변동성 돌파 전략 - 변동성 응축 후 폭발적 상승 포착
- **목표**: 조용한 시장에서 에너지 응축 후 급등하는 돌파 순간에 진입하여 상승 추세 포착

#### 주요 파라미터
```python
parameters = {
    "lookback_period": 1,       # 변동폭 계산 기간 (기본값: 1일, 전일)
    "k_value": 0.5,             # 변동폭 승수 (기본값: 0.5)
    "entry_time": "open",       # 진입 기준: "open" | "current"
    "exit_rule": "close",       # 청산 규칙: "close" | "trailing" | "target"
    "stop_loss_ratio": 0.02     # 손절 비율 (기본값: 2%)
}
```

#### 신호 생성 로직
```python
def generate_signals(self, data):
    """
    변동성 돌파 신호 생성 (래리 윌리엄스 방식)
    """
    signals = []
    
    for i in range(self.lookback_period, len(data)):
        current_open = data[i]['open']
        
        # 변동폭 계산 (전일 기준)
        prev_high = data[i-1]['high']
        prev_low = data[i-1]['low']
        daily_range = prev_high - prev_low
        
        # 목표 매수가 계산
        target_buy_price = current_open + (daily_range * self.k_value)
        
        # 현재가가 목표가를 돌파하면 매수
        current_price = data[i]['close']  # 또는 실시간 가격
        
        if current_price >= target_buy_price:
            signals.append('BUY')
        else:
            signals.append('HOLD')
    
    return signals

def get_exit_signal(self, entry_price, current_data, entry_time):
    """
    청산 신호 생성
    """
    current_price = current_data['close']
    
    # 손절 조건
    if current_price <= entry_price * (1 - self.stop_loss_ratio):
        return 'SELL'
    
    # 당일 종가 청산 (기본 규칙)
    if self.exit_rule == "close":
        # 장 마감 시간 체크 로직 필요
        return 'SELL'
    
    return 'HOLD'
```

## 🔗 전략간 상호작용 고려사항

### 추세 vs 역추세 특성
- **추세 추종**: 이동평균 교차, 변동성 돌파
- **역추세**: RSI, 볼린저 밴드 (반전 모드)

### 조합 시 주의사항
1. **상반된 성격**: 추세/역추세 전략을 AND 조합시 신호 발생 빈도 매우 낮음
2. **시장 상황별 적합성**: 박스권에서는 역추세, 트렌드장에서는 추세 추종이 유리
3. **시간프레임 차이**: 단기(분봉) vs 장기(일봉) 신호의 충돌 가능성

## 📊 백테스팅 검증 기준

### 개별 전략 성능 지표
1. **수익률**: 연환산 수익률, 최대 수익률
2. **리스크**: 최대 손실폭(MDD), 변동성, 샤프 비율
3. **거래 특성**: 승률, 평균 수익/손실, 거래 빈도
4. **안정성**: 연속 손실 횟수, 손익 분포

### 조합 전략 추가 지표
1. **다양화 효과**: 개별 전략 대비 리스크 감소 정도
2. **상관관계**: 구성 전략간 신호 상관성
3. **적응성**: 다양한 시장 환경에서의 안정성

이 명세서를 바탕으로 정확한 전략 구현과 테스트가 가능합니다.
