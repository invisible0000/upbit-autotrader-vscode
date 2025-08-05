#!/usr/bin/env python3
"""
간단한 이벤트 버스 직접 테스트
"""

import asyncio
from upbit_auto_trading.infrastructure.events.event_bus_factory import EventBusFactory
from upbit_auto_trading.domain.events.base_domain_event import DomainEvent


class SimpleTestEvent(DomainEvent):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    @property
    def event_type(self) -> str:
        return "SimpleTestEvent"

    @property
    def aggregate_id(self) -> str:
        return "simple-test-123"


async def simple_test():
    print('🧪 간단한 이벤트 버스 테스트')

    # 이벤트 버스 생성
    event_bus = EventBusFactory.create_in_memory_event_bus()
    await event_bus.start()

    # 이벤트 핸들러
    received = []

    async def handler(event):
        received.append(event.message)
        print(f'📩 받음: {event.message}')

    # 구독 및 이벤트 발행
    sub_id = event_bus.subscribe(SimpleTestEvent, handler)
    print(f'✅ 구독 등록: {sub_id}')

    await event_bus.publish(SimpleTestEvent("테스트 메시지"))
    await asyncio.sleep(1.0)

    print(f'📊 결과: {received}')
    print(f'📈 통계: {event_bus.get_statistics()}')

    await event_bus.stop()
    print('✅ 완료')


if __name__ == '__main__':
    asyncio.run(simple_test())
