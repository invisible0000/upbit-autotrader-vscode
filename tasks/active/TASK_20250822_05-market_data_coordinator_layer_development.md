# 📋 TASK_20250822_05: Market Data Coordinator Layer 개발

## 🎯 태스크 목표
- **주요 목표**: 대용량 마켓 데이터 요청을 효율적으로 분할하고 병렬 처리하는 Coordinator Layer (Layer 3) 구현
- **완료 기준**:
  - ✅ 대용량 요청 자동 분할 (1000개 캔들 → 5번의 200개 요청)
  - ✅ 데이터 타입별 최적화된 분할 전략 (캔들/티커/호가창/체결)
  - ✅ 병렬 처리 및 레이트 제한 준수
  - ✅ Layer 2 Storage와 완벽 연동되는 Coordinator API

## 📊 현재 상황 분석 (2025-08-22 기준)

### ✅ **완료된 하위 Layer 상황**
- **Layer 1: Smart Routing V2.0** ✅ 완료 - 채널 선택 및 API 호출
- **Layer 2: Market Data Storage** 🔄 개발 중 - 캐시 및 영속성

### 🎯 **Layer 3: Coordinator의 역할 정의**

#### **핵심 책임**
- **대용량 요청 분할**: 클라이언트의 대용량 요청을 처리 가능한 크기로 자동 분할
- **병렬 처리 최적화**: 동시 요청 수 제어, 업비트 API 레이트 제한 준수
- **데이터 타입별 전략**: 캔들(시간 기반), 티커(심볼 기반), 호가창(심볼 기반), 체결(시간/카운트 기반)
- **결과 통합**: 분할된 응답들을 완전한 데이터셋으로 합성

#### **처리 시나리오 예시**
```
차트뷰어: "KRW-BTC 1분봉 1000개 조회"
    ↓ Coordinator 분할 전략
5번의 200개 캔들 요청 → Layer 2 Storage 병렬 전달
    ↓ 결과 통합
1000개 완전한 캔들 데이터 → 차트뷰어 반환

스크리너: "KRW 마켓 전체 189개 티커 조회"
    ↓ Coordinator 분할 전략
19번의 10개 심볼 요청 → Layer 2 Storage 병렬 전달
    ↓ 결과 통합
189개 완전한 티커 데이터 → 스크리너 반환

백테스터: "KRW-BTC 1분봉 3개월 데이터"
    ↓ Coordinator 분할 전략
수십 번의 시간 범위별 요청 → Layer 2 Storage 순차 전달
    ↓ 점진적 통합
완료된 구간부터 백테스터에 순차 반환
```

## 🛠️ Coordinator Layer 아키텍처 설계

### 🔗 **Layer 2 Storage와의 연동 흐름**

```
클라이언트 → Coordinator API (대용량 요청)
    ↓
Request Splitter (요청 분할기)
    ├─ 캔들: 시간 범위 기반 분할 (200개씩)
    ├─ 티커: 심볼 기반 분할 (10개씩)
    ├─ 호가창: 심볼 기반 분할 (5개씩)
    └─ 체결: 시간/카운트 기반 분할
    ↓
Parallel Processor (병렬 처리기)
    ├─ 레이트 제한 준수 (초당 10회)
    ├─ 동시 요청 수 제어 (최대 5개)
    └─ 에러 복구 및 재시도
    ↓
Layer 2 Storage (여러 번의 소규모 요청)
    ↓
Data Aggregator (결과 통합기)
    ├─ 시간순 정렬 (캔들)
    ├─ 심볼별 그룹화 (티커/호가창)
    ├─ 중복 제거 및 검증
    └─ 메타데이터 생성
    ↓
클라이언트 (완전한 대용량 데이터)
```

### 📊 **핵심 인터페이스 설계**

```python
# 표준 Coordinator 요청/응답 구조
@dataclass
class CoordinatorRequest:
    data_type: DataType  # CANDLE, TICKER, ORDERBOOK, TRADE
    symbols: List[str]
    timeframe: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    count: Optional[int] = None
    split_strategy: Optional[str] = None  # "auto", "time", "symbol", "count"

@dataclass
class CoordinatorResponse:
    success: bool
    data: List[Dict[str, Any]]
    metadata: CoordinatorMetadata
    error: Optional[str] = None

@dataclass
class CoordinatorMetadata:
    original_request_size: int
    split_count: int
    parallel_requests: int
    processing_time_ms: float
    data_count: int
    split_strategy_used: str
```

## 🗺️ 체계적 작업 계획

