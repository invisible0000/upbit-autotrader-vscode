# 🚀 CandleDataProvider v4.0 - Ryan-Style Step 2: Task 분해

## 📋 **PRD 승인 완료**
✅ **PRD v4.0 승인**: 업비트 특화 최적화 + 시간 처리 통일
✅ **핵심 요구사항**: 7개 파일, 4단계 최적화, 개별 테이블, INSERT OR IGNORE
✅ **성능 목표**: API 호출 60% 감소, 캐시 히트율 90%, 응답시간 P95 <200ms

---

## 🎯 **계층적 태스크 분해**

### **1. TimeUtils 확장 및 시간 통일 시스템** ⏰
**목표**: time_utils와 overlap_optimizer 간 100% 일치된 시간 처리 보장

#### **1.1 TimeUtils v4.0 확장** [ ]
- **Description**: 기존 time_utils.py에 get_timeframe_seconds() 메서드 추가 및 시간 일관성 보장 메서드 구현
- **Acceptance Criteria**:
  - get_timeframe_seconds("1m") → 60 반환
  - get_timeframe_seconds("5m") → 300 반환
  - 모든 timeframe에서 분 단위 * 60 = 초 단위 정확 변환
- **Test Plan**:
  - 단위 테스트: 모든 지원 timeframe(1m~1M) 변환 검증
  - 통합 테스트: 기존 V4 메서드들과 호환성 확인
- **Risk & Rollback**: 기존 메서드 영향 없음, 새 메서드만 추가
- **Effort**: 2시간 (Low)
- **Touch Points**: `upbit_auto_trading/infrastructure/market_data/candle/time_utils.py`

#### **1.2 시간 형식 표준화 메서드** [ ]
- **Description**: DB 저장/파싱용 ISO 형식 변환 및 시간 정렬 일관성 보장 메서드 추가
- **Acceptance Criteria**:
  - _normalize_db_time_format() → ISO 형식 반환
  - _parse_db_time_format() → datetime 객체 반환
  - _ensure_time_consistency() → 기존 _align_to_candle_boundary와 동일 결과
- **Test Plan**: 실제 DB 데이터와 매칭 테스트, 경계 시간 정렬 검증
- **Risk & Rollback**: 순수 함수 추가, 기존 로직 영향 없음
- **Effort**: 1시간 (Low)
- **Touch Points**: `time_utils.py` 확장

---

### **2. DDD Repository 패턴 구현** 💾
**목표**: Domain 인터페이스 + Infrastructure 구현체로 DDD 준수하면서 성능 최적화

#### **2.1 Domain Repository Interface 생성** [ ]
- **Description**: Domain Layer에 CandleRepositoryInterface 정의로 DDD 준수
- **Acceptance Criteria**:
  - CandleRepositoryInterface 추상 클래스 정의
  - save_candles(), get_candles() 메서드 시그니처 정의
  - Domain Layer 순수성 보장 (외부 의존성 없음)
- **Test Plan**:
  - 인터페이스 정의 검증
  - 추상 메서드 시그니처 확인
  - Domain Layer 의존성 검사
- **Risk & Rollback**: 인터페이스 변경 시 구현체 수정 필요
- **Effort**: 1시간 (Low)
- **Touch Points**: `upbit_auto_trading/domain/repositories/candle_repository_interface.py`

#### **2.2 Infrastructure Repository 구현체** [ ]
- **Description**: DatabaseManager 활용하는 SqliteCandleRepository 구현으로 DDD + 성능 최적화
- **Acceptance Criteria**:
  - DatabaseManager 의존성 주입으로 Connection Pooling + WAL 모드 활용
  - 개별 테이블 구조 + INSERT OR IGNORE 최적화 유지
  - RepositoryContainer에 등록 가능한 구조
- **Test Plan**:
  - DatabaseManager 연동 테스트
  - 개별 테이블 생성/관리 테스트
  - 성능 벤치마크 (기존 대비 30-90% 향상)
- **Risk & Rollback**: DatabaseManager 연동 실패 시 직접 SQLite 접근
- **Effort**: 5시간 (Medium)
- **Touch Points**: `upbit_auto_trading/infrastructure/repositories/sqlite_candle_repository.py`

---

### **3. 업비트 특화 4단계 겹침 최적화** 🎯
**목표**: 기존 7패턴 → 4단계 업비트 특화 로직으로 API 호출 60% 감소

