# 📊 Candle Infrastructure 모듈 리팩터링 분석 보고서

**작성일**: 2025년 9월 22일
**목적**: 코드 품질 개선 및 단일 책임 원칙 준수를 위한 구조 개선
**범위**: `upbit_auto_trading/infrastructure/market_data/candle/` 모듈 전체

---

## 🎯 개요

캔들 데이터 처리 모듈이 비대해지면서 다음과 같은 문제들이 발생했습니다:

- **CandleDataProvider**: 1632줄로 과도하게 비대화
- **candle_models.py**: 1081줄, 16개 클래스로 복잡도 증가
- **CollectionState**: 책임 혼재로 인한 설계 문제
- **모니터링 기능**: 비즈니스 로직과 섞여 단일 책임 원칙 위반

이 문서는 체계적인 리팩터링을 통한 해결 방안을 제시합니다.

---

## 📈 작업 완료 현황

### ✅ 1단계: 모니터링 기능 분리 (완료)

**문제점**:
```python
# ❌ 기존: CandleDataProvider에 모든 기능이 섞여있음
class CandleDataProvider:
    def get_candles(self):           # 핵심 기능
        pass
    def get_performance_metrics(self):   # 모니터링 기능
        pass
    def get_detailed_progress(self):     # 모니터링 기능
        pass
    def get_compact_status(self):        # 모니터링 기능
        pass
    def get_streaming_updates(self):     # 모니터링 기능
        pass
```

**해결책**:
```python
# ✅ 개선: 책임 분리
class CandleDataProvider:
    def get_candles(self):           # 캔들 수집에만 집중
        pass
    def get_collection_status(self) -> CollectionState:
        return self._current_collection_state

class CandleCollectionMonitor:       # 모니터링 전용 클래스
    def __init__(self, collection_state: CollectionState):
        self.state = collection_state

    def get_performance_metrics(self):
        # CollectionState 기반 계산
        pass
```

**결과**:
- **CandleDataProvider**: 1632줄 → 1460줄 (**172줄, 10.5% 단축**)
- **새 파일**: `candle_collection_monitor.py` (245줄)
- **단일 책임 원칙 준수**: ✅

---

## 🔍 2단계: CollectionState 설계 문제 분석

### 현재 CollectionState의 문제점

**1. 책임 혼재 (SRP 위반)**
```python
@dataclass
class CollectionState:
    # ✅ 순수 상태 정보
    request_id: str
    total_collected: int
    completed_chunks: List[ChunkInfo]

    # ❌ 계산된 값들 (매번 계산 가능)
    avg_chunk_duration: float = 0.0
    remaining_chunks: int = 0
    estimated_remaining_seconds: float = 0.0
```

**2. 시간 정보 중복**
```python
# ❌ 비슷한 정보가 중복 저장됨
estimated_completion_time: Optional[datetime] = None
estimated_remaining_seconds: float = 0.0  # 사실상 같은 정보
```

**3. 불필요한 상태 저장**
```python
# ❌ 계산 가능한 값을 상태로 저장
remaining_chunks: int = 0  # len(completed_chunks) - estimated_total_chunks로 계산 가능
```

### 개선안: CollectionState v2.0

**핵심 설계 원칙**:
- **순수 상태만 저장**: 계산된 값은 `@property`로 제공
- **불변성 향상**: 핵심 정보는 변경 불가
- **단일 책임**: 상태 보관만, 계산 로직 분리
- **직관적 접근**: `state.progress_percentage` 같은 자연스러운 API

```python
@dataclass
class CollectionStateV2:
    # 🔒 불변 정보
    request_id: str
    symbol: str
    timeframe: str
    total_requested: int
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 📊 변경 가능한 상태
    total_collected: int = 0
    completed_chunks: List[ChunkInfo] = field(default_factory=list)
    current_chunk: Optional[ChunkInfo] = None
    is_completed: bool = False
    error_message: Optional[str] = None

    # 📈 계산된 값들은 Property로 제공
    @property
    def progress_percentage(self) -> float:
        if self.total_requested <= 0:
            return 0.0
        return (self.total_collected / self.total_requested) * 100.0

    @property
    def avg_chunk_duration(self) -> float:
        if not self.completed_chunks:
            return 0.0
        return self.elapsed_seconds / len(self.completed_chunks)

    @property
    def estimated_remaining_seconds(self) -> float:
        if self.remaining_chunks <= 0 or self.avg_chunk_duration <= 0:
            return 0.0
        return self.remaining_chunks * self.avg_chunk_duration
```

