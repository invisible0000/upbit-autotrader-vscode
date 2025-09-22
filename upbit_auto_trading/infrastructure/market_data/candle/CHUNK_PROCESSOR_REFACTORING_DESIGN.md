# 📋 캔들 청크 처리기 분리 및 효율화 리팩터링 설계서

> **목적**: CandleDataProvider에서 청크 처리 로직을 분리하여 단일 책임 원칙을 준수하고, 동시에 성능을 최적화하는 리팩터링

---

## 🎯 리팩터링 목표

### 주요 목표
1. **청크 처리 로직 분리**: CandleDataProvider의 복잡성 감소
2. **메서드 명명 개선**: 기능과 동작을 명확히 표현하는 메서드명 적용
3. **성능 최적화**: 메모리 사용량 감소 및 처리 속도 향상
4. **기존 호환성 유지**: 현재 로직과 기능 구조는 그대로 유지
5. **테스트 용이성 확보**: 각 단계별 독립 테스트 가능한 구조

### 성과 지표
- 코드 복잡도 30% 감소
- 메모리 사용량 20% 절약
- 단위 테스트 커버리지 90% 이상
- API 호출 효율성 15% 향상

---

## 🔍 현재 문제점 분석

### CandleDataProvider의 문제점

#### 1. 책임 과부하 (God Object)
```python
class CandleDataProvider:
    # 전체 수집 조정 + 개별 청크 처리 + 계획 수립 + 빈 캔들 처리
    # → 1,200줄의 거대한 클래스
```

#### 2. 모호한 메서드명
- `mark_chunk_completed()` → 실제로는 전체 청크 처리를 수행
- `_process_chunk_direct_storage()` → 처리+저장이 뒤섞임
- `_analyze_chunk_overlap()` → 단순 OverlapAnalyzer 호출만 함

#### 3. 비효율적인 처리 흐름
```python
# 현재: 불필요한 중복 검증 및 메모리 낭비
def mark_chunk_completed():
    # 1. 복잡한 조건 분기
    # 2. 중복 데이터 검증
    # 3. 메모리에 중간 결과물 누적
    # 4. 겹침 분석 후에도 불필요한 API 호출
```

#### 4. 테스트 어려움
- 모든 기능이 얽혀있어 단위 테스트 불가능
- Mock 객체 사용 어려움
- 특정 기능만 테스트하기 어려움

---

## 🏗️ 새로운 ChunkProcessor 설계

### 핵심 설계 철학

#### 1. **Pipeline Pattern**: 명확한 4단계 처리 흐름
#### 2. **Single Responsibility**: 각 메서드는 하나의 명확한 책임
#### 3. **Early Exit**: 조기 종료로 불필요한 처리 방지
#### 4. **Memory Efficiency**: 스트림 처리로 메모리 최적화

### 전체 구조

```python
class ChunkProcessor:
    """
    캔들 청크 처리 전문 클래스

    책임:
    - 개별 청크의 4단계 파이프라인 처리
    - API 호출 최적화 및 겹침 분석
    - 빈 캔들 처리 및 데이터 정규화
    - 성능 모니터링 및 에러 처리
    """

    def __init__(self,
                 overlap_analyzer: OverlapAnalyzer,
                 upbit_client: UpbitPublicClient,
                 repository: CandleRepositoryInterface,
                 empty_candle_detector_factory,
                 performance_tracker: Optional[PerformanceTracker] = None):

        # 외부 의존성 주입 (테스트 용이성)
        self.overlap_analyzer = overlap_analyzer
        self.upbit_client = upbit_client
        self.repository = repository
        self.empty_candle_detector_factory = empty_candle_detector_factory

        # 성능 추적 (선택적)
        self.performance_tracker = performance_tracker or PerformanceTracker()

        # 로깅
        self.logger = create_component_logger("ChunkProcessor")
```

---

## 🔄 4단계 파이프라인 설계

### 메인 파이프라인

