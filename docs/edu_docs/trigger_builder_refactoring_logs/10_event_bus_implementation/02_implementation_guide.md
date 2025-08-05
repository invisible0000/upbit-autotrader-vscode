# 🛠️ Infrastructure Layer 이벤트 버스 구현 가이드

> **목적**: 이벤트 버스 시스템을 처음부터 구현하는 실용적 가이드
> **대상**: 주니어/중급 개발자, Python 비동기 프로그래밍 학습자
> **난이도**: ⭐⭐⭐ (중급)
> **예상 소요 시간**: 3-4시간

## 📋 구현 체크리스트

### Phase 1: 준비 (30분)
- [ ] 프로젝트 구조 이해
- [ ] 필요한 패키지 설치 (`asyncio`, `typing` 등)
- [ ] 기존 Domain Layer 이벤트 시스템 분석

### Phase 2: 핵심 구현 (2-3시간)
- [ ] 이벤트 버스 인터페이스 정의
- [ ] 메모리 기반 이벤트 버스 구현
- [ ] SQLite 이벤트 저장소 구현
- [ ] 팩토리 패턴 구현

### Phase 3: 검증 및 최적화 (1시간)
- [ ] 단위 테스트 작성
- [ ] 성능 테스트 실행
- [ ] 메모리 사용량 최적화

## 🎯 Step-by-Step 구현 가이드

### Step 1: 프로젝트 구조 설정

```bash
# 폴더 구조 생성
mkdir -p upbit_auto_trading/infrastructure/events/{bus,storage,processors}
mkdir -p tests/infrastructure/events/
```

```python
# 필수 import 정리
import asyncio
import json
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Callable, Type, Optional, Any
from concurrent.futures import ThreadPoolExecutor
```

### Step 2: 인터페이스 정의 (파일: `bus/event_bus_interface.py`)

```python
# 1. 이벤트 구독 정보 클래스
@dataclass
class EventSubscription:
    """이벤트 구독 정보"""
    event_type: Type
    handler: Callable
    priority: int = 1

    def __hash__(self):
        return hash((self.event_type.__name__, id(self.handler), self.priority))

# 2. 이벤트 처리 결과 클래스
@dataclass
class EventProcessingResult:
    """이벤트 처리 결과"""
    success: bool
    error_message: Optional[str] = None
    processing_time_ms: float = 0.0
    retry_count: int = 0

# 3. 이벤트 버스 인터페이스
class IEventBus(ABC):
    """이벤트 버스 인터페이스"""

    @abstractmethod
    async def start(self) -> None:
        """이벤트 버스 시작"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """이벤트 버스 중지"""
        pass

    @abstractmethod
    async def publish(self, event) -> bool:
        """이벤트 발행"""
        pass

    @abstractmethod
    def subscribe(self, event_type: Type, handler: Callable, priority: int = 1):
        """이벤트 구독"""
        pass
```

**💡 구현 팁**: 인터페이스를 먼저 정의하면 구현할 메서드들이 명확해집니다.

### Step 3: 메모리 기반 이벤트 버스 구현 (파일: `bus/in_memory_event_bus.py`)

#### 3.1 기본 구조
```python
class InMemoryEventBus(IEventBus):
    """메모리 기반 이벤트 버스"""

    def __init__(self,
                 max_queue_size: int = 1000,
                 worker_count: int = 1,
                 max_retries: int = 3,
                 base_retry_delay: float = 0.1):
        # 이벤트 큐 및 구독자 관리
        self._event_queue = asyncio.Queue(maxsize=max_queue_size)
        self._subscriptions: Dict[Type, List[EventSubscription]] = {}
        self._workers: List[asyncio.Task] = []

        # 설정값들
        self._max_queue_size = max_queue_size
        self._worker_count = worker_count
        self._max_retries = max_retries
        self._base_retry_delay = base_retry_delay

        # 상태 관리
        self._is_running = False
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "total_processing_time_ms": 0.0
        }
```

#### 3.2 워커 구현
```python
async def _worker(self, worker_id: int):
    """이벤트 처리 워커"""
    while self._is_running:
        try:
            # 큐에서 이벤트 가져오기 (타임아웃 설정)
            event = await asyncio.wait_for(
                self._event_queue.get(),
                timeout=1.0
            )

            # 이벤트 처리
            await self._process_event(event)

        except asyncio.TimeoutError:
            continue  # 타임아웃 시 계속 대기
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
```