#### **3.1 완전 겹침 확인 (count 기반)** [ ]
- **Description**: DB count와 요청 count 비교로 초고속 완전 겹침 판별
- **Acceptance Criteria**:
  - _check_complete_overlap() → DB 개수 == 요청 개수 시 True
  - timeframe_seconds 통일된 시간 계산 사용
  - BETWEEN 쿼리로 <30ms 응답
- **Test Plan**:
  - 완전 일치 시나리오 (100개 요청, DB 100개 존재)
  - 부분 일치 시나리오 (100개 요청, DB 80개 존재)
  - 성능 테스트 (대용량 데이터에서 <30ms)
- **Risk & Rollback**: 쿼리 성능 저하 시 기존 overlap_analyzer 사용
- **Effort**: 3시간 (Medium)
- **Touch Points**: `overlap_optimizer.py` (새 파일)

#### **3.2 파편화 겹침 확인 (SQLite 호환)** [ ]
- **Description**: LAG 윈도우 함수로 파편화 감지, SQLite datetime() 함수 활용
- **Acceptance Criteria**:
  - _check_fragmentation() → 2번 이상 끊어짐 감지
  - SQLite strftime() 함수로 시간 계산
  - gap_count 정확 계산
- **Test Plan**:
  - 연속 데이터 테스트 (gap_count = 0)
  - 파편화 데이터 테스트 (gap_count >= 2)
  - SQLite 호환성 테스트
- **Risk & Rollback**: LAG 함수 미지원 시 기본 JOIN 쿼리 사용
- **Effort**: 4시간 (Medium)
- **Touch Points**: `overlap_optimizer.py`

#### **3.3 연결된 끝 찾기 (SQLite datetime)** [ ]
- **Description**: ROW_NUMBER + datetime() 함수로 연속 데이터 끝점 찾기
- **Acceptance Criteria**:
  - _find_connected_end() → 200개 범위 내 연속 데이터 끝점 반환
  - SQLite datetime() 함수로 시간 계산
  - expected_start 비교로 연속성 판단
- **Test Plan**:
  - 완전 연속 데이터 테스트
  - 중간 끊어진 데이터 테스트
  - 200개 제한 테스트
- **Risk & Rollback**: 복잡한 쿼리 실패 시 단순 순차 검사
- **Effort**: 4시간 (Medium)
- **Touch Points**: `overlap_optimizer.py`

#### **3.4 4단계 통합 최적화 엔진** [ ]
- **Description**: 4단계 로직을 통합한 메인 최적화 엔진 구현
- **Acceptance Criteria**:
  - optimize_candle_requests() → API 요청 목록 및 절약 통계 반환
  - 단계별 성능 추적 및 로깅
  - API 호출 60% 감소 달성
- **Test Plan**:
  - 각 단계별 개별 테스트
  - 전체 최적화 흐름 통합 테스트
  - 성능 벤치마크 (기존 대비 60% 감소)
- **Risk & Rollback**: 최적화 실패 시 200개 단순 요청
- **Effort**: 6시간 (High)
- **Touch Points**: `overlap_optimizer.py`, `models.py`

---

### **4. 업비트 API 클라이언트 특화** 📡
**목표**: 200개 제한, 시작점 배제, 반간격 안전요청 구현

#### **4.1 업비트 특화 파라미터 최적화** [ ]
- **Description**: 시작점 배제 및 반간격 안전요청 로직 구현
- **Acceptance Criteria**:
  - _create_safe_api_request() → 반간격 이전 시작점 계산
  - 200개 제한 자동 적용
  - 업비트 API 형식 완벽 호환
- **Test Plan**:
  - 실제 업비트 API 호출 테스트
  - 파라미터 변환 정확성 테스트
  - Rate limit 준수 테스트
- **Risk & Rollback**: API 호출 실패 시 기존 파라미터 사용
- **Effort**: 4시간 (Medium)
- **Touch Points**: `candle_client.py` (새 파일)

#### **4.2 Rate Limit 및 재시도 전략** [ ]
- **Description**: 600req/min 제한 준수 및 지능형 재시도 구현
- **Acceptance Criteria**:
  - _calculate_rate_limit_delay() → 적절한 지연시간 계산
  - RetryConfig 기반 재시도 전략
  - 429, 5xx 오류 자동 재시도
- **Test Plan**:
  - Rate limit 시뮬레이션 테스트
  - 재시도 로직 테스트
  - 백오프 전략 검증
