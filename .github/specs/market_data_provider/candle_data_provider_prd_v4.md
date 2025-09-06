# 🎯 CandleDataProvider v4.0 PRD - 업비트 특화 최적화

## 📋 **Problem & Users**

### **Problem Statement**
- 기존 smart_data_provider_V4는 15개 모듈로 과도하게 복잡하고 범용적 설계로 인한 업비트 특성 미반영
- 심볼별 개별 테이블 구조(`candles_KRW_BTC_1m`)를 활용한 성능 최적화 필요
- INSERT OR IGNORE 기반 중복 제거와 candle_date_time_utc PRIMARY KEY 활용 최적화
- 7규칙 자동매매 전략에 특화된 단순하고 고성능 캔들 데이터 시스템 구축
- time_utils와 overlap_optimizer 간 시간 처리 방식 통일 필요

### **Target Users**
- **Primary**: 7규칙 자동매매 전략 실행 엔진
- **Secondary**: 백테스팅 시스템, 차트 UI 컴포넌트
- **Tertiary**: 기술적 분석 모듈, 시장 데이터 분석 도구

### **Value Proposition**
- **업비트 특화**: 심볼별 개별 테이블로 쿼리 성능 10배 향상
- **단순성**: 7개 파일, 단일 폴더로 복잡도 95% 감소
- **성능**: API 호출 60% 감소, 캐시 히트율 90% 달성
- **안정성**: INSERT OR IGNORE로 DB 레벨 중복 제거, 무결성 보장
- **시간 일관성**: time_utils 기반 통일된 시간 처리 보장

---

## 🎯 **Goals & Non-goals**

### **Primary Goals**
1. **📊 완전한 캔들 데이터 관리**: 심볼별 개별 테이블 기반 OHLCV 통합 솔루션
2. **⚡ 고성능 응답**: 캐시 3ms, DB 30ms, API 200ms (P95 기준) 달성
3. **🔒 데이터 무결성**: candle_date_time_utc PK + INSERT OR IGNORE로 중복 완전 차단
4. **🚀 업비트 특화 최적화**: 200개 제한, 시작점 배제, 반간격 안전요청 구현
5. **🎯 7규칙 완벽 지원**: RSI, 이동평균, 볼린저밴드 등 연속 데이터 보장
6. **⏰ 시간 처리 통일**: time_utils 중심의 일관된 시간 계산 및 정렬

### **Secondary Goals**
- 대용량 동기화: 업비트 특화 4단계 겹침분석으로 30일치 데이터 효율적 수집
- 품질 모니터링: 수집률, 캐시 히트율, API 절약률 실시간 추적
- 테이블 관리: 심볼/timeframe 조합 기반 동적 테이블 생성/관리
- SQLite 호환성: 모든 SQL 쿼리의 SQLite 완벽 호환 보장

### **Non-goals**
- ❌ **실시간 스트리밍**: WebSocket 기반 실시간 캔들 구독 (별도 시스템)
- ❌ **다중 거래소**: 업비트 전용 구현 (확장성 고려하되 다른 거래소는 별도)
- ❌ **복잡한 분석**: 기존 7가지 겹침 패턴 → 4단계 업비트 특화 로직으로 단순화

---

## 🏗️ **Scope & Architecture**

### **Core System Architecture**
```
upbit_auto_trading/infrastructure/market_data/candle/
├── candle_data_provider.py       # 🏆 메인 Facade (통합 API)
├── candle_client.py              # 📡 업비트 API 클라이언트 (200개 최적화)
├── candle_repository.py          # 💾 DB Repository (개별 테이블 관리)
├── candle_cache.py               # ⚡ 고속 메모리 캐시 (60초 TTL)
├── overlap_optimizer.py          # 🎯 업비트 특화 4단계 최적화 (시간 통일)
├── time_utils.py                 # ⏰ 시간 처리 유틸 (확장된 V4, 초 단위 지원)
└── models.py                     # 📝 데이터 모델 통합
```

### **새로운 DB 구조 활용**

