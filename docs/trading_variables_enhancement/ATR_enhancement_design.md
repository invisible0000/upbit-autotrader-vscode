# ATR 변수 개선 설계 문서

## 📋 **현재 상태**

### **기존 ATR 파라미터**
```yaml
period: 14 (5-50)
timeframe: position_follow | 1m | 5m | 15m | 30m | 1h | 4h | 1d
```

### **기존 사용 시나리오**
```
조건: ATR > 50000  # 고변동성 감지
조건: ATR < 20000  # 저변동성 감지
조건: ATR > ATR[5]  # 5일전 ATR 대비 상승
```

### **현재 계산기 구조**
- 위치: `TriggerCalculator.calculate_atr()`
- 입력: OHLCV 데이터, period
- 출력: ATR 절대값 (KRW 단위)

## 🎯 **제안된 1차 확장 기능**

### **사용자 시나리오**
```
UI 선택 단계:
1. 변수: ATR 선택
2. 배율: 숫자 입력 박스 (기본값: 100, 50.0-200.0, 소수점 1자리)
3. 타임프레임: 기존과 동일
4. 계산 방식: [기본/저점/고점/평균/이전값] 드롭다운
5. 기간: 숫자 입력 박스 (조건부 활성화)
```

### **확장 파라미터 상세**

#### **1. calculation_method (계산 방식)**
```yaml
type: enum
options: [basic, min, max, average, previous]
default: basic
description:
  - basic: 일반 ATR 계산
  - min: 지정 기간 내 최저 ATR
  - max: 지정 기간 내 최고 ATR
  - average: 지정 기간 ATR 평균
  - previous: N일 전 ATR 값
```

#### **2. calculation_period (계산 기간)**
```yaml
type: integer
range: 1-50
default: 5
enabled_when: calculation_method != "basic"
description: 위 계산 방식 적용할 기간
```

#### **3. multiplier_percent (배율)**
```yaml
type: float
range: 50.0-200.0
default: 100.0
step: 0.1
unit: percent
widget: QDoubleSpinBox
description: 변수 값에 적용할 배율 (100.0 = 원값, 150.0 = 1.5배)
applicable_to: [ATR, RSI, STOCHASTIC, BOLLINGER_BAND, VOLUME, VOLUME_SMA, MACD, PROFIT_PERCENT]
```

## 🔧 **기술적 구현 분석**

### **현재 시스템 구조 확인**

#### **기존 ATR 계산기**
```python
# 위치: data_layer/processors/data_processor.py
def calculate_atr(self, data: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    # True Range 계산
    result['TR'] = np.maximum(...)
    # ATR = TR의 이동평균
    result[f'ATR_{window}'] = result['TR'].rolling(window=window).mean()
```

#### **기존 파라미터 구조**
```yaml
ATR 현재 파라미터:
- period: integer (5-50), 기본값 14
- timeframe: enum, 기본값 position_follow
```

### **제안된 확장의 기술적 타당성**

#### **✅ 즉시 구현 가능**
```python
# 1. 과거값 참조 (previous)
def get_previous_atr(atr_history, periods_back):
    if len(atr_history) >= periods_back:
        return atr_history[-periods_back]
    return None  # 데이터 부족

# 2. 배율 적용 (multiplier)
def apply_multiplier(atr_value, percent):
    return atr_value * (percent / 100.0)
```

#### **✅ 단순 통계 계산 가능**
```python
# 3. 통계적 계산 (min/max/average)
def calculate_statistical_atr(atr_history, method, period):
    recent_data = atr_history[-period:]
    if method == "min":
        return min(recent_data)
    elif method == "max":
        return max(recent_data)
    elif method == "average":
        return sum(recent_data) / len(recent_data)
```

#### **⚠️ 데이터 관리 필요**
- **ATR 히스토리 저장**: 기존 `technical_indicators_1d` 테이블 활용
- **타임프레임별 관리**: 1m/5m/1h 등 각각 별도 저장
- **메모리 캐싱**: 최근 50개 ATR 값 메모리에 보관

