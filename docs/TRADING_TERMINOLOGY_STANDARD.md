# 🎯 트레이딩 지표 용어 표준화 문서

## 📌 목적
- 모든 코드에서 일관된 지표 용어 사용
- 호환성 검증 로직의 정확성 보장
- 개발자 간 커뮤니케이션 효율성 향상

---

## 🏷️ 변수 ID 표준 규칙

### **1. 기본 원칙**
- **변수 ID**: 모두 **대문자 + 언더스코어** 형태 (`SMA`, `RSI`, `MACD`)
- **카테고리**: 모두 **소문자** 형태 (`price_overlay`, `oscillator`)
- **표시명**: **한글** 사용자 친화적 이름 (`단순이동평균`, `RSI 지표`)

### **2. 대소문자 규칙**
```yaml
변수_ID_형태: "SMA"           # 코드 내부 식별자
표시명_형태: "단순이동평균"    # UI 표시용
검색키_형태: "sma"           # 소문자 검색/매핑용
```

---

## 📊 기술지표 표준 용어집

### **� 카테고리 분류 체계**
**이중 카테고리 시스템**: 용도별 + 차트 출력별로 분류

| 변수 ID | 한글 표시명 | 영문명 | 용도 카테고리 | 차트 카테고리 | 활성화 | 설명 |
|---------|-------------|--------|--------------|--------------|-------|------|

### **�🔸 이동평균 계열**
| 변수 ID | 한글 표시명 | 영문명 | 용도 카테고리 | 차트 카테고리 | 활성화 | 설명 |
|---------|-------------|--------|--------------|--------------|-------|------|
| `SMA` | 단순이동평균 | Simple Moving Average | `trend` | `price_overlay` | ✅ | 일정 기간 가격의 산술평균 |
| `EMA` | 지수이동평균 | Exponential Moving Average | `trend` | `price_overlay` | ✅ | 최근 가격에 더 큰 가중치 |
| `WMA` | 가중이동평균 | Weighted Moving Average | `trend` | `price_overlay` | 🚧 | 선형 가중치 적용 이동평균 |
| `HMA` | 헐 이동평균 | Hull Moving Average | `trend` | `price_overlay` | 🚧 | 매우 부드럽고 반응이 빠른 이동평균 |
| `TEMA` | 3중 지수 이평 | Triple EMA | `trend` | `price_overlay` | 🚧 | 지연을 최소화한 이동평균 |

### **🔸 오실레이터 계열**
| 변수 ID | 한글 표시명 | 영문명 | 용도 카테고리 | 차트 카테고리 | 활성화 | 설명 |
|---------|-------------|--------|--------------|--------------|-------|------|
| `RSI` | RSI 지표 | Relative Strength Index | `momentum` | `oscillator` | ✅ | 상대강도지수 (0-100 범위) |
| `STOCH` | 스토캐스틱 | Stochastic Oscillator | `momentum` | `oscillator` | ✅ | %K, %D 라인 오실레이터 |
| `CCI` | CCI 지표 | Commodity Channel Index | `momentum` | `oscillator` | 🚧 | 상품채널지수 |
| `WILLIAMS_R` | 윌리엄스 %R | Williams %R | `momentum` | `oscillator` | 🚧 | 스토캐스틱과 유사한 과매수/과매도 |
| `STOCH_RSI` | 스토캐스틱 RSI | Stochastic RSI | `momentum` | `oscillator` | 🚧 | RSI에 스토캐스틱 적용 |

### **🔸 모멘텀 신호 계열**
| 변수 ID | 한글 표시명 | 영문명 | 용도 카테고리 | 차트 카테고리 | 활성화 | 설명 |
|---------|-------------|--------|--------------|--------------|-------|------|
| `MACD` | MACD 지표 | MACD | `momentum` | `signal_line` | ✅ | 이동평균수렴확산 |
| `DMI` | DMI 지표 | Directional Movement Index | `momentum` | `signal_line` | 🚧 | 방향성 지수 |
| `ADX` | ADX 지표 | Average Directional Index | `momentum` | `signal_line` | 🚧 | 평균방향지수 |
| `AO` | 어썸 오실레이터 | Awesome Oscillator | `momentum` | `signal_line` | 🚧 | 5기간과 34기간 SMA 차이 |

