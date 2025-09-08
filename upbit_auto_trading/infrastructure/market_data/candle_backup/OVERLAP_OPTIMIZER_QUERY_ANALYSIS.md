# 📊 Overlap Optimizer 상태 확인 쿼리 해설

> **목적**: DB 비전문가도 overlap_optimizer.py의 4개 SQL 쿼리 동작과 잠재적 문제점을 이해할 수 있도록 돕는 문서

---

## 🔍 개요

`overlap_optimizer.py`는 업비트 캔들 데이터 수집 시 중복과 누락을 최소화하기 위해 4단계 최적화를 수행합니다. 각 단계는 특정 SQL 쿼리로 현재 상태를 확인하여 최적의 전략을 선택합니다.

### 4단계 최적화 전략
1. **START_OVERLAP**: 시작점 겹침 확인
2. **COMPLETE_OVERLAP**: 완전 겹침 확인
3. **FRAGMENTATION**: 파편화 확인
4. **CONNECTED_END**: 연결된 끝점 찾기

---

## 📋 쿼리 1: 시작점 겹침 확인 (START_OVERLAP)

### 쿼리 구조
```sql
SELECT 1 FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc BETWEEN '2024-01-01T00:00:00' AND '2024-01-01T03:19:00'
LIMIT 1
```

### 🎯 목적
- **질문**: "수집하려는 시간 범위에 이미 데이터가 있나요?"
- **답변**: 있으면 `1`, 없으면 빈 결과

### 🔧 동작 원리
1. 시작 시간부터 200개 캔들 범위 내에서 검색
2. 딱 1개만 찾으면 즉시 중단 (`LIMIT 1`)
3. 효율적: 존재 여부만 확인, 실제 데이터는 가져오지 않음

### ✅ 장점
- **매우 빠름**: 첫 번째 매칭 데이터를 찾으면 즉시 종료
- **메모리 효율적**: 실제 캔들 데이터를 읽지 않음
- **명확한 목적**: 단순한 존재 여부만 확인

### ⚠️ 잠재적 문제점
- **1초 타임프레임**: 거래가 없는 초가 많아 정상적인 "빈 구간"도 겹침으로 오인할 수 있음
- **인덱스 의존성**: `candle_date_time_utc` 컬럼에 인덱스가 없으면 전체 테이블 스캔 발생

---

## 📊 쿼리 2: 완전 겹침 확인 (COMPLETE_OVERLAP)

### 쿼리 구조
```sql
SELECT COUNT(*) FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc BETWEEN '2024-01-01T00:00:00' AND '2024-01-01T03:19:00'
```

### 🎯 목적
- **질문**: "예상되는 캔들 개수와 실제 저장된 개수가 일치하나요?"
- **답변**: 실제 저장된 캔들 개수 반환

### 🔧 동작 원리
1. 시간 범위 내 모든 캔들 개수를 세기
2. TimeUtils로 계산한 예상 개수와 비교
3. 일치하면 "완전 겹침"으로 판단

### ✅ 장점
- **정확성**: 실제 데이터 개수를 정확히 파악
- **완전성 검증**: 부분 겹침과 완전 겹침을 구분

### ⚠️ 잠재적 문제점
- **성능**: 범위 내 모든 레코드를 스캔해야 함
- **1초 타임프레임 이슈**:
  - 예상: 200개 (3분 20초 = 200초)
  - 실제: 150개 (거래가 없는 50초 제외)
  - → 완전 겹침이 아닌 것으로 잘못 판단
- **메모리 사용**: 큰 범위에서는 많은 메모리 필요

---

## 🧩 쿼리 3: 파편화 확인 (FRAGMENTATION)

### 쿼리 구조
```sql
WITH gaps AS (
    SELECT
        candle_date_time_utc,
        LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp,
        timestamp - LAG(timestamp) OVER (ORDER BY timestamp) as gap_seconds
    FROM candles_KRW_BTC_1m
    WHERE candle_date_time_utc BETWEEN '2024-01-01T00:00:00' AND '2024-01-01T03:19:00'
    ORDER BY timestamp
)
SELECT COUNT(CASE WHEN gap_seconds > 90 THEN 1 END) as significant_gaps
FROM gaps
WHERE prev_timestamp IS NOT NULL
```

