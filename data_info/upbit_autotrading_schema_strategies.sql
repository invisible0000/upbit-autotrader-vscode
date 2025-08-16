-- Upbit Auto Trading - Strategies Database Schema
-- ===============================================
-- DB: strategies.sqlite3
-- 용도: 사용자가 프로그램의 기본 기능을 이용하여 작성한 전략 전반에 관한 데이터
-- 생성일: 2025-08-01
-- 관리 대상: 전략 정의, 조건 설정, 컴포넌트 구성, 실행 기록

PRAGMA foreign_keys = ON;

-- =====================================
-- 전략 시스템 테이블들
-- =====================================

-- 전략 메인 테이블
CREATE TABLE strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    description TEXT,
    strategy_type TEXT DEFAULT 'manual',    -- 'manual', 'automated', 'hybrid'
    risk_level TEXT DEFAULT 'medium',       -- 'low', 'medium', 'high'
    target_market TEXT DEFAULT 'KRW',       -- 'KRW', 'BTC', 'USDT'
    is_active BOOLEAN DEFAULT 0,
    is_favorite BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_executed_at TIMESTAMP,
    execution_count INTEGER DEFAULT 0,
    total_profit_loss REAL DEFAULT 0.0,
    win_rate REAL DEFAULT 0.0,
    tags TEXT                               -- JSON 배열 형태의 태그
);

-- 전략 컴포넌트 (모듈화된 전략 구성요소)
CREATE TABLE strategy_components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    component_name TEXT NOT NULL,
    component_type TEXT NOT NULL,          -- 'entry', 'exit', 'management', 'filter'
    component_config TEXT NOT NULL,        -- JSON 형태의 컴포넌트 설정
    execution_order INTEGER DEFAULT 1,
    is_enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
);

-- 전략 조건 (구체적인 트레이딩 조건들)
CREATE TABLE strategy_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    condition_name TEXT NOT NULL,
    condition_type TEXT NOT NULL,          -- 'entry_long', 'entry_short', 'exit_long', 'exit_short', 'management'
    left_variable TEXT NOT NULL,           -- 변수 ID (예: 'RSI', 'SMA')
    operator TEXT NOT NULL,                -- '>', '<', '>=', '<=', '==', '!='
    right_variable TEXT,                   -- 비교 대상 변수 ID (선택적)
    right_value TEXT,                      -- 비교 대상 값 (선택적)
    logic_operator TEXT DEFAULT 'AND',     -- 'AND', 'OR' (다음 조건과의 관계)
    condition_order INTEGER DEFAULT 1,
    is_enabled BOOLEAN DEFAULT 1,
    variable_parameters TEXT,              -- JSON: 각 변수의 파라미터 설정
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
);

-- 전략 실행 기록
CREATE TABLE strategy_execution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    execution_type TEXT NOT NULL,          -- 'backtest', 'paper_trading', 'live_trading'
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT DEFAULT 'running',         -- 'running', 'completed', 'failed', 'stopped'
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_profit_loss REAL DEFAULT 0.0,
    max_drawdown REAL DEFAULT 0.0,
    sharpe_ratio REAL,
    execution_log TEXT,                    -- JSON 형태의 실행 로그
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
);

-- 컴포넌트 전략 (레거시 호환성)
CREATE TABLE component_strategy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    entry_conditions TEXT NOT NULL,        -- JSON
    exit_conditions TEXT NOT NULL,         -- JSON
    position_sizing TEXT,                  -- JSON
    risk_management TEXT,                  -- JSON
    timeframe TEXT DEFAULT '1d',
    target_symbols TEXT,                   -- JSON 배열
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    backtest_results TEXT,                 -- JSON
    performance_metrics TEXT               -- JSON
);

-- =====================================
-- 실행 및 이력 관리
-- =====================================

-- 실행 이력 (모든 거래 실행 기록)
CREATE TABLE execution_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER,
    symbol TEXT NOT NULL,                  -- 'KRW-BTC', 'KRW-ETH' 등
    action_type TEXT NOT NULL,             -- 'buy', 'sell', 'hold'
    order_type TEXT NOT NULL,              -- 'market', 'limit', 'stop'
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    total_amount REAL NOT NULL,
    commission REAL DEFAULT 0.0,
    executed_at TIMESTAMP NOT NULL,
    order_id TEXT,                         -- 거래소 주문 ID
    status TEXT DEFAULT 'pending',         -- 'pending', 'filled', 'cancelled', 'failed'
    profit_loss REAL DEFAULT 0.0,
    notes TEXT,
    market_conditions TEXT,                -- JSON: 실행 당시 시장 상황
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

-- =====================================
-- 시뮬레이션 시스템
-- =====================================

