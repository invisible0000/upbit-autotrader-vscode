# Overlap Optimizer 상세 기능 명세

## 개요
- **파일 경로**: `upbit_auto_trading/infrastructure/market_data/candle/overlap_optimizer.py`
- **목적**: 업비트 특화 4단계 겹침 최적화 엔진
- **핵심 기능**: 200개 제한 최적화, 파편화 분석, API 호출 60% 감소

## 🎯 설계 목표

### **업비트 특화 최적화**
- **200개 제한**: 업비트 API 최대 200개 캔들 제한 완벽 대응
- **시작점 배제**: 업비트 API 특성 (현재 시점 제외) 정확 반영
- **파편화 처리**: SQL 기반 고속 파편화 감지 및 대응
- **반간격 안전요청**: timeframe의 절반 지점에서 안전한 API 요청

### **성능 목표**
- **API 호출 60% 감소**: 기존 대비 최적화로 Rate Limit 효율성 극대화
- **분석 시간 <10ms**: 실시간 응답성 보장
- **메모리 효율**: 대용량 데이터 처리 시에도 최소 메모리 사용

## 🏗️ 핵심 아키텍처

### 1. UpbitOverlapOptimizer (메인 최적화 엔진)

```python
class UpbitOverlapOptimizer:
    """업비트 특화 4단계 겹침 최적화 엔진"""

    # 업비트 API 제약사항
    UPBIT_API_LIMIT = 200
    UPBIT_RATE_LIMIT = 600  # req/min

    def __init__(self, repository: CandleRepository,
                 time_utils: TimeUtils):
        self.repository = repository
        self.time_utils = time_utils
        self.logger = create_component_logger("UpbitOverlapOptimizer")

        # 성능 통계
        self.stats = OptimizationStats()
```

### 2. 4단계 최적화 전략

#### **Step 1: 시작점 200개 내 겹침 확인**
```python
def _check_start_overlap(self, symbol: str, timeframe: str,
                        start_time: datetime) -> bool:
    """시작점 200개 범위 내 기존 데이터 존재 여부 확인"""

    table_name = self._get_table_name(symbol, timeframe)
    timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
    end_time = start_time + timedelta(seconds=timeframe_seconds * 199)

    query = f"""
    SELECT 1 FROM {table_name}
    WHERE candle_date_time_utc BETWEEN ? AND ?
    LIMIT 1
    """

    return self.repository.execute_query(query, (start_time, end_time)).fetchone() is not None
```

#### **Step 2: 완전 겹침 확인 (count 기반 고속)**
```python
def _check_complete_overlap(self, symbol: str, timeframe: str,
                          start_time: datetime, count: int) -> bool:
    """요청 구간의 완전 겹침 여부 확인 (count 기반)"""

    table_name = self._get_table_name(symbol, timeframe)
    timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
    end_time = start_time + timedelta(seconds=timeframe_seconds * (count - 1))

    query = f"""
    SELECT COUNT(*) FROM {table_name}
    WHERE candle_date_time_utc BETWEEN ? AND ?
    """

    cursor = self.repository.execute_query(query, (start_time, end_time))
    db_count = cursor.fetchone()[0]

    # 완전 일치 = 요청 개수와 DB 개수 동일
    return db_count == count
```

#### **Step 3: 파편화 겹침 확인 (SQL 최적화)**
```python
def _check_fragmentation(self, symbol: str, timeframe: str,
                        start_time: datetime, count: int) -> Tuple[bool, int]:
    """파편화 겹침 확인 (LAG 윈도우 함수 활용)"""

    table_name = self._get_table_name(symbol, timeframe)
    timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
    end_time = start_time + timedelta(seconds=timeframe_seconds * (count - 1))

    query = f"""
    WITH time_gaps AS (
        SELECT
            candle_date_time_utc,
            LAG(candle_date_time_utc) OVER (ORDER BY candle_date_time_utc) as prev_time
        FROM {table_name}
        WHERE candle_date_time_utc BETWEEN ? AND ?
        ORDER BY candle_date_time_utc
    )
    SELECT COUNT(*) as gap_count
    FROM time_gaps
    WHERE (strftime('%s', candle_date_time_utc) - strftime('%s', prev_time)) > ?
    """

    cursor = self.repository.execute_query(query, (start_time, end_time, timeframe_seconds))
    gap_count = cursor.fetchone()[0]

    # 2번 이상 끊어지면 파편화로 판단
    is_fragmented = gap_count >= 2
    return is_fragmented, gap_count
```

