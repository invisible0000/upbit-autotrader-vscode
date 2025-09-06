# 🎯 CandleDataProvider v2.0 PRD - 신규 구현 방향

## 📋 **Problem & Users**

### **Problem Statement**
- 기존 smart_data_provider_V4는 15개 모듈로 과도하게 복잡하고 WebSocket/실시간 기능으로 인한 시스템 복잡성 증가
- SmartRouter 의존성으로 인한 캔들 데이터 전용 시스템의 불필요한 복잡도
- 래핑 방식으로는 기존 아키텍처의 복잡성을 근본적으로 해결할 수 없음
- 7규칙 자동매매 전략에 특화된 단순하고 안정적인 캔들 데이터 시스템 필요

### **Target Users**
- **Primary**: 7규칙 자동매매 전략 실행 엔진
- **Secondary**: 백테스팅 시스템, 차트 UI 컴포넌트
- **Tertiary**: 기술적 분석 모듈, 시장 데이터 분석 도구

### **Value Proposition**
- **단순성**: 9개 파일, 단일 폴더로 복잡도 90% 감소
- **안정성**: 검증된 로직 재구현으로 신뢰성 확보
- **성능**: API 호출 50% 감소, 캐시 히트율 85% 달성
- **유지보수성**: 명확한 책임 분리로 개발/운영 효율성 극대화

---

## 🎯 **Goals & Non-goals**

### **Primary Goals**
1. **📊 완전한 캔들 데이터 관리**: OHLCV 데이터 수집, 저장, 조회의 통합 솔루션
2. **⚡ 고성능 응답**: 캐시 5ms, DB 50ms, API 300ms (P95 기준) 달성
3. **🔒 데이터 무결성**: 빈 캔들 자동 채우기로 연속성 100% 보장
4. **🚀 API 최적화**: 지능형 겹침 분석으로 불필요한 API 호출 50% 감소
5. **🎯 7규칙 완벽 지원**: RSI, 이동평균, 볼린저밴드 등 모든 기술적 지표 지원

### **Secondary Goals**
- 대용량 동기화: 30일치 캔들 데이터 일괄 수집
- 품질 모니터링: 수집률, 캐시 히트율, 응답시간 추적
- 오류 복구: API 장애시 캐시/DB 폴백으로 가용성 99.9% 보장

### **Non-goals**
- ❌ **실시간 스트리밍**: WebSocket 기반 실시간 캔들 구독 (별도 시스템)
- ❌ **다중 거래소**: 업비트 전용 구현 (확장성 고려하되 다른 거래소는 별도)
- ❌ **고빈도 거래**: 초/밀리초 단위 실시간 데이터 (TradeDataProvider 영역)
- ❌ **복잡한 분석**: 고급 시장 분석 도구 (Analytics 레이어 영역)

---

## 🏗️ **Scope & Architecture**

### **Core System Architecture**
```
upbit_auto_trading/infrastructure/market_data/candle/
├── candle_data_provider.py       # 🏆 메인 Facade (통합 API)
├── candle_client.py              # 📡 업비트 API 클라이언트
├── candle_storage.py             # 💾 데이터베이스 관리
├── candle_cache.py               # ⚡ 고속 메모리 캐시
├── candle_status.py              # 📊 수집 상태 관리
├── overlap_analyzer.py           # 🎯 API 최적화 엔진
├── time_utils.py                 # ⏰ 시간 처리 유틸
├── models.py                     # 📝 데이터 모델
└── exceptions.py                 # ⚠️ 예외 정의
```

### **Key UX Flows**

#### **Flow 1: 기본 캔들 조회** (Primary)
```python
provider = CandleDataProvider()
# 개수 기반 조회 (기존 방식)
candles = await provider.get_candles("KRW-BTC", "1m", count=100)
# 기간 기반 조회 (신규 - 스크리너용)
candles = await provider.get_candles("KRW-BTC", "1m", end="2024-01-01T00:00:00Z", to="2024-01-02T00:00:00Z")
# end만 지정시 현재 시간 기준으로 자동 계산
candles = await provider.get_candles("KRW-BTC", "1m", end="2024-01-01T00:00:00Z")
# 1. 파라미터 검증 → 2. 캐시 확인 → 3. 겹침 분석 → 4. 최적화된 API 호출 → 5. DB 저장
```

