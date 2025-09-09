## 캔들 데이터 제공자 개선 로직

### 파일 구조 (DDD Infrastructure Layer)
```
upbit_auto_trading/
├── domain/
│   └── repositories/
│       └── candle_repository_interface.py      # Repository 인터페이스 (DDD)
├── infrastructure/
│   ├── database/
│   │   └── database_manager.py                 # DB 연결 관리
│   ├── repositories/
│   │   └── sqlite_candle_repository.py         # Repository 구현체
│   ├── external_apis/upbit/
│   │   └── upbit_public_client.py              # 업비트 API 클라이언트
│   └── market_data/candle/
│       ├── candle_data_provider.py             # 메인 Infrastructure Service
│       ├── overlap_analyzer.py                 # API 요청 최적화 엔진
│       ├── time_utils.py                       # 시간 계산 유틸리티
│       ├── candle_cache.py                     # 메모리 캐시 관리
│       └── models.py                           # 데이터 모델 통합
```

### 캔들 제공자 파라미터 (`get_candles()`)
- 시간은 UTC 기준, datetime 형식으로 내부 처리
- 업비트 API 호환: inclusive_start 처리로 사용자 의도 반영
- timeframe 경계 정렬: 캔들 시간 일치성 보장
- 청크 단위 처리: 200개 제한, 순차 수집

#### 입력 파라미터
- `symbol`: 거래 심볼 (예: KRW-BTC)
- `timeframe`: 타임프레임 (1m, 5m, 15m, 1h, 1d)
- `count`: 요청 캔들 개수 (최대 제한 없음, 자동 청크 분할)
- `start_time`: 시작 시간 (사용자 제공시 inclusive_start 적용)
- `end_time`: 종료 시간 (항상 포함)
- `inclusive_start`: 시작 시간 포함 여부 (기본값 True)

#### 지원하는 5가지 파라미터 케이스
1. **count만**: 최근 count개 캔들
2. **start_time + count**: 시작점부터 count개
3. **start_time + end_time**: 시간 범위 (count 자동 계산)
4. **end_time만**: 현재시간부터 end_time까지
5. **기본값**: count=200 (케이스 1과 동일)

#### 금지 조합
- **count + end_time**: 상호 배타적, ValidationError

#### 대량 요청 청크 처리
- 기본 청크 크기: 200개 (업비트 API 제한)
- 최대 청크 수: 2000개 (시스템 부하 고려, 4백만 캔들, 1분봉 기준 약 9개월)
- 순차 처리: target_end_time 도달시 자동 중단
- 겹침 분석: 각 청크별 DB/API 혼합 최적화
- **동적 계획**: 처음부터 모든 계획을 세우지 않고 청크별 겹침 분석으로 다음 청크 시작을 재계산
- **정지 조건**: `total_remain_count -= processed_count` 도달시 정지

#### 청크 시간 처리 규칙
- **첫 청크 시작 시간**: 입력 시간을 정렬 없이 사용 (사용자 의도 보존)
- **다음 청크들**: 자연스럽게 정렬된 시간 사용 (계산된 마지막 시간이 정렬되므로)
- **API 요청 시간**: 마지막 rest api 클라이언트 요청시만 `start_time + dt` 조정

### 시간 계산 시스템

#### 표준화 변수 체계
- `request_start_time`: 사용자 원본 시작 시간 (to 요청된 원래 시작 시간)
- `request_end_time`: 사용자 원본 종료 시간
- `recent_start_time`: 요청된 시작 시간이 없을 때 현재 시간
- `align_start_time`: 정렬된 시작 시간
- `target_start_time`: 계산된 목표 시작 시간 (expect_start_time)
- `target_end_time`: 계산된 목표 종료 시간 (expect_end_time)
- `api_start_time`: API 요청용 조정된 시작 시간

#### 청크 처리 상태 변수
- `expect_api_calls`: 예상 API 호출 횟수 (절대 정지 조건)
- `total_remain_count`: 남은 전체 캔들 수
- `total_count`: 총 요청 캔들 수
- `processed_count`: 처리 완료된 캔들 수

#### TimeUtils 핵심 메서드
- `determine_target_end_time()`: 5가지 파라미터 조합을 표준화된 시간 범위로 변환
- `_align_to_candle_boundary()`: timeframe에 맞는 캔들 경계 정렬
- `get_timeframe_seconds()`: timeframe을 초 단위로 변환
- `calculate_chunk_boundaries()`: 대량 요청을 200개 청크로 분할
- `adjust_start_from_connection()`: 연결된 데이터 끝점 기준 시작점 조정

