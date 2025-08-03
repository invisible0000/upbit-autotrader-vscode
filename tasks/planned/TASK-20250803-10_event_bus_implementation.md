# TASK-20250803-10

## Title
Infrastructure Layer - 이벤트 버스 구현 (도메인 이벤트 처리)

## Objective (목표)
도메인 계층에서 발생하는 이벤트들을 Infrastructure Layer에서 효율적으로 처리하기 위한 이벤트 버스 시스템을 구현합니다. 비동기 이벤트 처리, 이벤트 라우팅, 재시도 메커니즘, 이벤트 저장소 등을 포함한 완전한 이벤트 기반 아키텍처를 제공합니다.

## Source of Truth (준거 문서)
'리팩토링 계획 브리핑 문서' - Section "Phase 3: Infrastructure Layer 구현 (2주)" > "3.3 이벤트 버스 구현 (3일)"

## Pre-requisites (선행 조건)
- `TASK-20250803-04`: Domain Events 시스템 구현 완료
- `TASK-20250803-07`: Event Handlers 및 Notification 시스템 구현 완료
- `TASK-20250803-08`: Repository 구현 완료

## Detailed Steps (상세 실행 절차)

### 1. **[분석]** 이벤트 버스 요구사항 및 아키텍처 설계
- [ ] 도메인 이벤트 처리 패턴 분석 (Publish-Subscribe)
- [ ] 비동기 처리 요구사항 (백그라운드 태스크, 큐 시스템)
- [ ] 이벤트 순서 보장 및 재시도 메커니즘
- [ ] 이벤트 저장 및 복구 전략 (Event Sourcing 기초)

### 2. **[폴더 구조 생성]** Event Bus 인프라 구조
- [ ] `upbit_auto_trading/infrastructure/events/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/events/bus/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/events/storage/` 폴더 생성
- [ ] `upbit_auto_trading/infrastructure/events/processors/` 폴더 생성

### 3. **[새 코드 작성]** 이벤트 버스 기본 인터페이스
- [ ] `upbit_auto_trading/infrastructure/events/bus/event_bus_interface.py` 생성:
```python
from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Any, Optional, Type
import asyncio
from datetime import datetime

from upbit_auto_trading.domain.events.domain_event import DomainEvent

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
                 is_async: bool = True, priority: int = 1, retry_count: int = 3) -> str:
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
```