#### 3.3 이벤트 처리 로직
```python
async def _process_event(self, event):
    """개별 이벤트 처리"""
    event_type = type(event)

    if event_type not in self._subscriptions:
        return  # 구독자가 없으면 무시

    # 우선순위 순으로 핸들러 정렬
    handlers = sorted(
        self._subscriptions[event_type],
        key=lambda s: s.priority,
        reverse=True
    )

    # 각 핸들러로 이벤트 처리
    for subscription in handlers:
        result = await self._process_with_retry(event, subscription.handler)

        if result.success:
            self._stats["events_processed"] += 1
        else:
            self._stats["events_failed"] += 1
```

**💡 구현 팁**:
- 워커 수가 1이면 순서 보장, 여러 개면 성능 향상
- 우선순위 시스템으로 중요한 이벤트 먼저 처리 가능

#### 3.4 재시도 메커니즘
```python
async def _process_with_retry(self, event, handler) -> EventProcessingResult:
    """재시도 로직이 포함된 이벤트 처리"""
    start_time = time.time()

    for attempt in range(self._max_retries + 1):
        try:
            await handler(event)

            processing_time = (time.time() - start_time) * 1000
            return EventProcessingResult(
                success=True,
                processing_time_ms=processing_time,
                retry_count=attempt
            )

        except Exception as e:
            if attempt < self._max_retries:
                # 지수 백오프로 재시도 간격 증가
                delay = self._base_retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            else:
                # 최대 재시도 횟수 초과
                processing_time = (time.time() - start_time) * 1000
                return EventProcessingResult(
                    success=False,
                    error_message=str(e),
                    processing_time_ms=processing_time,
                    retry_count=attempt
                )
```

**💡 구현 팁**: 지수 백오프는 시스템 부하를 줄이면서 일시적 오류 복구에 효과적입니다.

### Step 4: SQLite 이벤트 저장소 구현 (파일: `storage/sqlite_event_storage.py`)

#### 4.1 데이터베이스 스키마 설정
```python
class SqliteEventStorage(IEventStorage):
    """SQLite 기반 이벤트 저장소"""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE,
                    processing_attempts INTEGER DEFAULT 0
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_aggregate_id
                ON events(aggregate_id)
            """)
```

#### 4.2 이벤트 저장 및 조회
```python
async def store_event(self, event) -> bool:
    """이벤트 저장"""
    try:
        event_data = {
            "event_type": type(event).__name__,
            "data": event.__dict__
        }

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO events
                (event_id, event_type, aggregate_id, event_data)
                VALUES (?, ?, ?, ?)
            """, (
                event.event_id,
                type(event).__name__,
                event.aggregate_id,
                json.dumps(event_data)
            ))

        return True

    except Exception as e:
        print(f"Event storage error: {e}")
        return False

async def get_events_by_aggregate(self, aggregate_id: str) -> List:
    """집합체별 이벤트 조회"""
    with sqlite3.connect(self.db_path) as conn:
        cursor = conn.execute("""
            SELECT event_data FROM events
            WHERE aggregate_id = ?
            ORDER BY timestamp
        """, (aggregate_id,))

        events = []
        for row in cursor.fetchall():
            event_data = json.loads(row[0])
            events.append(event_data)

        return events
```

**💡 구현 팁**:
- JSON으로 이벤트 직렬화하면 스키마 변경에 유연
- 인덱스로 조회 성능 최적화

### Step 5: 팩토리 패턴 구현 (파일: `event_bus_factory.py`)

```python
class EventBusFactory:
    """이벤트 버스 생성 팩토리"""

    @staticmethod
    def create_in_memory_event_bus(
        max_queue_size: int = 1000,
        worker_count: int = 1,
        **kwargs
    ) -> InMemoryEventBus:
        """메모리 기반 이벤트 버스 생성"""
        return InMemoryEventBus(
            max_queue_size=max_queue_size,
            worker_count=worker_count,
            **kwargs
        )

    @staticmethod
    def create_sqlite_event_storage(db_path: str = ":memory:") -> SqliteEventStorage:
        """SQLite 이벤트 저장소 생성"""
        return SqliteEventStorage(db_path)

    @staticmethod
    def create_complete_event_system(
        storage_path: str = ":memory:",
        **bus_config
    ) -> tuple[InMemoryEventBus, SqliteEventStorage]:
        """완전한 이벤트 시스템 생성"""
        event_bus = EventBusFactory.create_in_memory_event_bus(**bus_config)
        event_storage = EventBusFactory.create_sqlite_event_storage(storage_path)

        return event_bus, event_storage
```

**💡 구현 팁**: 팩토리 패턴으로 객체 생성을 중앙화하면 설정 관리가 편해집니다.

## 🧪 테스트 작성 가이드

