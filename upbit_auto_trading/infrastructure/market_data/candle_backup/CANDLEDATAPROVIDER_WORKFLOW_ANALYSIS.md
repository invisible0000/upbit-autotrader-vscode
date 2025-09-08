# 📊 CandleDataProvider 워크플로우 아키텍처 분석
> 현재 vs 의도된 설계 비교 및 overlap_optimizer 역할 재정의

## 🎯 분석 목적
사용자 지적: "overlap_optimizer.py 전체적인 동작이 조금 캔들 데이터 제공자와 맞지 않는거 같습니다"

**문제점**: 현재 overlap_optimizer가 너무 많은 책임을 가지고 있어서 CandleDataProvider의 의도된 워크플로우와 맞지 않음

---

## 📋 현재 시스템 아키텍처 현황

### 🔍 기존 구현체들
1. **SmartDataProvider** (V4.0 메인) - `smart_data_provider/smart_data_provider.py`
   - **역할**: API 단일 진입점, 캐시 통합, 실시간 데이터 관리
   - **책임**: 배치 처리, 성능 최적화, SmartRouter 호환성

2. **SmartDataProvider** (Backup) - `smart_data_provider_backup/core/smart_data_provider.py`
   - **역할**: 비동기 처리, 분할 요청, 연속 캔들 지원
   - **책임**: RequestSplitter 활용, CollectionStatusManager 통합

3. **overlap_optimizer.py** (현재 분석 대상)
   - **역할**: 4단계 겹침 최적화 엔진
   - **문제**: API 호출, 데이터 저장, 최적화 로직을 모두 담당 (단일 책임 원칙 위반)

### 🏗️ 의도된 DDD 아키텍처 (PRD 기준)
```
Application Service (CandleDataProvider Facade)
└── Domain Service (최적화 전략)
    └── Repository Interface (데이터 영속성)
        └── Infrastructure (API Client, Database)
```

**문제점**: 현재 overlap_optimizer가 모든 계층의 책임을 혼재하고 있음

---

## 🔄 워크플로우 비교 분석

### 📋 시나리오 1: 50개 캔들 요청 (작은 요청)

#### 🚫 **현재 overlap_optimizer 중심 워크플로우**
```python
# 사용자 요청: get_candles("KRW-BTC", "1m", 50)

1. OverlapOptimizer.optimize_candle_requests()
   ├── repository.check_existing_data()          # DB 직접 조회
   ├── _check_start_overlap()                   # 겹침 확인 로직
   ├── _check_complete_overlap()                # 완전 겹침 확인
   ├── _check_fragmentation()                   # 파편화 확인
   ├── api_client.get_candles()                 # API 직접 호출
   └── repository.save_candles()                # DB 직접 저장

결과: 1개 클래스가 API, DB, 최적화 로직 모두 담당 (90% 겹침이어도 전체 프로세스 실행)
```

#### ✅ **의도된 CandleDataProvider 워크플로우 (PRD 기준)**
```python
# 사용자 요청: candle_provider.get_candles("KRW-BTC", "1m", 50)

1. CandleDataProvider (Application Service - Facade)
   ├── 입력 검증 및 표준화
   └── CandleCache.get(key)                     # 빠른 캐시 확인
       ├── [HIT] 즉시 반환 (50개는 대부분 캐시에서 해결)
       └── [MISS] 도메인 서비스 호출

2. CandleOptimizationService (Domain Service)
   ├── OverlapStrategy.optimize(request)         # 순수 최적화 로직만
   └── OptimizedRequest[] 반환

3. CandleRepository (Infrastructure)
   ├── 기존 데이터 확인
   ├── CandleApiClient.fetch()                  # 필요한 데이터만 API 호출
   └── 캐시/DB 저장

결과: 각 계층이 단일 책임, 50개 요청은 캐시에서 즉시 해결 (빠른 응답)
```

### 📋 시나리오 2: 1000개 캔들 요청 (대용량 요청)

