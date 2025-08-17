# 🎯 우선순위 변수 5개 상세 분석

## 📊 분석 대상 변수

### 1. ATR (변동성의 왕) ⭐⭐⭐
**현재 상태**: 2개 파라미터 (period=14, timeframe=enum)
**도움말 발견 고급 기능**:
- [x] 정규화 ATR (ATR/CURRENT_PRICE*100) - 가격 독립적 분석
- [x] 변동성 레짐 감지 - ATR > 평균±표준편차*2로 4단계 구분
- [x] 동적 손절선 - 진입가-(ATR*배수)로 트레일링 스톱
- [x] 포지션 사이징 - 고정리스크/ATR*2 공식
- [x] 과거값 참조 - ATR[5] 형태로 추세 비교
- [x] Kelly Criterion 연계 - 최적 포지션 크기 계산
- [x] 시간대별 패턴 - 장시작/점심/마감 시간별 ATR 배율

**분류 결과**:
- **Type A 파라미터 확장** (우선순위: 높음):
  - `regime_detection_enabled`: boolean, 기본값 false
  - `normalization_enabled`: boolean, 기본값 false
  - `trailing_multiplier`: float, 기본값 2.0, 범위 1.0-5.0
- **Type B 새 변수 필요** (구현 복잡도: 중간):
  - `ATR_VOLATILITY_REGIME`: [low_vol, normal_vol, high_vol, extreme_vol]
  - `ATR_NORMALIZED`: 정규화된 ATR 백분율 값
  - `ATR_POSITION_SIZER`: Kelly 기반 포지션 크기 계산

### 2. RSI (모멘텀의 핵심) ⭐⭐⭐
**현재 상태**: 2개 파라미터 (period=14, timeframe=enum)
**도움말 발견 고급 기능**:
- [x] 확률적 RSI (StochRSI) - RSI에 Stochastic 공식 적용
- [x] 다이버전스 감지 - 가격 vs RSI 방향성 불일치 탐지
- [x] 볼라틸리티 조정 RSI (VI-RSI) - 변동성 지수 통합
- [x] 동적 과매수/과매도 임계값 - 시장 상황별 적응적 기준
- [x] 확률론적 모델링 - 현재 RSI에서 반전 확률 계산
- [x] 체제 변화 탐지 - Hidden Markov Model 활용
- [x] 기계학습 패턴 인식 - LSTM 기반 RSI 패턴 학습
- [x] 시장 레짐별 해석 - bull/bear/sideways 체제별 임계값

**분류 결과**:
- **Type A 파라미터 확장** (우선순위: 높음):
  - `divergence_period`: integer, 기본값 20, 범위 10-50
  - `dynamic_threshold_enabled`: boolean, 기본값 false
  - `volatility_adjustment`: boolean, 기본값 false
  - `reversal_probability_threshold`: float, 기본값 0.7, 범위 0.5-0.9
- **Type B 새 변수 필요** (구현 복잡도: 높음):
  - `RSI_STOCHASTIC`: StochRSI 값 (0.0-1.0)
  - `RSI_DIVERGENCE`: [none, bullish, bearish, hidden_bullish, hidden_bearish]
  - `RSI_VOLATILITY_ADJUSTED`: VI-RSI 값
  - `RSI_REVERSAL_PROBABILITY`: 현재 레벨에서 반전 확률

### 3. MACD (추세의 정수) ⭐⭐⭐
**현재 상태**: 5개 파라미터 (fast=12, slow=26, signal=9, timeframe=enum 등)
**도움말 발견 고급 기능**:
- [x] 히스토그램 분석 - 모멘텀 가속/감속 감지
- [x] 볼륨 가중 MACD (V-MACD) - 거래량 반영 계산
- [x] 다중 시간대 MACD - 여러 시간축 신호 조합
- [x] MACD-RSI 융합 - RSI(MACD_LINE, 14) 계산
- [x] 적응형 파라미터 - 시장 변동성별 Fast/Slow 조정
- [x] 포트폴리오 스코어링 - 여러 자산의 MACD 기반 점수 계산
- [x] 머신러닝 예측 - LSTM 기반 3일 후 MACD 방향 예측
- [x] 극한 상황 필터 - 블랙 스완 이벤트 감지 및 신호 중단