### Phase 1: 분할 전략 인터페이스 설계 📝 **Storage 완료 후 시작**
- [ ] 1.1 IMarketDataCoordinator 인터페이스 정의
- [ ] 1.2 ISplitStrategy 추상 인터페이스 설계
- [ ] 1.3 IDataAggregator 결과 통합 인터페이스 설계
- [ ] 1.4 Layer 2 Storage 연동 인터페이스 설계

### Phase 2: 데이터 타입별 분할 전략 구현
- [ ] 2.1 CandleSplitter - 시간 범위 기반 분할 (200개 단위)
- [ ] 2.2 TickerSplitter - 심볼 기반 분할 (10개 단위)
- [ ] 2.3 OrderbookSplitter - 심볼 기반 분할 (5개 단위)
- [ ] 2.4 TradeSplitter - 시간/카운트 하이브리드 분할
- [ ] 2.5 SplitStrategyFactory - 데이터 타입별 전략 자동 선택

### Phase 3: 병렬 처리 및 최적화 시스템
- [ ] 3.1 ParallelProcessor - 비동기 병렬 요청 처리기
- [ ] 3.2 RateLimiter - 업비트 API 제한 준수 (초당 10회)
- [ ] 3.3 RetryHandler - 실패 요청 자동 재시도
- [ ] 3.4 LoadBalancer - 시스템 부하 기반 동시성 조절

### Phase 4: 결과 통합 및 검증 시스템
- [ ] 4.1 DataAggregator - 타입별 데이터 통합기
- [ ] 4.2 CandleAggregator - 캔들 시간순 정렬 및 연속성 검증
- [ ] 4.3 RealtimeAggregator - 티커/호가창/체결 최신 데이터 우선
- [ ] 4.4 MetadataGenerator - 요청 통계 및 성능 지표 생성

### Phase 5: Coordinator Service 통합 구현
- [ ] 5.1 MarketDataCoordinatorService 메인 서비스
- [ ] 5.2 Layer 2 Storage 연동 (StorageConnector)
- [ ] 5.3 에러 처리 및 폴백 메커니즘
- [ ] 5.4 진행률 추적 및 모니터링

### Phase 6: 테스트 및 최적화
- [ ] 6.1 Layer 2 Storage 연동 테스트
- [ ] 6.2 대용량 데이터 분할/통합 테스트
- [ ] 6.3 병렬 처리 성능 테스트
- [ ] 6.4 레이트 제한 및 에러 복구 테스트

## 🛠️ 단순화된 파일 구조

```
market_data_coordinator/               # Layer 3 - Coordinator
├── __init__.py
├── interfaces/                        # 추상 인터페이스
│   ├── __init__.py
│   ├── coordinator_service.py         # IMarketDataCoordinator
│   ├── split_strategy.py              # ISplitStrategy
│   ├── data_aggregator.py             # IDataAggregator
│   └── storage_connector.py           # IStorageConnector
├── implementations/                   # 핵심 구현체
│   ├── __init__.py
│   ├── coordinator_service.py         # MarketDataCoordinatorService (메인)
│   ├── request_splitter.py            # 요청 분할 관리자
│   ├── parallel_processor.py          # 병렬 처리 엔진
│   ├── data_aggregator.py             # 결과 통합 관리자
│   └── storage_connector.py           # Layer 2 연동
├── strategies/                        # 분할 전략들
│   ├── __init__.py
│   ├── candle_splitter.py             # 캔들 시간 기반 분할
│   ├── ticker_splitter.py             # 티커 심볼 기반 분할
│   ├── orderbook_splitter.py          # 호가창 심볼 기반 분할
│   ├── trade_splitter.py              # 체결 시간/카운트 분할
│   └── strategy_factory.py            # 전략 자동 선택
├── aggregators/                       # 결과 통합기들
│   ├── __init__.py
│   ├── candle_aggregator.py           # 캔들 시간순 통합
│   ├── realtime_aggregator.py         # 실시간 데이터 통합
│   └── metadata_generator.py          # 메타데이터 생성
├── utils/                             # 유틸리티
│   ├── __init__.py
│   ├── rate_limiter.py                # 레이트 제한 관리
│   ├── retry_handler.py               # 재시도 로직
│   ├── load_balancer.py               # 부하 분산
│   └── progress_tracker.py            # 진행률 추적
├── models/                            # 데이터 모델
│   ├── __init__.py
│   ├── coordinator_request.py         # CoordinatorRequest 모델
│   ├── coordinator_response.py        # CoordinatorResponse 모델
│   ├── split_plan.py                  # 분할 계획 모델
│   └── aggregation_result.py          # 통합 결과 모델
└── monitoring/                        # 모니터링
    ├── __init__.py
    ├── performance_tracker.py         # 성능 추적
    ├── split_analyzer.py              # 분할 전략 분석
    └── metrics_collector.py           # 지표 수집
```

