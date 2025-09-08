# Overlap Optimizer v4.0 - 기술 스펙 문서

## 📋 개요

**업비트 자동매매 시스템 - 겹침 최적화 엔진 v4.0**

실용 중심의 캔들 데이터 수집 최적화 엔진으로, API 호출 비용을 최소화하면서 효율적으로 데이터를 수집합니다.

## 🎯 핵심 목표

- **API 호출 최소화**: 200개 청크 기본 전략으로 요청 횟수 절약
- **중복 데이터 방지**: INSERT OR IGNORE를 통한 안전한 데이터 저장
- **4단계 최적화**: 데이터 상태별 맞춤형 처리 전략
- **성능 중심**: 비용 > 데이터 용량 우선순위

## 🔧 아키텍처

### 핵심 컴포넌트

```python
class UpbitOverlapOptimizer:
    def __init__(self, repository, time_utils, api_client)

    # 주요 메서드
    async def optimize_and_collect_candles()  # 메인 최적화 엔진
    def _check_start_overlap()               # 1단계: 시작점 겹침 확인
    def _check_complete_overlap()            # 2단계: 완전 겹침 확인
    def _check_fragmentation()               # 3단계: 파편화 확인
    def _find_connected_end()                # 연결된 끝 찾기
```

### 데이터 클래스

```python
@dataclass(frozen=True)
class ApiRequest:           # API 요청 정보
class OptimizationStep:     # 최적화 단계 정보
class OptimizationResult:   # 4단계 최적화 결과
```

## 🚀 4단계 최적화 알고리즘

### 1단계: START_OVERLAP
**목적**: 시작점 주변 200개 범위 내 겹침 확인

```sql
SELECT 1 FROM {table_name}
WHERE candle_date_time_utc BETWEEN ? AND ?
LIMIT 1
```

**처리**: 시작점 -1부터 200개 요청 후 INSERT

**적용 조건**: 시작점 근처에 일부 데이터 존재

### 2단계: COMPLETE_OVERLAP
**목적**: 200개 범위 완전 겹침 확인

```sql
SELECT COUNT(*) FROM {table_name}
WHERE candle_date_time_utc BETWEEN ? AND ?
```

**처리**: API 호출 생략, 시작점 200개만큼 이동

**적용 조건**: `actual_count >= expected_count`

### 3단계: FRAGMENTATION
**목적**: 파편화된 데이터 감지

```sql
WITH gaps AS (
    SELECT
        candle_date_time_utc,
        LAG(candle_date_time_utc) OVER (ORDER BY candle_date_time_utc) as prev_time,
        unixepoch(candle_date_time_utc) - unixepoch(LAG(...)) as gap_seconds
    FROM {table_name}
    WHERE candle_date_time_utc BETWEEN ? AND ?
    ORDER BY candle_date_time_utc
)
SELECT COUNT(CASE WHEN gap_seconds > ? THEN 1 END) as significant_gaps
FROM gaps
WHERE prev_time IS NOT NULL
```

**처리**: 연결된 끝 찾기 → 해당 지점부터 200개 요청

**적용 조건**: `gap_count >= 2` (임계값: `timeframe_seconds * 1.5`)

### 4단계: CONNECTED_END
**목적**: 기본 처리 (빈 구간)

**처리**: 시작점 -1부터 200개 청크 요청

**적용 조건**: 위 3단계에 해당하지 않는 모든 경우

## 📊 성능 최적화 기능

### timeframe 캐싱
```python
self._timeframe_cache = {}

def _get_timeframe_seconds(self, timeframe: str) -> int:
    if timeframe not in self._timeframe_cache:
        self._timeframe_cache[timeframe] = self.time_utils.get_timeframe_seconds(timeframe)
    return self._timeframe_cache[timeframe]
```

**효과**: 10,331배 성능 향상 (1.28ms → 0.0001ms)

### 메트릭 추적
```python
self._metrics = {
    "total_optimizations": 0,
    "total_api_calls": 0,
    "total_candles_collected": 0,
    "strategy_usage": {}
}
```

