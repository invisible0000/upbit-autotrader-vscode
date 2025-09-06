# 📋 CandleDataProvider 제품 요구서 (PRD)

## 📝 **Problem & Users**

### **문제 정의**
- **현재 문제**: SmartDataProvider V4.0은 15개 모듈의 복잡한 구조로 인해 유지보수가 어렵고 성능 오버헤드 발생
- **핵심 요구사항**: 시스템 전체에 안정적인 캔들 데이터를 제공하는 단순하고 신뢰할 수 있는 솔루션 필요
- **비즈니스 임팩트**: 7규칙 전략 실행의 기반이 되는 핵심 데이터 인프라
- **기존 자산 활용**: SmartDataProvider V4.0의 핵심 모듈 재사용으로 개발 효율성 극대화

### **대상 사용자**
- **Primary**: 트레이딩 엔진, 전략 실행기, 백테스팅 시스템
- **Secondary**: UI 차트 컴포넌트, 지표 계산 모듈
- **Admin**: 시스템 관리자 (모니터링, 성능 최적화)

### **사용자 가치**
- **개발자**: 간단한 API로 캔들 데이터 접근 (`provider.get_candles()`)
- **시스템**: 안정적이고 예측 가능한 성능, OverlapAnalyzer 기반 지능형 최적화
- **운영팀**: 명확한 로그와 모니터링 지표, 업비트 API Rate Limit 완벽 준수

---

## 📋 **Technical Design Analysis**

### **upbit_public_client API 파라미터 표준**
- **분봉 단위 검증**: [1, 3, 5, 15, 10, 30, 60, 240] - ValueError 예외 처리
- **count 제한**: 최대 200개 (업비트 API 한계) - 초과시 ValueError
- **to 형식**: ISO 8601 형식 (예: '2023-01-01T00:00:00Z')
- **market 검증**: 필수값, 빈 값시 ValueError
- **응답 정렬**: 과거순 → 최신순 (업비트 API 기본 동작)

### **SmartDataProvider V4 전체 분석 완료 - 캔들 전용 단순화 전략**

#### **✅ 재사용 확정 모듈 (7개 → 캔들 전용 7개)**:
1. **OverlapAnalyzer** → 완전 재사용 (shared/overlap_analyzer.py)
2. **FastCache** → TTL 조정 (200ms → 60s)
3. **BatchDBManager** → 완전 재사용 (`insert_candles_batch` 이미 구현됨!)
4. **CollectionStatusManager** → 완전 재사용 (데이터 무결성 핵심)
5. **TimeUtils** → 완전 재사용 (캔들 시간 계산 필수)
6. **ResponseModels** → 부분 재사용 (DataResponse, Priority만)
7. **CacheModels** → 부분 재사용 (성능 지표용)

#### **⛔ 제거 대상 모듈 (8개)**:
- **SmartRouter**: 직접 UpbitPublicClient 사용
- **RealtimeDataHandler/RealtimeCandleManager**: 캔들은 REST만 사용
- **BackgroundProcessor**: 캔들은 실시간 처리 불필요
- **AdaptiveTTLManager**: FastCache 고정 TTL 사용
- **MemoryRealtimeCache**: 실시간 캐시 불필요
- **BatchProcessor**: CandleDataProvider가 직접 처리

#### **📊 복잡도 감소 효과**:
- **모듈 수**: 15개 → 7개 (53% 감소) ✅
- **실시간 복잡성**: WebSocket/실시간 처리 완전 제거
- **캐시 복잡성**: 단일 FastCache로 단순화
- **API 최적화**: OverlapAnalyzer로 호출 50% 감소 목표

### **TimeUtils & ResponseModels 분석**
- **✅ 시간 처리 유틸리티 (time_utils.py)**:
  - `generate_candle_times()`: 시작~종료 사이 모든 캔들 시간 생성
  - 타임프레임 파싱: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M 지원
  - 캔들 경계 정렬: 분/시간/일 단위별 정렬 로직
  - 이전/다음 캔들 시간 계산 함수