## 🎯 핵심 구현 목표

### 1. **지능적 분할 전략**
- **캔들 데이터**: 시간 범위 기반 분할 (200개 단위, 연속성 보장)
- **티커 데이터**: 심볼 기반 분할 (10개 단위, 병렬 최적화)
- **호가창 데이터**: 심볼 기반 분할 (5개 단위, 실시간 처리)
- **체결 데이터**: 시간/카운트 하이브리드 분할 (유연한 크기 조절)

### 2. **병렬 처리 최적화**
- **동시 요청 제어**: 시스템 리소스 기반 적응적 조절 (기본 5개)
- **레이트 제한 준수**: 업비트 API 제한 (초당 10회) 엄격 준수
- **부하 분산**: CPU/메모리 사용률 기반 동시성 자동 조절
- **에러 복구**: 개별 요청 실패 시 자동 재시도 (최대 3회)

### 3. **결과 통합 및 검증**
- **캔들 통합**: 시간순 정렬, 중복 제거, 연속성 검증
- **실시간 통합**: 최신 데이터 우선, 타임스탬프 기반 정렬
- **데이터 검증**: 요청 크기와 응답 크기 일치 확인
- **메타데이터**: 분할/병렬/통합 성능 지표 제공

### 4. **Layer 2 Storage 연동**
- **투명한 위임**: 분할된 요청을 Storage API로 투명하게 전달
- **에러 전파**: Storage 에러를 적절히 상위로 전파
- **성능 최적화**: Storage 캐시 활용으로 중복 요청 최소화
- **진행률 추적**: 대용량 처리 시 클라이언트에 진행률 피드백

## 🔗 데이터 타입별 분할 전략 상세

### **1. 캔들 데이터 분할 (CandleSplitter)**
```python
# 시간 범위 기반 분할
요청: KRW-BTC 1분봉 1000개
분할 전략:
├─ Request 1: 최근 200개 (현재 시간부터)
├─ Request 2: 201-400개
├─ Request 3: 401-600개
├─ Request 4: 601-800개
└─ Request 5: 801-1000개

통합 전략: 시간순 역순 정렬 → 중복 제거 → 연속성 검증
```

### **2. 티커 데이터 분할 (TickerSplitter)**
```python
# 심볼 기반 분할
요청: KRW 마켓 전체 189개 티커
분할 전략:
├─ Request 1: ['KRW-BTC', 'KRW-ETH', ... ] (10개)
├─ Request 2: ['KRW-ADA', 'KRW-DOT', ... ] (10개)
├─ ...
└─ Request 19: ['KRW-XXX', 'KRW-YYY'] (9개)

통합 전략: 심볼별 그룹화 → 최신 타임스탬프 우선
```

### **3. 호가창 데이터 분할 (OrderbookSplitter)**
```python
# 심볼 기반 분할 (더 작은 단위)
요청: 주요 10개 코인 호가창
분할 전략:
├─ Request 1: ['KRW-BTC', 'KRW-ETH', 'KRW-ADA', 'KRW-DOT', 'KRW-SOL'] (5개)
└─ Request 2: ['KRW-MATIC', 'KRW-AVAX', 'KRW-ATOM', 'KRW-NEAR', 'KRW-XRP'] (5개)

통합 전략: 심볼별 최신 호가 데이터 유지
```

### **4. 체결 데이터 분할 (TradeSplitter)**
```python
# 시간/카운트 하이브리드 분할
요청: KRW-BTC 최근 1000개 체결
분할 전략:
├─ 1시간 단위로 시간 분할
├─ 각 시간대별 200개 카운트 제한
└─ 동적 크기 조절 (거래량에 따라)

통합 전략: 시간순 정렬 → 중복 체결 ID 제거
```

## 🎯 성공 기준

### 기능적 성공 기준
- ✅ **대용량 분할**: 1000개+ 요청 자동 분할 및 병렬 처리
- ✅ **데이터 정합성**: 분할/통합 과정에서 데이터 손실 없음
- ✅ **타입별 최적화**: 캔들/티커/호가창/체결 각각 최적 전략 적용
- ✅ **Layer 2 연동**: Storage API와 완벽 연동

### 성능적 성공 기준
- ✅ **병렬 처리**: 순차 처리 대비 3-5배 성능 향상
- ✅ **레이트 제한**: 업비트 API 제한 (초당 10회) 100% 준수
- ✅ **응답 시간**: 1000개 캔들 분할 처리 < 5초
- ✅ **메모리 효율**: 대용량 데이터도 일정한 메모리 사용량 유지

