# 🤔 매매 변수 고급 기능 현실성 검토 보고서

## 💭 **침착한 분석 - 사용자 관점에서 본 현실성**

### 🎯 **핵심 제약사항들**

#### 1. **GUI 사용자 관점 (가장 중요)**
- ✅ **단순성이 핵심**: 클릭 몇 번으로 트리거 조건 만들어야 함
- ⚠️ **파라미터 3개 이하**: 그 이상은 혼란 초래
- ⚠️ **직관적 이해**: "정규화 ATR"은 일반 사용자에게 어려움
- ❌ **복잡한 설정**: StochRSI, 다이버전스 등은 전문가 수준

#### 2. **API 제약사항**
- ✅ **업비트 API 제공**: OHLCV, 현재가, 거래량, 호가 등
- ❌ **업비트 API 미제공**: RSI, MACD, ATR 등 (직접 계산 필요)
- ⚠️ **Rate Limit**: 초당 10회, 분당 600회 제한
- ⚠️ **과거 데이터**: 200개 캔들까지만 제공

#### 3. **DB 캐싱 현실성**
- ✅ **OHLCV 저장**: 캔들 데이터는 DB 저장 가능
- ✅ **기본 지표 캐싱**: RSI, MACD, ATR 등은 계산 후 저장 가능
- ⚠️ **복잡한 지표**: 다이버전스, 패턴 인식은 실시간 계산 부담
- ❌ **머신러닝**: LSTM, HMM 등은 개인 시스템에 과도함

## 📊 **현재 시스템 아키텍처 분석**

### **기존 계산 구조**
```python
# 현재: TriggerCalculator 클래스에서 기본 계산
class TriggerCalculator:
    def calculate_rsi(self, prices, period=14):
        # 단순한 RSI 계산

    def calculate_trigger_points(self, variable_data, operator, target_value):
        # 조건 만족 포인트 찾기
```

### **마켓 데이터 구조**
```sql
-- 실제 사용 가능한 데이터
- candlestick_data_1m/5m/15m/1h/4h/1d (OHLCV)
- technical_indicators_1d (SMA, EMA, RSI, MACD 등 캐시)
- market_symbols (심볼 정보)
```

### **UI 트리거 빌더 구조**
- 변수 선택 → 파라미터 설정 → 조건 설정 → 저장
- 현재: 22개 기본 변수, 각 2-5개 파라미터

## 🔄 **현실적인 3단계 접근법**

### **🟢 Phase 1: 즉시 가능 (Type A 파라미터만)**

**ATR 예시:**
```yaml
기존 파라미터:
- period: 14
- timeframe: 1h

추가 가능한 파라미터:
- normalization_enabled: boolean (ATR/현재가*100)
- smoothing_method: enum [sma, ema, wma]
- trailing_multiplier: float (동적 손절용)
```

**현실성 점수: ⭐⭐⭐ (높음)**
- API: OHLCV만 필요 ✅
- 계산: 기존 ATR에 간단한 수식 추가 ✅
- UI: 기존 파라미터 빌더에 3개 필드 추가 ✅
- 사용자: 이해 가능한 수준 ✅

### **🟡 Phase 2: 단기 구현 (Type B 단순 새 변수)**

**VOLUME_SPIKE_DETECTOR 예시:**
```yaml
새 변수:
- variable_id: VOLUME_SPIKE_DETECTOR
- 계산: VOLUME / VOLUME_SMA > threshold
- 출력: [none, low, medium, high, extreme]
- 파라미터: base_period(20), threshold_multiplier(2.0)
```

**현실성 점수: ⭐⭐ (중간)**
- API: OHLCV만 필요 ✅
- 계산: 단순 비율 계산 ✅
- UI: 새 변수 등록 필요 ⚠️
- 사용자: "거래량 급증" 정도로 이해 가능 ✅

### **🔴 Phase 3: 장기 검토 (Type B 복잡한 변수)**

