# 볼린저 밴드 변수 개선 설계 문서

**현재 분량**: 0줄 / 600줄 (0% 사용) 🟢
**마지막 검토**: 2025-08-18
**다음 분할 예정**: 500줄 도달 시

## 📋 **현재 상태 분석**

### **기존 BOLLINGER_BAND 파라미터**
```yaml
period: 20 (5-100)
std_dev: 2.0 (1.0-3.0)
timeframe: position_follow | 1m | 3m | 5m | 10m | 15m | 30m | 1h | 4h | 1d | 1w | 1M
band_position: upper | middle | lower
```

### **기존 사용 시나리오**
```
조건: CURRENT_PRICE > BOLLINGER_BAND[upper]   # 상단 돌파
조건: CURRENT_PRICE < BOLLINGER_BAND[lower]   # 하단 터치
조건: BOLLINGER_BAND[upper] - BOLLINGER_BAND[lower] > 5000  # 밴드 폭 확장
```

### **현재 계산기 구조**
```python
# 위치: TriggerEvaluationService._calculate_bb_*()
def _calculate_bb_upper(self, variable, market_data):
    period = variable.parameters.get("period", 20)
    std_dev = variable.parameters.get("std_dev", 2.0)
    bb_upper = market_data.get_indicator_value("BB_UPPER", {"period": period, "std_dev": std_dev})

def _calculate_bb_middle(self, variable, market_data):
    # SMA 계산 (중앙선)

def _calculate_bb_lower(self, variable, market_data):
    # 하단선 계산
```

## 🎯 **밴드 폭(Band Width) 분석**

### **핵심 질문: 새로운 변수 vs 기존 확장?**

#### **현재 구조 제약사항**
- `band_position` 파라미터로 upper/middle/lower 중 **하나만** 선택
- 밴드 폭 = upper - lower 계산을 위해서는 **두 값이 동시에 필요**
- 현재 변수 시스템은 **단일 값 반환** 구조

#### **밴드 폭 계산 복잡도 분석**
```python
# 볼린저 밴드 폭 계산 (Band Width)
def calculate_bb_width(data, period=20, std_dev=2.0):
    # 1. SMA 계산 (50라인)
    sma = data['close'].rolling(window=period).mean()

    # 2. 표준편차 계산 (30라인)
    std = data['close'].rolling(window=period).std()

    # 3. 상단/하단 계산 (30라인)
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)

    # 4. 밴드 폭 계산 (20라인)
    band_width = upper - lower

    # 5. 정규화 밴드 폭 (40라인)
    normalized_width = band_width / sma * 100  # %BB Width

    # 6. ATR 확장 기능 적용 (200라인)
    # - 최저/최고/평균/이전값 계산
    # - 배율 적용
    # - 캐싱 및 최적화

    return band_width

# 예상 총 라인: 370라인 (600라인 이하, 적정 범위)
```

## 🔧 **설계 결정: 새로운 변수 추가**

### **✅ BB_WIDTH 새 변수 생성 추천**

#### **1. 기술적 근거**
- **단일 책임 원칙**: 각 변수는 하나의 명확한 의미
- **계산 복잡도**: BB_WIDTH는 독립적 계산 로직 (370라인)
- **사용자 직관성**: "밴드 폭"은 상단/하단과 다른 개념
- **확장성**: BB_WIDTH 전용 최적화 가능

#### **2. 코드 분량 검증**
```python
class BollingerBandWidthCalculator(BaseCalculator):
    """볼린저 밴드 폭 전용 계산기 - 370라인 예상"""

    def calculate(self, market_data, params):           # 30라인
        # ATR 확장 기능 메인 로직

    def _calculate_basic_width(self, data, period, std_dev):  # 130라인
        # 기본 밴드 폭 계산

    def _apply_calculation_method(self, width_series, params):  # 150라인
        # min/max/average/previous 계산

    def _apply_multiplier(self, value, multiplier_percent):     # 20라인
        # 배율 적용

    def _normalize_width(self, width, sma):             # 40라인
        # %BB Width 정규화
```

