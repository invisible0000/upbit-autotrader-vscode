-- Upbit Auto Trading - Market Data Database Schema
-- ==============================================
-- DB: market_data.sqlite3
-- 용도: 프로그램 전체에서 공유되어 저장/사용되는 마켓 데이터
-- 생성일: 2025-08-01
-- 관리 대상: OHLCV 데이터, 시장 정보, 지표 계산 결과, 스크리너 데이터

PRAGMA foreign_keys = ON;

-- =====================================
-- 기본 시장 데이터
-- =====================================

-- 시장 정보 (거래 가능한 심볼들)
CREATE TABLE market_symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,           -- 'KRW-BTC', 'KRW-ETH' 등
    base_currency TEXT NOT NULL,           -- 'BTC', 'ETH' 등
    quote_currency TEXT NOT NULL,          -- 'KRW', 'USDT' 등
    display_name_ko TEXT,                  -- '비트코인', '이더리움' 등
    display_name_en TEXT,                  -- 'Bitcoin', 'Ethereum' 등
    market_warning TEXT,                   -- 'NONE', 'CAUTION' 등
    is_active BOOLEAN DEFAULT 1,
    min_order_amount REAL,                 -- 최소 주문 금액
    max_order_amount REAL,                 -- 최대 주문 금액
    price_precision INTEGER DEFAULT 8,     -- 가격 소수점 자릿수
    volume_precision INTEGER DEFAULT 8,    -- 거래량 소수점 자릿수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OHLCV 캔들 데이터 (1분봉 기준)
