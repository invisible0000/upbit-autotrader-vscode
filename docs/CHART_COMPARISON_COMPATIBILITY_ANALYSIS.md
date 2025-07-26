# 📊 차트 지표 비교 호환성 분석

## 🎯 **핵심 아이디어: 비교 가능성 기준 카테고리 재설계**

### **문제 인식**
- **오버레이 지표**: 모든 지표가 원화 단위로 비교 가능
- **서브플롯 지표**: 스케일과 의미가 달라서 비교 불가능한 경우 多

---

## 📈 **비교 가능성 매트릭스**

### **✅ 완전 비교 가능**

#### **1. 오버레이 그룹 (원화 단위)**
| 지표 | 예시 값 | 비교 가능 대상 |
|------|---------|---------------|
| SMA | 50,000원 | EMA, 볼린저밴드, 현재가 |
| EMA | 51,000원 | SMA, 볼린저밴드, 현재가 |
| 현재가 | 50,500원 | 모든 오버레이 지표 |
| VWAP | 49,800원 | 모든 오버레이 지표 |

**💡 특징**: 모두 원화 스케일이므로 직접 크기 비교 가능

#### **2. 퍼센트 그룹 (0-100% 범위)**
| 지표 | 예시 값 | 비교 가능 대상 |
|------|---------|---------------|
| RSI | 65% | STOCH, CCI, Williams %R, MFI |
| STOCH | 75% | RSI, CCI, Williams %R, MFI |
| MFI | 45% | RSI, STOCH, CCI, Williams %R |

**💡 특징**: 모두 0-100% 정규화되어 과매수/과매도 수준 비교 가능

#### **3. 거래량 그룹 (주/코인 단위)**
| 지표 | 예시 값 | 비교 가능 대상 |
|------|---------|---------------|
| VOLUME | 1,000,000주 | 거래량 이동평균 |
| VOLUME_MA | 850,000주 | 현재 거래량 |

**💡 특징**: 거래량 단위가 동일하므로 크기 비교 가능

---

### **🔶 조건부 비교 가능**

#### **4. 신호선 그룹 (중앙선 기준, 상이한 범위)**
| 지표 | 일반적 범위 | 특징 | 비교 조건 |
|------|-------------|------|----------|
| MACD | -500 ~ +500 | 빠른 신호 | 같은 기간 설정 시만 |
| AO | -1000 ~ +1000 | 느린 신호 | 계산 방식 고려 필요 |
| ROC | -10% ~ +10% | 비율 기반 | 퍼센트 변환 시 가능 |

**💡 특징**: 중앙선(0) 기준은 동일하지만 범위가 달라 정규화 필요

#### **5. 변동성 그룹 (절대값, 원화 단위)**
| 지표 | 예시 값 | 특징 | 비교 조건 |
|------|---------|------|----------|
| ATR | 800원 | 평균 변동폭 | 같은 원화 단위 |
| 볼린저밴드폭 | 1,200원 | 밴드 간격 | 같은 원화 단위 |
| 표준편차 | 600원 | 가격 분산 | 같은 원화 단위 |

**💡 특징**: 원화 단위는 동일하지만 계산 방식이 달라 의미 해석 주의

---

### **❌ 비교 불가능**

#### **6. 고유 스케일 그룹**
| 지표 | 스케일 | 비교 불가 이유 |
|------|--------|---------------|
| OBV | 누적 거래량 | 누적값이라 절대적 크기 의미 없음 |
| 상관계수 | -1 ~ +1 | 상관관계 수치로 크기 비교 무의미 |
| 지그재그 | 가격 포인트 | 중요 고점/저점만 표시 |
| ADX | 0 ~ 100 | 추세 강도(방향 없음)로 다른 지표와 비교 무의미 |

---

## 🔧 **개선된 차트 카테고리 제안**

### **새로운 차트 카테고리 시스템**
```python
IMPROVED_CHART_CATEGORIES = {
    # 완전 비교 가능 그룹
    "overlay_comparable": [
        "SMA", "EMA", "WMA", "BOLLINGER_BAND", 
        "CURRENT_PRICE", "OPEN_PRICE", "HIGH_PRICE", "LOW_PRICE", "VWAP"
    ],
    
    "percentage_comparable": [
        "RSI", "STOCH", "CCI", "WILLIAMS_R", "MFI"
    ],
    
    "volume_comparable": [
        "VOLUME", "VOLUME_MA"
    ],
    
    # 조건부 비교 가능 그룹
    "signal_conditional": [
        "MACD", "AO", "ROC", "MOMENTUM"
    ],
    
    "volatility_conditional": [
        "ATR", "BOLLINGER_WIDTH", "STANDARD_DEVIATION"
    ],
    
    # 비교 불가능 그룹
    "unique_scale": [
        "OBV", "ADX", "CORRELATION", "ZIGZAG"
    ]
}
```

