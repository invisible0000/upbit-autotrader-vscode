# 📋 OverlapAnalyzer v5.0 - 단순화된 설계 완전 가이드

> 제안된 겹침 분석 로직의 정확한 5개 상태 분류 및 구현 설계서

## 🎯 **핵심 설계 원칙**

### ✅ **단순성과 안정성 우선**
- **시간 중심 처리**: 변수 최소화, target_start/target_end 기준 판단
- **Repository 패턴**: DDD 계층 분리 완벽 준수
- **명확한 상태 분류**: DB 상태 패턴과 1:1 매핑
- **임시 검증**: 개발 초기에만 적용, 안정화 후 제거

### ⚡ **성능 최적화 전략**
- **단계별 검사**: 빠른 존재 확인 → 완전성 확인 → 상세 분석
- **효율적 쿼리**: LIMIT 1, COUNT, LEAD 윈도우 함수 활용
- **조기 종료**: NO_OVERLAP, COMPLETE_OVERLAP 조기 판단

---

## 📝 **입력/출력 인터페이스**

### 🔥 **입력 (OverlapRequest)**
```python
@dataclass(frozen=True)
class OverlapRequest:
    """겹침 분석 요청"""
    symbol: str                    # 거래 심볼 (예: 'KRW-BTC')
    timeframe: str                 # 타임프레임 ('1m', '5m', '15m', etc.)
    target_start: datetime         # 요청 시작 시간
    target_end: datetime           # 요청 종료 시간
    target_count: int              # 요청 캔들 개수 (1~200)
```

### 🎯 **출력 (OverlapResult)**
```python
@dataclass(frozen=True)
class OverlapResult:
    """겹침 분석 결과"""
    status: OverlapStatus          # 겹침 상태 (5가지)

    # API 요청 범위 (필요시만)
    api_start: Optional[datetime]  # API 요청 시작점
    api_end: Optional[datetime]    # API 요청 종료점

    # DB 조회 범위 (필요시만)
    db_start: Optional[datetime]   # DB 조회 시작점
    db_end: Optional[datetime]     # DB 조회 종료점

    # 추가 정보
    partial_end: Optional[datetime]    # 연속 데이터의 끝점
    partial_start: Optional[datetime]  # 데이터 시작점 (중간 겹침용)
```

---

## 🏗️ **5가지 겹침 상태 정확한 분류**

### 📊 **겹침 상태 Enum**
```python
class OverlapStatus(Enum):
    """겹침 상태 - 제안된 로직의 정확한 5개 분류"""
    NO_OVERLAP = "no_overlap"                        # 1. 겹침 없음
    COMPLETE_OVERLAP = "complete_overlap"            # 2.1. 완전 겹침
    PARTIAL_START = "partial_start"                  # 2.2.1. 시작 겹침
    PARTIAL_MIDDLE_FRAGMENT = "partial_middle_fragment"    # 2.2.2.1. 중간 겹침 (파편)
    PARTIAL_MIDDLE_CONTINUOUS = "partial_middle_continuous"  # 2.2.2.2. 중간 겹침 (말단)
```

### 🎯 **로직 트리 구조**
```
1. has_any_data_in_range() = false
   → NO_OVERLAP

2. has_any_data_in_range() = true
   ├── 2.1. is_range_complete() = true
   │   → COMPLETE_OVERLAP
   │
   └── 2.2. is_range_complete() = false (일부 겹침)
       ├── 2.2.1. has_data_in_start() = true
       │   → PARTIAL_START (시작 겹침)
       │
       └── 2.2.2. has_data_in_start() = false (중간 겹침)
           ├── 2.2.2.1. is_continue_till_end() = false
           │   → PARTIAL_MIDDLE_FRAGMENT (파편 겹침)
           │
           └── 2.2.2.2. is_continue_till_end() = true
               → PARTIAL_MIDDLE_CONTINUOUS (말단 겹침)
```

---

## 🔍 **상태별 상세 분석**

