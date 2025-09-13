-- =============================================
-- 업비트 API 완전 호환 마켓 데이터 스키마 v3.0
-- =============================================
-- DB: market_data.sqlite3
-- 설계 원칙: 업비트 API 응답과 100% 일치하는 필드명 사용
-- 개별 코인별 개별 타임프레임별 독립 테이블
-- 생성일: 2025-08-22

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = memory;

-- =====================================
-- 메타 정보 및 관리 테이블
-- =====================================

-- 스키마 버전 관리
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 스키마 버전 기록
INSERT OR REPLACE INTO schema_version (version, description)
VALUES ('3.0.0', '업비트 API 완전 호환 필드명으로 재설계');

-- 지원되는 마켓 심볼 목록
CREATE TABLE IF NOT EXISTS market_symbols (
    symbol TEXT PRIMARY KEY,               -- 'KRW-BTC', 'KRW-ETH' 등
    base_currency TEXT NOT NULL,           -- 'BTC', 'ETH' 등
    quote_currency TEXT NOT NULL,          -- 'KRW', 'USDT' 등
    display_name_ko TEXT,                  -- '비트코인', '이더리움' 등
    display_name_en TEXT,                  -- 'Bitcoin', 'Ethereum' 등
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 지원되는 타임프레임 목록
CREATE TABLE IF NOT EXISTS timeframes (
    timeframe TEXT PRIMARY KEY,            -- '1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M'
    interval_minutes INTEGER NOT NULL,     -- 분 단위 (1, 3, 5, 15, 30, 60, 240, 1440, 10080, 43200)
    display_name TEXT NOT NULL,            -- '1분', '3분', '5분' 등
    is_active BOOLEAN DEFAULT 1,
    sort_order INTEGER,                    -- 정렬 순서
    api_limit INTEGER DEFAULT 200          -- 업비트 API 한번 호출시 최대 캔들 수
);

-- 기본 타임프레임 데이터 삽입
INSERT OR REPLACE INTO timeframes (timeframe, interval_minutes, display_name, sort_order, api_limit) VALUES
('1m', 1, '1분', 1, 200),
('3m', 3, '3분', 2, 200),
('5m', 5, '5분', 3, 200),
('15m', 15, '15분', 4, 200),
('30m', 30, '30분', 5, 200),
('1h', 60, '1시간', 6, 200),
('4h', 240, '4시간', 7, 200),
('1d', 1440, '1일', 8, 200),
('1w', 10080, '1주', 9, 200),
('1M', 43200, '1월', 10, 200);

-- 테이블 목록 관리 (동적 테이블 추적)
CREATE TABLE IF NOT EXISTS candle_tables (
    table_name TEXT PRIMARY KEY,           -- 'candles_KRW_BTC_1m' 형식
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_update_at TIMESTAMP,
    record_count INTEGER DEFAULT 0,
    oldest_timestamp TIMESTAMP,            -- 가장 오래된 캔들 시간
    newest_timestamp TIMESTAMP,            -- 가장 최신 캔들 시간
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol),
    FOREIGN KEY (timeframe) REFERENCES timeframes(timeframe),
    UNIQUE(symbol, timeframe)
);

-- =====================================
-- 동적 캔들 테이블 생성 템플릿 (업비트 API 완전 호환)
-- =====================================

-- 캔들 테이블 구조 (업비트 API 응답과 100% 일치)
-- 테이블명 형식: candles_{SYMBOL}_{TIMEFRAME}
-- 예시: candles_KRW_BTC_1m, candles_KRW_ETH_5m

