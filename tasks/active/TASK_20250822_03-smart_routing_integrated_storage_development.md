# 📋 TASK_20250822_03: Market Data Backbone 4계층 통합 개발

## 🎯 태스크 목표
- **주요 목표**: 완성된 스마트 라우팅 V2.0을 기반으로 Market Data Backbone 4계층 아키텍처 완전 구현
- **완료 기준**:
  - ✅ **Layer 1**: Smart Routing V2.0 (완료) - WebSocket/REST 채널 선택 및 장애복구
  - ✅ **Layer 2**: Market Data Coordinator - 대용량 요청 분할 및 병렬 처리
  - ✅ **Layer 3**: Market Data Storage - 캔들 영속성 및 실시간 캐시
  - ✅ **Layer 4**: Backbone API - 단일 통합 인터페이스 (우선순위 기반)
  - ✅ 전체 시스템 통합 및 실전 준비 완료## 📊 현재 상황 분석 (2025-08-22 기준)

### ✅ **완료된 Layer 1: Smart Routing V2.0**
- **33개 테스트 100% 통과**: 스마트 라우팅 시스템 완전 검증 완료
- **실제 업비트 API 연동**: REST/WebSocket 클라이언트 정상 동작
- **메인 시스템 어댑터**: 기존 시스템과 완벽 연동 (`main_system_adapter.py`)
- **WebSocket 장애복구**: 3-Layer Fallback 시스템 구현
- **데이터 형식 통일**: `DataFormatUnifier`로 REST/WebSocket 응답 통일
- **채널 선택**: 실시간성/안정성 기반 최적 채널 자동 선택

### 🔄 **Market Data Backbone 4계층 아키텍처**

```
📱 클라이언트 (차트뷰어, 스크리너, 백테스터, 실거래봇)
    ↓ (단일 API 호출 + 우선순위)
🌐 Layer 4: Backbone API - 통합 인터페이스
    ↓ (우선순위별 라우팅)
🎯 Layer 3: Market Data Coordinator - 요청 분할 및 병렬 처리
    ↓ (소규모 요청들)
💾 Layer 2: Market Data Storage - 캐시 및 영속성
    ↓ (캐시 미스 시)
⚡ Layer 1: Smart Routing V2.0 - 채널 선택 및 API 호출 ✅ **완료**
    ↓ (실제 API 호출)
🏛️ 업비트 REST API & WebSocket
```

### 🎯 **4계층 역할 정의**

#### **Layer 4: Backbone API** (최상위 - 클라이언트 인터페이스)
- **단일 통합 API**: 캔들/티커/호가창/체결 4개 기본 API만 제공
- **우선순위 기반 라우팅**: CRITICAL(실거래) → HIGH(모니터링) → NORMAL(차트) → LOW(백테스트)
- **클라이언트 자율성**: 각 프로그램이 필요한 데이터를 스스로 요청
- **투명한 최적화**: 내부 복잡성 완전 추상화

#### **Layer 3: Market Data Coordinator** (요청 조율)
- **대용량 요청 분할**: 1000개 캔들 → 5번의 200개 요청으로 분할
- **병렬 처리 최적화**: 동시 요청 수 제어, 레이트 제한 준수
- **데이터 타입별 전략**: 캔들(시간 기반), 티커(심볼 기반) 등 차별화
- **결과 통합**: 분할된 응답을 완전한 데이터셋으로 합성

#### **Layer 2: Market Data Storage** (캐시 및 영속성)
- **선택적 영속성**: 캔들 데이터만 DB 저장, 실시간 데이터는 메모리 캐시
- **계층적 캐시**: Storage 메모리 → Storage 디스크 → SQLite DB
- **Smart Router 연동**: Layer 1 캐시와 협력하여 중복 방지
- **데이터 정합성**: 타임스탬프 기반 중복 검사, 연속성 검증

#### **Layer 1: Smart Routing V2.0** (채널 선택) ✅ **완료**
- **채널 선택**: WebSocket vs REST API 최적 선택
- **WebSocket 장애복구**: 3-Layer Fallback 시스템
- **데이터 형식 통일**: 채널별 응답 형식 표준화
- **실시간 메모리 캐시**: 5-30분 TTL 캐시 시스템

### 🔍 **통합 개발이 해결해야 할 핵심 과제**

