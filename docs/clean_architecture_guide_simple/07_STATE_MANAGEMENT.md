# 🔧 상태 관리 시스템

> **목적**: Clean Architecture에서 애플리케이션 상태 추적 및 관리  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 상태 관리 개요

### 상태 관리의 필요성
- **UI 상태**: 사용자 인터페이스 현재 상태 (선택된 전략, 입력값)
- **비즈니스 상태**: 도메인 객체 상태 (전략 실행 상태, 포지션 정보)
- **애플리케이션 상태**: 시스템 전체 상태 (로그인, 설정)

### 계층별 상태 책임
```
🎨 Presentation → UI 상태 (View State)
⚙️ Application  → 세션 상태 (Session State)  
💎 Domain       → 비즈니스 상태 (Entity State)
🔌 Infrastructure → 영속 상태 (Persistent State)
```

## 🏗️ 상태 관리 패턴

### 1. 단일 진실 원천 (Single Source of Truth)
```python
# ✅ 올바른 상태 관리
class TradingStrategyState:
    """전략 상태의 유일한 원천"""
    def __init__(self):
        self._strategies: Dict[str, Strategy] = {}
        self._active_strategy_id: Optional[str] = None
        
    def get_active_strategy(self) -> Optional[Strategy]:
        if self._active_strategy_id:
            return self._strategies.get(self._active_strategy_id)
        return None
        
    def set_active_strategy(self, strategy_id: str):
        if strategy_id in self._strategies:
            self._active_strategy_id = strategy_id
            self._notify_state_changed()

# ❌ 잘못된 상태 관리 - 상태 분산
class StrategyView:
    def __init__(self):
        self.current_strategy = None  # ❌ UI에 비즈니스 상태

class StrategyService:
    def __init__(self):
        self.active_strategy = None  # ❌ Service에도 동일 상태
```

### 2. 상태 변경 추적 (State Change Tracking)
```python
class StateManager:
    """상태 변경 추적 및 관리"""
    def __init__(self):
        self._observers: List[StateObserver] = []
        self._state_history: List[StateSnapshot] = []
        
    def register_observer(self, observer: StateObserver):
        self._observers.append(observer)
        
    def _notify_state_changed(self, old_state, new_state):
        # 상태 변경 히스토리 기록
        snapshot = StateSnapshot(old_state, new_state, datetime.now())
        self._state_history.append(snapshot)
        
        # 관찰자들에게 알림
        for observer in self._observers:
            observer.on_state_changed(old_state, new_state)

class StateSnapshot:
    """상태 스냅샷 - 디버깅과 복원에 활용"""
    def __init__(self, old_state, new_state, timestamp):
        self.old_state = old_state
        self.new_state = new_state
        self.timestamp = timestamp
```

## 🎨 UI 상태 관리

### MVP 패턴에서 상태 관리
```python
class TriggerBuilderView(QWidget):
    """View는 UI 상태만 관리"""
    def __init__(self):
        super().__init__()
        self._ui_state = TriggerBuilderUIState()
        self.presenter = None
        
    def set_selected_variable(self, variable_id: str):
        # ✅ UI 상태만 변경
        self._ui_state.selected_variable_id = variable_id
        self._update_ui_display()
        
        # ✅ 비즈니스 로직은 Presenter에 위임
        if self.presenter:
            self.presenter.on_variable_selected(variable_id)

class TriggerBuilderUIState:
    """UI 전용 상태 객체"""
    def __init__(self):
        self.selected_variable_id: Optional[str] = None
        self.parameter_values: Dict[str, Any] = {}
        self.validation_errors: List[str] = []
        self.is_loading: bool = False

class TriggerBuilderPresenter:
    """Presenter는 UI와 비즈니스 상태 연결"""
    def __init__(self, view, trigger_service):
        self.view = view
        self.trigger_service = trigger_service
        
    def on_variable_selected(self, variable_id: str):
        # ✅ 비즈니스 로직 처리
        variable = self.trigger_service.get_variable(variable_id)
        
        # ✅ UI 상태 업데이트
        self.view.update_parameter_form(variable.parameters)
```

### 상태 동기화 패턴
```python
class ViewStateSync:
    """View 간 상태 동기화"""
    def __init__(self):
        self._views: List[StatefulView] = []
        
    def register_view(self, view: StatefulView):
        self._views.append(view)
        
    def sync_state(self, state_key: str, state_value: Any):
        """모든 관련 View에 상태 변경 알림"""
        for view in self._views:
            if view.handles_state(state_key):
                view.update_state(state_key, state_value)

# 사용 예시
class StrategyListView(StatefulView):
    def handles_state(self, state_key: str) -> bool:
        return state_key.startswith('strategy_')
        
    def update_state(self, state_key: str, state_value: Any):
        if state_key == 'strategy_selected':
            self.highlight_strategy(state_value)
```

## 💎 도메인 상태 관리