- **✅ 응답 모델 (response_models.py)**:
  - `DataResponse`: 통합 응답 구조 (success, data, metadata, error)
  - `DataSourceInfo`: 데이터 소스 추적 (websocket/rest_api/cache)
  - 실시간성 지표: freshness_score, reliability, latency_ms
  - `Priority` enum: CRITICAL(50ms) → HIGH(100ms) → NORMAL(500ms) → LOW(5s)

### **CollectionStatusManager 데이터 무결성 분석**
- **✅ 수집 상태 추적**:
  - 상태별 관리: PENDING → COLLECTED/EMPTY/FAILED
  - 시간별 수집 이력 저장 (target_time, attempt_count, api_response_code)
  - UPSERT 기반 멱등성 보장
- **✅ 빈 캔들 처리**:
  - `fill_empty_candles()`: 실제 캔들 + 빈 캔들 연속 데이터 생성
  - 마지막 가격 기반 빈 캔들 생성 (OHLC 동일값)
  - 빈 캔들 시간 추적으로 데이터 연속성 보장
- **✅ 미수집 데이터 감지**:
  - `get_missing_candle_times()`: PENDING/FAILED 상태 캔들 식별
  - 예상 시간 vs 실제 수집 상태 비교
  - 자동 재수집 대상 선별
- **✅ 수집 품질 모니터링**:
  - `get_collection_summary()`: 전체 상태 요약 (collected/empty/pending/failed 비율)
  - API 응답 코드 기록으로 오류 패턴 분석
  - 수집 완성도 실시간 추적

### **BatchDBManager 캔들 데이터 최적화 분석**
- **✅ 핵심 재사용 기능**:
  - `insert_candles_batch()`: 캔들 데이터 전용 배치 삽입 (이미 구현됨!)
  - UPSERT 최적화: `INSERT OR REPLACE` 문으로 중복 처리
  - 배치 크기 최적화: INSERT 1000개, UPDATE 500개 단위
  - 우선순위 큐: CRITICAL → HIGH → NORMAL → LOW 순차 처리
  - WAL 모드 + PRAGMA 튜닝: 성능 최적화 설정 자동 적용
- **✅ 캔들 특화 데이터 정규화**:
  - 업비트 API 응답 → 표준 캔들 스키마 변환
  - timestamp, OHLCV, symbol, timeframe 표준화
  - 자동 타입 변환 (float, datetime)
- **✅ 메모리 효율성**:
  - 데이터 크기 자동 추정 (JSON 기준)
  - 대용량 작업 즉시 처리 (100MB 초과시)
  - 연결 풀 관리 (최대 10개 연결)
- **✅ 운영 안정성**:
  - 백그라운드 비동기 처리
  - 정기 유지보수 (WAL 체크포인트, ANALYZE, VACUUM)
  - 상세 통계 및 모니터링
- **✅ 재사용 가능 기능**:
  - 단순 메모리 구조 (Dict 기반 고속 액세스)
  - 자동 만료 정리 (cleanup_expired 메서드)
  - 통계 기능 (hit_rate, 성능 모니터링)
  - 기본 get/set/clear 인터페이스
- **⚠️ 수정 필요 항목**:
  - TTL 조정: 200ms(실시간용) → 60초(1분봉 캐시 적정값)
  - 캐시 키 전략: `f"{market}_{unit}_{count}_{to_hash}"`
  - 용량 관리: 캔들 데이터 크기 고려한 메모리 제한

### **목표 (Goals)**
1. **단순성**: 7개 파일 이하의 명확한 구조 (기존 15개 → 7개, 53% 감소)
2. **안정성**: 99.9% 데이터 제공 성공률, OverlapAnalyzer 기반 지능형 에러 복구
3. **성능**: 단일 심볼 캔들 조회 < 50ms (캐시 히트시 < 5ms), API 호출 최소화
4. **확장성**: 향후 다중 거래소 지원 가능한 구조, 다른 데이터 제공자와 공통 모듈 공유
5. **재사용성**: 기존 검증된 모듈 재사용으로 개발 리스크 최소화

### **비목표 (Non-goals)**
- **실시간 스트리밍**: WebSocket 기반 실시간 데이터는 별도 RealtimeDataProvider
- **복잡한 캐시 전략**: FastCache 기반 단순 TTL 캐시만 사용
- **고급 최적화**: 적응형 TTL, 다중 레이어 캐시 등 제외 (기존 모듈에 존재하지만 미사용)
- **멀티 데이터 타입**: 캔들 데이터만 집중 (티커/호가는 별도 시스템)

