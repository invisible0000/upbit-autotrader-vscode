# 📋 TASK_20250822_06: Market Data Backbone API 개발

## 🎯 태스크 목표
- **주요 목표**: 모든 클라이언트가 사용할 단일 통합 마켓 데이터 API (Layer 4) 구현
- **완료 기준**:
  - ✅ 4개 기본 API 제공 (캔들/티커/호가창/체결)
  - ✅ 우선순위 기반 라우팅 (CRITICAL/HIGH/NORMAL/LOW)
  - ✅ 클라이언트 완전 자율성 (차트뷰어, 스크리너, 백테스터, 실거래봇)
  - ✅ 내부 3계층 복잡성 완전 추상화

## 📊 현재 상황 분석 (2025-08-22 기준)

### ✅ **완료된 하위 Layer 상황**
- **Layer 1: Smart Routing V2.0** ✅ 완료 - 채널 선택 및 API 호출
- **Layer 2: Market Data Storage** 🔄 개발 예정 - 캐시 및 영속성
- **Layer 3: Market Data Coordinator** 🔄 개발 예정 - 요청 분할 및 병렬 처리

### 🎯 **Layer 4: Backbone API의 역할 정의**

#### **핵심 책임**
- **단일 진입점**: 모든 클라이언트가 하나의 API로 모든 마켓 데이터 접근
- **우선순위 라우팅**: 실거래(CRITICAL) vs 백테스트(LOW) 차별화 처리
- **투명한 최적화**: 내부 3계층의 복잡성을 완전히 숨김
- **클라이언트 자율성**: 각 프로그램이 필요한 데이터를 스스로 관리

#### **클라이언트별 사용 시나리오**
```
🖥️ 차트뷰어
요청: get_candle_data("KRW-BTC", "1m", count=1000, priority=NORMAL)
처리: Layer 3에서 분할 → Layer 2에서 캐시 → Layer 1에서 API 호출
응답: 1000개 캔들 데이터 (< 2초)

🔍 스크리너
요청: get_ticker_data(KRW_symbols, priority=HIGH)
처리: Layer 3에서 심볼 분할 → 병렬 처리 → 빠른 응답
응답: 189개 KRW 마켓 티커 (< 3초)

📈 백테스터
요청: get_candle_data("KRW-BTC", "1m", start="2024-01-01", priority=LOW)
처리: Protected Path → 백그라운드 처리 → 진행률 추적
응답: 3개월 데이터 (백그라운드, 실거래 방해 없음)

🤖 실거래봇
요청: get_ticker_data(["KRW-BTC"], priority=CRITICAL)
처리: Critical Path → Layer 1 직접 호출 → 즉시 응답
응답: 현재가 데이터 (< 50ms)
```

## 🛠️ Backbone API 아키텍처 설계

### 🔗 **우선순위 기반 라우팅 흐름**

```
📱 클라이언트 → Backbone API
    ↓
Priority Router (우선순위 라우터)
    ├─ CRITICAL → Critical Path (Layer 1 직접)
    ├─ HIGH → Standard Path (Layer 3 경유)
    ├─ NORMAL → Standard Path (Layer 3 경유)
    └─ LOW → Protected Path (부하 체크 후 Layer 3)
    ↓
Path별 처리
    ├─ Critical: Layer 1 Smart Router 직접 호출
    ├─ Standard: Layer 3 Coordinator 경유
    └─ Protected: 시스템 부하 확인 후 Layer 3
    ↓
클라이언트 (투명한 응답, 내부 복잡성 모름)
```

### 📊 **핵심 API 인터페이스 설계**

