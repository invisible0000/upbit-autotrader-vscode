# 캔들 데이터 제공자 v2.0 상세 계획서

## 📋 개요 및 목적

### 기존 문제점 분석
- v1의 복잡한 파라미터 조합 처리로 인한 예측 불가능한 동작
- 겹침 분석 로직의 불완전성으로 API 요청 최적화 실패
- 청크 처리 중 시간 정렬 불일치 문제
- 캐시와 DB 연동의 비효율성

### v2.0 개선 목표
- **단순성**: 파라미터 조합을 5가지로 명확히 제한하고 각각의 동작을 명확히 정의
- **예측성**: 모든 시간 계산과 데이터 처리 로직을 문서화하고 검증 가능하게 구성
- **효율성**: 겹침 분석을 통한 최적화된 API/DB 혼합 전략
- **안정성**: 각 컴포넌트별 명확한 책임 분리와 에러 처리

## 🏗️ 아키텍처 설계

### 컴포넌트 구조
```
CandleDataProviderV2
├── RequestValidator        # 요청 검증 및 표준화
├── TimeCalculator         # 시간 계산 엔진
├── OverlapAnalyzerV2      # 겹침 분석 엔진 (개선)
├── ChunkProcessor         # 청크 분할 및 처리
├── DataCollector          # DB/API 혼합 수집
├── CacheManager           # 캐시 관리
└── ResponseAssembler      # 응답 조합
```

### DDD 계층 준수
- **Infrastructure Service**: 외부 시스템(DB, API, Cache)과의 통합
- **Domain 의존성 없음**: 순수 데이터 제공 서비스
- **Repository 패턴**: DB 접근을 Repository 인터페이스로 추상화

## 📊 파라미터 조합 및 처리 로직

### 지원하는 5가지 파라미터 케이스

#### 1. count만 제공 (최근 데이터)
```python
get_candles(symbol="KRW-BTC", timeframe="1m", count=200)
```
- **동작**: 현재 시간부터 역순으로 count개
- **계산**: `end_time = align_to_boundary(now)`, `start_time = end_time - (count-1) * dt`
- **검증**: count <= 2000 (시스템 부하 고려)

#### 2. start_time + count (시작점 기준)
```python
get_candles(symbol="KRW-BTC", timeframe="1m",
           start_time=datetime(...), count=600)
```
- **동작**: 지정된 시작점부터 count개
- **계산**: `end_time = start_time + (count-1) * dt`
- **inclusive_start**: True시 start_time을 포함하도록 조정

#### 3. start_time + end_time (시간 범위)
```python
get_candles(symbol="KRW-BTC", timeframe="1m",
           start_time=datetime(...), end_time=datetime(...))
```
- **동작**: 시간 범위로 count 자동 계산
- **계산**: `count = (end_time - start_time) / dt + 1`
- **검증**: start_time < end_time

#### 4. end_time만 제공 (특정 시점까지)
```python
get_candles(symbol="KRW-BTC", timeframe="1m",
           end_time=datetime(...))
```
- **동작**: 현재시간부터 지정된 end_time까지
- **계산**: `count = (now - end_time) / dt + 1`, `start_time = end_time`
- **기본 count**: 200개 (제한)

#### 5. 기본값 (파라미터 없음)
```python
get_candles(symbol="KRW-BTC", timeframe="1m")
```
- **동작**: 최근 200개 (케이스 1과 동일)
- **계산**: count=200으로 처리

### 금지된 조합
- **count + end_time**: 상호 배타적이므로 ValidationError

## ⏰ 시간 계산 및 정렬 시스템

### 시간 변수 체계

#### 입력 시간 (사용자 제공)
- `request_start_time`: 사용자가 요청한 원래 시작 시간
- `request_end_time`: 사용자가 요청한 원래 종료 시간
- `request_count`: 사용자가 요청한 캔들 개수

#### 표준화된 시간 (내부 계산)
- `target_start_time`: 계산된 목표 시작 시간 (timeframe 경계 정렬)
- `target_end_time`: 계산된 목표 종료 시간 (timeframe 경계 정렬)
- `target_count`: 계산된 목표 캔들 개수

#### API 요청용 시간 (업비트 호환)
- `api_start_time`: API 요청에 사용할 시작 시간 (inclusive_start 조정 적용)
- `api_end_time`: API 요청에 사용할 종료 시간

