# ⚡ 이벤트 시스템 가이드

> **목적**: Domain Event와 UI Event 시스템 구현 및 활용  
> **대상**: 개발자, 아키텍처 설계자  
> **예상 읽기 시간**: 14분

## 🎯 Clean Architecture 이벤트 시스템

### 📊 이벤트 계층 구조
```
Domain Events     ← 비즈니스 중요 사건 (ConditionCreated, StrategyActivated)
     ↓
Application Events ← 유스케이스 완료 알림 (ConditionProcessed, BacktestCompleted)  
     ↓
UI Events         ← 사용자 인터페이스 갱신 (ViewRefresh, NotificationShow)
```

## 💎 Domain Events (도메인 이벤트)

### 1. 도메인 이벤트 정의
```python
# domain/events/base_domain_event.py
from abc import ABC
from datetime import datetime
from typing import Dict, Any
import uuid

class DomainEvent(ABC):
    """도메인 이벤트 기본 클래스"""
    
    def __init__(self):
        self.event_id = str(uuid.uuid4())
        self.occurred_at = datetime.utcnow()
        self.version = 1
    
    @property
    def event_name(self) -> str:
        return self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """이벤트를 딕셔너리로 변환"""
        return {
            'event_id': self.event_id,
            'event_name': self.event_name,
            'occurred_at': self.occurred_at.isoformat(),
            'version': self.version,
            'data': self._get_event_data()
        }
    
    def _get_event_data(self) -> Dict[str, Any]:
        """서브클래스에서 구현할 이벤트 데이터"""
        return {}

# domain/events/condition_events.py
class ConditionCreatedEvent(DomainEvent):
    """조건 생성 이벤트"""
    
    def __init__(self, condition_id: str, variable_id: str, operator: str, target_value: str):
        super().__init__()
        self.condition_id = condition_id
        self.variable_id = variable_id
        self.operator = operator
        self.target_value = target_value
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'condition_id': self.condition_id,
            'variable_id': self.variable_id,
            'operator': self.operator,
            'target_value': self.target_value
        }

class ConditionActivatedEvent(DomainEvent):
    """조건 활성화 이벤트"""
    
    def __init__(self, condition_id: str, activation_time: datetime):
        super().__init__()
        self.condition_id = condition_id
        self.activation_time = activation_time
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            'condition_id': self.condition_id,
            'activation_time': self.activation_time.isoformat()
        }
```

### 2. 엔티티에서 이벤트 발생
```python
# domain/entities/trading_condition.py
class TradingCondition:
    """거래 조건 엔티티"""
    
    def __init__(self, condition_id, variable, operator, target_value):
        self.id = condition_id
        self.variable = variable
        self.operator = operator
        self.target_value = target_value
        self._events = []  # 도메인 이벤트 저장
    
    @classmethod
    def create(cls, variable, operator, target_value):
        """조건 생성 - 도메인 이벤트 발생"""
        condition_id = ConditionId.generate()
        condition = cls(condition_id, variable, operator, target_value)
        
        # ✅ 도메인 이벤트 발생
        condition._add_event(
            ConditionCreatedEvent(
                condition_id=condition_id.value,
                variable_id=variable.id.value,
                operator=operator,
                target_value=target_value
            )
        )
        
        return condition
    
    def activate(self):
        """조건 활성화"""
        if self.is_active:
            raise ConditionAlreadyActiveError()
        
        self.is_active = True
        self.activated_at = datetime.utcnow()
        
        # ✅ 활성화 이벤트 발생
        self._add_event(
            ConditionActivatedEvent(
                condition_id=self.id.value,
                activation_time=self.activated_at
            )
        )
    
    def _add_event(self, event: DomainEvent):
        """도메인 이벤트 추가"""
        self._events.append(event)
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """커밋되지 않은 이벤트 조회"""
        return self._events.copy()
    
    def mark_events_as_committed(self):
        """이벤트를 커밋됨으로 표시"""
        self._events.clear()
```