### 기본 테스트 구조
```python
import pytest
import asyncio

@pytest.fixture
async def event_bus():
    """테스트용 이벤트 버스"""
    bus = EventBusFactory.create_in_memory_event_bus(worker_count=1)
    await bus.start()
    yield bus
    await bus.stop()

@pytest.mark.asyncio
async def test_event_publishing_and_processing(event_bus):
    """이벤트 발행 및 처리 테스트"""
    processed_events = []

    async def test_handler(event):
        processed_events.append(event.data)

    # 구독 등록
    event_bus.subscribe(TestEvent, test_handler)

    # 이벤트 발행
    test_event = TestEvent("test_data")
    success = await event_bus.publish(test_event)

    # 처리 대기
    await asyncio.sleep(0.1)

    # 검증
    assert success is True
    assert len(processed_events) == 1
    assert processed_events[0] == "test_data"
```

### 성능 테스트 예시
```python
@pytest.mark.asyncio
async def test_high_volume_processing(event_bus):
    """대량 이벤트 처리 테스트"""
    processed_count = 0

    async def counter_handler(event):
        nonlocal processed_count
        processed_count += 1

    event_bus.subscribe(TestEvent, counter_handler)

    # 1000개 이벤트 발행
    start_time = time.time()
    for i in range(1000):
        await event_bus.publish(TestEvent(f"data-{i}"))

    # 처리 대기
    await asyncio.sleep(2.0)

    total_time = time.time() - start_time

    # 성능 검증
    assert processed_count >= 950  # 95% 이상 처리
    assert total_time < 5.0  # 5초 이내
```

## 🚀 최적화 가이드

### 1. 성능 최적화
```python
# 배치 처리 구현
async def _process_events_batch(self, events: List):
    """이벤트 배치 처리"""
    tasks = []
    for event in events:
        task = asyncio.create_task(self._process_event(event))
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. 메모리 최적화
```python
# 큐 크기 제한으로 메모리 보호
if self._event_queue.qsize() > self._max_queue_size * 0.8:
    # 80% 도달 시 경고 로그
    print(f"Queue size warning: {self._event_queue.qsize()}")
```

### 3. 모니터링 추가
```python
def get_statistics(self) -> Dict[str, Any]:
    """통계 정보 반환"""
    return {
        "events_published": self._stats["events_published"],
        "events_processed": self._stats["events_processed"],
        "events_failed": self._stats["events_failed"],
        "queue_size": self._event_queue.qsize(),
        "worker_count": len(self._workers),
        "avg_processing_time_ms": self._get_avg_processing_time()
    }
```

## ❌ 흔한 실수와 해결책

### 실수 1: 무한 대기
```python
# ❌ 잘못된 방법
event = await self._event_queue.get()  # 무한 대기

# ✅ 올바른 방법
event = await asyncio.wait_for(
    self._event_queue.get(),
    timeout=1.0
)
```

### 실수 2: 예외 처리 누락
```python
# ❌ 잘못된 방법
await handler(event)  # 예외 시 워커 중단

# ✅ 올바른 방법
try:
    await handler(event)
except Exception as e:
    # 로깅하고 계속 진행
    self._logger.error(f"Handler error: {e}")
```

### 실수 3: 리소스 정리 누락
```python
# ✅ 올바른 정리
async def stop(self):
    self._is_running = False

    # 모든 워커 종료 대기
    if self._workers:
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
```

## 📚 확장 아이디어

### 1. 이벤트 필터링
```python
def subscribe_with_filter(self, event_type: Type, handler: Callable, filter_func: Callable):
    """조건부 이벤트 구독"""

    async def filtered_handler(event):
        if filter_func(event):
            await handler(event)

    self.subscribe(event_type, filtered_handler)
```

### 2. 이벤트 변환
```python
def subscribe_with_transform(self, event_type: Type, handler: Callable, transform_func: Callable):
    """이벤트 변환 후 처리"""

    async def transforming_handler(event):
        transformed_event = transform_func(event)
        await handler(transformed_event)

    self.subscribe(event_type, transforming_handler)
```

### 3. 분산 이벤트 버스
```python
class DistributedEventBus(IEventBus):
    """Redis/RabbitMQ 기반 분산 이벤트 버스"""
    # 마이크로서비스 간 이벤트 통신
```

---

**💡 구현 완료 체크리스트**:
- [ ] 모든 인터페이스 메서드 구현
- [ ] 예외 처리 및 로깅 추가
- [ ] 단위 테스트 작성 및 통과
- [ ] 성능 테스트 실행 및 기준 만족
- [ ] 메모리 사용량 모니터링
- [ ] 문서화 완료

**🎯 다음 단계**: Domain Layer와 통합하여 실제 비즈니스 이벤트 처리 구현
