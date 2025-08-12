"""
Event Handler Registry
모든 이벤트 핸들러를 등록하고 관리하며, 도메인 이벤트를 적절한 핸들러로 라우팅합니다.
"""

from typing import Dict, List, Type, Union
import asyncio

from .base_event_handler import BaseEventHandler
from .strategy_event_handlers import (
    StrategyCreatedHandler, StrategyUpdatedHandler, TriggerCreatedHandler
)
from .backtest_event_handlers import (
    BacktestStartedHandler, BacktestCompletedHandler, BacktestFailedHandler, BacktestProgressUpdatedHandler
)
from ..notifications.notification_service import NotificationService
from ..caching.cache_invalidation_service import CacheInvalidationService
from ...domain.events.base_domain_event import DomainEvent
from ...infrastructure.logging import create_component_logger

class CacheInvalidationHandler(BaseEventHandler):
    """캐시 무효화 전용 통합 핸들러"""

    def __init__(self, cache_service: CacheInvalidationService):
        """
        핸들러 초기화

        Args:
            cache_service: 캐시 무효화 서비스
        """
        super().__init__()
        self._cache_service = cache_service

    async def handle(self, event: DomainEvent) -> None:
        """
        이벤트 타입에 따른 캐시 무효화 처리

        Args:
            event: 도메인 이벤트
        """
        try:
            # 이벤트 타입별 캐시 무효화 처리
            event_type = event.event_type

            if event_type in ["strategy.created", "strategy.updated"]:
                strategy_id = getattr(event, 'strategy_id', None)
                if strategy_id:
                    await self._cache_service.invalidate_for_strategy_change(strategy_id)

            elif event_type == "trigger.created":
                strategy_id = getattr(event, 'strategy_id', None)
                trigger_id = getattr(event, 'trigger_id', None)
                if strategy_id:
                    await self._cache_service.invalidate_trigger_related_cache(strategy_id, trigger_id)

            elif event_type == "backtest.completed":
                strategy_id = getattr(event, 'strategy_id', None)
                symbol = getattr(event, 'symbol', None)
                if strategy_id and symbol:
                    await self._cache_service.invalidate_for_backtest_completion(strategy_id, symbol)

            # 기타 백테스팅 관련 이벤트들도 처리
            elif event_type in ["backtest.started", "backtest.failed"]:
                strategy_id = getattr(event, 'strategy_id', None)
                if strategy_id:
                    # 백테스팅 상태 변경에 따른 캐시 무효화
                    await self._cache_service.invalidate_backtest_related_cache(strategy_id)
        except Exception as e:
            self._logger.warning(f"캐시 무효화 실패 (계속 진행): {e}")

    def can_handle(self, event: DomainEvent) -> bool:
        """
        캐시 무효화가 필요한 이벤트인지 확인

        Args:
            event: 도메인 이벤트

        Returns:
            처리 가능 여부
        """
        cache_related_events = {
            "strategy.created", "strategy.updated", "strategy.deleted",
            "trigger.created", "trigger.updated", "trigger.deleted",
            "backtest.started", "backtest.completed", "backtest.failed"
        }
        return event.event_type in cache_related_events

    def get_event_type(self) -> type:
        """
        모든 도메인 이벤트를 처리하므로 object 반환

        Returns:
            object 타입 (모든 이벤트 처리)
        """
        return object

