#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
기존 데이터베이스에 전략 조합 및 백테스트 테이블 추가

기존 upbit_auto_trading.sqlite3에 새로운 테이블들을 추가합니다.
"""

import os
import sys
import sqlite3
from datetime import datetime

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

class DatabaseExtender:
    """기존 데이터베이스 확장 클래스"""
    
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def table_exists(self, table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table_name,))
        
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def create_strategy_tables(self):
        """전략 조합 관련 테이블 생성"""
        print("📊 전략 조합 테이블 생성 중...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 전략 정의 테이블
            if not self.table_exists('strategy_definitions'):
                cursor.execute("""
                    CREATE TABLE strategy_definitions (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        strategy_type TEXT NOT NULL CHECK (strategy_type IN ('entry', 'management')),
                        class_name TEXT NOT NULL,
                        default_parameters TEXT NOT NULL,  -- JSON string
                        parameter_schema TEXT NOT NULL,    -- JSON string
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                print("   ✅ strategy_definitions 테이블 생성")
            else:
                print("   ⏭️ strategy_definitions 테이블 이미 존재")
            
            # 2. 전략 설정 테이블
            if not self.table_exists('strategy_configs'):
                cursor.execute("""
                    CREATE TABLE strategy_configs (
                        config_id TEXT PRIMARY KEY,
                        strategy_definition_id TEXT NOT NULL,
                        strategy_name TEXT NOT NULL,
                        parameters TEXT NOT NULL,  -- JSON string
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        FOREIGN KEY (strategy_definition_id) REFERENCES strategy_definitions(id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_strategy_configs_definition 
                    ON strategy_configs(strategy_definition_id)
                """)
                print("   ✅ strategy_configs 테이블 생성")
            else:
                print("   ⏭️ strategy_configs 테이블 이미 존재")
            
            # 3. 전략 조합 테이블
            if not self.table_exists('strategy_combinations'):
                cursor.execute("""
                    CREATE TABLE strategy_combinations (
                        combination_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        entry_strategy_id TEXT NOT NULL,
                        conflict_resolution TEXT NOT NULL DEFAULT 'conservative' 
                            CHECK (conflict_resolution IN ('conservative', 'priority', 'merge')),
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        created_by TEXT,
                        FOREIGN KEY (entry_strategy_id) REFERENCES strategy_configs(config_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_combinations_name ON strategy_combinations(name)
                """)
                print("   ✅ strategy_combinations 테이블 생성")
            else:
                print("   ⏭️ strategy_combinations 테이블 이미 존재")
            
            # 4. 조합-관리전략 연결 테이블
            if not self.table_exists('combination_management_strategies'):
                cursor.execute("""
                    CREATE TABLE combination_management_strategies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        combination_id TEXT NOT NULL,
                        strategy_config_id TEXT NOT NULL,
                        priority INTEGER NOT NULL DEFAULT 1,
                        FOREIGN KEY (combination_id) REFERENCES strategy_combinations(combination_id),
                        FOREIGN KEY (strategy_config_id) REFERENCES strategy_configs(config_id),
                        UNIQUE(combination_id, strategy_config_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_combination_priority 
                    ON combination_management_strategies(combination_id, priority)
                """)
                print("   ✅ combination_management_strategies 테이블 생성")
            else:
                print("   ⏭️ combination_management_strategies 테이블 이미 존재")
            
            conn.commit()
            print("✅ 전략 조합 테이블 생성 완료")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 전략 테이블 생성 실패: {e}")
            raise
        finally:
            conn.close()
    
    def create_portfolio_tables(self):
        """포트폴리오 및 포지션 관리 테이블 생성"""
        print("💼 포트폴리오 관리 테이블 생성 중...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 포트폴리오 테이블
            if not self.table_exists('portfolios'):
                cursor.execute("""
                    CREATE TABLE portfolios (
                        portfolio_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        initial_capital REAL NOT NULL,
                        current_value REAL NOT NULL DEFAULT 0,
                        cash_balance REAL NOT NULL DEFAULT 0,
                        portfolio_type TEXT NOT NULL DEFAULT 'backtest' 
                            CHECK (portfolio_type IN ('backtest', 'live', 'paper')),
                        strategy_combination_id TEXT,
                        risk_settings TEXT,  -- JSON string
                        
                        -- 성과 지표 (실시간 계산)
                        total_return_percent REAL DEFAULT 0,
                        total_return_amount REAL DEFAULT 0,
                        unrealized_pnl REAL DEFAULT 0,
                        realized_pnl REAL DEFAULT 0,
                        max_drawdown REAL DEFAULT 0,
                        
                        -- 상태 관리
                        status TEXT NOT NULL DEFAULT 'active' 
                            CHECK (status IN ('active', 'paused', 'closed', 'liquidated')),
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        
                        FOREIGN KEY (strategy_combination_id) REFERENCES strategy_combinations(combination_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_portfolios_type_status 
                    ON portfolios(portfolio_type, status)
                """)
                cursor.execute("""
                    CREATE INDEX idx_portfolios_strategy 
                    ON portfolios(strategy_combination_id)
                """)
                print("   ✅ portfolios 테이블 생성")
            else:
                print("   ⏭️ portfolios 테이블 이미 존재")
            
            # 2. 포지션 테이블
            if not self.table_exists('positions'):
                cursor.execute("""
                    CREATE TABLE positions (
                        position_id TEXT PRIMARY KEY,
                        portfolio_id TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
                        
                        -- 포지션 기본 정보
                        entry_price REAL NOT NULL,
                        current_price REAL NOT NULL,
                        quantity REAL NOT NULL,
                        remaining_quantity REAL NOT NULL,
                        
                        -- 손익 정보
                        unrealized_pnl_percent REAL NOT NULL DEFAULT 0,
                        unrealized_pnl_amount REAL NOT NULL DEFAULT 0,
                        realized_pnl_amount REAL NOT NULL DEFAULT 0,
                        
                        -- 리스크 관리
                        stop_loss_price REAL,
                        take_profit_price REAL,
                        trailing_stop_price REAL,
                        max_position_value REAL,
                        
                        -- 전략 정보
                        entry_strategy_id TEXT,
                        entry_reason TEXT,
                        management_actions TEXT,  -- JSON string: 관리 전략 실행 이력
                        
                        -- 상태 관리
                        status TEXT NOT NULL DEFAULT 'open' 
                            CHECK (status IN ('open', 'partial_closed', 'closed', 'stopped_out')),
                        opened_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        closed_at TEXT,
                        
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
                        FOREIGN KEY (entry_strategy_id) REFERENCES strategy_configs(config_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_positions_portfolio_status 
                    ON positions(portfolio_id, status)
                """)
                cursor.execute("""
                    CREATE INDEX idx_positions_symbol_status 
                    ON positions(symbol, status)
                """)
                cursor.execute("""
                    CREATE INDEX idx_positions_opened_at 
                    ON positions(opened_at)
                """)
                print("   ✅ positions 테이블 생성")
            else:
                print("   ⏭️ positions 테이블 이미 존재")
            
            # 3. 포지션 이력 테이블 (포지션 변경 추적)
            if not self.table_exists('position_history'):
                cursor.execute("""
                    CREATE TABLE position_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        position_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        action TEXT NOT NULL CHECK (action IN ('OPEN', 'ADD', 'REDUCE', 'CLOSE', 'UPDATE_STOP', 'UPDATE_TARGET')),
                        
                        -- 변경 정보
                        price REAL NOT NULL,
                        quantity_change REAL NOT NULL,  -- 양수: 증가, 음수: 감소
                        quantity_after REAL NOT NULL,
                        
                        -- 손익 정보 (부분 청산시)
                        realized_pnl REAL,
                        fees REAL,
                        
                        -- 전략 정보
                        strategy_name TEXT,
                        reason TEXT,
                        triggered_by TEXT,  -- 'strategy', 'manual', 'risk_management'
                        
                        -- 리스크 관리 변경
                        stop_price_before REAL,
                        stop_price_after REAL,
                        target_price_before REAL,
                        target_price_after REAL,
                        
                        FOREIGN KEY (position_id) REFERENCES positions(position_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_position_history_position_timestamp 
                    ON position_history(position_id, timestamp)
                """)
                cursor.execute("""
                    CREATE INDEX idx_position_history_action 
                    ON position_history(action, timestamp)
                """)
                print("   ✅ position_history 테이블 생성")
            else:
                print("   ⏭️ position_history 테이블 이미 존재")
            
            # 4. 포트폴리오 스냅샷 테이블 (일별/시간별 성과 추적)
            if not self.table_exists('portfolio_snapshots'):
                cursor.execute("""
                    CREATE TABLE portfolio_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id TEXT NOT NULL,
                        snapshot_time TEXT NOT NULL,
                        snapshot_type TEXT NOT NULL DEFAULT 'hourly' 
                            CHECK (snapshot_type IN ('minute', 'hourly', 'daily', 'weekly')),
                        
                        -- 포트폴리오 상태
                        total_value REAL NOT NULL,
                        cash_balance REAL NOT NULL,
                        invested_amount REAL NOT NULL,
                        
                        -- 성과 지표
                        total_return_percent REAL NOT NULL,
                        total_return_amount REAL NOT NULL,
                        unrealized_pnl REAL NOT NULL,
                        realized_pnl REAL NOT NULL,
                        drawdown_percent REAL NOT NULL,
                        
                        -- 포지션 통계
                        open_positions_count INTEGER NOT NULL DEFAULT 0,
                        total_positions_value REAL NOT NULL DEFAULT 0,
                        
                        -- 리스크 지표
                        portfolio_beta REAL,
                        var_1d REAL,  -- 1일 VaR
                        sharpe_ratio REAL,
                        
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
                        UNIQUE(portfolio_id, snapshot_time, snapshot_type)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_portfolio_snapshots_portfolio_time 
                    ON portfolio_snapshots(portfolio_id, snapshot_time)
                """)
                cursor.execute("""
                    CREATE INDEX idx_portfolio_snapshots_type_time 
                    ON portfolio_snapshots(snapshot_type, snapshot_time)
                """)
                print("   ✅ portfolio_snapshots 테이블 생성")
            else:
                print("   ⏭️ portfolio_snapshots 테이블 이미 존재")
            
            conn.commit()
            print("✅ 포트폴리오 관리 테이블 생성 완료")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 포트폴리오 테이블 생성 실패: {e}")
            raise
        finally:
            conn.close()

    def create_backtest_tables(self):
        """백테스트 관련 테이블 생성"""
        print("🧪 백테스트 테이블 생성 중...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 백테스트 결과 테이블
            if not self.table_exists('backtest_results'):
                cursor.execute("""
                    CREATE TABLE backtest_results (
                        result_id TEXT PRIMARY KEY,
                        portfolio_id TEXT NOT NULL,  -- 포트폴리오 ID 연결
                        combination_id TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        initial_capital REAL NOT NULL,
                        trading_fee_rate REAL NOT NULL DEFAULT 0.0005,
                        slippage_rate REAL NOT NULL DEFAULT 0.001,
                        risk_settings TEXT NOT NULL,  -- JSON string
                        
                        -- 성과 지표
                        total_return REAL,
                        total_trades INTEGER,
                        winning_trades INTEGER,
                        losing_trades INTEGER,
                        win_rate REAL,
                        sharpe_ratio REAL,
                        max_drawdown REAL,
                        
                        -- 전략 기여도
                        entry_contribution TEXT,      -- JSON string
                        management_contribution TEXT, -- JSON string
                        
                        -- 실행 정보
                        status TEXT NOT NULL DEFAULT 'pending' 
                            CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                        backtest_start TEXT,
                        backtest_end TEXT,
                        data_points INTEGER,
                        error_message TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
                        FOREIGN KEY (combination_id) REFERENCES strategy_combinations(combination_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_backtest_portfolio 
                    ON backtest_results(portfolio_id)
                """)
                cursor.execute("""
                    CREATE INDEX idx_backtest_combination_symbol 
                    ON backtest_results(combination_id, symbol)
                """)
                cursor.execute("""
                    CREATE INDEX idx_backtest_date_range 
                    ON backtest_results(start_date, end_date)
                """)
                print("   ✅ backtest_results 테이블 생성")
            else:
                print("   ⏭️ backtest_results 테이블 이미 존재")
            
            # 2. 거래 로그 테이블 (포지션 ID 연결 강화)
            if not self.table_exists('trade_logs'):
                cursor.execute("""
                    CREATE TABLE trade_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backtest_result_id TEXT NOT NULL,
                        position_id TEXT,  -- 포지션 ID 연결 (NULL 가능)
                        timestamp TEXT NOT NULL,
                        action TEXT NOT NULL CHECK (action IN ('ENTER', 'EXIT', 'ADD_BUY', 'ADD_SELL', 'UPDATE_STOP')),
                        direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
                        price REAL NOT NULL,
                        quantity REAL NOT NULL,
                        
                        -- 손익 정보 (EXIT 액션에만)
                        pnl_percent REAL,
                        pnl_amount REAL,
                        fees REAL,
                        
                        -- 전략 정보
                        strategy_name TEXT,
                        reason TEXT,
                        
                        -- 리스크 관리 정보
                        stop_price REAL,
                        risk_percent REAL,
                        holding_time REAL,  -- 시간 단위
                        
                        -- 포트폴리오 상태 (거래 후)
                        portfolio_value_after REAL,
                        cash_balance_after REAL,
                        
                        FOREIGN KEY (backtest_result_id) REFERENCES backtest_results(result_id),
                        FOREIGN KEY (position_id) REFERENCES positions(position_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_trade_logs_backtest_timestamp 
                    ON trade_logs(backtest_result_id, timestamp)
                """)
                cursor.execute("""
                    CREATE INDEX idx_trade_logs_position 
                    ON trade_logs(position_id, timestamp)
                """)
                print("   ✅ trade_logs 테이블 생성")
            else:
                print("   ⏭️ trade_logs 테이블 이미 존재")
            
            # 3. 포지션 로그 테이블
            if not self.table_exists('position_logs'):
                cursor.execute("""
                    CREATE TABLE position_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backtest_result_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
                        entry_price REAL NOT NULL,
                        current_price REAL NOT NULL,
                        quantity REAL NOT NULL,
                        stop_price REAL,
                        
                        -- 손익 정보
                        unrealized_pnl_percent REAL NOT NULL,
                        unrealized_pnl_amount REAL NOT NULL,
                        
                        -- 관리 전략 이력
                        management_actions TEXT,  -- JSON string
                        
                        FOREIGN KEY (backtest_result_id) REFERENCES backtest_results(result_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_position_logs_backtest_timestamp 
                    ON position_logs(backtest_result_id, timestamp)
                """)
                print("   ✅ position_logs 테이블 생성")
            else:
                print("   ⏭️ position_logs 테이블 이미 존재")
            
            conn.commit()
            print("✅ 백테스트 테이블 생성 완료")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 백테스트 테이블 생성 실패: {e}")
            raise
        finally:
            conn.close()
    
    def create_optimization_tables(self):
        """매개변수 최적화 관련 테이블 생성"""
        print("🧬 최적화 테이블 생성 중...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 최적화 작업 테이블
            if not self.table_exists('optimization_jobs'):
                cursor.execute("""
                    CREATE TABLE optimization_jobs (
                        job_id TEXT PRIMARY KEY,
                        combination_id TEXT NOT NULL,
                        algorithm TEXT NOT NULL CHECK (algorithm IN ('GA', 'PSO', 'RANDOM', 'GRID')),
                        parameter_ranges TEXT NOT NULL,  -- JSON string
                        optimization_target TEXT NOT NULL 
                            CHECK (optimization_target IN ('fitness_score', 'sharpe_ratio', 'total_return', 'win_rate')),
                        
                        -- 알고리즘 설정
                        population_size INTEGER,
                        generations INTEGER,
                        iterations INTEGER,
                        
                        -- 실행 정보
                        status TEXT NOT NULL DEFAULT 'pending' 
                            CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                        progress REAL NOT NULL DEFAULT 0.0,
                        started_at TEXT,
                        completed_at TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        
                        -- 결과 정보
                        best_parameters TEXT,  -- JSON string
                        best_fitness REAL,
                        convergence_data TEXT,  -- JSON string
                        
                        FOREIGN KEY (combination_id) REFERENCES strategy_combinations(combination_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_optimization_combination_status 
                    ON optimization_jobs(combination_id, status)
                """)
                print("   ✅ optimization_jobs 테이블 생성")
            else:
                print("   ⏭️ optimization_jobs 테이블 이미 존재")
            
            # 2. 최적화 결과 테이블
            if not self.table_exists('optimization_results'):
                cursor.execute("""
                    CREATE TABLE optimization_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL,
                        generation INTEGER NOT NULL,
                        individual_id INTEGER NOT NULL,
                        parameters TEXT NOT NULL,  -- JSON string
                        fitness_score REAL NOT NULL,
                        
                        -- 성과 지표
                        total_return REAL,
                        sharpe_ratio REAL,
                        win_rate REAL,
                        max_drawdown REAL,
                        
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        
                        FOREIGN KEY (job_id) REFERENCES optimization_jobs(job_id)
                    )
                """)
                
                cursor.execute("""
                    CREATE INDEX idx_optimization_results_job_generation 
                    ON optimization_results(job_id, generation)
                """)
                cursor.execute("""
                    CREATE INDEX idx_optimization_results_fitness 
                    ON optimization_results(fitness_score DESC)
                """)
                print("   ✅ optimization_results 테이블 생성")
            else:
                print("   ⏭️ optimization_results 테이블 이미 존재")
            
            conn.commit()
            print("✅ 최적화 테이블 생성 완료")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 최적화 테이블 생성 실패: {e}")
            raise
        finally:
            conn.close()
    
    def insert_initial_data(self):
        """초기 데이터 삽입"""
        print("📝 초기 데이터 삽입 중...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 전략 정의 데이터 삽입
            strategy_definitions = [
                # 진입 전략
                ('rsi_entry', 'RSI 과매수/과매도', 'RSI 지표를 이용한 과매수/과매도 구간 진입', 
                 'entry', 'RSIEntry', 
                 '{"rsi_period": 14, "oversold": 30, "overbought": 70}',
                 '{"rsi_period": {"type": "int", "min": 5, "max": 30}, "oversold": {"type": "int", "min": 10, "max": 40}, "overbought": {"type": "int", "min": 60, "max": 90}}'),
                
                ('ma_cross_entry', '이동평균선 크로스', '단기/장기 이동평균선 교차 신호',
                 'entry', 'MovingAverageCrossEntry',
                 '{"short_window": 20, "long_window": 50}',
                 '{"short_window": {"type": "int", "min": 5, "max": 50}, "long_window": {"type": "int", "min": 20, "max": 200}}'),
                
                ('bollinger_entry', '볼린저 밴드', '볼린저 밴드 돌파 및 반등 신호',
                 'entry', 'BollingerBandsEntry',
                 '{"window": 20, "num_std": 2.0}',
                 '{"window": {"type": "int", "min": 10, "max": 50}, "num_std": {"type": "float", "min": 1.0, "max": 3.0}}'),
                
                # 관리 전략
                ('averaging_down', '물타기', '하락 시 추가 매수를 통한 평균단가 하향',
                 'management', 'AveragingDownManagement',
                 '{"drop_threshold": -0.05, "max_additions": 3, "addition_ratio": 0.5}',
                 '{"drop_threshold": {"type": "float", "min": -0.20, "max": -0.02}, "max_additions": {"type": "int", "min": 1, "max": 5}, "addition_ratio": {"type": "float", "min": 0.2, "max": 1.0}}'),
                
                ('trailing_stop', '트레일링 스탑', '수익 구간에서 동적 손절선 관리',
                 'management', 'TrailingStopManagement',
                 '{"activation_profit": 0.02, "trail_percent": 0.01}',
                 '{"activation_profit": {"type": "float", "min": 0.01, "max": 0.05}, "trail_percent": {"type": "float", "min": 0.005, "max": 0.03}}'),
                
                ('pyramiding', '불타기', '상승 시 추가 매수를 통한 수익 극대화',
                 'management', 'PyramidingManagement',
                 '{"profit_threshold": 0.03, "max_additions": 2, "addition_ratio": 0.3}',
                 '{"profit_threshold": {"type": "float", "min": 0.01, "max": 0.10}, "max_additions": {"type": "int", "min": 1, "max": 3}, "addition_ratio": {"type": "float", "min": 0.1, "max": 0.5}}')
            ]
            
            for strategy in strategy_definitions:
                cursor.execute("""
                    INSERT OR IGNORE INTO strategy_definitions 
                    (id, name, description, strategy_type, class_name, default_parameters, parameter_schema)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, strategy)
            
            # 전략 설정 데이터 삽입
            strategy_configs = [
                ('rsi_config_1', 'rsi_entry', 'RSI 과매수/과매도 (기본)', 
                 '{"rsi_period": 14, "oversold": 30, "overbought": 70}'),
                ('averaging_config_1', 'averaging_down', '물타기 (보수적)', 
                 '{"drop_threshold": -0.05, "max_additions": 2, "addition_ratio": 0.5}'),
                ('trailing_config_1', 'trailing_stop', '트레일링 스탑 (기본)', 
                 '{"activation_profit": 0.02, "trail_percent": 0.01}'),
            ]
            
            for config in strategy_configs:
                cursor.execute("""
                    INSERT OR IGNORE INTO strategy_configs 
                    (config_id, strategy_definition_id, strategy_name, parameters)
                    VALUES (?, ?, ?, ?)
                """, config)
            
            # 샘플 전략 조합 생성
            cursor.execute("""
                INSERT OR IGNORE INTO strategy_combinations 
                (combination_id, name, description, entry_strategy_id, conflict_resolution)
                VALUES (?, ?, ?, ?, ?)
            """, ('rsi_averaging_trailing', 'RSI + 물타기 + 트레일링', 
                  'RSI 진입 + 물타기 관리 + 트레일링 스탑', 'rsi_config_1', 'conservative'))
            
            # 관리 전략 연결
            cursor.execute("""
                INSERT OR IGNORE INTO combination_management_strategies 
                (combination_id, strategy_config_id, priority)
                VALUES (?, ?, ?)
            """, ('rsi_averaging_trailing', 'averaging_config_1', 1))
            
            cursor.execute("""
                INSERT OR IGNORE INTO combination_management_strategies 
                (combination_id, strategy_config_id, priority)
                VALUES (?, ?, ?)
            """, ('rsi_averaging_trailing', 'trailing_config_1', 2))
            
            # 샘플 포트폴리오 생성
            cursor.execute("""
                INSERT OR IGNORE INTO portfolios 
                (portfolio_id, name, description, initial_capital, current_value, cash_balance, 
                 portfolio_type, strategy_combination_id, risk_settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ('backtest_portfolio_1', 'RSI 전략 백테스트 포트폴리오', 
                  'RSI + 물타기 + 트레일링 스탑 조합 백테스트', 1000000.0, 1000000.0, 1000000.0,
                  'backtest', 'rsi_averaging_trailing', 
                  '{"max_position_size": 0.2, "stop_loss": 0.05, "max_daily_loss": 0.03}'))
            
            cursor.execute("""
                INSERT OR IGNORE INTO portfolios 
                (portfolio_id, name, description, initial_capital, current_value, cash_balance, 
                 portfolio_type, risk_settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ('live_portfolio_1', '실전 투자 포트폴리오', 
                  '실제 투자를 위한 포트폴리오', 5000000.0, 5000000.0, 5000000.0,
                  'live', '{"max_position_size": 0.15, "stop_loss": 0.03, "max_daily_loss": 0.02}'))
            
            conn.commit()
            print("✅ 초기 데이터 삽입 완료")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 초기 데이터 삽입 실패: {e}")
            raise
        finally:
            conn.close()
    
    def get_extended_stats(self):
        """확장된 데이터베이스 통계"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            print("\n📊 확장된 데이터베이스 현황:")
            
            # 기존 테이블들
            tables = ['market_data', 'trading_strategies', 'ohlcv_data', 'orderbook_data']
            for table in tables:
                if self.table_exists(table):
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   {table}: {count:,}개")
            
            print("   ────────────────────────")
            
            # 새로 추가된 테이블들
            new_tables = [
                'strategy_definitions', 'strategy_configs', 'strategy_combinations',
                'combination_management_strategies', 'portfolios', 'positions', 
                'position_history', 'portfolio_snapshots', 'backtest_results', 
                'trade_logs', 'position_logs', 'optimization_jobs', 'optimization_results'
            ]
            
            for table in new_tables:
                if self.table_exists(table):
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   {table}: {count:,}개")
                else:
                    print(f"   {table}: ❌ 없음")
            
        finally:
            conn.close()


def main():
    """메인 실행 함수"""
    print("🚀 기존 SQLite 데이터베이스 확장")
    print("=" * 60)
    
    try:
        # 데이터베이스 확장 매니저 생성
        extender = DatabaseExtender()
        
        # 테이블 생성
        extender.create_strategy_tables()
        extender.create_portfolio_tables()  # 포트폴리오 테이블 먼저 생성
        extender.create_backtest_tables()
        extender.create_optimization_tables()
        
        # 초기 데이터 삽입
        extender.insert_initial_data()
        
        # 통계 출력
        extender.get_extended_stats()
        
        print("\n🎉 데이터베이스 확장 완료!")
        print("   ✅ 기존 시장 데이터 보존")
        print("   🧬 전략 조합 시스템 추가")
        print("   🧪 백테스트 결과 저장 준비")
        print("   🔧 매개변수 최적화 테이블 준비")
        
    except Exception as e:
        print(f"\n❌ 확장 실패: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