### 시간 정렬 규칙

#### 캔들 경계 정렬 (align_to_candle_boundary)
```python
def align_to_candle_boundary(dt: datetime, timeframe: str) -> datetime:
    """
    timeframe에 맞는 캔들 경계로 정렬
    - 1m: 초를 0으로 설정
    - 5m: 분을 5의 배수로 설정
    - 1h: 분과 초를 0으로 설정
    - 1d: 시분초를 0으로 설정 (UTC 00:00)
    """
```

#### inclusive_start 처리 (업비트 API 호환)
```python
def adjust_for_inclusive_start(start_time: datetime, timeframe: str,
                              inclusive: bool) -> datetime:
    """
    업비트 API는 start_time을 배제하므로 포함하려면 이전 캔들 시간으로 조정
    - inclusive=True: start_time - dt (이전 캔들 시간)
    - inclusive=False: start_time 그대로 사용
    """
```

### 시간 계산 흐름
1. **파라미터 파싱**: 사용자 입력 → 표준화된 target_start, target_end, target_count
2. **경계 정렬**: timeframe에 맞는 캔들 경계로 정렬
3. **미래 시간 검증**: target_end <= now 확인
4. **API 조정**: inclusive_start 적용하여 api_start_time 계산
5. **청크 분할**: 200개 단위로 분할하여 처리

## 🔍 겹침 분석 시스템 v2.0

### 겹침 상태 정의

#### 1. 겹침 없음 (NO_OVERLAP)
```
DB: |------|  (데이터 없음)
요청: [target_start ===== target_end]
```
- **조건**: `has_any_data_in_range() = false`
- **처리**: 전체 구간 API 요청 → DB 저장 → 제공

#### 2. 완전 겹침 (COMPLETE_OVERLAP)
```
DB: |111111111111111111111|
요청: [target_start === target_end]
```
- **조건**: `is_range_complete() = true` (요청 개수와 DB 데이터 개수 일치)
- **처리**: DB에서만 조회 → 제공 (API 요청 없음)

#### 3. 부분 겹침 (PARTIAL_OVERLAP)
```
DB: |11111-----|  또는  |-----11111|  또는  |--111--111--|
요청: [target_start =========== target_end]
```
- **조건**: `has_any_data_in_range() = true` but `is_range_complete() = false`
- **세부 분류**:
  - **시작 겹침 (START_OVERLAP)**: target_start에 데이터 존재
  - **중간 겹침 (MIDDLE_OVERLAP)**: target_start에 데이터 없음, 중간에 존재

### 겹침 분석 알고리즘

#### 입력 파라미터
- `symbol`: 거래 심볼 (예: "KRW-BTC")
- `timeframe`: 타임프레임 (예: "1m", "5m")
- `target_start`: 요청 시작 시간
- `target_end`: 요청 종료 시간
- `target_count`: 요청 캔들 개수

#### 출력 결과
```python
@dataclass
class OverlapResult:
    status: OverlapStatus                    # 겹침 상태
    existing_start: Optional[datetime]       # 기존 데이터 시작점
    existing_end: Optional[datetime]         # 기존 데이터 종료점
    missing_ranges: List[Tuple[datetime, datetime]]  # 부족한 구간들
    api_request_needed: bool                 # API 요청 필요 여부
    optimization_info: dict                 # 최적화 정보 (통계용)
```

#### 단계별 분석 로직

##### 1단계: 기본 존재성 확인
```python
async def has_any_data_in_range(symbol: str, timeframe: str,
                               start: datetime, end: datetime) -> bool:
    """
    목표 범위 내 데이터 존재 확인 (LIMIT 1 최적화)
    """
    query = """
    SELECT 1 FROM candles
    WHERE symbol = ? AND timeframe = ?
    AND candle_time >= ? AND candle_time <= ?
    LIMIT 1
    """
```

##### 2단계: 완전성 검증
```python
async def is_range_complete(symbol: str, timeframe: str,
                          start: datetime, end: datetime,
                          expected_count: int) -> bool:
    """
    요청 범위의 완전성 확인 (COUNT 최적화)
    """
    query = """
    SELECT COUNT(*) FROM candles
    WHERE symbol = ? AND timeframe = ?
    AND candle_time >= ? AND candle_time <= ?
    """
    actual_count = await repository.execute_scalar(query, params)
    return actual_count >= expected_count
```

