# ⚡ 이벤트 시스템 가이드

> **목적**: Domain Event와 Application Event 구현 및 활용  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 이벤트 시스템 개요

### 이벤트 계층 구조
```
💎 Domain Events     ← 비즈니스 중요 사건 (전략 생성, 조건 활성화)
⚙️ Application Events ← 유스케이스 완료 (백테스트 완료, 저장 완료)
🎨 UI Events         ← 사용자 인터페이스 (화면 갱신, 알림 표시)
```

### 이벤트 처리 흐름
```python
Entity.do_something() → Domain Event 발생 → Event Publisher → Event Handlers → Side Effects
```

## 💎 Domain Events (도메인 이벤트)

### 기본 도메인 이벤트 클래스
```python
from abc import ABC
from datetime import datetime
from typing import Dict, Any
import uuid

class DomainEvent(ABC):
    """도메인 이벤트 기본 클래스"""
    def __init__(self):
        self.event_id = str(uuid.uuid4())
        self.occurred_at = datetime.utcnow()
        
    @property
    def event_name(self) -> str:
        return self.__class__.__name__
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_name': self.event_name,
            'occurred_at': self.occurred_at.isoformat(),
            'data': self._get_event_data()
        }
        
    def _get_event_data(self) -> Dict[str, Any]:
        """서브클래스에서 이벤트별 데이터 구현"""
        return {}
```

### 구체적 도메인 이벤트 예시
```python
class StrategyCreatedEvent(DomainEvent):
    """전략 생성 이벤트"""
    def __init__(self, strategy_id: str, strategy_name: str):
        super().__init__()
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name
        
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name
        }

class ConditionActivatedEvent(DomainEvent):
    """조건 활성화 이벤트"""
    def __init__(self, condition_id: str, trigger_value: float):
        super().__init__()
        self.condition_id = condition_id
        self.trigger_value = trigger_value
        
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'condition_id': self.condition_id,
            'trigger_value': self.trigger_value
        }
```

### Entity에서 이벤트 발생
```python
class Strategy:
    """전략 Entity - 이벤트 발생"""
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self._events: List[DomainEvent] = []
        
    def add_rule(self, rule: TradingRule):
        """규칙 추가 + 이벤트 발행"""
        if len(self.rules) >= 10:
            raise MaxRulesExceededError()
            
        self.rules.append(rule)
        
        # ✅ 도메인 이벤트 추가
        self.add_event(RuleAddedEvent(
            strategy_id=self.id,
            rule_id=rule.id,
            rule_type=rule.type
        ))
        
    def add_event(self, event: DomainEvent):
        """이벤트 내부 저장"""
        self._events.append(event)
        
    def get_events(self) -> List[DomainEvent]:
        """발생한 이벤트들 반환"""
        events = self._events.copy()
        self._events.clear()  # 이벤트 소비 후 초기화
        return events
```

## ⚙️ Event Publishing (이벤트 발행)

### Event Publisher 인터페이스
```python
from abc import ABC, abstractmethod
from typing import List

class EventPublisher(ABC):
    """이벤트 발행자 인터페이스"""
    
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """단일 이벤트 발행"""
        pass
        
    @abstractmethod
    def publish_all(self, events: List[DomainEvent]) -> None:
        """여러 이벤트 일괄 발행"""
        pass

class InMemoryEventPublisher(EventPublisher):
    """메모리 기반 이벤트 발행자"""
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        
    def subscribe(self, event_name: str, handler: 'EventHandler'):
        """이벤트 핸들러 등록"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        
    def publish(self, event: DomainEvent) -> None:
        """이벤트 발행 및 핸들러 실행"""
        handlers = self._handlers.get(event.event_name, [])
        for handler in handlers:
            try:
                handler.handle(event)
            except Exception as e:
                # 이벤트 처리 실패가 원래 작업을 방해하지 않도록
                print(f"⚠️ 이벤트 핸들러 오류: {e}")
                
    def publish_all(self, events: List[DomainEvent]) -> None:
        """여러 이벤트 일괄 발행"""
        for event in events:
            self.publish(event)
```

