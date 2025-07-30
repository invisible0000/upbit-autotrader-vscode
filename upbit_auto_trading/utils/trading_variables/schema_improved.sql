-- 트레이딩 지표 변수 관리 시스템 DB 스키마 (개선판)
-- SQLite3 호환 (버전 3.49.1 확인 완료)
-- 
-- ⚠️ 중요: 애플리케이션 레벨에서 파라미터 값의 숫자/타입 검증이 반드시 필요함
-- variable_parameters 테이블의 min_value, max_value, default_value는 TEXT 타입으로 저장되므로
-- Python 애플리케이션에서 parameter_type에 따른 적절한 타입 변환 및 범위 검증을 수행해야 함

-- UI 표시 텍스트(display_name_ko, description 등)를 DB에서 관리하여
-- 향후 지표 추가/수정 시 UI 코드 변경 없이 데이터만으로 확장 가능하도록 함.
-- 트레이딩 변수 메인 테이블
CREATE TABLE IF NOT EXISTS trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'RSI', 'MACD', 'BOLLINGER_BANDS'
    display_name_ko TEXT NOT NULL,          -- '단순이동평균', 'RSI 지표'
    display_name_en TEXT,                   -- 'Simple Moving Average', 'RSI Indicator'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum', 'volatility', 'volume', 'price'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable', etc.
    is_active BOOLEAN DEFAULT 1,            -- 활성화 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                       -- 지표 설명
    source TEXT DEFAULT 'built-in'          -- 'built-in', 'tradingview', 'custom'
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_purpose_category ON trading_variables(purpose_category);
CREATE INDEX IF NOT EXISTS idx_chart_category ON trading_variables(chart_category);
CREATE INDEX IF NOT EXISTS idx_comparison_group ON trading_variables(comparison_group);
CREATE INDEX IF NOT EXISTS idx_is_active ON trading_variables(is_active);

-- 지표별 파라미터 정의 테이블
CREATE TABLE IF NOT EXISTS variable_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,              -- 'RSI', 'MACD' 등 지표 ID
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
    FOREIGN KEY (variable_id) REFERENCES trading_variables(variable_id) ON DELETE CASCADE
);

-- 파라미터 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_variable_parameters_variable_id ON variable_parameters(variable_id);
CREATE INDEX IF NOT EXISTS idx_variable_parameters_display_order ON variable_parameters(variable_id, display_order);