##### 3단계: 연속성 분석
```python
async def find_continuous_ranges(symbol: str, timeframe: str,
                                start: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
    """
    연속된 데이터 구간들 찾기 (Gap 분석)
    """
    query = """
    SELECT candle_time,
           LAG(candle_time) OVER (ORDER BY candle_time) as prev_time
    FROM candles
    WHERE symbol = ? AND timeframe = ?
    AND candle_time >= ? AND candle_time <= ?
    ORDER BY candle_time
    """
    # Gap 감지하여 연속 구간들로 분할
```

### 겹침별 처리 전략

#### 시작 겹침 (START_OVERLAP) 처리
```
DB: |11111-----|
요청: [start ===== end]
```
1. 연결된 데이터의 끝점 탐색: `find_last_continuous_time(start)`
2. 부족한 구간 계산: `[continuous_end + dt, target_end]`
3. **최적화**: 기존 데이터는 DB 조회, 부족 구간만 API 요청

#### 중간 겹침 (MIDDLE_OVERLAP) 처리
```
DB: |--111--111--|
요청: [start ===== end]
```
1. 첫 번째 데이터 구간 탐색: `find_first_data_time(start, end)`
2. 각 Gap 구간들 식별
3. **최적화 판단**:
   - Gap이 2개 이상: 전체 API 요청 (복잡도 증가 방지)
   - Gap이 1개: 해당 구간만 API 요청

#### 말단 겹침 (END_OVERLAP) 처리
```
DB: |-----11111|
요청: [start === end]
```
1. 첫 번째 데이터 시작점 탐색: `find_first_continuous_time(end)`
2. 부족한 구간 계산: `[target_start, first_data_start - dt]`
3. **최적화**: 부족 구간만 API 요청, 기존 데이터는 DB 조회

## 📦 청크 분할 및 처리 시스템

### 청크 분할 규칙

#### 기본 원칙
- **청크 크기**: 200개 (업비트 API 최대 제한)
- **최대 청크 수**: 2000개 (시스템 부하 고려, 총 400만 캔들)
- **분할 방향**: 최신 시간(end_time)부터 과거 방향으로 순차 분할

#### 청크 모델
```python
@dataclass
class CandleChunk:
    symbol: str
    timeframe: str
    start_time: datetime          # 청크 시작 시간
    end_time: datetime            # 청크 종료 시간
    expected_count: int           # 예상 캔들 개수 (≤ 200)
    chunk_index: int              # 청크 순서 (0부터 시작)
    overlap_result: Optional[OverlapResult] = None  # 겹침 분석 결과
```

#### 분할 알고리즘
```python
def split_into_chunks(symbol: str, timeframe: str,
                     total_count: int, start_time: datetime,
                     end_time: datetime) -> List[CandleChunk]:
    """
    대량 요청을 200개 청크로 분할

    처리 방향: end_time → start_time (최신부터 과거로)
    """
    chunks = []
    dt = get_timeframe_delta(timeframe)
    current_end = end_time
    remaining_count = total_count
    chunk_index = 0

    while remaining_count > 0 and chunk_index < 2000:
        # 현재 청크 크기 결정 (최대 200개)
        chunk_size = min(remaining_count, 200)
        chunk_start = current_end - timedelta(seconds=dt.total_seconds() * (chunk_size - 1))

        # 시작 경계 검증
        if chunk_start < start_time:
            chunk_start = start_time
            chunk_size = int((current_end - chunk_start).total_seconds() / dt.total_seconds()) + 1

        # 청크 생성
        chunk = CandleChunk(
            symbol=symbol,
            timeframe=timeframe,
            start_time=chunk_start,
            end_time=current_end,
            expected_count=chunk_size,
            chunk_index=chunk_index
        )
        chunks.append(chunk)

        # 다음 청크 준비
        current_end = chunk_start - dt
        remaining_count -= chunk_size
        chunk_index += 1

        # 종료 조건
        if current_end < start_time:
            break

    return chunks
```

### 청크별 처리 전략

