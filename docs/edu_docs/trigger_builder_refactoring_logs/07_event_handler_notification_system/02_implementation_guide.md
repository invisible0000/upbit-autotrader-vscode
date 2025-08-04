# 🛠️ Event Handler & Notification 시스템 구현 가이드

> **대상**: 주니어 개발자
> **목적**: DDD 기반 도메인 이벤트 시스템과 멀티채널 알림 시스템 구현 방법 습득
> **난이도**: 중급 (DDD 기본 지식 필요)

## 📋 구현 개요

### 🎯 시스템 목표
- **도메인 이벤트**: 비즈니스 로직과 부가 기능(알림, 캐시) 분리
- **멀티채널 알림**: UI Toast, Status Bar, Log File, System Notification 통합
- **캐시 무효화**: 도메인 변경 시 관련 캐시 자동 무효화
- **예외 격리**: 한 핸들러 실패가 다른 핸들러에 영향 없음

### 🏗️ 아키텍처 구조
```
application/
├── event_handlers/          # Event Handler 구현체
│   ├── strategy_event_handlers.py
│   ├── backtest_event_handlers.py
│   └── cache_invalidation_handler.py
├── services/               # 핵심 서비스
│   ├── notification_service.py
│   ├── cache_invalidation_service.py
│   └── event_handler_registry.py
└── dto/                   # 데이터 전송 객체
    └── notification_dto.py
```

## 🚀 단계별 구현 가이드

### Step 1: 기본 구조 생성 (15분)

#### 1.1 폴더 구조 생성
```powershell
# PowerShell에서 실행
New-Item -ItemType Directory -Path "upbit_auto_trading/application/event_handlers"
New-Item -ItemType Directory -Path "upbit_auto_trading/application/services"
New-Item -ItemType Directory -Path "upbit_auto_trading/application/dto"
```

#### 1.2 기본 DTO 정의
```python
# upbit_auto_trading/application/dto/notification_dto.py
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class NotificationChannel(Enum):
    UI_TOAST = "ui_toast"
    UI_STATUS_BAR = "ui_status_bar"
    LOG_FILE = "log_file"
    SYSTEM_NOTIFICATION = "system_notification"

class NotificationType(Enum):
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class Notification:
    id: str
    title: str
    message: str
    type: NotificationType
    channels: List[NotificationChannel]
    timestamp: datetime
    metadata: Dict[str, Any]
    read: bool = False
```

**💡 핵심 포인트**:
- Enum을 활용한 타입 안전성 확보
- dataclass로 간결한 DTO 정의
- 메타데이터로 확장성 제공

### Step 2: Event Handler Registry 구현 (20분)

```python
# upbit_auto_trading/application/services/event_handler_registry.py
from collections import defaultdict
from typing import List, Dict, Any, Type
from abc import ABC, abstractmethod

class EventHandler(ABC):
    @abstractmethod
    def handle(self, event: Any) -> None:
        pass

class EventHandlerRegistry:
    def __init__(self):
        self._handlers: Dict[Type, List[EventHandler]] = defaultdict(list)
        self._global_handlers: List[EventHandler] = []
        self.logger = get_integrated_logger("EventHandlerRegistry")

    def register_handler(self, event_type: Type, handler: EventHandler):
        """핸들러 등록 - CacheInvalidation은 글로벌 핸들러로 자동 분류"""
        if 'CacheInvalidation' in handler.__class__.__name__:
            self._global_handlers.append(handler)
            self.logger.info(f"글로벌 핸들러 등록: {handler.__class__.__name__}")
        else:
            self._handlers[event_type].append(handler)
            self.logger.info(f"이벤트 핸들러 등록: {event_type.__name__} -> {handler.__class__.__name__}")

    def publish_event(self, event: Any):
        """이벤트 발행 및 모든 핸들러 실행"""
        event_type = type(event)
        all_handlers = self._handlers[event_type] + self._global_handlers

        for handler in all_handlers:
            try:
                handler.handle(event)
            except Exception as e:
                self.logger.error(f"핸들러 {handler.__class__.__name__} 실행 실패: {e}")
                # 다른 핸들러는 계속 실행
```

**💡 핵심 포인트**:
- **예외 격리**: 한 핸들러 실패가 다른 핸들러에 영향 없음
- **글로벌 핸들러**: 모든 이벤트를 처리하는 핸들러 (캐시 무효화 등)
- **타입 기반 라우팅**: 이벤트 타입에 따른 자동 핸들러 선택

### Step 3: Notification Service 구현 (25분)