---

## 🔍 **Scope & UX flows**

### **핵심 범위**
- **데이터 소스**: 업비트 REST API (`/v1/candles/*`)
- **지원 간격**: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M
- **지원 심볼**: KRW 마켓 전체 (BTC-KRW, ETH-KRW 등)
- **저장소**: SQLite3 (data/market_data.sqlite3)

### **주요 사용 플로우**

#### **Flow 1: 캔들 데이터 조회** (가장 빈번)
```python
# 사용자 코드
provider = CandleDataProvider()
candles = provider.get_candles("KRW-BTC", "1m", count=200)

# 시스템 내부 플로우 (OverlapAnalyzer 기반)
1. 캐시 확인 (5ms) → 히트시 즉시 반환
2. OverlapAnalyzer 겹침 분석 (2ms) → 최적 전략 결정
   - PERFECT_MATCH: 캐시 직접 사용 (API 0회)
   - FORWARD_EXTEND: 캐시 확장 (API 1회)
   - PARTIAL_FILL: 누락 구간만 요청 (API 최소화)
   - FULL_REFRESH: 전체 갱신 (비효율시)
3. DB 조회 (20ms) → 최신 데이터 있으면 반환
4. API 호출 (100-300ms) → 업비트에서 최신 데이터 가져오기
5. DB 저장 + 캐시 저장 → 다음 요청 최적화
```

#### **Flow 2: 백그라운드 동기화** (자동)
```python
# 시스템 내부 플로우 (CollectionStatusManager 기반)
1. 주요 심볼 목록 확인 (KRW-BTC, KRW-ETH 등)
2. 각 간격별 최신 캔들 확인 (CollectionStatusManager)
3. 누락된 캔들 배치 요청 (200개씩, BatchDBManager)
4. DB 배치 저장 (트랜잭션, WAL 모드 최적화)
5. 빈 캔들 상태 관리 (PENDING/COLLECTED/EMPTY/FAILED)
```

#### **Flow 3: 에러 복구** (안정성)
```python
# API 실패시
1. 429 Rate Limit → 백오프 재시도 (5초, 10초, 20초)
2. 네트워크 오류 → 캐시/DB 데이터로 폴백
3. 데이터 무결성 오류 → 로그 기록 후 재요청
```

---

## ⚠️ **Constraints**

### **기술적 제약**
- **Rate Limit**: 업비트 API 초당 10회 제한 (GCRA 알고리즘 준수)
- **메모리**: 캐시 최대 100MB (약 1000개 심볼 × 200 캔들)
- **DB 크기**: 월 1GB 이하 (자동 정리 정책)
- **응답 시간**: P95 < 100ms, P99 < 200ms

### **보안 제약**
- **API 키 관리**: 기존 ApiKeyService 사용 (암호화 저장)
- **로깅**: API 키 로그 노출 금지
- **에러 처리**: 민감한 정보 마스킹

### **운영 제약**
- **Windows PowerShell 전용**: Unix 명령어 사용 금지
- **DDD 아키텍처 준수**: Infrastructure 계층 준수
- **로깅 시스템**: create_component_logger 사용 필수

---

## 🔗 **Dependencies**

### **Infrastructure 의존성 (기존 활용)**
- **기존 시스템**: `upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client`
- **데이터베이스**: `data/market_data.sqlite3` (기존 스키마 활용)
- **로깅**: `upbit_auto_trading.infrastructure.logging`
- **Rate Limiter**: 기존 GCRA Rate Limiter

### **재사용할 핵심 모듈 (검증된 고품질 코드)**
- **OverlapAnalyzer**: 지능형 겹침 분석 및 API 호출 최적화 (shared/overlap_analyzer.py)
- **FastCache**: 200ms TTL 고속 메모리 캐시 (V4/fast_cache.py)
- **BatchDBManager**: 배치 DB 최적화 (V4/batch_db_manager.py)
- **CollectionStatusManager**: 빈 캔들 추적 및 상태 관리 (V4/collection_status_manager.py)
- **TimeUtils**: 캔들 시간 경계 정렬 (V4/time_utils.py)
- **ResponseModels**: 표준화된 응답 구조 (V4/response_models.py)