#### 순차 처리 (Sequential Processing)
```python
async def process_chunks_sequentially(chunks: List[CandleChunk],
                                    target_end_time: datetime) -> CollectionResult:
    """
    청크들을 순차적으로 처리 (최신 → 과거)

    중요: target_end_time 도달 시 자동 중단
    """
    collected_candles = []
    data_sources = []

    for chunk in chunks:
        # target_end_time 도달 확인
        if chunk.end_time < target_end_time:
            logger.info(f"target_end_time 도달, 처리 중단: {chunk.end_time} < {target_end_time}")
            break

        # 겹침 분석
        chunk.overlap_result = await overlap_analyzer.analyze_overlap(
            chunk.symbol, chunk.timeframe, chunk.start_time, chunk.expected_count
        )

        # 겹침 상태별 처리
        chunk_data, source = await process_single_chunk(chunk)

        collected_candles.extend(chunk_data)
        data_sources.append(source)

        # Rate limiting (API 요청시만)
        if source in ["api", "mixed"]:
            await asyncio.sleep(0.1)  # 100ms 지연

    return CollectionResult(collected_candles, data_sources)
```

#### 단일 청크 처리
```python
async def process_single_chunk(chunk: CandleChunk) -> Tuple[List[CandleData], str]:
    """
    단일 청크의 겹침 상태별 처리
    """
    overlap = chunk.overlap_result

    if overlap.status == OverlapStatus.NO_OVERLAP:
        # 전체 API 요청
        candles = await api_client.get_candles(
            chunk.symbol, chunk.timeframe,
            count=chunk.expected_count,
            to=chunk.end_time
        )
        await repository.bulk_insert(candles)
        return candles, "api"

    elif overlap.status == OverlapStatus.COMPLETE_OVERLAP:
        # DB 전용 조회
        candles = await repository.get_candles_range(
            chunk.symbol, chunk.timeframe,
            chunk.start_time, chunk.end_time
        )
        return candles, "db"

    elif overlap.status == OverlapStatus.PARTIAL_OVERLAP:
        # 혼합 처리
        return await process_partial_overlap(chunk)
```

#### 부분 겹침 혼합 처리
```python
async def process_partial_overlap(chunk: CandleChunk) -> Tuple[List[CandleData], str]:
    """
    부분 겹침의 최적화된 혼합 처리
    """
    overlap = chunk.overlap_result
    all_candles = []

    # 기존 데이터 조회 (DB)
    if overlap.existing_start and overlap.existing_end:
        existing_data = await repository.get_candles_range(
            chunk.symbol, chunk.timeframe,
            overlap.existing_start, overlap.existing_end
        )
        all_candles.extend(existing_data)

    # 부족한 구간들 API 요청
    for missing_start, missing_end in overlap.missing_ranges:
        missing_count = calculate_count_between_times(missing_start, missing_end, chunk.timeframe)

        # 200개 초과시 추가 분할
        if missing_count <= 200:
            new_data = await api_client.get_candles(
                chunk.symbol, chunk.timeframe,
                count=missing_count, to=missing_end
            )
            await repository.bulk_insert(new_data)
            all_candles.extend(new_data)
        else:
            # 200개 초과 시 재귀적 청크 분할
            sub_chunks = split_missing_range(missing_start, missing_end, chunk)
            for sub_chunk in sub_chunks:
                sub_data, _ = await process_single_chunk(sub_chunk)
                all_candles.extend(sub_data)

    # 시간순 정렬
    all_candles.sort(key=lambda x: x.candle_date_time_utc)
    return all_candles, "mixed"
```

## 💾 데이터 수집 및 저장 시스템

### DB 상태별 수집 전략

#### Case 1: 겹침 없음 (Cold Start)
```
DB: |------|  (빈 상태)
수집: [====API 요청====] → DB 저장 → 캐시 저장 → 반환
```

#### Case 2: 시작 겹침 (Warm Start)
```
DB: |11111-----|
수집: [DB조회] + [--API요청--] → 병합 → 캐시 저장 → 반환
```

#### Case 3: 완전 겹침 (Hot Cache)
```
DB: |111111111111|
수집: [====DB 조회====] → 캐시 저장 → 반환 (API 요청 없음)
```

### API 요청 최적화

#### Rate Limiting 전략
```python
class APIRateLimiter:
    def __init__(self):
        self.requests_per_second = 10      # 업비트 제한
        self.last_request_time = 0
        self.request_interval = 0.1        # 100ms 간격

    async def wait_if_needed(self):
        """요청 간격 제어"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.request_interval:
            await asyncio.sleep(self.request_interval - elapsed)

        self.last_request_time = time.time()
```