#### **Flow 2: 대용량 데이터 동기화** (Secondary)
```python
success = await provider.sync_candles("KRW-BTC", "1m", days=30)
# 1. 누락 구간 분석 → 2. OverlapAnalyzer 최적화 → 3. 배치 수집 → 4. 진행률 추적 → 5. 품질 리포트
```

#### **Flow 3: 품질 모니터링** (Operational)
```python
report = await provider.get_quality_report("KRW-BTC", "1m")
# 1. 수집률 계산 → 2. 캐시 성능 → 3. 오류율 → 4. 권장사항
```

---

## 🔧 **Technical Constraints & Dependencies**

### **Performance Constraints**
- **응답시간 SLA**: 캐시 <5ms, DB <50ms, API <300ms (P95)
- **처리량**: 100 req/sec 동시 처리 (7규칙 전략 실행 기준)
- **메모리 사용량**: 100MB 이하 안정적 운영
- **API Rate Limit**: upbit_public_client에서 내재적 준수 (600req/min 제한)

### **Data Constraints**
- **저장 용량**: 심볼당 최대 1년치 캔들 데이터 (약 500MB)
- **정밀도**: Decimal 기반 정확한 가격 계산
- **무결성**: 빈 캔들 5% 이하 유지
- **일관성**: 시간대 UTC 통일, 캔들 경계 정확한 정렬

### **System Dependencies**
- **Database**: SQLite3 market_data.sqlite3 (단일 DB 집중)
- **API Client**: upbit_public_client (검증된 API 클라이언트)
- **Logging**: Infrastructure 로깅 시스템 (create_component_logger)
- **Environment**: Python 3.9+, Windows PowerShell 환경

---

## ✅ **Acceptance Criteria**

### **Functional Requirements**
- [ ] **API 완전성**: get_candles() 모든 파라미터 조합 완벽 동작
  - count 기반: (symbol, interval, count, to) 조합
  - 기간 기반: (symbol, interval, end, to) 조합 - 자동 count 계산
  - end만 지정시 현재 시간 기준 자동 처리
- [ ] **데이터 연속성**: 실제 업비트 API 데이터 기반 연속성 보장 (빈 캔들 논리적 검증 필요)
- [ ] **배치 처리**: sync_candles()로 30일치 데이터 일괄 수집 성공
- [ ] **오류 복구**: API 장애시 캐시→DB→빈응답 순차 폴백으로 시스템 중단 방지
- [ ] **7규칙 지원**: RSI, 이동평균, 볼린저밴드 등 모든 기술적 지표 계산 가능

### **Performance Requirements**
- [ ] **응답시간**: 캐시 5ms, DB 50ms, API 300ms (P95 기준) 달성
- [ ] **캐시 효율**: 85% 이상 히트율, TTL 60초 최적화
- [ ] **API 최적화**: OverlapAnalyzer로 50% 호출 감소 확인
- [ ] **처리량**: 100 req/sec 동시 처리 성공
- [ ] **메모리 안정성**: 100MB 이하에서 24시간 연속 동작

### **Quality Requirements**
- [ ] **테스트 커버리지**: 90% 이상, 모든 비즈니스 로직 검증
- [ ] **로깅 완전성**: 모든 주요 동작 Infrastructure 로깅으로 추적 가능
- [ ] **에러 처리**: 모든 예외 상황 graceful handling, 시스템 중단 방지
- [ ] **UI 통합**: `python run_desktop_ui.py` 7규칙 전략 완전 동작

---

## 📊 **Observability & Monitoring**

