# 🚀 CandleDataProvider 구현 태스크 분해 - Ryan-Style 3-Step Phase 2 (단순화 버전)

## 📋 **프로젝트 개요**
- **목표**: 단일 `candle/` 폴더에 9개 파일로 캔들 전용 시스템 구축
- **아키텍처**: 래퍼 패턴 + 직접 복사로 89% 코드 재사용
- **총 라인 수**: 1,424줄 (재사용 1,277줄 + 신규 147줄)
- **예상 기간**: 9일 (단순화로 2일 추가 단축)

---

## 🎯 **Phase 1: 기존 모듈 복사 & 기본 구조** (Day 1-2)

### **1. 단일 폴더 구조 생성 및 기존 모듈 복사**
- **Description**: `candle/` 단일 폴더에 9개 파일 구조 생성 후 검증된 모듈 직접 복사
- **Acceptance Criteria**:
  - [ ] `upbit_auto_trading/infrastructure/market_data/candle/` 폴더 생성
  - [ ] overlap_analyzer.py 복사 (200줄) - 수정 없이 완전 재사용
  - [ ] time_utils.py 복사 (74줄) - 수정 없이 완전 재사용
  - [ ] models.py 생성 - ResponseModels + CacheModels + 캔들 모델 통합
  - [ ] exceptions.py 생성 - 캔들 전용 예외 클래스
  - [ ] __init__.py 생성 - CandleDataProvider 메인 API 노출
- **Test Plan**:
  ```python
  from candle.overlap_analyzer import OverlapAnalyzer
  from candle.time_utils import generate_candle_times
  from candle.models import DataResponse, Priority
  from candle.exceptions import InvalidParameterError

  # 기본 import 테스트
  analyzer = OverlapAnalyzer()
  assert analyzer is not None
  ```
- **Risk & Rollback**: import 오류시 상대 경로 수정, 원본 V4 백업 유지
- **Effort**: 2시간 (복사 + 기본 구조)
- **Touch Points**:
  - `candle/overlap_analyzer.py` (복사)
  - `candle/time_utils.py` (복사)
  - `candle/models.py` (신규)
  - `candle/exceptions.py` (신규)

### **1.1 CandleDataProvider 메인 Facade 기본 구조**
- **Description**: 모든 기능의 진입점인 메인 Facade 클래스 기본 틀 구현
- **Acceptance Criteria**:
  - [ ] CandleDataProvider 클래스 생성 (300줄 목표)
  - [ ] 의존성 주입 패턴: CandleClient, CandleStorage, CandleCache, CandleStatus
  - [ ] get_candles() 메서드 기본 구조 (TODO 마커 포함)
  - [ ] sync_candles() 메서드 기본 구조
  - [ ] Infrastructure 로깅 (create_component_logger) 적용
  - [ ] DataResponse 기반 응답 구조
- **Test Plan**:
  ```python
  provider = CandleDataProvider()
  assert provider.client is not None  # 의존성 주입 확인
  assert provider.storage is not None
  assert provider.cache is not None
  assert provider.status is not None
  assert provider.overlap_analyzer is not None
  ```
- **Risk & Rollback**: 의존성 순환 참조 발생시 인터페이스 분리
- **Effort**: 3시간 (메인 클래스 설계)
- **Touch Points**: `candle/candle_data_provider.py`

### **1.2 기본 모델 및 예외 클래스 구현**
- **Description**: 통합 모델과 캔들 전용 예외 클래스 완성
- **Acceptance Criteria**:
  - [ ] DataResponse, DataSourceInfo, Priority 모델 구현
  - [ ] CacheMetrics, CandleCollectionSummary 모델 구현
  - [ ] InvalidParameterError, CacheError, StorageError 예외 구현
  - [ ] 모든 모델에 타입 힌트 적용
  - [ ] frozen=True dataclass로 불변성 보장 (필요시)
- **Test Plan**:
  ```python
  # 모델 테스트
  response = DataResponse(success=True, data={'test': 'data'})
  assert response.success == True

  # 예외 테스트
  with pytest.raises(InvalidParameterError):
      raise InvalidParameterError("테스트 파라미터 오류")
  ```
