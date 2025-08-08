"""
도메인 이벤트 게시자 (Domain Event Publisher)
도메인 이벤트 발행과 구독 관리를 위한 전용 클래스
"""

from typing import List, Callable, Dict, Type, Any, Optional
from threading import Lock
import asyncio

from upbit_auto_trading.infrastructure.logging import create_component_logger

# Forward reference로 순환 import 해결
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
else:
    # 런타임에서는 __init__.py에서 DomainEvent를 가져옴
    DomainEvent = 'DomainEvent'

# 이벤트 핸들러 타입 정의
EventHandler = Callable[['DomainEvent'], None]
AsyncEventHandler = Callable[['DomainEvent'], Any]  # Awaitable 반환


class DomainEventPublisher:
    """도메인 이벤트 발행을 담당하는 게시자"""

    def __init__(self):
        # 동기 핸들러들
        self._handlers: Dict[Type[Any], List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []

        # 비동기 핸들러들
        self._async_handlers: Dict[Type[Any], List[AsyncEventHandler]] = {}
        self._async_global_handlers: List[AsyncEventHandler] = []

        # 스레드 안전성을 위한 락
        self._lock = Lock()

        # 게시자 활성화 상태 (테스트용)
        self._enabled = True

        # 로거
        self.logger = create_component_logger("DomainEventPublisher")

    def subscribe(self, event_type: Type[Any], handler: EventHandler) -> None:
        """동기 이벤트 핸들러 등록"""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            handler_name = getattr(handler, '__name__', str(handler))
            self.logger.debug(f"동기 핸들러 등록: {event_type.__name__} -> {handler_name}")

    def subscribe_async(self, event_type: Type[Any], handler: AsyncEventHandler) -> None:
        """비동기 이벤트 핸들러 등록"""
        with self._lock:
            if event_type not in self._async_handlers:
                self._async_handlers[event_type] = []
            self._async_handlers[event_type].append(handler)
            handler_name = getattr(handler, '__name__', str(handler))
            self.logger.debug(f"비동기 핸들러 등록: {event_type.__name__} -> {handler_name}")

    def subscribe_global(self, handler: EventHandler) -> None:
        """모든 이벤트를 처리하는 글로벌 핸들러 등록"""
        with self._lock:
            self._global_handlers.append(handler)
            handler_name = getattr(handler, '__name__', str(handler))
            self.logger.debug(f"글로벌 핸들러 등록: {handler_name}")

    def subscribe_global_async(self, handler: AsyncEventHandler) -> None:
        """모든 이벤트를 처리하는 비동기 글로벌 핸들러 등록"""
        with self._lock:
            self._async_global_handlers.append(handler)
            handler_name = getattr(handler, '__name__', str(handler))
            self.logger.debug(f"비동기 글로벌 핸들러 등록: {handler_name}")

    def unsubscribe(self, event_type: Type[Any], handler: EventHandler) -> bool:
        """이벤트 핸들러 등록 해제"""
        with self._lock:
            if event_type in self._handlers and handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.debug(f"핸들러 등록 해제: {event_type.__name__} -> {handler_name}")
                return True
            return False

    def unsubscribe_async(self, event_type: Type[Any], handler: AsyncEventHandler) -> bool:
        """비동기 이벤트 핸들러 등록 해제"""
        with self._lock:
            if event_type in self._async_handlers and handler in self._async_handlers[event_type]:
                self._async_handlers[event_type].remove(handler)
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.debug(f"비동기 핸들러 등록 해제: {event_type.__name__} -> {handler_name}")
                return True
            return False

    def publish(self, event: Any) -> None:
        """동기 이벤트 발행"""
        if not self._enabled:
            return

        self.logger.info(f"도메인 이벤트 발행: {event.event_type} (ID: {event.event_id})")

        # 특정 이벤트 타입 핸들러들 실행
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                handler(event)
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.debug(f"핸들러 실행 완료: {handler_name}")
            except Exception as e:
                # 핸들러 실행 실패는 로깅만 하고 다른 핸들러에 영향 주지 않음
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.error(f"이벤트 핸들러 실행 실패: {handler_name}, 오류: {e}")

        # 글로벌 핸들러들 실행
        for handler in self._global_handlers:
            try:
                handler(event)
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.debug(f"글로벌 핸들러 실행 완료: {handler_name}")
            except Exception as e:
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.error(f"글로벌 이벤트 핸들러 실행 실패: {handler_name}, 오류: {e}")

    async def publish_async(self, event: Any) -> None:
        """비동기 이벤트 발행"""
        if not self._enabled:
            return

        self.logger.info(f"비동기 도메인 이벤트 발행: {event.event_type} (ID: {event.event_id})")

        # 특정 이벤트 타입 비동기 핸들러들 실행
        event_type = type(event)
        async_handlers = self._async_handlers.get(event_type, [])

        tasks = []
        for handler in async_handlers:
            try:
                task = asyncio.create_task(handler(event))
                tasks.append(task)
            except Exception as e:
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.error(f"비동기 핸들러 태스크 생성 실패: {handler_name}, 오류: {e}")

        # 글로벌 비동기 핸들러들 실행
        for handler in self._async_global_handlers:
            try:
                task = asyncio.create_task(handler(event))
                tasks.append(task)
            except Exception as e:
                handler_name = getattr(handler, '__name__', str(handler))
                self.logger.error(f"비동기 글로벌 핸들러 태스크 생성 실패: {handler_name}, 오류: {e}")

        # 모든 비동기 핸들러 완료 대기
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 확인 및 예외 로깅
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"비동기 핸들러 실행 실패 (태스크 {i}): {result}")
                else:
                    self.logger.debug(f"비동기 핸들러 실행 완료 (태스크 {i})")

    def publish_all(self, events: List[Any]) -> None:
        """여러 이벤트 일괄 발행"""
        for event in events:
            self.publish(event)

    async def publish_all_async(self, events: List[Any]) -> None:
        """여러 이벤트 비동기 일괄 발행"""
        tasks = [self.publish_async(event) for event in events]
        await asyncio.gather(*tasks, return_exceptions=True)

    def enable(self) -> None:
        """이벤트 발행 활성화"""
        self._enabled = True
        self.logger.info("도메인 이벤트 발행 활성화")

    def disable(self) -> None:
        """이벤트 발행 비활성화 (테스트용)"""
        self._enabled = False
        self.logger.info("도메인 이벤트 발행 비활성화")

    def clear_handlers(self) -> None:
        """모든 핸들러 제거 (테스트용)"""
        with self._lock:
            self._handlers.clear()
            self._async_handlers.clear()
            self._global_handlers.clear()
            self._async_global_handlers.clear()
            self.logger.info("모든 이벤트 핸들러 제거 완료")

    def get_handler_count(self, event_type: Type[Any]) -> int:
        """특정 이벤트 타입의 핸들러 개수 반환"""
        sync_count = len(self._handlers.get(event_type, []))
        async_count = len(self._async_handlers.get(event_type, []))
        return sync_count + async_count

    def get_total_handler_count(self) -> Dict[str, int]:
        """전체 핸들러 통계 반환"""
        total_sync = len(self._global_handlers)
        total_async = len(self._async_global_handlers)

        for handlers in self._handlers.values():
            total_sync += len(handlers)

        for handlers in self._async_handlers.values():
            total_async += len(handlers)

        return {
            "sync_handlers": total_sync,
            "async_handlers": total_async,
            "global_handlers": len(self._global_handlers),
            "total_handlers": total_sync + total_async
        }


# 전역 이벤트 게시자 인스턴스
_domain_event_publisher: Optional[DomainEventPublisher] = None


def get_domain_event_publisher() -> DomainEventPublisher:
    """전역 도메인 이벤트 게시자 반환"""
    global _domain_event_publisher
    if _domain_event_publisher is None:
        _domain_event_publisher = DomainEventPublisher()
        logger = create_component_logger("DomainEventPublisher")
        logger.info("전역 도메인 이벤트 게시자 초기화 완료")
    return _domain_event_publisher


def reset_domain_event_publisher() -> None:
    """전역 도메인 이벤트 게시자 재설정 (테스트용)"""
    global _domain_event_publisher
    if _domain_event_publisher is not None:
        _domain_event_publisher.clear_handlers()
    _domain_event_publisher = None
    logger = create_component_logger("DomainEventPublisher")
    logger.info("전역 도메인 이벤트 게시자 재설정 완료")