### Entity 상태 패턴
```python
class Strategy:
    """도메인 Entity - 자체 상태 관리"""
    def __init__(self, name: str):
        self.name = name
        self._state = StrategyState.INACTIVE
        self._rules: List[TradingRule] = []
        self._events: List[DomainEvent] = []
        
    def activate(self):
        """상태 변경 + 이벤트 발행"""
        if self._state == StrategyState.INACTIVE:
            old_state = self._state
            self._state = StrategyState.ACTIVE
            
            # 도메인 이벤트 추가
            self.add_event(StrategyStateChanged(
                strategy_id=self.id,
                old_state=old_state,
                new_state=self._state
            ))
            
    def can_add_rule(self) -> bool:
        """상태 기반 비즈니스 규칙"""
        return self._state == StrategyState.INACTIVE and len(self._rules) < 10

class StrategyState(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
```

### 상태 머신 패턴
```python
class StrategyStateMachine:
    """전략 상태 전이 관리"""
    
    TRANSITIONS = {
        StrategyState.INACTIVE: [StrategyState.ACTIVE],
        StrategyState.ACTIVE: [StrategyState.PAUSED, StrategyState.ARCHIVED],
        StrategyState.PAUSED: [StrategyState.ACTIVE, StrategyState.ARCHIVED],
        StrategyState.ARCHIVED: []  # 최종 상태
    }
    
    @classmethod
    def can_transition(cls, from_state: StrategyState, to_state: StrategyState) -> bool:
        """상태 전이 가능 여부 검증"""
        return to_state in cls.TRANSITIONS.get(from_state, [])
        
    @classmethod
    def get_available_transitions(cls, current_state: StrategyState) -> List[StrategyState]:
        """현재 상태에서 가능한 다음 상태들"""
        return cls.TRANSITIONS.get(current_state, [])
```

## 🔄 상태 이벤트 처리

### 상태 변경 이벤트
```python
class StateChangedEvent:
    """상태 변경 이벤트 기본 클래스"""
    def __init__(self, entity_id: str, old_state: Any, new_state: Any):
        self.entity_id = entity_id
        self.old_state = old_state
        self.new_state = new_state
        self.timestamp = datetime.now()

class StrategyStateHandler:
    """전략 상태 변경 이벤트 핸들러"""
    def __init__(self, notification_service):
        self.notification_service = notification_service
        
    def handle(self, event: StrategyStateChanged):
        """상태 변경에 따른 부가 작업"""
        if event.new_state == StrategyState.ACTIVE:
            self.notification_service.notify_strategy_activated(event.entity_id)
        elif event.new_state == StrategyState.ARCHIVED:
            self.notification_service.notify_strategy_archived(event.entity_id)
```

## 🔍 상태 디버깅 도구

### 상태 로깅
```python
class StateLogger:
    """상태 변경 로깅"""
    def __init__(self, logger):
        self.logger = logger
        
    def log_state_change(self, entity_id: str, old_state: Any, new_state: Any):
        self.logger.info(
            f"🔄 상태 변경: {entity_id} | {old_state} → {new_state}"
        )

class StateValidator:
    """상태 일관성 검증"""
    def __init__(self):
        self.validation_rules: List[StateValidationRule] = []
        
    def validate_state(self, entity: Any) -> List[str]:
        """상태 검증 및 오류 반환"""
        errors = []
        for rule in self.validation_rules:
            if not rule.validate(entity):
                errors.append(rule.error_message)
        return errors
```

## 🚀 성능 최적화

### 상태 캐싱
```python
class StateCacheManager:
    """자주 접근하는 상태 캐싱"""
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=5)
        
    def get_cached_state(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if self._is_cache_valid(key):
                return self._cache[key]
            else:
                self._invalidate_cache(key)
        return None
        
    def cache_state(self, key: str, state: Any):
        self._cache[key] = state
        self._cache_timestamps[key] = datetime.now()
```

### 상태 업데이트 배칭
```python
class BatchStateUpdater:
    """여러 상태 변경을 배치로 처리"""
    def __init__(self):
        self._pending_updates: List[StateUpdate] = []
        self._update_timer = None
        
    def schedule_update(self, entity_id: str, new_state: Any):
        """상태 업데이트 예약"""
        update = StateUpdate(entity_id, new_state, datetime.now())
        self._pending_updates.append(update)
        
        # 100ms 후 배치 처리
        if self._update_timer:
            self._update_timer.stop()
        self._update_timer = Timer(0.1, self._process_batch_updates)
        self._update_timer.start()
        
    def _process_batch_updates(self):
        """배치 업데이트 처리"""
        if self._pending_updates:
            # 동일 entity의 최신 상태만 적용
            latest_updates = {}
            for update in self._pending_updates:
                latest_updates[update.entity_id] = update
                
            for update in latest_updates.values():
                self._apply_state_update(update)
                
            self._pending_updates.clear()
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 전체 아키텍처와 상태 관리 위치
- [UI 개발](05_UI_DEVELOPMENT.md): MVP 패턴에서 상태 관리
- [이벤트 시스템](08_EVENT_SYSTEM.md): 상태 변경 이벤트 처리
- [문제 해결](06_TROUBLESHOOTING.md): 상태 관련 문제 해결

---
**💡 핵심**: "각 계층이 자신의 책임에 맞는 상태만 관리하고, 상태 변경은 이벤트로 전파하세요!"