#### 1. **Layer 간 효율적 통신**
- **문제**: 4개 Layer가 효율적으로 협력하면서 중복 제거 필요
- **해결 방안**: 표준 통신 프로토콜 및 인터페이스 정의
- **우선순위**: 🔥 **최우선** (아키텍처 무결성)

#### 2. **우선순위 기반 처리**
- **문제**: 실거래 요청과 백테스트 요청의 우선순위 차별화 필요
- **해결 방안**: 전체 Layer에 걸친 우선순위 전파 시스템
- **우선순위**: 🔥 **최우선** (실거래 안정성)

#### 3. **대용량 데이터 처리**
- **문제**: 백테스트용 대용량 캔들 데이터 효율적 처리
- **해결 방안**: Coordinator의 분할 전략과 Storage의 영속성 결합
- **우선순위**: 📋 **중간** (성능 최적화)

#### 4. **기존 시스템 호환성**
- **문제**: 기존 market_data_backbone 시스템과의 호환성 유지
- **해결 방안**: Backbone API의 어댑터 패턴으로 투명한 전환
- **우선순위**: 📋 **중간** (점진적 마이그레이션)

## 🛠️ Market Data Backbone 4계층 통합 아키텍처

### 🔗 **완전한 데이터 처리 흐름**

```
📱 클라이언트 요청 (차트뷰어: 1000개 캔들, priority=NORMAL)
    ↓
🌐 Layer 4: Backbone API
    ├─ 우선순위 확인: NORMAL → Standard Path
    ├─ 요청 검증: 1000개 캔들 → 대용량 요청 감지
    └─ Layer 3 Coordinator에 위임
    ↓
🎯 Layer 3: Market Data Coordinator
    ├─ 분할 전략: 1000개 → 5번의 200개 요청
    ├─ 병렬 처리: 5개 요청 동시 실행
    └─ 각 요청을 Layer 2에 전달
    ↓
💾 Layer 2: Market Data Storage
    ├─ 캐시 확인: Storage 메모리 → Storage 디스크 → SQLite DB
    ├─ 캐시 미스 시 Layer 1에 요청
    └─ 받은 데이터를 캐시에 저장
    ↓
⚡ Layer 1: Smart Routing V2.0 ✅ **완료**
    ├─ 채널 선택: WebSocket vs REST 최적 선택
    ├─ 실제 API 호출: 업비트 API 호출
    ├─ 데이터 형식 통일: 표준 응답 구조 변환
    └─ Layer 2로 데이터 반환
    ↓
📊 결과 통합 및 반환
    ├─ Layer 3: 5개 응답을 1000개 캔들로 통합
    ├─ Layer 4: 클라이언트에 최종 응답
    └─ 클라이언트: 받은 데이터로 차트 렌더링
```

### 🎯 **우선순위별 처리 흐름**

#### **CRITICAL 경로 (실거래봇)**
```
실거래봇 (긴급 티커 요청)
    ↓ priority=CRITICAL
Layer 4: Backbone API → Critical Path 활성화
    ↓ (Layer 2,3 우회)
Layer 1: Smart Router → 즉시 API 호출
    ↓
실거래봇 (< 50ms 응답, 매매 신호 판단)
```

#### **LOW 경로 (백테스터)**
```
백테스터 (대용량 캔들 요청)
    ↓ priority=LOW
Layer 4: Backbone API → Protected Path (부하 체크)
    ↓ (시스템 여유 있을 때만)
Layer 3: Coordinator → 세밀한 분할 처리
    ↓
Layer 2: Storage → 백그라운드 캐싱
    ↓
Layer 1: Smart Router → 비긴급 API 호출
```

### 🔄 **Layer 간 통신 프로토콜**

#### **표준 요청/응답 구조**
```python
# 모든 Layer 간 표준 요청 구조
@dataclass
class BackboneRequest:
    data_type: DataType  # CANDLE, TICKER, ORDERBOOK, TRADE
    symbols: List[str]
    timeframe: Optional[str] = None  # 캔들용
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    count: Optional[int] = None
    priority: Priority = Priority.NORMAL  # CRITICAL, HIGH, NORMAL, LOW
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

# 모든 Layer 간 표준 응답 구조
@dataclass
class BackboneResponse:
    success: bool
    data: List[Dict[str, Any]]
    metadata: BackboneMetadata
    error: Optional[str] = None
    request_id: str = ""

@dataclass
class BackboneMetadata:
    source_layer: str  # "layer_1", "layer_2", "layer_3", "layer_4"
    cache_hit: bool
    processing_time_ms: float
    data_count: int
    priority_used: Priority
    split_info: Optional[Dict] = None  # Coordinator 분할 정보
```