- **Risk & Rollback**: 재시도 실패 시 기본 예외 발생
- **Effort**: 3시간 (Medium)
- **Touch Points**: `candle_client.py`

---

### **5. 고속 메모리 캐시 시스템** ⚡
**목표**: 90% 캐시 히트율, TTL 60초, 3ms 응답시간 달성

#### **5.1 CandleCache 구현** [ ]
- **Description**: fast_cache.py 기반 TTL 60초 캐시 시스템 구현
- **Acceptance Criteria**:
  - get() → 3ms 이내 응답
  - TTL 60초 정확 적용
  - 90% 이상 히트율 달성
- **Test Plan**:
  - 캐시 히트/미스 테스트
  - TTL 만료 테스트
  - 동시 접근 성능 테스트
- **Risk & Rollback**: 캐시 실패 시 DB 직접 조회
- **Effort**: 2시간 (Low) - 기존 코드 이관
- **Touch Points**: `candle_cache.py` (기존 fast_cache.py 이관)

---

### **6. 메인 Facade 및 통합 시스템** 🏆
**목표**: 단일 API로 모든 기능 통합, 기존 인터페이스 호환성 유지

#### **6.1 CandleDataProvider 메인 Facade** [ ]
- **Description**: 모든 컴포넌트를 통합한 단일 진입점 구현
- **Acceptance Criteria**:
  - get_candles() → 모든 파라미터 조합 지원
  - 기존 인터페이스 100% 호환
  - 내부적으로 4단계 최적화 적용
- **Test Plan**:
  - 기존 API 호환성 테스트
  - 모든 파라미터 조합 테스트
  - 7규칙 전략과의 통합 테스트
- **Risk & Rollback**: 통합 실패 시 개별 컴포넌트 직접 사용
- **Effort**: 5시간 (Medium)
- **Touch Points**: `candle_data_provider.py` (새 파일)

#### **6.2 데이터 모델 통합** [ ]
- **Description**: 모든 컴포넌트에서 사용할 통일된 데이터 모델 정의
- **Acceptance Criteria**:
  - CandleModel → 업비트 API 응답 완벽 매핑
  - OptimizationResult → 최적화 결과 상세 정보
  - ApiRequest → 업비트 API 파라미터 변환
- **Test Plan**:
  - 데이터 모델 변환 테스트
  - 타입 힌트 검증
  - 직렬화/역직렬화 테스트
- **Risk & Rollback**: 기존 dict 형태로 폴백
- **Effort**: 2시간 (Low)
- **Touch Points**: `models.py` (새 파일)

---

### **7. 성능 모니터링 및 품질 보증** 📊
**목표**: 실시간 성능 추적 및 품질 지표 모니터링

#### **7.1 성능 메트릭 수집** [ ]
- **Description**: API 절약률, 캐시 히트율, 응답시간 등 핵심 지표 수집
- **Acceptance Criteria**:
  - get_optimization_metrics() → 실시간 성능 지표 반환
  - Infrastructure 로깅 연동
  - 대시보드 지원 형태 데이터 제공
- **Test Plan**:
  - 메트릭 정확성 테스트
  - 로깅 포맷 검증
  - 성능 오버헤드 측정
- **Risk & Rollback**: 모니터링 실패 시 기본 로깅만 사용
- **Effort**: 3시간 (Medium)
- **Touch Points**: 모든 파일 (로깅 추가)

#### **7.2 통합 테스트 및 검증** [ ]
#### **7.2 통합 테스트 및 검증** [ ]
- **Description**: 전체 시스템 통합 테스트 및 7규칙 전략 호환성 검증
- **Acceptance Criteria**:
  - `python run_desktop_ui.py` → 7규칙 전략 완전 동작
  - 모든 Acceptance Criteria 100% 만족
  - 성능 목표 달성 검증
- **Test Plan**:
  - End-to-End 테스트
  - 성능 벤치마크
  - 7규칙 전략 통합 테스트
- **Risk & Rollback**: 검증 실패 시 개별 컴포넌트 수정
- **Effort**: 4시간 (Medium)
- **Touch Points**: 전체 시스템

---

## 📅 **구현 순서 및 의존성**

### **Phase 1: 기반 시스템** (1-2일)
```
1.1 TimeUtils 확장 [ ] → 1.2 시간 형식 표준화 [ ]
└── 2.1 CandleTableManager [ ] → 2.2 CandleRepository [ ]
```