### **Key Metrics**
```python
# 성능 지표
response_time_p95: float        # 응답시간 95퍼센타일
cache_hit_rate: float           # 캐시 히트율 (목표: 85%+)
api_call_reduction: float       # API 호출 감소율 (목표: 50%+)

# 품질 지표
data_coverage: float            # 데이터 수집률 (목표: 95%+)
empty_candle_rate: float        # 빈 캔들 비율 (목표: 5% 이하)
error_rate: float               # 오류율 (목표: 1% 이하)

# 운영 지표
memory_usage_mb: float          # 메모리 사용량 (목표: 100MB 이하)
concurrent_requests: int        # 동시 처리 요청 수
uptime_percentage: float        # 가용성 (목표: 99.9%+)
```

### **Logging Strategy**
```python
# 성공 케이스
logger.info("캔들 조회 성공", extra={
    "symbol": "KRW-BTC", "interval": "1m", "count": 100,
    "source": "cache", "response_time_ms": 3.2,
    "operation_id": "candle_123456"
})

# 성능 모니터링
logger.info("API 최적화 효과", extra={
    "original_calls": 3, "optimized_calls": 1,
    "reduction_rate": 66.7, "overlap_type": "COMPLETE_OVERLAP"
})

# 데이터 품질
logger.warning("빈 캔들 생성", extra={
    "symbol": "KRW-BTC", "missing_count": 5,
    "time_range": "2024-01-01 09:00 ~ 09:05"
})
```

### **Alert Conditions**
- **Critical**: 응답시간 P95 > 1000ms, 캐시 히트율 < 50%, 오류율 > 5%
- **Warning**: 빈 캔들 비율 > 10%, API 호출 감소율 < 30%
- **Info**: 메모리 사용량 > 80MB, 동시 요청 > 80개

---

## 🚨 **Risks & Rollback Strategy**

### **High Risk Issues**
1. **OverlapAnalyzer 복잡성 과소평가**
   - **Risk**: 200개 청크 기반 DB 파편화 분석과 최적화 로직이 예상보다 복잡
   - **Critical Point**: DB 기존 데이터 순차성 분석, 겹침 삭제 vs 청크 분할 결정 로직
   - **Mitigation**: 별도 상세 분석 문서 작성, 단계별 구현 검증
   - **Rollback**: 기본 200개 단위 요청으로 폴백

2. **성능 목표 미달성**
   - **Risk**: 응답시간 또는 처리량 목표 달성 실패
   - **Mitigation**: 단계별 성능 측정, 조기 최적화
   - **Rollback**: TTL 조정, 캐시 크기 확대, 배치 크기 최적화

### **Medium Risk Issues**
1. **빈 캔들 처리 로직 검증 필요**
   - **Risk**: 현재 빈 캔들 자동 생성 방식의 타당성 검증 필요
   - **Question**: 실제 업비트 API 데이터만으로 충분한지, 인위적 생성이 필요한지 분석
   - **Mitigation**: 기존 collection_status_manager 로직 상세 분석, 실제 데이터 검증
   - **Rollback**: 원본 API 데이터만 반환, 인위적 생성 비활성화

2. **API 클라이언트 통합 이슈**
   - **Risk**: upbit_public_client와의 파라미터 불일치
   - **Mitigation**: 기존 코드 철저 분석, 파라미터 검증 로직 강화
   - **Rollback**: 기본 파라미터로 요청, 검증 로직 단순화

### **Rollback Plan**
```python
# Phase 1: 기본 기능 폴백
class SimpleCandleProvider:
    """최소 기능 폴백 시스템"""
    async def get_candles_simple(self, symbol: str, interval: str, count: int):
        # 캐시 확인 → API 직접 호출 → DB 저장
        # 겹침 분석, 빈 캔들 생성 등 고급 기능 제외

# Phase 2: 기존 시스템 임시 복원
# smart_data_provider_V4의 핵심 모듈만 선별적 복원
```

---

## 🎯 **Implementation Approach**

### **기존 코드 참조 및 이관 전략**