- **Risk & Rollback**: 모델 설계 오류시 기존 V4 모델 그대로 사용
- **Effort**: 1시간 (모델 통합)
- **Touch Points**: `candle/models.py`, `candle/exceptions.py`

---

## 🔧 **Phase 2: 래퍼 클래스 구현 - API & DB** (Day 3-4)

### **2. CandleClient 구현 - upbit_public_client 래퍼**
- **Description**: 업비트 API 파라미터 검증 특화 클라이언트 래퍼 구현
- **Acceptance Criteria**:
  - [ ] UpbitPublicClient 인스턴스 생성 및 래핑
  - [ ] get_candles_minutes() 메서드: unit 검증 [1,3,5,15,10,30,60,240]
  - [ ] get_candles_days() 메서드: 일봉 조회 지원
  - [ ] validate_parameters() 파라미터 검증 로직
    - count ≤ 200 검증
    - market 형식 검증 (KRW-BTC 패턴)
    - to ISO 8601 형식 검증 (2023-01-01T00:00:00Z)
  - [ ] 일관된 ValueError 메시지 ("지원하지 않는 분봉 단위", "최대 200개" 등)
  - [ ] API 호출 성공/실패 로깅
- **Test Plan**:
  ```python
  client = CandleClient()

  # 정상 케이스
  candles = await client.get_candles_minutes("KRW-BTC", 1, 100)
  assert len(candles) <= 100

  # 오류 케이스
  with pytest.raises(InvalidParameterError, match="지원하지 않는 분봉 단위"):
      await client.get_candles_minutes("KRW-BTC", 2, 100)

  with pytest.raises(InvalidParameterError, match="최대 200개"):
      await client.get_candles_minutes("KRW-BTC", 1, 300)
  ```
- **Risk & Rollback**: API 검증 로직 오류시 기본 검증으로 단순화
- **Effort**: 3시간 (파라미터 검증 + 테스트)
- **Touch Points**: `candle/candle_client.py`

### **2.1 CandleStorage 구현 - BatchDBManager 래퍼**
- **Description**: BatchDBManager의 캔들 전용 래퍼로 배치 저장 최적화
- **Acceptance Criteria**:
  - [ ] BatchDBManager 인스턴스 생성 및 DB 연결 팩토리 설정
  - [ ] save_candles_batch() 메서드: insert_candles_batch() 직접 활용
  - [ ] get_candles_from_db() 메서드: 시간 범위별 캔들 조회
  - [ ] get_latest_candle_time() 메서드: 동기화 시작점 결정
  - [ ] 업비트 API 응답 → 표준 캔들 스키마 변환 확인
  - [ ] 배치 크기 1000개, 우선순위 NORMAL 설정
  - [ ] 저장 성공/실패 로깅 (operation_id 포함)
- **Test Plan**:
  ```python
  storage = CandleStorage()

  # 배치 저장 테스트
  sample_candles = [{'market': 'KRW-BTC', 'opening_price': 50000000, ...}]
  operation_id = await storage.save_candles_batch("KRW-BTC", "1m", sample_candles)
  assert operation_id != ""

  # DB 조회 테스트
  start_time = datetime(2023, 1, 1)
  end_time = datetime(2023, 1, 2)
  candles = await storage.get_candles_from_db("KRW-BTC", "1m", start_time, end_time)
  assert isinstance(candles, list)
  ```
- **Risk & Rollback**: BatchDBManager 통합 실패시 개별 INSERT로 폴백
- **Effort**: 3시간 (래퍼 구현 + DB 테스트)
- **Touch Points**: `candle/candle_storage.py`

### **2.2 CandleCache 구현 - FastCache 래퍼**
- **Description**: FastCache의 캔들 전용 래퍼로 60초 TTL 최적화
- **Acceptance Criteria**:
  - [ ] FastCache 인스턴스 생성 (default_ttl=60.0)
  - [ ] get_cached_candles() 메서드: 캐시 키로 캔들 조회
  - [ ] cache_candles() 메서드: 캔들 데이터 + 메타데이터 저장
  - [ ] generate_cache_key() 메서드: "KRW-BTC_1m_100_abc123" 형식
  - [ ] get_cache_stats() 메서드: hit_rate, total_requests 등 성능 지표
  - [ ] cleanup_expired() 메서드: 만료된 캐시 정리
  - [ ] 캐시 히트/미스 로깅
