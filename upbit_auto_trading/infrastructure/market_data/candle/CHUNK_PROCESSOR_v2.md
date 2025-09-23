# 📋 ChunkProcessor v2.0 설계서 - Legacy 로직 완전 보존 버전

> **핵심 철학**: 기존 잘 동작하던 Legacy 로직을 100% 보존하면서 구조만 개선
> **목표**: 독립적 사용 가능 + 명확한 책임 분리 + UI 연동 지원

---

## 🎯 설계 목표

### 주요 목표
1. **Legacy 로직 100% 보존**: `candle_data_provider_legacy.py`의 검증된 로직 그대로 이식
2. **독립적 사용 지원**: ChunkProcessor만으로 완전한 캔들 수집 가능 (코인 스크리너 등)
3. **명확한 책임 분리**: CandleDataProvider는 얇은 인터페이스 레이어로 변경
4. **UI 연동 지원**: Progress Callback을 통한 실시간 진행 상황 보고
5. **기존 호환성 유지**: 현재 인터페이스와 100% 호환
6. **불필요한 기능 제거**: 기존에 없던 추가 검증이나 기능은 제거

### 설계 원칙
- **Legacy First**: 새로운 기능보다 기존 로직 보존 우선
- **Minimal Change**: 구조 변경만 하고 로직은 그대로
- **Single Responsibility**: 각 클래스는 하나의 명확한 책임만
- **Clean Interface**: 사용하기 쉬운 깔끔한 API 제공

---

## 🔍 현재 문제점 분석

### v7.0 ChunkProcessor 문제점

#### 1. 복잡한 4단계 파이프라인
```python
# 현재: 불필요하게 복잡한 구조
Phase 1: prepare_execution → OverlapAnalysis 객체 생성
Phase 2: fetch_data → ApiResponse 객체 생성
Phase 3: process_data → ProcessedData 객체 생성
Phase 4: persist_data → StorageResult 객체 생성
```
**문제**: Legacy에는 없던 복잡한 중간 객체들과 검증 로직 추가

#### 2. 과도한 추상화
- `ExecutionPlan`, `OverlapAnalysis`, `ApiResponse` 등 Legacy에 없던 객체들
- Legacy의 간단하고 직접적인 로직이 추상화로 인해 복잡해짐

#### 3. 독립적 사용 불가
- CandleDataProvider의 CollectionState에 의존
- ChunkProcessor만으로는 완전한 수집 불가능

#### 4. Legacy 로직 누락
- 요청 타입별 세밀한 처리 로직 일부 누락
- 첫 청크 구분 로직의 미묘한 차이
- 안전한 참조 범위 계산 로직 단순화

---

## 🏗️ 새로운 ChunkProcessor v2.0 설계

### 핵심 설계 철학

#### 1. **Legacy 로직 완전 이식**
```python
# Legacy → ChunkProcessor v2.0 이식 맵핑
Legacy._process_chunk_direct_storage()     → ChunkProcessor._process_chunk()
Legacy._handle_overlap_direct_storage()    → ChunkProcessor._handle_overlap()
Legacy._fetch_chunk_from_api()            → ChunkProcessor._fetch_from_api()
Legacy._analyze_chunk_overlap()           → ChunkProcessor._analyze_overlap()
Legacy._process_api_candles_with_empty_filling() → ChunkProcessor._process_empty_candles()
Legacy.plan_collection()                  → ChunkProcessor._plan_collection()
```

#### 2. **이중 인터페이스 지원**
```python
class ChunkProcessor:
    # 독립 사용용 (코인 스크리너 등)
    async def execute_full_collection(
        self, symbol, timeframe, count=None, to=None, end=None,
        progress_callback=None
    ) -> CollectionResult

    # CandleDataProvider 연동용 (기존 호환성)
    async def execute_single_chunk(
        self, chunk_info: ChunkInfo, collection_state: CollectionState
    ) -> ChunkResult
```