```python
async def execute_chunk_pipeline(self,
                                chunk_info: ChunkInfo,
                                collection_state: CollectionState) -> ChunkResult:
    """
    🚀 청크 처리 메인 파이프라인 - 전체 흐름이 한눈에 보임

    Args:
        chunk_info: 처리할 청크 정보
        collection_state: 전체 수집 상태

    Returns:
        ChunkResult: 처리 결과 (성공/실패, 저장 개수, 메타데이터)
    """

    chunk_id = chunk_info.chunk_id
    self.logger.info(f"🚀 청크 파이프라인 시작: {chunk_id}")

    with self.performance_tracker.measure_chunk_execution(chunk_id):
        try:
            # Phase 1: 📋 준비 및 분석 단계
            execution_plan = await self._phase1_prepare_execution(chunk_info)

            # 조기 종료: 완전 겹침인 경우 API 호출 생략
            if execution_plan.should_skip_api_call:
                return self._create_skip_result(execution_plan, chunk_info)

            # Phase 2: 🌐 데이터 수집 단계
            api_response = await self._phase2_fetch_data(chunk_info, execution_plan)

            # 조기 종료: 빈 응답 또는 업비트 데이터 끝
            if api_response.requires_early_exit:
                return self._handle_early_exit(api_response, chunk_info)

            # Phase 3: ⚙️ 데이터 처리 단계
            processed_data = await self._phase3_process_data(api_response, chunk_info)

            # Phase 4: 💾 데이터 저장 단계
            storage_result = await self._phase4_persist_data(processed_data, chunk_info)

            # ✅ 성공 결과 생성
            return self._create_success_result(storage_result, chunk_info)

        except Exception as e:
            self.logger.error(f"❌ 청크 파이프라인 실패: {chunk_id}, 오류: {e}")
            return self._create_error_result(e, chunk_info)
```

### Phase 1: 준비 및 분석 단계

```python
async def _phase1_prepare_execution(self, chunk_info: ChunkInfo) -> ExecutionPlan:
    """
    📋 청크 실행 준비 및 겹침 분석

    책임:
    - 겹침 상태 분석
    - API 호출 전략 결정
    - 실행 계획 수립
    """

    with self.performance_tracker.measure_phase('preparation'):
        self.logger.debug(f"📋 실행 준비: {chunk_info.chunk_id}")

        # 겹침 분석 수행
        overlap_analysis = await self._analyze_data_overlap(chunk_info)

        # 실행 계획 수립
        execution_plan = self._build_execution_plan(chunk_info, overlap_analysis)

        # ChunkInfo 메타데이터 업데이트
        chunk_info.set_overlap_info(overlap_analysis.overlap_result)

        self.logger.debug(f"📋 실행 준비 완료: {execution_plan.strategy}")
        return execution_plan

async def _analyze_data_overlap(self, chunk_info: ChunkInfo) -> OverlapAnalysis:
    """
    🔍 데이터 겹침 상태 정밀 분석

    현재 _analyze_chunk_overlap() 메서드를 개선:
    - 더 명확한 메서드명
    - 분석 결과를 구조화된 객체로 반환
    """

    # 청크 시간 범위 계산
    chunk_start = chunk_info.to
    chunk_end = self._calculate_chunk_end_time(chunk_info)

    # OverlapAnalyzer를 통한 겹침 분석
    overlap_result = await self.overlap_analyzer.analyze_overlap(
        OverlapRequest(
            symbol=chunk_info.symbol,
            timeframe=chunk_info.timeframe,
            target_start=chunk_start,
            target_end=chunk_end,
            target_count=chunk_info.count
        )
    )

    return OverlapAnalysis(
        overlap_result=overlap_result,
        analysis_time=datetime.now(timezone.utc),
        optimization_applied=True
    )
```

### Phase 2: 데이터 수집 단계

