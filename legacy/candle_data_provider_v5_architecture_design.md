# 🏗️ CandleDataProvider v5.0 - Architecture Design & Interface Specification
> 기반 컴포넌트 통합을 위한 상세 아키텍처 설계

## 🎯 Overall Architecture

### Component Integration Map
```
CandleDataProvider v5.0
├── Core Integration Layer
│   ├── OverlapAnalyzer v5.0      ✅ (5-state classification)
│   ├── TimeUtils                 ✅ (timedelta-based, 27 timeframes)
│   ├── CandleModels             ✅ (CandleData + Response models)
│   ├── SqliteCandleRepository   ✅ (10 optimized methods)
│   └── CandleRepositoryInterface ✅ (DDD compliance)
│
├── Service Layer (NEW)
│   ├── Request Validation & Standardization
│   ├── Chunk Management (200 candles max)
│   ├── Cache Layer (60s TTL)
│   └── Response Assembly
│
└── Client Interface
    └── get_candles() - Single Entry Point
```

### Data Flow Architecture
```
┌─ Application Layer Request ─┐
│  get_candles(symbol, timeframe, count?, start_time?, end_time?, inclusive_start?)
└─────────────┬─────────────────┘
              │
┌─────────────▼─────────────────┐
│    CandleDataProvider v5.0   │
│  ┌─────────────────────────┐  │
│  │ 1. Request Validation   │  │ ◄── TimeUtils (시간 계산)
│  └─────────────────────────┘  │
│  ┌─────────────────────────┐  │
│  │ 2. Cache Check (60s)    │  │ ◄── CandleCache (메모리)
│  └─────────────────────────┘  │
│  ┌─────────────────────────┐  │
│  │ 3. Chunk Split (200개)  │  │ ◄── TimeUtils (범위 계산)
│  └─────────────────────────┘  │
│  ┌─────────────────────────┐  │
│  │ 4. Sequential Collection │  │
│  │   ├─ OverlapAnalyzer    │  │ ◄── 5-state classification
│  │   ├─ DB Query           │  │ ◄── SqliteCandleRepository
│  │   ├─ API Request        │  │ ◄── UpbitPublicClient
│  │   └─ Data Storage       │  │ ◄── Repository.save_chunk()
│  └─────────────────────────┘  │
│  ┌─────────────────────────┐  │
│  │ 5. Response Assembly    │  │ ◄── CandleDataResponse
│  └─────────────────────────┘  │
└─────────────┬─────────────────┘
              │
┌─────────────▼─────────────────┐
│     CandleDataResponse        │
│  ┌─────────────────────────┐  │
│  │ success: bool           │  │
│  │ candles: List[CandleData│  │
│  │ total_count: int        │  │
│  │ data_source: str        │  │
│  │ response_time_ms: float │  │
│  │ error_message?: str     │  │
│  └─────────────────────────┘  │
└───────────────────────────────┘
```

---

## 🔧 Detailed Component Integration

### 1. OverlapAnalyzer v5.0 Integration

#### Integration Point
```python
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import OverlapRequest, OverlapResult, OverlapStatus

class CandleDataProvider:
    def __init__(self, ...):
        self.overlap_analyzer = OverlapAnalyzer(
            repository=self.repository,
            time_utils=self.time_utils,
            enable_validation=True  # 개발 초기는 True, 안정화 후 False
        )
```

#### Usage Pattern
```python
async def _analyze_chunk_overlap(self, chunk: CandleChunk) -> OverlapResult:
    """청크별 겹침 분석 - OverlapAnalyzer v5.0 활용"""
    request = OverlapRequest(
        symbol=chunk.symbol,
        timeframe=chunk.timeframe,
        target_start=chunk.start_time,
        target_end=self._calculate_chunk_end_time(chunk),
        target_count=chunk.count
    )

    result = await self.overlap_analyzer.analyze_overlap(request)

    # 5-state 결과에 따른 처리 분기
    if result.status == OverlapStatus.NO_OVERLAP:
        return await self._collect_full_api_chunk(chunk)
    elif result.status == OverlapStatus.COMPLETE_OVERLAP:
        return await self._collect_full_db_chunk(chunk)
    elif result.status == OverlapStatus.PARTIAL_START:
        return await self._collect_mixed_from_start(chunk, result.partial_end)
    elif result.status in [OverlapStatus.PARTIAL_MIDDLE_FRAGMENT, OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS]:
        return await self._collect_mixed_middle(chunk, result)
    else:
        # Fallback: 전체 API 요청
        return await self._collect_full_api_chunk(chunk)
```

