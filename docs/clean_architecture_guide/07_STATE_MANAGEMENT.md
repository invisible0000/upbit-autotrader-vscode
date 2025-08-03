# 🔧 상태 관리 시스템

> **목적**: Clean Architecture에서 복잡한 상태 추적 및 관리 방법  
> **대상**: 개발자, 시스템 아키텍트  
> **예상 읽기 시간**: 16분

## 🎯 상태 관리의 복잡성 문제

### ❌ 기존 방식의 문제점
```python
# 전역 변수로 상태 관리 (위험!)
current_positions = {}
active_strategies = {}
market_data_cache = {}

# UI에서 직접 상태 변경 (결합도 높음)
def on_strategy_created(self):
    strategy = create_strategy()
    active_strategies[strategy.id] = strategy  # 직접 조작
    self.update_ui()  # UI도 직접 업데이트
```

### ✅ Clean Architecture 상태 관리
```python
# Domain에서 상태 정의
class TradingSession:
    def __init__(self):
        self._positions = {}
        self._strategies = {}
        self._events = []
    
    def add_strategy(self, strategy):
        # 비즈니스 규칙 검증
        self._validate_strategy_addition(strategy)
        self._strategies[strategy.id] = strategy
        self._events.append(StrategyAddedEvent(strategy.id))

# Application에서 상태 조율
class TradingSessionService:
    def create_strategy(self, command):
        session = self.session_repo.get_current()
        strategy = Strategy.create(command.data)
        session.add_strategy(strategy)
        self.session_repo.save(session)
        # 이벤트를 통해 UI 업데이트
```

## 🏗️ 상태 관리 아키텍처

### 계층별 상태 책임
```
┌─────────────────────────────────────────────┐
│              Presentation                   │ ← UI 상태만 관리
│  (버튼 활성화, 로딩 스피너, 폼 입력값)         │
├─────────────────────────────────────────────┤
│              Application                    │ ← 비즈니스 흐름 상태
│    (진행 중인 유스케이스, 트랜잭션 상태)       │
├─────────────────────────────────────────────┤
│                Domain                       │ ← 핵심 비즈니스 상태
│   (포지션, 전략, 시장 상황, 도메인 규칙)       │
├─────────────────────────────────────────────┤
│             Infrastructure                  │ ← 기술적 상태
│  (DB 연결, API 상태, 캐시, 네트워크 상태)     │
└─────────────────────────────────────────────┘
```

## 💎 Domain 상태 관리

### 핵심 상태 엔티티들
```python
# domain/entities/trading_session.py
class TradingSession:
    """거래 세션 - 전체 거래 상태의 루트 엔티티"""
    
    def __init__(self, session_id: SessionId, user_id: UserId):
        self.id = session_id
        self.user_id = user_id
        self.status = SessionStatus.INACTIVE
        self.positions = PositionCollection()
        self.strategies = StrategyCollection()
        self.market_state = MarketState()
        self.created_at = datetime.utcnow()
        self._events = []
    
    def start_trading(self):
        """거래 시작 - 상태 변경과 비즈니스 규칙"""
        if self.status != SessionStatus.INACTIVE:
            raise InvalidSessionStateError("이미 활성화된 세션입니다")
        
        if not self.strategies.has_entry_strategy():
            raise MissingEntryStrategyError("진입 전략이 필요합니다")
        
        self.status = SessionStatus.ACTIVE
        self._events.append(TradingSessionStartedEvent(self.id))
    
    def add_position(self, symbol: str, entry_price: Price, quantity: Quantity):
        """포지션 추가 - 상태 일관성 보장"""
        if self.status != SessionStatus.ACTIVE:
            raise InvalidSessionStateError("활성 세션에서만 포지션 추가 가능")
        
        if self.positions.has_position_for_symbol(symbol):
            raise DuplicatePositionError(f"이미 {symbol} 포지션이 존재합니다")
        
        position = Position.create(
            PositionId.generate(), 
            symbol, 
            entry_price, 
            quantity
        )
        
        self.positions.add(position)
        self._events.append(PositionOpenedEvent(position.id, symbol))
        
        return position
    
    def update_position_with_price(self, symbol: str, current_price: Price):
        """가격 업데이트로 포지션 상태 갱신"""
        position = self.positions.get_by_symbol(symbol)
        if not position:
            return
        
        # 관련 전략들의 신호 수집
        signals = []
        for strategy in self.strategies.get_management_strategies():
            signal = strategy.evaluate_position(position, current_price)
            if signal != TradingSignal.HOLD:
                signals.append(signal)
        
        # 신호 충돌 해결
        resolved_signal = self._resolve_signal_conflicts(signals)
        
        # 신호에 따른 포지션 상태 변경
        if resolved_signal == TradingSignal.CLOSE_POSITION:
            self._close_position(position, current_price)
        elif resolved_signal.signal_type == "ADD_BUY":
            self._add_to_position(position, resolved_signal.quantity)
    
    def _close_position(self, position: Position, exit_price: Price):
        """포지션 청산"""
        profit_loss = position.calculate_profit_loss(exit_price)
        position.close(exit_price)
        
        self.positions.remove(position)
        self._events.append(PositionClosedEvent(
            position.id, 
            position.symbol, 
            profit_loss
        ))

# domain/value_objects/position_collection.py
class PositionCollection:
    """포지션 컬렉션 - 비즈니스 규칙 포함"""
    
    def __init__(self):
        self._positions = {}
        self._max_positions = 10  # 최대 동시 포지션 수
    
    def add(self, position: Position):
        if len(self._positions) >= self._max_positions:
            raise MaxPositionsReachedError(f"최대 {self._max_positions}개 포지션 초과")
        
        self._positions[position.symbol] = position
    
    def get_by_symbol(self, symbol: str) -> Position:
        return self._positions.get(symbol)
    
    def has_position_for_symbol(self, symbol: str) -> bool:
        return symbol in self._positions
    
    def get_total_unrealized_pnl(self, current_prices: Dict[str, Price]) -> Money:
        """미실현 손익 계산"""
        total_pnl = Money.zero()
        for symbol, position in self._positions.items():
            if symbol in current_prices:
                pnl = position.calculate_unrealized_pnl(current_prices[symbol])
                total_pnl = total_pnl.add(pnl)
        return total_pnl
```