```python
# 4개 기본 API 인터페이스
class MarketDataBackboneAPI:
    """모든 마켓 데이터의 단일 진입점"""

    async def get_candle_data(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        priority: Priority = Priority.NORMAL
    ) -> BackboneResponse:
        """캔들 데이터 조회"""

    async def get_ticker_data(
        self,
        symbols: List[str],
        priority: Priority = Priority.NORMAL
    ) -> BackboneResponse:
        """현재가 데이터 조회"""

    async def get_orderbook_data(
        self,
        symbols: List[str],
        priority: Priority = Priority.NORMAL
    ) -> BackboneResponse:
        """호가창 데이터 조회"""

    async def get_trade_data(
        self,
        symbol: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        priority: Priority = Priority.NORMAL
    ) -> BackboneResponse:
        """체결 데이터 조회"""

# 우선순위 열거형
class Priority(Enum):
    CRITICAL = "critical"  # 실거래봇 (< 50ms)
    HIGH = "high"         # 실시간 모니터링 (< 100ms)
    NORMAL = "normal"     # 일반 차트/스크리너 (< 500ms)
    LOW = "low"          # 백테스트 (백그라운드)

# 통합 응답 구조
@dataclass
class BackboneResponse:
    success: bool
    data: List[Dict[str, Any]]
    metadata: BackboneMetadata
    error: Optional[str] = None

@dataclass
class BackboneMetadata:
    priority_used: Priority
    path_taken: str  # "critical", "standard", "protected"
    processing_time_ms: float
    data_count: int
    source_layers: List[str]  # ["layer_1", "layer_2", "layer_3"]
    cache_hit: bool
```

## 🗺️ 체계적 작업 계획

### Phase 1: 핵심 API 인터페이스 설계 📝 **Coordinator 완료 후 시작**
- [ ] 1.1 IMarketDataBackboneAPI 인터페이스 정의
- [ ] 1.2 Priority 열거형 및 라우팅 규칙 설계
- [ ] 1.3 BackboneResponse 통합 응답 구조 설계
- [ ] 1.4 Layer 3 Coordinator 연동 인터페이스 설계

### Phase 2: 우선순위 기반 라우팅 시스템
- [ ] 2.1 PriorityRouter - 우선순위별 경로 선택
- [ ] 2.2 CriticalPath - 실거래봇 전용 고속 경로 (Layer 1 직접)
- [ ] 2.3 StandardPath - 일반 클라이언트 경로 (Layer 3 경유)
- [ ] 2.4 ProtectedPath - 백테스트 전용 보호 경로 (부하 체크)

### Phase 3: 4개 기본 API 구현
- [ ] 3.1 CandleDataAPI - 캔들 데이터 조회 (시간 범위, 개수 지원)
- [ ] 3.2 TickerDataAPI - 현재가 데이터 조회 (다중 심볼 지원)
- [ ] 3.3 OrderbookDataAPI - 호가창 데이터 조회 (실시간 지원)
- [ ] 3.4 TradeDataAPI - 체결 데이터 조회 (시간 범위 지원)

### Phase 4: 시스템 통합 및 관리
- [ ] 4.1 BackboneManager - 전체 시스템 생명주기 관리
- [ ] 4.2 Layer 연동 - Layer 1,2,3과의 완벽한 통합
- [ ] 4.3 SystemMonitor - 실시간 시스템 상태 모니터링
- [ ] 4.4 LoadBalancer - 우선순위별 부하 분산

### Phase 5: 클라이언트 지원 시스템
- [ ] 5.1 ClientAdapter - 기존 시스템 호환성 어댑터
- [ ] 5.2 ProgressTracker - 대용량 요청 진행률 추적
- [ ] 5.3 ErrorHandler - 계층별 에러 처리 및 폴백
- [ ] 5.4 MetricsCollector - 성능 지표 수집 및 분석

### Phase 6: 테스트 및 최적화
- [ ] 6.1 우선순위별 성능 테스트 (CRITICAL < 50ms 등)
- [ ] 6.2 4계층 통합 테스트
- [ ] 6.3 클라이언트별 시나리오 테스트
- [ ] 6.4 부하 테스트 및 안정성 검증

## 🛠️ 단순화된 파일 구조