### 4. **[새 코드 작성]** 메모리 기반 이벤트 버스 구현
- [ ] `upbit_auto_trading/infrastructure/events/bus/in_memory_event_bus.py` 생성:
```python
import asyncio
import logging
import time
from typing import List, Callable, Dict, Any, Optional, Type, Set
from collections import defaultdict, deque
from datetime import datetime, timedelta
import traceback

from upbit_auto_trading.domain.events.domain_event import DomainEvent
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import (
    IEventBus, EventSubscription, EventProcessingResult, IEventStorage
)

class InMemoryEventBus(IEventBus):
    """메모리 기반 이벤트 버스 구현"""
    
    def __init__(self, event_storage: Optional[IEventStorage] = None,
                 max_queue_size: int = 10000, worker_count: int = 4,
                 batch_size: int = 10, batch_timeout_seconds: float = 1.0):
        self._subscriptions: Dict[Type[DomainEvent], List[EventSubscription]] = defaultdict(list)
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._event_storage = event_storage
        self._worker_count = worker_count
        self._batch_size = batch_size
        self._batch_timeout = batch_timeout_seconds
        
        # 실행 상태
        self._is_running = False
        self._workers: List[asyncio.Task] = []
        self._lock = asyncio.Lock()
        
        # 통계
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'processing_time_total': 0.0,
            'last_reset': datetime.now()
        }
        
        # 실패한 이벤트 관리
        self._failed_events: deque = deque(maxlen=1000)
        self._retry_queue: asyncio.Queue = asyncio.Queue()
        
        self._logger = logging.getLogger(__name__)
    
    async def publish(self, event: DomainEvent) -> None:
        """단일 이벤트 발행"""
        if not self._is_running:
            raise RuntimeError("이벤트 버스가 시작되지 않았습니다")
        
        try:
            # 이벤트 저장 (선택적)
            if self._event_storage:
                event.event_id = await self._event_storage.store_event(event)
            
            # 큐에 추가
            await self._event_queue.put(event)
            
            async with self._lock:
                self._stats['events_published'] += 1
            
            self._logger.debug(f"이벤트 발행됨: {event.__class__.__name__} (ID: {event.event_id})")
            
        except asyncio.QueueFull:
            self._logger.error(f"이벤트 큐가 가득참. 이벤트 삭제: {event.__class__.__name__}")
            raise RuntimeError("이벤트 큐 용량 초과")
        
        except Exception as e:
            self._logger.error(f"이벤트 발행 실패: {event.__class__.__name__} - {e}")
            raise
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """배치 이벤트 발행"""
        if not events:
            return
        
        # 이벤트 저장 (배치)
        if self._event_storage:
            for event in events:
                if not event.event_id:
                    event.event_id = await self._event_storage.store_event(event)
        
        # 큐에 배치 추가
        for event in events:
            try:
                await self._event_queue.put(event)
                async with self._lock:
                    self._stats['events_published'] += 1
            except asyncio.QueueFull:
                self._logger.error(f"배치 이벤트 발행 중 큐 가득참: {event.__class__.__name__}")
                break
        
        self._logger.info(f"배치 이벤트 {len(events)}개 발행 완료")
    
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable,
                 is_async: bool = True, priority: int = 1, retry_count: int = 3) -> str:
        """이벤트 구독"""
        subscription = EventSubscription(
            event_type=event_type,
            handler=handler,
            is_async=is_async,
            priority=priority,
            retry_count=retry_count
        )
        
        # 우선순위순으로 삽입 정렬
        subscriptions = self._subscriptions[event_type]
        insert_index = 0
        for i, existing in enumerate(subscriptions):
            if subscription.priority < existing.priority:
                insert_index = i
                break
            insert_index = i + 1
        
        subscriptions.insert(insert_index, subscription)
        
        self._logger.info(f"이벤트 구독 등록: {event_type.__name__} -> {handler.__name__}")
        return subscription.subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """구독 취소"""
        for event_type, subscriptions in self._subscriptions.items():
            for i, subscription in enumerate(subscriptions):
                if subscription.subscription_id == subscription_id:
                    del subscriptions[i]
                    self._logger.info(f"구독 취소됨: {subscription_id}")
                    return True
        
        return False
    
    async def start(self) -> None:
        """이벤트 버스 시작"""
        if self._is_running:
            return
        
        self._is_running = True
        
        # 워커 태스크 시작
        for i in range(self._worker_count):
            worker_task = asyncio.create_task(
                self._worker_loop(f"worker-{i}")
            )
            self._workers.append(worker_task)
        
        # 재시도 워커 시작
        retry_worker = asyncio.create_task(self._retry_worker_loop())
        self._workers.append(retry_worker)
        
        self._logger.info(f"이벤트 버스 시작됨 (워커 {self._worker_count}개)")
    
    async def stop(self) -> None:
        """이벤트 버스 중지"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # 워커 태스크 종료
        for worker in self._workers:
            worker.cancel()
        
        # 완료 대기
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        self._logger.info("이벤트 버스 중지됨")
    
    async def _worker_loop(self, worker_name: str) -> None:
        """워커 루프"""
        self._logger.debug(f"워커 시작됨: {worker_name}")
        
        while self._is_running:
            try:
                # 배치로 이벤트 수집
                events = []
                deadline = time.time() + self._batch_timeout
                
                while len(events) < self._batch_size and time.time() < deadline:
                    try:
                        timeout = max(0.1, deadline - time.time())
                        event = await asyncio.wait_for(
                            self._event_queue.get(), 
                            timeout=timeout
                        )
                        events.append(event)
                    except asyncio.TimeoutError:
                        break
                
                # 수집된 이벤트 처리
                if events:
                    await self._process_events_batch(events, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"워커 루프 오류 {worker_name}: {e}")
                await asyncio.sleep(1)
        
        self._logger.debug(f"워커 종료됨: {worker_name}")
    
    async def _process_events_batch(self, events: List[DomainEvent], worker_name: str) -> None:
        """이벤트 배치 처리"""
        for event in events:
            await self._process_single_event(event, worker_name)
    
    async def _process_single_event(self, event: DomainEvent, worker_name: str) -> None:
        """단일 이벤트 처리"""
        event_type = type(event)
        subscriptions = self._subscriptions.get(event_type, [])
        
        if not subscriptions:
            self._logger.debug(f"구독자 없음: {event_type.__name__}")
            return
        
        start_time = time.time()
        success_count = 0
        failure_count = 0
        
        # 모든 구독자에게 이벤트 전달
        for subscription in subscriptions:
            try:
                result = await self._invoke_handler(event, subscription, worker_name)
                
                if result.success:
                    success_count += 1
                else:
                    failure_count += 1
                    await self._handle_processing_failure(event, subscription, result)
                
                # 결과 저장
                if self._event_storage and event.event_id:
                    await self._event_storage.mark_event_processed(event.event_id, result)
                
            except Exception as e:
                failure_count += 1
                error_msg = f"핸들러 호출 실패: {subscription.handler.__name__} - {e}"
                self._logger.error(error_msg)
                
                result = EventProcessingResult(
                    event_id=event.event_id or 'unknown',
                    success=False,
                    error_message=error_msg
                )
                await self._handle_processing_failure(event, subscription, result)
        
        # 통계 업데이트
        processing_time = (time.time() - start_time) * 1000
        async with self._lock:
            self._stats['events_processed'] += 1
            self._stats['events_failed'] += failure_count
            self._stats['processing_time_total'] += processing_time
        
        self._logger.debug(
            f"이벤트 처리 완료: {event_type.__name__} "
            f"(성공: {success_count}, 실패: {failure_count}, "
            f"처리시간: {processing_time:.1f}ms, 워커: {worker_name})"
        )
    
    async def _invoke_handler(self, event: DomainEvent, subscription: EventSubscription,
                            worker_name: str) -> EventProcessingResult:
        """핸들러 호출"""
        start_time = time.time()
        
        try:
            if subscription.is_async:
                if asyncio.iscoroutinefunction(subscription.handler):
                    await subscription.handler(event)
                else:
                    # 동기 함수를 스레드풀에서 실행
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, subscription.handler, event)
            else:
                subscription.handler(event)
            
            processing_time = (time.time() - start_time) * 1000
            
            return EventProcessingResult(
                event_id=event.event_id or 'unknown',
                success=True,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_msg = f"핸들러 실행 오류: {subscription.handler.__name__} - {str(e)}"
            
            return EventProcessingResult(
                event_id=event.event_id or 'unknown',
                success=False,
                error_message=error_msg,
                processing_time_ms=processing_time
            )
    
    async def _handle_processing_failure(self, event: DomainEvent, 
                                       subscription: EventSubscription,
                                       result: EventProcessingResult) -> None:
        """처리 실패 이벤트 처리"""
        # 재시도 큐에 추가 (재시도 횟수 체크)
        if result.retry_attempt < subscription.retry_count:
            retry_event = {
                'event': event,
                'subscription': subscription,
                'retry_attempt': result.retry_attempt + 1,
                'scheduled_time': time.time() + (2 ** result.retry_attempt)  # 지수 백오프
            }
            
            try:
                await self._retry_queue.put(retry_event)
                self._logger.info(
                    f"재시도 스케줄됨: {event.__class__.__name__} "
                    f"(시도 {result.retry_attempt + 1}/{subscription.retry_count})"
                )
            except asyncio.QueueFull:
                self._logger.error("재시도 큐가 가득참")
        else:
            # 최대 재시도 횟수 초과 - 실패 이벤트로 기록
            self._failed_events.append({
                'event': event,
                'subscription': subscription,
                'final_result': result,
                'failed_at': datetime.now()
            })
            
            self._logger.error(
                f"이벤트 처리 최종 실패: {event.__class__.__name__} "
                f"- {result.error_message}"
            )
    
    async def _retry_worker_loop(self) -> None:
        """재시도 워커 루프"""
        self._logger.debug("재시도 워커 시작됨")
        
        while self._is_running:
            try:
                retry_item = await asyncio.wait_for(
                    self._retry_queue.get(), 
                    timeout=1.0
                )
                
                # 스케줄된 시간까지 대기
                wait_time = retry_item['scheduled_time'] - time.time()
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
                # 재시도 실행
                result = await self._invoke_handler(
                    retry_item['event'],
                    retry_item['subscription'],
                    'retry-worker'
                )
                
                result.retry_attempt = retry_item['retry_attempt']
                
                if not result.success:
                    await self._handle_processing_failure(
                        retry_item['event'],
                        retry_item['subscription'],
                        result
                    )
                else:
                    self._logger.info(
                        f"재시도 성공: {retry_item['event'].__class__.__name__} "
                        f"(시도 {result.retry_attempt})"
                    )
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"재시도 워커 오류: {e}")
                await asyncio.sleep(1)
        
        self._logger.debug("재시도 워커 종료됨")
    
    def get_statistics(self) -> Dict[str, Any]:
        """처리 통계 조회"""
        current_time = datetime.now()
        uptime = current_time - self._stats['last_reset']
        
        avg_processing_time = 0.0
        if self._stats['events_processed'] > 0:
            avg_processing_time = (
                self._stats['processing_time_total'] / self._stats['events_processed']
            )
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'events_published': self._stats['events_published'],
            'events_processed': self._stats['events_processed'],
            'events_failed': self._stats['events_failed'],
            'avg_processing_time_ms': round(avg_processing_time, 2),
            'queue_size': self._event_queue.qsize(),
            'retry_queue_size': self._retry_queue.qsize(),
            'failed_events_count': len(self._failed_events),
            'subscription_count': sum(len(subs) for subs in self._subscriptions.values()),
            'is_running': self._is_running,
            'worker_count': len(self._workers)
        }
    
    def get_failed_events(self) -> List[Dict[str, Any]]:
        """실패한 이벤트 목록 조회"""
        return list(self._failed_events)
    
    def clear_failed_events(self) -> None:
        """실패한 이벤트 목록 초기화"""
        self._failed_events.clear()
        self._logger.info("실패한 이벤트 목록이 초기화되었습니다")
```

