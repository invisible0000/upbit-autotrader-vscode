from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Any, Optional, Type
from datetime import datetime

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent


class EventSubscription:
    """이벤트 구독 정보"""

    def __init__(self, event_type: Type[DomainEvent], handler: Callable,
                 is_async: bool = True, priority: int = 1, retry_count: int = 3):
        self.event_type = event_type
        self.handler = handler
        self.is_async = is_async
        self.priority = priority  # 낮을수록 우선순위 높음
        self.retry_count = retry_count
        self.subscription_id = f"{event_type.__name__}_{id(handler)}"
        self.created_at = datetime.now()


class EventProcessingResult:
    """이벤트 처리 결과"""

    def __init__(self, event_id: str, success: bool,
                 error_message: Optional[str] = None,
                 processing_time_ms: float = 0.0,
                 retry_attempt: int = 0):
        self.event_id = event_id
        self.success = success
        self.error_message = error_message
        self.processing_time_ms = processing_time_ms
        self.retry_attempt = retry_attempt
        self.processed_at = datetime.now()


class IEventBus(ABC):
    """이벤트 버스 인터페이스"""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """이벤트 발행"""
        pass

    @abstractmethod
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """배치 이벤트 발행"""
        pass

    @abstractmethod
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable,
                  is_async: bool = True, priority: int = 1,
                  retry_count: int = 3) -> str:
        """이벤트 구독"""
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """구독 취소"""
        pass

    @abstractmethod
    async def start(self) -> None:
        """이벤트 버스 시작"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """이벤트 버스 중지"""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """처리 통계 조회"""
        pass


class IEventStorage(ABC):
    """이벤트 저장소 인터페이스"""

    @abstractmethod
    async def store_event(self, event: DomainEvent) -> str:
        """이벤트 저장"""
        pass

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[DomainEvent]:
        """이벤트 조회"""
        pass

    @abstractmethod
    async def get_events_by_aggregate(self, aggregate_id: str,
                                      aggregate_type: str) -> List[DomainEvent]:
        """집합체별 이벤트 조회"""
        pass

    @abstractmethod
    async def get_unprocessed_events(self, limit: int = 100) -> List[DomainEvent]:
        """미처리 이벤트 조회"""
        pass

    @abstractmethod
    async def mark_event_processed(self, event_id: str,
                                   result: EventProcessingResult) -> None:
        """이벤트 처리 완료 표시"""
        pass
