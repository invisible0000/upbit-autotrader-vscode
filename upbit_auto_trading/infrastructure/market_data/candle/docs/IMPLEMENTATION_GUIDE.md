# 🛠️ Candle Infrastructure 구현 가이드

**대상**: 개발자
**목적**: 리팩터링 작업의 구체적인 구현 방법 제시
**연관 문서**: `REFACTORING_ANALYSIS_REPORT.md`

---

## 📋 Phase 0: 폴더 구조 개편 (NEW - 최우선)

### 현재 문제점

#### 문제 1: 파일 구조 혼재
```
candle/
├── candle_models.py (1081줄) - 너무 비대함
├── candle_data_provider.py
├── candle_collection_monitor.py
├── candle_cache.py
├── overlap_analyzer.py
├── empty_candle_detector.py
├── time_utils.py
└── docs/
```

**문제점**:
- 모든 파일이 한 폴더에 평면적으로 나열
- candle_models.py가 1081줄로 과도하게 비대화
- 기능별 그룹핑 부재로 코드 탐색 어려움
- import 구문이 길고 복잡함

#### 문제 2: 책임 혼재
- 모델, 제공자, 분석기, 유틸리티가 모두 같은 레벨에 존재
- 각 컴포넌트의 역할과 의존성이 명확하지 않음

### 현재 구현된 구조 (2025-09-22)

```
candle/
├── models/                    # 📊 데이터 모델 (✅ 완료)
│   ├── __init__.py
│   ├── candle_core_models.py      # CandleData, CandleDataResponse, Enum 등
│   ├── candle_request_models.py   # OverlapRequest, TimeChunk 등
│   ├── candle_cache_models.py     # CacheKey, CacheEntry 등
│   └── candle_collection_models.py # CollectionState, ChunkInfo 등
├── candle_data_provider.py   # 🔄 메인 데이터 제공자
├── candle_collection_monitor.py # � 모니터링 전용 클래스
├── overlap_analyzer.py        # 🔍 겹침 분석
├── empty_candle_detector.py   # 🔍 빈 캔들 처리
├── time_utils.py             # 🛠️ 시간 유틸리티
├── candle_cache.py           # 🛠️ 캐시 관리
├── candle_models.py          # 🔗 호환성 레이어
└── docs/                     # 📚 문서
```

**참고**: providers/, analyzers/, utils/ 폴더는 필요시 단계별로 추가 예정

### 개선 효과

#### 1. 명확한 책임 분리
```python
# Before (혼재된 import)
from .candle_models import CandleData, CacheKey, CollectionState, OverlapRequest

# After (역할별 import) - 현재 구현된 구조
from .models import CandleData, CollectionState, OverlapRequest
from .models.candle_cache_models import CacheKey
from . import candle_data_provider, overlap_analyzer  # 아직 폴더 분리 안됨
```

#### 2. 효율적인 import 구조
```python
# __init__.py를 통한 깔끔한 import
from upbit_auto_trading.infrastructure.market_data.candle import (
    CandleData,           # models/core_models.py
    CandleDataProvider,   # providers/candle_data_provider.py
    OverlapAnalyzer,      # analyzers/overlap_analyzer.py
)
```

#### 3. 확장성 향상
- 새로운 모델 추가시 적절한 models/ 하위 파일에만 추가
- 새로운 분석기 추가시 analyzers/ 폴더에만 영향
- 각 영역의 독립적 개발 가능

### 구현 단계

#### ✅ Step 0-1: 현재 구조 분석 (완료)
- [x] 기존 파일들의 역할과 의존성 파악 완료
- [x] 새로운 폴더 구조 설계 완료

#### ✅ Step 0-2: models/ 폴더 생성 (완료)
```python
# models/__init__.py
"""Candle Data Models - 캔들 데이터 관련 모델들

모든 데이터 구조와 DTO 클래스들을 포함합니다.
"""

# 핵심 모델 (가장 자주 사용)
from .candle_core_models import (
    CandleData,
    CandleDataResponse,
    OverlapStatus,
    ChunkStatus
)

# 요청/응답 모델
from .candle_request_models import (
    CandleChunk,
    OverlapRequest,
    OverlapResult,
    TimeChunk,
    CollectionResult
)

# 수집 프로세스 모델
from .candle_collection_models import (
    CollectionState,
    CollectionPlan,
    RequestInfo,
    ChunkInfo,
    ProcessingStats
)

# 캐시 모델 (선택적 import)
# from .cache_models import CacheKey, CacheEntry, CacheStats

__all__ = [
    # 핵심 모델
    'CandleData', 'CandleDataResponse', 'OverlapStatus', 'ChunkStatus',
    # 요청 모델
    'CandleChunk', 'OverlapRequest', 'OverlapResult', 'TimeChunk', 'CollectionResult',
    # 수집 모델
    'CollectionState', 'CollectionPlan', 'RequestInfo', 'ChunkInfo', 'ProcessingStats',
]
```