#### **3. 변수 메타데이터**
```yaml
BB_WIDTH:
  variable_id: BB_WIDTH
  display_name_ko: 볼린저 밴드 폭
  display_name_en: Bollinger Band Width
  purpose_category: volatility
  chart_category: subplot
  comparison_group: volatility_comparable
  description: 볼린저 밴드 상단과 하단 사이의 거리 (변동성 지표)
```

#### **4. 파라미터 구조**
```sql
-- BB_WIDTH 전용 파라미터
INSERT INTO tv_variable_parameters VALUES
('BB_WIDTH', 'period', 'integer', '20', '5', '100', NULL, NULL),
('BB_WIDTH', 'std_dev', 'decimal', '2.0', '1.0', '3.0', NULL, NULL),
('BB_WIDTH', 'timeframe', 'enum', 'position_follow', NULL, NULL,
 '["position_follow", "1m", "5m", "15m", "1h", "4h", "1d"]', NULL),
('BB_WIDTH', 'calculation_method', 'enum', 'basic', NULL, NULL,
 '["basic", "previous", "min", "max", "average"]', '["기본", "이전값", "최저값", "최고값", "평균값"]'),
('BB_WIDTH', 'calculation_period', 'integer', '5', '1', '50', NULL, NULL),
('BB_WIDTH', 'multiplier_percent', 'float', '100.0', '50.0', '200.0', NULL, NULL),
('BB_WIDTH', 'normalization', 'enum', 'absolute', NULL, NULL,
 '["absolute", "percentage"]', '["절대값", "백분율"]');
```

## 🚀 **BB_WIDTH 활용 시나리오**

### **시나리오 1: 변동성 수축 감지 (스퀴즈)**
```yaml
설정:
- 계산방식: min (20일 최저 밴드폭)
- 기간: 20일
- 배율: 120%
- 정규화: percentage

조건: BB_WIDTH < BB_WIDTH(20일최저, 120%, 백분율)
의미: 현재 밴드폭이 최근 20일 최저의 120%보다 작을 때 (극도 수축)
```

### **시나리오 2: 변동성 급증 감지 (익스팬션)**
```yaml
설정:
- 계산방식: average (10일 평균 밴드폭)
- 기간: 10일
- 배율: 150%
- 정규화: absolute

조건: BB_WIDTH > BB_WIDTH(10일평균, 150%, 절대값)
의미: 현재 밴드폭이 최근 10일 평균의 150%보다 클 때 (급격한 확장)
```

### **시나리오 3: 변동성 정상화 확인**
```yaml
설정:
- 계산방식: previous (5일전 밴드폭)
- 기간: 5일
- 배율: 100%
- 정규화: percentage

조건: BB_WIDTH > BB_WIDTH(5일전, 100%, 백분율)
의미: 밴드폭이 5일전보다 증가 (변동성 정상화)
```

## ⚖️ **대안: 기존 BOLLINGER_BAND 확장**

### **❌ 기존 변수 확장시 문제점**

#### **1. 파라미터 복잡성 폭증**
```yaml
# 기존에 추가되어야 할 파라미터들
band_calculation_target: width | upper | lower | middle
width_normalization: absolute | percentage
calculation_method: basic | min | max | average | previous
calculation_period: 1-50
multiplier_percent: 50.0-200.0

# 총 파라미터: 기존 4개 + 신규 5개 = 9개
# UI 복잡도 급증, 사용자 혼란 야기
```

#### **2. 계산 로직 분기 복잡성**
```python
def calculate_bollinger_band(self, params):
    if params['band_calculation_target'] == 'width':
        # 밴드 폭 계산 (200라인)
        if params['width_normalization'] == 'percentage':
            # 정규화 로직 (50라인)
        # ATR 확장 적용 (200라인)
    elif params['band_calculation_target'] == 'upper':
        # 상단 계산 (100라인)
        # ATR 확장 적용 (200라인)
    # ... 기타 분기들

# 예상 총 라인: 750+ 라인 (600라인 초과!)
```

