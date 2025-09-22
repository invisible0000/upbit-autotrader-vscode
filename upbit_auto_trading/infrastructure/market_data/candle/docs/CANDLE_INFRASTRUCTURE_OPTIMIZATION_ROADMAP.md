# 🚀 캔들 인프라 최적화 로드맵 v2.0

> **작성일**: 2025-09-22
> **목적**: ChunkInfo 통합 완료 후 성능 최적화 및 코드 정리
> **대상**: 캔들 수집 시스템 전반의 안정성, 성능, 확장성 강화
> **영향도**: 메모리 사용량 최적화, API 효율성 향상, 유지보수성 개선

## 🎯 **현재 상태 및 달성 목표**

### **완료된 핵심 통합 작업**
✅ **ChunkInfo 모델 통합**: OverlapResult 정보 흡수, 단일 set_overlap_info 인터페이스
✅ **CandleDataProvider 리팩터링**: ChunkInfo.get_effective_end_time 기반 로직으로 전환
✅ **테스트 검증**: 모든 ChunkInfo 관련 단위/통합 테스트 통과
✅ **수동 검증**: 실제 시나리오에서 새로운 모델 동작 확인

### **다음 단계 최적화 목표**
🎯 **성능 최적화**: 메모리 사용량 15% 감소, API 호출 효율성 5% 개선
🎯 **코드 정리**: Deprecated 필드/메서드 완전 제거, 코드 복잡도 20% 감소
🎯 **확장성 강화**: 멀티 청크 조합, 고급 캐싱, 예측 로딩 기능 추가
🎯 **모니터링 강화**: 실시간 성능 메트릭, 상세 디버깅 정보 제공

---

## 📋 **Phase 1: Deprecated 코드 정리 (우선도: 🔴 높음)**

### **1.1 CollectionState.last_candle_time 완전 제거**

#### **현재 상태**
```python
# candle_data_provider.py:208
last_candle_time: Optional[str] = None  # ⚠️ Deprecated: get_last_effective_time() 사용 권장
```

#### **작업 내용**
```python
# 1. 필드 제거
@dataclass
class CollectionState:
    # last_candle_time: Optional[str] = None  # 🗑️ 완전 제거

# 2. 기존 사용처를 get_last_effective_time()으로 대체
# _is_collection_complete(), _create_next_chunk_params() 등에서 사용하는 모든 지점 확인 및 대체
```

#### **영향도 분석**
- **메모리**: 각 CollectionState 인스턴스당 문자열 필드 제거
- **일관성**: 단일 정보 소스로 데이터 동기화 이슈 완전 해결
- **유지보수**: 중복 정보 관리 포인트 제거

### **1.2 ChunkInfo.connected_end 정리**

#### **현재 상태**
```python
# candle_models.py:286
connected_end: Optional[datetime] = None  # deprecated: partial_end 사용 권장
```

#### **작업 내용**
```python
# 1. 사용 현황 조사
grep -r "connected_end" upbit_auto_trading/infrastructure/market_data/candle/

# 2. partial_end로 마이그레이션 또는 완전 제거
# 3. 관련 테스트 업데이트
```

### **1.3 미사용 메서드 및 import 정리**

#### **작업 대상**
```bash
# 1. 미사용 import 정리
ruff check --select F401 upbit_auto_trading/infrastructure/market_data/candle/

# 2. 미사용 메서드 탐지
# _extract_last_candle_time_from_api_response 등 제거된 메서드 참조 확인

# 3. Dead code 제거
vulture upbit_auto_trading/infrastructure/market_data/candle/
```

---

## 📊 **Phase 2: 성능 및 메모리 최적화 (우선도: 🟡 중간)**

### **2.1 ChunkInfo 객체 메모리 최적화**

#### **현재 메모리 사용량 분석**
```python
# 각 ChunkInfo 인스턴스의 메모리 footprint 측정
def analyze_chunkinfo_memory():
    import sys
    chunk = ChunkInfo(chunk_id="test", symbol="KRW-BTC", timeframe="1m", planned_count=100)

    # 필드별 메모리 사용량 분석
    memory_usage = {}
    for field in chunk.__dataclass_fields__:
        value = getattr(chunk, field)
        memory_usage[field] = sys.getsizeof(value) if value else 0

    return memory_usage
```