```python
async def _phase2_fetch_data(self,
                            chunk_info: ChunkInfo,
                            execution_plan: ExecutionPlan) -> ApiResponse:
    """
    🌐 최적화된 API 데이터 수집

    개선사항:
    - 겹침 분석 결과 기반 최적화된 API 호출
    - 응답 데이터 즉시 검증
    - 업비트 데이터 끝 감지
    """

    with self.performance_tracker.measure_phase('api_fetch'):
        self.logger.debug(f"🌐 API 데이터 수집: {chunk_info.chunk_id}")

        # 최적화된 API 파라미터 사용
        api_params = execution_plan.get_optimized_api_params()

        # API 호출 (기존 _fetch_chunk_from_api 로직 활용)
        raw_data = await self._call_upbit_api(chunk_info, api_params)

        # 응답 즉시 검증
        validation_result = self._validate_api_response(raw_data, chunk_info)

        # ChunkInfo에 API 응답 정보 저장
        chunk_info.set_api_response_info(raw_data)

        # 구조화된 응답 객체 생성
        return ApiResponse(
            raw_data=raw_data,
            validation_result=validation_result,
            has_upbit_data_end=len(raw_data) < api_params['count'],
            requires_early_exit=validation_result.has_critical_errors
        )

async def _call_upbit_api(self, chunk_info: ChunkInfo, api_params: Dict) -> List[Dict]:
    """
    📡 업비트 API 호출 (기존 로직 유지)

    현재 _fetch_chunk_from_api() 메서드를 분리:
    - 더 명확한 메서드명
    - API 호출 로직만 집중
    """

    # 기존 _fetch_chunk_from_api의 타임프레임별 분기 로직 그대로 사용
    if chunk_info.timeframe == '1s':
        return await self.upbit_client.get_candles_seconds(**api_params)
    elif chunk_info.timeframe.endswith('m'):
        unit = int(chunk_info.timeframe[:-1])
        return await self.upbit_client.get_candles_minutes(unit=unit, **api_params)
    # ... 기타 타임프레임 처리
```

### Phase 3: 데이터 처리 단계

```python
async def _phase3_process_data(self,
                              api_response: ApiResponse,
                              chunk_info: ChunkInfo) -> ProcessedData:
    """
    ⚙️ 캔들 데이터 처리 및 정규화

    책임:
    - 빈 캔들 감지 및 채우기
    - 데이터 정규화 및 검증
    - 처리 메타데이터 생성
    """

    with self.performance_tracker.measure_phase('data_processing'):
        self.logger.debug(f"⚙️ 데이터 처리: {chunk_info.chunk_id}")

        # 빈 캔들 처리 (기존 로직 유지)
        filled_data = await self._detect_and_fill_gaps(
            api_response.raw_data, chunk_info
        )

        # 데이터 정규화
        normalized_data = self._normalize_candle_data(filled_data)

        # 최종 검증
        validation_result = self._validate_processed_data(normalized_data, chunk_info)

        # ChunkInfo에 최종 처리 정보 저장
        chunk_info.set_final_candle_info(normalized_data)

        return ProcessedData(
            candles=normalized_data,
            gap_filled_count=len(filled_data) - len(api_response.raw_data),
            processing_metadata=self._create_processing_metadata(chunk_info),
            validation_passed=validation_result.is_valid
        )

async def _detect_and_fill_gaps(self,
                               raw_candles: List[Dict],
                               chunk_info: ChunkInfo) -> List[Dict]:
    """
    🔍 빈 캔들 감지 및 채우기 (기존 로직 유지)

    현재 _process_api_candles_with_empty_filling() 메서드를 개선:
    - 더 명확한 메서드명
    - 빈 캔들 처리만 집중
    """

    # 기존 빈 캔들 처리 로직 그대로 사용
    detector = self.empty_candle_detector_factory(chunk_info.symbol, chunk_info.timeframe)

    return detector.detect_and_fill_gaps(
        raw_candles,
        api_start=chunk_info.api_request_start,
        api_end=chunk_info.api_request_end,
        is_first_chunk=len(chunk_info.completed_chunks) == 0
    )
```

### Phase 4: 데이터 저장 단계

