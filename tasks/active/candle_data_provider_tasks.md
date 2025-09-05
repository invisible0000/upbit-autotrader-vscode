# 🚀 CandleDataProvider 구현 태스크 분해 - Ryan-Style 3-Step Phase 2

## 📋 **프로젝트 개요**
- **목표**: SmartDataProvider V4에서 캔들 전용 단순화 시스템 구축
- **복잡도 감소**: 15개 모듈 → 7개 모듈 (53% 감소)
- **재사용률**: 89% (1,635줄 검증된 코드 활용)
- **예상 기간**: 11일 (기존 모듈 재사용으로 2일 단축)

---

## 🎯 **Phase 1: 핵심 모듈 복사 & 초기 구조** (Day 1-2)

### **1. 검증된 모듈 복사 및 통합**
- **Description**: SmartDataProvider V4의 7개 핵심 모듈을 candle/ 및 shared/ 폴더로 복사
- **Acceptance Criteria**:
  - [x] OverlapAnalyzer → shared/overlap_analyzer.py 복사 완료
  - [ ] FastCache → candle/cache/fast_cache.py 복사
  - [ ] BatchDBManager → candle/storage/batch_db_manager.py 복사
  - [ ] CollectionStatusManager → candle/status/collection_status_manager.py 복사
  - [ ] TimeUtils → shared/time_utils.py 복사
  - [ ] ResponseModels → shared/response_models.py 복사
  - [ ] CacheModels → shared/cache_models.py 복사
- **Test Plan**: 각 모듈 import 테스트, 기본 기능 동작 확인
- **Risk & Rollback**: import 오류시 상대 경로 수정, 원본 V4 백업 유지
- **Effort**: 2시간 (단순 복사 + 경로 수정)
- **Touch Points**:
  - `upbit_auto_trading/infrastructure/market_data/candle/`
  - `upbit_auto_trading/infrastructure/market_data/shared/`

### **1.1 폴더 구조 생성**
- **Description**: DDD 계층 기반 캔들 데이터 전용 폴더 구조 생성
- **Acceptance Criteria**:
  - [ ] market_data/candle/ 메인 폴더 생성
  - [ ] candle/cache/ - 캐시 관련 모듈
  - [ ] candle/storage/ - DB 저장 관련 모듈
  - [ ] candle/status/ - 수집 상태 관리
  - [ ] candle/models/ - 캔들 전용 모델
  - [ ] market_data/shared/ - 공통 유틸리티
- **Test Plan**: 폴더 구조 확인, __init__.py 파일 생성 테스트
- **Risk & Rollback**: 경로 오류시 기존 구조로 복원
- **Effort**: 30분
- **Touch Points**: 전체 market_data 구조

### **1.2 기본 CandleDataProvider 클래스 구현**
- **Description**: 메인 Facade 클래스 기본 구조 구현, 의존성 주입 패턴 적용
- **Acceptance Criteria**:
  - [ ] CandleDataProvider 클래스 생성
  - [ ] get_candles() 메서드 기본 구조
  - [ ] 의존성 주입: FastCache, BatchDBManager, CollectionStatusManager
  - [ ] Infrastructure 로깅 (create_component_logger) 적용
  - [ ] DataResponse 기반 응답 구조
- **Test Plan**:
  ```python
  provider = CandleDataProvider()
  response = await provider.get_candles("KRW-BTC", "1m", 10)
  assert response.success == True
  ```
- **Risk & Rollback**: 순환 import 발생시 인터페이스 분리
- **Effort**: 2시간
- **Touch Points**: `candle/candle_data_provider.py`

---

## 🔧 **Phase 2: 캐시 & 저장 시스템 통합** (Day 3-4)

### **2. FastCache 캔들 전용 최적화**
- **Description**: FastCache TTL을 200ms → 60초로 조정, 캔들 전용 키 전략 구현
- **Acceptance Criteria**:
  - [ ] TTL 60초로 변경 (1분봉 캐시 최적 시간)
  - [ ] 캔들 전용 키 생성: f"{market}_{unit}_{count}_{to_hash}"
  - [ ] 캐시 통계 모니터링 (hit_rate, miss_rate)
  - [ ] cleanup_expired() 주기적 실행 (5분마다)
  - [ ] 메모리 사용량 모니터링 (<100MB 제한)
- **Test Plan**:
  ```python
  cache = FastCache(default_ttl=60.0)
  cache.set("KRW-BTC_1m_100_abc123", candle_data)
  result = cache.get("KRW-BTC_1m_100_abc123")
  assert result is not None
  ```