-- 현재 활성 지표들 데이터 입력 (30개) - variable_id 표준화 적용
INSERT OR REPLACE INTO trading_variables VALUES 
-- 📈 추세 지표 (Trend Indicators) - 8개
('SMA', '단순이동평균', 'Simple Moving Average', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간의 가격을 산술 평균한 값', 'built-in'),
('EMA', '지수이동평균', 'Exponential Moving Average', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '최근 가격에 더 큰 가중치를 부여한 이동평균', 'built-in'),
('WMA', '가중이동평균', 'Weighted Moving Average', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '기간 내 가격에 선형적으로 가중치를 부여한 이동평균', 'built-in'),
('BOLLINGER_BANDS', '볼린저 밴드', 'Bollinger Bands', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '이동평균선과 표준편차를 이용한 변동성 채널', 'built-in'),
('ICHIMOKU', '일목균형표', 'Ichimoku Cloud', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '전환선, 기준선, 구름대 등을 통한 종합 분석 지표', 'built-in'),
('PARABOLIC_SAR', '파라볼릭 SAR', 'Parabolic SAR', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '추세의 전환 가능 지점을 점으로 나타내는 추세 추종 지표', 'built-in'),
('ADX', '평균방향성지수', 'Average Directional Index', 'trend', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '추세의 강도를 측정하는 지표 (방향은 알려주지 않음)', 'built-in'),
('AROON', '아룬 지표', 'Aroon Indicator', 'trend', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '최고가/최저가 도달 후 경과 시간으로 추세 시작을 파악', 'built-in'),

-- ⚡ 모멘텀 지표 (Momentum Indicators) - 8개
('RSI', 'RSI 지표', 'Relative Strength Index', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '상승압력과 하락압력 간의 상대적 강도를 나타내는 모멘텀 지표', 'built-in'),
('STOCHASTIC_OSCILLATOR', '스토캐스틱', 'Stochastic Oscillator', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간 주가 변동 범위에서 현재 주가의 위치를 백분율로 표시', 'built-in'),
('STOCHASTIC_RSI', '스토캐스틱 RSI', 'Stochastic RSI', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'RSI 값에 스토캐스틱 공식을 적용하여 더 민감한 신호 생성', 'built-in'),
('WILLIAMS_R', '윌리엄스 %R', 'Williams %R', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '스토캐스틱과 유사하게 과매수/과매도 수준을 측정', 'built-in'),
('CCI', '상품채널지수', 'Commodity Channel Index', 'momentum', 'subplot', 'centered_oscillator', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '현재 가격이 평균 가격과 얼마나 떨어져 있는지를 측정', 'built-in'),
('MACD', 'MACD 지표', 'Moving Average Convergence Divergence', 'momentum', 'subplot', 'signal_conditional', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '두 이동평균선 사이의 관계를 보여주는 모멘텀 및 추세 지표', 'built-in'),
('ROC', '가격변동률', 'Rate of Change', 'momentum', 'subplot', 'centered_oscillator', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '현재 가격과 n일 전 가격의 변화율을 측정', 'built-in'),
('MFI', '자금흐름지수', 'Money Flow Index', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '거래량을 고려한 RSI로, 자금의 유입 및 유출 강도를 나타냄', 'built-in'),

-- 🔥 변동성 지표 (Volatility Indicators) - 3개
('ATR', '평균실제범위', 'Average True Range', 'volatility', 'subplot', 'volatility_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '주가의 변동성을 측정하는 지표. 절대적인 가격 변동폭을 나타냄', 'built-in'),
('BOLLINGER_BANDS_WIDTH', '볼린저 밴드 폭', 'Bollinger Bands Width', 'volatility', 'subplot', 'volatility_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '볼린저 밴드의 상하단 폭으로 변동성의 축소/확대를 파악', 'built-in'),
('STANDARD_DEVIATION', '표준편차', 'Standard Deviation', 'volatility', 'subplot', 'volatility_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '가격이 평균에서 얼마나 떨어져 있는지를 측정하는 통계적 변동성 지표', 'built-in'),

-- 📦 거래량 지표 (Volume Indicators) - 4개
('VOLUME', '거래량', 'Volume', 'volume', 'subplot', 'volume_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간 동안 거래된 주식의 총 수량', 'built-in'),
('OBV', '온밸런스 볼륨', 'On-Balance Volume', 'volume', 'subplot', 'volume_flow', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '상승일 거래량은 더하고 하락일 거래량은 빼서 거래량 흐름을 표시', 'built-in'),
('VOLUME_PROFILE', '거래량 프로파일', 'Volume Profile', 'volume', 'overlay', 'volume_distribution', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '가격대별 거래량을 히스토그램으로 표시', 'built-in'),
('VWAP', '거래량가중평균가격', 'Volume Weighted Average Price', 'volume', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '당일 거래량을 가중치로 부여한 평균 가격', 'built-in'),

-- 💰 가격 데이터 (Price Data) - 4개
('CURRENT_PRICE', '현재가', 'Current Price', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '현재 시점의 가격', 'built-in'),
('HIGH_PRICE', '고가', 'High Price', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간의 최고가', 'built-in'),
('LOW_PRICE', '저가', 'Low Price', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간의 최저가', 'built-in'),
('OPEN_PRICE', '시가', 'Open Price', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '특정 기간의 시작 가격', 'built-in'),

-- 🏆 인기 커뮤니티 지표 (Popular Community Indicators) - 3개
('SQUEEZE_MOMENTUM', '스퀴즈 모멘텀', 'Squeeze Momentum Indicator', 'momentum', 'subplot', 'centered_oscillator', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '볼린저 밴드와 켈트너 채널을 이용해 변동성 압축 후 폭발 방향을 예측', 'tradingview'),
('SUPERTREND', '슈퍼트렌드', 'Supertrend', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'ATR을 기반으로 추세의 방향과 변동성을 시각적으로 표시', 'tradingview'),
('PIVOT_POINTS', '피봇 포인트', 'Pivot Points', 'support_resistance', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, '전일/전주/전월의 고가, 저가, 종가를 이용해 지지선과 저항선을 계산', 'built-in');

-- 비교 그룹 정의를 위한 메타데이터 테이블 (추후 확장용)
CREATE TABLE IF NOT EXISTS comparison_groups (
    group_id TEXT PRIMARY KEY,
    group_name_ko TEXT NOT NULL,
    group_name_en TEXT NOT NULL,
    description TEXT,
    can_compare_with TEXT,  -- JSON 형태로 호환 가능한 그룹들 저장
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 비교 그룹 메타데이터 삽입
INSERT OR REPLACE INTO comparison_groups VALUES
('price_comparable', '가격 비교 가능', 'Price Comparable', '가격 기반 지표들끼리 비교 가능', '["price_comparable"]', CURRENT_TIMESTAMP),
('percentage_comparable', '퍼센트 비교 가능', 'Percentage Comparable', '0-100% 범위의 지표들끼리 비교 가능', '["percentage_comparable"]', CURRENT_TIMESTAMP),
('centered_oscillator', '중심선 오실레이터', 'Centered Oscillator', '0을 중심으로 한 오실레이터들끼리 비교 가능', '["centered_oscillator"]', CURRENT_TIMESTAMP),
('signal_conditional', '신호 조건부', 'Signal Conditional', '특별한 신호 조건에서만 비교 가능', '["signal_conditional"]', CURRENT_TIMESTAMP),
('volatility_comparable', '변동성 비교 가능', 'Volatility Comparable', '변동성 지표들끼리 비교 가능', '["volatility_comparable"]', CURRENT_TIMESTAMP),
('volume_comparable', '거래량 비교 가능', 'Volume Comparable', '거래량 기반 지표들끼리 비교 가능', '["volume_comparable"]', CURRENT_TIMESTAMP),
('volume_flow', '거래량 흐름', 'Volume Flow', '거래량 흐름 지표들끼리 비교 가능', '["volume_flow"]', CURRENT_TIMESTAMP),
('volume_distribution', '거래량 분포', 'Volume Distribution', '거래량 분포 지표들끼리 비교 가능', '["volume_distribution"]', CURRENT_TIMESTAMP);

-- 스키마 버전 관리
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR REPLACE INTO schema_version VALUES 
('1.2.0', CURRENT_TIMESTAMP, '표준화 및 일관성 개선 - variable_id 명명 규칙 통일, source 파라미터 추가');

-- 주요 지표들의 파라미터 정의 추가 (표준화된 variable_id 적용)
INSERT OR REPLACE INTO variable_parameters VALUES
-- SMA 파라미터
(1, 'SMA', 'period', 'integer', '20', '1', '200', NULL, 1, '기간', 'Period', '이동평균 계산 기간', 1, CURRENT_TIMESTAMP),
(2, 'SMA', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 2, CURRENT_TIMESTAMP),

-- EMA 파라미터
(3, 'EMA', 'period', 'integer', '20', '1', '200', NULL, 1, '기간', 'Period', '지수이동평균 계산 기간', 1, CURRENT_TIMESTAMP),
(4, 'EMA', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 2, CURRENT_TIMESTAMP),

-- WMA 파라미터 (source 파라미터 추가)
(5, 'WMA', 'period', 'integer', '20', '1', '200', NULL, 1, '기간', 'Period', '가중이동평균 계산 기간', 1, CURRENT_TIMESTAMP),
(6, 'WMA', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 2, CURRENT_TIMESTAMP),

-- RSI 파라미터
(7, 'RSI', 'period', 'integer', '14', '2', '100', NULL, 1, '기간', 'Period', 'RSI 계산 기간', 1, CURRENT_TIMESTAMP),
(8, 'RSI', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 2, CURRENT_TIMESTAMP),

-- STOCHASTIC_OSCILLATOR 파라미터 (기존 STOCH에서 이름 변경)
(9, 'STOCHASTIC_OSCILLATOR', 'k_period', 'integer', '14', '1', '100', NULL, 1, '%K 기간', '%K Period', '%K 라인 계산 기간', 1, CURRENT_TIMESTAMP),
(10, 'STOCHASTIC_OSCILLATOR', 'd_period', 'integer', '3', '1', '50', NULL, 1, '%D 기간', '%D Period', '%D 라인 계산 기간', 2, CURRENT_TIMESTAMP),
(11, 'STOCHASTIC_OSCILLATOR', 'smooth', 'integer', '3', '1', '10', NULL, 1, '스무딩', 'Smooth', '스토캐스틱 스무딩 기간', 3, CURRENT_TIMESTAMP),

-- STOCHASTIC_RSI 파라미터 (기존 STOCH_RSI에서 이름 변경)
(12, 'STOCHASTIC_RSI', 'rsi_period', 'integer', '14', '2', '100', NULL, 1, 'RSI 기간', 'RSI Period', 'RSI 계산 기간', 1, CURRENT_TIMESTAMP),
(13, 'STOCHASTIC_RSI', 'stoch_period', 'integer', '14', '1', '100', NULL, 1, '스토캐스틱 기간', 'Stochastic Period', '스토캐스틱 계산 기간', 2, CURRENT_TIMESTAMP),
(14, 'STOCHASTIC_RSI', 'k_period', 'integer', '3', '1', '50', NULL, 1, '%K 기간', '%K Period', '%K 스무딩 기간', 3, CURRENT_TIMESTAMP),
(15, 'STOCHASTIC_RSI', 'd_period', 'integer', '3', '1', '50', NULL, 1, '%D 기간', '%D Period', '%D 스무딩 기간', 4, CURRENT_TIMESTAMP),

-- WILLIAMS_R 파라미터 (source 파라미터 추가)
(16, 'WILLIAMS_R', 'period', 'integer', '14', '1', '100', NULL, 1, '기간', 'Period', 'Williams %R 계산 기간', 1, CURRENT_TIMESTAMP),
(17, 'WILLIAMS_R', 'source', 'enum', 'hlc3', NULL, NULL, '["high", "low", "close", "hlc3"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 2, CURRENT_TIMESTAMP),

-- MACD 파라미터
(18, 'MACD', 'fast_period', 'integer', '12', '1', '50', NULL, 1, '빠른 기간', 'Fast Period', '빠른 EMA 기간', 1, CURRENT_TIMESTAMP),
(19, 'MACD', 'slow_period', 'integer', '26', '1', '100', NULL, 1, '느린 기간', 'Slow Period', '느린 EMA 기간', 2, CURRENT_TIMESTAMP),
(20, 'MACD', 'signal_period', 'integer', '9', '1', '50', NULL, 1, '시그널 기간', 'Signal Period', '시그널 라인 기간', 3, CURRENT_TIMESTAMP),
(21, 'MACD', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 4, CURRENT_TIMESTAMP),

-- ROC 파라미터 (source 파라미터 추가)
(22, 'ROC', 'period', 'integer', '12', '1', '100', NULL, 1, '기간', 'Period', 'ROC 계산 기간', 1, CURRENT_TIMESTAMP),
(23, 'ROC', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 2, CURRENT_TIMESTAMP),

-- MFI 파라미터 (거래량을 고려하므로 source 파라미터는 제외)
(24, 'MFI', 'period', 'integer', '14', '1', '100', NULL, 1, '기간', 'Period', 'MFI 계산 기간', 1, CURRENT_TIMESTAMP),

-- BOLLINGER_BANDS 파라미터
(25, 'BOLLINGER_BANDS', 'period', 'integer', '20', '2', '100', NULL, 1, '기간', 'Period', '이동평균 기간', 1, CURRENT_TIMESTAMP),
(26, 'BOLLINGER_BANDS', 'multiplier', 'float', '2.0', '0.1', '5.0', NULL, 1, '표준편차 배수', 'Std Dev Multiplier', '표준편차 곱셈 계수', 2, CURRENT_TIMESTAMP),
(27, 'BOLLINGER_BANDS', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 3, CURRENT_TIMESTAMP),

-- BOLLINGER_BANDS_WIDTH 파라미터 (기존 BOLLINGER_WIDTH에서 이름 변경)
(28, 'BOLLINGER_BANDS_WIDTH', 'period', 'integer', '20', '2', '100', NULL, 1, '기간', 'Period', '볼린저 밴드 기간', 1, CURRENT_TIMESTAMP),
(29, 'BOLLINGER_BANDS_WIDTH', 'multiplier', 'float', '2.0', '0.1', '5.0', NULL, 1, '표준편차 배수', 'Std Dev Multiplier', '표준편차 곱셈 계수', 2, CURRENT_TIMESTAMP),
(30, 'BOLLINGER_BANDS_WIDTH', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 3, CURRENT_TIMESTAMP),

-- STANDARD_DEVIATION 파라미터 (source 파라미터 추가)
(31, 'STANDARD_DEVIATION', 'period', 'integer', '20', '1', '100', NULL, 1, '기간', 'Period', '표준편차 계산 기간', 1, CURRENT_TIMESTAMP),
(32, 'STANDARD_DEVIATION', 'source', 'enum', 'close', NULL, NULL, '["open", "high", "low", "close", "hl2", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 2, CURRENT_TIMESTAMP),

-- ATR 파라미터
(33, 'ATR', 'period', 'integer', '14', '1', '100', NULL, 1, '기간', 'Period', 'ATR 계산 기간', 1, CURRENT_TIMESTAMP),

-- ADX 파라미터
(34, 'ADX', 'period', 'integer', '14', '1', '100', NULL, 1, '기간', 'Period', 'ADX 계산 기간', 1, CURRENT_TIMESTAMP),

-- AROON 파라미터
(35, 'AROON', 'period', 'integer', '14', '1', '100', NULL, 1, '기간', 'Period', 'AROON 계산 기간', 1, CURRENT_TIMESTAMP),

-- CCI 파라미터 (source 파라미터 추가)
(36, 'CCI', 'period', 'integer', '20', '1', '100', NULL, 1, '기간', 'Period', 'CCI 계산 기간', 1, CURRENT_TIMESTAMP),
(37, 'CCI', 'factor', 'float', '0.015', '0.001', '1.0', NULL, 1, '상수', 'Factor', 'CCI 계산 상수', 2, CURRENT_TIMESTAMP),
(38, 'CCI', 'source', 'enum', 'hlc3', NULL, NULL, '["high", "low", "close", "hlc3", "ohlc4"]', 1, '데이터 소스', 'Data Source', '계산에 사용할 가격 데이터', 3, CURRENT_TIMESTAMP),

-- PARABOLIC_SAR 파라미터
(39, 'PARABOLIC_SAR', 'start', 'float', '0.02', '0.001', '0.2', NULL, 1, '시작 가속도', 'Start Acceleration', '초기 가속도 팩터', 1, CURRENT_TIMESTAMP),
(40, 'PARABOLIC_SAR', 'increment', 'float', '0.02', '0.001', '0.2', NULL, 1, '증가값', 'Increment', '가속도 증가값', 2, CURRENT_TIMESTAMP),
(41, 'PARABOLIC_SAR', 'maximum', 'float', '0.2', '0.1', '1.0', NULL, 1, '최대값', 'Maximum', '최대 가속도 팩터', 3, CURRENT_TIMESTAMP),

-- ICHIMOKU 파라미터
(42, 'ICHIMOKU', 'tenkan_period', 'integer', '9', '1', '50', NULL, 1, '전환선 기간', 'Tenkan Period', '전환선 계산 기간', 1, CURRENT_TIMESTAMP),
(43, 'ICHIMOKU', 'kijun_period', 'integer', '26', '1', '100', NULL, 1, '기준선 기간', 'Kijun Period', '기준선 계산 기간', 2, CURRENT_TIMESTAMP),
(44, 'ICHIMOKU', 'senkou_b_period', 'integer', '52', '1', '200', NULL, 1, '선행스팬B 기간', 'Senkou B Period', '선행스팬B 계산 기간', 3, CURRENT_TIMESTAMP),
(45, 'ICHIMOKU', 'displacement', 'integer', '26', '1', '100', NULL, 1, '후행스팬 이동', 'Displacement', '후행스팬 이동 기간', 4, CURRENT_TIMESTAMP),

-- VWAP 파라미터 (거래량가중평균가격 - 기간 설정 가능)
(46, 'VWAP', 'session_type', 'enum', 'daily', NULL, NULL, '["daily", "weekly", "monthly", "custom"]', 1, '세션 타입', 'Session Type', 'VWAP 계산 세션 유형', 1, CURRENT_TIMESTAMP),

-- OBV 파라미터 (기본적으로는 파라미터 없음, 하지만 스무딩 옵션 추가 가능)
(47, 'OBV', 'smoothing', 'boolean', 'false', NULL, NULL, NULL, 0, '스무딩 적용', 'Apply Smoothing', 'OBV에 이동평균 스무딩 적용 여부', 1, CURRENT_TIMESTAMP),
(48, 'OBV', 'smoothing_period', 'integer', '10', '1', '50', NULL, 0, '스무딩 기간', 'Smoothing Period', '스무딩에 사용할 이동평균 기간', 2, CURRENT_TIMESTAMP),

-- SUPERTREND 파라미터
(49, 'SUPERTREND', 'period', 'integer', '10', '1', '100', NULL, 1, '기간', 'Period', 'ATR 계산 기간', 1, CURRENT_TIMESTAMP),
(50, 'SUPERTREND', 'multiplier', 'float', '3.0', '0.1', '10.0', NULL, 1, '배수', 'Multiplier', 'ATR 배수', 2, CURRENT_TIMESTAMP),

-- SQUEEZE_MOMENTUM 파라미터
(51, 'SQUEEZE_MOMENTUM', 'bb_period', 'integer', '20', '1', '100', NULL, 1, '볼린저 밴드 기간', 'BB Period', '볼린저 밴드 계산 기간', 1, CURRENT_TIMESTAMP),
(52, 'SQUEEZE_MOMENTUM', 'bb_multiplier', 'float', '2.0', '0.1', '5.0', NULL, 1, '볼린저 밴드 배수', 'BB Multiplier', '볼린저 밴드 표준편차 배수', 2, CURRENT_TIMESTAMP),
(53, 'SQUEEZE_MOMENTUM', 'kc_period', 'integer', '20', '1', '100', NULL, 1, '켈트너 채널 기간', 'KC Period', '켈트너 채널 계산 기간', 3, CURRENT_TIMESTAMP),
(54, 'SQUEEZE_MOMENTUM', 'kc_multiplier', 'float', '1.5', '0.1', '5.0', NULL, 1, '켈트너 채널 배수', 'KC Multiplier', '켈트너 채널 ATR 배수', 4, CURRENT_TIMESTAMP),

-- PIVOT_POINTS 파라미터
(55, 'PIVOT_POINTS', 'calculation_type', 'enum', 'traditional', NULL, NULL, '["traditional", "fibonacci", "woodie", "camarilla", "demark"]', 1, '계산 방식', 'Calculation Type', '피봇 포인트 계산 방식', 1, CURRENT_TIMESTAMP),
(56, 'PIVOT_POINTS', 'timeframe', 'enum', 'daily', NULL, NULL, '["daily", "weekly", "monthly"]', 1, '시간틀', 'Timeframe', '피봇 포인트 계산 시간틀', 2, CURRENT_TIMESTAMP);

-- 성공적인 스키마 생성 확인
SELECT 'Trading Variables Schema v1.2.0 successfully created!' as status,
       COUNT(*) as total_indicators,
       (SELECT COUNT(*) FROM variable_parameters) as total_parameters
FROM trading_variables 
WHERE is_active = 1;
