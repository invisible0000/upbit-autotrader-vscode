"""
원자적 전략 빌더 DB 스키마 설계
Atomic Strategy Builder Database Schema

기존 시스템과 독립적으로 동작하는 원자적 전략 빌더 전용 테이블들
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

class AtomicStrategyDBSchema:
    """원자적 전략 빌더 DB 스키마 관리 클래스"""
    
    def __init__(self, db_path: str = "data/upbit_auto_trading.sqlite3"):
        self.db_path = db_path
        
    def create_atomic_strategy_tables(self):
        """원자적 전략 빌더 전용 테이블들 생성"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. atomic_variables 테이블 - 변수 정의
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atomic_variables (
                    variable_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    category TEXT NOT NULL,  -- price, indicator, volume, time
                    data_type TEXT NOT NULL, -- float, int, datetime, boolean
                    description TEXT,
                    parameters TEXT,  -- JSON: 지표 계산에 필요한 파라미터들
                    default_value TEXT,  -- JSON: 기본값
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. atomic_conditions 테이블 - 조건 정의
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atomic_conditions (
                    condition_id TEXT PRIMARY KEY,
                    variable_id TEXT NOT NULL,
                    operator TEXT NOT NULL,  -- <, >, <=, >=, ==, !=, between, in
                    value TEXT NOT NULL,  -- JSON: 비교값 (단일값 또는 배열)
                    logic_operator TEXT,  -- AND, OR (다중 조건의 경우)
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (variable_id) REFERENCES atomic_variables(variable_id)
                )
            """)
            
            # 3. atomic_actions 테이블 - 액션 정의
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atomic_actions (
                    action_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    action_type TEXT NOT NULL,  -- market_buy, market_sell, limit_buy, limit_sell, stop_loss, take_profit
                    parameters TEXT NOT NULL,  -- JSON: 액션 실행에 필요한 파라미터들
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 4. atomic_rules 테이블 - 규칙 (조건 + 액션)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atomic_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    role TEXT NOT NULL,  -- ENTRY, EXIT, MANAGEMENT, RISK_MGMT
                    priority INTEGER DEFAULT 1,
                    condition_group TEXT NOT NULL,  -- JSON: 조건들의 그룹과 논리 연산
                    action_id TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (action_id) REFERENCES atomic_actions(action_id)
                )
            """)
            
            # 5. atomic_strategies 테이블 - 완전한 전략 (규칙들의 조합)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atomic_strategies (
                    strategy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,  -- basic, advanced, custom
                    tags TEXT,  -- JSON: 태그 배열
                    rule_ids TEXT NOT NULL,  -- JSON: 규칙 ID 배열
                    execution_order TEXT,  -- JSON: 규칙 실행 순서 및 우선순위
                    conflict_resolution TEXT DEFAULT 'priority',  -- priority, majority, weighted
                    risk_settings TEXT,  -- JSON: 리스크 관리 설정
                    performance_metrics TEXT,  -- JSON: 백테스트 성과 지표
                    is_template BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_by TEXT,  -- 생성자 정보
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 6. atomic_strategy_templates 테이블 - 전략 템플릿
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atomic_strategy_templates (
                    template_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,  -- beginner, intermediate, advanced
                    template_data TEXT NOT NULL,  -- JSON: 전체 전략 구성 데이터
                    tags TEXT,  -- JSON: 태그 배열
                    difficulty_level INTEGER DEFAULT 1,  -- 1-5
                    estimated_time_minutes INTEGER DEFAULT 5,
                    is_featured BOOLEAN DEFAULT 0,
                    download_count INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 7. atomic_strategy_executions 테이블 - 전략 실행 기록
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atomic_strategy_executions (
                    execution_id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    execution_type TEXT NOT NULL,  -- backtest, live, paper
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT DEFAULT 'running',  -- running, completed, failed, stopped
                    initial_capital REAL,
                    current_capital REAL,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    total_return_percent REAL DEFAULT 0.0,
                    max_drawdown_percent REAL DEFAULT 0.0,
                    execution_log TEXT,  -- JSON: 실행 로그
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (strategy_id) REFERENCES atomic_strategies(strategy_id)
                )
            """)
            
            # 8. atomic_rule_conditions 테이블 - 규칙-조건 매핑 (다대다)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atomic_rule_conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL,
                    condition_id TEXT NOT NULL,
                    condition_group INTEGER DEFAULT 1,  -- 조건 그룹 번호
                    logic_operator TEXT DEFAULT 'AND',  -- AND, OR
                    weight REAL DEFAULT 1.0,  -- 조건 가중치
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (rule_id) REFERENCES atomic_rules(rule_id),
                    FOREIGN KEY (condition_id) REFERENCES atomic_conditions(condition_id),
                    UNIQUE(rule_id, condition_id)
                )
            """)
            
            # 인덱스 생성
            self._create_indexes(cursor)
            
            conn.commit()
            print("✅ 원자적 전략 빌더 DB 스키마 생성 완료!")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ DB 스키마 생성 실패: {e}")
            raise
        finally:
            conn.close()
    
    def _create_indexes(self, cursor):
        """인덱스 생성"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_atomic_variables_category ON atomic_variables(category)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_conditions_variable ON atomic_conditions(variable_id)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_rules_role ON atomic_rules(role)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_rules_priority ON atomic_rules(priority)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_strategies_category ON atomic_strategies(category)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_strategies_active ON atomic_strategies(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_executions_strategy ON atomic_strategy_executions(strategy_id)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_executions_status ON atomic_strategy_executions(status)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_templates_category ON atomic_strategy_templates(category)",
            "CREATE INDEX IF NOT EXISTS idx_atomic_rule_conditions_rule ON atomic_rule_conditions(rule_id)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def insert_default_data(self):
        """기본 데이터 삽입"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 기본 변수들 삽입
            self._insert_default_variables(cursor)
            
            # 기본 액션들 삽입
            self._insert_default_actions(cursor)
            
            # 7규칙 전략 템플릿 삽입
            self._insert_seven_rule_template(cursor)
            
            conn.commit()
            print("✅ 기본 데이터 삽입 완료!")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 기본 데이터 삽입 실패: {e}")
            raise
        finally:
            conn.close()
    
    def _insert_default_variables(self, cursor):
        """기본 변수들 삽입"""
        variables = [
            # 가격 관련 변수
            {
                'variable_id': str(uuid.uuid4()),
                'name': 'current_price',
                'display_name': '현재가',
                'category': 'price',
                'data_type': 'float',
                'description': '현재 거래가격',
                'parameters': '{}',
                'default_value': '0.0'
            },
            {
                'variable_id': str(uuid.uuid4()),
                'name': 'profit_rate',
                'display_name': '수익률 (%)',
                'category': 'price',
                'data_type': 'float',
                'description': '현재 포지션의 수익률',
                'parameters': '{}',
                'default_value': '0.0'
            },
            # 지표 관련 변수
            {
                'variable_id': str(uuid.uuid4()),
                'name': 'rsi_14',
                'display_name': 'RSI (14)',
                'category': 'indicator',
                'data_type': 'float',
                'description': '14일 RSI 지표',
                'parameters': '{"period": 14}',
                'default_value': '50.0'
            },
            {
                'variable_id': str(uuid.uuid4()),
                'name': 'sma_20',
                'display_name': '단순이평선 (20)',
                'category': 'indicator',
                'data_type': 'float',
                'description': '20일 단순이동평균선',
                'parameters': '{"period": 20}',
                'default_value': '0.0'
            },
            # 볼륨 관련 변수
            {
                'variable_id': str(uuid.uuid4()),
                'name': 'volume_24h',
                'display_name': '24시간 거래량',
                'category': 'volume',
                'data_type': 'float',
                'description': '24시간 누적 거래량',
                'parameters': '{}',
                'default_value': '0.0'
            },
            # 시간 관련 변수
            {
                'variable_id': str(uuid.uuid4()),
                'name': 'holding_hours',
                'display_name': '보유시간 (시간)',
                'category': 'time',
                'data_type': 'float',
                'description': '포지션 보유시간',
                'parameters': '{}',
                'default_value': '0.0'
            }
        ]
        
        for var in variables:
            cursor.execute("""
                INSERT OR IGNORE INTO atomic_variables 
                (variable_id, name, display_name, category, data_type, description, parameters, default_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                var['variable_id'], var['name'], var['display_name'], 
                var['category'], var['data_type'], var['description'],
                var['parameters'], var['default_value']
            ))
    
    def _insert_default_actions(self, cursor):
        """기본 액션들 삽입"""
        actions = [
            {
                'action_id': str(uuid.uuid4()),
                'name': 'market_buy_5_percent',
                'display_name': '시장가 매수 (5%)',
                'action_type': 'market_buy',
                'parameters': '{"allocation_percent": 5.0, "max_slippage": 0.1}',
                'description': '가용 자금의 5%로 시장가 매수'
            },
            {
                'action_id': str(uuid.uuid4()),
                'name': 'market_sell_100_percent',
                'display_name': '시장가 전량 매도',
                'action_type': 'market_sell',
                'parameters': '{"allocation_percent": 100.0, "max_slippage": 0.1}',
                'description': '보유 수량 전량 시장가 매도'
            },
            {
                'action_id': str(uuid.uuid4()),
                'name': 'trailing_stop_3_percent',
                'display_name': '트레일링 스탑 (3%)',
                'action_type': 'trailing_stop',
                'parameters': '{"trail_percent": 3.0, "activation_profit": 5.0}',
                'description': '고점 대비 3% 하락시 매도하는 트레일링 스탑'
            }
        ]
        
        for action in actions:
            cursor.execute("""
                INSERT OR IGNORE INTO atomic_actions 
                (action_id, name, display_name, action_type, parameters, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                action['action_id'], action['name'], action['display_name'],
                action['action_type'], action['parameters'], action['description']
            ))
    
    def _insert_seven_rule_template(self, cursor):
        """7규칙 전략 템플릿 삽입"""
        template_data = {
            "name": "기본 7규칙 전략",
            "description": "RSI 진입부터 급등 감지까지 완전한 매매 전략",
            "rules": [
                {
                    "name": "RSI 과매도 진입",
                    "role": "ENTRY",
                    "conditions": [{"variable": "rsi_14", "operator": "<", "value": 20}],
                    "action": "market_buy_5_percent"
                },
                {
                    "name": "수익 시 불타기",
                    "role": "MANAGEMENT",
                    "conditions": [{"variable": "profit_rate", "operator": ">=", "value": 5}],
                    "action": "market_buy_5_percent"
                },
                {
                    "name": "계획된 익절",
                    "role": "EXIT",
                    "conditions": [{"variable": "profit_rate", "operator": ">=", "value": 15}],
                    "action": "market_sell_100_percent"
                },
                {
                    "name": "트레일링 스탑",
                    "role": "EXIT",
                    "conditions": [{"variable": "profit_rate", "operator": ">=", "value": 5}],
                    "action": "trailing_stop_3_percent"
                },
                {
                    "name": "하락 시 물타기",
                    "role": "MANAGEMENT",
                    "conditions": [{"variable": "profit_rate", "operator": "<=", "value": -5}],
                    "action": "market_buy_5_percent"
                },
                {
                    "name": "급락 감지",
                    "role": "RISK_MGMT",
                    "conditions": [{"variable": "profit_rate", "operator": "<=", "value": -10}],
                    "action": "market_sell_100_percent"
                },
                {
                    "name": "급등 감지",
                    "role": "MANAGEMENT",
                    "conditions": [{"variable": "profit_rate", "operator": ">=", "value": 10}],
                    "action": "trailing_stop_3_percent"
                }
            ]
        }
        
        cursor.execute("""
            INSERT OR IGNORE INTO atomic_strategy_templates 
            (template_id, name, description, category, template_data, tags, difficulty_level, estimated_time_minutes, is_featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            "기본 7규칙 전략",
            "RSI 과매도 진입부터 급등 감지까지 완전한 매매 전략. 초보자도 5분 내에 구현 가능한 검증된 템플릿",
            "beginner",
            json.dumps(template_data, ensure_ascii=False),
            json.dumps(["RSI", "불타기", "트레일링스탑", "리스크관리"], ensure_ascii=False),
            1,
            5,
            1
        ))

def main():
    """스키마 생성 및 기본 데이터 삽입"""
    print("🔧 원자적 전략 빌더 DB 스키마 초기화 시작...")
    
    schema = AtomicStrategyDBSchema()
    
    # 스키마 생성
    schema.create_atomic_strategy_tables()
    
    # 기본 데이터 삽입
    schema.insert_default_data()
    
    print("🎉 원자적 전략 빌더 DB 초기화 완료!")
    print("📖 이제 ui_prototypes/atomic_strategy_builder_ui.py에서 DB 연동을 테스트할 수 있습니다.")

if __name__ == "__main__":
    main()
