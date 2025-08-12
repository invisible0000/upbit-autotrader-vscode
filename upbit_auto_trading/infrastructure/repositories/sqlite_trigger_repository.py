"""
SQLite 기반 Trigger Repository 구현

Domain Layer의 TriggerRepository 인터페이스를 SQLite로 구현합니다.
strategies.sqlite3 데이터베이스의 strategy_conditions 테이블과 연동하여
Trigger Entity의 영속성을 관리합니다.

주요 기능:
- Trigger CRUD 연산 (생성, 조회, 수정, 삭제)
- 전략별 트리거 조회 및 관리
- 트리거 타입별 분류 조회
- 성능 통계 및 분석 기능

Note: Mock 패턴으로 Domain Entity 호환성 보장
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.mappers.strategy_mapper import TriggerMapper

class SqliteTriggerRepository:
    """SQLite 기반 Trigger Repository 구현

    DDD 용어 사전 준수:
    - Repository Pattern: Domain Repository 인터페이스 구현
    - Entity Mapping: Trigger Entity ↔ strategy_conditions 테이블
    - Mock Pattern: Domain Layer 완성 전 호환성 보장
    """

    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._logger = logging.getLogger(__name__)

    def save_trigger(self, trigger) -> None:
        """트리거 저장 (Upsert 패턴)

        Args:
            trigger: MockTrigger - 저장할 트리거 엔티티
        """
        existing = self.find_by_id(trigger.trigger_id)

        if existing is None:
            self._insert_trigger(trigger)
        else:
            self._update_trigger(trigger)

    def _insert_trigger(self, trigger) -> None:
        """새 트리거 삽입

        테이블: strategy_conditions (실제 스키마 기준)
        컬럼: id, condition_name, strategy_id, variable_id, variable_params,
              operator, target_value, component_type, is_enabled, execution_order
        """
        insert_query = """
        INSERT INTO strategy_conditions (
            id, condition_name, strategy_id, variable_id, variable_params,
            operator, target_value, component_type, is_enabled, execution_order,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = TriggerMapper.to_insert_params(trigger)

        try:
            self._db.execute_command('strategies', insert_query, params)
            self._logger.info(f"✅ 트리거 저장 완료: {trigger.trigger_id.value}")
        except Exception as e:
            self._logger.error(f"❌ 트리거 저장 실패: {trigger.trigger_id.value} - {e}")
            raise

    def _update_trigger(self, trigger) -> None:
        """기존 트리거 업데이트"""
        update_query = """
        UPDATE strategy_conditions
        SET condition_name = ?, variable_id = ?, variable_params = ?,
            operator = ?, target_value = ?, component_type = ?,
            is_enabled = ?, execution_order = ?
        WHERE id = ?
        """

        record = TriggerMapper.to_database_record(trigger)
        params = (
            record['condition_name'],
            record['variable_id'],
            record['variable_params'],
            record['operator'],
            record['target_value'],
            record['component_type'],
            record['is_enabled'],
            record['execution_order'],
            record['id']
        )

        try:
            rows_affected = self._db.execute_command('strategies', update_query, params)
            if rows_affected == 0:
                raise ValueError(f"업데이트할 트리거를 찾을 수 없습니다: {trigger.trigger_id.value}")

            self._logger.info(f"✅ 트리거 업데이트 완료: {trigger.trigger_id.value}")
        except Exception as e:
            self._logger.error(f"❌ 트리거 업데이트 실패: {trigger.trigger_id.value} - {e}")
            raise

    def find_by_id(self, trigger_id) -> Optional[Any]:
        """ID로 트리거 조회

        Args:
            trigger_id: MockTriggerId - 트리거 고유 식별자

        Returns:
            Optional[MockTrigger] - 조회된 트리거 엔티티 또는 None
        """
        query = "SELECT * FROM strategy_conditions WHERE id = ?"

        try:
            rows = self._db.execute_query('strategies', query, (trigger_id.value,))

            if not rows:
                return None

            return TriggerMapper.to_entity(dict(rows[0]))

        except Exception as e:
            self._logger.error(f"❌ 트리거 조회 실패: {trigger_id.value} - {e}")
            raise

    def find_by_strategy_id(self, strategy_id) -> List:
        """전략 ID로 트리거 목록 조회

        Args:
            strategy_id: MockStrategyId - 전략 고유 식별자

        Returns:
            List[MockTrigger] - 해당 전략의 활성 트리거 목록
        """
        query = """
        SELECT * FROM strategy_conditions
        WHERE strategy_id = ? AND is_enabled = 1
        ORDER BY component_type, execution_order DESC
        """

        try:
            rows = self._db.execute_query('strategies', query, (strategy_id.value,))
            triggers = []

            for row in rows:
                trigger = TriggerMapper.to_entity(dict(row))
                triggers.append(trigger)

            return triggers

        except Exception as e:
            self._logger.error(f"❌ 전략별 트리거 조회 실패: {strategy_id.value} - {e}")
            raise

    def find_by_type(self, trigger_type: str) -> List:
        """타입별 트리거 조회

        Args:
            trigger_type: str - 트리거 타입 ('entry', 'exit', 'management')

        Returns:
            List[MockTrigger] - 해당 타입의 활성 트리거 목록
        """
        query = """
        SELECT * FROM strategy_conditions
        WHERE component_type = ? AND is_enabled = 1
        ORDER BY strategy_id, execution_order DESC
        """

        try:
            rows = self._db.execute_query('strategies', query, (trigger_type,))
            triggers = []

            for row in rows:
                trigger = TriggerMapper.to_entity(dict(row))
                triggers.append(trigger)

            return triggers

        except Exception as e:
            self._logger.error(f"❌ 타입별 트리거 조회 실패: {trigger_type} - {e}")
            raise

    def count_all_triggers(self) -> int:
        """전체 활성 트리거 수 조회

        Returns:
            int - 활성 상태인 트리거의 총 개수
        """
        query = "SELECT COUNT(*) FROM strategy_conditions WHERE is_enabled = 1"

        try:
            rows = self._db.execute_query('strategies', query)
            return rows[0][0] if rows else 0
        except Exception as e:
            self._logger.error(f"❌ 전체 트리거 수 조회 실패: {e}")
            raise

    def get_trigger_statistics_by_variable_type(
            self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """변수 타입별 트리거 통계 조회

        Args:
            start_date: datetime - 시작 날짜
            end_date: datetime - 종료 날짜

        Returns:
            List[Dict[str, Any]] - 변수별 통계 정보
        """
        query = """
        SELECT
            variable_id,
            COUNT(*) as total_count,
            SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as active_count,
            AVG(execution_order) as avg_weight
        FROM strategy_conditions
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
                # 통계 보강 (실제로는 execution_history 테이블과 조인 필요)
                stat['success_rate'] = 75.0  # 임시값 - 실제로는 계산 필요
                stat['avg_execution_time_ms'] = 15.0  # 임시값
                stat['variable_type'] = stat['variable_id']  # 단순화
                statistics.append(stat)

            return statistics

        except Exception as e:
            self._logger.error(f"❌ 트리거 통계 조회 실패: {e}")
            raise

    def delete_trigger(self, trigger_id) -> None:
        """트리거 삭제 (소프트 삭제)

        Args:
            trigger_id: MockTriggerId - 삭제할 트리거 ID
        """
        update_query = "UPDATE strategy_conditions SET is_enabled = 0 WHERE id = ?"

        try:
            rows_affected = self._db.execute_command(
                'strategies',
                update_query,
                (trigger_id.value,)
            )

            if rows_affected == 0:
                raise ValueError(f"삭제할 트리거를 찾을 수 없습니다: {trigger_id.value}")

            self._logger.info(f"✅ 트리거 삭제 완료: {trigger_id.value}")

        except Exception as e:
            self._logger.error(f"❌ 트리거 삭제 실패: {trigger_id.value} - {e}")
            raise

    def find_all_active_triggers(self) -> List:
        """모든 활성 트리거 조회

        Returns:
            List[MockTrigger] - 모든 활성 트리거 목록
        """
        query = """
        SELECT * FROM strategy_conditions
        WHERE is_enabled = 1
        ORDER BY strategy_id, component_type, execution_order DESC
        """

        try:
            rows = self._db.execute_query('strategies', query)
            triggers = []

            for row in rows:
                trigger = TriggerMapper.to_entity(dict(row))
                triggers.append(trigger)

            return triggers

        except Exception as e:
            self._logger.error(f"❌ 모든 활성 트리거 조회 실패: {e}")
            raise