#### 배치 요청 전략
```python
async def batch_api_requests(missing_ranges: List[Tuple[datetime, datetime]],
                           symbol: str, timeframe: str) -> List[CandleData]:
    """
    여러 부족 구간을 효율적으로 배치 요청
    """
    all_data = []

    for start, end in missing_ranges:
        count = calculate_count_between_times(start, end, timeframe)

        # 200개 이하: 단일 요청
        if count <= 200:
            data = await api_client.get_candles(symbol, timeframe, count=count, to=end)
            all_data.extend(data)
            await rate_limiter.wait_if_needed()

        # 200개 초과: 청크 분할
        else:
            sub_chunks = split_range_into_chunks(start, end, timeframe)
            for chunk_start, chunk_end in sub_chunks:
                chunk_count = calculate_count_between_times(chunk_start, chunk_end, timeframe)
                data = await api_client.get_candles(symbol, timeframe, count=chunk_count, to=chunk_end)
                all_data.extend(data)
                await rate_limiter.wait_if_needed()

    return all_data
```

### DB 저장 최적화

#### 벌크 삽입 전략
```python
async def bulk_insert_optimized(candles: List[CandleData]) -> bool:
    """
    대량 데이터 효율적 삽입 (중복 방지)
    """
    if not candles:
        return True

    # 배치 크기 제한 (메모리 고려)
    batch_size = 1000
    success_count = 0

    for i in range(0, len(candles), batch_size):
        batch = candles[i:i + batch_size]

        try:
            # UPSERT 쿼리로 중복 방지
            query = """
            INSERT OR REPLACE INTO candles
            (symbol, timeframe, candle_time, open_price, high_price, low_price, close_price, volume, ...)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ...)
            """

            values = [candle.to_db_tuple() for candle in batch]
            await repository.execute_many(query, values)
            success_count += len(batch)

        except Exception as e:
            logger.error(f"배치 {i//batch_size + 1} 저장 실패: {e}")

            # 개별 저장 시도 (부분 실패 허용)
            for candle in batch:
                try:
                    await repository.insert_single(candle)
                    success_count += 1
                except Exception as single_error:
                    logger.warning(f"개별 저장 실패: {candle.symbol} {candle.candle_date_time_utc}, {single_error}")

    return success_count == len(candles)
```

## 🚀 캐시 관리 시스템

### 캐시 구조
```python
@dataclass
class CacheEntry:
    symbol: str
    timeframe: str
    start_time: datetime
    candles: List[CandleData]
    cached_at: datetime
    ttl_seconds: int = 60           # 기본 TTL 60초
    access_count: int = 0
    last_access: datetime = None

    @property
    def is_expired(self) -> bool:
        return (datetime.now() - self.cached_at).total_seconds() > self.ttl_seconds
```

### 캐시 전략

#### LRU + TTL 하이브리드
```python
class CandleCacheV2:
    def __init__(self, max_memory_mb: int = 100, default_ttl: int = 60):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: OrderedDict = OrderedDict()
        self.memory_usage = 0

    async def get_complete_range(self, symbol: str, timeframe: str,
                               start_time: datetime, count: int) -> Optional[List[CandleData]]:
        """완전한 범위의 캐시 데이터 조회"""
        cache_key = self._generate_cache_key(symbol, timeframe, start_time, count)

        if cache_key in self.cache:
            entry = self.cache[cache_key]

            # TTL 만료 확인
            if entry.is_expired:
                await self._evict_entry(cache_key)
                return None

            # 액세스 업데이트 (LRU)
            entry.access_count += 1
            entry.last_access = datetime.now()
            self.access_order.move_to_end(cache_key)

            return entry.candles.copy()

        return None

    async def store_range(self, symbol: str, timeframe: str,
                         start_time: datetime, candles: List[CandleData]) -> bool:
        """범위 데이터 캐시 저장"""
        if not candles:
            return False

        cache_key = self._generate_cache_key(symbol, timeframe, start_time, len(candles))
        entry_size = self._calculate_entry_size(candles)

        # 메모리 한계 확인 및 정리
        await self._ensure_memory_capacity(entry_size)

        # 캐시 엔트리 생성
        entry = CacheEntry(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            candles=candles.copy(),
            cached_at=datetime.now(),
            ttl_seconds=self.default_ttl
        )

        self.cache[cache_key] = entry
        self.access_order[cache_key] = datetime.now()
        self.memory_usage += entry_size

        return True
```