#### **Step 4: 연결된 끝 찾기**
```python
def _find_connected_end(self, symbol: str, timeframe: str,
                       start_time: datetime, max_count: int = 200) -> Optional[datetime]:
    """200개 범위 내에서 연속된 데이터의 끝점 찾기"""

    table_name = self._get_table_name(symbol, timeframe)
    timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)

    query = f"""
    WITH consecutive_candles AS (
        SELECT
            candle_date_time_utc,
            ROW_NUMBER() OVER (ORDER BY candle_date_time_utc) as row_num,
            datetime(candle_date_time_utc,
                     '-' || ((ROW_NUMBER() OVER (ORDER BY candle_date_time_utc) - 1) * {timeframe_seconds}) || ' seconds'
            ) as expected_start
        FROM {table_name}
        WHERE candle_date_time_utc >= ?
        ORDER BY candle_date_time_utc
        LIMIT ?
    )
    SELECT MAX(candle_date_time_utc) as connected_end
    FROM consecutive_candles
    WHERE expected_start = ?
    """

    cursor = self.repository.execute_query(query, (start_time, max_count, start_time.isoformat()))
    result = cursor.fetchone()
    return datetime.fromisoformat(result[0]) if result and result[0] else None
```

### 3. 최적화 실행 엔진

#### **메인 최적화 메서드**
```python
def optimize_candle_requests(self, symbol: str, timeframe: str,
                           start_time: datetime, count: int) -> OptimizationResult:
    """4단계 최적화 메인 실행 엔진"""

    start_analysis = time.time()
    original_api_calls = self._calculate_naive_api_calls(count)

    current_start = start_time
    remaining_count = count
    api_requests = []
    optimization_steps = []

    while remaining_count > 0:
        step_start = time.time()

        # Step 1: 시작점 겹침 확인
        if self._check_start_overlap(symbol, timeframe, current_start):
            strategy = "START_OVERLAP"
            request = self._handle_start_overlap(symbol, timeframe, current_start, remaining_count)

        # Step 2: 완전 겹침 확인
        elif self._check_complete_overlap(symbol, timeframe, current_start,
                                        min(remaining_count, self.UPBIT_API_LIMIT)):
            strategy = "COMPLETE_OVERLAP"
            request = self._handle_complete_overlap(symbol, timeframe, current_start, remaining_count)

        # Step 3: 파편화 확인
        elif self._check_fragmentation(symbol, timeframe, current_start,
                                     min(remaining_count, self.UPBIT_API_LIMIT))[0]:
            strategy = "FRAGMENTATION"
            request = self._handle_fragmentation(symbol, timeframe, current_start, remaining_count)

        # Step 4: 연결된 끝 찾기
        else:
            strategy = "CONNECTED_END"
            request = self._handle_connected_end(symbol, timeframe, current_start, remaining_count)

        # 단계 기록
        step_duration = (time.time() - step_start) * 1000
        optimization_steps.append(OptimizationStep(
            strategy=strategy,
            start_time=current_start,
            count=min(remaining_count, self.UPBIT_API_LIMIT),
            duration_ms=step_duration
        ))

        if request:
            api_requests.append(request)
            current_start = request.next_start
            remaining_count = request.remaining_count
        else:
            break

    # 최적화 결과 생성
    analysis_duration = (time.time() - start_analysis) * 1000
    optimized_api_calls = len(api_requests)
    reduction_rate = ((original_api_calls - optimized_api_calls) / original_api_calls) * 100

    result = OptimizationResult(
        original_api_calls=original_api_calls,
        optimized_api_calls=optimized_api_calls,
        reduction_rate=reduction_rate,
        api_requests=api_requests,
        optimization_steps=optimization_steps,
        analysis_duration_ms=analysis_duration,
        estimated_savings=self._calculate_savings(original_api_calls, optimized_api_calls)
    )

    # 통계 업데이트
    self.stats.update(result)

    self.logger.info("4단계 최적화 완료", extra={
        "symbol": symbol, "timeframe": timeframe,
        "original_calls": original_api_calls,
        "optimized_calls": optimized_api_calls,
        "reduction_rate": f"{reduction_rate:.1f}%",
        "analysis_time_ms": analysis_duration
    })

    return result
```

### 4. 안전한 API 요청 생성