```
market_data_backbone_api/              # Layer 4 - Backbone API
├── __init__.py
├── interfaces/                        # 추상 인터페이스
│   ├── __init__.py
│   ├── backbone_api.py                # IMarketDataBackboneAPI
│   ├── priority_router.py             # IPriorityRouter
│   ├── data_api.py                    # IDataAPI (4개 API 공통)
│   └── coordinator_connector.py       # ICoordinatorConnector
├── implementations/                   # 핵심 구현체
│   ├── __init__.py
│   ├── backbone_api_service.py        # MarketDataBackboneAPI (메인)
│   ├── priority_router.py             # 우선순위 라우터
│   ├── candle_data_api.py             # 캔들 데이터 API
│   ├── ticker_data_api.py             # 티커 데이터 API
│   ├── orderbook_data_api.py          # 호가창 데이터 API
│   ├── trade_data_api.py              # 체결 데이터 API
│   └── coordinator_connector.py       # Layer 3 연동
├── routing/                           # 우선순위별 라우팅
│   ├── __init__.py
│   ├── critical_path.py               # CRITICAL 경로 (Layer 1 직접)
│   ├── standard_path.py               # HIGH/NORMAL 경로 (Layer 3)
│   ├── protected_path.py              # LOW 경로 (부하 체크)
│   └── path_factory.py                # 경로 자동 선택
├── management/                        # 시스템 관리
│   ├── __init__.py
│   ├── backbone_manager.py            # 전체 시스템 생명주기
│   ├── system_monitor.py              # 시스템 상태 모니터링
│   ├── load_balancer.py               # 부하 분산
│   └── health_checker.py              # 헬스 체크
├── adapters/                          # 클라이언트 지원
│   ├── __init__.py
│   ├── legacy_adapter.py              # 기존 시스템 호환
│   ├── progress_tracker.py            # 진행률 추적
│   └── client_helpers.py              # 클라이언트 편의 기능
├── models/                            # 데이터 모델
│   ├── __init__.py
│   ├── backbone_request.py            # BackboneRequest 모델
│   ├── backbone_response.py           # BackboneResponse 모델
│   ├── priority.py                    # Priority 열거형
│   └── routing_context.py             # 라우팅 컨텍스트
├── monitoring/                        # 모니터링
│   ├── __init__.py
│   ├── performance_tracker.py         # 성능 추적
│   ├── metrics_collector.py           # 지표 수집
│   ├── dashboard_api.py               # 모니터링 대시보드
│   └── alert_system.py                # 경고 시스템
└── utils/                             # 유틸리티
    ├── __init__.py
    ├── response_builder.py            # 응답 구조 생성
    ├── error_handler.py               # 에러 처리
    ├── validation.py                  # 요청 검증
    └── time_utils.py                  # 시간 유틸리티
```

## 🎯 핵심 구현 목표

### 1. **극도의 단순화**
- **4개 API만**: get_candle_data, get_ticker_data, get_orderbook_data, get_trade_data
- **우선순위 매개변수**: priority=Priority.XXX 하나로 모든 라우팅 제어
- **통합 응답**: 모든 API가 동일한 BackboneResponse 구조 반환
- **설정 제로**: 클라이언트는 어떤 복잡한 설정도 필요 없음

### 2. **우선순위 기반 차별화**
- **CRITICAL (실거래)**: Layer 1 직접 접근, < 50ms 응답 보장
- **HIGH (모니터링)**: Layer 3 경유, < 100ms 빠른 처리
- **NORMAL (차트)**: Layer 3 경유, < 500ms 표준 처리
- **LOW (백테스트)**: Protected Path, 시스템 부하 고려하여 백그라운드 처리

### 3. **완전한 투명성**
- **내부 복잡성 숨김**: 클라이언트는 3계층 존재를 모름
- **자동 최적화**: 내부에서 알아서 최적 경로 선택
- **캐시 투명화**: 캐시 히트/미스 여부를 클라이언트가 신경 쓸 필요 없음
- **에러 추상화**: 계층별 에러를 클라이언트 친화적 메시지로 변환

### 4. **클라이언트 자율성**
- **필요한 데이터만**: 각 클라이언트가 필요한 데이터를 정확히 요청
- **자체 캐싱**: 클라이언트가 알아서 추가 캐싱 및 메모리 관리
- **비즈니스 로직**: 받은 데이터로 클라이언트가 알아서 분석/처리
- **UI 최적화**: 클라이언트가 알아서 부드러운 렌더링 및 사용자 경험

## 🔗 우선순위별 처리 흐름 상세

