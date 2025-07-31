-- Upbit Auto Trading Unified Schema
-- 완전한 통합 스키마 (settings DB에서 추출)
-- 생성일: 2025-07-31 15:59:45
-- 추출 도구: Super Schema Extractor
PRAGMA foreign_keys = ON;

-- Table: app_settings
CREATE TABLE app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

-- Table: backup_info
CREATE TABLE backup_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backup_name TEXT NOT NULL,
            backup_path TEXT NOT NULL,
            backup_size INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        );

-- Table: chart_layout_templates
CREATE TABLE chart_layout_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    main_chart_height_ratio REAL DEFAULT 0.6,
                    subplot_configurations TEXT NOT NULL,  -- JSON
                    color_palette TEXT,  -- JSON
                    is_default INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );

-- Table: chart_variables
CREATE TABLE chart_variables (
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
                    compatible_categories TEXT,  -- JSON
                    is_active INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

-- Table: execution_history
CREATE TABLE execution_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT,
            condition_id INTEGER,
            rule_id TEXT,
            executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            trigger_type TEXT,
            action_type TEXT,
            market_data TEXT, -- JSON
            result TEXT,
            profit_loss REAL,
            notes TEXT,
            FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id),
            FOREIGN KEY (condition_id) REFERENCES trading_conditions (id)
        );

-- Table: simulation_market_data
CREATE TABLE simulation_market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                rsi_14 REAL,
                sma_20 REAL,
                sma_60 REAL,
                volatility_30d REAL,
                return_7d REAL,
                return_30d REAL,
                profit_rate REAL DEFAULT 0,
                is_processed BOOLEAN DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id)
            );

-- Table: simulation_sessions
CREATE TABLE simulation_sessions (
                session_id TEXT PRIMARY KEY,
                scenario_name TEXT NOT NULL,
                scenario_description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                data_start_time TEXT NOT NULL,
                data_end_time TEXT NOT NULL,
                initial_capital REAL DEFAULT 1000000,
                current_capital REAL DEFAULT 1000000,
                current_price REAL DEFAULT 0,
                position_quantity REAL DEFAULT 0,
                position_avg_price REAL DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                triggered_conditions TEXT,
                execution_log TEXT,
                status TEXT DEFAULT 'running',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

-- Table: simulation_trades
CREATE TABLE simulation_trades (
                trade_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                amount REAL NOT NULL,
                trigger_name TEXT,
                trigger_condition TEXT,
                profit_rate REAL,
                portfolio_value REAL,
                reason TEXT,
                FOREIGN KEY (session_id) REFERENCES simulation_sessions(session_id)
            );

-- Table: strategies
CREATE TABLE strategies (
            strategy_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            strategy_type TEXT DEFAULT 'custom',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            rules_count INTEGER DEFAULT 0,
            tags TEXT, -- JSON array
            strategy_data TEXT, -- JSON
            backtest_results TEXT, -- JSON
            performance_metrics TEXT -- JSON
        );

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

-- Table: strategy_conditions
CREATE TABLE strategy_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            condition_id INTEGER NOT NULL,
            condition_order INTEGER DEFAULT 0,
            condition_logic TEXT DEFAULT 'AND', -- AND, OR, NOT
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id),
            FOREIGN KEY (condition_id) REFERENCES trading_conditions (id)
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

-- Table: system_settings
CREATE TABLE system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

-- Table: trading_conditions
CREATE TABLE trading_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            variable_id TEXT NOT NULL,
            variable_name TEXT NOT NULL,
            variable_params TEXT, -- JSON
            operator TEXT NOT NULL,
            comparison_type TEXT DEFAULT 'fixed',
            target_value TEXT,
            external_variable TEXT, -- JSON
            trend_direction TEXT DEFAULT 'static',
            is_active INTEGER DEFAULT 1,
            category TEXT DEFAULT 'custom',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0, chart_category TEXT DEFAULT 'subplot',
            UNIQUE(name) -- 중복 이름 방지
        );

-- Table: tv_comparison_groups
CREATE TABLE tv_comparison_groups (
    group_id TEXT PRIMARY KEY,
    group_name_ko TEXT NOT NULL,
    group_name_en TEXT NOT NULL,
    description TEXT,
    can_compare_with TEXT,  -- JSON 형태로 호환 가능한 그룹들 저장
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: tv_help_texts
CREATE TABLE tv_help_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variable_id TEXT NOT NULL,
            parameter_name TEXT,
            help_text TEXT NOT NULL,
            help_type TEXT DEFAULT 'tooltip',
            language TEXT DEFAULT 'ko',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
        );

-- Table: tv_indicator_categories
CREATE TABLE tv_indicator_categories (
            category_id TEXT PRIMARY KEY,
            category_name TEXT NOT NULL,
            description TEXT,
            display_order INTEGER DEFAULT 0,
            icon_name TEXT,
            color_code TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

-- Table: tv_indicator_library
CREATE TABLE tv_indicator_library (
            library_id TEXT PRIMARY KEY,
            variable_id TEXT NOT NULL,
            formula_expression TEXT,
            calculation_method TEXT,
            usage_examples TEXT,
            performance_notes TEXT,
            related_indicators TEXT,
            technical_notes TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
        );

-- Table: tv_parameter_types
CREATE TABLE tv_parameter_types (
            type_id TEXT PRIMARY KEY,
            type_name TEXT NOT NULL,
            description TEXT,
            validation_rule TEXT,
            default_widget TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

-- Table: tv_placeholder_texts
CREATE TABLE tv_placeholder_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variable_id TEXT NOT NULL,
            parameter_name TEXT,
            placeholder_text TEXT NOT NULL,
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

-- Table: tv_variable_parameters
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

-- Table: variable_compatibility_rules
CREATE TABLE variable_compatibility_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    base_variable_id TEXT NOT NULL,
                    compatible_category TEXT NOT NULL,
                    compatibility_reason TEXT,
                    min_value_constraint REAL,
                    max_value_constraint REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (base_variable_id) REFERENCES chart_variables (variable_id)
                );

-- Table: variable_usage_logs
CREATE TABLE variable_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    variable_id TEXT NOT NULL,
                    condition_id INTEGER,
                    usage_context TEXT NOT NULL,
                    chart_display_info TEXT,  -- JSON
                    render_time_ms INTEGER,
                    user_feedback TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (variable_id) REFERENCES chart_variables (variable_id)
                );

-- Indexes
CREATE INDEX idx_tv_chart_category ON tv_trading_variables(chart_category);
CREATE INDEX idx_tv_comparison_group ON tv_trading_variables(comparison_group);
CREATE INDEX idx_tv_is_active ON tv_trading_variables(is_active);
CREATE INDEX idx_tv_purpose_category ON tv_trading_variables(purpose_category);
CREATE INDEX idx_tv_variable_parameters_display_order ON tv_variable_parameters(variable_id, display_order);
CREATE INDEX idx_tv_variable_parameters_variable_id ON tv_variable_parameters(variable_id);