## 🗺️ 체계적 4계층 통합 작업 계획

### Phase 1: Layer 간 통신 프로토콜 설계 📝 **즉시 시작 가능**
- [ ] 1.1 표준 요청/응답 구조 설계 (BackboneRequest/Response)
- [ ] 1.2 우선순위 전파 시스템 설계 (CRITICAL → LOW)
- [ ] 1.3 Layer 간 인터페이스 정의 (ILayer2, ILayer3, ILayer4)
- [ ] 1.4 에러 처리 및 폴백 체계 설계

### Phase 2: Layer 3 - Market Data Coordinator 구현
- [ ] 2.1 IMarketDataCoordinator 인터페이스 구현
- [ ] 2.2 데이터 타입별 분할 전략 (캔들, 티커, 호가창, 체결)
- [ ] 2.3 병렬 처리 및 레이트 제한 시스템
- [ ] 2.4 Layer 1 (Smart Router) 연동 및 결과 통합

### Phase 3: Layer 2 - Market Data Storage 구현
- [ ] 3.1 IMarketDataStorage 인터페이스 구현
- [ ] 3.2 선택적 영속성 시스템 (캔들=DB, 실시간=메모리)
- [ ] 3.3 계층적 캐시 (Storage 메모리 → 디스크 → SQLite)
- [ ] 3.4 Layer 1 캐시와 연동하여 중복 방지

### Phase 4: Layer 4 - Backbone API 구현
- [ ] 4.1 IMarketDataBackboneAPI 통합 인터페이스
- [ ] 4.2 우선순위 기반 라우팅 (Critical/Standard/Protected Path)
- [ ] 4.3 클라이언트별 최적화 (차트뷰어, 스크리너, 백테스터, 실거래봇)
- [ ] 4.4 기존 시스템 호환 어댑터 구현

### Phase 5: 전체 시스템 통합 및 최적화
- [ ] 5.1 4계층 통합 테스트 및 검증
- [ ] 5.2 우선순위별 성능 벤치마크
- [ ] 5.3 실거래 시나리오 검증 (CRITICAL 경로)
- [ ] 5.4 시스템 모니터링 및 메트릭 수집

## 🛠️ 4계층 파일 구조 및 구현 계획