- **Risk & Rollback**: TTL 너무 길면 실시간성 저하, 30초로 조정
- **Effort**: 1시간 (설정 변경 + 키 전략)
- **Touch Points**: `candle/cache/fast_cache.py`

### **2.1 BatchDBManager 캔들 배치 처리 통합**
- **Description**: 기존 insert_candles_batch() 메서드 활용하여 캔들 데이터 배치 저장
- **Acceptance Criteria**:
  - [ ] BatchDBManager 인스턴스 생성 및 초기화
  - [ ] insert_candles_batch() 메서드 테스트
  - [ ] 업비트 API 응답 → 표준 캔들 스키마 변환 확인
  - [ ] 배치 크기 1000개 설정 검증
  - [ ] WAL 모드 + PRAGMA 최적화 설정 적용
  - [ ] 우선순위 큐 동작 확인 (NORMAL priority)
- **Test Plan**:
  ```python
  batch_manager = BatchDBManager(db_connection_factory)
  operation_id = await batch_manager.insert_candles_batch(
      "KRW-BTC", "1m", sample_candles
  )
  assert operation_id != ""
  ```
- **Risk & Rollback**: 배치 처리 실패시 개별 INSERT로 폴백
- **Effort**: 2시간 (통합 + 테스트)
- **Touch Points**: `candle/storage/batch_db_manager.py`

### **2.2 CollectionStatusManager 데이터 무결성 통합**
- **Description**: 빈 캔들 추적 및 자동 채우기 기능 통합
- **Acceptance Criteria**:
  - [ ] CollectionStatusManager 인스턴스 생성
  - [ ] get_missing_candle_times() 미수집 데이터 감지
  - [ ] fill_empty_candles() 빈 캔들 자동 채우기 테스트
  - [ ] 수집 상태 추적 (PENDING → COLLECTED/EMPTY/FAILED)
  - [ ] get_collection_summary() 데이터 품질 모니터링
- **Test Plan**:
  ```python
  status_manager = CollectionStatusManager()
  missing_times = status_manager.get_missing_candle_times(
      "KRW-BTC", "1m", start_time, end_time
  )
  filled_candles = status_manager.fill_empty_candles(
      real_candles, "KRW-BTC", "1m", start_time, end_time
  )
  assert len(filled_candles) > len(real_candles)  # 빈 캔들 추가됨
  ```
- **Risk & Rollback**: 빈 캔들 생성 실패시 실제 데이터만 반환
- **Effort**: 2시간 (통합 + 빈 캔들 테스트)
- **Touch Points**: `candle/status/collection_status_manager.py`

---

## ⚡ **Phase 3: 지능형 API 최적화** (Day 5-7)

### **3. OverlapAnalyzer API 호출 최적화**
- **Description**: 6가지 겹침 패턴으로 API 호출 50% 감소 목표 달성
- **Acceptance Criteria**:
  - [ ] OverlapAnalyzer 통합 및 겹침 분석 로직 구현
  - [ ] PERFECT_MATCH: 캐시 데이터 완전 일치시 API 호출 스킵
  - [ ] FORWARD_EXTEND: 앞쪽 확장 요청 최적화
  - [ ] BACKWARD_EXTEND: 뒤쪽 확장 요청 최적화
  - [ ] SPLIT_REQUEST: 큰 요청을 효율적 분할
  - [ ] API 호출 전략 로깅 (strategy=EXTEND_CACHE 등)
  - [ ] 겹침 효율성 점수 80% 이상 달성
- **Test Plan**:
  ```python
  analyzer = OverlapAnalyzer()
  strategy = analyzer.analyze_overlap(request_range, cached_ranges)
  assert strategy.api_calls < original_calls * 0.7  # 30% 이상 감소
  ```
- **Risk & Rollback**: 겹침 분석 실패시 기본 API 호출로 폴백
- **Effort**: 4시간 (복잡한 로직 통합)
- **Touch Points**: `shared/overlap_analyzer.py`, `candle_data_provider.py`

### **3.1 upbit_public_client 파라미터 표준 준수**
- **Description**: 업비트 API 파라미터 검증 및 표준화 구현
- **Acceptance Criteria**:
  - [ ] unit 검증: [1, 3, 5, 15, 10, 30, 60, 240] 제한
  - [ ] count 검증: 최대 200개 제한
  - [ ] market 검증: 필수값, 형식 확인 (KRW-BTC 패턴)
  - [ ] to 검증: ISO 8601 형식 (2023-01-01T00:00:00Z)
  - [ ] ValueError 일관성 있는 에러 메시지
  - [ ] 응답 정렬: 과거순 → 최신순 보장
