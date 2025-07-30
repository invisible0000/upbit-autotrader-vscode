-- 트레이딩 지표 변수 관리 시스템 DB 스키마 (기존 코드 호환 완벽 버전)
-- SQLite3 호환 (버전 3.49.1 확인 완료)
-- 
-- ⚠️ 중요: 애플리케이션 레벨에서 파라미터 값의 숫자/타입 검증이 반드시 필요함
-- tv_variable_parameters 테이블의 min_value, max_value, default_value는 TEXT 타입으로 저장되므로
-- Python 애플리케이션에서 parameter_type에 따른 적절한 타입 변환 및 범위 검증을 수행해야 함

-- UI 표시 텍스트(display_name_ko, description 등)를 DB에서 관리하여
-- 향후 지표 추가/수정 시 UI 코드 변경 없이 데이터만으로 확장 가능하도록 함.

-- 🏗️ 테이블 접두사 규칙: tv_ (Trading Variables)
-- 이는 향후 다른 모듈 추가 시 이름 충돌을 방지하고 명확한 분류를 위함
-- 예: auth_users (인증), chart_settings (차트), strategy_rules (전략) 등

-- 트레이딩 변수 메인 테이블
CREATE TABLE IF NOT EXISTS tv_trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'RSI', 'SMA', 'BOLLINGER_BAND' (기존 코드 호환)
    display_name_ko TEXT NOT NULL,          -- '단순이동평균', 'RSI 지표'
    display_name_en TEXT,                   -- 'Simple Moving Average', 'RSI Indicator'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum', 'volatility', 'volume', 'price', 'capital', 'state'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable', etc.
    is_active BOOLEAN DEFAULT 1,            -- 활성화 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                       -- 지표 설명
    source TEXT DEFAULT 'built-in'          -- 'built-in', 'tradingview', 'custom'
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_tv_purpose_category ON tv_trading_variables(purpose_category);
CREATE INDEX IF NOT EXISTS idx_tv_chart_category ON tv_trading_variables(chart_category);
CREATE INDEX IF NOT EXISTS idx_tv_comparison_group ON tv_trading_variables(comparison_group);
CREATE INDEX IF NOT EXISTS idx_tv_is_active ON tv_trading_variables(is_active);

-- 지표별 파라미터 정의 테이블
CREATE TABLE IF NOT EXISTS tv_variable_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,              -- 'RSI', 'SMA' 등 지표 ID
    parameter_name TEXT NOT NULL,           -- 'period', 'source', 'multiplier'
    parameter_type TEXT NOT NULL,           -- 'integer', 'float', 'string', 'boolean', 'enum'
    default_value TEXT,                     -- 기본값 (문자열로 저장)
    min_value TEXT,                         -- 최소값 (숫자형일 때)
    max_value TEXT,                         -- 최대값 (숫자형일 때)
    enum_values TEXT,                       -- enum 타입일 때 가능한 값들 (JSON 배열)
    is_required BOOLEAN DEFAULT 1,          -- 필수 파라미터 여부
    display_name_ko TEXT NOT NULL,          -- '기간', '데이터 소스'
    display_name_en TEXT,                   -- 'Period', 'Data Source'
    description TEXT,                       -- 파라미터 설명
    display_order INTEGER DEFAULT 0,        -- UI 표시 순서
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id) ON DELETE CASCADE
);

-- 파라미터 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_tv_variable_parameters_variable_id ON tv_variable_parameters(variable_id);
CREATE INDEX IF NOT EXISTS idx_tv_variable_parameters_display_order ON tv_variable_parameters(variable_id, display_order);

