# 변수 호환성 규칙 가이드

## 📋 개요

트리거 빌더에서 변수 간 비교 시 의미있는 조합만 허용하고, 논리적으로 맞지 않는 비교를 방지하기 위한 변수 호환성 규칙 시스템입니다.

## 🎯 핵심 원칙

### 1. 카테고리 기반 호환성
변수는 **카테고리**에 따라 호환 여부가 결정됩니다.

```
✅ 호환 가능한 조합:
- RSI(oscillator) ↔ 스토캐스틱(oscillator) - 같은 0-100 스케일
- 현재가(price_overlay) ↔ 이동평균(price_overlay) - 같은 가격 단위
- MACD(momentum) ↔ ROC(momentum) - 같은 모멘텀 지표

❌ 호환 불가능한 조합:
- RSI(oscillator) ↔ MACD(momentum) - 다른 스케일과 의미
- 현재가(price_overlay) ↔ 거래량(volume) - 완전히 다른 단위
- RSI(oscillator) ↔ 거래량(volume) - 의미없는 비교
```

### 2. 단위 기반 호환성
같은 단위나 스케일을 가진 변수들만 비교 가능합니다.

```
✅ 단위 호환:
- 원화 기반: 현재가, 이동평균, 볼린저밴드
- 퍼센트 기반: RSI, 스토캐스틱 (%K, %D)
- 무차원: MACD, ROC, 모멘텀 지표

❌ 단위 불일치:
- 원화(현재가) vs 퍼센트(RSI)
- 개수(거래량) vs 원화(가격)
```

## 🔧 구현 요구사항

### 1. UI 레벨 검증 (최우선 ⭐⭐⭐)
트리거 빌더 UI에서 **실시간으로** 호환성을 검사하고 불가능한 조합을 차단해야 합니다.

```python
# 외부변수 선택 시 즉시 검증
def on_external_variable_selected(self, variable_id):
    base_variable = self.get_current_base_variable()
    
    if not self.chart_variable_service.is_compatible_external_variable(
        base_variable, variable_id
    )[0]:
        # 선택 차단 및 경고 메시지
        self.show_compatibility_warning(base_variable, variable_id)
        self.external_variable_combo.setCurrentIndex(0)  # 초기화
        return False
    
    return True
```

### 2. 백엔드 검증 (필수 ⭐⭐)
조건 저장 시 서버 측에서도 호환성을 재검증해야 합니다.

```python
# 조건 저장 전 최종 검증
def save_condition(self, condition_data):
    base_var = condition_data.get('variable_id')
    external_var = condition_data.get('external_variable', {}).get('variable_id')
    
    if external_var:
        is_compatible, reason = self.chart_variable_service.is_compatible_external_variable(
            base_var, external_var
        )
        
        if not is_compatible:
            raise ValidationError(f"변수 호환성 오류: {reason}")
    
    # 저장 진행...
```

### 3. 데이터베이스 제약 조건 (권장 ⭐)
DB 레벨에서도 호환성 규칙을 강제할 수 있습니다.

```sql
-- 호환성 검증 트리거 (SQLite)
CREATE TRIGGER check_variable_compatibility
BEFORE INSERT ON trading_conditions
WHEN NEW.external_variable IS NOT NULL
BEGIN
    SELECT CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM variable_compatibility_rules vcr
            JOIN chart_variables cv1 ON NEW.variable_id = cv1.variable_id
            JOIN chart_variables cv2 ON json_extract(NEW.external_variable, '$.variable_id') = cv2.variable_id
            WHERE vcr.base_variable_id = cv1.variable_id 
            AND vcr.compatible_category = cv2.category
        )
        THEN RAISE(ABORT, '변수 호환성 규칙 위반')
    END;
END;
```

## 📊 현재 등록된 호환성 규칙

### RSI 변수
```
✅ 호환 카테고리:
- oscillator: 같은 오실레이터 계열 (0-100 스케일)
- percentage: 퍼센트 단위 (0-100 범위)

❌ 불가능:
- price_overlay: 가격 단위와 퍼센트 단위 불일치
- volume: 거래량과 오실레이터 의미 불일치
- momentum: MACD 등과 스케일 차이
```

### 현재가 변수
```
✅ 호환 카테고리:
- price_overlay: 같은 가격 스케일
- currency: 통화 단위

❌ 불가능:
- oscillator: 가격과 퍼센트 단위 불일치
- volume: 가격과 거래량 의미 불일치
- momentum: 가격과 모멘텀 지표 차이
```