- **Test Plan**:
  ```python
  cache = CandleCache()

  # 캐시 키 생성 테스트
  key = cache.generate_cache_key("KRW-BTC", "1m", 100)
  assert key == "KRW-BTC_1m_100"

  # 캐시 저장/조회 테스트
  sample_candles = [{'market': 'KRW-BTC', ...}]
  cache.cache_candles(key, sample_candles)

  cached = cache.get_cached_candles(key)
  assert cached == sample_candles

  # TTL 테스트 (60초 후 만료)
  ```
- **Risk & Rollback**: TTL 너무 길면 30초로 조정, 캐시 실패시 바로 API 호출
- **Effort**: 2시간 (캐시 래퍼 + TTL 테스트)
- **Touch Points**: `candle/candle_cache.py`

---

## ⚡ **Phase 3: 상태 관리 & 지능형 최적화** (Day 5-6)

### **3. CandleStatus 구현 - CollectionStatusManager 래퍼**
- **Description**: 데이터 무결성 보장을 위한 수집 상태 관리 래퍼
- **Acceptance Criteria**:
  - [ ] CollectionStatusManager 인스턴스 생성 및 래핑
  - [ ] track_collection_status() 메서드: COLLECTED/EMPTY/FAILED 상태 추적
  - [ ] get_missing_times() 메서드: 미수집 캔들 시간 반환
  - [ ] fill_empty_candles() 메서드: 빈 캔들 자동 채우기
  - [ ] get_quality_summary() 메서드: 수집률, 빈 캔들 비율 등 품질 지표
  - [ ] 상태 변경 로깅 (PENDING → COLLECTED 등)
  - [ ] 빈 캔들 추가시 개수 로깅
- **Test Plan**:
  ```python
  status = CandleStatus()

  # 상태 추적 테스트
  await status.track_collection_status("KRW-BTC", "1m", datetime.now(), "COLLECTED")

  # 미수집 데이터 감지 테스트
  missing = await status.get_missing_times("KRW-BTC", "1m", start_time, end_time)
  assert isinstance(missing, list)

  # 빈 캔들 채우기 테스트
  sample_candles = [candle1, candle3]  # candle2 누락
  filled = await status.fill_empty_candles(sample_candles, "KRW-BTC", "1m", start, end)
  assert len(filled) > len(sample_candles)  # 빈 캔들 추가됨
  ```
- **Risk & Rollback**: 빈 캔들 생성 실패시 원본 데이터 그대로 반환
- **Effort**: 3시간 (상태 관리 래퍼 + 빈 캔들 테스트)
- **Touch Points**: `candle/candle_status.py`

### **3.1 CandleDataProvider 메인 로직 구현 - OverlapAnalyzer 통합**
- **Description**: 지능형 최적화를 포함한 메인 get_candles() 로직 완성
- **Acceptance Criteria**:
  - [ ] get_candles() 메서드 완전 구현:
    1. 파라미터 검증 (CandleClient 활용)
    2. 캐시 키 생성 및 확인 (CandleCache)
    3. OverlapAnalyzer로 최적 전략 결정
       - PERFECT_MATCH: 캐시 데이터 반환
       - FORWARD_EXTEND: 부분 API 호출 + 캐시 병합
       - BACKWARD_EXTEND: 과거 데이터 추가 요청
       - SPLIT_REQUEST: 큰 요청을 효율적 분할
    4. API 호출 (필요시)
    5. DB 저장 (CandleStorage.save_candles_batch)
    6. 상태 업데이트 (CandleStatus.track_collection_status)
    7. 빈 캔들 채우기 (CandleStatus.fill_empty_candles)
    8. 캐시 저장
    9. DataResponse 생성 (소스 정보 포함)
  - [ ] 전략별 로깅: "strategy=EXTEND_CACHE, api_calls=1, cache_hit=85%"
  - [ ] 오류 처리 및 폴백 전략 구현