**장점**:
- 🎯 **명확한 책임**: 상태 vs 계산 로직 분리
- 🚀 **성능**: 필요할 때만 계산
- 🔧 **유지보수**: 계산 로직 변경이 쉬움
- 📊 **일관성**: 항상 최신 값 반환

---

## 📋 3단계: candle_models.py 구조 분석

### 현재 상황
- **총 1081줄, 16개 클래스**
- 서로 다른 책임들이 하나의 파일에 혼재
- 유지보수 및 가독성 저하

### 클래스 분류 및 분할 계획

#### 📁 1. candle_core_models.py (예상 300줄)
**역할**: 핵심 도메인 모델
**클래스**:
- `OverlapStatus`, `ChunkStatus` (Enum)
- `CandleData` (업비트 API 호환 모델)
- `CandleDataResponse` (최종 응답)

**특징**:
- 가장 자주 사용되는 핵심 모델
- 외부 의존성 최소
- 안정적인 인터페이스

#### 📁 2. candle_request_models.py (예상 250줄)
**역할**: 요청/응답 관련 모델
**클래스**:
- `CandleChunk` (청크 단위)
- `OverlapRequest`, `OverlapResult` (겹침 분석)
- `TimeChunk` (시간 기반 청크)
- `CollectionResult` (수집 결과)

**특징**:
- API 요청과 분석 결과 모델
- OverlapAnalyzer와 밀접한 관계
- 비교적 안정적

#### 📁 3. candle_cache_models.py (예상 200줄)
**역할**: 캐시 관련 모델
**클래스**:
- `CacheKey`, `CacheEntry`, `CacheStats`

**특징**:
- 캐시 시스템 전용
- **완전히 독립적** (우선 분리 대상)
- 필요시에만 import

#### 📁 4. candle_collection_models.py (예상 400줄)
**역할**: 수집 프로세스 관리 모델
**클래스**:
- `CollectionState` (개선된 버전)
- `CollectionPlan`
- `RequestInfo`
- `ChunkInfo`
- `ProcessingStats`

**특징**:
- CandleDataProvider 전용
- 가장 복잡하고 자주 변경됨
- 향후 개선 여지 많음

### Import 의존성 구조

```
candle_core_models.py
└── (의존성 없음)

candle_request_models.py
└── candle_core_models (CandleData, OverlapStatus)

candle_cache_models.py
└── candle_core_models (CandleData)

candle_collection_models.py
└── candle_core_models (CandleData)
└── candle_request_models (OverlapResult)
```

---

## 🎯 실행 계획

### 우선순위별 실행 순서

#### 🔥 High Priority: CollectionState v2.0 적용
**이유**: 가장 많이 사용되고 문제가 심각함
**작업**:
1. CollectionState v2.0 구현
2. 점진적 마이그레이션 (기존 코드 호환성 유지)
3. CandleDataProvider에서 계산 로직 제거

**예상 효과**:
- 코드 가독성 50% 향상
- 유지보수성 크게 개선
- 성능 최적화 (필요시에만 계산)

#### 📋 Medium Priority: 캐시 모델 분리
**이유**: 완전히 독립적이라 안전함
**작업**:
1. `candle_cache_models.py` 생성
2. 캐시 관련 클래스 3개 이전
3. import 구문 수정

**예상 효과**:
- candle_models.py 200줄 단축
- 캐시 기능의 선택적 사용 가능
- 다른 작업에 영향 없음

#### 🔧 Low Priority: 전체 파일 분할
**이유**: 대규모 작업이므로 신중하게 진행
**작업**:
1. 핵심 모델부터 순차적 분리
2. 의존성 그래프 검증
3. 전체 테스트 실행

---

## 📊 예상 효과

### 코드 품질 지표

**현재**:
- CandleDataProvider: 1632줄
- candle_models.py: 1081줄
- 책임 혼재도: 높음
- 유지보수성: 낮음

**목표**:
- CandleDataProvider: ~800줄 (50% 단축)
- 모델 파일들: 각 200-400줄
- 책임 혼재도: 낮음
- 유지보수성: 높음