- **Test Plan**:
  ```python
  # 유효하지 않은 unit
  with pytest.raises(ValueError, match="지원하지 않는 분봉 단위"):
      await provider.get_candles("KRW-BTC", "2m", 100)

  # count 초과
  with pytest.raises(ValueError, match="최대 200개"):
      await provider.get_candles("KRW-BTC", "1m", 300)
  ```
- **Risk & Rollback**: 검증 로직 오류시 기본 검증으로 단순화
- **Effort**: 2시간 (검증 로직 + 테스트)
- **Touch Points**: `candle/candle_data_provider.py`

### **3.2 TimeUtils 캔들 시간 처리 통합**
- **Description**: 캔들 시간 경계 정렬 및 시간 계산 로직 통합
- **Acceptance Criteria**:
  - [ ] generate_candle_times() 예상 캔들 시간 생성
  - [ ] align_to_candle_boundary() 시간 경계 정렬
  - [ ] 타임프레임 파싱: 1m, 5m, 15m, 30m, 1h, 4h, 1d 지원
  - [ ] get_previous_candle_time(), get_next_candle_time() 시간 계산
  - [ ] 캔들 요청 범위 최적화 (정확한 시작/종료 시간)
- **Test Plan**:
  ```python
  times = generate_candle_times(
      datetime(2023, 1, 1, 10, 5),
      datetime(2023, 1, 1, 10, 15),
      "5m"
  )
  assert times == [
      datetime(2023, 1, 1, 10, 5),
      datetime(2023, 1, 1, 10, 10),
      datetime(2023, 1, 1, 10, 15)
  ]
  ```
- **Risk & Rollback**: 시간 계산 오류시 기본 시간 범위로 폴백
- **Effort**: 2시간 (통합 + 시간 계산 테스트)
- **Touch Points**: `shared/time_utils.py`, `candle_data_provider.py`

---

## 🛡️ **Phase 4: 데이터 무결성 & 오류 처리** (Day 8-9)

### **4. 미수집 데이터 자동 감지 및 보완**
- **Description**: CollectionStatusManager로 데이터 누락 감지 및 자동 보완
- **Acceptance Criteria**:
  - [ ] get_missing_candle_times() 정기 실행 (1시간마다)
  - [ ] 미수집 데이터 자동 재수집 시도
  - [ ] 재시도 정책: 3회 시도, 지수 백오프 (1s, 2s, 4s)
  - [ ] FAILED 상태 데이터 별도 처리 (수동 확인 알림)
  - [ ] 수집 완성도 95% 이상 유지
- **Test Plan**:
  ```python
  missing_times = status_manager.get_missing_candle_times(
      "KRW-BTC", "1m",
      datetime.now() - timedelta(hours=1),
      datetime.now()
  )
  assert len(missing_times) == 0  # 완전 수집
  ```
- **Risk & Rollback**: 자동 보완 실패시 수동 수집 모드로 전환
- **Effort**: 3시간 (재시도 로직 + 스케줄링)
- **Touch Points**: `candle/status/collection_status_manager.py`

### **4.1 빈 캔들 자동 채우기 시스템**
- **Description**: fill_empty_candles()로 연속적인 캔들 데이터 보장
- **Acceptance Criteria**:
  - [ ] 빈 캔들 감지: 거래량 0 또는 데이터 누락
  - [ ] 마지막 가격으로 OHLC 생성 (open=high=low=close)
  - [ ] 빈 캔들 표시: is_empty=True 플래그
  - [ ] 연속 데이터 생성: 시간 순서 보장
  - [ ] 빈 캔들 비율 5% 이하 유지 (품질 관리)
- **Test Plan**:
  ```python
  real_candles = [candle1, candle3]  # candle2 누락
  filled = status_manager.fill_empty_candles(
      real_candles, "KRW-BTC", "1m", start, end
  )
  assert len(filled) == 3  # candle2가 빈 캔들로 추가
  assert filled[1].is_empty == True
  ```
- **Risk & Rollback**: 빈 캔들 생성 실패시 누락 데이터 그대로 반환
- **Effort**: 2시간 (빈 캔들 로직 + 테스트)
- **Touch Points**: `candle/status/collection_status_manager.py`

### **4.2 API 오류 처리 및 복구 시스템**
- **Description**: 업비트 API 오류 상황 처리 및 폴백 전략
- **Acceptance Criteria**:
  - [ ] Rate Limit (429) 오류: 자동 백오프 및 재시도
  - [ ] API 응답 오류 (500, 503): 3회 재시도 후 캐시 폴백
  - [ ] 네트워크 오류: DB에서 최근 데이터 반환
  - [ ] 타임아웃 오류: 부분 데이터라도 반환
  - [ ] 오류율 1% 이하 유지 (SLA 목표)