**RSI_DIVERGENCE 예시:**
```yaml
새 변수:
- variable_id: RSI_DIVERGENCE
- 계산: 가격 추세 vs RSI 추세 비교
- 출력: [none, bullish, bearish, hidden_bullish, hidden_bearish]
- 파라미터: lookback_period(20), slope_threshold(0.1)
```

**현실성 점수: ⭐ (낮음)**
- API: OHLCV 필요 ✅
- 계산: 복잡한 추세선 분석 ❌
- UI: 다이버전스 개념 설명 필요 ❌
- 사용자: 전문 지식 필요 ❌

## ⚡ **현실적인 우선순위 재조정**

### **즉시 구현 추천 (1-2주)**

1. **ATR_NORMALIZED** (Type A 파라미터)
   ```yaml
   - normalization_enabled: boolean
   - 계산: (ATR / CURRENT_PRICE) * 100
   - 사용자 이해: "변동성 백분율"
   ```

2. **VOLUME_RELATIVE** (Type A 파라미터)
   ```yaml
   - relative_calculation: boolean
   - 계산: VOLUME / VOLUME_SMA
   - 사용자 이해: "평균 대비 거래량 배율"
   ```

3. **RSI_SMOOTHED** (Type A 파라미터)
   ```yaml
   - smoothing_enabled: boolean
   - smoothing_period: 3
   - 계산: RSI의 3일 이동평균
   ```

### **단기 검토 (3-4주)**

1. **ATR_REGIME** (Type B 단순 새 변수)
   ```yaml
   - 계산: ATR vs 50일 평균 비교
   - 출력: [low, normal, high, extreme]
   - 기준: 표준편차 배수
   ```

2. **VOLUME_SPIKE** (Type B 단순 새 변수)
   ```yaml
   - 계산: VOLUME / VOLUME_SMA
   - 출력: spike_level (1.0-5.0)
   - 임계값: 설정 가능
   ```

### **장기 보류 (복잡도 높음)**

❌ **RSI_DIVERGENCE**: 추세선 분석 복잡
❌ **MACD_ML_PREDICTION**: 머신러닝 과도
❌ **PATTERN_RECOGNITION**: 패턴 인식 어려움

## 🛠️ **구현 가이드라인**

### **Type A 파라미터 추가 기준**
✅ **허용 조건:**
- 기존 변수에 단순 수식 추가 (±×÷ 수준)
- 파라미터 1-2개 추가로 해결
- 일반 사용자가 이해 가능한 개념
- API 호출 증가 없음

### **Type B 새 변수 기준**
✅ **허용 조건:**
- 기존 데이터로 계산 가능
- 출력이 명확한 의미 (숫자 또는 enum)
- 복잡한 알고리즘 불필요
- 실시간 계산 부담 낮음

❌ **금지 조건:**
- 머신러닝/AI 모델 필요
- 복잡한 패턴 인식 알고리즘
- 대량의 히스토리컬 데이터 필요
- 실시간 계산 시 성능 문제

## 🎯 **최종 권장 사항**

### **지금 바로 시작 (현실적 접근)**

1. **ATR에 정규화 파라미터만 추가**
   - 파라미터: `normalization_enabled: boolean`
   - 계산: 기존 ATR / CURRENT_PRICE * 100
   - UI: 체크박스 하나만 추가
   - 테스트: 기존 ATR과 병행 운영

2. **성공하면 점진적 확장**
   - VOLUME 상대화 파라미터
   - RSI 스무딩 파라미터
   - SMA/EMA 적응형 기간

3. **복잡한 기능은 검증 후 결정**
   - 사용자 피드백 수집
   - 성능 영향 측정
   - 실제 매매 효과 검증

### **성공 기준**
- [ ] 기존 시스템 안정성 유지
- [ ] 사용자가 혼란 없이 사용 가능
- [ ] API 호출량 10% 이하 증가
- [ ] 계산 시간 20% 이하 증가
- [ ] 실제 매매 성과 개선 확인

---

**결론: 혁신적인 아이디어들을 현실적으로 단계별 구현하자! 🚀**