### 2. TimeUtils Integration

#### Integration Point
```python
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

class CandleDataProvider:
    def __init__(self, ...):
        self.time_utils = TimeUtils
```

#### Usage Patterns
```python
def _validate_and_standardize_request(self, ...) -> Tuple[datetime, datetime, int]:
    """요청 검증 및 표준화 - TimeUtils 활용"""

    # 1. 타임프레임 검증
    try:
        timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
    except ValueError as e:
        raise ValidationError(f"지원하지 않는 타임프레임: {timeframe}")

    # 2. 시간 범위 계산
    if start_time and end_time:
        expected_count = self.time_utils.calculate_expected_count(start_time, end_time, timeframe)
        return start_time, end_time, expected_count
    elif start_time and count:
        delta = self.time_utils.get_timeframe_delta(timeframe)
        end_time = start_time + (delta * (count - 1))
        return start_time, end_time, count
    elif count:
        # 현재 시간부터 역순
        now = datetime.now(timezone.utc)
        aligned_now = self.time_utils._align_to_candle_boundary(now, timeframe)
        start_time = self.time_utils.get_aligned_time_by_ticks(aligned_now, timeframe, -(count-1))
        return start_time, aligned_now, count
    else:
        raise ValidationError("count, start_time+count, 또는 start_time+end_time 중 하나는 필수")

def _split_into_chunks(self, symbol: str, timeframe: str, count: int,
                      start_time: datetime, end_time: datetime) -> List[CandleChunk]:
    """200개 청크 분할 - TimeUtils 활용"""
    chunks = []
    chunk_size = 200

    # TimeUtils로 시간 시퀀스 생성
    time_sequence = self.time_utils.get_time_range(start_time, end_time, timeframe)

    for i in range(0, len(time_sequence), chunk_size):
        chunk_start = time_sequence[i]
        chunk_times = time_sequence[i:i+chunk_size]
        chunk_count = len(chunk_times)

        chunk = CandleChunk(
            symbol=symbol,
            timeframe=timeframe,
            start_time=chunk_start,
            count=chunk_count,
            chunk_index=len(chunks)
        )
        chunks.append(chunk)

    return chunks
```

### 3. CandleModels Integration

#### Import Strategy
```python
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import (
    CandleData, CandleDataResponse, CandleChunk, CollectionResult,
    OverlapRequest, OverlapResult, OverlapStatus,
    create_success_response, create_error_response
)
```

#### Model Usage Patterns
```python
async def _collect_api_chunk(self, chunk: CandleChunk) -> CollectionResult:
    """API에서 청크 수집 - CandleModels 활용"""
    start_time = time.perf_counter()

    try:
        # API 호출
        api_data = await self.upbit_client.get_candles(
            market=chunk.symbol,
            timeframe=chunk.timeframe,
            count=chunk.count,
            to=chunk.start_time.isoformat()
        )

        # CandleData 모델로 변환
        candles = [
            CandleData.from_upbit_api(data, chunk.timeframe)
            for data in api_data
        ]

        collection_time = (time.perf_counter() - start_time) * 1000

        return CollectionResult(
            chunk=chunk,
            collected_candles=candles,
            data_source="api",
            api_requests_made=1,
            collection_time_ms=collection_time
        )

    except Exception as e:
        logger.error(f"API 청크 수집 실패: {e}")
        return CollectionResult(
            chunk=chunk,
            collected_candles=[],
            data_source="error",
            api_requests_made=0,
            collection_time_ms=(time.perf_counter() - start_time) * 1000
        )

async def _assemble_final_response(self, results: List[CollectionResult],
                                 request_start_time: float) -> CandleDataResponse:
    """최종 응답 조합 - CandleDataResponse 활용"""

    # 모든 결과 조합
    all_candles = []
    data_sources = []
    total_api_requests = 0

    for result in results:
        all_candles.extend(result.collected_candles)
        data_sources.append(result.data_source)
        total_api_requests += result.api_requests_made

    # 중복 제거 및 정렬 (CandleData 모델의 정렬 키 활용)
    unique_candles = {
        f"{c.symbol}_{c.timeframe}_{c.candle_date_time_utc}": c
        for c in all_candles
    }
    sorted_candles = sorted(
        unique_candles.values(),
        key=lambda c: c.candle_date_time_utc
    )

    # 응답 시간 계산
    response_time_ms = (time.perf_counter() - request_start_time) * 1000

    # 데이터 소스 결정
    unique_sources = set(data_sources)
    if len(unique_sources) > 1:
        data_source = "mixed"
    elif "db" in unique_sources:
        data_source = "db"
    elif "api" in unique_sources:
        data_source = "api"
    else:
        data_source = "cache"

    # CandleDataResponse 생성
    return create_success_response(
        candles=sorted_candles,
        data_source=data_source,
        response_time_ms=response_time_ms
    )
```

