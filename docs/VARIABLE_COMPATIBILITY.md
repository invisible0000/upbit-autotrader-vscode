# 🔗 변수 호환성 검증 가이드

## 📋 개요

DDD 기반 Domain Service로 구현된 **의미있는 변수 비교**만 허용하고, 논리적으로 맞지 않는 조합을 방지하는 호환성 시스템입니다.

## 🎯 핵심 호환성 규칙

### 같은 Comparison Group = 직접 비교 가능
```python
# ✅ 호환 가능한 조합
"SMA(20) > EMA(10)"           # 둘 다 price_comparable
"RSI > Stochastic_K"          # 둘 다 percentage_comparable  
"MACD > Williams_R"           # 둘 다 zero_centered

# ⚠️ 경고 - 정규화 필요
"Close > RSI"                 # price vs percentage (자동 정규화)

# ❌ 비교 불가
"RSI > MACD"                  # percentage vs zero_centered
"Volume > RSI"                # 완전히 다른 단위
```

### 카테고리별 분류
```python
COMPARISON_GROUPS = {
    "price_comparable": {
        "variables": ["Close", "Open", "High", "Low", "SMA", "EMA", "BB_Upper", "BB_Lower"],
        "unit": "KRW",
        "range": "동적 (시장 가격에 따라 변동)"
    },
    "percentage_comparable": {
        "variables": ["RSI", "Stochastic_K", "Stochastic_D", "Williams_R"],
        "unit": "%",
        "range": "0-100 또는 -100~0"
    },
    "zero_centered": {
        "variables": ["MACD", "MACD_Signal", "MACD_Histogram", "ROC", "CCI"],
        "unit": "없음",
        "range": "0 중심으로 양수/음수 변동"
    },
    "volume_based": {
        "variables": ["Volume", "Volume_SMA", "VWAP"],
        "unit": "개수/KRW", 
        "range": "거래량 기준"
    }
}
```

## 🔧 Domain Service 기반 실시간 검증

### 변수 선택 시 즉시 필터링
```python
# Domain Service로 구현된 호환성 검증
class VariableCompatibilityDomainService:
    def filter_compatible_variables(self, base_variable_id: VariableId) -> List[Variable]:
        """기본 변수와 호환 가능한 변수들만 반환"""
        base_variable = self.variable_repository.find_by_id(base_variable_id)
        
        compatible_variables = []
        all_variables = self.variable_repository.find_all_active()
        
        for var in all_variables:
            compatibility = self.check_compatibility(base_variable, var)
            
            if compatibility.is_valid():
                compatible_variables.append(var)
                
        return compatible_variables
        
    def check_compatibility(self, var1: Variable, var2: Variable) -> CompatibilityResult:
        """Domain Logic으로 호환성 검증"""
        return var1.check_compatibility_with(var2)
```

### 실시간 경고 표시
```python
def on_external_variable_selected(self, variable_id):
    base_variable = self.get_current_base_variable()
    compatibility = self.check_compatibility(base_variable.id, variable_id)
    
    if compatibility == "incompatible":
        self.show_error_message(f"'{base_variable.name}'과 '{variable_id}'는 비교할 수 없습니다.")
        self.reset_external_variable_selection()
        return False
    
    elif compatibility == "warning":
        warning_msg = f"정규화를 통한 비교입니다. 결과 해석에 주의하세요."
        self.show_warning_message(warning_msg)
    
    return True
```

## 🧮 자동 정규화 시스템

### Price vs Percentage 비교
```python
def normalize_for_comparison(self, price_value, percentage_value, normalization_method="minmax"):
    """가격과 백분율 지표 간 비교를 위한 정규화"""
    
    if normalization_method == "minmax":
        # 0-100 스케일로 정규화
        price_normalized = (price_value - price_min) / (price_max - price_min) * 100
        return price_normalized, percentage_value
    
    elif normalization_method == "zscore":
        # Z-스코어 정규화
        price_zscore = (price_value - price_mean) / price_std
        percentage_zscore = (percentage_value - 50) / 28.87  # RSI 표준편차 근사값
        return price_zscore, percentage_zscore
```

### 경고 메시지 템플릿
```python
WARNING_MESSAGES = {
    "price_vs_percentage": "가격 지표와 백분율 지표를 비교합니다. 정규화가 적용됩니다.",
    "different_timeframes": "서로 다른 시간 프레임의 지표입니다. 시점 차이를 고려하세요.",
    "leading_vs_lagging": "선행 지표와 후행 지표의 조합입니다. 신호 지연을 고려하세요."
}
```

## 📊 호환성 매트릭스

### 비교 가능성 표
```
            | Price | Percentage | Zero-Centered | Volume
------------|-------|------------|---------------|--------
Price       |   ✅   |     ⚠️     |       ❌      |   ❌
Percentage  |   ⚠️   |     ✅     |       ❌      |   ❌  
Zero-Center |   ❌   |     ❌     |       ✅      |   ❌
Volume      |   ❌   |     ❌     |       ❌      |   ✅

✅ 직접 비교 가능
⚠️ 정규화 후 비교 가능 (경고 표시)
❌ 비교 불가능 (차단)
```

## 🧪 테스트 케이스

### 호환성 검증 테스트
```python
def test_compatibility_checking():
    checker = VariableCompatibilityChecker()
    
    # 같은 그룹 = 호환
    assert checker.check_compatibility("SMA", "EMA") == "compatible"
    assert checker.check_compatibility("RSI", "Stochastic") == "compatible"
    
    # 정규화 가능 = 경고
    assert checker.check_compatibility("Close", "RSI") == "warning"
    
    # 완전 비호환 = 불가
    assert checker.check_compatibility("RSI", "MACD") == "incompatible"
    assert checker.check_compatibility("Volume", "RSI") == "incompatible"
```

### UI 통합 테스트
```python
def test_ui_variable_filtering():
    trigger_builder = TriggerBuilderWidget()
    
    # RSI 선택 시 호환 가능한 변수만 표시
    trigger_builder.select_base_variable("RSI")
    available_vars = trigger_builder.get_available_external_variables()
    
    # 호환 가능한 변수들만 포함되어야 함
    compatible_vars = ["Stochastic_K", "Stochastic_D", "Williams_R"]
    incompatible_vars = ["MACD", "Volume", "ATR"]
    
    for var in compatible_vars:
        assert var in available_vars
    
    for var in incompatible_vars:
        assert var not in available_vars
```

## 🚀 구현 우선순위

### Phase 1: 기본 차단 (즉시 구현)
- 완전히 비호환인 조합 UI에서 차단
- 기본적인 경고 메시지 표시

### Phase 2: 정규화 시스템 (1주 내)
- Price vs Percentage 자동 정규화
- 상세한 경고 메시지와 해석 가이드

### Phase 3: 고급 검증 (향후)
- 시간 프레임별 호환성 검사
- 선행/후행 지표 조합 경고
- 통계적 유의성 검증

## 📚 관련 문서

- [트리거 빌더 가이드](TRIGGER_BUILDER_GUIDE.md)
- [트레이딩 변수 관리](TRADING_VARIABLES_COMPACT.md)
- [DB 스키마](DB_SCHEMA.md)