## ⚙️ Application Layer 이벤트 처리

### 1. 이벤트 발행자 (Event Publisher)
```python
# application/events/event_publisher.py
from abc import ABC, abstractmethod
from typing import List

class EventPublisher(ABC):
    """이벤트 발행자 인터페이스"""
    
    @abstractmethod
    def publish(self, event: DomainEvent):
        """이벤트 발행"""
        pass
    
    @abstractmethod
    def publish_batch(self, events: List[DomainEvent]):
        """배치 이벤트 발행"""
        pass

# application/events/in_memory_event_publisher.py
class InMemoryEventPublisher(EventPublisher):
    """메모리 기반 이벤트 발행자"""
    
    def __init__(self):
        self._handlers = {}  # {event_type: [handler1, handler2, ...]}
    
    def register_handler(self, event_type: type, handler):
        """이벤트 핸들러 등록"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def publish(self, event: DomainEvent):
        """단일 이벤트 발행"""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                handler.handle(event)
            except Exception as e:
                # 이벤트 처리 실패는 로그만 남기고 계속 진행
                logger.error(f"이벤트 처리 실패: {event.event_name}, 핸들러: {handler.__class__.__name__}, 오류: {str(e)}")
    
    def publish_batch(self, events: List[DomainEvent]):
        """배치 이벤트 발행"""
        for event in events:
            self.publish(event)
```

### 2. 이벤트 핸들러 구현
```python
# application/events/handlers/condition_event_handlers.py
class ConditionCreatedEventHandler:
    """조건 생성 이벤트 핸들러"""
    
    def __init__(self, notification_service, analytics_service):
        self.notification_service = notification_service
        self.analytics_service = analytics_service
    
    def handle(self, event: ConditionCreatedEvent):
        """조건 생성 이벤트 처리"""
        try:
            # 1. 사용자 알림
            self.notification_service.send_notification(
                message=f"새 조건이 생성되었습니다: {event.variable_id} {event.operator} {event.target_value}",
                type="info"
            )
            
            # 2. 분석 데이터 수집
            self.analytics_service.track_event("condition_created", {
                "variable_id": event.variable_id,
                "operator": event.operator,
                "timestamp": event.occurred_at
            })
            
            # 3. 캐시 무효화 (필요시)
            # self.cache_service.invalidate_condition_cache()
            
        except Exception as e:
            logger.error(f"조건 생성 이벤트 처리 실패: {str(e)}")

class ConditionActivatedEventHandler:
    """조건 활성화 이벤트 핸들러"""
    
    def __init__(self, trading_signal_service, position_service):
        self.trading_signal_service = trading_signal_service
        self.position_service = position_service
    
    def handle(self, event: ConditionActivatedEvent):
        """조건 활성화 이벤트 처리"""
        try:
            # 1. 매매 신호 생성
            signal = self.trading_signal_service.generate_signal_for_condition(
                event.condition_id
            )
            
            # 2. 포지션 관리 시스템에 알림
            if signal.action != "HOLD":
                self.position_service.process_trading_signal(signal)
                
        except Exception as e:
            logger.error(f"조건 활성화 이벤트 처리 실패: {str(e)}")
```

### 3. Application Service에서 이벤트 발행
```python
# application/services/condition_creation_service.py
class ConditionCreationService:
    """조건 생성 서비스"""
    
    def __init__(self, condition_repo, event_publisher, unit_of_work):
        self.condition_repo = condition_repo
        self.event_publisher = event_publisher
        self.unit_of_work = unit_of_work
    
    def create_condition(self, command: CreateConditionCommand):
        """조건 생성 유스케이스"""
        try:
            with self.unit_of_work.transaction():
                # 1. 도메인 객체 생성 (이벤트 자동 생성됨)
                condition = TradingCondition.create(
                    variable=command.variable,
                    operator=command.operator,
                    target_value=command.target_value
                )
                
                # 2. 저장
                self.condition_repo.save(condition)
                
                # 3. ✅ 도메인 이벤트 발행
                events = condition.get_uncommitted_events()
                for event in events:
                    self.event_publisher.publish(event)
                
                condition.mark_events_as_committed()
            
            return Result.ok(CreateConditionResult(condition))
            
        except Exception as e:
            return Result.fail(str(e))
```

