# 📋 CandleDataProvider v4.0 - Infrastructure Service 상세 설계
> DDD Infrastructure Layer에서 서브시스템에 캔들 데이터 제공 서비스

## 🎯 **전체 시스템 구조 (DDD + API 요청 최적화)**
```
upbit_auto_trading/
├── domain/
│   └── repositories/
│       └── candle_repository_interface.py      # 🎯 Repository 인터페이스 (DDD)
├── infrastructure/
│   ├── database/
│   │   └── database_manager.py                 # ⚡ Connection Pooling + WAL 모드
│   ├── repositories/
│   │   └── sqlite_candle_repository.py         # 🔧 DDD 준수 구현체
│   └── market_data/candle/
│       ├── candle_data_provider.py             # 🏆 메인 Infrastructure Service
│       ├── rest_api_client.py                  # 📡 업비트 API 클라이언트
│       ├── candle_cache.py                     # ⚡ 고속 메모리 캐시 (60초 TTL)
│       ├── overlap_analyzer.py                 # 🎯 API 요청 최적화 (DB/API 혼합 전략)
│       ├── time_utils.py                       # ⏰ 시간 처리 유틸 (end_time 계산)
│       └── models.py                           # 📝 데이터 모델 통합
```

## 🎯 핵심 동작 원리

### 📋 **DDD Infrastructure Service 관점**
- **Infrastructure Service**: 서브시스템들이 import하여 사용하는 간편한 인터페이스
- **단일 진입점**: 모든 캔들 데이터 요청은 CandleDataProvider 통해서만
- **200개 청크 처리**: 업비트 API 제한에 맞춘 청크 단위 관리
- **겹침 최적화**: 기존 데이터와 중복 없는 효율적 수집

---

## 🏗️ **DDD Infrastructure Layer - 파일별 역할**

### 📋 **Domain Interface 의존성 (중요!)**
```python
# Domain Layer Interface (수정 필요)
from upbit_auto_trading.domain.repositories.candle_repository_interface import CandleRepositoryInterface

# Infrastructure가 Domain Interface를 구현
class SqliteCandleRepository(CandleRepositoryInterface):
    # Domain 인터페이스 구현...
```

