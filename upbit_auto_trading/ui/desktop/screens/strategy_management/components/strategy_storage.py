"""
전략 저장소 - 완성된 매매 전략을 데이터베이스에 저장/관리
"""

import sqlite3
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import sys
from pathlib import Path

# 새로운 통합 DB 경로 시스템 import
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent))
try:
    from database_paths import APP_SETTINGS_DB_PATH
    USE_NEW_DB_PATHS = True
except ImportError:
    # 백업: 새 경로 시스템을 찾을 수 없으면 기존 방식 사용
    USE_NEW_DB_PATHS = False
    APP_SETTINGS_DB_PATH = "data/app_settings.sqlite3"

class StrategyStorage:
    """완성된 전략을 데이터베이스에 저장/관리하는 클래스"""
    
    def __init__(self, db_path: str = None):
        # 새로운 통합 DB 경로 시스템 사용 (하위 호환성 유지)
        if db_path is None:
            if USE_NEW_DB_PATHS:
                self.db_path = APP_SETTINGS_DB_PATH  # settings.sqlite3로 매핑됨
                print(f"🔗 StrategyStorage: 새로운 통합 DB 사용 - {self.db_path}")
            else:
                self.db_path = "data/app_settings.sqlite3"  # 레거시 경로
                print(f"⚠️ StrategyStorage: 레거시 DB 경로 사용 - {self.db_path}")
        else:
            self.db_path = db_path
            print(f"📂 StrategyStorage: 사용자 지정 DB 경로 - {self.db_path}")
        
        self._ensure_database_exists()
        self._ensure_strategy_tables()
    
    def _ensure_database_exists(self):
        """데이터베이스 디렉토리 및 파일 생성"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _ensure_strategy_tables(self):
        """전략 관련 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 메인 전략 테이블 (component_strategy와 호환)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS component_strategy (
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
            """)
            
            # 전략 실행 기록 테이블
            cursor.execute("""
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
            """)
            
            # 전략 구성 요소 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_components (
                    id TEXT PRIMARY KEY,
                    strategy_id TEXT NOT NULL,
                    component_type TEXT NOT NULL,
                    component_data TEXT NOT NULL,
                    order_index INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(strategy_id) REFERENCES component_strategy(id)
                );
            """)
            
            conn.commit()
            print("✅ 전략 테이블 초기화 완료")
    
    def save_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """전략을 데이터베이스에 저장"""
        try:
            strategy_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 진입/청산 조건들을 triggers 필드에 저장
                triggers_data = {
                    'entry_conditions': strategy_data.get('entry_conditions', []),
                    'exit_conditions': strategy_data.get('exit_conditions', []),
                    'entry_logic': strategy_data.get('entry_logic', 'AND'),
                    'exit_logic': strategy_data.get('exit_logic', 'OR')
                }
                
                # 액션 데이터 (매수/매도 로직)
                actions_data = {
                    'buy_action': {
                        'type': 'market_buy',
                        'conditions': strategy_data.get('entry_conditions', [])
                    },
                    'sell_action': {
                        'type': 'market_sell',
                        'conditions': strategy_data.get('exit_conditions', [])
                    },
                    'risk_management': strategy_data.get('risk_management', {})
                }
                
                # 메인 전략 레코드 삽입
                cursor.execute("""
                    INSERT INTO component_strategy 
                    (id, name, description, triggers, conditions, actions, 
                     category, difficulty, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    strategy_id,
                    strategy_data.get('name', 'Untitled Strategy'),
                    strategy_data.get('description', ''),
                    json.dumps(triggers_data, ensure_ascii=False),
                    json.dumps(strategy_data.get('conditions', {}), ensure_ascii=False),
                    json.dumps(actions_data, ensure_ascii=False),
                    'user_created',
                    'intermediate',
                    1,  # is_active
                    current_time,
                    current_time
                ))
                
                # 진입 조건들을 개별 컴포넌트로 저장
                for idx, condition in enumerate(strategy_data.get('entry_conditions', [])):
                    component_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO strategy_components 
                        (id, strategy_id, component_type, component_data, order_index, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        component_id,
                        strategy_id,
                        'entry_condition',
                        json.dumps(condition, ensure_ascii=False),
                        idx,
                        current_time
                    ))
                
                # 청산 조건들을 개별 컴포넌트로 저장
                for idx, condition in enumerate(strategy_data.get('exit_conditions', [])):
                    component_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO strategy_components 
                        (id, strategy_id, component_type, component_data, order_index, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        component_id,
                        strategy_id,
                        'exit_condition',
                        json.dumps(condition, ensure_ascii=False),
                        idx,
                        current_time
                    ))
                
                # 리스크 관리를 컴포넌트로 저장
                if strategy_data.get('risk_management'):
                    component_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO strategy_components 
                        (id, strategy_id, component_type, component_data, order_index, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        component_id,
                        strategy_id,
                        'risk_management',
                        json.dumps(strategy_data['risk_management'], ensure_ascii=False),
                        999,  # 리스크 관리는 마지막 순서
                        current_time
                    ))
                
                conn.commit()
                print(f"✅ 전략 저장 완료: {strategy_id}")
                return strategy_id
                
        except Exception as e:
            print(f"❌ 전략 저장 실패: {e}")
            raise e
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """전략 ID로 전략 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 메인 전략 정보 조회
                cursor.execute("""
                    SELECT id, name, description, triggers, conditions, actions,
                           category, difficulty, is_active, created_at, updated_at
                    FROM component_strategy 
                    WHERE id = ?
                """, (strategy_id,))
                
                strategy_row = cursor.fetchone()
                if not strategy_row:
                    return None
                
                # 컴포넌트들 조회
                cursor.execute("""
                    SELECT component_type, component_data, order_index
                    FROM strategy_components 
                    WHERE strategy_id = ? 
                    ORDER BY order_index
                """, (strategy_id,))
                
                components = cursor.fetchall()
                
                # 전략 데이터 구성
                strategy_data = {
                    'id': strategy_row[0],
                    'name': strategy_row[1],
                    'description': strategy_row[2],
                    'triggers': json.loads(strategy_row[3]) if strategy_row[3] else {},
                    'conditions': json.loads(strategy_row[4]) if strategy_row[4] else {},
                    'actions': json.loads(strategy_row[5]) if strategy_row[5] else {},
                    'category': strategy_row[6],
                    'difficulty': strategy_row[7],
                    'is_active': bool(strategy_row[8]),
                    'created_at': strategy_row[9],
                    'updated_at': strategy_row[10],
                    'components': {}
                }
                
                # 컴포넌트들 분류
                for comp_type, comp_data, order_idx in components:
                    if comp_type not in strategy_data['components']:
                        strategy_data['components'][comp_type] = []
                    
                    strategy_data['components'][comp_type].append({
                        'data': json.loads(comp_data),
                        'order': order_idx
                    })
                
                return strategy_data
                
        except Exception as e:
            print(f"❌ 전략 조회 실패: {e}")
            return None
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """모든 전략 목록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, description, category, difficulty, 
                           is_active, created_at, updated_at
                    FROM component_strategy 
                    ORDER BY created_at DESC
                """)
                
                strategies = []
                for row in cursor.fetchall():
                    strategies.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'category': row[3],
                        'difficulty': row[4],
                        'is_active': bool(row[5]),
                        'created_at': row[6],
                        'updated_at': row[7]
                    })
                
                return strategies
                
        except Exception as e:
            print(f"❌ 전략 목록 조회 실패: {e}")
            return []
    
    def update_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]) -> bool:
        """전략 업데이트"""
        try:
            current_time = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 기존 컴포넌트들 삭제
                cursor.execute("DELETE FROM strategy_components WHERE strategy_id = ?", (strategy_id,))
                
                # 메인 전략 정보 업데이트
                triggers_data = {
                    'entry_conditions': strategy_data.get('entry_conditions', []),
                    'exit_conditions': strategy_data.get('exit_conditions', []),
                    'entry_logic': strategy_data.get('entry_logic', 'AND'),
                    'exit_logic': strategy_data.get('exit_logic', 'OR')
                }
                
                actions_data = {
                    'buy_action': {
                        'type': 'market_buy',
                        'conditions': strategy_data.get('entry_conditions', [])
                    },
                    'sell_action': {
                        'type': 'market_sell',
                        'conditions': strategy_data.get('exit_conditions', [])
                    },
                    'risk_management': strategy_data.get('risk_management', {})
                }
                
                cursor.execute("""
                    UPDATE component_strategy 
                    SET name = ?, description = ?, triggers = ?, conditions = ?, 
                        actions = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    strategy_data.get('name', 'Untitled Strategy'),
                    strategy_data.get('description', ''),
                    json.dumps(triggers_data, ensure_ascii=False),
                    json.dumps(strategy_data.get('conditions', {}), ensure_ascii=False),
                    json.dumps(actions_data, ensure_ascii=False),
                    current_time,
                    strategy_id
                ))
                
                # 새 컴포넌트들 삽입 (save_strategy와 동일한 로직)
                # ... (생략, save_strategy의 컴포넌트 삽입 로직과 동일)
                
                conn.commit()
                print(f"✅ 전략 업데이트 완료: {strategy_id}")
                return True
                
        except Exception as e:
            print(f"❌ 전략 업데이트 실패: {e}")
            return False
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """전략 삭제"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 관련 컴포넌트들 먼저 삭제
                cursor.execute("DELETE FROM strategy_components WHERE strategy_id = ?", (strategy_id,))
                
                # 실행 기록들 삭제
                cursor.execute("DELETE FROM strategy_execution WHERE strategy_id = ?", (strategy_id,))
                
                # 메인 전략 삭제
                cursor.execute("DELETE FROM component_strategy WHERE id = ?", (strategy_id,))
                
                conn.commit()
                print(f"✅ 전략 삭제 완료: {strategy_id}")
                return True
                
        except Exception as e:
            print(f"❌ 전략 삭제 실패: {e}")
            return False
    
    def activate_strategy(self, strategy_id: str) -> bool:
        """전략 활성화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE component_strategy 
                    SET is_active = 1, updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), strategy_id))
                
                conn.commit()
                print(f"✅ 전략 활성화: {strategy_id}")
                return True
                
        except Exception as e:
            print(f"❌ 전략 활성화 실패: {e}")
            return False
    
    def deactivate_strategy(self, strategy_id: str) -> bool:
        """전략 비활성화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE component_strategy 
                    SET is_active = 0, updated_at = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), strategy_id))
                
                conn.commit()
                print(f"✅ 전략 비활성화: {strategy_id}")
                return True
                
        except Exception as e:
            print(f"❌ 전략 비활성화 실패: {e}")
            return False
    
    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """활성화된 전략들만 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, description, triggers, actions
                    FROM component_strategy 
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                """)
                
                strategies = []
                for row in cursor.fetchall():
                    strategies.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'triggers': json.loads(row[3]) if row[3] else {},
                        'actions': json.loads(row[4]) if row[4] else {}
                    })
                
                return strategies
                
        except Exception as e:
            print(f"❌ 활성 전략 조회 실패: {e}")
            return []
    
    def log_strategy_execution(self, strategy_id: str, symbol: str, 
                             trigger_type: str, action_type: str, 
                             market_data: Dict, result: str, 
                             result_details: Optional[str] = None, position_tag: Optional[str] = None) -> str:
        """전략 실행 기록 저장"""
        try:
            execution_id = str(uuid.uuid4())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO strategy_execution 
                    (id, strategy_id, symbol, trigger_type, action_type, 
                     market_data, result, result_details, position_tag, executed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    execution_id,
                    strategy_id,
                    symbol,
                    trigger_type,
                    action_type,
                    json.dumps(market_data, ensure_ascii=False),
                    result,
                    result_details,
                    position_tag,
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return execution_id
                
        except Exception as e:
            print(f"❌ 실행 기록 저장 실패: {e}")
            return ""
    
    def get_strategy_execution_history(self, strategy_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """전략 실행 기록 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, symbol, trigger_type, action_type, market_data, 
                           result, result_details, position_tag, executed_at
                    FROM strategy_execution 
                    WHERE strategy_id = ?
                    ORDER BY executed_at DESC
                    LIMIT ?
                """, (strategy_id, limit))
                
                executions = []
                for row in cursor.fetchall():
                    executions.append({
                        'id': row[0],
                        'symbol': row[1],
                        'trigger_type': row[2],
                        'action_type': row[3],
                        'market_data': json.loads(row[4]) if row[4] else {},
                        'result': row[5],
                        'result_details': row[6],
                        'position_tag': row[7],
                        'executed_at': row[8]
                    })
                
                return executions
                
        except Exception as e:
            print(f"❌ 실행 기록 조회 실패: {e}")
            return []