### 5. **[새 코드 작성]** SQLite 기반 이벤트 저장소
- [ ] `upbit_auto_trading/infrastructure/events/storage/sqlite_event_storage.py` 생성:
```python
import json
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from upbit_auto_trading.domain.events.domain_event import DomainEvent
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import (
    IEventStorage, EventProcessingResult
)
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

class SqliteEventStorage(IEventStorage):
    """SQLite 기반 이벤트 저장소"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db = db_manager
        self._logger = logging.getLogger(__name__)
        self._ensure_tables()
    
    def _ensure_tables(self) -> None:
        """이벤트 저장용 테이블 생성"""
        create_events_table = """
        CREATE TABLE IF NOT EXISTS event_store (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            aggregate_id TEXT NOT NULL,
            aggregate_type TEXT NOT NULL,
            event_data TEXT NOT NULL,
            metadata TEXT,
            version INTEGER NOT NULL DEFAULT 1,
            occurred_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_processed BOOLEAN DEFAULT 0,
            processed_at TIMESTAMP,
            processing_result TEXT
        )
        """
        
        create_processing_log_table = """
        CREATE TABLE IF NOT EXISTS event_processing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            handler_name TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            processing_time_ms REAL,
            retry_attempt INTEGER DEFAULT 0,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES event_store(event_id)
        )
        """
        
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_event_store_aggregate ON event_store(aggregate_id, aggregate_type)",
            "CREATE INDEX IF NOT EXISTS idx_event_store_type ON event_store(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_event_store_occurred ON event_store(occurred_at)",
            "CREATE INDEX IF NOT EXISTS idx_event_store_processed ON event_store(is_processed)",
            "CREATE INDEX IF NOT EXISTS idx_processing_log_event ON event_processing_log(event_id)"
        ]
        
        try:
            self._db.execute_command('strategies', create_events_table)
            self._db.execute_command('strategies', create_processing_log_table)
            
            for index_sql in create_indexes:
                self._db.execute_command('strategies', index_sql)
            
            self._logger.info("이벤트 저장소 테이블 초기화 완료")
            
        except Exception as e:
            self._logger.error(f"이벤트 저장소 테이블 생성 실패: {e}")
            raise
    
    async def store_event(self, event: DomainEvent) -> str:
        """이벤트 저장"""
        try:
            # 이벤트 ID 생성 (없을 경우)
            if not event.event_id:
                import uuid
                event.event_id = str(uuid.uuid4())
            
            # 이벤트 데이터 직렬화
            event_data = self._serialize_event(event)
            metadata = self._serialize_metadata(event)
            
            insert_query = """
            INSERT INTO event_store (
                event_id, event_type, aggregate_id, aggregate_type,
                event_data, metadata, version, occurred_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                event.event_id,
                event.__class__.__name__,
                event.aggregate_id,
                event.aggregate_type,
                event_data,
                metadata,
                event.version,
                event.occurred_at.isoformat()
            )
            
            self._db.execute_command('strategies', insert_query, params)
            
            self._logger.debug(f"이벤트 저장 완료: {event.event_id}")
            return event.event_id
            
        except Exception as e:
            self._logger.error(f"이벤트 저장 실패: {e}")
            raise
    
    async def get_event(self, event_id: str) -> Optional[DomainEvent]:
        """이벤트 조회"""
        try:
            query = "SELECT * FROM event_store WHERE event_id = ?"
            
            rows = self._db.execute_query('strategies', query, (event_id,))
            
            if not rows:
                return None
            
            return self._deserialize_event(dict(rows[0]))
            
        except Exception as e:
            self._logger.error(f"이벤트 조회 실패 {event_id}: {e}")
            return None
    
    async def get_events_by_aggregate(self, aggregate_id: str, 
                                    aggregate_type: str) -> List[DomainEvent]:
        """집합체별 이벤트 조회"""
        try:
            query = """
            SELECT * FROM event_store 
            WHERE aggregate_id = ? AND aggregate_type = ?
            ORDER BY occurred_at ASC, version ASC
            """
            
            rows = self._db.execute_query('strategies', query, (aggregate_id, aggregate_type))
            
            events = []
            for row in rows:
                event = self._deserialize_event(dict(row))
                if event:
                    events.append(event)
            
            return events
            
        except Exception as e:
            self._logger.error(f"집합체 이벤트 조회 실패 {aggregate_id}: {e}")
            return []
    
    async def get_unprocessed_events(self, limit: int = 100) -> List[DomainEvent]:
        """미처리 이벤트 조회"""
        try:
            query = """
            SELECT * FROM event_store 
            WHERE is_processed = 0
            ORDER BY occurred_at ASC
            LIMIT ?
            """
            
            rows = self._db.execute_query('strategies', query, (limit,))
            
            events = []
            for row in rows:
                event = self._deserialize_event(dict(row))
                if event:
                    events.append(event)
            
            return events
            
        except Exception as e:
            self._logger.error(f"미처리 이벤트 조회 실패: {e}")
            return []
    
    async def mark_event_processed(self, event_id: str, 
                                  result: EventProcessingResult) -> None:
        """이벤트 처리 완료 표시"""
        try:
            # 이벤트 상태 업데이트
            update_query = """
            UPDATE event_store 
            SET is_processed = ?, processed_at = ?, processing_result = ?
            WHERE event_id = ?
            """
            
            processing_result_json = json.dumps({
                'success': result.success,
                'error_message': result.error_message,
                'processing_time_ms': result.processing_time_ms,
                'retry_attempt': result.retry_attempt,
                'processed_at': result.processed_at.isoformat()
            })
            
            self._db.execute_command('strategies', update_query, (
                1 if result.success else 0,
                result.processed_at.isoformat(),
                processing_result_json,
                event_id
            ))
            
            # 처리 로그 추가
            log_query = """
            INSERT INTO event_processing_log (
                event_id, handler_name, success, error_message,
                processing_time_ms, retry_attempt
            ) VALUES (?, ?, ?, ?, ?, ?)
            """
            
            # 핸들러 이름은 결과에서 추출하거나 기본값 사용
            handler_name = getattr(result, 'handler_name', 'unknown')
            
            self._db.execute_command('strategies', log_query, (
                event_id,
                handler_name,
                result.success,
                result.error_message,
                result.processing_time_ms,
                result.retry_attempt
            ))
            
            self._logger.debug(f"이벤트 처리 상태 업데이트: {event_id} - {result.success}")
            
        except Exception as e:
            self._logger.error(f"이벤트 처리 상태 업데이트 실패 {event_id}: {e}")
    
    def _serialize_event(self, event: DomainEvent) -> str:
        """이벤트 직렬화"""
        try:
            # 이벤트 속성을 딕셔너리로 변환
            event_dict = {}
            for key, value in event.__dict__.items():
                if not key.startswith('_'):
                    if isinstance(value, datetime):
                        event_dict[key] = value.isoformat()
                    elif hasattr(value, '__dict__'):
                        # 복합 객체는 딕셔너리로 변환
                        event_dict[key] = value.__dict__
                    else:
                        event_dict[key] = value
            
            return json.dumps(event_dict, default=str)
            
        except Exception as e:
            self._logger.error(f"이벤트 직렬화 실패: {e}")
            return "{}"
    
    def _serialize_metadata(self, event: DomainEvent) -> str:
        """메타데이터 직렬화"""
        try:
            metadata = {
                'event_class': event.__class__.__module__ + '.' + event.__class__.__name__,
                'serialized_at': datetime.now().isoformat(),
                'version': getattr(event, 'schema_version', 1)
            }
            
            return json.dumps(metadata)
            
        except Exception as e:
            self._logger.error(f"메타데이터 직렬화 실패: {e}")
            return "{}"
    
    def _deserialize_event(self, event_row: Dict[str, Any]) -> Optional[DomainEvent]:
        """이벤트 역직렬화"""
        try:
            event_data = json.loads(event_row['event_data'])
            metadata = json.loads(event_row.get('metadata', '{}'))
            
            # 이벤트 클래스 동적 로드
            event_class = self._get_event_class(event_row['event_type'], metadata)
            
            if not event_class:
                self._logger.warning(f"이벤트 클래스를 찾을 수 없음: {event_row['event_type']}")
                return None
            
            # 이벤트 객체 재구성
            event = event_class.__new__(event_class)
            
            # 기본 속성 설정
            event.event_id = event_row['event_id']
            event.aggregate_id = event_row['aggregate_id']
            event.aggregate_type = event_row['aggregate_type']
            event.version = event_row['version']
            event.occurred_at = datetime.fromisoformat(event_row['occurred_at'])
            
            # 이벤트 데이터 복원
            for key, value in event_data.items():
                if key not in ['event_id', 'aggregate_id', 'aggregate_type', 'version', 'occurred_at']:
                    setattr(event, key, value)
            
            return event
            
        except Exception as e:
            self._logger.error(f"이벤트 역직렬화 실패: {e}")
            return None
    
    def _get_event_class(self, event_type: str, metadata: Dict[str, Any]):
        """이벤트 클래스 조회"""
        try:
            # 메타데이터에서 전체 클래스 경로 가져오기
            class_path = metadata.get('event_class')
            
            if class_path:
                module_name, class_name = class_path.rsplit('.', 1)
                module = __import__(module_name, fromlist=[class_name])
                return getattr(module, class_name)
            
            # 폴백: 이벤트 타입으로 추정
            # 실제 구현에서는 이벤트 타입 레지스트리 사용 권장
            return None
            
        except Exception as e:
            self._logger.error(f"이벤트 클래스 로드 실패: {e}")
            return None
    
    async def get_event_statistics(self) -> Dict[str, Any]:
        """이벤트 저장소 통계"""
        try:
            stats_query = """
            SELECT 
                COUNT(*) as total_events,
                COUNT(CASE WHEN is_processed = 1 THEN 1 END) as processed_events,
                COUNT(CASE WHEN is_processed = 0 THEN 1 END) as unprocessed_events,
                COUNT(DISTINCT event_type) as unique_event_types,
                COUNT(DISTINCT aggregate_id) as unique_aggregates,
                MIN(occurred_at) as earliest_event,
                MAX(occurred_at) as latest_event
            FROM event_store
            """
            
            rows = self._db.execute_query('strategies', stats_query)
            
            if rows:
                stats = dict(rows[0])
                
                # 이벤트 타입별 통계
                type_query = """
                SELECT event_type, COUNT(*) as count
                FROM event_store
                GROUP BY event_type
                ORDER BY count DESC
                """
                
                type_rows = self._db.execute_query('strategies', type_query)
                stats['event_types'] = [dict(row) for row in type_rows]
                
                return stats
            
            return {}
            
        except Exception as e:
            self._logger.error(f"이벤트 통계 조회 실패: {e}")
            return {}
```