### 📋 **candle_data_provider.py** (🏆 Infrastructure Service - 서브시스템 단일 진입점)
```python
class CandleDataProvider:
    """서브시스템들이 import하여 사용하는 캔들 데이터 Infrastructure Service"""

    # === 서브시스템 진입점 ===
    async def get_candles(
        symbol: str,
        timeframe: str,
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        inclusive_start: bool = True  # 🎯 사용자 제공 start_time 포함 처리
    ) -> CandleDataResponse:
        """
        캔들 데이터 조회 - 5가지 파라미터 조합 지원

        파라미터 조합 케이스:
        1. count만: 현재시간부터 역순 → start_time 자동생성 (inclusive_start 무관)
        2. start_time + count: 시작점부터 → inclusive_start 적용! (start_time 조정)
        3. start_time + end_time: 구간지정 → inclusive_start 적용! (start_time 조정)
        4. end_time만: 과거시점까지 → start_time 자동계산 (inclusive_start 무관)
        5. 파라미터 없음: 기본 200개 → 자동생성 (inclusive_start 무관)

        Args:
            inclusive_start: 사용자가 직접 제공한 start_time에만 적용
                           True: start_time 포함하도록 조정 (기본, 직관적)
                           False: API 네이티브 배제 방식 (고급 사용자용)

        시간 처리 원칙:
        - 사용자 제공 start_time (케이스 2,3): inclusive_start에 따라 조정 여부 결정
        - 시스템 자동 start_time (케이스 1,4,5): 조정 없음 (자연스러운 동작)
        - end_time: 사용자가 이미 포함을 기대하므로 어떠한 조정도 불필요
        - 미래 시간 요청: ValidationError (사용자 책임)
        """
        # 서브시스템의 단일 진입점 - 모든 파라미터 조합 지원
        # 1. 요청 검증 및 표준화 (count/start_time/end_time 조합 처리)
        # 2. 미래 시간 요청 검증 → ValidationError (사용자 책임)
        # 3. TimeUtils로 시간 계산 및 start_time 조정 처리
        # 4. 캐시 우선 확인 (완전 데이터 존재시 즉시 반환)
        # 5. 대량 요청시 200개 청크로 순차 수집
        # 6. target_end_time 도달시 수집 중단
        # 7. 최종 응답 반환

    def _adjust_start_time_for_api(self, start_time: datetime, timeframe: str, inclusive_start: bool, user_provided_start: bool) -> datetime:
        """업비트 API 시간 처리 - 사용자 제공 start_time에만 조정 적용"""
        if start_time is None or not user_provided_start or not inclusive_start:
            # 조정 불필요 케이스:
            # 1. start_time 없음
            # 2. 시스템 자동 생성 start_time (케이스 1,4,5)
            # 3. 사용자가 배제 모드 선택 (inclusive_start=False)
            return start_time

        # 사용자 제공 start_time + inclusive_start=True: 포함하도록 조정
        # 업비트 API는 start_time을 배제하므로, 시간상 과거로 조정하여 포함 보장
        adjusted_start = TimeUtils.get_before_candle_time(start_time, timeframe)
        logger.debug(f"사용자 start_time 포함 조정: {start_time} → {adjusted_start} (timeframe: {timeframe})")
        return adjusted_start

    # === 대량 요청 청크 분할 처리 ===
    def _split_into_chunks(self, symbol: str, timeframe: str, count: int, start_time: datetime, end_time: datetime) -> List[CandleChunk]:
        # TimeUtils.calculate_chunk_boundaries() 활용하여 200개 청크로 분할
        # 각 청크의 시작시간과 개수 계산
        # CandleChunk 객체 리스트 반환

    async def _collect_chunks_sequentially(self, chunks: List[CandleChunk], target_end_time: datetime) -> List[CandleData]:
        # 청크들을 순서대로 하나씩 수집
        # 각 청크마다: 겹침 분석 → DB/API 혼합 수집 → 저장
        # connected_end 추적하여 다음 청크의 API 요청 범위 최적화
        # target_end_time 도달시 수집 중단

    async def _collect_single_chunk(self, chunk: CandleChunk, connected_end: datetime) -> CollectionResult:
        # 단일 청크 수집 로직
        # 1. OverlapAnalyzer에 겹침 분석 요청 → 연속된 데이터의 끝점(connected_end) 확인
        # 2. connected_end까지는 DB에서 조회, 그 이후부터만 API 요청
        # 3. REST API Client를 통한 신규 데이터 수집 (이미 있는 부분은 API 요청 안 함)
        # 4. Repository 저장 및 Cache 업데이트

    def _adjust_chunk_timing(self, chunk: CandleChunk, connected_end: datetime) -> CandleChunk:
        # TimeUtils.adjust_start_from_connection() 활용
        # connected_end 기준으로 청크 시작점 조정
        # 이미 존재하는 데이터는 건너뛰고 없는 부분부터만 API 요청

    def _is_collection_complete(self, current_chunk_end: datetime, target_end: datetime) -> bool:
        # 현재 청크가 목표 target_end_time을 포함하는지 확인
        # 수집 완료 여부 판단

    async def _assemble_response(self, collected_chunks: List[CandleData]) -> CandleDataResponse:
        # 수집된 모든 청크를 하나의 응답으로 조합
        # 중복 제거, 시간순 정렬, 메타데이터 추가
```