### 상태 변경 추적
```python
# domain/events/domain_events.py
@dataclass
class PositionStateChangedEvent(DomainEvent):
    """포지션 상태 변경 이벤트"""
    position_id: PositionId
    old_state: PositionState
    new_state: PositionState
    reason: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TradingSessionStateChangedEvent(DomainEvent):
    """거래 세션 상태 변경 이벤트"""
    session_id: SessionId
    old_status: SessionStatus
    new_status: SessionStatus
    triggered_by: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)
```

## ⚙️ Application 상태 관리

### 상태 조율 서비스
```python
# application/services/trading_state_service.py
class TradingStateService:
    """거래 상태 관리 서비스"""
    
    def __init__(
        self,
        session_repo: TradingSessionRepository,
        market_data_service: MarketDataService,
        notification_service: NotificationService,
        event_publisher: EventPublisher
    ):
        self.session_repo = session_repo
        self.market_data_service = market_data_service
        self.notification_service = notification_service
        self.event_publisher = event_publisher
    
    def start_trading_session(self, command: StartTradingCommand):
        """거래 세션 시작"""
        try:
            # 현재 세션 상태 확인
            existing_session = self.session_repo.find_active_by_user(command.user_id)
            if existing_session:
                return Result.fail("이미 활성화된 거래 세션이 있습니다")
            
            # 새 세션 생성
            session = TradingSession(
                SessionId.generate(),
                command.user_id
            )
            
            # 전략들 등록
            for strategy_config in command.strategies:
                strategy = StrategyFactory.create(strategy_config)
                session.add_strategy(strategy)
            
            # 거래 시작
            session.start_trading()
            
            # 저장
            self.session_repo.save(session)
            
            # 이벤트 발행
            for event in session.get_uncommitted_events():
                self.event_publisher.publish(event)
            session.mark_events_as_committed()
            
            return Result.ok(StartTradingResult(session.id))
            
        except DomainException as e:
            return Result.fail(f"거래 시작 실패: {e.message}")
    
    def process_market_update(self, symbol: str, price_data: PriceData):
        """시장 데이터 업데이트 처리"""
        # 해당 심볼의 활성 세션들 조회
        active_sessions = self.session_repo.find_active_with_symbol(symbol)
        
        for session in active_sessions:
            try:
                # 세션 상태 업데이트
                session.update_position_with_price(symbol, price_data.close_price)
                
                # 변경사항 저장
                self.session_repo.save(session)
                
                # 이벤트 발행
                for event in session.get_uncommitted_events():
                    self.event_publisher.publish(event)
                session.mark_events_as_committed()
                
            except Exception as e:
                # 개별 세션 오류가 전체 처리를 막지 않도록
                self.notification_service.send_error_notification(
                    session.user_id,
                    f"세션 {session.id} 업데이트 오류: {str(e)}"
                )
    
    def get_trading_state_summary(self, user_id: UserId):
        """거래 상태 요약 조회"""
        session = self.session_repo.find_active_by_user(user_id)
        if not session:
            return TradingStateSummary.inactive()
        
        # 현재 시장 가격 조회
        symbols = session.positions.get_all_symbols()
        current_prices = self.market_data_service.get_current_prices(symbols)
        
        # 상태 요약 생성
        return TradingStateSummary(
            session_id=session.id,
            status=session.status,
            position_count=session.positions.count(),
            total_unrealized_pnl=session.positions.get_total_unrealized_pnl(current_prices),
            active_strategies=session.strategies.get_active_count(),
            last_update=session.updated_at
        )
```

