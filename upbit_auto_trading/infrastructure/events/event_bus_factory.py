from typing import Optional
import logging

from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus, IEventStorage
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.infrastructure.events.storage.sqlite_event_storage import SqliteEventStorage
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

class EventBusFactory:
    """이벤트 버스 팩토리"""

    @staticmethod
    def create_in_memory_event_bus(
        event_storage: Optional[IEventStorage] = None,
        max_queue_size: int = 10000,
        worker_count: int = 4,
        batch_size: int = 10,
        batch_timeout_seconds: float = 1.0
    ) -> IEventBus:
        """메모리 기반 이벤트 버스 생성"""

        return InMemoryEventBus(
            event_storage=event_storage,
            max_queue_size=max_queue_size,
            worker_count=worker_count,
            batch_size=batch_size,
            batch_timeout_seconds=batch_timeout_seconds
        )

    @staticmethod
    def create_sqlite_event_storage(db_manager: DatabaseManager) -> IEventStorage:
        """SQLite 이벤트 저장소 생성"""
        return SqliteEventStorage(db_manager)

    @staticmethod
    def create_default_event_bus(db_manager: DatabaseManager) -> IEventBus:
        """기본 설정으로 이벤트 버스 생성 (메모리 + SQLite 저장소)"""

        # SQLite 이벤트 저장소 생성
        event_storage = EventBusFactory.create_sqlite_event_storage(db_manager)

        # 메모리 이벤트 버스 생성 (저장소 포함)
        event_bus = EventBusFactory.create_in_memory_event_bus(
            event_storage=event_storage,
            max_queue_size=10000,
            worker_count=4,
            batch_size=10,
            batch_timeout_seconds=1.0
        )

        logger = logging.getLogger(__name__)
        logger.info("기본 이벤트 버스 생성 완료 (InMemory + SQLite)")

        return event_bus