```python
async def _phase4_persist_data(self,
                              processed_data: ProcessedData,
                              chunk_info: ChunkInfo) -> StorageResult:
    """
    💾 처리된 데이터 영구 저장

    책임:
    - Repository를 통한 데이터 저장
    - 저장 결과 검증
    - 저장 메타데이터 생성
    """

    with self.performance_tracker.measure_phase('data_storage'):
        self.logger.debug(f"💾 데이터 저장: {chunk_info.chunk_id}")

        # 저장 실행 (기존 로직 유지)
        saved_count = await self.repository.save_raw_api_data(
            chunk_info.symbol,
            chunk_info.timeframe,
            processed_data.candles
        )

        # 저장 결과 검증
        storage_validation = self._validate_storage_result(saved_count, processed_data)

        self.logger.info(f"💾 저장 완료: {saved_count}개 저장")

        return StorageResult(
            saved_count=saved_count,
            expected_count=len(processed_data.candles),
            storage_time=datetime.now(timezone.utc),
            validation_passed=storage_validation.is_valid,
            metadata=self._create_storage_metadata(chunk_info, saved_count)
        )
```

---

## 📊 데이터 모델 설계

### 새로운 결과 객체들

```python
@dataclass
class ExecutionPlan:
    """청크 실행 계획"""
    strategy: str  # 'skip_complete_overlap', 'partial_fetch', 'full_fetch'
    should_skip_api_call: bool
    optimized_api_params: Dict[str, Any]
    expected_data_range: Tuple[datetime, datetime]
    overlap_optimization: bool = True

    def get_optimized_api_params(self) -> Dict[str, Any]:
        """겹침 분석 기반 최적화된 API 파라미터 반환"""
        return self.optimized_api_params

@dataclass
class OverlapAnalysis:
    """겹침 분석 결과"""
    overlap_result: Any  # OverlapResult 객체
    analysis_time: datetime
    optimization_applied: bool
    recommendations: List[str] = field(default_factory=list)

@dataclass
class ApiResponse:
    """API 응답 래퍼"""
    raw_data: List[Dict[str, Any]]
    validation_result: Any  # ValidationResult 객체
    has_upbit_data_end: bool
    requires_early_exit: bool
    response_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessedData:
    """처리된 캔들 데이터"""
    candles: List[Dict[str, Any]]
    gap_filled_count: int
    processing_metadata: Dict[str, Any]
    validation_passed: bool

@dataclass
class StorageResult:
    """데이터 저장 결과"""
    saved_count: int
    expected_count: int
    storage_time: datetime
    validation_passed: bool
    metadata: Dict[str, Any]

@dataclass
class ChunkResult:
    """청크 처리 최종 결과"""
    success: bool
    chunk_id: str
    saved_count: int
    processing_time_ms: float
    phases_completed: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None

    def is_successful(self) -> bool:
        return self.success and self.error is None
```

---

## ⚡ 성능 최적화 전략

### 1. 조기 종료 패턴 (Early Exit)

```python
async def execute_chunk_pipeline(self, chunk_info, collection_state):
    # 🚀 최적화 1: 완전 겹침 시 API 호출 생략
    execution_plan = await self._phase1_prepare_execution(chunk_info)
    if execution_plan.should_skip_api_call:
        self.logger.info(f"⚡ 완전 겹침으로 API 호출 생략: {chunk_info.chunk_id}")
        return self._create_skip_result(execution_plan, chunk_info)

    # 🚀 최적화 2: 빈 응답 시 즉시 종료
    api_response = await self._phase2_fetch_data(chunk_info, execution_plan)
    if api_response.requires_early_exit:
        self.logger.info(f"⚡ 빈 응답으로 조기 종료: {chunk_info.chunk_id}")
        return self._handle_early_exit(api_response, chunk_info)
```

### 2. 메모리 스트리밍 처리

