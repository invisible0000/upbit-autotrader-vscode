"""
컴포넌트 전략 시스템을 위한 데이터베이스 마이그레이션
Component Strategy System Database Migration

기존 Strategy 모델을 LegacyStrategy로 변경하고
새로운 ComponentStrategy 모델을 추가합니다.
"""

from sqlalchemy import text
import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

def migrate_to_component_system(session) -> bool:
    """
    컴포넌트 시스템으로 마이그레이션
    
    1. 기존 strategy 테이블을 legacy_strategy로 변경
    2. 새로운 컴포넌트 테이블들 생성
    3. 관련 외래키 업데이트
    
    Args:
        session: SQLAlchemy 세션
        
    Returns:
        bool: 마이그레이션 성공 여부
    """
    try:
        # 1. 기존 테이블들 백업
        logger.info("🔄 기존 strategy 테이블을 legacy_strategy로 마이그레이션 중...")
        
        # strategy 테이블이 존재하는지 확인
        result = session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='strategy';
        """))
        
        if result.fetchone():
            # 기존 strategy 테이블을 legacy_strategy로 rename
            session.execute(text("ALTER TABLE strategy RENAME TO legacy_strategy;"))
            logger.info("✅ strategy 테이블을 legacy_strategy로 변경 완료")
            
            # 관련 외래키들 업데이트
            _update_foreign_keys(session)
        else:
            logger.info("ℹ️ 기존 strategy 테이블이 없습니다. 새로운 테이블만 생성합니다.")
        
        # 2. 새로운 컴포넌트 테이블들 생성
        _create_component_tables(session)
        
        # 3. 커밋
        session.commit()
        logger.info("✅ 컴포넌트 시스템 마이그레이션 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 컴포넌트 시스템 마이그레이션 실패: {e}")
        session.rollback()
        return False

def _update_foreign_keys(session):
    """외래키 업데이트"""
    try:
        # backtest 테이블의 strategy_id를 legacy_strategy_id로 변경
        logger.info("🔄 외래키 업데이트 중...")
        
        # SQLite는 ALTER COLUMN을 지원하지 않으므로 새 테이블 생성 후 데이터 이동
        session.execute(text("""
            CREATE TABLE backtest_temp (
                id TEXT PRIMARY KEY,
                legacy_strategy_id TEXT,
                component_strategy_id TEXT,
                symbol TEXT NOT NULL,
                portfolio_id TEXT,
                timeframe TEXT NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                initial_capital REAL NOT NULL,
                performance_metrics TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(legacy_strategy_id) REFERENCES legacy_strategy(id),
                FOREIGN KEY(portfolio_id) REFERENCES portfolio(id)
            );
        """))
        
        # 기존 데이터 복사
        session.execute(text("""
            INSERT INTO backtest_temp (id, legacy_strategy_id, symbol, portfolio_id, 
                                     timeframe, start_date, end_date, initial_capital, 
                                     performance_metrics, created_at)
            SELECT id, strategy_id, symbol, portfolio_id, timeframe, start_date, 
                   end_date, initial_capital, performance_metrics, created_at
            FROM backtest;
        """))
        
        # 기존 테이블 삭제 후 새 테이블 rename
        session.execute(text("DROP TABLE backtest;"))
        session.execute(text("ALTER TABLE backtest_temp RENAME TO backtest;"))
        
        logger.info("✅ backtest 테이블 외래키 업데이트 완료")
        
        # portfolio_coin 테이블 업데이트
        session.execute(text("""
            CREATE TABLE portfolio_coin_temp (
                id INTEGER PRIMARY KEY,
                portfolio_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                legacy_strategy_id TEXT,
                component_strategy_id TEXT,
                weight REAL NOT NULL,
                FOREIGN KEY(portfolio_id) REFERENCES portfolio(id),
                FOREIGN KEY(legacy_strategy_id) REFERENCES legacy_strategy(id)
            );
        """))
        
        session.execute(text("""
            INSERT INTO portfolio_coin_temp (id, portfolio_id, symbol, 
                                           legacy_strategy_id, weight)
            SELECT id, portfolio_id, symbol, strategy_id, weight
            FROM portfolio_coin;
        """))
        
        session.execute(text("DROP TABLE portfolio_coin;"))
        session.execute(text("ALTER TABLE portfolio_coin_temp RENAME TO portfolio_coin;"))
        
        logger.info("✅ portfolio_coin 테이블 외래키 업데이트 완료")
        
        # trading_session 테이블 업데이트 (만약 존재한다면)
        result = session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='trading_session';
        """))
        
        if result.fetchone():
            session.execute(text("""
                CREATE TABLE trading_session_temp (
                    id TEXT PRIMARY KEY,
                    legacy_strategy_id TEXT,
                    component_strategy_id TEXT,
                    symbol TEXT NOT NULL,
                    status TEXT NOT NULL,
                    amount REAL NOT NULL,
                    risk_params TEXT NOT NULL,
                    created_at DATETIME,
                    FOREIGN KEY(legacy_strategy_id) REFERENCES legacy_strategy(id)
                );
            """))
            
            session.execute(text("""
                INSERT INTO trading_session_temp (id, legacy_strategy_id, symbol, 
                                                status, amount, risk_params, created_at)
                SELECT id, strategy_id, symbol, status, amount, risk_params, created_at
                FROM trading_session;
            """))
            
            session.execute(text("DROP TABLE trading_session;"))
            session.execute(text("ALTER TABLE trading_session_temp RENAME TO trading_session;"))
            
            logger.info("✅ trading_session 테이블 외래키 업데이트 완료")
        
    except Exception as e:
        logger.error(f"❌ 외래키 업데이트 실패: {e}")
        raise

