from typing import List
import logging
import asyncio

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
from upbit_auto_trading.domain.events.domain_event_publisher import DomainEventPublisher
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus


class InfrastructureDomainEventPublisher(DomainEventPublisher):
    """Infrastructure 이벤트 버스를 사용하는 도메인 이벤트 Publisher"""

    def __init__(self, event_bus: IEventBus):
        super().__init__()
        self._event_bus = event_bus
        self._logger = logging.getLogger(__name__)

    def publish(self, event: DomainEvent) -> None:
        """단일 이벤트 발행 (동기 인터페이스)"""
        try:
            # 비동기 메서드를 동기적으로 실행
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 태스크로 스케줄
                loop.create_task(self._async_publish(event))
            else:
                # 새로운 루프에서 실행
                loop.run_until_complete(self._async_publish(event))

            self._logger.debug(f"도메인 이벤트 발행: {event.__class__.__name__}")
        except Exception as e:
            self._logger.error(f"도메인 이벤트 발행 실패: {event.__class__.__name__} - {e}")
            raise

    def publish_all(self, events: List[DomainEvent]) -> None:
        """배치 이벤트 발행 (동기 인터페이스)"""
        if not events:
            return

        try:
            # 비동기 메서드를 동기적으로 실행
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 이미 실행 중인 루프가 있으면 태스크로 스케줄
                loop.create_task(self._async_publish_all(events))
            else:
                # 새로운 루프에서 실행
                loop.run_until_complete(self._async_publish_all(events))

            self._logger.debug(f"도메인 이벤트 배치 발행: {len(events)}개")
        except Exception as e:
            self._logger.error(f"도메인 이벤트 배치 발행 실패: {len(events)}개 - {e}")
            raise

    async def _async_publish(self, event: DomainEvent) -> None:
        """내부 비동기 이벤트 발행"""
        await self._event_bus.publish(event)

    async def _async_publish_all(self, events: List[DomainEvent]) -> None:
        """내부 비동기 배치 이벤트 발행"""
        await self._event_bus.publish_batch(events)

    def clear(self) -> None:
        """이벤트 목록 초기화 (상위 클래스 호환성)"""
        # Infrastructure 이벤트 버스에서는 별도 처리 불필요
        pass