#### **🟢 완전 이관 대상 (핵심 로직)**
| 기존 파일 | 이관 대상 | 핵심 기능 | 수정 사항 |
|-----------|-----------|-----------|-----------|
| `fast_cache.py` (97줄) | `candle_cache.py` | TTL 60초 메모리 캐시 | TTL만 60초로 조정 |
| `time_utils.py` (74줄) | `time_utils.py` | 캔들 시간 경계 정렬 | 완전 동일하게 이관 |
| `response_models.py` (177줄) | `models.py` | DataResponse, Priority | 캔들 전용으로 단순화 |
| `overlap_analyzer.py` (200줄) | `overlap_analyzer.py` | 6가지 겹침 패턴 분석 | API 호출 로직만 수정 |

#### **🟡 부분 이관 대상 (핵심 기능만 추출)**
| 기존 파일 | 이관 대상 | 추출할 핵심 기능 | 제거할 부분 |
|-----------|-----------|------------------|-------------|
| `batch_db_manager.py` (654줄) | `candle_storage.py` | `insert_candles_batch()` 메서드 | SmartRouter 의존성, 복잡한 설정 |
| `collection_status_manager.py` (252줄) | `candle_status.py` | 빈 캔들 자동 생성 로직 | 실시간 상태 추적, WebSocket 연동 |
| `smart_data_provider.py` (377줄) | `candle_data_provider.py` | 단일/다중 심볼 처리 로직 | SmartRouter, 실시간 채널 선택 |

#### **🔴 신규 구현 대상 (단순화 및 특화)**
| 신규 파일 | 구현 기능 | 기존 참조 | 신규 특화 요소 |
|-----------|-----------|-----------|----------------|
| `candle_client.py` | 업비트 API 클라이언트 특화 | `upbit_public_client` | 기간→count 자동변환, 파라미터 검증 |
| `models.py` | 통합 데이터 모델 | 3개 모델 파일 | 캔들 전용 단순화 |
| `exceptions.py` | 캔들 전용 예외 | - | 명확한 에러 분류 |

### **중요: 상세 분석 필요 영역**
- **OverlapAnalyzer**: 별도 상세 로직 분석 문서 필요 (DB 파편화, 청크 최적화 전략)
- **빈 캔들 처리**: collection_status_manager 기존 구현 방식 검증 필요
- **개별 파일 명세**: 각 신규 파일별 상세 기능 명세 문서 작성 필요

### **핵심 기능별 이관 세부사항**

#### **1. 캐시 시스템 이관** (`fast_cache.py` → `candle_cache.py`)
```python
# 기존 코드 (fast_cache.py - 97줄)
class FastCache:
    def __init__(self, default_ttl: float = 0.2):  # 200ms
        self.cache: Dict[str, CacheItem] = {}
        self.default_ttl = default_ttl

# 신규 구현 (candle_cache.py)
class CandleCache:
    def __init__(self, default_ttl: float = 60.0):  # 60초로 변경
        self._cache = FastCache(default_ttl=default_ttl)  # 기존 로직 재사용

    def get_candles(self, key: str) -> Optional[List[dict]]:
        """캔들 전용 캐시 조회"""
        return self._cache.get(key)
```

#### **2. 시간 처리 이관** (`time_utils.py` → `time_utils.py`)
```python
# 기존 코드 (time_utils.py - 74줄) - 완전 동일하게 이관
def generate_candle_times(start_time: datetime, end_time: datetime, timeframe: str) -> List[datetime]:
    """시작~종료 사이 모든 캔들 시간 생성 - 완전 이관"""

def _align_to_candle_boundary(dt: datetime, timeframe_minutes: int) -> datetime:
    """캔들 경계 정렬 - 완전 이관"""

# 신규 추가: 캔들 전용 유틸리티
def get_candle_key(symbol: str, interval: str, timestamp: datetime) -> str:
    """캔들 캐시 키 생성"""
    return f"candle:{symbol}:{interval}:{timestamp.isoformat()}"
```