### Market Data Backbone 전체 구조
```
market_data_backbone/
├── __init__.py
├── layer_1_smart_routing/             # ✅ 완료 - Smart Routing V2.0
│   ├── __init__.py                   # 기존 smart_routing 폴더
│   ├── smart_router.py               # ✅ 완료
│   ├── models.py                     # ✅ 완료
│   ├── data_format_unifier.py        # ✅ 완료
│   ├── channel_selector.py           # ✅ 완료
│   └── main_system_adapter.py        # ✅ 완료
├── layer_2_storage/                   # 🔥 새로 구현 - Market Data Storage
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── storage_service.py        # IMarketDataStorage
│   │   ├── cache_layer.py            # ICacheLayer
│   │   └── repository.py             # IRepository
│   ├── implementations/
│   │   ├── __init__.py
│   │   ├── storage_service.py        # Storage 메인 서비스
│   │   ├── candle_repository.py      # 캔들 영속성 (SQLite)
│   │   ├── realtime_cache.py         # 실시간 데이터 캐시
│   │   └── layer1_connector.py       # Layer 1 연동
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── memory_cache.py           # Storage 메모리 캐시
│   │   ├── disk_cache.py             # Storage 디스크 캐시
│   │   └── cache_policies.py         # TTL, LRU 정책
│   └── persistence/
│       ├── __init__.py
│       ├── sqlite_manager.py         # SQLite 연결 관리
│       ├── schema_manager.py         # 스키마 관리
│       └── optimization_manager.py   # DB 최적화
├── layer_3_coordinator/              # 🔥 새로 구현 - Market Data Coordinator
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── coordinator.py            # IMarketDataCoordinator
│   │   ├── splitter.py               # ISplitStrategy
│   │   └── aggregator.py             # IDataAggregator
│   ├── implementations/
│   │   ├── __init__.py
│   │   ├── coordinator_service.py    # 메인 조율자
│   │   ├── request_splitter.py       # 요청 분할기
│   │   ├── data_aggregator.py        # 결과 통합기
│   │   └── layer2_connector.py       # Layer 2 연동
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── candle_splitter.py        # 캔들 시간 기반 분할
│   │   ├── ticker_splitter.py        # 티커 심볼 기반 분할
│   │   ├── orderbook_splitter.py     # 호가창 심볼 기반 분할
│   │   └── trade_splitter.py         # 체결 시간/카운트 분할
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py           # 레이트 제한 관리
│       ├── retry_handler.py          # 재시도 로직
│       └── validators.py             # 데이터 검증
├── layer_4_backbone_api/             # 🔥 새로 구현 - Backbone API
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── backbone_api.py           # IMarketDataBackboneAPI
│   │   ├── priority_router.py        # IPriorityRouter
│   │   └── client_adapter.py         # IClientAdapter
│   ├── implementations/
│   │   ├── __init__.py
│   │   ├── backbone_api_service.py   # 메인 API 서비스
│   │   ├── priority_router.py        # 우선순위 라우터
│   │   ├── layer3_connector.py       # Layer 3 연동
│   │   └── legacy_adapter.py         # 기존 시스템 호환
│   ├── routing/
│   │   ├── __init__.py
│   │   ├── critical_path.py          # CRITICAL 경로 (실거래)
│   │   ├── standard_path.py          # NORMAL/HIGH 경로
│   │   └── protected_path.py         # LOW 경로 (백테스트)
│   └── monitoring/
│       ├── __init__.py
│       ├── metrics_collector.py      # 성능 메트릭 수집
│       ├── system_monitor.py         # 시스템 상태 모니터링
│       └── dashboard_api.py          # 모니터링 대시보드 API
├── shared/                            # 🔗 공통 모듈
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── backbone_request.py       # 표준 요청 모델
│   │   ├── backbone_response.py      # 표준 응답 모델
│   │   ├── priority.py               # 우선순위 열거형
│   │   └── data_types.py             # 데이터 타입 열거형
│   ├── protocols/
│   │   ├── __init__.py
│   │   ├── layer_communication.py    # Layer 간 통신 프로토콜
│   │   └── error_handling.py         # 에러 처리 표준
│   └── utils/
│       ├── __init__.py
│       ├── time_utils.py             # 시간 유틸리티
│       ├── validation.py             # 공통 검증 로직
│       └── logging_utils.py          # 로깅 유틸리티
└── integration/                       # 🔄 통합 및 테스트
    ├── __init__.py
    ├── backbone_manager.py           # 전체 시스템 생명주기 관리
    ├── integration_tests/
    │   ├── __init__.py
    │   ├── test_4layer_integration.py
    │   ├── test_priority_routing.py
    │   └── test_performance.py
    └── monitoring/
        ├── __init__.py
        ├── health_checker.py         # 시스템 헬스 체크
        └── performance_tracker.py    # 성능 추적
```

## 🎯 4계층 통합 구현 목표

### 1. **Layer 4: Backbone API - 완벽한 클라이언트 인터페이스**
- **단일 통합 API**: 캔들/티커/호가창/체결 4개 기본 API만 제공
- **우선순위 기반 라우팅**: CRITICAL(실거래) 최고 성능, LOW(백테스트) 리소스 보호
- **클라이언트 자율성**: 각 프로그램이 필요한 데이터를 스스로 요청하여 사용
- **투명한 최적화**: 내부 3개 Layer의 복잡성 완전 추상화

### 2. **Layer 3: Coordinator - 효율적 대용량 처리**
- **지능적 분할**: 1000개 캔들 → 5번의 200개 요청으로 자동 분할
- **병렬 처리**: 동시 요청 수 제어, 레이트 제한 준수
- **데이터 타입별 최적화**: 캔들(시간), 티커(심볼), 호가창(심볼), 체결(시간/카운트)
- **결과 통합**: 분할된 응답을 완전한 데이터셋으로 합성

