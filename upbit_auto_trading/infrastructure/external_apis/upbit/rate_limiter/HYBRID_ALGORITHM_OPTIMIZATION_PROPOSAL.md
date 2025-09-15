# 하이브리드 Rate Limiting 알고리즘 최적화 제안서

## 📋 **현재 상황 분석**

### 🔍 **확인된 문제점**
1. **이중 버스트 체크**: GCRA와 윈도우 알고리즘이 각각 다른 기준으로 버스트 허용
2. **알고리즘 일관성 부족**: 시간 기반(GCRA) vs 슬롯 기반(윈도우) 버스트 판정의 혼재
3. **성능 오버헤드**: 두 알고리즘을 모두 실행하여 `max(gcra_delay, window_delay)` 계산

### 📊 **현재 동작 방식**
```python
# GCRA 버스트: 시간 기반 (tau = burst_capacity * interval)
if debt_time <= tau:
    gcra_delay = 0.0  # 버스트 허용

# 윈도우 버스트: 슬롯 기반
if len(window) < window_capacity:
    window_delay = 0.0  # 빈슬롯 허용

# 최종 결정: 더 보수적인 쪽 선택
final_delay = max(gcra_delay, window_delay)
```

---

## 🎯 **최적화 방안 제안**

### **Option 1: 역할 분담 명확화** ⭐ 권장
```python
# GCRA: 평균 RPS 유지 (장기 안정성)
# 윈도우: 단기 스파이크 제어 (버스트 허용/거부)

if window_delay > 0:
    # 윈도우 거부 → 무조건 대기 (스파이크 방지 우선)
    final_delay = window_delay
    decision_reason = "윈도우 스파이크 방지"
else:
    # 윈도우 허용 → GCRA 체크 (평균 속도 유지)
    final_delay = gcra_delay
    decision_reason = "GCRA 속도 제어"
```

**장점**:
- 명확한 책임 분할
- 스파이크 방지 우선 정책
- 성능 최적화 (조건부 실행)

**단점**:
- GCRA 버스트 허용 효과 제한

---

### **Option 2: 알고리즘 선택 모드**
```python
class HybridMode(Enum):
    GCRA_PRIMARY = "gcra_primary"      # GCRA만 버스트 체크
    WINDOW_PRIMARY = "window_primary"  # 윈도우만 버스트 체크
    BALANCED = "balanced"              # 현재 방식 (max 선택)
```

**구현**:
```python
if config.hybrid_mode == HybridMode.GCRA_PRIMARY:
    final_delay = gcra_delay
elif config.hybrid_mode == HybridMode.WINDOW_PRIMARY:
    final_delay = window_delay
else:  # BALANCED
    final_delay = max(gcra_delay, window_delay)
```

**장점**:
- 사용 시나리오별 선택 가능
- 기존 동작 유지 옵션 제공

**단점**:
- 설정 복잡도 증가
- 최적 모드 선택 어려움

---

### **Option 3: 가중치 기반 통합**
```python
# 알고리즘별 가중치 적용
gcra_weight = config.gcra_priority_weight    # 예: 0.7
window_weight = config.window_priority_weight # 예: 0.3

# 가중 평균으로 최종 지연 계산
final_delay = (gcra_delay * gcra_weight + window_delay * window_weight)
```

**장점**:
- 세밀한 밸런스 조정 가능
- 두 알고리즘 장점 모두 활용

**단점**:
- 복잡도 증가
- 가중치 튜닝 필요
- 직관적이지 않은 동작

---

### **Option 4: 단계별 필터링**
```python
# 1단계: 윈도우 pre-filter (빠른 거부)
if not self._has_empty_slots(group):
    # 윈도우 가득참 → 상세 시차 계산
    window_delay = self._calculate_timestamp_gap_delay(...)
    if window_delay > 0:
        return False, current_time + window_delay

# 2단계: GCRA 정밀 제어 (윈도우 통과시에만)
return await self._gcra_token_check(group, now, current_rate_ratio)
```

**장점**:
- 성능 최적화 (early return)
- 명확한 단계별 처리

**단점**:
- GCRA 버스트 허용 제한
- 복잡한 코드 구조

---

## 🔧 **구현 우선순위**

### **Phase 1: 즉시 적용 (권장: Option 1)**
```python
# UnifiedRateLimiterConfig에 추가
hybrid_decision_mode: str = "window_priority"  # "gcra_priority", "balanced"

# _consume_single_token_atomic 수정
if config.hybrid_decision_mode == "window_priority":
    if window_delay > 0:
        final_delay = window_delay
    else:
        final_delay = gcra_delay
```

### **Phase 2: 성능 최적화**
- 조건부 알고리즘 실행
- early return 패턴 적용
- 불필요한 계산 제거

### **Phase 3: 고급 기능 (필요시)**
- 가중치 기반 통합
- 동적 모드 전환
- 실시간 성능 모니터링

---

## 📊 **성능 및 일관성 개선 예상 효과**

### **성능 개선**
- CPU 사용률: 15-25% 감소 (조건부 실행)
- 메모리 사용: 5-10% 감소 (중복 계산 제거)
- 레이턴시: 10-20% 개선 (early return)

### **일관성 개선**
- 버스트 정책 명확화
- 예측 가능한 동작
- 디버깅 용이성 향상

### **유지보수성**
- 코드 복잡도 감소
- 테스트 시나리오 단순화
- 문제 진단 용이

---

## 🚀 **추천 실행 계획**

1. **즉시**: Option 1 (역할 분담) 구현 및 테스트
2. **1주 후**: 성능 벤치마크 및 피드백 수집
3. **필요시**: Option 2 (선택 모드) 추가 구현
4. **장기**: 실제 운영 데이터 기반 최적화

---

## ⚠️ **주의사항**

- **기존 동작 호환성**: 기본값은 현재 방식 유지
- **테스트 필수**: 극한 버스트 시나리오 검증
- **모니터링**: 변경 후 429 에러율 추적
- **롤백 준비**: 문제 발생시 즉시 되돌리기 가능하도록

---

**작성일**: 2025년 9월 15일
**상태**: 추가 토의 필요
**우선순위**: 높음 (성능 및 일관성 개선)