- **Test Plan**:
  ```python
  provider = CandleDataProvider()

  # 정상 케이스
  response = await provider.get_candles("KRW-BTC", "1m", 100)
  assert response.success == True
  assert len(response.data.get('candles', [])) == 100

  # 캐시 효율성 테스트
  response2 = await provider.get_candles("KRW-BTC", "1m", 100)  # 동일 요청
  assert response2.data_source.channel == "cache"  # 캐시에서 반환

  # OverlapAnalyzer 효과 테스트
  response3 = await provider.get_candles("KRW-BTC", "1m", 150)  # 확장 요청
  # 로그에서 "strategy=FORWARD_EXTEND" 확인
  ```
- **Risk & Rollback**: OverlapAnalyzer 실패시 기본 캐시 확인 → API 호출로 폴백
- **Effort**: 5시간 (복잡한 오케스트레이션 로직)
- **Touch Points**: `candle/candle_data_provider.py`

### **3.2 대용량 동기화 시스템 구현**
- **Description**: sync_candles() 메서드로 누락 데이터 일괄 보완
- **Acceptance Criteria**:
  - [ ] sync_candles() 메서드 구현
  - [ ] 기간별 미수집 데이터 감지 (CandleStatus.get_missing_times)
  - [ ] 배치 단위 분할 수집 (200개씩)
  - [ ] 진행률 추적 및 로깅 ("동기화 진행: 1000/5000 (20%)")
  - [ ] 실패한 배치 재시도 로직 (3회 시도)
  - [ ] 동기화 완료 후 품질 리포트 생성
- **Test Plan**:
  ```python
  # 대용량 동기화 테스트
  success = await provider.sync_candles("KRW-BTC", "1m", days=7)
  assert success == True

  # 품질 리포트 확인
  report = await provider.get_quality_report("KRW-BTC", "1m")
  assert report['collection_rate'] > 95.0  # 95% 이상 수집
  ```
- **Risk & Rollback**: 동기화 실패시 부분 성공 결과라도 반환
- **Effort**: 2시간 (배치 처리 + 진행률 추적)
- **Touch Points**: `candle/candle_data_provider.py`

---

## 🛡️ **Phase 4: 오류 처리 & 데이터 품질** (Day 7-8)

### **4. 포괄적 오류 처리 시스템**
- **Description**: API 오류, 네트워크 실패, 데이터 오류 등 모든 예외 상황 처리
- **Acceptance Criteria**:
  - [ ] Rate Limit (429) 오류: 자동 백오프 및 재시도 (1s, 2s, 4s)
  - [ ] API 서버 오류 (500, 503): 3회 재시도 후 캐시/DB 폴백
  - [ ] 네트워크 타임아웃: 부분 데이터라도 반환
  - [ ] 데이터 검증 오류: 잘못된 형식 데이터 필터링
  - [ ] DB 저장 실패: 메모리 임시 저장 → 재시도
  - [ ] 모든 오류 상황에서 적절한 DataResponse 반환
  - [ ] 오류율 추적 및 임계값 초과시 알림
- **Test Plan**:
  ```python
  # API 오류 시뮬레이션
  with mock.patch('upbit_client.get_candles_minutes', side_effect=TimeoutError):
      response = await provider.get_candles("KRW-BTC", "1m", 100)
      assert response.success == True  # DB 폴백 성공
      assert response.data_source.channel == "cache"

  # Rate Limit 시뮬레이션
  with mock.patch('upbit_client.get_candles_minutes', side_effect=HTTPError(429)):
      response = await provider.get_candles("KRW-BTC", "1m", 100)
      # 자동 재시도 후 성공 확인
  ```
- **Risk & Rollback**: 모든 폴백 실패시 빈 응답이라도 시스템 중단 방지
- **Effort**: 4시간 (다양한 오류 시나리오 + 테스트)
- **Touch Points**: `candle/candle_data_provider.py`, `candle/candle_client.py`

### **4.1 데이터 품질 보증 시스템**
- **Description**: 데이터 무결성 검증 및 품질 지표 모니터링
- **Acceptance Criteria**:
  - [ ] 캔들 데이터 검증 로직: OHLC 관계, 거래량 음수 체크 등
  - [ ] 시간 연속성 검증: 시간 순서, 중복 시간 체크
  - [ ] 빈 캔들 자동 보완 비율 모니터링 (5% 이하 유지)
  - [ ] 수집 완성도 실시간 추적 (95% 이상 목표)
  - [ ] 품질 지표 주기적 리포트 (1시간마다)
  - [ ] 품질 임계값 위반시 경고 로그