### 4. SqliteCandleRepository Integration

#### Repository Pattern Usage
```python
from upbit_auto_trading.infrastructure.repositories.sqlite_candle_repository import SqliteCandleRepository

class CandleDataProvider:
    def __init__(self, db_manager: DatabaseManager, ...):
        self.repository = SqliteCandleRepository(db_manager)

async def _collect_db_chunk(self, chunk: CandleChunk) -> CollectionResult:
    """DB에서 청크 수집 - Repository 10개 메서드 활용"""
    start_time = time.perf_counter()

    try:
        # 테이블 존재 확인
        if not await self.repository.table_exists(chunk.symbol, chunk.timeframe):
            logger.debug(f"테이블 없음: {chunk.symbol}_{chunk.timeframe}")
            return CollectionResult(
                chunk=chunk,
                collected_candles=[],
                data_source="db",
                api_requests_made=0,
                collection_time_ms=(time.perf_counter() - start_time) * 1000
            )

        # 범위 데이터 조회 (새로운 CandleData 모델 반환)
        chunk_end_time = self._calculate_chunk_end_time(chunk)
        candles = await self.repository.get_candles_by_range(
            chunk.symbol, chunk.timeframe, chunk.start_time, chunk_end_time
        )

        collection_time = (time.perf_counter() - start_time) * 1000

        return CollectionResult(
            chunk=chunk,
            collected_candles=candles,
            data_source="db",
            api_requests_made=0,
            collection_time_ms=collection_time
        )

    except Exception as e:
        logger.error(f"DB 청크 수집 실패: {e}")
        return CollectionResult(
            chunk=chunk,
            collected_candles=[],
            data_source="error",
            api_requests_made=0,
            collection_time_ms=(time.perf_counter() - start_time) * 1000
        )

async def _save_collected_candles(self, symbol: str, timeframe: str,
                                candles: List[CandleData]) -> int:
    """수집된 캔들 저장 - Repository save_chunk 활용"""
    if not candles:
        return 0

    try:
        # 테이블 생성 (필요시)
        await self.repository.ensure_table_exists(symbol, timeframe)

        # 배치 저장 (INSERT OR IGNORE 방식)
        saved_count = await self.repository.save_candle_chunk(symbol, timeframe, candles)

        logger.debug(f"캔들 저장 완료: {saved_count}/{len(candles)}개 (중복 제외)")
        return saved_count

    except Exception as e:
        logger.error(f"캔들 저장 실패: {e}")
        return 0
```

### 5. CandleRepositoryInterface Compliance