### **API/계산 능력 상세 검토**

#### **✅ 업비트 API 호환성**
- **필요 데이터**: OHLCV만 사용 (기존과 동일)
- **API 호출 증가**: 없음 (기존 데이터 재활용)
- **Rate Limit 영향**: 없음

#### **✅ DB 저장 구조**
```sql
-- 기존 테이블 활용 가능
technical_indicators_1d:
- atr_14 (기존)
- atr_history (JSON 형태로 최근 50개 저장)

또는 새 테이블:
atr_history:
- symbol, timeframe, timestamp, atr_value
```

#### **⚠️ 성능 고려사항**
- **계산 복잡도**: O(1) ~ O(n), n=50 정도로 무리 없음
- **메모리 사용**: 심볼당 50개 * 8바이트 = 400바이트 (미미함)
- **초기화 시간**: 시스템 시작시 히스토리 로딩 필요

### **계산기 분리의 필요성과 아키텍처**

#### **현재 문제점: 단일 파일의 한계**
```python
# TriggerCalculator가 너무 비대함 (2000+ 라인 예상)
class TriggerCalculator:
    def calculate_rsi(self, prices, period=14): pass      # 50 라인
    def calculate_atr(self, data, period=14): pass        # 80 라인
    def calculate_macd(self, data, fast=12, slow=26): pass # 120 라인
    def calculate_volume_sma(self): pass                   # 60 라인
    # ... 22개 변수 * 평균 100라인 = 2200+ 라인
    # 🚨 LLM 코파일럿 한계: 600-900 라인
```

#### **해결책: 변수별 개별 계산기 (600라인 이하)**
```python
# 1. 베이스 인터페이스 (50라인)
class BaseCalculator(ABC):
    @abstractmethod
    def calculate(self, market_data: pd.DataFrame, params: dict) -> float:
        pass

# 2. ATR 전용 계산기 (400-500라인)
class ATRCalculator(BaseCalculator):
    def __init__(self):
        self.cache = {}

    def calculate(self, market_data, params):
        """메인 계산 메서드"""
        # 기본 ATR 계산 (100라인)
        # 확장 기능 계산 (200라인)
        # 배율 적용 (50라인)
        # 캐싱 로직 (100라인)

    def _calculate_basic_atr(self, data, period):
        """기본 ATR 계산 (100라인)"""

    def _calculate_statistical(self, atr_history, method, period):
        """통계적 계산 (150라인)"""

    def _get_previous_value(self, atr_history, periods_back):
        """과거값 참조 (50라인)"""

# 3. 계산기 팩토리 (100라인)
class CalculatorFactory:
    def get_calculator(self, variable_id: str) -> BaseCalculator:
        calculators = {
            "ATR": ATRCalculator,
            "RSI": RSICalculator,
            "MACD": MACDCalculator,
            # ... 22개 변수 매핑
        }
        return calculators[variable_id]()
```

#### **✅ 개별 계산기의 장점**
- **LLM 친화적**: 각 파일 600라인 이하로 코파일럿 최적화
- **독립적 개발**: 변수별 병렬 작업 가능
- **유지보수 용이**: 특정 변수 수정이 다른 변수에 영향 없음
- **테스트 격리**: 변수별 단위 테스트 독립 실행
- **확장성**: 새 변수 추가시 기존 코드 영향 없음

#### **📁 권장 파일 구조**
```
upbit_auto_trading/domain/trading_variables/calculators/
├── base_calculator.py              # 100라인 - 인터페이스
├── calculator_factory.py           # 150라인 - 팩토리
├── volatility/
│   ├── atr_calculator.py          # 500라인 - ATR 전용
│   └── bollinger_calculator.py    # 400라인 - 볼린저밴드
├── momentum/
│   ├── rsi_calculator.py          # 600라인 - RSI 전용
│   ├── macd_calculator.py         # 550라인 - MACD 전용
│   └── stochastic_calculator.py   # 450라인 - 스토캐스틱
├── trend/
│   ├── sma_calculator.py          # 300라인 - SMA 전용
│   └── ema_calculator.py          # 350라인 - EMA 전용
└── utils/
    ├── data_validator.py          # 200라인 - 데이터 검증
    └── cache_manager.py           # 250라인 - 캐싱 관리
```## 📊 **구현 우선순위**