### 3. **Layer 2: Storage - 선택적 영속성 및 캐시**
- **선택적 영속성**: 캔들만 SQLite DB 저장, 실시간 데이터는 메모리 캐시만
- **계층적 캐시**: Storage 메모리 → Storage 디스크 → SQLite DB
- **Layer 1 연동**: Smart Router 캐시와 협력하여 중복 방지
- **데이터 정합성**: 타임스탬프 기반 중복 검사, 연속성 검증

### 4. **Layer 1: Smart Router - 채널 선택 및 API 호출** ✅ **완료**
- **채널 선택**: WebSocket vs REST API 최적 선택
- **WebSocket 장애복구**: 3-Layer Fallback 시스템
- **데이터 형식 통일**: 채널별 응답 형식 표준화
- **실시간 메모리 캐시**: 5-30분 TTL 캐시 시스템

### 5. **전체 시스템 통합**
- **4계층 생명주기 관리**: BackboneManager로 자동 초기화/종료
- **우선순위 전파**: 모든 Layer에 걸친 우선순위 기반 처리
- **에러 처리**: Layer별 폴백 및 복구 메커니즘
- **모니터링**: 실시간 성능 메트릭 및 시스템 상태 추적

## 🔗 4계층 통합 협력 흐름

### **일반적인 데이터 요청 흐름 (차트뷰어 예시)**
```
🖥️ 차트뷰어: "KRW-BTC 1분봉 1000개 조회" + priority=NORMAL
    ↓
🌐 Layer 4: Backbone API
    ├─ 요청 검증: 1000개 캔들 → 대용량 요청 감지
    ├─ 우선순위: NORMAL → Standard Path 선택
    └─ Layer 3 Coordinator에 위임
    ↓
🎯 Layer 3: Coordinator
    ├─ 분할 전략: 1000개 → 5번의 200개 요청
    ├─ 병렬 처리: 5개 요청 동시 실행
    └─ 각 요청을 Layer 2에 전달
    ↓
💾 Layer 2: Storage
    ├─ 캐시 확인: Storage 메모리 → Storage 디스크 → SQLite DB
    ├─ 캐시 미스: Layer 1에 200개 캔들 요청
    └─ 받은 데이터를 모든 캐시 레벨에 저장
    ↓
⚡ Layer 1: Smart Router ✅ **완료**
    ├─ 채널 선택: WebSocket vs REST 최적 선택
    ├─ API 호출: 업비트 API 호출
    ├─ 데이터 형식 통일: 표준 응답 구조 변환
    └─ Layer 2로 200개 캔들 데이터 반환
    ↓
📊 결과 통합 및 반환
    ├─ Layer 2: 200개 캔들 캐시 저장
    ├─ Layer 3: 5개 응답을 1000개 캔들로 통합
    ├─ Layer 4: 클라이언트에 최종 응답
    └─ 차트뷰어: 받은 1000개 캔들로 차트 렌더링
```

### **실거래 긴급 요청 흐름 (CRITICAL 경로)**
```
🤖 실거래봇: "KRW-BTC 현재가" + priority=CRITICAL
    ↓
🌐 Layer 4: Backbone API
    ├─ 우선순위: CRITICAL → Critical Path 활성화
    └─ Layer 2,3 완전 우회 → Layer 1 직접 호출
    ↓
⚡ Layer 1: Smart Router
    ├─ 최고 우선순위: 즉시 API 호출
    ├─ 채널 선택: 가장 빠른 채널 선택
    └─ < 50ms 내 응답 보장
    ↓
🤖 실거래봇: 즉시 매매 신호 판단 및 실행
```

### **대용량 백테스트 요청 흐름 (LOW 경로)**
```
📈 백테스터: "KRW-BTC 1분봉 3개월 데이터" + priority=LOW
    ↓
🌐 Layer 4: Backbone API
    ├─ 우선순위: LOW → Protected Path 활성화
    ├─ 시스템 부하 체크: 여유 있을 때만 처리
    └─ Layer 3에 위임 (백그라운드 처리)
    ↓
🎯 Layer 3: Coordinator
    ├─ 세밀한 분할: 3개월 → 수십 번의 시간 범위별 요청
    ├─ 순차 처리: 시스템 부하 최소화
    └─ 진행률 추적: 백테스터에 진행률 피드백
    ↓
💾 Layer 2: Storage
    ├─ 캐시 확인: 기존 데이터 최대한 활용
    ├─ 증분 요청: 없는 데이터만 Layer 1에 요청
    └─ 배치 저장: 대용량 데이터 효율적 DB 저장
    ↓
📈 백테스터: 완료된 구간부터 순차적으로 시뮬레이션 시작
```