### 📋 **overlap_analyzer.py** (🎯 API 요청 최적화 분석 엔진)
```python
class OverlapAnalyzer:
    """핵심 목적: 이미 존재하는 데이터는 API 요청하지 않고 DB에서 조회하여 효율성 극대화"""

    # === 핵심 분석 메서드 (API 요청 최적화) ===
    def analyze_overlap(self, target_start: datetime, target_count: int, timeframe: str, existing_ranges: List[DataRange]) -> OverlapResult:
        """
        요청 구간과 기존 DB 데이터를 비교하여 겹침 분석
        목적: 이미 있는 데이터는 API 요청 생략, 없는 부분만 API 요청
        반환: 겹침 상태 + 연속된 데이터의 끝점 (connected_end)

        검증된 최적화 로직 활용:
        - find_last_continuous_time() 309x 성능 최적화 적용 (LEAD 윈도우 함수)
        - 90000ms (1.5분) 임계값으로 연속성 정확 판단
        - ORDER BY timestamp DESC로 업비트 API 순서 일치
        """
        pass

    # === 겹침 상태 판단 ===
    def _detect_overlap_status(self, target_range: TimeRange, existing_ranges: List[DataRange]) -> OverlapStatus:
        # NO_OVERLAP: 겹침 없음 → 전체 구간 API 요청 필요
        # HAS_OVERLAP: 겹침 있음 → 일부는 DB 조회, 일부는 API 요청

    def find_connected_end(self, target_start: datetime, existing_ranges: List[DataRange]) -> Optional[datetime]:
        """
        target_start부터 연속적으로 존재하는 데이터의 마지막 시점 찾기

        최적화된 연속성 검사:
        - SQLite LEAD 윈도우 함수 활용 (309x 성능 향상)
        - 직접 매핑: 1분(90000ms), 5분(450000ms) 임계값
        - 예: 10:00~11:30 연속 존재, 11:30~12:00 누락 → connected_end = 11:30
        - 결과: 10:00~11:30은 DB 조회, 11:30부터는 API 요청
        """
        pass
```

### 📋 **Domain Interface 업데이트 사항**

기존 `candle_repository_interface.py`는 다음 사항들을 수정해야 합니다:

1. **모델 통합**: `CandleData` 모델을 새로운 Infrastructure 모델과 매핑
2. **메서드 단순화**: 4단계 최적화 복잡성을 Infrastructure로 이동
3. **청크 지원**: 200개 청크 단위 처리를 위한 인터페이스 조정
4. **DDD 순수성**: Domain이 Infrastructure 세부사항에 노출되지 않도록 추상화

### 📋 **sqlite_candle_repository.py** (🔧 Infrastructure Persistence)
```python
class SqliteCandleRepository:
    """캔들 데이터 영속성 Infrastructure Service"""

    # === 데이터 저장 ===
    async def save_candle_chunk(symbol: str, timeframe: str, candles: List[CandleData]) -> bool:
        # 청크 단위 캔들 데이터 저장
        # INSERT OR IGNORE 방식으로 중복 처리 (중복시 삽입 무시)
        # 🎯 이유: UTC 시간이 PRIMARY KEY + 업비트 서버 데이터 불변
        # 심볼별 개별 테이블 관리

    # === 기존 데이터 조회 ===
    async def get_data_ranges(symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> List[DataRange]:
        # 지정 구간의 기존 데이터 범위 조회
        # 겹침 분석을 위한 메타데이터 제공

    async def get_candles_by_range(symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> List[CandleData]:
        # 특정 시간 범위의 실제 캔들 데이터 조회
        # 캐시 미스시 DB에서 직접 조회
```

### 📋 **candle_cache.py** (⚡ Infrastructure Cache)
```python
class CandleCache:
    """고속 메모리 캐시 Infrastructure Service"""

    # === 캐시 저장 ===
    def store_chunk(cache_key: str, candles: List[CandleData], ttl: int = 60) -> None:
        # 청크 단위 캐시 저장
        # TTL 기반 자동 만료

    # === 캐시 조회 ===
    def get_cached_chunk(cache_key: str) -> Optional[List[CandleData]]:
        # 캐시에서 청크 조회
        # 만료된 데이터는 자동 제거

    def has_complete_range(symbol: str, timeframe: str, start_time: datetime, count: int) -> bool:
        # 요청 범위가 캐시에 완전히 존재하는지 확인
        # 완전 데이터 존재시 즉시 반환 가능성 확인
```