#### **심볼별 개별 테이블 전략**
```sql
-- 테이블명 패턴: candles_{SYMBOL}_{TIMEFRAME}
CREATE TABLE candles_KRW_BTC_1m (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market TEXT NOT NULL,
    candle_date_time_utc DATETIME PRIMARY KEY,  -- 🔑 중복 방지 핵심
    candle_date_time_kst DATETIME NOT NULL,
    opening_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    trade_price DECIMAL(20,8) NOT NULL,
    timestamp BIGINT NOT NULL,
    candle_acc_trade_price DECIMAL(30,8) NOT NULL,
    candle_acc_trade_volume DECIMAL(30,8) NOT NULL,
    unit INTEGER DEFAULT 1,
    trade_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스: candle_date_time_utc (PK로 자동 생성)
-- 추가 인덱스: timestamp, created_at (조회 최적화용)
```

#### **INSERT OR IGNORE 활용**
```python
def save_candles(self, symbol: str, timeframe: str, candles: List[dict]) -> int:
    """업비트 특화 캔들 저장 (중복 자동 차단)"""
    table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"

    query = f"""
    INSERT OR IGNORE INTO {table_name} (
        market, candle_date_time_utc, candle_date_time_kst,
        opening_price, high_price, low_price, trade_price,
        timestamp, candle_acc_trade_price, candle_acc_trade_volume,
        unit, trade_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # 배치 실행: executemany로 고성능 처리
    inserted_count = cursor.executemany(query, candle_data).rowcount
    return inserted_count
```

### **업비트 특화 4단계 겹침 최적화 (시간 통일)**

#### **기존 복잡한 7패턴 → 업비트 특화 4단계**
```python
class UpbitOverlapOptimizer:
    """업비트 200개 제한 특화 최적화"""

    def __init__(self, repository: CandleRepository, time_utils: TimeUtils):
        self.repository = repository
        self.time_utils = time_utils  # 통일된 시간 처리

    def optimize_candle_requests(self, symbol: str, timeframe: str,
                                start_time: datetime, count: int) -> List[ApiRequest]:
        """4단계 최적화 전략 (time_utils 기반)"""

        # 시간 정렬 보장 (time_utils 활용)
        aligned_start = self.time_utils._align_to_candle_boundary(
            start_time, self.time_utils._parse_timeframe_to_minutes(timeframe)
        )

        current_start = aligned_start
        remaining_count = count
        api_requests = []

        while remaining_count > 0:
            # 1. 시작점 200개 내 겹침 확인
            if self._check_start_overlap(symbol, timeframe, current_start):
                request = self._create_extend_request(current_start, remaining_count)

            # 2. 완전 겹침 확인 (count 기반 빠른 확인)
            elif self._check_complete_overlap(symbol, timeframe, current_start,
                                            min(remaining_count, 200)):
                # DB에서 직접 반환, API 호출 불필요
                break

            # 3. 파편화 겹침 확인 (2번 이상 끊어짐)
            elif self._check_fragmentation(symbol, timeframe, current_start, 200):
                # 전체 200개 요청이 효율적
                request = self._create_full_request(current_start, remaining_count)

            # 4. 연결된 끝 찾기
            else:
                request = self._create_optimal_request(current_start, remaining_count)

            api_requests.append(request)
            current_start, remaining_count = self._update_progress(request)

        return api_requests
```

#### **핵심 로직: 완전 겹침 확인 (count 기반)**
```python
def _check_complete_overlap(self, symbol: str, timeframe: str,
                          start_time: datetime, count: int) -> bool:
    """count 기반 완전 겹침 확인 (초고속)"""

    table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
    timeframe_seconds = self.time_utils.get_timeframe_seconds(timeframe)  # 통일된 시간 계산
    end_time = start_time + timedelta(seconds=timeframe_seconds * (count - 1))

    query = f"""
    SELECT COUNT(*) FROM {table_name}
    WHERE candle_date_time_utc BETWEEN ? AND ?
    """

    cursor = self.repository.execute_query(query, (start_time, end_time))
    db_count = cursor.fetchone()[0]

    # 완전 일치 = DB 개수와 요청 개수 동일
    return db_count == count
```

#### **파편화 체크 (SQLite 호환 SQL)**
```python
def _check_fragmentation(self, symbol: str, timeframe: str,
                        start_time: datetime, count: int) -> bool:
    """파편화 겹침 확인 (SQLite 호환 쿼리)"""

    table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
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
    return gap_count >= 2
```