### 6. **[새 코드 작성]** 이벤트 버스 팩토리
- [ ] `upbit_auto_trading/infrastructure/events/event_bus_factory.py` 생성:
```python
from typing import Optional
import logging

from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus, IEventStorage
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.infrastructure.events.storage.sqlite_event_storage import SqliteEventStorage
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

class EventBusFactory:
    """이벤트 버스 팩토리"""
    
    @staticmethod
    def create_in_memory_event_bus(
        event_storage: Optional[IEventStorage] = None,
        max_queue_size: int = 10000,
        worker_count: int = 4,
        batch_size: int = 10,
        batch_timeout_seconds: float = 1.0
    ) -> IEventBus:
        """메모리 기반 이벤트 버스 생성"""
        
        return InMemoryEventBus(
            event_storage=event_storage,
            max_queue_size=max_queue_size,
            worker_count=worker_count,
            batch_size=batch_size,
            batch_timeout_seconds=batch_timeout_seconds
        )
    
    @staticmethod
    def create_sqlite_event_storage(db_manager: DatabaseManager) -> IEventStorage:
        """SQLite 이벤트 저장소 생성"""
        return SqliteEventStorage(db_manager)
    
    @staticmethod
    def create_default_event_bus(db_manager: DatabaseManager) -> IEventBus:
        """기본 설정으로 이벤트 버스 생성 (메모리 + SQLite 저장소)"""
        
        # SQLite 이벤트 저장소 생성
        event_storage = EventBusFactory.create_sqlite_event_storage(db_manager)
        
        # 메모리 이벤트 버스 생성 (저장소 포함)
        event_bus = EventBusFactory.create_in_memory_event_bus(
            event_storage=event_storage,
            max_queue_size=10000,
            worker_count=4,
            batch_size=10,
            batch_timeout_seconds=1.0
        )
        
        logger = logging.getLogger(__name__)
        logger.info("기본 이벤트 버스 생성 완료 (InMemory + SQLite)")
        
        return event_bus
```