-- 시뮬레이션 세션
CREATE TABLE simulation_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_name TEXT NOT NULL,
    strategy_id INTEGER,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital REAL NOT NULL,
    final_capital REAL,
    total_return REAL,
    max_drawdown REAL,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    win_rate REAL,
    sharpe_ratio REAL,
    status TEXT DEFAULT 'pending',         -- 'pending', 'running', 'completed', 'failed'
    simulation_config TEXT,               -- JSON: 시뮬레이션 설정
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

-- 시뮬레이션 거래 기록
CREATE TABLE simulation_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    action_type TEXT NOT NULL,             -- 'buy', 'sell'
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    total_amount REAL NOT NULL,
    commission REAL DEFAULT 0.0,
    trade_date TIMESTAMP NOT NULL,
    profit_loss REAL DEFAULT 0.0,
    portfolio_value REAL,
    notes TEXT,
    FOREIGN KEY (session_id) REFERENCES simulation_sessions(id) ON DELETE CASCADE
);

-- =====================================
-- 포트폴리오 및 포지션 관리
-- =====================================

-- 포지션 정보 (현재 보유 포지션)
CREATE TABLE current_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER,
    symbol TEXT NOT NULL,                  -- 'KRW-BTC', 'KRW-ETH' 등
    position_type TEXT NOT NULL,           -- 'long', 'short'
    quantity REAL NOT NULL,
    avg_entry_price REAL NOT NULL,
    current_price REAL,
    unrealized_pnl REAL DEFAULT 0.0,
    realized_pnl REAL DEFAULT 0.0,
    entry_date TIMESTAMP NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stop_loss_price REAL,
    take_profit_price REAL,
    notes TEXT,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

-- 포트폴리오 스냅샷 (일정 시점의 포트폴리오 상태)
CREATE TABLE portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER,
    snapshot_date DATE NOT NULL,
    total_value REAL NOT NULL,
    cash_balance REAL NOT NULL,
    asset_value REAL NOT NULL,
    total_pnl REAL DEFAULT 0.0,
    daily_return REAL DEFAULT 0.0,
    positions_count INTEGER DEFAULT 0,
    risk_score REAL,
    notes TEXT,
    detailed_positions TEXT,              -- JSON: 상세 포지션 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

-- =====================================
-- 알림 및 모니터링
-- =====================================

-- 전략 알림 설정
CREATE TABLE strategy_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,              -- 'profit_target', 'stop_loss', 'condition_met', 'error'
    alert_condition TEXT NOT NULL,         -- JSON: 알림 조건
    is_enabled BOOLEAN DEFAULT 1,
    notification_methods TEXT,             -- JSON: ['email', 'push', 'webhook']
    last_triggered_at TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
);

-- 전략 성능 메트릭
CREATE TABLE strategy_performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_id INTEGER NOT NULL,
    metric_date DATE NOT NULL,
    total_return REAL DEFAULT 0.0,
    daily_return REAL DEFAULT 0.0,
    volatility REAL DEFAULT 0.0,
    sharpe_ratio REAL,
    max_drawdown REAL DEFAULT 0.0,
    win_rate REAL DEFAULT 0.0,
    profit_factor REAL DEFAULT 0.0,
    total_trades INTEGER DEFAULT 0,
    avg_trade_duration_hours REAL,
    best_trade REAL DEFAULT 0.0,
    worst_trade REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE CASCADE
);

-- =====================================
-- 인덱스 생성
-- =====================================

-- 전략 관련 인덱스
CREATE INDEX idx_strategies_is_active ON strategies(is_active);
CREATE INDEX idx_strategies_strategy_type ON strategies(strategy_type);
CREATE INDEX idx_strategies_created_at ON strategies(created_at);
CREATE INDEX idx_strategies_is_favorite ON strategies(is_favorite);

-- 전략 컴포넌트 관련 인덱스
CREATE INDEX idx_strategy_components_strategy_id ON strategy_components(strategy_id);
CREATE INDEX idx_strategy_components_type ON strategy_components(component_type);
CREATE INDEX idx_strategy_components_order ON strategy_components(strategy_id, execution_order);

-- 전략 조건 관련 인덱스
CREATE INDEX idx_strategy_conditions_strategy_id ON strategy_conditions(strategy_id);
CREATE INDEX idx_strategy_conditions_type ON strategy_conditions(condition_type);
CREATE INDEX idx_strategy_conditions_order ON strategy_conditions(strategy_id, condition_order);

-- 실행 기록 관련 인덱스
CREATE INDEX idx_execution_history_strategy_id ON execution_history(strategy_id);
CREATE INDEX idx_execution_history_symbol ON execution_history(symbol);
CREATE INDEX idx_execution_history_executed_at ON execution_history(executed_at);
CREATE INDEX idx_execution_history_action_type ON execution_history(action_type);