### **🔸 가격 데이터**
| 변수 ID | 한글 표시명 | 영문명 | 용도 카테고리 | 차트 카테고리 | 활성화 | 설명 |
|---------|-------------|--------|--------------|--------------|-------|------|
| `CURRENT_PRICE` | 현재가 | Current Price | `price` | `price_data` | ✅ | 실시간 거래가격 |
| `OPEN_PRICE` | 시가 | Open Price | `price` | `price_data` | ✅ | 봉 시작 가격 |
| `HIGH_PRICE` | 고가 | High Price | `price` | `price_data` | ✅ | 봉 최고 가격 |
| `LOW_PRICE` | 저가 | Low Price | `price` | `price_data` | ✅ | 봉 최저 가격 |
| `VWAP` | 거래량가중평균 | VWAP | `price` | `price_overlay` | 🚧 | 거래량 가중 평균 가격 |

### **🔸 변동성 지표**
| 변수 ID | 한글 표시명 | 영문명 | 용도 카테고리 | 차트 카테고리 | 활성화 | 설명 |
|---------|-------------|--------|--------------|--------------|-------|------|
| `BOLLINGER_BAND` | 볼린저밴드 | Bollinger Bands | `volatility` | `price_overlay` | ✅ | 표준편차 기반 밴드 |
| `ATR` | ATR 지표 | Average True Range | `volatility` | `indicator_subplot` | 🚧 | 평균진폭 (변동성) |
| `BOLLINGER_WIDTH` | 볼밴 폭 | Bollinger Band Width | `volatility` | `indicator_subplot` | 🚧 | 밴드 폭으로 변동성 측정 |
| `KELTNER_CHANNELS` | 켈트너 채널 | Keltner Channels | `volatility` | `price_overlay` | 🚧 | ATR 기반 채널 |

### **🔸 거래량 지표**
| 변수 ID | 한글 표시명 | 영문명 | 용도 카테고리 | 차트 카테고리 | 활성화 | 설명 |
|---------|-------------|--------|--------------|--------------|-------|------|
| `VOLUME` | 거래량 | Volume | `volume` | `volume_subplot` | ✅ | 거래량 데이터 |
| `VOLUME_MA` | 거래량 이평 | Volume Moving Average | `volume` | `volume_subplot` | 🚧 | 거래량 이동평균 |
| `OBV` | 온밸런스 볼륨 | On-Balance Volume | `volume` | `indicator_subplot` | 🚧 | 거래량 흐름 지표 |
| `MFI` | 자금흐름지수 | Money Flow Index | `volume` | `oscillator` | 🚧 | 거래량 기반 RSI |

---

## 🎨 카테고리 분류 기준

### **🏷️ 용도 카테고리 (Purpose Category)**
비즈니스 로직에서 사용하는 카테고리 - **호환성 검증의 기준**

#### **📈 trend (추세)**
- **용도**: 가격의 방향성과 추세를 파악
- **호환성**: 같은 추세 지표끼리 호환
- **예시**: SMA, EMA, WMA, HMA, TEMA

#### **⚡ momentum (모멘텀)**
- **용도**: 가격 변화의 속도와 강도를 측정
- **호환성**: 모멘텀 지표끼리 호환
- **예시**: RSI, STOCH, MACD, CCI, Williams %R

#### **🔥 volatility (변동성)**
- **용도**: 가격의 불확실성과 변동폭을 측정
- **호환성**: 변동성 지표끼리 호환
- **예시**: ATR, 볼린저밴드, 표준편차, 볼린저밴드폭

#### **📦 volume (거래량)**
- **용도**: 거래량과 자금 흐름을 분석
- **호환성**: 거래량 지표끼리 호환
- **예시**: VOLUME, OBV, MFI, CMF

#### **💰 price (가격)**
- **용도**: 원시 가격 데이터 및 가격 기반 계산
- **호환성**: 가격 데이터끼리 호환
- **예시**: 현재가, 시가, 고가, 저가, VWAP

---