CREATE TABLE candlestick_data_1m (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,          -- 캔들 시작 시간 (KST)
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume REAL NOT NULL,                  -- 거래량 (코인 수량)
    quote_volume REAL NOT NULL,            -- 거래대금 (KRW)
    trade_count INTEGER DEFAULT 0,         -- 거래 횟수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- OHLCV 캔들 데이터 (5분봉)
CREATE TABLE candlestick_data_5m (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume REAL NOT NULL,
    quote_volume REAL NOT NULL,
    trade_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- OHLCV 캔들 데이터 (1시간봉)
CREATE TABLE candlestick_data_1h (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume REAL NOT NULL,
    quote_volume REAL NOT NULL,
    trade_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- OHLCV 캔들 데이터 (1일봉)
CREATE TABLE candlestick_data_1d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,          -- 날짜 (YYYY-MM-DD 00:00:00)
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume REAL NOT NULL,
    quote_volume REAL NOT NULL,
    trade_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- =====================================
-- 기술적 지표 계산 결과
-- =====================================

-- 기술적 지표 데이터 (1일봉 기준)
CREATE TABLE technical_indicators_1d (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    -- 이동평균선들
    sma_5 REAL,
    sma_10 REAL,
    sma_20 REAL,
    sma_50 REAL,
    sma_100 REAL,
    sma_200 REAL,
    ema_12 REAL,
    ema_26 REAL,
    -- 모멘텀 지표들
    rsi_14 REAL,
    stoch_k REAL,
    stoch_d REAL,
    macd_line REAL,
    macd_signal REAL,
    macd_histogram REAL,
    -- 변동성 지표들
    bb_upper REAL,                         -- 볼린저밴드 상단
    bb_middle REAL,                        -- 볼린저밴드 중간선
    bb_lower REAL,                         -- 볼린저밴드 하단
    bb_width REAL,                         -- 볼린저밴드 폭
    atr_14 REAL,                          -- Average True Range
    -- 거래량 지표들
    volume_sma_20 REAL,
    volume_ratio REAL,                     -- 현재 거래량 / 평균 거래량
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- 기술적 지표 데이터 (1시간봉 기준)
CREATE TABLE technical_indicators_1h (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    sma_20 REAL,
    sma_50 REAL,
    ema_12 REAL,
    ema_26 REAL,
    rsi_14 REAL,
    macd_line REAL,
    macd_signal REAL,
    macd_histogram REAL,
    bb_upper REAL,
    bb_middle REAL,
    bb_lower REAL,
    atr_14 REAL,
    volume_sma_20 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- =====================================
-- 실시간 데이터
-- =====================================

-- 실시간 시세 (현재가, 호가)
CREATE TABLE real_time_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    current_price REAL NOT NULL,
    bid_price REAL,                        -- 매수 호가
    ask_price REAL,                        -- 매도 호가
    bid_size REAL,                         -- 매수 호가 수량
    ask_size REAL,                         -- 매도 호가 수량
    volume_24h REAL,                       -- 24시간 거래량
    quote_volume_24h REAL,                 -- 24시간 거래대금
    price_change_24h REAL,                 -- 24시간 가격 변동
    price_change_rate_24h REAL,            -- 24시간 변동률
    high_24h REAL,                         -- 24시간 최고가
    low_24h REAL,                          -- 24시간 최저가
    market_state TEXT DEFAULT 'ACTIVE',    -- 'ACTIVE', 'PREVIEW', 'DELISTED'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- 호가창 데이터
CREATE TABLE order_book_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    -- 매도 호가 (ask) - 상위 10개
    ask_price_1 REAL, ask_size_1 REAL,
    ask_price_2 REAL, ask_size_2 REAL,
    ask_price_3 REAL, ask_size_3 REAL,
    ask_price_4 REAL, ask_size_4 REAL,
    ask_price_5 REAL, ask_size_5 REAL,
    ask_price_6 REAL, ask_size_6 REAL,
    ask_price_7 REAL, ask_size_7 REAL,
    ask_price_8 REAL, ask_size_8 REAL,
    ask_price_9 REAL, ask_size_9 REAL,
    ask_price_10 REAL, ask_size_10 REAL,
    -- 매수 호가 (bid) - 상위 10개
    bid_price_1 REAL, bid_size_1 REAL,
    bid_price_2 REAL, bid_size_2 REAL,
    bid_price_3 REAL, bid_size_3 REAL,
    bid_price_4 REAL, bid_size_4 REAL,
    bid_price_5 REAL, bid_size_5 REAL,
    bid_price_6 REAL, bid_size_6 REAL,
    bid_price_7 REAL, bid_size_7 REAL,
    bid_price_8 REAL, bid_size_8 REAL,
    bid_price_9 REAL, bid_size_9 REAL,
    bid_price_10 REAL, bid_size_10 REAL,
    total_ask_size REAL,                   -- 총 매도 물량
    total_bid_size REAL,                   -- 총 매수 물량
    spread REAL,                           -- 스프레드 (ask_price_1 - bid_price_1)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- =====================================
-- 시뮬레이션용 마켓 데이터
-- =====================================

-- 시뮬레이션용 마켓 데이터 (백테스팅)
CREATE TABLE simulation_market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    timeframe TEXT NOT NULL,               -- '1m', '5m', '1h', '1d'
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume REAL NOT NULL,
    quote_volume REAL NOT NULL,
    -- 계산된 지표들 (빠른 접근을 위해)
    sma_20 REAL,
    ema_12 REAL,
    rsi_14 REAL,
    macd REAL,
    bb_upper REAL,
    bb_lower REAL,
    atr_14 REAL,
    data_source TEXT DEFAULT 'upbit',      -- 'upbit', 'binance', 'manual' 등
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timestamp, timeframe),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- =====================================
-- 마켓 분석 및 스크리너
-- =====================================

-- 일일 마켓 분석 결과
CREATE TABLE daily_market_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_date DATE NOT NULL,
    symbol TEXT NOT NULL,
    -- 기본 통계
    price_change_24h REAL,
    volume_change_24h REAL,
    volatility REAL,                       -- 변동성 (표준편차)
    -- 기술적 분석 신호
    trend_signal TEXT,                     -- 'bullish', 'bearish', 'neutral'
    momentum_signal TEXT,
    volume_signal TEXT,
    -- 종합 점수
    technical_score REAL,                  -- 0-100 기술적 점수
    volume_score REAL,                     -- 0-100 거래량 점수
    overall_score REAL,                    -- 0-100 종합 점수
    -- 알고리즘 판단
    recommendation TEXT,                   -- 'strong_buy', 'buy', 'hold', 'sell', 'strong_sell'
    confidence_level REAL,                -- 0-1 신뢰도
    analysis_notes TEXT,                   -- JSON 형태의 상세 분석
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_date, symbol),
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- 스크리너 결과 (조건 기반 종목 선별)
CREATE TABLE screener_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_date DATE NOT NULL,
    scan_name TEXT NOT NULL,               -- 스크린 조건 이름
    symbol TEXT NOT NULL,
    rank_score REAL,                       -- 순위 점수
    matching_conditions TEXT,              -- JSON: 매칭된 조건들
    key_metrics TEXT,                      -- JSON: 주요 지표 값들
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol) REFERENCES market_symbols(symbol)
);

-- 마켓 상태 요약 (전체 마켓 현황)
CREATE TABLE market_state_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summary_date DATE NOT NULL UNIQUE,
    total_market_cap REAL,                 -- 전체 시가총액 (KRW 기준)
    total_volume_24h REAL,                 -- 전체 24시간 거래량
    active_symbols_count INTEGER,          -- 활성 심볼 수
    trending_up_count INTEGER,             -- 상승 종목 수
    trending_down_count INTEGER,           -- 하락 종목 수
    high_volume_symbols TEXT,              -- JSON: 고거래량 종목들
    top_gainers TEXT,                      -- JSON: 상위 상승 종목들
    top_losers TEXT,                       -- JSON: 상위 하락 종목들
    market_sentiment TEXT,                 -- 'bullish', 'bearish', 'neutral'
    fear_greed_index REAL,                 -- 공포탐욕지수 (0-100)
    volatility_index REAL,                 -- 시장 변동성 지수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 데이터 품질 및 메타정보
-- =====================================

-- 데이터 품질 모니터링
CREATE TABLE data_quality_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    timeframe TEXT,
    data_date DATE NOT NULL,
    missing_candles_count INTEGER DEFAULT 0,
    invalid_prices_count INTEGER DEFAULT 0,
    zero_volume_count INTEGER DEFAULT 0,
    data_completeness_rate REAL,          -- 0-1 데이터 완성도
    quality_score REAL,                   -- 0-100 품질 점수
    issues_detected TEXT,                 -- JSON: 발견된 문제들
    corrective_actions TEXT,              -- JSON: 수정 조치들
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 데이터 수집 상태
CREATE TABLE data_collection_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    last_collected_at TIMESTAMP,
    next_collection_at TIMESTAMP,
    collection_status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    last_candle_timestamp TIMESTAMP,      -- 마지막 수집된 캔들 시간
    collection_gap_hours REAL,            -- 수집 갭 (시간)
    auto_collection_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timeframe)
);