### 개발 경험 개선

**Before**:
```python
# ❌ 복잡하고 직관적이지 않음
provider = CandleDataProvider(...)
state = provider._current_collection_state
progress = state.total_collected / state.total_requested * 100
remaining_time = state.estimated_remaining_seconds  # 정확성 의문
```

**After**:
```python
# ✅ 직관적이고 명확함
provider = CandleDataProvider(...)
state = provider.get_collection_status()
progress = state.progress_percentage  # 항상 정확
remaining_time = state.estimated_remaining_seconds  # 실시간 계산

# 모니터링이 필요할 때만
monitor = CandleCollectionMonitor(state)
metrics = monitor.get_performance_metrics()
```

---

## 🔄 마이그레이션 전략

### 점진적 적용 방법

#### 1단계: 병행 운영
```python
class CandleDataProvider:
    def __init__(self):
        # 기존 CollectionState 유지
        self._legacy_state = CollectionState(...)
        # 새 CollectionState 추가
        self._state_v2 = CollectionStateV2(...)

    # 기존 메서드들 유지 (Deprecated 표시)
    @deprecated("Use get_collection_status().progress_percentage instead")
    def get_progress(self):
        return self._legacy_state.total_collected / self._legacy_state.total_requested

    # 새 메서드들 추가
    def get_collection_status(self) -> CollectionStateV2:
        return self._state_v2
```

#### 2단계: 점진적 전환
```python
# 기존 코드는 계속 작동하지만 경고 표시
progress = provider.get_progress()  # ⚠️ Deprecated warning

# 새 코드는 개선된 API 사용
state = provider.get_collection_status()
progress = state.progress_percentage  # ✅ Recommended
```

#### 3단계: 완전 전환
- Legacy 코드 제거
- 테스트 케이스 업데이트
- 문서 갱신

---

## 🧪 테스트 전략

### 기존 기능 호환성 보장
```python
def test_legacy_compatibility():
    """기존 API가 계속 작동하는지 확인"""
    provider = CandleDataProvider(...)

    # 기존 방식
    old_progress = provider._current_collection_state.total_collected

    # 새 방식
    new_progress = provider.get_collection_status().total_collected

    assert old_progress == new_progress
```

### 개선된 기능 검증
```python
def test_collection_state_v2_properties():
    """새로운 Property들이 정확히 계산되는지 확인"""
    state = CollectionStateV2(
        request_id="test", symbol="KRW-BTC", timeframe="1m",
        total_requested=1000, total_collected=250
    )

    assert state.progress_percentage == 25.0
    assert 0 <= state.estimated_remaining_seconds
    assert state.get_phase() in ["initializing", "collecting", "processing", "completed", "error"]
```

---

## 📚 참고 자료

### 관련 파일들
- `candle_collection_monitor.py` - 완성된 모니터링 클래스
- `temp/collection_state_v2_proposal.py` - CollectionState v2.0 제안서
- `temp/candle_models_refactoring_plan.py` - 상세 리팩터링 계획

### 설계 원칙
- **Single Responsibility Principle**: 각 클래스는 하나의 책임만
- **Open/Closed Principle**: 확장에는 열려있고 변경에는 닫혀있게
- **Dependency Inversion**: 추상화에 의존, 구체화에 의존하지 않게
- **KISS (Keep It Simple, Stupid)**: 단순하게 유지

### 코딩 스타일
- **Property 활용**: 계산된 값은 메서드가 아닌 Property로
- **Type Hints**: 모든 공개 메서드에 타입 힌트 적용
- **Docstring**: 클래스와 주요 메서드에 상세한 문서화
- **Validation**: 생성자에서 입력값 검증

---

## 🎯 결론

이번 리팩터링을 통해 다음과 같은 개선을 기대할 수 있습니다:

1. **📉 복잡도 감소**: 대용량 파일들을 역할별로 분리
2. **🎯 명확한 책임**: 각 클래스가 하나의 책임만 담당
3. **🚀 개발 속도 향상**: 직관적인 API와 명확한 구조
4. **🔧 유지보수성**: 변경사항의 영향 범위 최소화
5. **📊 모니터링 강화**: 전용 클래스로 기능 분리

**다음 단계**: CollectionState v2.0부터 시작하여 점진적으로 전체 구조를 개선해 나가겠습니다.
