import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import (
    IEventStorage, EventProcessingResult
)
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

class SqliteEventStorage(IEventStorage):
    """SQLite 기반 이벤트 저장소"""

    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._logger = logging.getLogger(__name__)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """이벤트 저장용 테이블 생성"""
        create_events_table = """
        CREATE TABLE IF NOT EXISTS event_store (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            aggregate_type TEXT NOT NULL,
            event_data TEXT NOT NULL,
            metadata TEXT,
            version INTEGER NOT NULL DEFAULT 1,
            occurred_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_processed BOOLEAN DEFAULT 0,
            processed_at TIMESTAMP,
            processing_result TEXT
        )
        """

        create_processing_log_table = """
        CREATE TABLE IF NOT EXISTS event_processing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            handler_name TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            processing_time_ms REAL,
            retry_attempt INTEGER DEFAULT 0,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES event_store(event_id)
        )
        """

        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_event_store_aggregate ON event_store(aggregate_id, aggregate_type)",
            "CREATE INDEX IF NOT EXISTS idx_event_store_type ON event_store(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_event_store_occurred ON event_store(occurred_at)",
            "CREATE INDEX IF NOT EXISTS idx_event_store_processed ON event_store(is_processed)",
            "CREATE INDEX IF NOT EXISTS idx_processing_log_event ON event_processing_log(event_id)"
        ]

        try:
            self._db.execute_command('strategies', create_events_table)
            self._db.execute_command('strategies', create_processing_log_table)

            for index_sql in create_indexes:
                self._db.execute_command('strategies', index_sql)

            self._logger.info("이벤트 저장소 테이블 초기화 완료")

        except Exception as e:
            self._logger.error(f"이벤트 저장소 테이블 생성 실패: {e}")
            raise

    async def store_event(self, event: DomainEvent) -> str:
        """이벤트 저장"""
        try:
            # 이벤트 ID 생성 (없을 경우)
            event_id = event.event_id
            if not event_id:
                import uuid
                event_id = str(uuid.uuid4())

            # 이벤트 데이터 직렬화
            event_data = self._serialize_event(event)
            metadata = self._serialize_metadata(event)

            insert_query = """
            INSERT INTO event_store (
                event_id, event_type, aggregate_id, aggregate_type,
                event_data, metadata, version, occurred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                event_id,
                event.__class__.__name__,
                event.aggregate_id,
                getattr(event, 'aggregate_type', event.__class__.__name__),
                event_data,
                metadata,
                event.version,
                event.occurred_at.isoformat()
            )

            self._db.execute_command('strategies', insert_query, params)

            self._logger.debug(f"이벤트 저장 완료: {event_id}")
            return event_id

        except Exception as e:
            self._logger.error(f"이벤트 저장 실패: {e}")
            raise

    async def get_event(self, event_id: str) -> Optional[DomainEvent]:
        """이벤트 조회"""
        try:
            query = "SELECT * FROM event_store WHERE event_id = ?"

            rows = self._db.execute_query('strategies', query, (event_id,))

            if not rows:
                return None

            return self._deserialize_event(dict(rows[0]))

        except Exception as e:
            self._logger.error(f"이벤트 조회 실패 {event_id}: {e}")
            return None

    async def get_events_by_aggregate(self, aggregate_id: str,
                                      aggregate_type: str) -> List[DomainEvent]:
        """집합체별 이벤트 조회"""
        try:
            query = """
            SELECT * FROM event_store
            WHERE aggregate_id = ? AND aggregate_type = ?
            ORDER BY occurred_at ASC, version ASC
            """

            rows = self._db.execute_query('strategies', query, (aggregate_id, aggregate_type))

            events = []
            for row in rows:
                event = self._deserialize_event(dict(row))
                if event:
                    events.append(event)

            return events

        except Exception as e:
            self._logger.error(f"집합체 이벤트 조회 실패 {aggregate_id}: {e}")
            return []

    async def get_unprocessed_events(self, limit: int = 100) -> List[DomainEvent]:
        """미처리 이벤트 조회"""
        try:
            query = """
            SELECT * FROM event_store
            WHERE is_processed = 0
            ORDER BY occurred_at ASC
            LIMIT ?
            """

            rows = self._db.execute_query('strategies', query, (limit,))

            events = []
            for row in rows:
                event = self._deserialize_event(dict(row))
                if event:
                    events.append(event)

            return events

        except Exception as e:
            self._logger.error(f"미처리 이벤트 조회 실패: {e}")
            return []

    async def mark_event_processed(self, event_id: str,
                                   result: EventProcessingResult) -> None:
        """이벤트 처리 완료 표시"""
        try:
            # 이벤트 상태 업데이트
            update_query = """
            UPDATE event_store
            SET is_processed = ?, processed_at = ?, processing_result = ?
            WHERE event_id = ?
            """

            processing_result_json = json.dumps({
                'success': result.success,
                'error_message': result.error_message,
                'processing_time_ms': result.processing_time_ms,
                'retry_attempt': result.retry_attempt,
                'processed_at': result.processed_at.isoformat()
            })

            self._db.execute_command('strategies', update_query, (
                1 if result.success else 0,
                result.processed_at.isoformat(),
                processing_result_json,
                event_id
            ))

            # 처리 로그 추가
            log_query = """
            INSERT INTO event_processing_log (
                event_id, handler_name, success, error_message,
                processing_time_ms, retry_attempt
            ) VALUES (?, ?, ?, ?, ?, ?)
            """

            # 핸들러 이름은 결과에서 추출하거나 기본값 사용
            handler_name = getattr(result, 'handler_name', 'unknown')

            self._db.execute_command('strategies', log_query, (
                event_id,
                handler_name,
                result.success,
                result.error_message,
                result.processing_time_ms,
                result.retry_attempt
            ))

            self._logger.debug(f"이벤트 처리 상태 업데이트: {event_id} - {result.success}")

        except Exception as e:
            self._logger.error(f"이벤트 처리 상태 업데이트 실패 {event_id}: {e}")

    def _serialize_event(self, event: DomainEvent) -> str:
        """이벤트 직렬화"""
        try:
            # 이벤트 속성을 딕셔너리로 변환
            event_dict = {}
            for key, value in event.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, datetime):
                        event_dict[key] = value.isoformat()
                    elif hasattr(value, '__dict__'):
                        # 복합 객체는 딕셔너리로 변환
                        event_dict[key] = value.__dict__
                    else:
                        event_dict[key] = value

            return json.dumps(event_dict, default=str)

        except Exception as e:
            self._logger.error(f"이벤트 직렬화 실패: {e}")
            return "{}"

    def _serialize_metadata(self, event: DomainEvent) -> str:
        """메타데이터 직렬화"""
        try:
            metadata = {
                'event_class': event.__class__.__module__ + '.' + event.__class__.__name__,
                'serialized_at': datetime.now().isoformat(),
                'version': getattr(event, 'schema_version', 1)
            }

            return json.dumps(metadata)

        except Exception as e:
            self._logger.error(f"메타데이터 직렬화 실패: {e}")
            return "{}"

    def _deserialize_event(self, event_row: Dict[str, Any]) -> Optional[DomainEvent]:
        """이벤트 역직렬화"""
        try:
            event_data = json.loads(event_row['event_data'])
            metadata = json.loads(event_row.get('metadata', '{}'))

            # 이벤트 클래스 동적 로드
            event_class = self._get_event_class(event_row['event_type'], metadata)

            if not event_class:
                self._logger.warning(f"이벤트 클래스를 찾을 수 없음: {event_row['event_type']}")
                return None

            # 이벤트 객체 재구성
            event = event_class.__new__(event_class)

            # 기본 속성 설정
            event._event_id = event_row['event_id']
            event._occurred_at = datetime.fromisoformat(event_row['occurred_at'])
            event._version = event_row['version']

            # 이벤트 데이터 복원
            for key, value in event_data.items():
                if key not in ['_event_id', '_occurred_at', '_version']:
                    setattr(event, key, value)

            return event

        except Exception as e:
            self._logger.error(f"이벤트 역직렬화 실패: {e}")
            return None

    def _get_event_class(self, event_type: str, metadata: Dict[str, Any]):
        """이벤트 클래스 조회"""
        try:
            # 메타데이터에서 전체 클래스 경로 가져오기
            class_path = metadata.get('event_class')

            if class_path:
                module_name, class_name = class_path.rsplit('.', 1)
                module = __import__(module_name, fromlist=[class_name])
                return getattr(module, class_name)

            # 폴백: 이벤트 타입으로 추정
            # 실제 구현에서는 이벤트 타입 레지스트리 사용 권장
            return None

        except Exception as e:
            self._logger.error(f"이벤트 클래스 로드 실패: {e}")
            return None

    async def get_event_statistics(self) -> Dict[str, Any]:
        """이벤트 저장소 통계"""
        try:
            stats_query = """
            SELECT
                COUNT(*) as total_events,
                COUNT(CASE WHEN is_processed = 1 THEN 1 END) as processed_events,
                COUNT(CASE WHEN is_processed = 0 THEN 1 END) as unprocessed_events,
                COUNT(DISTINCT event_type) as unique_event_types,
                COUNT(DISTINCT aggregate_id) as unique_aggregates,
                MIN(occurred_at) as earliest_event,
                MAX(occurred_at) as latest_event
            FROM event_store
            """

            rows = self._db.execute_query('strategies', stats_query)

            if rows:
                stats = dict(rows[0])

                # 이벤트 타입별 통계
                type_query = """
                SELECT event_type, COUNT(*) as count
                FROM event_store
                GROUP BY event_type
                ORDER BY count DESC
                """

                type_rows = self._db.execute_query('strategies', type_query)
                stats['event_types'] = [dict(row) for row in type_rows]

                return stats

            return {}

        except Exception as e:
            self._logger.error(f"이벤트 통계 조회 실패: {e}")
            return {}