### 🎯 목적
- **질문**: "저장된 데이터에 의미있는 시간 간격이 있나요?"
- **답변**: 임계값(1.5 × timeframe)을 초과하는 간격의 개수

### 🔧 동작 원리
1. **CTE (Common Table Expression)**: `gaps` 임시 테이블 생성
2. **LAG 윈도우 함수**: 이전 캔들의 timestamp 가져오기
3. **간격 계산**: 현재 - 이전 = 시간 차이 (초)
4. **임계값 비교**: 90초(1분 × 1.5) 초과하는 간격 찾기
5. **카운트**: 의미있는 간격이 2개 이상이면 "파편화"

### 📊 LAG 윈도우 함수 상세 동작

**LAG**는 "이전 행의 값을 가져오는" 윈도우 함수입니다. 마치 **시간 여행**을 해서 "바로 전 데이터"를 현재 행에서 볼 수 있게 해줍니다.

#### 1단계: 원본 데이터 예시
```
candle_date_time_utc    timestamp
2024-01-01T00:00:00    1704067200  (00:00:00)
2024-01-01T00:01:00    1704067260  (00:01:00)
2024-01-01T00:02:00    1704067320  (00:02:00)
2024-01-01T00:04:00    1704067440  (00:04:00)  ← 00:03:00 누락!
2024-01-01T00:05:00    1704067500  (00:05:00)
```

#### 2단계: LAG 함수 적용
```sql
LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp
```

**결과:**
```
candle_date_time_utc    timestamp    prev_timestamp    gap_seconds
2024-01-01T00:00:00    1704067200   NULL              NULL
2024-01-01T00:01:00    1704067260   1704067200        60초      ← 정상 (1분)
2024-01-01T00:02:00    1704067320   1704067260        60초      ← 정상 (1분)
2024-01-01T00:04:00    1704067440   1704067320        120초     ← 비정상! (2분)
2024-01-01T00:05:00    1704067500   1704067440        60초      ← 정상 (1분)
```

#### 3단계: 임계값 판단 (timeframe별 적응형)
- **1초 타임프레임**: 1.5초 초과 시 파편화
- **1분 타임프레임**: 90초(60 × 1.5) 초과 시 파편화
- **5분 타임프레임**: 450초(300 × 1.5) 초과 시 파편화

```python
# 올바른 임계값 계산
timeframe_seconds = get_timeframe_seconds(timeframe)  # 1s→1, 1m→60, 5m→300
threshold = timeframe_seconds * 1.5
```

#### 4단계: CASE 조건부 카운팅
```sql
COUNT(CASE WHEN gap_seconds > threshold THEN 1 END)
-- gap_seconds > 90이면 1, 아니면 NULL
-- COUNT는 NULL을 제외하고 1만 세기
```

**실제 계산:**
```
gap_seconds: 60, 60, 120, 60
90초 초과?: 아니오, 아니오, 예, 아니오
카운트: 0, 0, 1, 0
최종 결과: significant_gaps = 1
```

### ✅ 장점
- **정교한 분석**: 실제 시간 간격을 분석하여 파편화 정확히 탐지
- **유연한 임계값**: timeframe에 따라 적응적 임계값 설정

### ⚠️ 잠재적 문제점
- **복잡성**: CTE + 윈도우 함수로 가장 복잡한 쿼리
- **성능 오버헤드**:
  - 전체 데이터 정렬 필요
  - 각 행마다 이전 행과 비교 연산
  - 200개 × 윈도우 함수 연산
- **임계값 하드코딩**: 90초로 고정되어 1초 타임프레임에서 부적절
  - **1초 타임프레임**: 1.5초가 적절하지만 90초 사용으로 감지 실패
  - **현재 코드**: `timeframe_seconds * 1.5` 계산하지만 쿼리에는 90 하드코딩
- **비효율적 전체 스캔**: 2개 발견해도 끝까지 계속 스캔
  - **개선 가능**: 2번째 간격 발견 시 즉시 종료 (`LIMIT 2` 활용)
- **끊어짐 위치 미활용**: 첫 번째 간격 위치를 기록하지 않아 CONNECTED_END에서 재계산
  - **개선 가능**: 첫 번째 끊어짐 위치를 반환하여 다음 단계에서 재사용