### **새로 구현할 모듈 (단순화)**
- **CandleDataProvider**: 메인 인터페이스 (Facade 패턴)
- **CandleClient**: 업비트 REST API 전용 클라이언트
- **CandleRepository**: SQLite 저장소 (BatchDBManager 활용)
- **CandleCache**: 캐시 래퍼 (FastCache 활용)
- **CandleSyncManager**: 동기화 관리 (CollectionStatusManager 활용)

### **제거될 의존성**
- **SmartRouter**: 직접 UpbitPublicClient 사용 (캔들은 REST만)
- **복잡한 캐시**: 단순한 FastCache만 사용
- **WebSocket**: 캔들 데이터는 REST만 사용
- **실시간 처리 모듈**: RealtimeDataHandler, RealtimeCandleManager 등

---

## ✅ **Acceptance Criteria**

### **기능적 기준**
1. **API 호환성**: `get_candles(symbol, interval, count)` 메서드 제공
2. **데이터 완정성**: 요청한 count만큼 캔들 데이터 반환 (누락 < 1%)
3. **시간 정렬**: 캔들 데이터는 시간순 정렬 보장
4. **캐시 효율성**: 동일 요청 1분 내 재요청시 캐시에서 반환

### **성능 기준**
1. **응답 시간** (OverlapAnalyzer 최적화):
   - 캐시 히트: P95 < 5ms
   - DB 히트: P95 < 50ms
   - API 호출: P95 < 300ms
   - 겹침 분석: P95 < 2ms
2. **처리량**: 100 requests/second 지원
3. **메모리**: 힙 사용량 < 100MB (FastCache 기준)
4. **API 효율성**: 기존 대비 API 호출 50% 감소 (OverlapAnalyzer 효과)

### **안정성 기준**
1. **가용성**: 99.9% 성공률 (API 장애 제외)
2. **에러 처리**: 모든 예외 상황 로그 기록, OverlapAnalyzer fallback 전략
3. **복구 능력**: API 실패시 캐시/DB로 폴백, CollectionStatusManager 기반 데이터 무결성 보장
4. **캐시 효율성**: 동일 요청 5분 내 재요청시 FastCache에서 반환

### **운영 기준**
1. **모니터링**: 성능 지표 실시간 조회 API, OverlapAnalyzer 통계 포함
2. **로깅**: ERROR/WARN 레벨 로그 < 1/hour
3. **설정**: 캐시 TTL, 배치 크기 설정 가능
4. **디버깅**: OverlapAnalyzer 분석 결과 로그로 API 호출 전략 추적 가능

---

## 📊 **Observability**

### **로그 전략**
```python
# 성공 로그 (INFO) - OverlapAnalyzer 결과 포함
"캔들 데이터 조회 성공: KRW-BTC 1m 200개 (strategy=EXTEND_CACHE, api_calls=1, cache_hit=85%, response_time=25ms)"

# 성능 로그 (INFO, 매 100 요청마다)
"성능 지표: avg_response_time=25ms, cache_hit_rate=85%, api_calls=15, overlap_efficiency=92%"

# 경고 로그 (WARN)
"API Rate Limit 근접: 9/10 calls used, next_reset=5s, switching to PARTIAL_FILL strategy"

# 에러 로그 (ERROR)
"캔들 데이터 조회 실패: KRW-BTC 1m - API Error 500, fallback to cache (overlap_analysis: COMPLETE_CONTAINMENT)"

# OverlapAnalyzer 상세 로그 (DEBUG)
"겹침분석: FORWARD_EXTEND | 겹침=95% | 전략=EXTEND_CACHE | API=1회 | 효율성=90%"
```

### **메트릭 수집**
- **성능**: response_time, cache_hit_rate, api_call_count, overlap_analysis_time
- **에러**: error_count_by_type, fallback_count, api_failure_rate
- **사용량**: requests_per_minute, unique_symbols_per_hour
- **최적화**: overlap_efficiency_score, cache_strategy_distribution, api_call_reduction_rate