### 상태 동기화 관리
```python
# application/services/state_synchronization_service.py
class StateSynchronizationService:
    """상태 동기화 서비스 - 분산 상태 일관성 보장"""
    
    def __init__(
        self,
        session_repo: TradingSessionRepository,
        cache_service: CacheService,
        event_publisher: EventPublisher
    ):
        self.session_repo = session_repo
        self.cache_service = cache_service
        self.event_publisher = event_publisher
        self.sync_locks = {}
    
    def synchronize_session_state(self, session_id: SessionId):
        """세션 상태 동기화"""
        lock_key = f"sync_session_{session_id.value}"
        
        # 동시 동기화 방지
        if lock_key in self.sync_locks:
            return
        
        try:
            self.sync_locks[lock_key] = True
            
            # DB에서 최신 상태 조회
            db_session = self.session_repo.find_by_id(session_id)
            
            # 캐시에서 현재 상태 조회
            cached_session = self.cache_service.get_session(session_id)
            
            # 상태 충돌 검사 및 해결
            if self._has_state_conflict(db_session, cached_session):
                resolved_session = self._resolve_state_conflict(db_session, cached_session)
                
                # 해결된 상태로 업데이트
                self.session_repo.save(resolved_session)
                self.cache_service.update_session(resolved_session)
                
                # 충돌 해결 이벤트 발행
                self.event_publisher.publish(
                    StateConflictResolvedEvent(session_id, "auto_resolved")
                )
        
        finally:
            self.sync_locks.pop(lock_key, None)
    
    def _has_state_conflict(self, db_session: TradingSession, cached_session: TradingSession) -> bool:
        """상태 충돌 검사"""
        if not cached_session:
            return False
        
        # 버전 충돌 검사
        if db_session.version != cached_session.version:
            return True
        
        # 포지션 수 불일치
        if db_session.positions.count() != cached_session.positions.count():
            return True
        
        # 전략 상태 불일치
        if db_session.strategies.get_hash() != cached_session.strategies.get_hash():
            return True
        
        return False
    
    def _resolve_state_conflict(self, db_session: TradingSession, cached_session: TradingSession) -> TradingSession:
        """상태 충돌 해결 - Last Writer Wins 전략"""
        # 최근 업데이트가 우선
        if db_session.updated_at > cached_session.updated_at:
            return db_session
        else:
            return cached_session
```

## 🎨 Presentation 상태 관리

### UI 상태 분리
```python
# presentation/state/ui_state_manager.py
class UIStateManager:
    """UI 상태 관리자 - UI 전용 상태만 관리"""
    
    def __init__(self):
        self.form_states = {}      # 폼 입력 상태
        self.loading_states = {}   # 로딩 상태
        self.dialog_states = {}    # 다이얼로그 상태
        self.tab_states = {}       # 탭 활성화 상태
        self.observers = []        # 상태 변경 관찰자
    
    def set_form_state(self, form_id: str, field: str, value: Any):
        """폼 필드 상태 설정"""
        if form_id not in self.form_states:
            self.form_states[form_id] = {}
        
        old_value = self.form_states[form_id].get(field)
        self.form_states[form_id][field] = value
        
        # 변경 알림
        self._notify_observers("form_changed", {
            "form_id": form_id,
            "field": field,
            "old_value": old_value,
            "new_value": value
        })
    
    def get_form_state(self, form_id: str) -> dict:
        """폼 상태 조회"""
        return self.form_states.get(form_id, {})
    
    def set_loading_state(self, component_id: str, is_loading: bool):
        """로딩 상태 설정"""
        old_state = self.loading_states.get(component_id, False)
        self.loading_states[component_id] = is_loading
        
        if old_state != is_loading:
            self._notify_observers("loading_changed", {
                "component_id": component_id,
                "is_loading": is_loading
            })
    
    def is_loading(self, component_id: str) -> bool:
        """로딩 상태 확인"""
        return self.loading_states.get(component_id, False)
    
    def add_observer(self, observer_func):
        """상태 변경 관찰자 등록"""
        self.observers.append(observer_func)
    
    def _notify_observers(self, event_type: str, data: dict):
        """관찰자들에게 변경 알림"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                print(f"UI 상태 관찰자 오류: {e}")

# presentation/presenters/strategy_builder_presenter.py
class StrategyBuilderPresenter:
    """전략 빌더 Presenter - UI와 비즈니스 상태 연결"""
    
    def __init__(self, view, ui_state_manager, strategy_service):
        self.view = view
        self.ui_state = ui_state_manager
        self.strategy_service = strategy_service
        
        # UI 상태 변경 관찰
        self.ui_state.add_observer(self._on_ui_state_changed)
    
    def on_condition_form_changed(self, field: str, value: Any):
        """조건 폼 변경 처리"""
        # UI 상태 업데이트
        self.ui_state.set_form_state("condition_form", field, value)
        
        # 실시간 검증
        self._validate_condition_form()
    
    def create_condition(self, form_data: dict):
        """조건 생성"""
        # 로딩 상태 시작
        self.ui_state.set_loading_state("condition_creation", True)
        
        try:
            # 비즈니스 로직 실행
            result = self.strategy_service.create_condition(form_data)
            
            if result.success:
                # 성공 시 폼 초기화
                self.ui_state.form_states.pop("condition_form", None)
                self.view.show_success_message("조건이 생성되었습니다")
                self.view.clear_form()
            else:
                self.view.show_error_message(result.error)
        
        finally:
            # 로딩 상태 종료
            self.ui_state.set_loading_state("condition_creation", False)
    
    def _on_ui_state_changed(self, event_type: str, data: dict):
        """UI 상태 변경 반응"""
        if event_type == "form_changed" and data["form_id"] == "condition_form":
            # 폼 변경 시 실시간 미리보기 업데이트
            self._update_condition_preview()
        
        elif event_type == "loading_changed":
            # 로딩 상태에 따른 UI 업데이트
            component_id = data["component_id"]
            is_loading = data["is_loading"]
            self.view.set_component_loading(component_id, is_loading)
    
    def _validate_condition_form(self):
        """조건 폼 실시간 검증"""
        form_state = self.ui_state.get_form_state("condition_form")
        
        # 필수 필드 검증
        required_fields = ["variable_id", "operator", "target_value"]
        missing_fields = [field for field in required_fields if not form_state.get(field)]
        
        if missing_fields:
            self.view.set_create_button_enabled(False)
            self.view.show_form_validation_errors(missing_fields)
        else:
            self.view.set_create_button_enabled(True)
            self.view.clear_form_validation_errors()
```

