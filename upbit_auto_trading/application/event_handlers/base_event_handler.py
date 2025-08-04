"""
Application Layer Event Handler 기본 인터페이스

도메인 이벤트를 받아 부수 효과(알림, 로깅, 캐시 무효화 등)를 처리하는
모든 Event Handler의 기본 클래스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic
import logging

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent

T = TypeVar('T', bound=DomainEvent)


class BaseEventHandler(ABC, Generic[T]):
    """모든 Event Handler의 기본 클래스

    Application Layer에서 도메인 이벤트를 받아 알림, 로깅, 캐시 무효화 등의
    부수 효과를 처리하는 핸들러들의 기본 인터페이스입니다.

    Generic 타입으로 특정 이벤트 타입에 대한 타입 안전성을 보장합니다.
    """

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def handle(self, event: T) -> None:
        """이벤트 처리

        Args:
            event: 처리할 도메인 이벤트

        Note:
            - 이 메소드는 예외가 발생해도 전체 시스템에 영향을 주지 않아야 합니다
            - 모든 부수 효과는 비동기로 처리하여 도메인 로직을 블로킹하지 않습니다
        """
        pass

    def can_handle(self, event: DomainEvent) -> bool:
        """이벤트 처리 가능 여부 확인

        Args:
            event: 확인할 도메인 이벤트

        Returns:
            bool: 이 핸들러가 해당 이벤트를 처리할 수 있는지 여부
        """
        return isinstance(event, self.get_event_type())

    @abstractmethod
    def get_event_type(self) -> type:
        """처리할 이벤트 타입 반환

        Returns:
            type: 이 핸들러가 처리하는 도메인 이벤트 클래스
        """
        pass

    def _log_event_processing(self, event: T, action: str = "처리") -> None:
        """이벤트 처리 로깅

        Args:
            event: 처리 중인 이벤트
            action: 수행 중인 액션 (예: "처리", "시작", "완료")
        """
        self._logger.info(
            f"이벤트 {action}: {event.event_type} "
            f"(ID: {event.event_id}, 시간: {event.occurred_at})"
        )

    def _log_error(self, event: T, error: Exception, context: str = "") -> None:
        """이벤트 처리 오류 로깅

        Args:
            event: 처리 중이던 이벤트
            error: 발생한 예외
            context: 추가 컨텍스트 정보
        """
        self._logger.error(
            f"이벤트 처리 실패: {event.event_type} "
            f"(ID: {event.event_id}) - {error} {context}"
        )