### **📊 차트 카테고리 (Chart Display Category)**
UI에서 차트 표시 방식을 결정하는 카테고리

#### **� price_overlay (가격 오버레이)**
- **표시**: 메인 가격 차트에 오버레이
- **스케일**: 가격과 동일한 Y축 사용
- **예시**: SMA, EMA, 볼린저밴드, 켈트너채널

#### **📊 price_data (가격 데이터)**
- **표시**: 메인 가격 차트 (OHLC 캔들)
- **스케일**: 가격 단위
- **예시**: 현재가, 시가, 고가, 저가

#### **� oscillator (오실레이터)**
- **표시**: 별도 서브플롯 (고정 범위)
- **스케일**: 0-100% 또는 -100~+100
- **예시**: RSI, 스토캐스틱, CCI, MFI

#### **⚡ signal_line (신호선)**
- **표시**: 별도 서브플롯 (중앙선 기준)
- **스케일**: 0 중심선 또는 신호선 기준
- **예시**: MACD, ADX, DMI, AO

#### **� indicator_subplot (지표 서브플롯)**
- **표시**: 별도 서브플롯 (가변 범위)
- **스케일**: 지표별 고유 범위
- **예시**: ATR, 볼린저밴드폭, OBV

#### **📦 volume_subplot (거래량 서브플롯)**
- **표시**: 별도 거래량 전용 서브플롯
- **스케일**: 거래량 단위
- **예시**: VOLUME, 거래량 이동평균

---

### **✅ 활성화 상태**
- **✅ 활성**: 현재 구현 완료되어 사용 가능한 지표
- **🚧 개발중**: 정의되었지만 아직 구현되지 않은 지표
- **🔍 계획**: 향후 추가 예정인 지표
- **❌ 비활성**: 임시로 비활성화된 지표

---

## 🔧 코드 구현 가이드라인

### **1. 변수 ID 매핑 표준화**
```python
# ✅ 올바른 방식
STANDARD_VARIABLE_MAPPING = {
    # 표시명 → 변수 ID
    "단순이동평균": "SMA",
    "RSI 지표": "RSI", 
    "MACD 지표": "MACD",
    "현재가": "CURRENT_PRICE",
    "거래량": "VOLUME"
}

# ✅ 역매핑 (변수 ID → 표시명)
VARIABLE_DISPLAY_NAMES = {
    "SMA": "단순이동평균",
    "RSI": "RSI 지표",
    "MACD": "MACD 지표", 
    "CURRENT_PRICE": "현재가",
    "VOLUME": "거래량"
}
```

