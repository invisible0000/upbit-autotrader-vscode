# Batch DB Manager 기능 명세

## 개요
- **파일 경로**: `smart_data_provider_V4/batch_db_manager.py`
- **코드 라인 수**: 654줄
- **목적**: 대용량 데이터의 배치 처리 최적화 및 DB 성능 극대화
- **핵심 기능**: 비동기 배치 처리, 우선순위 큐, DB 최적화, 메모리 관리

## 주요 컴포넌트

### 1. 데이터 모델

#### BatchOperation (배치 작업)
```python
@dataclass
class BatchOperation:
    operation_id: str
    table_name: str
    operation_type: OperationType
    data_rows: List[Dict[str, Any]]
    priority: Priority = Priority.NORMAL
    estimated_size_mb: float = 0.0
    callback: Optional[Callable] = None
```

**메타데이터 추적**:
- 생성시간, 처리시간, 에러 메시지
- 자동 크기 추정 (JSON 직렬화 기준)

#### BatchConfig (배치 설정)
```python
@dataclass
class BatchConfig:
    insert_batch_size: int = 1000
    update_batch_size: int = 500
    max_memory_mb: float = 100.0
    flush_interval_seconds: float = 10.0
    max_queue_size: int = 10000
```

**성능 튜닝 옵션**:
- WAL 체크포인트 간격: 1시간
- VACUUM 간격: 24시간
- ANALYZE 간격: 1시간
- 동시 처리 배치 수: 최대 3개

### 2. 열거형 정의

#### OperationType (작업 타입)
- `INSERT`: 신규 삽입
- `UPDATE`: 기존 데이터 수정
- `UPSERT`: INSERT OR REPLACE (중복 처리)
- `DELETE`: 데이터 삭제

#### Priority (우선순위)
- `CRITICAL`: 최우선 (실거래봇)
- `HIGH`: 높음 (실시간 모니터링)
- `NORMAL`: 보통 (차트뷰어)
- `LOW`: 낮음 (백테스터)

## 핵심 기능

### 1. BatchDBManager (배치 DB 관리자)
```python
class BatchDBManager:
    def __init__(self, db_connection_factory: Callable[[], sqlite3.Connection]):
        self.db_factory = db_connection_factory
        self.config = BatchConfig()
        self.operation_queues: Dict[Priority, deque] = {...}
```

**초기화 특징**:
- DB 연결 팩토리 패턴 사용
- 우선순위별 큐 시스템 (deque 기반)
- 연결 풀 관리 (최대 10개 연결)
- 통계 추적 시스템

### 2. 비동기 배치 처리

#### 시작/중지 관리
```python
async def start() -> None          # DB 최적화 + 백그라운드 처리 시작
async def stop() -> None           # 남은 작업 처리 후 정리
```

#### 배치 작업 큐잉
```python
async def queue_operation(table_name, operation_type, data_rows, priority, callback) -> str
```

**큐잉 로직**:
1. **큐 크기 확인**: 최대 크기 초과 시 강제 플러시
2. **메모리 체크**: 대용량 작업(100MB+) 즉시 처리
3. **우선순위 배치**: Priority별 별도 큐 관리

#### 캔들 데이터 특화 API
```python
async def insert_candles_batch(symbol, timeframe, candles, priority) -> str
```

**데이터 정규화**:
- 업비트 API 응답 → 표준 캔들 스키마 변환
- 필드 매핑: opening_price → open_price, trade_price → close_price
- 타임스탬프 정규화 및 메타데이터 추가

### 3. 백그라운드 처리 시스템

#### 처리 루프
```python
async def _background_processor() -> None
```

**처리 알고리즘**:
1. **주기적 플러시**: 10초마다 큐 확인
2. **우선순위 처리**: CRITICAL → HIGH → NORMAL → LOW 순서
3. **병렬 처리**: 최대 3개 배치 동시 실행
4. **정기 유지보수**: WAL 체크포인트, ANALYZE, VACUUM

#### 배치 실행 엔진
```python
async def _process_operation(operation: BatchOperation) -> None
```

**실행 특징**:
- 연결 풀에서 DB 연결 획득
- 작업 타입별 최적화된 쿼리 실행
- 처리시간 추적 및 통계 업데이트
- 성공/실패 콜백 실행

### 4. DB 최적화

#### WAL 모드 + PRAGMA 튜닝
```python
async def _optimize_database() -> None
```

**최적화 설정**:
- `journal_mode=WAL`: Write-Ahead Logging
- `cache_size=10000`: 캐시 크기 (40MB)
- `synchronous=NORMAL`: 동기화 모드
- `mmap_size=268435456`: 메모리 맵 크기 (256MB)
- `busy_timeout=30000`: 잠금 대기시간 (30초)

#### 정기 유지보수
```python
async def _periodic_maintenance() -> None
```