#### inclusive_start 처리 로직
- **사용자 제공 start_time만 조정**: 케이스 2,3에서만 적용
- **inclusive_start=True**: start_time을 포함하도록 이전 캔들 시간으로 조정
- **inclusive_start=False**: API 네이티브 배제 방식 유지
- **시스템 자동 계산 시간**: 조정 없이 그대로 사용

### 겹침 분석 시스템 (OverlapAnalyzer)

#### 입력 파라미터
- `symbol`: 거래 심볼
- `timeframe`: 타임프레임
- `target_start`: 요청 시작 시간
- `target_count`: 요청 캔들 개수

#### 출력 결과 (OverlapResult)
- `status`: 겹침 상태 (NO_OVERLAP, PARTIAL_OVERLAP, COMPLETE_OVERLAP)
- `connected_end`: 연속된 데이터의 끝점

#### Repository 의존 메서드
- `has_any_data_in_range()`: 범위 내 데이터 존재 확인 (LIMIT 1 최적화)
- `is_range_complete()`: 완전 겹침 확인 (COUNT vs expected)
- `find_last_continuous_time()`: 연속된 데이터 끝점 찾기
- `has_data_in_start()`: 시작점 데이터 존재 확인
- `is_continue_till_end()`: 끝점까지 연속성 확인

#### 겹침 상태별 처리 전략 (상세 분류)

##### 1. 겹침 없음 (NO_OVERLAP)
```
DB: |------|  (데이터 없음)
요청: [target_start ===== target_end]
```
- **조건**: `has_any_data_in_range() = false`
- **처리**: 전체 구간 API 요청 → DB 저장 → 제공

##### 2. 겹침 있음 (HAS_OVERLAP)
```
DB: |--1---|  (일부 데이터 존재)
요청: [target_start ===== target_end]
```
- **조건**: `has_any_data_in_range() = true`

###### 2.1 완전 겹침 (COMPLETE_OVERLAP)
```
DB: |111111111111111111111|
요청: [target_start === target_end]
```
- **조건**: `is_range_complete() = true`
- **처리**: DB에서만 조회 → 제공 (API 요청 없음)

###### 2.2 일부 겹침 (PARTIAL_OVERLAP)
```
DB: |11--11|  (부분 데이터 존재)
요청: [target_start ===== target_end]
```
- **조건**: `is_range_complete() = false`

####### 2.2.1 시작 겹침 (START_OVERLAP)
```
DB: |11----| or |11-1--|
요청: [target_start ===== target_end]
```
- **조건**: `has_data_in_start() = true`
- **로직**: 연결된 데이터의 끝 찾기 `partial_end`
- **처리**: `[partial_end + dt, target_end]` API 요청, 기존 데이터와 병합

####### 2.2.2 중간 겹침 (MIDDLE_OVERLAP)
```
DB: |--11--| or |--1111| or |--1-11|
요청: [target_start ===== target_end]
```
- **조건**: `has_data_in_start() = false`
- **로직**: 데이터 시작점 찾기 `partial_start`, 연결된 끝점 탐색 `partial_end`

######## 2.2.2.1 파편 겹침 (FRAGMENTED_OVERLAP)
```
DB: |--1-11| or |--1-1-|
요청: [target_start ===== target_end]
```
- **조건**: `is_continue_till_end() = false` (2번 Gap 감지)
- **처리**: 전체 구간 API 요청 (복잡도 증가 방지)

######## 2.2.2.2 말단 겹침 (END_OVERLAP)
```
DB: |--1111|
요청: [target_start ===== target_end]
```
- **조건**: `is_continue_till_end() = true` (목표 끝까지 연속)
- **처리**: `[target_start, partial_start + dt]` API 요청, 기존 데이터와 병합

### 청크 분할 및 수집 시스템

#### CandleChunk 모델
- `symbol`: 거래 심볼
- `timeframe`: 타임프레임
- `start_time`: 청크 시작 시간
- `count`: 청크 내 캔들 개수 (최대 200개)
- `chunk_index`: 청크 순서

#### 청크 분할 로직 (`_split_into_chunks()`)
- **분할 방향**: end_time → start_time (최신부터 과거로)
- **청크 크기**: 200개 (업비트 API 최대 제한)
- **중단 조건**: 2000개 청크 또는 start_time 도달

#### 순차 수집 로직 (`_collect_chunks_sequentially()`)
- **target_end_time 도달시 중단**: 불필요한 API 요청 방지
- **겹침 분석 연동**: 각 청크별 최적화 전략 결정
- **Rate Limiting**: API 요청시 100ms 지연

#### 단일 청크 처리 (`_collect_single_chunk()`)
- **NO_OVERLAP**: `_collect_from_api_only()` → API 요청 → DB 저장
- **COMPLETE_OVERLAP**: `_collect_from_db_only()` → DB 조회만
- **PARTIAL_OVERLAP**: `_collect_mixed_optimized()` → DB/API 혼합