---

## 📊 데이터 모델 설계

### Progress Reporting 모델

```python
@dataclass
class CollectionProgress:
    """수집 진행 상황 (UI 업데이트용)"""
    # 기본 정보
    symbol: str
    timeframe: str
    request_id: str

    # 진행 상황
    current_chunk: int
    total_chunks: int
    collected_candles: int
    requested_candles: int

    # 시간 정보
    elapsed_seconds: float
    estimated_remaining_seconds: float
    estimated_completion_time: datetime

    # 상태
    current_status: str  # "analyzing", "fetching", "processing", "storing"
    last_chunk_info: Optional[str]  # "수집: 200개 (overlap: NO_OVERLAP)"

@dataclass
class CollectionResult:
    """수집 완료 결과"""
    success: bool
    collected_count: int
    requested_count: int
    processing_time_seconds: float

    # 오류 정보
    error: Optional[Exception] = None
    error_chunk_id: Optional[str] = None

    # 메타데이터
    chunks_processed: int = 0
    api_calls_made: int = 0
    overlap_optimizations: int = 0
    empty_candles_filled: int = 0

# Progress Callback 타입
ProgressCallback = Callable[[CollectionProgress], None]
```

### Legacy 호환 모델

```python
# 기존 모델들 그대로 유지
class ChunkResult:
    """개별 청크 처리 결과 (기존과 동일)"""
    success: bool
    chunk_id: str
    saved_count: int
    processing_time_ms: float
    # ... 기존 필드들 그대로
```

---

## 🔄 핵심 메서드 설계

### 1. 독립 사용용 메인 메서드

```python
async def execute_full_collection(
    self,
    symbol: str,
    timeframe: str,
    count: Optional[int] = None,
    to: Optional[datetime] = None,
    end: Optional[datetime] = None,
    progress_callback: Optional[ProgressCallback] = None,
    dry_run: bool = False
) -> CollectionResult:
    """
    🚀 완전 독립적 캔들 수집 (코인 스크리너 등에서 사용)

    Legacy plan_collection + mark_chunk_completed 로직을 완전 통합
    """
    start_time = time.time()

    try:
        # 1. RequestInfo 생성 및 검증 (Legacy 로직)
        request_info = self._create_request_info(symbol, timeframe, count, to, end)

        # 2. 수집 계획 수립 (Legacy plan_collection 이식)
        collection_plan = self._plan_collection(request_info)

        # 3. 내부 수집 상태 생성
        collection_state = self._create_internal_collection_state(
            request_info, collection_plan
        )

        # 4. 청크별 순차 처리 (Legacy mark_chunk_completed 로직)
        while not collection_state.is_completed:
            # Progress 보고
            if progress_callback:
                progress = self._create_progress_report(collection_state, start_time)
                progress_callback(progress)

            # 현재 청크 처리 (Legacy _process_chunk_direct_storage)
            chunk_result = await self._process_current_chunk(collection_state)

            # 상태 업데이트 (Legacy 로직)
            self._update_collection_state(collection_state, chunk_result)

            # 완료 확인 (Legacy _is_collection_complete)
            if self._is_collection_complete(collection_state):
                break

            # 다음 청크 준비 (Legacy _prepare_next_chunk)
            self._prepare_next_chunk(collection_state)

        # 5. 최종 결과 생성
        return self._create_success_result(collection_state, start_time)

    except Exception as e:
        return self._create_error_result(e, start_time, collection_state)
```

### 2. Legacy 로직 완전 이식 메서드들

