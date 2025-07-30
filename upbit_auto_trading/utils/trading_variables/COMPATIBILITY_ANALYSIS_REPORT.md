# 🚨 Schema 개선안과 기존 코드 호환성 분석 보고서

## 📋 문제 요약

개선된 스키마 (`schema_improved.sql`)를 그대로 적용하면 **기존 프로그램이 완전히 동작하지 않습니다**. 다음과 같은 심각한 호환성 문제들이 발견되었습니다.

---

## 🚨 Critical Issues (즉시 수정 필요)

### 1. **테이블명 불일치**
**문제**: 기존 코드 vs 새 스키마 테이블명이 다름

| 구분 | 기존 코드 | 새 스키마 | 영향도 |
|------|-----------|-----------|---------|
| 메인 테이블 | `tv_trading_variables` | `trading_variables` | 🔴 Critical |
| 파라미터 테이블 | `tv_variable_parameters` | `variable_parameters` | 🔴 Critical |

**영향 범위**:
- `compatibility_validator.py`: 모든 DB 쿼리 실패
- 기타 DB 접근 코드: 테이블을 찾을 수 없음

### 2. **Variable ID 표준화 충돌**
**문제**: 기존 코드에서 사용하는 ID vs 새 스키마의 표준화된 ID가 불일치

| 기존 UI/코드 | 새 스키마 | 사용 위치 | 영향도 |
|--------------|-----------|-----------|---------|
| `STOCHASTIC` | `STOCHASTIC_OSCILLATOR` | variable_definitions.py, condition_dialog.py | 🔴 Critical |
| `BOLLINGER_BAND` | `BOLLINGER_BANDS` | variable_definitions.py, condition_dialog.py | 🔴 Critical |
| `STOCH` (validator 내부) | `STOCHASTIC_OSCILLATOR` | compatibility_validator.py | 🔴 Critical |

### 3. **매핑 테이블 불일치**
**문제**: `compatibility_validator.py`의 정규화 매핑이 새 스키마와 맞지 않음

```python
# 현재 매핑 (호환되지 않음)
id_mapping = {
    'STOCHASTIC': 'STOCH',  # 🚨 새 스키마에는 'STOCHASTIC_OSCILLATOR'
    'BOLLINGER_BANDS': 'BOLLINGER_BAND',  # 🚨 새 스키마에는 'BOLLINGER_BANDS'
}
```

---

## ⚠️ High Priority Issues

### 4. **Chart Category 불일치**
**문제**: `variable_definitions.py`의 차트 카테고리와 새 스키마 데이터 불일치

| 변수 | variable_definitions.py | 새 스키마 | 정확한 값 |
|------|-------------------------|-----------|-----------|
| `BOLLINGER_BAND` | `overlay` | `BOLLINGER_BANDS` = `overlay` | ✅ 일치하지만 ID 다름 |
| `STOCHASTIC` | `subplot` | `STOCHASTIC_OSCILLATOR` = `subplot` | ✅ 일치하지만 ID 다름 |

### 5. **파라미터 정의 불일치**
**문제**: 새 스키마의 풍부한 파라미터 vs 기존 하드코딩된 파라미터

- 새 스키마: `source` 파라미터 대폭 추가 (WMA, ROC, WILLIAMS_R 등)
- 기존 코드: 제한된 파라미터만 정의됨

---

## 🛠️ 해결 방안

### Option 1: 기존 코드 호환성 유지 (권장)
새 스키마를 기존 코드와 호환되도록 수정

### Option 2: 전면 마이그레이션
모든 기존 코드를 새 스키마에 맞게 수정

---

## 🎯 즉시 적용 가능한 해결책

### 1단계: 테이블명 통일
새 스키마의 테이블명을 기존 코드와 맞춤:

```sql
-- 수정 전
CREATE TABLE IF NOT EXISTS trading_variables (

-- 수정 후  
CREATE TABLE IF NOT EXISTS tv_trading_variables (
```

### 2단계: Variable ID 호환성 확보
새 스키마에서 기존 코드가 사용하는 ID를 유지하거나 별칭 추가

### 3단계: 점진적 마이그레이션
기존 시스템이 동작하는 상태에서 점진적으로 개선

---

## 📊 상세 충돌 지점 분석

### A. compatibility_validator.py
```python
# Line 95: 테이블명 하드코딩 ❌
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tv_trading_variables'")

# Line 160-180: 매핑 테이블 ❌
'STOCHASTIC': 'STOCH',  # 새 스키마에는 'STOCHASTIC_OSCILLATOR'
'BOLLINGER_BANDS': 'BOLLINGER_BAND',  # 새 스키마에는 'BOLLINGER_BANDS'
```

### B. variable_definitions.py
```python
# Line 27, 35: Variable ID 불일치 ❌
"BOLLINGER_BAND": "overlay",  # 새 스키마: BOLLINGER_BANDS
"STOCHASTIC": "subplot",      # 새 스키마: STOCHASTIC_OSCILLATOR
```

### C. condition_dialog.py
```python
# 여러 곳에서 'stochastic', 'bollinger_band' 소문자 사용 ❌
# 새 스키마의 표준화된 ID와 맞지 않음
```

---

## 🚀 권장 수정 계획

### Phase 1: 긴급 호환성 패치 (1-2시간)
1. 새 스키마 테이블명을 `tv_` 접두사 추가
2. Variable ID를 기존 코드와 호환되도록 조정
3. 기본 동작 확인

### Phase 2: 점진적 개선 (1-2주)
1. 새로 추가된 파라미터들을 기존 시스템에 통합
2. UI에서 새 파라미터 활용
3. 호환성 검증기 개선

### Phase 3: 완전 마이그레이션 (1개월)
1. 모든 코드를 새 표준에 맞게 수정
2. 성능 최적화
3. 확장성 개선

---

## 🔧 즉시 적용할 수정 사항

다음 섹션에서 구체적인 수정 코드를 제공하겠습니다.