#### **연결된 끝 찾기 (SQLite datetime 함수 활용)**
```python
def _find_connected_end(self, symbol: str, timeframe: str,
                       start_time: datetime, max_count: int = 200) -> Optional[datetime]:
    """200개 범위 내에서 연속된 데이터의 끝점 찾기 (SQLite 호환)"""

    table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"
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

### **확장된 TimeUtils (v4.0)**

#### **기존 기능 유지 + 초 단위 지원**
```python
class TimeUtils:
    """통일된 시간 처리 유틸리티 (v4.0 확장)"""

    def get_timeframe_seconds(self, timeframe: str) -> int:
        """타임프레임을 초 단위로 변환 (overlap_optimizer 호환)"""
        timeframe_minutes = self._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")
        return timeframe_minutes * 60

    def _normalize_db_time_format(self, dt: datetime) -> str:
        """DB 저장용 시간 형식 표준화 (ISO 형식)"""
        return dt.isoformat()

    def _parse_db_time_format(self, time_str: str) -> datetime:
        """DB에서 읽은 시간 문자열을 datetime으로 변환"""
        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

    def _ensure_time_consistency(self, dt: datetime, timeframe: str) -> datetime:
        """시간 정렬 일관성 보장"""
        return self._align_to_candle_boundary(
            dt, self._parse_timeframe_to_minutes(timeframe)
        )

    # 기존 V4 메서드들 모두 유지
    # generate_candle_times, _align_to_candle_boundary 등
```

### **Key UX Flows**

#### **Flow 1: 기본 캔들 조회** (Primary)
```python
provider = CandleDataProvider()

# 개수 기반 조회 (업비트 호환)
candles = await provider.get_candles("KRW-BTC", "1m", count=100)

# 기간 기반 조회 (count 자동 계산)
candles = await provider.get_candles("KRW-BTC", "1m",
                                   end="2024-01-01T00:00:00Z",
                                   to="2024-01-02T00:00:00Z")

# Flow: 파라미터 검증 → 시간 정렬 → 캐시 확인 → 4단계 겹침 최적화 → API 최소 호출 → INSERT OR IGNORE
```

#### **Flow 2: 대용량 동기화** (Secondary)
```python
# 업비트 특화 30일 동기화 (4단계 최적화 적용)
progress = await provider.sync_candles("KRW-BTC", "1m", days=30)

