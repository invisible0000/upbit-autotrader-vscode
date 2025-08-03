# TASK-20250803-07

## Title
Event Handler 및 Notification 시스템 구현 (도메인 이벤트 처리)

## Objective (목표)
도메인 계층에서 발행되는 이벤트들을 처리하는 Application Layer의 Event Handler를 구현합니다. 전략 생성/수정, 트리거 평가, 백테스팅 완료 등의 도메인 이벤트에 대응하여 알림, 로깅, 캐시 무효화 등의 부수 효과를 처리합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 2: Application Layer 구축 (2주)" > "2.4 이벤트 핸들러 구현 (3일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-04`: 도메인 이벤트 시스템 구현 완료
- `TASK-20250803-05`: Application Service 구현 완료
- `TASK-20250803-06`: Query 패턴 및 CQRS 구현 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 이벤트 처리 요구사항 분석
- [ ] UI 알림이 필요한 이벤트들 식별 (전략 생성 완료, 백테스팅 완료 등)
- [ ] 캐시 무효화가 필요한 이벤트들 식별 (데이터 변경 이벤트)
- [ ] 로깅/감사가 필요한 이벤트들 식별 (중요한 비즈니스 액션)
- [ ] 성능 모니터링이 필요한 이벤트들 식별 (시간 측정, 빈도 추적)

### 2. **[폴더 구조 생성]** Event Handler 시스템 구조
- [ ] `upbit_auto_trading/application/event_handlers/` 폴더 생성
- [ ] `upbit_auto_trading/application/notifications/` 폴더 생성
- [ ] `upbit_auto_trading/application/caching/` 폴더 생성

### 3. **[새 코드 작성]** 기본 Event Handler 인터페이스
- [ ] `upbit_auto_trading/application/event_handlers/base_event_handler.py` 생성:
```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic
import logging

from upbit_auto_trading.domain.events.base_domain_event import DomainEvent

T = TypeVar('T', bound=DomainEvent)

class BaseEventHandler(ABC, Generic[T]):
    """모든 Event Handler의 기본 클래스"""
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def handle(self, event: T) -> None:
        """이벤트 처리"""
        pass
    
    def can_handle(self, event: DomainEvent) -> bool:
        """이벤트 처리 가능 여부 확인"""
        return isinstance(event, self.get_event_type())
    
    @abstractmethod
    def get_event_type(self) -> type:
        """처리할 이벤트 타입 반환"""
        pass
    
    def _log_event_processing(self, event: T, action: str = "처리") -> None:
        """이벤트 처리 로깅"""
        self._logger.info(
            f"이벤트 {action}: {event.event_type} "
            f"(ID: {event.event_id}, 시간: {event.occurred_at})"
        )
```

### 4. **[새 코드 작성]** Notification 시스템 구현
- [ ] `upbit_auto_trading/application/notifications/notification_service.py` 생성:
```python
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio

class NotificationType(Enum):
    SUCCESS = "success"
    WARNING = "warning" 
    ERROR = "error"
    INFO = "info"

class NotificationChannel(Enum):
    UI_TOAST = "ui_toast"
    UI_STATUS_BAR = "ui_status_bar"
    LOG_FILE = "log_file"
    SYSTEM_NOTIFICATION = "system_notification"

@dataclass
class Notification:
    """알림 메시지 데이터"""
    id: str
    title: str
    message: str
    notification_type: NotificationType
    channels: List[NotificationChannel]
    timestamp: datetime
    metadata: Dict[str, Any]
    auto_dismiss_seconds: Optional[int] = None

class NotificationService:
    """알림 관리 서비스"""
    
    def __init__(self):
        self._subscribers: Dict[NotificationChannel, List[callable]] = {}
        self._notification_history: List[Notification] = []
        self._max_history_size = 1000
    
    def subscribe(self, channel: NotificationChannel, callback: callable) -> None:
        """채널별 알림 구독자 등록"""
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append(callback)
    
    async def send_notification(self, notification: Notification) -> None:
        """알림 발송"""
        # 히스토리에 추가
        self._notification_history.append(notification)
        if len(self._notification_history) > self._max_history_size:
            self._notification_history.pop(0)
        
        # 각 채널의 구독자들에게 알림 전송
        tasks = []
        for channel in notification.channels:
            if channel in self._subscribers:
                for callback in self._subscribers[channel]:
                    tasks.append(self._send_to_subscriber(callback, notification))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_to_subscriber(self, callback: callable, notification: Notification) -> None:
        """개별 구독자에게 알림 전송"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(notification)
            else:
                callback(notification)
        except Exception as e:
            # 알림 전송 실패는 전체 시스템에 영향주지 않도록 처리
            print(f"⚠️ 알림 전송 실패: {e}")
    
    def get_recent_notifications(self, limit: int = 50) -> List[Notification]:
        """최근 알림 목록 조회"""
        return self._notification_history[-limit:]
    
    def clear_notifications(self) -> None:
        """알림 히스토리 초기화"""
        self._notification_history.clear()
```

### 5. **[새 코드 작성]** 전략 이벤트 핸들러 구현
- [ ] `upbit_auto_trading/application/event_handlers/strategy_event_handlers.py` 생성:
```python
from typing import Optional
import uuid

from upbit_auto_trading.application.event_handlers.base_event_handler import BaseEventHandler
from upbit_auto_trading.application.notifications.notification_service import (
    NotificationService, Notification, NotificationType, NotificationChannel
)
from upbit_auto_trading.domain.events.strategy_events import (
    StrategyCreated, StrategyUpdated, StrategyDeleted, StrategyActivated, StrategyDeactivated,
    TriggerAdded, TriggerRemoved
)
from datetime import datetime

class StrategyCreatedHandler(BaseEventHandler[StrategyCreated]):
    """전략 생성 이벤트 핸들러"""
    
    def __init__(self, notification_service: NotificationService):
        super().__init__()
        self._notification_service = notification_service
    
    async def handle(self, event: StrategyCreated) -> None:
        """전략 생성 이벤트 처리"""
        self._log_event_processing(event)
        
        # 성공 알림 전송
        notification = Notification(
            id=str(uuid.uuid4()),
            title="전략 생성 완료",
            message=f"새로운 전략 '{event.strategy_name}'이(가) 성공적으로 생성되었습니다.",
            notification_type=NotificationType.SUCCESS,
            channels=[NotificationChannel.UI_TOAST, NotificationChannel.LOG_FILE],
            timestamp=datetime.now(),
            metadata={
                "strategy_id": event.strategy_id.value,
                "strategy_name": event.strategy_name,
                "created_by": event.created_by
            },
            auto_dismiss_seconds=5
        )
        
        await self._notification_service.send_notification(notification)
        
        # 추가 비즈니스 로직 (예: 캐시 무효화, 통계 업데이트 등)
        await self._update_strategy_statistics()
    
    def get_event_type(self) -> type:
        return StrategyCreated
    
    async def _update_strategy_statistics(self) -> None:
        """전략 통계 업데이트"""
        # 실제로는 통계 서비스를 호출하여 전략 수 업데이트
        self._logger.debug("전략 생성으로 인한 통계 업데이트 완료")

class StrategyUpdatedHandler(BaseEventHandler[StrategyUpdated]):
    """전략 수정 이벤트 핸들러"""
    
    def __init__(self, notification_service: NotificationService):
        super().__init__()
        self._notification_service = notification_service
    
    async def handle(self, event: StrategyUpdated) -> None:
        """전략 수정 이벤트 처리"""
        self._log_event_processing(event)
        
        # 수정 내용에 따른 적절한 알림
        if self._is_significant_change(event):
            notification = Notification(
                id=str(uuid.uuid4()),
                title="전략 수정 완료",
                message=f"전략 '{event.strategy_name}'의 {', '.join(event.updated_fields)}이(가) 수정되었습니다.",
                notification_type=NotificationType.INFO,
                channels=[NotificationChannel.UI_STATUS_BAR, NotificationChannel.LOG_FILE],
                timestamp=datetime.now(),
                metadata={
                    "strategy_id": event.strategy_id.value,
                    "updated_fields": event.updated_fields,
                    "updated_by": event.updated_by
                },
                auto_dismiss_seconds=3
            )
            
            await self._notification_service.send_notification(notification)
        
        # 캐시 무효화
        await self._invalidate_strategy_cache(event.strategy_id.value)
    
    def get_event_type(self) -> type:
        return StrategyUpdated
    
    def _is_significant_change(self, event: StrategyUpdated) -> bool:
        """중요한 변경사항인지 판단"""
        significant_fields = {"name", "triggers", "status"}
        return any(field in significant_fields for field in event.updated_fields)
    
    async def _invalidate_strategy_cache(self, strategy_id: str) -> None:
        """전략 관련 캐시 무효화"""
        # 실제로는 캐시 서비스를 호출
        self._logger.debug(f"전략 {strategy_id} 캐시 무효화 완료")

class TriggerAddedHandler(BaseEventHandler[TriggerAdded]):
    """트리거 추가 이벤트 핸들러"""
    
    def __init__(self, notification_service: NotificationService):
        super().__init__()
        self._notification_service = notification_service
    
    async def handle(self, event: TriggerAdded) -> None:
        """트리거 추가 이벤트 처리"""
        self._log_event_processing(event)
        
        # 트리거 추가 알림
        trigger_type_name = "진입 조건" if event.trigger_type == "ENTRY" else "청산 조건"
        
        notification = Notification(
            id=str(uuid.uuid4()),
            title="트리거 추가 완료",
            message=f"{trigger_type_name} '{event.variable_id}' 트리거가 추가되었습니다.",
            notification_type=NotificationType.INFO,
            channels=[NotificationChannel.UI_STATUS_BAR],
            timestamp=datetime.now(),
            metadata={
                "strategy_id": event.strategy_id.value,
                "trigger_id": event.trigger_id.value,
                "trigger_type": event.trigger_type,
                "variable_id": event.variable_id
            },
            auto_dismiss_seconds=3
        )
        
        await self._notification_service.send_notification(notification)
        
        # 전략 유효성 재검증 트리거
        await self._trigger_strategy_validation(event.strategy_id.value)
    
    def get_event_type(self) -> type:
        return TriggerAdded
    
    async def _trigger_strategy_validation(self, strategy_id: str) -> None:
        """전략 유효성 재검증"""
        # 실제로는 유효성 검증 서비스를 호출
        self._logger.debug(f"전략 {strategy_id} 유효성 재검증 완료")
```

### 6. **[새 코드 작성]** 백테스팅 이벤트 핸들러 구현
- [ ] `upbit_auto_trading/application/event_handlers/backtest_event_handlers.py` 생성:
```python
from upbit_auto_trading.application.event_handlers.base_event_handler import BaseEventHandler
from upbit_auto_trading.application.notifications.notification_service import (
    NotificationService, Notification, NotificationType, NotificationChannel
)
from upbit_auto_trading.domain.events.backtest_events import (
    BacktestStarted, BacktestCompleted, BacktestFailed, BacktestProgressUpdated
)
import uuid
from datetime import datetime

class BacktestStartedHandler(BaseEventHandler[BacktestStarted]):
    """백테스팅 시작 이벤트 핸들러"""
    
    def __init__(self, notification_service: NotificationService):
        super().__init__()
        self._notification_service = notification_service
    
    async def handle(self, event: BacktestStarted) -> None:
        """백테스팅 시작 이벤트 처리"""
        self._log_event_processing(event)
        
        notification = Notification(
            id=str(uuid.uuid4()),
            title="백테스팅 시작",
            message=f"{event.symbol} 백테스팅이 시작되었습니다 ({event.start_date.strftime('%Y-%m-%d')} ~ {event.end_date.strftime('%Y-%m-%d')})",
            notification_type=NotificationType.INFO,
            channels=[NotificationChannel.UI_TOAST],
            timestamp=datetime.now(),
            metadata={
                "backtest_id": event.backtest_id,
                "strategy_id": event.strategy_id.value,
                "symbol": event.symbol,
                "initial_capital": event.initial_capital
            },
            auto_dismiss_seconds=3
        )
        
        await self._notification_service.send_notification(notification)
    
    def get_event_type(self) -> type:
        return BacktestStarted

class BacktestCompletedHandler(BaseEventHandler[BacktestCompleted]):
    """백테스팅 완료 이벤트 핸들러"""
    
    def __init__(self, notification_service: NotificationService):
        super().__init__()
        self._notification_service = notification_service
    
    async def handle(self, event: BacktestCompleted) -> None:
        """백테스팅 완료 이벤트 처리"""
        self._log_event_processing(event)
        
        # 결과에 따른 알림 타입 결정
        if event.total_return > 0:
            notification_type = NotificationType.SUCCESS
            result_emoji = "📈"
        else:
            notification_type = NotificationType.WARNING
            result_emoji = "📉"
        
        notification = Notification(
            id=str(uuid.uuid4()),
            title="백테스팅 완료",
            message=f"{result_emoji} {event.symbol} 백테스팅 완료! 총 수익률: {event.total_return:.2f}%, 거래횟수: {event.total_trades}회",
            notification_type=notification_type,
            channels=[NotificationChannel.UI_TOAST, NotificationChannel.SYSTEM_NOTIFICATION],
            timestamp=datetime.now(),
            metadata={
                "backtest_id": event.backtest_id,
                "strategy_id": event.strategy_id.value,
                "symbol": event.symbol,
                "total_return": event.total_return,
                "max_drawdown": event.max_drawdown,
                "sharpe_ratio": event.sharpe_ratio,
                "total_trades": event.total_trades,
                "win_rate": event.win_rate,
                "duration_seconds": event.duration_seconds
            },
            auto_dismiss_seconds=10
        )
        
        await self._notification_service.send_notification(notification)
        
        # 성과 통계 업데이트
        await self._update_performance_statistics(event)
    
    def get_event_type(self) -> type:
        return BacktestCompleted
    
    async def _update_performance_statistics(self, event: BacktestCompleted) -> None:
        """성과 통계 업데이트"""
        self._logger.info(
            f"백테스팅 완료 통계 업데이트: "
            f"수익률 {event.total_return:.2f}%, "
            f"MDD {event.max_drawdown:.2f}%, "
            f"샤프비율 {event.sharpe_ratio:.2f}"
        )

class BacktestFailedHandler(BaseEventHandler[BacktestFailed]):
    """백테스팅 실패 이벤트 핸들러"""
    
    def __init__(self, notification_service: NotificationService):
        super().__init__()
        self._notification_service = notification_service
    
    async def handle(self, event: BacktestFailed) -> None:
        """백테스팅 실패 이벤트 처리"""
        self._log_event_processing(event)
        
        notification = Notification(
            id=str(uuid.uuid4()),
            title="백테스팅 실패",
            message=f"❌ {event.symbol} 백테스팅이 실패했습니다: {event.error_message}",
            notification_type=NotificationType.ERROR,
            channels=[NotificationChannel.UI_TOAST, NotificationChannel.LOG_FILE],
            timestamp=datetime.now(),
            metadata={
                "backtest_id": event.backtest_id,
                "strategy_id": event.strategy_id.value,
                "symbol": event.symbol,
                "error_message": event.error_message,
                "error_type": event.error_type,
                "progress_percentage": event.progress_percentage
            },
            auto_dismiss_seconds=0  # 수동 닫기
        )
        
        await self._notification_service.send_notification(notification)
        
        # 에러 리포팅
        await self._report_error(event)
    
    def get_event_type(self) -> type:
        return BacktestFailed
    
    async def _report_error(self, event: BacktestFailed) -> None:
        """에러 리포팅"""
        self._logger.error(
            f"백테스팅 실패 리포트: "
            f"ID={event.backtest_id}, "
            f"에러={event.error_message}, "
            f"진행률={event.progress_percentage}%"
        )
```

### 7. **[새 코드 작성]** 캐시 무효화 시스템 구현
- [ ] `upbit_auto_trading/application/caching/cache_invalidation_service.py` 생성:
```python
from typing import Set, Dict, Any, List
from abc import ABC, abstractmethod
import asyncio

class CacheKey:
    """캐시 키 관리"""
    
    @staticmethod
    def strategy_list() -> str:
        return "strategy:list"
    
    @staticmethod
    def strategy_detail(strategy_id: str) -> str:
        return f"strategy:detail:{strategy_id}"
    
    @staticmethod
    def strategy_triggers(strategy_id: str) -> str:
        return f"strategy:triggers:{strategy_id}"
    
    @staticmethod
    def dashboard_data() -> str:
        return "dashboard:data"
    
    @staticmethod
    def backtest_results(strategy_id: str) -> str:
        return f"backtest:results:{strategy_id}"

class CacheInvalidationService:
    """캐시 무효화 관리 서비스"""
    
    def __init__(self):
        self._invalidation_rules: Dict[str, List[str]] = {}
        self._setup_invalidation_rules()
    
    def _setup_invalidation_rules(self) -> None:
        """무효화 규칙 설정"""
        # 전략 생성/수정 시 무효화할 캐시들
        self._invalidation_rules["strategy_changed"] = [
            CacheKey.strategy_list(),
            CacheKey.dashboard_data()
        ]
        
        # 트리거 변경 시 무효화할 캐시들
        self._invalidation_rules["trigger_changed"] = [
            CacheKey.strategy_list(),
            CacheKey.dashboard_data()
        ]
        
        # 백테스팅 완료 시 무효화할 캐시들
        self._invalidation_rules["backtest_completed"] = [
            CacheKey.dashboard_data()
        ]
    
    async def invalidate_strategy_related_cache(self, strategy_id: str) -> None:
        """전략 관련 캐시 무효화"""
        keys_to_invalidate = [
            CacheKey.strategy_detail(strategy_id),
            CacheKey.strategy_triggers(strategy_id),
            CacheKey.backtest_results(strategy_id)
        ] + self._invalidation_rules.get("strategy_changed", [])
        
        await self._invalidate_cache_keys(keys_to_invalidate)
    
    async def invalidate_trigger_related_cache(self, strategy_id: str) -> None:
        """트리거 관련 캐시 무효화"""
        keys_to_invalidate = [
            CacheKey.strategy_detail(strategy_id),
            CacheKey.strategy_triggers(strategy_id)
        ] + self._invalidation_rules.get("trigger_changed", [])
        
        await self._invalidate_cache_keys(keys_to_invalidate)
    
    async def invalidate_backtest_related_cache(self, strategy_id: str) -> None:
        """백테스팅 관련 캐시 무효화"""
        keys_to_invalidate = [
            CacheKey.backtest_results(strategy_id)
        ] + self._invalidation_rules.get("backtest_completed", [])
        
        await self._invalidate_cache_keys(keys_to_invalidate)
    
    async def _invalidate_cache_keys(self, keys: List[str]) -> None:
        """캐시 키들 무효화"""
        # 실제로는 Redis나 메모리 캐시에서 키들을 삭제
        # 여기서는 로깅으로 대체
        for key in keys:
            print(f"🗑️ 캐시 무효화: {key}")
        
        # 비동기 처리 시뮬레이션
        await asyncio.sleep(0.01)
```

### 8. **[새 코드 작성]** Event Handler 등록 및 관리
- [ ] `upbit_auto_trading/application/event_handlers/event_handler_registry.py` 생성:
```python
from typing import Dict, List, Type
import asyncio

from upbit_auto_trading.application.event_handlers.base_event_handler import BaseEventHandler
from upbit_auto_trading.application.event_handlers.strategy_event_handlers import (
    StrategyCreatedHandler, StrategyUpdatedHandler, TriggerAddedHandler
)
from upbit_auto_trading.application.event_handlers.backtest_event_handlers import (
    BacktestStartedHandler, BacktestCompletedHandler, BacktestFailedHandler
)
from upbit_auto_trading.application.notifications.notification_service import NotificationService
from upbit_auto_trading.application.caching.cache_invalidation_service import CacheInvalidationService
from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher

class EventHandlerRegistry:
    """Event Handler 등록 및 관리"""
    
    def __init__(self, notification_service: NotificationService,
                 cache_service: CacheInvalidationService):
        self._notification_service = notification_service
        self._cache_service = cache_service
        self._handlers: Dict[Type[DomainEvent], List[BaseEventHandler]] = {}
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """모든 이벤트 핸들러 등록"""
        # 전략 관련 핸들러
        self._register_handler(StrategyCreatedHandler(self._notification_service))
        self._register_handler(StrategyUpdatedHandler(self._notification_service))
        self._register_handler(TriggerAddedHandler(self._notification_service))
        
        # 백테스팅 관련 핸들러
        self._register_handler(BacktestStartedHandler(self._notification_service))
        self._register_handler(BacktestCompletedHandler(self._notification_service))
        self._register_handler(BacktestFailedHandler(self._notification_service))
        
        # 캐시 무효화 핸들러 (통합)
        self._register_cache_invalidation_handlers()
    
    def _register_handler(self, handler: BaseEventHandler) -> None:
        """개별 핸들러 등록"""
        event_type = handler.get_event_type()
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def _register_cache_invalidation_handlers(self) -> None:
        """캐시 무효화 핸들러들 등록"""
        from upbit_auto_trading.domain.events.strategy_events import (
            StrategyCreated, StrategyUpdated, TriggerAdded, TriggerRemoved
        )
        from upbit_auto_trading.domain.events.backtest_events import BacktestCompleted
        
        # 전략 변경 시 캐시 무효화
        cache_handler = CacheInvalidationHandler(self._cache_service)
        self._register_handler(cache_handler)
    
    async def handle_event(self, event: DomainEvent) -> None:
        """이벤트 처리"""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            print(f"⚠️ 등록된 핸들러가 없습니다: {event_type.__name__}")
            return
        
        # 모든 핸들러를 병렬로 실행
        tasks = [handler.handle(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 발생한 핸들러 로깅
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                handler_name = handlers[i].__class__.__name__
                print(f"❌ 핸들러 실행 실패: {handler_name} - {result}")
    
    def register_with_event_publisher(self) -> None:
        """도메인 이벤트 게시자와 연동"""
        publisher = get_domain_event_publisher()
        
        # 모든 이벤트를 이 레지스트리로 라우팅
        async def event_router(event: DomainEvent):
            await self.handle_event(event)
        
        publisher.subscribe_global_async(event_router)
    
    def get_handler_count(self) -> Dict[str, int]:
        """등록된 핸들러 수 반환"""
        return {
            event_type.__name__: len(handlers)
            for event_type, handlers in self._handlers.items()
        }

class CacheInvalidationHandler(BaseEventHandler):
    """캐시 무효화 전용 핸들러"""
    
    def __init__(self, cache_service: CacheInvalidationService):
        super().__init__()
        self._cache_service = cache_service
    
    async def handle(self, event: DomainEvent) -> None:
        """이벤트 타입에 따른 캐시 무효화"""
        from upbit_auto_trading.domain.events.strategy_events import (
            StrategyCreated, StrategyUpdated, TriggerAdded, TriggerRemoved
        )
        from upbit_auto_trading.domain.events.backtest_events import BacktestCompleted
        
        if isinstance(event, (StrategyCreated, StrategyUpdated)):
            await self._cache_service.invalidate_strategy_related_cache(
                event.strategy_id.value
            )
        elif isinstance(event, (TriggerAdded, TriggerRemoved)):
            await self._cache_service.invalidate_trigger_related_cache(
                event.strategy_id.value
            )
        elif isinstance(event, BacktestCompleted):
            await self._cache_service.invalidate_backtest_related_cache(
                event.strategy_id.value
            )
    
    def get_event_type(self) -> type:
        # 모든 이벤트를 처리하므로 기본 DomainEvent 반환
        return DomainEvent
    
    def can_handle(self, event: DomainEvent) -> bool:
        """캐시 무효화가 필요한 이벤트인지 확인"""
        from upbit_auto_trading.domain.events.strategy_events import (
            StrategyCreated, StrategyUpdated, TriggerAdded, TriggerRemoved
        )
        from upbit_auto_trading.domain.events.backtest_events import BacktestCompleted
        
        return isinstance(event, (
            StrategyCreated, StrategyUpdated, TriggerAdded, TriggerRemoved, BacktestCompleted
        ))
```

### 9. **[테스트 코드 작성]** Event Handler 테스트
- [ ] `tests/application/event_handlers/` 폴더 생성
- [ ] `tests/application/event_handlers/test_strategy_event_handlers.py` 생성:
```python
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from upbit_auto_trading.application.event_handlers.strategy_event_handlers import StrategyCreatedHandler
from upbit_auto_trading.application.notifications.notification_service import NotificationService
from upbit_auto_trading.domain.events.strategy_events import StrategyCreated
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId

class TestStrategyCreatedHandler:
    def setup_method(self):
        self.notification_service = Mock(spec=NotificationService)
        self.notification_service.send_notification = AsyncMock()
        self.handler = StrategyCreatedHandler(self.notification_service)
    
    @pytest.mark.asyncio
    async def test_handle_strategy_created_event(self):
        # Given
        event = StrategyCreated(
            strategy_id=StrategyId("TEST_001"),
            strategy_name="테스트 전략",
            created_by="user"
        )
        
        # When
        await self.handler.handle(event)
        
        # Then
        self.notification_service.send_notification.assert_called_once()
        
        # 알림 내용 검증
        call_args = self.notification_service.send_notification.call_args[0][0]
        assert "테스트 전략" in call_args.message
        assert call_args.title == "전략 생성 완료"
    
    def test_get_event_type(self):
        # When
        event_type = self.handler.get_event_type()
        
        # Then
        assert event_type == StrategyCreated
```

### 10. **[통합]** Event Handler 시스템 통합
- [ ] `upbit_auto_trading/application/event_handlers/__init__.py` 생성:
```python
from .event_handler_registry import EventHandlerRegistry
from .base_event_handler import BaseEventHandler

__all__ = ['EventHandlerRegistry', 'BaseEventHandler']
```

- [ ] Application Service Container에 Event Handler 등록:
```python
# upbit_auto_trading/application/container.py 수정
class ApplicationServiceContainer:
    def __init__(self, repository_container):
        self._repo_container = repository_container
        self._services = {}
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Event Handler 시스템 초기화"""
        notification_service = NotificationService()
        cache_service = CacheInvalidationService()
        
        event_registry = EventHandlerRegistry(notification_service, cache_service)
        event_registry.register_with_event_publisher()
        
        self._services["notification"] = notification_service
        self._services["event_registry"] = event_registry
    
    def get_notification_service(self) -> NotificationService:
        return self._services["notification"]
```

## Verification Criteria (완료 검증 조건)

### **[Event Handler 동작 검증]** 모든 핸들러 정상 동작 확인
- [ ] `pytest tests/application/event_handlers/ -v` 실행하여 모든 테스트 통과
- [ ] Python REPL에서 이벤트 발행 및 핸들러 동작 확인:
```python
from upbit_auto_trading.domain.events.strategy_events import StrategyCreated
from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher
from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId

# 이벤트 발행
event = StrategyCreated(
    strategy_id=StrategyId("TEST_001"),
    strategy_name="테스트 전략"
)

publisher = get_domain_event_publisher()
publisher.publish(event)

print("✅ 이벤트 핸들러 동작 검증 완료")
```

### **[알림 시스템 검증]** Notification Service 정상 동작 확인
- [ ] 다양한 채널로 알림 전송 테스트
- [ ] 알림 히스토리 관리 기능 테스트
- [ ] 구독자 등록/해제 기능 테스트

### **[캐시 무효화 검증]** 캐시 무효화 로직 확인
- [ ] 전략 변경 시 관련 캐시 무효화 확인
- [ ] 백테스팅 완료 시 캐시 무효화 확인

### **[통합 검증]** Event Handler Registry 전체 동작 확인
- [ ] 모든 이벤트 타입에 대한 핸들러 등록 확인
- [ ] 병렬 핸들러 실행 및 예외 처리 확인

## Notes (주의사항)
- Event Handler는 이벤트 처리 실패가 전체 시스템에 영향을 주지 않도록 예외 격리 필수
- 알림 시스템은 UI와 느슨하게 결합되어야 하며, UI가 없어도 동작해야 함
- 캐시 무효화는 성능에 영향을 주므로 필요한 경우만 최소한으로 실행
- 모든 Event Handler는 비동기로 동작하여 도메인 로직 실행을 블로킹하지 않아야 함
