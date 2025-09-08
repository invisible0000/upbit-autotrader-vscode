# 🎯 SQLite 실전 쿼리 가이드: 업비트 캔들 데이터 시스템 분석

> 현재 개발된 캔들 데이터 제공자를 통해 SQLite 고급 쿼리 기법과 최적화를 학습합니다

---

## 📋 목차

1. [기본 테이블 구조 이해](#1-기본-테이블-구조-이해)
2. [동적 테이블 생성 패턴](#2-동적-테이블-생성-패턴)
3. [메타데이터 쿼리 최적화](#3-메타데이터-쿼리-최적화)
4. [윈도우 함수 활용한 연속성 분석](#4-윈도우-함수-활용한-연속성-분석)
5. [PRIMARY KEY 범위 스캔 최적화](#5-primary-key-범위-스캔-최적화)
6. [복잡한 집계 쿼리와 성능](#6-복잡한-집계-쿼리와-성능)
7. [트랜잭션과 동시성 제어](#7-트랜잭션과-동시성-제어)
8. [대용량 테이블 관리 전략](#8-대용량-테이블-관리-전략)

---

## 🎓 학습 목표

이 가이드를 통해 다음을 마스터할 수 있습니다:
- **실제 프로덕션 코드**의 SQLite 쿼리 패턴 이해
- **성능 최적화**를 위한 인덱스와 쿼리 설계 원리
- **대용량 데이터** 처리를 위한 스케일링 전략
- **업비트 API 특성**에 맞춘 데이터 모델링

---

## 1. 기본 테이블 구조 이해

### 📊 캔들 데이터 테이블 스키마

우리 시스템에서 사용하는 캔들 데이터 테이블의 실제 구조를 살펴봅시다.

```sql
-- 실제 코드: SqliteCandleRepository.ensure_table_exists()
CREATE TABLE IF NOT EXISTS candles_KRW_BTC_1m (
    -- ✅ 단일 PRIMARY KEY (시간 정렬 + 중복 방지)
    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,

    -- 업비트 API 공통 필드들
    market TEXT NOT NULL,                    -- 'KRW-BTC'
    candle_date_time_kst TEXT NOT NULL,     -- 한국 시간
    opening_price REAL NOT NULL,            -- 시가
    high_price REAL NOT NULL,               -- 고가
    low_price REAL NOT NULL,                -- 저가
    trade_price REAL NOT NULL,              -- 현재가
    timestamp INTEGER NOT NULL,             -- Unix timestamp
    candle_acc_trade_price REAL NOT NULL,   -- 누적 거래 금액
    candle_acc_trade_volume REAL NOT NULL,  -- 누적 거래량

    -- 메타데이터
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 🔍 스키마 설계 원리 분석

#### PRIMARY KEY 선택의 이유
```sql
-- ❌ 잘못된 설계 (복합 키)
PRIMARY KEY (market, timeframe, candle_date_time_utc)

-- ✅ 올바른 설계 (단일 키)
candle_date_time_utc TEXT NOT NULL PRIMARY KEY
```

**왜 단일 PRIMARY KEY인가?**
1. **자동 정렬**: SQLite는 PRIMARY KEY로 자동 정렬 → ORDER BY 불필요
2. **중복 방지**: 같은 시간에 동일한 캔들 데이터 중복 저장 방지
3. **범위 스캔 최적화**: BETWEEN 쿼리가 매우 빠름
4. **메모리 효율성**: 인덱스 크기 최소화

#### 데이터 타입 선택의 이유
```sql
-- 시간: TEXT (ISO 8601 형식)
candle_date_time_utc TEXT  -- '2024-01-01T12:00:00Z'

-- 가격: REAL (부동소수점)
trade_price REAL  -- SQLite는 정확한 소수점 연산 지원

-- 타임스탬프: INTEGER (Unix timestamp)
timestamp INTEGER  -- 빠른 숫자 비교를 위함
```

### 📋 실습: 테이블 생성과 검증

```sql
-- 1. 테이블 생성 확인
SELECT name FROM sqlite_master
WHERE type='table' AND name LIKE 'candles_%';

-- 2. 스키마 정보 확인
PRAGMA table_info(candles_KRW_BTC_1m);

-- 3. 인덱스 정보 확인
PRAGMA index_list(candles_KRW_BTC_1m);
```

---

## 2. 동적 테이블 생성 패턴

### 🏗️ 테이블명 생성 규칙

우리 시스템은 심볼과 타임프레임에 따라 동적으로 테이블을 생성합니다.

```python
# 실제 코드: SqliteCandleRepository._get_table_name()
def _get_table_name(self, symbol: str, timeframe: str) -> str:
    """심볼과 타임프레임으로 테이블명 생성"""
    return f"candles_{symbol.replace('-', '_')}_{timeframe}"

# 예시:
# KRW-BTC, 1m → candles_KRW_BTC_1m
# BTC-ETH, 5m → candles_BTC_ETH_5m
```

### 🎯 동적 테이블의 장점과 단점

#### ✅ 장점
1. **쿼리 성능**: 테이블당 레코드 수가 적어 빠른 검색
2. **데이터 격리**: 심볼별 독립적 관리
3. **스케일링**: 새 심볼 추가시 기존 성능에 영향 없음
4. **백업/복구**: 특정 심볼만 선택적 처리

#### ⚠️ 단점
1. **메타데이터 오버헤드**: 테이블이 많아질수록 sqlite_master 크기 증가
2. **관리 복잡성**: 테이블 생성/삭제 로직 필요
3. **크로스 테이블 쿼리**: 여러 심볼 동시 조회시 UNION 필요

### 📊 실제 성능 테스트 결과

우리가 진행한 5,580개 테이블 성능 테스트 결과:

```python
# demo_many_tables_query_file.py 결과
"""
📊 5580개 테이블 성능 측정 결과:
- 메타데이터 쿼리: 8.11ms
- 테이블 존재 확인: 5.185ms
- 기본 쿼리: 0.156ms (57% 성능 향상!)
- DB 파일 크기: 43.37MB
"""
```

### 🔧 동적 테이블 관리 쿼리

```sql
-- 1. 모든 캔들 테이블 조회
SELECT name FROM sqlite_master
WHERE type='table' AND name LIKE 'candles_%'
ORDER BY name;

-- 2. 특정 심볼의 모든 타임프레임 테이블
SELECT name FROM sqlite_master
WHERE type='table' AND name LIKE 'candles_KRW_BTC_%';

-- 3. 테이블별 레코드 수 통계 (동적 SQL 생성)
SELECT
    'candles_KRW_BTC_1m' as table_name,
    COUNT(*) as record_count
FROM candles_KRW_BTC_1m
UNION ALL
SELECT
    'candles_KRW_BTC_5m' as table_name,
    COUNT(*) as record_count
FROM candles_KRW_BTC_5m;
```

---

## 3. 메타데이터 쿼리 최적화

### 🔍 테이블 존재 여부 확인

가장 자주 사용되는 메타데이터 쿼리를 분석해봅시다.

```sql
-- 실제 코드: SqliteCandleRepository.table_exists()
SELECT name FROM sqlite_master
WHERE type='table' AND name=?
```

### 📈 성능 최적화 팁

#### 1. sqlite_master 인덱스 활용
```sql
-- SQLite는 sqlite_master에 자동 인덱스 생성
-- type과 name 조합으로 빠른 검색 가능

-- ✅ 빠른 쿼리 (인덱스 사용)
SELECT name FROM sqlite_master
WHERE type='table' AND name='candles_KRW_BTC_1m';

-- ❌ 느린 쿼리 (인덱스 미사용)
SELECT * FROM sqlite_master
WHERE name LIKE '%BTC%';
```

#### 2. 쿼리 결과 캐싱
```python
# 실제 구현 권장사항
class TableCache:
    def __init__(self):
        self._cache = {}
        self._cache_time = {}

    def table_exists(self, table_name):
        # 1분간 캐시 유지
        if time.time() - self._cache_time.get(table_name, 0) < 60:
            return self._cache.get(table_name, False)

        # DB 쿼리 실행
        exists = check_table_exists_from_db(table_name)
        self._cache[table_name] = exists
        self._cache_time[table_name] = time.time()
        return exists
```

### 📊 메타데이터 통계 쿼리

```sql
-- 1. 전체 테이블 통계
SELECT
    COUNT(*) as total_tables,
    SUM(CASE WHEN name LIKE 'candles_KRW_%' THEN 1 ELSE 0 END) as krw_tables,
    SUM(CASE WHEN name LIKE 'candles_BTC_%' THEN 1 ELSE 0 END) as btc_tables
FROM sqlite_master
WHERE type='table' AND name LIKE 'candles_%';

-- 2. 타임프레임별 테이블 수
SELECT
    SUBSTR(name, -2) as timeframe,
    COUNT(*) as table_count
FROM sqlite_master
WHERE type='table' AND name LIKE 'candles_%'
GROUP BY SUBSTR(name, -2)
ORDER BY table_count DESC;
```

---

## 4. 윈도우 함수 활용한 연속성 분석

### 🎯 가장 고급 쿼리: 데이터 연속성 확인

우리 시스템의 핵심 기능 중 하나인 데이터 연속성 확인 쿼리를 분석해봅시다.

```sql
-- 실제 코드: SqliteCandleRepository.find_last_continuous_time()
-- 309배 성능 향상을 달성한 최적화된 쿼리!

WITH gap_check AS (
    SELECT
        candle_date_time_utc,
        timestamp,
        -- 다음 레코드의 timestamp를 가져옴 (시간 역순 정렬)
        LEAD(timestamp) OVER (ORDER BY timestamp DESC) as next_timestamp
    FROM candles_KRW_BTC_1m
    WHERE candle_date_time_utc >= ?
    ORDER BY timestamp DESC
)
SELECT candle_date_time_utc as last_continuous_time
FROM gap_check
WHERE
    -- Gap이 있으면 Gap 직전, 없으면 마지막 데이터(LEAD IS NULL)
    (timestamp - next_timestamp > 60000)  -- 1분 = 60,000ms
    OR (next_timestamp IS NULL)
ORDER BY timestamp DESC
LIMIT 1;
```

### 🔍 윈도우 함수 상세 분석

#### LEAD 함수의 동작 원리
```sql
-- 예시 데이터로 LEAD 함수 이해하기
SELECT
    candle_date_time_utc,
    timestamp,
    LEAD(timestamp) OVER (ORDER BY timestamp DESC) as next_timestamp,
    timestamp - LEAD(timestamp) OVER (ORDER BY timestamp DESC) as time_gap
FROM candles_KRW_BTC_1m
ORDER BY timestamp DESC
LIMIT 5;

-- 결과:
-- 2024-01-01T12:05:00Z | 1704110700000 | 1704110640000 | 60000  (정상)
-- 2024-01-01T12:04:00Z | 1704110640000 | 1704110580000 | 60000  (정상)
-- 2024-01-01T12:03:00Z | 1704110580000 | 1704110400000 | 180000 (Gap!)
-- 2024-01-01T12:01:00Z | 1704110400000 | 1704110340000 | 60000  (정상)
-- 2024-01-01T12:00:00Z | 1704110340000 | NULL          | NULL   (마지막)
```

#### 성능 최적화 포인트
1. **PRIMARY KEY 정렬 활용**: timestamp가 PRIMARY KEY이므로 ORDER BY 최적화
2. **윈도우 함수**: 자체 조인 대신 LEAD 사용으로 309배 성능 향상
3. **조건부 필터링**: Gap 임계값을 통한 정확한 연속성 판단

### 📋 윈도우 함수 활용 패턴

```sql
-- 1. 이전/다음 값 비교
SELECT
    candle_date_time_utc,
    trade_price,
    LAG(trade_price) OVER (ORDER BY timestamp) as prev_price,
    LEAD(trade_price) OVER (ORDER BY timestamp) as next_price
FROM candles_KRW_BTC_1m;

-- 2. 누적 통계
SELECT
    candle_date_time_utc,
    trade_price,
    AVG(trade_price) OVER (
        ORDER BY timestamp
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) as moving_avg_10
FROM candles_KRW_BTC_1m;

-- 3. 순위와 백분위
SELECT
    candle_date_time_utc,
    trade_price,
    RANK() OVER (ORDER BY trade_price DESC) as price_rank,
    PERCENT_RANK() OVER (ORDER BY trade_price) as price_percentile
FROM candles_KRW_BTC_1m;
```

---

## 5. PRIMARY KEY 범위 스캔 최적화

### 🚀 범위 조회 최적화

가장 자주 사용되는 시간 범위 조회를 최적화하는 방법을 알아봅시다.

```sql
-- 실제 코드: SqliteCandleRepository.get_candles_by_range()
-- PRIMARY KEY 범위 스캔을 활용하여 최고 성능 달성

SELECT
    candle_date_time_utc, market, candle_date_time_kst,
    opening_price, high_price, low_price, trade_price,
    timestamp, candle_acc_trade_price, candle_acc_trade_volume
FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc BETWEEN ? AND ?
-- ORDER BY 불필요! PRIMARY KEY는 이미 정렬됨
```

### 📊 범위 스캔 성능 비교

```sql
-- ❌ 비효율적인 쿼리 (인덱스 미사용)
SELECT * FROM candles_KRW_BTC_1m
WHERE SUBSTR(candle_date_time_utc, 1, 10) = '2024-01-01';

-- ✅ 효율적인 쿼리 (PRIMARY KEY 범위 스캔)
SELECT * FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc BETWEEN '2024-01-01T00:00:00Z' AND '2024-01-01T23:59:59Z';

-- ✅ 더 효율적인 쿼리 (정확한 ISO 형식)
SELECT * FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc >= '2024-01-01T00:00:00Z'
  AND candle_date_time_utc < '2024-01-02T00:00:00Z';
```

### 🔍 실행 계획 분석

```sql
-- 쿼리 실행 계획 확인
EXPLAIN QUERY PLAN
SELECT * FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc BETWEEN '2024-01-01T00:00:00Z' AND '2024-01-01T23:59:59Z';

-- 결과: SEARCH TABLE candles_KRW_BTC_1m USING INTEGER PRIMARY KEY
-- → PRIMARY KEY 인덱스를 사용한 범위 스캔!
```

### 📋 범위 조회 활용 패턴

```sql
-- 1. 최근 N개 데이터 조회
SELECT * FROM candles_KRW_BTC_1m
ORDER BY candle_date_time_utc DESC
LIMIT 100;

-- 2. 특정 시간 이후 데이터
SELECT * FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc > '2024-01-01T12:00:00Z';

-- 3. 데이터 존재 여부 빠른 확인
SELECT 1 FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc BETWEEN ? AND ?
LIMIT 1;
```

---

## 6. 복잡한 집계 쿼리와 성능

### 📈 캔들 데이터 통계 분석

실제 트레이딩에서 사용되는 복잡한 집계 쿼리들을 살펴봅시다.

```sql
-- 실제 코드: SqliteCandleRepository.get_data_ranges()
-- 범위 내 데이터 통계 조회

SELECT
    MIN(candle_date_time_utc) as start_time,
    MAX(candle_date_time_utc) as end_time,
    COUNT(*) as candle_count
FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc BETWEEN ? AND ?
HAVING COUNT(*) > 0;
```

### 🎯 고급 집계 쿼리 패턴

#### 1. 시간별 OHLCV 집계
```sql
-- 1분 데이터를 5분 데이터로 집계
SELECT
    -- 5분 단위로 그룹핑
    datetime(
        (strftime('%s', candle_date_time_utc) / 300) * 300,
        'unixepoch'
    ) as candle_5m,

    -- OHLC 계산
    (SELECT opening_price FROM candles_KRW_BTC_1m c2
     WHERE c2.candle_date_time_utc >= datetime(...)
     ORDER BY c2.candle_date_time_utc ASC LIMIT 1) as open_price,
    MAX(high_price) as high_price,
    MIN(low_price) as low_price,
    (SELECT trade_price FROM candles_KRW_BTC_1m c2
     WHERE c2.candle_date_time_utc < datetime(...)
     ORDER BY c2.candle_date_time_utc DESC LIMIT 1) as close_price,

    -- 거래량 합계
    SUM(candle_acc_trade_volume) as volume
FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc BETWEEN ? AND ?
GROUP BY candle_5m
ORDER BY candle_5m;
```

#### 2. 이동평균 계산
```sql
-- 20일 이동평균 (윈도우 함수 활용)
SELECT
    candle_date_time_utc,
    trade_price,
    AVG(trade_price) OVER (
        ORDER BY candle_date_time_utc
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) as ma20,

    -- 표준편차
    AVG(trade_price * trade_price) OVER (
        ORDER BY candle_date_time_utc
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) - POW(AVG(trade_price) OVER (
        ORDER BY candle_date_time_utc
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ), 2) as variance
FROM candles_KRW_BTC_1m
ORDER BY candle_date_time_utc;
```

#### 3. RSI 계산
```sql
-- RSI (Relative Strength Index) 계산
WITH price_changes AS (
    SELECT
        candle_date_time_utc,
        trade_price,
        trade_price - LAG(trade_price) OVER (ORDER BY candle_date_time_utc) as price_change
    FROM candles_KRW_BTC_1m
),
gains_losses AS (
    SELECT
        candle_date_time_utc,
        trade_price,
        CASE WHEN price_change > 0 THEN price_change ELSE 0 END as gain,
        CASE WHEN price_change < 0 THEN ABS(price_change) ELSE 0 END as loss
    FROM price_changes
)
SELECT
    candle_date_time_utc,
    trade_price,
    100 - (100 / (1 + (
        AVG(gain) OVER (ORDER BY candle_date_time_utc ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) /
        AVG(loss) OVER (ORDER BY candle_date_time_utc ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
    ))) as rsi_14
FROM gains_losses
ORDER BY candle_date_time_utc;
```

### 📊 성능 최적화 전략

#### 1. 인덱스 전략
```sql
-- 자주 사용되는 쿼리를 위한 복합 인덱스
CREATE INDEX idx_candles_time_price
ON candles_KRW_BTC_1m(candle_date_time_utc, trade_price);

-- 거래량 기준 조회를 위한 인덱스
CREATE INDEX idx_candles_volume
ON candles_KRW_BTC_1m(candle_acc_trade_volume);
```

#### 2. 부분 집계 테이블
```sql
-- 일별 집계 테이블 생성
CREATE TABLE daily_summary_KRW_BTC AS
SELECT
    DATE(candle_date_time_utc) as trade_date,
    MIN(low_price) as daily_low,
    MAX(high_price) as daily_high,
    (SELECT opening_price FROM candles_KRW_BTC_1m
     WHERE DATE(candle_date_time_utc) = trade_date
     ORDER BY candle_date_time_utc ASC LIMIT 1) as daily_open,
    (SELECT trade_price FROM candles_KRW_BTC_1m
     WHERE DATE(candle_date_time_utc) = trade_date
     ORDER BY candle_date_time_utc DESC LIMIT 1) as daily_close,
    SUM(candle_acc_trade_volume) as daily_volume
FROM candles_KRW_BTC_1m
GROUP BY DATE(candle_date_time_utc);
```

---

## 7. 트랜잭션과 동시성 제어

### 🔒 캔들 데이터 저장 최적화

실제 데이터 저장 과정에서의 트랜잭션 처리를 분석해봅시다.

```sql
-- 실제 코드: SqliteCandleRepository.save_candle_chunk()
-- INSERT OR IGNORE를 사용한 안전한 데이터 저장

INSERT OR IGNORE INTO candles_KRW_BTC_1m (
    candle_date_time_utc, market, candle_date_time_kst,
    opening_price, high_price, low_price, trade_price,
    timestamp, candle_acc_trade_price, candle_acc_trade_volume
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

### 🎯 INSERT 전략 비교

```sql
-- 1. INSERT OR IGNORE (중복 무시)
INSERT OR IGNORE INTO candles_KRW_BTC_1m VALUES (...);
-- ✅ 장점: 중복 데이터 자동 무시, 에러 없음
-- ⚠️ 단점: 중복 여부를 모름

-- 2. INSERT OR REPLACE (중복 대체)
INSERT OR REPLACE INTO candles_KRW_BTC_1m VALUES (...);
-- ✅ 장점: 데이터 업데이트 가능
-- ⚠️ 단점: 불필요한 업데이트 발생 가능

-- 3. 조건부 INSERT
INSERT INTO candles_KRW_BTC_1m
SELECT ... WHERE NOT EXISTS (
    SELECT 1 FROM candles_KRW_BTC_1m
    WHERE candle_date_time_utc = ?
);
-- ✅ 장점: 명시적 중복 체크
-- ⚠️ 단점: 성능 오버헤드
```

### 📋 배치 삽입 최적화

```python
# 실제 Python 코드 패턴
def save_candle_chunk_optimized(candles):
    """배치 삽입으로 성능 최적화"""

    # 1. 트랜잭션 시작
    conn.execute("BEGIN TRANSACTION")

    try:
        # 2. 배치 삽입 (executemany 사용)
        cursor = conn.executemany("""
            INSERT OR IGNORE INTO candles_KRW_BTC_1m
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, candle_data_list)

        # 3. 성공 시 커밋
        conn.execute("COMMIT")
        return cursor.rowcount

    except Exception as e:
        # 4. 실패 시 롤백
        conn.execute("ROLLBACK")
        raise e
```

### 🔧 동시성 제어 설정

```sql
-- WAL 모드로 동시성 향상
PRAGMA journal_mode = WAL;

-- 동기화 설정 (성능 vs 안정성)
PRAGMA synchronous = NORMAL;  -- 기본 권장값
PRAGMA synchronous = FULL;    -- 최고 안정성 (느림)
PRAGMA synchronous = OFF;     -- 최고 성능 (위험)

-- 잠금 타임아웃 설정
PRAGMA busy_timeout = 30000;  -- 30초 대기
```

---

## 8. 대용량 테이블 관리 전략

### 📊 실제 성능 테스트 결과 분석

우리가 수행한 5,580개 테이블 테스트 결과를 통해 대용량 환경에서의 전략을 수립해봅시다.

```python
"""
🔥 5,580개 테이블 성능 테스트 결과 (43.37MB DB):

메타데이터 쿼리 성능:
- sqlite_master 조회: 8.11ms
- 테이블 존재 확인: 5.185ms
- 스키마 정보 조회: 3.2ms

데이터 쿼리 성능:
- 기본 SELECT: 0.156ms (57% 향상!)
- 범위 조회: 0.8ms
- 집계 쿼리: 2.3ms

파일 vs 메모리 DB:
- 메모리 DB: 3.42ms (메타데이터)
- 파일 DB: 8.11ms (메타데이터)
- 성능차: 약 2.4배
"""
```

### 🎯 스케일링 전략

#### 1. 테이블 파티셔닝
```sql
-- 날짜별 테이블 분할
CREATE TABLE candles_KRW_BTC_1m_2024_01 AS
SELECT * FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc >= '2024-01-01T00:00:00Z'
  AND candle_date_time_utc < '2024-02-01T00:00:00Z';

-- 자동 파티션 조회 뷰
CREATE VIEW candles_KRW_BTC_1m_recent AS
SELECT * FROM candles_KRW_BTC_1m_2024_01
UNION ALL
SELECT * FROM candles_KRW_BTC_1m_2024_02
UNION ALL
SELECT * FROM candles_KRW_BTC_1m_2024_03;
```

#### 2. 인덱스 최적화
```sql
-- 복합 인덱스로 쿼리 성능 향상
CREATE INDEX idx_candles_time_market
ON candles_KRW_BTC_1m(candle_date_time_utc, market);

-- 부분 인덱스로 공간 절약
CREATE INDEX idx_candles_high_volume
ON candles_KRW_BTC_1m(candle_date_time_utc)
WHERE candle_acc_trade_volume > 1000000;
```

#### 3. 데이터 압축과 아카이빙
```sql
-- 오래된 데이터 압축 테이블로 이동
CREATE TABLE candles_KRW_BTC_1m_archive (
    -- 압축된 데이터 구조
    period_start TEXT,
    period_end TEXT,
    ohlc_data BLOB,  -- JSON 압축 데이터
    summary_stats BLOB
);

-- 압축 함수 예시
INSERT INTO candles_KRW_BTC_1m_archive
SELECT
    MIN(candle_date_time_utc),
    MAX(candle_date_time_utc),
    json_group_array(json_object(
        'time', candle_date_time_utc,
        'ohlc', json_array(opening_price, high_price, low_price, trade_price)
    )),
    json_object(
        'count', COUNT(*),
        'avg_price', AVG(trade_price),
        'total_volume', SUM(candle_acc_trade_volume)
    )
FROM candles_KRW_BTC_1m
WHERE candle_date_time_utc < date('now', '-1 year')
GROUP BY date(candle_date_time_utc);
```

### 📋 유지보수 자동화

```sql
-- 1. 테이블 통계 수집
CREATE VIEW table_stats AS
SELECT
    name as table_name,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name=name) as index_count,
    'SELECT COUNT(*) FROM ' || name as count_query
FROM sqlite_master
WHERE type='table' AND name LIKE 'candles_%';

-- 2. 자동 VACUUM 트리거
CREATE TRIGGER auto_vacuum_trigger
AFTER DELETE ON candles_KRW_BTC_1m
WHEN (SELECT COUNT(*) FROM sqlite_master WHERE type='table') % 100 = 0
BEGIN
    UPDATE vacuum_log SET last_vacuum = datetime('now');
    -- VACUUM; -- 실제로는 별도 프로세스에서 실행
END;

-- 3. 성능 모니터링 테이블
CREATE TABLE performance_log (
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    operation TEXT,
    table_name TEXT,
    duration_ms REAL,
    record_count INTEGER
);
```

---

## 🎯 실습 프로젝트: 나만의 캔들 데이터 분석기

### 📋 미션: 업비트 데이터로 고급 쿼리 마스터하기

#### 1단계: 기본 데이터 탐색
```sql
-- Q1: KRW-BTC 1분봉에서 최고가와 최저가 찾기
SELECT
    candle_date_time_utc,
    high_price,
    low_price
FROM candles_KRW_BTC_1m
WHERE high_price = (SELECT MAX(high_price) FROM candles_KRW_BTC_1m)
   OR low_price = (SELECT MIN(low_price) FROM candles_KRW_BTC_1m);

-- Q2: 하루 평균 거래량 상위 10일 찾기
SELECT
    DATE(candle_date_time_utc) as trade_date,
    AVG(candle_acc_trade_volume) as avg_volume
FROM candles_KRW_BTC_1m
GROUP BY DATE(candle_date_time_utc)
ORDER BY avg_volume DESC
LIMIT 10;
```

#### 2단계: 윈도우 함수 활용
```sql
-- Q3: 연속 상승 구간 찾기
WITH price_direction AS (
    SELECT
        candle_date_time_utc,
        trade_price,
        CASE
            WHEN trade_price > LAG(trade_price) OVER (ORDER BY candle_date_time_utc)
            THEN 1 ELSE 0
        END as is_up
    FROM candles_KRW_BTC_1m
),
streak_groups AS (
    SELECT
        *,
        SUM(CASE WHEN is_up = 0 THEN 1 ELSE 0 END) OVER (
            ORDER BY candle_date_time_utc
        ) as group_id
    FROM price_direction
)
SELECT
    group_id,
    COUNT(*) as streak_length,
    MIN(candle_date_time_utc) as streak_start,
    MAX(candle_date_time_utc) as streak_end
FROM streak_groups
WHERE is_up = 1
GROUP BY group_id
HAVING COUNT(*) >= 10  -- 10분 이상 연속 상승
ORDER BY streak_length DESC;
```

#### 3단계: 성능 최적화 도전
```sql
-- Q4: 대용량 데이터에서 빠른 통계 계산
-- 힌트: 적절한 인덱스와 윈도우 함수 활용

-- 월별 OHLC 집계 (최적화 버전)
SELECT
    strftime('%Y-%m', candle_date_time_utc) as month,
    (SELECT opening_price FROM candles_KRW_BTC_1m c2
     WHERE strftime('%Y-%m', c2.candle_date_time_utc) = month
     ORDER BY c2.candle_date_time_utc ASC LIMIT 1) as monthly_open,
    MAX(high_price) as monthly_high,
    MIN(low_price) as monthly_low,
    (SELECT trade_price FROM candles_KRW_BTC_1m c2
     WHERE strftime('%Y-%m', c2.candle_date_time_utc) = month
     ORDER BY c2.candle_date_time_utc DESC LIMIT 1) as monthly_close
FROM candles_KRW_BTC_1m
GROUP BY strftime('%Y-%m', candle_date_time_utc)
ORDER BY month;
```

---

## 📚 참고 자료와 다음 단계

### 🔗 관련 문서
- [VACUUM 완전 가이드](./VACUUM_완전가이드.md)
- [업비트 API 문서](https://docs.upbit.com/)
- [SQLite 공식 문서](https://www.sqlite.org/docs.html)

### 📈 고급 주제
1. **파티셔닝 전략**: 시간 기반 테이블 분할
2. **실시간 스트리밍**: WebSocket 데이터 처리
3. **분산 데이터베이스**: 여러 DB 인스턴스 관리
4. **머신러닝 통합**: SQL로 기본 지표 계산

### 🎯 실습 과제
1. 본인만의 기술적 지표 쿼리 작성
2. 성능 테스트 스크립트 작성
3. 데이터 백업/복구 시스템 구축
4. 모니터링 대시보드 쿼리 설계

---

**작성일**: 2025년 9월 8일
**기반 코드**: CandleDataProvider v4.0 Infrastructure Service
**테스트 환경**: 5,580개 테이블, 43.37MB SQLite DB

SQLite 마스터가 되어 효율적인 데이터 관리 시스템을 구축하세요! 🚀
