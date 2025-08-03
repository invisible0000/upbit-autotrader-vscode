# 📈 전략 시스템 명세서

## 📋 개요

전략 시스템은 **진입 전략**과 **관리 전략**을 분리하여 포지션 상태에 따른 차별화된 매매 로직을 제공합니다.

## 🔄 핵심 아키텍처: 역할 분리 구조

### 전략 유형 구분
- **진입 전략**: 포지션이 없을 때만 작동 → 최초 진입 신호
- **관리 전략**: 활성 포지션이 있을 때만 작동 → 리스크 관리

### 상태 기반 실행 로직
```
포지션 없음 → 진입 전략 실행 → BUY/SELL/HOLD
     ↓ (진입 완료)
활성 포지션 → 관리 전략 실행 → ADD_BUY/CLOSE_POSITION/UPDATE_STOP
```

### 조합 규칙
- **필수**: 1개 진입 전략
- **선택**: 0~N개 관리 전략
- **제약**: 같은 유형 전략 중복 불가

## 📈 진입 전략 (6종)

### 1. 이동평균 교차 (MA Crossover)
```python
# 단기 이평선이 장기 이평선을 상향 돌파
signal = "BUY" if SMA(short) > SMA(long) else "SELL"

# 파라미터
{
    "short_period": 5,      # 단기 기간
    "long_period": 20,      # 장기 기간
    "source": "close"       # 데이터 소스
}
```

### 2. RSI 진입 전략
```python
# 과매도/과매수 구간 진입
signal = "BUY" if RSI < oversold else "SELL" if RSI > overbought else "HOLD"

# 파라미터
{
    "period": 14,           # 계산 기간
    "oversold": 30,         # 과매도 기준
    "overbought": 70,       # 과매수 기준
    "source": "close"
}
```

### 3. 볼린저 밴드 전략
```python
# 밴드 터치 시 반전/돌파 전략
if strategy_type == "mean_reversion":
    signal = "BUY" if price <= lower_band else "SELL" if price >= upper_band
else:  # breakout
    signal = "BUY" if price > upper_band else "SELL" if price < lower_band

# 파라미터  
{
    "period": 20,           # 기간
    "std_dev": 2.0,        # 표준편차 승수
    "strategy": "mean_reversion"  # "mean_reversion" or "breakout"
}
```

### 4. 변동성 돌파 전략
```python
# 전일 변동폭 기준 돌파
high_break = today_high > yesterday_high + (yesterday_range * threshold)
low_break = today_low < yesterday_low - (yesterday_range * threshold)

signal = "BUY" if high_break else "SELL" if low_break else "HOLD"

# 파라미터
{
    "threshold": 0.5,       # 돌파 기준 (0.5 = 50%)
    "lookback": 1           # 과거 몇일 기준
}
```

### 5. MACD 전략
```python
# MACD와 시그널라인 교차
signal = "BUY" if MACD > signal_line and prev_MACD <= prev_signal
signal = "SELL" if MACD < signal_line and prev_MACD >= prev_signal

# 파라미터
{
    "fast_period": 12,      # 빠른 EMA
    "slow_period": 26,      # 느린 EMA  
    "signal_period": 9      # 시그널 라인
}
```

### 6. 스토캐스틱 전략
```python
# %K와 %D 교차 신호
signal = "BUY" if k_percent > d_percent and k_percent < oversold
signal = "SELL" if k_percent < d_percent and k_percent > overbought

# 파라미터
{
    "k_period": 14,         # %K 기간
    "d_period": 3,          # %D 기간
    "oversold": 20,         # 과매도 기준
    "overbought": 80        # 과매수 기준
}
```

## 🛡️ 관리 전략 (6종)

### 1. 물타기 전략 (Dollar Cost Averaging)
```python
# 하락 시 추가 매수로 평균 단가 낮추기
if current_loss_percent >= trigger_loss:
    if additional_buy_count < max_buys:
        action = "ADD_BUY"
        amount = base_amount * multiplier ** additional_buy_count

# 파라미터
{
    "trigger_loss": -5.0,   # 손실 % 기준 (-5%)
    "max_buys": 5,          # 최대 추가 매수 횟수
    "multiplier": 1.5,      # 매수량 증가 배수
    "interval": 24          # 추가 매수 간격 (시간)
}
```