### Application Layer에서 이벤트 발행
```python
class StrategyService:
    """Application Service - 이벤트 발행 책임"""
    def __init__(self, strategy_repo, event_publisher):
        self.strategy_repo = strategy_repo
        self.event_publisher = event_publisher
        
    def create_strategy(self, command: CreateStrategyCommand) -> str:
        """전략 생성 및 이벤트 발행"""
        # 1. 도메인 로직 실행
        strategy = Strategy(command.name)
        strategy.add_rules(command.rules)
        
        # 2. 영속화
        self.strategy_repo.save(strategy)
        
        # 3. 도메인 이벤트 발행
        events = strategy.get_events()
        self.event_publisher.publish_all(events)
        
        return strategy.id
```

## 🎯 Event Handlers (이벤트 핸들러)

### Event Handler 인터페이스
```python
class EventHandler(ABC):
    """이벤트 핸들러 기본 클래스"""
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """이벤트 처리 로직"""
        pass
        
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """처리 가능한 이벤트인지 확인"""
        pass
```

### 구체적 이벤트 핸들러 예시
```python
class StrategyNotificationHandler(EventHandler):
    """전략 관련 알림 핸들러"""
    def __init__(self, notification_service):
        self.notification_service = notification_service
        
    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, (StrategyCreatedEvent, StrategyActivatedEvent))
        
    def handle(self, event: DomainEvent) -> None:
        if isinstance(event, StrategyCreatedEvent):
            self.notification_service.notify_strategy_created(
                event.strategy_id, event.strategy_name
            )
        elif isinstance(event, StrategyActivatedEvent):
            self.notification_service.notify_strategy_activated(
                event.strategy_id
            )

class BacktestCacheHandler(EventHandler):
    """백테스트 캐시 관리 핸들러"""
    def __init__(self, cache_service):
        self.cache_service = cache_service
        
    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, (StrategyModifiedEvent, RuleAddedEvent))
        
    def handle(self, event: DomainEvent) -> None:
        """전략 변경 시 관련 백테스트 캐시 무효화"""
        if hasattr(event, 'strategy_id'):
            self.cache_service.invalidate_backtest_cache(event.strategy_id)
            print(f"🗑️ 백테스트 캐시 무효화: {event.strategy_id}")
```

## 🎨 UI Event Integration

### Presenter에서 Domain Event 구독
```python
class StrategyBuilderPresenter:
    """Presenter가 Domain Event 구독"""
    def __init__(self, view, strategy_service, event_publisher):
        self.view = view
        self.strategy_service = strategy_service
        self.event_publisher = event_publisher
        
        # ✅ Domain Event 구독
        self.event_publisher.subscribe('StrategyCreatedEvent', self)
        self.event_publisher.subscribe('RuleAddedEvent', self)
        
    def handle(self, event: DomainEvent) -> None:
        """Domain Event 처리 → UI 갱신"""
        if isinstance(event, StrategyCreatedEvent):
            self.view.show_success_message(f"전략 '{event.strategy_name}' 생성 완료")
            self.view.refresh_strategy_list()
            
        elif isinstance(event, RuleAddedEvent):
            self.view.update_rule_count(event.strategy_id)
            self.view.enable_backtest_button()
```

### UI Event와 Domain Event 분리
```python
# ✅ UI Event (View 내부)
class TriggerBuilderView(QWidget):
    # PyQt 시그널 (UI Event)
    variable_selected = pyqtSignal(str)
    parameter_changed = pyqtSignal(str, object)
    
    def on_variable_click(self, variable_id: str):
        """UI 이벤트 발생"""
        self.variable_selected.emit(variable_id)  # UI Event
        
# ✅ Domain Event (Presenter → Service)
class TriggerBuilderPresenter:
    def on_variable_selected(self, variable_id: str):
        """UI Event → Domain Event 변환"""
        # Domain Service 호출 → Domain Event 발생
        self.trigger_service.select_variable(variable_id)
```

## 🔄 Event Sourcing (이벤트 소싱)

