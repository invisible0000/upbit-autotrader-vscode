# TASK-20250803-04

## Title
도메인 이벤트 시스템 구현 (이벤트 기반 아키텍처)

## Objective (목표)
도메인 계층에서 발생하는 중요한 비즈니스 이벤트를 추적하고 처리하기 위한 도메인 이벤트 시스템을 구현합니다. 전략 생성, 트리거 평가, 포지션 변경 등의 핵심 비즈니스 이벤트를 명시적으로 정의하고, 느슨한 결합을 통한 이벤트 기반 아키텍처의 기반을 마련합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 1: Domain Layer 구축 (2주)" > "1.4 도메인 이벤트 시스템 (4일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-01`: 도메인 엔티티 설계 및 구현이 완료되어야 함
- `TASK-20250803-02`: 도메인 서비스 구현이 완료되어야 함
- `TASK-20250803-03`: Repository 인터페이스 정의가 완료되어야 함

## Detailed Steps (상세 실행 절차 - 체크리스트)

### 1. **[분석]** 기존 이벤트 처리 패턴 및 비즈니스 이벤트 식별
- [ ] 현재 시스템에서 발생하는 주요 비즈니스 이벤트들 식별 (전략 생성, 트리거 활성화, 매매 신호 등)
- [ ] 기존 UI 이벤트 처리 코드에서 비즈니스 로직과 관련된 이벤트들 분석
- [ ] `upbit_auto_trading/business_logic/` 폴더에서 이벤트성 로직 패턴 분석
- [ ] 로깅 시스템에서 기록되는 중요한 비즈니스 이벤트들 확인
- [ ] 향후 알림, 감사 로그, 성능 모니터링에 필요한 이벤트들 정의

### 2. **[폴더 구조 생성]** 도메인 이벤트 시스템 폴더 구조 생성
- [ ] `upbit_auto_trading/domain/events/` 폴더 생성
- [ ] `upbit_auto_trading/domain/events/__init__.py` 파일 생성

### 3. **[새 코드 작성]** 기본 도메인 이벤트 추상 클래스 정의
- [ ] `upbit_auto_trading/domain/events/base_domain_event.py` 파일 생성:
  ```python
  from abc import ABC
  from dataclasses import dataclass, field
  from datetime import datetime
  from typing import Dict, Any, Optional
  import uuid
  
  @dataclass
  class DomainEvent(ABC):
      """모든 도메인 이벤트의 기본 클래스"""
      
      event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
      occurred_at: datetime = field(default_factory=datetime.now)
      version: int = field(default=1)
      correlation_id: Optional[str] = field(default=None)
      causation_id: Optional[str] = field(default=None)
      metadata: Dict[str, Any] = field(default_factory=dict)
      
      def __post_init__(self):
          """이벤트 생성 후 추가 초기화"""
          if not self.correlation_id:
              self.correlation_id = self.event_id
      
      @property
      def event_type(self) -> str:
          """이벤트 타입 반환 (클래스명 기반)"""
          return self.__class__.__name__
      
      def add_metadata(self, key: str, value: Any) -> None:
          """메타데이터 추가"""
          self.metadata[key] = value
      
      def to_dict(self) -> Dict[str, Any]:
          """이벤트를 딕셔너리로 변환 (직렬화용)"""
          return {
              "event_id": self.event_id,
              "event_type": self.event_type,
              "occurred_at": self.occurred_at.isoformat(),
              "version": self.version,
              "correlation_id": self.correlation_id,
              "causation_id": self.causation_id,
              "metadata": self.metadata,
              "data": self._get_event_data()
          }
      
      def _get_event_data(self) -> Dict[str, Any]:
          """이벤트별 고유 데이터 반환 (하위 클래스에서 구현)"""
          # 기본적으로 dataclass의 모든 필드를 반환 (기본 필드 제외)
          base_fields = {"event_id", "occurred_at", "version", "correlation_id", "causation_id", "metadata"}
          return {
              key: value for key, value in self.__dict__.items() 
              if key not in base_fields
          }
  ```

### 4. **[새 코드 작성]** 전략 관련 도메인 이벤트 정의
- [ ] `upbit_auto_trading/domain/events/strategy_events.py` 파일 생성:
  ```python
  from dataclasses import dataclass
  from datetime import datetime
  from typing import List, Dict, Any
  
  from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
  
  @dataclass
  class StrategyCreated(DomainEvent):
      """전략 생성 이벤트"""
      strategy_id: StrategyId
      strategy_name: str
      created_by: str = "system"
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "strategy_name": self.strategy_name,
              "created_by": self.created_by
          }
  
  @dataclass
  class StrategyUpdated(DomainEvent):
      """전략 수정 이벤트"""
      strategy_id: StrategyId
      strategy_name: str
      updated_fields: List[str]
      previous_values: Dict[str, Any]
      new_values: Dict[str, Any]
      updated_by: str = "system"
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "strategy_name": self.strategy_name,
              "updated_fields": self.updated_fields,
              "previous_values": self.previous_values,
              "new_values": self.new_values,
              "updated_by": self.updated_by
          }
  
  @dataclass
  class StrategyDeleted(DomainEvent):
      """전략 삭제 이벤트"""
      strategy_id: StrategyId
      strategy_name: str
      deleted_by: str = "system"
      soft_delete: bool = True
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "strategy_name": self.strategy_name,
              "deleted_by": self.deleted_by,
              "soft_delete": self.soft_delete
          }
  
  @dataclass
  class StrategyActivated(DomainEvent):
      """전략 활성화 이벤트"""
      strategy_id: StrategyId
      strategy_name: str
      activated_by: str = "system"
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "strategy_name": self.strategy_name,
              "activated_by": self.activated_by
          }
  
  @dataclass
  class StrategyDeactivated(DomainEvent):
      """전략 비활성화 이벤트"""
      strategy_id: StrategyId
      strategy_name: str
      reason: str
      deactivated_by: str = "system"
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "strategy_name": self.strategy_name,
              "reason": self.reason,
              "deactivated_by": self.deactivated_by
          }
  
  @dataclass
  class TriggerAdded(DomainEvent):
      """전략에 트리거 추가 이벤트"""
      strategy_id: StrategyId
      trigger_id: TriggerId
      trigger_type: str
      variable_id: str
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "trigger_id": self.trigger_id.value,
              "trigger_type": self.trigger_type,
              "variable_id": self.variable_id
          }
  
  @dataclass
  class TriggerRemoved(DomainEvent):
      """전략에서 트리거 제거 이벤트"""
      strategy_id: StrategyId
      trigger_id: TriggerId
      reason: str = "user_requested"
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "trigger_id": self.trigger_id.value,
              "reason": self.reason
          }
  ```

### 5. **[새 코드 작성]** 트리거 평가 관련 도메인 이벤트 정의
- [ ] `upbit_auto_trading/domain/events/trigger_events.py` 파일 생성:
  ```python
  from dataclasses import dataclass
  from datetime import datetime
  from typing import Dict, Any, Optional
  
  from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
  from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  
  @dataclass
  class TriggerEvaluated(DomainEvent):
      """트리거 평가 완료 이벤트"""
      trigger_id: TriggerId
      strategy_id: StrategyId
      symbol: str
      result: bool
      current_value: float
      target_value: float
      operator: str
      market_data_timestamp: datetime
      evaluation_duration_ms: float = 0.0
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "trigger_id": self.trigger_id.value,
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "result": self.result,
              "current_value": self.current_value,
              "target_value": self.target_value,
              "operator": self.operator,
              "market_data_timestamp": self.market_data_timestamp.isoformat(),
              "evaluation_duration_ms": self.evaluation_duration_ms
          }
  
  @dataclass
  class TriggerActivated(DomainEvent):
      """트리거 조건 만족 (활성화) 이벤트"""
      trigger_id: TriggerId
      strategy_id: StrategyId
      symbol: str
      trigger_type: str  # ENTRY, EXIT, MANAGEMENT
      condition_description: str
      current_value: float
      target_value: float
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "trigger_id": self.trigger_id.value,
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "trigger_type": self.trigger_type,
              "condition_description": self.condition_description,
              "current_value": self.current_value,
              "target_value": self.target_value
          }
  
  @dataclass
  class TriggerDeactivated(DomainEvent):
      """트리거 조건 불만족 (비활성화) 이벤트"""
      trigger_id: TriggerId
      strategy_id: StrategyId
      symbol: str
      reason: str
      previous_value: float
      current_value: float
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "trigger_id": self.trigger_id.value,
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "reason": self.reason,
              "previous_value": self.previous_value,
              "current_value": self.current_value
          }
  
  @dataclass
  class TriggerEvaluationFailed(DomainEvent):
      """트리거 평가 실패 이벤트"""
      trigger_id: TriggerId
      strategy_id: StrategyId
      symbol: str
      error_message: str
      error_type: str
      retry_count: int = 0
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "trigger_id": self.trigger_id.value,
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "error_message": self.error_message,
              "error_type": self.error_type,
              "retry_count": self.retry_count
          }
  ```

### 6. **[새 코드 작성]** 매매 신호 관련 도메인 이벤트 정의
- [ ] `upbit_auto_trading/domain/events/trading_events.py` 파일 생성:
  ```python
  from dataclasses import dataclass
  from datetime import datetime
  from typing import Dict, Any, Optional
  from enum import Enum
  
  from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  
  class TradingSignalType(Enum):
      BUY = "BUY"
      SELL = "SELL"
      HOLD = "HOLD"
      ADD_BUY = "ADD_BUY"
      CLOSE_POSITION = "CLOSE_POSITION"
      UPDATE_STOP = "UPDATE_STOP"
  
  @dataclass
  class TradingSignalGenerated(DomainEvent):
      """매매 신호 생성 이벤트"""
      strategy_id: StrategyId
      symbol: str
      signal_type: TradingSignalType
      confidence: float  # 0.0 ~ 1.0
      price: float
      quantity: Optional[float] = None
      reason: str = ""
      risk_level: int = 3  # 1(낮음) ~ 5(높음)
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "signal_type": self.signal_type.value,
              "confidence": self.confidence,
              "price": self.price,
              "quantity": self.quantity,
              "reason": self.reason,
              "risk_level": self.risk_level
          }
  
  @dataclass
  class TradingSignalExecuted(DomainEvent):
      """매매 신호 실행 이벤트"""
      strategy_id: StrategyId
      symbol: str
      signal_type: TradingSignalType
      executed_price: float
      executed_quantity: float
      order_id: str
      execution_time: datetime
      fees: float = 0.0
      slippage: float = 0.0
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "signal_type": self.signal_type.value,
              "executed_price": self.executed_price,
              "executed_quantity": self.executed_quantity,
              "order_id": self.order_id,
              "execution_time": self.execution_time.isoformat(),
              "fees": self.fees,
              "slippage": self.slippage
          }
  
  @dataclass
  class TradingSignalRejected(DomainEvent):
      """매매 신호 거부 이벤트"""
      strategy_id: StrategyId
      symbol: str
      signal_type: TradingSignalType
      rejection_reason: str
      risk_assessment: Dict[str, Any]
      suggested_price: Optional[float] = None
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "signal_type": self.signal_type.value,
              "rejection_reason": self.rejection_reason,
              "risk_assessment": self.risk_assessment,
              "suggested_price": self.suggested_price
          }
  ```

### 7. **[새 코드 작성]** 백테스팅 관련 도메인 이벤트 정의
- [ ] `upbit_auto_trading/domain/events/backtest_events.py` 파일 생성:
  ```python
  from dataclasses import dataclass
  from datetime import datetime
  from typing import Dict, Any, Optional
  
  from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  
  @dataclass
  class BacktestStarted(DomainEvent):
      """백테스팅 시작 이벤트"""
      backtest_id: str
      strategy_id: StrategyId
      symbol: str
      start_date: datetime
      end_date: datetime
      initial_capital: float
      settings: Dict[str, Any]
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "backtest_id": self.backtest_id,
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "start_date": self.start_date.isoformat(),
              "end_date": self.end_date.isoformat(),
              "initial_capital": self.initial_capital,
              "settings": self.settings
          }
  
  @dataclass
  class BacktestCompleted(DomainEvent):
      """백테스팅 완료 이벤트"""
      backtest_id: str
      strategy_id: StrategyId
      symbol: str
      duration_seconds: float
      total_return: float
      max_drawdown: float
      sharpe_ratio: float
      total_trades: int
      win_rate: float
      data_points_processed: int
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "backtest_id": self.backtest_id,
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "duration_seconds": self.duration_seconds,
              "total_return": self.total_return,
              "max_drawdown": self.max_drawdown,
              "sharpe_ratio": self.sharpe_ratio,
              "total_trades": self.total_trades,
              "win_rate": self.win_rate,
              "data_points_processed": self.data_points_processed
          }
  
  @dataclass
  class BacktestFailed(DomainEvent):
      """백테스팅 실패 이벤트"""
      backtest_id: str
      strategy_id: StrategyId
      symbol: str
      error_message: str
      error_type: str
      progress_percentage: float
      processed_data_points: int
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "backtest_id": self.backtest_id,
              "strategy_id": self.strategy_id.value,
              "symbol": self.symbol,
              "error_message": self.error_message,
              "error_type": self.error_type,
              "progress_percentage": self.progress_percentage,
              "processed_data_points": self.processed_data_points
          }
  
  @dataclass
  class BacktestProgressUpdated(DomainEvent):
      """백테스팅 진행률 업데이트 이벤트"""
      backtest_id: str
      strategy_id: StrategyId
      progress_percentage: float
      current_date: datetime
      processed_data_points: int
      estimated_completion_time: Optional[datetime] = None
      
      def _get_event_data(self) -> Dict[str, Any]:
          return {
              "backtest_id": self.backtest_id,
              "strategy_id": self.strategy_id.value,
              "progress_percentage": self.progress_percentage,
              "current_date": self.current_date.isoformat(),
              "processed_data_points": self.processed_data_points,
              "estimated_completion_time": self.estimated_completion_time.isoformat() if self.estimated_completion_time else None
          }
  ```

### 8. **[새 코드 작성]** 도메인 이벤트 게시자 구현
- [ ] `upbit_auto_trading/domain/events/domain_event_publisher.py` 파일 생성:
  ```python
  from typing import List, Callable, Dict, Type, Any
  from threading import Lock
  
  from upbit_auto_trading.domain.events.base_domain_event import DomainEvent
  
  # 이벤트 핸들러 타입 정의
  EventHandler = Callable[[DomainEvent], None]
  AsyncEventHandler = Callable[[DomainEvent], Any]  # Awaitable 반환
  
  class DomainEventPublisher:
      """도메인 이벤트 발행을 담당하는 게시자"""
      
      def __init__(self):
          self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
          self._async_handlers: Dict[Type[DomainEvent], List[AsyncEventHandler]] = {}
          self._global_handlers: List[EventHandler] = []
          self._async_global_handlers: List[AsyncEventHandler] = []
          self._lock = Lock()
          self._enabled = True
      
      def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
          """동기 이벤트 핸들러 등록"""
          with self._lock:
              if event_type not in self._handlers:
                  self._handlers[event_type] = []
              self._handlers[event_type].append(handler)
      
      def subscribe_async(self, event_type: Type[DomainEvent], handler: AsyncEventHandler) -> None:
          """비동기 이벤트 핸들러 등록"""
          with self._lock:
              if event_type not in self._async_handlers:
                  self._async_handlers[event_type] = []
              self._async_handlers[event_type].append(handler)
      
      def subscribe_global(self, handler: EventHandler) -> None:
          """모든 이벤트를 처리하는 글로벌 핸들러 등록"""
          with self._lock:
              self._global_handlers.append(handler)
      
      def subscribe_global_async(self, handler: AsyncEventHandler) -> None:
          """모든 이벤트를 처리하는 비동기 글로벌 핸들러 등록"""
          with self._lock:
              self._async_global_handlers.append(handler)
      
      def unsubscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> bool:
          """이벤트 핸들러 등록 해제"""
          with self._lock:
              if event_type in self._handlers and handler in self._handlers[event_type]:
                  self._handlers[event_type].remove(handler)
                  return True
              return False
      
      def publish(self, event: DomainEvent) -> None:
          """동기 이벤트 발행"""
          if not self._enabled:
              return
          
          # 특정 이벤트 타입 핸들러들 실행
          event_type = type(event)
          handlers = self._handlers.get(event_type, [])
          
          for handler in handlers:
              try:
                  handler(event)
              except Exception as e:
                  # 핸들러 실행 실패는 로깅만 하고 다른 핸들러에 영향 주지 않음
                  print(f"⚠️ 이벤트 핸들러 실행 실패: {e}")
          
          # 글로벌 핸들러들 실행
          for handler in self._global_handlers:
              try:
                  handler(event)
              except Exception as e:
                  print(f"⚠️ 글로벌 이벤트 핸들러 실행 실패: {e}")
      
      async def publish_async(self, event: DomainEvent) -> None:
          """비동기 이벤트 발행"""
          if not self._enabled:
              return
          
          import asyncio
          
          # 특정 이벤트 타입 비동기 핸들러들 실행
          event_type = type(event)
          async_handlers = self._async_handlers.get(event_type, [])
          
          tasks = []
          for handler in async_handlers:
              tasks.append(asyncio.create_task(handler(event)))
          
          # 글로벌 비동기 핸들러들 실행
          for handler in self._async_global_handlers:
              tasks.append(asyncio.create_task(handler(event)))
          
          # 모든 비동기 핸들러 완료 대기
          if tasks:
              await asyncio.gather(*tasks, return_exceptions=True)
      
      def publish_all(self, events: List[DomainEvent]) -> None:
          """여러 이벤트 일괄 발행"""
          for event in events:
              self.publish(event)
      
      async def publish_all_async(self, events: List[DomainEvent]) -> None:
          """여러 이벤트 비동기 일괄 발행"""
          import asyncio
          tasks = [self.publish_async(event) for event in events]
          await asyncio.gather(*tasks, return_exceptions=True)
      
      def enable(self) -> None:
          """이벤트 발행 활성화"""
          self._enabled = True
      
      def disable(self) -> None:
          """이벤트 발행 비활성화 (테스트용)"""
          self._enabled = False
      
      def clear_handlers(self) -> None:
          """모든 핸들러 제거 (테스트용)"""
          with self._lock:
              self._handlers.clear()
              self._async_handlers.clear()
              self._global_handlers.clear()
              self._async_global_handlers.clear()
      
      def get_handler_count(self, event_type: Type[DomainEvent]) -> int:
          """특정 이벤트 타입의 핸들러 개수 반환"""
          sync_count = len(self._handlers.get(event_type, []))
          async_count = len(self._async_handlers.get(event_type, []))
          return sync_count + async_count
  
  # 전역 이벤트 게시자 인스턴스
  _domain_event_publisher = DomainEventPublisher()
  
  def get_domain_event_publisher() -> DomainEventPublisher:
      """전역 도메인 이벤트 게시자 반환"""
      return _domain_event_publisher
  ```

### 9. **[새 코드 작성]** 도메인 엔티티에 이벤트 발행 기능 추가
- [ ] `upbit_auto_trading/domain/entities/strategy.py` 파일 수정하여 이벤트 발행 기능 추가:
  ```python
  # Strategy 클래스에 이벤트 발행 기능 추가
  from upbit_auto_trading.domain.events.strategy_events import (
      StrategyCreated, TriggerAdded, TriggerRemoved
  )
  
  class Strategy:
      # ... 기존 코드 ...
      
      @classmethod
      def create_new(cls, strategy_id: StrategyId, name: str) -> 'Strategy':
          """새 전략 생성 (팩토리 메서드)"""
          strategy = cls(strategy_id, name)
          
          # 전략 생성 이벤트 발행
          event = StrategyCreated(
              strategy_id=strategy_id,
              strategy_name=name,
              created_by="system"
          )
          strategy._domain_events.append(event)
          
          return strategy
      
      def add_trigger(self, trigger: 'Trigger') -> None:
          """트리거 추가 시 호환성 검증 및 이벤트 발행"""
          if not self._is_compatible_trigger(trigger):
              raise IncompatibleTriggerError(f"트리거 {trigger.trigger_id}는 현재 전략과 호환되지 않습니다")
          
          if trigger.trigger_type == TriggerType.ENTRY:
              self.entry_triggers.append(trigger)
          elif trigger.trigger_type == TriggerType.EXIT:
              self.exit_triggers.append(trigger)
          
          # 트리거 추가 이벤트 발행
          event = TriggerAdded(
              strategy_id=self.strategy_id,
              trigger_id=trigger.trigger_id,
              trigger_type=trigger.trigger_type.value,
              variable_id=trigger.variable.variable_id
          )
          self._domain_events.append(event)
      
      def remove_trigger(self, trigger_id: TriggerId, reason: str = "user_requested") -> bool:
          """트리거 제거"""
          # 진입 트리거에서 찾아서 제거
          for i, trigger in enumerate(self.entry_triggers):
              if trigger.trigger_id == trigger_id:
                  removed_trigger = self.entry_triggers.pop(i)
                  self._publish_trigger_removed_event(removed_trigger, reason)
                  return True
          
          # 청산 트리거에서 찾아서 제거
          for i, trigger in enumerate(self.exit_triggers):
              if trigger.trigger_id == trigger_id:
                  removed_trigger = self.exit_triggers.pop(i)
                  self._publish_trigger_removed_event(removed_trigger, reason)
                  return True
          
          return False
      
      def _publish_trigger_removed_event(self, trigger: 'Trigger', reason: str):
          """트리거 제거 이벤트 발행"""
          event = TriggerRemoved(
              strategy_id=self.strategy_id,
              trigger_id=trigger.trigger_id,
              reason=reason
          )
          self._domain_events.append(event)
      
      def clear_domain_events(self) -> None:
          """도메인 이벤트 클리어 (발행 후 호출)"""
          self._domain_events.clear()
  ```

### 10. **[새 코드 작성]** 도메인 서비스에 이벤트 발행 기능 추가
- [ ] `upbit_auto_trading/domain/services/trigger_evaluation_service.py` 파일 수정하여 이벤트 발행 기능 추가:
  ```python
  # TriggerEvaluationService에 이벤트 발행 기능 추가
  from upbit_auto_trading.domain.events.trigger_events import (
      TriggerEvaluated, TriggerActivated, TriggerDeactivated, TriggerEvaluationFailed
  )
  from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher
  
  class TriggerEvaluationService:
      def __init__(self, market_data_repository: MarketDataRepository = None):
          self._market_data_repository = market_data_repository
          self._event_publisher = get_domain_event_publisher()
      
      def evaluate_trigger(self, trigger: Trigger, market_data: MarketData) -> EvaluationResult:
          """단일 트리거 조건 평가 (이벤트 발행 포함)"""
          start_time = time.time()
          
          try:
              # 기존 평가 로직
              current_value = self._calculate_variable_value(trigger.variable, market_data)
              target_value = self._calculate_target_value(trigger.target_value, market_data)
              comparison_result = self._perform_comparison(current_value, trigger.operator, target_value)
              
              # 평가 완료 이벤트 발행
              evaluation_duration = (time.time() - start_time) * 1000  # ms
              
              evaluation_event = TriggerEvaluated(
                  trigger_id=trigger.trigger_id,
                  strategy_id=StrategyId("UNKNOWN"),  # 실제로는 Strategy에서 호출 시 전달
                  symbol=market_data.symbol,
                  result=comparison_result,
                  current_value=current_value,
                  target_value=target_value,
                  operator=trigger.operator.value,
                  market_data_timestamp=market_data.timestamp,
                  evaluation_duration_ms=evaluation_duration
              )
              self._event_publisher.publish(evaluation_event)
              
              # 트리거 활성화/비활성화 이벤트 발행
              if comparison_result:
                  activation_event = TriggerActivated(
                      trigger_id=trigger.trigger_id,
                      strategy_id=StrategyId("UNKNOWN"),
                      symbol=market_data.symbol,
                      trigger_type=trigger.trigger_type.value,
                      condition_description=trigger.to_human_readable(),
                      current_value=current_value,
                      target_value=target_value
                  )
                  self._event_publisher.publish(activation_event)
              
              return EvaluationResult(
                  trigger_id=trigger.trigger_id.value,
                  result=comparison_result,
                  value=current_value,
                  target_value=target_value,
                  operator=trigger.operator.value,
                  message=f"{trigger.variable.display_name}: {current_value} {trigger.operator.value} {target_value}",
                  timestamp=market_data.timestamp
              )
              
          except Exception as e:
              # 평가 실패 이벤트 발행
              failure_event = TriggerEvaluationFailed(
                  trigger_id=trigger.trigger_id,
                  strategy_id=StrategyId("UNKNOWN"),
                  symbol=market_data.symbol,
                  error_message=str(e),
                  error_type=type(e).__name__,
                  retry_count=0
              )
              self._event_publisher.publish(failure_event)
              
              # 실패 시에도 결과 반환
              return EvaluationResult(
                  trigger_id=trigger.trigger_id.value,
                  result=False,
                  value=0.0,
                  target_value=0.0,
                  operator=trigger.operator.value,
                  message=f"평가 오류: {str(e)}",
                  timestamp=market_data.timestamp
              )
  ```

### 11. **[테스트 코드 작성]** 도메인 이벤트 시스템 테스트 구현
- [ ] `tests/domain/events/` 폴더 생성
- [ ] `tests/domain/events/test_domain_event_publisher.py` 파일 생성:
  ```python
  import pytest
  from unittest.mock import Mock
  from datetime import datetime
  
  from upbit_auto_trading.domain.events.domain_event_publisher import DomainEventPublisher
  from upbit_auto_trading.domain.events.strategy_events import StrategyCreated
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  
  class TestDomainEventPublisher:
      def setup_method(self):
          self.publisher = DomainEventPublisher()
          self.publisher.clear_handlers()  # 테스트 간 격리
      
      def test_subscribe_and_publish_event(self):
          # Given
          handler = Mock()
          event = StrategyCreated(
              strategy_id=StrategyId("TEST_001"),
              strategy_name="테스트 전략"
          )
          
          # When
          self.publisher.subscribe(StrategyCreated, handler)
          self.publisher.publish(event)
          
          # Then
          handler.assert_called_once_with(event)
      
      def test_multiple_handlers_for_same_event(self):
          # Given
          handler1 = Mock()
          handler2 = Mock()
          event = StrategyCreated(
              strategy_id=StrategyId("TEST_001"),
              strategy_name="테스트 전략"
          )
          
          # When
          self.publisher.subscribe(StrategyCreated, handler1)
          self.publisher.subscribe(StrategyCreated, handler2)
          self.publisher.publish(event)
          
          # Then
          handler1.assert_called_once_with(event)
          handler2.assert_called_once_with(event)
      
      def test_global_handler(self):
          # Given
          global_handler = Mock()
          specific_handler = Mock()
          event = StrategyCreated(
              strategy_id=StrategyId("TEST_001"),
              strategy_name="테스트 전략"
          )
          
          # When
          self.publisher.subscribe_global(global_handler)
          self.publisher.subscribe(StrategyCreated, specific_handler)
          self.publisher.publish(event)
          
          # Then
          global_handler.assert_called_once_with(event)
          specific_handler.assert_called_once_with(event)
      
      def test_unsubscribe_handler(self):
          # Given
          handler = Mock()
          event = StrategyCreated(
              strategy_id=StrategyId("TEST_001"),
              strategy_name="테스트 전략"
          )
          
          # When
          self.publisher.subscribe(StrategyCreated, handler)
          result = self.publisher.unsubscribe(StrategyCreated, handler)
          self.publisher.publish(event)
          
          # Then
          assert result == True
          handler.assert_not_called()
      
      def test_handler_exception_does_not_affect_other_handlers(self):
          # Given
          failing_handler = Mock(side_effect=Exception("Handler failed"))
          working_handler = Mock()
          event = StrategyCreated(
              strategy_id=StrategyId("TEST_001"),
              strategy_name="테스트 전략"
          )
          
          # When
          self.publisher.subscribe(StrategyCreated, failing_handler)
          self.publisher.subscribe(StrategyCreated, working_handler)
          self.publisher.publish(event)
          
          # Then
          failing_handler.assert_called_once_with(event)
          working_handler.assert_called_once_with(event)
      
      def test_disable_and_enable_publisher(self):
          # Given
          handler = Mock()
          event = StrategyCreated(
              strategy_id=StrategyId("TEST_001"),
              strategy_name="테스트 전략"
          )
          self.publisher.subscribe(StrategyCreated, handler)
          
          # When: 비활성화 후 이벤트 발행
          self.publisher.disable()
          self.publisher.publish(event)
          
          # Then: 핸들러 호출되지 않음
          handler.assert_not_called()
          
          # When: 재활성화 후 이벤트 발행
          self.publisher.enable()
          self.publisher.publish(event)
          
          # Then: 핸들러 호출됨
          handler.assert_called_once_with(event)
  ```

- [ ] `tests/domain/events/test_strategy_events.py` 파일 생성:
  ```python
  import pytest
  from datetime import datetime
  
  from upbit_auto_trading.domain.events.strategy_events import (
      StrategyCreated, StrategyUpdated, TriggerAdded
  )
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  from upbit_auto_trading.domain.value_objects.trigger_id import TriggerId
  
  class TestStrategyEvents:
      def test_strategy_created_event(self):
          # Given
          strategy_id = StrategyId("TEST_001")
          
          # When
          event = StrategyCreated(
              strategy_id=strategy_id,
              strategy_name="테스트 전략",
              created_by="user"
          )
          
          # Then
          assert event.strategy_id == strategy_id
          assert event.strategy_name == "테스트 전략"
          assert event.created_by == "user"
          assert event.event_type == "StrategyCreated"
          assert event.event_id is not None
          assert isinstance(event.occurred_at, datetime)
      
      def test_event_to_dict_serialization(self):
          # Given
          event = StrategyCreated(
              strategy_id=StrategyId("TEST_001"),
              strategy_name="테스트 전략"
          )
          
          # When
          event_dict = event.to_dict()
          
          # Then
          assert event_dict["event_type"] == "StrategyCreated"
          assert event_dict["data"]["strategy_id"] == "TEST_001"
          assert event_dict["data"]["strategy_name"] == "테스트 전략"
          assert "event_id" in event_dict
          assert "occurred_at" in event_dict
      
      def test_trigger_added_event(self):
          # Given
          strategy_id = StrategyId("STRATEGY_001")
          trigger_id = TriggerId("TRIGGER_001")
          
          # When
          event = TriggerAdded(
              strategy_id=strategy_id,
              trigger_id=trigger_id,
              trigger_type="ENTRY",
              variable_id="RSI"
          )
          
          # Then
          assert event.strategy_id == strategy_id
          assert event.trigger_id == trigger_id
          assert event.trigger_type == "ENTRY"
          assert event.variable_id == "RSI"
  ```

### 12. **[통합]** 기존 엔티티와 서비스에 이벤트 시스템 통합
- [ ] 도메인 서비스들이 이벤트를 발행하도록 수정
- [ ] Repository save 메서드에서 엔티티의 도메인 이벤트를 발행하도록 인터페이스 수정:
  ```python
  # Repository 인터페이스에 이벤트 발행 지원 추가
  from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher
  
  class StrategyRepository(BaseRepository[Strategy, StrategyId]):
      # ... 기존 코드 ...
      
      @abstractmethod
      def save(self, strategy: Strategy) -> None:
          """전략 저장 후 도메인 이벤트 발행"""
          # 구현체에서 저장 후 이벤트 발행 처리
          pass
  ```

## Verification Criteria (완료 검증 조건)

### **[이벤트 정의 검증]** 모든 도메인 이벤트 클래스 구현 확인
- [ ] 모든 이벤트 클래스 파일이 올바른 위치에 생성되었는지 확인
- [ ] 각 이벤트가 DomainEvent를 상속하고 적절한 데이터를 포함하는지 확인
- [ ] 이벤트 직렬화(`to_dict()`) 기능이 정상 동작하는지 확인

### **[이벤트 발행자 검증]** DomainEventPublisher 동작 확인
- [ ] `pytest tests/domain/events/test_domain_event_publisher.py -v` 실행하여 모든 테스트 통과 확인
- [ ] 동기/비동기 이벤트 발행이 모두 정상 동작하는지 확인
- [ ] 핸들러 예외가 다른 핸들러에 영향을 주지 않는지 확인

### **[엔티티 통합 검증]** 도메인 엔티티에서 이벤트 발행 확인
- [ ] Python REPL에서 전략 생성 시 이벤트가 발행되는지 확인:
  ```python
  from upbit_auto_trading.domain.entities.strategy import Strategy
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher
  
  # 이벤트 핸들러 등록
  def event_handler(event):
      print(f"이벤트 수신: {event.event_type} - {event.to_dict()}")
  
  publisher = get_domain_event_publisher()
  publisher.subscribe_global(event_handler)
  
  # 전략 생성 및 이벤트 확인
  strategy = Strategy.create_new(StrategyId("TEST_001"), "테스트 전략")
  events = strategy.get_domain_events()
  
  # 이벤트 발행
  publisher.publish_all(events)
  
  # 이벤트 클리어
  strategy.clear_domain_events()
  
  print("✅ 엔티티 이벤트 발행 검증 완료")
  ```

### **[서비스 통합 검증]** 도메인 서비스에서 이벤트 발행 확인
- [ ] Python REPL에서 트리거 평가 시 이벤트가 발행되는지 확인:
  ```python
  from upbit_auto_trading.domain.services.trigger_evaluation_service import (
      TriggerEvaluationService, MarketData
  )
  from upbit_auto_trading.domain.entities.trigger import Trigger, TradingVariable
  from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher
  from datetime import datetime
  
  # 이벤트 핸들러 등록
  event_count = 0
  def count_events(event):
      global event_count
      event_count += 1
      print(f"이벤트 수신: {event.event_type}")
  
  publisher = get_domain_event_publisher()
  publisher.subscribe_global(count_events)
  
  # 트리거 평가 서비스 생성
  service = TriggerEvaluationService()
  
  # 테스트 데이터
  trigger = create_test_trigger()  # 헬퍼 함수 필요
  market_data = MarketData("KRW-BTC", datetime.now(), 50000, 1000, {"RSI": 25})
  
  # 트리거 평가 (이벤트 자동 발행)
  result = service.evaluate_trigger(trigger, market_data)
  
  print(f"발행된 이벤트 수: {event_count}")
  assert event_count > 0, "트리거 평가 시 이벤트가 발행되어야 합니다"
  
  print("✅ 서비스 이벤트 발행 검증 완료")
  ```

### **[이벤트 체계 검증]** 전체 이벤트 시스템 일관성 확인
- [ ] 모든 이벤트 타입이 일관된 명명 규칙을 따르는지 확인
- [ ] 이벤트 간 상관관계(correlation_id, causation_id)가 올바르게 설정되는지 확인
- [ ] 이벤트 메타데이터가 적절히 활용되는지 확인

### **[성능 검증]** 이벤트 발행 성능 확인
- [ ] 대량 이벤트 발행 시 성능 저하가 없는지 확인:
  ```python
  import time
  from upbit_auto_trading.domain.events.strategy_events import StrategyCreated
  from upbit_auto_trading.domain.events.domain_event_publisher import get_domain_event_publisher
  from upbit_auto_trading.domain.value_objects.strategy_id import StrategyId
  
  publisher = get_domain_event_publisher()
  
  # 성능 테스트용 핸들러
  processed_count = 0
  def performance_handler(event):
      global processed_count
      processed_count += 1
  
  publisher.subscribe_global(performance_handler)
  
  # 1000개 이벤트 발행 시간 측정
  start_time = time.time()
  events = []
  for i in range(1000):
      event = StrategyCreated(
          strategy_id=StrategyId(f"PERF_TEST_{i:04d}"),
          strategy_name=f"성능 테스트 전략 {i}"
      )
      events.append(event)
  
  publisher.publish_all(events)
  end_time = time.time()
  
  duration = end_time - start_time
  print(f"1000개 이벤트 발행 시간: {duration:.3f}초")
  print(f"처리된 이벤트 수: {processed_count}")
  
  assert duration < 1.0, "1000개 이벤트 발행이 1초 이내에 완료되어야 합니다"
  assert processed_count == 1000, "모든 이벤트가 처리되어야 합니다"
  
  print("✅ 이벤트 시스템 성능 검증 완료")
  ```

### **[메모리 누수 검증]** 이벤트 핸들러 메모리 관리 확인
- [ ] 이벤트 핸들러 등록/해제가 정상적으로 동작하는지 확인
- [ ] 대량 이벤트 처리 후 메모리 사용량이 적절한 수준으로 유지되는지 확인

## Notes (주의사항)
- 이 단계에서는 이벤트 시스템의 기본 구조만 구현합니다. 실제 이벤트 핸들러들은 Phase 2: Application Layer에서 구현할 예정입니다.
- 비동기 이벤트 처리는 기본 구조만 제공하며, 실제 비동기 처리 로직은 Infrastructure Layer에서 완성할 예정입니다.
- 이벤트 저장소(Event Store) 기능은 포함하지 않습니다. 필요 시 추후 Infrastructure Layer에서 추가할 수 있습니다.
- 현재는 인메모리 이벤트 발행만 지원하며, 분산 시스템을 위한 메시지 큐 연동은 향후 확장사항입니다.
- 모든 이벤트는 도메인 관점에서 정의되어야 하며, 기술적 구현 세부사항을 포함하지 않아야 합니다.
