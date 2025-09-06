# 🎯 OverlapAnalyzer 상세 기능 명세서

## 📋 **개요**
OverlapAnalyzer는 요청된 캔들 데이터와 DB 기존 데이터 간의 겹침을 분석하여 API 호출을 최적화하는 핵심 모듈입니다. 업비트 API의 200개 제한을 고려한 청크 기반 최적화 전략을 구현합니다.

---

## 🔍 **핵심 문제 정의**

### **업비트 API 제약사항**
- **최대 200개**: 한 번에 최대 200개 캔들만 조회 가능
- **Rate Limit**: 600req/min (초당 10req)
- **시간 역순**: 최신 데이터부터 과거 순으로 반환

### **DB 파편화 시나리오**
```
요청: KRW-BTC 1m 2024-01-01 09:00 ~ 09:30 (30개)
DB 현재 상태:
┌─────────────────────────────────────────────────────────┐
│ 09:00│09:01│09:02│     │09:15│09:16│     │09:28│09:29│ │
│  ✓  │  ✓  │  ✓  │ ... │  ✓  │  ✓  │ ... │  ✓  │  ✓  │ │
└─────────────────────────────────────────────────────────┘
     존재    존재    누락      존재   누락      존재   누락

파편화 문제:
1. 09:03~09:14 구간 누락 (12개)
2. 09:17~09:27 구간 누락 (11개)
3. 09:30 누락 (1개)
```

### **최적화 전략 선택**
1. **개별 요청**: 3번 API 호출 (비효율)
2. **전체 요청**: 200개 요청 후 필터링 (과도)
3. **지능형 청크**: 겹침 분석 후 최적 구간 결정 ⭐

---

## 🧠 **겹침 분석 패턴 (6가지)**

### **Pattern 1: COMPLETE_OVERLAP (완전 포함)**
```
요청 구간: [09:00 ~ 09:05]
DB 데이터: [09:00, 09:01, 09:02, 09:03, 09:04, 09:05]
결과: API 호출 불필요 → 캐시/DB 응답
```

### **Pattern 2: NO_OVERLAP (완전 분리)**
```
요청 구간: [09:00 ~ 09:05]
DB 데이터: [10:00, 10:01, 10:02, ...]
결과: 전체 API 요청 필요
```

### **Pattern 3: PARTIAL_OVERLAP_START (앞부분 겹침)**
```
요청 구간: [09:00 ~ 09:10]
DB 데이터: [09:00, 09:01, 09:02]
누락 구간: [09:03 ~ 09:10]
최적화: 09:03부터 API 요청
```

### **Pattern 4: PARTIAL_OVERLAP_END (뒷부분 겹침)**
```
요청 구간: [09:00 ~ 09:10]
DB 데이터: [09:08, 09:09, 09:10]
누락 구간: [09:00 ~ 09:07]
최적화: 09:00~09:07만 API 요청
```

### **Pattern 5: PARTIAL_OVERLAP_MIDDLE (중간 겹침)**
```
요청 구간: [09:00 ~ 09:10]
DB 데이터: [09:03, 09:04, 09:05]
누락 구간: [09:00~09:02] + [09:06~09:10]
최적화: 2개 구간 개별 요청 vs 전체 요청 비교
```

### **Pattern 6: FRAGMENTED_OVERLAP (파편화 겹침)**
```
요청 구간: [09:00 ~ 09:20]
DB 데이터: [09:00, 09:02, 09:05, 09:18, 09:20]
누락 구간: [09:01, 09:03~09:04, 09:06~09:17, 09:19]
최적화: 청크 분할 vs 전체 요청 비교 결정
```

---

## ⚙️ **최적화 결정 알고리즘**

### **Step 1: 요청 분석**
```python
class RequestAnalysis:
    requested_range: TimeRange      # 요청된 시간 구간
    requested_count: int            # 요청된 캔들 개수
    interval_minutes: int           # 캔들 간격 (1m=1, 5m=5)
    max_api_limit: int = 200        # 업비트 API 제한
```

### **Step 2: DB 현황 분석**
```python
class DBAnalysis:
    existing_candles: List[datetime]    # DB에 이미 있는 캔들 시간들
    missing_ranges: List[TimeRange]     # 누락된 시간 구간들
    fragmentation_ratio: float          # 파편화 비율 (0.0~1.0)
    total_gaps: int                     # 전체 누락 개수
```

### **Step 3: 비용 계산**
```python
class CostAnalysis:
    individual_requests: int        # 개별 요청시 API 호출 수
    bulk_request_cost: int         # 전체 요청시 비용 (중복 데이터 포함)
    optimal_strategy: str          # 최적 전략
    estimated_savings: float       # 예상 절약률 (%)
```

### **Step 4: 전략 결정**
```python
def decide_strategy(request: RequestAnalysis, db: DBAnalysis) -> Strategy:
    # 1. 완전 포함 체크
    if db.fragmentation_ratio == 0.0:
        return Strategy.CACHE_ONLY

    # 2. 요청 크기가 200개 이하 + 파편화 심각
    if request.requested_count <= 200 and db.fragmentation_ratio > 0.7:
        return Strategy.BULK_REQUEST

    # 3. 누락 구간이 연속적
    if len(db.missing_ranges) <= 2:
        return Strategy.TARGETED_REQUESTS

    # 4. 복잡한 파편화 → 비용 비교
    return compare_costs(request, db)
```

---

## 🔧 **구현 핵심 로직**