#### 캐시 무효화 전략
```python
async def invalidate_related_caches(self, symbol: str, timeframe: str,
                                  affected_time_range: Tuple[datetime, datetime]) -> None:
    """
    관련 캐시 무효화 (새 데이터 삽입 시)
    """
    start_time, end_time = affected_time_range
    keys_to_remove = []

    for cache_key, entry in self.cache.items():
        if (entry.symbol == symbol and entry.timeframe == timeframe):
            # 시간 범위 겹침 확인
            entry_end = entry.start_time + timedelta(seconds=get_timeframe_seconds(timeframe) * len(entry.candles))

            if self._ranges_overlap(entry.start_time, entry_end, start_time, end_time):
                keys_to_remove.append(cache_key)

    for key in keys_to_remove:
        await self._evict_entry(key)
```

## 📈 성능 최적화 및 모니터링

### 성능 메트릭

#### 통계 수집
```python
@dataclass
class PerformanceStats:
    # 기본 통계
    total_requests: int = 0
    cache_hits: int = 0
    cache_hit_rate: float = 0.0

    # DB/API 분석
    db_only_requests: int = 0
    api_only_requests: int = 0
    mixed_requests: int = 0

    # 최적화 효과
    api_requests_saved: int = 0
    optimization_rate: float = 0.0

    # 성능 지표
    average_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0

    # 에러 추적
    validation_errors: int = 0
    api_errors: int = 0
    db_errors: int = 0

    def calculate_derived_metrics(self):
        """파생 지표 계산"""
        if self.total_requests > 0:
            self.cache_hit_rate = self.cache_hits / self.total_requests
            self.optimization_rate = self.api_requests_saved / self.total_requests
```

#### 로깅 시스템
```python
class PerformanceLogger:
    def __init__(self):
        self.logger = create_component_logger("CandleProviderV2.Performance")
        self.response_times = []

    async def log_request_start(self, symbol: str, timeframe: str,
                              params: dict) -> str:
        """요청 시작 로깅"""
        request_id = str(uuid.uuid4())[:8]
        self.logger.info(f"🚀 [{request_id}] 요청 시작: {symbol} {timeframe} {params}")
        return request_id

    async def log_request_complete(self, request_id: str, result: dict) -> None:
        """요청 완료 로깅"""
        self.logger.info(f"✅ [{request_id}] 완료: {result}")

        # 응답 시간 수집
        if 'response_time_ms' in result:
            self.response_times.append(result['response_time_ms'])

            # 주기적 통계 출력 (100 요청마다)
            if len(self.response_times) % 100 == 0:
                await self._log_performance_summary()

    async def _log_performance_summary(self) -> None:
        """성능 요약 출력"""
        if not self.response_times:
            return

        import statistics
        recent_times = self.response_times[-100:]  # 최근 100개

        summary = {
            'count': len(recent_times),
            'avg_ms': statistics.mean(recent_times),
            'median_ms': statistics.median(recent_times),
            'p95_ms': statistics.quantiles(recent_times, n=20)[18] if len(recent_times) >= 20 else 0,
            'max_ms': max(recent_times)
        }

        self.logger.info(f"📊 성능 요약 (최근 100 요청): {summary}")
```

### 병목 지점 분석

#### 프로파일링 시스템
```python
import cProfile
import pstats
from contextlib import asynccontextmanager

@asynccontextmanager
async def profile_request(request_id: str):
    """요청별 프로파일링"""
    profiler = cProfile.Profile()
    profiler.enable()

    try:
        yield
    finally:
        profiler.disable()

        # 통계 분석
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')

        # 상위 10개 함수 로깅
        import io
        s = io.StringIO()
        stats.print_stats(10)
        profile_output = s.getvalue()

        logger.debug(f"🔍 [{request_id}] 프로파일링 결과:\n{profile_output}")
```

## 🧪 테스트 전략

### 단위 테스트