### Repository 인터페이스 (DDD 준수)

#### OverlapAnalyzer 지원 메서드
- `has_any_data_in_range()`: 범위 내 데이터 존재 확인
- `is_range_complete()`: 완전성 확인
- `find_last_continuous_time()`: 연속 끝점 탐색
- `get_data_ranges()`: 기존 데이터 범위 조회

#### CandleDataProvider 지원 메서드
- `ensure_table_exists()`: 캔들 테이블 생성
- `save_candle_chunk()`: 청크 단위 저장 (INSERT OR IGNORE)
- `get_candles_by_range()`: 범위별 캔들 조회
- `count_candles_in_range()`: 범위 내 캔들 개수

### 캐시 관리 시스템 (CandleCache)

#### 캐시 구조
- **LRU + TTL 하이브리드**: 60초 TTL + 메모리 기반 LRU
- **완전 범위 확인**: `has_complete_range()` → 즉시 반환
- **청크 단위 저장**: `store_chunk()` → 범위별 캐시

#### 캐시 핵심 메서드
- `get_cached_chunk()`: 청크 단위 캐시 조회
- `store_chunk()`: 청크 단위 캐시 저장
- `has_complete_range()`: 완전 데이터 존재 확인
- `clear_expired()`: 만료된 엔트리 정리
- `_ensure_memory_space()`: LRU 방식 메모리 관리

#### 캐시 키 구조 (CacheKey)
- `symbol`: 거래 심볼
- `timeframe`: 타임프레임
- `start_time`: 시작 시간
- `count`: 캔들 개수

### API 클라이언트 연동 (UpbitPublicClient)

#### API 요청 메서드 (`_call_upbit_api()`)
- **Rate Limiting**: 100ms 간격 요청
- **파라미터 변환**: datetime → ISO 문자열
- **응답 변환**: API 응답 → CandleData 모델
- **에러 처리**: API 오류시 재시도 로직

#### 업비트 API 호환성
- **to 파라미터**: API 요청시 start_time + dt 조정
- **count 제한**: 최대 200개
- **시간 형식**: ISO 8601 UTC 문자열
- **응답 정렬**: 최신순 (latest → past)

### 응답 조합 시스템

#### CandleDataResponse 모델
- `success`: 성공 여부
- `candles`: CandleData 리스트 (시간순 정렬)
- `total_count`: 총 개수
- `data_source`: 데이터 소스 ("cache", "db", "api", "mixed")
- `response_time_ms`: 응답 시간
- `error_message`: 에러 메시지 (실패시)

#### 응답 조합 로직 (`_assemble_response()`)
- **데이터 병합**: 모든 청크 데이터 통합
- **중복 제거**: 시간 기준 중복 캔들 제거
- **시간순 정렬**: candle_date_time_utc 기준
- **통계 수집**: API 요청수, 캐시 히트율, 응답 시간

### 성능 모니터링

#### 통계 수집 항목
- `total_requests`: 총 요청 수
- `cache_hits`: 캐시 히트 수
- `api_requests`: API 요청 수
- `mixed_optimizations`: 혼합 최적화 횟수
- `api_requests_saved`: 절약된 API 요청 수
- `average_response_time_ms`: 평균 응답 시간

#### 로깅 시스템
- **요청 시작**: 파라미터와 요청 ID 로깅
- **청크 처리**: 각 청크별 처리 결과 로깅
- **겹침 분석**: 최적화 효과 로깅
- **응답 완료**: 최종 통계와 성능 지표 로깅

### 에러 처리 전략

#### 검증 에러 (ValidationError)
- **파라미터 조합**: count + end_time 동시 사용
- **미래 시간**: start_time/end_time이 현재 시간보다 미래
- **음수 count**: count <= 0
- **timeframe 형식**: 지원하지 않는 timeframe

#### API 에러 처리
- **Rate Limit**: 지수 백오프 재시도
- **Network Error**: 연결 재시도 (최대 3회)
- **Invalid Response**: 응답 형식 오류시 로깅 후 계속

#### DB 에러 처리
- **Connection Error**: 연결 풀 재시도
- **Query Error**: 쿼리 오류 로깅 후 빈 결과 반환
- **Table Missing**: 자동 테이블 생성 시도

### 팩토리 함수

#### `create_candle_data_provider()`
- **동기 버전**: 기본 의존성으로 인스턴스 생성
- **의존성 주입**: db_manager, upbit_client 선택적 주입

#### `create_candle_data_provider_async()`
- **비동기 버전**: 비동기 컨텍스트에서 사용
- **자동 리소스 관리**: __aenter__/__aexit__ 지원