### **비교 호환성 검증 로직**
```python
def is_chart_comparable(base_var_id: str, external_var_id: str) -> tuple[bool, str]:
    """
    차트 스케일 기준 비교 가능성 검증
    Returns: (비교 가능 여부, 설명 메시지)
    """
    
    base_chart_group = get_chart_comparison_group(base_var_id)
    external_chart_group = get_chart_comparison_group(external_var_id)
    
    # 1. 완전 비교 가능 그룹
    if base_chart_group == external_chart_group:
        if base_chart_group in ["overlay_comparable", "percentage_comparable", "volume_comparable"]:
            return True, f"✅ 같은 {get_group_name(base_chart_group)} 스케일로 직접 비교 가능"
    
    # 2. 조건부 비교 가능 그룹
    if base_chart_group == external_chart_group:
        if base_chart_group in ["signal_conditional", "volatility_conditional"]:
            return True, f"🔶 같은 {get_group_name(base_chart_group)} 그룹이지만 정규화 필요"
    
    # 3. 비교 불가능
    if base_chart_group == "unique_scale" or external_chart_group == "unique_scale":
        return False, "❌ 고유 스케일 지표로 비교 불가능"
    
    # 4. 다른 그룹 간 비교 불가
    return False, f"❌ 다른 차트 그룹 간 비교 불가 ({get_group_name(base_chart_group)} ≠ {get_group_name(external_chart_group)})"

def get_group_name(group_key: str) -> str:
    group_names = {
        "overlay_comparable": "원화 단위",
        "percentage_comparable": "퍼센트 범위", 
        "volume_comparable": "거래량 단위",
        "signal_conditional": "신호선 기준",
        "volatility_conditional": "변동성 단위",
        "unique_scale": "고유 스케일"
    }
    return group_names.get(group_key, "알 수 없음")
```

---

## 🎨 **UI 개선 아이디어**

### **콤보박스 표시 개선**
```python
def populate_comparison_aware_combo(self):
    """비교 가능성을 고려한 콤보박스 구성"""
    
    combos = {
        "📈 원화 비교 가능": [
            ("SMA", "🔗 단순이동평균"),
            ("EMA", "🔗 지수이동평균"), 
            ("CURRENT_PRICE", "🔗 현재가")
        ],
        "📊 퍼센트 비교 가능": [
            ("RSI", "📈 RSI 지표"),
            ("STOCH", "📈 스토캐스틱"),
            ("MFI", "📈 자금흐름지수")
        ],
        "⚡ 신호선 (조건부 비교)": [
            ("MACD", "⚡ MACD 지표"),
            ("AO", "⚡ 어썸 오실레이터")
        ],
        "🚫 비교 불가": [
            ("OBV", "💽 온밸런스볼륨"),
            ("ADX", "📊 ADX 지표")
        ]
    }
```

### **호환성 상태 표시 개선**
```
[현재] ✅ 호환 가능
[개선] ✅ 원화 단위로 직접 비교 가능 (SMA: 50,000원 vs EMA: 51,000원)

[현재] ❌ 호환 불가
[개선] ❌ 다른 스케일로 비교 불가 (RSI: 0-100% vs VOLUME: 거래량 단위)
```

---

## 🎯 **실제 사용 시나리오**

### **시나리오 1: 추세 지표 비교**
```
사용자: "SMA 50일선이 현재가보다 높은가?"
시스템: ✅ 둘 다 원화 단위로 직접 비교 가능
결과: SMA(50,000원) vs 현재가(50,500원) → 현재가가 500원 높음
```

### **시나리오 2: 모멘텀 지표 비교**
```
사용자: "RSI가 스토캐스틱보다 높은가?"
시스템: ✅ 둘 다 0-100% 범위로 직접 비교 가능
결과: RSI(65%) vs STOCH(75%) → 스토캐스틱이 10% 높음
```

### **시나리오 3: 불가능한 비교**
```
사용자: "RSI가 거래량보다 높은가?"
시스템: ❌ 다른 스케일로 비교 불가 (RSI: 0-100% vs 거래량: 1,000,000주)
결과: 비교 조건 생성 불가능
```

---

## 💡 **추가 아이디어**

### **1. 스마트 정규화 기능**
```python
def smart_normalize_for_comparison(var1_id: str, var1_value: float, 
                                  var2_id: str, var2_value: float) -> tuple[float, float]:
    """스케일이 다른 지표들을 비교 가능하도록 정규화"""
    
    group1 = get_chart_comparison_group(var1_id)
    group2 = get_chart_comparison_group(var2_id)
    
    # 신호선 그룹 간 비교 시 0 기준 상대적 위치로 정규화
    if group1 == "signal_conditional" and group2 == "signal_conditional":
        range1 = get_typical_range(var1_id)
        range2 = get_typical_range(var2_id)
        
        normalized1 = var1_value / range1  # -1 ~ +1 정규화
        normalized2 = var2_value / range2  # -1 ~ +1 정규화
        
        return normalized1, normalized2
    
    return var1_value, var2_value  # 정규화 불가능
```

### **2. 비교 가능성 미리보기**
```python
def preview_comparison_compatibility(base_var_id: str, external_var_id: str) -> str:
    """비교 선택 전에 호환성 미리보기"""
    
    is_compatible, message = is_chart_comparable(base_var_id, external_var_id)
    
    if is_compatible:
        example = get_comparison_example(base_var_id, external_var_id)
        return f"{message}\n예시: {example}"
    else:
        suggestion = get_alternative_suggestion(base_var_id, external_var_id)
        return f"{message}\n💡 대안: {suggestion}"
```

---

## 🚀 **결론 및 제안**

### **핵심 아이디어 요약**
1. **오버레이**: 모든 지표 비교 가능 (원화 단위)
2. **퍼센트 서브플롯**: 0-100% 지표들끼리 비교 가능
3. **신호선 서브플롯**: 조건부 비교 가능 (정규화 필요)
4. **고유 스케일**: 비교 불가능한 지표들 별도 분류

### **구현 우선순위**
1. **1차**: 오버레이 + 퍼센트 그룹 완전 지원
2. **2차**: 신호선 그룹 조건부 비교 지원
3. **3차**: 스마트 정규화 기능 추가

이 방식으로 사용자가 **의미 있는 비교만** 할 수 있도록 안내하면서, **혼란을 방지**할 수 있습니다! 🎯