**유지보수 작업**:
- **WAL 체크포인트**: 1시간마다 메모리 → 디스크 동기화
- **ANALYZE**: 1시간마다 쿼리 최적화기 통계 갱신
- **VACUUM**: 24시간마다 데이터베이스 압축

### 5. 캔들 데이터 최적화 UPSERT

#### 최적화된 배치 UPSERT
```python
async def _upsert_candles_optimized(conn, candles) -> None
```

**최적화 전략**:
- **배치 크기**: 1000개씩 분할 처리
- **INSERT OR REPLACE**: 중복 키 자동 처리
- **executemany()**: 단일 트랜잭션 내 대량 삽입
- **스키마 최적화**: 고정 필드 순서로 성능 향상

### 6. 연결 풀 관리

#### 간단한 연결 풀
```python
async def _get_connection() -> sqlite3.Connection
async def _return_connection(conn) -> None
async def _cleanup_connection_pool() -> None
```

**풀 특징**:
- 최대 10개 연결 유지
- 사용 후 자동 반환
- 외래키 제약 활성화
- 종료 시 안전한 정리

### 7. 상태 모니터링

#### 큐 상태 조회
```python
async def get_queue_status() -> Dict[str, Any]
```

**모니터링 정보**:
- 우선순위별 큐 크기
- 예상 메모리 사용량
- 처리 통계 (성공/실패/총 처리 시간)
- 마지막 유지보수 시간

## 기술적 특징

### 성능 최적화
- **비동기 처리**: asyncio 기반 논블로킹 I/O
- **배치 처리**: 1000개씩 묶어서 DB 부하 분산
- **우선순위 큐**: 중요한 작업 우선 처리
- **연결 풀**: DB 연결 오버헤드 최소화

### 메모리 관리
- **크기 추정**: JSON 직렬화 기준 자동 계산
- **메모리 임계값**: 100MB 초과 작업 즉시 처리
- **큐 크기 제한**: 10,000개 초과 시 강제 플러시

### 안정성
- **WAL 모드**: 읽기/쓰기 동시성 향상
- **트랜잭션 안전**: 배치 단위 커밋
- **에러 처리**: 개별 작업 실패가 전체에 영향 없음
- **정기 유지보수**: 자동 최적화 및 압축

### 확장성
- **동적 배치 크기**: 테이블별 최적화 가능
- **콜백 시스템**: 작업 완료 시 사용자 정의 로직
- **팩토리 패턴**: 다양한 DB 연결 방식 지원

## 사용 시나리오

### 1. 캔들 데이터 대량 삽입
```python
manager = BatchDBManager(lambda: sqlite3.connect("market_data.sqlite3"))
await manager.start()

# 1000개 캔들 배치 삽입
await manager.insert_candles_batch(
    symbol="KRW-BTC",
    timeframe="1m",
    candles=api_response_candles,
    priority=Priority.HIGH
)
```

### 2. 우선순위 기반 처리
```python
# 실거래봇: 최우선
await manager.queue_operation(
    "orders", OperationType.INSERT, order_data, Priority.CRITICAL
)

# 백테스터: 낮은 우선순위
await manager.queue_operation(
    "backtest_results", OperationType.INSERT, results, Priority.LOW
)
```

### 3. 처리 상태 모니터링
```python
status = await manager.get_queue_status()
print(f"대기 중인 작업: {status['total_queued_operations']}")
print(f"메모리 사용량: {status['estimated_memory_mb']:.1f}MB")
print(f"처리 성공률: {status['stats']['successful_operations']/status['stats']['total_operations']:.1%}")
```

### 4. 콜백을 통한 완료 처리
```python
async def on_batch_complete(operation: BatchOperation):
    if operation.is_processed:
        print(f"배치 완료: {operation.operation_id}, {operation.processing_time:.2f}s")

await manager.queue_operation(
    "candles", OperationType.UPSERT, data, Priority.NORMAL, on_batch_complete
)
```

## 의존성
- **비동기**: asyncio, threading
- **데이터베이스**: sqlite3
- **데이터 구조**: collections.deque
- **로깅**: Infrastructure 컴포넌트 로거
- **아키텍처 계층**: Infrastructure Layer (DDD)

## 성능 특성
- **처리량**: 1000개/배치 × 3개 동시 = 최대 3000개/초
- **메모리 효율**: 100MB 제한으로 OOM 방지
- **응답성**: 우선순위 기반 10초 이내 처리
- **안정성**: WAL 모드로 데이터 무결성 보장

## 핵심 가치
1. **고성능**: 배치 처리 + 비동기 + DB 최적화
2. **안정성**: WAL 모드 + 트랜잭션 안전 + 에러 격리
3. **확장성**: 우선순위 큐 + 동적 설정 + 콜백 시스템
4. **모니터링**: 상세한 통계 + 상태 추적 + 자동 유지보수
