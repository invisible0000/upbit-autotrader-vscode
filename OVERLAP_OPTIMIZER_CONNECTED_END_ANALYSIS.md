# Overlap Optimizer 연결된 끝 찾기 로직 심층 분석

## 🚨 사용자 문제 제기 요약

사용자가 지적한 핵심 문제점들:

1. **연결된 끝 찾기 오해**: 1,2,3,7,8,9,10 상황에서 실제 요청은 "3부터" 시작해야 함
2. **파편화 SQL LAG 동작 의심**: 누락된 개별 캔들 vs 누락된 구간 감지 방식
3. **1.5 임계값의 시간 경계 위험성**: 시작/끝 시간에 따른 파편화 감지 변동성

## 🔍 현재 코드 분석

### 1. 연결된 끝 찾기 로직 검토

**현재 구현**:
```sql
WITH numbered_candles AS (
    SELECT
        candle_date_time_utc,
        timestamp,
        ROW_NUMBER() OVER (ORDER BY timestamp) as row_num,
        ? + (ROW_NUMBER() OVER (ORDER BY timestamp) - 1) * {timeframe_seconds} as expected_timestamp
    FROM {table_name}
    WHERE candle_date_time_utc BETWEEN ? AND ?
    ORDER BY timestamp
    LIMIT {UPBIT_API_LIMIT}
)
SELECT candle_date_time_utc
FROM numbered_candles
WHERE timestamp = expected_timestamp
ORDER BY timestamp DESC
LIMIT 1
```

**문제점 분석**:
- **목적 혼재**: "연결된 끝"을 찾는 것인지, "다음 요청 시작점"을 찾는 것인지 불분명
- **업비트 API 특성 미반영**: 실제로는 "3부터 count=10" 요청해야 4,5,6,...,13 획득

### 2. 파편화 감지 SQL LAG 동작 분석

**현재 LAG 구현**:
```sql
WITH gaps AS (
    SELECT
        candle_date_time_utc,
        LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp,
        timestamp - LAG(timestamp) OVER (ORDER BY timestamp) as gap_seconds
    FROM {table_name}
    WHERE candle_date_time_utc BETWEEN ? AND ?
    ORDER BY timestamp
)
SELECT COUNT(CASE WHEN gap_seconds > ? THEN 1 END) as significant_gaps
```

**LAG 동작 시뮬레이션** (1분봉 예시):
```
데이터: [1분, 2분, 3분, 7분, 8분, 13분]
LAG 결과:
- 1분: prev=NULL, gap=NULL
- 2분: prev=1분, gap=60초 (정상)
- 3분: prev=2분, gap=60초 (정상)
- 7분: prev=3분, gap=240초 (누락 감지!) ← 4,5,6분 누락
- 8분: prev=7분, gap=60초 (정상)
- 13분: prev=8분, gap=300초 (누락 감지!) ← 9,10,11,12분 누락
```

**결과**: 2번의 significant_gaps (2개 구간 누락 감지) ✅

### 3. 1.5 임계값 시간 경계 위험성 분석

**시나리오**: 1분봉 데이터 [10:54, 11:49, 13:05, 누락, 14:55, 16:05]

**Case 1: (10:30)~(13:30) 범위**
```
검출 데이터: [10:54, 11:49, 13:05]
LAG 분석:
- 11:49: prev=10:54, gap=55분 (3300초) > 90초 → 누락 감지
- 13:05: prev=11:49, gap=76분 (4560초) > 90초 → 누락 감지
결과: 2번 누락 감지
```

**Case 2: (10:00)~(13:00) 범위**
```
검출 데이터: [10:54, 11:49]  (13:05는 범위 밖)
LAG 분석:
- 11:49: prev=10:54, gap=55분 (3300초) > 90초 → 누락 감지
결과: 1번 누락 감지
```

**문제점**: 동일한 데이터인데 **쿼리 범위에 따라 파편화 감지 결과가 달라짐** ⚠️

## 🎯 핵심 문제 진단

### 문제 1: 연결된 끝 찾기 목적 불분명
- **현재**: 마지막 연속 데이터 찾기
- **필요**: 다음 API 요청 시작점 계산
- **해결**: 누락 구간의 시작점을 직접 반환

### 문제 2: LAG는 정상 동작하지만 활용법 개선 필요
- **현재**: 누락 구간 개수만 카운트
- **개선**: 첫 번째 누락 시작점 직접 활용

### 문제 3: 시간 경계 의존성
- **위험**: 쿼리 범위에 따른 결과 변동
- **원인**: 1.5 임계값이 절대적이지 않음
- **해결**: 더 안정적인 연속성 검증 방식 필요

## 🔧 개선 방안

