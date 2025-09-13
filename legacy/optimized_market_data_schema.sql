-- =============================================
-- 최적화된 업비트 마켓 데이터 스키마 v2.0
-- =============================================
-- DB: market_data.sqlite3
-- 설계 원칙: 개별 코인별 개별 타임프레임별 독립 테이블
-- 목적: 파편화 방지, 순서 인덱싱 최적화, 캐시 효율성 극대화
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
    description TEXT,
    migration_notes TEXT
);

-- 초기 스키마 버전 기록
INSERT OR REPLACE INTO schema_version (version, description)
VALUES ('2.0.0', '최적화된 개별 코인별 테이블 구조');-- 지원되는 마켓 심볼 목록
CREATE TABLE IF NOT EXISTS market_symbols (
    symbol TEXT PRIMARY KEY,               -- 'KRW-BTC', 'KRW-ETH' 등
    base_currency TEXT NOT NULL,           -- 'BTC', 'ETH' 등
    quote_currency TEXT NOT NULL,          -- 'KRW', 'USDT' 등
    display_name_ko TEXT,                  -- '비트코인', '이더리움' 등
    display_name_en TEXT,                  -- 'Bitcoin', 'Ethereum' 등
    is_active BOOLEAN DEFAULT 1,
    price_precision INTEGER DEFAULT 8,     -- 가격 소수점 자릿수
    volume_precision INTEGER DEFAULT 8,    -- 거래량 소수점 자릿수
    min_order_amount REAL,                 -- 최소 주문 금액
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
    data_quality_score REAL DEFAULT 100.0, -- 0-100 데이터 품질 점수
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol),
    FOREIGN KEY (timeframe) REFERENCES timeframes(timeframe),
    UNIQUE(symbol, timeframe)
);

-- =====================================
-- 동적 캔들 테이블 생성 템플릿
-- =====================================

-- 캔들 테이블 생성 함수 (SQL 템플릿)
-- 테이블명 형식: candles_{SYMBOL}_{TIMEFRAME}
-- 예시: candles_KRW_BTC_1m, candles_KRW_ETH_5m

/*
개별 캔들 테이블 구조 (예시: candles_KRW_BTC_1m):

CREATE TABLE candles_KRW_BTC_1m (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL UNIQUE,   -- 캔들 시작 시간 (UTC)
    opening_price REAL NOT NULL,           -- 시가
    high_price REAL NOT NULL,              -- 고가
    low_price REAL NOT NULL,               -- 저가
    closing_price REAL NOT NULL,           -- 종가
    volume REAL NOT NULL,                  -- 거래량 (코인 수량)
    quote_volume REAL NOT NULL,            -- 거래대금 (KRW/USDT)
    trade_count INTEGER DEFAULT 0,         -- 거래 횟수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 최적화된 인덱스
    INDEX idx_timestamp DESC,              -- 시간 역순 조회 최적화
    INDEX idx_timestamp_range,             -- 범위 조회 최적화
    INDEX idx_created_at                   -- 삽입 순서 추적
);

-- 데이터 무결성 트리거
CREATE TRIGGER validate_candle_data_KRW_BTC_1m
    BEFORE INSERT ON candles_KRW_BTC_1m
    FOR EACH ROW
BEGIN
    -- 가격 유효성 검증
    SELECT CASE
        WHEN NEW.opening_price <= 0 OR NEW.high_price <= 0 OR
             NEW.low_price <= 0 OR NEW.closing_price <= 0 THEN
            RAISE(ABORT, 'Invalid price: all prices must be positive')
        WHEN NEW.high_price < NEW.low_price THEN
            RAISE(ABORT, 'Invalid price: high price cannot be less than low price')
        WHEN NEW.high_price < NEW.opening_price OR NEW.high_price < NEW.closing_price THEN
            RAISE(ABORT, 'Invalid price: high price must be >= opening and closing price')
        WHEN NEW.low_price > NEW.opening_price OR NEW.low_price > NEW.closing_price THEN
            RAISE(ABORT, 'Invalid price: low price must be <= opening and closing price')
        WHEN NEW.volume < 0 OR NEW.quote_volume < 0 THEN
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
        MIN(timestamp),
        MAX(timestamp)
    FROM candles_KRW_BTC_1m;
END;
*/