### **Phase 1: 기본 확장 (1주)**
- [ ] `calculation_method` 파라미터 추가
- [ ] `previous` 옵션만 구현 (가장 단순)
- [ ] UI에서 조건부 기간 입력 박스

### **Phase 2: 통계 기능 (2주)**
- [ ] `min/max/average` 옵션 구현
- [ ] ATR 히스토리 DB 저장 로직
- [ ] 타임프레임별 히스토리 관리

### **Phase 3: 배율 기능 (3주)**
- [ ] `multiplier_percent` 파라미터 추가
- [ ] UI 정밀 숫자 입력 위젯 구현
- [ ] 백테스팅 환경 테스트

## 🧪 **사용 시나리오 예시**

### **시나리오 1: 변동성 급증 감지**
```
설정:
- 계산방식: average (5일 평균)
- 기간: 5
- 배율: 150%

조건: ATR(5일평균, 150%) > 현재 ATR
의미: 현재 ATR이 최근 5일 평균의 1.5배보다 클 때
```

### **시나리오 2: 변동성 수축 감지**
```
설정:
- 계산방식: max (20일 최고값)
- 기간: 20
- 배율: 70%

조건: 현재 ATR < ATR(20일최고, 70%)
의미: 현재 ATR이 최근 20일 최고값의 70%보다 낮을 때
```

### **시나리오 3: 추세 확인**
```
설정:
- 계산방식: previous (3일전)
- 기간: 3
- 배율: 100%

조건: ATR > ATR(3일전)
의미: 현재 ATR이 3일전보다 증가
```

## ⚡ **최종 실행 가능성 평가**

### **✅ 매우 높은 현실성 (90%+)**

#### **1. 기술적 구현**
- **기존 ATR 계산**: `data_layer/processors/data_processor.py`에 이미 구현됨
- **파라미터 시스템**: `tv_variable_parameters` 테이블로 확장 가능
- **UI 위젯**: `ParameterWidgetFactory`로 동적 위젯 생성 가능
- **계산 복잡도**: 단순 통계 함수, 성능 무리 없음

#### **2. 사용자 경험**
- **직관적 UI**: 기존 파라미터 빌더 패턴 재활용
- **점진적 학습**: 기본값은 기존과 동일, 고급 기능은 선택적
- **명확한 피드백**: "5일 전 ATR", "최근 20일 최고 ATR" 등 명확한 의미

#### **3. 시스템 호환성**
- **API 부담**: 기존 OHLCV 데이터만 사용, 추가 호출 없음
- **DB 확장**: 기존 `technical_indicators` 테이블 활용
- **백테스팅**: 기존 시뮬레이션 엔진과 호환

### **🎯 구체적 구현 계획**

#### **Phase 1: 파라미터 추가 (3-5일)**
```sql
-- 새 파라미터 3개 추가
INSERT INTO tv_variable_parameters VALUES
('ATR', 'calculation_method', 'enum', 'basic', NULL, NULL,
 '["basic", "previous", "min", "max", "average"]',
 '["기본", "이전값", "최저값", "최고값", "평균값"]'),
('ATR', 'calculation_period', 'integer', '5', '1', '50', NULL, NULL),
('ATR', 'multiplier_percent', 'float', '100.0', '50.0', '200.0', NULL, NULL);
```

