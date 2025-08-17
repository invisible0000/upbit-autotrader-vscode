-- ========================================
-- UPBIT AUTO TRADING SETTINGS DATABASE
-- ENHANCED Schema with Multilingual Enum Support
-- Generated: 2025-08-17
-- Version: v3.1 (Added enum_values_ko support)
-- ========================================

-- ========================================
-- CORE CONFIGURATION TABLES
-- ========================================

-- Table: cfg_app_settings
-- Application-level configuration settings
CREATE TABLE cfg_app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: cfg_system_settings
-- System-level configuration settings
CREATE TABLE cfg_system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: secure_keys
-- Encrypted API keys and sensitive data storage
CREATE TABLE secure_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_type TEXT NOT NULL UNIQUE,
    key_value BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_secure_keys_type ON secure_keys(key_type);
CREATE INDEX idx_secure_keys_created_at ON secure_keys(created_at);

-- ========================================
-- TRADING VARIABLES SYSTEM v3.1
-- ========================================

-- Table: tv_schema_version
-- Database schema version tracking
CREATE TABLE tv_schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Table: tv_trading_variables
-- Core trading variables registry (SMA, RSI, MACD, etc.)
CREATE TABLE tv_trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,          -- '단순이동평균', 'RSI 지표'
    display_name_en TEXT,                   -- 'Simple Moving Average', 'RSI Indicator'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum', 'volatility', 'volume', 'price', 'capital', 'state', 'meta'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable', etc.
    is_active BOOLEAN DEFAULT 1,            -- 활성화 여부
    description TEXT,                       -- 변수 설명
    source TEXT DEFAULT 'built-in',         -- 'built-in', 'tradingview', 'custom'
    parameter_required BOOLEAN DEFAULT 0,   -- 파라미터 필요 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tv_purpose_category ON tv_trading_variables(purpose_category);
CREATE INDEX idx_tv_chart_category ON tv_trading_variables(chart_category);
CREATE INDEX idx_tv_comparison_group ON tv_trading_variables(comparison_group);
CREATE INDEX idx_tv_is_active ON tv_trading_variables(is_active);

-- Table: tv_variable_parameters (ENHANCED with enum_values_ko)
-- Trading variable parameters with multilingual enum support
CREATE TABLE tv_variable_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,              -- 'RSI', 'SMA' 변수ID
    parameter_name TEXT NOT NULL,           -- 'period', 'source', 'multiplier'
    parameter_type TEXT NOT NULL,           -- 'integer', 'decimal', 'string', 'boolean', 'enum'
    default_value TEXT,                     -- 기본값(문자열 저장)
    min_value TEXT,                         -- 최소값(문자열 저장)
    max_value TEXT,                         -- 최대값(문자열 저장)
    enum_values TEXT,                       -- enum 영문 값들의 JSON 배열 (["upper", "middle", "lower"])
    enum_values_ko TEXT,                    -- enum 한글 값들의 JSON 배열 (["상단", "중앙선", "하단"]) -- ✨ NEW COLUMN
    is_required BOOLEAN DEFAULT 1,          -- 필수 파라미터 여부
    display_name_ko TEXT NOT NULL,          -- '기간', '데이터소스'
    display_name_en TEXT,                   -- 'Period', 'Data Source'
    description TEXT,                       -- 파라미터 설명
    display_order INTEGER DEFAULT 0,        -- UI 표시 순서
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id) ON DELETE CASCADE
);

CREATE INDEX idx_tv_variable_parameters_variable_id ON tv_variable_parameters(variable_id);
CREATE INDEX idx_tv_variable_parameters_display_order ON tv_variable_parameters(variable_id, display_order);
CREATE INDEX idx_tv_parameters_variable ON tv_variable_parameters(variable_id, parameter_name);

-- ========================================
-- HELP & DOCUMENTATION SYSTEM
-- ========================================