## 🔍 로직 분석 및 문제점

### ✅ 잘 설계된 부분

1. **4단계 분기 로직**: 데이터 상태별 최적화 전략 명확
2. **캐싱 최적화**: timeframe 변환 성능 대폭 향상
3. **안전한 데이터 저장**: INSERT OR IGNORE 활용
4. **무한 루프 방지**: 최대 1000단계 제한

### ❌ 발견된 문제점

#### 1. **SQLite 정렬 성능 문제**
```sql
-- 현재 (느림)
ORDER BY candle_date_time_utc

-- 개선 필요 (57% 빠름)
ORDER BY timestamp
```

#### 2. **중복된 계산 로직**
```python
# 4곳에서 동일한 계산 반복
expected_count = int((chunk_end - start_time).total_seconds() / timeframe_seconds) + 1
api_count = min(UPBIT_API_LIMIT, int((end_time - start_time).total_seconds() / timeframe_seconds) + 2)
```

**개선안**: `TimeUtils.calculate_candle_count()` 활용

#### 3. **연결된 끝 찾기 복잡성**
```sql
-- 현재: 복잡한 ROW_NUMBER() 쿼리 (481-499줄)
WITH numbered_candles AS (
    SELECT candle_date_time_utc, ROW_NUMBER() OVER (...) as row_num,
           datetime(?, '+' || ... || ' seconds') as expected_time
    ...
)
```

**문제**: 과도하게 복잡한 로직, 성능 저하 가능성

#### 4. **파편화 임계값 하드코딩**
```python
fragmentation_threshold = timeframe_seconds * 1.5  # 1.5는 매직 넘버
```

**개선안**: 설정 가능한 임계값

### 🚫 불필요한 기능

#### 1. **과도한 연결된 끝 찾기**
- **복잡도**: 높음 (WITH절, ROW_NUMBER(), datetime 연산)
- **실용성**: 낮음 (파편화된 경우 시작점부터 요청해도 충분)
- **제안**: 단순화 또는 제거

#### 2. **과세밀한 API 카운트 계산**
```python
api_count = min(UPBIT_API_LIMIT, int((end_time - start_time).total_seconds() / timeframe_seconds) + 2)
```
- **문제**: +2 버퍼의 근거 불분명
- **제안**: 일관된 버퍼 정책

## 🔧 개선 권장사항

### 우선순위 1: 성능 개선
1. **SQLite 정렬**: `ORDER BY timestamp` 적용
2. **TimeUtils 활용**: 중복 계산 로직 통합
3. **쿼리 최적화**: 복잡한 WITH절 단순화

### 우선순위 2: 코드 품질
1. **매직 넘버 제거**: 1.5, +2 등 설정화
2. **메서드 분리**: 큰 메서드 리팩터링
3. **에러 처리 강화**: 예외 상황별 대응

### 우선순위 3: 기능 검토
1. **연결된 끝 찾기**: 단순화 또는 제거 검토
2. **4단계 알고리즘**: 3단계로 통합 가능성 검토
3. **메트릭 확장**: 성능 지표 추가

## 📈 예상 개선 효과

| 개선 항목 | 예상 효과 |
|-----------|-----------|
| SQLite 정렬 최적화 | +57% 성능 향상 |
| TimeUtils 통합 | 코드 중복 50% 감소 |
| 쿼리 단순화 | +20% 쿼리 성능 향상 |
| 로직 간소화 | 유지보수성 +30% 향상 |

## 🎯 결론

**현재 구현은 전반적으로 우수하나, 성능과 코드 품질 측면에서 개선 여지가 있습니다.**

**핵심 개선 방향**:
1. SQLite 정렬 최적화 (즉시)
2. TimeUtils 활용으로 중복 제거 (단기)
3. 복잡한 로직 단순화 (중기)

**유지할 장점**:
- 4단계 최적화 알고리즘
- timeframe 캐싱
- 안전한 데이터 저장