```python
# upbit_auto_trading/application/services/notification_service.py
from typing import Dict, List, Callable, Optional
from collections import defaultdict
import uuid
from datetime import datetime

class NotificationService:
    def __init__(self):
        self._subscribers: Dict[NotificationChannel, List[Callable]] = defaultdict(list)
        self._history: List[Notification] = []
        self.logger = get_integrated_logger("NotificationService")

    def send_notification(self, notification: Notification):
        """멀티채널 알림 전송"""
        self._history.append(notification)
        self.logger.info(f"알림 전송: {notification.title} -> {[ch.value for ch in notification.channels]}")

        for channel in notification.channels:
            message = self._format_message_for_channel(notification, channel)

            # 구독자들에게 알림 전송
            for callback in self._subscribers[channel]:
                try:
                    callback(message, notification)
                except Exception as e:
                    self.logger.error(f"알림 전송 실패 ({channel.value}): {e}")

    def _format_message_for_channel(self, notification: Notification, channel: NotificationChannel) -> str:
        """채널별 메시지 포맷팅"""
        if channel == NotificationChannel.UI_TOAST:
            # Toast: 짧고 간결하게 (30자 이내)
            icon = {"SUCCESS": "✅", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}
            return f"{icon.get(notification.type.name, '📝')} {notification.title}"

        elif channel == NotificationChannel.UI_STATUS_BAR:
            # Status Bar: 상태 정보 포함 (50자 이내)
            return f"📊 {notification.title} - {notification.metadata.get('status', '')}"

        elif channel == NotificationChannel.LOG_FILE:
            # Log: 상세 정보 포함
            return f"📝 {notification.title}: {notification.message}"

        else:  # SYSTEM_NOTIFICATION
            # System: 전체 메시지
            return f"🔔 {notification.title}\n{notification.message}"

    def subscribe(self, channel: NotificationChannel, callback: Callable):
        """채널 구독"""
        self._subscribers[channel].append(callback)
        self.logger.info(f"구독 등록: {channel.value}")

    def unsubscribe(self, channel: NotificationChannel, callback: Callable):
        """채널 구독 해제"""
        if callback in self._subscribers[channel]:
            self._subscribers[channel].remove(callback)
            self.logger.info(f"구독 해제: {channel.value}")
```

**💡 핵심 포인트**:
- **채널별 메시지 최적화**: Toast는 짧게, Log는 상세하게
- **구독자 패턴**: UI와 느슨한 결합
- **히스토리 관리**: 사용자 경험 향상

### Step 4: 캐시 무효화 서비스 구현 (20분)

```python
# upbit_auto_trading/application/services/cache_invalidation_service.py
from typing import Dict, List, Set
import fnmatch

class CacheInvalidationService:
    def __init__(self):
        self.invalidation_rules: Dict[str, List[str]] = {
            'strategy_changed': [
                'strategy_list_cache',
                'strategy_performance_cache',
                'dashboard_summary_cache',
                'active_strategies_cache'
            ],
            'trigger_changed': [
                'trigger_list_cache',
                'trigger_compatibility_cache'
            ],
            'backtest_completed': [
                'backtest_results_cache',
                'strategy_performance_cache',
                'dashboard_summary_cache'
            ]
        }
        self.logger = get_integrated_logger("CacheInvalidationService")

    def invalidate_for_strategy_change(self, strategy_id: str = None):
        """전략 변경 시 캐시 무효화"""
        cache_keys = self.invalidation_rules['strategy_changed']
        self._invalidate_caches(cache_keys, context={'strategy_id': strategy_id})

    def invalidate_for_backtest_completion(self, strategy_id: str = None):
        """백테스팅 완료 시 캐시 무효화"""
        cache_keys = self.invalidation_rules['backtest_completed']
        self._invalidate_caches(cache_keys, context={'strategy_id': strategy_id})

    def _invalidate_caches(self, cache_keys: List[str], context: Dict = None):
        """실제 캐시 무효화 실행"""
        for cache_key in cache_keys:
            try:
                # 실제 캐시 무효화 로직 (Redis, Memory Cache 등)
                self.logger.info(f"캐시 무효화: {cache_key}")
                if context:
                    self.logger.debug(f"컨텍스트: {context}")
            except Exception as e:
                self.logger.error(f"캐시 무효화 실패 ({cache_key}): {e}")
```

**💡 핵심 포인트**:
- **규칙 기반 무효화**: 설정으로 복잡성 관리
- **컨텍스트 정보**: 무효화 이유 추적
- **실패 격리**: 일부 캐시 실패가 전체에 영향 없음

### Step 5: Event Handler 구현체 (25분)

```python
# upbit_auto_trading/application/event_handlers/strategy_event_handlers.py
from upbit_auto_trading.domain.events import StrategyCreated, StrategyUpdated

class StrategyCreatedHandler(EventHandler):
    def __init__(self, notification_service, cache_service):
        self.notification_service = notification_service
        self.cache_service = cache_service
        self.logger = get_integrated_logger("StrategyCreatedHandler")

    def handle(self, event: StrategyCreated):
        """전략 생성 이벤트 처리"""
        # 1. 성공 알림 전송
        notification = Notification(
            id=str(uuid.uuid4()),
            title="전략 생성 완료",
            message=f"새로운 전략 '{event.strategy_name}'이 성공적으로 생성되었습니다.",
            type=NotificationType.SUCCESS,
            channels=[NotificationChannel.UI_TOAST, NotificationChannel.LOG_FILE],
            timestamp=datetime.now(),
            metadata={
                'strategy_id': event.strategy_id,
                'strategy_name': event.strategy_name,
                'event_type': 'strategy_created'
            }
        )
        self.notification_service.send_notification(notification)

        # 2. 캐시 무효화
        self.cache_service.invalidate_for_strategy_change(event.strategy_id)
        self.logger.info(f"전략 생성 이벤트 처리 완료: {event.strategy_name}")

class CacheInvalidationHandler(EventHandler):
    def __init__(self, cache_service):
        self.cache_service = cache_service
        self.logger = get_integrated_logger("CacheInvalidationHandler")

    def handle(self, event):
        """모든 이벤트에 대한 캐시 무효화 처리"""
        event_name = event.__class__.__name__

        if 'Strategy' in event_name:
            self.cache_service.invalidate_for_strategy_change(
                getattr(event, 'strategy_id', None)
            )
        elif 'Backtest' in event_name:
            self.cache_service.invalidate_for_backtest_completion(
                getattr(event, 'strategy_id', None)
            )

        self.logger.info(f"캐시 무효화 처리: {event_name}")
```