### 7. **[새 코드 작성]** 도메인 이벤트 Publisher 업데이트
- [ ] `upbit_auto_trading/infrastructure/events/domain_event_publisher_impl.py` 생성:
```python
import asyncio
from typing import List
import logging

from upbit_auto_trading.domain.events.domain_event import DomainEvent
from upbit_auto_trading.domain.events.domain_event_publisher import DomainEventPublisher
from upbit_auto_trading.infrastructure.events.bus.event_bus_interface import IEventBus

class InfrastructureDomainEventPublisher(DomainEventPublisher):
    """Infrastructure 이벤트 버스를 사용하는 도메인 이벤트 Publisher"""
    
    def __init__(self, event_bus: IEventBus):
        super().__init__()
        self._event_bus = event_bus
        self._logger = logging.getLogger(__name__)
    
    async def publish(self, event: DomainEvent) -> None:
        """단일 이벤트 발행"""
        try:
            await self._event_bus.publish(event)
            self._logger.debug(f"도메인 이벤트 발행: {event.__class__.__name__}")
        except Exception as e:
            self._logger.error(f"도메인 이벤트 발행 실패: {event.__class__.__name__} - {e}")
            raise
    
    async def publish_all(self, events: List[DomainEvent]) -> None:
        """배치 이벤트 발행"""
        if not events:
            return
        
        try:
            await self._event_bus.publish_batch(events)
            self._logger.debug(f"도메인 이벤트 배치 발행: {len(events)}개")
        except Exception as e:
            self._logger.error(f"도메인 이벤트 배치 발행 실패: {len(events)}개 - {e}")
            raise
    
    def clear(self) -> None:
        """이벤트 목록 초기화 (상위 클래스 호환성)"""
        # Infrastructure 이벤트 버스에서는 별도 처리 불필요
        pass
```