/*
개별 캔들 테이블 구조 (예시: candles_KRW_BTC_1m):

CREATE TABLE candles_KRW_BTC_1m (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- 업비트 API 응답과 100% 동일한 필드명
    market TEXT NOT NULL,                       -- 'KRW-BTC'
    candle_date_time_utc TEXT NOT NULL,         -- '2025-08-22T06:14:00'
    candle_date_time_kst TEXT NOT NULL,         -- '2025-08-22T15:14:00'
    opening_price REAL NOT NULL,               -- 시가
    high_price REAL NOT NULL,                  -- 고가
    low_price REAL NOT NULL,                   -- 저가
    trade_price REAL NOT NULL,                 -- 종가 (업비트는 trade_price가 종가)
    timestamp INTEGER NOT NULL,                -- 1755843264990
    candle_acc_trade_price REAL NOT NULL,      -- 누적 거래대금
    candle_acc_trade_volume REAL NOT NULL,     -- 누적 거래량
    unit INTEGER NOT NULL,                     -- 분 단위 (1, 3, 5, 15, 30, 60 등)

    -- 내부 관리용
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 유니크 제약 (동일한 타임스탬프 중복 방지)
    UNIQUE(candle_date_time_kst),
    UNIQUE(timestamp)
);

-- 최적화된 인덱스
CREATE INDEX idx_candles_KRW_BTC_1m_timestamp DESC ON candles_KRW_BTC_1m(timestamp DESC);
CREATE INDEX idx_candles_KRW_BTC_1m_kst_time DESC ON candles_KRW_BTC_1m(candle_date_time_kst DESC);
CREATE INDEX idx_candles_KRW_BTC_1m_created_at ON candles_KRW_BTC_1m(created_at);

-- 데이터 무결성 트리거
CREATE TRIGGER validate_candle_data_KRW_BTC_1m
    BEFORE INSERT ON candles_KRW_BTC_1m
    FOR EACH ROW
BEGIN
    -- 가격 유효성 검증
    SELECT CASE
        WHEN NEW.opening_price <= 0 OR NEW.high_price <= 0 OR
             NEW.low_price <= 0 OR NEW.trade_price <= 0 THEN
            RAISE(ABORT, 'Invalid price: all prices must be positive')
        WHEN NEW.high_price < NEW.low_price THEN
            RAISE(ABORT, 'Invalid price: high price cannot be less than low price')
        WHEN NEW.high_price < NEW.opening_price OR NEW.high_price < NEW.trade_price THEN
            RAISE(ABORT, 'Invalid price: high price must be >= opening and trade price')
        WHEN NEW.low_price > NEW.opening_price OR NEW.low_price > NEW.trade_price THEN
            RAISE(ABORT, 'Invalid price: low price must be <= opening and trade price')
        WHEN NEW.candle_acc_trade_volume < 0 OR NEW.candle_acc_trade_price < 0 THEN
            RAISE(ABORT, 'Invalid volume: volume cannot be negative')
    END;
END;

-- 테이블 상태 업데이트 트리거
CREATE TRIGGER update_table_stats_KRW_BTC_1m
    AFTER INSERT ON candles_KRW_BTC_1m
    FOR EACH ROW
BEGIN
    INSERT OR REPLACE INTO candle_tables (
        table_name, symbol, timeframe, last_update_at,
        record_count, oldest_timestamp, newest_timestamp
    )
    SELECT
        'candles_KRW_BTC_1m',
        'KRW-BTC',
        '1m',
        CURRENT_TIMESTAMP,
        COUNT(*),
        MIN(candle_date_time_kst),
        MAX(candle_date_time_kst)
    FROM candles_KRW_BTC_1m;
END;
*/

-- =====================================
-- 실시간 데이터 (업비트 API 호환)
-- =====================================

-- 실시간 티커 데이터 (업비트 API 응답과 100% 동일한 필드명)
CREATE TABLE IF NOT EXISTS real_time_tickers (
    symbol TEXT PRIMARY KEY,               -- market 필드와 동일

    -- 업비트 티커 API 응답과 100% 동일한 필드명
    market TEXT NOT NULL,                  -- 'KRW-BTC'
    trade_date TEXT,                       -- '20250822'
    trade_time TEXT,                       -- '061504'
    trade_date_kst TEXT,                   -- '20250822'
    trade_time_kst TEXT,                   -- '151504'
    trade_timestamp INTEGER,               -- 1755843304254
    opening_price REAL,                    -- 시가
    high_price REAL,                       -- 고가
    low_price REAL,                        -- 저가
    trade_price REAL,                      -- 현재가
    prev_closing_price REAL,               -- 전일 종가
    change TEXT,                           -- 'RISE', 'FALL', 'EVEN'
    change_price REAL,                     -- 변화액
    change_rate REAL,                      -- 변화율
    signed_change_price REAL,              -- 부호가 있는 변화액
    signed_change_rate REAL,               -- 부호가 있는 변화율
    trade_volume REAL,                     -- 마지막 거래량
    acc_trade_price REAL,                  -- 누적 거래대금 (당일)
    acc_trade_price_24h REAL,              -- 24시간 누적 거래대금
    acc_trade_volume REAL,                 -- 누적 거래량 (당일)
    acc_trade_volume_24h REAL,             -- 24시간 누적 거래량
    highest_52_week_price REAL,            -- 52주 최고가
    highest_52_week_date TEXT,             -- 52주 최고가 달성일
    lowest_52_week_price REAL,             -- 52주 최저가
    lowest_52_week_date TEXT,              -- 52주 최저가 달성일
    timestamp INTEGER,                     -- 타임스탬프

    -- 내부 관리용
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- =====================================
-- 데이터 수집 및 관리
-- =====================================

-- 데이터 수집 상태 추적
CREATE TABLE IF NOT EXISTS collection_status (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    last_collected_at TIMESTAMP,
    next_collection_at TIMESTAMP,
    status TEXT DEFAULT 'pending',         -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    gap_minutes INTEGER DEFAULT 0,         -- 수집 갭 (분)
    auto_enabled BOOLEAN DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timeframe),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol),
    FOREIGN KEY (timeframe) REFERENCES timeframes(timeframe)
);