def _create_component_tables(session):
    """새로운 컴포넌트 테이블들 생성"""
    try:
        logger.info("🔄 컴포넌트 테이블들 생성 중...")
        
        # ComponentStrategy 테이블 생성
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS component_strategy (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                triggers TEXT NOT NULL,
                conditions TEXT,
                actions TEXT NOT NULL,
                tags TEXT,
                category TEXT,
                difficulty TEXT DEFAULT 'beginner',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                is_template BOOLEAN NOT NULL DEFAULT 0,
                performance_metrics TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # StrategyExecution 테이블 생성
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS strategy_execution (
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
        """))
        
        # StrategyTemplate 테이블 생성
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS strategy_template (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                template_data TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty TEXT NOT NULL DEFAULT 'beginner',
                tags TEXT,
                usage_count INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # ComponentConfiguration 테이블 생성
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS component_configuration (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                component_type TEXT NOT NULL,
                component_name TEXT NOT NULL,
                configuration TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 1,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
            );
        """))
        
        logger.info("✅ 컴포넌트 테이블들 생성 완료")
        
        # 샘플 템플릿 데이터 삽입
        _insert_sample_templates(session)
        
    except Exception as e:
        logger.error(f"❌ 컴포넌트 테이블 생성 실패: {e}")
        raise

def _insert_sample_templates(session):
    """샘플 전략 템플릿 데이터 삽입"""
    try:
        logger.info("🔄 샘플 전략 템플릿 삽입 중...")
        
        sample_templates = [
            {
                'id': 'template_basic_buy',
                'name': '기본 매수 전략',
                'description': '가격 변동을 감지하여 매수하는 기본 전략',
                'template_data': '''{
                    "triggers": [
                        {
                            "type": "price_change",
                            "config": {"threshold": -5, "timeframe": "1h"}
                        }
                    ],
                    "actions": [
                        {
                            "type": "market_buy",
                            "config": {"amount_percent": 10}
                        }
                    ]
                }''',
                'category': 'basic',
                'difficulty': 'beginner'
            },
            {
                'id': 'template_rsi_strategy',
                'name': 'RSI 과매도 전략',
                'description': 'RSI 과매도 구간에서 매수하는 전략',
                'template_data': '''{
                    "triggers": [
                        {
                            "type": "rsi",
                            "config": {"threshold": 30, "period": 14}
                        }
                    ],
                    "actions": [
                        {
                            "type": "market_buy",
                            "config": {"amount_percent": 15}
                        }
                    ]
                }''',
                'category': 'technical',
                'difficulty': 'intermediate'
            }
        ]
        
        for template in sample_templates:
            session.execute(text("""
                INSERT OR IGNORE INTO strategy_template 
                (id, name, description, template_data, category, difficulty)
                VALUES (:id, :name, :description, :template_data, :category, :difficulty)
            """), template)
        
        logger.info("✅ 샘플 전략 템플릿 삽입 완료")
        
    except Exception as e:
        logger.warning(f"⚠️ 샘플 템플릿 삽입 실패 (무시됨): {e}")

def rollback_migration(session) -> bool:
    """
    마이그레이션 롤백 (개발 중에만 사용)
    
    Args:
        session: SQLAlchemy 세션
        
    Returns:
        bool: 롤백 성공 여부
    """
    try:
        logger.warning("🔄 컴포넌트 시스템 마이그레이션 롤백 중...")
        
        # 컴포넌트 테이블들 삭제
        component_tables = [
            'component_configuration',
            'strategy_template', 
            'strategy_execution',
            'component_strategy'
        ]
        
        for table in component_tables:
            session.execute(text(f"DROP TABLE IF EXISTS {table};"))
        
        # legacy_strategy를 다시 strategy로 변경
        result = session.execute(text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='legacy_strategy';
        """))
        
        if result.fetchone():
            session.execute(text("ALTER TABLE legacy_strategy RENAME TO strategy;"))
            logger.info("✅ legacy_strategy를 strategy로 복구 완료")
        
        session.commit()
        logger.warning("⚠️ 컴포넌트 시스템 마이그레이션 롤백 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 마이그레이션 롤백 실패: {e}")
        session.rollback()
        return False