# Flow: 누락 구간 분석 → 시간 정렬 → 4단계 최적화 → 배치 수집 → 진행률 추적 → API 절약 리포트
```

#### **Flow 3: 성능 모니터링** (Operational)
```python
# 업비트 특화 최적화 효과 측정
metrics = await provider.get_optimization_metrics("KRW-BTC", "1m")
# {
#   "api_calls_saved": 156,      # 절약된 API 호출 수
#   "cache_hit_rate": 0.92,      # 캐시 히트율
#   "fragmentation_rate": 0.03,  # 파편화 비율
#   "table_size_mb": 45.2,       # 테이블 크기
#   "time_consistency": 1.0      # 시간 정렬 일관성 (100%)
# }
```

---

## 🔧 **Technical Constraints & Dependencies**

### **Performance Constraints**
- **응답시간 SLA**: 캐시 <3ms, DB <30ms, API <200ms (P95) - 개별 테이블로 향상
- **처리량**: 150 req/sec 동시 처리 (기존 100→150 향상)
- **메모리 사용량**: 80MB 이하 안정적 운영 (개별 테이블 메모리 효율성)
- **API Rate Limit**: 600req/min → 4단계 최적화로 실효 1200req/min 효과

### **Data Constraints**
- **테이블 구조**: `candles_{SYMBOL}_{TIMEFRAME}` 패턴 (동적 생성)
- **PRIMARY KEY**: candle_date_time_utc (INSERT OR IGNORE 핵심)
- **정밀도**: Decimal 기반 정확한 가격 계산 (기존 동일)
- **무결성**: INSERT OR IGNORE로 DB 레벨 중복 완전 차단
- **시간 일관성**: time_utils 기반 모든 시간 계산 통일

### **System Dependencies**
- **Database**: SQLite3 market_data.sqlite3 (심볼별 개별 테이블)
- **API Client**: upbit_public_client (200개 제한 최적화)
- **Logging**: Infrastructure 로깅 시스템
- **Table Management**: 동적 테이블 생성/관리 시스템
- **Time Processing**: 확장된 time_utils (초 단위 지원)

---

## ✅ **Acceptance Criteria**

### **Functional Requirements**
- [ ] **API 완전성**: get_candles() 모든 파라미터 조합 완벽 동작
  - count 기반: (symbol, interval, count, to) 조합
  - 기간 기반: (symbol, interval, end, to) 조합 자동 count 계산
- [ ] **중복 완전 차단**: INSERT OR IGNORE로 동일 candle_date_time_utc 중복 0%
- [ ] **4단계 최적화**: 업비트 특화 겹침 분석으로 API 호출 60% 감소
- [ ] **테이블 관리**: 새로운 symbol/timeframe 조합 시 자동 테이블 생성
- [ ] **7규칙 지원**: 연속 데이터 보장으로 모든 기술적 지표 계산 가능
- [ ] **시간 일관성**: time_utils와 overlap_optimizer 간 100% 일치된 시간 계산

### **Performance Requirements**
- [ ] **응답시간**: 캐시 3ms, DB 30ms, API 200ms (P95 기준) 달성
- [ ] **캐시 효율**: 90% 이상 히트율, TTL 60초 최적화
- [ ] **API 최적화**: 4단계 분석으로 60% 호출 감소 확인
- [ ] **처리량**: 150 req/sec 동시 처리 성공
- [ ] **테이블 성능**: 개별 테이블 쿼리 <30ms 달성
- [ ] **SQLite 호환**: 모든 SQL 쿼리 SQLite 환경에서 100% 동작

### **Quality Requirements**
- [ ] **테스트 커버리지**: 95% 이상, 4단계 최적화 로직 완전 검증
- [ ] **DDD 준수**: Repository 패턴으로 DB 로직 캡슐화
- [ ] **예외 처리**: 테이블 생성 실패, API 제한 등 모든 상황 대응
- [ ] **모니터링**: API 절약률, 테이블별 성능 지표 추적
- [ ] **시간 통일성**: 모든 컴포넌트 간 시간 처리 일관성 검증

---

## 📊 **Observability & Monitoring**

### **Key Metrics**
```python
# 업비트 특화 성능 지표
response_time_p95: float        # 응답시간 95퍼센타일 (목표: <200ms)
cache_hit_rate: float           # 캐시 히트율 (목표: 90%+)
api_call_reduction: float       # API 호출 감소율 (목표: 60%+)
overlap_optimization_rate: float # 4단계 최적화 적용률

# 테이블 관리 지표
table_count: int                # 생성된 테이블 수
table_size_distribution: dict   # 테이블별 크기 분포
fragmentation_rate: float       # 평균 파편화 비율
insert_ignore_rate: float       # INSERT OR IGNORE 중복 차단률