-- =====================================
-- 실시간 데이터 (단일 테이블)
-- =====================================

-- 실시간 티커 데이터 (최신 상태만 유지)
CREATE TABLE IF NOT EXISTS real_time_tickers (
    symbol TEXT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    current_price REAL NOT NULL,
    bid_price REAL,                        -- 매수 호가
    ask_price REAL,                        -- 매도 호가
    volume_24h REAL,                       -- 24시간 거래량
    quote_volume_24h REAL,                 -- 24시간 거래대금
    price_change_24h REAL,                 -- 24시간 가격 변동
    price_change_rate_24h REAL,            -- 24시간 변동률
    high_24h REAL,                         -- 24시간 최고가
    low_24h REAL,                          -- 24시간 최저가
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- 실시간 호가 데이터 (최신 상태만 유지)
CREATE TABLE IF NOT EXISTS real_time_orderbooks (
    symbol TEXT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    -- 매도 호가 (ask) - 상위 5개만 저장
    ask_price_1 REAL, ask_size_1 REAL,
    ask_price_2 REAL, ask_size_2 REAL,
    ask_price_3 REAL, ask_size_3 REAL,
    ask_price_4 REAL, ask_size_4 REAL,
    ask_price_5 REAL, ask_size_5 REAL,
    -- 매수 호가 (bid) - 상위 5개만 저장
    bid_price_1 REAL, bid_size_1 REAL,
    bid_price_2 REAL, bid_size_2 REAL,
    bid_price_3 REAL, bid_size_3 REAL,
    bid_price_4 REAL, bid_size_4 REAL,
    bid_price_5 REAL, bid_size_5 REAL,
    total_ask_size REAL,                   -- 총 매도 물량
    total_bid_size REAL,                   -- 총 매수 물량
    spread REAL,                           -- 스프레드
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- =====================================
-- 데이터 품질 및 모니터링
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

-- 데이터 품질 로그
CREATE TABLE IF NOT EXISTS quality_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    check_date DATE NOT NULL,
    missing_candles INTEGER DEFAULT 0,
    invalid_prices INTEGER DEFAULT 0,
    zero_volumes INTEGER DEFAULT 0,
    completeness_rate REAL DEFAULT 100.0,  -- 완성도 (%)
    quality_score REAL DEFAULT 100.0,      -- 품질 점수 (0-100)
    issues TEXT,                           -- JSON 형태 이슈 목록
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
CREATE INDEX IF NOT EXISTS idx_tickers_timestamp ON real_time_tickers(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderbooks_timestamp ON real_time_orderbooks(timestamp DESC);

-- 수집 상태 인덱스
CREATE INDEX IF NOT EXISTS idx_collection_status_next ON collection_status(next_collection_at);
CREATE INDEX IF NOT EXISTS idx_collection_status_auto ON collection_status(auto_enabled);

-- 품질 로그 인덱스
CREATE INDEX IF NOT EXISTS idx_quality_logs_date ON quality_logs(check_date DESC);
CREATE INDEX IF NOT EXISTS idx_quality_logs_score ON quality_logs(quality_score);

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
    ct.data_quality_score,
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
    rt.current_price,
    rt.price_change_rate_24h,
    rt.quote_volume_24h,
    rt.timestamp as last_updated,
    CASE
        WHEN rt.price_change_rate_24h > 5 THEN 'strong_up'
        WHEN rt.price_change_rate_24h > 0 THEN 'up'
        WHEN rt.price_change_rate_24h < -5 THEN 'strong_down'
        WHEN rt.price_change_rate_24h < 0 THEN 'down'
        ELSE 'neutral'
    END as trend_signal
FROM market_symbols ms
LEFT JOIN real_time_tickers rt ON ms.symbol = rt.symbol
WHERE ms.is_active = 1
ORDER BY rt.quote_volume_24h DESC NULLS LAST;

-- =====================================
-- 데이터 정리 및 유지보수
-- =====================================

-- 오래된 실시간 데이터 정리 (7일 이상된 데이터)
-- 주기적으로 실행할 정리 쿼리들을 별도 스크립트로 관리

-- 테이블 생성 기록
INSERT OR IGNORE INTO schema_version (version, description)
VALUES (
    '2.0.0-base',
    '기본 메타 테이블 생성 완료'
);