-- =====================================
-- 인덱스 생성
-- =====================================

-- 기본 마켓 데이터 인덱스
CREATE INDEX idx_market_symbols_symbol ON market_symbols(symbol);
CREATE INDEX idx_market_symbols_is_active ON market_symbols(is_active);
CREATE INDEX idx_market_symbols_quote_currency ON market_symbols(quote_currency);

-- 캔들 데이터 인덱스 (시간별)
CREATE INDEX idx_candlestick_1m_symbol_timestamp ON candlestick_data_1m(symbol, timestamp DESC);
CREATE INDEX idx_candlestick_5m_symbol_timestamp ON candlestick_data_5m(symbol, timestamp DESC);
CREATE INDEX idx_candlestick_1h_symbol_timestamp ON candlestick_data_1h(symbol, timestamp DESC);
CREATE INDEX idx_candlestick_1d_symbol_timestamp ON candlestick_data_1d(symbol, timestamp DESC);

-- 기술적 지표 인덱스
CREATE INDEX idx_technical_indicators_1d_symbol_timestamp ON technical_indicators_1d(symbol, timestamp DESC);
CREATE INDEX idx_technical_indicators_1h_symbol_timestamp ON technical_indicators_1h(symbol, timestamp DESC);

-- 실시간 데이터 인덱스
CREATE INDEX idx_real_time_quotes_symbol ON real_time_quotes(symbol);
CREATE INDEX idx_real_time_quotes_timestamp ON real_time_quotes(timestamp DESC);
CREATE INDEX idx_order_book_symbol_timestamp ON order_book_snapshots(symbol, timestamp DESC);