## 🔄 상태 이벤트 시스템

### 상태 변경 이벤트 처리
```python
# application/event_handlers/state_change_event_handlers.py
class TradingStateEventHandler:
    """거래 상태 변경 이벤트 핸들러"""
    
    def __init__(self, notification_service, ui_update_service):
        self.notification_service = notification_service
        self.ui_update_service = ui_update_service
    
    def handle_position_opened(self, event: PositionOpenedEvent):
        """포지션 개설 이벤트 처리"""
        # 사용자 알림
        self.notification_service.send_notification(
            event.user_id,
            f"{event.symbol} 포지션이 개설되었습니다",
            NotificationType.INFO
        )
        
        # UI 업데이트
        self.ui_update_service.update_position_list(event.user_id)
        self.ui_update_service.update_portfolio_summary(event.user_id)
    
    def handle_position_closed(self, event: PositionClosedEvent):
        """포지션 청산 이벤트 처리"""
        # 수익/손실에 따른 알림
        notification_type = (
            NotificationType.SUCCESS if event.profit_loss > 0 
            else NotificationType.WARNING
        )
        
        self.notification_service.send_notification(
            event.user_id,
            f"{event.symbol} 포지션 청산: {event.profit_loss:+.2f}원",
            notification_type
        )
        
        # UI 업데이트
        self.ui_update_service.remove_position_from_list(event.position_id)
        self.ui_update_service.update_portfolio_summary(event.user_id)
        self.ui_update_service.add_to_transaction_history(event)
```

## 🚀 상태 최적화 전략

### 메모리 최적화
```python
# 상태 크기 제한
class StateManager:
    MAX_CACHE_SIZE = 1000
    
    def add_to_cache(self, key, value):
        if len(self.cache) >= self.MAX_CACHE_SIZE:
            # LRU 제거
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = value
```

### 상태 지연 로딩
```python
# 필요할 때만 상태 로드
class LazyPositionCollection:
    def __init__(self, session_id):
        self.session_id = session_id
        self._loaded = False
        self._positions = None
    
    def get_positions(self):
        if not self._loaded:
            self._positions = self._load_positions()
            self._loaded = True
        return self._positions
```

## 🔍 다음 단계

- **[이벤트 시스템](09_EVENT_SYSTEM.md)**: Domain Event 상세 구현
- **[성능 최적화](10_PERFORMANCE_OPTIMIZATION.md)**: 상태 관리 최적화
- **[디버깅 가이드](15_DEBUGGING_GUIDE.md)**: 상태 관련 문제 해결

---
**💡 핵심**: "상태 관리는 각 계층의 책임을 명확히 하고, 이벤트로 상태 변경을 추적하는 것이 핵심입니다!"