- **Test Plan**:
  ```python
  # API 서버 다운 시뮬레이션
  with mock.patch('upbit_client.get_candles', side_effect=TimeoutError):
      response = await provider.get_candles("KRW-BTC", "1m", 100)
      assert response.success == True  # DB 폴백 성공
      assert response.data_source.channel == "cache"
  ```
- **Risk & Rollback**: 모든 폴백 실패시 에러 응답 반환, 시스템 중단 방지
- **Effort**: 3시간 (다양한 오류 시나리오 + 테스트)
- **Touch Points**: `candle/candle_data_provider.py`

---

## 🧪 **Phase 5: 테스트 & 성능 최적화** (Day 10-11)

### **5. 단위 테스트 및 통합 테스트**
- **Description**: 모든 모듈의 기능 검증 및 통합 시나리오 테스트
- **Acceptance Criteria**:
  - [ ] FastCache 테스트: TTL, 만료, 통계
  - [ ] BatchDBManager 테스트: 배치 INSERT, 트랜잭션
  - [ ] CollectionStatusManager 테스트: 빈 캔들, 상태 추적
  - [ ] OverlapAnalyzer 테스트: 6가지 겹침 패턴
  - [ ] TimeUtils 테스트: 시간 계산, 타임프레임 파싱
  - [ ] CandleDataProvider 통합 테스트: 전체 플로우
  - [ ] 테스트 커버리지 90% 이상
- **Test Plan**:
  ```bash
  pytest candle/ -v --cov=candle --cov-report=html
  # 커버리지 90% 이상 확인
  ```
- **Risk & Rollback**: 테스트 실패시 해당 기능 수정 후 재테스트
- **Effort**: 4시간 (포괄적 테스트 작성)
- **Touch Points**: `tests/candle/` 전체

### **5.1 성능 테스트 및 최적화**
- **Description**: 목표 성능 지표 달성 확인 및 최적화
- **Acceptance Criteria**:
  - [ ] 응답 시간: P95 < 50ms (캐시), < 300ms (API)
  - [ ] 처리량: 100 requests/second 지원
  - [ ] 메모리 사용량: < 100MB 유지
  - [ ] API 호출 감소: OverlapAnalyzer로 50% 감소 확인
  - [ ] 캐시 히트율: > 85% 달성
- **Test Plan**:
  ```python
  # 부하 테스트
  async def load_test():
      tasks = []
      for i in range(100):
          task = provider.get_candles("KRW-BTC", "1m", 100)
          tasks.append(task)

      start_time = time.time()
      await asyncio.gather(*tasks)
      elapsed = time.time() - start_time

      assert elapsed < 1.0  # 100개 요청이 1초 이내
      assert provider.cache.get_stats()['hit_rate'] > 85
  ```
- **Risk & Rollback**: 성능 목표 미달시 캐시 TTL 조정 또는 배치 크기 최적화
- **Effort**: 3시간 (성능 측정 + 최적화)
- **Touch Points**: 전체 시스템 성능

### **5.2 최종 통합 검증**
- **Description**: 7규칙 전략과의 호환성 및 실제 운영 환경 검증
- **Acceptance Criteria**:
  - [ ] `python run_desktop_ui.py` 실행 성공
  - [ ] 전략 관리 → 트리거 빌더에서 7규칙 구성 가능
  - [ ] 실제 캔들 데이터 조회 및 저장 테스트
  - [ ] RSI, 이동평균 계산을 위한 캔들 데이터 제공 확인
  - [ ] 메모리 누수 없음 (24시간 연속 실행)
  - [ ] 로그 레벨 ERROR/WARN < 1건/hour
- **Test Plan**:
  ```bash
  # 실제 UI 실행 테스트
  python run_desktop_ui.py
  # 전략 관리 → 트리거 빌더 → 7규칙 구성 시도
  # RSI 과매도 진입, 수익시 불타기 등 캔들 데이터 의존 기능 테스트
  ```
- **Risk & Rollback**: UI 통합 실패시 API 레벨에서 디버깅, 점진적 통합
- **Effort**: 2시간 (실제 환경 테스트)
- **Touch Points**: 전체 시스템 통합

---

## 📊 **성공 기준 및 검증 지표**

### **기능적 성공 기준**
- [ ] **API 호환성**: get_candles(symbol, interval, count) 완전 동작
- [ ] **데이터 무결성**: 빈 캔들 자동 채우기로 연속성 100% 보장
- [ ] **캐시 효율성**: 85% 이상 히트율로 응답 속도 향상
- [ ] **오류 복구**: API 장애시 캐시/DB 폴백으로 가용성 99.9%