```python
async def _process_current_chunk(self, collection_state: InternalCollectionState) -> ChunkResult:
    """
    Legacy _process_chunk_direct_storage() 완전 이식

    기존 로직을 그대로 유지:
    - 첫 청크 구분
    - 안전한 참조 범위 계산
    - 요청 타입별 처리
    - 겹침 분석 및 최적화
    """
    chunk_info = collection_state.current_chunk
    is_first_chunk = len(collection_state.completed_chunks) == 0
    request_type = collection_state.request_info.get_request_type()

    # Legacy: 안전한 참조 범위 계산
    safe_range_start = None
    safe_range_end = None
    if collection_state.completed_chunks and chunk_info.end:
        safe_range_start = collection_state.completed_chunks[0].to
        safe_range_end = chunk_info.end

    # Legacy: 겹침 분석 (첫 청크 + COUNT_ONLY/END_ONLY는 건너뛰기)
    overlap_result = None
    if not (is_first_chunk and request_type in [RequestType.COUNT_ONLY, RequestType.END_ONLY]):
        overlap_result = await self._analyze_overlap(chunk_info)

    # Legacy: 겹침 결과에 따른 처리 분기
    if overlap_result and hasattr(overlap_result, 'status'):
        return await self._handle_overlap(
            chunk_info, overlap_result, collection_state,
            is_first_chunk, safe_range_start, safe_range_end
        )
    else:
        return await self._handle_no_overlap(
            chunk_info, collection_state,
            is_first_chunk, safe_range_start, safe_range_end
        )

async def _handle_overlap(
    self, chunk_info: ChunkInfo, overlap_result, collection_state,
    is_first_chunk: bool, safe_range_start, safe_range_end
) -> ChunkResult:
    """
    Legacy _handle_overlap_direct_storage() 완전 이식
    """
    # Legacy 겹침 처리 로직 그대로 이식
    from upbit_auto_trading.infrastructure.market_data.candle.models import OverlapStatus

    status = overlap_result.status

    if status == OverlapStatus.COMPLETE_OVERLAP:
        # Legacy: 완전 겹침 - API 호출 없이 0개 저장
        chunk_info.set_api_request_info(0, None, None)
        chunk_info.set_api_response_info([])
        chunk_info.set_final_candle_info([])

        saved_count = 0
        last_candle_time_str = None

    elif status == OverlapStatus.NO_OVERLAP:
        # Legacy: 겹침 없음 - 전체 API 호출
        saved_count, last_candle_time_str = await self._fetch_and_store_full_chunk(
            chunk_info, is_first_chunk, safe_range_start, safe_range_end
        )

    elif status in [OverlapStatus.PARTIAL_START, OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS]:
        # Legacy: 부분 겹침 - 최적화된 API 호출
        saved_count, last_candle_time_str = await self._fetch_and_store_partial_chunk(
            chunk_info, overlap_result, is_first_chunk, safe_range_start, safe_range_end
        )

    else:
        # Legacy: 기타 - 전체 API 호출로 폴백
        saved_count, last_candle_time_str = await self._fetch_and_store_full_chunk(
            chunk_info, is_first_chunk, safe_range_start, safe_range_end
        )

    return ChunkResult(
        success=True,
        chunk_id=chunk_info.chunk_id,
        saved_count=saved_count,
        processing_time_ms=0,  # Legacy와 동일하게 처리
        metadata={'last_candle_time': last_candle_time_str}
    )

async def _fetch_from_api(self, chunk_info: ChunkInfo) -> List[Dict[str, Any]]:
    """
    Legacy _fetch_chunk_from_api() 완전 이식
    """
    # Legacy API 호출 로직 그대로 이식 (타임프레임별 분기 포함)
    logger.debug(f"API 청크 요청: {chunk_info.chunk_id}")

    api_count, api_to = chunk_info.get_api_params()

    try:
        # Legacy: 타임프레임별 API 분기 로직 그대로
        if chunk_info.timeframe == '1s':
            # 초봉 API 지점 보정 (Legacy 로직)
            to_param = None
            if api_to:
                timeframe_delta = TimeUtils.get_timeframe_delta(chunk_info.timeframe)
                fetch_time = api_to + timeframe_delta
                to_param = fetch_time.strftime("%Y-%m-%dT%H:%M:%S")

            candles = await self.upbit_client.get_candles_seconds(
                market=chunk_info.symbol,
                count=api_count,
                to=to_param
            )

        elif chunk_info.timeframe.endswith('m'):
            # 분봉 (Legacy 로직)
            unit = int(chunk_info.timeframe[:-1])
            if unit not in [1, 3, 5, 10, 15, 30, 60, 240]:
                raise ValueError(f"지원하지 않는 분봉 단위: {unit}")

            to_param = None
            if api_to:
                timeframe_delta = TimeUtils.get_timeframe_delta(chunk_info.timeframe)
                fetch_time = api_to + timeframe_delta
                to_param = fetch_time.strftime("%Y-%m-%dT%H:%M:%S")

            candles = await self.upbit_client.get_candles_minutes(
                unit=unit,
                market=chunk_info.symbol,
                count=api_count,
                to=to_param
            )

        # ... 기타 타임프레임들도 Legacy 로직 그대로

        logger.info(f"API 청크 완료: {chunk_info.chunk_id}, 수집: {len(candles)}개")
        return candles

    except Exception as e:
        logger.error(f"API 청크 실패: {chunk_info.chunk_id}, 오류: {e}")
        raise

async def _process_empty_candles(
    self, api_candles: List[Dict[str, Any]], chunk_info: ChunkInfo,
    is_first_chunk: bool, safe_range_start, safe_range_end
) -> List[Dict[str, Any]]:
    """
    Legacy _process_api_candles_with_empty_filling() 완전 이식
    """
    if not self.enable_empty_candle_processing:
        return api_candles

    # Legacy EmptyCandleDetector 사용 (그대로)
    detector = self.empty_candle_detector_factory(chunk_info.symbol, chunk_info.timeframe)

    processed_candles = detector.detect_and_fill_gaps(
        api_candles,
        api_start=chunk_info.api_request_start,
        api_end=chunk_info.api_request_end,
        is_first_chunk=is_first_chunk
    )

    # Legacy: 캔들 수 보정 로깅
    if len(processed_candles) != len(api_candles):
        filled_count = len(processed_candles) - len(api_candles)
        logger.info(f"빈 캔들 채우기: {filled_count}개 추가 (API: {len(api_candles)} → 최종: {len(processed_candles)})")

    return processed_candles
```