### 이벤트 저장소
```python
class EventStore:
    """이벤트 영속화 저장소"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def append_event(self, event: DomainEvent) -> None:
        """이벤트 저장"""
        query = """
        INSERT INTO event_store (event_id, event_name, occurred_at, event_data)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute(query, (
            event.event_id,
            event.event_name,
            event.occurred_at,
            json.dumps(event.to_dict())
        ))
        
    def get_events(self, entity_id: str) -> List[DomainEvent]:
        """특정 엔티티의 이벤트 히스토리 조회"""
        query = """
        SELECT event_data FROM event_store 
        WHERE event_data LIKE ? 
        ORDER BY occurred_at
        """
        rows = self.db.execute(query, (f'%"entity_id":"{entity_id}"%',)).fetchall()
        
        events = []
        for row in rows:
            event_data = json.loads(row[0])
            event = self._reconstruct_event(event_data)
            events.append(event)
            
        return events
```

## 📊 이벤트 모니터링

### 이벤트 로깅
```python
class EventLogger(EventHandler):
    """이벤트 로깅 핸들러"""
    def __init__(self, logger):
        self.logger = logger
        
    def can_handle(self, event: DomainEvent) -> bool:
        return True  # 모든 이벤트 로깅
        
    def handle(self, event: DomainEvent) -> None:
        self.logger.info(
            f"📅 이벤트 발생: {event.event_name} | "
            f"ID: {event.event_id} | "
            f"시간: {event.occurred_at}"
        )

class EventMetrics:
    """이벤트 지표 수집"""
    def __init__(self):
        self.event_counts: Dict[str, int] = {}
        self.processing_times: Dict[str, List[float]] = {}
        
    def record_event(self, event_name: str, processing_time: float):
        # 이벤트 카운트
        self.event_counts[event_name] = self.event_counts.get(event_name, 0) + 1
        
        # 처리 시간 기록
        if event_name not in self.processing_times:
            self.processing_times[event_name] = []
        self.processing_times[event_name].append(processing_time)
```

## 🚀 성능 최적화

### 비동기 이벤트 처리
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncEventPublisher(EventPublisher):
    """비동기 이벤트 발행자"""
    def __init__(self, max_workers=4):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def publish_async(self, event: DomainEvent) -> None:
        """비동기 이벤트 발행"""
        handlers = self._handlers.get(event.event_name, [])
        
        # 모든 핸들러를 병렬로 실행
        tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._run_handler(handler, event))
            tasks.append(task)
            
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def _run_handler(self, handler: EventHandler, event: DomainEvent):
        """핸들러 실행 (오류 처리 포함)"""
        try:
            if asyncio.iscoroutinefunction(handler.handle):
                await handler.handle(event)
            else:
                # 동기 핸들러는 별도 스레드에서 실행
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, handler.handle, event)
        except Exception as e:
            print(f"⚠️ 비동기 이벤트 핸들러 오류: {e}")
```

### 이벤트 배칭
```python
class BatchEventPublisher(EventPublisher):
    """배치 이벤트 발행자"""
    def __init__(self, batch_size=10, flush_interval=1.0):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._batch: List[DomainEvent] = []
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._start_flush_timer()
        
    def publish(self, event: DomainEvent) -> None:
        """배치에 이벤트 추가"""
        self._batch.append(event)
        
        if len(self._batch) >= self.batch_size:
            self._flush_batch()
            
    def _flush_batch(self):
        """배치 이벤트 일괄 처리"""
        if not self._batch:
            return
            
        events_to_process = self._batch.copy()
        self._batch.clear()
        
        for event in events_to_process:
            handlers = self._handlers.get(event.event_name, [])
            for handler in handlers:
                try:
                    handler.handle(event)
                except Exception as e:
                    print(f"⚠️ 배치 이벤트 핸들러 오류: {e}")
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 이벤트 시스템의 전체 위치
- [상태 관리](07_STATE_MANAGEMENT.md): 상태 변경 이벤트 패턴  
- [성능 최적화](09_PERFORMANCE_OPTIMIZATION.md): 이벤트 처리 성능 향상
- [문제 해결](06_TROUBLESHOOTING.md): 이벤트 관련 문제 해결

---
**💡 핵심**: "Domain Event로 계층 간 결합도를 낮추고, 시스템의 확장성을 높이세요!"