#### **최적화 방안**
```python
# 1. __slots__ 적용으로 메모리 사용량 감소
@dataclass
class ChunkInfo:
    __slots__ = ['chunk_id', 'symbol', 'timeframe', ...]  # 모든 필드 명시

# 2. Optional 필드 지연 초기화
def __post_init__(self):
    # 필수 필드만 즉시 초기화, Optional 필드는 필요시 초기화
    if not hasattr(self, '_initialized_optionals'):
        self._initialized_optionals = set()

# 3. 문자열 interning으로 메모리 절약
symbol: str = field(default="", repr=False)
def __post_init__(self):
    self.symbol = sys.intern(self.symbol)  # 동일 symbol 재사용
```

### **2.2 CollectionState 성능 최적화**

#### **계산 속성 캐싱**
```python
from functools import lru_cache

class CollectionState:
    @property
    @lru_cache(maxsize=1)
    def get_last_effective_time_cached(self) -> Optional[str]:
        """캐시된 마지막 유효 시간 (completed_chunks 변경 시 캐시 무효화)"""
        return self.get_last_effective_time()

    def add_completed_chunk(self, chunk: ChunkInfo):
        """청크 추가 시 캐시 무효화"""
        self.completed_chunks.append(chunk)
        self.get_last_effective_time_cached.cache_clear()
```

### **2.3 API 호출 패턴 최적화**

#### **배치 처리 및 병렬화**
```python
# 1. 청크 생성 시 미리 예측 로딩
async def prefetch_next_chunks(self, state: CollectionState, lookahead: int = 2):
    """다음 청크들을 미리 준비하여 지연시간 감소"""
    if len(state.completed_chunks) >= 2:  # 패턴 분석 가능할 때
        predicted_params = self._predict_next_chunk_params(state, lookahead)
        # 백그라운드에서 겹침 분석 미리 수행

# 2. 동적 청크 크기 조정
def optimize_chunk_size(self, state: CollectionState) -> int:
    """API 응답 패턴 기반 최적 청크 크기 계산"""
    if len(state.completed_chunks) >= 3:
        avg_response_ratio = sum(chunk.api_response_count / chunk.api_request_count
                               for chunk in state.completed_chunks[-3:]) / 3
        # 응답 비율이 낮으면 청크 크기 증가, 높으면 유지
        return min(int(200 / avg_response_ratio), 500)
    return 200  # 기본값
```

---

## 🔧 **Phase 3: 확장성 및 기능 강화 (우선도: 🟢 낮음)**

### **3.1 CandleCache 멀티 청크 조합 기능**

#### **현재 TODO 항목**
```python
# candle_cache.py:188
# TODO: 향후 확장 - 여러 청크를 조합하여 완전 범위 구성 가능한지 확인
```

#### **구현 계획**
```python
class CandleCache:
    def get_combined_range_coverage(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> dict:
        """
        여러 청크 조합으로 요청 범위 커버리지 분석

        Returns:
            {
                'coverage_ratio': float,  # 0.0~1.0
                'missing_ranges': List[Tuple[datetime, datetime]],
                'available_chunks': List[str],  # chunk_id 리스트
                'combination_strategy': str  # 'full', 'partial', 'none'
            }
        """

    async def get_candles_from_combined_chunks(self, coverage_info: dict) -> List[CandleData]:
        """여러 청크를 조합해서 캔들 데이터 반환"""
        combined_candles = []
        for chunk_id in coverage_info['available_chunks']:
            chunk_candles = await self.get_chunk_candles(chunk_id)
            combined_candles.extend(chunk_candles)

        # 시간순 정렬 및 중복 제거
        return self._deduplicate_and_sort(combined_candles)
```

### **3.2 실시간 성능 모니터링 시스템**