### 3. CandleDataProvider 연동용 메서드

```python
async def execute_single_chunk(
    self, chunk_info: ChunkInfo, collection_state: CollectionState
) -> ChunkResult:
    """
    CandleDataProvider.mark_chunk_completed()에서 사용
    기존 인터페이스 완전 호환
    """
    # 내부 상태로 변환
    internal_state = self._convert_to_internal_state(collection_state)
    internal_state.current_chunk = chunk_info

    # 단일 청크 처리
    result = await self._process_current_chunk(internal_state)

    # 외부 상태 업데이트
    self._update_external_state(collection_state, internal_state, result)

    return result
```

---

## 🎨 CandleDataProvider 간소화 설계

### 새로운 CandleDataProvider (얇은 레이어)

```python
class CandleDataProvider:
    """
    얇은 인터페이스 레이어 - ChunkProcessor에 위임
    """

    def __init__(self, ...):
        # ChunkProcessor 초기화
        self.chunk_processor = ChunkProcessor(...)

    async def get_candles(
        self, symbol: str, timeframe: str,
        count: Optional[int] = None,
        to: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[CandleData]:
        """
        완전 간소화된 캔들 수집 - ChunkProcessor에 완전 위임
        """
        logger.info(f"캔들 수집 요청: {symbol} {timeframe}")

        try:
            # ChunkProcessor에 전체 수집 위임
            collection_result = await self.chunk_processor.execute_full_collection(
                symbol=symbol,
                timeframe=timeframe,
                count=count,
                to=to,
                end=end
            )

            if collection_result.success:
                # Repository에서 결과 조회
                return await self._get_final_result_from_db(
                    symbol, timeframe, collection_result
                )
            else:
                logger.error(f"수집 실패: {collection_result.error}")
                return []

        except Exception as e:
            logger.error(f"캔들 수집 실패: {e}")
            raise

    async def _get_final_result_from_db(
        self, symbol: str, timeframe: str, collection_result: CollectionResult
    ) -> List[CandleData]:
        """Repository에서 최종 결과 조회 (Legacy 로직 유지)"""
        # Legacy _get_final_result 로직 그대로 사용
        pass

    # 기존 호환성 메서드들 (ChunkProcessor 위임)
    def start_collection(self, ...) -> str:
        """기존 호환성을 위해 유지하되 내부적으로 ChunkProcessor 사용"""
        pass

    async def mark_chunk_completed(self, request_id: str) -> bool:
        """기존 호환성을 위해 유지하되 내부적으로 ChunkProcessor 사용"""
        pass
```