### **실시간 스크리닝 요청 흐름 (HIGH 경로)**
```
🔍 스크리너: "KRW 마켓 전체 티커" + priority=HIGH
    ↓
🌐 Layer 4: Backbone API
    ├─ 우선순위: HIGH → Standard Path (빠른 처리)
    └─ Layer 3에 위임
    ↓
🎯 Layer 3: Coordinator
    ├─ 심볼 분할: 189개 KRW 마켓 → 20번의 10개씩 요청
    ├─ 병렬 처리: 높은 동시성으로 빠른 처리
    └─ Layer 2에 다중 요청
    ↓
💾 Layer 2: Storage
    ├─ 캐시 우선: 대부분 캐시에서 즉시 응답
    ├─ 캐시 미스: 일부만 Layer 1에 요청
    └─ 실시간 캐시 갱신
    ↓
🔍 스크리너: 받은 티커 데이터로 조건 필터링 및 알림
```

## 🎯 4계층 통합 성공 기준

### Layer별 성공 기준

#### **Layer 4: Backbone API**
- ✅ **단일 API**: 캔들/티커/호가창/체결 4개 기본 API만 제공
- ✅ **우선순위 처리**: CRITICAL < 50ms, HIGH < 100ms, NORMAL < 500ms, LOW 백그라운드
- ✅ **클라이언트 투명성**: 내부 복잡성 완전 추상화
- ✅ **기존 호환**: 기존 API 호출 방식 100% 지원

#### **Layer 3: Coordinator**
- ✅ **대용량 분할**: 1000개+ 요청 자동 분할 및 병렬 처리
- ✅ **레이트 제한**: 업비트 API 제한 준수 (초당 10회)
- ✅ **데이터 정합성**: 분할/통합 과정에서 데이터 손실 없음
- ✅ **타입별 최적화**: 캔들/티커/호가창/체결 각각 최적 전략 적용

#### **Layer 2: Storage**
- ✅ **선택적 영속성**: 캔들만 DB 저장, 실시간 데이터는 메모리만
- ✅ **캐시 효율**: 전체 캐시 히트율 > 85%
- ✅ **DB 성능**: 캔들 1000개 조회 < 100ms
- ✅ **메모리 관리**: 중복 캐싱 방지로 메모리 50% 절약

#### **Layer 1: Smart Router** ✅ **완료**
- ✅ **채널 선택**: 실시간성/안정성 기반 최적 선택
- ✅ **장애복구**: WebSocket 3-Layer Fallback 정상 동작
- ✅ **데이터 통일**: REST/WebSocket 응답 100% 통일
- ✅ **성능**: 평균 응답시간 < 50ms

### 전체 시스템 성공 기준
- ✅ **우선순위 보장**: CRITICAL 요청이 LOW 요청에 방해받지 않음
- ✅ **확장성**: 동시 100개 클라이언트 요청 처리 가능
- ✅ **안정성**: 24시간 연속 운영 99.9% 가용성
- ✅ **모니터링**: 실시간 성능 메트릭 및 시스템 상태 추적

### 클라이언트별 성공 기준
- ✅ **차트뷰어**: 1000개 캔들 < 1초, 실시간 업데이트 부드러움
- ✅ **스크리너**: 189개 KRW 마켓 티커 < 2초, 조건 필터링 정확
- ✅ **백테스터**: 3개월 데이터 백그라운드 처리, 진행률 추적
- ✅ **실거래봇**: 긴급 요청 < 50ms, 시스템 지연 없음

##  즉시 시작할 작업

### 1. 4계층 아키텍처 기반 설계 확인
```powershell
# 기존 Smart Router 구조 분석 (Layer 1)
Get-ChildItem upbit_auto_trading\infrastructure\market_data_backbone\smart_routing -Recurse -Include "*.py"

# 기존 market_data_backbone 시스템 분석
Get-ChildItem upbit_auto_trading\infrastructure\market_data_backbone -Recurse -Name

# DB 스키마 확인
python tools\super_db_table_viewer.py market_data
```