## 🎨 UI Layer 이벤트 시스템

### 1. UI 이벤트 정의
```python
# presentation/events/ui_events.py
class UIEvent:
    """UI 이벤트 기본 클래스"""
    
    def __init__(self, event_type: str, data: dict = None):
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = datetime.utcnow()

class ConditionListRefreshEvent(UIEvent):
    """조건 목록 새로고침 이벤트"""
    
    def __init__(self):
        super().__init__("condition_list_refresh")

class NotificationShowEvent(UIEvent):
    """알림 표시 이벤트"""
    
    def __init__(self, message: str, notification_type: str = "info"):
        super().__init__("notification_show", {
            "message": message,
            "type": notification_type
        })
```

### 2. UI 이벤트 버스
```python
# presentation/events/ui_event_bus.py
from PyQt6.QtCore import QObject, pyqtSignal

class UIEventBus(QObject):
    """UI 이벤트 버스 (Qt 시그널/슬롯 기반)"""
    
    # Qt 시그널 정의
    condition_list_refresh_requested = pyqtSignal()
    notification_requested = pyqtSignal(str, str)  # message, type
    strategy_updated = pyqtSignal(str)  # strategy_id
    
    _instance = None
    
    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def emit_condition_list_refresh(self):
        """조건 목록 새로고침 이벤트 발행"""
        self.condition_list_refresh_requested.emit()
    
    def emit_notification(self, message: str, notification_type: str = "info"):
        """알림 이벤트 발행"""
        self.notification_requested.emit(message, notification_type)
    
    def emit_strategy_updated(self, strategy_id: str):
        """전략 업데이트 이벤트 발행"""
        self.strategy_updated.emit(strategy_id)

# 전역 이벤트 버스 인스턴스
ui_event_bus = UIEventBus()
```

### 3. Domain Event → UI Event 연결
```python
# application/events/handlers/ui_event_handlers.py
class UIUpdateEventHandler:
    """UI 업데이트 이벤트 핸들러"""
    
    def __init__(self, ui_event_bus):
        self.ui_event_bus = ui_event_bus
    
    def handle_condition_created(self, event: ConditionCreatedEvent):
        """조건 생성 → UI 업데이트"""
        # UI 이벤트 발행
        self.ui_event_bus.emit_condition_list_refresh()
        self.ui_event_bus.emit_notification(
            f"조건 '{event.variable_id} {event.operator} {event.target_value}'이 생성되었습니다",
            "success"
        )
    
    def handle_condition_activated(self, event: ConditionActivatedEvent):
        """조건 활성화 → UI 알림"""
        self.ui_event_bus.emit_notification(
            f"조건이 활성화되었습니다",
            "warning"
        )

# 이벤트 핸들러 등록
def setup_ui_event_handlers(event_publisher, ui_event_bus):
    """UI 이벤트 핸들러 설정"""
    ui_handler = UIUpdateEventHandler(ui_event_bus)
    
    event_publisher.register_handler(
        ConditionCreatedEvent, 
        ui_handler.handle_condition_created
    )
    event_publisher.register_handler(
        ConditionActivatedEvent,
        ui_handler.handle_condition_activated
    )
```