#### Interface Compliance Check
```python
from upbit_auto_trading.domain.repositories.candle_repository_interface import CandleRepositoryInterface

# SqliteCandleRepository가 모든 abstract method를 구현했는지 확인
class CandleDataProvider:
    def __init__(self, db_manager: DatabaseManager, ...):
        # 타입 체크로 interface 준수 확인
        self.repository: CandleRepositoryInterface = SqliteCandleRepository(db_manager)

        # 런타임에서 10개 메서드 존재 확인 (개발 단계에서만)
        required_methods = [
            'get_data_ranges', 'has_any_data_in_range', 'is_range_complete',
            'find_last_continuous_time', 'is_continue_till_end', 'has_data_at_time',
            'find_data_start_in_range', 'ensure_table_exists', 'save_candle_chunk',
            'get_candles_by_range'
        ]

        for method_name in required_methods:
            if not hasattr(self.repository, method_name):
                raise RuntimeError(f"Repository에서 {method_name} 메서드 누락")
```

---

## 🎛️ Public Interface Specification

### Main Entry Point
```python
async def get_candles(
    self,
    symbol: str,                    # 거래 심볼 (예: 'KRW-BTC')
    timeframe: str,                 # 타임프레임 ('1s', '1m', '5m', ..., '1y')
    count: Optional[int] = None,    # 캔들 개수 (1~10000)
    start_time: Optional[datetime] = None,  # 시작 시간 (UTC)
    end_time: Optional[datetime] = None,    # 종료 시간 (UTC)
    inclusive_start: bool = True    # start_time 포함 여부
) -> CandleDataResponse:
    """
    캔들 데이터 조회 - 5가지 파라미터 조합 지원

    Parameter Combinations:
    1. count만: 최신 데이터부터 역순으로 count개
    2. start_time + count: start_time부터 count개 (inclusive_start 적용)
    3. start_time + end_time: 구간 지정 (inclusive_start 적용)
    4. count + end_time: end_time까지 역순으로 count개
    5. 모든 파라미터: start_time~end_time 범위에서 최대 count개

    Performance:
    - 100개 캔들: 평균 50ms 이하
    - 1000개 캔들: 평균 500ms 이하
    - 캐시 히트시: 평균 10ms 이하

    Error Handling:
    - 미래 시간 요청: ValidationError
    - 지원하지 않는 타임프레임: ValidationError
    - Rate limit 초과: 자동 백오프 재시도
    - 네트워크 오류: 최대 3회 재시도

    Returns:
        CandleDataResponse:
            - success: 성공 여부
            - candles: CandleData 리스트 (시간순 정렬)
            - total_count: 실제 반환된 캔들 수
            - data_source: "cache"/"db"/"api"/"mixed"
            - response_time_ms: 응답 시간
            - error_message: 에러 메시지 (실패시)
    """
```

### Convenience Methods
```python
async def get_latest_candles(
    self,
    symbol: str,
    timeframe: str,
    count: int = 200
) -> CandleDataResponse:
    """최신 캔들 조회 (get_candles의 간편 버전)"""
    return await self.get_candles(symbol, timeframe, count=count)

def get_stats(self) -> dict:
    """서비스 통계 조회

    Returns:
        {
            'total_requests': int,
            'cache_hits': int,
            'cache_misses': int,
            'api_requests': int,
            'average_response_time_ms': float,
            'supported_timeframes': List[str],
            'active_cache_entries': int
        }
    """

def get_supported_timeframes(self) -> List[str]:
    """지원하는 타임프레임 목록 반환"""
    return ['1s', '1m', '3m', '5m', '10m', '15m', '30m', '60m', '240m',
            '1h', '4h', '1d', '1w', '1M', '1y']

def get_cache_stats(self) -> dict:
    """캐시 통계 조회

    Returns:
        {
            'total_entries': int,
            'memory_usage_mb': float,
            'hit_rate': float,
            'average_ttl_remaining': float
        }
    """

# Factory Functions
def create_candle_data_provider(
    db_manager: Optional[DatabaseManager] = None,
    upbit_client: Optional[UpbitPublicClient] = None
) -> CandleDataProvider:
    """CandleDataProvider 팩토리 함수 (동기 버전)"""

async def create_candle_data_provider_async(
    db_manager: Optional[DatabaseManager] = None,
    upbit_client: Optional[UpbitPublicClient] = None
) -> CandleDataProvider:
    """CandleDataProvider 팩토리 함수 (비동기 버전, 초기화 포함)"""
```

---

## ⚡ Performance Optimization Strategy