**분류 결과**:
- **Type A 파라미터 확장** (우선순위: 중간):
  - `histogram_analysis_enabled`: boolean, 기본값 false
  - `volume_weighting_enabled`: boolean, 기본값 false
  - `adaptive_parameters`: boolean, 기본값 false
  - `extreme_event_filter`: boolean, 기본값 true
- **Type B 새 변수 필요** (구현 복잡도: 중간):
  - `MACD_VOLUME_WEIGHTED`: V-MACD 라인 값
  - `MACD_HISTOGRAM_MOMENTUM`: 히스토그램 변화율
  - `MACD_RSI_FUSION`: RSI(MACD) 값
  - `MACD_MULTI_TIMEFRAME`: 다중 시간대 종합 신호

### 4. VOLUME_SMA (거래량의 비밀) ⭐⭐
**현재 상태**: 2개 파라미터 (period=20, timeframe=enum)
**도움말 발견 고급 기능**:
- [x] 상대 거래량 비율 - VOLUME/VOLUME_SMA 비교
- [x] 거래량 스파이크 감지 - 평균 대비 N배 이상 급증
- [x] 거래량 추세 분석 - VOLUME_SMA 기울기 계산
- [x] 다중 기간 조합 - 5일/20일/50일 SMA 골든/데드 크로스
- [x] 가격-거래량 다이버전스 - 가격↑거래량↓ 패턴 감지
- [x] 거래량 강도 측정 - 여러 기간 동시 돌파 확인
- [x] 시장 참여도 분석 - 거래량 기저 변화 추세

**분류 결과**:
- **Type A 파라미터 확장** (우선순위: 중간):
  - `spike_threshold_multiplier`: float, 기본값 2.0, 범위 1.5-5.0
  - `trend_analysis_enabled`: boolean, 기본값 false
  - `multi_period_analysis`: boolean, 기본값 false
- **Type B 새 변수 필요** (구현 복잡도: 낮음):
  - `VOLUME_SPIKE_DETECTOR`: [none, low, medium, high, extreme]
  - `VOLUME_TREND_STRENGTH`: 거래량 추세 강도 (-1.0 ~ 1.0)
  - `VOLUME_DIVERGENCE`: [none, bullish, bearish]
  - `VOLUME_RELATIVE_STRENGTH`: 상대 거래량 비율

### 5. LOW_PRICE (지지선의 마법) ⭐⭐
**현재 상태**: 1개 파라미터 (period=20)
**도움말 발견 고급 기능**:
- [x] 다중 지지선 레벨 - 여러 기간의 저점 계층 분석
- [x] 지지선 강도 측정 - 테스트 횟수 및 반등 강도
- [x] 바닥 패턴 인식 - 더블바텀, 트리플바텀, 역헤드앤숄더
- [x] 지지선 이탈 감지 - 거래량 동반 여부 확인
- [x] ATR 기반 진입 - 저점 + ATR*0.5 이내 접근
- [x] 라운딩 바텀 패턴 - 6개월 이상 U자형 패턴
- [x] 통계적 저점 분석 - 히스토리컬 저점 백분위 계산

**분류 결과**:
- **Type A 파라미터 확장** (우선순위: 낮음):
  - `support_levels_count`: integer, 기본값 3, 범위 2-5
  - `strength_threshold`: float, 기본값 0.02, 범위 0.01-0.05
  - `pattern_recognition_enabled`: boolean, 기본값 false
- **Type B 새 변수 필요** (구현 복잡도: 높음):
  - `SUPPORT_STRENGTH`: 지지선 강도 점수 (0.0-1.0)
  - `BOTTOM_PATTERN_DETECTOR`: [none, double_bottom, triple_bottom, inverse_h&s, rounding]
  - `SUPPORT_BREAK_PROBABILITY`: 지지선 이탈 확률