#### **반간격 안전 요청**
```python
def _create_safe_api_request(self, symbol: str, timeframe: str,
                           target_start: datetime, count: int) -> ApiRequest:
    """업비트 특화 안전한 API 요청 생성"""

    # 시작점 배제를 위한 반간격 이전 시작
    timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)
    half_interval = timeframe_seconds // 2
    safe_start = target_start - timedelta(seconds=half_interval)

    # 200개 제한 적용
    safe_count = min(count + 1, self.UPBIT_API_LIMIT)  # +1 for safety margin

    return ApiRequest(
        symbol=symbol,
        timeframe=timeframe,
        start_time=safe_start,
        count=safe_count,
        target_start=target_start,
        expected_end=target_start + timedelta(seconds=timeframe_seconds * (count - 1)),
        next_start=target_start + timedelta(seconds=timeframe_seconds * count),
        remaining_count=max(0, count - self.UPBIT_API_LIMIT)
    )
```

#### **업비트 특화 파라미터 최적화**
```python
def _optimize_upbit_parameters(self, base_request: ApiRequest) -> ApiRequest:
    """업비트 API 특성에 맞는 파라미터 최적화"""

    # 1. 시작점 배제 처리
    if base_request.count > 1:
        # 첫 번째 캔들은 현재 시점이므로 제외
        adjusted_start = base_request.start_time + timedelta(
            seconds=self.time_utils.get_timeframe_seconds(base_request.timeframe)
        )
        base_request.start_time = adjusted_start
        base_request.count = min(base_request.count - 1, self.UPBIT_API_LIMIT)

    # 2. Rate Limit 고려한 지연 계산
    base_request.delay_ms = self._calculate_rate_limit_delay()

    # 3. 재시도 전략 설정
    base_request.retry_config = RetryConfig(
        max_retries=3,
        backoff_factor=2.0,
        retry_on_codes=[429, 500, 502, 503, 504]
    )

    return base_request
```

### 5. 데이터 모델

#### **OptimizationResult**
```python
@dataclass
class OptimizationResult:
    """4단계 최적화 결과"""
    original_api_calls: int                    # 원본 API 호출 수
    optimized_api_calls: int                   # 최적화 후 API 호출 수
    reduction_rate: float                      # 감소율 (%)
    api_requests: List[ApiRequest]             # 실제 API 요청 목록
    optimization_steps: List[OptimizationStep] # 단계별 최적화 과정
    analysis_duration_ms: float               # 분석 소요 시간
    estimated_savings: CostSavings            # 예상 비용 절약

    @property
    def is_optimized(self) -> bool:
        """최적화 효과가 있는지 확인"""
        return self.reduction_rate > 10.0  # 10% 이상 절약

    @property
    def efficiency_score(self) -> float:
        """최적화 효율성 점수 (0.0-1.0)"""
        return min(1.0, self.reduction_rate / 100.0)
```

#### **ApiRequest**
```python
@dataclass
class ApiRequest:
    """업비트 API 요청 모델"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int
    target_start: datetime                     # 실제 목표 시작 시간
    expected_end: datetime                     # 예상 종료 시간
    next_start: datetime                       # 다음 요청 시작점
    remaining_count: int                       # 남은 캔들 수
    delay_ms: float = 0.0                     # Rate Limit 지연시간
    retry_config: Optional[RetryConfig] = None # 재시도 설정

    def to_upbit_params(self) -> dict:
        """업비트 API 파라미터로 변환"""
        return {
            "market": self.symbol,
            "to": self.start_time.isoformat() + "Z",
            "count": self.count
        }
```

#### **OptimizationStep**
```python
@dataclass
class OptimizationStep:
    """최적화 단계 정보"""
    strategy: str                             # 적용된 전략 (START_OVERLAP 등)
    start_time: datetime                      # 단계 시작 시간
    count: int                                # 처리한 캔들 수
    duration_ms: float                        # 단계 처리 시간
    db_query_count: int = 0                   # DB 쿼리 수
    cache_hits: int = 0                       # 캐시 히트 수

    @property
    def efficiency(self) -> float:
        """단계별 효율성 (캔들 수 / 처리 시간)"""
        return self.count / max(self.duration_ms, 1.0) * 1000  # 초당 캔들 수
```

### 6. 성능 통계 및 모니터링