### 운영적 성공 기준
- ✅ **에러 복구**: 개별 요청 실패 시 자동 재시도 및 복구
- ✅ **진행률 추적**: 대용량 처리 시 실시간 진행률 제공
- ✅ **부하 조절**: 시스템 상황에 따른 동적 동시성 조절
- ✅ **모니터링**: 분할/병렬/통합 성능 메트릭 수집

## 💡 작업 시 주의사항

### Layer 2 연동 원칙
- **투명한 위임**: Coordinator는 분할만, 실제 데이터는 Storage에서
- **에러 전파**: Storage 에러를 적절히 클라이언트에 전파
- **캐시 활용**: Storage 캐시를 최대한 활용하여 중복 요청 방지
- **성능 추적**: 각 Storage 요청의 성능 지표 수집

### 분할 전략 원칙
- **데이터 타입 최적화**: 각 데이터 타입의 특성에 맞는 분할
- **연속성 보장**: 캔들 데이터의 시간적 연속성 유지
- **중복 방지**: 분할된 요청 간 데이터 중복 최소화
- **동적 조절**: 시스템 상황에 따른 분할 크기 자동 조절

### 병렬 처리 원칙
- **레이트 제한 엄수**: 업비트 API 제한 절대 위반 금지
- **리소스 보호**: CPU/메모리 과부하 방지
- **에러 격리**: 개별 요청 실패가 전체 처리에 영향 없도록
- **진행률 피드백**: 대용량 처리 시 클라이언트에 진행 상황 알림

## 🚀 Storage 완료 후 즉시 시작할 작업

### 1. Layer 2 Storage API 분석
```powershell
# Storage Layer 인터페이스 확인 (Storage 완료 후)
Get-ChildItem upbit_auto_trading\infrastructure\market_data_backbone\market_data_storage -Include "*.py" -Recurse

# Storage 응답 구조 확인
python -c "
# Storage 완료 후 실제 API 테스트
from upbit_auto_trading.infrastructure.market_data_backbone.market_data_storage import MarketDataStorageService
# 실제 연동 테스트 코드
"
```

### 2. 분할 전략 설계
- `interfaces/split_strategy.py`: ISplitStrategy 인터페이스 정의
- `strategies/candle_splitter.py`: 캔들 시간 기반 분할 로직
- 업비트 API 제한 (초당 10회) 기반 최적 분할 크기 계산

### 3. 병렬 처리 엔진 설계
- `implementations/parallel_processor.py`: 비동기 병렬 처리
- `utils/rate_limiter.py`: 업비트 API 레이트 제한 관리
- 시스템 리소스 기반 동적 동시성 조절

## 📋 관련 문서 및 리소스

### 핵심 참고 문서
- **Layer 2 Storage**: `TASK_20250822_04-market_data_storage_layer_development.md`
- **Layer 1 Smart Router**: `upbit_auto_trading/infrastructure/market_data_backbone/smart_routing/`
- **업비트 API 문서**: 레이트 제한 및 요청 크기 제한 확인

### 설계 참고 자료
- **기존 Coordinator 설계**: `tasks/active/TASK_20250820_03-market_data_coordinator_development.md`
- **분할 전략 참고**: 기존 문서의 데이터 타입별 분할 방안

## 🔄 태스크 연관성

### 의존성 태스크
- **TASK_20250822_04**: Market Data Storage Layer 개발 (필수 완료)

### 후속 태스크 계획
- **TASK_20250822_06**: Backbone API 개발 (Layer 4)
- **TASK_20250822_07**: 4계층 통합 테스트

### 전체 아키텍처에서의 위치
```
Layer 4: Backbone API (클라이언트 단일 진입점)
    ↓
Layer 3: Coordinator (대용량 요청 분할) ← 이번 태스크
    ↓
Layer 2: Storage (캐시 및 영속성) ← 이전 태스크
    ↓
Layer 1: Smart Router (채널 선택) ← 완료
```

---

## 📊 **예상 소요 시간**

### 🔥 **우선순위별 작업**
1. **Phase 1 - 인터페이스 설계**: 0.5일
2. **Phase 2 - 분할 전략**: 2일
3. **Phase 3 - 병렬 처리**: 1.5일
4. **Phase 4 - 결과 통합**: 1.5일
5. **Phase 5 - Coordinator 통합**: 1일
6. **Phase 6 - 테스트 최적화**: 0.5일

### 📈 **총 예상 소요 시간**: 7일

---

**시작 조건**: Layer 2 Storage 완료 후 즉시 시작
**핵심 가치**: 대용량 데이터 처리의 복잡성 완전 추상화
**성공 지표**: 분할 효율성 + 병렬 성능 + 데이터 정합성 + Layer 2 연동

**🎯 이번 태스크 목표**: 클라이언트가 대용량 데이터를 간단히 요청할 수 있도록 하는 지능적 조율 시스템 구축