## 🎯 **현실적인 즉시 실행 액션**

### **🚀 Step 1: ATR 정규화 파라미터 추가 (오늘)**

**구현 범위**: 기존 ATR 변수에 파라미터 1개만 추가
```sql
-- tv_variable_parameters 테이블에 추가
INSERT INTO tv_variable_parameters (
    variable_id, parameter_name, parameter_type, default_value,
    display_name_ko, description
) VALUES (
    'ATR', 'normalization_enabled', 'boolean', 'false',
    '정규화 사용', 'ATR을 가격 대비 백분율로 표시'
);
```

**계산 로직**: 기존 TriggerCalculator에 조건부 추가
```python
def calculate_atr(self, data, period=14, normalization_enabled=False):
    atr = self._basic_atr_calculation(data, period)
    if normalization_enabled:
        current_price = data['close'][-1]
        return (atr / current_price) * 100
    return atr
```

**UI 변경**: 기존 ATR 파라미터 패널에 체크박스 1개 추가

### **🎯 Step 2: 검증 및 테스트 (내일)**

**백테스팅 검증**:
1. 기존 ATR과 정규화 ATR 병행 테스트
2. `ATR > 50000` vs `ATR_NORMALIZED > 2.5` 비교
3. 계산 성능 영향 측정

**사용자 테스트**:
1. 트리거 빌더에서 정규화 옵션 선택 가능 확인
2. 조건 설정: `ATR (정규화) > 2.5` 형태로 표시
3. 백테스팅 결과에서 정상 동작 확인

### **⚡ Step 3: 성공시 점진적 확장 (3-5일 후)**

**다음 후보**: VOLUME 상대화 파라미터
- 계산: `VOLUME / VOLUME_SMA`
- 의미: "평균 대비 거래량 배율"
- 조건 예시: `VOLUME (상대) > 2.0` (평균의 2배)

## 🛠️ **현실적 구현 가이드라인**

### **Type A 파라미터 추가 허용 기준**
✅ **OK 조건:**
- 기존 변수에 단순 수식 추가 (±×÷ 수준)
- 파라미터 1-2개로 해결
- 일반 사용자 이해 가능
- API 호출 증가 없음
- 실시간 계산 부담 최소

❌ **NG 조건:**
- 복잡한 알고리즘 필요
- 과거 데이터 대량 분석
- 전문 지식 필요한 개념
- 성능 영향 큰 계산

### **Type B 새 변수 최소 기준**
✅ **허용:**
- 기존 OHLCV 데이터로 계산 가능
- 출력이 명확한 의미 (숫자/enum)
- 실시간 계산 가능
- 사용자가 이해할 수 있는 결과

❌ **금지:**
- 머신러닝/AI 모델
- 복잡한 패턴 인식
- 다이버전스 같은 고급 개념
- 대량 히스토리컬 데이터 필요

## 📊 **현실성 기반 우선순위 재조정**

### **🟢 즉시 구현 (1-2주) - 높은 현실성**

1. **ATR 정규화** (Type A 파라미터) ⭐⭐⭐
   - 파라미터: `normalization_enabled: boolean`
   - 계산: `(ATR / CURRENT_PRICE) * 100`
   - 사용자 이해: "변동성 백분율"
   - API 부담: 없음 (기존 데이터 활용)

2. **VOLUME 상대화** (Type A 파라미터) ⭐⭐⭐
   - 파라미터: `relative_calculation: boolean`
   - 계산: `VOLUME / VOLUME_SMA`
   - 사용자 이해: "평균 대비 거래량 배율"
   - API 부담: 없음

3. **RSI 스무딩** (Type A 파라미터) ⭐⭐
   - 파라미터: `smoothing_enabled: boolean`, `smoothing_period: 3`
   - 계산: RSI의 이동평균
   - 사용자 이해: "부드러운 RSI"