### **성능 성공 기준**
- [ ] **응답 시간**: 캐시 5ms, DB 50ms, API 300ms (P95 기준)
- [ ] **API 최적화**: OverlapAnalyzer로 50% 호출 감소
- [ ] **메모리 효율**: 100MB 이하 사용량 유지
- [ ] **처리량**: 100 req/sec 동시 처리

### **운영 성공 기준**
- [ ] **시스템 안정성**: 7규칙 전략 완벽 지원
- [ ] **코드 품질**: 테스트 커버리지 90%, 재사용률 89%
- [ ] **복잡도 감소**: 15개 → 7개 모듈 (53% 감소)
- [ ] **개발 효율**: 11일 완료 (기존 모듈 재사용 효과)

---

## 🚨 **리스크 관리 계획**

### **High Risk**
1. **OverlapAnalyzer 통합 복잡성**
   - **Mitigation**: 단계별 구현, 기본 API 호출 폴백 유지
   - **Contingency**: 겹침 분석 실패시 단순 캐시 확인만 수행

2. **BatchDBManager 성능 이슈**
   - **Mitigation**: 배치 크기 점진적 증가 (100 → 1000)
   - **Contingency**: 배치 실패시 개별 INSERT로 자동 폴백

### **Medium Risk**
1. **TimeUtils 시간 계산 오류**
   - **Mitigation**: 철저한 단위 테스트, 경계값 테스트
   - **Contingency**: 시간 계산 실패시 기본 범위 요청

2. **캐시 메모리 사용량 초과**
   - **Mitigation**: 주기적 cleanup, 메모리 모니터링
   - **Contingency**: 메모리 임계값 도달시 캐시 비우기

### **Low Risk**
1. **API 파라미터 검증 누락**
   - **Mitigation**: upbit_public_client 표준 완전 준수
   - **Contingency**: 검증 실패시 기본값으로 요청

---

## 📅 **상세 일정 계획**

| Day | Phase | 주요 작업 | 예상 시간 | 중요도 |
|-----|-------|-----------|----------|--------|
| 1 | 1 | 모듈 복사 + 폴더 구조 | 3시간 | ⭐⭐⭐ |
| 2 | 1 | CandleDataProvider 기본 구조 | 4시간 | ⭐⭐⭐ |
| 3 | 2 | FastCache + BatchDBManager 통합 | 6시간 | ⭐⭐⭐ |
| 4 | 2 | CollectionStatusManager 통합 | 4시간 | ⭐⭐⭐ |
| 5 | 3 | OverlapAnalyzer 통합 | 6시간 | ⭐⭐ |
| 6 | 3 | upbit_public_client 표준 준수 | 4시간 | ⭐⭐⭐ |
| 7 | 3 | TimeUtils 시간 처리 통합 | 4시간 | ⭐⭐ |
| 8 | 4 | 데이터 무결성 시스템 | 6시간 | ⭐⭐⭐ |
| 9 | 4 | 오류 처리 및 복구 | 5시간 | ⭐⭐ |
| 10 | 5 | 테스트 작성 및 실행 | 7시간 | ⭐⭐⭐ |
| 11 | 5 | 성능 최적화 + 최종 검증 | 5시간 | ⭐⭐⭐ |

**총 소요시간**: 54시간 (11일 × 5시간/일 평균)

---

## ✅ **체크포인트 및 승인 기준**

### **Phase 1 완료 승인**
- [ ] 7개 모듈 모두 정상 import
- [ ] 기본 CandleDataProvider 인스턴스 생성 성공
- [ ] Infrastructure 로깅 정상 동작

### **Phase 2 완료 승인**
- [ ] FastCache 60초 TTL 동작 확인
- [ ] BatchDBManager 캔들 배치 저장 성공
- [ ] CollectionStatusManager 빈 캔들 채우기 성공

### **Phase 3 완료 승인**
- [ ] OverlapAnalyzer API 호출 30% 이상 감소
- [ ] upbit_public_client 파라미터 검증 완료
- [ ] TimeUtils 시간 계산 정확성 검증

### **Phase 4 완료 승인**
- [ ] 미수집 데이터 자동 보완 동작
- [ ] API 오류 상황 폴백 전략 동작
- [ ] 데이터 무결성 95% 이상 유지

### **Phase 5 완료 승인**
- [ ] 테스트 커버리지 90% 이상
- [ ] 성능 목표 모두 달성
- [ ] 7규칙 전략 완벽 지원 확인

---

**🎯 이 태스크 분해를 승인하고 Phase 3 (순차 실행)로 진행하시겠습니까?**