### 📋 **time_utils.py** (⏰ Infrastructure Utility - 시간 계산 및 동작 중단 판단)
```python
class TimeUtils:
    """시간 계산 Infrastructure Utility - end_time 계산 및 동작 중단 판단"""

    # === 검증된 핵심 메서드들 (개발 완료) ===
    @staticmethod
    def determine_target_end_time(
        count: int = None,
        start_time: datetime = None,
        end_time: datetime = None,
        timeframe: str = "1m"
    ) -> Tuple[datetime, datetime, int]:
        """
        모든 파라미터 조합을 처리하여 (start_time, end_time, count) 튜플 반환

        ✅ 검증 완료: 27개 테스트 케이스 통과
        ✅ Python 3.12+ 호환: datetime.now(timezone.utc) 적용
        ✅ 5가지 파라미터 조합 지원:
            1. count만 제공 → 현재시간부터 역순으로 count개
            2. start_time + count → end_time 계산
            3. start_time + end_time → count 자동 계산
            4. end_time만 제공 → 현재시간부터 end_time까지 count 계산
            5. 파라미터 없음 → 기본 200개 최신 데이터

        제약: count + end_time 동시 제공 불가 (ValidationError)
        """
        pass

    @staticmethod
    def calculate_chunk_boundaries(
        start_time: datetime,
        end_time: datetime,
        timeframe: str,
        chunk_size: int = 200
    ) -> List[TimeChunk]:
        """
        전체 요청을 200개 청크로 분할

        ✅ 검증 완료: 청크 분할 로직 테스트 통과
        ✅ 각 청크의 시작/끝 시간 정확 계산
        ✅ 마지막 청크 경계 처리 완료
        """
        pass

    @staticmethod
    def adjust_start_from_connection(
        connected_end: datetime,
        timeframe: str,
        count: int = 200
    ) -> datetime:
        """
        connected_end 기준으로 겹침 없는 새로운 시작점 반환

        ✅ 검증 완료: 겹침 최적화 연동 테스트 통과
        ✅ 연속 처리 최적화: 끝시간 → 다음 시작점 자동 계산
        """
        pass

    @staticmethod
    def get_before_candle_time(dt: datetime, timeframe: str) -> datetime:
        """
        이전 캔들 시간 계산 (업비트 순서상 before = 시간상 과거)

        🎯 목적: 업비트 API의 start_time 배제 동작을 보상하여 포함 보장
        ✅ 검증 완료: 업비트 시간 정렬 패턴 일치
        ✅ 1m/5m/15m/1h 타임프레임 지원

        사용 예: 사용자가 10:00부터 요청 → 09:59로 조정 → API에서 10:00부터 포함
        업비트 순서: 미래 ← 10:02, 10:01, 10:00, 09:59 → 과거
        """
        pass

    @staticmethod
    def get_after_candle_time(dt: datetime, timeframe: str) -> datetime:
        """
        다음 캔들 시간 계산 (업비트 순서상 after = 시간상 미래)

        ✅ 검증 완료: 업비트 시간 정렬 패턴 일치
        ✅ 1m/5m/15m/1h 타임프레임 지원

        사용 목적: 시간 범위 계산, 청크 분할 등에서 활용
        """
        pass

    # === 업비트 UTC 시간 정렬 (검증된 로직) ===
    @staticmethod
    def _align_to_candle_boundary(dt: datetime, timeframe: str) -> datetime:
        """
        업비트 UTC 경계에 맞춰 시간 정렬

        ✅ 검증된 업비트 실제 패턴:
        - 1분: 02:41:00, 02:40:00, 02:39:00 (분 단위 경계)
        - 5분: 02:40:00, 02:35:00, 02:30:00 (5분 간격, 정시 기준)
        - 15분: 02:30:00, 02:15:00, 02:00:00 (15분 간격)
        """
        pass

    @staticmethod
    def get_timeframe_seconds(timeframe: str) -> int:
        """타임프레임을 초 단위로 변환 (overlap_analyzer 연동용)"""
        pass

    # === 기존 호환성 유지 메서드들 ===
    @staticmethod
    def generate_candle_times(start_time: datetime, end_time: datetime, timeframe: str) -> List[datetime]:
        """시작 시간부터 종료 시간까지 예상되는 캔들 시간 목록 생성"""
        pass

    @staticmethod
    def get_previous_candle_time(dt: datetime, timeframe: str) -> datetime:
        """이전 캔들 시간 계산"""
        pass
```

