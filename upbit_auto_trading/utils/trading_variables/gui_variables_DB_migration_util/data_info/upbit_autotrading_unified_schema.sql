-- Upbit Auto Trading Unified Schema
-- 완전한 통합 스키마 (settings DB에서 추출)
-- 생성일: 2025-08-14 22:21:34
-- 추출 도구: Super DB Schema Extractor
PRAGMA foreign_keys = ON;

-- Table: cfg_app_settings
CREATE TABLE cfg_app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: cfg_chart_layout_templates
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

-- Table: cfg_system_settings
CREATE TABLE cfg_system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: component_strategy
CREATE TABLE component_strategy (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    triggers TEXT NOT NULL,
                    conditions TEXT,
                    actions TEXT NOT NULL,
                    tags TEXT,
                    category TEXT DEFAULT 'user_created',
                    difficulty TEXT DEFAULT 'intermediate',
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    is_template BOOLEAN NOT NULL DEFAULT 0,
                    performance_metrics TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

-- Table: secure_keys
CREATE TABLE secure_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_type TEXT NOT NULL UNIQUE,
                    key_value BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

-- Table: sqlite_stat1
CREATE TABLE sqlite_stat1(tbl,idx,stat);

-- Table: sqlite_stat4
CREATE TABLE sqlite_stat4(tbl,idx,neq,nlt,ndlt,sample);

-- Table: strategy_components
CREATE TABLE strategy_components (
                    id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    component_type TEXT NOT NULL,
                    component_data TEXT NOT NULL,
                    order_index INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
                );

-- Table: strategy_execution
CREATE TABLE strategy_execution (
                    id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    market_data TEXT,
                    result TEXT NOT NULL,
                    result_details TEXT,
                    position_tag TEXT,
                    executed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
                );

-- Table: sys_backup_info
CREATE TABLE sys_backup_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_name TEXT NOT NULL,
    backup_path TEXT NOT NULL,
    backup_size INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Table: trading_conditions
CREATE TABLE trading_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition_name TEXT NOT NULL,
    condition_type TEXT NOT NULL,          -- 'entry', 'exit', 'management'
    description TEXT,
    variable_mappings TEXT,               -- JSON: ?????? ??????????
    is_template BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: tv_chart_variables
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

-- Table: tv_comparison_groups
CREATE TABLE tv_comparison_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT UNIQUE NOT NULL,
    display_name_ko TEXT NOT NULL,
    display_name_en TEXT,
    description TEXT,
    compatibility_rules TEXT,              -- JSON ?????????????
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: tv_help_texts
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

-- Table: tv_indicator_categories
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

-- Table: tv_indicator_library
CREATE TABLE tv_indicator_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id TEXT UNIQUE NOT NULL,
    display_name_ko TEXT NOT NULL,
    display_name_en TEXT,
    category TEXT NOT NULL,
    calculation_method TEXT,
    calculation_note TEXT,
    description TEXT,
    usage_examples TEXT,                   -- JSON ???????? ???
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: tv_parameter_types
CREATE TABLE tv_parameter_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT UNIQUE NOT NULL,
    description TEXT,
    validation_pattern TEXT,
    validation_example TEXT,
    ui_component TEXT DEFAULT 'input',
    default_constraints TEXT,               -- JSON ???????? ???
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: tv_placeholder_texts
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

-- Table: tv_schema_version
CREATE TABLE tv_schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Table: tv_trading_variables
CREATE TABLE tv_trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,          -- '?????????', 'RSI ????
    display_name_en TEXT,                   -- 'Simple Moving Average', 'RSI Indicator'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum', 'volatility', 'volume', 'price'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable', etc.
    is_active BOOLEAN DEFAULT 1,            -- ????????
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                       -- ???????
    source TEXT DEFAULT 'built-in'          -- 'built-in', 'tradingview', 'custom'
, parameter_required BOOLEAN DEFAULT 0);

-- Table: tv_variable_compatibility_rules
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

-- Table: tv_variable_parameters
CREATE TABLE tv_variable_parameters (
    parameter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,              -- 'RSI', 'SMA' ??????ID
    parameter_name TEXT NOT NULL,           -- 'period', 'source', 'multiplier'
    parameter_type TEXT NOT NULL,           -- 'integer', 'float', 'string', 'boolean', 'enum'
    default_value TEXT,                     -- ?????(?????? ????
    min_value TEXT,                         -- ?????(?????? ??
    max_value TEXT,                         -- ?????(?????? ??
    enum_values TEXT,                       -- enum ????? ??????? ??? (JSON ???)
    is_required BOOLEAN DEFAULT 1,          -- ??? ?????? ???
    display_name_ko TEXT NOT NULL,          -- '???', '????????'
    display_name_en TEXT,                   -- 'Period', 'Data Source'
    description TEXT,                       -- ?????? ???
    display_order INTEGER DEFAULT 0,        -- UI ??? ???
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id) ON DELETE CASCADE
);

-- Table: tv_variable_usage_logs
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

-- Table: tv_workflow_guides
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

-- Indexes
CREATE INDEX idx_secure_keys_created_at ON secure_keys(created_at);
CREATE UNIQUE INDEX idx_secure_keys_type ON secure_keys(key_type);
CREATE INDEX idx_trading_conditions_is_active ON trading_conditions(is_active);
CREATE INDEX idx_trading_conditions_type ON trading_conditions(condition_type);
CREATE INDEX idx_tv_chart_category ON tv_trading_variables(chart_category);
CREATE INDEX idx_tv_chart_variables_category ON tv_chart_variables(category);
CREATE INDEX idx_tv_chart_variables_is_active ON tv_chart_variables(is_active);
CREATE INDEX idx_tv_comparison_group ON tv_trading_variables(comparison_group);
CREATE INDEX idx_tv_is_active ON tv_trading_variables(is_active);
CREATE INDEX idx_tv_purpose_category ON tv_trading_variables(purpose_category);
CREATE INDEX idx_tv_variable_parameters_display_order ON tv_variable_parameters(variable_id, display_order);
CREATE INDEX idx_tv_variable_parameters_variable_id ON tv_variable_parameters(variable_id);
CREATE INDEX idx_tv_variable_usage_logs_created_at ON tv_variable_usage_logs(created_at);
CREATE INDEX idx_tv_variable_usage_logs_variable_id ON tv_variable_usage_logs(variable_id);