-- =====================================
-- 성능 최적화 인덱스
-- =====================================

-- 메타 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_market_symbols_active ON market_symbols(is_active);
CREATE INDEX IF NOT EXISTS idx_market_symbols_quote ON market_symbols(quote_currency);
CREATE INDEX IF NOT EXISTS idx_timeframes_active ON timeframes(is_active);
CREATE INDEX IF NOT EXISTS idx_timeframes_sort ON timeframes(sort_order);

-- 테이블 관리 인덱스
CREATE INDEX IF NOT EXISTS idx_candle_tables_symbol ON candle_tables(symbol);
CREATE INDEX IF NOT EXISTS idx_candle_tables_timeframe ON candle_tables(timeframe);
CREATE INDEX IF NOT EXISTS idx_candle_tables_update ON candle_tables(last_update_at DESC);

-- 실시간 데이터 인덱스
CREATE INDEX IF NOT EXISTS idx_tickers_trade_timestamp ON real_time_tickers(trade_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tickers_timestamp ON real_time_tickers(timestamp DESC);

-- 수집 상태 인덱스
CREATE INDEX IF NOT EXISTS idx_collection_status_next ON collection_status(next_collection_at);
CREATE INDEX IF NOT EXISTS idx_collection_status_auto ON collection_status(auto_enabled);

-- =====================================
-- 유용한 뷰
-- =====================================

-- 테이블 현황 요약 뷰
CREATE VIEW IF NOT EXISTS table_summary AS
SELECT
    ct.symbol,
    ct.timeframe,
    ct.table_name,
    ct.record_count,
    ct.oldest_timestamp,
    ct.newest_timestamp,
    CASE
        WHEN ct.newest_timestamp IS NULL THEN 'empty'
        WHEN datetime(ct.newest_timestamp, '+' || tf.interval_minutes || ' minutes') < datetime('now') THEN 'outdated'
        ELSE 'current'
    END as data_status,
    tf.display_name as timeframe_display
FROM candle_tables ct
JOIN timeframes tf ON ct.timeframe = tf.timeframe
ORDER BY ct.symbol, tf.sort_order;

-- 실시간 마켓 요약 뷰
CREATE VIEW IF NOT EXISTS market_summary AS
SELECT
    ms.symbol,
    ms.display_name_ko,
    rt.trade_price as current_price,
    rt.signed_change_rate as price_change_rate_24h,
    rt.acc_trade_price_24h as quote_volume_24h,
    rt.trade_timestamp as last_updated,
    rt.change as trend_direction,
    CASE
        WHEN rt.signed_change_rate > 0.05 THEN 'strong_up'
        WHEN rt.signed_change_rate > 0 THEN 'up'
        WHEN rt.signed_change_rate < -0.05 THEN 'strong_down'
        WHEN rt.signed_change_rate < 0 THEN 'down'
        ELSE 'neutral'
    END as trend_signal
FROM market_symbols ms
LEFT JOIN real_time_tickers rt ON ms.symbol = rt.symbol
WHERE ms.is_active = 1
ORDER BY rt.acc_trade_price_24h DESC NULLS LAST;

-- 기본 시장 심볼 데이터 삽입
INSERT OR IGNORE INTO market_symbols (symbol, base_currency, quote_currency, display_name_ko, display_name_en) VALUES
('KRW-BTC', 'BTC', 'KRW', '비트코인', 'Bitcoin'),
('KRW-ETH', 'ETH', 'KRW', '이더리움', 'Ethereum'),
('KRW-ADA', 'ADA', 'KRW', '에이다', 'Cardano'),
('KRW-DOT', 'DOT', 'KRW', '폴카닷', 'Polkadot'),
('KRW-LINK', 'LINK', 'KRW', '체인링크', 'Chainlink');

-- 테이블 생성 기록
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (
    '3.0.0-base',
    '업비트 API 호환 기본 메타 테이블 생성 완료'
);