### 📋 **models.py** (📝 Infrastructure Data Models)
```python
# === 요청/응답 모델 ===
@dataclass
class CandleChunk:
    """캔들 청크 정보 (네트워크 전송 단위)"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int
    chunk_index: int  # 청크 순서

@dataclass
class CandleDataResponse:
    """서브시스템 응답 모델"""
    success: bool
    candles: List[CandleData]
    total_count: int
    data_source: str  # cache, db, api
    response_time_ms: float

# === 분석 결과 모델 (단순화) ===
@dataclass
class OverlapResult:
    """겹침 분석 결과 - API 요청 최적화 정보"""
    status: OverlapStatus  # NO_OVERLAP, HAS_OVERLAP
    connected_end: Optional[datetime]  # 연속된 데이터의 끝점 (이 시점까지는 DB 조회 가능)

@dataclass
class DataRange:
    """기존 데이터 범위"""
    start_time: datetime
    end_time: datetime
    candle_count: int
    is_continuous: bool

# === 시간 관련 모델 ===
@dataclass
class TimeChunk:
    """시간 기반 청크"""
    start_time: datetime
    end_time: datetime
    expected_count: int

# === 도메인 모델 ===
@dataclass
class CandleData:
    """캔들 데이터 도메인 모델"""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    symbol: str
    timeframe: str
```

## 🔄 **서브시스템 사용 시나리오**

### 📋 **서브시스템 관점: 직접 CandleDataProvider 사용**

```python
# === 서브시스템에서의 직접 사용 (CandleClient 없이) ===
from upbit_auto_trading.infrastructure.market_data.candle import CandleDataProvider

# 서브시스템 코드
async def analyze_market_trend():
    provider = CandleDataProvider()

    # 다양한 요청 방식 지원
    # 방식 1: count만 지정 (최근 1000개)
    candles = await provider.get_candles(
        symbol="KRW-BTC",
        timeframe="1m",
        count=1000
    )

    # 방식 2: start_time + count (사용자 제공 start_time - 포함됨)
    candles = await provider.get_candles(
        symbol="KRW-BTC",
        timeframe="1m",
        start_time=datetime.now() - timedelta(hours=16),  # 🎯 사용자 제공 → inclusive_start 적용
        count=1000,
        inclusive_start=True  # 기본값, 16시간 전 시점부터 포함됨
    )

    # 방식 3: start_time + end_time (사용자 제공 start_time - 포함됨)
    candles = await provider.get_candles(
        symbol="KRW-BTC",
        timeframe="1m",
        start_time=datetime.now() - timedelta(hours=16),  # 🎯 사용자 제공 → inclusive_start 적용
        end_time=datetime.now() - timedelta(hours=2),     # end_time은 조정 불필요 (이미 포함 기대)
        inclusive_start=True  # 기본값, 16시간 전 시점부터 포함됨
    )

    # 방식 4: end_time만 지정 (시스템 자동 start_time)
    candles = await provider.get_candles(
        symbol="KRW-BTC",
        timeframe="1m",
        end_time=datetime.now() - timedelta(hours=2)  # start_time 자동계산, inclusive_start 무관
    )

    # 🎯 고급 사용자용: inclusive_start=False (API 네이티브 배제 방식)
    # 첫 번째 요청 (count만 - 시스템 자동 start_time)
    initial_data = await provider.get_candles(
        symbol="KRW-BTC",
        timeframe="1m",
        count=500  # start_time 자동생성, inclusive_start 무관
    )

    # 연속 요청 (사용자 제공 start_time - 배제 모드로 중복 방지)
    last_time = initial_data.candles[-1].timestamp
    additional_data = await provider.get_candles(
        symbol="KRW-BTC",
        timeframe="1m",
        start_time=last_time,             # 🎯 사용자 제공 start_time
        count=500,
        inclusive_start=False             # 🔧 배제 모드: API 네이티브 방식, 중복 없음
    )

    # 주의: count + end_time 동시 사용 불가 (ValidationError)
    # ❌ provider.get_candles(symbol="KRW-BTC", timeframe="1m", count=100, end_time=some_time)

    # 서브시스템은 내부 청크 처리를 모르고 결과만 사용
    return analyze_candles(candles.candles)
```