### 8. **[테스트 코드 작성]** 이벤트 버스 테스트
- [ ] `tests/infrastructure/events/` 폴더 생성
- [ ] `tests/infrastructure/events/test_event_bus.py` 생성:
```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from upbit_auto_trading.domain.events.domain_event import DomainEvent
from upbit_auto_trading.infrastructure.events.bus.in_memory_event_bus import InMemoryEventBus
from upbit_auto_trading.infrastructure.events.event_bus_factory import EventBusFactory

class TestEvent(DomainEvent):
    def __init__(self, test_data: str):
        super().__init__(
            aggregate_id="test-aggregate",
            aggregate_type="TestAggregate"
        )
        self.test_data = test_data

class TestEventBus:
    
    @pytest.fixture
    async def event_bus(self):
        bus = EventBusFactory.create_in_memory_event_bus(
            max_queue_size=1000,
            worker_count=2,
            batch_size=5,
            batch_timeout_seconds=0.1
        )
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_bus):
        # Given
        received_events = []
        
        async def test_handler(event: TestEvent):
            received_events.append(event)
        
        # When
        subscription_id = event_bus.subscribe(TestEvent, test_handler)
        
        test_event = TestEvent("test data")
        await event_bus.publish(test_event)
        
        # 이벤트 처리 대기
        await asyncio.sleep(0.2)
        
        # Then
        assert len(received_events) == 1
        assert received_events[0].test_data == "test data"
        assert event_bus.unsubscribe(subscription_id)
    
    @pytest.mark.asyncio
    async def test_batch_publish(self, event_bus):
        # Given
        received_events = []
        
        async def batch_handler(event: TestEvent):
            received_events.append(event)
        
        event_bus.subscribe(TestEvent, batch_handler)
        
        # When
        events = [TestEvent(f"data-{i}") for i in range(5)]
        await event_bus.publish_batch(events)
        
        # 배치 처리 대기
        await asyncio.sleep(0.3)
        
        # Then
        assert len(received_events) == 5
        for i, event in enumerate(received_events):
            assert event.test_data == f"data-{i}"
    
    @pytest.mark.asyncio
    async def test_handler_priority(self, event_bus):
        # Given
        execution_order = []
        
        async def high_priority_handler(event: TestEvent):
            execution_order.append("high")
        
        async def low_priority_handler(event: TestEvent):
            execution_order.append("low")
        
        # When (낮은 숫자가 높은 우선순위)
        event_bus.subscribe(TestEvent, low_priority_handler, priority=5)
        event_bus.subscribe(TestEvent, high_priority_handler, priority=1)
        
        await event_bus.publish(TestEvent("priority test"))
        await asyncio.sleep(0.2)
        
        # Then
        assert execution_order == ["high", "low"]
    
    @pytest.mark.asyncio
    async def test_handler_exception_handling(self, event_bus):
        # Given
        successful_calls = []
        
        async def failing_handler(event: TestEvent):
            raise ValueError("Intentional test error")
        
        async def successful_handler(event: TestEvent):
            successful_calls.append(event)
        
        # When
        event_bus.subscribe(TestEvent, failing_handler, retry_count=1)
        event_bus.subscribe(TestEvent, successful_handler)
        
        await event_bus.publish(TestEvent("error test"))
        await asyncio.sleep(0.3)  # 재시도 대기 시간 포함
        
        # Then
        assert len(successful_calls) == 1  # 성공 핸들러는 정상 동작
        
        stats = event_bus.get_statistics()
        assert stats['events_failed'] > 0
    
    @pytest.mark.asyncio
    async def test_statistics(self, event_bus):
        # Given
        async def stats_handler(event: TestEvent):
            pass
        
        event_bus.subscribe(TestEvent, stats_handler)
        
        # When
        for i in range(3):
            await event_bus.publish(TestEvent(f"stats-{i}"))
        
        await asyncio.sleep(0.2)
        
        # Then
        stats = event_bus.get_statistics()
        assert stats['events_published'] == 3
        assert stats['events_processed'] >= 3
        assert stats['is_running'] is True
        assert stats['worker_count'] == 2
        assert 'avg_processing_time_ms' in stats
```