class EventHandlerRegistry:
    """Event Handler 등록 및 관리 레지스트리"""

    def __init__(self, notification_service: NotificationService,
                 cache_service: CacheInvalidationService):
        """
        레지스트리 초기화

        Args:
            notification_service: 알림 서비스
            cache_service: 캐시 무효화 서비스
        """
        self._notification_service = notification_service
        self._cache_service = cache_service
        self._logger = create_component_logger("EventHandlerRegistry")

        # 이벤트 타입별 핸들러 매핑
        self._handlers: Dict[str, List[BaseEventHandler]] = {}

        # 글로벌 핸들러 (모든 이벤트를 처리)
        self._global_handlers: List[BaseEventHandler] = []

        # 핸들러 설정
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """모든 이벤트 핸들러 등록"""
        # 전략 관련 핸들러 등록
        self._register_handler(StrategyCreatedHandler(self._notification_service))
        self._register_handler(StrategyUpdatedHandler(self._notification_service))
        self._register_handler(TriggerCreatedHandler(self._notification_service))

        # 백테스팅 관련 핸들러 등록
        self._register_handler(BacktestStartedHandler(self._notification_service))
        self._register_handler(BacktestCompletedHandler(self._notification_service))
        self._register_handler(BacktestFailedHandler(self._notification_service))
        self._register_handler(BacktestProgressUpdatedHandler(self._notification_service))

        # 캐시 무효화 핸들러 등록 (글로벌)
        cache_handler = CacheInvalidationHandler(self._cache_service)
        self._register_global_handler(cache_handler)

        self._logger.info(f"이벤트 핸들러 등록 완료: "
                          f"타입별 핸들러={len(self._handlers)}, "
                          f"글로벌 핸들러={len(self._global_handlers)}")

    def _register_handler(self, handler: BaseEventHandler) -> None:
        """
        타입별 이벤트 핸들러 등록

        Args:
            handler: 등록할 핸들러
        """
        event_type = handler.get_event_type()
        event_type_name = getattr(event_type, '__name__', str(event_type))

        # 이벤트 타입별로 핸들러 그룹화
        if event_type_name not in self._handlers:
            self._handlers[event_type_name] = []

        self._handlers[event_type_name].append(handler)

        self._logger.debug(f"핸들러 등록: {handler.__class__.__name__} -> {event_type_name}")

    def _register_global_handler(self, handler: BaseEventHandler) -> None:
        """
        글로벌 이벤트 핸들러 등록 (모든 이벤트 처리)

        Args:
            handler: 등록할 글로벌 핸들러
        """
        self._global_handlers.append(handler)
        self._logger.debug(f"글로벌 핸들러 등록: {handler.__class__.__name__}")

    async def handle_event(self, event: DomainEvent) -> None:
        """
        이벤트 처리

        Args:
            event: 처리할 도메인 이벤트
        """
        event_type_name = event.__class__.__name__
        event_type = event.event_type

        # 타입별 핸들러 수집
        type_handlers = self._handlers.get(event_type_name, [])

        # 글로벌 핸들러 중 해당 이벤트를 처리할 수 있는 것들 수집
        applicable_global_handlers = [
            handler for handler in self._global_handlers
            if handler.can_handle(event)
        ]

        # 모든 적용 가능한 핸들러 병합
        all_handlers = type_handlers + applicable_global_handlers

        if not all_handlers:
            self._logger.warning(f"등록된 핸들러가 없습니다: {event_type_name} (event_type: {event_type})")
            return

        self._logger.debug(f"이벤트 처리 시작: {event_type_name}, 핸들러 수={len(all_handlers)}")

        # 모든 핸들러를 병렬로 실행
        tasks = []
        for handler in all_handlers:
            task = asyncio.create_task(
                self._handle_with_error_isolation(handler, event)
            )
            tasks.append(task)

        # 모든 핸들러 실행 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 실행 결과 로깅
        success_count = 0
        error_count = 0

        for i, result in enumerate(results):
            handler_name = all_handlers[i].__class__.__name__
            if isinstance(result, Exception):
                self._logger.error(f"핸들러 실행 실패: {handler_name} - {result}")
                error_count += 1
            else:
                success_count += 1

        self._logger.info(f"이벤트 처리 완료: {event_type_name}, "
                          f"성공={success_count}, 실패={error_count}")

    async def _handle_with_error_isolation(self, handler: BaseEventHandler, event: DomainEvent) -> None:
        """
        예외 격리를 보장하는 핸들러 실행

        Args:
            handler: 실행할 핸들러
            event: 처리할 이벤트
        """
        try:
            await handler.handle(event)
        except Exception as e:
            # 개별 핸들러 실패가 다른 핸들러에 영향을 주지 않도록 예외 격리
            handler_name = handler.__class__.__name__
            self._logger.error(f"핸들러 실행 중 예외 발생: {handler_name}", exc_info=True)
            raise e

    def register_with_domain_event_publisher(self) -> None:
        """도메인 이벤트 게시자와 연동 등록"""
        try:
            from ...domain.events.domain_event_publisher import get_domain_event_publisher

            publisher = get_domain_event_publisher()

            # 모든 이벤트를 이 레지스트리로 라우팅
            async def event_router(event: DomainEvent):
                await self.handle_event(event)

            # 비동기 글로벌 구독자로 등록
            publisher.subscribe_global_async(event_router)

            self._logger.info("도메인 이벤트 게시자와 연동 완료")

        except ImportError as e:
            self._logger.error(f"도메인 이벤트 게시자 연동 실패: {e}")

    def get_handler_statistics(self) -> Dict[str, Union[int, Dict[str, int]]]:
        """
        등록된 핸들러 통계 반환

        Returns:
            핸들러 통계 정보
        """
        type_handler_count = {
            event_type: len(handlers)
            for event_type, handlers in self._handlers.items()
        }

        return {
            "total_type_handlers": sum(type_handler_count.values()),
            "total_global_handlers": len(self._global_handlers),
            "type_handler_breakdown": type_handler_count,
            "unique_event_types": len(self._handlers)
        }

    def get_supported_event_types(self) -> List[str]:
        """
        지원하는 이벤트 타입 목록 반환

        Returns:
            지원하는 이벤트 타입 리스트
        """
        return list(self._handlers.keys())

    async def health_check(self) -> Dict[str, Union[bool, str, int]]:
        """
        레지스트리 상태 점검

        Returns:
            상태 점검 결과
        """
        try:
            stats = self.get_handler_statistics()

            return {
                "healthy": True,
                "total_handlers": stats["total_type_handlers"] + stats["total_global_handlers"],
                "supported_event_types": stats["unique_event_types"],
                "notification_service_healthy": self._notification_service is not None,
                "cache_service_healthy": self._cache_service is not None,
                "message": "EventHandlerRegistry is healthy"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "message": "EventHandlerRegistry health check failed"
            }

    def get_handlers_for_event(self, event: DomainEvent) -> List[BaseEventHandler]:
        """
        특정 이벤트에 대한 핸들러 목록 반환 (테스트용)

        Args:
            event: 확인할 이벤트

        Returns:
            해당 이벤트를 처리할 수 있는 핸들러 목록
        """
        event_type_name = event.__class__.__name__

        # 타입별 핸들러 수집
        type_handlers = self._handlers.get(event_type_name, [])

        # 글로벌 핸들러 중 해당 이벤트를 처리할 수 있는 것들 수집
        applicable_global_handlers = [
            handler for handler in self._global_handlers
            if handler.can_handle(event)
        ]

        return type_handlers + applicable_global_handlers

    def get_all_handlers(self) -> List[BaseEventHandler]:
        """
        모든 등록된 핸들러 반환 (테스트용)

        Returns:
            모든 핸들러 목록
        """
        all_handlers = []
        for handlers in self._handlers.values():
            all_handlers.extend(handlers)
        all_handlers.extend(self._global_handlers)
        return all_handlers

    def get_handler_count(self) -> int:
        """
        총 핸들러 개수 반환 (테스트용)

        Returns:
            총 핸들러 개수
        """
        type_handler_count = sum(len(handlers) for handlers in self._handlers.values())
        return type_handler_count + len(self._global_handlers)

    def register_handler(self, handler: BaseEventHandler) -> None:
        """
        외부에서 핸들러 등록 (테스트용)

        Args:
            handler: 등록할 핸들러
        """
        # CacheInvalidationHandler는 글로벌 핸들러로 등록
        if isinstance(handler, CacheInvalidationHandler):
            self._register_global_handler(handler)
        else:
            self._register_handler(handler)

    def unregister_handler(self, handler: BaseEventHandler) -> None:
        """
        핸들러 등록 해제 (테스트용)

        Args:
            handler: 해제할 핸들러
        """
        # 타입별 핸들러에서 제거
        for event_type_name, handlers in self._handlers.items():
            if handler in handlers:
                handlers.remove(handler)
                self._logger.debug(f"핸들러 해제: {handler.__class__.__name__} from {event_type_name}")
                return

        # 글로벌 핸들러에서 제거
        if handler in self._global_handlers:
            self._global_handlers.remove(handler)
            self._logger.debug(f"글로벌 핸들러 해제: {handler.__class__.__name__}")

    def clear_handlers(self) -> None:
        """
        모든 핸들러 제거 (테스트용)
        """
        self._handlers.clear()
        self._global_handlers.clear()
        self._logger.debug("모든 핸들러 제거 완료")
