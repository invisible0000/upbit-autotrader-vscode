# 베이직 수집 테스트 시나리오 문서

## 목적
CandleDataProvider의 기본 수집 동작을 검증하기 위한 겹침 없는 순수 수집 테스트

## 공통 설정
- **심볼**: KRW-BTC
- **타임프레임**: 1m
- **기준 종료 시간**: `2025-09-08T00:00:00` (UTC)
- **수집 방향**: 역순 (종료 시간부터 과거로)

---

## 테스트 시나리오 1: 겹침없이 그냥 수집 100개

### 전제조건
- `candles_KRW_BTC_1m` 테이블 완전 비움

### 실행
```python
response = await provider.get_candles(
    symbol="KRW-BTC",
    timeframe="1m",
    count=100,
    end_time=datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc)
)
```

### 검증 기준
1. **DB 레코드 수**: ≥ 100개
   - *수집량과 저장량은 다를 수 있음 (청크 전략)*
2. **시간 범위 포함**: `2025-09-08T00:00:00` ~ `2025-09-07T22:21:00`
   - *100개 = 1시간 39분 구간*
3. **API 요청**: 1회 (새 DB이므로 API 필수)
4. **응답 성공**: `response.success = True`

---

## 테스트 시나리오 2: 겹침없이 그냥 수집 200개

### 전제조건
- `candles_KRW_BTC_1m` 테이블 완전 비움

### 실행
```python
response = await provider.get_candles(
    symbol="KRW-BTC",
    timeframe="1m",
    count=200,
    end_time=datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc)
)
```

### 검증 기준
1. **DB 레코드 수**: ≥ 200개
2. **시간 범위 포함**: `2025-09-08T00:00:00` ~ `2025-09-07T20:41:00`
   - *200개 = 3시간 19분 구간*
3. **API 요청**: 1회 (200개 청크 1개)
4. **응답 성공**: `response.success = True`

---

## 테스트 시나리오 3: 겹침없이 그냥 수집 300개

### 전제조건
- `candles_KRW_BTC_1m` 테이블 완전 비움

### 실행
```python
response = await provider.get_candles(
    symbol="KRW-BTC",
    timeframe="1m",
    count=300,
    end_time=datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc)
)
```

### 검증 기준
1. **DB 레코드 수**: ≥ 300개
2. **시간 범위 포함**: `2025-09-08T00:00:00` ~ `2025-09-07T19:01:00`
   - *300개 = 4시간 59분 구간*
3. **API 요청**: 2회 (200개 + 100개 청크)
4. **응답 성공**: `response.success = True`

---

## 테스트 시나리오 4: 겹침없이 그냥 수집 1000개

### 전제조건
- `candles_KRW_BTC_1m` 테이블 완전 비움

### 실행
```python
response = await provider.get_candles(
    symbol="KRW-BTC",
    timeframe="1m",
    count=1000,
    end_time=datetime(2025, 9, 8, 0, 0, 0, tzinfo=timezone.utc)
)
```

### 검증 기준
1. **DB 레코드 수**: ≥ 1000개
2. **시간 범위 포함**: `2025-09-08T00:00:00` ~ `2025-09-07T07:21:00`
   - *1000개 = 16시간 39분 구간*
3. **API 요청**: 5회 (200×4 + 200×1 청크)
4. **응답 성공**: `response.success = True`

---

## 핵심 검증 포인트

### ✅ 성공 기준
- 요청한 `count` 이상의 DB 레코드 생성
- 계산된 시간 범위가 DB에 존재
- 예상 API 요청 횟수와 일치
- 응답 객체가 성공 상태

### ❌ 실패 징후
- DB 레코드 수 < 요청 count
- 시간 범위 누락 또는 공백
- API 요청 횟수 불일치
- 응답 실패 또는 오류

---

## 시간 계산 공식
```
종료_시간 = 2025-09-08T00:00:00
시작_시간 = 종료_시간 - (count - 1) 분
구간_시간 = (count - 1) 분 = count - 1 분
```

**예시:**
- 100개: `00:00:00` ~ `22:21:00` (전날)
- 200개: `00:00:00` ~ `20:41:00` (전날)
- 300개: `00:00:00` ~ `19:01:00` (전날)
- 1000개: `00:00:00` ~ `07:21:00` (전날)