### 9. **[통합]** 이벤트 시스템 초기화 스크립트
- [ ] `upbit_auto_trading/infrastructure/events/event_system_initializer.py` 생성:
```python
import asyncio
import logging
from typing import Optional, Dict, Any

from upbit_auto_trading.infrastructure.events.event_bus_factory import EventBusFactory
from upbit_auto_trading.infrastructure.events.domain_event_publisher_impl import InfrastructureDomainEventPublisher
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.domain.events.domain_event_publisher import DomainEventPublisher

class EventSystemInitializer:
    """이벤트 시스템 초기화 관리"""
    
    @staticmethod
    async def initialize_event_system(
        db_manager: DatabaseManager,
        config: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """완전한 이벤트 시스템 초기화"""
        
        if config is None:
            config = {
                'max_queue_size': 10000,
                'worker_count': 4,
                'batch_size': 10,
                'batch_timeout_seconds': 1.0
            }
        
        logger = logging.getLogger(__name__)
        
        try:
            # 1. 이벤트 버스 생성
            event_bus = EventBusFactory.create_default_event_bus(db_manager)
            
            # 2. 도메인 이벤트 Publisher 생성
            domain_publisher = InfrastructureDomainEventPublisher(event_bus)
            
            # 3. 이벤트 버스 시작
            await event_bus.start()
            
            logger.info("이벤트 시스템 초기화 완료")
            
            return event_bus, domain_publisher
            
        except Exception as e:
            logger.error(f"이벤트 시스템 초기화 실패: {e}")
            raise
    
    @staticmethod
    async def shutdown_event_system(event_bus, timeout: float = 10.0) -> None:
        """이벤트 시스템 종료"""
        logger = logging.getLogger(__name__)
        
        try:
            # 이벤트 버스 정상 종료
            await asyncio.wait_for(event_bus.stop(), timeout=timeout)
            logger.info("이벤트 시스템 종료 완료")
            
        except asyncio.TimeoutError:
            logger.warning(f"이벤트 시스템 종료 타임아웃 ({timeout}초)")
        except Exception as e:
            logger.error(f"이벤트 시스템 종료 실패: {e}")
            raise
```