### **CRITICAL 경로 (실거래봇)**
```
🤖 실거래봇
    ↓ get_ticker_data(["KRW-BTC"], priority=CRITICAL)
🌐 Backbone API
    ├─ 우선순위 확인: CRITICAL → Critical Path 활성화
    └─ Layer 2,3 완전 우회
    ↓
⚡ Layer 1: Smart Router (직접 호출)
    ├─ 최고 우선순위 플래그 설정
    ├─ 가장 빠른 채널 선택 (WebSocket 우선)
    └─ 즉시 API 호출
    ↓
🤖 실거래봇 (< 50ms 내 응답, 즉시 매매 신호 판단)
```

### **STANDARD 경로 (차트뷰어)**
```
🖥️ 차트뷰어
    ↓ get_candle_data("KRW-BTC", "1m", count=1000, priority=NORMAL)
🌐 Backbone API
    ├─ 우선순위 확인: NORMAL → Standard Path
    ├─ 대용량 요청 감지: 1000개 > 임계값
    └─ Layer 3 Coordinator에 위임
    ↓
🎯 Layer 3: Coordinator
    ├─ 분할 전략: 1000개 → 5번의 200개 요청
    ├─ 병렬 처리: 5개 요청 동시 실행
    └─ Layer 2에 분할 요청
    ↓
💾 Layer 2: Storage → ⚡ Layer 1: Smart Router
    ↓
🖥️ 차트뷰어 (< 2초 내 1000개 캔들 수신, 차트 렌더링)
```

### **PROTECTED 경로 (백테스터)**
```
📈 백테스터
    ↓ get_candle_data("KRW-BTC", "1m", start="2024-01-01", priority=LOW)
🌐 Backbone API
    ├─ 우선순위 확인: LOW → Protected Path
    ├─ 시스템 부하 체크: CPU < 70%, 메모리 < 80%
    └─ 부하 허용 시에만 Layer 3에 위임
    ↓
🎯 Layer 3: Coordinator (백그라운드 처리)
    ├─ 세밀한 분할: 3개월 → 수십 번의 시간 범위별 요청
    ├─ 순차 처리: 실거래 방해 없도록 낮은 동시성
    └─ 진행률 추적: 백테스터에 진행률 피드백
    ↓
📈 백테스터 (완료된 구간부터 순차적으로 시뮬레이션 시작)
```

## 🎯 성공 기준

### 기능적 성공 기준
- ✅ **4개 API**: 캔들/티커/호가창/체결 API 완벽 동작
- ✅ **우선순위 라우팅**: CRITICAL < 50ms, LOW는 백그라운드 처리
- ✅ **투명성**: 클라이언트는 내부 3계층 존재 인식 불필요
- ✅ **클라이언트 자율성**: 각 프로그램이 필요한 데이터만 요청하여 자체 처리

### 성능적 성공 기준
- ✅ **CRITICAL 경로**: < 50ms 응답 (실거래봇)
- ✅ **HIGH 경로**: < 100ms 응답 (실시간 모니터링)
- ✅ **NORMAL 경로**: < 500ms 응답 (차트/스크리너)
- ✅ **LOW 경로**: 백그라운드 처리, 실거래 방해 없음

### 사용성 성공 기준
- ✅ **API 단순성**: 기존 대비 50% 적은 코드로 동일 기능
- ✅ **설정 제로**: 우선순위 외 어떤 설정도 불필요
- ✅ **에러 친화적**: 이해하기 쉬운 에러 메시지
- ✅ **진행률 추적**: 대용량 요청 시 실시간 진행률 제공

### 운영적 성공 기준
- ✅ **확장성**: 동시 100개 클라이언트 요청 처리
- ✅ **안정성**: 24시간 연속 운영 99.9% 가용성
- ✅ **모니터링**: 실시간 성능 지표 및 경고 시스템
- ✅ **부하 보호**: 과부하 시 LOW 우선순위 요청 자동 지연

## 💡 작업 시 주의사항

### 우선순위 라우팅 원칙
- **CRITICAL 절대 우선**: 실거래 요청은 절대 지연되어서는 안 됨
- **부하 보호**: LOW 우선순위는 시스템 부하 상황 고려
- **공정성**: 동일 우선순위 내에서는 FIFO 처리
- **투명성**: 클라이언트는 라우팅 결과를 알 필요 없음