- **메모리 집약적**: 중간 결과를 메모리에 저장해야 함

### 💡 최적화 아이디어
1. **조기 종료**: `HAVING COUNT(...) >= 2` → 2개 발견 시 즉시 중단
2. **끊어짐 위치 반환**: 첫 번째 gap_seconds > threshold인 위치도 함께 반환
3. **적응형 임계값**: timeframe에 따른 동적 threshold 계산

---

## 🔗 쿼리 4: 연결된 끝점 찾기 (CONNECTED_END)

### 쿼리 구조
```sql
WITH numbered_candles AS (
    SELECT
        candle_date_time_utc,
        timestamp,
        ROW_NUMBER() OVER (ORDER BY timestamp) as row_num,
        1640995200 + (ROW_NUMBER() OVER (ORDER BY timestamp) - 1) * 60 as expected_timestamp
    FROM candles_KRW_BTC_1m
    WHERE candle_date_time_utc >= '2024-01-01T00:00:00'
        AND candle_date_time_utc <= '2024-01-01T03:19:00'
    ORDER BY timestamp
    LIMIT 200
)
SELECT candle_date_time_utc
FROM numbered_candles
WHERE timestamp = expected_timestamp
ORDER BY timestamp DESC
LIMIT 1
```

### 🎯 목적
- **질문**: "연속적으로 저장된 데이터의 마지막 지점은 어디인가요?"
- **답변**: 예상 시간과 실제 시간이 정확히 일치하는 마지막 캔들

### 🔧 동작 원리
1. **CTE**: `numbered_candles` 임시 테이블 생성
2. **ROW_NUMBER()**: 각 캔들에 순번 부여 (1, 2, 3, ...)
3. **expected_timestamp 계산**:
   - 시작점 + (순번-1) × timeframe초
   - 예: 1640995200 + (1-1) × 60 = 1640995200 (첫 번째)
   - 예: 1640995200 + (2-1) × 60 = 1640995260 (두 번째)
4. **정확성 검증**: 실제 timestamp와 expected_timestamp가 일치하는지 확인
5. **마지막 연속점**: 일치하는 것 중 가장 늦은 시간 반환

### ✅ 장점
- **정밀한 연속성 검증**: 시간 순서와 간격이 모두 정확한지 확인
- **연속 구간 식별**: 어디까지가 "믿을 수 있는" 연속 데이터인지 파악

### ⚠️ 잠재적 문제점
- **최고 복잡성**: 4개 쿼리 중 가장 복잡함
  - CTE + 윈도우 함수 + 계산 공식 + 조건 비교
- **성능 문제**:
  - ROW_NUMBER() 윈도우 함수로 전체 정렬 필요
  - 각 행마다 복잡한 계산 수행
  - expected_timestamp 계산 오버헤드
- **중복 계산**: FRAGMENTATION에서 이미 찾은 끊어짐 위치를 재계산
  - **비효율**: 파편화 단계에서 첫 번째 끊어짐을 찾았는데 다시 처음부터 스캔
  - **개선 가능**: 파편화 결과의 끊어짐 위치를 재사용하여 바로 연결된 끝 계산
- **1초 타임프레임 특수 문제**:
  - 거래가 없는 초는 timestamp가 존재하지 않음
  - expected_timestamp는 연속적이지만 실제는 불연속
  - → 연속점을 거의 찾지 못할 가능성
- **정확성 이슈**:
  - 시작점 timestamp를 하드코딩 (1640995200)
  - 시간대 변환 오류 가능성
  - 업비트 API의 실제 특성과 불일치 위험
- **불필요한 전체 검색**: 첫 번째 연결된 끝만 필요한데 모든 데이터 검사

---

## 🚨 1초 타임프레임의 특수 문제

### 근본적 특성
- **거래 기반**: 1초마다 반드시 거래가 있는 것이 아님
- **자연스러운 빈 구간**: 거래량이 적은 시간대에는 수십 초간 거래 없음
- **불규칙성**: 거래 패턴에 따라 데이터 밀도가 크게 달라짐

### 쿼리별 영향
1. **START_OVERLAP**: 정상적인 빈 구간을 겹침으로 오인
2. **COMPLETE_OVERLAP**: 예상 개수 불일치로 불완전 겹침 판단
3. **FRAGMENTATION**: 정상적인 거래 간격을 파편화로 오진단
4. **CONNECTED_END**: 연속점을 거의 찾지 못해 기능 무력화