- **Test Plan**:
  ```python
  # 데이터 검증 테스트
  invalid_candle = {'opening_price': 100, 'high_price': 50, ...}  # high < open (잘못됨)
  valid_candles = provider._validate_candle_data([invalid_candle])
  assert len(valid_candles) == 0  # 잘못된 데이터 필터링됨

  # 품질 리포트 테스트
  report = await provider.get_quality_report("KRW-BTC", "1m")
  assert report['data_quality_score'] > 95.0
  assert report['empty_rate'] < 5.0
  ```
- **Risk & Rollback**: 검증 로직 오류시 기본 데이터 반환, 검증 단계 스킵
- **Effort**: 3시간 (데이터 검증 + 품질 지표)
- **Touch Points**: `candle/candle_status.py`, `candle/candle_data_provider.py`

---

## 🧪 **Phase 5: 테스트 & 성능 최적화** (Day 9)

### **5. 포괄적 테스트 스위트**
- **Description**: 단위 테스트, 통합 테스트, 성능 테스트 작성
- **Acceptance Criteria**:
  - [ ] 단위 테스트 (각 클래스별):
    - CandleClient: 파라미터 검증, API 호출
    - CandleStorage: 배치 저장, DB 조회
    - CandleCache: 캐시 저장/조회, TTL 만료
    - CandleStatus: 상태 추적, 빈 캔들 채우기
    - CandleDataProvider: 메인 로직, 오케스트레이션
  - [ ] 통합 테스트: 전체 플로우 시나리오
  - [ ] 성능 테스트: 응답시간, 처리량, 메모리 사용량
  - [ ] 부하 테스트: 100 req/sec 동시 처리
  - [ ] 테스트 커버리지 90% 이상
- **Test Plan**:
  ```bash
  # 단위 테스트 실행
  pytest candle/test_candle_client.py -v
  pytest candle/test_candle_storage.py -v
  pytest candle/test_candle_cache.py -v
  pytest candle/test_candle_status.py -v
  pytest candle/test_candle_data_provider.py -v

  # 통합 테스트
  pytest candle/test_integration.py -v

  # 성능 테스트
  pytest candle/test_performance.py -v

  # 커버리지 확인
  pytest candle/ --cov=candle --cov-report=html
  ```
- **Risk & Rollback**: 테스트 실패시 해당 기능 수정 후 재테스트
- **Effort**: 4시간 (포괄적 테스트 작성)
- **Touch Points**: `candle/tests/` 전체

### **5.1 성능 최적화 및 최종 검증**
- **Description**: 목표 성능 지표 달성 확인 및 최적화
- **Acceptance Criteria**:
  - [ ] 응답 시간 목표 달성:
    - 캐시 히트: P95 < 5ms
    - DB 히트: P95 < 50ms
    - API 호출: P95 < 300ms
  - [ ] 처리량: 100 requests/second 지원
  - [ ] 메모리 사용량: < 100MB 유지
  - [ ] API 호출 감소: OverlapAnalyzer로 50% 감소 확인
  - [ ] 캐시 히트율: > 85% 달성
  - [ ] 데이터 품질: 수집률 > 95%, 빈 캔들 < 5%
  - [ ] 7규칙 전략 호환성: `python run_desktop_ui.py` 완전 동작
- **Test Plan**:
  ```python
  # 성능 벤치마크
  async def performance_test():
      start_time = time.time()

      # 100개 동시 요청
      tasks = [provider.get_candles("KRW-BTC", "1m", 100) for _ in range(100)]
      responses = await asyncio.gather(*tasks)

      elapsed = time.time() - start_time
      assert elapsed < 1.0  # 1초 이내 완료

      # 성공률 확인
      success_count = sum(1 for r in responses if r.success)
      assert success_count >= 95  # 95% 이상 성공

      # 캐시 효율성 확인
      cache_stats = provider.cache.get_cache_stats()
      assert cache_stats['hit_rate'] > 85.0

  # 7규칙 전략 호환성 테스트
  def test_7_rules_compatibility():
      # RSI, 이동평균 등 계산용 캔들 데이터 제공 확인
      candles = await provider.get_candles("KRW-BTC", "1m", 200)
      assert len(candles.data['candles']) == 200

      # 데이터 형식 확인 (OHLCV)
      first_candle = candles.data['candles'][0]
      required_fields = ['opening_price', 'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']
      for field in required_fields:
          assert field in first_candle
  ```