#### ✅ Step 0-3: candle_models.py 분할 (완료)
1. **candle_core_models.py**: CandleData, CandleDataResponse, OverlapStatus, ChunkStatus ✅
2. **candle_request_models.py**: OverlapRequest, TimeChunk, CollectionResult, RequestInfo ✅
3. **candle_cache_models.py**: CacheKey, CacheEntry, CacheStats ✅
4. **candle_collection_models.py**: CollectionState, ChunkInfo, ProcessingStats ✅

#### [ ] Step 0-4: 추가 폴더 정리 (필요시 진행)
1. **providers/**: candle_data_provider.py, candle_collection_monitor.py 이동 (보류)
2. **analyzers/**: overlap_analyzer.py, empty_candle_detector.py 이동 (보류)
3. **utils/**: time_utils.py, candle_cache.py 이동 (보류)

#### ✅ Step 0-5: models/__init__.py 파일 작성 (완료)
깔끔한 import 구조 구축 완료

#### ✅ Step 0-6: import 구문 업데이트 (완료)
전체 프로젝트의 import 구문을 새로운 models 구조에 맞게 업데이트 완료

#### ✅ Step 0-7: 테스트 및 검증 (완료)
- ✅ 모델 import 및 기본 기능 테스트 성공
- ✅ ChunkInfo.get_api_params() 메서드 누락 문제 해결
- ✅ 전체 캔들 모델 시스템 정상 작동 확인

---

## 📋 Task 1: CollectionState v2.0 구현

### 현재 문제점과 해결책

#### 문제 1: 계산된 값의 상태 저장
```python
# ❌ 현재: 계산된 값을 상태로 저장
class CollectionState:
    avg_chunk_duration: float = 0.0
    remaining_chunks: int = 0
    estimated_remaining_seconds: float = 0.0

    def update_stats(self):
        # 매번 수동으로 업데이트해야 함
        self.avg_chunk_duration = self.elapsed_seconds / len(self.completed_chunks)
        self.remaining_chunks = self.estimated_total_chunks - len(self.completed_chunks)
        # ... 복잡한 계산 로직
```

```python
# ✅ 개선: Property로 자동 계산
class CollectionStateV2:
    @property
    def avg_chunk_duration(self) -> float:
        if not self.completed_chunks:
            return 0.0
        return self.elapsed_seconds / len(self.completed_chunks)

    @property
    def remaining_chunks(self) -> int:
        return max(0, self.estimated_total_chunks - len(self.completed_chunks))
```

#### 문제 2: 시간 정보 중복
```python
# ❌ 현재: 중복된 시간 정보
estimated_completion_time: Optional[datetime] = None
estimated_remaining_seconds: float = 0.0

# ✅ 개선: 하나는 Property로 계산
@property
def estimated_completion_time(self) -> Optional[datetime]:
    if self.estimated_remaining_seconds <= 0:
        return None
    return datetime.now(timezone.utc) + timedelta(seconds=self.estimated_remaining_seconds)
```

### 구현 단계

#### Step 1: 새 클래스 정의
```python
# candle_models.py에 추가
@dataclass
class CollectionStateV2:
    """캔들 수집 상태 v2.0 - 순수 상태 중심 설계"""

    # 불변 정보 (생성 후 변경 안됨)
    request_id: str = field(repr=True)
    symbol: str = field(repr=True)
    timeframe: str = field(repr=True)
    total_requested: int = field(repr=True)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 변경 가능한 상태
    total_collected: int = 0
    completed_chunks: List[ChunkInfo] = field(default_factory=list)
    current_chunk: Optional[ChunkInfo] = None
    is_completed: bool = False
    error_message: Optional[str] = None
    last_candle_time: Optional[str] = None
    last_update_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # 계산된 값들은 모두 Property로
    @property
    def progress_percentage(self) -> float: ...

    @property
    def elapsed_seconds(self) -> float: ...

    # ... 기타 Property들
```

#### Step 2: 마이그레이션 헬퍼 구현
```python
def migrate_to_v2(old_state: CollectionState) -> CollectionStateV2:
    """기존 CollectionState를 v2로 변환"""
    return CollectionStateV2(
        request_id=old_state.request_id,
        symbol=old_state.symbol,
        timeframe=old_state.timeframe,
        total_requested=old_state.total_requested,
        start_time=old_state.start_time,
        total_collected=old_state.total_collected,
        completed_chunks=old_state.completed_chunks.copy(),
        current_chunk=old_state.current_chunk,
        is_completed=old_state.is_completed,
        error_message=old_state.error_message,
        last_candle_time=old_state.last_candle_time,
        last_update_time=old_state.last_update_time
    )
```

#### Step 3: CandleDataProvider 업데이트
```python
class CandleDataProvider:
    def __init__(self, ...):
        # 기존 상태 유지 (하위 호환성)
        self._legacy_state: Optional[CollectionState] = None
        # 새 상태 추가
        self._state_v2: Optional[CollectionStateV2] = None
        self._use_v2 = False  # 점진적 전환을 위한 플래그

    def get_collection_status_v2(self) -> CollectionStateV2:
        """새로운 CollectionState v2.0 반환"""
        return self._state_v2

    def enable_collection_state_v2(self, enable: bool = True):
        """CollectionState v2.0 사용 여부 설정"""
        self._use_v2 = enable
        if enable and self._legacy_state:
            self._state_v2 = migrate_to_v2(self._legacy_state)
```

---

## 📋 Task 2: 캐시 모델 분리

### 분리 대상 클래스들

```python
# candle_models.py에서 분리할 클래스들
class CacheKey: ...
class CacheEntry: ...
class CacheStats: ...
```

### 구현 단계

#### Step 1: 새 파일 생성
```python
# candle_cache_models.py
"""
Candle Cache Models - 캔들 데이터 캐시 관련 모델

분리 이유:
- 캐시 기능은 선택적 기능
- 완전히 독립적인 책임
- 다른 모델들과 의존성 없음
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

# 순환 import 방지를 위한 TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .candle_core_models import CandleData

@dataclass
class CacheKey:
    """캐시 키 구조화"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int

    def __post_init__(self):
        if not self.symbol:
            raise ValueError("심볼은 필수입니다")
        if self.count <= 0:
            raise ValueError("개수는 1 이상이어야 합니다")

    def to_string(self) -> str:
        return f"candles_{self.symbol}_{self.timeframe}_{self.start_time.isoformat()}_{self.count}"

# ... 나머지 캐시 관련 클래스들
```

#### Step 2: Import 구문 업데이트
```python
# 기존 코드에서 캐시 모델 사용하는 부분들 찾아서 업데이트
# Before
from .candle_models import CacheKey, CacheEntry, CacheStats

# After
from .candle_cache_models import CacheKey, CacheEntry, CacheStats
```

#### Step 3: 원본 파일에서 제거
```python
# candle_models.py에서 해당 클래스들과 관련 코드 제거
# - CacheKey 클래스 정의 제거
# - CacheEntry 클래스 정의 제거
# - CacheStats 클래스 정의 제거
```

---

## 📋 Task 3: CandleCollectionMonitor 완성

### 현재 누락된 기능들

#### 1. CollectionState 의존 기능들
```python
class CandleCollectionMonitor:
    def get_detailed_progress(self) -> Dict[str, Any]:
        # TODO: target_end 정보를 어떻게 가져올지 결정 필요
        # TODO: should_continue_collection 로직 처리 필요
```

#### 2. 해결 방법

**Option A: 추가 정보를 생성자에서 받기**
```python
class CandleCollectionMonitor:
    def __init__(
        self,
        collection_state: CollectionState,
        target_end: Optional[datetime] = None,
        continue_checker: Optional[Callable[[], Tuple[bool, List[str]]]] = None
    ):
        self.state = collection_state
        self.target_end = target_end
        self.continue_checker = continue_checker

    def get_detailed_progress(self) -> Dict[str, Any]:
        # 이제 target_end 사용 가능
        time_progress = None
        if self.target_end:
            # 시간 기반 진행률 계산 가능
            ...
```

**Option B: CollectionState를 확장**
```python
@dataclass
class CollectionStateV2:
    # 기존 필드들...

    # 새 필드 추가
    target_end: Optional[datetime] = None

    def should_continue_collection(self) -> Tuple[bool, List[str]]:
        """완료 조건 체크"""
        reasons = []

        if self.total_collected >= self.total_requested:
            reasons.append("count_reached")

        if self.target_end and self.last_candle_time:
            last_time = datetime.fromisoformat(self.last_candle_time.replace('Z', '+00:00'))
            if last_time <= self.target_end:
                reasons.append("time_reached")

        return len(reasons) == 0, reasons
```

### 권장 방법: Option B
CollectionState에 필요한 정보를 추가하는 것이 더 깔끔합니다.

---

## 📋 Task 4: 테스트 케이스 작성

### CollectionState v2.0 테스트

```python
# tests/infrastructure/market_data/candle/test_collection_state_v2.py
import pytest
from datetime import datetime, timezone, timedelta
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import CollectionStateV2, ChunkInfo

class TestCollectionStateV2:
    def test_progress_percentage_calculation(self):
        """진행률 계산이 정확한지 확인"""
        state = CollectionStateV2(
            request_id="test_001",
            symbol="KRW-BTC",
            timeframe="1m",
            total_requested=1000,
            total_collected=250
        )

        assert state.progress_percentage == 25.0

    def test_elapsed_seconds_calculation(self):
        """경과 시간 계산이 정확한지 확인"""
        start_time = datetime.now(timezone.utc) - timedelta(seconds=60)
        state = CollectionStateV2(
            request_id="test_002",
            symbol="KRW-BTC",
            timeframe="1m",
            total_requested=1000,
            start_time=start_time
        )

        # 약간의 오차 허용 (실행 시간 때문에)
        assert 59 <= state.elapsed_seconds <= 61

    def test_avg_chunk_duration_with_no_chunks(self):
        """청크가 없을 때 평균 처리 시간이 0인지 확인"""
        state = CollectionStateV2(
            request_id="test_003",
            symbol="KRW-BTC",
            timeframe="1m",
            total_requested=1000
        )

        assert state.avg_chunk_duration == 0.0

    def test_avg_chunk_duration_with_chunks(self):
        """청크가 있을 때 평균 처리 시간 계산"""
        start_time = datetime.now(timezone.utc) - timedelta(seconds=120)
        state = CollectionStateV2(
            request_id="test_004",
            symbol="KRW-BTC",
            timeframe="1m",
            total_requested=1000,
            start_time=start_time
        )

        # 2개 청크 추가 (시뮬레이션)
        chunk1 = ChunkInfo.create_chunk(0, "KRW-BTC", "1m", 200)
        chunk2 = ChunkInfo.create_chunk(1, "KRW-BTC", "1m", 200)
        state.completed_chunks = [chunk1, chunk2]

        # 120초 / 2청크 = 60초/청크
        assert state.avg_chunk_duration == 60.0

    def test_property_immutability(self):
        """Property들이 실시간으로 업데이트되는지 확인"""
        state = CollectionStateV2(
            request_id="test_005",
            symbol="KRW-BTC",
            timeframe="1m",
            total_requested=1000,
            total_collected=100
        )

        assert state.progress_percentage == 10.0

        # 상태 업데이트
        state.total_collected = 500

        # Property가 자동으로 업데이트됨
        assert state.progress_percentage == 50.0
```

### CandleCollectionMonitor 테스트

```python
# tests/infrastructure/market_data/candle/test_candle_collection_monitor.py
import pytest
from upbit_auto_trading.infrastructure.market_data.candle.candle_collection_monitor import CandleCollectionMonitor
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import CollectionStateV2

class TestCandleCollectionMonitor:
    def test_performance_metrics_basic(self):
        """기본 성능 지표 계산"""
        state = CollectionStateV2(
            request_id="test_monitor_001",
            symbol="KRW-BTC",
            timeframe="1m",
            total_requested=1000,
            total_collected=500
        )

        monitor = CandleCollectionMonitor(state)
        metrics = monitor.get_performance_metrics()

        assert 'throughput' in metrics
        assert 'efficiency' in metrics
        assert 'timing' in metrics
        assert metrics['throughput']['candles_per_second'] >= 0

    def test_real_time_stats(self):
        """실시간 통계 정보"""
        state = CollectionStateV2(
            request_id="test_monitor_002",
            symbol="KRW-BTC",
            timeframe="1m",
            total_requested=2000,
            total_collected=800
        )

        monitor = CandleCollectionMonitor(state)
        stats = monitor.get_real_time_stats()

        assert stats['progress']['percentage'] == 40.0
        assert stats['progress']['collected'] == 800
        assert stats['progress']['requested'] == 2000
        assert stats['status']['is_completed'] == False
        assert stats['status']['phase'] in ['initializing', 'collecting', 'processing', 'completed', 'error']
```

---

## 🔧 구현 체크리스트

### Phase 0: Models 폴더 구조 개편 (✅ 완료)
- [x] 현재 구조 분석 및 새 구조 설계
- [x] models/ 폴더 생성
- [x] candle_models.py 분석 및 클래스 분류
- [x] candle_core_models.py 생성 (CandleData, CandleDataResponse, Enum 등)
- [x] candle_request_models.py 생성 (OverlapRequest, TimeChunk 등)
- [x] candle_cache_models.py 생성 (CacheKey, CacheEntry 등)
- [x] candle_collection_models.py 생성 (CollectionState, ChunkInfo 등)
- [x] models/__init__.py 작성
- [x] 전체 프로젝트 import 구문 업데이트
- [x] 기존 candle_models.py → 호환성 레이어로 변경
- [x] 테스트 실행 및 검증 (ChunkInfo 메서드 누락 문제 해결)

### CollectionState v2.0
- [ ] 새 클래스 정의 완료
- [ ] Property 메서드들 구현
- [ ] 마이그레이션 헬퍼 작성
- [ ] CandleDataProvider 업데이트
- [ ] 하위 호환성 유지
- [ ] 테스트 케이스 작성
- [ ] 성능 벤치마크

### 캐시 모델 분리 (Phase 0에 통합됨)
- [x] models/candle_cache_models.py 생성 (Phase 0에서 처리)
- [ ] 클래스 이전 완료
- [ ] Import 구문 업데이트
- [ ] 원본 파일에서 제거
- [ ] 순환 import 방지 확인
- [ ] 테스트 케이스 유지

### CandleCollectionMonitor 완성
- [ ] 누락된 기능 구현
- [ ] CollectionState 확장 (필요시)
- [ ] 에러 처리 강화
- [ ] 문서화 완료
- [ ] 사용 예시 작성

---

## ⚠️ 주의사항

### 1. 순환 Import 방지
```python
# ❌ 위험: 순환 import 발생 가능
from .candle_models import CollectionState
from .candle_collection_monitor import CandleCollectionMonitor

# ✅ 안전: TYPE_CHECKING 사용
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .candle_models import CollectionState
```

### 2. 하위 호환성 유지
```python
# 기존 코드가 깨지지 않도록 점진적 전환
class CandleDataProvider:
    @deprecated("Use get_collection_status_v2() instead")
    def get_collection_status(self) -> CollectionState:
        """기존 메서드 유지 (Deprecated)"""
        return self._legacy_state

    def get_collection_status_v2(self) -> CollectionStateV2:
        """새로운 메서드"""
        return self._state_v2
```

### 3. 성능 고려사항
```python
# Property는 매번 계산되므로 복잡한 로직 주의
@property
def expensive_calculation(self) -> float:
    # 캐싱이 필요한 경우
    if not hasattr(self, '_cached_value'):
        self._cached_value = self._do_expensive_calculation()
    return self._cached_value

def invalidate_cache(self):
    """상태 변경시 캐시 무효화"""
    if hasattr(self, '_cached_value'):
        delattr(self, '_cached_value')
```

---

## 🎯 성공 기준

1. **기능적 요구사항**
   - [ ] 기존 모든 기능이 정상 동작
   - [ ] 새로운 API가 더 직관적
   - [ ] 성능 저하 없음

2. **코드 품질**
   - [ ] 각 클래스의 책임이 명확
   - [ ] 코드 중복 제거
   - [ ] 테스트 커버리지 90% 이상

3. **유지보수성**
   - [ ] 새로운 기능 추가가 쉬움
   - [ ] 버그 수정 범위가 제한적
   - [ ] 문서화가 충실

이 가이드를 따라 단계별로 구현하면 안전하고 효과적인 리팩터링이 가능할 것입니다.