```python
async def _process_large_dataset(self, raw_data: List[Dict]) -> AsyncGenerator[Dict, None]:
    """
    🚀 대용량 데이터 스트림 처리
    - 메모리에 모든 데이터를 올리지 않음
    - 배치 단위로 처리하여 메모리 효율성 확보
    """

    BATCH_SIZE = 100  # 배치 크기

    for i in range(0, len(raw_data), BATCH_SIZE):
        batch = raw_data[i:i + BATCH_SIZE]

        # 배치 처리
        processed_batch = await self._process_candle_batch(batch)

        # 즉시 yield하여 메모리 해제
        for candle in processed_batch:
            yield candle
```

### 3. 계산 결과 캐싱

```python
from functools import lru_cache

class ChunkProcessor:
    @lru_cache(maxsize=256)
    def _calculate_timeframe_metadata(self, timeframe: str) -> Dict[str, Any]:
        """
        🚀 반복 계산 캐싱
        - 타임프레임별 메타데이터는 불변이므로 캐시 적용
        - 계산 오버헤드 제거
        """
        return {
            'delta': TimeUtils.get_timeframe_delta(timeframe),
            'format': TimeUtils.get_timeframe_format(timeframe),
            'api_method': self._get_api_method_for_timeframe(timeframe)
        }

    def _invalidate_cache(self):
        """필요시 캐시 무효화"""
        self._calculate_timeframe_metadata.cache_clear()
```

### 4. 비동기 배치 처리

```python
import asyncio

async def _parallel_validation(self, data_chunks: List[List[Dict]]) -> List[bool]:
    """
    🚀 병렬 데이터 검증
    - 독립적인 검증 작업을 병렬 처리
    - I/O 바운드 작업 효율성 극대화
    """

    # 병렬 검증 태스크 생성
    validation_tasks = [
        self._validate_chunk_data(chunk)
        for chunk in data_chunks
    ]

    # 모든 검증을 병렬로 실행
    results = await asyncio.gather(*validation_tasks, return_exceptions=True)

    # 예외 처리
    return [
        result if not isinstance(result, Exception) else False
        for result in results
    ]
```

---

## 🔄 CandleDataProvider와의 분리 전략

### 분리 인터페이스 설계

```python
class CandleDataProvider:
    """
    수집 조정자로 역할 변경

    남은 책임:
    - 전체 수집 프로세스 조정
    - Collection 상태 관리
    - 수집 계획 수립
    - 최종 결과 조회
    """

    def __init__(self,
                 repository: CandleRepositoryInterface,
                 upbit_client: UpbitPublicClient,
                 overlap_analyzer: OverlapAnalyzer,
                 chunk_size: int = 200,
                 enable_empty_candle_processing: bool = True):

        # 기존 초기화는 그대로 유지
        self.repository = repository
        self.upbit_client = upbit_client
        self.overlap_analyzer = overlap_analyzer

        # 🆕 ChunkProcessor 의존성 주입
        self.chunk_processor = ChunkProcessor(
            overlap_analyzer=overlap_analyzer,
            upbit_client=upbit_client,
            repository=repository,
            empty_candle_detector_factory=self._get_empty_candle_detector
        )

    async def mark_chunk_completed(self, request_id: str) -> bool:
        """
        ✨ 개선된 청크 완료 처리 - ChunkProcessor에 위임

        기존 복잡한 로직을 ChunkProcessor로 위임하여 단순화
        """

        if request_id not in self.active_collections:
            raise ValueError(f"알 수 없는 요청 ID: {request_id}")

        collection_state = self.active_collections[request_id]
        current_chunk = collection_state.current_chunk

        if current_chunk is None:
            raise ValueError("처리 중인 청크가 없습니다")

        self.logger.info(f"청크 처리 시작: {current_chunk.chunk_id}")

        try:
            # 🚀 핵심 변경: ChunkProcessor에 위임
            chunk_result = await self.chunk_processor.execute_chunk_pipeline(
                current_chunk, collection_state
            )

            # 결과 처리 및 상태 업데이트
            self._process_chunk_result(collection_state, chunk_result)

            # 수집 완료 확인
            if self._is_collection_complete(collection_state):
                collection_state.is_completed = True
                collection_state.current_chunk = None
                self.logger.info(f"전체 수집 완료: {request_id}")
                return True

            # 다음 청크 준비
            self._prepare_next_chunk(collection_state,
                                   collection_state.request_info.get_request_type())
            return False

        except Exception as e:
            self.logger.error(f"청크 처리 실패: {current_chunk.chunk_id}, 오류: {e}")
            raise

    def _process_chunk_result(self,
                             collection_state: CollectionState,
                             chunk_result: ChunkResult):
        """청크 처리 결과를 CollectionState에 반영"""

        if chunk_result.is_successful():
            # 성공적인 청크 완료 처리
            completed_chunk = collection_state.current_chunk
            completed_chunk.status = "completed"
            collection_state.completed_chunks.append(completed_chunk)

            # 카운팅 업데이트 (기존 로직 유지)
            collection_state.total_collected += completed_chunk.count

            self.logger.info(f"청크 완료: {completed_chunk.chunk_id}, "
                           f"저장: {chunk_result.saved_count}개, "
                           f"누적: {collection_state.total_collected}/{collection_state.total_requested}")
        else:
            # 실패 처리
            collection_state.current_chunk.status = "failed"
            collection_state.error_message = str(chunk_result.error)
            raise chunk_result.error
```