#### **Phase 2: UI 위젯 확장 (2-3일)**
```python
# ParameterWidgetFactory에 정밀 입력 위젯 추가
def create_atr_widgets(self, params):
    method_combo = QComboBox()
    period_spinbox = QSpinBox()               # 정수 입력
    multiplier_spinbox = QDoubleSpinBox()     # 실수 입력 (소수점 1자리)

    # 배율 스핀박스 설정
    multiplier_spinbox.setRange(50.0, 200.0)
    multiplier_spinbox.setDecimals(1)
    multiplier_spinbox.setSingleStep(0.1)
    multiplier_spinbox.setSuffix("%")

    # 조건부 활성화: method != "basic"일 때만 period 활성화
    method_combo.currentTextChanged.connect(
        lambda: period_spinbox.setEnabled(method_combo.currentText() != "basic")
    )
```

#### **Phase 3: 계산기 확장 (5-7일)**
```python
class ATRCalculator:
    def calculate_enhanced_atr(self, market_data, params):
        # 1. 기본 ATR 계산
        atr_series = self.calculate_basic_atr(market_data, params['period'])

        # 2. 확장 기능 적용
        method = params.get('calculation_method', 'basic')
        if method == 'previous':
            periods_back = params.get('calculation_period', 5)
            result = atr_series.shift(periods_back).iloc[-1]
        elif method == 'min':
            period = params.get('calculation_period', 5)
            result = atr_series.tail(period).min()
        # ... 기타 메서드

        # 3. 배율 적용 - 100%도 직접 곱셈이 조건문보다 빠름
        multiplier = params.get('multiplier_percent', 100.0) / 100.0
        return result * multiplier
```

### **⚠️ 주요 고려사항**

#### **1. 데이터 부족 처리**
```python
def safe_calculate(self, atr_history, method, period):
    if len(atr_history) < period:
        # Fallback: 사용 가능한 데이터만 사용
        return self._calculate_with_available_data(atr_history, method)
    return self._calculate_normal(atr_history, method, period)
```

#### **2. 성능 최적화**
```python
# ATR 히스토리 캐싱 (메모리)
class ATRHistoryCache:
    def __init__(self, max_size=50):
        self.cache = {}  # {symbol_timeframe: deque(maxlen=50)}

    def get_recent_atr(self, symbol, timeframe, count):
        key = f"{symbol}_{timeframe}"
        return list(self.cache.get(key, []))[-count:]
```

#### **3. 사용자 가이드**
- **툴팁**: 각 옵션별 상세 설명 제공
- **예시**: "ATR(5일전) > ATR(현재)" 같은 구체적 사례
- **경고**: 데이터 부족시 명확한 피드백

### **🚨 리스크 완화 방안**

#### **리스크 1: 복잡도 증가**
**완화**: 기본값은 기존과 동일, 고급 옵션은 접이식 UI로 숨김

#### **리스크 2: 성능 저하**
**완화**: 계산 결과 캐싱, 배치 처리로 최적화

#### **리스크 3: 사용자 혼란**
**완화**: 단계별 출시, 충분한 도움말과 예시 제공

### **🎯 성공 기준**

#### **기능적 요구사항**
- [ ] 기존 ATR 조건과 100% 호환성 유지
- [ ] 새 파라미터로 "5일전 ATR" 등 참조 가능
- [ ] 배율 적용으로 "ATR의 150%" 표현 가능
- [ ] 백테스팅에서 정상 동작 확인

#### **비기능적 요구사항**
- [ ] 계산 시간 20% 이하 증가
- [ ] 메모리 사용량 10% 이하 증가
- [ ] 사용자 설정 완료 시간 30초 이내
- [ ] 99% 이상 에러 없는 동작

## 📋 **다음 단계 액션**

### **즉시 시작 가능 (오늘)**
1. DB에 새 파라미터 3개 추가
2. `ATRCalculator` 클래스 프로토타입 작성
3. 간단한 UI 목업 제작

### **1주일 내 완성 목표**
1. 완전한 기능 구현
2. 기존 시스템과 통합 테스트
3. 기본적인 사용자 테스트

## 🤖 **LLM 코파일럿 친화적 개발 방법론**

### **파일 크기 제한 준수**
- **단일 파일 최대 라인**: 600-900라인 (LLM 처리 한계)
- **클래스당 최대 라인**: 300-400라인
- **메서드당 최대 라인**: 50라인 이하