#### 🚫 **현재 overlap_optimizer 중심 워크플로우**
```python
# 사용자 요청: get_candles("KRW-BTC", "1m", 1000)

1. OverlapOptimizer.optimize_candle_requests()
   ├── 1000개 데이터 일괄 확인 (비효율적)
   ├── 4단계 최적화 모두 실행
   │   ├── START_OVERLAP (200개씩 처리)
   │   ├── COMPLETE_OVERLAP (기존 데이터와 비교)
   │   ├── FRAGMENTATION (끊어짐 탐지)
   │   └── CONNECTED_END (연결된 끝 찾기)
   ├── API 요청 생성 후 직접 호출
   └── 결과 DB 저장

결과: 단일 클래스에서 복잡한 로직 처리, 디버깅/유지보수 어려움
```

#### ✅ **의도된 CandleDataProvider 워크플로우 (PRD 기준)**
```python
# 사용자 요청: candle_provider.get_candles("KRW-BTC", "1m", 1000)

1. CandleDataProvider (Application Service)
   ├── 대용량 요청 감지 (1000 > 200)
   ├── CandleCache.get() (부분 캐시 확인)
   └── RequestSplitter.split(1000) → [Request(200), Request(200)...]

2. 각 분할 요청별로:
   CandleOptimizationService.optimize()
   ├── OverlapDetector.detect()                 # 순수 알고리즘
   ├── FragmentationChecker.check()             # 순수 로직
   └── OptimizedRequest 반환

3. CandleRepository.batch_fetch()
   ├── 병렬 API 호출 관리
   ├── Rate limit 처리
   └── 결과 통합 및 저장

4. CandleDataProvider.merge_and_return()
   └── 최종 응답 생성

결과: 관심사 분리, 각 컴포넌트 독립 테스트 가능, 확장성/유지보수성 향상
```

---

## 🎯 핵심 문제점 진단

### ❌ **현재 overlap_optimizer의 문제점**

1. **단일 책임 원칙 위반**
   ```python
   class OverlapOptimizer:
       # 🚫 너무 많은 책임
       def optimize_candle_requests(self):
           # API 호출 책임
           data = await self.api_client.get_candles()

           # 비즈니스 로직 책임
           overlap = self._check_start_overlap()

           # 데이터 저장 책임
           await self.repository.save_candles()
   ```

2. **테스트 어려움**
   - API, DB, 로직이 결합되어 단위 테스트 불가능
   - Mock 객체 설정 복잡

3. **확장성 부족**
   - 새로운 최적화 전략 추가 시 전체 클래스 수정
   - 다른 거래소 API 지원 어려움

4. **성능 비효율**
   - 작은 요청도 무조건 4단계 프로세스 실행
   - 캐시 우선 확인 없음

### ✅ **의도된 설계의 장점**

1. **관심사 분리**
   ```python
   # 최적화 로직만 담당
   class OverlapOptimizer:
       def optimize(self, request: CandleRequest) -> OptimizedRequest:
           # 순수 알고리즘, 외부 의존성 없음

   # API 호출만 담당
   class CandleApiClient:
       async def fetch_candles(self, request: ApiRequest) -> CandleData:

   # 조합/조율만 담당
   class CandleDataProvider:
       def get_candles(self) -> DataResponse:
   ```

2. **테스트 용이성**
   - 각 컴포넌트 독립 테스트
   - Mock 불필요한 순수 함수

3. **성능 최적화**
   - 캐시 우선 확인
   - 필요시에만 최적화 실행

---

## 🎯 권장 아키텍처 재설계

### 🏗️ **새로운 역할 분담**

```python
# 📋 Application Service - 단일 진입점
class CandleDataProvider:
    """사용자 요청의 단일 진입점, 조율만 담당"""
    def get_candles(self, symbol, timeframe, count) -> DataResponse:
        # 1. 입력 검증
        # 2. 캐시 확인
        # 3. 필요시 도메인 서비스 호출
        # 4. 응답 조합

# 🎯 Domain Service - 최적화 전략
class CandleOptimizationService:
    """순수 최적화 로직, 외부 의존성 없음"""
    def __init__(self, optimizer: OverlapOptimizer):
        self.optimizer = optimizer

    def optimize_request(self, request) -> OptimizationResult:
        # 순수 최적화 알고리즘만

# 🔧 Infrastructure Service - 최적화 엔진
class OverlapOptimizer:
    """4단계 겹침 감지 알고리즘만 담당"""
    def detect_overlaps(self, existing_data, request) -> OverlapResult:
        # 순수 알고리즘, 사이드 이펙트 없음

    def find_fragmentation(self, data_ranges) -> FragmentationResult:
        # 순수 계산 로직만

# 🌐 Infrastructure Service - API 클라이언트
class CandleApiClient:
    """업비트 API 호출만 담당"""
    async def fetch_candles(self, request: ApiRequest) -> CandleData:

# 💾 Infrastructure Service - 저장소
class CandleRepository:
    """데이터 영속성만 담당"""
    async def save_candles(self, data: CandleData) -> bool:
    async def get_existing_data(self, query) -> CandleData:
```