### 1. Caching Layer
```python
class CandleCache:
    """60초 TTL 메모리 캐시"""
    def __init__(self, max_memory_mb: int = 100):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_memory_bytes = max_memory_mb * 1024 * 1024

    async def get(self, key: CacheKey) -> Optional[List[CandleData]]:
        """캐시에서 데이터 조회"""

    async def set(self, key: CacheKey, candles: List[CandleData], ttl: int = 60):
        """캐시에 데이터 저장"""

    def cleanup_expired(self):
        """만료된 엔트리 정리"""
```

### 2. Chunk Processing Optimization
```python
async def _collect_chunks_sequentially(
    self, chunks: List[CandleChunk], target_end_time: datetime
) -> Tuple[List[CandleData], List[str]]:
    """청크 순차 수집 - 조기 중단 최적화"""

    all_candles = []
    data_sources = []

    for chunk in chunks:
        # target_end_time 도달시 조기 중단
        if self._is_collection_complete(chunk, target_end_time):
            logger.debug(f"target_end_time 도달, 수집 중단: {chunk.chunk_index+1}/{len(chunks)}")
            break

        # 청크별 최적화된 수집
        result = await self._collect_chunk_optimized(chunk)
        all_candles.extend(result.collected_candles)
        data_sources.append(result.data_source)

        # 통계 업데이트
        self._update_chunk_stats(result)

    return all_candles, data_sources
```

### 3. Memory Management
```python
def _monitor_memory_usage(self):
    """메모리 사용량 모니터링 및 정리"""
    if self.cache.get_memory_usage_mb() > 80:  # 80MB 초과시
        self.cache.cleanup_expired()
        self.cache.evict_lru()  # LRU 정책으로 추가 정리
```

---

## 🔍 Error Handling & Recovery

### Error Hierarchy
```python
class CandleDataProviderError(Exception):
    """기본 에러 클래스"""

class ValidationError(CandleDataProviderError):
    """파라미터 검증 에러"""

class RateLimitError(CandleDataProviderError):
    """API Rate Limit 에러"""

class NetworkError(CandleDataProviderError):
    """네트워크 연결 에러"""

class DataIntegrityError(CandleDataProviderError):
    """데이터 무결성 에러"""
```

### Recovery Strategies
```python
async def _handle_api_error(self, error: Exception, chunk: CandleChunk,
                           retry_count: int = 0) -> CollectionResult:
    """API 에러 처리 및 복구"""

    if isinstance(error, RateLimitError) and retry_count < 3:
        # 지수 백오프 재시도
        wait_time = 2 ** retry_count
        await asyncio.sleep(wait_time)
        return await self._collect_api_chunk(chunk)

    elif isinstance(error, NetworkError) and retry_count < 3:
        # 선형 백오프 재시도
        await asyncio.sleep(1 * (retry_count + 1))
        return await self._collect_api_chunk(chunk)

    else:
        # 복구 불가능 - DB 폴백 시도
        logger.warning(f"API 복구 실패, DB 폴백 시도: {error}")
        return await self._collect_db_chunk(chunk)
```

---

## 📊 Monitoring & Observability

### Metrics Collection
```python
def _update_metrics(self, operation: str, duration_ms: float, success: bool):
    """메트릭 업데이트"""
    self.stats[f'{operation}_count'] += 1
    self.stats[f'{operation}_total_time_ms'] += duration_ms

    if success:
        self.stats[f'{operation}_success_count'] += 1
    else:
        self.stats[f'{operation}_error_count'] += 1

def get_health_status(self) -> dict:
    """헬스 체크 정보"""
    return {
        'status': 'healthy' if self._is_healthy() else 'unhealthy',
        'cache_status': self.cache.get_health_status(),
        'repository_status': self.repository.get_health_status(),
        'api_client_status': self.upbit_client.get_health_status(),
        'last_successful_request': self.stats.get('last_successful_request'),
        'error_rate_last_hour': self._calculate_error_rate()
    }
```

이제 이 아키텍처 설계를 바탕으로 실제 구현을 진행할 준비가 완료되었습니다. 승인해주시면 다음 단계인 API 명세서 작성으로 넘어가겠습니다.
