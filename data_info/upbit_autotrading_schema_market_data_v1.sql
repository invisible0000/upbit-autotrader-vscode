-- Upbit Auto Trading - Market Data Database Schema v1.0
-- =====================================================
-- DB: market_data.sqlite3
-- 용도: CandleDataProvider에서 사용하는 실제 캔들 데이터 테이블 스키마
-- 생성일: 2025-09-12
-- 기준: sqlite_candle_repository.py의 ensure_table_exists 메서드
-- 특징: 동적 테이블 생성 패턴 (candles_{symbol}_{timeframe})

PRAGMA foreign_keys = ON;

-- =====================================
-- 동적 캔들 테이블 스키마
-- =====================================

-- 캔들 데이터는 심볼별 + 타임프레임별로 동적 테이블 생성
-- 테이블 이름 패턴: candles_{symbol}_{timeframe}
-- 예시: candles_KRW_BTC_1m, candles_KRW_ETH_5m, candles_KRW_BTC_1h, candles_KRW_BTC_1d

-- 기본 캔들 테이블 템플릿 (CandleDataProvider에서 자동 생성됨)
-- CREATE TABLE IF NOT EXISTS candles_{symbol}_{timeframe} (
--     -- ✅ 단일 PRIMARY KEY (시간 정렬 + 중복 방지)
--     candle_date_time_utc TEXT NOT NULL PRIMARY KEY,
--
--     -- 업비트 API 공통 필드들
--     market TEXT NOT NULL,
--     candle_date_time_kst TEXT NOT NULL,
--     opening_price REAL NOT NULL,
--     high_price REAL NOT NULL,
--     low_price REAL NOT NULL,
--     trade_price REAL NOT NULL,
--     timestamp INTEGER NOT NULL,
--     candle_acc_trade_price REAL NOT NULL,
--     candle_acc_trade_volume REAL NOT NULL,
--
--     -- 메타데이터
--     created_at TEXT DEFAULT CURRENT_TIMESTAMP
-- );

-- 🚀 성능 최적화를 위한 timestamp 인덱스
-- CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp
-- ON {table_name}(timestamp DESC);

-- =====================================
-- 실제 생성 예시들
-- =====================================