-- Table: tv_help_texts
-- Short help texts and tooltips for parameters
CREATE TABLE tv_help_texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,
    parameter_name TEXT,
    help_text_ko TEXT NOT NULL,
    help_text_en TEXT,
    tooltip_ko TEXT,
    tooltip_en TEXT,
    language TEXT DEFAULT 'ko',
    context_type TEXT DEFAULT 'tooltip',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
);

CREATE INDEX idx_tv_help_texts_lookup ON tv_help_texts(variable_id, parameter_name);

-- Table: tv_placeholder_texts
-- Input field placeholders and examples
CREATE TABLE tv_placeholder_texts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,
    parameter_name TEXT,
    placeholder_text_ko TEXT NOT NULL,
    placeholder_text_en TEXT,
    example_value TEXT,
    validation_pattern TEXT,
    input_type TEXT DEFAULT 'text',
    language TEXT DEFAULT 'ko',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
);

CREATE INDEX idx_tv_placeholder_lookup ON tv_placeholder_texts(variable_id, parameter_name);

-- Table: tv_variable_help_documents
-- Comprehensive help documentation (concept/usage/advanced guides)
CREATE TABLE tv_variable_help_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,
    help_category TEXT NOT NULL,            -- 'concept', 'usage', 'advanced'
    content_type TEXT NOT NULL,
    title_ko TEXT,
    title_en TEXT,
    content_ko TEXT NOT NULL,
    content_en TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
);

CREATE INDEX idx_help_docs_variable_category ON tv_variable_help_documents(variable_id, help_category);

-- ========================================
-- SCHEMA VERSION INITIALIZATION
-- ========================================

-- Record current schema version
INSERT OR REPLACE INTO tv_schema_version (version, description)
VALUES ('3.1', 'Added enum_values_ko column for multilingual enum support');

-- ========================================
-- MIGRATION SCRIPT FOR EXISTING DATABASES
-- ========================================

-- Step 1: Add enum_values_ko column (if not exists)
-- For existing databases, run this SQL:

ALTER TABLE tv_variable_parameters
ADD COLUMN enum_values_ko TEXT;

-- Step 2: Update schema version
INSERT OR REPLACE INTO tv_schema_version (version, description)
VALUES ('3.1', 'Added enum_values_ko column for multilingual enum support');

-- Step 3: Populate existing enum mappings
-- MACD Type mappings
UPDATE tv_variable_parameters
SET enum_values_ko = '["MACD선", "시그널선", "히스토그램"]'
WHERE variable_id = 'MACD' AND parameter_name = 'macd_type';

-- Bollinger Band mappings
UPDATE tv_variable_parameters
SET enum_values_ko = '["상단", "중앙선", "하단"]'
WHERE variable_id = 'BOLLINGER_BAND' AND parameter_name = 'band_position';

-- Timeframe mappings (for all timeframe parameters)
UPDATE tv_variable_parameters
SET enum_values_ko = '["포지션 설정 따름", "1분", "3분", "5분", "10분", "15분", "30분", "1시간", "4시간", "1일", "1주", "1월"]'
WHERE parameter_name = 'timeframe' AND parameter_type = 'enum';

-- META Calculation Method mappings
UPDATE tv_variable_parameters
SET enum_values_ko = '["평단가 기준 %p", "진입가 기준 %p", "정적 차이값", "극값 비율 %"]'
WHERE parameter_name = 'calculation_method' AND parameter_type = 'enum';

-- META Trail Direction mappings
UPDATE tv_variable_parameters
SET enum_values_ko = '["상승 (불타기)", "하락 (물타기)"]'
WHERE variable_id = 'META_PYRAMID_TARGET' AND parameter_name = 'trail_direction';

UPDATE tv_variable_parameters
SET enum_values_ko = '["상승 추적", "하락 추적"]'
WHERE variable_id = 'META_TRAILING_STOP' AND parameter_name = 'trail_direction';