### MACD 변수
```
✅ 호환 카테고리:
- momentum: 모멘텀 지표 계열

❌ 불가능:
- price_overlay: 가격 단위와 MACD 값 차이
- oscillator: 0-100 스케일과 MACD 스케일 차이
- volume: 거래량과 모멘텀 지표 의미 불일치
```

## 🚨 중요한 구현 포인트

### 1. 사용자 경험 우선
```python
# 좋은 예: 즉시 피드백
def update_external_variable_options(self, base_variable_id):
    """기본 변수 변경 시 호환 가능한 외부변수만 표시"""
    compatible_variables = []
    
    for var_id in self.all_variables:
        is_compatible, _ = self.chart_variable_service.is_compatible_external_variable(
            base_variable_id, var_id
        )
        if is_compatible:
            compatible_variables.append(var_id)
    
    self.external_variable_combo.clear()
    self.external_variable_combo.addItems(compatible_variables)

# 나쁜 예: 저장 시점에만 검증
def save_condition(self):
    # ... 모든 데이터 입력 후
    if not compatible:  # 너무 늦은 검증!
        show_error("호환되지 않는 변수입니다")
```

### 2. 명확한 오류 메시지
```python
# 좋은 예
error_messages = {
    'category_mismatch': "RSI(오실레이터)는 MACD(모멘텀 지표)와 비교할 수 없습니다. 같은 카테고리의 변수를 선택해주세요.",
    'unit_mismatch': "현재가(원화)는 RSI(퍼센트)와 비교할 수 없습니다. 같은 단위의 변수를 선택해주세요.",
    'scale_mismatch': "거래량은 가격 지표와 비교할 수 없습니다. 의미있는 비교를 위해 같은 성격의 지표를 선택해주세요."
}

# 나쁜 예
error_message = "변수가 호환되지 않습니다."  # 너무 모호함
```

### 3. 성능 고려사항
```python
# 호환성 검사 결과 캐싱
class CompatibilityCache:
    def __init__(self):
        self._cache = {}
    
    def is_compatible(self, base_var, external_var):
        cache_key = f"{base_var}:{external_var}"
        
        if cache_key not in self._cache:
            result = self._check_compatibility(base_var, external_var)
            self._cache[cache_key] = result
        
        return self._cache[cache_key]
```

## 🔍 테스트 케이스

### 필수 테스트 시나리오
```python
def test_variable_compatibility():
    # 1. 같은 카테고리 - 성공
    assert is_compatible("rsi", "stochastic") == True
    
    # 2. 다른 카테고리 - 실패
    assert is_compatible("rsi", "macd") == False
    
    # 3. 가격 오버레이 - 성공
    assert is_compatible("current_price", "moving_average") == True
    
    # 4. 단위 불일치 - 실패
    assert is_compatible("current_price", "volume") == False
    
    # 5. UI 블로킹 테스트
    assert external_variable_selection_blocked("rsi", "volume") == True
```

## 📝 체크리스트

### UI 구현 체크리스트
- [ ] 기본 변수 선택 시 호환 가능한 외부변수만 활성화
- [ ] 호환되지 않는 변수 선택 시 즉시 경고 메시지
- [ ] 호환성 상태를 시각적으로 표시 (색상, 아이콘)
- [ ] 도움말 텍스트로 호환 이유 설명

### 백엔드 구현 체크리스트
- [ ] 조건 저장 전 호환성 재검증
- [ ] 호환성 규칙 동적 업데이트 지원
- [ ] 성능 최적화 (캐싱, 배치 검증)
- [ ] 상세한 로깅 및 모니터링

### 테스트 체크리스트
- [ ] 모든 변수 조합에 대한 호환성 테스트
- [ ] UI 상호작용 테스트 (실제 사용자 시나리오)
- [ ] 성능 테스트 (대량 변수 조합)
- [ ] 오류 처리 테스트 (예외 상황)

## 🎯 우선순위

1. **최우선 (즉시 구현)**: UI 레벨 실시간 검증
2. **높음 (다음 스프린트)**: 백엔드 검증 및 오류 메시지 개선
3. **중간 (향후)**: DB 제약 조건 및 성능 최적화
4. **낮음 (장기)**: 고급 호환성 규칙 (범위 제약 등)

---

> ⚠️ **중요**: 변수 호환성 규칙은 사용자가 의미없는 트리거를 생성하는 것을 방지하는 핵심 기능입니다. 
> 반드시 UI 레벨에서 즉시 검증되어야 하며, 사용자에게 명확한 피드백을 제공해야 합니다.