### 📋 **Infrastructure Layer 내부 처리 흐름**

```
서브시스템 → CandleDataProvider.get_candles()

1. CandleDataProvider._split_into_chunks()
   ├── TimeUtils.determine_target_end_time() → 최종 end_time 결정
   ├── 1000개 → 5개 청크로 분할 (200개씩)
   ├── 청크1: start_time + 0분 ~ +200분 (200개)
   ├── 청크2: start_time + 200분 ~ +400분 (200개)
   ├── 청크3: start_time + 400분 ~ +600분 (200개)
   ├── 청크4: start_time + 600분 ~ +800분 (200개)
   └── 청크5: start_time + 800분 ~ +1000분 (200개)

2. CandleDataProvider._collect_chunks_sequentially()

   📋 청크1 수집:
   ├── OverlapAnalyzer.analyze_overlap(청크1_시작, 200, "1m", 기존_범위들)
   ├── 결과: NO_OVERLAP (겹침 없음) → 전체 200개 API 요청 필요
   ├── REST API Client 호출 → 업비트 API 요청 (200개)
   ├── SqliteCandleRepository.save_candle_chunk() → DB 저장
   ├── CandleCache.store_chunk() → 캐시 저장
   └── connected_end = 청크1의 마지막 시간

   📋 청크2 수집:
   ├── OverlapAnalyzer.analyze_overlap(청크2_시작, 200, "1m", 기존_범위들)
   ├── 결과: HAS_OVERLAP + connected_end = 11:30 (연속 데이터의 끝)
   ├── 10:00~11:30: DB에서 조회 (130개) → API 요청 안 함
   ├── 11:30~13:20: REST API 호출 (70개만) → DB/캐시 저장
   └── connected_end = 청크2의 마지막 시간 (13:20)

   📋 청크3~4 수집:
   ├── connected_end 기준으로 시작점 최적화
   ├── 이미 있는 부분은 DB 조회, 없는 부분만 API 요청
   └── connected_end 업데이트

   📋 청크5 수집:
   ├── connected_end 기준으로 최적화된 수집
   ├── CandleDataProvider._is_collection_complete() 확인
   ├── 결과: 청크5_마지막 > target_end_time → 수집 완료!
   └── 처리 종료

3. CandleDataProvider._assemble_response()
   ├── 모든 수집된 청크 데이터 조합
   ├── 중복 제거 및 시간순 정렬
   ├── CandleDataResponse 생성 (성공, 1000개, 소스정보, 응답시간)
   └── 서브시스템에 반환
```---

## 🎯 **DDD Infrastructure Service 설계 원칙**

### ✅ **서브시스템 친화적 단일 인터페이스**
- **CandleDataProvider만**: 서브시스템들이 직접 import하여 사용
- **CandleClient 불필요**: get_candles()가 이미 모든 기능 제공
- **다양한 요청 방식**: count/start_time/end_time 조합 지원
- **복잡성 숨김**: 내부 청크 분할, 겹침 분석 등을 서브시스템에서 감춤