### **1. 겹침 없음 (NO_OVERLAP)**
```
DB 상태: |------|
판단: has_any_data_in_range() = false
```

**조건:**
- `target_start`, `target_end` 내에 1개의 데이터도 없음

**결과:**
- **API 요청**: `[target_start, target_end]` 전체 구간
- **DB 조회**: 없음

**구현:**
```python
has_data = await self.repository.has_any_data_in_range(
    symbol, timeframe, target_start, target_end
)
if not has_data:
    return OverlapResult(
        status=OverlapStatus.NO_OVERLAP,
        api_start=target_start,
        api_end=target_end,
        db_start=None,
        db_end=None
    )
```

---

### **2. 완전 겹침 (COMPLETE_OVERLAP)**
```
DB 상태: |111111|
판단: has_any_data_in_range() = true, is_range_complete() = true
```

**조건:**
- `target_start`, `target_end` 내의 데이터 개수가 `target_count`와 일치

**결과:**
- **API 요청**: 없음
- **DB 조회**: `[target_start, target_end]` 전체 구간

**구현:**
```python
is_complete = await self.repository.is_range_complete(
    symbol, timeframe, target_start, target_end, target_count
)
if is_complete:
    return OverlapResult(
        status=OverlapStatus.COMPLETE_OVERLAP,
        api_start=None,
        api_end=None,
        db_start=target_start,
        db_end=target_end
    )
```

---

### **3. 시작 겹침 (PARTIAL_START)**
```
DB 상태: |11----| or |11-1--|
판단: has_data_in_start() = true
```

**조건:**
- `target_start`에 데이터 존재
- 연속된 데이터의 끝점(`partial_end`)이 `target_end`보다 작음

**결과:**
- **API 요청**: `[partial_end - dt, target_end]` (부족한 부분)
- **DB 조회**: `[target_start, partial_end]` (기존 부분)

**구현:**
```python
# target_start에 데이터 존재 확인
has_start = await self.has_data_in_start(symbol, timeframe, target_start)

if has_start:
    # 연속된 끝점 찾기
    partial_end = await self.repository.find_last_continuous_time(
        symbol, timeframe, target_start
    )

    if partial_end and partial_end < target_end:
        dt = self.time_utils.get_timeframe_seconds(timeframe)
        return OverlapResult(
            status=OverlapStatus.PARTIAL_START,
            api_start=partial_end - timedelta(seconds=dt),  # 업비트 내림차순: 다음 캔들은 과거 방향
            api_end=target_end,
            db_start=target_start,
            db_end=partial_end,
            partial_end=partial_end
        )
```

---

### **4. 중간 겹침 - 파편 (PARTIAL_MIDDLE_FRAGMENT)**
```
DB 상태: |--1-11| or |--1-1-|
판단: has_data_in_start() = false, is_continue_till_end() = false
```

**조건:**
- `target_start`에 데이터 없음
- 데이터 시작점부터 `target_end`까지 연속되지 않음 (2번째 gap 발견)

**결과:**
- **API 요청**: `[target_start, target_end]` 전체 구간 (gap이 2개 이상이므로)
- **DB 조회**: 없음

**구현:**
```python
# target_start에 데이터 없음 확인됨
# 데이터 시작점 찾기
partial_start = await self.find_data_start_in_range(
    symbol, timeframe, target_start, target_end
)

if partial_start:
    # 연속성 확인
    is_continuous = await self.is_continue_till_end(
        symbol, timeframe, partial_start, target_end
    )

    if not is_continuous:
        # 2번째 gap 발견 → 전체 API 요청
        return OverlapResult(
            status=OverlapStatus.PARTIAL_MIDDLE_FRAGMENT,
            api_start=target_start,
            api_end=target_end,
            db_start=None,
            db_end=None,
            partial_start=partial_start
        )
```

---

### **5. 중간 겹침 - 말단 (PARTIAL_MIDDLE_CONTINUOUS)**
```
DB 상태: |--1111|
판단: has_data_in_start() = false, is_continue_till_end() = true
```