### **2. 카테고리 매핑 표준화**
```python
# ✅ 변수 ID → 용도 카테고리 매핑 (호환성 검증용)
VARIABLE_PURPOSE_CATEGORIES = {
    # 추세 지표
    "SMA": "trend",
    "EMA": "trend", 
    "WMA": "trend",
    "HMA": "trend",
    "TEMA": "trend",
    "BOLLINGER_BAND": "volatility",  # 볼린저밴드는 변동성 지표
    "KELTNER_CHANNELS": "volatility",
    "DONCHIAN_CHANNELS": "trend",
    "ICHIMOKU": "trend",
    "PSAR": "trend",
    
    # 가격 데이터
    "CURRENT_PRICE": "price",
    "OPEN_PRICE": "price",
    "HIGH_PRICE": "price", 
    "LOW_PRICE": "price",
    "VWAP": "price",
    
    # 모멘텀 지표
    "RSI": "momentum",
    "STOCH": "momentum",
    "STOCH_RSI": "momentum",
    "CCI": "momentum",
    "WILLIAMS_R": "momentum",
    "MFI": "volume",  # MFI는 거래량 기반
    "MACD": "momentum", 
    "ADX": "momentum",
    "AROON": "momentum",
    "ROC": "momentum",
    "MOMENTUM": "momentum",
    "AO": "momentum",
    
    # 변동성 지표
    "ATR": "volatility",
    "BOLLINGER_WIDTH": "volatility",
    "STANDARD_DEVIATION": "volatility",
    "VOLATILITY_INDEX": "volatility",
    
    # 거래량 지표
    "VOLUME": "volume",
    "VOLUME_MA": "volume",
    "OBV": "volume",
    "CMF": "volume",
    "AD": "volume"
}

# ✅ 변수 ID → 차트 카테고리 매핑 (UI 표시용)
VARIABLE_CHART_CATEGORIES = {
    # 가격 오버레이 (메인 차트)
    "SMA": "price_overlay",
    "EMA": "price_overlay", 
    "WMA": "price_overlay",
    "HMA": "price_overlay",
    "TEMA": "price_overlay",
    "BOLLINGER_BAND": "price_overlay",
    "KELTNER_CHANNELS": "price_overlay",
    "DONCHIAN_CHANNELS": "price_overlay",
    "ICHIMOKU": "price_overlay",
    "PSAR": "price_overlay",
    "VWAP": "price_overlay",
    
    # 가격 데이터 (원시 데이터)
    "CURRENT_PRICE": "price_data",
    "OPEN_PRICE": "price_data",
    "HIGH_PRICE": "price_data", 
    "LOW_PRICE": "price_data",
    
    # 오실레이터 (0-100 또는 고정 범위)
    "RSI": "oscillator",
    "STOCH": "oscillator",
    "STOCH_RSI": "oscillator",
    "CCI": "oscillator",
    "WILLIAMS_R": "oscillator",
    "MFI": "oscillator",
    
    # 신호선 (중앙선 기준, 가변 범위)
    "MACD": "signal_line", 
    "ADX": "signal_line",
    "AROON": "signal_line",
    "ROC": "signal_line",
    "MOMENTUM": "signal_line",
    "AO": "signal_line",
    
    # 지표 서브플롯 (가변 범위)
    "ATR": "indicator_subplot",
    "BOLLINGER_WIDTH": "indicator_subplot",
    "STANDARD_DEVIATION": "indicator_subplot",
    "VOLATILITY_INDEX": "indicator_subplot",
    "OBV": "indicator_subplot",
    "CMF": "indicator_subplot",
    "AD": "indicator_subplot",
    
    # 거래량 서브플롯
    "VOLUME": "volume_subplot",
    "VOLUME_MA": "volume_subplot"
}

# ✅ 활성화 상태 매핑
VARIABLE_ACTIVATION_STATUS = {
    # 현재 활성화된 지표 (✅)
    "SMA": True,
    "EMA": True,
    "RSI": True,
    "STOCH": True,
    "MACD": True,
    "CURRENT_PRICE": True,
    "OPEN_PRICE": True,
    "HIGH_PRICE": True,
    "LOW_PRICE": True,
    "VOLUME": True,
    "BOLLINGER_BAND": True,
    
    # 개발 중인 지표 (🚧)
    "WMA": False,
    "HMA": False,
    "TEMA": False,
    "CCI": False,
    "WILLIAMS_R": False,
    "STOCH_RSI": False,
    "DMI": False,
    "ADX": False,
    "AO": False,
    "VWAP": False,
    "ATR": False,
    "BOLLINGER_WIDTH": False,
    "KELTNER_CHANNELS": False,
    "VOLUME_MA": False,
    "OBV": False,
    "MFI": False,
    
    # 계획 중인 지표들은 기본적으로 False
}
```

### **3. 호환성 검증 로직 (이중 카테고리 시스템)**
```python
def is_compatible(base_var_id: str, external_var_id: str) -> bool:
    """
    이중 카테고리 시스템을 사용한 호환성 검증
    - 용도 카테고리가 같으면 호환 가능
    - 두 지표 모두 활성화되어 있어야 함
    """
    # 1. 활성화 상태 확인
    if not (VARIABLE_ACTIVATION_STATUS.get(base_var_id, False) and 
            VARIABLE_ACTIVATION_STATUS.get(external_var_id, False)):
        return False
    
    # 2. 용도 카테고리 기준으로 호환성 검증
    base_purpose = VARIABLE_PURPOSE_CATEGORIES.get(base_var_id)
    external_purpose = VARIABLE_PURPOSE_CATEGORIES.get(external_var_id)
    
    return (base_purpose == external_purpose and 
            base_purpose is not None)

def get_chart_display_category(var_id: str) -> str:
    """차트 표시 방식을 결정하는 카테고리 반환"""
    return VARIABLE_CHART_CATEGORIES.get(var_id, "indicator_subplot")

def is_variable_active(var_id: str) -> bool:
    """변수가 현재 사용 가능한지 확인"""
    return VARIABLE_ACTIVATION_STATUS.get(var_id, False)

def get_active_variables_by_purpose(purpose_category: str) -> list:
    """특정 용도 카테고리의 활성화된 변수들만 반환"""
    active_vars = []
    for var_id, is_active in VARIABLE_ACTIVATION_STATUS.items():
        if (is_active and 
            VARIABLE_PURPOSE_CATEGORIES.get(var_id) == purpose_category):
            active_vars.append(var_id)
    return active_vars
```

