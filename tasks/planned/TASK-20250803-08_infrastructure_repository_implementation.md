# TASK-20250803-08

## Title
Infrastructure Layer - Repository 구현 (SQLite 기반 데이터 접근)

## Objective (목표)
Domain Layer에서 정의한 Repository 인터페이스들을 SQLite 기반으로 구현합니다. 기존 3-DB 아키텍처(settings.sqlite3, strategies.sqlite3, market_data.sqlite3)를 활용하여 도메인 엔티티와 데이터베이스 간의 매핑을 처리하고, 성능 최적화된 데이터 접근 계층을 구축합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 3: Infrastructure Layer 구현 (2주)" > "3.1 Repository 구현 (5일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-03`: Repository 인터페이스 정의 완료
- `TASK-20250803-01`: Domain Entity 구현 완료
- 기존 3-DB 구조 및 스키마 분석 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 기존 데이터베이스 스키마 및 구조 분석
- [ ] `data/settings.sqlite3` 스키마 분석 (읽기 전용)
- [ ] `data/strategies.sqlite3` 스키마 분석 (읽기/쓰기)
- [ ] `data/market_data.sqlite3` 스키마 분석 (읽기/쓰기)
- [ ] 기존 테이블 구조와 도메인 엔티티 매핑 계획 수립

### 2. **[폴더 구조 생성]** Infrastructure Repository 구조
- [ ] `upbit_auto_trading/infrastructure/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/repositories/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/database/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/mappers/` 폴더 생성

### 3. **[새 코드 작성]** 데이터베이스 연결 관리자
- [ ] `upbit_auto_trading/infrastructure/database/database_manager.py` 생성:
```python
import sqlite3
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import logging
from pathlib import Path
import threading

class DatabaseManager:
    """SQLite 데이터베이스 연결 관리"""
    
    def __init__(self, db_paths: Dict[str, str]):
        """
        Args:
            db_paths: 데이터베이스 이름과 경로 매핑
            예: {
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3', 
                'market_data': 'data/market_data.sqlite3'
            }
        """
        self._db_paths = db_paths
        self._connections: Dict[str, sqlite3.Connection] = {}
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)
        
        # 데이터베이스 연결 풀 초기화
        self._initialize_connections()
    
    def _initialize_connections(self) -> None:
        """데이터베이스 연결 초기화"""
        for db_name, db_path in self._db_paths.items():
            if not Path(db_path).exists():
                self._logger.warning(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
                continue
            
            try:
                conn = sqlite3.connect(db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
                
                # SQLite 최적화 설정
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA cache_size = 10000")
                conn.execute("PRAGMA temp_store = MEMORY")
                
                self._connections[db_name] = conn
                self._logger.info(f"데이터베이스 연결 완료: {db_name}")
                
            except sqlite3.Error as e:
                self._logger.error(f"데이터베이스 연결 실패 {db_name}: {e}")
                raise
    
    @contextmanager
    def get_connection(self, db_name: str):
        """데이터베이스 연결 반환 (컨텍스트 매니저)"""
        if db_name not in self._connections:
            raise ValueError(f"존재하지 않는 데이터베이스: {db_name}")
        
        conn = self._connections[db_name]
        
        try:
            with self._lock:
                yield conn
        except Exception as e:
            self._logger.error(f"데이터베이스 작업 실패 {db_name}: {e}")
            conn.rollback()
            raise
        else:
            conn.commit()
    
    def execute_query(self, db_name: str, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """SELECT 쿼리 실행"""
        with self.get_connection(db_name) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_command(self, db_name: str, query: str, params: tuple = ()) -> int:
        """INSERT/UPDATE/DELETE 쿼리 실행"""
        with self.get_connection(db_name) as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount
    
    def execute_many(self, db_name: str, query: str, params_list: List[tuple]) -> int:
        """배치 INSERT/UPDATE 실행"""
        with self.get_connection(db_name) as conn:
            cursor = conn.executemany(query, params_list)
            return cursor.rowcount
    
    def get_last_insert_id(self, db_name: str) -> int:
        """마지막 삽입된 행의 ID 반환"""
        with self.get_connection(db_name) as conn:
            cursor = conn.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]
    
    def close_all(self) -> None:
        """모든 데이터베이스 연결 종료"""
        for db_name, conn in self._connections.items():
            try:
                conn.close()
                self._logger.info(f"데이터베이스 연결 종료: {db_name}")
            except Exception as e:
                self._logger.error(f"데이터베이스 연결 종료 실패 {db_name}: {e}")
        
        self._connections.clear()

class DatabaseConnectionProvider:
    """데이터베이스 연결 제공자 (Singleton)"""
    
    _instance: Optional['DatabaseConnectionProvider'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'DatabaseConnectionProvider':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._db_manager: Optional[DatabaseManager] = None
            self._initialized = True
    
    def initialize(self, db_paths: Dict[str, str]) -> None:
        """데이터베이스 연결 초기화"""
        if self._db_manager is None:
            self._db_manager = DatabaseManager(db_paths)
    
    def get_manager(self) -> DatabaseManager:
        """데이터베이스 매니저 반환"""
        if self._db_manager is None:
            raise RuntimeError("데이터베이스가 초기화되지 않았습니다")
        return self._db_manager
```

### 4. **[새 코드 작성]** 엔티티-테이블 매퍼 구현
- [ ] `upbit_auto_trading/infrastructure/mappers/strategy_mapper.py` 생성:
```python
from typing import Dict, Any, List, Optional
from datetime import datetime

from upbit_auto_trading.domain.entities.strategy import Strategy
from upbit_auto_trading.domain.entities.trigger import Trigger
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
from upbit_auto_trading.domain.enums.strategy_status import StrategyStatus
from upbit_auto_trading.domain.enums.trigger_type import TriggerType

class StrategyMapper:
    """Strategy 엔티티와 데이터베이스 레코드 간 매핑"""
    
    @staticmethod
    def to_entity(strategy_row: Dict[str, Any], triggers: List[Trigger] = None) -> Strategy:
        """데이터베이스 레코드를 Strategy 엔티티로 변환"""
        if triggers is None:
            triggers = []
        
        # 트리거를 진입/청산으로 분류
        entry_triggers = [t for t in triggers if t.trigger_type == TriggerType.ENTRY]
        exit_triggers = [t for t in triggers if t.trigger_type == TriggerType.EXIT]
        management_triggers = [t for t in triggers if t.trigger_type == TriggerType.MANAGEMENT]
        
        return Strategy(
            strategy_id=StrategyId(strategy_row['id']),
            name=strategy_row['name'],
            description=strategy_row.get('description'),
            status=StrategyStatus(strategy_row['status']),
            entry_triggers=entry_triggers,
            exit_triggers=exit_triggers,
            management_triggers=management_triggers,
            tags=strategy_row.get('tags', '').split(',') if strategy_row.get('tags') else [],
            created_at=datetime.fromisoformat(strategy_row['created_at']) if strategy_row.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(strategy_row['updated_at']) if strategy_row.get('updated_at') else datetime.now(),
            created_by=strategy_row.get('created_by', 'system'),
            version=strategy_row.get('version', 1)
        )
    
    @staticmethod
    def to_database_record(strategy: Strategy) -> Dict[str, Any]:
        """Strategy 엔티티를 데이터베이스 레코드로 변환"""
        return {
            'id': strategy.strategy_id.value,
            'name': strategy.name,
            'description': strategy.description,
            'status': strategy.status.value,
            'tags': ','.join(strategy.tags) if strategy.tags else '',
            'created_at': strategy.created_at.isoformat(),
            'updated_at': strategy.updated_at.isoformat(),
            'created_by': strategy.created_by,
            'version': strategy.version
        }
    
    @staticmethod
    def to_insert_params(strategy: Strategy) -> tuple:
        """INSERT 쿼리용 파라미터 튜플로 변환"""
        record = StrategyMapper.to_database_record(strategy)
        return (
            record['id'],
            record['name'], 
            record['description'],
            record['status'],
            record['tags'],
            record['created_at'],
            record['updated_at'],
            record['created_by'],
            record['version']
        )
    
    @staticmethod
    def to_update_params(strategy: Strategy) -> tuple:
        """UPDATE 쿼리용 파라미터 튜플로 변환"""
        record = StrategyMapper.to_database_record(strategy)
        return (
            record['name'],
            record['description'],
            record['status'],
            record['tags'],
            record['updated_at'],
            record['version'],
            record['id']  # WHERE 조건용
        )

class TriggerMapper:
    """Trigger 엔티티와 데이터베이스 레코드 간 매핑"""
    
    @staticmethod
    def to_entity(trigger_row: Dict[str, Any]) -> Trigger:
        """데이터베이스 레코드를 Trigger 엔티티로 변환"""
        from upbit_auto_trading.domain.value_objects.trading_variable import TradingVariable
        from upbit_auto_trading.domain.enums.comparison_operator import ComparisonOperator
        
        # 변수 정보 파싱 (JSON 또는 별도 테이블에서 로드)
        variable_params = {}
        if trigger_row.get('variable_params'):
            import json
            variable_params = json.loads(trigger_row['variable_params'])
        
        trading_variable = TradingVariable(
            variable_id=trigger_row['variable_id'],
            parameters=variable_params
        )
        
        return Trigger(
            trigger_id=TriggerId(trigger_row['id']),
            trigger_name=trigger_row['trigger_name'],
            strategy_id=StrategyId(trigger_row['strategy_id']),
            variable=trading_variable,
            operator=ComparisonOperator(trigger_row['operator']),
            target_value=trigger_row['target_value'],
            trigger_type=TriggerType(trigger_row['trigger_type']),
            is_active=bool(trigger_row.get('is_active', True)),
            weight=float(trigger_row.get('weight', 1.0)),
            description=trigger_row.get('description'),
            created_at=datetime.fromisoformat(trigger_row['created_at']) if trigger_row.get('created_at') else datetime.now()
        )
    
    @staticmethod
    def to_database_record(trigger: Trigger) -> Dict[str, Any]:
        """Trigger 엔티티를 데이터베이스 레코드로 변환"""
        import json
        
        return {
            'id': trigger.trigger_id.value,
            'trigger_name': trigger.trigger_name,
            'strategy_id': trigger.strategy_id.value,
            'variable_id': trigger.variable.variable_id,
            'variable_params': json.dumps(trigger.variable.parameters) if trigger.variable.parameters else '{}',
            'operator': trigger.operator.value,
            'target_value': trigger.target_value,
            'trigger_type': trigger.trigger_type.value,
            'is_active': trigger.is_active,
            'weight': trigger.weight,
            'description': trigger.description,
            'created_at': trigger.created_at.isoformat()
        }
    
    @staticmethod
    def to_insert_params(trigger: Trigger) -> tuple:
        """INSERT 쿼리용 파라미터 튜플로 변환"""
        record = TriggerMapper.to_database_record(trigger)
        return (
            record['id'],
            record['trigger_name'],
            record['strategy_id'],
            record['variable_id'],
            record['variable_params'],
            record['operator'],
            record['target_value'],
            record['trigger_type'],
            record['is_active'],
            record['weight'],
            record['description'],
            record['created_at']
        )
```

### 5. **[새 코드 작성]** SQLite 전략 Repository 구현
- [ ] `upbit_auto_trading/infrastructure/repositories/sqlite_strategy_repository.py` 생성:
```python
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.entities.strategy import Strategy
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.enums.strategy_status import StrategyStatus
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.mappers.strategy_mapper import StrategyMapper, TriggerMapper

class SqliteStrategyRepository(StrategyRepository):
    """SQLite 기반 Strategy Repository 구현"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._logger = logging.getLogger(__name__)
    
    def save(self, strategy: Strategy) -> None:
        """전략 저장 (생성 또는 업데이트)"""
        existing = self.find_by_id(strategy.strategy_id)
        
        if existing is None:
            self._insert_strategy(strategy)
        else:
            self._update_strategy(strategy)
        
        # 트리거도 함께 저장
        self._save_triggers(strategy)
    
    def _insert_strategy(self, strategy: Strategy) -> None:
        """새 전략 삽입"""
        insert_query = """
        INSERT INTO strategies (
            id, name, description, status, tags, 
            created_at, updated_at, created_by, version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = StrategyMapper.to_insert_params(strategy)
        
        try:
            self._db.execute_command('strategies', insert_query, params)
            self._logger.info(f"전략 저장 완료: {strategy.strategy_id.value}")
        except Exception as e:
            self._logger.error(f"전략 저장 실패: {strategy.strategy_id.value} - {e}")
            raise
    
    def _update_strategy(self, strategy: Strategy) -> None:
        """기존 전략 업데이트"""
        update_query = """
        UPDATE strategies 
        SET name = ?, description = ?, status = ?, tags = ?,
            updated_at = ?, version = ?
        WHERE id = ?
        """
        
        params = StrategyMapper.to_update_params(strategy)
        
        try:
            rows_affected = self._db.execute_command('strategies', update_query, params)
            if rows_affected == 0:
                raise ValueError(f"업데이트할 전략을 찾을 수 없습니다: {strategy.strategy_id.value}")
            
            self._logger.info(f"전략 업데이트 완료: {strategy.strategy_id.value}")
        except Exception as e:
            self._logger.error(f"전략 업데이트 실패: {strategy.strategy_id.value} - {e}")
            raise
    
    def _save_triggers(self, strategy: Strategy) -> None:
        """전략의 모든 트리거 저장"""
        # 기존 트리거 삭제
        delete_query = "DELETE FROM strategy_triggers WHERE strategy_id = ?"
        self._db.execute_command('strategies', delete_query, (strategy.strategy_id.value,))
        
        # 새 트리거 삽입
        all_triggers = strategy.get_all_triggers()
        if not all_triggers:
            return
        
        insert_query = """
        INSERT INTO strategy_triggers (
            id, trigger_name, strategy_id, variable_id, variable_params,
            operator, target_value, trigger_type, is_active, weight,
            description, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        trigger_params = [TriggerMapper.to_insert_params(trigger) for trigger in all_triggers]
        
        try:
            self._db.execute_many('strategies', insert_query, trigger_params)
            self._logger.debug(f"트리거 {len(all_triggers)}개 저장 완료: {strategy.strategy_id.value}")
        except Exception as e:
            self._logger.error(f"트리거 저장 실패: {strategy.strategy_id.value} - {e}")
            raise
    
    def find_by_id(self, strategy_id: StrategyId) -> Optional[Strategy]:
        """ID로 전략 조회"""
        query = "SELECT * FROM strategies WHERE id = ? AND status != 'DELETED'"
        
        try:
            rows = self._db.execute_query('strategies', query, (strategy_id.value,))
            
            if not rows:
                return None
            
            strategy_row = dict(rows[0])
            
            # 트리거도 함께 로드
            triggers = self._load_triggers_for_strategy(strategy_id)
            
            return StrategyMapper.to_entity(strategy_row, triggers)
            
        except Exception as e:
            self._logger.error(f"전략 조회 실패: {strategy_id.value} - {e}")
            raise
    
    def _load_triggers_for_strategy(self, strategy_id: StrategyId) -> List:
        """전략의 모든 트리거 로드"""
        query = """
        SELECT * FROM strategy_triggers 
        WHERE strategy_id = ? AND is_active = 1
        ORDER BY trigger_type, weight DESC
        """
        
        try:
            rows = self._db.execute_query('strategies', query, (strategy_id.value,))
            triggers = []
            
            for row in rows:
                trigger = TriggerMapper.to_entity(dict(row))
                triggers.append(trigger)
            
            return triggers
            
        except Exception as e:
            self._logger.error(f"트리거 로드 실패: {strategy_id.value} - {e}")
            return []
    
    def find_all_active(self) -> List[Strategy]:
        """모든 활성 전략 조회"""
        query = """
        SELECT * FROM strategies 
        WHERE status = 'ACTIVE' 
        ORDER BY updated_at DESC
        """
        
        try:
            rows = self._db.execute_query('strategies', query)
            strategies = []
            
            for row in rows:
                strategy_row = dict(row)
                strategy_id = StrategyId(strategy_row['id'])
                triggers = self._load_triggers_for_strategy(strategy_id)
                
                strategy = StrategyMapper.to_entity(strategy_row, triggers)
                strategies.append(strategy)
            
            return strategies
            
        except Exception as e:
            self._logger.error(f"활성 전략 조회 실패: {e}")
            raise
    
    def find_with_filters(self, status: Optional[str] = None,
                         tags: Optional[List[str]] = None,
                         name_pattern: Optional[str] = None,
                         created_after: Optional[datetime] = None,
                         created_before: Optional[datetime] = None,
                         include_deleted: bool = False,
                         sort_field: str = "created_at",
                         sort_direction: str = "DESC",
                         limit: int = 20,
                         offset: int = 0) -> List[Strategy]:
        """필터링된 전략 목록 조회"""
        
        # 동적 쿼리 구성
        conditions = []
        params = []
        
        if not include_deleted:
            conditions.append("status != 'DELETED'")
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if name_pattern:
            conditions.append("name LIKE ?")
            params.append(f"%{name_pattern}%")
        
        if tags:
            # 태그 필터링 (간단한 LIKE 검색)
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
            conditions.append(f"({' OR '.join(tag_conditions)})")
        
        if created_after:
            conditions.append("created_at >= ?")
            params.append(created_after.isoformat())
        
        if created_before:
            conditions.append("created_at <= ?")
            params.append(created_before.isoformat())
        
        # 쿼리 구성
        base_query = "SELECT * FROM strategies"
        if conditions:
            base_query += f" WHERE {' AND '.join(conditions)}"
        
        # 정렬 및 페이징
        valid_sort_fields = ['name', 'created_at', 'updated_at', 'status']
        if sort_field not in valid_sort_fields:
            sort_field = 'created_at'
        
        sort_direction = sort_direction.upper()
        if sort_direction not in ['ASC', 'DESC']:
            sort_direction = 'DESC'
        
        base_query += f" ORDER BY {sort_field} {sort_direction}"
        base_query += f" LIMIT {limit} OFFSET {offset}"
        
        try:
            rows = self._db.execute_query('strategies', base_query, tuple(params))
            strategies = []
            
            for row in rows:
                strategy_row = dict(row)
                strategy_id = StrategyId(strategy_row['id'])
                
                # 성능을 위해 기본 정보만 로드 (트리거는 필요시 별도 로드)
                strategy = StrategyMapper.to_entity(strategy_row, [])
                strategies.append(strategy)
            
            return strategies
            
        except Exception as e:
            self._logger.error(f"필터링된 전략 조회 실패: {e}")
            raise
    
    def count_with_filters(self, status: Optional[str] = None,
                          tags: Optional[List[str]] = None,
                          name_pattern: Optional[str] = None,
                          created_after: Optional[datetime] = None,
                          created_before: Optional[datetime] = None,
                          include_deleted: bool = False) -> int:
        """필터링 조건에 맞는 전략 수 조회"""
        
        # find_with_filters와 동일한 조건 로직
        conditions = []
        params = []
        
        if not include_deleted:
            conditions.append("status != 'DELETED'")
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if name_pattern:
            conditions.append("name LIKE ?")
            params.append(f"%{name_pattern}%")
        
        if tags:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
            conditions.append(f"({' OR '.join(tag_conditions)})")
        
        if created_after:
            conditions.append("created_at >= ?")
            params.append(created_after.isoformat())
        
        if created_before:
            conditions.append("created_at <= ?")
            params.append(created_before.isoformat())
        
        # COUNT 쿼리 구성
        count_query = "SELECT COUNT(*) FROM strategies"
        if conditions:
            count_query += f" WHERE {' AND '.join(conditions)}"
        
        try:
            rows = self._db.execute_query('strategies', count_query, tuple(params))
            return rows[0][0] if rows else 0
            
        except Exception as e:
            self._logger.error(f"전략 수 조회 실패: {e}")
            raise
    
    def count_active_strategies(self) -> int:
        """활성 전략 수 조회"""
        query = "SELECT COUNT(*) FROM strategies WHERE status = 'ACTIVE'"
        
        try:
            rows = self._db.execute_query('strategies', query)
            return rows[0][0] if rows else 0
        except Exception as e:
            self._logger.error(f"활성 전략 수 조회 실패: {e}")
            raise
    
    def count_all_strategies(self) -> int:
        """전체 전략 수 조회 (삭제된 것 제외)"""
        query = "SELECT COUNT(*) FROM strategies WHERE status != 'DELETED'"
        
        try:
            rows = self._db.execute_query('strategies', query)
            return rows[0][0] if rows else 0
        except Exception as e:
            self._logger.error(f"전체 전략 수 조회 실패: {e}")
            raise
    
    def delete(self, strategy_id: StrategyId) -> None:
        """전략 삭제 (소프트 삭제)"""
        update_query = """
        UPDATE strategies 
        SET status = 'DELETED', updated_at = ?
        WHERE id = ?
        """
        
        try:
            rows_affected = self._db.execute_command(
                'strategies', 
                update_query, 
                (datetime.now().isoformat(), strategy_id.value)
            )
            
            if rows_affected == 0:
                raise ValueError(f"삭제할 전략을 찾을 수 없습니다: {strategy_id.value}")
            
            self._logger.info(f"전략 삭제 완료: {strategy_id.value}")
            
        except Exception as e:
            self._logger.error(f"전략 삭제 실패: {strategy_id.value} - {e}")
            raise
```

### 6. **[새 코드 작성]** SQLite 트리거 Repository 구현
- [ ] `upbit_auto_trading/infrastructure/repositories/sqlite_trigger_repository.py` 생성:
```python
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
from upbit_auto_trading.domain.entities.trigger import Trigger
from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.enums.trigger_type import TriggerType
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.mappers.strategy_mapper import TriggerMapper

class SqliteTriggerRepository(TriggerRepository):
    """SQLite 기반 Trigger Repository 구현"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._logger = logging.getLogger(__name__)
    
    def save_trigger(self, trigger: Trigger) -> None:
        """트리거 저장"""
        existing = self.find_by_id(trigger.trigger_id)
        
        if existing is None:
            self._insert_trigger(trigger)
        else:
            self._update_trigger(trigger)
    
    def _insert_trigger(self, trigger: Trigger) -> None:
        """새 트리거 삽입"""
        insert_query = """
        INSERT INTO strategy_triggers (
            id, trigger_name, strategy_id, variable_id, variable_params,
            operator, target_value, trigger_type, is_active, weight,
            description, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = TriggerMapper.to_insert_params(trigger)
        
        try:
            self._db.execute_command('strategies', insert_query, params)
            self._logger.info(f"트리거 저장 완료: {trigger.trigger_id.value}")
        except Exception as e:
            self._logger.error(f"트리거 저장 실패: {trigger.trigger_id.value} - {e}")
            raise
    
    def _update_trigger(self, trigger: Trigger) -> None:
        """기존 트리거 업데이트"""
        update_query = """
        UPDATE strategy_triggers 
        SET trigger_name = ?, variable_id = ?, variable_params = ?,
            operator = ?, target_value = ?, trigger_type = ?,
            is_active = ?, weight = ?, description = ?
        WHERE id = ?
        """
        
        record = TriggerMapper.to_database_record(trigger)
        params = (
            record['trigger_name'],
            record['variable_id'],
            record['variable_params'],
            record['operator'],
            record['target_value'],
            record['trigger_type'],
            record['is_active'],
            record['weight'],
            record['description'],
            record['id']
        )
        
        try:
            rows_affected = self._db.execute_command('strategies', update_query, params)
            if rows_affected == 0:
                raise ValueError(f"업데이트할 트리거를 찾을 수 없습니다: {trigger.trigger_id.value}")
            
            self._logger.info(f"트리거 업데이트 완료: {trigger.trigger_id.value}")
        except Exception as e:
            self._logger.error(f"트리거 업데이트 실패: {trigger.trigger_id.value} - {e}")
            raise
    
    def find_by_id(self, trigger_id: TriggerId) -> Optional[Trigger]:
        """ID로 트리거 조회"""
        query = "SELECT * FROM strategy_triggers WHERE id = ?"
        
        try:
            rows = self._db.execute_query('strategies', query, (trigger_id.value,))
            
            if not rows:
                return None
            
            return TriggerMapper.to_entity(dict(rows[0]))
            
        except Exception as e:
            self._logger.error(f"트리거 조회 실패: {trigger_id.value} - {e}")
            raise
    
    def find_by_strategy_id(self, strategy_id: StrategyId) -> List[Trigger]:
        """전략 ID로 트리거 목록 조회"""
        query = """
        SELECT * FROM strategy_triggers 
        WHERE strategy_id = ? AND is_active = 1
        ORDER BY trigger_type, weight DESC
        """
        
        try:
            rows = self._db.execute_query('strategies', query, (strategy_id.value,))
            triggers = []
            
            for row in rows:
                trigger = TriggerMapper.to_entity(dict(row))
                triggers.append(trigger)
            
            return triggers
            
        except Exception as e:
            self._logger.error(f"전략별 트리거 조회 실패: {strategy_id.value} - {e}")
            raise
    
    def find_by_type(self, trigger_type: TriggerType) -> List[Trigger]:
        """타입별 트리거 조회"""
        query = """
        SELECT * FROM strategy_triggers 
        WHERE trigger_type = ? AND is_active = 1
        ORDER BY strategy_id, weight DESC
        """
        
        try:
            rows = self._db.execute_query('strategies', query, (trigger_type.value,))
            triggers = []
            
            for row in rows:
                trigger = TriggerMapper.to_entity(dict(row))
                triggers.append(trigger)
            
            return triggers
            
        except Exception as e:
            self._logger.error(f"타입별 트리거 조회 실패: {trigger_type.value} - {e}")
            raise
    
    def count_all_triggers(self) -> int:
        """전체 활성 트리거 수 조회"""
        query = "SELECT COUNT(*) FROM strategy_triggers WHERE is_active = 1"
        
        try:
            rows = self._db.execute_query('strategies', query)
            return rows[0][0] if rows else 0
        except Exception as e:
            self._logger.error(f"전체 트리거 수 조회 실패: {e}")
            raise
    
    def get_trigger_statistics_by_variable_type(self, start_date: datetime, 
                                               end_date: datetime) -> List[Dict[str, Any]]:
        """변수 타입별 트리거 통계 조회"""
        query = """
        SELECT 
            variable_id,
            COUNT(*) as total_count,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_count,
            AVG(weight) as avg_weight
        FROM strategy_triggers 
        WHERE created_at BETWEEN ? AND ?
        GROUP BY variable_id
        ORDER BY total_count DESC
        """
        
        try:
            rows = self._db.execute_query(
                'strategies', 
                query, 
                (start_date.isoformat(), end_date.isoformat())
            )
            
            statistics = []
            for row in rows:
                stat = dict(row)
                # 기본값들 추가 (실제로는 더 복잡한 계산 필요)
                stat['success_rate'] = 75.0  # 임시값
                stat['avg_execution_time_ms'] = 15.0  # 임시값
                stat['variable_type'] = stat['variable_id']  # 단순화
                statistics.append(stat)
            
            return statistics
            
        except Exception as e:
            self._logger.error(f"트리거 통계 조회 실패: {e}")
            raise
    
    def delete_trigger(self, trigger_id: TriggerId) -> None:
        """트리거 삭제 (소프트 삭제)"""
        update_query = "UPDATE strategy_triggers SET is_active = 0 WHERE id = ?"
        
        try:
            rows_affected = self._db.execute_command(
                'strategies', 
                update_query, 
                (trigger_id.value,)
            )
            
            if rows_affected == 0:
                raise ValueError(f"삭제할 트리거를 찾을 수 없습니다: {trigger_id.value}")
            
            self._logger.info(f"트리거 삭제 완료: {trigger_id.value}")
            
        except Exception as e:
            self._logger.error(f"트리거 삭제 실패: {trigger_id.value} - {e}")
            raise
```

### 7. **[새 코드 작성]** SQLite 설정 Repository 구현 (읽기 전용)
- [ ] `upbit_auto_trading/infrastructure/repositories/sqlite_settings_repository.py` 생성:
```python
from typing import List, Dict, Any, Optional
import logging

from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
from upbit_auto_trading.domain.value_objects.trading_variable import TradingVariable
from upbit_auto_trading.domain.value_objects.compatibility_rules import CompatibilityRules
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

class SqliteSettingsRepository(SettingsRepository):
    """SQLite 기반 Settings Repository 구현 (읽기 전용)"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._logger = logging.getLogger(__name__)
        self._cache: Dict[str, Any] = {}  # 성능을 위한 캐시
    
    def get_trading_variables(self) -> List[TradingVariable]:
        """매매 변수 정의 목록 조회"""
        if 'trading_variables' in self._cache:
            return self._cache['trading_variables']
        
        query = """
        SELECT tv.*, 
               GROUP_CONCAT(
                   vp.parameter_name || ':' || 
                   vp.parameter_type || ':' || 
                   COALESCE(vp.default_value, '') || ':' ||
                   COALESCE(vp.min_value, '') || ':' ||
                   COALESCE(vp.max_value, '') || ':' ||
                   COALESCE(vp.enum_values, '') || ':' ||
                   vp.is_required || ':' ||
                   vp.display_name_ko
               ) as parameters
        FROM tv_trading_variables tv
        LEFT JOIN tv_variable_parameters vp ON tv.variable_id = vp.variable_id
        WHERE tv.is_active = 1
        GROUP BY tv.variable_id
        ORDER BY tv.variable_id
        """
        
        try:
            rows = self._db.execute_query('settings', query)
            variables = []
            
            for row in rows:
                row_dict = dict(row)
                
                # 파라미터 파싱
                parameters = []
                if row_dict.get('parameters'):
                    param_strings = row_dict['parameters'].split(',')
                    for param_str in param_strings:
                        if param_str.strip():
                            parts = param_str.split(':')
                            if len(parts) >= 8:
                                param = {
                                    'name': parts[0],
                                    'type': parts[1],
                                    'default_value': parts[2] if parts[2] else None,
                                    'min_value': float(parts[3]) if parts[3] else None,
                                    'max_value': float(parts[4]) if parts[4] else None,
                                    'enum_values': parts[5].split('|') if parts[5] else None,
                                    'is_required': bool(int(parts[6])),
                                    'display_name': parts[7]
                                }
                                parameters.append(param)
                
                variable = TradingVariable(
                    variable_id=row_dict['variable_id'],
                    display_name_ko=row_dict['display_name_ko'],
                    display_name_en=row_dict.get('display_name_en'),
                    purpose_category=row_dict['purpose_category'],
                    chart_category=row_dict['chart_category'],
                    comparison_group=row_dict['comparison_group'],
                    parameters=parameters,
                    description=row_dict.get('description'),
                    source=row_dict.get('source', 'built-in')
                )
                variables.append(variable)
            
            # 캐시 저장
            self._cache['trading_variables'] = variables
            
            self._logger.info(f"매매 변수 {len(variables)}개 로드 완료")
            return variables
            
        except Exception as e:
            self._logger.error(f"매매 변수 조회 실패: {e}")
            raise
    
    def get_variable_by_id(self, variable_id: str) -> Optional[TradingVariable]:
        """특정 매매 변수 조회"""
        variables = self.get_trading_variables()
        
        for variable in variables:
            if variable.variable_id == variable_id:
                return variable
        
        return None
    
    def get_compatibility_rules(self) -> CompatibilityRules:
        """호환성 규칙 조회"""
        if 'compatibility_rules' in self._cache:
            return self._cache['compatibility_rules']
        
        # 카테고리별 규칙 조회
        category_query = """
        SELECT category_type, category_key, category_name_ko, description
        FROM tv_indicator_categories
        WHERE is_active = 1
        ORDER BY category_type, display_order
        """
        
        try:
            rows = self._db.execute_query('settings', category_query)
            
            purpose_categories = {}
            chart_categories = {}
            comparison_groups = {}
            
            for row in rows:
                row_dict = dict(row)
                category_type = row_dict['category_type']
                category_key = row_dict['category_key']
                category_info = {
                    'name': row_dict['category_name_ko'],
                    'description': row_dict.get('description', '')
                }
                
                if category_type == 'purpose':
                    purpose_categories[category_key] = category_info
                elif category_type == 'chart':
                    chart_categories[category_key] = category_info
                elif category_type == 'comparison':
                    comparison_groups[category_key] = category_info
            
            # 호환성 매트릭스 구성 (간단한 버전)
            compatibility_matrix = {
                'price_comparable': ['price_comparable'],
                'percentage_comparable': ['percentage_comparable'],
                'zero_centered': ['zero_centered'],
                'volume_based': ['volume_based']
            }
            
            rules = CompatibilityRules(
                purpose_categories=purpose_categories,
                chart_categories=chart_categories,
                comparison_groups=comparison_groups,
                compatibility_matrix=compatibility_matrix
            )
            
            # 캐시 저장
            self._cache['compatibility_rules'] = rules
            
            self._logger.info("호환성 규칙 로드 완료")
            return rules
            
        except Exception as e:
            self._logger.error(f"호환성 규칙 조회 실패: {e}")
            raise
    
    def get_variable_parameters(self, variable_id: str) -> List[Dict[str, Any]]:
        """특정 변수의 파라미터 정의 조회"""
        query = """
        SELECT * FROM tv_variable_parameters
        WHERE variable_id = ?
        ORDER BY display_order
        """
        
        try:
            rows = self._db.execute_query('settings', query, (variable_id,))
            parameters = []
            
            for row in rows:
                param = dict(row)
                # enum_values JSON 파싱
                if param.get('enum_values'):
                    import json
                    try:
                        param['enum_values'] = json.loads(param['enum_values'])
                    except json.JSONDecodeError:
                        param['enum_values'] = param['enum_values'].split('|')
                
                parameters.append(param)
            
            return parameters
            
        except Exception as e:
            self._logger.error(f"변수 파라미터 조회 실패: {variable_id} - {e}")
            raise
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        self._cache.clear()
        self._logger.info("설정 캐시 초기화 완료")
```

### 8. **[테스트 코드 작성]** Repository 테스트
- [ ] `tests/infrastructure/repositories/` 폴더 생성
- [ ] `tests/infrastructure/repositories/test_sqlite_strategy_repository.py` 생성:
```python
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from upbit_auto_trading.infrastructure.repositories.sqlite_strategy_repository import SqliteStrategyRepository
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.domain.entities.strategy import Strategy
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
from upbit_auto_trading.domain.enums.strategy_status import StrategyStatus

class TestSqliteStrategyRepository:
    def setup_method(self):
        self.db_manager = Mock(spec=DatabaseManager)
        self.repository = SqliteStrategyRepository(self.db_manager)
    
    def test_save_new_strategy(self):
        # Given
        strategy = Strategy(
            strategy_id=StrategyId("TEST_001"),
            name="테스트 전략",
            status=StrategyStatus.ACTIVE,
            entry_triggers=[],
            exit_triggers=[],
            management_triggers=[],
            created_by="test_user"
        )
        
        # find_by_id에서 None 반환 (새 전략)
        self.db_manager.execute_query.return_value = []
        
        # When
        self.repository.save(strategy)
        
        # Then
        # INSERT 쿼리 실행 확인
        self.db_manager.execute_command.assert_called()
        call_args = self.db_manager.execute_command.call_args
        assert "INSERT INTO strategies" in call_args[0][1]
    
    def test_find_by_id_existing_strategy(self):
        # Given
        strategy_id = StrategyId("TEST_001")
        mock_row = {
            'id': 'TEST_001',
            'name': '테스트 전략',
            'status': 'ACTIVE',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.db_manager.execute_query.return_value = [mock_row]
        
        # When
        result = self.repository.find_by_id(strategy_id)
        
        # Then
        assert result is not None
        assert result.strategy_id.value == "TEST_001"
        assert result.name == "테스트 전략"
    
    def test_find_by_id_nonexistent_strategy(self):
        # Given
        strategy_id = StrategyId("NONEXISTENT")
        self.db_manager.execute_query.return_value = []
        
        # When
        result = self.repository.find_by_id(strategy_id)
        
        # Then
        assert result is None
```

### 9. **[통합]** Repository Container 구성
- [ ] `upbit_auto_trading/infrastructure/repositories/repository_container.py` 생성:
```python
from typing import Optional

from upbit_auto_trading.domain.repositories.strategy_repository import StrategyRepository
from upbit_auto_trading.domain.repositories.trigger_repository import TriggerRepository
from upbit_auto_trading.domain.repositories.settings_repository import SettingsRepository
from upbit_auto_trading.domain.repositories.market_data_repository import MarketDataRepository
from upbit_auto_trading.domain.repositories.backtest_repository import BacktestRepository

from upbit_auto_trading.infrastructure.repositories.sqlite_strategy_repository import SqliteStrategyRepository
from upbit_auto_trading.infrastructure.repositories.sqlite_trigger_repository import SqliteTriggerRepository
from upbit_auto_trading.infrastructure.repositories.sqlite_settings_repository import SqliteSettingsRepository
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager, DatabaseConnectionProvider

class RepositoryContainer:
    """Repository들의 의존성 주입 컨테이너"""
    
    def __init__(self, db_paths: Optional[Dict[str, str]] = None):
        if db_paths is None:
            db_paths = {
                'settings': 'data/settings.sqlite3',
                'strategies': 'data/strategies.sqlite3',
                'market_data': 'data/market_data.sqlite3'
            }
        
        # 데이터베이스 연결 초기화
        provider = DatabaseConnectionProvider()
        provider.initialize(db_paths)
        self._db_manager = provider.get_manager()
        
        # Repository 인스턴스들
        self._strategy_repository: Optional[StrategyRepository] = None
        self._trigger_repository: Optional[TriggerRepository] = None
        self._settings_repository: Optional[SettingsRepository] = None
        self._market_data_repository: Optional[MarketDataRepository] = None
        self._backtest_repository: Optional[BacktestRepository] = None
    
    def get_strategy_repository(self) -> StrategyRepository:
        """Strategy Repository 반환"""
        if self._strategy_repository is None:
            self._strategy_repository = SqliteStrategyRepository(self._db_manager)
        return self._strategy_repository
    
    def get_trigger_repository(self) -> TriggerRepository:
        """Trigger Repository 반환"""
        if self._trigger_repository is None:
            self._trigger_repository = SqliteTriggerRepository(self._db_manager)
        return self._trigger_repository
    
    def get_settings_repository(self) -> SettingsRepository:
        """Settings Repository 반환"""
        if self._settings_repository is None:
            self._settings_repository = SqliteSettingsRepository(self._db_manager)
        return self._settings_repository
    
    def get_market_data_repository(self) -> MarketDataRepository:
        """Market Data Repository 반환 (추후 구현)"""
        if self._market_data_repository is None:
            # TODO: SqliteMarketDataRepository 구현
            raise NotImplementedError("Market Data Repository는 추후 구현 예정")
        return self._market_data_repository
    
    def get_backtest_repository(self) -> BacktestRepository:
        """Backtest Repository 반환 (추후 구현)"""
        if self._backtest_repository is None:
            # TODO: SqliteBacktestRepository 구현
            raise NotImplementedError("Backtest Repository는 추후 구현 예정")
        return self._backtest_repository
    
    def close_all_connections(self) -> None:
        """모든 데이터베이스 연결 종료"""
        self._db_manager.close_all()
```

### 10. **[통합]** Infrastructure 패키지 초기화
- [ ] `upbit_auto_trading/infrastructure/__init__.py` 생성:
```python
from .repositories.repository_container import RepositoryContainer
from .database.database_manager import DatabaseManager

__all__ = ['RepositoryContainer', 'DatabaseManager']
```

## Verification Criteria (완료 검증 조건)

### **[Repository 동작 검증]** 모든 Repository 구현 확인
- [ ] `pytest tests/infrastructure/repositories/ -v` 실행하여 모든 테스트 통과
- [ ] Python REPL에서 Repository 연동 테스트:
```python
from upbit_auto_trading.infrastructure.repositories.repository_container import RepositoryContainer

# Repository Container 생성
container = RepositoryContainer()

# Strategy Repository 테스트
strategy_repo = container.get_strategy_repository()
active_strategies = strategy_repo.find_all_active()

print(f"활성 전략 수: {len(active_strategies)}")
print("✅ Repository 동작 검증 완료")
```

### **[데이터베이스 연결 검증]** 3-DB 연결 정상 동작 확인
- [ ] 모든 데이터베이스 파일에 정상 연결 확인
- [ ] 트랜잭션 처리 및 롤백 기능 확인
- [ ] SQLite 최적화 설정 적용 확인

### **[매핑 정확성 검증]** Entity-Table 매핑 확인
- [ ] Domain Entity ↔ Database Record 양방향 변환 정확성 확인
- [ ] 복합 객체 (Strategy + Triggers) 매핑 확인

### **[성능 검증]** Repository 성능 확인
- [ ] 대용량 데이터 상황에서 쿼리 성능 테스트
- [ ] 필터링 쿼리 최적화 확인

## Notes (주의사항)
- 기존 데이터베이스 스키마 변경 없이 매핑 레이어만 구현
- SQLite WAL 모드 설정으로 동시성 향상
- Repository는 도메인 인터페이스만 의존하고 Infrastructure 세부사항 숨김
- 성능을 위한 적절한 캐싱 전략 적용 (설정 데이터 등)
- 트랜잭션 경계는 Repository 메서드 단위로 설정