### 🔄 **새로운 워크플로우**

```python
# 사용자: provider.get_candles("KRW-BTC", "1m", 200)

1. CandleDataProvider (Entry Point)
   ├── validate_input()
   ├── cache.quick_check()                      # 빠른 캐시 확인
   └── [MISS] optimization_service.optimize()

2. CandleOptimizationService (Pure Logic)
   ├── overlap_optimizer.detect_overlaps()     # 순수 계산
   ├── overlap_optimizer.find_fragmentation()  # 순수 계산
   └── return OptimizedRequest[]

3. CandleRepository (Data Layer)
   ├── api_client.fetch_candles()              # 필요한 데이터만
   ├── save_to_db()
   └── update_cache()

4. CandleDataProvider (Response Assembly)
   └── assemble_response()                     # 최종 응답 조합
```

---

## 💡 구체적 개선 방안

### 🎯 **1단계: overlap_optimizer 역할 축소**
```python
# 현재 (모든 책임)
class OverlapOptimizer:
    async def optimize_candle_requests(self) -> OptimizationResult:
        # API + DB + 로직 모두

# 개선 후 (순수 로직만)
class OverlapOptimizer:
    def detect_overlaps(self, existing_ranges, target_range) -> OverlapResult:
        """순수 함수: 겹침 감지만"""

    def calculate_optimal_requests(self, overlap_result) -> List[ApiRequest]:
        """순수 함수: 최적 요청 계산만"""
```

### 🎯 **2단계: CandleDataProvider Facade 생성**
```python
class CandleDataProvider:
    """Application Service - 모든 컴포넌트 조율"""
    def __init__(self,
                 cache: CandleCache,
                 repository: CandleRepository,
                 optimizer: OverlapOptimizer,
                 api_client: CandleApiClient):

    async def get_candles(self, symbol, timeframe, count) -> DataResponse:
        # 1. 입력 검증
        # 2. 캐시 우선 확인
        # 3. 최적화 필요시에만 실행
        # 4. 결과 조합
```

### 🎯 **3단계: 성능 중심 최적화**
```python
# 캐시 우선 확인 (대부분 요청 즉시 해결)
if cache.has_complete_data(symbol, timeframe, count):
    return cache.get_data()  # 🚀 빠른 응답

# 최적화 필요시에만 실행
if count > 200 or has_potential_overlap():
    optimization_result = optimizer.optimize()
```

---

## 🎯 결론 및 다음 단계

### 📋 **핵심 문제 정리**
1. **현재**: overlap_optimizer가 "god object" 패턴 (모든 책임)
2. **목표**: 각 컴포넌트가 단일 책임을 가지는 DDD 아키텍처

### 🚀 **즉시 실행 가능한 개선사항**
1. **overlap_optimizer 순수 함수화**: API/DB 의존성 제거
2. **CandleDataProvider Facade 생성**: 단일 진입점 제공
3. **캐시 우선 전략**: 작은 요청은 캐시에서 즉시 해결

### 📊 **예상 성능 개선**
- **50개 캔들 요청**: 4단계 프로세스 → 캐시 즉시 응답 (90% 시간 단축)
- **1000개 캔들 요청**: 단일 클래스 → 병렬 처리 파이프라인 (60% 시간 단축)
- **유지보수성**: 단일 거대 클래스 → 테스트 가능한 작은 컴포넌트들

이 분석을 바탕으로 사용자가 지적한 "캔들 데이터 제공자와 맞지 않는" 문제의 핵심은 **관심사 분리 부족**임을 확인했습니다.