---

## 📝 마이그레이션 체크리스트

### **🔍 수정이 필요한 파일들**

#### **1. variable_definitions.py**
- [ ] 변수 ID를 대문자 표준으로 통일
- [ ] 카테고리 분류를 표준 기준으로 수정
- [ ] 표시명을 한글 표준으로 통일

#### **2. chart_variable_service.py**  
- [ ] 변수 ID 매핑을 표준 방식으로 수정
- [ ] 카테고리 매핑 로직 표준화
- [ ] 호환성 검증 로직 간소화

#### **3. condition_dialog.py**
- [ ] `get_current_variable_id()` 매핑 표준화
- [ ] `_get_variable_category()` 표준 테이블 사용
- [ ] 변수명 변환 로직 통일

#### **4. UI 컴포넌트들**
- [ ] 콤보박스 표시명 표준화
- [ ] 변수 설명 텍스트 표준화
- [ ] 에러 메시지 표준 용어 적용

---

## ⚡ 즉시 수정 권장사항

### **1. 단순이동평균 호환성 문제 해결 (이중 카테고리 적용)**
```python
# variable_definitions.py에서 SMA를 trend 카테고리로 수정
def get_category_variables():
    return {
        "trend": [  # ✅ 추세 지표 카테고리 추가
            ("SMA", "단순이동평균"),  # ✅ 여기로 이동
            ("EMA", "지수이동평균"),
            ("WMA", "가중이동평균"),
            ("BOLLINGER_BAND", "볼린저밴드"),  # 사실은 volatility지만 UI상 trend로 분류
        ],
        "momentum": [
            ("RSI", "RSI 지표"),
            ("STOCH", "스토캐스틱"),
            ("MACD", "MACD 지표"),
        ],
        "volume": [
            ("VOLUME", "거래량"),
            ("VOLUME_MA", "거래량 이평"),
        ],
        "price": [
            ("CURRENT_PRICE", "현재가"),
            ("OPEN_PRICE", "시가"),
            ("HIGH_PRICE", "고가"),
            ("LOW_PRICE", "저가"),
        ]
    }
```

### **2. 이중 매핑 테이블 구현**
```python
# condition_dialog.py에서 이중 카테고리 시스템 적용
def _get_variable_category(self, variable_id: str) -> str:
    """용도 카테고리를 반환 (호환성 검증용)"""
    return VARIABLE_PURPOSE_CATEGORIES.get(variable_id, "unknown")

def _get_chart_category(self, variable_id: str) -> str:
    """차트 표시 카테고리를 반환 (UI 표시용)"""
    return VARIABLE_CHART_CATEGORIES.get(variable_id, "indicator_subplot")

def check_variable_compatibility(self):
    """이중 카테고리 시스템으로 호환성 검증"""
    base_var_id = self.get_current_variable_id()
    external_var_id = self.external_variable_combo.currentData()
    
    if base_var_id and external_var_id:
        # 1. 활성화 상태 확인
        if not (is_variable_active(base_var_id) and is_variable_active(external_var_id)):
            self.show_compatibility_status("❌ 비활성화된 지표입니다", False)
            return
        
        # 2. 용도 카테고리 기준 호환성 검증
        is_compatible_result = is_compatible(base_var_id, external_var_id)
        
        if is_compatible_result:
            self.show_compatibility_status("✅ 호환 가능", True)
        else:
            purpose1 = VARIABLE_PURPOSE_CATEGORIES.get(base_var_id, "unknown")
            purpose2 = VARIABLE_PURPOSE_CATEGORIES.get(external_var_id, "unknown")
            self.show_compatibility_status(
                f"❌ 호환 불가 ({purpose1} ≠ {purpose2})", False
            )
```

