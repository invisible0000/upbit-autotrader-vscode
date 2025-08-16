-- Upbit Auto Trading - Settings Database Schema
-- =================================================
-- DB: settings.sqlite3
-- 용도: 프로그램 전반의 기본 기능 동작을 위한 설정 및 메타데이터
-- 생성일: 2025-08-01
-- 관리 대상: 시스템 설정, 트레이딩 변수 정의, UI 설정, 백업 정보

PRAGMA foreign_keys = ON;

-- =====================================
-- 시스템 설정 테이블들
-- =====================================

-- API 키 보안 시스템
CREATE TABLE IF NOT EXISTS secure_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_type TEXT NOT NULL UNIQUE,          -- 'encryption', 'api_access', 'api_secret' 등
    key_value BLOB NOT NULL,                -- 암호화된 키 데이터 (BLOB 타입)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 앱 전반 설정
CREATE TABLE cfg_app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 시스템 설정
CREATE TABLE cfg_system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 백업 정보
CREATE TABLE sys_backup_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_name TEXT NOT NULL,
    backup_path TEXT NOT NULL,
    backup_size INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- =====================================
-- 트레이딩 변수 시스템 (core tables)
-- =====================================

-- 트레이딩 변수 메인 정의
CREATE TABLE tv_trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,          -- '단순이동평균', 'RSI 지표'
    display_name_en TEXT,                   -- 'Simple Moving Average', 'RSI Indicator'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum', 'volatility', 'volume', 'price'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable', etc.
    parameter_required BOOLEAN DEFAULT 0,   -- 파라미터 필요 여부 (0: 불필요, 1: 필요)
    is_active BOOLEAN DEFAULT 1,            -- 활성화 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                       -- 지표 설명
    source TEXT DEFAULT 'built-in'          -- 'built-in', 'tradingview', 'custom'
);

-- 변수별 파라미터 정의
CREATE TABLE tv_variable_parameters (
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

-- 도움말 텍스트
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

-- 플레이스홀더 텍스트
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

-- 지표 카테고리
CREATE TABLE tv_indicator_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL,
    display_name_ko TEXT NOT NULL,
    display_name_en TEXT,
    description TEXT,
    chart_position TEXT DEFAULT 'subplot',
    color_scheme TEXT DEFAULT 'default',
    color_theme TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 파라미터 타입 정의
CREATE TABLE tv_parameter_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT UNIQUE NOT NULL,
    description TEXT,
    validation_pattern TEXT,
    validation_example TEXT,
    ui_component TEXT DEFAULT 'input',
    default_constraints TEXT,               -- JSON 형태의 제약 조건
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 비교 그룹 정의
CREATE TABLE tv_comparison_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT UNIQUE NOT NULL,
    display_name_ko TEXT NOT NULL,
    display_name_en TEXT,
    description TEXT,
    compatibility_rules TEXT,              -- JSON 형태의 호환성 규칙
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 지표 라이브러리
CREATE TABLE tv_indicator_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id TEXT UNIQUE NOT NULL,
    display_name_ko TEXT NOT NULL,
    display_name_en TEXT,
    category TEXT NOT NULL,
    calculation_method TEXT,
    calculation_note TEXT,
    description TEXT,
    usage_examples TEXT,                   -- JSON 형태의 사용 예시
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 스키마 버전 관리
CREATE TABLE tv_schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- 워크플로우 가이드
CREATE TABLE tv_workflow_guides (
    guide_id TEXT PRIMARY KEY,
    guide_title TEXT NOT NULL,
    guide_content TEXT NOT NULL,
    step_order INTEGER DEFAULT 0,
    target_audience TEXT DEFAULT 'general',
    difficulty_level TEXT DEFAULT 'basic',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 차트 시스템 설정
-- =====================================

-- 차트 레이아웃 템플릿
CREATE TABLE cfg_chart_layout_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL UNIQUE,
    description TEXT,
    main_chart_height_ratio REAL DEFAULT 0.6,
    subplot_configurations TEXT NOT NULL,  -- JSON
    color_palette TEXT,                    -- JSON
    is_default INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 차트 변수 정의
CREATE TABLE tv_chart_variables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL UNIQUE,
    variable_name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    display_type TEXT NOT NULL,
    scale_min REAL,
    scale_max REAL,
    unit TEXT DEFAULT '',
    default_color TEXT DEFAULT '#007bff',
    subplot_height_ratio REAL DEFAULT 0.3,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 변수 호환성 규칙
CREATE TABLE tv_variable_compatibility_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_variable_id TEXT NOT NULL,
    compatible_category TEXT NOT NULL,
    compatibility_reason TEXT,
    min_value_constraint REAL,
    max_value_constraint REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (base_variable_id) REFERENCES tv_chart_variables (variable_id)
);

-- 변수 사용 로그
CREATE TABLE tv_variable_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,
    condition_id INTEGER,
    usage_context TEXT NOT NULL,
    chart_display_info TEXT,              -- JSON
    render_time_ms INTEGER,
    user_feedback TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_chart_variables (variable_id)
);