### 점진적 분리 로드맵

#### Phase 1: ChunkProcessor 클래스 생성 (1주차)

```python
# 1. 새로운 클래스 생성 (기존 코드는 유지)
class ChunkProcessor:
    # 새로운 메서드들 구현
    pass

# 2. CandleDataProvider에 ChunkProcessor 주입
class CandleDataProvider:
    def __init__(self, ...):
        self.chunk_processor = ChunkProcessor(...)  # 추가
        # 기존 코드는 그대로 유지
```

#### Phase 2: 메서드 이주 (2주차)

```python
# 3. 기존 메서드들을 ChunkProcessor로 복사
# 4. CandleDataProvider에서 ChunkProcessor 메서드 호출
async def mark_chunk_completed(self, request_id: str):
    # 기존 로직 유지 + ChunkProcessor 호출 추가
    chunk_result = await self.chunk_processor.execute_chunk_pipeline(...)
    # 기존 후처리 로직 유지
```

#### Phase 3: 기존 메서드 제거 (3주차)

```python
# 5. 모든 테스트 통과 확인 후 기존 메서드들 제거
# 6. 코드 정리 및 최적화 적용
```

---

## 🧪 테스트 전략

### 단위 테스트 구조

```python
class TestChunkProcessor:
    """ChunkProcessor 전용 테스트"""

    @pytest.fixture
    def chunk_processor(self):
        """테스트용 ChunkProcessor 인스턴스"""
        return ChunkProcessor(
            overlap_analyzer=Mock(),
            upbit_client=Mock(),
            repository=Mock(),
            empty_candle_detector_factory=Mock(),
        )

    async def test_execute_chunk_pipeline_success(self, chunk_processor):
        """정상적인 청크 처리 파이프라인 테스트"""

        # Given
        chunk_info = create_test_chunk_info()
        collection_state = create_test_collection_state()

        # When
        result = await chunk_processor.execute_chunk_pipeline(chunk_info, collection_state)

        # Then
        assert result.is_successful()
        assert result.saved_count > 0

    async def test_phase1_prepare_execution_with_complete_overlap(self, chunk_processor):
        """완전 겹침 상황에서의 실행 준비 테스트"""

        # Given: 완전 겹침 상황 설정
        chunk_info = create_chunk_info_with_complete_overlap()

        # When
        execution_plan = await chunk_processor._phase1_prepare_execution(chunk_info)

        # Then
        assert execution_plan.should_skip_api_call is True
        assert execution_plan.strategy == 'skip_complete_overlap'

    async def test_phase2_fetch_data_with_rate_limit(self, chunk_processor):
        """Rate Limit 상황에서의 데이터 수집 테스트"""
        # Rate Limit 관련 테스트 로직
        pass

    async def test_phase3_process_data_with_gaps(self, chunk_processor):
        """Gap이 있는 데이터 처리 테스트"""
        # 빈 캔들 처리 관련 테스트 로직
        pass

    async def test_phase4_persist_data_with_storage_failure(self, chunk_processor):
        """저장 실패 상황 테스트"""
        # 저장 실패 복구 로직 테스트
        pass
```