**💡 핵심 포인트**:
- **단일 책임**: 각 핸들러는 하나의 명확한 역할
- **메타데이터 활용**: 추적 가능한 이벤트 처리
- **글로벌 핸들러**: CacheInvalidationHandler는 모든 이벤트 처리

## 🧪 테스트 전략

### 단위 테스트 예시
```python
# tests/application/services/test_notification_service.py
def test_send_notification_multiple_channels():
    # Given
    service = NotificationService()
    test_callbacks = []

    # Mock 콜백 등록
    for channel in [NotificationChannel.UI_TOAST, NotificationChannel.LOG_FILE]:
        callback = Mock()
        service.subscribe(channel, callback)
        test_callbacks.append(callback)

    # When
    notification = Notification(
        id="test-id",
        title="테스트 알림",
        message="테스트 메시지",
        type=NotificationType.INFO,
        channels=[NotificationChannel.UI_TOAST, NotificationChannel.LOG_FILE],
        timestamp=datetime.now(),
        metadata={}
    )
    service.send_notification(notification)

    # Then
    assert len(service._history) == 1
    for callback in test_callbacks:
        callback.assert_called_once()
```

### 통합 테스트 스크립트
```python
# test_event_system_integration.py
def test_complete_event_flow():
    """전체 이벤트 플로우 통합 테스트"""
    # 1. 서비스 초기화
    registry = EventHandlerRegistry()
    notification_service = NotificationService()
    cache_service = CacheInvalidationService()

    # 2. 핸들러 등록
    strategy_handler = StrategyCreatedHandler(notification_service, cache_service)
    cache_handler = CacheInvalidationHandler(cache_service)

    registry.register_handler(StrategyCreated, strategy_handler)
    registry.register_handler(StrategyCreated, cache_handler)

    # 3. 이벤트 발행
    event = StrategyCreated(
        strategy_id="test-strategy-id",
        strategy_name="테스트 전략"
    )
    registry.publish_event(event)

    # 4. 결과 검증
    assert len(notification_service._history) == 1
    assert "전략 생성 완료" in notification_service._history[0].title
```

## ⚠️ 주의사항 및 베스트 프랙티스

### 1. 성능 고려사항
```python
# ❌ 잘못된 방식: 동기 처리
def publish_event(self, event):
    for handler in handlers:
        handler.handle(event)  # 하나 실패하면 전체 블로킹

# ✅ 올바른 방식: 예외 격리
def publish_event(self, event):
    for handler in handlers:
        try:
            handler.handle(event)
        except Exception as e:
            self.logger.error(f"핸들러 실패: {e}")
            # 다른 핸들러는 계속 실행
```

### 2. 메모리 관리
```python
# 알림 히스토리 크기 제한
class NotificationService:
    def __init__(self, max_history=1000):
        self.max_history = max_history

    def send_notification(self, notification):
        self._history.append(notification)
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
```

### 3. 로깅 전략
```python
# 구조화된 로깅
self.logger.info(
    f"이벤트 처리 완료",
    extra={
        'event_type': event.__class__.__name__,
        'handler': self.__class__.__name__,
        'processing_time': processing_time,
        'metadata': event_metadata
    }
)
```

## 📚 확장 포인트

### 1. 비동기 처리 추가
```python
import asyncio

class AsyncEventHandlerRegistry(EventHandlerRegistry):
    async def publish_event_async(self, event):
        tasks = []
        for handler in self.get_handlers(event):
            if hasattr(handler, 'handle_async'):
                tasks.append(handler.handle_async(event))
            else:
                tasks.append(asyncio.create_task(self._sync_to_async(handler, event)))

        await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. 이벤트 재시도 메커니즘
```python
class RetryableEventHandler(EventHandler):
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def handle_with_retry(self, event):
        for attempt in range(self.max_retries):
            try:
                return self.handle(event)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
```

---

**💡 핵심 원칙**: "이벤트 기반 시스템은 느슨한 결합과 예외 격리가 핵심이다!"

**🎯 다음 단계**: Infrastructure Layer와 연동하여 실제 캐시 시스템과 UI 알림 연결