**조건:**
- `target_start`에 데이터 없음
- 데이터 시작점부터 `target_end`까지 연속됨

**결과:**
- **API 요청**: `[target_start, partial_start - dt]` (앞 부분만)
- **DB 조회**: `[partial_start, target_end]` (뒷 부분)

**구현:**
```python
# target_start에 데이터 없음 확인됨
# 데이터 시작점 찾기
partial_start = await self.find_data_start_in_range(
    symbol, timeframe, target_start, target_end
)

if partial_start:
    # 연속성 확인
    is_continuous = await self.is_continue_till_end(
        symbol, timeframe, partial_start, target_end
    )

    if is_continuous:
        # 앞 부분만 API 요청
        dt = self.time_utils.get_timeframe_seconds(timeframe)
        return OverlapResult(
            status=OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS,
            api_start=target_start,
            api_end=partial_start - timedelta(seconds=dt),  # 업비트 내림차순: 과거 방향
            db_start=partial_start,
            db_end=target_end,
            partial_start=partial_start
        )
```

---

## 🧪 **내부 메서드 목록**

### 🔧 **Repository 연동 메서드 (기존 활용)**
```python
class OverlapAnalyzer:

    # === 기존 Repository 메서드 활용 ===
    async def has_any_data_in_range(self, symbol, timeframe, start_time, end_time) -> bool:
        """범위 내 데이터 존재 여부 (기존 구현 활용)"""
        return await self.repository.has_any_data_in_range(symbol, timeframe, start_time, end_time)

    async def is_range_complete(self, symbol, timeframe, start_time, end_time, count) -> bool:
        """범위 완전성 확인 (기존 구현 활용)"""
        return await self.repository.is_range_complete(symbol, timeframe, start_time, end_time, count)

    async def find_last_continuous_time(self, symbol, timeframe, start_time) -> Optional[datetime]:
        """연속 데이터 끝점 찾기 (기존 구현 활용)"""
        return await self.repository.find_last_continuous_time(symbol, timeframe, start_time)
```

### 🆕 **새로운 Repository 메서드 구현 필요**

#### **1. has_data_at_time() - 특정 시점 데이터 존재 확인**
```python
# sqlite_candle_repository.py에 추가 구현 필요
async def has_data_at_time(self, symbol: str, timeframe: str, target_time: datetime) -> bool:
    """특정 시점에 캔들 데이터 존재 여부 확인 (LIMIT 1 최적화)

    target_start에 정확히 해당하는 candle_date_time_utc가 있는지 확인하는 가장 빠른 방법
    """
    if not await self.table_exists(symbol, timeframe):
        logger.debug(f"테이블 없음: {symbol} {timeframe}")
        return False

    table_name = self._get_table_name(symbol, timeframe)

    try:
        with self.db_manager.get_connection("market_data") as conn:
            # PRIMARY KEY 점검색으로 가장 빠른 성능
            cursor = conn.execute(f"""
                SELECT 1 FROM {table_name}
                WHERE candle_date_time_utc = ?
                LIMIT 1
            """, (target_time.isoformat(),))

            exists = cursor.fetchone() is not None
            logger.debug(f"특정 시점 데이터 확인: {symbol} {timeframe} {target_time} -> {exists}")
            return exists

    except Exception as e:
        logger.error(f"특정 시점 데이터 확인 실패: {symbol} {timeframe}, {e}")
        return False
```