-- KRW-BTC 1분봉 (가장 일반적)
CREATE TABLE IF NOT EXISTS candles_KRW_BTC_1m (
    -- ✅ 단일 PRIMARY KEY (시간 정렬 + 중복 방지)
    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,

    -- 업비트 API 공통 필드들
    market TEXT NOT NULL,
    candle_date_time_kst TEXT NOT NULL,
    opening_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    trade_price REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    candle_acc_trade_price REAL NOT NULL,
    candle_acc_trade_volume REAL NOT NULL,

    -- 메타데이터
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- KRW-BTC 5분봉
CREATE TABLE IF NOT EXISTS candles_KRW_BTC_5m (
    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,
    market TEXT NOT NULL,
    candle_date_time_kst TEXT NOT NULL,
    opening_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    trade_price REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    candle_acc_trade_price REAL NOT NULL,
    candle_acc_trade_volume REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- KRW-BTC 15분봉
CREATE TABLE IF NOT EXISTS candles_KRW_BTC_15m (
    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,
    market TEXT NOT NULL,
    candle_date_time_kst TEXT NOT NULL,
    opening_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    trade_price REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    candle_acc_trade_price REAL NOT NULL,
    candle_acc_trade_volume REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- KRW-BTC 1시간봉
CREATE TABLE IF NOT EXISTS candles_KRW_BTC_1h (
    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,
    market TEXT NOT NULL,
    candle_date_time_kst TEXT NOT NULL,
    opening_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    trade_price REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    candle_acc_trade_price REAL NOT NULL,
    candle_acc_trade_volume REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- KRW-BTC 1일봉
CREATE TABLE IF NOT EXISTS candles_KRW_BTC_1d (
    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,
    market TEXT NOT NULL,
    candle_date_time_kst TEXT NOT NULL,
    opening_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    trade_price REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    candle_acc_trade_price REAL NOT NULL,
    candle_acc_trade_volume REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- KRW-ETH 1분봉 (두 번째로 많이 사용)
CREATE TABLE IF NOT EXISTS candles_KRW_ETH_1m (
    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,
    market TEXT NOT NULL,
    candle_date_time_kst TEXT NOT NULL,
    opening_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    trade_price REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    candle_acc_trade_price REAL NOT NULL,
    candle_acc_trade_volume REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- KRW-ETH 5분봉
CREATE TABLE IF NOT EXISTS candles_KRW_ETH_5m (
    candle_date_time_utc TEXT NOT NULL PRIMARY KEY,
    market TEXT NOT NULL,
    candle_date_time_kst TEXT NOT NULL,
    opening_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    trade_price REAL NOT NULL,
    timestamp INTEGER NOT NULL,
    candle_acc_trade_price REAL NOT NULL,
    candle_acc_trade_volume REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 성능 최적화 인덱스들
-- =====================================

-- 🚀 timestamp 인덱스들 (ORDER BY timestamp DESC 최적화)
CREATE INDEX IF NOT EXISTS idx_candles_KRW_BTC_1m_timestamp
ON candles_KRW_BTC_1m(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_KRW_BTC_5m_timestamp
ON candles_KRW_BTC_5m(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_KRW_BTC_15m_timestamp
ON candles_KRW_BTC_15m(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_KRW_BTC_1h_timestamp
ON candles_KRW_BTC_1h(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_KRW_BTC_1d_timestamp
ON candles_KRW_BTC_1d(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_KRW_ETH_1m_timestamp
ON candles_KRW_ETH_1m(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_KRW_ETH_5m_timestamp
ON candles_KRW_ETH_5m(timestamp DESC);

-- =====================================
-- 스키마 설명 및 주의사항
-- =====================================

-- 필드 설명:
-- - candle_date_time_utc: PRIMARY KEY, UTC 시간 문자열 (YYYY-MM-DDTHH:MM:SS)
-- - market: 마켓 코드 (예: 'KRW-BTC')
-- - candle_date_time_kst: KST 시간 문자열 (UTC + 9시간)
-- - opening_price: 시가
-- - high_price: 고가
-- - low_price: 저가
-- - trade_price: 종가
-- - timestamp: Unix timestamp (밀리초)
-- - candle_acc_trade_price: 누적 거래대금
-- - candle_acc_trade_volume: 누적 거래량
-- - created_at: 레코드 생성 시간

-- 특징:
-- 1. candle_date_time_utc가 PRIMARY KEY로 자동 정렬 및 중복 방지
-- 2. timestamp 인덱스로 ORDER BY timestamp DESC 성능 최적화
-- 3. INSERT OR IGNORE 방식으로 중복 처리 (업비트 데이터 불변성)
-- 4. 업비트 API 공통 필드만 저장하여 통일성 확보
-- 5. 동적 테이블 생성으로 심볼별/타임프레임별 분리 저장

-- 프로덕션 사용법:
-- 1. CandleDataProvider.ensure_table_exists()에서 자동 생성
-- 2. save_candle_chunk()에서 INSERT OR IGNORE로 데이터 저장
-- 3. get_candles_by_range()에서 PRIMARY KEY 범위 스캔으로 조회
-- 4. OverlapAnalyzer의 효율적 쿼리들이 이 스키마 기반으로 동작

-- 테이블 명명 규칙:
-- candles_{심볼을 언더스코어로 변환}_{타임프레임}
-- 예시:
-- - KRW-BTC + 1m → candles_KRW_BTC_1m
-- - KRW-ETH + 5m → candles_KRW_ETH_5m
-- - USDT-BTC + 1h → candles_USDT_BTC_1h