### 4. View에서 이벤트 구독
```python
# presentation/views/condition_list_view.py
class ConditionListView(QWidget):
    """조건 목록 View"""
    
    def __init__(self):
        super().__init__()
        self.presenter = None
        self.setup_ui()
        self.setup_event_subscriptions()
    
    def setup_event_subscriptions(self):
        """이벤트 구독 설정"""
        from presentation.events.ui_event_bus import ui_event_bus
        
        # 조건 목록 새로고침 이벤트 구독
        ui_event_bus.condition_list_refresh_requested.connect(
            self.refresh_condition_list
        )
        
        # 알림 이벤트 구독
        ui_event_bus.notification_requested.connect(
            self.show_notification
    
    def refresh_condition_list(self):
        """조건 목록 새로고침"""
        if self.presenter:
            self.presenter.load_condition_list()
    
    def show_notification(self, message: str, notification_type: str):
        """알림 표시"""
        if notification_type == "success":
            QMessageBox.information(self, "성공", message)
        elif notification_type == "warning":
            QMessageBox.warning(self, "주의", message)
        elif notification_type == "error":
            QMessageBox.critical(self, "오류", message)
```

## 🔄 이벤트 저장소 (Event Store)

### Infrastructure Layer 이벤트 저장
```python
# infrastructure/events/sqlite_event_store.py
class SQLiteEventStore:
    """SQLite 기반 이벤트 저장소"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._ensure_event_table()
    
    def store_event(self, event: DomainEvent):
        """이벤트 저장"""
        query = """
        INSERT INTO domain_events 
        (event_id, event_name, aggregate_id, event_data, occurred_at, version)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        event_dict = event.to_dict()
        
        self.db.execute(query, (
            event.event_id,
            event.event_name,
            self._extract_aggregate_id(event),
            json.dumps(event_dict['data']),
            event.occurred_at,
            event.version
        ))
    
    def get_events_by_aggregate(self, aggregate_id: str) -> List[dict]:
        """집합체별 이벤트 조회"""
        query = """
        SELECT * FROM domain_events 
        WHERE aggregate_id = ? 
        ORDER BY occurred_at ASC
        """
        
        return self.db.fetchall(query, (aggregate_id,))
    
    def _ensure_event_table(self):
        """이벤트 테이블 생성"""
        query = """
        CREATE TABLE IF NOT EXISTS domain_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            event_name TEXT NOT NULL,
            aggregate_id TEXT,
            event_data TEXT NOT NULL,
            occurred_at TIMESTAMP NOT NULL,
            version INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(query)
    
    def _extract_aggregate_id(self, event: DomainEvent) -> str:
        """이벤트에서 집합체 ID 추출"""
        if hasattr(event, 'condition_id'):
            return event.condition_id
        elif hasattr(event, 'strategy_id'):
            return event.strategy_id
        return ""
```

## 🚀 이벤트 시스템 초기화

```python
# main.py 또는 의존성 주입 설정
def setup_event_system():
    """이벤트 시스템 초기화"""
    
    # 1. 이벤트 발행자 생성
    event_publisher = InMemoryEventPublisher()
    
    # 2. 이벤트 저장소 생성
    event_store = SQLiteEventStore(db_connection)
    
    # 3. 도메인 이벤트 핸들러 등록
    condition_handler = ConditionCreatedEventHandler(
        notification_service, analytics_service
    )
    event_publisher.register_handler(ConditionCreatedEvent, condition_handler)
    
    # 4. UI 이벤트 핸들러 등록
    setup_ui_event_handlers(event_publisher, ui_event_bus)
    
    # 5. 이벤트 저장 핸들러 등록 (모든 이벤트 저장)
    def store_all_events(event):
        event_store.store_event(event)
    
    for event_type in [ConditionCreatedEvent, ConditionActivatedEvent]:
        event_publisher.register_handler(event_type, store_all_events)
    
    return event_publisher
```

## 🔍 다음 단계

- **[성능 최적화](10_PERFORMANCE_OPTIMIZATION.md)**: 이벤트 처리 성능 향상
- **[에러 처리](11_ERROR_HANDLING.md)**: 이벤트 처리 실패 대응
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 이벤트 흐름 추적

---
**💡 핵심**: "이벤트 시스템으로 계층 간 느슨한 결합을 유지하면서 비즈니스 로직과 UI를 동기화합니다!"