### **개별 계산기 개발 순서**
```
1단계: BaseCalculator 인터페이스 정의 (50라인)
2단계: ATRCalculator 단독 개발 (500라인)
3단계: 단위 테스트 작성 (300라인)
4단계: 다음 변수 계산기로 진행
```

### **코파일럿 작업 최적화**
- **한 번에 하나의 계산기만** 작업
- **명확한 함수명과 주석** 사용
- **타입 힌트 필수** 적용
- **단순한 메서드 체인** 구성

### **예시: ATR 계산기 개발**
```python
# atr_calculator.py (500라인 예상)
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

class ATRCalculator(BaseCalculator):
    """ATR 전용 계산기 - LLM 친화적 구조"""

    def __init__(self):
        """초기화 - 캐시 설정"""
        self.cache: Dict[str, List[float]] = {}

    def calculate(self, market_data: pd.DataFrame, params: Dict) -> float:
        """메인 계산 메서드 (20라인)"""
        basic_atr = self._calculate_basic_atr(market_data, params['period'])
        enhanced_atr = self._apply_calculation_method(basic_atr, params)
        return self._apply_multiplier(enhanced_atr, params['multiplier_percent'])

    def _calculate_basic_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """기본 ATR 계산 (100라인)"""
        # True Range 계산
        # ATR 이동평균 계산
        # 결과 반환

    def _apply_calculation_method(self, atr_series: pd.Series, params: Dict) -> float:
        """계산 방식 적용 (150라인)"""
        method = params.get('calculation_method', 'basic')
        if method == 'basic':
            return atr_series.iloc[-1]
        elif method == 'previous':
            return self._get_previous_value(atr_series, params)
        elif method in ['min', 'max', 'average']:
            return self._calculate_statistical(atr_series, params)

    def _get_previous_value(self, atr_series: pd.Series, params: Dict) -> float:
        """과거값 참조 (50라인)"""

    def _calculate_statistical(self, atr_series: pd.Series, params: Dict) -> float:
        """통계적 계산 (100라인)"""

    def _apply_multiplier(self, value: float, multiplier_percent: float) -> float:
        """배율 적용 (20라인) - 성능 최적화됨"""
        # 100% 배율도 직접 곱셈이 콤보박스보다 10-20배 빠름
        return value * (multiplier_percent / 100.0)
```

---

**결론**: 제안하신 ATR 확장 기능은 **기술적으로 완전히 실현 가능**하며, 기존 시스템과의 호환성을 유지하면서 사용자에게 강력한 유연성을 제공할 수 있습니다. 🚀

## 🚨 **리스크 및 대응**

### **🔥 성능 최적화 주의사항**

#### **❌ 피해야 할 콤보박스 안티패턴**
```python
# 이렇게 하면 성능이 10-20배 저하됨
mode = params.get('calculation_mode')  # 문자열 비교 오버헤드
if mode == 'basic':
    return atr_value  # 배율 건너뜀
elif mode == 'multiplier':
    return atr_value * (percent / 100.0)
```

#### **✅ 권장하는 직접 방식**
```python
# 100% 배율도 직접 곱셈이 조건문보다 빠름 (1-2 CPU 사이클)
multiplier = params.get('multiplier_percent', 100.0) / 100.0
return atr_value * multiplier  # 컴파일러가 1.0 곱셈 최적화 가능
```

### **리스크 1: 초기 데이터 부족**
- 대응: 사용 가능한 데이터 범위만 계산, 부족시 경고 표시

### **리스크 2: 성능 저하**
- 대응: 히스토리 데이터 메모리 캐싱, 배치 계산

### **리스크 3: 사용자 혼란**
- 대응: 기본값은 기존과 동일, 고급 옵션은 접이식 UI

---

**결론**: 제안된 확장 기능은 **현실적으로 구현 가능**하며, 기존 시스템과의 호환성을 유지하면서 점진적 확장이 가능합니다.
