"""
데이터베이스 스키마 초기화 도구 - strategies와 market_data DB 기본 테이블 생성
"""

import sqlite3
from pathlib import Path
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("DatabaseSchemaInit")


def init_strategies_database():
    """전략 데이터베이스 기본 스키마 생성"""
    db_path = Path("data/strategies.sqlite3")
    db_path.parent.mkdir(exist_ok=True)

    logger.info("전략 데이터베이스 스키마 초기화 시작")

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()

        # 1. 전략 메타정보 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                strategy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                version TEXT DEFAULT '1.0.0',
                author TEXT,
                tags TEXT,  -- JSON 배열 형태
                risk_level INTEGER DEFAULT 3,  -- 1(낮음) ~ 5(높음)
                expected_return_pct REAL,
                max_drawdown_pct REAL,
                target_symbols TEXT,  -- JSON 배열 형태
                timeframes TEXT,  -- JSON 배열 형태
                config_json TEXT  -- 전략 설정 JSON
            )
        """)

        # 2. 전략 조건/규칙 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_conditions (
                condition_id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                condition_type TEXT NOT NULL,  -- entry, exit, stop_loss, take_profit
                condition_name TEXT NOT NULL,
                condition_config TEXT NOT NULL,  -- JSON 형태
                display_order INTEGER DEFAULT 0,
                is_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id) ON DELETE CASCADE
            )
        """)

        # 3. 백테스트 결과 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                result_id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                initial_capital REAL NOT NULL,
                final_capital REAL NOT NULL,
                total_return_pct REAL NOT NULL,
                max_drawdown_pct REAL NOT NULL,
                sharpe_ratio REAL,
                total_trades INTEGER DEFAULT 0,
                win_trades INTEGER DEFAULT 0,
                win_rate_pct REAL DEFAULT 0,
                profit_factor REAL,
                avg_trade_return_pct REAL,
                execution_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                config_snapshot TEXT,  -- 백테스트 당시 설정 스냅샷
                FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id) ON DELETE CASCADE
            )
        """)

        # 4. 인덱스 생성
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_strategies_active ON strategies (is_active)",
            "CREATE INDEX IF NOT EXISTS idx_strategies_risk ON strategies (risk_level)",
            "CREATE INDEX IF NOT EXISTS idx_strategy_conditions_strategy ON strategy_conditions (strategy_id, condition_type)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtest_results (strategy_id, symbol, timeframe)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_performance ON backtest_results (total_return_pct, max_drawdown_pct)"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        # 5. 스키마 버전 관리
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version, description)
            VALUES ('1.0.0', '전략 DB 기본 스키마 초기화')
        """)

        conn.commit()
        logger.info("✅ 전략 데이터베이스 스키마 초기화 완료")


def init_market_data_database():
    """마켓 데이터베이스 기본 스키마 생성"""
    db_path = Path("data/market_data.sqlite3")
    db_path.parent.mkdir(exist_ok=True)

    logger.info("마켓 데이터베이스 스키마 초기화 시작")

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()

        # 1. 캔들 데이터 테이블 (파티션 고려)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candle_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,  -- Unix timestamp
                open_price REAL NOT NULL,
                high_price REAL NOT NULL,
                low_price REAL NOT NULL,
                close_price REAL NOT NULL,
                volume REAL NOT NULL,
                quote_volume REAL,
                trade_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """)

        # 2. 티커 데이터 (실시간 가격)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticker_data (
                symbol TEXT PRIMARY KEY,
                current_price REAL NOT NULL,
                bid_price REAL,
                ask_price REAL,
                volume_24h REAL,
                change_24h_pct REAL,
                high_24h REAL,
                low_24h REAL,
                market_cap REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. 지표 계산 결과 캐시
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indicator_cache (
                cache_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                indicator_name TEXT NOT NULL,
                parameters_hash TEXT NOT NULL,  -- 파라미터 해시값
                start_timestamp INTEGER NOT NULL,
                end_timestamp INTEGER NOT NULL,
                values_json TEXT NOT NULL,  -- 계산된 지표 값들 (JSON)
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)

        # 4. 마켓 이벤트 로그
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_events (
                event_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                event_type TEXT NOT NULL,  -- price_alert, volume_spike, etc.
                event_data TEXT NOT NULL,  -- JSON 형태
                severity_level INTEGER DEFAULT 1,  -- 1(낮음) ~ 5(높음)
                triggered_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. 인덱스 생성
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_candle_symbol_tf_time ON candle_data (symbol, timeframe, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_candle_timestamp ON candle_data (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ticker_price ON ticker_data (current_price, change_24h_pct)",
            "CREATE INDEX IF NOT EXISTS idx_indicator_cache_lookup ON indicator_cache (symbol, timeframe, indicator_name, parameters_hash)",
            "CREATE INDEX IF NOT EXISTS idx_indicator_cache_expires ON indicator_cache (expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_market_events_symbol_type ON market_events (symbol, event_type, triggered_at)"
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        # 6. 스키마 버전 관리
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)

        cursor.execute("""
            INSERT OR REPLACE INTO schema_version (version, description)
            VALUES ('1.0.0', '마켓 데이터 DB 기본 스키마 초기화')
        """)

        conn.commit()
        logger.info("✅ 마켓 데이터베이스 스키마 초기화 완료")


def main():
    """메인 실행"""
    logger.info("🚀 데이터베이스 스키마 초기화 시작")

    # 1. 전략 데이터베이스 초기화
    init_strategies_database()

    # 2. 마켓 데이터베이스 초기화
    init_market_data_database()

    logger.info("✅ 모든 데이터베이스 스키마 초기화 완료")


if __name__ == "__main__":
    main()