-- =====================================
-- 조건 및 전략 메타데이터 (구조만)
-- =====================================

-- 트레이딩 조건 메타구조
CREATE TABLE trading_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition_name TEXT NOT NULL,
    condition_type TEXT NOT NULL,          -- 'entry', 'exit', 'management'
    description TEXT,
    variable_mappings TEXT,               -- JSON: 사용되는 변수들의 매핑
    is_template BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- 인덱스 생성
-- =====================================

-- API 키 보안 관련 인덱스
CREATE UNIQUE INDEX IF NOT EXISTS idx_secure_keys_type ON secure_keys(key_type);
CREATE INDEX IF NOT EXISTS idx_secure_keys_created_at ON secure_keys(created_at);

-- 트레이딩 변수 관련 인덱스
CREATE INDEX idx_tv_chart_category ON tv_trading_variables(chart_category);
CREATE INDEX idx_tv_comparison_group ON tv_trading_variables(comparison_group);
CREATE INDEX idx_tv_is_active ON tv_trading_variables(is_active);
CREATE INDEX idx_tv_purpose_category ON tv_trading_variables(purpose_category);
CREATE INDEX idx_tv_variable_parameters_variable_id ON tv_variable_parameters(variable_id);
CREATE INDEX idx_tv_variable_parameters_display_order ON tv_variable_parameters(variable_id, display_order);

-- 차트 시스템 관련 인덱스
CREATE INDEX idx_tv_chart_variables_category ON tv_chart_variables(category);
CREATE INDEX idx_tv_chart_variables_is_active ON tv_chart_variables(is_active);
CREATE INDEX idx_tv_variable_usage_logs_variable_id ON tv_variable_usage_logs(variable_id);
CREATE INDEX idx_tv_variable_usage_logs_created_at ON tv_variable_usage_logs(created_at);

-- 조건 관련 인덱스
CREATE INDEX idx_trading_conditions_type ON trading_conditions(condition_type);
CREATE INDEX idx_trading_conditions_is_active ON trading_conditions(is_active);

-- =====================================
-- 기본 데이터 삽입
-- =====================================

-- 스키마 버전 정보
INSERT INTO tv_schema_version (version, description)
VALUES ('1.0.0', 'Initial settings database schema');

-- 기본 앱 설정
INSERT OR IGNORE INTO cfg_app_settings (key, value) VALUES
('app_version', '1.0.0'),
('default_language', 'ko'),
('theme', 'dark'),
('auto_backup_enabled', 'true'),
('backup_retention_days', '30');

-- 기본 시스템 설정
INSERT OR IGNORE INTO cfg_system_settings (setting_name, setting_value) VALUES
('max_concurrent_strategies', '10'),
('default_timeframe', '1d'),
('api_timeout_seconds', '30'),
('log_level', 'INFO');

-- =====================================
-- 뷰 생성 (필요시)
-- =====================================

-- 활성 트레이딩 변수 뷰
CREATE VIEW IF NOT EXISTS active_trading_variables AS
SELECT
    tv.variable_id,
    tv.display_name_ko,
    tv.display_name_en,
    tv.purpose_category,
    tv.chart_category,
    tv.comparison_group,
    tv.description,
    COUNT(tvp.parameter_id) as parameter_count
FROM tv_trading_variables tv
LEFT JOIN tv_variable_parameters tvp ON tv.variable_id = tvp.variable_id
WHERE tv.is_active = 1
GROUP BY tv.variable_id;

-- 완전한 변수 정보 뷰 (파라미터 포함)
CREATE VIEW IF NOT EXISTS complete_variable_info AS
SELECT
    tv.variable_id,
    tv.display_name_ko as variable_name_ko,
    tv.display_name_en as variable_name_en,
    tv.purpose_category,
    tv.chart_category,
    tv.comparison_group,
    tvp.parameter_id,
    tvp.parameter_name,
    tvp.parameter_type,
    tvp.default_value,
    tvp.display_name_ko as param_name_ko,
    tvp.display_name_en as param_name_en,
    tvp.is_required,
    tvp.display_order
FROM tv_trading_variables tv
LEFT JOIN tv_variable_parameters tvp ON tv.variable_id = tvp.variable_id
WHERE tv.is_active = 1
ORDER BY tv.variable_id, tvp.display_order;