#### 파라미터 조합 테스트
```python
class TestParameterCombinations:
    """5가지 파라미터 조합 테스트"""

    @pytest.mark.asyncio
    async def test_count_only(self):
        """케이스 1: count만 제공"""
        provider = CandleDataProviderV2()
        result = await provider.get_candles("KRW-BTC", "1m", count=100)

        assert result.success
        assert len(result.candles) == 100
        assert result.candles[0].candle_date_time_utc <= result.candles[-1].candle_date_time_utc

    @pytest.mark.asyncio
    async def test_start_time_and_count(self):
        """케이스 2: start_time + count"""
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        provider = CandleDataProviderV2()
        result = await provider.get_candles("KRW-BTC", "1m",
                                          start_time=start, count=50)

        assert result.success
        assert len(result.candles) == 50
        assert result.candles[0].candle_date_time_utc >= start.isoformat()

    @pytest.mark.asyncio
    async def test_time_range(self):
        """케이스 3: start_time + end_time"""
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2025, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        provider = CandleDataProviderV2()
        result = await provider.get_candles("KRW-BTC", "1m",
                                          start_time=start, end_time=end)

        assert result.success
        assert len(result.candles) == 61  # 1시간 = 61개 캔들 (포함)

    @pytest.mark.asyncio
    async def test_invalid_combinations(self):
        """금지된 조합 테스트"""
        provider = CandleDataProviderV2()

        with pytest.raises(ValidationError):
            await provider.get_candles("KRW-BTC", "1m",
                                     count=100, end_time=datetime.now())
```

#### 겹침 분석 테스트
```python
class TestOverlapAnalysis:
    """겹침 분석 로직 테스트"""

    @pytest.fixture
    async def mock_repository(self):
        """Mock Repository 설정"""
        repo = MagicMock()
        # 테스트 데이터 설정
        return repo

    @pytest.mark.asyncio
    async def test_no_overlap(self, mock_repository):
        """겹침 없음 케이스"""
        mock_repository.has_any_data_in_range.return_value = False

        analyzer = OverlapAnalyzerV2(mock_repository, TimeUtils)
        result = await analyzer.analyze_overlap("KRW-BTC", "1m",
                                               datetime.now(), 100)

        assert result.status == OverlapStatus.NO_OVERLAP
        assert result.api_request_needed == True

    @pytest.mark.asyncio
    async def test_complete_overlap(self, mock_repository):
        """완전 겹침 케이스"""
        mock_repository.has_any_data_in_range.return_value = True
        mock_repository.is_range_complete.return_value = True

        analyzer = OverlapAnalyzerV2(mock_repository, TimeUtils)
        result = await analyzer.analyze_overlap("KRW-BTC", "1m",
                                               datetime.now(), 100)

        assert result.status == OverlapStatus.COMPLETE_OVERLAP
        assert result.api_request_needed == False
```

### 통합 테스트

#### End-to-End 테스트
```python
class TestEndToEnd:
    """전체 시스템 통합 테스트"""

    @pytest.mark.asyncio
    async def test_large_request_chunking(self):
        """대량 요청 청크 분할 테스트"""
        provider = CandleDataProviderV2()

        # 1000개 요청 (5개 청크로 분할 예상)
        result = await provider.get_candles("KRW-BTC", "1m", count=1000)

        assert result.success
        assert len(result.candles) == 1000
        assert "chunk" in result.metadata
        assert result.metadata["chunks_processed"] == 5

    @pytest.mark.asyncio
    async def test_mixed_optimization(self):
        """DB/API 혼합 최적화 테스트"""
        provider = CandleDataProviderV2()

        # 첫 번째 요청 (API에서 수집)
        result1 = await provider.get_candles("KRW-BTC", "1m", count=100)
        assert result1.data_source == "api"

        # 겹치는 두 번째 요청 (혼합 최적화 예상)
        start_time = datetime.fromisoformat(result1.candles[50].candle_date_time_utc)
        result2 = await provider.get_candles("KRW-BTC", "1m",
                                           start_time=start_time, count=100)
        assert result2.data_source == "mixed"
        assert result2.metadata["api_requests_saved"] > 0
```

### 성능 테스트

