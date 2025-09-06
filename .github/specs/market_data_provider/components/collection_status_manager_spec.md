# Collection Status Manager 기능 명세

## 개요
- **파일 경로**: `smart_data_provider_V4/collection_status_manager.py`
- **코드 라인 수**: 252줄
- **목적**: 캔들 데이터 수집 상태 관리 및 빈 캔들 처리
- **핵심 기능**: 수집 상태 추적, 빈 캔들 생성, 연속 데이터 보장

## 주요 컴포넌트

### 1. CollectionStatusManager (수집 상태 관리자)
```python
class CollectionStatusManager:
    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        self.logger = create_component_logger("CollectionStatusManager")
```

**데이터베이스 연결**:
- 기본 경로: `data/market_data.sqlite3`
- 테이블: `candle_collection_status`
- Infrastructure 로깅 사용

## 핵심 기능

### 1. 수집 상태 조회 및 업데이트
```python
def get_collection_status(symbol, timeframe, target_time) -> Optional[CollectionStatusRecord]
def update_collection_status(record: CollectionStatusRecord) -> None
```

**특징**:
- **UPSERT 패턴**: INSERT ... ON CONFLICT DO UPDATE 사용
- **상태 추적**: PENDING/COLLECTED/EMPTY/FAILED 상태 관리
- **시간 정밀도**: ISO 포맷으로 datetime 저장/조회

### 2. 미수집 캔들 탐지
```python
def get_missing_candle_times(symbol, timeframe, start_time, end_time) -> List[datetime]
```

**알고리즘**:
1. `generate_candle_times()`로 예상 시간 목록 생성
2. DB에서 기존 수집 상태 조회 (IN 절 사용)
3. PENDING/FAILED 상태 또는 미기록 시간 필터링

**반환**: 수집이 필요한 캔들 시간 목록

### 3. 빈 캔들 처리
```python
def get_empty_candle_times(symbol, timeframe, start_time, end_time) -> List[datetime]
def fill_empty_candles(candles, symbol, timeframe, start_time, end_time) -> List[CandleWithStatus]
```

**빈 캔들 채우기 로직**:
1. **예상 시간 생성**: 전체 시간 범위의 모든 캔들 시간
2. **실제 데이터 매핑**: 시간별 캔들 데이터 인덱싱
3. **빈 캔들 식별**: EMPTY 상태로 마킹된 시간 조회
4. **연속 데이터 생성**:
   - 실제 캔들: 원본 데이터 사용
   - 빈 캔들: 마지막 가격으로 OHLC 생성 (`CandleWithStatus.create_empty()`)

### 4. 수집 상태 마킹
```python
def mark_candle_collected(symbol, timeframe, target_time, api_response_code=200)
def mark_candle_empty(symbol, timeframe, target_time, api_response_code=200)
def mark_candle_failed(symbol, timeframe, target_time, api_response_code=None)
```

**상태 전환 패턴**:
- 기존 레코드 조회 → 상태 업데이트 → DB 저장
- 신규 레코드 시 PENDING 상태로 생성 후 전환
- API 응답 코드 추적 (200, 404 등)

### 5. 수집 상태 요약
```python
def get_collection_summary(symbol, timeframe, start_time, end_time) -> CollectionSummary
```

**요약 정보**:
- `total_expected`: 예상 캔들 총 개수
- `collected_count`: 수집 완료 캔들 수
- `empty_count`: 빈 캔들 수
- `pending_count`: 미수집 캔들 수 (DB 미기록 포함)
- `failed_count`: 수집 실패 캔들 수

## 데이터 모델 의존성

### CollectionStatus (Enum)
- `PENDING`: 수집 대기
- `COLLECTED`: 수집 완료
- `EMPTY`: 빈 캔들 (거래 없음)
- `FAILED`: 수집 실패

### CollectionStatusRecord
- 수집 상태 레코드 (DB 테이블 매핑)
- 상태 전환 메서드 제공

### CandleWithStatus
- 캔들 데이터 + 수집 상태 정보
- `create_empty()`: 빈 캔들 생성 팩토리 메서드

## 기술적 특징

### 데이터베이스 최적화
- **UPSERT 사용**: 중복 삽입 방지
- **IN 절 최적화**: 대량 시간 조회 시 단일 쿼리
- **인덱스 활용**: (symbol, timeframe, target_time) 복합 키

### 빈 캔들 전략
- **마지막 가격 유지**: 빈 캔들의 OHLC는 직전 종가 사용
- **연속성 보장**: 시간 갭 없는 완전한 캔들 시퀀스 제공
- **상태 구분**: `is_empty=True`로 실제/빈 캔들 구분

### 성능 최적화
- **배치 조회**: 시간 범위별 일괄 상태 조회
- **메모리 효율**: 딕셔너리 기반 빠른 룩업
- **DB 연결 관리**: with 문을 통한 자동 연결 해제

## 사용 시나리오

### 1. 캔들 수집 후 상태 업데이트
```python
manager = CollectionStatusManager()

# 수집 성공
manager.mark_candle_collected("KRW-BTC", "1m", target_time, 200)

# 빈 캔들 (거래 없음)
manager.mark_candle_empty("KRW-BTC", "1m", target_time, 200)

# 수집 실패
manager.mark_candle_failed("KRW-BTC", "1m", target_time, 404)
```

### 2. 미수집 캔들 탐지 및 보완
```python
missing_times = manager.get_missing_candle_times(
    "KRW-BTC", "1m", start_time, end_time
)

for time in missing_times:
    # API 호출하여 캔들 수집
    collect_candle_data(time)
```

### 3. 연속 데이터 생성 (빈 캔들 포함)
```python
raw_candles = api.get_candles("KRW-BTC", "1m", start_time, end_time)

continuous_candles = manager.fill_empty_candles(
    raw_candles, "KRW-BTC", "1m", start_time, end_time
)

# 이제 시간 갭 없는 완전한 캔들 시퀀스 사용 가능
```

### 4. 수집 진행상황 모니터링
```python
summary = manager.get_collection_summary(
    "KRW-BTC", "1m", start_time, end_time
)

completion_rate = summary.collected_count / summary.total_expected
print(f"수집 완료율: {completion_rate:.1%}")
```

## 의존성
- **데이터베이스**: sqlite3 (market_data.sqlite3)
- **시간 유틸리티**: `time_utils.generate_candle_times()`
- **데이터 모델**: collection_models 모듈
- **로깅**: Infrastructure 컴포넌트 로거
- **아키텍처 계층**: Infrastructure Layer (DDD)

## 성능 특성
- **DB 최적화**: 복합 인덱스 활용한 빠른 조회
- **배치 처리**: 대량 시간 범위 일괄 처리 지원
- **메모리 효율**: 필요 시점에만 데이터 로드

## 핵심 가치
1. **완전성**: 빈 캔들 채우기로 연속 데이터 보장
2. **추적성**: 모든 캔들의 수집 상태 명확한 기록
3. **복구성**: 실패한 수집 작업 재시도 지원
4. **모니터링**: 수집 진행상황 실시간 추적