### 10. **[통합]** Infrastructure Events 패키지 초기화
- [ ] `upbit_auto_trading/infrastructure/events/__init__.py` 생성:
```python
from .event_bus_factory import EventBusFactory
from .bus.event_bus_interface import IEventBus, IEventStorage
from .domain_event_publisher_impl import InfrastructureDomainEventPublisher
from .event_system_initializer import EventSystemInitializer

__all__ = [
    'EventBusFactory',
    'IEventBus', 
    'IEventStorage',
    'InfrastructureDomainEventPublisher',
    'EventSystemInitializer'
]
```

## Verification Criteria (완료 검증 조건)

### **[이벤트 버스 동작 검증]** 전체 이벤트 시스템 정상 동작 확인
- [ ] `pytest tests/infrastructure/events/ -v` 실행하여 모든 테스트 통과
- [ ] Python REPL에서 이벤트 시스템 테스트:
```python
import asyncio
from upbit_auto_trading.infrastructure.events import EventSystemInitializer, EventBusFactory
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

async def test_event_system():
    db_paths = {
        'strategies': 'data/strategies.sqlite3'
    }
    db_manager = DatabaseManager(db_paths)
    
    # 이벤트 시스템 초기화
    event_bus, publisher = await EventSystemInitializer.initialize_event_system(db_manager)
    
    # 통계 확인
    stats = event_bus.get_statistics()
    print(f"이벤트 버스 상태: {stats}")
    
    # 종료
    await EventSystemInitializer.shutdown_event_system(event_bus)
    print("✅ 이벤트 시스템 검증 완료")

asyncio.run(test_event_system())
```

### **[이벤트 저장소 검증]** SQLite 이벤트 저장 및 조회 확인
- [ ] 이벤트 저장 및 조회 기능 테스트
- [ ] 미처리 이벤트 복구 기능 테스트
- [ ] 이벤트 처리 결과 로깅 기능 테스트

### **[성능 검증]** 대량 이벤트 처리 성능 확인
- [ ] 1000개 이벤트 배치 처리 시간 측정 (목표: 5초 이내)
- [ ] 동시 발행/처리 성능 테스트
- [ ] 메모리 사용량 모니터링 (큐 크기 제한 확인)

### **[장애 처리 검증]** 다양한 오류 상황 대응 확인
- [ ] 핸들러 예외 발생 시 재시도 로직 확인
- [ ] 이벤트 버스 재시작 시 미처리 이벤트 복구
- [ ] 큐 용량 초과 시 적절한 에러 메시지

## Notes (주의사항)
- 이벤트 처리 순서가 중요한 경우 단일 워커 사용 권장
- 이벤트 저장소는 선택적으로 사용 (메모리만으로도 동작 가능)
- 실제 프로덕션에서는 Redis나 RabbitMQ 같은 전용 메시지 브로커 고려
- 이벤트 스키마 변경 시 하위 호환성 유지 필요
- 장기간 실행 시 이벤트 저장소 크기 관리 (아카이빙 전략 수립)