### **Phase 2: 최적화 엔진** (3-4일)
```
3.1 완전 겹침 확인 [ ] → 3.2 파편화 확인 [ ] → 3.3 연결된 끝 찾기 [ ]
└── 3.4 4단계 통합 최적화 엔진 [ ]
```

### **Phase 3: API 및 캐시** (5일)
```
4.1 업비트 파라미터 최적화 [ ] → 4.2 Rate Limit 처리 [ ]
└── 5.1 CandleCache 구현 [ ]
```

### **Phase 4: 통합 및 검증** (6-7일)
```
6.1 메인 Facade [ ] → 6.2 데이터 모델 통합 [ ]
└── 7.1 성능 모니터링 [ ] → 7.2 통합 테스트 [ ]
```

---

## 🎯 **핵심 성공 지표**

### **개발 단계 KPI**
- [ ] **코드 품질**: 타입 힌트 100%, DDD 패턴 준수
- [ ] **테스트 커버리지**: 95% 이상, 모든 핵심 로직 검증
- [ ] **성능 목표**: 각 컴포넌트별 응답시간 SLA 준수

### **통합 단계 KPI**
- [ ] **API 호출 감소**: 60% 이상 달성
- [ ] **캐시 효율**: 90% 히트율 달성
- [ ] **응답시간**: P95 < 200ms 달성
- [ ] **시간 일관성**: 100% 정확한 시간 계산

### **운영 준비 KPI**
- [ ] **7규칙 호환**: 완전한 기술적 지표 계산 지원
- [ ] **모니터링**: 실시간 성능 지표 수집
- [ ] **안정성**: 예외 상황 완벽 대응

---

## 💡 **Risk Mitigation Strategy**

### **High Risk → Medium Risk**
- **SQLite 호환성**: 모든 SQL 문법 사전 검증
- **시간 일관성**: 단위 테스트로 time_utils 연동 완벽 검증
- **성능 목표**: 각 단계별 벤치마크로 조기 성능 이슈 발견

### **Technical Debt 최소화**
- **DDD 패턴**: Repository, Entity 명확한 분리
- **Infrastructure 로깅**: 모든 컴포넌트 표준 로깅 적용
- **타입 안전성**: 완전한 타입 힌트로 런타임 오류 방지

**🚀 Ready for Implementation**: 모든 태스크가 구체적이고 측정 가능하며 독립적으로 개발 가능합니다!

---

## 📝 **Persistent Notes**

### **Touched Files** (DDD 준수 구조)
- [ ] `upbit_auto_trading/domain/repositories/candle_repository_interface.py` - **Domain Layer** Repository 인터페이스
- [ ] `upbit_auto_trading/infrastructure/repositories/sqlite_candle_repository.py` - **Infrastructure Layer** Repository 구현체
- [ ] `upbit_auto_trading/infrastructure/market_data/candle/time_utils.py` - 확장됨 (Infrastructure Layer)
- [ ] `upbit_auto_trading/infrastructure/market_data/candle/overlap_optimizer.py` - 신규 생성 (Infrastructure Layer)
- [ ] `upbit_auto_trading/infrastructure/market_data/candle/candle_client.py` - 신규 생성 (Infrastructure Layer)
- [ ] `upbit_auto_trading/infrastructure/market_data/candle/candle_cache.py` - 기존 이관 (Infrastructure Layer)
- [ ] `upbit_auto_trading/infrastructure/market_data/candle/candle_data_provider.py` - **Application Service** Facade
- [ ] `upbit_auto_trading/infrastructure/market_data/candle/models.py` - 신규 생성 (Infrastructure Layer)

### **Unexpected Findings** (구현 중 발견사항)
- (구현 진행 중 업데이트 예정)

### **Useful Links & References**
- PRD v4.0: `candle_data_provider_prd_v4.md`
- 기존 time_utils 분석: `time_utils_spec.md`
- overlap_optimizer 상세 스펙: `overlap_optimizer_spec.md`
- SQLite 공식 문서: https://www.sqlite.org/lang_datefunc.html
- 업비트 API 문서: https://docs.upbit.com/reference

### **Implementation Progress**
- **완료된 태스크**: (Step 3 진행 중 업데이트)
- **현재 작업 중**: (현재 태스크 표시)
- **다음 예정**: (다음 태스크 표시)

### **Performance Benchmarks** (구현 후 업데이트)
- API 호출 감소율: (목표 60%)
- 캐시 히트율: (목표 90%)
- 응답시간 P95: (목표 <200ms)
- 시간 일관성: (목표 100%)