### 성능 테스트

```python
class TestChunkProcessorPerformance:
    """성능 최적화 검증 테스트"""

    async def test_memory_usage_optimization(self):
        """메모리 사용량 최적화 검증"""

        # 대용량 데이터로 테스트
        large_dataset = create_large_test_dataset(10000)

        initial_memory = get_memory_usage()

        # 청크 처리 실행
        await chunk_processor.execute_chunk_pipeline(...)

        final_memory = get_memory_usage()

        # 메모리 증가량이 임계값 이하인지 확인
        memory_increase = final_memory - initial_memory
        assert memory_increase < MEMORY_THRESHOLD

    async def test_api_call_optimization(self):
        """API 호출 최적화 검증"""

        # 겹침 상황에서 API 호출 수 확인
        with patch.object(upbit_client, 'get_candles_minutes') as mock_api:
            await chunk_processor.execute_chunk_pipeline(...)

            # 예상보다 적은 API 호출 확인
            assert mock_api.call_count < expected_calls
```

### 통합 테스트

```python
class TestChunkProcessorIntegration:
    """CandleDataProvider와의 통합 테스트"""

    async def test_integration_with_candle_data_provider(self):
        """실제 CandleDataProvider와의 연동 테스트"""

        provider = CandleDataProvider(...)

        # 기존 get_candles 메서드 동작 검증
        candles = await provider.get_candles('KRW-BTC', '1m', count=100)

        assert len(candles) == 100
        # 기존 동작과 동일한 결과 확인
```

---

## 📈 성능 모니터링

### 내장 성능 추적기

```python
class PerformanceTracker:
    """청크 처리 성능 추적"""

    def __init__(self):
        self.metrics = {}
        self.logger = create_component_logger("PerformanceTracker")

    @contextmanager
    def measure_chunk_execution(self, chunk_id: str):
        """전체 청크 실행 시간 측정"""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            self.metrics[f"{chunk_id}_total"] = execution_time
            self.logger.info(f"⏱️ 청크 실행 시간: {chunk_id} = {execution_time:.3f}초")

    @contextmanager
    def measure_phase(self, phase_name: str):
        """개별 Phase 시간 측정"""
        start_time = time.time()
        try:
            yield
        finally:
            phase_time = time.time() - start_time
            self.metrics[f"phase_{phase_name}"] = phase_time
            self.logger.debug(f"📊 Phase 시간: {phase_name} = {phase_time:.3f}초")

    def get_performance_report(self) -> Dict[str, float]:
        """성능 리포트 생성"""
        return {
            'avg_total_time': np.mean([v for k, v in self.metrics.items() if '_total' in k]),
            'avg_preparation_time': np.mean([v for k, v in self.metrics.items() if 'phase_preparation' in k]),
            'avg_api_fetch_time': np.mean([v for k, v in self.metrics.items() if 'phase_api_fetch' in k]),
            'avg_processing_time': np.mean([v for k, v in self.metrics.items() if 'phase_data_processing' in k]),
            'avg_storage_time': np.mean([v for k, v in self.metrics.items() if 'phase_data_storage' in k]),
        }
```

### 성능 알림 시스템