### 2. 불타기 전략 (Pyramid Adding)
```python
# 상승 시 추가 매수로 수익 극대화
if current_profit_percent >= trigger_profit:
    if pyramid_count < max_pyramids:
        action = "ADD_BUY"
        amount = base_amount * reduction_ratio ** pyramid_count

# 파라미터
{
    "trigger_profit": 3.0,  # 수익 % 기준 (+3%)
    "max_pyramids": 3,      # 최대 피라미드 횟수
    "reduction_ratio": 0.7, # 매수량 감소 비율
    "profit_lock": True     # 수익 보장 기능
}
```

### 3. 트레일링 스탑
```python
# 최고점 대비 일정 % 하락 시 손절
peak_price = max(entry_price, current_peak)
stop_price = peak_price * (1 - trailing_percent / 100)

if current_price <= stop_price:
    action = "CLOSE_POSITION"

# 파라미터
{
    "trailing_percent": 5.0,  # 트레일링 % (5%)
    "activation_profit": 2.0, # 활성화 수익률 (2%)
    "step_size": 0.5          # 업데이트 단위 (0.5%)
}
```

### 4. 고정 익절/손절
```python
# 목표 수익률/손실률 도달 시 자동 청산
if current_profit_percent >= take_profit:
    action = "CLOSE_POSITION"
elif current_loss_percent <= -stop_loss:
    action = "CLOSE_POSITION"

# 파라미터
{
    "take_profit": 10.0,    # 익절 기준 (+10%)
    "stop_loss": 5.0,       # 손절 기준 (-5%)
    "partial_close": False   # 부분 청산 여부
}
```

### 5. 부분 청산 전략
```python
# 단계별 수익 실현
for level in profit_levels:
    if current_profit >= level["profit"] and not level["executed"]:
        close_amount = position_size * level["close_ratio"]
        action = "PARTIAL_CLOSE"

# 파라미터
{
    "levels": [
        {"profit": 5.0, "close_ratio": 0.3},   # 5% 수익 시 30% 청산
        {"profit": 10.0, "close_ratio": 0.5},  # 10% 수익 시 50% 청산
        {"profit": 20.0, "close_ratio": 1.0}   # 20% 수익 시 전체 청산
    ]
}
```

### 6. 시간 기반 청산
```python
# 최대 보유 시간 제한
holding_hours = (current_time - entry_time).total_seconds() / 3600

if holding_hours >= max_holding_hours:
    action = "CLOSE_POSITION"

# 파라미터
{
    "max_holding_hours": 168,  # 최대 보유 시간 (7일)
    "force_close": True,       # 강제 청산 여부
    "time_zone": "KST"         # 시간대
}
```

## 🔗 전략 조합 예시

### 보수적 전략 조합
```python
# 진입: RSI 과매도 + 이동평균 상향 돌파
entry_strategy = RSI_Strategy(oversold=25) + MA_Crossover(5, 20)

# 관리: 고정 손익 + 트레일링 스탑
management_strategies = [
    FixedProfitLoss(take_profit=8, stop_loss=4),
    TrailingStop(trailing_percent=3)
]
```

### 공격적 전략 조합
```python
# 진입: 변동성 돌파
entry_strategy = VolatilityBreakout(threshold=0.7)

# 관리: 불타기 + 물타기 + 부분 청산
management_strategies = [
    PyramidAdding(max_pyramids=2),
    DollarCostAveraging(max_buys=3),
    PartialClose(levels=[{"profit": 15, "ratio": 0.5}])
]
```

## 🧪 백테스팅 검증

### 성능 지표
- **총 수익률**: 전체 기간 수익률
- **최대 손실폭(MDD)**: 최대 드로우다운
- **샤프 비율**: 위험 대비 수익
- **승률**: 수익 거래 비율
- **평균 보유 시간**: 포지션 평균 유지 기간

### 검증 기준
- **데이터**: 1년치 분봉 데이터
- **처리 시간**: 5분 이내 완료
- **거래 비용**: 수수료 0.05% 반영
- **슬리피지**: 호가 스프레드 고려

## 📚 관련 문서

- [트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)
- [백테스팅 시스템](BACKTESTING_SYSTEM.md)
- [전략 메이커 UI](STRATEGY_MAKER_UI.md)