---

## 🚀 사용 예시

### 1. 독립 사용 (코인 스크리너)

```python
# 다중 코인 수집 시나리오
chunk_processor = ChunkProcessor(
    repository=repository,
    upbit_client=upbit_client,
    overlap_analyzer=overlap_analyzer,
    empty_candle_detector_factory=detector_factory
)

# Progress UI 업데이트 함수
def update_progress_ui(progress: CollectionProgress):
    progress_bar.set_value(progress.collected_candles / progress.requested_candles * 100)
    status_label.set_text(f"{progress.symbol}: {progress.current_status}")
    eta_label.set_text(f"완료 예상: {progress.estimated_remaining_seconds:.1f}초")

# 여러 코인 순차 수집
symbols = ['KRW-BTC', 'KRW-ETH', 'KRW-ADA', 'KRW-DOT']
results = {}

for symbol in symbols:
    print(f"\n🚀 {symbol} 수집 시작...")

    result = await chunk_processor.execute_full_collection(
        symbol=symbol,
        timeframe='1d',
        count=365,  # 1년치 데이터
        progress_callback=update_progress_ui
    )

    if result.success:
        print(f"✅ {symbol} 수집 완료: {result.collected_count}개")
        results[symbol] = result
    else:
        print(f"❌ {symbol} 수집 실패: {result.error}")

print(f"\n📊 전체 수집 결과: {len(results)}/{len(symbols)} 성공")
```

### 2. CandleDataProvider 연동 (기존 호환)

```python
# 기존 코드 그대로 동작
provider = CandleDataProvider(...)

candles = await provider.get_candles(
    symbol='KRW-BTC',
    timeframe='1m',
    count=1000
)

print(f"수집된 캔들: {len(candles)}개")
```

### 3. 실시간 진행 상황 모니터링

```python
import asyncio
from datetime import datetime

# 실시간 진행 상황 출력
def print_progress(progress: CollectionProgress):
    now = datetime.now().strftime("%H:%M:%S")
    percent = (progress.collected_candles / progress.requested_candles) * 100

    print(f"[{now}] {progress.symbol} {progress.timeframe} | "
          f"청크: {progress.current_chunk}/{progress.total_chunks} | "
          f"캔들: {progress.collected_candles}/{progress.requested_candles} ({percent:.1f}%) | "
          f"상태: {progress.current_status} | "
          f"남은시간: {progress.estimated_remaining_seconds:.1f}초")

# 대용량 데이터 수집 (진행 상황 실시간 모니터링)
result = await chunk_processor.execute_full_collection(
    symbol='KRW-BTC',
    timeframe='1m',
    count=10000,  # 약 7일치 1분봉
    progress_callback=print_progress
)

# 출력 예시:
# [14:23:10] KRW-BTC 1m | 청크: 1/50 | 캔들: 200/10000 (2.0%) | 상태: fetching | 남은시간: 245.2초
# [14:23:12] KRW-BTC 1m | 청크: 2/50 | 캔들: 400/10000 (4.0%) | 상태: processing | 남은시간: 230.1초
# ...
```