-- 시뮬레이션 관련 인덱스
CREATE INDEX idx_simulation_sessions_strategy_id ON simulation_sessions(strategy_id);
CREATE INDEX idx_simulation_sessions_status ON simulation_sessions(status);
CREATE INDEX idx_simulation_trades_session_id ON simulation_trades(session_id);
CREATE INDEX idx_simulation_trades_symbol ON simulation_trades(symbol);

-- 포지션 관련 인덱스
CREATE INDEX idx_current_positions_strategy_id ON current_positions(strategy_id);
CREATE INDEX idx_current_positions_symbol ON current_positions(symbol);
CREATE INDEX idx_portfolio_snapshots_strategy_id ON portfolio_snapshots(strategy_id);
CREATE INDEX idx_portfolio_snapshots_date ON portfolio_snapshots(snapshot_date);

-- 성능 메트릭 관련 인덱스
CREATE INDEX idx_strategy_performance_strategy_id ON strategy_performance_metrics(strategy_id);
CREATE INDEX idx_strategy_performance_date ON strategy_performance_metrics(metric_date);

-- =====================================
-- 뷰 생성
-- =====================================

-- 활성 전략 요약 뷰
CREATE VIEW IF NOT EXISTS active_strategies_summary AS
SELECT 
    s.id,
    s.strategy_name,
    s.description,
    s.strategy_type,
    s.risk_level,
    s.is_favorite,
    s.execution_count,
    s.total_profit_loss,
    s.win_rate,
    s.last_executed_at,
    COUNT(DISTINCT sc.id) as component_count,
    COUNT(DISTINCT scond.id) as condition_count,
    COALESCE(cp.position_count, 0) as current_positions
FROM strategies s
LEFT JOIN strategy_components sc ON s.id = sc.strategy_id AND sc.is_enabled = 1
LEFT JOIN strategy_conditions scond ON s.id = scond.strategy_id AND scond.is_enabled = 1
LEFT JOIN (
    SELECT strategy_id, COUNT(*) as position_count 
    FROM current_positions 
    GROUP BY strategy_id
) cp ON s.id = cp.strategy_id
WHERE s.is_active = 1
GROUP BY s.id;

-- 전략 성과 요약 뷰
CREATE VIEW IF NOT EXISTS strategy_performance_summary AS
SELECT 
    s.id as strategy_id,
    s.strategy_name,
    COUNT(DISTINCT eh.id) as total_trades,
    SUM(CASE WHEN eh.profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(eh.profit_loss) as total_profit_loss,
    AVG(eh.profit_loss) as avg_profit_per_trade,
    MAX(eh.profit_loss) as best_trade,
    MIN(eh.profit_loss) as worst_trade,
    ROUND(
        CAST(SUM(CASE WHEN eh.profit_loss > 0 THEN 1 ELSE 0 END) AS FLOAT) / 
        NULLIF(COUNT(eh.id), 0) * 100, 2
    ) as win_rate_calculated
FROM strategies s
LEFT JOIN execution_history eh ON s.id = eh.strategy_id AND eh.status = 'filled'
WHERE s.is_active = 1
GROUP BY s.id, s.strategy_name;

-- 최근 거래 활동 뷰
CREATE VIEW IF NOT EXISTS recent_trading_activity AS
SELECT 
    eh.id,
    s.strategy_name,
    eh.symbol,
    eh.action_type,
    eh.quantity,
    eh.price,
    eh.total_amount,
    eh.profit_loss,
    eh.executed_at,
    eh.status
FROM execution_history eh
JOIN strategies s ON eh.strategy_id = s.id
WHERE eh.executed_at >= datetime('now', '-30 days')
ORDER BY eh.executed_at DESC;

-- =====================================
-- 트리거 생성 (자동 업데이트)
-- =====================================

-- 전략 업데이트 시간 자동 갱신
CREATE TRIGGER IF NOT EXISTS update_strategy_timestamp
    AFTER UPDATE ON strategies
    FOR EACH ROW
BEGIN
    UPDATE strategies 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- 실행 기록 추가 시 전략 통계 자동 업데이트
CREATE TRIGGER IF NOT EXISTS update_strategy_stats_on_execution
    AFTER INSERT ON execution_history
    FOR EACH ROW
    WHEN NEW.status = 'filled'
BEGIN
    UPDATE strategies 
    SET 
        execution_count = execution_count + 1,
        total_profit_loss = total_profit_loss + NEW.profit_loss,
        last_executed_at = NEW.executed_at,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.strategy_id;
END;