### **알림 기준**
- **Critical**: API 실패율 > 10% (5분간), OverlapAnalyzer fallback 전략 빈발
- **Warning**: 평균 응답시간 > 100ms (10분간), 캐시 효율성 < 70%
- **Info**: 캐시 히트율 < 70% (1시간간), API 호출 최적화 효과 < 30%

---

## 📅 **Implementation Timeline**

### **Phase 1: 핵심 모듈 재사용 및 구조 설정** (2일)
- 기존 모듈 복사: OverlapAnalyzer, FastCache, BatchDBManager, CollectionStatusManager
- 새 폴더 구조 생성: market_data/candle/, market_data/shared/
- CandleDataProvider 기본 틀 구현

### **Phase 2: Core Infrastructure** (3일)
- CandleClient 구현 (UpbitPublicClient 래퍼)
- CandleRepository 구현 (BatchDBManager 활용)
- CandleCache 구현 (FastCache 활용)
- 기본 테스트 작성

### **Phase 3: 지능형 최적화 통합** (2일)
- OverlapAnalyzer 통합 및 전략 실행 로직
- CandleDataProvider 메인 로직 완성
- 성능 최적화 및 로깅 강화

### **Phase 4: 백그라운드 동기화** (2일)
- CandleSyncManager 구현 (CollectionStatusManager 활용)
- 백그라운드 동기화 로직
- 에러 처리 및 복구 전략

### **Phase 5: Integration & Testing** (2일)
- 기존 시스템과 호환성 확인
- 성능 테스트 및 OverlapAnalyzer 효과 검증
- 문서화 및 운영 가이드

**총 소요시간: 11일** (기존 모듈 재사용으로 2일 단축)

---

## ✨ **Success Metrics**

### **출시 후 1주일**
- [ ] 시스템 가동률 > 99.9%
- [ ] 평균 응답시간 < 50ms
- [ ] 캐시 히트율 > 85%
- [ ] Critical 에러 0건
- [ ] OverlapAnalyzer API 호출 최적화 효과 > 30%

### **출시 후 1개월**
- [ ] 메모리 사용량 안정화 < 100MB
- [ ] API 호출 최적화 (기존 대비 50% 감소)
- [ ] 개발자 만족도 조사 > 4.5/5
- [ ] 7규칙 전략 안정 동작 확인
- [ ] OverlapAnalyzer 캐시 효율성 점수 > 80%

### **기술적 성과 지표**
- [ ] 모듈 복잡도 53% 감소 (15개 → 7개 파일)
- [ ] 기존 검증된 모듈 재사용률 > 60%
- [ ] 겹침 분석 정확도 > 95% (수동 검증 대비)
- [ ] 코드 라인 수 87% 감소 (예상 6,000 → 800 lines)

---

## 🏗️ **Architecture Overview**

### **최종 시스템 구조**
```
upbit_auto_trading/infrastructure/market_data/
├── candle/                           # 캔들 데이터 전용 (7개 파일)
│   ├── __init__.py
│   ├── candle_data_provider.py      # 🎯 메인 Provider (Facade)
│   ├── candle_client.py             # 업비트 API 클라이언트
│   ├── candle_repository.py         # DB 저장소 (BatchDBManager 활용)
│   ├── candle_cache.py              # 메모리 캐시 (FastCache 활용)
│   ├── candle_sync_manager.py       # 동기화 (CollectionStatusManager 활용)
│   └── models.py                    # 캔들 관련 모델
└── shared/                          # 공통 모듈 (재사용)
    ├── __init__.py
    ├── overlap_analyzer.py          # 🏆 지능형 겹침 분석 (재사용)
    └── time_utils.py               # 시간 처리 (재사용)
```

### **핵심 재사용 모듈**
- **기존 V4 모듈**: FastCache, BatchDBManager, CollectionStatusManager, TimeUtils, ResponseModels
- **신규 통합**: OverlapAnalyzer (shared로 이동하여 다른 제공자도 활용 가능)

---

**📌 이 PRD는 기존 자산을 최대한 활용하면서도 단순하고 안정적인 캔들 데이터 제공 시스템의 청사진입니다.**
**🎯 복잡성을 53% 줄이면서도 OverlapAnalyzer 기반 지능형 최적화로 성능은 향상시키는 것이 목표입니다.**