---

## 💡 개선 방향 제안

### 1. TimeUtils 기반 단순화
- **복잡한 SQL → 간단한 Python**: 윈도우 함수 대신 TimeUtils 활용
- **boundary 정렬**: 업비트 API 특성에 맞는 시간 경계 사용
- **예측 가능성**: 복잡한 계산 로직을 투명하고 테스트 가능한 Python으로

### 2. 적응형 임계값 시스템
```python
def get_fragmentation_threshold(timeframe: str) -> int:
    """timeframe별 적응형 파편화 임계값"""
    timeframe_seconds = get_timeframe_seconds(timeframe)
    return int(timeframe_seconds * 1.5)

# 1s → 1.5초, 1m → 90초, 5m → 450초
```

### 3. 조기 종료 최적화
```sql
-- 현재: 모든 데이터 스캔 후 카운트
SELECT COUNT(CASE WHEN gap_seconds > ? THEN 1 END) FROM gaps

-- 개선: 2개 발견 시 즉시 중단
SELECT 1 FROM gaps WHERE gap_seconds > ? LIMIT 2
-- 결과가 2개면 파편화, 아니면 연속
```

### 4. 끊어짐 위치 재사용 시스템
```python
class FragmentationResult:
    has_fragmentation: bool
    first_gap_position: Optional[datetime]  # 첫 번째 끊어짐 위치
    gap_count: int

# FRAGMENTATION에서 반환
def check_fragmentation() -> FragmentationResult:
    # 첫 번째 gap > threshold 위치도 함께 반환

# CONNECTED_END에서 재사용
def find_connected_end(frag_result: FragmentationResult):
    if frag_result.first_gap_position:
        # 이미 알고 있는 끊어짐 위치 활용
        return frag_result.first_gap_position
    else:
        # 전체 연속 상태
```

### 5. 1초 타임프레임 특별 처리
- **거래 기반 로직**: 연속성 대신 거래 존재 여부 기준
- **유연한 임계값**: timeframe별 적응적 기준값
- **실용적 접근**: 완벽한 연속성보다 데이터 품질 중심

### 6. 성능 최적화
- **인덱스 최적화**: 자주 사용되는 컬럼에 복합 인덱스
- **쿼리 단순화**: 복잡한 CTE를 여러 단계로 분할
- **캐싱 활용**: 반복 계산 결과 메모리 캐싱
- **중복 제거**: 단계 간 결과 재사용으로 불필요한 재계산 방지

### 7. 관찰 가능성 개선
- **단계별 로깅**: 각 쿼리 실행 시간과 결과 기록
- **성능 모니터링**: 쿼리별 평균 실행 시간 추적
- **예외 상황 감지**: 비정상적인 결과 패턴 알림

---

## 📈 결론

현재 4개 쿼리는 각각 명확한 목적을 가지고 있지만, **복잡성과 1초 타임프레임 특성**으로 인해 다음 문제들이 예상됩니다:

### 주요 위험 요소
- **성능 저하**: 복잡한 윈도우 함수로 인한 실행 시간 증가
- **오진단**: 1초 타임프레임의 자연스러운 특성을 문제로 인식
- **유지보수성**: 복잡한 SQL 로직으로 디버깅과 수정 어려움

### 권장 사항
1. **단계적 단순화**: 가장 복잡한 쿼리 3, 4번부터 TimeUtils 기반으로 재작성
2. **적응형 임계값**: timeframe별 동적 계산 (1s→1.5초, 1m→90초)
3. **조기 종료**: 2번째 간격 발견 시 즉시 중단으로 성능 향상
4. **결과 재사용**: 파편화 단계의 끊어짐 위치를 연결된 끝 찾기에서 재활용
5. **성능 테스트**: 실제 데이터로 쿼리별 성능 측정 및 병목 지점 식별

> **핵심**: 복잡한 SQL 대신 검증된 TimeUtils + 명확한 Python 로직으로 더 안전하고 유지보수하기 쉬운 시스템 구축
> **최적화 포인트**: 임계값 적응화, 조기 종료, 결과 재사용으로 성능과 정확성 동시 개선