---

## 🔄 마이그레이션 로드맵

### Phase 1: ChunkProcessor v2.0 구현 (1주)

**목표**: Legacy 로직 완전 이식된 새로운 ChunkProcessor 구현

- [ ] `ChunkProcessor` 클래스 기본 구조 생성
- [ ] Legacy 메서드들 완전 이식:
  - [ ] `_process_chunk_direct_storage()` → `_process_current_chunk()`
  - [ ] `_handle_overlap_direct_storage()` → `_handle_overlap()`
  - [ ] `_fetch_chunk_from_api()` → `_fetch_from_api()`
  - [ ] `_analyze_chunk_overlap()` → `_analyze_overlap()`
  - [ ] `_process_api_candles_with_empty_filling()` → `_process_empty_candles()`
  - [ ] `plan_collection()` → `_plan_collection()`
- [ ] `execute_full_collection()` 메인 메서드 구현
- [ ] Progress Reporting 시스템 구현
- [ ] 독립 단위 테스트 작성

### Phase 2: CandleDataProvider 간소화 (3일)

**목표**: CandleDataProvider를 얇은 레이어로 변경

- [ ] `get_candles()` 메서드 간소화 (ChunkProcessor 위임)
- [ ] 기존 호환성 메서드들 ChunkProcessor 위임으로 변경
- [ ] 복잡한 상태 관리 로직 제거
- [ ] `execute_single_chunk()` 연동 구현

### Phase 3: 통합 테스트 및 검증 (2일)

**목표**: 기존 기능 100% 호환 확인

- [ ] 기존 단위 테스트 모두 통과 확인
- [ ] 성능 회귀 테스트 (속도, 메모리 사용량)
- [ ] 실제 데이터로 수집 테스트
- [ ] UI 통합 테스트
- [ ] 독립 사용 시나리오 테스트

### Phase 4: 문서화 및 배포 (1일)

**목표**: 완전한 전환 완료

- [ ] API 문서 업데이트
- [ ] 사용 예시 가이드 작성
- [ ] 기존 코드 정리 및 Legacy 백업
- [ ] 프로덕션 배포

---

## 🧪 테스트 전략

### 1. Legacy 로직 호환성 테스트

```python
class TestLegacyCompatibility:
    """Legacy 로직과 100% 동일한 결과 보장 테스트"""

    async def test_identical_results_with_legacy(self):
        """Legacy와 새 버전이 동일한 결과 생성하는지 확인"""

        # 동일한 조건으로 Legacy와 새 버전 실행
        test_cases = [
            {'symbol': 'KRW-BTC', 'timeframe': '1m', 'count': 100},
            {'symbol': 'KRW-ETH', 'timeframe': '1d', 'count': 30},
            {'symbol': 'KRW-ADA', 'timeframe': '1w', 'to': datetime(2024, 1, 1)},
        ]

        for case in test_cases:
            # Legacy 결과
            legacy_provider = CandleDataProviderLegacy(...)
            legacy_result = await legacy_provider.get_candles(**case)

            # 새 버전 결과
            new_provider = CandleDataProvider(...)
            new_result = await new_provider.get_candles(**case)

            # 결과 비교 (개수, 시간, 데이터)
            assert len(legacy_result) == len(new_result)
            for i, (legacy_candle, new_candle) in enumerate(zip(legacy_result, new_result)):
                assert legacy_candle.candle_date_time_kst == new_candle.candle_date_time_kst
                assert legacy_candle.opening_price == new_candle.opening_price
                # ... 모든 필드 비교
```

### 2. 독립 사용 테스트