### **3. 점진적 활성화 시스템**
```python
# 새로운 지표 추가 시 비활성 상태로 시작
def add_new_indicator(var_id: str, display_name: str, 
                     purpose_category: str, chart_category: str):
    """새 지표를 비활성 상태로 추가"""
    
    # 1. 표준 매핑에 추가
    VARIABLE_DISPLAY_NAMES[var_id] = display_name
    VARIABLE_PURPOSE_CATEGORIES[var_id] = purpose_category
    VARIABLE_CHART_CATEGORIES[var_id] = chart_category
    
    # 2. 비활성 상태로 추가
    VARIABLE_ACTIVATION_STATUS[var_id] = False
    
    print(f"✅ {display_name} ({var_id}) 지표가 비활성 상태로 추가되었습니다.")
    print(f"   용도: {purpose_category}, 차트: {chart_category}")
    print(f"   구현 완료 후 activate_indicator('{var_id}')로 활성화하세요.")

def activate_indicator(var_id: str):
    """지표 구현 완료 후 활성화"""
    if var_id in VARIABLE_ACTIVATION_STATUS:
        VARIABLE_ACTIVATION_STATUS[var_id] = True
        display_name = VARIABLE_DISPLAY_NAMES.get(var_id, var_id)
        print(f"🎉 {display_name} ({var_id}) 지표가 활성화되었습니다!")
    else:
        print(f"❌ {var_id} 지표를 찾을 수 없습니다.")
```

---

## 🎯 기대 효과 (이중 카테고리 시스템)

### **🔧 기술적 효과**
1. **호환성 문제 해결**: 단순이동평균끼리 정상 호환 인식
2. **차트 표시 최적화**: 각 지표의 특성에 맞는 차트 배치
3. **코드 확장성 향상**: 새로운 지표 추가 시 표준 적용
4. **점진적 개발 지원**: 비활성 → 개발 → 활성화 단계별 관리

### **💼 비즈니스 효과**
1. **개발 효율성 향상**: 일관된 용어로 개발 속도 증가  
2. **유지보수성 개선**: 표준 기준으로 코드 가독성 향상
3. **사용자 경험 개선**: 직관적인 지표 분류 및 호환성 안내
4. **안정성 향상**: 표준화된 검증 로직으로 에러 감소

### **📈 확장성 효과**
1. **다양한 지표 지원**: 트레이딩뷰 200+ 지표까지 확장 가능
2. **커스터마이징 가능**: 용도별/표시별 독립적 카테고리 관리
3. **단계별 릴리스**: 준비된 지표만 선별적으로 활성화
4. **호환성 보장**: 새 지표 추가 시에도 기존 로직과 충돌 방지

### **🎨 사용자 인터페이스 개선**
```
[기존] 단순 카테고리
├── indicator (RSI, SMA, MACD 혼재)
└── price (현재가, 시가, 고가)

[개선] 이중 카테고리 시스템
├── 용도별 분류 (호환성 검증)
│   ├── trend (SMA, EMA, WMA)
│   ├── momentum (RSI, STOCH, MACD)
│   └── volume (VOLUME, OBV, MFI)
└── 차트별 분류 (표시 방식)
    ├── price_overlay (메인 차트 오버레이)
    ├── oscillator (0-100% 서브플롯)
    └── signal_line (중앙선 기준 서브플롯)
```

---

## 📞 문의 및 제안
- 새로운 지표 추가 시 이 문서 기준 적용
- 용어 표준 수정 제안은 이슈로 등록
- 마이그레이션 진행 시 단계별 테스트 필요

---
**마지막 업데이트**: 2025년 7월 26일  
**버전**: v1.0  
**담당**: 트리거 빌더 개발팀