#### 부하 테스트
```python
class TestPerformance:
    """성능 및 부하 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """동시 요청 처리 테스트"""
        provider = CandleDataProviderV2()

        # 10개 동시 요청
        tasks = []
        for i in range(10):
            task = provider.get_candles("KRW-BTC", "1m", count=100)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # 모든 요청 성공 확인
        assert all(r.success for r in results)

        # 평균 응답 시간 확인 (5초 이내)
        avg_time = sum(r.response_time_ms for r in results) / len(results)
        assert avg_time < 5000

    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """메모리 사용량 테스트"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        provider = CandleDataProviderV2()

        # 대량 요청 (10만개)
        result = await provider.get_candles("KRW-BTC", "1m", count=100000)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # 메모리 증가량 확인 (500MB 이내)
        assert memory_increase < 500 * 1024 * 1024
        assert result.success
```

## 🔄 마이그레이션 계획

### v1 → v2 마이그레이션

#### 단계별 전환
1. **Phase 1**: v2 구현 완료 및 테스트
2. **Phase 2**: v1과 v2 병렬 운영 (Feature Flag)
3. **Phase 3**: 점진적 트래픽 전환 (10% → 50% → 100%)
4. **Phase 4**: v1 제거 및 정리

#### 호환성 보장
```python
class CandleDataProviderV2Adapter:
    """v1 API 호환성 제공"""

    def __init__(self):
        self.v2_provider = CandleDataProviderV2()

    async def get_candles_legacy(self, *args, **kwargs):
        """v1 메서드 시그니처 지원"""
        # v1 파라미터를 v2 형식으로 변환
        converted_params = self._convert_v1_to_v2_params(*args, **kwargs)

        # v2 호출
        result = await self.v2_provider.get_candles(**converted_params)

        # v1 응답 형식으로 변환
        return self._convert_v2_to_v1_response(result)
```

### 데이터 마이그레이션

#### DB 스키마 검증
```python
async def validate_db_compatibility():
    """기존 DB와 v2 호환성 검증"""
    # 스키마 확인
    # 인덱스 검증
    # 데이터 무결성 체크
    pass
```

## 📋 구현 체크리스트

### Phase 1: 기반 구조 (2주)
- [ ] TimeCalculator 구현 (파라미터 조합 처리)
- [ ] OverlapAnalyzerV2 구현 (겹침 분석 개선)
- [ ] RequestValidator 구현 (요청 검증)
- [ ] 기본 단위 테스트 작성

### Phase 2: 핵심 로직 (3주)
- [ ] ChunkProcessor 구현 (청크 분할)
- [ ] DataCollector 구현 (DB/API 혼합 수집)
- [ ] CandleDataProviderV2 메인 클래스 구현
- [ ] 통합 테스트 작성

### Phase 3: 최적화 (2주)
- [ ] CacheManagerV2 구현 (캐시 전략 개선)
- [ ] 성능 모니터링 시스템 구현
- [ ] 부하 테스트 및 최적화
- [ ] 에러 처리 개선

### Phase 4: 마이그레이션 (1주)
- [ ] v1 호환성 어댑터 구현
- [ ] 점진적 전환 시스템 구현
- [ ] 문서화 및 가이드 작성
- [ ] 프로덕션 배포

## 📖 결론

CandleDataProvider v2.0은 기존 v1의 복잡성과 예측 불가능성을 해결하고, 명확하고 효율적인 캔들 데이터 제공 서비스를 목표로 합니다.

### 핵심 개선사항
1. **명확한 파라미터 처리**: 5가지 케이스로 단순화
2. **최적화된 겹침 분석**: DB/API 혼합 전략으로 효율성 극대화
3. **안정적인 청크 처리**: 200개 단위 분할과 순차 처리
4. **향상된 캐시 시스템**: LRU + TTL 하이브리드 전략
5. **포괄적인 모니터링**: 성능 지표와 최적화 효과 추적

### 예상 효과
- **API 요청 감소**: 겹침 분석을 통해 30-50% API 요청 절약
- **응답 시간 개선**: 캐시와 DB 조회 활용으로 평균 응답 시간 50% 단축
- **시스템 안정성**: 명확한 에러 처리와 검증으로 오류율 90% 감소
- **개발 생산성**: 예측 가능한 동작으로 디버깅 시간 단축

이 계획서를 바탕으로 단계적 구현을 진행하여 안정적이고 효율적인 캔들 데이터 제공 시스템을 구축할 수 있습니다.
