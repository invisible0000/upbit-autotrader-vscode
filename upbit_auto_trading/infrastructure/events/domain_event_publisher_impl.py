from typing import List
import logging
import asyncio

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
from upbit_auto_trading.domain.events.domain_event_publisher import DomainEventPublisher
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus
from upbit_auto_trading.infrastructure.runtime import ensure_main_loop


class InfrastructureDomainEventPublisher(DomainEventPublisher):
    """Infrastructure 이벤트 버스를 사용하는 도메인 이벤트 Publisher"""

    def __init__(self, event_bus: IEventBus):
        super().__init__()
        self._event_bus = event_bus
        self._logger = logging.getLogger(__name__)

    def publish(self, event: DomainEvent) -> None:
        """단일 이벤트 발행 (동기 인터페이스, QAsync 환경 가정)"""
        try:
            # QAsync 환경에서는 항상 실행 중인 루프 가정
            ensure_main_loop(where="DomainEventPublisher.publish")
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._async_publish(event))

            # 태스크 매니저에 등록 (선택적)
            # TODO: AppKernel TaskManager 통합 시 추가

            self._logger.debug(f"도메인 이벤트 발행: {event.__class__.__name__}")
            return task  # 태스크 참조 반환
        except RuntimeError:
            # QAsync 환경이 아닌 경우 에러 로깅 및 복구
            self._logger.error(f"QAsync 환경이 아닙니다. 시스템 설정을 확인하세요. 위치: {event.__class__.__name__}")
            raise
        except Exception as e:
            self._logger.error(f"도메인 이벤트 발행 실패: {event.__class__.__name__} - {e}")
            raise

    def publish_all(self, events: List[DomainEvent]) -> None:
        """배치 이벤트 발행 (동기 인터페이스, QAsync 환경 가정)"""
        if not events:
            return

        try:
            # QAsync 환경에서는 항상 실행 중인 루프 가정
            ensure_main_loop(where="DomainEventPublisher.publish_all")
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._async_publish_all(events))

            # 태스크 매니저에 등록 (선택적)
            # TODO: AppKernel TaskManager 통합 시 추가

            self._logger.debug(f"도메인 이벤트 배치 발행: {len(events)}개")
            return task  # 태스크 참조 반환
        except RuntimeError:
            # QAsync 환경이 아닌 경우 에러 로깅 및 복구
            self._logger.error(f"QAsync 환경이 아닙니다. 시스템 설정을 확인하세요. 배치: {len(events)}개")
            raise
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