- **Risk & Rollback**: 성능 목표 미달시 캐시 TTL 조정, 배치 크기 최적화
- **Effort**: 3시간 (성능 측정 + 최적화 + 최종 검증)
- **Touch Points**: 전체 시스템 성능

---

## 📊 **성공 기준 및 검증 지표**

### **기능적 성공 기준**
- [ ] **API 완전성**: get_candles() 모든 파라미터 조합 동작
- [ ] **데이터 무결성**: 빈 캔들 자동 채우기로 연속성 100% 보장
- [ ] **캐시 효율성**: 85% 이상 히트율 달성
- [ ] **오류 복구**: API 장애시 캐시/DB 폴백으로 가용성 99.9%
- [ ] **7규칙 호환성**: RSI, 이동평균 등 모든 전략 지원

### **성능 성공 기준**
- [ ] **응답 시간**: 캐시 5ms, DB 50ms, API 300ms (P95 기준)
- [ ] **API 최적화**: OverlapAnalyzer로 50% 호출 감소
- [ ] **처리량**: 100 req/sec 동시 처리
- [ ] **메모리 효율**: 100MB 이하 안정적 사용

### **품질 성공 기준**
- [ ] **테스트 커버리지**: 90% 이상
- [ ] **코드 재사용**: 89% 기존 검증된 코드 활용
- [ ] **복잡도 관리**: 9개 파일, 단일 폴더 구조
- [ ] **데이터 품질**: 수집률 95%, 빈 캔들 5% 이하

---

## 🚨 **리스크 관리 계획**

### **High Risk**
1. **OverlapAnalyzer 통합 복잡성**
   - **Mitigation**: 단계별 구현, PERFECT_MATCH부터 시작
   - **Contingency**: 겹침 분석 실패시 단순 캐시 확인만 수행

2. **래퍼 클래스 의존성 문제**
   - **Mitigation**: 각 래퍼별 독립적 테스트, 인터페이스 명확화
   - **Contingency**: 래퍼 문제시 기존 모듈 직접 사용

### **Medium Risk**
1. **성능 목표 미달성**
   - **Mitigation**: 단계별 성능 측정, 조기 최적화
   - **Contingency**: TTL 조정, 배치 크기 조정

2. **데이터 품질 이슈**
   - **Mitigation**: 철저한 검증 로직, 단계별 품질 확인
   - **Contingency**: 검증 실패시 원본 데이터 반환

### **Low Risk**
1. **API 파라미터 검증 누락**
   - **Mitigation**: upbit_public_client 표준 완전 준수
   - **Contingency**: 검증 실패시 기본값으로 요청

---

## 📅 **상세 일정 계획**

| Day | Phase | 주요 작업 | 예상 시간 | 중요도 | 완료 기준 |
|-----|-------|-----------|----------|--------|-----------|
| 1 | 1 | 모듈 복사 + 폴더 구조 | 2시간 | ⭐⭐⭐ | import 성공 |
| 1 | 1 | CandleDataProvider 기본 구조 | 3시간 | ⭐⭐⭐ | 의존성 주입 완료 |
| 2 | 1 | 모델 + 예외 클래스 | 1시간 | ⭐⭐ | 타입 힌트 완료 |
| 2 | 2 | CandleClient 구현 | 3시간 | ⭐⭐⭐ | 파라미터 검증 완료 |
| 3 | 2 | CandleStorage 구현 | 3시간 | ⭐⭐⭐ | 배치 저장 성공 |
| 3 | 2 | CandleCache 구현 | 2시간 | ⭐⭐ | TTL 60초 동작 |
| 4 | 3 | CandleStatus 구현 | 3시간 | ⭐⭐⭐ | 빈 캔들 채우기 |
| 5 | 3 | 메인 로직 + OverlapAnalyzer | 5시간 | ⭐⭐⭐ | API 최적화 동작 |
| 6 | 3 | 대용량 동기화 | 2시간 | ⭐⭐ | 배치 처리 완료 |
| 7 | 4 | 오류 처리 시스템 | 4시간 | ⭐⭐⭐ | 모든 폴백 동작 |
| 8 | 4 | 데이터 품질 시스템 | 3시간 | ⭐⭐ | 품질 95% 달성 |
| 9 | 5 | 테스트 + 성능 최적화 | 7시간 | ⭐⭐⭐ | 모든 목표 달성 |