### ✅ **최소 역할 분담 (핵심만)**
- **CandleDataProvider**: 전체 조율, 청크 분할, 순차 수집, DB/API 혼합 전략 결정
- **OverlapAnalyzer**: API 요청 최적화 (검증된 309x 성능 향상 적용)
- **Repository**: DB 영속성만
- **Cache**: 메모리 캐시만
- **TimeUtils**: 검증 완료된 시간 계산 (27개 테스트 통과)

### ✅ **업비트 API 시간 처리 정교화 (핵심 개선)**
- **사용자 제공 start_time만 조정**: 케이스 2,3에서 사용자가 직접 제공한 start_time에만 inclusive_start 적용
- **시스템 자동 start_time 유지**: 케이스 1,4,5에서 자동 생성된 start_time은 조정 없음 (자연스러운 동작)
- **inclusive_start=True (기본)**: 사용자 제공 start_time 포함하도록 조정 (직관적)
- **inclusive_start=False**: 사용자 제공 start_time도 API 네이티브 배제 방식 (고급 사용자용)
- **end_time 조정 불필요**: 사용자가 이미 포함을 기대하므로 어떠한 조정도 불필요
- **미래 시간 검증**: start_time/end_time이 미래일 경우 ValidationError (사용자 책임)
- **기존 코드 호환성**: 기존 count만 사용하는 코드는 변경 없이 동일하게 동작

### ✅ **검증된 컴포넌트 활용**
- **TimeUtils**: ✅ 완전 개발 완료, 27개 테스트 케이스 통과
- **OverlapAnalyzer**: ✅ 309x 성능 최적화 검증 (LEAD 윈도우 함수)
- **SQLite 최적화**: ✅ 90000ms 임계값, ORDER BY timestamp DESC 적용

### ✅ **청크(Chunk) 용어 적절한 활용**
- **네트워크 처리 단위**: "200개 캔들 청크로 전송"
- **API 요청 단위**: "업비트 API 청크 요청"
- **캐시 저장 단위**: "청크 단위 캐시 관리"
- **자연스러운 활용**: 네트워크/데이터 처리 맥락에서 표준 용어

### ✅ **end_time 처리 및 동작 중단**
- **다양한 입력**: count만, start_time+count, start_time+end_time 모두 지원
- **TimeUtils 계산**: 최종 target_end_time 결정
- **자동 중단**: target_end_time 도달시 청크 수집 중단
- **정확한 범위**: 요청한 시간 범위만 정확히 수집

### ✅ **서브시스템 사용 패턴**
1. **간단한 최근 데이터**: `provider.get_candles(symbol, timeframe, count=100)`
2. **특정 시점부터**: `provider.get_candles(symbol, timeframe, start_time=..., count=500)` (start_time 포함)
3. **시간 범위 지정**: `provider.get_candles(symbol, timeframe, start_time=..., end_time=...)` (start_time 포함)
4. **고급 사용자 모드**: `provider.get_candles(..., inclusive_start=False)` (API 네이티브)
5. **대량 데이터**: 내부적으로 자동 청크 분할 처리 (200개씩)

### ✅ **OverlapAnalyzer API 요청 최적화**
- **입력**: 시작점, 개수, 타임프레임, 기존 데이터 범위
- **출력**: 겹침 상태 (NO_OVERLAP/HAS_OVERLAP) + 연속된 데이터의 끝점 (connected_end)
- **최적화 원리**: 이미 존재하는 데이터는 API 요청하지 않고 DB에서 조회
- **검증된 성능**: 309x 향상된 연속성 검사 알고리즘 적용
- **효율성**: 전체 요청 중 일부만 API 호출, 나머지는 DB 활용으로 속도/비용 절약

이렇게 각 컴포넌트가 최소한의 명확한 역할만 가지면서 서브시스템에게는 간단한 단일 인터페이스를 제공하고, **업비트 API 시간 처리 이슈를 우아하게 해결**하는 구조입니다!