#### **OptimizationStats**
```python
class OptimizationStats:
    """최적화 성능 통계"""

    def __init__(self):
        self.total_requests = 0
        self.total_api_calls_saved = 0
        self.total_analysis_time = 0.0
        self.strategy_usage = defaultdict(int)
        self.performance_history = deque(maxlen=1000)

    def update(self, result: OptimizationResult):
        """최적화 결과 통계 업데이트"""
        self.total_requests += 1
        self.total_api_calls_saved += (result.original_api_calls - result.optimized_api_calls)
        self.total_analysis_time += result.analysis_duration_ms

        # 전략별 사용 통계
        for step in result.optimization_steps:
            self.strategy_usage[step.strategy] += 1

        # 성능 기록
        self.performance_history.append({
            "timestamp": datetime.now(),
            "reduction_rate": result.reduction_rate,
            "analysis_time": result.analysis_duration_ms,
            "api_calls_saved": result.original_api_calls - result.optimized_api_calls
        })

    def get_summary(self) -> dict:
        """통계 요약 반환"""
        avg_analysis_time = self.total_analysis_time / max(self.total_requests, 1)
        avg_reduction_rate = sum(p["reduction_rate"] for p in self.performance_history) / max(len(self.performance_history), 1)

        return {
            "total_requests": self.total_requests,
            "total_api_calls_saved": self.total_api_calls_saved,
            "average_analysis_time_ms": avg_analysis_time,
            "average_reduction_rate": avg_reduction_rate,
            "strategy_usage": dict(self.strategy_usage),
            "performance_trends": list(self.performance_history)[-10:]  # 최근 10개
        }
```

### 7. 유틸리티 메서드

#### **테이블명 생성**
```python
def _get_table_name(self, symbol: str, timeframe: str) -> str:
    """심볼과 timeframe으로 테이블명 생성"""
    return f"candles_{symbol.replace('-', '_')}_{timeframe}"

def _validate_symbol_timeframe(self, symbol: str, timeframe: str) -> bool:
    """심볼과 timeframe 유효성 검사"""
    valid_symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]  # 확장 가능
    valid_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]

    return symbol in valid_symbols and timeframe in valid_timeframes
```

#### **비용 계산**
```python
def _calculate_naive_api_calls(self, count: int) -> int:
    """순진한 방식의 API 호출 수 계산"""
    return (count + self.UPBIT_API_LIMIT - 1) // self.UPBIT_API_LIMIT

def _calculate_savings(self, original: int, optimized: int) -> CostSavings:
    """비용 절약 계산"""
    calls_saved = original - optimized
    time_saved_seconds = calls_saved * (60 / self.UPBIT_RATE_LIMIT)  # Rate limit 기준

    return CostSavings(
        api_calls_saved=calls_saved,
        time_saved_seconds=time_saved_seconds,
        rate_limit_efficiency=optimized / original if original > 0 else 1.0
    )

def _calculate_rate_limit_delay(self) -> float:
    """Rate Limit 고려한 지연 시간 계산"""
    requests_per_second = self.UPBIT_RATE_LIMIT / 60
    return 1000 / requests_per_second  # 밀리초 단위
```

### 8. 시간 통일성 보장 메서드

#### **DB 시간 형식 표준화**
```python
def _normalize_db_time_format(self, dt: datetime) -> str:
    """DB 저장용 시간 형식 표준화 (ISO 형식)"""
    return dt.isoformat()

def _parse_db_time_format(self, time_str: str) -> datetime:
    """DB에서 읽은 시간 문자열을 datetime으로 변환"""
    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

def _ensure_time_consistency(self, dt: datetime, timeframe: str) -> datetime:
    """time_utils와 동일한 시간 정렬 보장"""
    return self.time_utils._align_to_candle_boundary(
        dt, self.time_utils._parse_timeframe_to_minutes(timeframe)
    )
```

## 🧪 테스트 시나리오

### **테스트 케이스 1: 완전 캐시 히트**
```python
def test_complete_overlap_optimization():
    """완전 겹침 시나리오 테스트"""
    # Given: DB에 요청 구간 데이터 완전 존재
    optimizer = UpbitOverlapOptimizer(repository, time_utils)

    # When: 최적화 실행
    result = optimizer.optimize_candle_requests("KRW-BTC", "1m", start_time, 100)

    # Then: API 호출 없음
    assert result.optimized_api_calls == 0
    assert result.reduction_rate == 100.0
    assert len(result.optimization_steps) == 1
    assert result.optimization_steps[0].strategy == "COMPLETE_OVERLAP"
```