**총 소요시간**: 37시간 (9일 × 4시간/일 평균)

---

## ✅ **체크포인트 및 승인 기준**

### **Phase 1 완료 승인 (Day 2 완료)**
- [ ] 9개 파일 모두 정상 import
- [ ] CandleDataProvider 기본 인스턴스 생성 성공
- [ ] 모든 의존성 주입 완료
- [ ] Infrastructure 로깅 정상 동작

### **Phase 2 완료 승인 (Day 4 완료)**
- [ ] CandleClient 파라미터 검증 100% 동작
- [ ] CandleStorage 배치 저장 성공
- [ ] CandleCache 60초 TTL 동작 확인
- [ ] 모든 래퍼 클래스 기본 기능 동작

### **Phase 3 완료 승인 (Day 6 완료)**
- [ ] CandleStatus 빈 캔들 채우기 성공
- [ ] CandleDataProvider 메인 로직 완전 동작
- [ ] OverlapAnalyzer 최적화 효과 30% 이상 확인
- [ ] 대용량 동기화 성공

### **Phase 4 완료 승인 (Day 8 완료)**
- [ ] 모든 오류 상황 폴백 전략 동작
- [ ] 데이터 품질 95% 이상 달성
- [ ] API 오류율 1% 이하 유지

### **Phase 5 완료 승인 (Day 9 완료)**
- [ ] 테스트 커버리지 90% 이상
- [ ] 모든 성능 목표 달성
- [ ] 7규칙 전략 완벽 지원 확인
- [ ] `python run_desktop_ui.py` 완전 동작

---

## 🎯 **최종 검증 체크리스트**

### **기능 검증**
```python
# 1. 기본 API 호출
response = await provider.get_candles("KRW-BTC", "1m", 100)
assert response.success == True
assert len(response.data['candles']) == 100

# 2. 캐시 효율성
response2 = await provider.get_candles("KRW-BTC", "1m", 100)  # 동일 요청
assert response2.data_source.channel == "cache"

# 3. 빈 캔들 처리
# 실제 거래가 없는 시간대 요청 → 빈 캔들 자동 채우기 확인

# 4. 대용량 동기화
success = await provider.sync_candles("KRW-BTC", "1m", days=7)
assert success == True
```

### **성능 검증**
```bash
# 응답 시간 측정
time curl "http://localhost:8000/candles?symbol=KRW-BTC&interval=1m&count=100"

# 메모리 사용량 모니터링
ps aux | grep python

# 동시 요청 처리
ab -n 1000 -c 100 "http://localhost:8000/candles?symbol=KRW-BTC&interval=1m&count=100"
```

### **UI 통합 검증**
```bash
# 7규칙 전략 동작 확인
python run_desktop_ui.py
# → 전략 관리 → 트리거 빌더 → 7규칙 구성 가능 확인
# → RSI 과매도 진입, 수익시 불타기, 계획된 익절, 트레일링 스탑, 하락시 물타기, 급락 감지, 급등 감지
```

---

**🎯 이 단순화된 태스크 분해를 승인하고 Phase 3 (순차 실행)로 진행하시겠습니까?**

**주요 개선사항**:
- ✅ **단일 폴더**: 9개 파일로 복잡성 최소화
- ✅ **래퍼 패턴**: 89% 기존 코드 재사용으로 안정성 보장
- ✅ **9일 완료**: 단순화로 2일 추가 단축
- ✅ **명확한 책임**: 파일별 역할 분리로 개발/테스트 용이