### **1. 시간 구간 분석**
```python
def analyze_time_gaps(requested_times: List[datetime],
                     existing_times: List[datetime]) -> List[TimeRange]:
    """누락된 시간 구간 탐지"""
    missing_ranges = []

    for req_time in requested_times:
        if req_time not in existing_times:
            # 연속된 누락 구간으로 병합
            merge_or_create_range(missing_ranges, req_time)

    return missing_ranges
```

### **2. 청크 분할 최적화**
```python
def optimize_chunks(missing_ranges: List[TimeRange],
                   api_limit: int = 200) -> List[APIRequest]:
    """200개 제한 고려한 최적 청크 분할"""
    requests = []

    for range in missing_ranges:
        chunk_count = calculate_chunk_count(range)

        if chunk_count <= api_limit:
            # 단일 요청 가능
            requests.append(create_api_request(range))
        else:
            # 분할 필요
            sub_chunks = split_range(range, api_limit)
            requests.extend(sub_chunks)

    return requests
```

### **3. 겹침 처리 전략**
```python
def handle_overlap_strategy(existing_data: List[Candle],
                           new_data: List[Candle]) -> List[Candle]:
    """겹치는 데이터 처리 방식 결정"""

    # 전략 1: 기존 데이터 우선 (DB 신뢰)
    if prefer_existing_data:
        return merge_prefer_existing(existing_data, new_data)

    # 전략 2: 신규 데이터 우선 (최신성 보장)
    if prefer_new_data:
        return merge_prefer_new(existing_data, new_data)

    # 전략 3: 타임스탬프 기준 정합성 검증
    return merge_with_validation(existing_data, new_data)
```

---

## 📊 **성능 최적화 지표**

### **최적화 효과 측정**
```python
@dataclass
class OptimizationMetrics:
    original_api_calls: int         # 기존 방식 API 호출 수
    optimized_api_calls: int        # 최적화 후 API 호출 수
    reduction_percentage: float     # 감소율 (%)
    saved_requests: int             # 절약된 요청 수
    processing_time_ms: float       # 분석 처리 시간
    cache_hit_improvement: float    # 캐시 히트율 개선
```

### **성공 기준**
- **API 호출 50% 감소**: 기존 대비 절반 이하 호출
- **분석 처리 시간 < 50ms**: 실시간 응답성 보장
- **메모리 사용량 < 10MB**: 분석 과정 메모리 효율성
- **정확도 100%**: 누락 데이터 없는 완전한 커버리지

---

## 🧪 **테스트 시나리오**

### **시나리오 1: 완전 캐시 히트**
```python
# Given: DB에 요청 구간 데이터 완전 존재
db_data = ["09:00", "09:01", "09:02", "09:03", "09:04"]
request = ("09:00", "09:04", count=5)

# When: OverlapAnalyzer 분석
result = analyzer.analyze(request, db_data)

# Then: API 호출 없음
assert result.strategy == "CACHE_ONLY"
assert result.api_calls == 0
```

### **시나리오 2: 파편화 데이터 최적화**
```python
# Given: 파편화된 DB 데이터
db_data = ["09:00", "09:02", "09:05", "09:07"]
request = ("09:00", "09:10", count=11)

# When: 최적화 분석
result = analyzer.analyze(request, db_data)

# Then: 최적화된 요청 생성
assert result.missing_ranges == [("09:01", "09:01"), ("09:03", "09:04"), ...]
assert result.api_calls < 3  # 개별 요청보다 효율적
```

### **시나리오 3: 대용량 요청 처리**
```python
# Given: 500개 요청 (200개 제한 초과)
request = ("09:00", "17:00", count=480)  # 8시간 1분봉

# When: 청크 분할 최적화
result = analyzer.analyze(request, [])

# Then: 적절한 청크 분할
assert len(result.api_requests) == 3  # 200+200+80 분할
assert all(req.count <= 200 for req in result.api_requests)
```

---

## ⚠️ **위험 요소 및 대응**

### **High Risk**
1. **복잡도 폭증**
   - **위험**: 파편화 패턴 조합이 기하급수적 증가
   - **대응**: 최대 분석 시간 50ms 제한, 초과시 기본 전략 사용

2. **메모리 사용량 급증**
   - **위험**: 대용량 시간 구간 분석시 메모리 부족
   - **대응**: 스트리밍 방식 분석, 10MB 제한

### **Medium Risk**
1. **시간 계산 오류**
   - **위험**: 캔들 경계 정렬 실수로 중복/누락 발생
   - **대응**: time_utils.py 철저한 테스트, 경계값 검증

2. **DB 상태 변화**
   - **위험**: 분석 중 DB 데이터 변경으로 분석 결과 무효화
   - **대응**: 분석 시점 스냅샷 고정, 낙관적 락 적용

---

## 🎯 **구현 우선순위**

### **Phase 1: 기본 패턴 구현** (2일)
- COMPLETE_OVERLAP, NO_OVERLAP 구현
- 기본 시간 구간 분석 로직
- 단순 최적화 전략

### **Phase 2: 고급 패턴 구현** (2일)
- PARTIAL_OVERLAP 변형들 구현
- 청크 분할 최적화 로직
- 비용 계산 알고리즘

### **Phase 3: 파편화 처리** (1일)
- FRAGMENTED_OVERLAP 구현
- 복잡한 파편화 시나리오 처리
- 성능 최적화 및 테스트

**🎯 결론**: OverlapAnalyzer는 API 비용 50% 절감의 핵심이지만, 구현 복잡도가 높으므로 단계적 접근과 철저한 테스트가 필수입니다.
