#!/usr/bin/env python3
"""
간단한 이벤트 저장소 검증 테스트
"""

import asyncio
import os
import tempfile

from upbit_auto_trading.infrastructure.events.storage.sqlite_event_storage import SqliteEventStorage
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.domain.events.base_domain_event import DomainEvent


class TestStorageEvent(DomainEvent):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    @property
    def event_type(self) -> str:
        return "TestStorageEvent"

    @property
    def aggregate_id(self) -> str:
        return "test-storage-123"


async def test_storage_basic():
    """기본 저장소 기능 테스트"""
    print('🗄️ 이벤트 저장소 기본 기능 테스트...')

    # 임시 데이터베이스
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3') as tmp_file:
        temp_db_path = tmp_file.name

    try:
        # 저장소 생성
        db_manager = DatabaseManager({'strategies': temp_db_path})
        storage = SqliteEventStorage(db_manager)

        # 이벤트 저장
        event = TestStorageEvent("저장소 테스트 메시지")
        event_id = await storage.store_event(event)
        print(f'✅ 이벤트 저장 완료: {event_id}')

        # 이벤트 조회
        retrieved_event = await storage.get_event(event_id)
        if retrieved_event:
            print(f'✅ 이벤트 조회 성공: {retrieved_event.message}')
        else:
            print('❌ 이벤트 조회 실패')
            return False

        # 미처리 이벤트 조회
        unprocessed = await storage.get_unprocessed_events()
        print(f'📊 미처리 이벤트 수: {len(unprocessed)}')

        # 통계 조회
        stats = await storage.get_event_statistics()
        print(f'📈 저장소 통계:')
        print(f'   - 총 이벤트: {stats.get("total_events", 0)}')
        print(f'   - 미처리 이벤트: {stats.get("unprocessed_events", 0)}')

        print('✅ 기본 저장소 기능 테스트 성공!')
        return True

    except Exception as e:
        print(f'❌ 테스트 실패: {e}')
        import traceback
        traceback.print_exc()
        return False

    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)


if __name__ == '__main__':
    success = asyncio.run(test_storage_basic())
    exit(0 if success else 1)