# 품질 지표
data_coverage: float            # 데이터 수집률 (목표: 98%+)
duplicate_prevention_rate: float # 중복 방지율 (목표: 100%)
error_rate: float               # 오류율 (목표: 0.5% 이하)
time_consistency_rate: float    # 시간 처리 일관성 (목표: 100%)
```

### **4단계 최적화 모니터링**
```python
# 최적화 단계별 성과 추적
logger.info("4단계 최적화 결과", extra={
    "symbol": "KRW-BTC", "timeframe": "1m",
    "step1_start_overlap": True,
    "step2_complete_overlap": False,
    "step3_fragmentation": False,
    "step4_connected_end": True,
    "original_api_calls": 5,
    "optimized_api_calls": 1,
    "reduction_rate": 80.0,
    "optimization_time_ms": 12.3,
    "time_alignment_consistent": True  # 시간 정렬 일관성
})
```

### **테이블 성능 모니터링**
```python
# 개별 테이블 성능 추적
logger.info("테이블 성능", extra={
    "table_name": "candles_KRW_BTC_1m",
    "query_time_ms": 8.5,
    "row_count": 43200,  # 30일치 1분봉
    "table_size_mb": 12.4,
    "fragmentation_rate": 0.02,
    "last_insert_time": "2024-01-01T10:30:00Z",
    "sql_compatibility": "sqlite3"  # SQLite 호환성 확인
})
```

---

## 🔧 **Implementation Approach**

### **기존 코드 이관 전략 (v4.0 업데이트)**

#### **🟢 완전 이관 + 확장 대상**
| 기존 파일 | 신규 파일 | 핵심 기능 | 수정 사항 |
|-----------|-----------|-----------|-----------|
| `time_utils.py` (74줄) | `time_utils.py` | 캔들 시간 경계 정렬 + 초 단위 변환 | get_timeframe_seconds() 추가 |
| `fast_cache.py` (97줄) | `candle_cache.py` | TTL 캐시 | TTL 60초로 조정 |

#### **🟡 신규 구현 대상 (업비트 특화)**
| 신규 파일 | 구현 기능 | 업비트 특화 요소 |
|-----------|-----------|------------------|
| `candle_repository.py` | 개별 테이블 관리 | `candles_{SYMBOL}_{TIMEFRAME}` 동적 생성 |
| `overlap_optimizer.py` | 4단계 최적화 | 200개 제한, SQLite 호환 쿼리, time_utils 통합 |
| `candle_client.py` | API 클라이언트 | 시작점 배제, 반간격 안전요청 |

#### **🔴 제거 대상**
- `overlap_analyzer.py` (404줄): 7패턴 → 4단계로 단순화
- `batch_db_manager.py`: INSERT OR IGNORE로 단순화
- `collection_status_manager.py`: 빈 캔들 로직 내재화

### **핵심 구현 우선순위**

#### **1단계: 통일된 시간 처리 시스템**
```python
class TimeUtils:
    """v4.0 확장된 시간 처리 유틸리티"""

    def get_timeframe_seconds(self, timeframe: str) -> int:
        """overlap_optimizer 호환용 초 단위 변환"""
        timeframe_minutes = self._parse_timeframe_to_minutes(timeframe)
        if timeframe_minutes is None:
            raise ValueError(f"지원하지 않는 타임프레임: {timeframe}")
        return timeframe_minutes * 60

    def ensure_consistent_alignment(self, dt: datetime, timeframe: str) -> datetime:
        """모든 컴포넌트에서 동일한 시간 정렬 보장"""
        return self._align_to_candle_boundary(
            dt, self._parse_timeframe_to_minutes(timeframe)
        )
```

#### **2단계: 테이블 관리 시스템**
```python
class CandleTableManager:
    """심볼별 개별 테이블 관리"""

    def __init__(self, time_utils: TimeUtils):
        self.time_utils = time_utils

    def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        """테이블 존재 확인 및 생성"""
        table_name = f"candles_{symbol.replace('-', '_')}_{timeframe}"

        if not self._table_exists(table_name):
            self._create_candle_table(table_name)

        return table_name
```

#### **3단계: 4단계 최적화 엔진 (시간 통일)**
```python
class UpbitOverlapOptimizer:
    """업비트 200개 제한 특화 최적화 (시간 통일)"""

    def __init__(self, repository: CandleRepository, time_utils: TimeUtils):
        self.repository = repository
        self.time_utils = time_utils  # 통일된 시간 처리

    def optimize_requests(self, symbol: str, timeframe: str,
                         start_time: datetime, count: int) -> OptimizationResult:
        """4단계 최적화 메인 로직 (시간 일관성 보장)"""

        # 시간 정렬 보장
        aligned_start = self.time_utils.ensure_consistent_alignment(start_time, timeframe)

        # 4단계 최적화 실행 (time_utils 기반 시간 계산)
        return self._execute_optimization(aligned_start, count)
```

#### **4단계: Repository 패턴 구현**
```python
class CandleRepository:
    """DDD 준수 캔들 데이터 Repository"""

    def __init__(self, table_manager: CandleTableManager, time_utils: TimeUtils):
        self.table_manager = table_manager
        self.time_utils = time_utils

    def save_candles(self, symbol: str, timeframe: str,
                    candles: List[CandleModel]) -> int:
        """INSERT OR IGNORE 기반 캔들 저장 (시간 정렬 보장)"""
        table_name = self.table_manager.ensure_table_exists(symbol, timeframe)

        # 시간 정렬 일관성 보장
        normalized_candles = [
            self._normalize_candle_time(candle, timeframe) for candle in candles
        ]

        return self._execute_batch_insert(table_name, normalized_candles)