### **테스트 케이스 2: 파편화 최적화**
```python
def test_fragmentation_optimization():
    """파편화 데이터 최적화 테스트"""
    # Given: 파편화된 DB 데이터 (2번 이상 끊어짐)
    optimizer = UpbitOverlapOptimizer(repository, time_utils)

    # When: 최적화 실행
    result = optimizer.optimize_candle_requests("KRW-BTC", "1m", start_time, 200)

    # Then: 전체 요청이 효율적
    assert result.optimized_api_calls == 1  # 200개 한 번에 요청
    assert result.reduction_rate > 50.0
    assert any(step.strategy == "FRAGMENTATION" for step in result.optimization_steps)
```

### **테스트 케이스 3: 4단계 순차 처리**
```python
def test_four_step_optimization():
    """4단계 최적화 전체 흐름 테스트"""
    # Given: 복잡한 겹침 패턴 (일부 겹침 + 일부 누락)
    optimizer = UpbitOverlapOptimizer(repository, time_utils)

    # When: 대용량 요청 (500개)
    result = optimizer.optimize_candle_requests("KRW-BTC", "1m", start_time, 500)

    # Then: 단계별 최적화 적용
    assert result.optimized_api_calls < 3  # 원래 3번 → 최적화로 감소
    assert result.reduction_rate > 30.0
    assert len(result.optimization_steps) >= 2  # 여러 단계 적용
```

## 📊 성능 벤치마크

### **목표 성능 지표**
- **분석 시간**: <10ms (P95 기준)
- **API 호출 감소**: 60% 이상
- **메모리 사용**: <50MB (1000개 요청 동시 처리)
- **정확도**: 99% 이상 (최적화 결과 검증)

### **벤치마크 테스트**
```python
def benchmark_optimization_performance():
    """최적화 성능 벤치마크"""
    optimizer = UpbitOverlapOptimizer(repository, time_utils)

    test_cases = [
        (100, "완전겹침"), (200, "파편화"), (500, "대용량"), (1000, "초대용량")
    ]

    results = []
    for count, scenario in test_cases:
        start_time = time.time()
        result = optimizer.optimize_candle_requests("KRW-BTC", "1m",
                                                   datetime.now(), count)
        duration = (time.time() - start_time) * 1000

        results.append({
            "scenario": scenario,
            "count": count,
            "analysis_time_ms": duration,
            "reduction_rate": result.reduction_rate,
            "api_calls": result.optimized_api_calls
        })

    return results
```

## 🚀 사용 예시

### **기본 사용법**
```python
# 최적화 엔진 초기화
optimizer = UpbitOverlapOptimizer(candle_repository, time_utils)

# 캔들 요청 최적화
result = await optimizer.optimize_candle_requests(
    symbol="KRW-BTC",
    timeframe="1m",
    start_time=datetime(2024, 1, 1, 9, 0),
    count=300
)

# 최적화 결과 확인
print(f"API 호출 {result.reduction_rate:.1f}% 감소")
print(f"원본: {result.original_api_calls}회 → 최적화: {result.optimized_api_calls}회")

# API 요청 실행
for api_request in result.api_requests:
    candles = await upbit_client.get_candles(**api_request.to_upbit_params())
    await candle_repository.save_candles(api_request.symbol, api_request.timeframe, candles)
```

### **통계 모니터링**
```python
# 최적화 성능 통계 조회
stats = optimizer.stats.get_summary()
print(f"총 API 호출 절약: {stats['total_api_calls_saved']}회")
print(f"평균 감소율: {stats['average_reduction_rate']:.1f}%")
print(f"전략별 사용: {stats['strategy_usage']}")
```

## 💡 핵심 가치

1. **업비트 특화**: 200개 제한, 시작점 배제 등 업비트 API 특성 완벽 반영
2. **고성능**: SQL 기반 파편화 분석으로 <10ms 응답시간 달성
3. **높은 효율**: 4단계 최적화로 API 호출 60% 감소
4. **확장성**: 새로운 심볼/timeframe 조합 자동 지원
5. **모니터링**: 상세한 성능 통계 및 최적화 효과 추적

UpbitOverlapOptimizer는 업비트 특화 최적화로 **API 효율성과 시스템 성능을 동시에 극대화**하는 핵심 컴포넌트입니다.