#### **ChunkInfo 성능 메트릭 수집**
```python
@dataclass
class ChunkPerformanceMetrics:
    chunk_id: str

    # 시간 메트릭
    creation_time: datetime
    overlap_analysis_duration: float
    api_call_duration: Optional[float]
    processing_duration: Optional[float]
    total_duration: float

    # 메모리 메트릭
    memory_usage_mb: float
    peak_memory_mb: float

    # API 효율성 메트릭
    api_request_count: int
    api_response_count: int
    cache_hit_ratio: float

    def to_monitoring_event(self) -> dict:
        """모니터링 시스템으로 전송할 이벤트 형태"""
        return {
            'event_type': 'chunk_performance',
            'chunk_id': self.chunk_id,
            'metrics': {
                'duration': {
                    'total': self.total_duration,
                    'overlap_analysis': self.overlap_analysis_duration,
                    'api_call': self.api_call_duration,
                    'processing': self.processing_duration
                },
                'efficiency': {
                    'cache_hit_ratio': self.cache_hit_ratio,
                    'api_efficiency': self.api_response_count / self.api_request_count,
                    'memory_efficiency': self.memory_usage_mb / max(self.api_response_count, 1)
                }
            }
        }
```

### **3.3 고급 예측 및 최적화 엔진**

#### **수집 패턴 학습 및 예측**
```python
class CollectionPatternAnalyzer:
    def __init__(self):
        self.pattern_history: List[CollectionState] = []
        self.optimization_rules: Dict[str, Callable] = {}

    def analyze_collection_pattern(self, state: CollectionState) -> dict:
        """수집 패턴 분석 및 최적화 제안"""
        return {
            'pattern_type': self._classify_pattern(state),
            'efficiency_score': self._calculate_efficiency_score(state),
            'optimization_suggestions': self._generate_optimizations(state),
            'predicted_completion_time': self._predict_completion(state)
        }

    def _classify_pattern(self, state: CollectionState) -> str:
        """수집 패턴 분류 (sequential, sparse, dense, mixed)"""
        if len(state.completed_chunks) < 3:
            return "insufficient_data"

        # 청크 간 시간 간격 분석
        time_gaps = []
        for i in range(1, len(state.completed_chunks)):
            prev_chunk = state.completed_chunks[i-1]
            curr_chunk = state.completed_chunks[i]

            prev_end = prev_chunk.get_effective_end_time()
            curr_start = curr_chunk.planned_start

            if prev_end and curr_start:
                gap = (curr_start - prev_end).total_seconds()
                time_gaps.append(gap)

        if not time_gaps:
            return "unknown"

        avg_gap = sum(time_gaps) / len(time_gaps)
        gap_variance = sum((gap - avg_gap) ** 2 for gap in time_gaps) / len(time_gaps)

        # 패턴 분류 로직
        if gap_variance < 60:  # 1분 미만 분산
            return "sequential"
        elif avg_gap > 3600:  # 평균 1시간 이상 간격
            return "sparse"
        elif avg_gap < 300:   # 평균 5분 미만 간격
            return "dense"
        else:
            return "mixed"
```

---

## 🧪 **Phase 4: 테스트 강화 및 검증 (우선도: 🟡 중간)**

### **4.1 성능 회귀 테스트 자동화**

#### **벤치마크 테스트 추가**
```python
# tests/performance/test_candle_performance_regression.py

import pytest
import time
from dataclasses import dataclass
from typing import List

@dataclass
class PerformanceBenchmark:
    test_name: str
    max_duration_seconds: float
    max_memory_mb: float
    min_cache_hit_ratio: float

class TestCandlePerformanceRegression:

    BENCHMARKS = [
        PerformanceBenchmark("chunk_creation", 0.1, 10, 0.0),
        PerformanceBenchmark("overlap_analysis", 0.5, 20, 0.8),
        PerformanceBenchmark("collection_1000_candles", 30.0, 100, 0.7),
        PerformanceBenchmark("memory_cleanup", 1.0, 50, 0.0),
    ]

    @pytest.mark.performance
    @pytest.mark.parametrize("benchmark", BENCHMARKS)
    async def test_performance_benchmark(self, benchmark: PerformanceBenchmark):
        """성능 기준 달성 여부 검증"""

        # 메모리 사용량 추적 시작
        import tracemalloc
        tracemalloc.start()

        start_time = time.perf_counter()

        # 벤치마크별 테스트 실행
        if benchmark.test_name == "chunk_creation":
            await self._test_chunk_creation_performance()
        elif benchmark.test_name == "overlap_analysis":
            await self._test_overlap_analysis_performance()
        elif benchmark.test_name == "collection_1000_candles":
            await self._test_large_collection_performance()

        duration = time.perf_counter() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024

        # 성능 기준 검증
        assert duration <= benchmark.max_duration_seconds, \
            f"성능 저하 감지: {duration:.2f}s > {benchmark.max_duration_seconds}s"

        assert peak_mb <= benchmark.max_memory_mb, \
            f"메모리 사용량 초과: {peak_mb:.2f}MB > {benchmark.max_memory_mb}MB"
```