```

---

## 📅 **Implementation Timeline**

### **Phase 1: 시간 처리 통일** (1일)
- Day 1: TimeUtils 확장 (get_timeframe_seconds, 일관성 보장 메서드)

### **Phase 2: 테이블 관리 시스템** (2일)
- Day 2: CandleTableManager 구현 (동적 생성, 스키마 관리)
- Day 3: CandleRepository 구현 (INSERT OR IGNORE, 시간 정렬)

### **Phase 3: 4단계 최적화 엔진** (3일)
- Day 4: SQLite 호환 쿼리 구현 (파편화, 연결된 끝 찾기)
- Day 5: 4단계 통합 최적화 엔진 구현 (time_utils 통합)
- Day 6: 업비트 API 클라이언트 특화 구현

### **Phase 4: 통합 시스템 구축** (1일)
- Day 7: CandleDataProvider 메인 Facade 구현, 전체 시스템 통합 테스트

**총 기간**: 7일 (시간 통일성 보장으로 안정성 강화)

---

## ✅ **Success Criteria Summary**

### **즉시 검증 가능한 성공 기준**
- [ ] `python run_desktop_ui.py` → 7규칙 전략 생성 → 완전 동작
- [ ] 100개 캔들 조회 P95 < 200ms 달성 (기존 300ms 대비 향상)
- [ ] INSERT OR IGNORE 중복 차단률 100% 달성
- [ ] 4단계 최적화로 API 호출 60% 감소 확인
- [ ] time_utils와 overlap_optimizer 간 시간 계산 100% 일치

### **운영 단계 성공 기준**
- [ ] 캐시 히트율 90% 이상 유지 (기존 85% 대비 향상)
- [ ] 개별 테이블 쿼리 시간 <30ms 지속
- [ ] 30일 동기화 효율성 향상 (API 호출 수 기존 대비 60% 감소)
- [ ] 메모리 사용량 80MB 이하 유지
- [ ] 모든 SQL 쿼리 SQLite 환경에서 정상 동작

### **업비트 특화 성공 기준**
- [ ] 심볼별 개별 테이블 성능 이점 확인 (쿼리 속도 5-10배 향상)
- [ ] candle_date_time_utc PK 기반 중복 완전 차단
- [ ] 200개 제한 최적화로 실효 API 처리량 2배 증대
- [ ] 파편화 감지 정확도 95% 이상 달성
- [ ] 시간 처리 일관성 100% 보장

**🎯 최종 목표**: 업비트 특화 최적화와 통일된 시간 처리로 단순하고 고성능이며 일관성 있는 캔들 데이터 시스템 구축, 7규칙 자동매매 전략의 완벽한 기반 제공

---

## 🔄 **Migration & Compatibility**

### **기존 데이터 마이그레이션**
```python
class DataMigrationManager:
    """기존 통합 테이블 → 개별 테이블 마이그레이션"""

    def __init__(self, time_utils: TimeUtils):
        self.time_utils = time_utils

    def migrate_existing_data(self) -> MigrationResult:
        """기존 candles 테이블을 심볼별로 분할 (시간 정렬 보장)"""

        # 1. 기존 데이터 분석
        symbols_timeframes = self._analyze_existing_data()

        # 2. 개별 테이블 생성 (시간 일관성 보장)
        for symbol, timeframe in symbols_timeframes:
            self._create_and_migrate_table_with_time_alignment(symbol, timeframe)

        # 3. 데이터 무결성 및 시간 일관성 검증
        return self._verify_migration_and_time_consistency()
```

### **호환성 유지**
- **API 호환성**: 기존 `get_candles()` 인터페이스 완전 유지
- **데이터 형식**: 동일한 응답 구조 보장
- **설정 호환성**: 기존 config 파일 그대로 활용
- **시간 호환성**: 기존 시간 계산 결과와 100% 일치 보장

**🎯 핵심 차별점**: v4.0은 업비트 특화 최적화와 통일된 시간 처리로 성능, 안정성, 일관성을 모두 확보한 차세대 캔들 데이터 시스템입니다.