```python
class PerformanceAlertSystem:
    """성능 임계값 모니터링"""

    def __init__(self, thresholds: Dict[str, float]):
        self.thresholds = thresholds
        self.logger = create_component_logger("PerformanceAlert")

    def check_performance_thresholds(self, metrics: Dict[str, float]):
        """성능 임계값 체크 및 알림"""

        for metric_name, value in metrics.items():
            threshold = self.thresholds.get(metric_name)

            if threshold and value > threshold:
                self.logger.warning(f"🚨 성능 임계값 초과: {metric_name} = {value:.3f}초 (임계값: {threshold:.3f}초)")

                # 필요시 추가 알림 로직 (Slack, 이메일 등)
                self._send_performance_alert(metric_name, value, threshold)
```

---

## 📝 구현 로드맵

### Week 1: ChunkProcessor 기본 구조 구현
- [ ] ChunkProcessor 클래스 생성
- [ ] 4단계 파이프라인 메인 메서드 구현
- [ ] 데이터 모델 (ExecutionPlan, ApiResponse 등) 구현
- [ ] 기본 단위 테스트 작성

### Week 2: Phase 1-2 구현 (준비 & 수집)
- [ ] `_phase1_prepare_execution` 구현
- [ ] `_analyze_data_overlap` 구현
- [ ] `_phase2_fetch_data` 구현
- [ ] `_call_upbit_api` 구현 (기존 로직 이주)
- [ ] 조기 종료 로직 구현

### Week 3: Phase 3-4 구현 (처리 & 저장)
- [ ] `_phase3_process_data` 구현
- [ ] `_detect_and_fill_gaps` 구현 (기존 로직 이주)
- [ ] `_phase4_persist_data` 구현
- [ ] 성능 최적화 로직 적용

### Week 4: CandleDataProvider 통합
- [ ] CandleDataProvider에 ChunkProcessor 주입
- [ ] `mark_chunk_completed` 메서드 개선
- [ ] 기존 메서드들과의 호환성 확보
- [ ] 통합 테스트 실행

### Week 5: 성능 최적화 & 마무리
- [ ] 성능 모니터링 시스템 구현
- [ ] 메모리 최적화 적용
- [ ] 캐싱 로직 구현
- [ ] 문서화 완료

### Week 6: 테스트 & 검증
- [ ] 전체 테스트 스위트 실행
- [ ] 성능 벤치마크 측정
- [ ] 기존 기능 회귀 테스트
- [ ] 프로덕션 배포 준비

---

## 🎯 예상 성과

### 코드 품질 개선
- **복잡도 감소**: CandleDataProvider 1,200줄 → 800줄 (33% 감소)
- **책임 분리**: 단일 책임 원칙 준수로 유지보수성 향상
- **테스트 커버리지**: 70% → 90% (단위 테스트 용이성 확보)

### 성능 개선
- **메모리 사용량**: 조기 종료 및 스트리밍으로 20% 절약
- **API 효율성**: 겹침 분석 최적화로 15% 호출 감소
- **처리 속도**: 병렬 처리 및 캐싱으로 10% 향상

### 개발 생산성 향상
- **디버깅 용이성**: 단계별 로깅으로 문제 지점 빠른 파악
- **기능 확장성**: 새로운 처리 로직 추가가 용이함
- **테스트 효율성**: 개별 Phase 단위 테스트로 정밀한 검증

---

## 🚀 결론

이 리팩터링을 통해 다음과 같은 핵심 목표를 달성할 수 있습니다:

1. **명확한 책임 분리**: CandleDataProvider는 조정자, ChunkProcessor는 실행자
2. **직관적인 메서드명**: 기능과 동작이 명확히 표현되는 메서드명 적용
3. **성능 최적화**: 조기 종료, 메모리 효율성, 캐싱을 통한 성능 향상
4. **기존 호환성 유지**: 현재 로직과 기능 구조를 그대로 보존
5. **테스트 용이성**: 각 단계별 독립적인 단위 테스트 가능

**최종적으로 더 깔끔하고, 더 빠르고, 더 테스트하기 쉬운 캔들 처리 시스템을 구축할 수 있습니다.** 🎯

---

> **Next Steps**: 이 설계서를 바탕으로 실제 구현을 진행하며, 각 단계별로 테스트를 통해 검증해나가겠습니다.