-- 현재 활성 지표들 데이터 입력 (기존 코드와 완벽 호환)
INSERT OR REPLACE INTO tv_trading_variables VALUES 
-- 📈 추세 지표 (Trend Indicators)
('SMA', '단순이동평균', 'Simple Moving Average', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간의 가격을 산술 평균한 값', 'built-in'),
('EMA', '지수이동평균', 'Exponential Moving Average', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '최근 가격에 더 큰 가중치를 부여한 이동평균', 'built-in'),

-- ⚡ 모멘텀 지표 (Momentum Indicators)
('RSI', 'RSI 지표', 'Relative Strength Index', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '상승압력과 하락압력 간의 상대적 강도를 나타내는 모멘텀 지표', 'built-in'),
('STOCHASTIC', '스토캐스틱', 'Stochastic Oscillator', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간 주가 변동 범위에서 현재 주가의 위치를 백분율로 표시', 'built-in'),
('MACD', 'MACD 지표', 'Moving Average Convergence Divergence', 'momentum', 'subplot', 'signal_conditional', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '두 이동평균선 사이의 관계를 보여주는 모멘텀 및 추세 지표', 'built-in'),

-- 🔥 변동성 지표 (Volatility Indicators)
('BOLLINGER_BAND', '볼린저 밴드', 'Bollinger Bands', 'volatility', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '이동평균선과 표준편차를 이용한 변동성 채널', 'built-in'),
('ATR', '평균실제범위', 'Average True Range', 'volatility', 'subplot', 'volatility_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '주가의 변동성을 측정하는 지표. 절대적인 가격 변동폭을 나타냄', 'built-in'),

-- 📦 거래량 지표 (Volume Indicators)
('VOLUME', '거래량', 'Volume', 'volume', 'subplot', 'volume_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간 동안 거래된 주식의 총 수량', 'built-in'),
('VOLUME_SMA', '거래량 이동평균', 'Volume Simple Moving Average', 'volume', 'subplot', 'volume_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '거래량의 단순이동평균으로 평균 거래량 대비 현재 거래량 비교', 'built-in'),

-- 💰 가격 데이터 (Price Data)
('CURRENT_PRICE', '현재가', 'Current Price', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '현재 시점의 가격', 'built-in'),
('OPEN_PRICE', '시가', 'Open Price', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간의 시작 가격', 'built-in'),
('HIGH_PRICE', '고가', 'High Price', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간의 최고가', 'built-in'),
('LOW_PRICE', '저가', 'Low Price', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간의 최저가', 'built-in'),

-- 💳 자본 관리 (Capital Management)
('CASH_BALANCE', '현금 잔고', 'Cash Balance', 'capital', 'subplot', 'capital_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '사용 가능한 현금 잔고', 'built-in'),
('COIN_BALANCE', '코인 보유량', 'Coin Balance', 'capital', 'subplot', 'capital_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '현재 보유중인 코인 수량', 'built-in'),
('TOTAL_BALANCE', '총 자산', 'Total Balance', 'capital', 'subplot', 'capital_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '현금과 코인을 합친 총 자산', 'built-in'),

-- 📊 거래 상태 (Trading State)
('PROFIT_PERCENT', '현재 수익률(%)', 'Current Profit Percentage', 'state', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '매수가 대비 현재 수익률', 'built-in'),
('PROFIT_AMOUNT', '현재 수익 금액', 'Current Profit Amount', 'state', 'subplot', 'capital_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '매수가 대비 현재 수익 금액', 'built-in'),
('POSITION_SIZE', '포지션 크기', 'Position Size', 'state', 'subplot', 'quantity_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '현재 포지션의 크기', 'built-in'),
('AVG_BUY_PRICE', '평균 매수가', 'Average Buy Price', 'state', 'subplot', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '수수료 포함 평균 매수가', 'built-in');

-- 비교 그룹 정의를 위한 메타데이터 테이블 (추후 확장용)
CREATE TABLE IF NOT EXISTS tv_comparison_groups (
    group_id TEXT PRIMARY KEY,
    group_name_ko TEXT NOT NULL,
    group_name_en TEXT NOT NULL,
    description TEXT,
    can_compare_with TEXT,  -- JSON 형태로 호환 가능한 그룹들 저장
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 비교 그룹 메타데이터 삽입
INSERT OR REPLACE INTO tv_comparison_groups VALUES
('price_comparable', '가격 비교 가능', 'Price Comparable', '가격 기반 지표들끼리 비교 가능', '["price_comparable"]', CURRENT_TIMESTAMP),
('percentage_comparable', '퍼센트 비교 가능', 'Percentage Comparable', '0-100% 범위의 지표들끼리 비교 가능', '["percentage_comparable"]', CURRENT_TIMESTAMP),
('signal_conditional', '신호 조건부', 'Signal Conditional', '특별한 신호 조건에서만 비교 가능', '["signal_conditional"]', CURRENT_TIMESTAMP),
('volatility_comparable', '변동성 비교 가능', 'Volatility Comparable', '변동성 지표들끼리 비교 가능', '["volatility_comparable"]', CURRENT_TIMESTAMP),
('volume_comparable', '거래량 비교 가능', 'Volume Comparable', '거래량 기반 지표들끼리 비교 가능', '["volume_comparable"]', CURRENT_TIMESTAMP),
('capital_comparable', '자본 비교 가능', 'Capital Comparable', '자본/자산 관련 지표들끼리 비교 가능', '["capital_comparable"]', CURRENT_TIMESTAMP),
('quantity_comparable', '수량 비교 가능', 'Quantity Comparable', '수량 관련 지표들끼리 비교 가능', '["quantity_comparable"]', CURRENT_TIMESTAMP);

-- 스키마 버전 관리
CREATE TABLE IF NOT EXISTS tv_schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR REPLACE INTO tv_schema_version VALUES 
('2.0.0', CURRENT_TIMESTAMP, '기존 코드 완벽 호환 - 테이블명 접두사 적용, 누락된 변수 추가, 카테고리 시스템 통합');

-- 주요 지표들의 파라미터 정의 추가 (기존 코드 패턴 반영)
INSERT OR REPLACE INTO tv_variable_parameters VALUES
-- RSI 파라미터 (기존 코드 패턴)
(1, 'RSI', 'period', 'integer', '14', '2', '240', NULL, 1, '기간', 'Period', 'RSI 계산 기간', 1, CURRENT_TIMESTAMP),
(2, 'RSI', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '봉 단위 시간 (전략 기본값 사용 시 무시)', 2, CURRENT_TIMESTAMP),

-- SMA 파라미터 (기존 코드 패턴)
(3, 'SMA', 'period', 'integer', '20', '1', '240', NULL, 1, '기간', 'Period', '단기: 5,10,20 / 중기: 60,120 / 장기: 200,240', 1, CURRENT_TIMESTAMP),
(4, 'SMA', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '봉 단위 시간', 2, CURRENT_TIMESTAMP),

-- EMA 파라미터 (기존 코드 패턴)
(5, 'EMA', 'period', 'integer', '12', '1', '240', NULL, 1, '기간', 'Period', '지수이동평균 계산 기간', 1, CURRENT_TIMESTAMP),
(6, 'EMA', 'exponential_factor', 'float', '2.0', '0.1', '10.0', NULL, 1, '지수 계수', 'Exponential Factor', '지수 가중치 (2/(기간+1)이 표준)', 2, CURRENT_TIMESTAMP),
(7, 'EMA', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '봉 단위 시간', 3, CURRENT_TIMESTAMP),

-- STOCHASTIC 파라미터 (기존 코드 패턴)
(8, 'STOCHASTIC', 'k_period', 'integer', '14', '1', '100', NULL, 1, '%K 기간', '%K Period', '%K 라인 계산 기간', 1, CURRENT_TIMESTAMP),
(9, 'STOCHASTIC', 'd_period', 'integer', '3', '1', '50', NULL, 1, '%D 기간', '%D Period', '%D 라인 계산 기간', 2, CURRENT_TIMESTAMP),
(10, 'STOCHASTIC', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '봉 단위 시간', 3, CURRENT_TIMESTAMP),

-- MACD 파라미터 (기존 코드 패턴 + 개선)
(11, 'MACD', 'fast_period', 'integer', '12', '1', '50', NULL, 1, '빠른 기간', 'Fast Period', '빠른 EMA 기간', 1, CURRENT_TIMESTAMP),
(12, 'MACD', 'slow_period', 'integer', '26', '1', '100', NULL, 1, '느린 기간', 'Slow Period', '느린 EMA 기간', 2, CURRENT_TIMESTAMP),
(13, 'MACD', 'signal_period', 'integer', '9', '1', '50', NULL, 1, '시그널 기간', 'Signal Period', '시그널 라인 기간', 3, CURRENT_TIMESTAMP),
(14, 'MACD', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '봉 단위 시간', 4, CURRENT_TIMESTAMP),

-- BOLLINGER_BAND 파라미터 (기존 코드 이름 + 개선)
(15, 'BOLLINGER_BAND', 'period', 'integer', '20', '2', '100', NULL, 1, '기간', 'Period', '이동평균 기간', 1, CURRENT_TIMESTAMP),
(16, 'BOLLINGER_BAND', 'multiplier', 'float', '2.0', '0.1', '5.0', NULL, 1, '표준편차 배수', 'Std Dev Multiplier', '표준편차 곱셈 계수', 2, CURRENT_TIMESTAMP),
(17, 'BOLLINGER_BAND', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '봉 단위 시간', 3, CURRENT_TIMESTAMP),

-- ATR 파라미터
(18, 'ATR', 'period', 'integer', '14', '1', '100', NULL, 1, '기간', 'Period', 'ATR 계산 기간', 1, CURRENT_TIMESTAMP),
(19, 'ATR', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "3분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '봉 단위 시간', 2, CURRENT_TIMESTAMP),

-- VOLUME 파라미터 (기존 코드 패턴)
(20, 'VOLUME', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '거래량 기준 봉 단위', 1, CURRENT_TIMESTAMP),
(21, 'VOLUME', 'volume_type', 'enum', '거래량', NULL, NULL, '["거래량", "거래대금", "상대거래량"]', 1, '거래량 종류', 'Volume Type', '거래량: 코인수량, 거래대금: 원화금액, 상대거래량: 평균대비 비율', 2, CURRENT_TIMESTAMP),

-- VOLUME_SMA 파라미터 (기존 코드에서 사용)
(22, 'VOLUME_SMA', 'period', 'integer', '20', '1', '240', NULL, 1, '기간', 'Period', '거래량 이동평균 계산 기간', 1, CURRENT_TIMESTAMP),
(23, 'VOLUME_SMA', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '봉 단위 시간', 2, CURRENT_TIMESTAMP),

-- 가격 데이터 파라미터들 (기존 코드 패턴)
(24, 'OPEN_PRICE', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '시가 기준 봉 단위 (당일 시작가 등)', 1, CURRENT_TIMESTAMP),
(25, 'HIGH_PRICE', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '고가 기준 봉 단위', 1, CURRENT_TIMESTAMP),
(26, 'LOW_PRICE', 'timeframe', 'enum', '포지션 설정 따름', NULL, NULL, '["포지션 설정 따름", "1분", "5분", "15분", "30분", "1시간", "4시간", "1일"]', 1, '타임프레임', 'Timeframe', '저가 기준 봉 단위', 1, CURRENT_TIMESTAMP),

-- 자본 관리 파라미터들 (기존 코드 패턴)
(27, 'TOTAL_BALANCE', 'currency', 'enum', 'KRW', NULL, NULL, '["KRW", "USD", "BTC"]', 1, '표시 통화', 'Display Currency', '총 자산 표시 기준 통화', 1, CURRENT_TIMESTAMP),
(28, 'TOTAL_BALANCE', 'scope', 'enum', '포지션제한', NULL, NULL, '["포지션제한", "계좌전체"]', 1, '범위', 'Scope', '포지션 할당 자본 vs 전체 계좌', 2, CURRENT_TIMESTAMP),

(29, 'CASH_BALANCE', 'currency', 'enum', 'KRW', NULL, NULL, '["KRW", "USD", "BTC"]', 1, '표시 통화', 'Display Currency', '현금 잔고 표시 기준 통화', 1, CURRENT_TIMESTAMP),
(30, 'CASH_BALANCE', 'scope', 'enum', '포지션제한', NULL, NULL, '["포지션제한", "계좌전체"]', 1, '범위', 'Scope', '포지션 할당 vs 전체 사용가능 현금', 2, CURRENT_TIMESTAMP),

(31, 'COIN_BALANCE', 'coin_unit', 'enum', '코인수량', NULL, NULL, '["코인수량", "원화가치", "USD가치"]', 1, '표시 단위', 'Display Unit', '코인 보유량 표시 방식', 1, CURRENT_TIMESTAMP),
(32, 'COIN_BALANCE', 'scope', 'enum', '현재코인', NULL, NULL, '["현재코인", "전체코인"]', 1, '범위', 'Scope', '현재 거래중인 코인 vs 보유한 모든 코인', 2, CURRENT_TIMESTAMP),

-- 거래 상태 파라미터들 (기존 코드 패턴)
(33, 'PROFIT_AMOUNT', 'currency', 'enum', 'KRW', NULL, NULL, '["KRW", "USD", "BTC"]', 1, '표시 통화', 'Display Currency', '수익 금액 표시 통화', 1, CURRENT_TIMESTAMP),
(34, 'PROFIT_AMOUNT', 'calculation_method', 'enum', '미실현', NULL, NULL, '["미실현", "실현", "전체"]', 1, '계산 방식', 'Calculation Method', '미실현: 현재가기준, 실현: 매도완료, 전체: 누적', 2, CURRENT_TIMESTAMP),
(35, 'PROFIT_AMOUNT', 'include_fees', 'enum', '포함', NULL, NULL, '["포함", "제외"]', 1, '수수료 포함', 'Include Fees', '거래 수수료 및 슬리피지 포함 여부', 3, CURRENT_TIMESTAMP),

(36, 'POSITION_SIZE', 'unit_type', 'enum', '수량', NULL, NULL, '["수량", "금액", "비율"]', 1, '단위 형태', 'Unit Type', '수량: 코인개수, 금액: 원화가치, 비율: 포트폴리오대비%', 1, CURRENT_TIMESTAMP),

(37, 'AVG_BUY_PRICE', 'display_currency', 'enum', '원화', NULL, NULL, '["원화", "USD", "코인단위"]', 1, '표시 통화', 'Display Currency', '평균 매수가 표시 통화 (수수료 포함된 평단가)', 1, CURRENT_TIMESTAMP);

-- 성공적인 스키마 생성 확인
SELECT 'Trading Variables Schema v2.0.0 (기존 코드 완벽 호환) successfully created!' as status,
       COUNT(*) as total_indicators,
       (SELECT COUNT(*) FROM tv_variable_parameters) as total_parameters
FROM tv_trading_variables 
WHERE is_active = 1;