#### **2. find_data_start_in_range() - 범위 내 데이터 시작점 찾기**
```python
# sqlite_candle_repository.py에 추가 구현 필요
async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> Optional[datetime]:
    """범위 내 데이터 시작점 찾기 (업비트 내림차순 특성 반영)

    업비트 서버 응답: 최신 → 과거 순 (내림차순)
    따라서 MAX(candle_date_time_utc)가 업비트 기준 '시작점'
    """
    if not await self.table_exists(symbol, timeframe):
        logger.debug(f"테이블 없음: {symbol} {timeframe}")
        return None

    table_name = self._get_table_name(symbol, timeframe)

    try:
        with self.db_manager.get_connection("market_data") as conn:
            # candle_date_time_utc PRIMARY KEY 인덱스 활용으로 빠른 성능
            cursor = conn.execute(f"""
                SELECT MAX(candle_date_time_utc)
                FROM {table_name}
                WHERE candle_date_time_utc BETWEEN ? AND ?
            """, (start_time.isoformat(), end_time.isoformat()))

            result = cursor.fetchone()
            if result and result[0]:
                data_start = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                logger.debug(f"범위 내 데이터 시작점: {symbol} {timeframe} -> {data_start}")
                return data_start

            logger.debug(f"범위 내 데이터 없음: {symbol} {timeframe} ({start_time} ~ {end_time})")
            return None

    except Exception as e:
        logger.error(f"데이터 시작점 조회 실패: {symbol} {timeframe}, {e}")
        return None
```

### 🆕 **새로운 보조 메서드**
```python
    # === 제안된 로직을 위한 새로운 메서드 ===
    async def has_data_in_start(self, symbol: str, timeframe: str, start_time: datetime) -> bool:
        """target_start에 데이터 존재 여부 확인 (특정 시점 정확 검사)"""
        return await self.repository.has_data_at_time(symbol, timeframe, start_time)

    async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                      start_time: datetime, end_time: datetime) -> Optional[datetime]:
        """범위 내 데이터 시작점 찾기 (MAX 쿼리)

        업비트 서버 내림차순 특성: 최신 시간이 데이터의 '시작점'
        target_start ~ target_end 범위에서 candle_date_time_utc의 MAX 값 반환
        """
        return await self.repository.find_data_start_in_range(symbol, timeframe, start_time, end_time)

    async def is_continue_till_end(self, symbol: str, timeframe: str,
                                  start_time: datetime, end_time: datetime) -> bool:
        """start_time부터 end_time까지 연속성 확인"""
        connected_end = await self.repository.find_last_continuous_time(
            symbol, timeframe, start_time
        )
        return connected_end is not None and connected_end >= end_time
```
        connected_end = await self.repository.find_last_continuous_time(
            symbol, timeframe, start_time
        )
        return connected_end is not None and connected_end >= end_time
```

### ⏰ **시간 계산 메서드**
```python
def get_timeframe_dt(self, timeframe: str) -> int:
    """타임프레임 → 초 단위 변환 (time_utils 연동)"""
    return self.time_utils.get_timeframe_seconds(timeframe)