#### **3. 겹침 분석 이관** (`overlap_analyzer.py` → `overlap_analyzer.py`)
```python
# 기존 핵심 로직 (overlap_analyzer.py - 200줄)
class OverlapAnalyzer:
    def find_optimal_requests(self, requested_range, available_data):
        """6가지 겹침 패턴 분석 - 핵심 로직 이관"""
        # COMPLETE_OVERLAP, PARTIAL_OVERLAP 등 로직 완전 이관

# 신규 특화: API 호출 직접 통합
class CandleOverlapAnalyzer:
    def __init__(self, api_client: CandleClient):
        self._analyzer = OverlapAnalyzer()  # 기존 로직 재사용
        self._client = api_client

    async def get_optimized_candles(self, symbol: str, interval: str, count: int) -> List[dict]:
        """겹침 분석 + API 호출 통합"""
        # 기존 분석 로직 + 직접 API 호출
```

#### **4. 데이터베이스 이관** (`batch_db_manager.py` → `candle_storage.py`)
```python
# 기존 핵심 기능 (batch_db_manager.py - 654줄)
class BatchDBManager:
    def insert_candles_batch(self, candles: List[dict], batch_size: int = 1000):
        """배치 INSERT 최적화 - 핵심 로직 이관"""

# 신규 특화 구현
class CandleStorage:
    def __init__(self):
        self._batch_manager = BatchDBManager()  # 기존 로직 재사용

    async def save_candles(self, symbol: str, interval: str, candles: List[dict]) -> bool:
        """캔들 전용 저장 로직"""
        # 기존 batch_insert + 캔들 특화 검증
        return self._batch_manager.insert_candles_batch(candles)
```

### **제거되는 기능들**
- **SmartRouter 전체**: WebSocket/REST 자동 선택 (캔들은 REST만 사용)
- **실시간 처리 모듈**: `realtime_data_handler.py`, `realtime_candle_manager.py`
- **복잡한 캐시**: `adaptive_ttl_manager.py`, `memory_realtime_cache.py`
- **백그라운드 처리**: `background_processor.py` (동기화 기능만 단순 구현)

### **신규 보완 기능들**
- **통합 Facade**: `CandleDataProvider` 단일 진입점
- **파라미터 검증**: `CandleClient`에서 업비트 API 스펙 완전 준수
- **통합 모델**: `models.py`에서 응답/캐시/수집 모델 통합
- **명확한 예외**: `exceptions.py`로 에러 분류 체계화

---

## 📅 **Implementation Timeline**

### **Phase 1: 기존 로직 이관** (3일)
- Day 1: 핵심 모듈 이관 (`time_utils.py`, `fast_cache.py`)
- Day 2: 복잡 모듈 부분 이관 (`overlap_analyzer.py`, `batch_db_manager.py`)
- Day 3: 응답 모델 통합 (`response_models.py` → `models.py`)

### **Phase 2: 신규 특화 구현** (4일)
- Day 4-5: `CandleDataProvider` 메인 Facade 구현
- Day 6: `CandleClient` API 클라이언트 구현
- Day 7: `CandleStorage`, `CandleStatus` 구현

### **Phase 3: 통합 및 최적화** (2일)
- Day 8: 전체 시스템 통합, 성능 최적화
- Day 9: 테스트 커버리지 90% 달성, 최종 검증

**총 기간**: 9일 (기존 계획 대비 동일, 이관 효율성으로 품질 향상)

---

## ✅ **Success Criteria Summary**

### **즉시 검증 가능한 성공 기준**
- [ ] `python run_desktop_ui.py` → 7규칙 전략 생성 → 완전 동작
- [ ] 100개 캔들 조회 P95 < 300ms 달성
- [ ] 30일 동기화 성공률 95% 이상
- [ ] 24시간 연속 운영 메모리 100MB 이하

### **운영 단계 성공 기준**
- [ ] 캐시 히트율 85% 이상 유지
- [ ] API 호출 50% 감소 확인
- [ ] 빈 캔들 비율 5% 이하 유지
- [ ] 오류율 1% 이하 지속

**🎯 최종 목표**: 단순하고 안정적이며 고성능인 캔들 데이터 시스템으로 7규칙 자동매매 전략의 완벽한 기반 구축