### **4.2 Edge Case 및 스트레스 테스트**

#### **극한 상황 테스트 시나리오**
```python
class TestCandleEdgeCases:

    @pytest.mark.stress
    async def test_massive_chunk_collection(self):
        """대용량 청크 수집 안정성 테스트"""
        # 10,000개 청크로 스트레스 테스트

    @pytest.mark.edge_case
    async def test_complete_overlap_edge_cases(self):
        """COMPLETE_OVERLAP 엣지 케이스 테스트"""
        # db_end가 None인 경우
        # db_end와 api_response_end가 다른 경우
        # 시간 순서가 맞지 않는 경우

    @pytest.mark.edge_case
    async def test_memory_pressure_scenarios(self):
        """메모리 부족 상황 대응 테스트"""
        # 메모리 제한 환경에서 수집 동작 검증

    @pytest.mark.edge_case
    async def test_api_failure_recovery(self):
        """API 장애 상황 복구 테스트"""
        # 연속 API 실패 시 상태 관리
        # 부분 실패 후 재시도 로직
```

---

## 📈 **구현 우선순위 및 일정 계획**

### **Sprint 1: 코드 정리 및 안정성 (1주)**
```bash
Week 1:
├─ Day 1-2: CollectionState.last_candle_time 완전 제거
├─ Day 3: ChunkInfo.connected_end 정리
├─ Day 4: 미사용 코드 및 import 정리
└─ Day 5: 기본 성능 회귀 테스트 추가
```

### **Sprint 2: 성능 최적화 (1-2주)**
```bash
Week 2-3:
├─ Week 2: ChunkInfo 메모리 최적화 (__slots__, 지연 초기화)
├─ Week 3 Day 1-3: CollectionState 계산 속성 캐싱
└─ Week 3 Day 4-5: API 호출 패턴 최적화
```

### **Sprint 3: 확장 기능 (2주)**
```bash
Week 4-5:
├─ Week 4: CandleCache 멀티 청크 조합 기능
├─ Week 5 Day 1-3: 실시간 성능 모니터링 시스템
└─ Week 5 Day 4-5: 수집 패턴 분석 엔진 기초
```

### **Sprint 4: 테스트 및 검증 (1주)**
```bash
Week 6:
├─ Day 1-3: 스트레스 테스트 및 Edge Case 테스트 추가
├─ Day 4: 성능 벤치마크 자동화
└─ Day 5: 전체 시스템 검증 및 문서화
```

---

## 🎯 **성공 메트릭 및 검증 기준**

### **성능 목표**
- ✅ **메모리 사용량**: 현재 대비 15% 감소
- ✅ **API 호출 효율성**: 캐시 히트율 5% 개선
- ✅ **수집 완료 시간**: 대용량 수집 시 10% 단축
- ✅ **코드 복잡도**: Cyclomatic complexity 20% 감소

### **품질 목표**
- ✅ **테스트 커버리지**: 95% 이상 유지
- ✅ **성능 회귀 감지**: 자동화된 벤치마크 통과율 100%
- ✅ **메모리 누수**: 장시간 실행 시 메모리 증가율 < 1%/시간
- ✅ **API 장애 복구**: 99% 이상 자동 복구 성공율