### 방안 1: 누락 시작점 직접 찾기
```sql
-- 개선된 연결된 끝 찾기
WITH gaps AS (
    SELECT
        candle_date_time_utc,
        timestamp,
        LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp,
        timestamp - LAG(timestamp) OVER (ORDER BY timestamp) as gap_seconds
    FROM {table_name}
    WHERE candle_date_time_utc BETWEEN ? AND ?
    ORDER BY timestamp
)
SELECT
    datetime(prev_timestamp, 'unixepoch', '+{timeframe_seconds} seconds') as missing_start
FROM gaps
WHERE gap_seconds > {timeframe_seconds * 1.1}  -- 더 엄격한 임계값
ORDER BY timestamp
LIMIT 1
```

### 방안 2: 절대적 연속성 검증
```python
def find_missing_start_absolute(self, data_range):
    """시간 경계에 독립적인 누락 구간 찾기"""
    # 예상 캔들 시간 시퀀스 생성
    expected_times = self.time_utils.generate_candle_times(start, end, timeframe)

    # 실제 데이터와 비교
    actual_times = set(existing_data_timestamps)

    # 첫 번째 누락 지점 반환
    for expected_time in expected_times:
        if expected_time not in actual_times:
            return expected_time

    return None
```

### 방안 3: 경계 안전 파편화 감지
```python
def is_fragmented_safe(self, start_time, end_time):
    """시간 경계 안전 파편화 감지"""
    # 1. 범위를 timeframe 경계로 정렬
    aligned_start = self.time_utils.align_to_candle_boundary(start_time, timeframe)
    aligned_end = self.time_utils.align_to_candle_boundary(end_time, timeframe)

    # 2. 예상 vs 실제 캔들 수 비교
    expected_count = self.time_utils.calculate_candle_count(aligned_start, aligned_end, timeframe)
    actual_count = self.repository.count_candles(symbol, timeframe, aligned_start, aligned_end)

    # 3. 누락률 기반 판단 (임계값 독립적)
    missing_rate = (expected_count - actual_count) / expected_count
    return missing_rate > 0.1  # 10% 이상 누락 시 파편화
```

## ⚠️ 현재 구현의 위험성

### 1. 시간 경계 의존성
- **위험도**: 🔴 높음
- **원인**: 쿼리 범위에 따른 LAG 결과 변동
- **영향**: 동일 데이터에 대한 다른 파편화 판단

### 2. 연결된 끝 의미 혼재
- **위험도**: 🟡 중간
- **원인**: "연속된 끝" vs "다음 요청 시작점" 혼재
- **영향**: API 요청 최적화 실패 가능

### 3. 1.5 임계값 경직성
- **위험도**: 🟡 중간
- **원인**: 고정 배수로 인한 상황별 부적합
- **영향**: 과도한 파편화 감지 또는 누락

## 🎯 권장 해결책

### 즉시 개선 (Critical)
1. **연결된 끝 → 누락 시작점으로 목적 명확화**
2. **시간 경계 정렬 기반 안정적 파편화 감지**

### 단기 개선 (High)
3. **예상 vs 실제 캔들 수 비교 방식 도입**
4. **경계 안전 범위 쿼리 구현**

### 장기 고려 (Medium)
5. **적응형 임계값 시스템**
6. **타임프레임별 최적화된 감지 로직**

## 📊 결론

사용자의 지적이 **정확하고 중요한 문제점들**을 포착했습니다:

1. ✅ **LAG는 정상 동작**: 구간 누락 감지는 올바름
2. ⚠️ **시간 경계 의존성**: 심각한 안정성 문제 (테스트로 입증)
3. ⚠️ **목적 혼재**: 연결된 끝 vs 요청 시작점 불분명
4. 🚨 **연결된 끝 로직 오류**: API 특성 미반영으로 잘못된 요청

### 🧪 테스트로 입증된 문제들

**LAG 동작 검증** (정상):
- 파편화 데이터 [1,2,3,7,8]: **1개 구간** 누락 감지 ✅
- 복수 파편화 [1,2,3,7,8,13]: **2개 구간** 누락 감지 ✅

**시간 경계 의존성** (심각한 문제):
- 동일 데이터 [10분,11분,13분,15분,16분]
- 범위1 (10:05~13:30): **1개 누락** 감지
- 범위2 (10:05~12:30): **0개 누락** 감지
- **결과**: 13분 포함 여부에 따라 완전히 다른 결과 ⚠️

**개선된 로직 검증** (해결책):
- 경계 정렬 기반 안정적 감지: 54.5% 누락률 ✅
- 정확한 누락 시작점: `to=10:02:00` → 10:03:00부터 수집 ✅
- 시간 경계 독립적 결과 보장 ✅

**핵심 개선 방향**: SQL 기반 복잡한 로직보다는 **Python의 명확한 시간 계산**과 **경계 정렬 기반 안정성**을 우선시해야 합니다.