def calculate_expected_count(self, start_time: datetime, end_time: datetime, timeframe: str) -> int:
    """시간 범위 → 예상 캔들 개수 계산"""
    dt = self.get_timeframe_dt(timeframe)
    time_diff = int((end_time - start_time).total_seconds())
    return (time_diff // dt) + 1
```

---

## 🔍 **임시 검증 로직**

### ✅ **개발 초기 검증 (안정화 후 제거)**
```python
def _validate_request(self, request: OverlapRequest) -> None:
    """개발 초기 임시 검증 - 기능 안정화 후 제거 가능"""

    # 1. count 범위 검증
    if request.target_count <= 1:
        raise ValueError(f"count는 1보다 커야 합니다: {request.target_count}")

    if request.target_count > 200:
        raise ValueError(f"count는 200 이하여야 합니다: {request.target_count}")

    # 2. 시간 순서 검증
    if request.target_start >= request.target_end:
        raise ValueError(
            f"start_time이 end_time보다 크거나 같습니다: "
            f"{request.target_start} >= {request.target_end}"
        )

    # 3. 카운트 계산 일치성 검증
    expected_count = self.calculate_expected_count(
        request.target_start, request.target_end, request.timeframe
    )
    if expected_count != request.target_count:
        raise ValueError(
            f"시간 범위와 count가 일치하지 않습니다: "
            f"계산된 count={expected_count}, 요청 count={request.target_count}"
        )

# 검증 활성화/비활성화 플래그
class OverlapAnalyzer:
    def __init__(self, repository, time_utils, enable_validation: bool = True):
        self.repository = repository
        self.time_utils = time_utils
        self.enable_validation = enable_validation  # 안정화 후 False로 설정
```

---

## 📊 **DB 상태 케이스 매핑**

### 🎯 **정확한 5개 상태별 DB 시각화**
```
1. 겹침 없음 (NO_OVERLAP):                    |------|
2. 완전 겹침 (COMPLETE_OVERLAP):               |111111|
3. 시작 겹침 (PARTIAL_START):                  |11----| or |11-1--|
4. 중간 겹침-파편 (PARTIAL_MIDDLE_FRAGMENT):   |--1-11| or |--1-1-|
5. 중간 겹침-말단 (PARTIAL_MIDDLE_CONTINUOUS): |--1111|

범례:
- |: target_start, target_end 경계
- 1: 데이터 존재
- -: 데이터 없음 (gap)
```

### 🔍 **제안된 로직의 세부 케이스**
```
2. 겹침 있음의 하위 분류:
   ├── 2.1. 완전 겹침: |111111|
   └── 2.2. 일부 겹침: |11--11| (예시)
       ├── 2.2.1. 시작 겹침: |11----| or |11-1--|
       └── 2.2.2. 중간 겹침: |--11--| or |--1111| or |--1-11|
           ├── 2.2.2.1. 파편 겹침: |--1-11| or |--1-1-|
           └── 2.2.2.2. 말단 겹침: |--1111|
```

---

## 🚀 **메인 알고리즘 흐름**

### 🔥 **analyze_overlap 구현 로직 (정확한 5단계)**
```python
async def analyze_overlap(self, request: OverlapRequest) -> OverlapResult:
    """
    제안된 5단계 겹침 분석 알고리즘

    성능 최적화: 단계별 조기 종료로 불필요한 쿼리 방지
    """
    # 0. 임시 검증 (개발 초기에만)
    if self.enable_validation:
        self._validate_request(request)

    # 1. 겹침 없음 확인 (LIMIT 1 쿼리)
    has_data = await self.repository.has_any_data_in_range(
        request.symbol, request.timeframe,
        request.target_start, request.target_end
    )

    if not has_data:
        return self._create_no_overlap_result(request)

    # 2. 완전성 확인 (COUNT 쿼리)
    is_complete = await self.repository.is_range_complete(
        request.symbol, request.timeframe,
        request.target_start, request.target_end, request.target_count
    )

    if is_complete:
        return self._create_complete_overlap_result(request)

    # 3. 일부 겹침 - 시작점 확인
    has_start = await self.has_data_in_start(
        request.symbol, request.timeframe, request.target_start
    )

    if has_start:
        # 3.1. 시작 겹침 처리
        return await self._handle_start_overlap(request)
    else:
        # 3.2. 중간 겹침 처리
        return await self._handle_middle_overlap(request)

async def _handle_start_overlap(self, request: OverlapRequest) -> OverlapResult:
    """시작 겹침 처리 (PARTIAL_START)"""
    partial_end = await self.repository.find_last_continuous_time(
        request.symbol, request.timeframe, request.target_start
    )

    if partial_end and partial_end < request.target_end:
        dt = self.get_timeframe_dt(request.timeframe)
        return OverlapResult(
            status=OverlapStatus.PARTIAL_START,
            api_start=partial_end - timedelta(seconds=dt),  # 업비트 내림차순: 과거 방향
            api_end=request.target_end,
            db_start=request.target_start,
            db_end=partial_end,
            partial_end=partial_end
        )
    else:
        # 예상치 못한 케이스 → 전체 API 요청
        return self._create_fallback_result(request)

async def _handle_middle_overlap(self, request: OverlapRequest) -> OverlapResult:
    """중간 겹침 처리 (PARTIAL_MIDDLE_*)"""
    # 데이터 시작점 찾기
    partial_start = await self.find_data_start_in_range(
        request.symbol, request.timeframe,
        request.target_start, request.target_end
    )

    if not partial_start:
        # 데이터 시작점을 찾을 수 없음 → 전체 API 요청
        return self._create_fallback_result(request)

    # 연속성 확인
    is_continuous = await self.is_continue_till_end(
        request.symbol, request.timeframe, partial_start, request.target_end
    )

    if is_continuous:
        # 말단 겹침 (PARTIAL_MIDDLE_CONTINUOUS)
        dt = self.get_timeframe_dt(request.timeframe)
        return OverlapResult(
            status=OverlapStatus.PARTIAL_MIDDLE_CONTINUOUS,
            api_start=request.target_start,
            api_end=partial_start + timedelta(seconds=dt),
            db_start=partial_start,
            db_end=request.target_end,
            partial_start=partial_start
        )
    else:
        # 파편 겹침 (PARTIAL_MIDDLE_FRAGMENT)
        return OverlapResult(
            status=OverlapStatus.PARTIAL_MIDDLE_FRAGMENT,
            api_start=request.target_start,
            api_end=request.target_end,
            db_start=None,
            db_end=None,
            partial_start=partial_start
        )

def _create_fallback_result(self, request: OverlapRequest) -> OverlapResult:
    """예상치 못한 케이스 → 전체 API 요청으로 폴백"""
    return OverlapResult(
        status=OverlapStatus.PARTIAL_MIDDLE_FRAGMENT,  # 안전한 폴백
        api_start=request.target_start,
        api_end=request.target_end,
        db_start=None,
        db_end=None
    )
```

---

## 🧪 **테스트 케이스 설계**

### 📋 **상태별 단위 테스트**
```python
# 테스트 파일: test_overlap_analyzer_v5.py

class TestOverlapAnalyzerV5:

    @pytest.mark.asyncio
    async def test_no_overlap(self):
        """겹침 없음: |------|"""
        # DB에 데이터 없는 상태에서 요청

    @pytest.mark.asyncio
    async def test_complete_overlap(self):
        """완전 겹침: |111111|"""
        # DB에 요청 범위 전체 데이터 존재

    @pytest.mark.asyncio
    async def test_partial_start_simple(self):
        """시작 겹침 (단순): |11----|"""
        # 앞부분만 존재, 뒷부분 누락

    @pytest.mark.asyncio
    async def test_partial_start_with_gap(self):
        """시작 겹침 (gap 포함): |11-1--|"""
        # 앞부분 + 중간 gap + 일부 데이터 + 마지막 gap

    @pytest.mark.asyncio
    async def test_partial_middle_continuous(self):
        """중간 겹침 (말단): |--1111|"""
        # 앞부분 누락, 뒷부분 연속 존재

    @pytest.mark.asyncio
    async def test_partial_middle_fragment_simple(self):
        """중간 겹침 (파편-단순): |--1-1-|"""
        # 2번째 gap 발견으로 파편 겹침

    @pytest.mark.asyncio
    async def test_partial_middle_fragment_complex(self):
        """중간 겹침 (파편-복잡): |--1-11|"""
        # 중간 gap으로 파편 겹침
```

---

## 🎯 **성능 최적화 전략**

### ⚡ **쿼리 최적화**
1. **LIMIT 1**: 존재 여부만 확인
2. **COUNT**: 완전성 확인
3. **MIN/MAX**: 시작/끝점 찾기
4. **LEAD 윈도우**: 연속성 확인 (기존 309x 최적화 활용)

### 🚀 **알고리즘 최적화**
1. **조기 종료**: NO_OVERLAP, COMPLETE_OVERLAP 즉시 반환
2. **단계별 검사**: 필요한 쿼리만 실행
3. **캐시 활용**: 동일 요청 결과 캐싱 가능

---

## 📋 **구현 우선순위**

### 🥇 **1단계: 기본 구조**
- OverlapStatus Enum 정의
- OverlapRequest/OverlapResult 데이터클래스
- 기본 클래스 구조 및 의존성 주입

### 🥈 **2단계: 간단한 케이스**
- NO_OVERLAP, COMPLETE_OVERLAP 구현
- 기존 Repository 메서드 연동

### 🥉 **3단계: 부분 겹침**
- PARTIAL_START, PARTIAL_MIDDLE_* 구현
- 새로운 보조 메서드 추가

### 🏅 **4단계: 검증 및 최적화**
- 임시 검증 로직 추가
- 단위 테스트 작성
- 성능 측정 및 최적화

---

## ✅ **마무리**

이 설계는 **제안하신 정확한 5개 상태 분류를 완벽히 구현**하면서:

- ✅ **5가지 명확한 상태 분류** (NO_OVERLAP, COMPLETE_OVERLAP, PARTIAL_START, PARTIAL_MIDDLE_FRAGMENT, PARTIAL_MIDDLE_CONTINUOUS)
- ✅ **DDD Repository 패턴 완벽 준수**
- ✅ **시간 중심 처리로 변수 최소화**
- ✅ **성능 최적화된 단계별 쿼리**
- ✅ **임시 검증으로 개발 안정성 확보**
- ✅ **제안된 로직의 정확한 트리 구조 구현**

를 모두 달성하는 **정확하고 실용적인 설계**입니다.

### 🎯 **핵심 차이점 정리**
- **기존 복잡한 overlap_analyzer**: 6+ 상태, 복잡한 로직
- **제안된 단순화 설계**: 정확히 5개 상태, 명확한 트리 구조
- **성능 향상**: 단계별 조기 종료로 불필요한 쿼리 방지
- **유지보수성**: 시간 중심 처리로 디버깅 용이

### 🔧 **구현 시 필요한 추가 작업**

#### **1. Repository 인터페이스 확장 완료**
```python
# candle_repository_interface.py에 추가됨
async def has_data_at_time(self, symbol: str, timeframe: str, target_time: datetime) -> bool
async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                   start_time: datetime, end_time: datetime) -> Optional[datetime]
```

#### **2. Repository 구현체 확장 완료**
```python
# sqlite_candle_repository.py에 추가됨
# - has_data_at_time(): PRIMARY KEY = 검색으로 최고 성능
# - find_data_start_in_range(): MAX 쿼리로 업비트 내림차순 특성 반영
```

#### **3. 권장 성능 최적화**
- **has_data_at_time()**: PRIMARY KEY 점검색 → 인덱스 스캔 없이 O(1) 성능
- **find_data_start_in_range()**: MAX + BETWEEN → 인덱스 범위 스캔으로 빠른 성능
- **조기 종료**: NO_OVERLAP, COMPLETE_OVERLAP 케이스에서 불필요한 쿼리 방지

이제 이 정확한 설계를 바탕으로 단계별 구현을 진행하시면 됩니다! 🚀

---

## 💡 **추가 보강이 필요한 부분들**

### ⚠️ **1. 시간 정밀도 고려**
- **이슈**: `datetime` 비교 시 마이크로초 차이로 인한 오판 가능성
- **해결**: Repository에서 ISO 문자열 비교 또는 timestamp 정수 비교 고려

### ⚠️ **2. 타임존 일관성**
- **이슈**: UTC vs KST 혼재 시 겹침 분석 오류 가능성
- **해결**: Repository에서 모든 시간을 UTC로 정규화 확인

### ⚠️ **3. 예외 상황 처리**
- **이슈**: DB 연결 실패, 테이블 없음 등의 예외 케이스
- **해결**: OverlapAnalyzer에서 Repository 예외 상황 시 fallback 전략 필요

### ⚠️ **4. 성능 모니터링**
- **이슈**: 쿼리 성능 저하 탐지 부재
- **해결**: Repository 메서드에 쿼리 실행 시간 로깅 추가 고려

### ⚠️ **5. 테스트 데이터 준비**
- **이슈**: 5가지 겹침 상태 테스트를 위한 DB 데이터 셋업 복잡성
- **해결**: 테스트용 데이터 생성 헬퍼 함수 필요