### 2. Layer 간 표준 통신 프로토콜 설계
```python
# shared/models/backbone_request.py 설계 시작
@dataclass
class BackboneRequest:
    data_type: DataType  # CANDLE, TICKER, ORDERBOOK, TRADE
    symbols: List[str]
    priority: Priority   # CRITICAL, HIGH, NORMAL, LOW
    # ... 기타 필수 필드

# shared/models/backbone_response.py 설계 시작
@dataclass
class BackboneResponse:
    success: bool
    data: List[Dict[str, Any]]
    metadata: BackboneMetadata
    # ... 기타 필수 필드
```

### 3. Layer 2 (Storage) 인터페이스 정의부터 시작
- `layer_2_storage/interfaces/storage_service.py` 설계
- Layer 1 (Smart Router)과의 연동점 분석
- 선택적 영속성 전략 구체화

## 📋 관련 문서 및 리소스

### 핵심 참고 문서
- **Layer 1 완료**: `upbit_auto_trading/infrastructure/market_data_backbone/smart_routing/`
- **기존 Backbone**: `upbit_auto_trading/infrastructure/market_data_backbone/`
- **Coordinator 설계**: `tasks/active/TASK_20250820_03-market_data_coordinator_development.md`
- **Backbone API 설계**: `tasks/active/TASK_20250820_04-market_data_backbone_api_development.md`

### 테스트 리소스
- **Smart Router 테스트**: `tests/infrastructure/smart_routing_test/`
- **통합 테스트 계획**: 4계층 전체 통합 테스트 필요

## 🔄 이전 태스크와의 연관성

### 완료된 선행 작업 ✅
- **TASK_20250822_01**: 스마트 라우팅 V2.0 통합 완료 (100% 완료)
- **TASK_20250822_02**: 스마트 라우팅 완전 검증 완료 (68.8% 성공률, 핵심 기능 정상)

### 통합 대상 태스크들
- **TASK_20250820_03**: Market Data Coordinator 개발 → **Layer 3**
- **TASK_20250820_02**: Market Data Storage 개발 → **Layer 2**
- **TASK_20250820_04**: Backbone API 개발 → **Layer 4**

### 통합 후 효과
- **단일 진입점**: 모든 클라이언트가 Backbone API 하나로 통합
- **효율성 극대화**: 4계층이 협력하여 최적 성능
- **확장성**: 각 Layer 독립적 최적화 가능
- **유지보수성**: 계층별 책임 분리로 관리 용이

---

## 📊 **예상 소요 시간 및 우선순위**

### 🔥 **최우선 (즉시 시작)**
1. **Phase 1 - Layer 간 통신 프로토콜**: 1-2일 소요
2. **Phase 2 - Layer 2 Storage**: 2-3일 소요

### 📅 **고우선순위 (1주 내 완료)**
3. **Phase 3 - Layer 3 Coordinator**: 2-3일 소요
4. **Phase 4 - Layer 4 Backbone API**: 1-2일 소요

### 🔧 **통합 및 최적화**
5. **Phase 5 - 전체 시스템 통합**: 1-2일 소요

### 📈 **전체 예상 소요 시간**: 1.5-2주

---

**시작 조건**: ✅ **즉시 시작 가능** - Layer 1 (Smart Routing V2.0) 완전 준비 완료
**핵심 가치**: 완전한 4계층 Market Data Backbone 구축으로 모든 마켓 데이터 요구사항 통합 해결
**성공 지표**: 클라이언트 완전 자율성 + 우선순위 기반 처리 + 확장성 + 유지보수성

**⚠️ 핵심 포인트**:
- **원래 설계 존중**: 4계층 아키텍처 완전 구현으로 설계 의도 실현
- **Layer 1 기반**: 완성된 Smart Router를 견고한 기반으로 활용
- **우선순위 중심**: 실거래 안정성을 최우선으로 하는 시스템 구축
- **클라이언트 자율성**: 각 프로그램이 필요한 데이터를 스스로 관리하는 구조

**🎯 최종 목표**: 스마트 라우팅 V2.0을 기반으로 한 완전한 Market Data Backbone 4계층 시스템 구축으로 모든 마켓 데이터 니즈 통합 해결