### **확장성 목표**
- ✅ **멀티 청크 조합**: 80% 이상 케이스에서 성공적 조합
- ✅ **예측 정확도**: 완료 시간 예측 오차 < 10%
- ✅ **모니터링 커버리지**: 모든 주요 지표 실시간 수집
- ✅ **패턴 분류**: 90% 이상 정확한 패턴 식별

---

## 🔄 **구현 가이드라인**

### **코드 품질 기준**
```python
# 1. 모든 새로운 클래스/메서드에 타입 힌트 필수
def optimize_chunk_size(self, state: CollectionState) -> int:

# 2. Infrastructure 로깅 사용
logger = create_component_logger("CandleOptimizer")

# 3. 성능 크리티컬 구간에서 메트릭 수집
@performance_monitor("chunk_creation")
def create_chunk_info(...) -> ChunkInfo:

# 4. 모든 최적화에 대한 A/B 테스트 지원
@feature_flag("enable_chunk_size_optimization")
def get_optimized_chunk_size(...):
```

### **테스트 작성 기준**
```python
# 1. 성능 테스트에는 명확한 기준 설정
@pytest.mark.performance
@pytest.mark.timeout(30)  # 30초 내 완료
async def test_collection_performance():

# 2. Edge case 테스트에는 설명 주석 필수
@pytest.mark.edge_case
async def test_complete_overlap_with_none_db_end():
    """
    COMPLETE_OVERLAP 상태이지만 db_end가 None인 경우:
    - OverlapResult에서 db_end 정보를 제대로 못 가져온 경우
    - 이때 get_effective_end_time()는 다른 우선순위로 fallback해야 함
    """

# 3. 메모리 테스트는 정확한 측정
def test_memory_usage():
    import tracemalloc
    tracemalloc.start()
    # ... 테스트 실행
    current, peak = tracemalloc.get_traced_memory()
    assert peak < target_memory_bytes
```

### **롤백 및 안전장치**
```python
# 1. 기능 플래그로 점진적 활성화
FEATURE_FLAGS = {
    "enable_memory_optimization": False,  # 초기에는 비활성화
    "enable_chunk_size_optimization": False,
    "enable_pattern_prediction": False
}

# 2. 성능 모니터링으로 자동 롤백
class PerformanceGuard:
    def monitor_and_rollback_if_needed(self, metric_name: str, current_value: float):
        if current_value > self.thresholds[metric_name] * 1.2:  # 20% 성능 저하 시
            self.disable_optimization(metric_name)
            logger.warning(f"성능 저하로 인한 자동 롤백: {metric_name}")
```

---

## 🎉 **최종 목표 및 비전**

이 로드맵을 완료하면 다음과 같은 **차세대 캔들 수집 시스템**을 구축하게 됩니다:

### **🚀 고성능 시스템**
- **메모리 효율성**: 최적화된 객체 구조로 대용량 처리 지원
- **API 효율성**: 지능적 캐싱과 예측 로딩으로 최소 API 호출
- **처리 속도**: 병렬 처리와 배치 최적화로 빠른 수집 완료

### **🛡️ 안정적 시스템**
- **장애 복구**: 자동 재시도와 상태 복원으로 높은 가용성
- **메모리 안정성**: 메모리 누수 방지와 효율적 가비지 컬렉션
- **데이터 무결성**: 엄격한 검증과 모니터링으로 데이터 품질 보장

### **📈 확장 가능한 시스템**
- **적응적 최적화**: 사용 패턴 학습으로 자동 성능 조정
- **모듈화 구조**: 새로운 기능 추가가 용이한 아키텍처
- **실시간 모니터링**: 상세한 메트릭으로 지속적인 개선 지원

### **🧠 지능적 시스템**
- **패턴 인식**: 수집 패턴 자동 분석 및 최적화 제안
- **예측 능력**: 완료 시간과 리소스 사용량 정확한 예측
- **자가 최적화**: 운영 중 자동 성능 튜닝 및 문제 해결

**이 시스템은 업비트 자동매매의 핵심 인프라로서 안정적이고 효율적인 데이터 수집을 보장하며, 향후 더욱 고도화된 거래 전략의 기반이 될 것입니다.**
