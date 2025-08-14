"""
Domain Events Publisher - 순수 Domain Layer 이벤트 발행
Infrastructure 의존성 없는 Domain Events 시스템
"""

from typing import List, Callable, Dict
import threading
from .base_domain_event import DomainEvent


class DomainEventPublisher:
    """
    도메인 이벤트 발행자 (Singleton)

    Domain Layer에서 순수하게 작동하는 이벤트 시스템
    Infrastructure Layer에서 구독하여 실제 로깅/저장 수행
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._subscribers: Dict[str, List[Callable[[DomainEvent], None]]] = {}
            self._global_subscribers: List[Callable[[DomainEvent], None]] = []
            self._subscription_lock = threading.Lock()
            self._initialized = True

    def publish(self, event: DomainEvent) -> None:
        """
        도메인 이벤트 발행

        Args:
            event: 발행할 도메인 이벤트
        """
        event_type = event.event_type

        # 특정 이벤트 타입 구독자들에게 발행
        with self._subscription_lock:
            if event_type in self._subscribers:
                for subscriber in self._subscribers[event_type]:
                    try:
                        subscriber(event)
                    except Exception:
                        # Domain Layer에서는 로깅 불가능하므로 조용히 무시
                        # Infrastructure Layer에서 에러 핸들링 필요
                        pass

            # 전역 구독자들에게 발행
            for subscriber in self._global_subscribers:
                try:
                    subscriber(event)
                except Exception:
                    # Domain Layer에서는 로깅 불가능하므로 조용히 무시
                    pass

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        """
        특정 이벤트 타입 구독

        Args:
            event_type: 구독할 이벤트 타입
            handler: 이벤트 핸들러
        """
        with self._subscription_lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[DomainEvent], None]) -> None:
        """
        모든 이벤트 구독

        Args:
            handler: 이벤트 핸들러
        """
        with self._subscription_lock:
            self._global_subscribers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        """
        이벤트 구독 해제

        Args:
            event_type: 구독 해제할 이벤트 타입
            handler: 제거할 핸들러
        """
        with self._subscription_lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                except ValueError:
                    pass

    def clear_subscribers(self) -> None:
        """모든 구독자 제거 (테스트용)"""
        with self._subscription_lock:
            self._subscribers.clear()
            self._global_subscribers.clear()


# 전역 인스턴스 (편의 함수용)
_publisher = DomainEventPublisher()


def publish_domain_event(event: DomainEvent) -> None:
    """도메인 이벤트 발행 (편의 함수)"""
    _publisher.publish(event)


def subscribe_to_domain_events(
    event_type: str,
    handler: Callable[[DomainEvent], None]
) -> None:
    """도메인 이벤트 구독 (편의 함수)"""
    _publisher.subscribe(event_type, handler)


def subscribe_to_all_domain_events(
    handler: Callable[[DomainEvent], None]
) -> None:
    """모든 도메인 이벤트 구독 (편의 함수)"""
    _publisher.subscribe_all(handler)


def get_domain_event_publisher() -> DomainEventPublisher:
    """Domain Event Publisher 인스턴스 반환 (편의 함수)"""
    return _publisher