### **🟡 단기 검토 (3-4주) - 중간 현실성**

1. **ATR_REGIME** (Type B 단순 새 변수) ⭐⭐
   - 계산: ATR vs 50일 평균 비교
   - 출력: [low, normal, high, extreme]
   - 사용자 이해: "변동성 상태"

2. **VOLUME_SPIKE** (Type B 단순 새 변수) ⭐⭐
   - 계산: VOLUME / VOLUME_SMA 비율
   - 출력: spike_level (1.0-5.0)
   - 사용자 이해: "거래량 급증 수준"

### **🔴 장기 보류 - 낮은 현실성**

❌ **RSI_DIVERGENCE**: 추세선 분석 복잡, 사용자 이해 어려움
❌ **MACD_ML_PREDICTION**: 머신러닝 과도, 개인 시스템 부적합
❌ **PATTERN_RECOGNITION**: 패턴 인식 알고리즘 복잡
❌ **LSTM 기반 예측**: AI 모델 개인 시스템에 과도함

## 🔧 기술적 구현 가이드

### **파라미터 확장 표준 절차**
1. `tv_variable_parameters` 테이블에 새 파라미터 추가
2. 해당 변수의 Calculator 클래스 업데이트
3. UI Parameter Builder에서 새 파라미터 렌더링
4. 백테스팅 엔진에서 파라미터 적용

### **새 변수 추가 표준 절차**
1. `tv_trading_variables` 테이블에 새 변수 등록
2. 전용 Calculator 클래스 생성
3. `purpose_category`, `chart_category`, `comparison_group` 설정
4. UI Trigger Builder에서 선택 옵션 추가
5. 도움말 시스템에 설명 등록

## 📈 예상 결과

**1주 후**:
- [ ] 5개 변수 완전 분석 완료
- [ ] Type A/B 분류 기준 확정
- [ ] 첫 번째 고급 변수 프로토타입

**2주 후**:
- [ ] 핵심 변수 5개 강화 완료
- [ ] 고급 계산기 프레임워크 구축
- [ ] UI에서 새 기능 테스트 가능

**3주 후**:
- [ ] 22개 모든 변수 분석 완료
- [ ] 새로운 고급 변수 10-15개 추가
- [ ] 메타 변수 (Type C) 구현 시작

## 🚨 **현실성 검토 결과 - 중요한 제약사항들**

### **⚠️ 핵심 제약사항 (잊지 말아야 할 것들)**

1. **👤 사용자는 GUI에서 클릭으로 트리거 생성**
   - 파라미터 3개 이하 제한 (복잡도 관리)
   - 직관적 이해 가능한 개념만 허용
   - "정규화 ATR", "다이버전스" 등은 일반 사용자에게 어려움

2. **🔌 업비트 API 제약사항**
   - 제공: OHLCV, 현재가, 거래량, 호가
   - 미제공: RSI, MACD, ATR (직접 계산 필요)
   - Rate Limit: 초당 10회, 분당 600회
   - 과거 데이터: 200캔들까지만

3. **💾 DB 마켓 데이터 캐싱**
   - ✅ OHLCV 저장 가능
   - ✅ 기본 지표(RSI, MACD) 계산 후 저장
   - ⚠️ 복잡한 분석은 실시간 계산 부담
   - ❌ 머신러닝 모델은 과도함

### **🔄 현실적 3단계 접근법**

**🟢 Phase 1 (즉시 가능)**: Type A 파라미터만 - 기존 변수에 간단한 수식 추가
**🟡 Phase 2 (단기 구현)**: Type B 단순 새 변수 - 명확한 의미의 간단한 계산
**🔴 Phase 3 (장기 보류)**: Type B 복잡한 변수 - 머신러닝, 패턴인식 등

---

**다음 에이전트에게: 이 파일을 기준으로 ATR부터 차근차근 분석 시작하시면 됩니다! 🚀**