-- 시뮬레이션 데이터 인덱스
CREATE INDEX idx_simulation_market_data_symbol_timeframe ON simulation_market_data(symbol, timeframe, timestamp DESC);

-- 분석 결과 인덱스
CREATE INDEX idx_daily_market_analysis_date ON daily_market_analysis(analysis_date DESC);
CREATE INDEX idx_daily_market_analysis_symbol ON daily_market_analysis(symbol);
CREATE INDEX idx_daily_market_analysis_score ON daily_market_analysis(overall_score DESC);
CREATE INDEX idx_screener_results_scan_date ON screener_results(scan_date DESC);
CREATE INDEX idx_screener_results_scan_name ON screener_results(scan_name);

-- 데이터 품질 인덱스
CREATE INDEX idx_data_quality_logs_data_date ON data_quality_logs(data_date DESC);
CREATE INDEX idx_data_collection_status_symbol_timeframe ON data_collection_status(symbol, timeframe);
CREATE INDEX idx_data_collection_status_next_collection ON data_collection_status(next_collection_at);

-- =====================================
-- 뷰 생성
-- =====================================

-- 최신 시세 요약 뷰
CREATE VIEW IF NOT EXISTS latest_market_summary AS
SELECT 
    ms.symbol,
    ms.display_name_ko,
    ms.base_currency,
    ms.quote_currency,
    rtq.current_price,
    rtq.price_change_24h,
    rtq.price_change_rate_24h,
    rtq.volume_24h,
    rtq.quote_volume_24h,
    rtq.high_24h,
    rtq.low_24h,
    rtq.timestamp as last_updated
FROM market_symbols ms
LEFT JOIN real_time_quotes rtq ON ms.symbol = rtq.symbol
WHERE ms.is_active = 1
  AND rtq.id IN (
    SELECT MAX(id) 
    FROM real_time_quotes 
    GROUP BY symbol
  );

-- 기술적 분석 최신 상태 뷰
CREATE VIEW IF NOT EXISTS latest_technical_analysis AS
SELECT 
    ti.symbol,
    ti.timestamp,
    ti.rsi_14,
    ti.macd_line,
    ti.macd_signal,
    ti.bb_upper,
    ti.bb_middle,
    ti.bb_lower,
    ti.atr_14,
    CASE 
        WHEN ti.rsi_14 > 70 THEN 'overbought'
        WHEN ti.rsi_14 < 30 THEN 'oversold'
        ELSE 'neutral'
    END as rsi_signal,
    CASE 
        WHEN ti.macd_line > ti.macd_signal THEN 'bullish'
        WHEN ti.macd_line < ti.macd_signal THEN 'bearish'
        ELSE 'neutral'
    END as macd_signal
FROM technical_indicators_1d ti
WHERE ti.id IN (
    SELECT MAX(id) 
    FROM technical_indicators_1d 
    GROUP BY symbol
);

-- 고거래량 종목 뷰
CREATE VIEW IF NOT EXISTS high_volume_symbols AS
SELECT 
    rtq.symbol,
    ms.display_name_ko,
    rtq.current_price,
    rtq.volume_24h,
    rtq.quote_volume_24h,
    rtq.price_change_rate_24h,
    RANK() OVER (ORDER BY rtq.quote_volume_24h DESC) as volume_rank
FROM real_time_quotes rtq
JOIN market_symbols ms ON rtq.symbol = ms.symbol
WHERE rtq.id IN (
    SELECT MAX(id) 
    FROM real_time_quotes 
    GROUP BY symbol
)
  AND ms.is_active = 1
  AND rtq.quote_volume_24h > 0
ORDER BY rtq.quote_volume_24h DESC;

-- =====================================
-- 트리거 생성
-- =====================================

-- 마켓 심볼 업데이트 시간 자동 갱신
CREATE TRIGGER IF NOT EXISTS update_market_symbols_timestamp
    AFTER UPDATE ON market_symbols
    FOR EACH ROW
BEGIN
    UPDATE market_symbols 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- 데이터 수집 상태 업데이트 시간 자동 갱신
CREATE TRIGGER IF NOT EXISTS update_data_collection_status_timestamp
    AFTER UPDATE ON data_collection_status
    FOR EACH ROW
BEGIN
    UPDATE data_collection_status 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;