#### **3. 테스트 복잡도**
```python
# 테스트 케이스 폭증
test_bollinger_upper()              # 기존
test_bollinger_lower()              # 기존
test_bollinger_middle()             # 기존
test_bollinger_width_absolute()     # 신규
test_bollinger_width_percentage()   # 신규
test_bollinger_width_min()          # 신규
test_bollinger_width_max()          # 신규
test_bollinger_width_average()      # 신규
test_bollinger_width_previous()     # 신규
test_bollinger_width_multiplier()   # 신규

# 테스트 파일도 600라인 초과 예상
```

## 💡 **최종 설계 결론**

### **✅ BB_WIDTH 새 변수 생성이 최적**

#### **핵심 근거 3가지**
1. **LLM 친화적**: 단일 파일 600라인 이하 유지
2. **단일 책임**: 각 변수가 명확한 단일 목적
3. **확장성**: 독립적 개발/테스트/최적화 가능

#### **구현 우선순위**
```
Phase 1: BB_WIDTH 기본 계산기 (1주)
- 기본 밴드 폭 계산
- 절대값/백분율 정규화
- 기본 파라미터 UI

Phase 2: ATR 확장 기능 적용 (1주)
- calculation_method (min/max/average/previous)
- calculation_period (1-50)
- multiplier_percent (50-200%)

Phase 3: 통합 테스트 및 최적화 (3일)
- 성능 최적화
- 캐싱 구현
- 백테스팅 검증
```

## 🔄 **기존 BOLLINGER_BAND 변수 영향**

### **✅ 기존 변수 호환성 보장**
- **기존 파라미터**: 변경 없음 (period, std_dev, timeframe, band_position)
- **기존 사용법**: 100% 호환성 유지
- **기존 전략**: 영향 없음

### **🚀 새로운 조합 전략 가능**
```python
# 볼린저 밴드 + 밴드 폭 조합 전략
진입 조건 1: CURRENT_PRICE < BOLLINGER_BAND[lower]        # 하단 터치
진입 조건 2: BB_WIDTH < BB_WIDTH(20일최저, 110%)          # 밴드 수축 확인
→ 스퀴즈 후 하단 터치시 강력한 반등 기대

출구 조건: BB_WIDTH > BB_WIDTH(5일평균, 150%)             # 밴드 급확장
→ 변동성 급증시 수익 실현
```

## 📊 **구현 로드맵**

### **Week 1: BB_WIDTH 기본 구현**
```python
# 파일: volatility/bb_width_calculator.py (370라인)
class BollingerBandWidthCalculator(BaseCalculator):
    def calculate(self, market_data, params):
        # 메인 계산 로직

    def _calculate_basic_width(self, data, period, std_dev):
        # 기본 밴드 폭 계산

    def _normalize_width(self, width, sma, method):
        # 정규화 (절대값/백분율)
```

### **Week 2: ATR 확장 기능 통합**
```python
# ATR 확장 메서드 추가
def _apply_calculation_method(self, width_series, params):
    # min/max/average/previous 구현

def _apply_multiplier(self, value, multiplier_percent):
    # 배율 적용
```

### **Week 3: UI 및 테스트**
```python
# UI: ParameterWidgetFactory 확장
def create_bb_width_widgets(self, params):
    # 정규화 콤보박스 추가
    # 기타 ATR 확장 위젯
```

## 🎯 **성공 기준**

### **기능적 요구사항**
- [ ] BB_WIDTH 기본 계산 (절대값/백분율)
- [ ] ATR 확장 기능 완전 적용
- [ ] 기존 BOLLINGER_BAND와 독립적 동작
- [ ] 7규칙 전략에서 활용 가능

### **비기능적 요구사항**
- [ ] 단일 파일 600라인 이하
- [ ] 계산 성능 기존 대비 유사
- [ ] UI 응답성 300ms 이하
- [ ] 백테스팅 정확도 99% 이상

---

**결론**: BB_WIDTH를 새로운 독립 변수로 생성하는 것이 **구조적/성능적/유지보수** 모든 측면에서 최적의 설계입니다. 🚀