```python
class TestIndependentUsage:
    """ChunkProcessor 독립 사용 테스트"""

    async def test_independent_collection(self):
        """CandleDataProvider 없이도 수집 가능한지 확인"""

        chunk_processor = ChunkProcessor(...)

        result = await chunk_processor.execute_full_collection(
            symbol='KRW-BTC',
            timeframe='1m',
            count=100
        )

        assert result.success
        assert result.collected_count == 100

    async def test_progress_callback(self):
        """Progress Callback이 정상 호출되는지 확인"""

        progress_calls = []

        def track_progress(progress: CollectionProgress):
            progress_calls.append(progress)

        result = await chunk_processor.execute_full_collection(
            symbol='KRW-BTC',
            timeframe='1m',
            count=100,
            progress_callback=track_progress
        )

        assert len(progress_calls) > 0
        assert all(p.symbol == 'KRW-BTC' for p in progress_calls)
```

### 3. 성능 회귀 테스트

```python
class TestPerformanceRegression:
    """성능 회귀가 없는지 확인"""

    async def test_memory_usage(self):
        """메모리 사용량이 Legacy와 비슷한지 확인"""

        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Legacy 메모리 사용량
        memory_before = process.memory_info().rss
        legacy_result = await legacy_provider.get_candles('KRW-BTC', '1m', 1000)
        legacy_memory = process.memory_info().rss - memory_before

        # 새 버전 메모리 사용량
        memory_before = process.memory_info().rss
        new_result = await new_provider.get_candles('KRW-BTC', '1m', 1000)
        new_memory = process.memory_info().rss - memory_before

        # 메모리 사용량 비교 (±10% 허용)
        assert abs(new_memory - legacy_memory) / legacy_memory < 0.1

    async def test_execution_time(self):
        """실행 시간이 Legacy와 비슷한지 확인"""

        import time

        # Legacy 실행 시간
        start = time.time()
        legacy_result = await legacy_provider.get_candles('KRW-BTC', '1m', 1000)
        legacy_time = time.time() - start

        # 새 버전 실행 시간
        start = time.time()
        new_result = await new_provider.get_candles('KRW-BTC', '1m', 1000)
        new_time = time.time() - start

        # 실행 시간 비교 (±20% 허용)
        assert abs(new_time - legacy_time) / legacy_time < 0.2
```

---

## 📈 예상 성과

### 코드 품질 개선
- **복잡도 감소**: CandleDataProvider 1,200줄 → 300줄 (75% 감소)
- **책임 분리**: 명확한 단일 책임 원칙 준수
- **테스트 용이성**: 독립적 단위 테스트 가능

### 기능성 향상
- **독립적 사용**: ChunkProcessor만으로 완전한 수집 가능
- **UI 연동**: Progress Callback을 통한 실시간 진행 상황 보고
- **확장성**: 새로운 사용 사례 쉽게 추가 가능

### 유지보수성 향상
- **Legacy 로직 보존**: 검증된 로직을 그대로 유지
- **명확한 구조**: 각 메서드의 역할이 명확함
- **호환성 보장**: 기존 코드 변경 없이 동작

---

## 🎯 결론

ChunkProcessor v2.0은 다음 원칙을 철저히 준수합니다:

1. **Legacy First**: 기존 잘 동작하던 로직을 100% 보존
2. **Clean Structure**: 명확하고 이해하기 쉬운 구조
3. **Independent Operation**: 독립적으로 완전한 기능 수행
4. **UI Integration**: Progress Callback으로 실시간 연동
5. **Backward Compatibility**: 기존 인터페이스 완전 호환

**최종적으로 더 깔끔하고, 더 사용하기 쉽고, 더 확장 가능한 캔들 수집 시스템을 구축할 수 있습니다.** 🎯

---

> **Next Steps**: 이 설계서를 바탕으로 Phase 1부터 순차적으로 구현을 진행하며, 각 단계별로 Legacy 호환성 테스트를 통해 검증해나가겠습니다.