### Layer 연동 원칙
- **투명한 위임**: Backbone은 라우팅만, 실제 처리는 하위 Layer
- **에러 추상화**: 하위 Layer 에러를 클라이언트 친화적으로 변환
- **성능 추적**: 모든 요청의 Layer별 성능 지표 수집
- **장애 격리**: 특정 Layer 장애가 전체 시스템에 영향 없도록

### 클라이언트 지원 원칙
- **기존 호환성**: 기존 API 호출 방식 100% 지원
- **점진적 마이그레이션**: 강제 전환 없는 자연스러운 전환
- **편의 기능**: 자주 사용되는 패턴의 편의 메서드 제공
- **문서화**: 명확하고 실용적인 사용 가이드

## 🚀 Coordinator 완료 후 즉시 시작할 작업

### 1. Layer 3 Coordinator API 분석
```powershell
# Coordinator Layer 인터페이스 확인 (Coordinator 완료 후)
Get-ChildItem upbit_auto_trading\infrastructure\market_data_backbone\market_data_coordinator -Include "*.py" -Recurse

# Coordinator 응답 구조 확인
python -c "
# Coordinator 완료 후 실제 API 테스트
from upbit_auto_trading.infrastructure.market_data_backbone.market_data_coordinator import MarketDataCoordinatorService
# 실제 연동 테스트 코드
"
```

### 2. 우선순위 라우팅 설계
- `routing/priority_router.py`: 우선순위별 경로 선택 로직
- `routing/critical_path.py`: 실거래봇 전용 고속 경로
- 시스템 부하 모니터링 기반 동적 라우팅 조절

### 3. 4개 기본 API 설계
- `implementations/backbone_api_service.py`: 메인 API 서비스
- 4개 데이터 타입별 API 인터페이스 통일
- 클라이언트 사용 편의성 극대화

## 📋 관련 문서 및 리소스

### 핵심 참고 문서
- **Layer 3 Coordinator**: `TASK_20250822_05-market_data_coordinator_layer_development.md`
- **Layer 2 Storage**: `TASK_20250822_04-market_data_storage_layer_development.md`
- **Layer 1 Smart Router**: `upbit_auto_trading/infrastructure/market_data_backbone/smart_routing/`

### 설계 참고 자료
- **기존 Backbone API 설계**: `tasks/active/TASK_20250820_04-market_data_backbone_api_development.md`
- **클라이언트 사용 패턴**: 차트뷰어, 스크리너, 백테스터, 실거래봇 분석

## 🔄 태스크 연관성

### 의존성 태스크
- **TASK_20250822_04**: Market Data Storage Layer 개발 (필수 완료)
- **TASK_20250822_05**: Market Data Coordinator Layer 개발 (필수 완료)

### 최종 통합 태스크
- **TASK_20250822_07**: 4계층 통합 테스트 및 시스템 검증

### 전체 아키텍처 완성
```
Layer 4: Backbone API (클라이언트 단일 진입점) ← 이번 태스크
    ↓
Layer 3: Coordinator (대용량 요청 분할) ← 이전 태스크
    ↓
Layer 2: Storage (캐시 및 영속성) ← 이전 태스크
    ↓
Layer 1: Smart Router (채널 선택) ← 완료
```

---

## 📊 **예상 소요 시간**

### 🔥 **우선순위별 작업**
1. **Phase 1 - API 인터페이스**: 0.5일
2. **Phase 2 - 우선순위 라우팅**: 1.5일
3. **Phase 3 - 4개 기본 API**: 2일
4. **Phase 4 - 시스템 통합**: 1.5일
5. **Phase 5 - 클라이언트 지원**: 1일
6. **Phase 6 - 테스트 검증**: 1일

### 📈 **총 예상 소요 시간**: 7.5일

---

**시작 조건**: Layer 2,3 완료 후 즉시 시작
**핵심 가치**: 극도로 단순한 API + 클라이언트 완전 자율성 + 우선순위 기반 처리
**성공 지표**: API 단순성 + 성능 차별화 + 투명성 + 호환성

**🎯 최종 목표**: 모든 마켓 데이터 요구사항을 4개 API로 해결하는 완벽한 단일 진입점 구축

**🌟 프로젝트 완성**: 이 태스크 완료 시 Market Data Backbone 4계층 아키텍처 완전 구현!
